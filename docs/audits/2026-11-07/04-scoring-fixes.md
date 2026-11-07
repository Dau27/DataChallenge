# Scoring fixes

Completed 7 November 2026 after the initial audit. Scope: existing evaluation correctness, validation and associated regression coverage. No new product view, endpoint, database schema, provider, policy retrieval system or scoring formula was added.

## What changed

| Defect | Correction |
| --- | --- |
| False uncertainty about the first human greeting | The request explicitly identifies the first and final human operator turns, alongside the complete unchanged transcript. Prompt rules distinguish human handover from earlier bot messages and forbid invented title/patronymic/timing requirements |
| Needs confused with whether the customer already knew the answer | Clarified that sufficiency means enough customer context for the operator. Added positive clarification examples as well as N/A examples |
| No/N/A contradiction | The provider now reports an explicit N/A-condition observation. The adapter rejects a decision inconsistent with that observation. A true condition requires the N/A branch; forbidden N/A remains forbidden |
| Assessed values mixed with N/A/review reasons | The provider decision has exactly one key: assessed value, N/A reason or missing-basis reason. A strict adapter translates this into the unchanged saved/UI Judgment contract |
| Polite wishes credited as complete closing | Clarified compound requirements and examples. Added a narrow source-evidence check: under the original closing definition, a positive finding cannot be supported solely by courtesy/farewell phrases |
| Unsupported closing result survives an evidence error | A failed evidence check enters the existing bounded repair path. It does not silently replace the model answer or manufacture a total |
| Placeholder uncertainty such as /none/ | Rejected as a missing-basis reason. Repair feedback identifies the criterion and required correction |
| Omitted material question treated as minor/unverifiable | Clarified primary/material omissions versus minor secondary detail, correct next-step credit, and the distinction between omitted content and an unknown official fee |
| Unrelated bot, tone or completeness faults transferred between criteria | Kept explicit operator-only, independent-criterion rules and source-grounded examples |
| Variable responses during debugging | GPT-4.1 requests use temperature 0, recorded in generation metadata and cache identity. Other model families do not receive that parameter |

Temperature 0 is a variation-reduction setting, not a guarantee of correctness or identical outputs. The request format and prompting changes were checked against the [official GPT-4.1 guidance](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-4.1) and [Responses API parameter reference](https://developers.openai.com/api/reference/resources/responses/methods/create), then tested through actual configured-provider calls.

## Scope and compatibility

The final request uses prompt literal-rubric-evidence-v12, schema validated-applicability-exclusive-decision-v7 and evidence validator source-closing-courtesy-v1. The model remains the existing gpt-4.1-mini; responses record its actual snapshot identity.

The stored assessment, API response, appeal/reviewer contract, TypeScript types and deterministic scorer are unchanged. Only the private provider representation is decoded from an exclusive decision. It remains one normal model request for all criteria, with at most one output repair and the existing network-attempt bounds.

Criteria and allowed values remain generated from the saved checklist. The closing evidence check matches the source definition, not a fixed criterion ID or conversation ID. Renaming the ID still applies that definition; changing the saved definition disables that source-specific check. It rejects a narrow, provably insufficient citation; it does not claim to validate all semantic support or automatically impose No.

New evaluator/schema/validation metadata invalidate incompatible cache reuse. Old model outputs and review decisions remain inspectable. No historical result was relabeled as having used the newest prompt.

Implementation references:

- [Evaluator and source-evidence validation](C:/Users/user/Desktop/DataChallenge/backend/app/services/evaluator.py)
- [Judgment consistency validation](C:/Users/user/Desktop/DataChallenge/backend/app/domain.py)
- [Request-size budget reservation](C:/Users/user/Desktop/DataChallenge/scripts/run_dev.py)
- [New evaluator regressions](C:/Users/user/Desktop/DataChallenge/backend/tests/test_evaluator_context.py)
- [Scoring validation tests](C:/Users/user/Desktop/DataChallenge/backend/tests/test_scoring.py)

## Verification during implementation

Several small real trials exposed further defects and were preserved:

- v6 improved greetings/closing but still confused needs applicability and produced a placeholder review reason.
- v7 still produced decision inconsistencies; one job failed validation after its bounded repair.
- v8/v9 trials tested evidence-first schema ordering and reduced sampling variation.
- v10 processed all 65 records; some source citations and two terminal failures required follow-up. An earlier failed v10 item was also preserved.
- v11 used the exclusive decision shape and source-citation validation to rerun nine rejected/failed records.
- v12 explicitly coupled the N/A observation and decision, correcting the remaining targeted applicability contradiction.

The failed candidates are not presented as successes. Across this fix task there were 101 new evaluation jobs and 120 reported provider attempts: 97 jobs succeeded, four failed and remain in history. The accepted DEV set has no latest failure. All trial, failed and superseded usage is included in the cost report.

The code preserves full transcripts, role/timestamp order, N/A weight rules, scale anchors and independent critical flags. No dataset-specific verdict is hardcoded into the evaluator.

## Tests actually run

Final backend suite: **94 passed**, one existing Starlette/AnyIO deprecation warning. New regressions cover human-turn boundaries, strict applicability/decision consistency, exclusive-decision decoding, courtesy-only evidence, repair bounds, changed definitions and renamed IDs. Existing arithmetic, persistence, cache, quota and appeal checks still pass.

Client suite: **7 passed / one paid opt-in skipped**. TypeScript/Vite production build passed. Python compileall and pip check passed. No frontend code or dependency was changed.

The final provider schema was also tested with an actual new diagnostic checklist containing a custom binary, scale and unscored flag on real DEV input: expected answers and deterministic total 50.00 passed. This is a labeled configuration diagnostic, not the operator's score under the official initial rubric.

See [re-audit results](C:/Users/user/Desktop/DataChallenge/docs/audits/2026-11-07/05-scoring-reaudit-results.md) for the accepted result set, budget, persistence checks and remaining limitations.
