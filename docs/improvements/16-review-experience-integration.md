# Integrated review experience and practical design features

Verified locally on 8 November 2026, combining the design, merged refinements, UI consistency fixes, backend limits/queue changes, and saved-data insight tools. **283 backend tests / 107 client tests passed; one paid opt-in test skipped. TypeScript and production build passed. No inference spending. Demo remains deferred.**

## New design features

- **Quick review views:** All in view, Needs review, Pending appeals, and Critical findings. Counts describe conversations within the current text/ID search, dataset, language and channel. Selecting a view replaces only the state/appeal/critical filters. Loading/error searches do not display misleading counts or permit stale selection.
- **Removable filter chips:** show the applied constraints and remove one at a time. Literal search values retain their exact characters, including underscores. Long values fit narrow screens and retain their full tooltip. Clearing a chip marks a saved preset edited; it does not overwrite or delete it.
- **Comfortable/compact rows:** compact spacing shows more records without truncating source or assessment content. The preference is remembered locally when browser storage is available and remains usable in memory when storage is blocked. It changes no scores, filters, selected IDs or exports.

These use the existing React/CSS/filter contracts and stored data. No new library, account, generated graphic, provider request, scoring threshold or database schema was introduced by this UI pass.

## Integration and UX repairs

1. Selected-run and per-run export failures reveal their tool group if it was collapsed during the download. Late failures from obsolete selections remain ignored.
2. The queue's select-all checkbox now exposes its native indeterminate state and `aria-checked=mixed` for partial visible selections. Filtering and clearing keep it consistent.
3. Priority loading/error states are distinct from an empty queue. Failure feedback remains available outside the collapsed priority controls, and Show normal queue restores the existing filtered source rows safely.
4. Breakdown case lists previously opened far below the viewport: the reproduced desktop panel started about **2,297 px** below the visible page top. Opening now scrolls/focuses the case region; closing returns focus to the originating bucket. The verified case panel appeared at about **24 px** from the viewport top.
5. New analysis disclosures follow the existing spacing, palette, focus treatment, and expansion affordances. They remain individually collapsible. Queue selection/export uses the actual priority-filtered visible rows.

The other chat resolved the Git merge while this review was underway. Its first transient conflict-marker state caused an initial client test failure; the settled merge preserves the design and refinements, and the final source has no unresolved conflict markers. The later consistency and insight changes were checked together rather than reverted to the older merge snapshot.

## Verification actually performed

- Latest full backend gate: `.venv/Scripts/python.exe -m pytest -q` — **283 passed**, 41.51 s; one existing Starlette/AnyIO deprecation warning.
- Latest full client gate with `CQA_LIVE_SMOKE=0`: direct Node/Vitest — **107 passed / one paid test skipped**, 10.12 s.
- `npm run build` — **passed**, including TypeScript; Vite 2.12 s, 50 modules. The normal `frontend/dist` includes the combined interface.
- Added **six integration UX regressions** and **five design-feature regressions**, covering partial selection, hidden export failures, stale export failures, priority recovery, case-list focus/return, scoped quick views, precise chip removal, density persistence/storage failure, and pending-search counts.
- Disposable-copy browser workflow: submit an explicitly labeled test appeal; make a separate reviewer decision that withholds its total; observe the already-open comparison refresh to no comparable delta; preserve original **92.31**; download actual JSON/archive CSV/simple CSV and confirm their agreement; reload; restore the preserved original judgment through a second attributed test decision; verify the appeal becomes decided and the total returns to **92.31**.
- Downloaded JSON contained original **92.31**, effective **null**, the preserved original Contact answer, and one test review at the withholding checkpoint. Archive CSV parsed as **21 records**; simple CSV as **16 criterion rows**. Selected simple CSV contained exactly the selected saved run's **16 original/effective criterion rows**.
- A deliberately delayed local export outage confirmed that failure automatically reopens the collapsed report tools. A deliberately failed priority request confirmed visible recovery and **no false empty-filter message**; the normal queue returned to **75 rows**.
- Insight checks: priority filtering showed the two unresolved conversations; breakdowns separated **DEV 65** from **SYNTHETIC_TEST_ONLY 10**; case focus/return worked. Weighting the copied run's Contact criterion from **10 to 20** changed the simulated total **92.31 → 93.33**, while its saved total stayed **92.31**. Restoring weight 10 returned the simulated difference to **0.00**. No checklist version was saved.
- Checklist-change validation passed through the actual preview route. Cold backend restart/reload preserved the copied review history and restored score. Quick-view counts and compact density remained correct after restart/reload.
- Layout checks covered desktop **1440 px**, phone **390 px**, and narrow **320 px**, including a long applied filter and the new tools. No page-level horizontal overflow was observed; data tables retain their own horizontal scroll.
- Read-only service verification repeated **249 original/effective comparisons**, **249 JSON**, **249 archive CSV**, **249 simple CSV**, and exact **100-run batches in all three formats**, with provider/external HTTP forbidden.
- Every pre-existing main database table matches the baseline. All **249 original judgments/scores, attempts and provenance** are preserved, as are all **30 protected files**, including credentials, baseline, rubrics and archived references. Only the disposable copy has the explicitly labeled extra appeal/two decisions and expected budget bootstrap.
- `git diff --check` passed. Source hashes and private reports are retained under ignored `local_data/design_integration_20261107`.

The ordinary tests and preview server forbid provider requests. Browser tests used empty credentials and a disposable SQLite copy. The initial custom preview origin was correctly refused by the application's write boundary, so writable checks moved to the normal allowed origin on port 8000. The private middleware was corrected to allow the actual checklist-preview path; no production boundary was relaxed. Initial test-helper annotations and CSV byte decoding were corrected before the final gates.

## Scope

This report records the tested local combined workspace. It does not claim a separate commit/push, independent model accuracy, live inference, organizer control/freeze completion, or a demo. Ongoing pagination/indexed-search work in another chat is a later task and requires its own acceptance gate when applied. Temporary verification servers/tabs are closed during teardown; unrelated chats' resources are preserved.

During cleanup, the later pagination task changed shared files. A compatibility recheck repeated **283 backend / 107 client tests and build**, and the saved-data preservation check passed again. After that recheck, further edits appeared in `backend/app/api_history.py`, `backend/app/db.py` and `backend/app/main.py`. Those subsequent history/pagination edits are outside this report's acceptance claim. The exact source hashes and deltas are retained privately; the UI additions and integration repairs above are complete.
