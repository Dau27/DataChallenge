"""New read-only cohort routes; mounted by the integration owner."""
from fastapi import APIRouter, Request, Response

from backend.app.services.cohort_comparison import CohortCompareRequest, cohort_options, compare_cohorts

router = APIRouter(prefix="/api/insights/cohorts")


@router.get("/options")
def options(request: Request, response: Response):
    response.headers["Cache-Control"] = "no-store"
    with request.app.state.db.read_snapshot() as session:
        return cohort_options(session)


@router.post("/compare")
def compare(body: CohortCompareRequest, request: Request, response: Response):
    response.headers["Cache-Control"] = "no-store"
    with request.app.state.db.read_snapshot() as session:
        return compare_cohorts(session, body)
