"""Read-only criterion breakdown requests."""
from typing import Literal

from fastapi import APIRouter, Request, Response

from backend.app.services.insights_common import SavedScope
from backend.app.services.criterion_breakdown import criterion_breakdown

router = APIRouter()


class BreakdownRequest(SavedScope):
    basis: Literal["original", "effective"] = "effective"


@router.post("/api/insights/breakdown")
def breakdown(body: BreakdownRequest, request: Request, response: Response):
    response.headers["Cache-Control"] = "no-store"
    with request.app.state.db.read_snapshot() as session:
        return criterion_breakdown(session, body.checklist_id, body.conversation_ids, body.basis)
