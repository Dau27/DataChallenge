"""Synthetic regressions for narrow evidence checks; never hosted inference."""
from copy import deepcopy
from decimal import Decimal
import json

import httpx
import pytest
from pydantic import ValidationError

from backend.app.config import Settings
from backend.app.domain import Checklist, validate_assessment
from backend.app.services import evaluator
from backend.app.services.evaluator import validate_source_evidence
from backend.app.services.scoring import score
from backend.tests.conftest import full_assessment
from backend.tests.test_workflow import client_and_calls, evaluate_one, response_for, synthetic_payload


def source():
    return {"transcript": [
        {"id": "m0001", "speaker": "bot", "text": "Hello, I am a bot."},
        {"id": "m0002", "speaker": "operator", "text": "Hello, I am Alex. If you need anything else, contact us. Goodbye."},
        {"id": "m0003", "speaker": "client", "text": "Where is Reports?"},
        {"id": "m0004", "speaker": "operator", "text": "Open Reports."},
        {"id": "m0005", "speaker": "system", "text": "SYNTHETIC system event."}]}


@pytest.mark.parametrize("criterion_id", ["contact", "consultation", "closing", "critical_errors"])
@pytest.mark.parametrize("citation", ["m0001", "m0003", "m0005"])
def test_initial_positive_human_actions_cannot_use_only_nonoperator_citations(checklist, criterion_id, citation):
    assessment = full_assessment(checklist, message_id="m0002")
    judgment = assessment.results[criterion_id]
    if criterion_id == "critical_errors":
        judgment.value = True
    judgment.evidence[0].start_message_id = judgment.evidence[0].end_message_id = citation
    validate_assessment(checklist, assessment, [m["id"] for m in source()["transcript"]])
    with pytest.raises(ValueError, match=criterion_id + ": positive human-action"):
        validate_source_evidence(checklist, assessment, source())


def test_initial_contact_cites_the_first_human_turn_not_a_later_one(checklist):
    assessment = full_assessment(checklist, message_id="m0002")
    judgment = assessment.results["contact"]
    judgment.evidence[0].start_message_id = judgment.evidence[0].end_message_id = "m0004"
    with pytest.raises(ValueError, match="first human operator response"):
        validate_source_evidence(checklist, assessment, source())


@pytest.mark.parametrize("language", ["Hello, I am Alex. If you need anything else, contact us. Goodbye.",
    "Здравствуйте, я Анна. Если нужна дальнейшая помощь, обращайтесь. До свидания.",
    "Сәлеметсіз бе, мен Айым. Қосымша көмек керек болса, хабарласыңыз. Сау болыңыз."])
def test_supported_human_evidence_still_accepts_all_three_languages(checklist, language):
    conversation = source()
    conversation["transcript"][1]["text"] = language
    validate_source_evidence(checklist, full_assessment(checklist, message_id="m0002"), conversation)


def test_negative_absence_and_na_can_use_context_without_operator_credit(checklist):
    assessment = full_assessment(checklist, message_id="m0002")
    for cid in ("contact", "closing", "critical_errors", "consultation"):
        judgment = assessment.results[cid]
        judgment.value = 0 if cid == "consultation" else False
        judgment.evidence[0].start_message_id = judgment.evidence[0].end_message_id = "m0003"
        judgment.evidence[0].kind = "absence"
    needs = assessment.results["needs"]
    needs.disposition, needs.value, needs.na_reason = "not_applicable", None, "The initial customer request already supplies the required context."
    needs.evidence[0].start_message_id = needs.evidence[0].end_message_id = "m0003"
    validate_assessment(checklist, assessment, [m["id"] for m in source()["transcript"]])
    validate_source_evidence(checklist, assessment, source())


def test_positive_citation_can_include_client_context_in_the_same_ordered_range(checklist):
    assessment = full_assessment(checklist, message_id="m0002")
    evidence = assessment.results["consultation"].evidence[0]
    evidence.start_message_id, evidence.end_message_id, evidence.kind = "m0003", "m0004", "context"
    validate_source_evidence(checklist, assessment, source())


def test_definition_changes_disable_old_semantic_assumptions_but_id_renames_do_not(checklist):
    changed = deepcopy(checklist)
    changed.criteria[0].description = "Yes when the bot says hello; the human response is irrelevant for this custom rule."
    assessment = full_assessment(changed, message_id="m0002")
    assessment.results["contact"].evidence[0].start_message_id = assessment.results["contact"].evidence[0].end_message_id = "m0001"
    validate_source_evidence(changed, assessment, source())
    renamed = deepcopy(checklist)
    renamed.criteria[0].id = "custom_id"
    assessment = full_assessment(renamed, message_id="m0002")
    assessment.results["custom_id"].evidence[0].start_message_id = assessment.results["custom_id"].evidence[0].end_message_id = "m0001"
    with pytest.raises(ValueError, match="custom_id: positive human-action"):
        validate_source_evidence(renamed, assessment, source())


@pytest.mark.parametrize("reason", ["none", " /NONE/ ", "null", "N/A", "na", "not applicable", "\u00a0none\u00a0"])
def test_placeholder_na_reasons_cannot_remove_weight(checklist, reason):
    assessment = full_assessment(checklist)
    needs = assessment.results["needs"]
    needs.disposition, needs.value, needs.na_reason = "not_applicable", None, reason
    with pytest.raises(ValueError, match="placeholder is not an N/A"):
        score(checklist, assessment)


@pytest.mark.parametrize("value", ["0.10000000000000000001", "9007199254740993", "1e400"])
def test_unrepresentable_scale_anchors_rejected_before_saved_configuration(checklist, value):
    data = checklist.model_dump(mode="json")
    data["criteria"][3]["scale"][0]["value"] = value
    with pytest.raises(ValidationError, match="Scale anchor precision"):
        Checklist.model_validate(data)


def test_decimal_anchors_round_trip_through_provider_schema_and_decoder(checklist):
    data = checklist.model_dump(mode="json")
    data["criteria"][3]["scale"] = [{"value": "0.1", "description": "partial"}, {"value": "0.2", "description": "complete"}]
    rubric = Checklist.model_validate(data)
    assessment = full_assessment(rubric)
    assessment.results["consultation"].value = .1
    decoded = evaluator.decode_assessment(response_for(assessment.model_dump(mode="json"))["output"][0]["content"][0]["text"], rubric)
    assert score(rubric, decoded)["total"] == "90.00"
    enum = evaluator.output_schema(rubric)["properties"]["results"]["properties"]["consultation"]["properties"]["decision"]["anyOf"][0]["properties"]["assessed_value"]["enum"]
    assert enum == [.1, .2]


def test_precision_preview_and_save_errors_do_not_create_a_version(tmp_path):
    client, _, _ = client_and_calls(tmp_path, budget_limit_usd=Decimal(0))
    with client:
        before = client.get('/api/checklists').json()
        draft = deepcopy(before[0]['snapshot'])
        draft['criteria'][3]['scale'][0]['value'] = '0.10000000000000000001'
        preview = client.post('/api/checklists/1/preview', json=draft).json()
        assert preview['valid'] is False
        assert any(issue['location'] == ['criteria', 3, 'scale', 0, 'value'] for issue in preview['errors'])
        assert client.post('/api/checklists', json=draft).status_code == 422
        assert client.get('/api/checklists').json() == before


def test_guard_version_invalidates_old_cache_without_altering_the_rubric(checklist, monkeypatch):
    settings = Settings(model="SYNTHETIC_MODEL")
    before = checklist.model_dump(mode="json")
    new_key = evaluator.cache_key('SYNTHETIC_SOURCE_HASH', checklist, settings)
    monkeypatch.setattr(evaluator, 'EVIDENCE_VALIDATION_VERSION', 'source-closing-courtesy-v1')
    assert new_key != evaluator.cache_key('SYNTHETIC_SOURCE_HASH', checklist, settings)
    assert checklist.model_dump(mode="json") == before


@pytest.mark.parametrize("repair", [True, False])
def test_unsupported_human_citation_repairs_once_or_fails_without_saved_judgment(tmp_path, repair):
    count = 0
    def handler(payload):
        nonlocal count
        count += 1
        rubric = Checklist.model_validate(json.loads(payload['input'])['saved_checklist'])
        result = full_assessment(rubric, message_id='m0002').model_dump(mode='json')
        if count == 1 or not repair:
            result['results']['contact']['evidence'][0].update(start_message_id='m0001', end_message_id='m0001')
        return httpx.Response(200, json=response_for(result))
    client, calls, _ = client_and_calls(tmp_path, handler)
    with client:
        imported = client.post('/api/import/json', json=synthetic_payload()).json()
        result = evaluate_one(client, imported['conversation_ids'][0])
        assert count == len(calls) == 2
        assert 'positive human-action' in result['attempts'][0]['validation_error']
        assert result['state'] == ('succeeded' if repair else 'failed')
        assert (result['original'] is not None) is repair
