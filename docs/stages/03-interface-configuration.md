# Stage 3 — Interface and versioned configuration

Later enhancement: [checklist preview and field errors](../improvements/02-checklist-preview.md), budget-aware evaluation controls and [pending/critical review filters](../improvements/03-review-filters.md) passed root/isolated-source tests plus copied-data browser verification without inference. The original stage evidence below remains historical.

Status: **PASS**. Real UI/component → actual API → actual provider flow and in-app browser smoke verified.

- React/TypeScript/Vite UI includes conversation import, dataset/language/channel/status filters, selection/batch evaluation, and persistent job states.
- Conversation detail shows the exact source transcript next to assessments, original/effective totals, sections, criterion definitions, points, N/A and uncertainty reasons, and independent flags.
- Evidence navigation uses stored message IDs and renders excerpts from stored source text. Calls provide recording access with no invented timestamp-to-audio mapping.
- Checklist editor supports adding/removing/editing criteria, types, weights, section definitions, scale anchors, and N/A conditions. Backend validation is authoritative.
- Draft edits are retained in browser session storage and saved separately as complete immutable versions. The UI makes the selected future-evaluation version explicit.
- Client interaction test adds a substantively new ticket-reference criterion through the editor and verifies a complete new-version request without altering the source snapshot. Backend integration test verifies that the new criterion changes provider schema/coverage and invalidates cache reuse. Both use explicitly synthetic test inputs.
- Local application responds at `http://127.0.0.1:8000`; home/health/transcript APIs returned HTTP 200 for real RU/KZ/EN records. All 65 real records are visible through the API as not evaluated.
- Initial browser verification was blocked on Windows Chrome URL confidence. Later the in-app browser became available: verified queue/filter states, withheld totals, exact evidence highlighting, saved versions/new criterion and responsive layout at the available pane width. Fixed a hidden-upload-input overflow and verified document/viewport widths match. Broader device testing is not claimed.

Checks actually run: initial TypeScript/Vite build passed; client tests passed (7 tests). A later test-fixture TypeScript error was found and fixed; final build/check repetition is recorded in CURRENT_CONTEXT.md.

Dependency audit: initial pins reported vulnerabilities; upgraded Vite to 6.4.5 and Vitest to 4.1.12, compatible with the installed Node 22.11.0. `npm audit` then reported zero vulnerabilities, including after adding DOM test dependencies.

Later live acceptance: `npm run live-smoke` passed. It adds a substantively new ticket-reference requirement using React editor controls, saves a complete new version, evaluates an actual DEV conversation with the real hosted provider, and verifies the new criterion returns No without changing application code. Exact old snapshots remain unchanged. This test uses a DOM emulator with real network/API/data, not mocked model output; it does not claim screenshot/browser verification.
