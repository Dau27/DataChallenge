"""Portable reports derived from a single read transaction; never inference."""
import csv
import io
import json
import re
from urllib.parse import parse_qsl, unquote, urlsplit

from backend.app.db import Conversation
from backend.app.services.saved_results import evaluation_snapshot, source_view

META_KEYS = {"provider", "model", "prompt_version", "prompt_hash", "schema_version", "schema_hash", "scoring_version",
             "generation", "mode", "evidence_validation_version", "rate"}
ATTEMPT_KEYS = {"number", "status", "http_status", "latency_ms", "input_tokens", "output_tokens", "response_model",
                "retry_after_seconds", "error_code", "validation_error", "input_token_upper_bound", "max_output_tokens"}
PRIVATE_KEYS = {"api_key", "authorization", "password", "secret", "credential", "access_token", "refresh_token",
                "organizer_url", "audio_url", "headers", "request", "response", "payload"}


def export_packet(session, evaluation_id, settings, include_excerpts=False):
    saved = evaluation_snapshot(session, evaluation_id)
    conversation = session.get(Conversation, saved["conversation_id"])
    saved["metadata"] = {k: v for k, v in saved["metadata"].items() if k in META_KEYS}
    saved["attempts"] = [{k: v for k, v in a.items() if k in ATTEMPT_KEYS} for a in saved["attempts"]]

    def private_metadata(value):
        if isinstance(value, dict):
            return {k: private_metadata(v) for k, v in value.items() if k.casefold() not in PRIVATE_KEYS}
        if isinstance(value, list):
            return [private_metadata(v) for v in value]
        return value
    saved["metadata"] = private_metadata(saved["metadata"])
    packet = {"export_schema_version": 1, "source": source_view(conversation), "evaluation": saved,
              "export_policy": {"source_excerpts_included": include_excerpts, "recording_urls_included": False,
                  "credentials_included": False, "metadata_fields": "evaluation provenance and attempt accounting only",
                  "notice": "Stored results and review history, not a new evaluation. Estimates are not invoices. Explanations and review comments may quote source text."}}
    if include_excerpts:
        messages = conversation.snapshot["transcript"]
        ids = [m["id"] for m in messages]
        excerpts = []
        assessments = [(basis, (saved[basis] or {}).get("results", {})) for basis in ("original", "effective")]
        assessments += [(f"review:{r['id']}", {r["criterion_id"]: r["judgment"]}) for r in saved["reviews"]]
        for basis, results in assessments:
            for cid, judgment in results.items():
                for evidence in judgment["evidence"]:
                    start, end = evidence["start_message_id"], evidence["end_message_id"]
                    valid = start in ids and end in ids and ids.index(start) <= ids.index(end)
                    excerpts.append({"basis": basis, "criterion_id": cid, "evidence": evidence,
                        "messages": messages[ids.index(start):ids.index(end) + 1] if valid else [], "range_available": valid})
        packet["source_excerpts"] = excerpts

    # Redact known local credentials/URLs even if pasted into explanations or reviews.
    hidden = [s for s in (settings.api_key, settings.organizer_url, conversation.snapshot.get("audio_url")) if s]
    redactions = 0
    def safe_string(value):
        nonlocal redactions
        for secret in hidden:
            for spelling in {secret, unquote(secret)}:
                if spelling and spelling in value:
                    redactions += value.count(spelling); value = value.replace(spelling, "[REDACTED]")
        value, count = re.subn(r"\b(?:sk-[A-Za-z0-9_-]{12,}|Bearer\s+\S+)", "[REDACTED]", value, flags=re.IGNORECASE)
        redactions += count
        def url(match):
            nonlocal redactions
            text = match.group(0)
            try:
                parts = urlsplit(text)
                sensitive = parts.username or parts.password or any(
                    re.search(r"token|signature|credential|secret|api.?key|authorization|^sig$|^key$", key, re.IGNORECASE)
                    for key, _ in parse_qsl(parts.query))
            except ValueError:
                sensitive = True
            if sensitive:
                redactions += 1
                return "[REDACTED URL]"
            return text
        return re.sub(r"https?://[^\s<>\"']+", url, value)
    def scrub(value):
        if isinstance(value, str): return safe_string(value)
        if isinstance(value, dict): return {safe_string(str(k)): scrub(v) for k, v in value.items()}
        if isinstance(value, list): return [scrub(v) for v in value]
        return value
    packet = scrub(packet)
    packet["export_policy"]["redacted_string_occurrences"] = redactions
    return packet


def json_report(packet):
    return json.dumps(packet, ensure_ascii=False, indent=2, allow_nan=False).encode("utf-8")


def csv_report(packet):
    """Typed long-form records; JSON cells preserve booleans/nulls and nested history."""
    headers = ["record_type", "evaluation_id", "conversation_id", "source_id", "revision", "content_hash", "checklist_id",
               "basis", "criterion_id", "name", "answer_type", "disposition", "value_json", "weight", "raw_points",
               "normalized_contribution", "total", "total_reason", "explanation", "na_reason", "review_reason", "evidence_json", "data_json"]
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=headers)
    writer.writeheader()
    evaluation, source = packet["evaluation"], packet["source"]
    common = {"evaluation_id": evaluation["id"], "conversation_id": source["id"], "source_id": source["source_id"],
              "revision": source["revision"], "content_hash": source["content_hash"], "checklist_id": evaluation["checklist"]["id"]}
    def encoded(value): return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    def cell(value):
        text = str(value) if value is not None else ""
        # Keep formula-like text inert in spreadsheet applications, including whitespace prefixes.
        return "'" + text if text.lstrip().startswith(("=", "+", "-", "@")) or text.startswith(("\t", "\r", "\n")) else text
    def row(record_type, **values):
        writer.writerow({k: cell(v) for k, v in {**common, "record_type": record_type, **values}.items()})
    context = {k: v for k, v in packet.items() if k not in {"evaluation", "source_excerpts"}}
    context["evaluation"] = {k: v for k, v in evaluation.items() if k not in {"original", "effective", "original_score", "effective_score", "appeals", "reviews"}}
    row("evaluation", data_json=encoded(context))
    for basis in ("original", "effective"):
        assessment, calculated = evaluation[basis], evaluation[basis + "_score"]
        row("score", basis=basis, total=(calculated or {}).get("total"), total_reason=(calculated or {}).get("reason"), data_json=encoded(calculated))
        points = {r["criterion_id"]: r for r in (calculated or {}).get("criteria", [])}
        for criterion in evaluation["checklist"]["snapshot"]["criteria"]:
            cid = criterion["id"]; judgment = (assessment or {}).get("results", {}).get(cid)
            raw = points.get(cid, {})
            row("criterion", basis=basis, criterion_id=cid, name=criterion["name"], answer_type=criterion["answer_type"],
                disposition=(judgment or {}).get("disposition"), value_json=encoded(judgment["value"]) if judgment else "",
                weight=criterion["weight"], raw_points=raw.get("raw_points"), normalized_contribution=raw.get("normalized_contribution"),
                explanation=(judgment or {}).get("explanation"), na_reason=(judgment or {}).get("na_reason"), review_reason=(judgment or {}).get("review_reason"),
                evidence_json=encoded((judgment or {}).get("evidence", [])), data_json=encoded({"criterion": criterion, "judgment": judgment, "points": raw or None}))
    for kind, items in (("appeal", evaluation["appeals"]), ("review", evaluation["reviews"]), ("excerpt", packet.get("source_excerpts", []))):
        for item in items:
            row(kind, criterion_id=item.get("criterion_id"), basis=item.get("basis", ""), data_json=encoded(item))
    return stream.getvalue().encode("utf-8-sig")
