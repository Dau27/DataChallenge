from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from decimal import Decimal
from threading import Barrier
import json

import httpx
import pytest
from sqlalchemy import delete, select

from backend.app.config import Settings
from backend.app.db import BudgetReservation, BudgetState, Database
from backend.app.domain import content_hash
from backend.app.services.budget import Budget, BudgetError, evaluation_bound
from backend.app.services.evaluator import Provider, EvaluationFailure
from backend.tests.test_workflow import client_and_calls, import_one, evaluate_one, response_for, synthetic_payload


def test_zero_default_blocks_ui_batch_and_access_check_before_any_request(tmp_path):
    client, calls, _ = client_and_calls(tmp_path, budget_limit_usd=Decimal(0))
    with client:
        cid = import_one(client)
        preview = client.post('/api/evaluations/preview', json={'conversation_ids': [cid], 'checklist_id': 1}).json()
        assert preview['affordable'] is False and 'zero spending' in preview['blocked_reason']
        assert client.post('/api/evaluations', json={'conversation_ids': [cid], 'checklist_id': 1}).status_code == 409
        assert client.post('/api/access/check-provider').status_code == 409
        assert client.get('/api/evaluations').json() == []
        assert calls == []
        assert client.get('/api/budget').json()['reserved_usd'] == '0'


def test_unreserved_adapter_cannot_send_even_with_a_test_transport(tmp_path):
    calls = []
    provider = Provider(Settings(database_path=tmp_path/'x.db'), httpx.MockTransport(lambda r: calls.append(r)))
    with pytest.raises(EvaluationFailure, match='reservation'):
        provider.request({'max_output_tokens': 256}, lambda *args: 0)
    assert calls == []


def test_atomic_reservations_across_two_instances_do_not_oversubscribe(tmp_path):
    db = Database(tmp_path/'atomic.db')
    settings = Settings(input_rate=Decimal('.4'), output_rate=Decimal('1.6'), rate_source='TEST RATE',
                        budget_limit_usd=Decimal('1'), budget_overhead_usd=Decimal(0))
    first, second = Budget(db, settings), Budget(db, settings)
    barrier = Barrier(2)
    def reserve(service, key):
        barrier.wait()
        try:
            with db.transaction() as session:
                service.reserve(session, 'access_check', key, Decimal('.6'), 2)
            return True
        except BudgetError:
            return False
    with ThreadPoolExecutor(2) as pool:
        a = pool.submit(reserve, first, 'A'); b = pool.submit(reserve, second, 'B')
        assert sorted([a.result(), b.result()]) == [False, True]
    assert Decimal(first.status()['reserved_usd']) == Decimal('.6')
    db.engine.dispose()


def test_unaffordable_batch_rolls_back_all_new_jobs(tmp_path):
    client, calls, _ = client_and_calls(tmp_path, budget_limit_usd=Decimal('.001'))
    with client:
        first = import_one(client)
        payload = synthetic_payload(source_id='SECOND_SYNTHETIC')
        second = client.post('/api/import/json', json=payload).json()['conversation_ids'][0]
        response = client.post('/api/evaluations', json={'conversation_ids': [first, second], 'checklist_id': 1})
        assert response.status_code == 409
        assert client.get('/api/evaluations').json() == [] and calls == []
        with client.app.state.db.sessions() as session:
            assert list(session.scalars(select(BudgetReservation))) == []


def test_settlement_releases_unused_retry_reserve_and_cached_reuse_is_free(tmp_path):
    client, calls, _ = client_and_calls(tmp_path)
    with client:
        cid = import_one(client)
        result = evaluate_one(client, cid)
        assert len(calls) == 1
    paused, later_calls, _ = client_and_calls(tmp_path, budget_limit_usd=Decimal(0))
    with paused:
        state = paused.get('/api/budget').json()
        assert Decimal(state['accounted_usd']) == Decimal(result['usage']['estimated_cost_usd'])
        assert Decimal(state['reserved_usd']) == 0
        preview = paused.post('/api/evaluations/preview', json={'conversation_ids': [cid], 'checklist_id': 1}).json()
        assert preview['cached'] == 1 and preview['affordable'] and Decimal(preview['required_reservation_usd']) == 0
        cached = evaluate_one(paused, cid)
        assert cached['cached_from'] == result['id'] and later_calls == []
        appeal = paused.post(f"/api/evaluations/{result['id']}/appeals", json={'criterion_id': 'contact', 'comment': 'SYNTHETIC free review'}).json()['id']
        assert paused.post('/api/appeals/'+appeal+'/decision', json={'action': 'confirm', 'judgment': None,
            'rationale': 'SYNTHETIC review while spending paused', 'expected_updated_at': result['updated_at']}).status_code == 201
        assert later_calls == [] and paused.get('/api/budget').json()['accounted_usd'] == state['accounted_usd']
        assert paused.post('/api/evaluations', json={'conversation_ids': [cid], 'checklist_id': 1, 'reuse_cache': False}).status_code == 409


def test_unknown_usage_survives_restart_and_paused_retry_cannot_spend(tmp_path):
    client, calls, _ = client_and_calls(tmp_path, lambda _: httpx.Response(429, json={'error': {'code': 'insufficient_quota'}}))
    with client:
        result = evaluate_one(client, import_one(client))
        assert result['state'] == 'failed' and len(calls) == 1
    paused, calls2, _ = client_and_calls(tmp_path, budget_limit_usd=Decimal(0))
    with paused:
        status = paused.get('/api/budget').json()
        assert Decimal(status['accounted_usd']) > 0 and Decimal(status['reserved_usd']) == 0
        assert paused.post(f"/api/evaluations/{result['id']}/retry").status_code == 409
        assert paused.get(f"/api/evaluations/{result['id']}").json()['attempts'] == result['attempts'] and calls2 == []


def test_retry_with_changed_prices_requires_a_new_evaluation(tmp_path):
    client, _, _ = client_and_calls(tmp_path, lambda _: httpx.Response(429, json={'error': {'code': 'insufficient_quota'}}))
    with client:
        result = evaluate_one(client, import_one(client))
    changed, calls, _ = client_and_calls(tmp_path, input_rate=Decimal('.5'))
    with changed:
        response = changed.post(f"/api/evaluations/{result['id']}/retry")
        assert response.status_code == 422 and 'Cost rates changed' in response.json()['detail']
        assert calls == [] and changed.get(f"/api/evaluations/{result['id']}").json()['attempts'] == result['attempts']


def test_every_access_check_is_accounted_even_when_last_report_is_replaced(tmp_path):
    client, calls, _ = client_and_calls(tmp_path, lambda _: httpx.Response(200, json=response_for({'ok': True})))
    with client:
        for _ in range(2):
            assert client.post('/api/access/check-provider').json()['succeeded']
    restarted, _, _ = client_and_calls(tmp_path)
    with restarted:
        status = restarted.get('/api/budget').json()
        assert status['ready'] and Decimal(status['accounted_usd']) == Decimal('.00024')
        assert len(calls) == 2


def test_crash_keeps_started_unknown_request_cost_but_releases_unsent_part(tmp_path):
    db = Database(tmp_path/'crash.db')
    settings = Settings(input_rate=Decimal('.4'), output_rate=Decimal('1.6'), rate_source='TEST RATE', budget_limit_usd=Decimal('1'))
    service = Budget(db, settings)
    with db.transaction() as session:
        rid = service.reserve(session, 'access_check', 'crashed-check', Decimal('.1'), 2)
    service.recorder(rid)({'status': 'started', 'input_tokens': None, 'output_tokens': None,
                           'input_token_upper_bound': 1000, 'max_output_tokens': 200})
    restarted = Budget(db, settings); restarted.recover()
    assert Decimal(restarted.status()['accounted_usd']) == Decimal('.00072')
    assert Decimal(restarted.status()['reserved_usd']) == 0
    db.engine.dispose()


def test_request_bound_and_attempt_count_are_enforced_before_recording_a_send(tmp_path):
    db = Database(tmp_path/'bounds.db')
    settings = Settings(input_rate=Decimal('.4'), output_rate=Decimal('1.6'), rate_source='TEST RATE', budget_limit_usd=Decimal('1'))
    service = Budget(db, settings)
    with db.transaction() as session:
        rid = service.reserve(session, 'access_check', 'bounded', Decimal('.001'), 1)
    record = service.recorder(rid)
    with pytest.raises(BudgetError, match='cost bound'):
        record({'input_token_upper_bound': 10000, 'max_output_tokens': 1000})
    with db.sessions() as session:
        assert session.get(BudgetReservation, rid).attempts == []
    record({'input_token_upper_bound': 100, 'max_output_tokens': 100, 'input_tokens': None, 'output_tokens': None})
    with pytest.raises(BudgetError, match='attempt limit'):
        record({'input_token_upper_bound': 100, 'max_output_tokens': 100})
    service.settle(rid)
    assert Decimal(service.status()['accounted_usd']) == Decimal('.0002')
    db.engine.dispose()


def test_missing_or_incorrect_rates_and_changed_untracked_history_fail_closed(tmp_path):
    client, calls, _ = client_and_calls(tmp_path, input_rate=None)
    with client:
        cid = import_one(client)
        assert client.post('/api/evaluations', json={'conversation_ids': [cid], 'checklist_id': 1}).status_code == 409
        assert calls == []


@pytest.mark.parametrize('valid', [False, True])
def test_reviewed_historical_baseline_includes_external_spend_without_double_counting(tmp_path, valid):
    client, _, _ = client_and_calls(tmp_path)
    with client:
        result = evaluate_one(client, import_one(client))
    db = Database(tmp_path/'test.sqlite3')
    with db.transaction() as session:
        session.execute(delete(BudgetReservation)); session.execute(delete(BudgetState))
    db.engine.dispose()
    baseline = {'schema_version': 1, 'opening_usd': '.5', 'provenance': 'TEST historical and external audit reservation',
                'coverage': {'evaluations': {result['id']: {'attempt_count': len(result['attempts']),
                    'attempts_hash': content_hash(result['attempts']) if valid else 'INVALID', 'metadata_hash': content_hash(result['metadata']),
                    'accounted_usd': result['usage']['estimated_cost_usd']}}, 'access_checks': {}}}
    path = tmp_path/'baseline.json'; path.write_text(json.dumps(baseline))
    restarted, calls, _ = client_and_calls(tmp_path, budget_baseline_path=path)
    with restarted:
        status = restarted.get('/api/budget').json()
        assert status['ready'] is valid
        if valid:
            assert Decimal(status['accounted_usd']) == Decimal('.5')
        else:
            assert restarted.post('/api/access/check-provider').status_code == 409 and calls == []
