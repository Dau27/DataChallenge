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
from backend.app.api_history import HistoryNavigation, evaluation_history_page, router as history_router
from backend.app.limits import IMPORT_BYTE_LIMIT, RequestBodyLimit
from backend.app.db import AccessCheck, ChecklistVersion, Conversation, Database, now
from backend.app.domain import Checklist, Contract, ImportEnvelope, Judgment, Text, content_hash, nonblank
from backend.app.services.evaluator import EvaluationFailure, Provider, usage_summary
from backend.app.services.importer import fetch_organizer, import_payload
from backend.app.services.jobs import Jobs
from backend.app.services.reviews import decide, submit_appeal
from backend.app.services.budget import BudgetError, request_bound
from backend.app.services.checklists import preview_checklist
from backend.app.services.saved_results import SavedResultNotFound, compare_saved, evaluation_snapshot, saved_summaries, source_view, version_view
from backend.app.services.queue import conversation_queue
from backend.app.services.exports import batch_csv_report, csv_report, export_batch, export_packet, json_report, simple_csv_report
from backend.app.services.transcript_index import indexed_message_page
from backend.app.insights_api import router as insights_router


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


class SearchHighlight(Contract):
    start: int = Field(ge=0)
    end: int = Field(ge=0)


class SearchMatch(Contract):
    id: str
    speaker: str
    timestamp: str
    snippet: str
    highlights: list[SearchHighlight] = Field(default_factory=list)


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
    search_matches: list[SearchMatch] = Field(default_factory=list)
    search_total_matches: int = 0


class ConversationDetail(Contract):
    id: str
    group_id: str
    source_id: str
    revision: int
    content_hash: str
    snapshot: dict[str, Any]
    evaluations: list[EvaluationSummary]


class PagedConversationDetail(ConversationDetail):
    history_page: HistoryNavigation


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
    app.include_router(history_router)
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
        return await call_next(request)

    # The byte boundary runs before parsers and the HTTP dispatch middleware; an
    # interrupted upload never reaches an endpoint or causes a missing-response error.
    app.add_middleware(RequestBodyLimit, max_bytes=IMPORT_BYTE_LIMIT)

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
            return conversation_queue(session, checklist_id, latest_only, q, speaker)

    @app.get("/api/conversations/{conversation_id}", response_model=ConversationDetail | PagedConversationDetail)
    def conversation_detail(conversation_id: str, history_limit: int | None = Query(None, ge=1, le=100),
                            history_cursor: str | None = Query(None, min_length=1, max_length=2048)):
        with db.read_snapshot() as session:
            row = session.get(Conversation, conversation_id)
            if not row:
                raise HTTPException(404, "Conversation revision not found")
            result = {"id": row.id, "group_id": row.group_id, "source_id": row.source_id, "revision": row.revision,
                    "content_hash": row.content_hash, "snapshot": row.snapshot,
                    "evaluations": []}
            if history_limit is not None:
                page = evaluation_history_page(session, row.id, history_limit, history_cursor)
                result['evaluations'] = page.pop('items')
                page.pop('source')
                result['history_page'] = page
            else:
                if history_cursor:
                    raise ValueError('history_limit is required when using a history cursor')
                result['evaluations'] = saved_summaries(session, row.id)
            return result

    @app.get("/api/conversations/{conversation_id}/matches")
    def conversation_matches(conversation_id: str, q: str = Query("", max_length=200),
                             speaker: Literal["all", "operator", "client", "bot", "system"] = "all",
                             offset: int = Query(0, ge=0, le=1000000), limit: int = Query(5, ge=1, le=25)):
        with db.read_snapshot() as session:
            row = session.get(Conversation, conversation_id)
            if not row:
                raise HTTPException(404, "Conversation revision not found")
            matches, total = indexed_message_page(session, row, q, speaker, limit=limit, offset=offset)
            return {"source": source_view(row), "query": q.strip(), "speaker": speaker, "offset": offset,
                    "limit": limit, "total_matches": total, "matches": matches}

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
            return saved_summaries(session, conversation_id)

    @app.get("/api/evaluations/compare")
    def compare_evaluations(left_id: str, right_id: str,
                            left_basis: Literal["original", "effective"] = "effective",
                            right_basis: Literal["original", "effective"] = "effective"):
        with db.read_snapshot() as session:
            return compare_saved(session, left_id, right_id, left_basis, right_basis)

    @app.get("/api/evaluations/export-batch")
    def export_selected_evaluations(evaluation_id: list[str] = Query(...),
                                    format: Literal["json", "csv", "simple_csv"] = "json", include_excerpts: bool = False):
        with db.read_snapshot() as session:
            packet = export_batch(session, evaluation_id, settings, include_excerpts)
        serializer = json_report if format == "json" else simple_csv_report if format == "simple_csv" else batch_csv_report
        filename = "cqa-selected-criteria.csv" if format == "simple_csv" else f"cqa-selected.{format}"
        return Response(serializer(packet), media_type="application/json" if format == "json" else "text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{filename}"', "Cache-Control": "no-store",
                     "X-Content-Type-Options": "nosniff"})

    @app.get("/api/evaluations/{evaluation_id}", response_model=EvaluationDetail)
    def evaluation_detail(evaluation_id: str):
        with db.read_snapshot() as session:
            return evaluation_snapshot(session, evaluation_id)

    @app.get("/api/evaluations/{evaluation_id}/export")
    def export_evaluation(evaluation_id: str, format: Literal["json", "csv", "simple_csv"] = "json", include_excerpts: bool = False):
        with db.read_snapshot() as session:
            packet = export_packet(session, evaluation_id, settings, include_excerpts)
        # Names come from the stored identifier; no caller-supplied path/header fragments.
        safe_id = "".join(c for c in packet["evaluation"]["id"] if c.isascii() and (c.isalnum() or c in "_-"))[:80] or "saved"
        serializer = json_report if format == "json" else simple_csv_report if format == "simple_csv" else csv_report
        filename = f"cqa-{safe_id}-criteria.csv" if format == "simple_csv" else f"cqa-{safe_id}.{format}"
        return Response(serializer(packet),
            media_type="application/json" if format == "json" else "text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{filename}"', "Cache-Control": "no-store",
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

    app.include_router(insights_router)
    dist = ROOT / "frontend/dist"
    if dist.is_dir():
        app.mount("/", StaticFiles(directory=dist, html=True), name="frontend")
    return app
