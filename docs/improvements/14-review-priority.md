# Explained review-priority queue

Verified 8 November 2026. Extended the existing queue with explicit saved-state reasons, optional priority ordering and reason filtering. The same visible rows feed selection and exports. **No risk score, operator penalty, reviewer decision or model call is added. Demo remains deferred.**

## Market pattern and fit

[CallMiner documents prioritised review lists](https://callminer.com/solutions/quality-management); [Observe.AI documents evidence-backed evaluations, disputes and follow-up](https://www.observe.ai/post-interaction/auto-qa). We adapt the workflow to our recorded states and exact evidence targets. Public documentation supports these patterns, not knowledge of either vendor's internal ranking algorithm.

The implementation avoids a second review table, a team-assignment system or a new manual reference-labeling exercise. It preserves anonymous appeal/reviewer actions and the project's existing rubric.

## Implemented behavior

- Reasons distinguish open appeals, unresolved/unavailable judgments, recorded critical findings, unknown critical status, failed/interrupted work, unstarted work and work in progress. Unknown is never a clean result; a custom rubric without flags is described as having no configured flags.
- Historical open appeals are retained for the same dataset/source identity and selected checklist, including earlier source revisions. Their links target the original appeal's exact conversation/run/criterion.
- Users explicitly choose normal order, appeals first, unresolved first, critical findings first, failed/interrupted first or oldest recorded reason first. The order and deterministic tie-breakers are explained; timestamps are recorded-state timestamps, not a promised SLA or inferred business severity.
- Reason counts count conversations and may overlap. The optional reason filter updates the existing queue, select-all, visible selection and selected-run exports consistently.
- Default behavior makes no new request or order change. Opening the tool reads a bounded snapshot; active ordering/filtering keeps necessary refreshes enabled even when the disclosure is closed.
- Active criteria, loading/failure state, retry/edit/reset remain visible outside a collapsed tool. Stale priority-filtered results are withheld until a matching result arrives or the view is reset.
- Manifest checks, request identity and late-response guards preserve source/run/checklist consistency. Strict flag handling treats malformed numeric booleans, N/A and missing data as unknown.

Implementation: `services/review_priority.py`, `api_priority.py`, `ReviewPriority.tsx`, shared saved-scope reader and a hook in `Conversations.tsx`. No persistence or scoring changes.

## Acceptance actually run

- Feature backend: **6 passed**; client: **7 passed**; TypeScript and owned diff checks passed. Tests cover historical appeals/dataset collisions, failure/unknown/no-flag cases, malformed stored judgments, deterministic ordering, filter/reset, closed-disclosure status, manifest mismatch and obsolete responses.
- An intermediate client assertion expected raw synthetic network-error text; `api.ts` intentionally normalizes network failures. The assertion was corrected; final targeted tests passed.
- Copied actual data: **five priority requests / 375 source checks**, one per saved checklist version. Open-appeal and critical-finding conversation counts match the existing queue; every configured flag is represented as true/false/unknown.
- Browser on the protected copy: filtering Open appeals reduces the existing 75-row queue to **one** row, p4-ru-005. Closing the tool keeps the active filter/count/reset banner visible. The historical appeal and unresolved-criterion links remain reachable.

Integrated tests/build and final preservation are recorded in [final verification](16-insights-verification.md). No archived organizer/reference-review task was reinstated; original scores and histories are unchanged.
