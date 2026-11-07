# Match navigation and safer presets - 7 November 2026

Acceptance gate: **PASS** for targeted and combined software tests. These refinements use saved transcripts/browser storage and no inference. Actual copied-data/browser verification follows in the final refinement report.

## Transcript matches

Added next/previous pages for all matching messages instead of stopping at five snippets. Each page retains the exact source revision/hash, query/speaker and message order. Links focus the actual message and selected saved run. Pending/error pages hide stale snippets, support retry and ignore late responses after navigating back or changing search context.

Literal occurrences are highlighted using offsets into the original Unicode source. Python code-point offsets are consumed with Array.from in React, including emoji, decomposed accents, Cyrillic/Kazakh text, case-fold expansions and Hangul normalization. No normalized/generated text replaces the source and no HTML is injected. Speaker-only searches and off-page matches are counted without building unnecessary snippet maps.

`GET /api/conversations/{id}/matches?q=...&speaker=...&offset=...&limit=...` is read-only, bounded to 1-25 matches per page (UI uses five), with a 200-character query. It supports exact historical revisions and explicit absent-source errors. Search totals count matching messages, not occurrences of a word inside one message.

## Saved presets

Browser storage v2 keeps presets and active selections in one validated record, preventing a two-write partial save. Valid v1 presets/active choices migrate while the old keys remain as recovery evidence. Dataset/checklist scope, 50-preset limit, 80-character names and existing filter fields remain validated. Invalid or blocked storage is reported; ordinary filtering continues to work.

Save filters creates a new named preset; Update saved filters changes the selected saved values. Rename retains unsaved edits, Duplicate copies the saved values, and collisions require a new name rather than silently overwriting another preset. A storage event from another tab preserves current edits and requires an explicit reload.

Preset JSON export contains only the current checklist's saved presets. Imports are limited to 100 KB, validate format/scope/fields, preview included search text and collision-renamed entries, and require an explicit import action. Import retains current filters until a preset is chosen. Files can contain private search quotations; the UI discloses that. No account/synchronization backend was added.

## Checks actually run

- Search-specific backend plus saved-inspection tests: **24 passed** (seven new search checks/17 existing), covering complete pagination, counts/order/roles, bounded parameters, source identity, Unicode highlight ranges and unchanged rows.
- Match navigation plus existing search/preset client tests: **11 passed** (three new/eight existing).
- Preset-specific plus existing search/preset tests: **20 passed** (12 new/eight existing), covering migration/scope, atomic storage failure, explicit edit operations, multi-tab drafts, bounded/invalid imports, preview confirmation and export privacy fields.
- Combined suite: **173 backend / 58 client passed, one paid opt-in skipped; build and pip check passed**. The existing deletion assertion was updated to inspect v2 storage; legacy v1 keys intentionally remain untouched.

No main data, credentials, originals, judgments, scorer or evaluator prompt changed. Presets remain local to one browser/origin; files are an explicit portability mechanism. No semantic search, embeddings, ASR, new model call or demo work.
