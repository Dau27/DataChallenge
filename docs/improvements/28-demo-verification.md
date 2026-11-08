# Stage 28 - demo resumed and zero-spend workflow verification

8 November 2026. The owner resumed the demonstration and remaining verification. The repository stays private; the owner plans to make it public at the deadline. Organizer control access is unavailable. Paid inference and optional paper-layout QA remain outside this task.

## Actual browser follow-up

The in-app browser became available. Observed the real production UI on a separate private presenter copy: source evidence, saved v1 score, an appeal and separate source-backed Closing replacement, **100.00 original /92.31 effective**, immutable v6 nine-criterion save/change preview, and the earlier real v2 ticket-reference judgment. Private screenshots browser-review-score.png and browser-checklist-v6.png retain the visible results. No browser model evaluation, external audio fetch or public data exposure.

The browser uncovered a genuine mismatch: opening a v1 queue row selected the source's newer diagnostic v5 run. Fixed both links in Conversations.tsx to include the displayed row's exact evaluation ID. Added two regressions for version changes and transcript-only navigation. Before fix:one failed/six passed; after:seven passed, repeated after removing a test-only TypeScript option caught by the build. Full frontend **184 passed /one paid opt-in skipped**,45.90s; final production build passed (Vite3.00s). Rebuilt/reloaded browser now opens v1/92.31 exactly as displayed, rather than diagnostic v5/50.00. No saved result changed.

My custom port8765 was outside the app's permitted browser origins. Kept security middleware unchanged and moved only the private presenter to documented8000 after confirming the port was free. It then saved the appeal, decision and new version successfully. Existing unrelated processes were not stopped. Current helpers/default/private links use8000 and still auto-stop after30minutes. The presenter copy now contains those practice writes; prepare another new copy for an unreviewed human run. UI source fixes and reports remain local at this checkpoint; the subsequently supplied Results appendix is handled in the [new audit/adapter](../audits/2026-11-08/04-appendix-submission-audit.md).

The earlier verification record below describes the initial pre-browser stage and its then-unverified visual status. Spoken timing and a fresh paid changed-criterion evaluation remain unperformed; the historical v2 example is explicitly separate from today's v6 draft.

## Completed work

- Replaced the stale presenter card with a [five-minute guide](../DEMO.md) centered on the required evaluation/evidence/N/A/appeal/review/checklist flow. Updated the prior 125/14 test claim to the applicable 460/182 evidence. Presentation allocations are explicitly not measured spoken timings.
- Prepared a consistent private backup of the main workspace and separate disposable technical/presenter databases. The main database, originals, review histories, credentials and budget baseline were not modified.
- Ran the actual React Detail, ReviewForm and ChecklistEditor components against the actual local backend and saved DEV data. No HTTP response, model output or dataset was mocked. The private server uses explicit credential-free settings, never loads .env and guards provider/HTTP/external sockets.
- Rehearsed real source-linked RU/KZ/EN evidence, recording-link presence, the unresolved call, actual appeal and separate evidence-backed replacement, recalculation, comparison refresh, field-level errors and a substantive new nine-criterion checklist save.
- Cold-restarted the copied workspace and verified the decision, original/effective results and new version persisted. Prepared a separate fresh presenter copy and exact private saved-run links, avoiding practice writes to the main workspace.

## Checks actually run

| Check | Actual result |
| --- | --- |
| Production build | TypeScript and Vite passed; Vite 2.26 seconds |
| Real React DOM + real local API checks | **3 passed**, test time 4.52 seconds / runner 7.88 seconds |
| Actual API requests in the three DOM checks | **37**, recorded individually |
| Real appeal/reviewer replacement on an older saved RU run | Original **100.00** preserved; effective **92.31**; recorded request-attempt count unchanged |
| Correct source basis for that replacement | Same complete transcript as the earlier documented closing correction; m0010-m0012 checks the missing recap/further-help offer |
| Evidence/languages/recording links | Five actual saved RU/KZ/EN/call cases checked; evidence highlights actual messages; unclear call retains a null effective total |
| Checklist validation/save | Negative weight gives field error and blocks save; corrected substantive nine-criterion draft saves as v6; v1 unchanged |
| Fresh evaluation while disabled | Expected HTTP 503; evaluation count remains 249, no fake result |
| Cold restart and JSON export | Decision/version/score retained, original unchanged; export excludes recording URL |
| Provider/external HTTP/socket/.env-load guard | **Zero attempts** across successful technical rehearsal and restart |
| Earlier genuine changed-checklist evidence | Existing real v2 run retains nine criteria and recorded provider attempts; explicitly historical, not an evaluation of today's v6 draft |

These three checks are functional DOM/API verification rather than a visual browser or human spoken rehearsal. They do not assign independent accuracy, a new v13 assessment, a control result or official project points. Prior exact-source full suites remain 460 backend / 182 client tests, one paid opt-in skipped; they were not redundantly rerun without a product change.

Early private harness attempts needed corrections: Windows virtual-environment launcher/server PIDs differ; external test discovery/import URLs needed a workspace root and explicit private path; Happy DOM needed the application's actual same origin; and the appeal test needed to reacquire its DOM node after a legitimate reload. An initial failed fork exit also reported Windows EPERM, so the private runner used one thread. The final run passed all three on a new copy. These were harness/configuration failures, not app fixes or first-attempt passes. Partial artifacts and databases remain private rather than being deleted or overwritten.

## Commands and private handoff

```powershell
.\.venv\Scripts\python.exe -X utf8 local_data/demo_verification_20261108/prepare.py
npm run build
node node_modules/vitest/vitest.mjs run --config ../local_data/demo_verification_20261108/vitest.demo.config.mjs
.\.venv\Scripts\python.exe -X utf8 local_data/demo_verification_20261108/verify_api.py
.\.venv\Scripts\python.exe -X utf8 local_data/demo_verification_20261108/stop_demo.py
.\.venv\Scripts\python.exe -X utf8 local_data/demo_verification_20261108/start_demo.py rehearsal_retry.sqlite3
.\.venv\Scripts\python.exe -X utf8 local_data/demo_verification_20261108/verify_api.py
.\.venv\Scripts\python.exe -X utf8 local_data/demo_verification_20261108/prepare_presenter.py
.\.venv\Scripts\python.exe -X utf8 local_data/demo_verification_20261108/start_demo.py presenter.sqlite3
```

The npm/Node commands ran from frontend; Python commands ran from the repository root. The initial helpers operated the owned localhost:8765 server; the browser follow-up above moved to documented8000 without changing app security. Ownership nonce/capability and automatic30-minute stop remain. The presenter copy was initially fresh and separate from the completed DOM-test copy, and now retains the observed browser practice writes. All helpers, cards, exact IDs, databases, logs and receipts remain under ignored local_data/demo_verification_20261108.

## Still distinct from a complete event presentation

Spoken rehearsal timings are not measured. Browser visual acceptance remains unverified at this report checkpoint; functional DOM success is not a screenshot or visual pass. External recording availability/intelligibility was not retested; source-player links were checked without fetching private audio. Today's new checklist was saved but deliberately not evaluated. The script labels the separate earlier real custom-checklist example honestly; a fresh changed-criterion evaluation needs later authorized inference and cannot be replaced by a mock.

Final independent preservation passed: all **15 main tables/schema, 249 saved evaluations, 30 protected files and 159 source files** unchanged, HEAD/index unchanged. All **249 copied original assessments/scores** are also unchanged. The technical copy contains exactly the expected extra checklist version, appeal, decision and budget-baseline row; all other table fingerprints match the baseline. The final helper used the actual checklist_versions/review_decisions schema names after correcting an initial generic-name assumption. No product change was needed. Source/history/Markdown scanning passed **241 candidate files / 514 then-reachable blobs / 82 Markdown files / 397 local links**, zero credential/private-path matches and clean diff check. Private final_preservation.json records the exact boundary, including visual/spoken checks still unverified.

The initial stage was documentation-only; its browser follow-up made the two frontend source/test changes described above. No provider/organizer access, paid spending, public release, push, official freeze or organizer submission. [Current context](../../CURRENT_CONTEXT.md) and private verification retain the evidence. Main remains the private pushed b29c791 lineage with local tested updates, including the later appendix adapter. Next concrete step is a timed spoken run and actual control inputs, not another optional-feature sprint.
