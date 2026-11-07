# Updated prompt — cohort comparison verification and handoff

Resume the COHORTS lane. The coordinator checked both chats and worktrees on 8 November: this implementation already exists at **d3242ef**, with a clean worktree. Preserve it and finish verification/handoff; do not restart or replace it. The builder previously reported 50 backend / 27 client tests and TypeScript passing. Those are historical outcomes, not a claim of a new rerun.

## Exact workspace and authority

- Work only in **C:\Users\user\Desktop\DataChallenge\local_data\sprint_20261108\cohorts** on **sprint-cohorts-20261108**.
- Common audited baseline: **d7d8a9d2a93ff5b537e34e689dd63b0e952f0fb3**. The coordinator's separate recovery checkpoint is 91be713; do not rebase onto it or older remote main.
- First read the CANONICAL root files: C:\Users\user\Desktop\DataChallenge\MASTER_CONTEXT.md, C:\Users\user\Desktop\DataChallenge\CURRENT_CONTEXT.md and C:\Users\user\Desktop\DataChallenge\docs\plans\2026-11-08-three-chat-handoff.md. The root handoff is **READY**; the old planning copy committed inside your worktree is superseded.
- Inspect your Git status/history and docs/improvements/19-cohort-comparison.md before editing. Preserve unexpected concurrent work. Do not reset/clean/recreate worktrees or copy credentials.

## Work now

Audit your existing owned implementation against the frozen contract. Fix reproducible defects only. Ensure recorded checklist/model/prompt/schema/evidence-validation selectors retain omitted=any, null=unknown, exact-string meanings; latest `(created_at,id)` selection per exact revision retains failed/unresolved runs. Keep datasets separate and the 200-pair bound explicit. Cover missing/failed/pending/unresolved/incompatible/no-numeric cases, criterion transitions, recorded point differences, cache lineage and exact pair IDs. Scores/differences are stored operator judgments, not measured evaluator accuracy. No new scoring or inference.

Keep existing interfaces: GET `/api/insights/cohorts/options`, POST `/api/insights/cohorts/compare`, router export from backend/app/api_cohorts.py; `CohortComparison({onOpenPair(leftEvaluationId, rightEvaluationId)})`. The pair preview must retain its requested original/effective basis and source/run/update guards. Document that the existing review screen owns its basis selectors; do not silently substitute effective for original.

Run the owned targeted tests and actual supplied-copy checks with empty credentials and external-network guards. Use **C:\Users\user\Desktop\DataChallenge\.venv\Scripts\python.exe** with `local_data/offline_pytest.py -q backend/tests/test_cohort_comparison.py backend/tests/test_cohort_saved_copy.py`; supplied DB is your worktree's local_data/review.sqlite3. For other local commands dot-source ./local_data/offline.ps1. Frontend: owned Vitest files only with maxWorkers2, TypeScript, and existing actual-response contract bridge. Use offline pinned dependencies only. Do not run full suites or preview servers; the coordinator owns combined/browser acceptance.

## Ownership and return

Own only the 12 new cohort files listed in stage19, including your service/router/components/types/scoped CSS/tests/report. Do not edit root/shared files, main.py, insights_api.py, App/Conversations/Detail, shared types/styles/config, evaluator/scorer/DB, dependencies or CURRENT_CONTEXT.md. Shared mounts, exact two-ID review hooks, combined suites/build and browser acceptance remain coordinator work. No new features beyond this contract.

Update your stage19 report with actual commands/outcomes, defects fixed, exact router/UI hooks and remaining checks. If nothing changed, state that clearly. Return **READY FOR INTEGRATION**, current full commit ID, changed-file list, test results and limits. Commit only owned changes locally if needed; no merge or push.

**Preserve originals/reviews/appeals/seeds/protected files and secrets. No hosted API/provider access checks, organizer fetches, new evaluations, paid-limit changes, publication or demo work. Added API spend must remain $0. Demo deferred.**
