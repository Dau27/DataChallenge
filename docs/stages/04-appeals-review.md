# Stage 4 — Appeals and persistent review

Status: **PASS**. Synthetic tests plus actual persisted DEV/React UI review flow and backend restart verified.

- Appeal submission persists an evaluation/criterion-specific comment without changing the assessment.
- A separate reviewer action shows original/current answers, evidence context, and the appeal comment. Anonymous demo actions are explicitly not production-secure roles.
- Reviewer can confirm or replace with a strict boolean, configured scale anchor, or permitted justified N/A. Decisions need a rationale and valid stored evidence ranges.
- Stale updates, forbidden N/A, invalid replacements, unresolved confirmation, and duplicate decisions are rejected.
- Effective judgments are rebuilt from the immutable original plus ordered saved review decisions. The same deterministic scorer recalculates the effective result without a provider call.
- Original score/judgments, every appeal, every decision, and the score at each decision are preserved. Cached evaluations reuse original assessments only and never copy human decisions.
- Integration test verifies original 90.00 → reviewer replacement → effective 100.00 → process restart → both scores and history remain. This is explicitly a synthetic temporary-database test, not a live DEV result.
- Client test verifies the reviewer form requires a separate review action and rationale before submitting a decision.

Commands: `.venv/Scripts/python.exe -m pytest -q` (50 passed at checkpoint); `npm test` (7 passed). Final reruns after audit-history improvements are recorded in CURRENT_CONTEXT.md.

Later real acceptance: the opt-in live UI test submitted appeals and reviewer replacements on the first actual model assessment. Original 100.00 was preserved, effective score became 92.31 after applying the saved N/A/closing rules, with no model call for review. After backend restart, the API still returned both scores, four appeals and four saved decisions (including repeated smoke-run demonstrations). Reasons explicitly attribute these to provisional agent demonstration review, not independent human labels. Browser visual inspection is still pending.
