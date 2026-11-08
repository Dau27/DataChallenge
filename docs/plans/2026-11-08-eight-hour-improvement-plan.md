# Eight-hour improvement plan

Current three-chat adaptation: [this chat's role and schedule](2026-11-08-this-chat-integration.md), with [cohort](2026-11-08-chat-cohort-comparison.md) and [print](2026-11-08-chat-printable-reports.md) prompts for the other two chats. This chat absorbs the reduced CLI-only recovery lane and integration; the health dashboard, extra charts and bulk print are omitted. The four-lane allocation below preserves the original recommendation.

Prepared 8 November 2026. **Planning only; no implementation chats or new features were started by this task.** The reference baseline is the combined local source that passed **309 backend / 118 client tests**, one paid opt-in skipped, and production build in the [latest audit](../audits/2026-11-08/01-integrated-pdf-audit.md).

## Objective and boundaries

Spend eight elapsed hours improving how people compare, preserve and communicate existing evaluations. Use **three build chats plus one integration chat**. Keep additional inference spending at **$0**, preserve originals/credentials, and leave the demo deferred.

This plan excludes the previously identified independent-accuracy/current-model validation, policy acquisition, organizer control/replacement test, unclear-call adjudication, public submission and official freeze. It also avoids repeating features already implemented: pairwise comparison, JSON/CSV/simple CSV, selected exports, transcript search/indexing, history pagination, saved filters, review priority, criterion breakdowns and weight preview.

The three deliverables below are engineering recommendations, not extra PDF requirements or a promise of additional grading points. Time estimates assume three builders and a coordinator are available concurrently, with no new infrastructure or dependencies.

## Recommended workstreams

### Chat A — cohort comparison over saved runs

**User benefit:** compare two saved configurations across a set of conversations rather than opening one pair at a time.

[Langfuse's documented experiment workflow](https://langfuse.com/docs/evaluation/experiments/compare-experiments) combines aggregate differences with inspection of individual cases and explicit dataset/evaluator identities. Adapt that workflow to our existing saved-run reader and pairwise comparison service; do not deploy another evaluation platform.

Minimum scope:

- Select baseline/candidate cohorts using actual stored checklist/model/prompt/schema/validation provenance. Missing metadata stays unknown, not an invented version.
- For each exact source revision, choose matching saved runs with a declared deterministic policy. Include their run IDs, update timestamps and cache lineage in a manifest.
- Show matched, missing, failed, unresolved and incompatible coverage separately. Keep DEV and extra synthetic datasets separate.
- Aggregate criterion answer/disposition transitions and comparable point differences. Keep definition/evidence/explanation-only changes distinct.
- Open the existing exact-pair comparison from any changed case. Bound an interactive request to at most 200 pairs and ask users to narrow oversized selections.
- Label results as historical differences. A higher operator score is not proof that an evaluator became more accurate; a cached reuse is not an independent assessment.

Proposed owned files: new `backend/app/services/cohort_comparison.py`, `backend/app/api_cohorts.py`, `frontend/src/CohortComparison.tsx`, scoped styles/types and feature tests. Reuse current interfaces without editing their shared implementations.

**Acceptance:** known synthetic transition counts; exact source/definition compatibility; missing/failed/null/flag handling; deterministic ties; stale-response rejection; real saved-pair drilldown; unchanged database rows and zero provider invocations. No new judgments or schema migration.

### Chat B — verified local backup/recovery and integrity diagnostics

**User benefit:** preserve and recover a complete local workspace through a documented command, instead of relying on task-specific private audit helpers.

The project already has private SQLite backups and a derived-index rebuild command. Reuse these approaches; the addition is a repeatable, verified operational workflow. Python's [SQLite backup API](https://docs.python.org/3.12/library/sqlite3.html#sqlite3.Connection.backup) supports backups while a database is in use, so use that API rather than copying a live database file alone.

Minimum scope:

- Create a private SQLite backup plus a manifest containing schema/version information, logical table counts/hashes and the backup file checksum.
- Exclude `.env` and credentials. Treat the database backup as private source data, including its transcripts and recording URLs; do not describe it as a redacted/shareable export.
- Verify the backup and restore **only to a new path**. Refuse an existing target or the active database path. Do not implement an in-place overwrite button.
- Add an on-demand, read-only integrity report: SQLite integrity/foreign keys, source/checklist identity, original-plus-review replay and index-version/coverage status. Distinguish structural integrity from judgment accuracy.
- Reuse the existing index maintenance command when a derived index needs rebuilding. Diagnostics themselves do not repair or re-score records automatically.

Proposed owned files: new `backend/app/services/workspace_integrity.py`, `scripts/backup_workspace.py`, `scripts/verify_workspace_backup.py`, tests and an operations MD report. A read-only health panel is optional only after the CLI acceptance passes; it is not required for the eight-hour deliverable.

**Acceptance:** a real copied workspace backs up, restores to a fresh location and retains exact original data; truncated/corrupt/mismatched backups fail clearly; existing targets are refused; missing/stale derived-index state is reported accurately; no active database writes, key copies or hosted requests. Read-only main inspection must avoid constructors that initialize/migrate a database.

### Chat C — printable saved-evaluation report

**User benefit:** a readable report for reviewing or keeping an evaluation, alongside the existing machine-readable downloads.

Build a print view from the current sanitized export packet. Browser [print styles and page rules](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Media_queries/Printing) provide the presentation mechanism; no PDF service or new rendering dependency is needed.

Minimum scope:

- One selected saved run, with source revision/checklist identity, original/effective results, section totals, criterion weights/answers/points, reasons and review history.
- Evidence IDs always present where saved; source excerpts explicitly optional using the existing export policy. Explanations may still quote source material, so the report is not anonymous by default.
- Preserve null totals, N/A denominators, unscored flags and actual saved provenance. A weight simulation must never appear as a recorded evaluation.
- Accessible print-preview/download actions, keyboard focus and failure/retry states. Browser Print / Save as PDF remains a user action.
- Escape all source text as data; exclude recording URLs/provider secrets and active scripts/remote assets. Add print-specific page breaks, wrapping and repeated table headings.
- Verify Russian/Kazakh/English characters, long explanations and a reviewed/unresolved result.

Proposed owned files: new `frontend/src/PrintableEvaluation.tsx`, `frontend/src/printEvaluation.ts`, `frontend/src/printEvaluation.css` and component/serialization tests. Existing export services remain unchanged unless the coordinator approves a specific contract fix.

**Acceptance:** actual saved original/effective values match the export packet; paper preview is readable without clipped content; long multilingual text wraps; excluded credentials/recording URLs remain excluded; source HTML cannot execute; no provider request or database change. Bulk printing is outside the minimum scope.

## Eight-hour elapsed schedule

Times are relative to the chosen start, not wall-clock appointments. Rows within the three build columns run simultaneously.

| Elapsed time | Chat A: cohorts | Chat B: recovery | Chat C: print report | Integration chat |
| --- | --- | --- | --- | --- |
| 0:00–0:30 | Review agreed contract | Review backup/restore contract | Review export contract | Capture audited local baseline, private data/source hashes, worktrees and file ownership |
| 0:30–2:00 | Pair-selection service and response manifest | Backup command and manifest verification | Render a real sanitized saved packet | Review interfaces and prepare integration tests; avoid shared-file edits by builders |
| 2:00–3:30 | Cohort controls, coverage and exact-case drilldown | Fresh-path restore and read-only diagnostics | Preview, print styling, excerpts and keyboard/error behavior | Review each small deliverable and resolve contract questions |
| 3:30–4:30 | Edge cases and copied saved pairs | Corruption/target-refusal/recovery checks | Unicode/long-report/privacy checks | Accept or reduce each lane's scope; collect targeted test evidence and MD reports |
| 4:30–5:30 | Fix integration findings | Fix integration findings | Fix integration findings | Integrate completed lanes one at a time, preferably B → A → C; wire shared routes/UI/types |
| 5:30–7:00 | Help investigate failures | Run preservation/restore checks | Verify combined screen/paper layouts | Run integrated suites/build, actual copied-data checks, source/secret/link scans and browser checks |
| 7:00–8:00 | Defects only | Defects only | Defects only | Close regressions, update final MD/context and retain a tested local checkpoint |

Reserve the final hour for defects/reporting. Do not start another feature after 4:30. If a lane misses its gate, keep its unfinished changes isolated; ship only accepted lanes.

## Parallel-chat boundaries

The previous audit found extensive uncommitted local work; remote main is still an older checkpoint. **Every worktree must start from the same audited local snapshot**, not blindly from remote main. Preparing that development checkpoint is not an official event freeze or a public submission.

| Owner | May change | Must leave to coordinator |
| --- | --- | --- |
| Chat A | New cohort service/router/component, own types/styles/tests/report | Existing scorer/evaluator, saved comparison service/component, main app/router mounting and queue integration |
| Chat B | New backup/integrity service/scripts/tests/report | Existing DB schema/startup/index/budget/provider code; any shared health-panel integration |
| Chat C | New report renderer/component/styles/tests/report | Existing export sanitation, Detail/SavedExport integration and global design stylesheet |
| Integration chat | `main.py`, `insights_api.py`, App/Conversations/Detail/SavedExport hooks, shared types, package/config changes, CURRENT_CONTEXT and final report | No changes to saved judgments, paid limits, provider credentials or rubric seeds |

Builders should request a contract adjustment from the coordinator rather than patching the same shared file independently. Keep feature-specific styles in new files. Any agreed exception gets one owner. No dependency upgrades or schema migrations are planned.

Each builder uses its own worktree and private data copy with empty provider credentials, zero budget and a provider/network guard. Do not copy `.env` into builder worktrees. Builders run targeted tests; the coordinator runs the full suites on the integrated candidate, avoiding several competing whole-project runs. One coordinator-owned copy/preview on the existing normal local ports is enough for final browser verification.

## Gates and scope cuts

1. **Baseline gate, 0:30:** all chats identify the same source snapshot, DTOs, route names, source/basis selection rules and owned files. Main data/protected hashes are captured. API calls remain blocked.
2. **Feature gates, 4:30:** each lane supplies working behavior on actual saved/copied data, relevant regressions, files changed, known limits and an MD report. A static panel or mock-only result does not pass.
3. **Integration gate, 7:00:** full tests/build pass; source identities and old result values match; actual new views/commands work together; all 249 existing saved runs and 30 protected files are preserved. Measure against the captured current dataset if it legitimately changes before the sprint.
4. **Completion gate, 8:00:** no known blocking regression, reports match commands actually run, sources and private backup locations are documented, and incomplete code remains isolated. No paid call, demo, public visibility change or organizer message.

If time is tight, cut chart polish/additional cohort charts, the optional diagnostics UI, and bulk print first. Keep accurate coverage/drilldowns, verified fresh-path recovery and one readable saved-run print report. Do not cut source identity, original preservation, privacy handling or integration tests.

With only **three total chats**, use two builders plus the coordinator: cohorts and recovery first; print becomes a follow-on rather than promising three full lanes with an overloaded integrator.

## Copy-ready chat briefs

### Integration chat

Prepare the audited local source as the common isolated baseline, preserving all uncommitted work/secrets. Own shared API/UI/type/config files and CURRENT_CONTEXT. Publish the exact baseline reference, DTO/route contracts and file ownership to the three builders. Integrate accepted work one lane at a time after 4:30; run full tests/build and actual copied-data/browser checks. Keep original results, zero paid budget and demo deferral. Finish with a truthful verification MD and local checkpoint; do not perform public/event actions.

### Chat A

Implement only the cohort-comparison lane in this plan on the supplied worktree/baseline. Reuse saved readers and exact-pair comparison; use actual metadata and source revisions; show missing/failed/incompatible coverage and exact-case drilldowns. Work only in new owned files. Do not run evaluations, change scoring, edit shared files or infer accuracy from score differences. Test synthetic edges and actual saved/copied pairs, then provide the feature MD and exact changes/results by 4:30.

### Chat B

Implement only verified private backup/fresh-path recovery and read-only integrity diagnostics. Reuse SQLite backup and existing index maintenance. Exclude credentials, never overwrite the active/existing database, and do not auto-repair judgments. Work in new owned files, with private copies/temporary paths and hosted access forbidden. Test a real copied workspace plus corruption/refusal cases. Provide the feature MD and exact preservation/test evidence by 4:30.

### Chat C

Implement only one-run printable evaluation reporting from the existing sanitized export contract. Retain saved original/effective values, nulls, flags and provenance; excerpts are optional; source strings are escaped and recording URLs/credentials excluded. Work in new owned files and leave existing hook points to the coordinator. Test actual saved/copied packets, long RU/KZ/EN text, print layout, focus/errors and privacy. Provide the feature MD and exact test/visual evidence by 4:30. No model calls, new PDF service or demo work.

## Work performed for this plan

Reviewed the latest audit/context, history/index/design reports, existing health and export boundaries, and official Langfuse/Python/MDN references. The schedule, file contracts and effort estimates are recommendations. No application code, data, secrets, branch, dependency or provider setting was changed; no implementation chats, tests, server, model request or demo were started. This plan does not promise an official score increase or independent scoring accuracy.
