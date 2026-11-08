"""Read-only HTTP endpoints for deterministic, fixed-judgment scenarios."""
from typing import Any, Literal

from fastapi import APIRouter, Query, Request
from pydantic import Field, field_validator

from backend.app.domain import Contract
from backend.app.services.weight_preview import preview_runs, weight_preview

router = APIRouter(prefix="/api/insights/weight-preview", tags=["Saved insights"])


class WeightPreviewRequest(Contract):
    checklist_id: int = Field(gt=0)
    evaluation_id: str = Field(min_length=1, max_length=200)
    basis: Literal["original", "effective"] = "effective"
    draft: dict[str, Any]

    @field_validator("evaluation_id")
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError("Select a saved run")
        return value


@router.get("/runs")
def runs(request: Request, checklist_id: int = Query(..., gt=0), offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=200)):
    from fastapi.responses import JSONResponse
    with request.app.state.db.read_snapshot() as session:
        packet = preview_runs(session, checklist_id, offset, limit)
    return JSONResponse(packet, headers={"Cache-Control": "no-store"})


@router.post("")
def preview(request: Request, body: WeightPreviewRequest):
    from fastapi.responses import JSONResponse
    with request.app.state.db.read_snapshot() as session:
        packet = weight_preview(session, body.checklist_id, body.evaluation_id, body.basis, body.draft)
    return JSONResponse(packet, headers={"Cache-Control": "no-store"})
