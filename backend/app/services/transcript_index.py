"""Derived SQLite search index; original source JSON remains authoritative."""
import unicodedata

from sqlalchemy import delete, exists, func, insert, or_, select, text
from sqlalchemy.exc import OperationalError

from backend.app.db import Conversation, TranscriptIndexState, TranscriptMessage
from backend.app.services.search import folded, search_messages

INDEX_VERSION = "literal-nfc-casefold-trigram-v1:" + unicodedata.unidata_version


def fts_available(connection):
    return connection.exec_driver_sql("SELECT 1 FROM sqlite_master WHERE type='table' AND name='transcript_fts'").first() is not None


def delete_index(connection, conversation_id):
    has_fts = fts_available(connection)
    old = list(connection.execute(select(TranscriptMessage.id, TranscriptMessage.folded_text).where(
        TranscriptMessage.conversation_id == conversation_id)))
    if has_fts:
        for row in old:
            connection.exec_driver_sql("INSERT INTO transcript_fts(transcript_fts,rowid,folded_text) VALUES('delete',?,?)", (row.id, row.folded_text))
    connection.execute(delete(TranscriptMessage).where(TranscriptMessage.conversation_id == conversation_id))
    connection.execute(delete(TranscriptIndexState).where(TranscriptIndexState.conversation_id == conversation_id))


def write_index(connection, conversation_id, digest, snapshot):
    delete_index(connection, conversation_id)
    has_fts = fts_available(connection)
    messages = snapshot.get("transcript", [])
    # Unsupported legacy source shapes stay on the exact source-scan fallback.
    if any(not isinstance(m, dict) or not isinstance(m.get('id'), str) or not isinstance(m.get('text'), str) or not isinstance(m.get('speaker'), str) for m in messages):
        return
    try:
        normalized = [folded(m['text']) for m in messages]
        for value in normalized:
            value.encode('utf-8')
    except UnicodeEncodeError:
        return
    for ordinal, (message, value) in enumerate(zip(messages, normalized)):
        result = connection.execute(insert(TranscriptMessage).values(conversation_id=conversation_id, message_id=message['id'],
            ordinal=ordinal, speaker=message['speaker'], folded_text=value, fts_safe='\x00' not in value))
        if has_fts:
            connection.exec_driver_sql("INSERT INTO transcript_fts(rowid,folded_text) VALUES(?,?)", (result.inserted_primary_key[0], value))
    connection.execute(insert(TranscriptIndexState).values(conversation_id=conversation_id, content_hash=digest, version=INDEX_VERSION))


def ensure_index(engine, force=False):
    """Atomic, restartable backfill; never modifies a source or evaluation row."""
    with engine.connect() as connection:
        connection.exec_driver_sql('BEGIN IMMEDIATE')
        try:
            existed = fts_available(connection)
            try:
                connection.exec_driver_sql("CREATE VIRTUAL TABLE IF NOT EXISTS transcript_fts USING fts5(folded_text, content='transcript_messages', content_rowid='id', tokenize='trigram case_sensitive 1')")
            except OperationalError as error:
                if not any(message in str(error).lower() for message in ('no such module: fts5', 'no such tokenizer: trigram')):
                    raise
            enabled = fts_available(connection)
            if enabled and not existed:
                connection.exec_driver_sql("INSERT INTO transcript_fts(transcript_fts) VALUES('rebuild')")
            query = select(Conversation.id, Conversation.content_hash, Conversation.snapshot).outerjoin(
                TranscriptIndexState, TranscriptIndexState.conversation_id == Conversation.id)
            if not force:
                query = query.where(or_(TranscriptIndexState.conversation_id.is_(None),
                    TranscriptIndexState.content_hash != Conversation.content_hash, TranscriptIndexState.version != INDEX_VERSION))
            rows = list(connection.execute(query))
            for row in rows:
                write_index(connection, row.id, row.content_hash, row.snapshot)
            if enabled and force:
                connection.exec_driver_sql("INSERT INTO transcript_fts(transcript_fts) VALUES('rebuild')")
            connection.commit()
            return {'indexed_sources': len(rows), 'fts_enabled': enabled, 'version': INDEX_VERSION}
        except BaseException:
            connection.rollback()
            raise


def valid_state():
    return exists(select(TranscriptIndexState.conversation_id).where(
        TranscriptIndexState.conversation_id == Conversation.id, TranscriptIndexState.content_hash == Conversation.content_hash,
        TranscriptIndexState.version == INDEX_VERSION))


def matching_messages(session, query, speaker='all'):
    needle = folded(query.strip())
    statement = select(TranscriptMessage)
    if speaker != 'all':
        statement = statement.where(TranscriptMessage.speaker == speaker)
    if needle:
        exact = func.instr(TranscriptMessage.folded_text, needle) > 0
        if len(needle) >= 3 and '\x00' not in needle and fts_available(session.connection()):
            phrase = '"' + needle.replace('"', '""') + '"'
            hits = select(text('rowid')).select_from(text('transcript_fts')).where(text('transcript_fts MATCH :literal_phrase')).params(literal_phrase=phrase)
            statement = statement.where(or_(TranscriptMessage.id.in_(hits), TranscriptMessage.fts_safe.is_(False)))
        statement = statement.where(exact)
    return statement


def narrow_sources(session, sources, query, speaker='all'):
    if not query.strip() and speaker == 'all':
        return sources
    matches = matching_messages(session, query, speaker).with_only_columns(TranscriptMessage.conversation_id)
    # Missing/outdated derived data is scanned, never silently omitted.
    return sources.where(or_(~valid_state(), Conversation.id.in_(matches)))


def indexed_message_page(session, conversation, query, speaker='all', limit=5, offset=0):
    state = session.get(TranscriptIndexState, conversation.id)
    if (not state or state.content_hash != conversation.content_hash or state.version != INDEX_VERSION
            or not query.strip() and speaker == 'all'):
        return search_messages(conversation.snapshot['transcript'], query, speaker, limit, offset)
    statement = matching_messages(session, query, speaker).where(TranscriptMessage.conversation_id == conversation.id)
    total = session.scalar(select(func.count()).select_from(statement.with_only_columns(TranscriptMessage.id).subquery()))
    ordinals = list(session.scalars(statement.with_only_columns(TranscriptMessage.ordinal).order_by(TranscriptMessage.ordinal).offset(offset).limit(limit)))
    messages = [conversation.snapshot['transcript'][ordinal] for ordinal in ordinals]
    snippets, _ = search_messages(messages, query, speaker, limit, 0)
    return snippets, total
