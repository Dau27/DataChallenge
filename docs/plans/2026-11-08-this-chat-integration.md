# This chat's eight-hour role — three-chat configuration

Started 8 November 2026. This adapts the [four-lane plan](2026-11-08-eight-hour-improvement-plan.md) to **this chat plus two others**. [Baseline/worktrees are READY](2026-11-08-three-chat-handoff.md); [CLI recovery is implemented and tested](../improvements/21-backup-recovery.md). The schedule below retains the original execution gates. Builder features remain separate until accepted and integrated.

## Assignment

- Other chat 1: [cohort comparison prompt](2026-11-08-chat-cohort-comparison.md).
- Other chat 2: [printable-report prompt](2026-11-08-chat-printable-reports.md).
- This chat: **common baseline, a narrowly scoped backup/recovery CLI, shared integration, final verification and reports**.

To make this realistic in eight elapsed hours, the backup lane stays CLI-only. The optional health dashboard, extra cohort charts and bulk printing are deferred. Integration wins over scope expansion.

## Work here

### 0:00–0:30 — establish a common source and contracts

1. Recheck changes from all chats and capture current source, the full database/index/schema and protected-file fingerprints. Preserve all existing changes and secrets.
2. Prepare a local development checkpoint from the complete audited working source. Older remote main is not a sufficient baseline. Do not change repository visibility or perform official/event freeze work.
3. Create isolated worktrees for both builders. Give each a copied/temporary database, empty provider configuration, zero budget and provider/network guards. Never copy .env into their worktrees.
4. Freeze route/DTO/component props and exact shared-file ownership. Publish actual baseline/worktree references in [the handoff file](2026-11-08-three-chat-handoff.md), mark it READY, then launch the two prompts.

### 0:30–3:00 — implement bounded backup/recovery

Reuse existing SQLite backup and preservation logic to provide:

- A private backup plus manifest/checksum and logical data/schema fingerprints.
- Verification of SQLite integrity, foreign keys, checklist/source identity and original-plus-review preservation.
- Restore to a **new target only**, refusing the active database or any existing target.
- Clear derived-index status, reusing existing index maintenance rather than another rebuild mechanism.

Own new helper/scripts/tests only. No new database schema, provider call, scoring change, automatic repair, destructive restore or administration screen. Backups contain private source data; credentials remain outside them and backups stay ignored/private.

Write stage21's report with actual copied-data recovery/refusal tests. A report-only screen does not substitute for a working command.

### 3:00–4:30 — finish recovery acceptance and review builders

- Complete restore/corruption/target-refusal checks and compare copied originals to the baseline.
- Check builder DTOs, source/basis identity, missing/incompatible cases and report privacy before integration.
- Prepare the smallest shared route/UI hooks without editing files still owned by builders.
- Require each builder's tested artifact, changed-file list, known limits and MD handoff by hour4:30. Clarify ownership before a follow-up edit.

### 4:30–5:30 — integrate sequentially

Integrate accepted cohorts and print reporting one at a time. This chat alone edits main.py, insights_api.py, App/Conversations/Detail/SavedExport hooks, existing shared types/styles/config and CURRENT_CONTEXT. Keep builders available for their own regression fixes.

Use the current design's secondary-tool disclosures and exact source/run identities. Do not redesign navigation or add extra capabilities during integration.

### 5:30–7:00 — verify the combined candidate

- Full guarded backend suite, ordinary bounded-worker client suite, production build and dependency checks.
- Actual saved/copied cohort pairs and exact-pair drilldowns; missing/incompatible/null/flag cases.
- Real copied backup → verified fresh-path recovery; corruption and existing-target refusals.
- Actual saved print packets, long multilingual text, source escaping/privacy and browser/paper layouts.
- Existing review/comparison/search/history/export/insight interactions on a dedicated copy with a zero-credential preview.
- All pre-existing records/index/schema/protected files against execution-start fingerprints; source/history secret scan and MD links.

Do not invent future pass counts or call hosted inference. The 309/118 audit is the baseline, not proof that new code passed.

### 7:00–8:00 — defects, documentation and checkpoint

Fix only reproducible regressions. Update feature MDs, README/CURRENT_CONTEXT and a final integration report with actual commands, outcomes, preservation evidence and limitations. Retain a reviewed local checkpoint. No demo preparation, publication, organizer messages or official freeze.

## Cut rules

- If backup/recovery is not complete by hour3, stop adding options and keep only create/verify/fresh-path recovery; preserve integration time.
- If a builder misses hour4:30, keep unfinished work isolated. Integrate accepted work only.
- If combined checks expose a blocking regression, fix it or remove the unfinished addition from the candidate. Never reset/discard unrelated working files.
- No new feature after hour4:30. No health UI, extra charts, bulk print or dependency upgrades in this version.

Known accuracy/organizer/audio/publication gaps remain outside this sprint. API spending stays zero and the demo stays deferred.
