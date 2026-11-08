# Stage 27 - private documentation commit and push

8 November 2026. The owner explicitly authorized committing and pushing the updated README and Markdown reports to the existing private Dau27/DataChallenge repository. This does not authorize public access, organizer submission, inference spending or demo work.

## Scope and preflight

- The pending handoff contains 15 Markdown files: the judge-facing README/operations guide, PDF requirement clarification, final offline preparation, stage indexes/runbooks and the retained print-deferral notes. This publication report is the additional stage record. No application, dependency, checklist or saved-data file is included.
- Read-only authenticated GitHub metadata confirmed **private=true, visibility=private, default branch=main**. No repository setting was changed. The fixed fetch and push target is the existing HTTPS Dau27/DataChallenge origin.
- Captured fresh read-only fingerprints for all 15 main tables/schema, 249 saved evaluations, 30 protected files and 159 source/config/test files, plus a consistent private SQLite snapshot and copies of every pending Markdown file. These remain ignored under local_data/docs_publish_20261108.
- Application code still matches tested merge 535444d. Prior exact-source acceptance remains 460 backend tests in both installed environments, 182 client tests with one paid opt-in skipped, production build and clean setup/startup/restart/recovery. No redundant application suite or fresh inference is run for Markdown-only publication.

## Commit and remote verification procedure

Commit only the explicitly selected Markdown paths. Fetch remote main first and require its head to be an ancestor of the candidate. Push the candidate to refs/heads/main without force, tags or other branches. Independently compare git ls-remote and a fresh fetch with the exact local commit, complete tree and all 159 tested source blobs.

Private wrappers use noninteractive Git, empty provider/model/organizer settings, zero spending ceiling and a disposable unused database path. Active hooks are checked before committing. GitHub credential material stays in process memory and is never printed or committed. Only Git/GitHub transport is used; no provider or organizer call.

## Verified private push

Committed all 15 requested Markdown files plus this stage record, then fast-forwarded private origin/main from ac9a6593188b0dbcc6f89eda375a51de55a687a4. No application code or private data was staged. GitHub metadata had confirmed private visibility; no setting was changed.

| Check | Actual result |
| --- | --- |
| Documentation commit | f4eabbdc919b4661706dfb3a8b126fc195fac304 |
| Independent git ls-remote main | Same f4eabbd commit |
| Freshly fetched remote main | Same f4eabbd commit |
| Complete fetched tree | 6a32d2ad2f7afeb3a5421d6051bf5bf4ec2261ee, identical to local |
| Tested merge 535444d | Ancestor of the fetched main |
| All 159 tested source/config/test blobs | Unchanged; all differences Markdown only |
| Pre-push source/history/Markdown scan | 240 candidates / 509 then-reachable blobs / 81 Markdown files / 384 local links; zero credential/private-path matches; diff check passed |
| Fresh post-push preservation | All 15 main tables/schema, 249 evaluations, 30 protected files and 159 source files unchanged; budget_state empty |

Actual commands through private wrappers:

```powershell
.\.venv\Scripts\python.exe -X utf8 local_data/docs_publish_20261108/github_preflight.py before
.\.venv\Scripts\python.exe -X utf8 local_data/docs_publish_20261108/final_checks.py
.\.venv\Scripts\python.exe -X utf8 local_data/docs_publish_20261108/commit_docs.py docs
.\.venv\Scripts\python.exe -X utf8 local_data/docs_publish_20261108/publish.py docs
.\.venv\Scripts\python.exe -X utf8 local_data/docs_publish_20261108/finalize.py
```

publish.py performs a pre-push fetch/ancestor check, an explicit non-force main push with tag-following disabled, independent advertisement and a fresh fetch into a verification ref. All 16 selected documents were committed and the working tree was clean. No active commit/push hook or custom hooks path was present. The GitHub API call was a metadata GET only, authenticated using the existing Git credential helper without displaying or saving its token.

The report-only follow-up containing these observed outcomes uses the same commit/push/tree/source checks and a second metadata GET to recheck privacy. Its exact final SHA/tree and completion evidence are retained in ignored receipt_verification.json, privacy_after.json and final_preservation.json under local_data/docs_publish_20261108, rather than pretending a commit can contain its own final hash. No successful final-head check should be inferred solely from the earlier f4eabbd checkpoint; the final receipt and task reply identify it.

## Preserved constraints

Saved results, originals/reviews, source revisions, credentials, budget baseline and initial checklist copies remain local and unchanged. Private transcripts, recording links, PDFs, databases and recovery artifacts stay excluded from Git. Organizer control data remain unavailable. Official freeze and organizer submission are not claimed. **No paid inference; demo and optional paper-layout QA remain deferred.**
