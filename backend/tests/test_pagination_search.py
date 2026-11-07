"""Synthetic cursor/index parity and migration tests; no hosted provider calls."""
from copy import deepcopy
import json
import random
from pathlib import Path

import pytest
from sqlalchemy import delete, event, func, select, text, update

from backend.app.db import Conversation, Database, Evaluation, TranscriptIndexState, TranscriptMessage
from backend.app.domain import content_hash
from backend.app.services.search import search_messages
from backend.app.services.transcript_index import INDEX_VERSION, ensure_index
from backend.tests.test_saved_inspection import saved, db_rows
from backend.tests.test_workflow import synthetic_payload


def test_cursor_pages_have_stable_ties_both_directions_and_ignore_newer_inserts(saved):
    client, db, _, cid, add = saved
    for i in range(63):
        add(f'RUN_{i:03}')
    with db.transaction() as session:
        session.execute(update(Evaluation).values(created_at='2026-01-01T00:00:00+00:00'))
    expected = client.get('/api/evaluations').json()
    first = client.get('/api/evaluations/page', params={'conversation_id': cid, 'limit': 10}).json()
    assert first['items'] == expected[:10] and first['previous_cursor'] is None
    assert first['start'] == 1 and first['end'] == 10 and first['total'] == 65
    add('NEWER_AFTER_PAGING_STARTED')
    combined, page = list(first['items']), first
    while page['next_cursor']:
        previous_page = page
        page = client.get('/api/evaluations/page', params={'conversation_id': cid, 'limit': 10, 'cursor': page['next_cursor']}).json()
        assert page['total'] == 65
        backward = client.get('/api/evaluations/page', params={'conversation_id': cid, 'limit': 10, 'cursor': page['previous_cursor']}).json()
        assert backward['items'] == previous_page['items']
        combined.extend(page['items'])
    assert combined == expected and len({row['id'] for row in combined}) == 65
    latest = client.get('/api/evaluations/page', params={'conversation_id': cid, 'limit': 10}).json()
    assert latest['items'][0]['id'] == 'NEWER_AFTER_PAGING_STARTED' and latest['total'] == 66


def test_bounded_detail_keeps_legacy_contract_and_all_scores(saved):
    client, db, _, cid, add = saved
    for i in range(40):
        add(f'HISTORY_{i}')
    before = db_rows(db)
    full = client.get('/api/conversations/' + cid).json()
    bounded = client.get('/api/conversations/' + cid, params={'history_limit': 25}).json()
    assert len(full['evaluations']) == 42 and 'history_page' not in full
    assert bounded['evaluations'] == full['evaluations'][:25]
    assert bounded['snapshot'] == full['snapshot'] and bounded['history_page']['total'] == 42
    second = client.get('/api/conversations/' + cid, params={'history_limit': 25, 'history_cursor': bounded['history_page']['next_cursor']}).json()
    assert second['evaluations'] == full['evaluations'][25:]
    assert db_rows(db) == before


@pytest.mark.parametrize('params', [{'limit': 0}, {'limit': 101}, {'cursor': 'not-a-valid-cursor'}, {'cursor': 'x'*2049}])
def test_bad_pagination_input_is_rejected(saved, params):
    client, _, _, cid, _ = saved
    assert client.get('/api/evaluations/page', params={'conversation_id': cid, **params}).status_code == 422


def test_cursor_is_bound_to_source_and_global_filter(saved):
    client, _, _, cid, _ = saved
    page = client.get('/api/evaluations/page', params={'conversation_id': cid, 'limit': 1}).json()
    assert client.get('/api/evaluations/page', params={'cursor': page['next_cursor']}).status_code == 422
    payload = synthetic_payload(source_id='OTHER_SOURCE')
    other = client.post('/api/import/json', json=payload).json()['conversation_ids'][0]
    assert client.get('/api/evaluations/page', params={'conversation_id': other, 'cursor': page['next_cursor']}).status_code == 422
    assert client.get('/api/evaluations/page', params={'conversation_id': 'ABSENT'}).status_code == 404
    assert client.get('/api/conversations/' + cid, params={'history_cursor': page['next_cursor']}).status_code == 422
    empty = client.get('/api/evaluations/page', params={'conversation_id': other}).json()
    assert empty['items'] == [] and empty['total'] == 0 and empty['next_cursor'] is None


def import_texts(client, texts, source_id='UNICODE_INDEX'):
    payload = synthetic_payload(source_id=source_id)
    payload['data']['records'][0]['transcript'] = [{'timestamp': f'{i//60:02}:{i%60:02}',
        'speaker': ['operator', 'client', 'bot', 'system'][i % 4], 'text': value} for i, value in enumerate(texts)]
    cid = client.post('/api/import/json', json=payload).json()['conversation_ids'][0]
    return cid, client.get('/api/conversations/' + cid).json()['snapshot']['transcript']


def test_index_preserves_literal_unicode_counts_highlights_speakers_and_pages(saved):
    client, db, _, _, _ = saved
    texts = ['SYNTHETIC Здравствуйте! Қазақша ӘҒҚҢӨҰҮҺІ.', 'Straße STRASSE café e\u0301lan İSTANBUL Σίσυφος ᎠᎡ',
             '100% _tag a"b \\path [AND] OR NOT NEAR + - ***', '👩‍💻 🎉🙂🙂🙂 x\x00after-null-needle',
             '\u0001control\nline\rreturn\tTAB', '""" %%% ___ () []', 'Й й Ё ё ҚАЗАҚША', 'unrelated']
    cid, messages = import_texts(client, texts)
    queries = ['здрав', 'қазақ', 'ӘҒҚ', 'STRASSE', 'café', 'e\u0301lan', 'İST', 'ίσυ', 'ᎠᎡ', '100%', '_tag', 'a"b',
        '\\path', '[AND]', 'OR', 'NOT', 'NEAR', '+', '-', '*', '👩‍💻', '🙂🙂🙂', 'after-null', '\x00', 'x\x00after',
        '\u0001con', '\nline', '\tTAB', '"""', '%%%', '___', 'й', 'Ё', ' ', 'ABSENT', 'қ', 'а']
    before = db_rows(db)
    for query in queries:
        for speaker in ('all', 'operator', 'client', 'bot', 'system'):
            expected, total = search_messages(messages, query, speaker)
            rows = client.get('/api/conversations', params={'q': query, 'speaker': speaker}).json()
            hit = next((row for row in rows if row['id'] == cid), None)
            if not query.strip() and speaker == 'all':
                assert hit is not None
            else:
                assert bool(hit) == bool(total), (query, speaker)
            if hit:
                assert hit['search_total_matches'] == total and hit['search_matches'] == expected
            page = client.get(f'/api/conversations/{cid}/matches', params={'q': query, 'speaker': speaker, 'limit': 2, 'offset': 1}).json()
            expected_page, expected_count = search_messages(messages, query, speaker, 2, 1)
            assert page['matches'] == expected_page and page['total_matches'] == expected_count, (query, speaker)
    assert db_rows(db) == before


def test_index_matches_random_literal_substrings_without_loading_unmatched_sources(saved):
    client, db, _, _, _ = saved
    randomizer = random.Random(74)
    alphabet = 'abc АБВ әғқңөұүһі ÉßİΣ🙂 %_"\n'
    texts = [''.join(randomizer.choice(alphabet) for _ in range(70)) for _ in range(35)]
    cid, messages = import_texts(client, texts, 'RANDOM_UNICODE')
    for _ in range(50):
        value = randomizer.choice(texts); start = randomizer.randrange(len(value)-8)
        query = value[start:start+randomizer.randint(1,8)]
        expected, total = search_messages(messages, query)
        hit = next((row for row in client.get('/api/conversations', params={'q': query}).json() if row['id'] == cid), None)
        assert bool(hit) == bool(total) if query.strip() else hit is not None
        if hit:
            assert hit['search_matches'] == expected
    unique, _ = import_texts(client, ['SYNTHETIC absolutely-unique-index-needle'], 'ONLY_MATCH')
    loaded, statements = [], []
    def track(row, context): loaded.append(row.id)
    def sql(conn, cursor, statement, params, context, many): statements.append(statement)
    event.listen(Conversation, 'load', track); event.listen(db.engine, 'before_cursor_execute', sql)
    try:
        rows = client.get('/api/conversations', params={'q': 'absolutely-unique-index-needle'}).json()
    finally:
        event.remove(Conversation, 'load', track); event.remove(db.engine, 'before_cursor_execute', sql)
    assert [row['id'] for row in rows] == [unique] and loaded == [unique]
    assert any('transcript_fts MATCH' in statement for statement in statements)


@pytest.mark.parametrize('damage', ['missing_state', 'old_version', 'no_fts'])
def test_index_fallback_and_restart_rebuild_keep_all_matches(saved, damage):
    client, db, _, _, _ = saved
    cid, _ = import_texts(client, ['SYNTHETIC қалпына-келтіру needle'], 'RECOVERY')
    with db.transaction() as session:
        if damage == 'missing_state': session.execute(delete(TranscriptIndexState).where(TranscriptIndexState.conversation_id == cid))
        if damage == 'old_version': session.get(TranscriptIndexState, cid).version = 'OLD'
        if damage == 'no_fts': session.execute(text('DROP TABLE transcript_fts'))
    assert any(row['id'] == cid for row in client.get('/api/conversations', params={'q': 'қалпына'}).json())
    assert client.get(f'/api/conversations/{cid}/matches', params={'q': 'needle'}).json()['total_matches'] == 1
    ensure_index(db.engine)
    assert any(row['id'] == cid for row in client.get('/api/conversations', params={'q': 'қалпына'}).json())
    with db.sessions() as session:
        assert session.get(TranscriptIndexState, cid).version == INDEX_VERSION


def test_source_and_index_updates_are_atomic_and_reimports_are_idempotent(saved):
    client, db, _, _, _ = saved
    before = db_rows(db)
    with pytest.raises(RuntimeError):
        with db.transaction() as session:
            session.add(Conversation(group_id='SYNTHETIC', source_id='ROLLBACK', revision=1, content_hash='SYNTHETIC',
                snapshot={'transcript': [{'id':'m0001','speaker':'operator','text':'rollback-unique-needle'}]}))
            session.flush()
            raise RuntimeError('SYNTHETIC abort')
    assert db_rows(db) == before
    cid, messages = import_texts(client, ['old-revision-index-needle'], 'REVISION')
    payload = synthetic_payload(source_id='REVISION'); payload['data']['records'][0]['transcript'] = [
        {'timestamp':'00:00', 'speaker':'operator', 'text':'new-revision-index-needle'}]
    new_id = client.post('/api/import/json', json=payload).json()['conversation_ids'][0]
    before_reimport = db_rows(db)
    assert client.post('/api/import/json', json=payload).json()['unchanged'] == 1
    assert db_rows(db) == before_reimport
    assert client.get('/api/conversations', params={'q':'old-revision-index-needle'}).json() == []
    assert client.get('/api/conversations', params={'q':'old-revision-index-needle','latest_only':False}).json()[0]['id'] == cid
    assert client.get('/api/conversations', params={'q':'new-revision-index-needle'}).json()[0]['id'] == new_id


def test_legacy_database_backfill_adds_only_derived_rows_and_history_index(saved):
    client, db, _, _, _ = saved
    original_names = {'conversation_revisions','evaluations','checklist_versions','appeals','review_decisions',
                      'provider_access_checks','budget_state','budget_reservations'}
    before = {key: value for key, value in db_rows(db).items() if key in original_names}
    with db.transaction() as session:
        for sql in ['DROP TABLE transcript_fts', 'DROP TABLE transcript_index_state', 'DROP TABLE transcript_messages',
                    'DROP INDEX ix_evaluation_source_history']:
            session.execute(text(sql))
    restarted = Database(Path(db.engine.url.database))
    try:
        after = {key: value for key, value in db_rows(restarted).items() if key in original_names}
        assert after == before
        with restarted.sessions() as session:
            assert session.scalar(select(func.count()).select_from(TranscriptMessage)) == 2
            plan = session.execute(text("EXPLAIN QUERY PLAN SELECT id FROM evaluations WHERE conversation_id='SYNTHETIC' ORDER BY created_at DESC,id DESC LIMIT 25")).all()
            assert any('ix_evaluation_source_history' in str(row) for row in plan)
    finally:
        restarted.engine.dispose()


def test_source_update_and_delete_keep_the_derived_index_synchronized(saved):
    client, db, _, _, _ = saved
    cid, _ = import_texts(client, ['SYNTHETIC old-sync-needle'], 'SYNC')
    with db.transaction() as session:
        source = session.get(Conversation, cid)
        snapshot = deepcopy(source.snapshot); snapshot['transcript'][0]['text'] = 'SYNTHETIC new-sync-needle'
        source.snapshot, source.content_hash = snapshot, content_hash(snapshot)
    assert client.get('/api/conversations', params={'q':'old-sync-needle'}).json() == []
    assert client.get('/api/conversations', params={'q':'new-sync-needle'}).json()[0]['id'] == cid
    with db.transaction() as session:
        session.delete(session.get(Conversation, cid))
    with db.sessions() as session:
        assert session.scalar(select(func.count()).select_from(TranscriptMessage).where(TranscriptMessage.conversation_id == cid)) == 0
        assert session.execute(text('SELECT rowid FROM transcript_fts WHERE transcript_fts MATCH :q'), {'q':'"new-sync-needle"'}).all() == []


def test_global_history_page_uses_order_index_and_preserves_all_members(saved):
    client, db, _, _, _ = saved
    expected = client.get('/api/evaluations').json()
    first = client.get('/api/evaluations/page', params={'limit':1}).json()
    second = client.get('/api/evaluations/page', params={'limit':1,'cursor':first['next_cursor']}).json()
    assert first['items'] + second['items'] == expected and first['source'] is None
    with db.sessions() as session:
        plan = session.execute(text('EXPLAIN QUERY PLAN SELECT id FROM evaluations ORDER BY created_at DESC,id DESC LIMIT 25')).all()
        assert any('ix_evaluation_global_history' in str(row) for row in plan)
