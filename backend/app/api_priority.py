from fastapi import APIRouter, Request, Response

from backend.app.services.insights_common import SavedScope
from backend.app.services.review_priority import review_priority

router = APIRouter()


@router.post("/api/insights/review-priority")
def saved_review_priority(body: SavedScope, request: Request, response: Response):
    response.headers["Cache-Control"] = "no-store"
    with request.app.state.db.read_snapshot() as session:
        return review_priority(session, body.checklist_id, body.conversation_ids)
