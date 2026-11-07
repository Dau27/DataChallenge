# Saved-run comparison — 7 November 2026

Stage passed its targeted acceptance gate. The detail screen can compare any two saved evaluations of the exact same conversation revision, with independent original/effective selectors, criterion answers, explanations, evidence links, configuration differences, raw points, saved totals and provenance. Failed runs and unresolved judgments retain unavailable/null values. Flags remain unscored.

`GET /api/evaluations/compare` reads one consistent SQLite snapshot. Cross-revision comparisons are rejected. Checklist or scoring-version differences suppress total deltas; changed criterion definitions suppress incompatible point/answer comparisons. A delta is a difference between stored results, not evidence of better model accuracy or operator behavior. No jobs, provider calls or database migrations are involved.

Commands actually run:

- `.venv/Scripts/python.exe -m pytest -q backend/tests/test_saved_inspection.py`: **4 passed**. Checks original/reviewed differences, preserved rows, revision boundaries, changed/added/removed rules, null totals, flags and failures; provider inference is forbidden by the fixture.
- `npm test -- --run src/savedInspection.test.tsx` from frontend with CQA_LIVE_SMOKE=0: **2 passed**. Checks answer-set selection, evidence navigation, changed-only filtering, stale-response rejection and retry.
- `npm run build` from frontend: **passed**, TypeScript and Vite.

The first backend run found an incorrect test expectation (-7.69); the all-applicable synthetic rubric has denominator 100, so the correct delta is -10.00. The expectation was corrected and the test passed; scoring code was not changed.

Private preservation baseline: local_data/inspection_features_20261107/before.sqlite3 and before.json. Main database and credentials have not been used for inference. Follow-up [full-suite, actual saved-data and preservation checks](06-transcript-search-saved-filters.md) passed: 249 stored self-comparisons, both answer sets and unavailable totals retained, zero provider requests. Scoring versions must be known and equal for deltas; normalized contribution changes are visible. Demo work remains deferred.
