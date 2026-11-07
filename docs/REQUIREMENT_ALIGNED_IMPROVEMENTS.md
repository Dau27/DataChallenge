# Improvements using existing data and requirements

Implementation update: the first three enhancements were subsequently implemented and tested without model calls. See [completed stage reports](improvements/README.md). The assessment below preserves its original recommendation context; saved-run comparison and export were not added.

Assessment date: 7 November 2026, implementation checkpoint 810e31f. Scope: identify improvements; no new feature implementation or paid inference in this assessment. Hidden organizer control data remain unavailable. The 65 DEV conversations and their saved results remain locally available.

## What we know

The required import/configure/evaluate/evidence/appeal/review/preservation workflow has been exercised. Latest clean-source verification passed 94 backend tests, nine client tests and the production build. All 65 accepted DEV results are complete, with 26/26 targeted provisional diagnostics and independent arithmetic checks of 130 snapshots passing.

These are verified functional/development results. They do not establish independent model accuracy or performance on unseen organizer cases. The accepted set combines 56 v10, eight v11 and one v12 provider run, rather than 65 calls using the final prompt. The earlier approximate 85/100 was an informal readiness estimate; the guide supplies no weighted project-grading scale. Its separate 100-point checklist evaluates operators.

Organizer-only control data are an expected external dependency. We can improve local correctness, configuration robustness and review usability without acquiring those hidden transcripts. We cannot certify control performance, invent official labels or treat a new mock-only test as evidence of model improvement.

## Improve judgment quality first

1. **Complete the prepared human review.** A qualified reviewer can assess the existing 15-transcript packet without organizer gold labels or additional inference. It has five transcripts per language, two calls and 120 blank criterion labels. Assess source/rubric before opening the saved model comparison. Report criterion-level disagreements, especially No/N/A, consultation anchors, critical flags and evidence support. Preserve unresolved external policy questions. This development sample is not a blind holdout or population benchmark. See [HUMAN_REVIEW.md](HUMAN_REVIEW.md).
2. **Compare saved outcomes locally.** Use the human labels, once actually completed, and existing model runs. Separate answer/disposition disagreement from arithmetic errors and evidence defects. Report language/channel counts and real evaluator versions. Human review can correct effective results through the existing workflow without another model call; it does not retroactively improve the original model answer.
3. **Expand configuration stress checks.** Existing tests already cover new/renamed/removed criteria, cache invalidation, anchors, N/A and separate flags. Extend combinations such as reordered criteria, changed scale units, fractional weights and new definitions that differ from the initial rubric. Check the generated schema, arithmetic, cache identity and preserved snapshots with deterministic/injected-transport tests. Fresh model interpretation of a newly worded rule remains unverified until a later real call; changing prompts without that check would not prove better results.

## Additional features that directly support the required workflow

These are optional engineering enhancements to already-covered requirements, not missing organizer mandates or a promised score increase. They fit the existing React/FastAPI/SQLite structure. None requires a replacement application or another provider.

| Priority | Enhancement | Requirement supported | Current implementation / useful addition | Added inference for implementation and ordinary use |
| --- | --- | --- | --- | --- |
| 1 | Shared spending limit and pre-run estimate | Guide p.4 model-cost transparency; engineering budget protection | The guarded batch runner exists, but UI starts/retries/provider checks reach backend operations without that combined guard. Reserve estimated worst-case cost before every paid request, reconcile unknown historical/separate-audit spend, and show cached versus new work. Preserve free navigation/review when funds are reserved | Zero; injected transports can verify rejection/reservation. Future actual evaluations remain paid |
| 2 | Checklist-change preview and field-level errors | Guide pp.1–2 editable criteria and organizer replacement test | The editor already saves immutable versions with backend validation. Add a readable diff of definitions, weights, types, anchors and N/A; locate invalid fields before save. Show which saved version a result uses | Zero for structural preview. Changed meanings require later fresh inference; an old answer is not a new assessment |
| 3 | Pending-appeals and critical-findings filters | Guide p.2 reviewer finds dispute, evidence and comment | The list already filters execution/completeness, language, channel and dataset; appeals appear inside details. Add pending-appeal counts/filter and a separate critical-flag filter with direct links to the criterion. Keep flags separate from numerical penalties | Zero; queries reuse existing appeals/reviews/results |
| 4 | Side-by-side saved-run comparison | Guide p.2 explain results; immutable configuration/evaluation provenance | Saved runs are selectable and original/effective decisions inspectable. Add criterion-level answer/N/A/evidence differences across two saved runs, with actual checklist/model/prompt identities. Mark missing/changed criteria and avoid implying scores from different rubrics measure the same thing | Zero when comparing saved runs |
| 5 | Downloadable evaluation/audit report | Guide pp.2,4 evidence, original/final review and cost explanation | Existing API/detail expose this data. Export a local report with checklist, criterion scores, evidence IDs, review rationale and actual usage/provenance. Exclude credentials and signed recording URLs. This supports private review and presentation | Zero; no model-generated summary needed |

The first item protects budget; it does not establish better model accuracy. Items two and three strengthen the required configuration/review demonstration. Saved comparison and reporting make existing evidence easier to inspect; they do not create new ground truth.

## Recommended implementation gates

1. **Spending gate:** failed affordability check sends no request and creates no misleading successful result; concurrent jobs/retries cannot double-spend a reservation. Cached reuse makes no provider call. Include historical unknown usage and separate audit ledgers; do not assert a current balance from estimates.
2. **Configuration gate:** preview identifies every changed field; invalid anchors/N/A/flags are tied to the correct field; old snapshots remain unchanged; editing a substantive rule invalidates incompatible cache reuse. Do not silently change the original seed to boost scores.
3. **Review gate:** pending-appeal counts reconcile with saved open appeals; resolved appeals leave the pending filter; filters respect dataset/checklist context; a criterion link reaches its real evidence and review action. No separate authentication system is needed for this demo.
4. **Comparison/report gate:** outputs exactly match stored results, preserve provenance and show unavailable/incomparable values explicitly. Export and comparison must not trigger evaluation.

Use private DB copies and ordinary tests for these gates. Live semantic acceptance on new criteria/control data remains a later, separately budgeted step.

## Implementation references

- [CLI spending guard](../scripts/run_dev.py), [job creation/retry](../backend/app/services/jobs.py), [provider access route](../backend/app/main.py).
- [Checklist editor](../frontend/src/ChecklistEditor.tsx), [strict rubric validation](../backend/app/domain.py).
- [Current list filters](../frontend/src/Conversations.tsx), [criterion detail and saved runs](../frontend/src/Detail.tsx), [review action](../frontend/src/ReviewForm.tsx).
- [Existing evaluator regressions](../backend/tests/test_evaluator_context.py), [cache/configuration checks](../backend/tests/test_provider_edges.py), [private human review instructions](HUMAN_REVIEW.md).

## Completed in this assessment and next step

Read current implementation/specification, readiness evidence and earlier market feasibility analysis; inspected list, editor, detail, review, job creation/retry, schema tests and CLI budget paths. Git status was initially clean. No organizer/model endpoint, paid test, account login or inference was invoked. Application tests were not rerun for this analysis-only change; counts above refer to the recorded clean-source run. No features, prompts, rubric values, dependencies or stored judgments were changed.

Next implementation recommendation: shared budget protection, then checklist preview/field errors and pending-appeal filtering. Complete human adjudication alongside those changes. Keep official control/freeze and public submission as explicit external handoff steps. Real-time coaching, speech recognition and full CRM integration remain outside the supplied prototype scope.
