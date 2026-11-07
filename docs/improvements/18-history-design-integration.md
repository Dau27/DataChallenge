# Saved history and design integration — 8 November 2026

Integrated the other chat's cursor pagination and indexed transcript search with the current review design. The combined local source passed **299 backend tests / 118 client tests**, with the paid smoke test skipped, and the normal TypeScript/production build. All 249 existing saved runs and 30 protected files were preserved. No paid requests were made; the demo remains deferred.

## Practical design additions

- **Return to the same queue view.** Opening a conversation or checklist keeps the queue mounted. Returning restores unsaved filters, row selections, priority controls, table position and page position. Route changes move keyboard focus to the content without discarding the saved queue position. Checklist changes still establish their own scoped queue.
- **Copy the exact saved-run link.** The selected assessment has a copy action with accessible success feedback. When clipboard access is unavailable, it exposes and selects a read-only link for manual copying. A late clipboard response cannot report success for another selected run. Unrelated URL query parameters are omitted. Links open the existing run in this local workspace.
- **Unambiguous saved-run context.** The assessment shows its checklist, state/completeness, full local date/time and short run ID. The same labels appear in history and comparison selectors, including a selected run outside the current page. History navigation uses the existing compact design and wraps on narrow screens.

## Integration repairs

- Comparison defaults now follow the backend's exact `(created_at, id)` history order. JavaScript date parsing drops sub-millisecond precision; equal or nearly equal timestamps previously allowed a newer run to be chosen as an earlier baseline. Identical timestamps and differing microseconds have regression coverage.
- Saved filters initialize once for the active checklist. The former post-paint initialization could overwrite a fast first filter change. The initial full client run exposed this intermittent failure; it was corrected before the final full run.
- Preserved bounded 25-run pages, deep-linked selections outside the current page, comparison choices across browsed pages, refreshed headers, source-revision guards, page retry, late-response protection and return-to-latest behavior from the pagination implementation.
- No Git conflict entries remain; whitespace validation passed. Concurrent backend/index/history changes were preserved. The report describes the tested shared working source, without claiming that another chat's later work is complete.

## Verification

Final source capture covered 106 application, test, style, configuration and frontend build-input files. Their hashes were unchanged throughout the final suites, saved-data checks and browser verification.

| Check | Result |
| --- | --- |
| `.venv/Scripts/python.exe -m pytest backend/tests -q` | **299 passed**, 87.34 seconds; one existing Starlette/AnyIO deprecation warning |
| `CQA_LIVE_SMOKE=0; npm test` in frontend | **118 passed / one paid opt-in skipped**, 18.62 seconds |
| `npm run build` | TypeScript passed; production bundle passed, Vite 2.77 seconds |
| Saved-data inspection | All **249** original/effective comparisons and each run's JSON, archive CSV and simple CSV passed |
| Selected-run exports | **100** exact selected runs passed all three formats |
| History parity | **88** bounded page reads across all copied sources plus the long-history fixture matched the unpaged summaries exactly |
| Indexed-search parity | **912** message-page comparisons matched literal search counts/snippets for Unicode and literal punctuation, including speaker filtering |
| Preservation | All **8** original main tables, all existing rows in the disposable copy, **249** saved runs and **30** protected files unchanged |
| Cold reopen | Original saved run and synthetic paged source reopened successfully; zero provider/external HTTP attempts |
| Browser cleanup | Temporary tab closed, viewport reset, owned port 8000 stopped |

The first full client run had one filter-retention failure; focused tests had passed. The filter initialization fix preceded both subsequent passing full runs. Final counts above include the other chat's additional history/index regression cases that arrived before the stable source capture.

## Browser checks

Used a SQLite backup in ignored `local_data/history_ux_20261108`. Added one explicitly synthetic source and **55 synthetic saved-run fixtures only to that disposable copy**; metadata and visible text say `SYNTHETIC HISTORY TEST ONLY`. These exercise pagination and do not represent model output or accuracy.

Verified all three pages, boundary button states, an oldest-run deep link outside the first page, unchanged open assessment during paging, retained comparison choices, and latest-page refresh. A simulated history 503 left the saved assessment visible; page retry recovered without losing either comparison choice. Clipboard success and narrow selected-run context worked.

On copied real data, indexed Kazakh text search produced a highlighted literal match. Its message link opened the exact saved run, highlighted/focused the intended transcript message, and returning retained the search. Queue language/ID filters and selection also survived a detail round trip.

At 1440 × 1000 and 320 × 850, history context/actions fit without page overflow. At 320 pixels, measured document width was 305 pixels with the vertical scrollbar; the history/selected-run/tool controls had equal scroll/client widths. The final browser console contained no warning/error entries.

Private evidence: `tested_source.json`, `saved_verification.json`, `final_verification.json`, `desktop-history.jpg`, `mobile-history.jpg` and the disposable verification helpers in that ignored folder. Screenshots show synthetic content. Provider calls and external HTTP were forbidden in the saved-data/cold-reopen checks; the browser server used empty provider settings, zero budget, a provider guard and blocked inference/organizer writes. No credentials, budget settings or original assessments were changed. No demo, publication or new accuracy claim is included.
