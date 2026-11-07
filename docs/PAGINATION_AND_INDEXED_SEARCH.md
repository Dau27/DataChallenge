# Saved-run pagination and indexed transcript search

Implemented in the current shared working tree. Existing evaluation, scoring, appeals, exports and concurrent insight/UI work are preserved. This follow-up adds bounded saved-run browsing and a rebuildable local search index without hosted inference.

## Completed behavior

- The conversation review screen requests **25 saved-run headers at a time**. Newer runs, Older runs and Latest runs controls support long histories without rendering the entire history in the selector.
- An explicitly selected or deep-linked older assessment stays open while browsing other pages. Its option remains pinned when outside the current page. Runs already browsed remain available for comparison; the comparison hint describes that loaded scope.
- Page errors have retry/return-to-latest actions. A late page response cannot overwrite the latest page or another source revision. Selected-run header state refreshes after an assessment update, even on an older page.
- Transcript search uses a SQLite **FTS5 trigram candidate index over the existing NFC + Python casefold representation**. The exact source matcher still determines snippets/highlights and verifies literal membership.
- **All 249 original evaluations and all eight pre-existing business tables are unchanged.** Search-derived tables and history-order indexes were added. The main database is already backfilled: **75 sources / 1,297 messages**. No model requests or API spending were added.

## Pagination API and consistency

New endpoint:

```text
GET /api/evaluations/page?conversation_id=<revision-id>&limit=25&cursor=<opaque-cursor>
```

`conversation_id` is optional for global history. `limit` is bounded to 1–100. The response contains `items`, `total`, `start`, `end`, `limit`, `next_cursor`, `previous_cursor`, `first_cursor`, and source identity when scoped to one conversation. A missing conversation is 404; malformed/oversized/cross-scope cursors are 422.

The bounded conversation-detail mode used by the UI is:

```text
GET /api/conversations/<revision-id>?history_limit=25&history_cursor=<opaque-cursor>
```

This retains the full immutable transcript and returns a bounded `evaluations` list plus `history_page` navigation metadata. Omitting `history_limit` preserves the previous unpaged response and shape. The existing `/api/evaluations` list endpoint also remains compatible, including its empty-filter behavior. Assessment details, reviewer history and audit exports remain complete; this pagination is for saved evaluation headers.

Pages use `(created_at, id)` keyset ordering and an initial upper ceiling, with matching B-tree indexes for source-scoped and global history. Equal timestamps have deterministic order. Normally newer runs are excluded from the current paging window until Latest runs starts a fresh window. Individual statuses and reviewed scores remain live data; the cursor is not a frozen assessment snapshot. Each page is read in one SQLite snapshot. Navigation cursors are bound to the conversation/filter and source content identity.

The UI verifies returned source ID/hash and run membership, retains the current assessment during history loading/failure, and ignores late results through the existing resource-identity guard. Only browsed public summaries are cached for comparison; judgments and transcripts are not copied into that header cache. Users can deliberately load further pages rather than triggering an automatic full-history download.

Implementation: [history API](../backend/app/api_history.py), [saved-run pager](../frontend/src/SavedRunPages.tsx), [review integration](../frontend/src/Detail.tsx).

## Literal multilingual search preservation

The index narrows candidate source/message rows before full transcript JSON is materialized. It does not change the operator checklist or reinterpret the query as words, stemming, fuzzy matching or Boolean search syntax.

Preserved behavior includes RU/KZ/EN text; Kazakh letters; Russian Й/Ё; composed/decomposed accents; Unicode casefold expansions such as `Straße`/`STRASSE`; dotted-I and Greek cases; emoji; punctuation; literal `%`, `_`, quotes and operator-looking strings; speaker filters; exact source revisions; matching-message counts; source message order; and original-text highlight offsets.

The full trigram accelerator is used for normalized queries of at least three code points. One/two-code-point queries use exact substring checks over normalized message rows. Embedded-NUL cases use the safe exact path, including when the NUL occurs before a matching substring in a message. Missing/stale index state falls back to the authoritative source scan, so such rows are not silently omitted. If FTS5/trigram support is unavailable, exact matching remains available without that accelerator.

The original [source matcher/highlighter](../backend/app/services/search.py) remains the presentation authority. Derived normalized text is never returned as a fabricated source quote. [Queue narrowing](../backend/app/services/queue.py) and message-page retrieval retain the existing API response shapes.

## Index lifecycle and preservation

[The index implementation](../backend/app/services/transcript_index.py) adds `transcript_messages`, `transcript_index_state`, and the FTS virtual/shadow structures. It stores source revision identity, message identity/order/speaker, normalized text and a version stamp. The stamp includes the normalization algorithm and Unicode database version. Content-hash or version changes cause a rebuild.

[Database initialization](../backend/app/db.py) creates missing structures and backfills existing sources in a restartable transaction. Imports maintain index data inside the same transaction as their source insertion; rollback removes both. Source updates/deletions also maintain the derived rows. An idempotent unchanged reimport does not duplicate index entries. Source/global history-order indexes are also created for existing databases.

A database backup was saved before migration under ignored `local_data/pagination_search_20261108/before.sqlite3`. Backfill was first tested on a private copy, then applied to the main database. All original table fingerprints and protected-file hashes matched afterward. No scores, effective/original judgments, appeals, reviews, source IDs, source messages, checklist versions, credentials or paid limits were rewritten.

Maintenance command, if an explicit rebuild is needed later:

```powershell
.\.venv\Scripts\python.exe scripts/rebuild_transcript_index.py --database local_data/cqa.sqlite3
```

The [maintenance script](../scripts/rebuild_transcript_index.py) requires an existing database and never creates an empty replacement. Its force-rebuild path was exercised on the private copy. Normal startup does not force a full rebuild when stamps are current. The preservation helper was updated to fingerprint binary FTS shadow data without changing hashes for original tables.

## Verification actually performed

- Final full backend snapshot: **299 passed**, one existing Starlette/AnyIO deprecation warning. The dedicated [pagination/index suite](../backend/tests/test_pagination_search.py) has **16 passing cases**.
- Final frontend snapshot: **118 passed / one paid opt-in skipped**; TypeScript/Vite production build passed. The new [history UI suite](../frontend/src/historyPagination.test.tsx) covers deep links, bounded selectors, retained comparison choices, failed/retried/late pages, wrong-source responses and selected-header refresh.
- Existing multilingual search, scoring, review, cache, budget, import, export and insight tests continue to pass. `pip check` was clean.
- On copied saved data, **258 query/speaker comparisons** exactly matched the source-scan queue output. **75 indexed message-page comparisons** matched original snippets, counts and offsets. Paged saved-history membership matched the unpaged list.
- Synthetic cases cover tie timestamps, both navigation directions, newer insertions during browsing, empty histories, cursor scope/limits, idempotent imports, transactional rollback, index loss/version changes/restart repair, legacy-schema backfill, direct source update/delete synchronization and use of the actual FTS/history-order indexes.
- Read requests do not rewrite derived or original rows. Selected DEV remains **64 complete / one needs review**; **130 original/effective snapshots** still validate and recalculate exactly. The main eight-table fingerprints and protected files remain unchanged.

Commands actually run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
.\.venv\Scripts\python.exe -m pytest backend/tests/test_pagination_search.py -q -p no:cacheprovider
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe scripts/rebuild_transcript_index.py --database local_data/pagination_search_20261108/indexed-copy.sqlite3
.\.venv\Scripts\python.exe -u scripts/audit_validation_gaps.py --saved-db local_data/cqa.sqlite3 --output local_data/pagination_search_20261108/saved-validation.json
cd frontend
$env:CQA_LIVE_SMOKE='0'
npm test
npm run build
```

Combined counts include independent features/tests added by other chats; this task does not claim authorship of those additions. Shared context/design/insight files owned by those chats were left intact. No commit, push, server launch, organizer fetch or paid-model request was performed by this task. Demo work remains deferred.

## Local measurements and limits

| Measurement | Result |
| --- | ---: |
| Copy backfill, 75 sources / 1,297 messages | About 1.2 seconds |
| Initial extra copy-file storage for derived index | About 0.8 MB |
| Saved-data literal query, four matching sources: source scan | 28.81 ms median |
| Same query with candidate index | 11.17 ms median |
| 5,015-run RAM history: unpaged headers | 81.52 ms median |
| Same RAM history: 25-header page | 8.14 ms median |

Search measurements use seven local trials, and history measurements use five. They exclude HTTP/serialization/DOM and do not establish production capacity or model accuracy. History amplification exists only in a RAM copy. Private build/parity/migration/benchmark evidence is under ignored `local_data/pagination_search_20261108/`.

Short queries and very common literals still require exact checks over many normalized rows; the index is not a guarantee that every query is faster. Larger datasets consume additional derived storage and startup/rebuild time. Exact total/range counts still read index entries; pagination bounds returned headers rather than promising constant-time work. Legacy callers can still request unpaged histories for compatibility. Very long decision/attempt histories remain part of full assessment/audit payloads. None of these changes validates the current prompt's judgment accuracy or resolves the unclear call.
