from collections import Counter
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import httpx
from sqlalchemy import func, select

from backend.app.db import Conversation
from backend.app.domain import ImportEnvelope, content_hash
from backend.app.limits import IMPORT_BYTE_LIMIT


def import_payload(db, envelope: ImportEnvelope) -> dict:
    created, unchanged, imported_ids = 0, 0, []
    group = envelope.data.dataset_group_id
    with db.transaction() as session:
        for record in envelope.data.records:
            source = record.model_dump(mode="json")
            digest = content_hash({"group_id": group, **source})
            existing = session.scalar(select(Conversation).where(Conversation.group_id == group,
                                      Conversation.source_id == record.conversation_id, Conversation.content_hash == digest))
            if existing:
                unchanged += 1
                imported_ids.append(existing.id)
                continue
            revision = (session.scalar(select(func.max(Conversation.revision)).where(Conversation.group_id == group,
                                       Conversation.source_id == record.conversation_id)) or 0) + 1
            source["transcript"] = [{"id": f"m{i:04d}", **message} for i, message in enumerate(source["transcript"], 1)]
            conversation = Conversation(group_id=group, source_id=record.conversation_id, revision=revision,
                                        content_hash=digest, snapshot=source)
            session.add(conversation)
            session.flush()
            imported_ids.append(conversation.id)
            created += 1
    return {"group_id": group, "actual_records": len(envelope.data.records), "created": created, "unchanged": unchanged,
            "conversation_ids": imported_ids, "languages": dict(Counter(r.language for r in envelope.data.records)),
            "channels": dict(Counter(r.channel for r in envelope.data.records))}


def organizer_url(configured_url: str, group_id: str):
    parts = urlsplit(configured_url)
    # Preserve all unrelated parameters, including private signatures. Do not log this URL.
    query = [(key, value) for key, value in parse_qsl(parts.query, keep_blank_values=True) if key != "group_id"]
    query.append(("group_id", group_id))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), ""))


def fetch_organizer(settings, group_id):
    if not settings.organizer_url:
        raise ValueError("ORGANIZER_API_URL is not configured")
    try:
        with httpx.Client(timeout=settings.timeout, follow_redirects=False) as client:
            with client.stream("GET", organizer_url(settings.organizer_url, group_id)) as response:
                if response.status_code != 200:
                    raise ValueError(f"Organizer HTTP {response.status_code}; no data imported")
                body = bytearray()
                for chunk in response.iter_bytes(chunk_size=65536):
                    if len(body) + len(chunk) > IMPORT_BYTE_LIMIT:
                        raise ValueError("Organizer response exceeds the 25 MB import safeguard")
                    body.extend(chunk)
        envelope = ImportEnvelope.model_validate_json(body)
    except httpx.HTTPError:
        raise ValueError("Organizer network/timeout failure; endpoint and response are hidden") from None
    if envelope.data.dataset_group_id != group_id:
        raise ValueError("Organizer returned a different dataset group; no data imported")
    return envelope
