# Transcript search and saved filters — 7 November 2026

Status: **PASS**. Implemented the third requested improvement without new inference, dependencies, database tables or migrations. These are optional usability improvements, not additional PDF scoring requirements.

## Completed

- Literal transcript-text search beside conversation-ID search, with operator/client/bot/system scope. Matching is case-insensitive with Unicode NFC normalization. Punctuation is literal; no regex, embeddings or model requests.
- Results include exact revision/hash/message IDs, source-based snippets (up to five matching messages per conversation) and total matching-message counts. Latest-revision selection precedes matching; superseded text is never attached to a newer revision. The API can explicitly include historical revisions.
- Dataset, language, channel, state, pending-appeal and critical filters compose with text/speaker search. Links select the actual saved run and focus/highlight the exact message. Missing message IDs have an explicit unavailable state.
- Named presets retain all nine filters and checklist-version scope in this browser. Selected presets restore after reload; unsaved edits do not overwrite them. Saving an existing name in the same scope replaces that preset. Default filters reset the view; deletion removes only a browser preset. Limit: 50 presets, 80-character names, 200-character text query.
- Invalid/unavailable browser storage is reported without breaking filtering. Search is debounced and stale responses ignored. Pending/error results and stale selected IDs are hidden. Errors offer retry instead of claiming no matches; revision/hash changes request queue refresh.

## Commands and acceptance evidence

- `.venv/Scripts/python.exe -m pytest -q`: **144 passed**, one existing Starlette/AnyIO deprecation warning. The new saved-inspection file contributes **17 tests** for comparison/export/search and consistent snapshots under concurrent review. Ordinary tests forbid real OpenAI HTTP; the new fixture additionally forbids Provider.request and uses a zero budget.
- `npm test` from frontend with CQA_LIVE_SMOKE=0: **27 passed / one paid opt-in skipped**. Eight search/preset checks cover combined filters and exact links, remount restoration, checklist isolation, unsaved edits/deletion, invalid/blocked storage, pending/error/late responses, changed revisions and missing/direct messages.
- `npm run build`: **passed**. `.venv/Scripts/python.exe -m pip check`: **no broken requirements**.
- `.venv/Scripts/python.exe local_data/inspection_features_20261107/verify_features.py`: copied-data verification passed **249 self-comparisons / 249 JSON exports / 249 CSV exports**. Saved fields and both score sets matched detail responses. Six actual multilingual/operator/client queries matched independent source-text checks; cold reopen passed. Provider and external HTTP transport were forbidden: **zero provider requests**.
- Browser checks on a read-only loopback copy at port 8124 confirmed combined search, preset restoration after reload, exact message focus, original/effective selectors, changed-only controls and evidence navigation. Both downloaded files were parsed from Downloads; CSV excerpts appeared only after opting in. Explicit control labels fixed browser targeting; grid-child sizing fixed a 9 px narrow-layout overflow. Final document/viewport content widths both **699 px**. The temporary server was stopped. No demo was prepared, rehearsed or performed.

The initial storage-error client test mocked a prototype method that the emulator did not use, so it did not simulate failure. Replacing the storage object with an explicitly throwing implementation exercised the intended behavior; all tests then passed. No real storage failure is hidden or claimed resolved.

## Preservation and limits

Every main database row/column is preserved, including 249 saved evaluations, originals, checklist versions, appeals and decisions. The .env, original rubric, budget baseline and 26 archived reference files are unchanged. The private backup, verification and report examples stay ignored under local_data/inspection_features_20261107. Source excerpts are not published to Git.

Final preservation checks distinguished the main database from app initialization on the browser copy: the existing Budget constructor creates its one initial budget_state row on that copy before requests. All pre-existing copied rows stayed identical, and no new evaluation/reservation/review appeared. The exhaustive comparison/export/search request pass changed no rows after that initialization. The first final check used an overly strict pre-initialization copy comparison; it exposed this expected bookkeeping addition, which is explicitly checked and reported rather than deleted. The main database has no additions or changes. The subsequent PDF audit corrected the earlier attribution to GET /api/budget; construction, rather than that GET, causes the bootstrap.

Added inference: **$0.00 / zero model calls**. The paid limit remains zero. p4-ru-005 keeps original Yes/92.31, effective contact needs_review/null total and its open appeal. These features do not establish independent semantic accuracy, validate prompt v13 live or change the earlier informal readiness estimate. Presets are local to one browser/origin. Search scans saved transcripts for this prototype; no large-scale indexing claim is made.

No feature work from this request remains pending. Demo execution remains deferred; organizer control data, independent judgment validation and public/event handoff remain separate external or deferred steps.
