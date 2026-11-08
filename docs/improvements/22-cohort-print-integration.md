# Stage 22 — cohort comparison and printable reports integrated

**Scope follow-up, 8 November:** the user deferred the remaining optional A4/Letter and multilingual paper-layout checks after Computer Use could not verify Chrome's URL. Reviewed/unresolved paper layouts remain unverified; existing saved-report tests and observed previews are retained. This is not a required-PDF workflow blocker and does not change the integrated implementation or any saved result. [Current print status](20-printable-saved-reports.md). No API spending; demo deferred. The original acceptance record below remains historical.

Completed 8 November 2026 using the latest handed-off work from both other chats. Their original worktrees and commits are preserved. No model, organizer or provider-access request was made; added inference spend is **$0.00**. The five-minute demo remains deferred.

## Accepted source and integration

- Cohort handoff **28818fa75e5d948424f43053fb97b4d6a8e8e484** includes the earlier d3242ef implementation plus malformed-metadata, nested-response, exact-identity and disclosure-refresh repairs. It was merged into the recovery coordinator through local merge **a47ad4d**.
- Print handoff **be951f39f28d808d130ea98c099a00269c45e75d** retains the 7a6d2a7 implementation and updated verification report. It was merged through local merge **bd9385d**. Both merges completed without conflicts.
- Both other chats were checked idle with clean assigned worktrees. The coordinator took ownership of shared mounting and integration fixes after handoff; no chat was restarted or its completed files replaced.

The existing insights router now includes the cohort router exactly once. The review queue mounts the cohort tool in its existing secondary tools. Recorded selectors, explicit coverage, criterion transitions and exact-pair inspection use stored data only. Missing, failed, unresolved, incompatible and cache/provenance cases remain explicit; an aggregate delta is not a measure of scoring accuracy.

Opening a cohort pair verifies both returned run IDs and their identical nonempty source-revision ID before navigation. The review route retains both exact IDs, loads the baseline even beyond the first saved-history page, and opens the comparison tools. Navigation-generation guards discard a delayed response after the user leaves. Existing queue continuity, history pages, evidence links and comparison refresh are retained. The cohort preview preserves its selected answer basis; the review comparison starts with Effective answers and explicitly offers Original through its existing selectors.

The selected assessment mounts the printable report alongside existing exports. Its current saved ID and update timestamp control report identity. Changing a run or reviewed result invalidates the old preview. The report consumes the existing sanitized JSON export, includes both original and effective results, and uses an isolated sandboxed document with explicit printing and optional excerpts. It does not recalculate scores, fetch a model, expose recording links or insert active source HTML.

Integration testing found and corrected two shared defects: identical sibling keys for export/print were replaced with a print-specific key; an unavailable exact baseline now has an explicit unavailable option and survives disclosure close/reopen without silently selecting a different recent run. An initial incomplete synthetic comparison fixture was corrected. The first build also caught a helper/prop naming collision; the helper was renamed. Final tests and build passed after these corrections.

## Commands and outcomes actually run

Commands below ran in the coordinator worktree unless otherwise stated. Frontend commands ran in its frontend directory. Backend tests used empty provider/organizer values, a disposable database, limit zero and an external-socket guard.

| Check | Actual result |
| --- | --- |
| `npm ci --offline --no-audit --no-fund` | 115 existing pinned packages installed; no dependency or lockfile changes |
| Absolute root `.venv/Scripts/python.exe local_data/offline_pytest.py -q` | **403 passed**, 77.62s; one existing Starlette/AnyIO deprecation warning |
| `CQA_LIVE_SMOKE=0; npm test` | **182 passed, one paid opt-in skipped**, 39.68s |
| `npm run build` | TypeScript and production Vite build passed, 2.22s |
| Root `.venv/Scripts/python.exe -m pip check` | No broken requirements |
| New mounted-router tests | Two passed; actual app routes, exact pair/export parity, bounds, origin checks, no-store and copied-row preservation |
| New client integration tests plus existing history integration | 16 passed, including five new cross-feature regressions |
| Private `verify_saved.py` | 20 cohort scenarios, 376 exact-pair requests, 249 JSON exports and three excerpt-enabled packets passed through the mounted app |
| Private `combined_saved.audit.ts` | All 252 actual packets rendered; 2,014 criterion entries / 3,212 original/effective judgments preserved; all 20 cohort and 376 pair DTOs accepted |

The private exhaustive renderer run initially exceeded Vitest's five-second per-test default. Its private acceptance configuration was raised to 30 seconds; unchanged assertions passed in 6.44s. Ordinary product test limits were not increased. A build command initially issued from the worktree root failed because package.json is in frontend; the corrected command above passed. These failed attempts are not counted as passes.

## Saved-data and browser acceptance

Private evidence is retained under ignored `local_data/cohort_print_integration_20261108`. A consistent execution-start SQLite backup was made using a raw read-only main connection. Application construction and requests ran only on separate copies. Each copy's single expected budget-state bootstrap row matches the retained private baseline; the main database was never initialized by this task.

The 249 exports matched every stored original/effective result and score snapshot exactly. The actual selected cases include reviewed Kazakh p1-kz-012 (84.62 original / 100.00 effective) and unresolved Russian call p4-ru-005 (92.31 original / unavailable effective). Their values were checked through export and renderer acceptance; they were not newly adjudicated.

A legitimate first-party local browser session opened the guarded copied-data application. It observed the recorded v10-to-v11 cohort comparison, nine paired sources, seven comparable totals, 56 candidate-missing sources and two failed/interrupted cases. It opened p1-en-002's exact pair and verified that the review route and both comparison selectors retained the two inspected IDs. At a 320px viewport the document width was 305px including scrollbar allowance, with no page-level horizontal overflow. The report preview opened, and the explicit print action produced a native ten-page saved-report preview with repeated table headings and stored totals. No physical print or PDF save was submitted.

**Visual limits:** further native controls were blocked by user-input detection. A4/Letter paper selection, long multilingual stress pagination and a full visual pass through reviewed/unresolved reports remain unverified. Automated multilingual serialization and narrow application checks do not establish those paper-layout results. The earlier native Chrome URL verification stop was not retried or bypassed. The temporary acceptance tab was closed, viewport override reset and owned preview server shut down; its provider, external HTTP/socket and blocked-write counts were all zero.

## Preservation and remaining work

Final acceptance checks cover every one of the main database's 15 tables and schema/index SQL, all 249 evaluations, 75 immutable source revisions, five checklists, nine appeals/nine reviews and all 30 protected files. Main budget_state remains empty. All unrelated pre-existing source/config/test files and the user's staged index are preserved. New code is mirrored into the shared working folder only after checking its execution-start hashes; the isolated integration branch supplies a local checkpoint. No remote push, publication or visibility change is performed.

This completes functional integration, not an official PDF regrade or new judgment-accuracy validation. Remaining product acceptance is the bounded paper-layout pass above. Existing wider delivery gaps remain: independent/current-configuration accuracy evidence, approved policy material, organizer-held control/replacement data, the unclear call introduction and final public/event handoff/freeze. The manual review packet is not reinstated as a requirement. **Next concrete step:** when native browser control is available, finish A4/Letter and long multilingual print acceptance without changing saved results or calling a model. Demo preparation remains deferred.

Final shared-folder verification passed: **34 files mirrored**, exactly five existing source integrations; all **129 unrelated pre-existing non-Markdown files** preserved. All **155 source/config/test files** match the tested coordinator source, allowing Git line-ending normalization. The shared-folder production build also passed (Vite 2.27s) and emitted the same asset names as the coordinator. Source/history scan: **227 candidate files / 438 then-reachable Git blobs**, zero credential/private-path matches; **72 Markdown files / 335 local links**, diff check passed. Both builder branches still point to their accepted commits with clean worktrees. Post-checkpoint verification is recorded in CURRENT_CONTEXT and private evidence; no remote publication is implied.

Combined code/report checkpoint **21835a52be79d5af092b24d5250db05dbfaabccf** is local on sprint-integration-20261108. Root main's original commit/index is retained with the tested integrated working source. Private `mirror_and_verify.py`, `finalize.py` and `final_checks.py` passed: all 227 Git-visible files match that checkpoint, 193 unrelated pre-existing files and all data/protected files are intact; 453 reachable history blobs at that checkpoint have zero credential/private-path matches. This final note is a documentation follow-up, not a new implementation/test-suite run.
