# Control data and official freeze

Status: procedure ready; no official control identifier, event timing or freeze instruction has been supplied. No control run or frozen commit is claimed.

## Before the official freeze

1. Obtain the exact control group identifier, official event start/freeze time and submission destination from organizers. Do not derive them from this computer's clock or try guessed groups.
2. Review the candidate source and secret-scan evidence. The readiness work records the reviewed source in the existing private repository; verify the actual checkpoint hash and push outcome in CURRENT_CONTEXT.md. Public visibility and submission must still be performed explicitly and verified. A private checkpoint is not an official frozen version.
3. Verify setup/start instructions and required tests on the exact source being delivered. The [post-integration audit](audits/2026-11-08/02-post-cohort-print-audit.md) passed408 backend /182 client tests and production build; the paid opt-in test was skipped. Earlier counts are historical. Rerun appropriate checks if the candidate changes, and record the actual commit and clean/dirty status. A source archive or private checkpoint is not an official freeze record.
4. Back up the private database with SQLite's backup API. Preserve .env, transcripts, rubric/evaluation snapshots, appeals and decisions. Keep the backup and organizer data outside Git.
5. Demo work is currently deferred by the user. Once explicitly resumed, rehearse the five-minute presentation and record actual timings in [DEMO.md](DEMO.md); do not start rehearsals under the present scope.

## When control data arrive

1. Use the existing import UI with the exact supplied group ID or upload its saved JSON. Inspect the actual count, languages, channels and any import error; the control composition need not match DEV. Unchanged imports must remain idempotent; changed content creates a revision.
2. Select the intended immutable checklist and inspect a transcript. An organizer criterion replacement must be saved through the editor, including its definition, answer type, anchors and N/A condition. Do not edit application code or prompt files to implement that replacement.
3. Import/navigation/edit/review can be performed without inference cost. New control assessments or a newly changed criterion require real provider calls. The current zero-spend task stops before those actions; neither a saved DEV result nor a mocked response substitutes for control evaluation.
4. Before later authorized inference, review the shared backend budget and opening baseline, including isolated-audit costs, historical unknown usage and overhead. Current conservative accounting is $4.13490090 against the user's $5 task allowance; it is not an account balance. BUDGET_LIMIT_USD remains zero by default. The CLI, UI, retries and provider checks now share the guard. Account for any unrelated/external spend before deliberately enabling new paid requests. A preflight quote is rechecked atomically at enqueue/send.
5. Account for every control record as complete, needs review, failed/interrupted, processing or unstarted. Inspect evidence and unresolved reasons. Use explicit retries within budget; never substitute fabricated results.

## At and after the actual freeze

Record official timing, `git rev-parse HEAD`, `git status --short`, source checksum and control-state counts. After the actual freeze, keep application code, prompt and dependency files fixed. The guide permits processing data and saving checklist changes through the interface; preserve each version and every original/reviewed result.

| Official evidence | Current value |
| --- | --- |
| Event start / freeze time | Not supplied |
| Control group | Not supplied |
| Delivered/frozen commit | Not recorded |
| Control states | Not run |
| Public repository verification | Pending; repository currently private |
| Submission confirmation | Not submitted |
