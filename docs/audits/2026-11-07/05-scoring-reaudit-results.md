# Scoring re-audit results

Completed 7 November 2026 after the scoring fixes. This supersedes the initial scoring-defect status while preserving reports 01–03 as the pre-fix audit record.

## Result

**The 26 targeted source-rule diagnostics now pass, and all 65 DEV conversations have complete, saved assessments.** Required workflow and arithmetic checks pass. Independent human agreement and official control testing are still unestablished; these results are not a dataset-wide accuracy claim.

| Measure | Initial audit | Accepted re-audit |
| --- | ---: | ---: |
| DEV records accounted for | 65 | 65 |
| Successful executions in selected set | 65 | 65 |
| Complete numerical assessments | 44 | 65 |
| Needs-review assessments | 21 | 0 |
| Latest failed/unstarted DEV records | 0 | 0 |
| Same targeted provisional checks matched | 7 / 26 | 26 / 26 |

A reduced review count alone is not evidence of better judgments. The substantive evidence is the explicit checked source-rule outcomes and validation below.

## How the result set was obtained

To conserve budget, the accepted set is **not 65 fresh calls using the final prompt**:

1. Ran all 65 DEV conversations with the refined v10 candidate, preserving the failed attempts.
2. Revalidated saved successes using the final result/evidence checks and retained 56 passing results.
3. Reran nine rejected or failed records with v11.
4. Reran one remaining No/N/A regression with v12.

Final composition is 56 v10 results, eight v11 results and one v12 result. All use the actual gpt-4.1-mini-2025-04-14 response snapshot with temperature 0; each keeps its real prompt/schema/settings and attempts. Retention is reuse of saved evidence in the audit, not a claim that the final provider schema was called on every record. The final schema additionally passed the actual custom-configuration test.

All 65 accepted assessments originated in real provider calls; none is a mock, a fabricated answer or an overwritten historical result. The main application's checklist-v1/DEV API now returns these 65 complete latest results.

## Source-rule regression checks

The same 26 provisional agent checks were applied before and after. They include:

- Greeting/introduction in the first human response without bot credit or invented extra requirements.
- Needs N/A when the initial customer context was sufficient.
- Identification N/A when no protected disclosure/action occurred, and confirmed verification where required.
- Full consultation credit for successful routine guidance and a correct referral/follow-up step.
- Partial consultation for an omitted material question, independently of dialogue clarity.
- Closing No for courtesy-only endings, and applicability rather than inappropriate N/A at ordinary endings.
- Applicable consultation after a request had already been formulated.
- Separate positive critical flags for the inspected off-company offers and operator insult.

**26 matched, zero mismatches or unchecked cases.** These are targeted development diagnostics created from the earlier failures, not independent human ground truth, a blind holdout or an accuracy percentage. The reference examples inspected during development must not later be described as untouched test data.

The narrow closing validator applies to the original definition and rejects positive courtesy-only citations; it does not settle every possible interpretation of a recap. Subjective boundaries and policy-dependent questions still require qualified adjudication.

## Arithmetic, integration and persistence

- Revalidated all **130 original/effective snapshots** in the accepted 65-record set: exact criteria, types, allowed values, permitted N/A, ordered existing evidence IDs and current source-citation guard.
- Independently recomputed global and section percentages using Decimal arithmetic, without calling the application's scorer: **zero mismatches**.
- Final backend tests: **94 passed**, one existing deprecation warning.
- Client tests: **7 passed / one paid opt-in skipped**; production build passed.
- Compileall and pip check passed.
- Re-imported DEV through the actual organizer API and saved JSON file: both HTTP 200, **65 unchanged / zero created**, correct 35 RU/15 KZ/15 EN and 60 chats/5 calls.
- Cold-restarted the final backend: all 65 complete evaluation-detail fingerprints remained identical.
- Actual browser confirmed the DEV filter contains 65 records and displayed the corrected needs=N/A and closing=No example after reload.
- The existing paid UI appeal test from the preceding audit was not rerun after the final fixes; no appeal/UI code changed. The final regression suite covers that contract, and pre-existing decisions were preserved.
- Actual current-provider custom checklist test passed for binary/scale/flag handling; the initial v1 snapshot remained unchanged.

No new recording or audio-alignment claim is made. The previously checked external recording player path remains the accepted path; the known inline HTML-wrapper issue was outside this scoring-only change.

## Cost and budget

| Item | Estimate |
| --- | ---: |
| Accepted 65-result set, including attempts belonging to those selected runs | $0.3983244 |
| Entire fix task: all trials, superseded/failed runs, repairs and custom diagnostic | **$0.6271780** |
| All known task/application inference including the preceding isolated audit | $1.61195315 |
| Conservative historical unknown-usage reservation | $2.42294775 |
| Additional overhead reserve | $0.10 |
| Combined conservative accounting | **$4.13490090** |

The fix used a $4.25 combined ceiling, leaving $0.75 headroom under the user's $5 task allowance at authorization time. The final conservative accounting is below that ceiling. These are application usage estimates and reservations, not an invoice or current account-balance check.

All 120 new provider attempts reported input/output usage; there was no new unknown-usage request. The historical unknown reservation covers 36 earlier jobs. It was conservatively recalculated and frozen against their metadata/attempt hashes, so changing the current prompt cannot repeatedly change old-request bookkeeping. Unknown usage remains unknown, not a free charge or an asserted actual cost.

The budget calculation deduplicated evaluation IDs across the main database and preceding audit copy. That includes the earlier $0.3018500 isolated audit cost, rather than counting shared cloned history twice or omitting the separate calls. Private ledgers and raw results are in ignored local_data/scoring_fix_20261107.

No further paid run is needed for this fix. A future main-database-only runner must still account for the preceding separate audit; its default alone is not a complete account ledger.

## Preservation and status

Every pre-existing database row remained unchanged. Original conversation revisions, four existing checklists, 148 existing evaluations, six appeals and six review decisions were preserved exactly. New data comprise 101 evaluation jobs and one clearly named SCORING_FIX_DIAGNOSTIC_ONLY checklist; the main database now has 75 conversation revisions, five checklist versions, 249 evaluations and the same six appeals/reviews.

The initial rubric/config copy and .env were preserved. No new product features, dependencies, public deployment, repository visibility change or organizer message was added. Source PDFs, data, credentials, raw results and databases remain untracked.

Final public-file credential/signed-link scan, local Markdown-link checks and git diff --check passed. The owned backend was stopped after restart verification; no listeners remained on ports 8000/8001/5173. Code and report changes remain local, with no new commit or push claimed.

The current prototype passes the observed functional and targeted scoring checks. Public repository/submission, timed human presentation, independent adjudication and organizer control/freeze remain separate outstanding steps. Code changes have not been represented as an official frozen or submitted version.
