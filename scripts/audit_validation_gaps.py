"""Reproduce validation boundaries offline; never submit an actual provider request.

All judgments/transcripts generated here are synthetic. A saved database, when
specified, is opened read-only and is never used by an application job runner.
Passing this audit means that its documented gaps/controls were reproduced,
not that unsupported judgments have been fixed or model accuracy was measured.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from dataclasses import dataclass
from decimal import Decimal
import hashlib
import json
import math
from pathlib import Path
import socket
import sqlite3
import statistics
import sys
import time
from unittest.mock import patch

from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.config import Settings
from backend.app.db import Base, ChecklistVersion, Conversation, Database, Evaluation
from backend.app.domain import Assessment, Checklist, canonical_json, content_hash, validate_assessment
from backend.app.services.evaluator import (
    EvaluationFailure, Provider, decode_assessment, evaluation_payload, output_schema, validate_source_evidence,
)
from backend.app.services.jobs import Jobs
from backend.app.services.reviews import decide, submit_appeal
from backend.app.services.scoring import score


@dataclass
class Case:
    name: str
    family: str
    checklist: Checklist
    conversation: dict
    response: dict
    expected: str
    unsupported: bool
    reason: str


def isolated(seed, criterion_id, **changes):
    data = seed.model_dump(mode="json")
    criterion = deepcopy(next(c for c in data["criteria"] if c["id"] == criterion_id))
    criterion.update(changes)
    data["criteria"] = [criterion]
    data["sections"] = [s for s in data["sections"] if s["id"] == criterion["section_id"]]
    data["name"] = "SYNTHETIC validation-boundary audit"
    return Checklist.model_validate(data)


def transcript(*turns):
    return {"conversation_id": "SYNTHETIC_AUDIT_ONLY", "channel": "agent chat", "language": "EN", "audio_url": None,
            "transcript": [{"id": f"m{i:04}", "timestamp": f"00:{i:02}", "speaker": role, "text": text}
                           for i, (role, text) in enumerate(turns, 1)]}


def response_for(checklist, decision, explanation, citation=1, end=None, condition=False):
    return {"results": {checklist.criteria[0].id: {
        "na_condition_met": condition,
        "evidence": [{"kind": "support", "start_message_id": f"m{citation:04}", "end_message_id": f"m{end or citation:04}"}],
        "explanation": explanation, "decision": decision}}}


def cases_for(seed):
    cases = []

    def add(name, family, criterion_id, turns, decision, explanation, reason, *, expected="accepted", unsupported=True,
            citation=1, end=None, condition=False, changes=None):
        rubric = isolated(seed, criterion_id, **(changes or {}))
        cases.append(Case(name, family, rubric, transcript(*turns),
                          response_for(rubric, decision, explanation, citation, end, condition), expected, unsupported, reason))

    add("NA-01", "N/A", "needs", [("client", "My app does not work."), ("operator", "Which platform are you using?"),
        ("client", "The web portal."), ("operator", "Reload the web page.")],
        {"not_applicable_reason": "The initial customer context was sufficient."}, "No clarification was necessary.",
        "The necessary platform was missing initially and the human explicitly elicited it.", condition=True, citation=2)
    add("NA-02", "N/A", "needs", [("client", "Where can I download a statement in the web portal?"),
        ("operator", "Open Reports, choose the date range and click Download.")], {"assessed_value": True},
        "The operator gave the requested instructions.", "Giving instructions is not clarification; the initial question was already sufficient.", citation=2)
    add("NA-03", "N/A", "consultation", [("client", "Where is the statement download button in the web portal?"),
        ("operator", "I cannot help with that. Goodbye.")], {"not_applicable_reason": "The request was not formulated before the chat ended."},
        "No request was available to assess.", "A concrete customer request is present, so this N/A event did not occur.", condition=True)
    add("NA-04", "N/A", "closing", [("client", "That solved it. Thank you."),
        ("operator", "Your download is now complete. If you need anything else, contact us. Goodbye.")],
        {"not_applicable_reason": "The client interrupted before the operator could close."}, "The operator had no opportunity to close.",
        "The complete ordinary closing is visible; premature interruption is fabricated.", condition=True, citation=2)
    add("NA-05", "N/A", "needs", [("client", "Where is Reports in the web portal?"), ("operator", "Open the Reports tab.")],
        {"not_applicable_reason": "none"}, "SYNTHETIC applicability explanation.",
        "The N/A reason is a placeholder, not an explicit condition justification.", condition=True)
    add("NA-06", "N/A", "identification", [("client", "Please show my private account balance."),
        ("operator", "I have not verified your identity. Your private balance is 500.")],
        {"not_applicable_reason": "Only general instructions were supplied."}, "No protected disclosure occurred.",
        "The synthetic operator explicitly discloses private account data without verification.", condition=True, citation=2)
    add("CONS-01", "Consultation", "consultation", [("client", "How do I download a statement and how do I change my phone number?"),
        ("operator", "Open Reports to download the statement. Goodbye.")], {"assessed_value": 20},
        "The statement question was answered, but the phone-number question was left unanswered.",
        "The maximum anchor contradicts both the source and its own explanation of an omitted material question.", citation=2)
    add("CONS-02", "Consultation", "consultation", [("client", "Where is Reports?"), ("operator", "Open Reports in the web portal."),
        ("client", "That worked; my question is answered.")], {"assessed_value": 0},
        "The operator answered the full request and the customer confirmed success.",
        "The zero anchor contradicts its explanation; numerical membership alone is checked.", citation=2)
    add("CONS-03", "Consultation", "consultation", [("client", "Where is the statement download?"),
        ("bot", "Go to Reports and Download."), ("operator", "I will not answer your question.")], {"assessed_value": 20},
        "The answer is present in the bot message.", "A bot's response is being credited as human operator consultation.", citation=2)
    add("CONS-04", "Consultation", "consultation", [("client", "Are all commissions zero for my account?"),
        ("operator", "All commissions are always zero for every account.")], {"assessed_value": 20},
        "The official policy claim is correct.",
        "No authoritative fee schedule is supplied. This proves unverified correctness can pass, not that the claim is factually false.", citation=2)
    add("RULE-01", "Changed criteria", "closing", [("operator", "You're welcome. Goodbye!")], {"assessed_value": True},
        "The operator was polite and said goodbye.",
        "A meaning-preserving paraphrase of the initial compound closing loses its exact-description guard.",
        changes={"description": "Yes only when the operator gives a recap OR offers further help, AND says goodbye."})
    add("RULE-02", "Changed criteria", "contact", [("operator", "Hello, I am Alex. I will investigate.")], {"assessed_value": True},
        "The operator supplied a ticket marker.", "The newly configured literal marker is absent.",
        changes={"id": "audit_ticket", "name": "SYNTHETIC ticket marker", "description": "Yes only if the operator writes the exact marker AUDIT-CASE-42."})
    add("RULE-03", "Changed criteria", "needs", [("client", "Where is Reports?"), ("operator", "Open Reports.")],
        {"not_applicable_reason": "The customer disconnected."}, "No review was possible.",
        "The edited N/A condition requires an explicit system event absent from the source.", condition=True,
        changes={"na_condition": "A system message explicitly contains CUSTOMER_DISCONNECTED."})
    add("RULE-04", "Changed criteria", "consultation", [("client", "What is the next step?"), ("operator", "I will investigate.")],
        {"assessed_value": 20}, "The operator gave complete instructions.", "The edited maximum anchor requires a missing marker.", citation=2,
        changes={"description": "Award 20 only if the operator supplies the exact marker AUDIT-CASE-42; otherwise use 0.",
                 "scale": [{"value": 20, "description": "The exact marker AUDIT-CASE-42 is present."},
                           {"value": 0, "description": "The exact marker is absent."}]})
    add("EVID-01", "Evidence/uncertainty", "contact", [("bot", "Hello, I am the automated assistant."),
        ("operator", "What do you want?")], {"assessed_value": True}, "A greeting and self-introduction exist in the bot turn.",
        "Human contact receives credit supported only by bot evidence.")
    add("EVID-02", "Evidence/uncertainty", "critical_errors", [("client", "You are an idiot."),
        ("operator", "Please keep this respectful. How can I help?")], {"assessed_value": True},
        "An insult is present in the transcript.", "A customer insult is attributed to the human operator.")
    add("EVID-03", "Evidence/uncertainty", "closing", [("client", "If you need anything else, contact me. Goodbye."),
        ("operator", "You're welcome. Goodbye!")], {"assessed_value": True}, "A further-help offer and goodbye were cited.",
        "Client-only evidence skips the closing guard because the cited operator-message list is empty.")
    add("EVID-04", "Evidence/uncertainty", "contact", [("operator", "Hello, I am Alex.")],
        {"needs_review_reason": "An official policy is needed to determine whether this visible greeting exists."},
        "The source is clear, but external policy is requested.", "A non-placeholder invented missing basis can withhold the total.")
    add("EVID-05", "Evidence/uncertainty", "closing", [("operator", "The code is 42.")], {"assessed_value": True},
        "The operator closed the conversation correctly.", "Unrelated operator words escape the courtesy-only blacklist despite lacking either closing component.")

    add("CTRL-01", "Controls", "closing", [("operator", "You're welcome. Goodbye!")], {"assessed_value": True},
        "Only courtesy and farewell are present.", "The existing initial-definition closing guard must reject this.", expected="rejected", unsupported=False)
    add("CTRL-02", "Controls", "contact", [("operator", "Hello, I am Alex.")], {"not_applicable_reason": "Not needed."},
        "Forbidden N/A.", "N/A disabled in configuration must be rejected.", condition=True, expected="rejected", unsupported=False)
    add("CTRL-03", "Controls", "contact", [("operator", "Hello, I am Alex.")], {"assessed_value": 1},
        "An integer is not a strict boolean.", "Binary answer types must remain strict.", expected="rejected", unsupported=False)
    add("CTRL-04", "Controls", "consultation", [("operator", "Open Reports.")], {"assessed_value": 19},
        "An unconfigured scale anchor.", "Values outside the saved anchors must be rejected.", expected="rejected", unsupported=False)
    add("CTRL-05", "Controls", "needs", [("client", "Where is Reports?")], {"not_applicable_reason": "Already sufficient."},
        "Contradictory N/A observation.", "The applicability boolean and selected branch must agree.", condition=False, expected="rejected", unsupported=False)
    add("CTRL-06", "Controls", "contact", [("operator", "Hello, I am Alex.")], {"assessed_value": True},
        "The citation is absent.", "Nonexistent evidence IDs must be rejected.", citation=9999, expected="rejected", unsupported=False)
    add("CTRL-07", "Controls", "contact", [("client", "Hello."), ("operator", "Hello, I am Alex.")], {"assessed_value": True},
        "The citation is reversed.", "Reversed evidence ranges must be rejected.", citation=2, end=1, expected="rejected", unsupported=False)
    add("CTRL-08", "Controls", "contact", [("operator", "Hello, I am Alex.")], {"needs_review_reason": "none"},
        "Placeholder uncertainty.", "The existing missing-basis placeholder check must reject this.", expected="rejected", unsupported=False)
    add("CTRL-09", "Controls", "closing", [("operator", "Goodbye!")], {"assessed_value": True},
        "The edited definition only requires goodbye.", "A genuine rule change must not be judged by the old compound rule.", unsupported=False,
        changes={"description": "Yes if the operator says goodbye. No recap is required."})
    add("CTRL-10", "Controls", "closing", [("operator", "If you need anything else, contact us. Goodbye!")], {"assessed_value": True},
        "A human offer of help and goodbye are present.", "A supported initial-rule closing remains accepted.", unsupported=False)
    changed = deepcopy(cases[-1])
    changed.name, changed.expected = "CTRL-11", "rejected"
    changed.reason = "Obsolete or extra criterion IDs must be rejected after a rubric change."
    changed.response["results"]["obsolete_rule"] = deepcopy(next(iter(changed.response["results"].values())))
    cases.append(changed)
    # Construct explicitly: an ID rename alone must not disable the exact-definition guard.
    rubric = isolated(seed, "closing", id="renamed_closing")
    cases.append(Case("CTRL-12", "Controls", rubric, transcript(("operator", "You're welcome. Goodbye!")),
                      response_for(rubric, {"assessed_value": True}, "Courtesy only."), "rejected", False,
                      "An ID rename preserves the exact source-definition guard."))
    for case in cases:
        if case.name in {"NA-05", "CONS-03", "EVID-01", "EVID-02", "EVID-03"}:
            case.expected = "rejected"
    return cases


class StaticProvider(Provider):
    def __init__(self, settings, response):
        super().__init__(settings, transport="SYNTHETIC_STATIC_RESPONSE_NO_HTTP")
        self.response, self.reads = response, 0

    def request(self, payload, record_attempt):
        self.reads += 1
        return json.dumps(self.response)


def emitted_schema_accepts(value, schema):
    """Check only the schema keywords emitted by output_schema; fail on new ones.

    This is an offline fixture sanity check, not a general JSON Schema validator
    or a claim about a hosted provider's enforcement.
    """
    supported = {"type", "anyOf", "enum", "properties", "required", "additionalProperties", "items", "minItems", "description"}
    if set(schema) - supported:
        raise AssertionError("Audit fixture checker must be extended for new schema keywords")
    if "anyOf" in schema and not any(emitted_schema_accepts(value, branch) for branch in schema["anyOf"]):
        return False
    kind = schema.get("type")
    checks = {"object": lambda: isinstance(value, dict), "array": lambda: isinstance(value, list),
              "string": lambda: isinstance(value, str), "boolean": lambda: type(value) is bool,
              "number": lambda: type(value) in {int, float} and math.isfinite(value)}
    if kind is not None and (kind not in checks or not checks[kind]()):
        return False
    if "enum" in schema and value not in schema["enum"]:
        return False
    if kind == "object":
        properties = schema.get("properties", {})
        if not set(schema.get("required", [])).issubset(value):
            return False
        if schema.get("additionalProperties") is False and set(value) - set(properties):
            return False
        return all(emitted_schema_accepts(item, properties[key]) for key, item in value.items() if key in properties)
    if kind == "array":
        return len(value) >= schema.get("minItems", 0) and all(emitted_schema_accepts(item, schema["items"]) for item in value)
    return True


def run_case(case):
    provider = StaticProvider(Settings(model="SYNTHETIC_AUDIT_MODEL"), case.response)
    schema_compatible = emitted_schema_accepts(case.response, output_schema(case.checklist, [m["id"] for m in case.conversation["transcript"]]))
    if case.unsupported and not schema_compatible:
        raise AssertionError(f"{case.name}: the unsupported fixture must conform to the emitted provider-schema subset")
    feedback = []
    try:
        result = provider.assess_payload(evaluation_payload(provider.settings, case.conversation, case.checklist),
            case.conversation, case.checklist, lambda update, index=-1: feedback.append(update))
        outcome, detail = "accepted", score(case.checklist, result, [m["id"] for m in case.conversation["transcript"]])
    except EvaluationFailure as error:
        outcome, detail = "rejected", str(error)
    if outcome != case.expected:
        raise AssertionError(f"{case.name}: expected {case.expected}, observed {outcome}")
    return {"id": case.name, "family": case.family, "unsupported_probe": case.unsupported, "outcome": outcome,
            "reason": case.reason, "emitted_schema_subset_compatible": schema_compatible,
            "synthetic_response_reads": provider.reads, "result": detail,
            "repair_feedback": feedback}


def scale_precision_probe(seed):
    try:
        rubric = isolated(seed, "consultation", scale=[
            {"value": "0.10000000000000000001", "description": "SYNTHETIC anchor one"},
            {"value": "0.10000000000000000002", "description": "SYNTHETIC anchor two"}])
    except ValidationError:
        return {"checklist_configuration_accepted": False, "blocked_before_save": True,
                "limit": "Precision is constrained to the existing numeric evaluation representation; ordinary decimals remain supported."}
    conversation = transcript(("operator", "SYNTHETIC answer."))
    response = response_for(rubric, {"assessed_value": 0.1}, "SYNTHETIC allowed-wire-number candidate.")
    case = Case("TECH-SCALE", "Technical quality", rubric, conversation, response, "rejected", False,
                "Two valid Decimal scale anchors collapse to the same float and the decoded float matches neither stored anchor.")
    result = run_case(case)
    enum = output_schema(rubric)["properties"]["results"]["properties"]["consultation"]["properties"]["decision"]["anyOf"][0]["properties"]["assessed_value"]["enum"]
    return {"checklist_configuration_accepted": True, "stored_anchor_values": [str(a.value) for a in rubric.criteria[0].scale],
            "generated_numeric_enum": enum, "distinct_wire_values": len(set(enum)), "assessment_outcome": result["outcome"],
            "limit": "Unusual precision edge case, not an observed failure for the initial integer-anchor rubric."}


def memory_db():
    db = Database.__new__(Database)
    db.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(db.engine)
    db.sessions = sessionmaker(db.engine, expire_on_commit=False)
    return db


def insert_source(db, case, *, assessment=None):
    with db.transaction() as session:
        version = ChecklistVersion(snapshot=case.checklist.model_dump(mode="json"), content_hash=content_hash(case.checklist))
        conversation = Conversation(group_id="SYNTHETIC_AUDIT_ONLY", source_id=case.name, revision=1,
                                    content_hash=content_hash(case.conversation), snapshot=case.conversation)
        session.add_all([version, conversation]); session.flush()
        if assessment is not None:
            stored = assessment.model_dump(mode="json")
            calculated = score(case.checklist, assessment, [m["id"] for m in case.conversation["transcript"]])
            row = Evaluation(conversation_id=conversation.id, checklist_id=version.id, cache_key="SYNTHETIC_AUDIT_ONLY",
                             state="succeeded", completeness=calculated["completeness"], original=stored, effective=deepcopy(stored),
                             original_score=calculated, effective_score=deepcopy(calculated), meta={"mode": "TEST/MOCK"}, attempts=[])
            session.add(row); session.flush()
            return conversation.id, version.id, row.id
        return conversation.id, version.id, None


def review_probe(case):
    db = memory_db()
    replacement = decode_assessment(json.dumps(case.response), case.checklist)
    original = deepcopy(replacement)
    judgment = next(iter(original.results.values()))
    judgment.disposition, judgment.na_reason, judgment.review_reason = "assessed", None, None
    judgment.value = 0 if case.checklist.criteria[0].answer_type == "scale" else False
    judgment.explanation = "SYNTHETIC original retained for audit-path verification."
    _, _, eid = insert_source(db, case, assessment=original)
    with db.sessions() as session:
        before = session.get(Evaluation, eid)
        stamp, fingerprint = before.updated_at, content_hash(before.original)
    aid = submit_appeal(db, eid, case.checklist.criteria[0].id, "SYNTHETIC validation-boundary probe")
    rid = decide(db, aid, "replace", "SYNTHETIC reviewer override; no independent human adjudication.",
                 next(iter(replacement.results.values())), stamp)
    with db.sessions() as session:
        after = session.get(Evaluation, eid)
        result = {"case": case.name, "decision_saved": bool(rid), "original_preserved": fingerprint == content_hash(after.original),
                  "effective_total": after.effective_score["total"], "completeness": after.completeness}
    db.engine.dispose()
    return result


def job_probe(case):
    db = memory_db()
    cid, vid, _ = insert_source(db, case)
    settings = Settings(database_path=Path("UNUSED_MEMORY_ONLY"), api_key="sk-SYNTHETIC-NEVER-SENT", model="SYNTHETIC_AUDIT_MODEL",
                        budget_limit_usd=Decimal("1"), input_rate=Decimal("0"), output_rate=Decimal("0"), rate_source="SYNTHETIC ZERO RATE")
    provider = StaticProvider(settings, case.response)
    jobs = Jobs(db, settings, provider)
    # Exercise the real claim/evaluate/persist path synchronously, without worker races.
    jobs.submit = jobs.run
    eid = jobs.create([cid], vid, reuse_cache=False)[0]
    with db.sessions() as session:
        row = session.get(Evaluation, eid)
        result = {"case": case.name, "state": row.state, "mode": row.meta["mode"], "total": row.effective_score["total"],
                  "completeness": row.completeness, "synthetic_response_reads": provider.reads}
    jobs.close(); db.engine.dispose()
    if result["state"] != "succeeded":
        raise AssertionError("The synthetic unsupported judgment did not reach the saved-success boundary")
    return result


def open_readonly(path):
    connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only=ON")
    connection.execute("BEGIN")
    return connection


def fingerprint_db(path):
    connection = open_readonly(path)
    result = {}
    for table, in connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"):
        quoted = '"' + table.replace('"', '""') + '"'
        columns = list(connection.execute("PRAGMA table_info(" + quoted + ")"))
        order = ",".join(str(i + 1) for i in range(len(columns)))
        rows = [[{"bytes_hex": cell.hex()} if isinstance(cell, bytes) else cell for cell in row]
                for row in connection.execute("SELECT * FROM " + quoted + " ORDER BY " + order)]
        result[table] = {"rows": len(rows), "sha256": hashlib.sha256(canonical_json(rows).encode("utf-8")).hexdigest()}
    connection.close()
    return result


def scan_saved(path):
    connection = open_readonly(path)
    versions = {row["id"]: Checklist.model_validate(json.loads(row["snapshot"])) for row in connection.execute("SELECT * FROM checklist_versions")}
    sources = {row["id"]: dict(row) for row in connection.execute("SELECT * FROM conversation_revisions")}
    latest_source = {}
    for row in sorted(sources.values(), key=lambda row: row["revision"], reverse=True):
        latest_source.setdefault((row["group_id"], row["source_id"]), row["id"])
    selected = {}
    for row in connection.execute("SELECT * FROM evaluations WHERE checklist_id=1 AND state='succeeded' ORDER BY created_at DESC"):
        source = sources[row["conversation_id"]]
        if source["group_id"] == "DEV" and latest_source[(source["group_id"], source["source_id"])] == source["id"]:
            selected.setdefault(source["id"], row)
    totals, source_failures, metadata = Counter(), [], Counter()
    known_correction = []
    for row in selected.values():
        rubric = versions[row["checklist_id"]]
        source = sources[row["conversation_id"]]
        conversation = json.loads(source["snapshot"])
        ids = [m["id"] for m in conversation["transcript"]]
        metadata[json.loads(row["meta"]).get("prompt_version", "unknown")] += 1
        totals["complete" if row["completeness"] == "complete" else "needs_review"] += 1
        for basis in ("original", "effective"):
            assessment = Assessment.model_validate(json.loads(row[basis]))
            validate_assessment(rubric, assessment, ids)
            totals["structural_snapshots_valid"] += 1
            calculated = score(rubric, assessment, ids)
            if calculated != json.loads(row[basis + "_score"]):
                raise AssertionError("A saved snapshot failed exact deterministic recalculation")
            totals["score_snapshots_equal"] += 1
            try:
                validate_source_evidence(rubric, assessment, conversation)
                totals["narrow_source_guard_accepted"] += 1
            except ValueError as error:
                totals["narrow_source_guard_rejected"] += 1
                source_failures.append({"source_id": source["source_id"], "basis": basis, "reason": str(error)})
            if source["source_id"] == "p1-kz-012":
                known_correction.append({"basis": basis, "needs_disposition": assessment.results["needs"].disposition,
                    "consultation_value": assessment.results["consultation"].value, "total": calculated["total"], "validators_accept": True})
    connection.close()
    return {"selected_DEV_conversations": len(selected), "counts": dict(totals), "prompt_versions": dict(metadata),
            "source_guard_diagnostics": source_failures, "previously_corrected_saved_example": known_correction,
            "limit": "Validator acceptance is not independent semantic adjudication or a new model benchmark."}


def profile_history(path):
    """Time read endpoints on a RAM-only backup; amplify historical rows there."""
    import backend.app.main as app_module

    source = open_readonly(path)
    memory = sqlite3.connect(":memory:", check_same_thread=False)
    source.backup(memory)
    source.close()
    memory.row_factory = sqlite3.Row
    original_rows = list(memory.execute("SELECT * FROM evaluations"))
    db = Database.__new__(Database)
    db.engine = create_engine("sqlite://", creator=lambda: memory, poolclass=StaticPool)
    db.sessions = sessionmaker(db.engine, expire_on_commit=False)
    settings = Settings(database_path=Path("UNUSED_MEMORY_ONLY"), api_key="", model="",
                        budget_baseline_path=ROOT / "local_data/budget_baseline.json")
    with patch.object(app_module, "Database", lambda _: db):
        app = app_module.create_app(settings)
    queue = next(route.endpoint for route in app.routes if getattr(route, "path", "") == "/api/conversations")

    def timed(operation, trials=3):
        times = []
        for _ in range(trials):
            start = time.perf_counter()
            result = operation()
            times.append((time.perf_counter() - start) * 1000)
        return {"median_ms": round(statistics.median(times), 2), "min_ms": round(min(times), 2), "max_ms": round(max(times), 2)}, result

    budget, _ = timed(app.state.jobs.budget.status)
    baseline, result = timed(lambda: queue(checklist_id=1, latest_only=True, q="", speaker="all"))
    search, _ = timed(lambda: queue(checklist_id=1, latest_only=True, q="а", speaker="all"))
    profiles = [{"evaluation_rows": len(original_rows), "conversation_rows_returned": len(result), **baseline}]
    if original_rows:
        keys = original_rows[0].keys()
        insert = "INSERT INTO evaluations (" + ",".join('"' + key + '"' for key in keys) + ") VALUES (" + ",".join("?" for _ in keys) + ")"
        for factor in (5, 20):
            memory.execute("DELETE FROM evaluations WHERE id LIKE ?", ("BENCH_MEMORY_ONLY_%",))
            for copy in range(1, factor):
                copies = []
                for row in original_rows:
                    data = dict(row); data["id"] = f"BENCH_MEMORY_ONLY_{copy}_" + data["id"]
                    copies.append(tuple(data[key] for key in keys))
                memory.executemany(insert, copies)
            memory.commit()
            duration, result = timed(lambda: queue(checklist_id=1, latest_only=True, q="", speaker="all"))
            profiles.append({"evaluation_rows": len(original_rows) * factor, "conversation_rows_returned": len(result), **duration})
    app.state.jobs.close()
    db.engine.dispose()
    return {"queue_route_only": profiles, "current_literal_search": search, "current_budget_status": budget,
            "limit": "One machine, RAM-only historical duplicates, three trials each; excludes HTTP/serialization/DOM and is not a production capacity forecast."}


def protected_hashes():
    return {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in [ROOT / ".env", ROOT / "initial_checklist.json", ROOT / "config/initial_checklist.json", ROOT / "local_data/budget_baseline.json"]
            if path.is_file()}


def forbidden(*args, **kwargs):
    raise AssertionError("External network/provider request forbidden by the offline audit")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saved-db", type=Path)
    parser.add_argument("--profile-history", action="store_true", help="Profile current queue and RAM-only amplified history")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    saved_path = args.saved_db.resolve() if args.saved_db else None
    if saved_path and not saved_path.is_file():
        raise SystemExit("Saved database is missing; no empty replacement will be created")
    if args.profile_history and not saved_path:
        raise SystemExit("--profile-history requires --saved-db")
    seed = Checklist.model_validate_json((ROOT / "config/initial_checklist.json").read_text(encoding="utf-8"))
    files_before = protected_hashes()
    rows_before = fingerprint_db(saved_path) if saved_path else None
    targets = ["backend/app/domain.py", "backend/app/services/evaluator.py", "backend/app/services/scoring.py",
               "backend/app/services/reviews.py", "backend/app/services/jobs.py"]
    source_hashes = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in targets}
    with patch.object(Provider, "request", forbidden), patch.object(socket.socket, "connect", forbidden), patch.object(socket.socket, "connect_ex", forbidden):
        cases = cases_for(seed)
        results = [run_case(case) for case in cases]
        output = {"scope": "Synthetic boundary probes plus optional read-only saved-result verification", "outbound_requests": 0,
                  "source_sha256": source_hashes, "cases": results,
                  "summary": {"total_probes": len(results),
                              "unsupported_accepted": sum(r["unsupported_probe"] and r["outcome"] == "accepted" for r in results),
                              "unsupported_rejected": sum(r["unsupported_probe"] and r["outcome"] == "rejected" for r in results),
                              "control_checks": sum(not r["unsupported_probe"] for r in results)},
                  "synthetic_job_persistence": job_probe(next(c for c in cases if c.name == "CONS-01")),
                  "synthetic_reviewer_path": [review_probe(next(c for c in cases if c.name == name)) for name in ("NA-01", "CONS-01", "CTRL-01")],
                  "custom_scale_precision": scale_precision_probe(seed),
                  "saved_verification": scan_saved(saved_path) if saved_path else None,
                  "technical_profile": profile_history(saved_path) if args.profile_history else None}
    output["preservation"] = {"protected_files_equal": files_before == protected_hashes(),
                              "protected_file_sha256": files_before,
                              "saved_tables_equal": rows_before == fingerprint_db(saved_path) if saved_path else None,
                              "saved_table_fingerprints": rows_before,
                              "audited_sources_equal": source_hashes == {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in targets}}
    if not all(value is True for key, value in output["preservation"].items() if key.endswith("equal") and value is not None):
        raise AssertionError("A protected source or saved-result boundary changed during the audit")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"summary": output["summary"], "synthetic_job_persistence": output["synthetic_job_persistence"],
                      "synthetic_reviewer_path": output["synthetic_reviewer_path"], "saved_verification": output["saved_verification"],
                      "technical_profile": output["technical_profile"],
                      "preservation": {k: v for k, v in output["preservation"].items() if k.endswith("equal")},
                      "outbound_requests": 0}, ensure_ascii=False))


if __name__ == "__main__":
    main()
