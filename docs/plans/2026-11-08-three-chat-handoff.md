# Three-chat implementation handoff

**Status: INTEGRATED — combined acceptance completed, 8 November 2026.** The original READY baseline and recovery checkpoint 91be713 are preserved. Latest cohort **28818fa** and print **be951f3** handoffs were merged locally without conflicts, mounted and tested together. **403 backend / 182 client passed, one paid opt-in skipped; production build and pip check passed.** [Integration report and visual limits](../improvements/22-cohort-print-integration.md). A4/Letter and long multilingual paper pagination remain unverified after native input control stopped. No API spend, remote publication or demo work.

The coordinator must update this file to **READY** before the two builders edit code. Until then, builders can inspect existing code read-only and propose interfaces.

## Coordinator fills during the first 30 minutes

| Field | Current value |
| --- | --- |
| Source baseline | Local commit d7d8a9d2a93ff5b537e34e689dd63b0e952f0fb3; complete audited source and reports |
| Remote main | Older checkpoint; do not use as the complete feature baseline |
| Coordinator integration branch/worktree | sprint-integration-20261108; C:\Users\user\Desktop\DataChallenge\local_data\sprint_20261108\integration |
| Cohort builder branch/worktree | sprint-cohorts-20261108; C:\Users\user\Desktop\DataChallenge\local_data\sprint_20261108\cohorts |
| Print builder branch/worktree | sprint-print-20261108; C:\Users\user\Desktop\DataChallenge\local_data\sprint_20261108\print |
| Cohort implementation handoff | 28818fa includes d3242ef and owned repairs; builder 55 backend / 42 client / TypeScript passed; coordinator mounting/exact-pair/narrow acceptance passed |
| Print implementation handoff | be951f3 includes 7a6d2a7; builder 29 tests / TypeScript passed; coordinator mounting/252-packet renderer/native print-preview passed; paper-size/stress visuals remain unverified |
| Private verification-copy paths | Each worktree's local_data/review.sqlite3; 249 evaluations / 75 sources / 15 tables; no .env copied |
| Source/data/protected fingerprints | local_data/sprint_20261108/baseline.json and baseline.sqlite3; 195 source/MD files, 30 protected files, all 15 tables/schema; prior audit parity confirmed |
| Cohort route/DTO | Contract below; owned new router only, coordinator mounts it |
| Print props | PrintableEvaluation({ evaluationId: string, updatedAt: string }); excerpt option owned by component, false initially |
| Preview server/browser | Coordinator only for combined acceptance; copied data, empty credentials, zero budget |

Acceptance repeated on the exact isolated coordinator source: **309 backend tests passed** with the external socket guard. Root client source matches the checkpoint apart from Git line-ending normalization: **118 passed / one paid opt-in skipped**, production build passed. [Baseline acceptance report](2026-11-08-baseline-acceptance.md). No inference, organizer fetch, remote push or demo work.

## Frozen interface and isolation rules

Read this canonical handoff in the original root folder; the baseline commit deliberately contains the earlier planning version. Do not replace your worktree or edit the root. No worktree has credentials. All three start at the same commit; do not rebase onto remote main. The root's original dirty work and index were preserved. Checkpoint is local only, with no publication or visibility change.

From your worktree use the absolute interpreter C:\Users\user\Desktop\DataChallenge\.venv\Scripts\python.exe with `local_data/offline_pytest.py -q <owned-test-paths>` for targeted backend tests. It supplies empty provider/organizer values, limit0, your disposable DB and an external socket guard. For other local commands first dot-source `./local_data/offline.ps1`; prefer direct Settings with empty credentials and your copy path for application construction. Do not run a live smoke/access check. Frontend dependencies may be installed with `npm ci --offline --no-audit --no-fund`; no dependency changes. Only the coordinator runs full suites or preview servers.

### Cohorts

- New router exports `router` from backend/app/api_cohorts.py. Read-only GET `/api/insights/cohorts/options` lists actual recorded dataset/checklist/provenance choices and unknown counts. POST `/api/insights/cohorts/compare` accepts `{dataset_group_id, left, right, basis, limit}`. Each selector has required positive checklist_id and optional model, prompt_version, schema_version, evidence_validation_version: absent means any recorded value, null means unknown, string means exact recorded equality. Use strict validation, reject extra fields, cap strings at150 and limit at200. Default basis effective, limit200. No caller SQL or arbitrary grouping fields.
- Select the latest `(created_at, id)` run matching each selector per exact conversation revision, retaining failed/unresolved cases. Use a single read snapshot, dataset separation and a declared deterministic page/limit coverage rule. Do not silently truncate coverage. Preserve checks for different source/checklist definitions, null totals, flags and cache reuse.
- Response version1 contains sanitized selectors, basis, dataset_group_id, coverage, pairs and criterion aggregates. Each pair identifies conversation_id/source revision/hash and left/right exact evaluation IDs or missing sides, compatibility/reasons, original/effective availability and cached_from. Detail shapes may be builder-owned but document them in stage19; shared code only consumes the owned component and pair IDs. Do not expose arbitrary raw meta/errors, source text, URLs or credentials in options/aggregates.
- `CohortComparison({onOpenPair: (leftEvaluationId: string, rightEvaluationId: string) => void})` owns its fetches/selector DTO and stylesheet. Exact pair callback fires only with two real saved IDs. Coordinator supplies the existing comparison hook. Leave mount/integration instructions in stage19; no shared file edits.

### Print

- Default export PrintableEvaluation from frontend/src/PrintableEvaluation.tsx with `{evaluationId: string, updatedAt: string}`. Fetch existing `/api/evaluations/{id}/export?format=json&include_excerpts=<boolean>` only. Include both original/effective values from that packet, never recalculate. Component owns preview/optional excerpts/retry/explicit print controls.
- Invalidate immediately on ID/update/options changes. Guard late responses by all those values and reject a mismatched packet's run ID/update identity. Null, failed and missing snapshots must remain explicit. No new routes, dependencies or shared export modifications.
- New print stylesheet must scope itself to an explicitly active preview; it must not hide or print the rest of the app during unrelated print actions. No automatic print dialog, remote assets or source HTML injection.

Both builder chats were checked idle with clean assigned worktrees and their latest handoffs were accepted by the coordinator. [Status and remaining acceptance](2026-11-08-other-chat-status.md). The [cohort prompt](2026-11-08-chat-cohort-comparison.md) and [print prompt](2026-11-08-chat-printable-reports.md) remain historical continuation instructions; do not restart completed lanes. Shared integration now includes exact two-ID navigation and the printable component with its live timestamp. No push/publication; demo deferred.

## Fixed ownership

- Other chat 1: new cohort service/router/component/types/styles/tests and stage19 report.
- Other chat 2: new printable component/renderer/styles/types/tests and stage20 report.
- This chat: backup/recovery CLI/integrity helper and stage21 report; existing shared route/UI/type/style/package/config integration; CURRENT_CONTEXT and final integration report.

Builders do not edit shared existing files. The coordinator does not overwrite builder files during active work; request a revision or take ownership explicitly after handoff. Report handoffs through the designated worktree MD files and final chat replies; no outbound messaging or public action is implied.
