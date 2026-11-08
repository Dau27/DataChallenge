"""Saved provenance is optional; malformed historical values must not block review."""
from copy import deepcopy

import pytest

from backend.app.db import Evaluation
from backend.tests.test_saved_inspection import saved, db_rows


@pytest.mark.parametrize('generation,expected', [
    ({'max_output_tokens': 10**400, 'temperature': 0}, {'temperature': 0}),
    ({'temperature': {'unexpected': 'SYNTHETIC'}, 'top_p': True}, {}),
    ({'reasoning': {'effort': []}}, {}),
    (['SYNTHETIC malformed generation'], {}),
    ({'temperature': None, 'max_output_tokens': 6000, 'top_p': 0.9,
      'reasoning': {'effort': 'low'}},
     {'temperature': None, 'max_output_tokens': 6000, 'top_p': 0.9,
      'reasoning': {'effort': 'low'}}),
])
def test_malformed_provenance_does_not_break_exact_saved_pair_or_change_rows(saved, generation, expected):
    client, db, _, _, _ = saved
    with db.transaction() as session:
        row = session.get(Evaluation, 'left')
        row.meta = {**deepcopy(row.meta), 'generation': generation}
    before = db_rows(db)
    response = client.get('/api/evaluations/compare', params={'left_id': 'left', 'right_id': 'right'})
    assert response.status_code == 200
    packet = response.json()
    assert packet['left']['metadata']['generation'] == expected
    assert packet['left']['id'] == 'left' and packet['right']['id'] == 'right'
    assert packet['left']['score']['total'] == packet['right']['score']['total']
    assert db_rows(db) == before
