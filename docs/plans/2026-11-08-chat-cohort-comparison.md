# Prompt for other chat 1 — saved-run cohort comparison

Implement saved-run cohort comparison for C:\Users\user\Desktop\DataChallenge.

Read MASTER_CONTEXT.md, CURRENT_CONTEXT.md, docs/plans/2026-11-08-eight-hour-improvement-plan.md and docs/plans/2026-11-08-three-chat-handoff.md. Your lane is COHORTS. The coordinator in the original chat owns shared integration files and backup/recovery work. Another chat owns printable reporting.

Use only the isolated worktree and common audited baseline recorded in the handoff file. Remote main is older than the current audited local solution; do not build from it blindly. If handoff status is not READY, limit work to read-only inspection and interface proposals until the coordinator supplies the baseline/worktree. Do not edit the shared main working folder or create a competing baseline.

Build a real read-only comparison of two cohorts of existing saved evaluations. Select cohorts using recorded checklist/model/prompt/schema/validation provenance; missing metadata remains unknown. Pair only exact source revisions with a declared deterministic selection rule. Show matched/missing/failed/unresolved/incompatible coverage, criterion answer/disposition transitions, and comparable point differences. Keep datasets separate, show cache lineage, and open an exact saved-pair drilldown. Limit interactive requests to 200 pairs. A higher operator score is not evidence of higher evaluator accuracy.

Reuse existing saved-result/comparison contracts. Work in new cohort-specific service/router/component/type/style/test files only. Proposed route prefix: /api/insights/cohorts; finalize the DTO with the coordinator before coding. Do not edit main.py, insights_api.py, App.tsx, Conversations.tsx, Detail.tsx, shared types/styles, existing evaluator/scorer/export/DB code, dependencies or CURRENT_CONTEXT.md. Send required shared-file changes as precise integration notes.

Preserve originals, reviews, seeds, credentials and concurrent work. Do not call a hosted model, check paid provider access, fetch organizer data, re-score records, change paid limits, add a schema migration, publish or prepare the demo. Use temporary/private database copies with empty credentials and provider/network guards.

Test compatibility, null/N/A/flag transitions, missing cases, identical timestamps, cache lineage, source identity, stale/error responses and actual saved pairs. Acceptance requires real saved-data behavior, not a static or mock-only screen. Run targeted tests; leave the full combined suite to the coordinator.

Target a tested handoff by elapsed hour 4:30. Write docs/improvements/19-cohort-comparison.md in your worktree: actual commands/results, changed files, remaining limits, proposed shared hooks, and exact DTO/route contract. Return the worktree/branch or commit reference and those instructions. Do not stage unrelated files, merge into main or push. After handoff, change owned files only to fix integration findings and report each revision.
