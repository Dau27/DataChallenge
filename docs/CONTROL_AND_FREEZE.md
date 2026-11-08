# Control data and official freeze

Status: procedure ready; no official control identifier, event timing or freeze instruction has been supplied. No control run or frozen commit is claimed.

**New organizer appendix:** exactly10 control chats arrive at hour23; receipt, assessment, validation, commit and push of results/prod/results.json must finish before hour24 stop-code. results/dev/results.json must also be in the repository; the real Vector Field DEV65 file is prepared locally (64ok/one permitted error). [Exact Results JSON1.0 commands and one-hour plan](SUBMISSION.md), [four-PDF audit](audits/2026-11-08/04-appendix-submission-audit.md). The dedicated exporter/validator is tested and free; archival UI JSON is not the required wire format. Control data are not available now, and no PROD placeholder is created. The owner's two-hour estimate is not a supplied official timestamp or group ID.

**Owner scope, 8 November:** keep the repository private until the owner releases it at the deadline. Organizer control access is unavailable. The [final offline documentation/recovery handoff](improvements/26-judge-readiness.md) is ready. The owner has now resumed [zero-spend demo preparation](DEMO.md); public access/submission, paid inference and actual control execution remain outside this task. No visibility change or organizer message.

Scope clarification: guide pages 1/4 require the public repository/link handoff, README startup steps, organizer control and criterion-replacement check, final frozen commit and an at-most-five-minute presentation. For a paid model, disclose its name and approximate whole-evaluation cost; the existing README has a historical example and recorded attempts retain usage/cost provenance. Printing and an independent reference-labeling exercise are not PDF delivery requirements. Backup, exact-source tests and secret scans below are engineering safeguards. [Original PDF reread](audits/2026-11-08/03-pdf-requirements-clarification.md). Demo preparation is resumed; new inference spending remains prohibited.

Main application checkpoint f481908 is now published and independently fetched/verified on GitHub, with all 159 tested source blobs unchanged from 535444d. [Publication receipt](improvements/25-main-publication.md). This does not certify anonymous/public availability, organizer submission or the official event freeze. Paid inference and the demo remain paused.

## Before the official freeze

1. Obtain the exact control group identifier, official event start/freeze time and submission destination from organizers. Do not derive them from this computer's clock or try guessed groups.
2. Review the candidate source and secret-scan evidence; verify the actual checkpoint hash and push outcome in CURRENT_CONTEXT.md. Main is published, but current anonymous public access and organizer receipt are not verified. Confirm those through the event process. A published checkpoint is not an official frozen version.
3. Verify setup/start instructions and required tests on the exact source being delivered. The [main sprint merge/handoff](improvements/24-main-sprint-merge.md) passed 460 backend / 182 client tests and production build at 535444d, followed by actual clean setup/startup/restart and a second 460-test backend run in the newly installed environment. The paid opt-in test was skipped. [Publication verification](improvements/25-main-publication.md) proves the remote contains the identical tested source; later differences are Markdown only. Earlier counts are historical. Rerun appropriate checks if the candidate code changes, and record the actual commit and clean/dirty status. A Git push is not an official freeze record.
4. Back up the private database with SQLite's backup API. Preserve .env, transcripts, rubric/evaluation snapshots, appeals and decisions. Keep the backup and organizer data outside Git.
5. Demo preparation is resumed. Use the disposable zero-spend workspace and [DEMO.md](DEMO.md); record actual spoken timings rather than claiming automated UI test duration as presentation length. The real DOM/API/cold-restart rehearsal passed. A fresh changed-criterion evaluation remains outside the zero-spend rehearsal; show the earlier genuine custom-checklist run as historical unless new inference is later authorized.

## When control data arrive

1. Use the existing import UI with the exact supplied group ID or upload its saved JSON. Inspect the actual count, languages, channels and any import error; the control composition need not match DEV. Unchanged imports must remain idempotent; changed content creates a revision.
2. Select the intended immutable checklist and inspect a transcript. An organizer criterion replacement must be saved through the editor, including its definition, answer type, anchors and N/A condition. Do not edit application code or prompt files to implement that replacement.
3. Import/navigation/edit/review can be performed without inference cost. New control assessments or a newly changed criterion require real provider calls. The current zero-spend task stops before those actions; neither a saved DEV result nor a mocked response substitutes for control evaluation.
4. Before later authorized inference, review the shared backend budget and opening baseline, including isolated-audit costs, historical unknown usage and overhead. Opening accounted usage$4.03490090 plus overhead$0.10 gives conservative$4.13490090 against the user's $5 task allowance; it is not an account balance. Effective BUDGET_LIMIT_USD remains0. The CLI, UI, retries and provider checks share the guard. Pure no-spend planning found ten worst-case representative reservations could exceed the hypothetical$0.86509910 remainder, while two fit. After authorization, preview actual control cases and start with two at a time, letting reservations settle. Never weaken the guard or raise the allowance automatically. [Recorded planning and limits](SUBMISSION.md). Account for unrelated/external spending; enqueue/send rechecks the quote atomically.
5. Account for every control record as complete, needs review, failed/interrupted, processing or unstarted. Inspect evidence and unresolved reasons. Use explicit retries within budget; never substitute fabricated results.
6. Before stop-code, run scripts/export_submission.py export/validate with the exact already-imported group and split=prod; require exactly10 original IDs including error records. Revalidate DEV65. Commit/push both actual files plus the tested code and verify the fetched commit/file contents. The owner makes the repository public at the deadline; verify public availability and organizer receipt when performed. Follow [SUBMISSION.md](SUBMISSION.md); no guessed group, fabricated score or local-only delivery claim.

## At and after the actual freeze

Record official timing, `git rev-parse HEAD`, `git status --short`, source checksum and control-state counts. After the actual freeze, keep application code, prompt and dependency files fixed. The guide permits processing data and saving checklist changes through the interface; preserve each version and every original/reviewed result.

| Official evidence | Current value |
| --- | --- |
| Event start / freeze time | Not supplied |
| Control group | Not supplied |
| Delivered/frozen commit | Not recorded |
| Control states | Not run |
| Public repository verification | Held by owner: do not make public yet; earlier authenticated main push verified |
| Submission confirmation | Not submitted |
