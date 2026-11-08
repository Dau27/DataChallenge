"""Synthetic draft/scoring boundaries; no hosted inference or real-data writes."""
import pytest

from backend.app.domain import Checklist
from backend.app.services.checklists import preview_checklist
from backend.app.services.scoring import score
from backend.tests.conftest import full_assessment
from backend.tests.test_workflow import client_and_calls


@pytest.mark.parametrize('weight', ['1e1000000', '1e-10000000', '1e101', '1e-101'])
def test_unscorable_magnitudes_are_field_errors_and_cannot_save(tmp_path, checklist, weight):
    client, calls, _ = client_and_calls(tmp_path)
    with client:
        draft = checklist.model_dump(mode='json')
        draft['criteria'][0]['weight'] = weight
        before = client.get('/api/checklists').json()
        response = client.post('/api/checklists/1/preview', json=draft)
        assert response.status_code == 200 and response.json()['valid'] is False
        assert ['criteria', 0, 'weight'] in [issue['location'] for issue in response.json()['errors']]
        assert client.post('/api/checklists', json=draft).status_code == 422
        assert client.get('/api/checklists').json() == before
        assert not calls


@pytest.mark.parametrize('weight', ['0', '0.000001', '1e-100', '1e100', '20'])
def test_supported_relative_weights_score_without_exception_or_losing_zero(checklist, weight):
    draft = checklist.model_dump(mode='json')
    draft['criteria'][0]['weight'] = weight
    parsed = Checklist.model_validate(draft)
    assert preview_checklist(checklist.model_dump(mode='json'), draft)['valid']
    result = score(parsed, full_assessment(parsed))
    assert result['total'] == '100.00'
    assert result['criteria'][0]['weight'] == str(parsed.criteria[0].weight)


def test_all_weights_zero_still_withholds_total(checklist):
    draft = checklist.model_dump(mode='json')
    for criterion in draft['criteria']:
        if criterion['answer_type'] != 'flag': criterion['weight'] = '0'
    parsed = Checklist.model_validate(draft)
    result = score(parsed, full_assessment(parsed))
    assert result['total'] is None and result['reason'] == 'NO_APPLICABLE_SCORED_WEIGHT'
