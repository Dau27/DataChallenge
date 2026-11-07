# Three-chat implementation handoff

**Status: NOT STARTED — planning only.** No implementation worktrees or new baseline commit have been prepared by this planning task.

The coordinator must update this file to **READY** before the two builders edit code. Until then, builders can inspect existing code read-only and propose interfaces.

## Coordinator fills during the first 30 minutes

| Field | Current value |
| --- | --- |
| Source baseline | Audited local source: 309 backend / 118 client passed; exact new baseline reference pending |
| Remote main | Older checkpoint; do not use as the complete feature baseline |
| Coordinator integration branch/worktree | Pending setup |
| Cohort builder branch/worktree | Pending setup |
| Print builder branch/worktree | Pending setup |
| Private verification-copy paths | Pending setup; credentials excluded |
| Source/data/protected fingerprints | Capture at execution start; latest audit evidence under ignored local_data/pdf_audit_20261108 |
| Cohort route/DTO | Proposed /api/insights/cohorts prefix; coordinator and builder finalize before coding |
| Print props | Exact saved run/update identity and excerpt options; coordinator and builder finalize before coding |
| Preview server/browser | Coordinator only for combined acceptance; copied data, empty credentials, zero budget |

## Fixed ownership

- Other chat 1: new cohort service/router/component/types/styles/tests and stage19 report.
- Other chat 2: new printable component/renderer/styles/types/tests and stage20 report.
- This chat: backup/recovery CLI/integrity helper and stage21 report; existing shared route/UI/type/style/package/config integration; CURRENT_CONTEXT and final integration report.

Builders do not edit shared existing files. The coordinator does not overwrite builder files during active work; request a revision or take ownership explicitly after handoff. Report handoffs through the designated worktree MD files and final chat replies; no outbound messaging or public action is implied.
