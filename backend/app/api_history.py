"""Bounded keyset pages. Saved assessments and audit exports remain immutable."""
import base64
import binascii
import json
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import StrictStr, ValidationError
from sqlalchemy import and_, func, or_, select

from backend.app.db import Conversation, Evaluation
from backend.app.domain import Contract, content_hash
from backend.app.services.saved_results import source_view, summary_columns

router = APIRouter(prefix='/api')


class HistoryNavigation(Contract):
    total: int
    start: int
    end: int
    limit: int
    next_cursor: str | None
    previous_cursor: str | None
    first_cursor: str | None


class HistoryPage(HistoryNavigation):
    items: list[dict[str, Any]]
    source: dict[str, Any] | None


class Cursor(Contract):
    version: Literal[1]
    scope: StrictStr
    ceiling: tuple[StrictStr, StrictStr]
    boundary: tuple[StrictStr, StrictStr] | None
    direction: Literal['older', 'newer']


def encode_cursor(scope, ceiling, boundary=None, direction='older'):
    raw = json.dumps({'version': 1, 'scope': scope, 'ceiling': ceiling, 'boundary': boundary, 'direction': direction}, separators=(',', ':')).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip('=')


def decode_cursor(value, scope):
    try:
        raw = base64.b64decode(value + '=' * (-len(value) % 4), altchars=b'-_', validate=True)
        cursor = Cursor.model_validate_json(raw)
        if cursor.scope != scope or any(not key or len(key) > 200 for pair in [cursor.ceiling, cursor.boundary] if pair for key in pair):
            raise ValueError
        return cursor
    except (ValueError, ValidationError, binascii.Error):
        raise ValueError('Invalid history cursor or a cursor from a different conversation/filter; return to the latest page.') from None


def key_before(key):
    return or_(Evaluation.created_at < key[0], and_(Evaluation.created_at == key[0], Evaluation.id < key[1]))


def key_after(key):
    return or_(Evaluation.created_at > key[0], and_(Evaluation.created_at == key[0], Evaluation.id > key[1]))


def evaluation_history_page(session, conversation_id=None, limit=25, cursor=None):
    source = session.get(Conversation, conversation_id) if conversation_id else None
    if conversation_id and source is None:
        raise HTTPException(404, 'Conversation revision not found')
    scope = content_hash({'kind': 'evaluation-history-v1', 'conversation_id': conversation_id or None,
                          'content_hash': source.content_hash if source else None})
    filters = [Evaluation.conversation_id == conversation_id] if conversation_id else []
    parsed = decode_cursor(cursor, scope) if cursor else None
    ceiling = parsed.ceiling if parsed else session.execute(select(Evaluation.created_at, Evaluation.id).where(*filters).order_by(
        Evaluation.created_at.desc(), Evaluation.id.desc()).limit(1)).first()
    if ceiling is None:
        return {'items': [], 'source': source_view(source) if source else None, 'total': 0, 'start': 0, 'end': 0,
                'limit': limit, 'next_cursor': None, 'previous_cursor': None, 'first_cursor': None}
    ceiling = tuple(ceiling)
    filters.append(or_(key_before(ceiling), and_(Evaluation.created_at == ceiling[0], Evaluation.id == ceiling[1])))
    total = session.scalar(select(func.count()).select_from(Evaluation).where(*filters))
    page_filters = list(filters)
    if parsed and parsed.boundary:
        page_filters.append(key_after(parsed.boundary) if parsed.direction == 'newer' else key_before(parsed.boundary))
    ascending = parsed is not None and parsed.direction == 'newer'
    order = (Evaluation.created_at.asc(), Evaluation.id.asc()) if ascending else (Evaluation.created_at.desc(), Evaluation.id.desc())
    items = [dict(row) for row in session.execute(select(*summary_columns()).where(*page_filters).order_by(*order).limit(limit)).mappings()]
    if ascending:
        items.reverse()
    start = session.scalar(select(func.count()).select_from(Evaluation).where(*filters, key_after((items[0]['created_at'], items[0]['id'])))) + 1 if items else 0
    end = start + len(items) - 1 if items else 0
    return {'items': items, 'source': source_view(source) if source else None, 'total': total, 'start': start, 'end': end, 'limit': limit,
        'next_cursor': encode_cursor(scope, ceiling, (items[-1]['created_at'], items[-1]['id'])) if items and end < total else None,
        'previous_cursor': encode_cursor(scope, ceiling, (items[0]['created_at'], items[0]['id']), 'newer') if items and start > 1 else None,
        'first_cursor': encode_cursor(scope, ceiling)}


@router.get('/evaluations/page', response_model=HistoryPage)
def history(request: Request, conversation_id: str | None = Query(None, max_length=200),
            limit: int = Query(25, ge=1, le=100), cursor: str | None = Query(None, min_length=1, max_length=2048)):
    with request.app.state.db.read_snapshot() as session:
        return evaluation_history_page(session, conversation_id or None, limit, cursor)
