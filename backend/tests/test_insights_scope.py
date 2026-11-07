from pathlib import Path

from fastapi import HTTPException
from pydantic import ValidationError
import pytest

from backend.app.db import ChecklistVersion, Conversation, Database, Evaluation
from backend.app.domain import content_hash
from backend.app.services.insights_common import SavedScope, load_scope
from backend.app.services.saved_results import SavedResultNotFound


def seeded(tmp_path, checklist):
    db = Database(tmp_path / 'synthetic-insights.sqlite3')
    with db.transaction() as session:
        session.add(ChecklistVersion(id=1, snapshot=checklist.model_dump(mode='json'), content_hash=content_hash(checklist)))
        session.add(ChecklistVersion(id=2, snapshot=checklist.model_dump(mode='json'), content_hash=content_hash(checklist)))
        session.add(Conversation(id='SOURCE', group_id='SYNTHETIC_TEST_ONLY', source_id='TEST-1', revision=1,
            content_hash='TEST_HASH', snapshot={'language': 'EN', 'channel': 'agent chat', 'transcript': [], 'audio_url': None}))
    return db


def test_scope_latest_failure_and_tie_break_are_not_replaced_with_old_success(tmp_path, checklist):
    db = seeded(tmp_path, checklist)
    with db.transaction() as session:
        for eid, version, state in [('A', 1, 'succeeded'), ('Z', 1, 'failed'), ('ZZ', 2, 'succeeded')]:
            session.add(Evaluation(id=eid, conversation_id='SOURCE', checklist_id=version, state=state,
                created_at='2026-11-07T00:00:00Z', updated_at='TEST_UPDATED', cache_key=eid))
    with db.read_snapshot() as session:
        result = load_scope(session, 1, ['SOURCE'])
    assert result['runs']['SOURCE']['id'] == 'Z'
    assert result['manifest'][0]['state'] == 'failed'
    assert 'snapshot' not in result['sources'][0]
    assert 'attempts' not in result['runs']['SOURCE'] and 'meta' not in result['runs']['SOURCE']
    assert result['sources'][0]['language'] == 'EN'


def test_scope_missing_versions_sources_and_empty_selection(tmp_path, checklist):
    db = seeded(tmp_path, checklist)
    with db.read_snapshot() as session:
        result = load_scope(session, 1, ['SOURCE'])
        assert result['manifest'][0]['evaluation_id'] is None
        assert result['manifest'][0]['state'] == 'not_evaluated'
        assert load_scope(session, 1, [])['sources'] == []
        with pytest.raises(SavedResultNotFound): load_scope(session, 99, [])
        with pytest.raises(SavedResultNotFound): load_scope(session, 1, ['MISSING'])


def test_scope_rejects_obsolete_revision_without_cross_dataset_collision(tmp_path, checklist):
    db = seeded(tmp_path, checklist)
    with db.transaction() as session:
        source = session.get(Conversation, 'SOURCE')
        session.add(Conversation(id='OTHER', group_id='OTHER_SYNTHETIC', source_id=source.source_id,
            revision=2, content_hash='OTHER_HASH', snapshot=source.snapshot))
    with db.read_snapshot() as session:
        assert load_scope(session, 1, ['SOURCE'])['sources'][0]['revision'] == 1
    with db.transaction() as session:
        source = session.get(Conversation, 'SOURCE')
        session.add(Conversation(id='NEW', group_id=source.group_id, source_id=source.source_id,
            revision=2, content_hash='NEW_HASH', snapshot=source.snapshot))
    with db.read_snapshot() as session:
        with pytest.raises(HTTPException) as error: load_scope(session, 1, ['SOURCE'])
        assert error.value.status_code == 409
        result = load_scope(session, 1, ['OTHER', 'NEW'])
        assert [row['id'] for row in result['sources']] == ['OTHER', 'NEW']


@pytest.mark.parametrize('ids', [[''], [' '], ['SOURCE', 'SOURCE'], ['x' * 201], ['x' + str(i) for i in range(201)], [1]])
def test_scope_rejects_unbounded_or_ambiguous_input(ids):
    with pytest.raises(ValidationError): SavedScope(checklist_id=1, conversation_ids=ids)
