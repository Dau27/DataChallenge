# Stage — common baseline and isolated worktrees

Completed 8 November 2026. Handoff is **READY** in the canonical [three-chat handoff](2026-11-08-three-chat-handoff.md).

Captured all 195 Git-visible source/document files without changing the root index or dirty source. Compared the 131 non-Markdown source/config/test files, all 15 database tables/schema and 30 protected files against the latest audit: exact parity. SQLite online backup captured all 249 saved evaluations, 75 source revisions, reviews, budget state and derived index. Private fingerprints/source snapshot/backup are under ignored local_data/sprint_20261108. No .env or other ignored data entered Git.

Created local commit **d7d8a9d2a93ff5b537e34e689dd63b0e952f0fb3** on sprint-integration-20261108 from the complete audited working source. Created sprint-cohorts-20261108 and sprint-print-20261108 from that same commit. Their absolute paths, API/component interfaces and ownership are in the handoff. Root main and all older worktrees remain intact. Nothing was pushed.

Each worktree has its own local_data/review.sqlite3 and ignored offline guard/settings scripts. No .env was copied. Empty provider/model/organizer values, paid limit0 and external socket blocking are supplied by offline_pytest.py. Ordinary app construction must use the disposable copy. The main DB has only been opened through raw read-only SQLite connections.

Commands actually run:

- Git status/log/worktree inspection and targeted specification/source reads.
- `.venv/Scripts/python.exe local_data/sprint_20261108/prepare_baseline.py`: 195 files, 15 tables, 249 evaluations, 30 protected files; prior audit parity passed.
- Private final_checks.py: 195 candidate files / 393 then-reachable blobs; zero credential/private-path matches; 64 MD / 296 local links; diff check passed before checkpoint.
- `git worktree add`, reviewed `git add --all` in the isolated coordinator only, `git diff --cached --check`, local baseline commit; two builder worktrees created from that commit.
- `.venv/Scripts/python.exe local_data/sprint_20261108/setup_copies.py`: three exact SQLite copies, no credentials, offline helpers installed.
- Absolute shared Python interpreter with `local_data/offline_pytest.py -q` from isolated coordinator: **309 passed**, 77.19s; one existing Starlette/AnyIO deprecation warning.
- Root frontend `npm test` with CQA_LIVE_SMOKE=0: **118 passed / one paid opt-in skipped**, 34.54s. `npm run build`: passed, Vite2.30s. Client source is identical to the checkpoint modulo Git line endings; no frontend changes during acceptance.

Next: implement and verify CLI-only backup/recovery in the coordinator worktree. Builders may implement only their owned files now. This is a development checkpoint, not official submission or a measured accuracy improvement. **$0.00 inference, demo deferred.**
