# Backend performance and import-limit improvements

Date: 7 November 2026. Implemented against the shared working tree following `5b726f9`, preserving the preceding validation/UI fixes and concurrent feature work. This task changes backend read paths and import boundaries. It does not change scoring, saved judgments, model prompts, provider configuration, or the spending limit.

## Result

Three concrete limitations were addressed:

1. **Queue and history views loaded full historical assessments.** Latest-run selection now happens in SQL, and summary queries retrieve only the fields they display. Older revision appeal targets, selected-checklist behavior, flags and null/failed scores remain intact.
2. **Budget refresh loaded unrelated assessment data and read reservations twice.** Reconciliation now reads accounting fields only, reuses the reservation rows, and runs public status reads in one consistent SQLite snapshot. Full history-integrity and unknown-usage checks remain enabled.
3. **Import limits were checked too late or trusted declared size.** Incoming writes are bounded by actual bytes before JSON parsing or endpoint execution. Organizer downloads are consumed incrementally and stopped when decoded content exceeds the existing 25,000,000-byte limit.

**Verified:** 281 backend tests passed at the final combined-source verification snapshot; one existing Starlette/AnyIO warning. This change adds 22 focused backend tests. The earlier frontend compatibility run passed **82 tests / one paid opt-in skipped**, and the TypeScript/Vite production build passed. Other chats continued adding independent features during this work; their tests are included in the combined totals but are not claimed as additions by this task.

The old and optimized queue responses match exactly across **70 combinations** on a RAM-only copy of saved data. All eight main database table fingerprints and protected configuration hashes match the pre-change baseline. **All 249 saved evaluations remain unchanged. Added paid inference: $0.00.** Demo and submission work remain deferred.

## Measured effect

Same machine, same saved database, three trials per measurement. History amplification duplicates evaluation rows only in memory and retains **75 returned conversation rows**. Measurements cover route-function work, excluding HTTP, response-model serialization and browser rendering.

| Read operation | Before median | After median |
| --- | ---: | ---: |
| Queue, 249 historical evaluations | 101.55 ms | 22.58 ms |
| Queue, 1,245 historical evaluations | 431.09 ms | 27.58 ms |
| Queue, 4,980 historical evaluations | 2,038.83 ms | 51.90 ms |
| Literal transcript search, current history | 162.14 ms | 79.00 ms |
| Budget status, current history | 76.89 ms | 23.75 ms |

The current queue measurement is approximately **4.5 times faster**; the amplified-history case is approximately **39 times faster**. These are local diagnostic ratios, not production-capacity or end-to-end latency guarantees. Hosted evaluation latency is unchanged.

Private reproducibility evidence: `local_data/backend_limitations_20261107/before.json`, `after.json`, `before-source/`, and `before.sqlite3`. The existing [offline audit harness](../../../scripts/audit_validation_gaps.py) exposes `profile_history` for reproducing current queue/budget measurements without starting a server or requesting inference. SQLite in this environment is **3.45.3**.

## Read-path changes and compatibility

[The queue service](../../../backend/app/services/queue.py) filters latest source revisions and ranks only lightweight evaluation IDs/timestamps in SQL. It fetches total/flag JSON fields only for winning runs, rather than deserializing original/effective judgments for every historical evaluation. Open appeals are joined to their exact old run/source identity, so an appeal on an earlier revision still links to the original evidence. Dataset namespaces remain separate even when external source IDs collide.

[Summary projections](../../../backend/app/services/saved_results.py) are shared by queue, evaluation-history and conversation-detail headers. Assessment detail/comparison/export endpoints retain their full snapshots. Newest failed or unresolved runs remain visible; the code does not quietly substitute an earlier successful score. Equal creation timestamps now have a deterministic descending run-ID tie break in all summary views. The existing empty history-filter behavior is retained.

The 70 saved-data comparisons cover checklist selection `None`, 1–5 and a missing version; latest-only versus all revisions; blank, Cyrillic, English and absent text queries; and all/operator/client speaker cases. Existing regressions also cover dynamic flags, cross-revision appeals, source revisions, multilingual search, cache identity, exports and persistence.

No table/column/index migration, result rewrite or derived score backfill was needed. The current API response shape is unchanged.

## Budget integrity and consistency

[Budget reconciliation](../../../backend/app/services/budget.py) still checks every covered attempt hash, metadata hash, rate/usage minimum, reservation offset, access-check report and opening amount. Only unrelated assessment/score columns are omitted from the SQL projection. Reservation rows are loaded once per status calculation and reused for reconciliation and totals; no persistent cached balance replaces the ledger audit.

Public status reads explicitly use one read transaction. Calls made inside reservation/write transactions continue using the caller's transaction. A concurrent-commit regression verifies that status reports either the old coherent state or the next coherent state, rather than mixing an opening amount with a later reservation set.

The zero paid limit, conservative unknown-usage accounting, atomic reservations and fail-closed behavior are unchanged. These estimates remain a local ledger, not a provider account balance.

## Import and upload behavior

[The ASGI byte boundary](../../../backend/app/limits.py) validates declared lengths and also counts actual incoming bytes, including missing or understated `Content-Length`. It buffers no more than the configured import-byte limit before replaying a complete body to the parser. Oversized requests receive a clear **413**; malformed/negative declared lengths receive **400**. Endpoints cannot partially import an oversized body. An interrupted upload does not invoke an endpoint. The boundary runs before HTTP dispatch/parser middleware, avoiding a spurious missing-response error on an already-disconnected upload.

[Organizer fetching](../../../backend/app/services/importer.py) uses an HTTP stream with bounded decoded chunks. It checks accumulated decoded bytes before appending another chunk, closes the response on size/error exits, and preserves the original envelope/group validation. Compressed response content is checked after decoding. Non-success HTTP responses are rejected without reading their response body; network errors keep signed URLs and source contents out of the error message.

The byte cap bounds the application import buffer, not all memory used by JSON objects or the HTTP library's decoder. No real organizer endpoint was fetched for these tests; the streams, compressed responses, failures and datasets are synthetic. No retry policy, redirect allowance or transcript truncation was added.

## Tests actually run

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests/test_backend_limits.py -q -p no:cacheprovider
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -u scripts/audit_validation_gaps.py --saved-db local_data/cqa.sqlite3 --output local_data/backend_limitations_20261107/saved-validation.json
cd frontend
$env:CQA_LIVE_SMOKE='0'
npm test
npm run build
```

Final combined backend result: **281 passed**. An earlier complete intermediate backend run passed 223 tests, before later streaming regressions and concurrent feature tests were added. Frontend compatibility snapshot: **82 passed / one skipped**, build passed. `pip check` found no broken requirements. Tests use injected HTTP transports; ordinary backend tests prohibit real OpenAI HTTP, and the offline saved-data harness prohibits provider requests.

[The new regressions](../../../backend/tests/test_backend_limits.py) verify that list headers do not materialize assessment ORM objects; equal-timestamp ordering; failed/null/latest behavior; old-revision appeals and dataset namespaces; budget projections and one reservation read; concurrent snapshot consistency; actual upload sizes, exact byte boundaries and invalid declarations; early ASGI stream rejection/disconnection; compressed organizer limits; response closing; and private network-error handling.

Saved validation remains **130/130 selected original/effective snapshots** with exact recalculation and valid strengthened citations; DEV remains **64 complete / one needs review**. Main rows, `.env`, both rubric seeds and the budget baseline match their before fingerprints. Raw evidence and preservation output stay under ignored `local_data/backend_limitations_20261107/`. No Git staging, commit, push, main-app launch, real organizer fetch or recording playback was performed by this task.

## Remaining limits

The subsequent [pagination/indexed-search follow-up](../../PAGINATION_AND_INDEXED_SEARCH.md) implements bounded saved-run browsing and a derived transcript index. The observations below describe the earlier checkpoint; short-query fallbacks and compatibility endpoints remain explicitly documented in that follow-up.

- Transcript search still scans source text; there is no full-text index. That preserves current literal Unicode semantics, but large datasets may need an indexed design with explicit normalization parity.
- History APIs return all lightweight summaries by default. Very long histories may eventually require paging in both API and UI.
- Budget integrity work remains proportional to recorded accounting history; projections reduce its cost without skipping checks.
- The job runner is still one local process with bounded workers. Multi-worker/distributed execution would need a different claim/recovery design.
- Model latency, missing authoritative policy information and the broader semantic cases in the [validation audit](semantic-validation-and-technical-quality.md) are unchanged. Faster reads do not establish model accuracy.

Frontend and insight-feature files owned by other chats were left intact. This report is the backend-specific record; shared context/index updates remain with those ongoing tasks.
