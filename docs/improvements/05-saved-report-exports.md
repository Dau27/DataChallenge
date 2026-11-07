# Saved JSON/CSV exports — 7 November 2026

Stage passed its targeted acceptance gate. Each saved evaluation has working JSON and CSV download controls. Reports include source identity/revision/hash, saved checklist, original/effective judgments and scores, explanations, evidence IDs, attempt/usage provenance, appeals and ordered reviewer decisions. Failed evaluations and withheld totals retain nulls. No new inference or evaluation jobs are created.

`GET /api/evaluations/{id}/export?format=json|csv&include_excerpts=false` reads one consistent SQLite snapshot. Source evidence excerpts, including reviewer evidence ranges, require an explicit checkbox. Stored explanations/comments can themselves quote the source; this is disclosed. Recording URLs, organizer configuration and credentials are excluded/redacted. Metadata/attempt fields are limited to evaluation provenance/accounting. Redaction counts are disclosed, and saved originals are never altered.

CSV is UTF-8 with a BOM and contains typed long-form evaluation/score/criterion/appeal/review records, plus excerpt records when requested. Nested JSON cells preserve strict booleans, nulls, Decimal strings, definitions, section totals and review history. Formula-like spreadsheet text is apostrophe-prefixed in scalar cells; nested JSON retains the sanitized report value. Downloads report errors and ignore responses after leaving a selected run.

Commands actually run:

- `.venv/Scripts/python.exe -m pytest -q backend/tests/test_saved_inspection.py`: **9 passed** (four comparison and five export checks). Export checks parse both formats, compare original/effective/history against saved detail, preserve rows, retain N/A/unresolved/flag types, verify Unicode/multiline/formula protection, excerpt opt-in, credential/URL redaction, failed results and invalid parameters. Provider inference is forbidden.
- `npm test -- --run src/savedInspection.test.tsx` from frontend with CQA_LIVE_SMOKE=0: **4 passed** (two comparison/two export). Checks actual response blobs/download clicks, both formats, explicit excerpt inclusion, errors and unmounted responses.
- `npm run build` from frontend: **passed**.

No API spending. Follow-up [full-suite and actual saved-data checks](06-transcript-search-saved-filters.md) passed: 249 JSON and 249 CSV reports matched stored fields/scores, actual browser downloads parsed correctly, and originals/private files remained unchanged. Consistent snapshot behavior during a concurrent synthetic review also passed. Demo remains deferred.
