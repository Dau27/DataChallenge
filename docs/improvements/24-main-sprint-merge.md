# Stage 24 — sprint integration merged into main

Completed 8 November 2026. Local **main** now includes sprint-integration-20261108 through merge **535444d9e8e905c24413faf70f98c1b52da6eac6**. Existing working changes and saved results are preserved. **460 backend / 182 client tests passed**, one paid client test skipped; production build, fresh setup/startup, restart, recovery and CLI handoff checks passed. **No provider/organizer request or inference spending. Demo remains deferred.**

## Preservation and merge

Started at main **5b726f9e3bb5b2899a6d8b98edfbf737f79e6cdf**, integration **0d95621799b0b9e033656289dcf8472ba106e9bf**. Main had 120 status entries, including directories representing multiple files. The staged patch was empty. All 234 Git-visible working files matched the 234-file integration tree, allowing Git line-ending normalization; there were no root-only, branch-only or differing files. These working changes were already the accepted integrated source, not an unrelated set to discard.

Before mutation, created a private consistent SQLite backup and all-table/schema fingerprints, copied all 234 working files, captured staged/unstaged patches and index/status inventories, and made an all-ref Git bundle. Local safety ref safety/main-before-sprint-merge-20261108 retains the original main. All artifacts stay under ignored local_data/main_sprint_merge_20261108; the database/recovery bundle contains private source/recording references and must not be published. The actual .env was not copied into the verification checkout or Git.

Checkpoint **81a27bd11f712988a6f558c5e8e5377a976a621a** committed the accepted working source on main. Its staged tree was verified equal to the integration tree before commit. Then:

```powershell
git merge --no-ff sprint-integration-20261108 -m "Merge sprint integration with preserved working changes"
```

The merge completed with **zero conflicts**. Parents are 81a27bd and 0d95621. Its tree equals the integration tree, and all 234 original working files remained **byte-for-byte unchanged** after checkpoint/merge. No stash, reset, checkout-overwrite, source deletion, schema change, rubric/evaluator/scorer change or feature addition was used. The initially empty staged patch is now a clean committed index; no staged content was lost. Existing builder/coordinator/older worktrees are retained.

## Exact-source tests and clean setup

Created detached verification worktree local_data/main_sprint_merge_20261108/verified at 535444d, with a separate coordinator-data copy at its ignored local_data/review.sqlite3. It has no user credential configuration. Verification source matches the merged main code; subsequent main commits for this task contain documentation only.

| Actual command/check | Outcome |
| --- | --- |
| Private socket-guarded run_tests.py, using existing pinned interpreter on exact checkout | **460 passed**, 102.88s; zero external connection attempts |
| `npm ci --offline --no-audit --no-fund` in verified/frontend | 115 pinned packages installed, 16s; no lockfile/dependency changes |
| `CQA_LIVE_SMOKE=0; npm test` | **182 passed / one paid opt-in skipped**, 39.82s |
| `npm run build` | TypeScript/Vite passed, 2.34s;62 modules; existing CSS/JS asset names retained |
| 24 pinned Python wheels fetched from official PyPI into private wheelhouse | Succeeded; package download only, no provider/organizer access |
| Actual `scripts/setup.ps1` from fresh checkout with fresh .venv | Succeeded: all 24 locked Python packages installed from local wheelhouse with pip no-index; npm offline install 115 packages/ 15s; production build passed, 2.15s; only the checkout's ignored blank .env created |
| Fresh .venv `pip check` and installed-version comparison with requirements.lock | Clean; all 24 pinned distributions match |
| Same guarded full backend suite using the newly installed .venv | **460 passed**, 97.69s; zero external connection attempts |
| Root existing environment `pip check` | No broken requirements |

Both backend runs retain the existing Starlette/AnyIO deprecation warning. No paid opt-in test or live model check was enabled. Python wheels were fetched as ordinary free package downloads; all application/runtime checks kept credentials empty and budget zero. No package versions or dependency files changed.

## Handoff verification

The private acceptance harness runs the actual **start.ps1 -SkipBuild** from the verification checkout, in hidden owned processes bound to 127.0.0.1:8000. A private process-local guard asserts an allowed disposable database, empty provider/model/organizer configuration and zero budget. It forbids provider/external HTTP/socket requests and application writes during HTTP inspection, and exposes a token-protected local shutdown hook. This guard is ignored test infrastructure, not application source or a production endpoint.

Three successful runs covered empty-data startup, saved-data startup and saved-data cold restart. **55 HTTP requests** verified the production HTML/assets, initial checklist, visible unconfigured-provider/paused-budget states, empty data, all 249 saved assessments/75 source revisions, English/reviewed-Kazakh/unresolved-Russian snapshots, exact original/effective comparisons, JSON export exclusion policy and the mounted cohort tool. Saved-data initialization added only the expected single budget-baseline row in its copy; every other table and schema matched the backup. Restart and requests changed no copied rows. All provider/external HTTP/socket/blocked-write counters were **zero**, and all owned servers stopped cleanly.

The first private handoff attempt incorrectly assumed the first returned checklist was v1, although the API intentionally returns newest first. It stopped safely with zero external/provider attempts and retained its private artifacts. The corrected harness selects exact v1 and passed all three runs on new copies. This was a verification assumption error, not a product defect or a passing first attempt.

Additional handoff checks used the **fresh installed interpreter and exact merged source**:

- Actual workspace backup CLI **create → verify → fresh-path restore** passed. Independent fingerprints prove all 15 restored tables/schema equal the execution-start backup, including 249 evaluations and original/review histories. Historical contract warnings remain warnings; no record was repaired or regraded.
- Actual quality-report CLI passed over 65 explicitly selected original DEV runs / 520 judgments. With no independent references, it correctly reports **unlabeled**, metrics null and zero disagreements; it does not invent accuracy. Main data/protected files and the source-copy bytes are preserved.
- Fresh preflight correctly exits 1 for missing provider/organizer configuration. This is an honest access blocker for new evaluations, not a successful provider-access check. Saved workflows remain available at zero budget.

Private evidence: before.json/before.sqlite3, before.bundle and source/patch backups; merge.json; backend_guard.json/backend_guard_fresh.json; handoff.json and startup/guard logs; cli_acceptance.json/recovery_responses.json; preflight.json; final preservation and scan summaries. None belongs in Git.

## Current boundaries

This is a **local merged/handoff-verified candidate**, not an official event freeze or public submission. Read-only git ls-remote succeeded and still reports remote main **5b726f9e3bb5b2899a6d8b98edfbf737f79e6cdf**. **No push or repository-visibility change was performed.** Public access, organizer submission and official freeze remain separate, explicit delivery steps.

Independent/current-configuration semantic accuracy, approved policy evidence, organizer control/replacement testing and the unclear call introduction remain unresolved. Optional A4/Letter/multilingual paper visuals were not retried; no browser or demo was run. Software tests and this merge do not raise an official project score. Final preservation/source/history/Markdown evidence and documentation checkpoint are recorded in CURRENT_CONTEXT. Next concrete delivery step: publish the reviewed main candidate when explicitly requested, then verify remote/public handoff; keep paid inference and the demo paused.

## Final preservation and report checkpoint

Independent finalize.py passed: all **159 pre-existing source files** are byte-identical; all **15 main tables/schema**, **249 evaluations** and **30 protected files** match the execution-start state; main budget_state remains empty. It confirms integration ancestry, exact merge parents, valid private before.bundle, retained safety ref, clean verification/builder worktrees, all-table recovery parity and stopped owned servers. All 234 working files were preserved at merge; subsequent differences from 535444d are confined to the authorized MD reports. Pre-report-commit scan passed 235 source candidates / 478 then-reachable history blobs / 76 Markdown files / 366 local links, zero credential/private-path matches and diff check passed. The final reports are committed on main; no application code changed after the exact-source tests, and no remote push occurred.
