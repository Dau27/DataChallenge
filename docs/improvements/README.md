# Implemented workflow improvements

Completed 7 November 2026. The latest authorized stages add saved-run comparison, JSON/CSV exports and transcript search with saved filters. Existing budget protection, checklist preview and review filters are retained. Demo work remains deferred.

Subsequent [PDF audit](../audits/2026-11-07/13-post-features-pdf-audit.md): regression/saved-data checks pass, but an open comparison can stay stale after a new review decision. The main result/history remain correct. Automatic comparison refresh is the next recommended fix; it was documented, not implemented by that audit. [Market-based refinements](../ADOPTED_FEATURE_REVIEW.md) are proposals, not completed changes.

| Latest stage | Result | Report |
| --- | --- | --- |
| 4 — Saved-run comparison | Passed: exact revision, original/effective selectors, evidence and rule/answer/points/provenance differences; incompatible/null totals handled | [Comparison](04-saved-run-comparison.md) |
| 5 — JSON/CSV exports | Passed: actual downloads, both score sets/history, typed records, opt-in excerpts and credential/URL/formula protection | [Exports](05-saved-report-exports.md) |
| 6 — Transcript search and saved filters | Passed: literal Unicode text/speaker search, exact links, combined filters, checklist-scoped presets and stale/error handling | [Search and final verification](06-transcript-search-saved-filters.md) |

Latest full checks: **144 backend / 27 client passed**, **one paid opt-in skipped**, build and pip check passed. Copied actual data: **249 comparisons / 249 JSON exports / 249 CSV exports**, six multilingual searches and cold reopen passed with provider calls forbidden. Actual browser downloads/preset reload/evidence links passed; narrow layout fits 699 px. Main rows, credentials, rubric, budget baseline and archived private evidence preserved. **Zero model calls / $0.00 added inference**. These are usability improvements, not an accuracy or official score claim. Stage 6 records commands and limitations.

## Earlier enhancement checkpoint

The following results describe the earlier budget/preview/review-filter implementation; their counts are historical.

| Stage | Result | Report |
| --- | --- | --- |
| 1 — Shared budget | Passed: persistent atomic reservations, guarded provider requests, default zero limit, cache-aware cost preview and shared CLI accounting | [Budget protection](01-shared-budget.md) |
| 2 — Checklist preview | Passed: read-only differences, field errors, stale-response protection and validated immutable save | [Checklist preview](02-checklist-preview.md) |
| 3 — Review filters | Passed: pending appeals across runs/revisions, effective critical flags and direct criterion links | [Review filters](03-review-filters.md) |

Final tests: **125 backend passed**, **14 client passed / one paid opt-in skipped**, TypeScript/Vite build passed. Copied real DEV data and actual local browser/HTTP checks verified the features without inference. The main database, original rubric and .env were preserved. Added model requests: **zero**; added inference estimate: **$0.00**.

The same 125 backend / 14 client checks and build also passed in the isolated installed source. Safe source/history and Markdown-link checks passed; the main database/.env hashes match the pre-change snapshot. Owned verification servers were stopped. These checks support the implementation, not independent model accuracy on hidden organizer data.

Paid requests are paused by default with BUDGET_LIMIT_USD=0. Compatible cached reuse, saved results, draft preview and application reviewer decisions remain available. The 65-complete count describes this implementation checkpoint; later audit reports preserve subsequent changes. Semantic accuracy remains unverified. Public submission and official organizer control/freeze remain pending.

Reviewed implementation checkpoint aa3c08f was fast-forward pushed to the existing private GitHub repository and verified with ls-remote. A documentation-only follow-up records that evidence. No official freeze, public visibility change or submission is claimed.
