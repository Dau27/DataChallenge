# Prompt for other chat 2 — printable saved reports

Implement printable saved-evaluation reports for C:\Users\user\Desktop\DataChallenge.

Read MASTER_CONTEXT.md, CURRENT_CONTEXT.md, docs/plans/2026-11-08-eight-hour-improvement-plan.md and docs/plans/2026-11-08-three-chat-handoff.md. Your lane is PRINT. The coordinator in the original chat owns shared integration and backup/recovery work. Another chat owns cohort comparison.

Use only the isolated worktree and audited baseline recorded in the handoff file. If status is not READY, inspect existing export/UI contracts read-only and propose your interface until the coordinator supplies the worktree. Do not start from older remote main or modify the shared main working folder.

Build a one-run print preview and readable printable report from the EXISTING sanitized export packet. Include source revision/checklist/run identity, original/effective judgments and totals, weights/points, sections, explanations, evidence IDs and reviewer history. Source excerpts are optional using the existing export policy. Preserve N/A denominators, null totals, unscored flags and recorded provenance; do not present a weight simulation as a real evaluation. Explanations can quote private source text, so do not claim the report is anonymous.

Support RU/KZ/EN characters, long explanations, sensible page breaks and repeated table headings. Add accessible preview/print controls, loading/error/retry and stale-response handling keyed to the exact run/update/basis/options. Treat source values as escaped data. Exclude recording URLs and credentials; do not add active source HTML/scripts or remote assets. Printing/Save as PDF remains an explicit user action; do not open print dialogs automatically.

Work only in new PrintableEvaluation.tsx, printEvaluation.ts, printEvaluation.css, owned types/tests and your report. Reuse existing JSON export/read APIs; no new backend is expected. Agree component props with the coordinator. Do not edit existing Detail/SavedExport/App/main files, shared types/styles, export sanitization, dependencies or CURRENT_CONTEXT.md. Provide exact hook instructions instead.

No hosted-model/provider checks, organizer fetch, schema changes, judgment edits, paid-limit changes, new PDF service/library, publication or demo work. Preserve originals/secrets/concurrent changes. Use copied data with provider access forbidden.

Test exact saved-value parity, reviewed/unresolved results, option/run changes and late responses, privacy/HTML escaping, keyboard/error behavior and long multilingual print layout. Visually inspect a rendered/print preview from actual saved/copied packets; clearly label synthetic fixtures. Run targeted tests; the coordinator owns full combined checks.

Target a tested handoff by elapsed hour 4:30. Write docs/improvements/20-printable-saved-reports.md in your worktree with actual commands/results, files changed, limitations, visual checks and exact integration props/hooks. Return the worktree/branch or commit reference. Do not stage unrelated files, merge into main or push. After handoff, change owned files only to fix integration findings and report each revision. Bulk printing is outside scope.
