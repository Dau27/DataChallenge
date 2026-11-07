"""Portable reports derived from a single read transaction; never inference."""
import csv
import io
import json
import re
from urllib.parse import parse_qsl, unquote, urlsplit

from backend.app.db import Conversation, now
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
    # Only sanitized identity fields enter the manifest; no settings or raw URLs.
    packet["manifest"] = _manifest([packet], include_excerpts)
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


def _manifest(reports, include_excerpts):
    """Describe only the sanitized, frozen saved snapshots actually included."""
    return {"schema_version": 1, "generated_at": now(), "selected_run_count": len(reports),
        "answer_sets": ["original", "effective"], "source_excerpts_included": include_excerpts,
        "runs": [{"evaluation_id": p["evaluation"]["id"], "updated_at": p["evaluation"]["updated_at"],
            "conversation_id": p["source"]["id"], "source_id": p["source"]["source_id"],
            "group_id": p["source"]["group_id"], "revision": p["source"]["revision"],
            "source_hash": p["source"]["content_hash"], "checklist_id": p["evaluation"]["checklist"]["id"],
            "checklist_hash": p["evaluation"]["checklist"]["content_hash"]} for p in reports],
        "notice": "Explicit saved-run selection from one read snapshot. No new assessment. Source quotations may be sensitive; credential redaction is not anonymization."}


def export_batch(session, evaluation_ids, settings, include_excerpts=False):
    """Caller supplies one db.read_snapshot session; no partial or implicit-all export."""
    if not isinstance(evaluation_ids, (list, tuple)) or not 1 <= len(evaluation_ids) <= 100:
        raise ValueError("Select between 1 and 100 saved evaluation IDs")
    if any(not isinstance(eid, str) or not eid.strip() or len(eid) > 200 for eid in evaluation_ids):
        raise ValueError("Saved evaluation IDs must be nonblank strings of at most 200 characters")
    if len(set(evaluation_ids)) != len(evaluation_ids):
        raise ValueError("Select unique saved evaluation IDs")
    # export_packet is read-only and raises SavedResultNotFound before any response is emitted.
    reports = [export_packet(session, eid, settings, include_excerpts) for eid in evaluation_ids]
    return {"export_schema_version": 1, "batch_schema_version": 1,
            "manifest": _manifest(reports, include_excerpts), "reports": reports}


def batch_csv_report(packet):
    """Keep archival record types and add one batch manifest, with one CSV header."""
    stream = io.StringIO(newline="")
    writer = None
    for report in packet["reports"]:
        reader = csv.DictReader(io.StringIO(csv_report(report).decode("utf-8-sig")))
        if writer is None:
            writer = csv.DictWriter(stream, fieldnames=reader.fieldnames)
            writer.writeheader()
            writer.writerow({"record_type": "batch_manifest", "data_json": json.dumps(packet["manifest"], ensure_ascii=False, separators=(",", ":"))})
        # Cells were already sanitized and formula-protected by csv_report; do not alter them twice.
        writer.writerows(reader)
    return stream.getvalue().encode("utf-8-sig")


def simple_csv_report(packet):
    """Spreadsheet view: exactly one scalar row per original/effective criterion.

    Manifest identity is represented in scalar columns, rather than adding a
    non-criterion record or repeating nested JSON. Use archival formats for the
    full checklist, reviewer history and nested provenance.
    """
    reports = packet.get("reports", [packet])
    manifest = packet.get("manifest") or _manifest(reports, bool(packet.get("export_policy", {}).get("source_excerpts_included")))
    headers = ["export_schema_version", "generated_at", "selected_run_count", "evaluation_id", "evaluation_state", "evaluation_updated_at",
        "conversation_id", "source_id", "group_id", "revision", "content_hash", "checklist_id", "checklist_hash", "basis",
        "criterion_id", "criterion_name", "answer_type", "disposition", "answer_label", "value_json", "weight", "raw_points",
        "normalized_contribution", "total", "total_availability", "total_reason", "explanation", "na_reason", "review_reason",
        "evidence_message_ids", "evidence_kinds", "source_excerpts_included", "source_excerpts", "redacted_string_occurrences"]
    stream = io.StringIO(newline=""); writer = csv.DictWriter(stream, fieldnames=headers); writer.writeheader()
    def cell(value):
        text = str(value) if value is not None else ""
        return "'" + text if text.lstrip().startswith(("=", "+", "-", "@")) or text.startswith(("\t", "\r", "\n")) else text
    for report in reports:
        evaluation, source = report["evaluation"], report["source"]
        common = {"export_schema_version": 1, "generated_at": manifest["generated_at"], "selected_run_count": manifest["selected_run_count"],
            "evaluation_id": evaluation["id"], "evaluation_state": evaluation["state"], "evaluation_updated_at": evaluation["updated_at"],
            "conversation_id": source["id"], "source_id": source["source_id"], "group_id": source["group_id"], "revision": source["revision"],
            "content_hash": source["content_hash"], "checklist_id": evaluation["checklist"]["id"], "checklist_hash": evaluation["checklist"]["content_hash"],
            "source_excerpts_included": str(report["export_policy"]["source_excerpts_included"]).lower(),
            "redacted_string_occurrences": report["export_policy"]["redacted_string_occurrences"]}
        for basis in ("original", "effective"):
            assessment, calculated = evaluation[basis], evaluation[basis + "_score"]
            points = {r["criterion_id"]: r for r in (calculated or {}).get("criteria", [])}
            for criterion in evaluation["checklist"]["snapshot"]["criteria"]:
                cid = criterion["id"]; judgment = (assessment or {}).get("results", {}).get(cid); raw = points.get(cid, {})
                disposition = (judgment or {}).get("disposition")
                value = judgment["value"] if judgment else None
                answer_label = ("Unavailable" if judgment is None else "N/A" if disposition == "not_applicable" else
                    "Needs review" if disposition == "needs_review" else "Yes" if value is True else "No" if value is False else str(value))
                evidence = (judgment or {}).get("evidence", [])
                excerpts = [item for item in report.get("source_excerpts", []) if item["basis"] == basis and item["criterion_id"] == cid]
                excerpt_messages = {m["id"]: m for item in excerpts for m in item["messages"]}
                row = {**common, "basis": basis, "criterion_id": cid, "criterion_name": criterion["name"], "answer_type": criterion["answer_type"],
                    "disposition": disposition or "unavailable", "answer_label": answer_label,
                    "value_json": json.dumps(value, ensure_ascii=False) if judgment else "", "weight": criterion["weight"],
                    "raw_points": raw.get("raw_points"), "normalized_contribution": raw.get("normalized_contribution"),
                    "total": (calculated or {}).get("total"), "total_availability": "available" if (calculated or {}).get("total") is not None else "unavailable",
                    "total_reason": (calculated or {}).get("reason") or ("ASSESSMENT_UNAVAILABLE" if calculated is None else ""),
                    "explanation": (judgment or {}).get("explanation"), "na_reason": (judgment or {}).get("na_reason"), "review_reason": (judgment or {}).get("review_reason"),
                    "evidence_message_ids": "; ".join(f"{e['start_message_id']}–{e['end_message_id']}" for e in evidence),
                    "evidence_kinds": "; ".join(e["kind"] for e in evidence),
                    "source_excerpts": "\n".join(f"{m['id']} | {m['speaker']} | {m['timestamp']} | {m['text']}" for m in excerpt_messages.values())}
                writer.writerow({k: cell(v) for k, v in row.items()})
    return stream.getvalue().encode("utf-8-sig")
