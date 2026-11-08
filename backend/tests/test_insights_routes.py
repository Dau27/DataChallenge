import json
import sqlite3

from fastapi.testclient import TestClient

from backend.app.config import Settings
from backend.app.main import create_app


class ForbiddenProvider:
    def request(self, *args, **kwargs):
        raise AssertionError('No provider invocation is allowed by saved insights')


def snapshot(path):
    with sqlite3.connect(path) as db:
        tables = [row[0] for row in db.execute("select name from sqlite_master where type='table' order by name")]
        return {table: sorted(json.dumps(list(row), default=str) for row in db.execute('select * from "' + table + '"')) for table in tables}


def test_main_mounts_read_only_tools_without_jobs_or_budget_mutations(tmp_path):
    path = tmp_path / 'synthetic-main.sqlite3'
    app = create_app(Settings(database_path=path, budget_baseline_path=tmp_path / 'absent.json'), ForbiddenProvider())
    with TestClient(app) as client:
        before = snapshot(path)
        for route in ('breakdown', 'review-priority'):
            response = client.post('/api/insights/' + route, json={'checklist_id': 1, 'conversation_ids': []})
            assert response.status_code == 200
            assert response.headers['cache-control'] == 'no-store'
            assert response.json()['manifest'] == []
            invalid = client.post('/api/insights/' + route, json={'checklist_id': 1, 'conversation_ids': ['MISSING']})
            assert invalid.status_code == 404
            assert client.post('/api/insights/' + route, json={'checklist_id': 1, 'conversation_ids': ['A', 'A']}).status_code == 422
        options = client.get('/api/insights/weight-preview/runs?checklist_id=1')
        assert options.status_code == 200 and options.json()['total'] == 0
        assert options.headers['cache-control'] == 'no-store'
        draft = client.get('/api/checklists').json()[0]['snapshot']
        assert client.post('/api/insights/weight-preview', json={'checklist_id': 1, 'evaluation_id': 'MISSING', 'draft': draft}).status_code == 404
        assert snapshot(path) == before
