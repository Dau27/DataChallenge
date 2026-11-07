# Simple CSV and selected-run exports - 7 November 2026

Acceptance gate: **PASS** for targeted and combined software tests. Actual copied-data/browser checks are recorded with the final refinement verification.

Added a simple CSV with exactly one row per saved run/answer-set/criterion. Columns include readable answer/disposition, typed value, weight/points, total availability/reason, evidence IDs and source/checklist/review timestamps. Nulls, N/A and unscored flags retain their meaning. Existing archival JSON/CSV remain available with both original/effective results and ordered review history.

Added bounded selected-run downloads from the queue. Only checked, currently visible conversations with a saved run contribute IDs; unstarted and hidden rows are excluded. No selection means disabled exports, never an implicit all-record export. Selection changes/unmount invalidate a pending download. Source excerpts remain explicit opt-in, and source quotations can be private even after credentials are redacted.

`GET /api/evaluations/export-batch` accepts 1-100 unique repeated evaluation_id parameters and format json/csv/simple_csv. Empty, duplicate, overlong and oversized selections fail validation; missing IDs fail the entire request with 404. IDs/order are preserved. A single read snapshot freezes all included data; no job or review is created. Standalone and batch manifests include generation time, exact run IDs/updated_at, source/checklist hashes and excerpt policy. No build identity is invented.

Verification actually run:

- Export-specific backend tests: **15 passed**, covering types, failed/unresolved results, Unicode/multiline/formula-like text, all three formats, exact selection/order/namespace, 100-run bound, privacy/opt-in and a consistent concurrent-review snapshot.
- Four additional HTTP-route cases passed in the combined suite, including format dispatch, filenames, validation, all-or-nothing errors and unchanged rows.
- Export-specific client plus existing saved-inspection tests: **11 passed**. Two additional queue-integration cases passed in the combined suite: hidden/unstarted rows cannot leak into an export and pending text search disables stale selection export.
- Combined final software checkpoint: **173 backend / 58 client passed, one paid opt-in skipped; TypeScript/Vite build passed**. Earlier intermediate builds identified unsupported exact options in two test helpers; those test-only options were removed and the final build passed.

Credential/recording/organizer URL filtering, Unicode and formula protection apply to every derived format. Manifests use sanitized identities. Model calls are forbidden in the new backend fixtures; no main database or .env edits. No migration, scoring-rule change or provider integration was added. Demo remains deferred.
