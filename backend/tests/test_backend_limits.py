"""Read-path and streaming-limit regressions using synthetic data only."""
from decimal import Decimal
import asyncio
import gzip
import json

import httpx
import pytest
from sqlalchemy import event, update

from backend.app.config import Settings
from backend.app.db import BudgetReservation, BudgetState, Database, Evaluation
from backend.app.limits import RequestBodyLimit
from backend.app.services import importer
from backend.app.services.budget import Budget
from backend.app.services.importer import fetch_organizer
from backend.tests.test_saved_inspection import saved, db_rows
from backend.tests.test_workflow import client_and_calls, synthetic_payload


def test_queue_and_history_headers_do_not_materialize_assessment_objects(saved):
    client, db, _, cid, add = saved
    for i in range(30):
        add(f"SYNTHETIC_HISTORY_{i}")
    loaded = []
    def track(row, context):
        loaded.append(row.id)
    before = db_rows(db)
    event.listen(Evaluation, 'load', track)
    try:
        queue = client.get('/api/conversations?checklist_id=1').json()
        history = client.get('/api/evaluations', params={'conversation_id': cid}).json()
        detail = client.get('/api/conversations/' + cid).json()
    finally:
        event.remove(Evaluation, 'load', track)
    assert loaded == []
    assert queue[0]['evaluation'] == history[0] == detail['evaluations'][0]
    assert len(history) == len(detail['evaluations']) == 32
    assert set(queue[0]['evaluation']) == {'id', 'conversation_id', 'checklist_id', 'state', 'completeness', 'cached_from', 'total', 'error', 'created_at', 'updated_at'}
    assert db_rows(db) == before


def test_equal_timestamp_selection_is_deterministic_in_all_summary_views(saved):
    client, db, _, cid, _ = saved
    with db.transaction() as session:
        session.execute(update(Evaluation).values(created_at='2026-01-01T00:00:00+00:00'))
    for _ in range(2):
        assert client.get('/api/conversations?checklist_id=1').json()[0]['evaluation']['id'] == 'right'
        assert client.get('/api/evaluations').json()[0]['id'] == 'right'
        assert client.get('/api/conversations/' + cid).json()['evaluations'][0]['id'] == 'right'


def test_empty_history_filter_keeps_the_existing_unfiltered_contract(saved):
    client, _, _, _, _ = saved
    assert client.get('/api/evaluations?conversation_id=').json() == client.get('/api/evaluations').json()


def test_latest_failed_run_keeps_null_score_and_old_revision_appeal_target(saved):
    client, db, rubric, cid, add = saved
    aid = client.post('/api/evaluations/left/appeals', json={'criterion_id': 'contact', 'comment': 'SYNTHETIC open dispute'}).json()['id']
    add('SYNTHETIC_FAILURE', state='failed')
    row = client.get('/api/conversations?checklist_id=1').json()[0]
    assert row['evaluation']['id'] == 'SYNTHETIC_FAILURE'
    assert row['evaluation']['total'] is None and row['critical_findings'] == []
    changed = synthetic_payload(); changed['data']['records'][0]['language'] = 'KZ'
    new_id = client.post('/api/import/json', json=changed).json()['conversation_ids'][0]
    latest = client.get('/api/conversations?checklist_id=1').json()[0]
    assert latest['id'] == new_id and latest['evaluation'] is None
    assert latest['pending_review_targets'][0]['appeal_id'] == aid
    assert latest['pending_review_targets'][0]['conversation_id'] == cid
    all_revisions = client.get('/api/conversations?checklist_id=1&latest_only=false').json()
    assert len(all_revisions) == 2
    assert next(row for row in all_revisions if row['id'] == cid)['pending_appeals'] == 1
    assert next(row for row in all_revisions if row['id'] == new_id)['pending_appeals'] == 0


def test_queue_preserves_dataset_namespace_when_source_ids_collide(saved):
    client, _, _, original_id, _ = saved
    payload = synthetic_payload()
    payload['data']['dataset_group_id'] = 'SECOND_SYNTHETIC_GROUP'
    new_id = client.post('/api/import/json', json=payload).json()['conversation_ids'][0]
    rows = client.get('/api/conversations?checklist_id=1').json()
    assert {row['id'] for row in rows} == {original_id, new_id}
    assert next(row for row in rows if row['id'] == new_id)['evaluation'] is None


def test_budget_status_uses_accounting_projections_and_reads_reservations_once(tmp_path):
    db = Database(tmp_path/'budget.sqlite3')
    service = Budget(db, Settings())
    statements, loaded = [], []
    def sql(conn, cursor, statement, parameters, context, many):
        statements.append(statement.lower())
    def track(row, context):
        loaded.append(row.id)
    event.listen(db.engine, 'before_cursor_execute', sql)
    event.listen(Evaluation, 'load', track)
    try:
        assert service.status()['ready'] is False
    finally:
        event.remove(db.engine, 'before_cursor_execute', sql)
        event.remove(Evaluation, 'load', track)
        db.engine.dispose()
    assert loaded == []
    evaluation_reads = [s for s in statements if 'from evaluations' in s]
    assert len(evaluation_reads) == 1
    assert all('evaluations.original' not in s and 'evaluations.effective' not in s for s in evaluation_reads)
    assert sum('from budget_reservations' in s for s in statements) == 1


def test_budget_status_is_a_consistent_snapshot_during_a_concurrent_commit(tmp_path):
    path = tmp_path/'snapshot.sqlite3'
    db, writer = Database(path), Database(path)
    service = Budget(db, Settings(budget_limit_usd=Decimal('100'), budget_overhead_usd=Decimal(0),
        input_rate=Decimal(1), output_rate=Decimal(1), rate_source='SYNTHETIC'))
    committed = False
    def concurrent_update(conn, cursor, statement, parameters, context, many):
        nonlocal committed
        if committed or 'from budget_state' not in statement.lower():
            return
        committed = True
        with writer.transaction() as session:
            session.get(BudgetState, 1).opening_usd = '10'
            session.add(BudgetReservation(kind='access_check', source_id='SYNTHETIC_PARALLEL', state='settled',
                reserved_usd='1', accounted_usd='1', rate={}, max_attempts=0, attempts=[]))
    event.listen(db.engine, 'after_cursor_execute', concurrent_update)
    try:
        assert service.status()['accounted_usd'] == '0'
        assert committed
        assert service.status()['accounted_usd'] == '11'
    finally:
        event.remove(db.engine, 'after_cursor_execute', concurrent_update)
        db.engine.dispose(); writer.engine.dispose()


@pytest.mark.parametrize('extra', [0, 1])
@pytest.mark.parametrize('declared_length', [None, '1'])
def test_actual_upload_bytes_are_bounded_before_import_even_without_honest_length(tmp_path, monkeypatch, extra, declared_length):
    from backend.app import main
    body = json.dumps(synthetic_payload()).encode('utf-8')
    monkeypatch.setattr(main, 'IMPORT_BYTE_LIMIT', len(body))
    client, calls, _ = client_and_calls(tmp_path, budget_limit_usd=Decimal(0))
    headers = {'Content-Type': 'application/json'}
    if declared_length is not None:
        headers['Content-Length'] = declared_length
    def chunks():
        yield body[:30]
        yield body[30:]
        if extra:
            yield b' '
    with client:
        response = client.post('/api/import/json', content=chunks(), headers=headers)
        assert response.status_code == (413 if extra else 200), response.text
        assert len(client.get('/api/conversations').json()) == (0 if extra else 1)
        assert calls == []


@pytest.mark.parametrize('length', ['-1', 'invalid'])
def test_invalid_declared_upload_length_has_a_clear_error(tmp_path, length):
    client, calls, _ = client_and_calls(tmp_path)
    with client:
        response = client.post('/api/import/json', content=b'{}', headers={'Content-Length': length})
        assert response.status_code == 400
        assert response.json()['detail'] == 'Invalid content length'
        assert client.get('/api/conversations').json() == [] and calls == []


class Stream(httpx.SyncByteStream):
    def __init__(self, chunks):
        self.chunks, self.reads, self.closed = chunks, 0, False

    def __iter__(self):
        for chunk in self.chunks:
            self.reads += 1
            yield chunk

    def close(self):
        self.closed = True


def mock_organizer(monkeypatch, stream, *, headers=None, status=200):
    original = httpx.Client
    transport = httpx.MockTransport(lambda request: httpx.Response(status, stream=stream, headers=headers or {}))
    monkeypatch.setattr(importer.httpx, 'Client', lambda **kwargs: original(transport=transport, **kwargs))
    return Settings(organizer_url='https://example.invalid/SYNTHETIC?sig=PRIVATE_TEST')


def test_organizer_stream_stops_at_the_decoded_limit_and_closes_response(monkeypatch):
    stream = Stream([b'x'*32768 for _ in range(100)])
    settings = mock_organizer(monkeypatch, stream, headers={'Content-Length': '1'})
    monkeypatch.setattr(importer, 'IMPORT_BYTE_LIMIT', 65536)
    with pytest.raises(ValueError, match='25 MB import safeguard'):
        fetch_organizer(settings, 'SYNTHETIC_TEST_ONLY')
    assert stream.reads <= 4 and stream.closed


def test_compressed_organizer_response_is_limited_after_decompression(monkeypatch):
    stream = Stream([gzip.compress(b'x'*131072)])
    settings = mock_organizer(monkeypatch, stream, headers={'Content-Encoding': 'gzip'})
    monkeypatch.setattr(importer, 'IMPORT_BYTE_LIMIT', 65536)
    with pytest.raises(ValueError, match='25 MB import safeguard'):
        fetch_organizer(settings, 'SYNTHETIC_TEST_ONLY')
    assert stream.closed


def test_small_streamed_organizer_json_preserves_envelope_validation(monkeypatch):
    body = json.dumps(synthetic_payload()).encode('utf-8')
    stream = Stream([body[:20], body[20:]])
    settings = mock_organizer(monkeypatch, stream)
    assert fetch_organizer(settings, 'SYNTHETIC_TEST_ONLY').data.total_records == 1
    assert stream.closed


def test_organizer_error_status_does_not_read_or_expose_response_body(monkeypatch):
    stream = Stream([b'PRIVATE SOURCE AND URL'])
    settings = mock_organizer(monkeypatch, stream, status=503)
    with pytest.raises(ValueError, match='Organizer HTTP 503') as error:
        fetch_organizer(settings, 'SYNTHETIC_TEST_ONLY')
    assert stream.reads == 0 and stream.closed
    assert 'PRIVATE' not in str(error.value) and 'example.invalid' not in str(error.value)


def test_organizer_stream_failure_closes_response_and_hides_network_details(monkeypatch):
    class Broken(Stream):
        def __iter__(self):
            yield b'{'
            raise httpx.ReadTimeout('PRIVATE SIGNED ENDPOINT AND SOURCE')
    stream = Broken([])
    settings = mock_organizer(monkeypatch, stream)
    with pytest.raises(ValueError, match='Organizer network/timeout failure') as error:
        fetch_organizer(settings, 'SYNTHETIC_TEST_ONLY')
    assert stream.closed and 'PRIVATE' not in str(error.value)


@pytest.mark.parametrize('mode', ['oversize', 'valid', 'disconnect', 'declared_oversize'])
def test_asgi_stream_boundary_stops_early_replays_exact_bytes_and_handles_disconnect(mode):
    async def scenario():
        sent, received, invoked = [], [], []
        if mode == 'disconnect':
            chunks = iter([{'type': 'http.request', 'body': b'12', 'more_body': True}, {'type': 'http.disconnect'}])
        else:
            chunks = iter([{'type': 'http.request', 'body': b'12', 'more_body': True},
                           {'type': 'http.request', 'body': b'345', 'more_body': mode == 'oversize'},
                           {'type': 'http.request', 'body': b'NEVER_READ', 'more_body': False}])
        async def receive():
            message = next(chunks); received.append(message); return message
        async def send(message):
            sent.append(message)
        async def app(scope, reader, sender):
            invoked.append(await reader())
            await sender({'type': 'http.response.start', 'status': 200, 'headers': []})
            await sender({'type': 'http.response.body', 'body': b'OK'})
        headers = [(b'content-length', b'999')] if mode == 'declared_oversize' else []
        await RequestBodyLimit(app, max_bytes=4 if mode == 'oversize' else 5)(
            {'type': 'http', 'method': 'POST', 'headers': headers}, receive, send)
        if mode == 'valid':
            assert invoked == [{'type': 'http.request', 'body': b'12345', 'more_body': False}]
            assert sent[0]['status'] == 200 and len(received) == 2
        elif mode == 'disconnect':
            assert invoked == sent == [] and len(received) == 2
        else:
            assert invoked == [] and sent[0]['status'] == 413
            assert len(received) == (0 if mode == 'declared_oversize' else 2)
    asyncio.run(scenario())
