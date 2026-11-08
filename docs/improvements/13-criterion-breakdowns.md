# Criterion breakdowns

Started 7 November, verified 8 November 2026. Implemented a read-only breakdown of the **currently visible queue**, for its selected saved checklist and an explicit original/effective judgment basis. Existing source records, saved results and reviewer decisions remain unchanged. **Zero provider calls; demo deferred.**

## Market pattern and fit

[Zendesk QA's documented dashboard](https://support.zendesk.com/hc/en-us/articles/9019507481242-Understanding-the-AutoQA-dashboard-in-Zendesk-QA) groups results by category/language and links aggregate data to underlying conversations. We adopt the aggregate-to-evidence workflow using our existing immutable source/run identities. We did not inspect or copy proprietary internals, adopt vendor accuracy claims or replace our scoring formula.

The tool is a collapsed disclosure in the existing queue. Opening it reads actual saved judgments; it does not create an evaluation. Source filters, transcript search and any active priority filter determine the visible selection. DEV and synthetic datasets receive separate tables.

## Implemented behavior

- Bounded snapshot selection, up to 200 visible conversations. Oversized selections get an explicit request to narrow filters; nothing is silently truncated.
- Latest source revision and latest run for the selected checklist, with a deterministic ID tie-breaker. A newer failed run stays failed rather than falling back to an older success. Obsolete source revisions return a refresh conflict.
- Dataset-specific execution coverage and binary/scale/N/A/needs-review/unavailable distributions. Flags show true/false/unknown separately and remain unscored. Invalid stored answers are unavailable/unknown rather than guessed as passes.
- Every bucket shows a count, selected-dataset denominator and percentage. The denominator includes that dataset's selected conversations, including missing/unresolved work; these are distributions, not accuracy or applicable-only pass rates.
- Counts and exact source/run/criterion membership come from the same database read snapshot. Clicking a nonempty cell opens those exact cases with deep links.
- Client request identity includes source/run/review state and judgment basis. Stale counts and drilldowns disappear immediately; obsolete responses/errors cannot overwrite a newer view. Server manifests are checked against current queue identities.

Implementation: `services/insights_common.py`, `services/criterion_breakdown.py`, `api_breakdown.py`, `CriterionBreakdown.tsx` and existing queue integration. No dependency, schema migration or provider change.

## Acceptance actually run

- Feature backend: **10 passed**; client: **6 passed**; TypeScript passed. Cases cover both bases, dataset boundaries, latest failure, queued/running coverage, N/A, unresolved/flag states, malformed criterion sets, strict booleans, scale anchors, signed zero, exact cases and stale UI responses.
- Shared selection/routing checks: **10 passed**, including missing/obsolete sources, bounded/duplicate inputs, deterministic latest selection and no job/budget/table mutation.
- Fresh actual-data copy: **10 breakdown requests across five checklist versions and both bases**, covering **152 dataset/criterion distributions**. Every bucket count equals its exact case membership; every criterion partitions its dataset's selected sources.
- Browser on the protected copy: v1 DEV displays 65 conversations separately from synthetic data. Contact shows **61 Yes / 3 No / 1 needs review**. The needs-review cell opens p4-ru-005's exact saved criterion. No reviewer decision or result was created.

The complete integrated suite/build and final preservation checks are recorded in [final verification](16-insights-verification.md). Private evidence: ignored `local_data/insights_20261107`. Descriptive distributions do not establish model correctness or an organizer grade.
