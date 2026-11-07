from copy import deepcopy
from decimal import Decimal

import pytest
from pydantic import ValidationError

from backend.app.domain import Assessment, Checklist
from backend.app.services.scoring import score


def test_full(checklist, assessment):
    result = score(checklist, assessment, ["m0001"])
    assert result["total"] == "100.00"
    assert result["sections"][-1]["total"] is None


def test_zero(checklist, assessment):
    for criterion in checklist.criteria:
        assessment.results[criterion.id].value = 0 if criterion.answer_type == "scale" else False
    assert score(checklist, assessment)["total"] == "0.00"


def test_dialogue_normalization(checklist, assessment):
    assessment.results["dialogue_management"].value = 7
    result = score(checklist, assessment)
    assert result["total"] == "95.50"
    assert next(r for r in result["criteria"] if r["criterion_id"] == "dialogue_management")["raw_points"] == "10.5"


def make_na(judgment):
    judgment.disposition = "not_applicable"
    judgment.value = None
    judgment.na_reason = "SYNTHETIC: exact applicability condition holds"


def test_na_60_over_80(checklist, assessment):
    make_na(assessment.results["identification"])
    assessment.results["consultation"].value = 0
    result = score(checklist, assessment)
    assert Decimal(result["raw_subtotal"]) == Decimal(60)
    assert result["applicable_weight"] == "80"
    assert result["total"] == "75.00"


def test_flag_never_changes_score(checklist, assessment):
    before = score(checklist, assessment)
    assessment.results["critical_errors"].value = True
    after = score(checklist, assessment)
    assert before["total"] == after["total"]
    assert after["flags"]["critical_errors"] is True


def test_no_positive_weight(checklist, assessment):
    for criterion in checklist.criteria:
        if criterion.weight is not None:
            criterion.weight = Decimal(0)
    result = score(checklist, assessment)
    assert result["total"] is None
    assert result["reason"] == "NO_APPLICABLE_SCORED_WEIGHT"


def test_unresolved_is_not_na(checklist, assessment):
    judgment = assessment.results["consultation"]
    judgment.disposition = "needs_review"
    judgment.value = None
    judgment.review_reason = "Authoritative fee schedule unavailable"
    result = score(checklist, assessment)
    assert result["total"] is None
    assert result["applicable_weight"] == "100"
    assert result["reason"] == "UNRESOLVED_CRITERIA"


@pytest.mark.parametrize("reason", ["none", "/none/", "N/A", "null", "not applicable"])
def test_placeholder_cannot_justify_uncertainty(checklist, assessment, reason):
    judgment = assessment.results["contact"]
    judgment.disposition, judgment.value, judgment.review_reason = "needs_review", None, reason
    with pytest.raises(ValueError, match="placeholder"):
        score(checklist, assessment)


@pytest.mark.parametrize("kind", ["missing", "extra", "na", "scale", "bool_scale", "number_binary", "evidence", "reversed", "empty_reason"])
def test_invalid_answers_cannot_complete(checklist, assessment, kind):
    if kind == "missing": del assessment.results["contact"]
    if kind == "extra": assessment.results["invented"] = assessment.results["contact"]
    if kind == "na": make_na(assessment.results["contact"])
    if kind == "scale": assessment.results["dialogue_management"].value = 8
    if kind == "bool_scale": assessment.results["dialogue_management"].value = True
    if kind == "number_binary": assessment.results["contact"].value = 1
    if kind == "evidence": assessment.results["contact"].evidence[0].start_message_id = "fabricated"
    if kind == "reversed":
        assessment.results["contact"].evidence[0].start_message_id = "m0002"
        assessment.results["contact"].evidence[0].end_message_id = "m0001"
    if kind == "empty_reason":
        make_na(assessment.results["needs"])
        assessment.results["needs"].na_reason = " "
    with pytest.raises(ValueError): score(checklist, assessment, ["m0001", "m0002"])


@pytest.mark.parametrize("kind", ["duplicate_id", "duplicate_section", "negative_weight", "nan", "duplicate_anchor", "zero_max", "negative_anchor", "boolean_anchor", "no_na_condition", "scored_flag", "binary_anchors", "unknown_section", "unknown_policy"])
def test_invalid_configuration(checklist, kind):
    data = checklist.model_dump(mode="json")
    if kind == "duplicate_id": data["criteria"][1]["id"] = "contact"
    if kind == "duplicate_section": data["sections"].append(data["sections"][0])
    if kind == "negative_weight": data["criteria"][0]["weight"] = -1
    if kind == "nan": data["criteria"][0]["weight"] = "NaN"
    if kind == "duplicate_anchor": data["criteria"][3]["scale"].append(data["criteria"][3]["scale"][0])
    if kind == "zero_max": data["criteria"][3]["scale"] = [{"value": 0, "description": "zero"}]
    if kind == "negative_anchor": data["criteria"][3]["scale"][0]["value"] = -1
    if kind == "boolean_anchor": data["criteria"][3]["scale"][0]["value"] = True
    if kind == "no_na_condition": data["criteria"][1]["na_condition"] = " "
    if kind == "scored_flag": data["criteria"][-1]["weight"] = 5
    if kind == "binary_anchors": data["criteria"][0]["scale"] = [{"value": 1, "description": "one"}]
    if kind == "unknown_section": data["criteria"][0]["section_id"] = "invented"
    if kind == "unknown_policy": data["scoring_policy"]["scale_normalization"] = "min_max"
    with pytest.raises(ValidationError): Checklist.model_validate(data)


def test_nonzero_minimum_divides_by_maximum(checklist, assessment):
    criterion = checklist.criteria[3]
    criterion.scale = [a for a in criterion.scale if a.value in [10, 20]]
    assessment.results[criterion.id].value = 10
    assert score(checklist, assessment)["total"] == "90.00"


def test_decimal_tie_half_up(checklist, assessment):
    # 1/32 * 100 = 3.125 -> 3.13, with no early rounding.
    checklist.criteria = checklist.criteria[:2]
    checklist.criteria[0].weight = Decimal(1)
    checklist.criteria[1].weight = Decimal(31)
    assessment.results = {key: assessment.results[key] for key in ["contact", "needs"]}
    assessment.results["needs"].value = False
    assert score(checklist, assessment)["total"] == "3.13"


def test_global_score_is_not_unweighted_section_average(checklist, assessment):
    assessment.results["contact"].value = False
    assert score(checklist, assessment)["total"] == "90.00"
