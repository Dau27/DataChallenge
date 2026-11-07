"""Saved-data inspection and deterministic simulation; never starts evaluations."""
from fastapi import APIRouter

from backend.app.api_breakdown import router as breakdown_router
from backend.app.api_priority import router as priority_router
from backend.app.api_weight_preview import router as weight_router
from backend.app.api_cohorts import router as cohorts_router

router = APIRouter()
router.include_router(breakdown_router)
router.include_router(priority_router)
router.include_router(weight_router)
router.include_router(cohorts_router)
