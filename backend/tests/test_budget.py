from decimal import Decimal
import json
from pathlib import Path
import runpy
import sys
import httpx

from backend.app.config import Settings
from scripts.run_dev import four_attempt_bound
from scripts.run_dev import historical_attempt_bound
from scripts.run_dev import affordable_batch


def test_budget_reservation_covers_all_four_attempts(checklist, tmp_path):
    settings = Settings(database_path=tmp_path / "test.sqlite3", input_rate=Decimal("0.75"), output_rate=Decimal("4.50"), max_output_tokens=6000)
    snapshot = {"transcript": [{"id": "m0001", "speaker": "client", "timestamp": "00:00", "text": "SYNTHETIC budget test"}]}
    bound = four_attempt_bound(settings, snapshot, checklist)
    # Even ignoring all input, reserve four full output limits, including possible repairs/retries.
    assert bound > 4 * Decimal(6000) * Decimal("4.50") / Decimal(1_000_000)
    larger = {"transcript": [{"id": "m0001", "speaker": "client", "timestamp": "00:00", "text": "SYNTHETIC " * 1000}]}
    assert four_attempt_bound(settings, larger, checklist) > bound


def test_historical_failures_reserve_sent_attempts_at_original_model_rates(checklist, tmp_path):
    current = Settings(database_path=tmp_path / "test.sqlite3", input_rate=Decimal("0.25"), output_rate=Decimal("2.00"), max_output_tokens=6000)
    result = {"metadata": {"rate": {"input_usd_per_million": "0.75", "output_usd_per_million": "4.50"}, "generation": {"max_output_tokens": 6000}},
              "checklist": {"snapshot": checklist.model_dump(mode="json")}, "attempts": [
                  {"input_token_upper_bound": 10000, "max_output_tokens": 6000},
                  {"input_token_upper_bound": 10000, "max_output_tokens": 6000}]}
    assert historical_attempt_bound(current, result, {}) == Decimal("0.069")


def test_concurrent_batch_reserves_every_inflight_job_before_start():
    rows = [{"id": "a"}, {"id": "b"}, {"id": "c"}]
    bounds = {"a": Decimal("0.20"), "b": Decimal("0.30"), "c": Decimal("0.10")}
    assert affordable_batch(rows, bounds, Decimal("0.50")) == rows[:2]
    assert affordable_batch(rows, bounds, Decimal("0.49")) == rows[:1]
    assert affordable_batch(rows, bounds, Decimal("0.19")) == []


def test_cli_reports_every_item_once_when_enqueue_budget_changes_after_preview(monkeypatch, tmp_path, checklist):
    settings = Settings(api_key='TEST_ONLY', model='TEST_MODEL', input_rate=Decimal('.4'), output_rate=Decimal('1.6'), rate_source='TEST RATE')
    monkeypatch.setattr(Settings, 'from_env', classmethod(lambda cls: settings))
    status = {'accounted_usd': '0', 'reserved_usd': '0', 'overhead_usd': '.1', 'available_usd': '3.9'}
    requests = []
    def handler(request):
        path = request.url.path; requests.append(path)
        if path == '/api/access': body = {'provider_configured': True}
        elif path == '/api/checklists': body = [{'id': 1, 'snapshot': checklist.model_dump(mode='json')}]
        elif path == '/api/conversations': body = [{'id': key, 'source_id': 'SYNTHETIC_'+key, 'group_id': 'DEV', 'language': 'EN', 'channel': 'agent chat', 'evaluation': None} for key in ['A', 'B']]
        elif path == '/api/evaluations/preview': body = {'affordable': True, 'required_reservation_usd': '.2', 'budget': status}
        elif path == '/api/evaluations': return httpx.Response(409, json={'code': 'BUDGET_BLOCKED', 'detail': 'Another request reserved the remaining funds'})
        elif path == '/api/budget': body = status
        else: raise AssertionError('Unexpected CLI endpoint')
        return httpx.Response(200, json=body)
    native_client = httpx.Client
    monkeypatch.setattr(httpx, 'Client', lambda *a, **kw: native_client(*a, **kw, transport=httpx.MockTransport(handler)))
    report = tmp_path/'cli.json'; write = Path.write_text
    def private_write(path, data, *args, **kwargs):
        assert path.name == 'dev_run.json'
        return write(report, data, *args, **kwargs)
    monkeypatch.setattr(Path, 'write_text', private_write)
    monkeypatch.setattr(sys, 'argv', ['run_dev.py'])
    runpy.run_path(str(Path(__file__).resolve().parents[2]/'scripts/run_dev.py'), run_name='__main__')
    result = json.loads(report.read_text(encoding='utf-8'))
    assert result['stopped_for_budget']
    assert len(result['records']) == 2 and len({r['source_id'] for r in result['records']}) == 2
    assert result['states'] == {'not_started_budget_guard': 2}
    assert requests.count('/api/evaluations') == 1
