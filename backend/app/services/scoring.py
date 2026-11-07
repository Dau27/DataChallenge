"""Decimal arithmetic only; the provider never supplies a total."""
from decimal import Decimal, ROUND_HALF_UP, localcontext

from backend.app.domain import Assessment, Checklist, validate_assessment

SCORING_VERSION = "decimal-global-weights-half-up-v1"


def score(checklist: Checklist, assessment: Assessment, message_ids: list[str] | None = None) -> dict:
    validate_assessment(checklist, assessment, message_ids)
    with localcontext() as context:
        context.prec = 50
        rows = []
        unresolved = []
        for criterion in checklist.criteria:
            judgment = assessment.results[criterion.id]
            applicable = criterion.answer_type != "flag" and judgment.disposition != "not_applicable"
            weight = criterion.weight or Decimal(0)
            points = None
            if judgment.disposition == "needs_review":
                unresolved.append(criterion.id)
            elif applicable:
                fraction = (Decimal(str(judgment.value)) / max(a.value for a in criterion.scale)
                            if criterion.answer_type == "scale" else Decimal(int(judgment.value)))
                points = weight * fraction
            rows.append({"criterion_id": criterion.id, "section_id": criterion.section_id,
                         "weight": str(criterion.weight) if criterion.weight is not None else None,
                         "applicable": applicable, "raw_points": str(points) if points is not None else None})

        def aggregate(selected, pending):
            denominator = sum((Decimal(r["weight"]) for r in selected if r["applicable"]), Decimal(0))
            subtotal = sum((Decimal(r["raw_points"]) for r in selected if r["raw_points"] is not None), Decimal(0))
            reason = "UNRESOLVED_CRITERIA" if pending else "NO_APPLICABLE_SCORED_WEIGHT" if denominator == 0 else None
            total = None if reason else str((100 * subtotal / denominator).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
            return {"total": total, "reason": reason, "applicable_weight": str(denominator),
                    "raw_subtotal": None if pending else str(subtotal)}

        global_result = aggregate(rows, unresolved)
        denominator = Decimal(global_result["applicable_weight"])
        for row in rows:
            row["normalized_contribution"] = (str(100 * Decimal(row["raw_points"]) / denominator)
                                                if row["raw_points"] is not None and denominator else None)
        sections = []
        for section in checklist.sections:
            selected = [r for r in rows if r["section_id"] == section.id]
            pending = [r["criterion_id"] for r in selected if r["criterion_id"] in unresolved]
            sections.append({"id": section.id, "title": section.title, **aggregate(selected, pending)})
        flags = {c.id: assessment.results[c.id].value for c in checklist.criteria if c.answer_type == "flag"}
        return {**global_result, "completeness": "needs_review" if unresolved else "complete",
                "unresolved_criteria": unresolved, "criteria": rows, "sections": sections,
                "flags": flags, "scoring_version": SCORING_VERSION}
