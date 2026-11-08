from copy import deepcopy
import json

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.app.api_priority import router
from backend.app.db import Appeal, ChecklistVersion, Conversation, Database, Evaluation
from backend.app.services.review_priority import review_priority


def make_db(tmp_path, flags=True):
    db = Database(tmp_path / 'synthetic-priority.sqlite3')
    criteria = [{"id": "contact", "name": "Contact", "answer_type": "binary"}]
    if flags:
        criteria.append({"id": "critical", "name": "Critical", "answer_type": "flag"})
    with db.transaction() as session:
        session.add(ChecklistVersion(id=1, content_hash='SYNTHETIC_RULES', snapshot={"criteria": criteria}))
        session.add(ChecklistVersion(id=2, content_hash='SYNTHETIC_OTHER_RULES', snapshot={"criteria": criteria}))
    return db


def source(session, id, group='DEV', source_id=None, revision=1):
    session.add(Conversation(id=id, group_id=group, source_id=source_id or id, revision=revision, content_hash='HASH_' + id,
                             snapshot={"language": "EN", "channel": "agent chat"}, created_at='2026-01-01T00:00:00+00:00'))


def run(session, id, conversation_id, state='succeeded', critical=False, unresolved=False, date='2026-01-02', checklist_id=1):
    results = {"contact": {"disposition": 'needs_review' if unresolved else 'assessed', "value": None if unresolved else True},
               "critical": {"disposition": 'assessed', "value": critical}}
    assessment = {"results": results} if state == 'succeeded' else None
    session.add(Evaluation(id=id, conversation_id=conversation_id, checklist_id=checklist_id, cache_key='SYNTHETIC_' + id,
                           state=state, completeness='needs_review' if unresolved else 'complete',
                           original=deepcopy(assessment), effective=assessment, created_at=date, updated_at=date))


def state(db):
    with db.sessions() as session:
        return [[{c.name: getattr(row, c.name) for c in model.__table__.columns} for row in session.scalars(select(model))]
                for model in (Conversation, Evaluation, ChecklistVersion, Appeal)]


def test_priority_preserves_latest_failure_and_exact_old_appeal_targets(tmp_path):
    db = make_db(tmp_path)
    with db.transaction() as session:
        source(session, 'OLD', source_id='same', revision=1)
        source(session, 'LATEST', source_id='same', revision=2)
        source(session, 'OTHER', group='SYNTHETIC', source_id='same')
        source(session, 'FLAGGED'); source(session, 'EMPTY')
        session.flush()
        run(session, 'OLD_RUN', 'OLD')
        run(session, 'PRIOR_SUCCESS', 'LATEST')
        run(session, 'LATEST_FAILURE', 'LATEST', state='failed', date='2026-01-03')
        run(session, 'FLAGGED_RUN', 'FLAGGED', critical=True, unresolved=True)
        run(session, 'OTHER_GROUP_RUN', 'OTHER')
        run(session, 'OTHER_CHECKLIST_RUN', 'LATEST', checklist_id=2)
        session.flush()
        for id, eid in [('EXACT_OLD_APPEAL', 'OLD_RUN'), ('OTHER_GROUP_APPEAL', 'OTHER_GROUP_RUN'), ('OTHER_CHECKLIST_APPEAL', 'OTHER_CHECKLIST_RUN')]:
            session.add(Appeal(id=id, evaluation_id=eid, criterion_id='contact', comment='SYNTHETIC', created_at='2025-12-31'))
    before = state(db)
    with db.read_snapshot() as session:
        packet = review_priority(session, 1, ['LATEST', 'FLAGGED', 'EMPTY'])
    assert state(db) == before
    latest, flagged, empty = packet['items']
    assert latest['evaluation_id'] == 'LATEST_FAILURE' and latest['state'] == 'failed'
    appeal = next(r for r in latest['reasons'] if r['code'] == 'open_appeal')
    assert appeal['targets'] == [{'appeal_id': 'EXACT_OLD_APPEAL', 'conversation_id': 'OLD', 'evaluation_id': 'OLD_RUN', 'criterion_id': 'contact', 'criterion_name': 'Contact'}]
    assert latest['oldest_reason_at'] == '2025-12-31'
    assert latest['flag_counts'] == {'true': 0, 'false': 0, 'unknown': 1}
    assert flagged['flag_counts'] == {'true': 1, 'false': 0, 'unknown': 0}
    assert empty['flag_counts'] == {'true': 0, 'false': 0, 'unknown': 1}
    assert packet['counts'] == {'open_appeal': 1, 'needs_review': 1, 'critical_true': 1, 'critical_unknown': 2,
                                'failed': 1, 'interrupted': 0, 'not_evaluated': 1, 'in_progress': 0}
    assert 'SYNTHETIC' not in json.dumps(packet)  # No comments, cache metadata or unrelated dataset escaped.


def test_latest_ties_are_deterministic_and_unknown_never_becomes_false(tmp_path):
    db = make_db(tmp_path)
    with db.transaction() as session:
        source(session, 'ONE'); source(session, 'TWO'); source(session, 'THREE')
        session.flush()
        run(session, 'A_TIE', 'ONE', critical=True)
        run(session, 'Z_TIE', 'ONE', state='interrupted')
        run(session, 'SECOND', 'TWO', critical=None)
        run(session, 'THIRD', 'THREE', critical=False)
    with db.read_snapshot() as session:
        packet = review_priority(session, 1, ['THREE', 'ONE', 'TWO'])
    assert [r['conversation_id'] for r in packet['items']] == ['THREE', 'ONE', 'TWO']
    assert packet['items'][0]['flag_counts']['false'] == 1
    assert packet['items'][1]['evaluation_id'] == 'Z_TIE'
    assert packet['counts']['critical_unknown'] == 2 and packet['counts']['critical_true'] == 0


def test_no_flags_and_queued_work_are_reported_without_invented_critical_status(tmp_path):
    db = make_db(tmp_path, flags=False)
    with db.transaction() as session:
        source(session, 'QUEUED'); session.flush(); run(session, 'Q_RUN', 'QUEUED', state='queued')
    with db.read_snapshot() as session:
        packet = review_priority(session, 1, ['QUEUED'])
    assert packet['counts']['in_progress'] == 1
    assert packet['counts']['critical_unknown'] == 0
    assert packet['items'][0]['configured_flags'] == 0


def test_endpoint_is_bounded_read_only_and_no_store(tmp_path):
    db = make_db(tmp_path)
    app = FastAPI(); app.state.db = db; app.include_router(router)
    before = state(db)
    with TestClient(app) as client:
        response = client.post('/api/insights/review-priority', json={'checklist_id': 1, 'conversation_ids': []})
        assert response.status_code == 200 and response.headers['cache-control'] == 'no-store'
        assert response.json()['items'] == []
        for ids in [['DUP', 'DUP'], [' '], [str(i) for i in range(201)]]:
            assert client.post('/api/insights/review-priority', json={'checklist_id': 1, 'conversation_ids': ids}).status_code == 422
    assert state(db) == before


def test_null_numeric_and_na_flag_answers_remain_unknown(tmp_path):
    db = make_db(tmp_path)
    with db.transaction() as session:
        for id in ('NULL', 'NUMERIC', 'NA'):
            source(session, id)
        session.flush()
        for id in ('NULL', 'NUMERIC', 'NA'):
            run(session, id + '_RUN', id)
        session.flush()
        for id, judgment in [('NULL', {'disposition': 'needs_review', 'value': None}),
                             ('NUMERIC', {'disposition': 'assessed', 'value': 1}),
                             ('NA', {'disposition': 'not_applicable', 'value': False})]:
            saved = session.get(Evaluation, id + '_RUN')
            updated = deepcopy(saved.effective); updated['results']['critical'] = judgment; saved.effective = updated
    with db.read_snapshot() as session:
        packet = review_priority(session, 1, ['NULL', 'NUMERIC', 'NA'])
    assert packet['counts']['critical_true'] == 0 and packet['counts']['critical_unknown'] == 3
    assert packet['counts']['needs_review'] == 1
    assert all(item['flag_counts'] == {'true': 0, 'false': 0, 'unknown': 1} for item in packet['items'])


def test_missing_or_malformed_saved_judgments_have_explicit_unavailable_reason(tmp_path):
    db = make_db(tmp_path)
    with db.transaction() as session:
        source(session, 'BROKEN'); session.flush(); run(session, 'BROKEN_RUN', 'BROKEN'); session.flush()
        session.get(Evaluation, 'BROKEN_RUN').effective = ['SYNTHETIC malformed historical payload']
    with db.read_snapshot() as session:
        packet = review_priority(session, 1, ['BROKEN'])
    assert packet['counts']['needs_review'] == 1
    unresolved = next(r for r in packet['items'][0]['reasons'] if r['code'] == 'needs_review')
    assert {target['criterion_id'] for target in unresolved['targets']} == {'contact', 'critical'}
    assert packet['items'][0]['flag_counts']['unknown'] == 1
