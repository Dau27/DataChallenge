import json
from pathlib import Path

import pytest
import httpx


@pytest.fixture(autouse=True)
def no_live_model_http(monkeypatch):
    original = httpx.HTTPTransport.handle_request
    def guarded(transport, request):
        if request.url.host == "api.openai.com":
            raise AssertionError("Real model HTTP is forbidden in the ordinary test suite")
        return original(transport, request)
    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", guarded)

from backend.app.domain import Assessment, Checklist


@pytest.fixture
def checklist():
    return Checklist.model_validate_json(Path("config/initial_checklist.json").read_text(encoding="utf-8"))


def full_assessment(checklist, message_id="m0001"):
    return Assessment.model_validate({"results": {
        c.id: {"disposition": "assessed", "value": float(max(a.value for a in c.scale)) if c.answer_type == "scale" else c.answer_type != "flag",
               "explanation": "SYNTHETIC test judgment", "na_reason": None, "review_reason": None,
               "evidence": [{"kind": "support", "start_message_id": message_id, "end_message_id": message_id}]}
        for c in checklist.criteria}})


@pytest.fixture
def assessment(checklist):
    return full_assessment(checklist)
