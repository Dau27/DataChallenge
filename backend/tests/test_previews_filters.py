from copy import deepcopy
from decimal import Decimal
import json
import httpx
import pytest

from backend.app.domain import Checklist
from backend.tests.conftest import full_assessment
from backend.tests.test_workflow import client_and_calls, import_one, evaluate_one, response_for, synthetic_payload


@pytest.mark.parametrize('field', ['description', 'weight', 'answer_type', 'na_condition', 'scale', 'sections', 'remove', 'add', 'order'])
def test_preview_shows_changes_without_saving_or_evaluating(tmp_path, field):
    client, calls, _ = client_and_calls(tmp_path)
    with client:
        before = client.get('/api/checklists').json()
        draft = deepcopy(before[0]['snapshot'])
        if field == 'description': draft['criteria'][0]['description'] = 'A substantively changed definition'
        elif field == 'weight': draft['criteria'][0]['weight'] = '2.5'
        elif field == 'answer_type': draft['criteria'][0].update(answer_type='flag', weight=None)
        elif field == 'na_condition': draft['criteria'][1]['na_condition'] = 'A new exact condition'
        elif field == 'scale': draft['criteria'][3]['scale'][0]['value'] = '30'
        elif field == 'sections': draft['sections'][0]['title'] = 'Changed section title'
        elif field == 'remove': draft['criteria'].pop()
        elif field == 'add': draft['criteria'].append({**draft['criteria'][0], 'id': 'NEW_RULE', 'name': 'New rule'})
        elif field == 'order': draft['criteria'].reverse()
        response = client.post('/api/checklists/1/preview', json=draft)
        assert response.status_code == 200
        preview = response.json()
        assert preview['valid'] and preview['changes']
        assert client.get('/api/checklists').json() == before
        assert client.get('/api/evaluations').json() == [] and calls == []


@pytest.mark.parametrize('kind,path', [('weight', ['criteria', 0, 'weight']), ('na', ['criteria', 1, 'na_condition']),
    ('anchor', ['criteria', 3, 'scale', 0, 'value']), ('duplicate', ['criteria', 3, 'scale']),
    ('section', ['criteria', 0, 'section_id']), ('title', ['sections', 0, 'title'])])
def test_preview_returns_field_errors_and_backend_still_rejects_invalid_save(tmp_path, kind, path):
    client, calls, _ = client_and_calls(tmp_path)
    with client:
        draft = client.get('/api/checklists').json()[0]['snapshot']
        if kind == 'weight': draft['criteria'][0]['weight'] = '-1'
        if kind == 'na': draft['criteria'][1]['na_condition'] = ''
        if kind == 'anchor': draft['criteria'][3]['scale'][0]['value'] = '-1'
        if kind == 'duplicate': draft['criteria'][3]['scale'].append(deepcopy(draft['criteria'][3]['scale'][0]))
        if kind == 'section': draft['criteria'][0]['section_id'] = 'ABSENT_SECTION'
        if kind == 'title': draft['sections'][0]['title'] = ''
        preview = client.post('/api/checklists/1/preview', json=draft).json()
        assert not preview['valid']
        assert path in [e['location'] for e in preview['errors']]
        assert client.post('/api/checklists', json=draft).status_code == 422
        assert len(client.get('/api/checklists').json()) == 1 and calls == []


def test_pending_appeals_include_older_runs_and_revisions_but_not_other_checklists(tmp_path):
    client, calls, _ = client_and_calls(tmp_path)
    with client:
        cid = import_one(client)
        first = evaluate_one(client, cid)
        latest = evaluate_one(client, cid, reuse_cache=False)
        aid = client.post(f"/api/evaluations/{first['id']}/appeals", json={'criterion_id': 'contact', 'comment': 'SYNTHETIC dispute'}).json()['id']
        row = client.get('/api/conversations?checklist_id=1').json()[0]
        assert row['pending_appeals'] == 1 and row['evaluation']['id'] == latest['id']
        assert row['pending_review_targets'][0]['evaluation_id'] == first['id']
        assert client.get('/api/conversations?checklist_id=99').json()[0]['pending_appeals'] == 0
        changed = synthetic_payload(); changed['data']['records'][0]['language'] = 'RU'
        new_id = client.post('/api/import/json', json=changed).json()['conversation_ids'][0]
        row = client.get('/api/conversations?checklist_id=1').json()[0]
        assert row['id'] == new_id and row['pending_appeals'] == 1
        assert row['pending_review_targets'][0]['conversation_id'] == cid
        count = len(calls)
        client.post('/api/appeals/'+aid+'/decision', json={'action': 'confirm', 'judgment': None, 'rationale': 'SYNTHETIC reviewer', 'expected_updated_at': first['updated_at']})
        assert client.get('/api/conversations?checklist_id=1').json()[0]['pending_appeals'] == 0
        assert len(calls) == count


def test_critical_filter_data_uses_effective_dynamic_flags_without_score_penalty(tmp_path):
    def handler(payload):
        rubric = Checklist.model_validate(json.loads(payload['input'])['saved_checklist'])
        assessment = full_assessment(rubric, message_id='m0002').model_dump(mode='json')
        assessment['results']['critical_errors']['value'] = True
        return httpx.Response(200, json=response_for(assessment))
    client, calls, _ = client_and_calls(tmp_path, handler)
    with client:
        result = evaluate_one(client, import_one(client))
        row = client.get('/api/conversations?checklist_id=1').json()[0]
        assert row['critical_findings'][0]['criterion_id'] == 'critical_errors'
        assert row['evaluation']['total'] == result['original_score']['total'] == '100.00'
        appeal = client.post(f"/api/evaluations/{result['id']}/appeals", json={'criterion_id': 'critical_errors', 'comment': 'SYNTHETIC review'}).json()['id']
        judgment = deepcopy(result['effective']['results']['critical_errors']); judgment['value'] = False
        assert client.post('/api/appeals/'+appeal+'/decision', json={'action': 'replace', 'judgment': judgment,
            'rationale': 'SYNTHETIC cleared finding', 'expected_updated_at': result['updated_at']}).status_code == 201
        row = client.get('/api/conversations?checklist_id=1').json()[0]
        assert row['critical_findings'] == [] and row['pending_appeals'] == 0
        assert row['evaluation']['total'] == '100.00' and len(calls) == 1
