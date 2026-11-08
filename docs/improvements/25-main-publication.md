# Stage 25 — main pushed to GitHub and verified

Completed 8 November 2026 under the user's explicit instruction to push main. GitHub main advanced from **5b726f9e3bb5b2899a6d8b98edfbf737f79e6cdf** to application/documentation checkpoint **f481908d5fde2be7a722a444624907df4042e2da**. A fresh fetch verified the exact commit and complete tree, not only a successful push message. [Published checkpoint](https://github.com/Dau27/DataChallenge/commit/f481908d5fde2be7a722a444624907df4042e2da).

The published checkpoint contains tested merge **535444d9e8e905c24413faf70f98c1b52da6eac6**. All **159 source/config/test files** have identical Git blob IDs to that tested merge. Changes after the tested merge are **Markdown only**. Publication does not create a new scoring result or require another inference run. **No API spending; saved results preserved; demo deferred.**

## Pre-push checks

- Local main was clean at f481908. The configured fetch and push destinations were verified as the existing Dau27/DataChallenge GitHub repository. No active pre-push hook or custom hook path was present; there was no hidden live-evaluation hook to run.
- Captured a fresh private preservation baseline for all 15 SQLite tables/schema, 249 evaluations, 30 protected files and 159 source files. The application/database constructor was not used. Main budget_state remained empty.
- Source/history and Markdown scan passed before publishing:235 candidate files,486 then-reachable blobs,76 Markdown files,366 local links; zero credential/private-path matches and clean diff check. .env, SQLite, recordings, saved-data copies, local backups and private acceptance logs remain excluded from Git.
- Reused the exact-source acceptance from [stage 24](24-main-sprint-merge.md):460 backend tests in both existing and newly installed environments; 182 client tests passed/one paid opt-in skipped; production build, fresh setup/startup/restart, recovery and CLI handoff checks passed. No new application test run or live provider result is claimed for this documentation/publication task.

## Publication and independent remote verification

Commands ran through an ignored private wrapper with empty provider/model/organizer settings, zero inference budget and noninteractive Git authentication. Only the explicitly selected main ref was pushed; no force update, tags, safety refs or builder branches were sent.

```powershell
git fetch --no-tags origin refs/heads/main:refs/verification/main-publish-20261108/code
git -c push.followTags=false push --porcelain origin f481908d5fde2be7a722a444624907df4042e2da:refs/heads/main
git ls-remote origin refs/heads/main
git fetch --no-tags origin refs/heads/main:refs/verification/main-publish-20261108/code-verified
```

Verified outcomes:

| Check | Actual result |
| --- | --- |
| Previous remote main | 5b726f9e3bb5b2899a6d8b98edfbf737f79e6cdf |
| Pushed local main | f481908d5fde2be7a722a444624907df4042e2da |
| Advertised remote main | Same f481908 commit |
| Freshly fetched remote main | Same f481908 commit |
| Fetched full tree | 33d396c7f2e8c7ff6620fdf4838c2698e68d4136, identical to local |
| Tested merge 535444d | Ancestor of fetched main |
| All 159 tested source/config/test blobs | Identical; all other differences Markdown only |

The commit containing this report is a Markdown-only publication follow-up. Its push repeats the same advertised-SHA, fresh-fetch, whole-tree, tested-ancestor and source-blob checks. [Main history](https://github.com/Dau27/DataChallenge/commits/main) shows the current documentation head; the final exact commit/tree receipt is retained in ignored local_data/main_publish_20261108/reports_verification.json and reported in the task reply. This avoids pretending that a commit can embed its own final hash.

## Preservation and scope

Private before/after fingerprints cover every main table/schema and all 249 evaluations, original/effective snapshots, review/appeal history, source index,30 protected files and 159 unchanged sources. Main was never initialized, no model/provider/organizer access check was made, no organizer conversation data was fetched or regraded, and no budget reservation was created. Only GitHub transport was used for publication. User credentials and all private results remain local/ignored.

Final publication verification and source/history/MD scans are recorded in CURRENT_CONTEXT and private evidence. No application code changes after the tested merge, no new semantic-accuracy estimate, no repository-visibility change, organizer submission or official event freeze is claimed. Public anonymous accessibility is separate from authenticated Git verification. The unclear call, genuine reference/control inputs and optional print-paper acceptance remain unresolved. **Paid inference stays paused and the demo stays deferred.**

After the application push, independent raw read-only fingerprints again matched all 15 main tables/schema, 249 evaluations, 30 protected files and 159 source files; main budget_state remained empty. Before committing this report follow-up, source/history/Markdown checks passed 236 candidates / 486 then-reachable blobs / 77 Markdown files / 375 local links, zero credential/private-path matches and clean diff check. Private finalization repeats those preservation checks after the report commit is advertised/fetched from GitHub; no application or private-data change is part of the follow-up.
