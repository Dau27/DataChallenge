from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
import json
from typing import Any, Literal

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import Field, ValidationError, field_validator
from sqlalchemy import select

from backend.app.config import ROOT, Settings
from backend.app.db import AccessCheck, Appeal, ChecklistVersion, Conversation, Database, Evaluation, Review, now
from backend.app.domain import Checklist, Contract, ImportEnvelope, Judgment, Text, content_hash, nonblank
from backend.app.services.evaluator import EvaluationFailure, Provider, usage_summary
from backend.app.services.importer import fetch_organizer, import_payload
from backend.app.services.jobs import Jobs
from backend.app.services.reviews import decide, submit_appeal
from backend.app.services.budget import BudgetError, request_bound
from backend.app.services.checklists import preview_checklist
from backend.app.services.saved_results import SavedResultNotFound, compare_saved, evaluation_snapshot, summary, version_view
from backend.app.services.exports import csv_report, export_packet, json_report
from backend.app.services.search import search_messages


class OrganizerImport(Contract):
    group_id: str = Field(default="DEV", pattern=r"^[A-Za-z0-9_-]{1,128}$")


class EvaluationStart(Contract):
    conversation_ids: list[str] = Field(min_length=1, max_length=200)
    checklist_id: int = Field(gt=0)
    reuse_cache: bool = True

    @field_validator("conversation_ids")
    @classmethod
    def unique(cls, values):
        if len(values) != len(set(values)):
            raise ValueError("Duplicate conversation revision IDs")
        return values


class AppealRequest(Contract):
    criterion_id: Text
    comment: str = Field(min_length=1, max_length=10000)
    _text = field_validator("comment")(nonblank)


class DecisionRequest(Contract):
    action: Literal["confirm", "replace"]
    rationale: str = Field(min_length=1, max_length=10000)
    judgment: Judgment | None = None
    expected_updated_at: Text
    _text = field_validator("rationale")(nonblank)


class IdResponse(Contract):
    id: str


class ImportResponse(Contract):
    group_id: str
    actual_records: int
    created: int
    unchanged: int
    conversation_ids: list[str]
    languages: dict[str, int]
    channels: dict[str, int]


class ChecklistResponse(Contract):
    id: int
    content_hash: str
    snapshot: Checklist
    created_at: str


class EvaluationSummary(Contract):
    id: str
    conversation_id: str
    checklist_id: int
    state: Literal["queued", "running", "succeeded", "failed", "interrupted"]
    completeness: Literal["complete", "needs_review", "incomplete"]
    cached_from: str | None
    total: str | None
    error: str | None
    created_at: str
    updated_at: str


class ConversationResponse(Contract):
    id: str
    group_id: str
    source_id: str
    revision: int
    content_hash: str
    language: str
    channel: str
    message_count: int
    audio_available: bool
    evaluation: EvaluationSummary | None
    created_at: str
    pending_appeals: int = 0
    pending_review_targets: list[dict[str, str]] = Field(default_factory=list)
    critical_findings: list[dict[str, str]] = Field(default_factory=list)
    search_matches: list[dict[str, str]] = Field(default_factory=list)
    search_total_matches: int = 0


class ConversationDetail(Contract):
    id: str
    group_id: str
    source_id: str
    revision: int
    content_hash: str
    snapshot: dict[str, Any]
    evaluations: list[EvaluationSummary]


class EvaluationDetail(EvaluationSummary):
    original: dict[str, Any] | None
    original_score: dict[str, Any] | None
    effective: dict[str, Any] | None
    effective_score: dict[str, Any] | None
    checklist: ChecklistResponse
    metadata: dict[str, Any]
    attempts: list[dict[str, Any]]
    usage: dict[str, Any]
    appeals: list[dict[str, Any]]
    reviews: list[dict[str, Any]]


class JobStartResponse(Contract):
    evaluation_ids: list[str]


def create_app(settings=None, provider=None):
    settings = settings or Settings.from_env()
    settings.validate()
    db = Database(settings.database_path)
    jobs = Jobs(db, settings, provider)
    with db.transaction() as session:
        if session.scalar(select(ChecklistVersion.id).limit(1)) is None:
            seed = Checklist.model_validate_json((ROOT / "config/initial_checklist.json").read_text(encoding="utf-8"))
            session.add(ChecklistVersion(snapshot=seed.model_dump(mode="json"), content_hash=content_hash(seed)))

    @asynccontextmanager
    async def lifespan(app):
        jobs.recover()
        yield
        jobs.close()
        db.engine.dispose()

    app = FastAPI(title="Conversation Quality Analytics", version="0.1.0", lifespan=lifespan)
    app.state.db, app.state.jobs, app.state.settings = db, jobs, settings
    provider_identity = content_hash({"provider": "openai-responses", "model": settings.model, "credential": settings.api_key})
    with db.sessions() as session:
        last_check = session.get(AccessCheck, provider_identity)
        app.state.provider_check = last_check.report if last_check else None

    @app.middleware("http")
    async def local_write_boundary(request: Request, call_next):
        # UI and API use one origin (Vite proxies /api). No permissive CORS or external URL fetch input.
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            origin = request.headers.get("origin")
            if origin and origin not in {"http://127.0.0.1:8000", "http://localhost:8000", "http://127.0.0.1:5173", "http://localhost:5173"}:
                return JSONResponse(status_code=403, content={"detail": "Cross-origin write is not allowed"})
            try:
                if int(request.headers.get("content-length", "0")) > 25_000_000:
                    return JSONResponse(status_code=413, content={"detail": "JSON upload exceeds 25 MB safeguard"})
            except ValueError:
                return JSONResponse(status_code=400, content={"detail": "Invalid content length"})
        return await call_next(request)

    @app.exception_handler(RequestValidationError)
    async def request_invalid(_, error):
        # Pydantic's default includes source inputs. Keep transcripts and private URLs out of error responses.
        return JSONResponse(status_code=422, content={"detail": [
            {"location": list(item["loc"]), "message": item["msg"], "type": item["type"]} for item in error.errors()]})

    @app.exception_handler(ValidationError)
    async def domain_invalid(_, error):
        return JSONResponse(status_code=422, content={"detail": [
            {"location": list(item["loc"]), "message": item["msg"], "type": item["type"]} for item in error.errors()]})

    @app.exception_handler(ValueError)
    async def operation_invalid(_, error):
        return JSONResponse(status_code=422, content={"detail": str(error)})

    @app.exception_handler(SavedResultNotFound)
    async def saved_result_missing(_, error):
        return JSONResponse(status_code=404, content={"detail": str(error)})

    @app.exception_handler(BudgetError)
    async def spending_blocked(_, error):
        return JSONResponse(status_code=409, content={"detail": str(error), "code": "BUDGET_BLOCKED"})

    @app.get("/api/budget")
    def budget_status() -> dict[str, Any]:
        return jobs.budget.status()

    @app.get("/api/health")
    def health() -> dict[str, Any]:
        return {"status": "ok", "storage": "sqlite", "demo_roles": "anonymous; submission and review are separate actions"}

    @app.get("/api/access")
    def access() -> dict[str, Any]:
        result = settings.public_access()
        check = app.state.provider_check
        result["provider_verified"] = bool(check and check["succeeded"])
        if check and not check["succeeded"]:
            result["provider_status"] = check["error"]
        return {**result, "last_provider_check": check}

    @app.post("/api/access/check-provider")
    def check_provider() -> dict[str, Any]:
        if not settings.provider_ready:
            raise HTTPException(503, settings.public_access()["provider_status"])
        payload = {"model": settings.model, "input": "Return the structured access-check result with ok true.", "store": False,
                   "max_output_tokens": 2048,
                   "text": {"format": {"type": "json_schema", "name": "access_check", "strict": True,
                            "schema": {"type": "object", "properties": {"ok": {"type": "boolean"}}, "required": ["ok"], "additionalProperties": False}}}}
        with db.transaction() as session:
            reservation_id = jobs.budget.reserve(session, "access_check", provider_identity, request_bound(settings, payload), 2)
        record = jobs.budget.recorder(reservation_id)
        try:
            raw = jobs.provider.request(payload, record)
            if json.loads(raw) != {"ok": True}:
                raise EvaluationFailure("Provider did not return the expected structured access-check result")
            result = {"succeeded": True, "model": settings.model}
        except (EvaluationFailure, ValueError) as error:
            result = {"succeeded": False, "model": settings.model, "error": str(error)}
        except BaseException:
            jobs.budget.settle(reservation_id)
            raise
        from backend.app.db import BudgetReservation
        with db.sessions() as session:
            result["attempts"] = session.get(BudgetReservation, reservation_id).attempts
        result["checked_at"] = now()
        jobs.budget.settle(reservation_id, result)
        app.state.provider_check = result
        return result

    @app.post("/api/import/json", response_model=ImportResponse)
    def upload(envelope: ImportEnvelope):
        return import_payload(db, envelope)

    @app.post("/api/import/organizer", response_model=ImportResponse)
    def import_api(body: OrganizerImport):
        return import_payload(db, fetch_organizer(settings, body.group_id))

    @app.get("/api/checklists", response_model=list[ChecklistResponse])
    def checklists():
        with db.sessions() as session:
            return [version_view(v) for v in session.scalars(select(ChecklistVersion).order_by(ChecklistVersion.id.desc()))]

    @app.post("/api/checklists", response_model=ChecklistResponse, status_code=201)
    def save_checklist(body: Checklist):
        with db.transaction() as session:
            version = ChecklistVersion(snapshot=body.model_dump(mode="json"), content_hash=content_hash(body))
            session.add(version)
            session.flush()
            return version_view(version)

    @app.post("/api/checklists/{checklist_id}/preview")
    def checklist_preview(checklist_id: int, draft: dict[str, Any]) -> dict[str, Any]:
        with db.sessions() as session:
            version = session.get(ChecklistVersion, checklist_id)
            if version is None:
                raise HTTPException(404, "Saved checklist version not found")
            return preview_checklist(version.snapshot, draft)

    @app.get("/api/conversations", response_model=list[ConversationResponse])
    def conversations(checklist_id: int | None = None, latest_only: bool = True,
                      q: str = Query("", max_length=200), speaker: Literal["all", "operator", "client", "bot", "system"] = "all"):
        with db.read_snapshot() as session:
            records = list(session.scalars(select(Conversation).order_by(Conversation.group_id, Conversation.source_id, Conversation.revision.desc())))
            evaluations = list(session.scalars(select(Evaluation).order_by(Evaluation.created_at.desc())))
            versions = {v.id: {c["id"]: c for c in v.snapshot["criteria"]} for v in session.scalars(select(ChecklistVersion))}
            eligible = {e.id: e for e in evaluations if checklist_id is None or e.checklist_id == checklist_id}
            identities = {r.id: (r.group_id, r.source_id) for r in records}
            pending = {}
            for appeal in session.scalars(select(Appeal).where(Appeal.status == "open").order_by(Appeal.created_at)):
                e = eligible.get(appeal.evaluation_id)
                if e:
                    pending.setdefault(identities[e.conversation_id] if latest_only else e.conversation_id, []).append({"appeal_id": appeal.id,
                        "conversation_id": e.conversation_id, "evaluation_id": e.id,
                        "criterion_id": appeal.criterion_id, "criterion_name": versions[e.checklist_id][appeal.criterion_id]["name"]})
            latest = {}
            for evaluation in evaluations:
                if checklist_id is None or checklist_id == evaluation.checklist_id:
                    latest.setdefault(evaluation.conversation_id, evaluation)
            seen, items = set(), []
            for row in records:
                identity = (row.group_id, row.source_id)
                if latest_only and identity in seen:
                    continue
                seen.add(identity)
                matches, match_count = search_messages(row.snapshot["transcript"], q, speaker)
                if (q.strip() or speaker != "all") and not match_count:
                    continue
                evaluation = latest.get(row.id)
                flags = [{"evaluation_id": evaluation.id, "criterion_id": cid, "criterion_name": versions[evaluation.checklist_id][cid]["name"]}
                         for cid, value in (evaluation.effective_score or {}).get("flags", {}).items() if value is True] if evaluation else []
                items.append({"id": row.id, "group_id": row.group_id, "source_id": row.source_id, "revision": row.revision,
                              "content_hash": row.content_hash, "language": row.snapshot["language"], "channel": row.snapshot["channel"],
                              "message_count": len(row.snapshot["transcript"]), "audio_available": bool(row.snapshot["audio_url"]),
                              "evaluation": summary(evaluation) if evaluation else None, "created_at": row.created_at,
                              "pending_appeals": len(pending.get(identity if latest_only else row.id, [])),
                              "pending_review_targets": pending.get(identity if latest_only else row.id, []),
                              "critical_findings": flags, "search_matches": matches, "search_total_matches": match_count})
            return items

    @app.get("/api/conversations/{conversation_id}", response_model=ConversationDetail)
    def conversation_detail(conversation_id: str):
        with db.sessions() as session:
            row = session.get(Conversation, conversation_id)
            if not row:
                raise HTTPException(404, "Conversation revision not found")
            return {"id": row.id, "group_id": row.group_id, "source_id": row.source_id, "revision": row.revision,
                    "content_hash": row.content_hash, "snapshot": row.snapshot,
                    "evaluations": [summary(e) for e in session.scalars(select(Evaluation).where(Evaluation.conversation_id == row.id).order_by(Evaluation.created_at.desc()))]}

    @app.post("/api/evaluations", response_model=JobStartResponse, status_code=202)
    def start_evaluation(body: EvaluationStart):
        if not settings.provider_ready:
            raise HTTPException(503, settings.public_access()["provider_status"])
        return {"evaluation_ids": jobs.create(body.conversation_ids, body.checklist_id, body.reuse_cache)}

    @app.post("/api/evaluations/preview")
    def preview_evaluation(body: EvaluationStart) -> dict[str, Any]:
        return jobs.preview(body.conversation_ids, body.checklist_id, body.reuse_cache)

    @app.get("/api/evaluations", response_model=list[EvaluationSummary])
    def evaluations(conversation_id: str | None = None):
        with db.sessions() as session:
            query = select(Evaluation).order_by(Evaluation.created_at.desc())
            if conversation_id:
                query = query.where(Evaluation.conversation_id == conversation_id)
            return [summary(e) for e in session.scalars(query)]

    @app.get("/api/evaluations/compare")
    def compare_evaluations(left_id: str, right_id: str,
                            left_basis: Literal["original", "effective"] = "effective",
                            right_basis: Literal["original", "effective"] = "effective"):
        with db.read_snapshot() as session:
            return compare_saved(session, left_id, right_id, left_basis, right_basis)

    @app.get("/api/evaluations/{evaluation_id}", response_model=EvaluationDetail)
    def evaluation_detail(evaluation_id: str):
        with db.read_snapshot() as session:
            return evaluation_snapshot(session, evaluation_id)

    @app.get("/api/evaluations/{evaluation_id}/export")
    def export_evaluation(evaluation_id: str, format: Literal["json", "csv"] = "json", include_excerpts: bool = False):
        with db.read_snapshot() as session:
            packet = export_packet(session, evaluation_id, settings, include_excerpts)
        # Names come from the stored identifier; no caller-supplied path/header fragments.
        safe_id = "".join(c for c in packet["evaluation"]["id"] if c.isascii() and (c.isalnum() or c in "_-"))[:80] or "saved"
        return Response(json_report(packet) if format == "json" else csv_report(packet),
            media_type="application/json" if format == "json" else "text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="cqa-{safe_id}.{format}"', "Cache-Control": "no-store",
                     "X-Content-Type-Options": "nosniff"})

    @app.post("/api/evaluations/{evaluation_id}/retry", response_model=IdResponse, status_code=202)
    def retry(evaluation_id: str):
        jobs.retry(evaluation_id)
        return {"id": evaluation_id}

    @app.post("/api/evaluations/{evaluation_id}/appeals", response_model=IdResponse, status_code=201)
    def appeal(evaluation_id: str, body: AppealRequest):
        return {"id": submit_appeal(db, evaluation_id, body.criterion_id, body.comment)}

    @app.post("/api/appeals/{appeal_id}/decision", response_model=dict[str, int], status_code=201)
    def review(appeal_id: str, body: DecisionRequest):
        return {"id": decide(db, appeal_id, body.action, body.rationale, body.judgment, body.expected_updated_at)}

    dist = ROOT / "frontend/dist"
    if dist.is_dir():
        app.mount("/", StaticFiles(directory=dist, html=True), name="frontend")
    return app
