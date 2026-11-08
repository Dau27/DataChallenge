"""Synthetic source/answer conflicts representing all 16 reviewed error patterns.

No real transcripts, reviewer answers, account credentials or provider calls.
These test rejection/repair, not hosted model semantic accuracy.
"""
from copy import deepcopy
import json

import httpx
import pytest

from backend.app.domain import Checklist
from backend.app.services.evaluator import output_schema
from backend.app.services.rubric_guards import validate_initial_rubric
from backend.tests.conftest import full_assessment
from backend.tests.test_workflow import client_and_calls, evaluate_one, response_for, synthetic_payload


def conversation(*turns):
    return {"transcript": [{"id": f"m{i:04}", "speaker": role, "text": text}
                           for i, (role, text) in enumerate(turns, 1)]}


SITE = conversation(("client", "I cannot sign in; several tabs are open."),
                    ("operator", "Which site are you using?"), ("client", "The company website."))
CURRENCY = conversation(("client", "Аударым жасағым келеді."),
                        ("operator", "Қай валютамен?"), ("client", "Еуромен."))
VAGUE = conversation(("operator", "Use the other one."), ("client", "Which other one? What address?"))
WRONG = conversation(("operator", "Тикерді қараудың қажеті жоқ. Өтінім қабылданбаса, ол міндетті түрде орындалып қойған."),
                     ("client", "Орындалды дегеніңіз қалай?"))
DISCLOSURE = conversation(("operator", "На вашем счёте действует ограничение на вывод."),
                          ("client", "Я ещё не подтверждал личность."))

# Each row isolates a criterion, so one failure cannot mask another correction.
CASES = [
    ("needs", None, True, SITE, "Initial context sufficient"),
    ("dialogue_management", 10, 4, VAGUE, "Responses clear"),
    ("closing", False, True, conversation(("client", "That worked."), ("operator", "Glad you got in. Have a good day!")), "Only gladness"),
    ("needs", None, True, CURRENCY, "Initial context sufficient"),
    ("closing", True, False, conversation(("operator", "Open the bank details and choose the currency."),
        ("client", "Thanks."), ("operator", "Көмегім тигеніне қуаныштымын. Сау болыңыз!")), "Implicit help offer"),
    ("needs", None, False, WRONG, "The topic is clear"),
    ("consultation", 10, 0, WRONG, "Definitive recommendation"),
    ("dialogue_management", 10, 4, WRONG, "Responses clear"),
    ("consultation", 10, 20, conversation(("client", "Which account buys shares?"),
        ("operator", "Use the trading account."), ("client", "Understood.")), "The question was answered, but a later personal money transfer bypassing the company is inappropriate"),
    ("needs", None, True, conversation(("operator", "Қалай көмектесе аламын?"),
        ("system", "Клиент сұрағын жазбай тұрып, чаттан шықты.")), "No request"),
    ("consultation", 20, 15, conversation(("client", "Where is the plan, and what is the report section called?"),
        ("operator", "Open Profile for the plan."), ("client", "I will look at the report later.")), "Второй вопрос не был раскрыт, но клиент посмотрит позже"),
    ("dialogue_management", 10, 4, conversation(("operator", "Use the same update menu."),
        ("client", "Я про вывод спрашиваю.")), "Clear"),
    ("closing", False, True, conversation(("operator", "Пока дополнительных действий от вас не нужно. Спасибо, до свидания!")), "No recap"),
    ("identification", None, False, DISCLOSURE, "Only app navigation"),
    ("dialogue_management", 7, 4, conversation(("operator", "Там оно стоит, через тот раздел."),
        ("client", "Что стоит? И через какой раздел?")), "One disruption"),
    ("critical_errors", False, True, DISCLOSURE, "No disclosure"),
]


def isolated(checklist, criterion_id, value, explanation):
    rubric = deepcopy(checklist)
    rubric.criteria = [next(c for c in rubric.criteria if c.id == criterion_id)]
    assessment = full_assessment(rubric)
    judgment = assessment.results[criterion_id]
    judgment.explanation = explanation
    if value is None:
        judgment.disposition, judgment.value, judgment.na_reason = "not_applicable", None, "Initially sufficient"
    else:
        judgment.value = value
    return rubric, assessment


@pytest.mark.parametrize("criterion,bad,good,source,reason", CASES)
def test_all_reviewed_error_families_reject_conflicts_and_accept_repairs(checklist, criterion, bad, good, source, reason):
    rubric, assessment = isolated(checklist, criterion, bad, reason)
    with pytest.raises(ValueError, match=criterion + ":"):
        validate_initial_rubric(rubric, assessment, source)
    assessment.results[criterion].disposition = "assessed"
    assessment.results[criterion].na_reason = None
    assessment.results[criterion].value = good
    assessment.results[criterion].explanation = "The observed action matches the selected anchor; unrelated violations are separate."
    validate_initial_rubric(rubric, assessment, source)


@pytest.mark.parametrize("change", ["description", "na", "anchors"])
def test_semantic_guard_respects_changed_definitions_conditions_and_anchors(checklist, change):
    criterion, bad, _, source, reason = CASES[0 if change != "anchors" else 1]
    rubric, assessment = isolated(checklist, criterion, bad, reason)
    selected = rubric.criteria[0]
    if change == "description": selected.description = "A different custom definition."
    elif change == "na": selected.na_condition = "N/A if a question is asked."
    else: selected.scale[0].description = "A different maximum anchor."
    validate_initial_rubric(rubric, assessment, source)


def test_renaming_and_weight_changes_do_not_hide_a_source_conflict(checklist):
    rubric, assessment = isolated(checklist, "needs", None, "Initially sufficient")
    rubric.criteria[0].id, rubric.criteria[0].weight = "renamed", 1
    assessment.results["renamed"] = assessment.results.pop("needs")
    with pytest.raises(ValueError, match="renamed:"):
        validate_initial_rubric(rubric, assessment, SITE)


@pytest.mark.parametrize("source", [
    conversation(("client", "I use the company website."), ("operator", "Which site?"), ("client", "The company website.")),
    conversation(("client", "EUR transfer."), ("operator", "Which currency?"), ("client", "Euros.")),
    conversation(("operator", "Open Reports."), ("client", "Where is the export button?")),
    conversation(("system", "Identity confirmed."), *[(m["speaker"], m["text"]) for m in DISCLOSURE["transcript"]]),
    conversation(("operator", "Verification is required before we check your account. Please use general help meanwhile.")),
])
def test_redundant_questions_new_followups_verified_and_future_checks_do_not_trigger(checklist, source):
    for criterion, value in [("needs", None), ("dialogue_management", 10), ("identification", True), ("critical_errors", False)]:
        rubric, assessment = isolated(checklist, criterion, value, "No contradiction")
        validate_initial_rubric(rubric, assessment, source)


@pytest.mark.parametrize("reason", ["All requests answered; no unanswered questions.", "No customer request is unanswered."])
def test_no_unanswered_questions_is_not_a_gap(checklist, reason):
    rubric, assessment = isolated(checklist, "consultation", 20, reason)
    validate_initial_rubric(rubric, assessment, SITE)


@pytest.mark.parametrize("text", ["A rejected order does not necessarily mean it executed.",
    "Rejected does not always mean executed.", "The rejected order was later actually executed after resubmission.",
    "Өтінім қабылданбаса, ол міндетті түрде орындалып қойған емес."])
def test_negated_or_later_changed_status_is_not_an_incorrect_key_recommendation(checklist, text):
    rubric, assessment = isolated(checklist, "consultation", 20, "Correct explanation")
    validate_initial_rubric(rubric, assessment, conversation(("operator", text)))


def test_observations_precede_applicability_in_wire_schema(checklist):
    fields = output_schema(checklist)["properties"]["results"]["properties"]["needs"]["properties"]
    assert list(fields) == ["evidence", "explanation", "na_condition_met", "decision"]


def test_one_repair_receives_multiple_conflicts_together(checklist):
    assessment = full_assessment(checklist)
    assessment.results["identification"].disposition = "not_applicable"
    assessment.results["identification"].value = None
    assessment.results["identification"].na_reason = "Only general guidance"
    source = deepcopy(DISCLOSURE)
    source["transcript"].extend([
        {"id": "m0003", "speaker": "operator", "text": "Use the other one."},
        {"id": "m0004", "speaker": "client", "text": "Which other one?"},
    ])
    with pytest.raises(ValueError) as error:
        validate_initial_rubric(checklist, assessment, source)
    assert all(name + ":" in str(error.value) for name in ["identification", "dialogue_management", "critical_errors"])
    assert len(str(error.value)) < 1500  # Fits the existing bounded repair feedback.


@pytest.mark.parametrize("repair", [True, False])
def test_new_source_conflict_uses_one_repair_or_withholds_saved_judgment(tmp_path, repair):
    count = 0
    def handler(payload):
        nonlocal count
        count += 1
        rubric = Checklist.model_validate(json.loads(payload["input"])["saved_checklist"])
        result = full_assessment(rubric, message_id="m0002").model_dump(mode="json")
        result["results"]["closing"]["value"] = False
        result["results"]["dialogue_management"]["value"] = 4 if repair and count == 2 else 10
        return httpx.Response(200, json=response_for(result))
    client, calls, _ = client_and_calls(tmp_path, handler)
    with client:
        payload = synthetic_payload()
        turns = payload["data"]["records"][0]["transcript"]
        turns[1]["text"] = "Hello, I am Alex. Use the other one."
        turns.append({"timestamp": "00:01", "speaker": "client", "text": "Which other one? What address?"})
        imported = client.post("/api/import/json", json=payload).json()
        result = evaluate_one(client, imported["conversation_ids"][0])
        assert len(calls) == count == 2
        assert "re-asks" in result["attempts"][0]["validation_error"]
        assert result["state"] == ("succeeded" if repair else "failed")
        assert (result["original"] is not None) is repair
