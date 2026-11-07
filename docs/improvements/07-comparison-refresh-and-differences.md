# Comparison refresh and clearer differences - 7 November 2026

Targeted acceptance gate: **PASS**. Fixes the P2 issue reproduced in the [post-feature PDF audit](../audits/2026-11-07/13-post-features-pdf-audit.md). Combined refinement verification follows in the later stage reports.

The comparison request identity now includes both selected runs' updated_at, execution/completeness state, total and cache lineage. A reviewer update hides the older comparison immediately and triggers a read-only GET for the same selections. Late responses from the previous identity cannot reappear. Changes to unrelated runs do not cause extra requests. Selected runs that disappear produce an explicit error. Reopening refreshes the result while retaining valid explicit choices.

Added separate difference views/counts for answers/dispositions, points, definitions and evidence/explanation-only changes. The initial baseline prefers the nearest earlier successful run with the same immutable checklist; failed/different versions remain available for intentional inspection. Prompt/schema hashes and validated recorded response-model identifiers are visible when actually saved; missing historical provenance stays unavailable. Numeric compatibility, unresolved/null totals and unscored flags retain their guards.

Commands actually run on this stage:

- `.venv/Scripts/python.exe -m pytest -q backend/tests/test_comparison_refinements.py backend/tests/test_saved_inspection.py`: **20 passed** at the stage checkpoint; final three comparison-specific checks also passed after malformed-provenance coverage was added.
- Direct Node/Vitest for comparisonRefinements.test.tsx and savedInspection.test.tsx: **11 passed** (seven new/four existing). Tests exercise both sides updating while open, state-only changes, null totals, unchanged explicit selections, late/error responses, reopen behavior, compatible defaults and local difference filters.
- TypeScript/Vite production build: **passed** at the stage checkpoint. The later combined build is recorded with the export/search/preset reports.

Backend tests use synthetic temporary databases, forbid Provider.request, confirm a review is visible on the next read, and preserve originals and rows during inspection. No scoring rules, evaluator prompt, main database or credentials were changed. The private main-data backup/preservation baseline is under ignored local_data/refinements_20261107.

No API spending. Demo remains deferred. This repair improves inspection consistency; it does not resolve the unclear call or establish independent model accuracy.
