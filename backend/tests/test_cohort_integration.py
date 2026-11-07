"""Acceptance through the actual app/router/export mounting; synthetic saved runs."""
from backend.tests.test_saved_inspection import saved, db_rows


def test_mounted_cohort_routes_and_export_share_saved_identity_without_writes(saved):
    client, db, _, source_id, _ = saved
    before = db_rows(db)
    options = client.get('/api/insights/cohorts/options')
    assert options.status_code == 200
    assert options.headers['cache-control'] == 'no-store'
    group = options.json()['datasets'][0]['dataset_group_id']
    response = client.post('/api/insights/cohorts/compare', json={
        'dataset_group_id': group, 'left': {'checklist_id': 1}, 'right': {'checklist_id': 1}, 'basis': 'effective', 'limit': 200})
    assert response.status_code == 200, response.text
    assert response.headers['cache-control'] == 'no-store'
    pair = response.json()['pairs'][0]
    assert pair['source']['conversation_id'] == source_id
    for side in ('left', 'right'):
        run_id = pair[side]['evaluation_id']
        detail = client.get('/api/evaluations/' + run_id).json()
        packet = client.get('/api/evaluations/' + run_id + '/export', params={'format':'json'}).json()
        assert detail['id'] == run_id == packet['evaluation']['id']
        assert packet['manifest']['runs'][0]['evaluation_id'] == run_id
        assert packet['source']['id'] == source_id
        assert detail['updated_at'] == pair[side]['updated_at'] == packet['evaluation']['updated_at']
        assert detail['original_score'] == packet['evaluation']['original_score']
        assert detail['effective_score'] == packet['evaluation']['effective_score']
    assert db_rows(db) == before


def test_mounted_cohort_validation_and_origin_protection_remain_enforced(saved):
    client, db, _, _, _ = saved
    before = db_rows(db)
    body = {'dataset_group_id':'SYNTHETIC_TEST_ONLY','left':{'checklist_id':1},'right':{'checklist_id':1},'limit':201}
    assert client.post('/api/insights/cohorts/compare', json=body).status_code == 422
    body['limit'] = 200
    assert client.post('/api/insights/cohorts/compare', json=body, headers={'Origin':'https://example.invalid'}).status_code == 403
    assert client.post('/api/insights/cohorts/compare', json=body, headers={'Origin':'http://127.0.0.1:5173'}).status_code == 200
    assert db_rows(db) == before
