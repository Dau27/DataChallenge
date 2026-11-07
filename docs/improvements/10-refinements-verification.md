# Refinements: final verification - 7 November 2026

**Completed:** stale comparison refresh repair, clearer difference views/provenance, simple and selected-run reports, all-message search navigation/highlights, and safer portable browser presets. No evaluator, rubric, scoring rule, model integration, dependency or main-data change. Demo remains deferred.

Stage details: [comparison repair](07-comparison-refresh-and-differences.md), [exports](08-simple-and-selected-exports.md), [search/presets](09-match-navigation-and-presets.md). This implements the selected refinements from the [market follow-up](../ADOPTED_FEATURE_REVIEW.md); it does not claim every optional recommendation there is implemented.

## Commands and outcomes

- `.venv/Scripts/python.exe -m pytest -q`: **173 passed**, 31.15 s; one existing Starlette/AnyIO deprecation warning. Real OpenAI HTTP is forbidden by ordinary tests. New backend fixtures also forbid Provider.request and use temporary synthetic databases.
- Frontend with CQA_LIVE_SMOKE=0, `node node_modules/vitest/vitest.mjs run`: **58 passed / one paid opt-in skipped**, 7.18 s. New tests cover either-side comparison refresh, state-only changes, late/error responses, compatibility/nulls, selection-safe downloads, Unicode match pages, v1 migration, atomic failures, cross-tab drafts and import preview.
- `npm run build`: **passed** after final wrapping styles, Vite 1.97 s. `pip check`: **no broken requirements**. Intermediate builds found unsupported exact options in two test helpers; these were corrected before the final successful build.
- Private verify_features.py on a new copy: **249 self-comparisons / 249 JSON exports / 249 archival CSV exports**, six multilingual source-text queries and cold reopen passed. Fields and score sets match saved detail responses; no feature request changed copied rows after app bootstrap. Provider and external HTTP transport forbidden.
- Private verify_refinements.py: **249 simple CSV exports**, **100-run batches in all three formats**, **187 match pages across 69 query/conversation pairs**, and the real unresolved-call comparison passed. Exact selection/order/source/checklist identities and null totals were retained; paginated message IDs matched complete source-text membership and order.
- Read-only saved-score/history verification: **130 selected original/effective snapshots**, zero arithmetic/contract issues, **198 exact review-history replays**, all 26 earlier development diagnostics plus three correction checks still match. DEV remains **64 complete / one needs review**. Originals, nine appeals/nine decisions and actual v10/v11/v12 provenance stay unchanged; no live v13 validation is claimed.

## Actual browser and downloaded files

Used a temporary loopback app on port 8125 with a private database copy, empty provider/organizer credentials, a zero budget, Provider.request blocked and all HTTP writes rejected. This was functional testing of the requested controls; no demo preparation, rehearsal or presentation.

- Literal search on actual p1-ru-001 showed messages 1-5 of nine, then 6-9, with highlighted original source text and exact message links.
- A selected simple CSV downloaded through the real browser and parsed as **16 criterion rows for exactly one selected v1 run**. No excerpts appeared without opt-in.
- Created a test preset, duplicated and renamed it, exported two saved presets, selected that file locally, inspected collision-renamed import entries, confirmed import and reloaded. Saved/imported choices remained available. Preset file schema 1 is independent of browser storage schema 2; its v1 filename identifies checklist v1.
- Comparison difference filters showed **zero answer/point changes and seven detail-only changes** for an actual historical pair, retaining its compatible total difference and recorded prompt/schema hashes/model identifier.
- Final document/content widths both **1265 px**; no horizontal page overflow. Added wrapping keeps portable-import previews within their panel. This audit does not claim additional responsive breakpoints were tested.

Review-refresh transitions were verified by component regressions and synthetic backend review tests. The actual saved-data browser checks inspected existing judgments and made no reviewer decision. Browser download examples and private evidence remain outside Git. The temporary server was stopped.

## Preservation, spending and limits

Every main row/column and all **30 protected files** match the pre-change baseline, including .env, budget baseline, both original rubric files and 26 archived reference files. All pre-existing copied rows are identical. The existing Budget constructor added only its one initial accounting row to the copy; opening amount, coverage and provenance match the reviewed baseline. No evaluation, appeal, review or reservation was added to the main database.

Call p4-ru-005 remains original Yes/**92.31**, effective contact **needs_review**, final total **null**, appeal open. The request does not authorize forcing an unclear introduction into a resolved score. No independent accuracy/official-grade claim is added.

Added provider requests: **0**. Added inference: **$0.00**. Paid limit remains zero. User/API credentials and original results are preserved. Private backup, machine-readable verification and final preservation evidence are under ignored local_data/refinements_20261107.

The selected refinement set is complete. Optional future work includes deeper queue-query optimization, explicit unknown-flag filtering, richer denominator explanations and configuration/cost coverage advisories. Independent/policy validation, live current-prompt behavior, organizer-held control/replacement data and public/event handoff remain separate gaps. **Demo execution remains deferred.**

## Concurrent work and exact checkpoint

Unrelated audit helpers/tests and later interface changes appeared while this task ran, including App/Budget/main, extracted queue filters and metadata added to the preset-hook return value. They were preserved. To avoid bundling that unfinished work, the verified refinement source was copied to an isolated worktree/branch **refinement-refresh-20261107**, based on **589d7a4**. Its queue integration was reconstructed from that base with only this task's changes; the original completed preset hook was fingerprint-checked. The shared working files were not overwritten or reverted.

Exact isolated-source checks passed again: **173 backend** (30.43 s), **58 client / one paid opt-in skipped** (8.44 s), and production build (Vite 3.48 s). `npm ci --offline --no-audit --no-fund` installed 115 already-cached pinned packages in 16 s into this isolated checkout. The generated JS/CSS asset identities match the versions used for the functional browser check. No dependency version changed.

The private feature checkpoint is kept separate from concurrent main-branch work; no automatic merge, visibility change or submission is performed. Machine-readable checkpoint/source scans are retained in the private refinement evidence folder. The scope is the requested repair/refinements, not the separate audit/interface effort.
