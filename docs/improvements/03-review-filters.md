# Stage 3 — Pending appeals and critical findings

Status: **PASS**, 7 November 2026. New hosted-model requests: **0**.

## Completed

- Added combinable pending-appeal and critical-finding filters beside the existing dataset/language/channel/status/search controls.
- Queue data include open-appeal counts and direct review targets. Pending appeals on earlier runs remain visible. For a latest-source queue, appeals on superseded revisions also remain discoverable, linked to their actual older transcript/evaluation rather than the latest revision's evidence.
- Counts respect the selected checklist and dataset/source namespace. Resolving an appeal removes it from the pending data on refresh.
- Critical findings use the latest selected run's **effective** unscored flags, including configured flag IDs. They remain separate from numerical totals. “No recorded critical findings” does not claim an unevaluated conversation is violation-free.
- Review/finding links select the actual saved run and focus/highlight its criterion. Original evidence and separate reviewer action remain available.

## Verification

Backend integration tests verify pending appeals across runs/revisions, exclusion of other checklist versions, clearing after a saved review and effective critical flags without a score penalty. Client tests combine dataset/language/pending/critical filters, check older-revision links and refresh removal. Filtering invokes no model request.

The final suite passed **125 backend / 14 client tests**. Actual browser verification used one clearly labeled technical appeal in a database copy: the DEV pending filter showed its single row, the review link focused the correct criterion/run, and evaluation was disabled by budget. The DEV critical filter displayed four stored positive findings; this is a recorded count, not independent verification of those model judgments. Actual HTTP confirmation cleared the technical appeal without inference. Queue data were identical after cold restart.

All 65 copied DEV original/effective assessments and scores matched the pre-change backup before the technical review. The main database's six appeals/six reviews and every original row were preserved. No production role/authentication, new judgment, external organizer message or automatic critical-flag penalty was added.

Next: complete independent human review using the existing packet and review workflow; use the filters to find saved disputes. Official control data remain an organizer dependency.
