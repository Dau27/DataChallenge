# Stage21 — private database backup and fresh-path recovery

Implemented 8 November 2026. This is a working offline CLI, developed on sprint-integration-20261108 from common audited baseline **d7d8a9d** and mirrored to the original root without overwriting existing source. [Baseline acceptance](../plans/2026-11-08-baseline-acceptance.md) and [READY builder handoff](../plans/2026-11-08-three-chat-handoff.md).

## Behavior

`scripts/workspace_backup.py` provides create, verify and restore. Creation uses SQLite's online backup API, including committed WAL pages, and changes only the new artifact to standalone journal mode. A new private directory contains database.sqlite3 and manifest.json: format version, artifact SHA256, complete schema/table logical hashes, row counts and privacy notice. An existing bundle is refused. A failed incomplete bundle has no valid manifest and must not be used.

Verification runs SQLite integrity and foreign-key checks; checks every table, including FTS shadow tables, against the manifest; recomputes immutable source/checklist identities; replays originals plus ordered review decisions; verifies effective result/recorded score preservation. This is storage/history verification, not a new evaluation, score correction or semantic accuracy claim. Today's contract rejects two historical assessments on the actual copy; verification reports those warnings while preserving their content.

Derived-index diagnostics compare version/content stamps AND indexed message IDs/order/speakers/folded content against the authoritative snapshots. Missing/stale indexes are reported without repair. FTS presence and exact artifact/table hashes are checked; independent FTS-posting consistency is not claimed. Existing literal-search fallback and explicit scripts/rebuild_transcript_index.py remain the maintenance path. No app/database constructor, schema migration, scoring change, budget initialization or provider is started.

Restoration verifies the bundle, stages and verifies a byte copy in the destination directory, then publishes via an atomic hard link that refuses replacement. It rejects the explicitly supplied active DB, the workspace default DB, every existing target (including links/directories), SQLite sidecars and absent parents. Rechecks and no-overwrite publication cover concurrent target creation. Staging files are cleaned after success/failure. A filesystem without hard-link support fails safely; no overwrite fallback is used. Recovery does not change DATABASE_PATH or start the application.

## Usage from the repository root

Choose a fresh bundle name and recovery filename each time:

```powershell
.venv/Scripts/python.exe scripts/workspace_backup.py create --database local_data/cqa.sqlite3 --destination local_data/backups/private-run-001
.venv/Scripts/python.exe scripts/workspace_backup.py verify --bundle local_data/backups/private-run-001
.venv/Scripts/python.exe scripts/workspace_backup.py restore --bundle local_data/backups/private-run-001 --target local_data/recovered-new.sqlite3 --active-database local_data/cqa.sqlite3
```

Use the actual configured active DB for --active-database when it differs. Output is JSON with hashes/counts/status; errors exit1 without dumping source, private configuration or raw SQLite errors. This command never loads .env. Inspect the restored copy before deliberately configuring an application to use it. Keep provider access blocked and the paid limit0 during recovery checks.

Bundles contain the **full private database**, including transcripts and recording URL references, and are unencrypted. They are not sanitized reports. Keep them under ignored local_data or another private directory with suitable local permissions. No .env, external budget_baseline.json, recording/media files, archived references, browser presets or app source are copied. Retain those originals separately. SQLite fingerprints/checksums detect damage relative to a trusted local manifest; they are not a signature against malicious replacement of both files. Strict compatibility warnings do not repair or certify old judgments.

## Acceptance actually performed

- Isolated guarded `local_data/offline_pytest.py -q backend/tests/test_workspace_backup.py`: **37 passed**, 8.59s. Healthy and committed-WAL round trips; all-row/schema/review parity; existing/active/default/hard-link/directory/sidecar/absent-parent refusals; truncation/checksum/logical/schema/format/path/JSON/missing-file damage; original/review/source/checklist/foreign-key damage; stale/missing index; historical contract warning preservation; concurrent target creation; changed staged copy; CLI and environment-file exclusion.
- Initial targeted run: 28 passed/2 failed, exposing WAL sidecars in the new artifact and temporary recovery path. Corrected the artifact's journal mode; subsequent 30-test pass, then expanded 37-test pass. Originals were never changed for these tests.
- Actual CLI create, verify and restore on isolated local_data/review.sqlite3: **249 evaluations / 75 source revisions / five checklists / nine appeals / nine reviews / 198 original-history replays**, SQLite integrity/foreign keys passed; index current 75/75 with 1297 messages. Actual recovered checksum/logical fingerprints match the verified bundle. The mirrored root CLI also independently verified this real saved-data bundle.
- Independent private final_preservation.py (using the earlier audit's separate fingerprint implementation): **all 15 recovered tables and schema match the execution-start backup exactly**; all main 15 tables/schema, all 30 protected files and all 131 original non-Markdown source/config/test files unchanged. Main budget_state remains empty; no budget bootstrap occurred. Three new owned code/test files copied to root only after checking they did not collide with concurrent files.
- Full isolated socket-guarded `local_data/offline_pytest.py -q`: **346 passed**, 54.59s (309 baseline + 37 recovery). Existing Starlette/AnyIO deprecation warning only. Frontend remained unchanged; same-stage baseline **118 passed / one paid opt-in skipped**, production build passed. Shared interpreter `pip check`: no broken requirements.
- Final pre-checkpoint source/history/MD scan: **200 candidate files / 393 then-reachable Git blobs**, zero credential/private-path matches; **66 Markdown files / 309 local links**, diff check passed. Recovery code/reports checkpointed locally on sprint-integration-20261108; no push or main checkout/reset.

Private acceptance data/results remain under ignored local_data/sprint_20261108. Root's previous dirty source/index, existing branches/worktrees, results and credentials are preserved. No remote publication, model request, organizer fetch or demo activity. **$0.00 added inference.**

## Files and next step

New owned files: backend/app/services/workspace_backup.py, scripts/workspace_backup.py, backend/tests/test_workspace_backup.py. No existing app source, schema or dependency change. Recovery stays CLI-only. Cohort and printable reports remain with their separate builders; this stage does not claim their completion or integration. Next: accept their tested owned-file handoffs, integrate shared hooks sequentially and repeat combined acceptance. The demo remains deferred.
