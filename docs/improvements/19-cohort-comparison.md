# Stage 19 — saved-run cohort comparison

**Builder handoff: ready for coordinator integration, 8 November 2026.** Implemented and tested in the coordinator-provided `sprint-cohorts-20261108` worktree, from audited baseline **d7d8a9d2a93ff5b537e34e689dd63b0e952f0fb3**. The canonical root handoff was confirmed **READY** before the first edit. No existing tracked file, shared route/screen/type/style, database/scoring implementation or `CURRENT_CONTEXT.md` was changed. No merge or push.

## Owned files

| File | Responsibility |
| --- | --- |
| `backend/app/services/cohort_comparison.py` | Strict request contracts, recorded options, exact run selection, coverage, transitions, compatibility and aggregates |
| `backend/app/api_cohorts.py` | New read-only options/comparison router; deliberately not mounted by this builder |
| `backend/tests/test_cohort_comparison.py` | Synthetic service/API/identity/bounds/compatibility/privacy/snapshot tests |
| `backend/tests/test_cohort_saved_copy.py` | Actual coordinator-copy checks through SQLite `mode=ro`, exact existing-reader parity and whole-copy preservation |
| `frontend/src/CohortComparison.tsx` | Standalone secondary-tool disclosure, selectors, coverage, transitions and exact-case lists |
| `frontend/src/CohortPairPreview.tsx` | Existing pair API reader with exact source/run/update/basis guards, criterion preview and evidence links |
| `frontend/src/cohortTypes.ts` | Feature-owned DTOs and defensive client response validation |
| `frontend/src/cohortComparison.css` | Scoped cohort layout, wrapping, table scrolling and focus styles |
| `frontend/src/cohortComparison.test.tsx` | Component behavior, selector meanings, limits, errors/retries, stale data and contract checks |
| `frontend/src/cohortPairPreview.test.tsx` | Exact-pair/basis/evidence identity, late results, retry and callback tests |
| `frontend/src/cohortTestFixtures.ts` | Explicitly synthetic client test data; not imported by application code |
| `docs/improvements/19-cohort-comparison.md` | This interface, acceptance and integration handoff |

Dependencies are unchanged. The provided frontend lockfile was installed offline. Private samples and verification helpers remain ignored under this worktree's `local_data`; no real saved-data fixture is added to source control.

## Frozen route and request interface

Export: `router` from `backend/app/api_cohorts.py`, with prefix **`/api/insights/cohorts`**.

- **GET `/api/insights/cohorts/options`** returns version1, `datasets`, global saved `checklists`, `selector_fields`, withheld-dataset count, selection/scope/unknown notices and `max_pairs: 200`.
- Each dataset includes `dataset_group_id`, count of all exact source revisions, saved evaluation count, and per-checklist profiles. Profiles contain run counts and `{values: [{value, count}], unknown_count}` for each selector field. These are counts across saved runs, not just the latest selected members.
- **POST `/api/insights/cohorts/compare`** accepts the following body. Both routes use one `db.read_snapshot()` and return `Cache-Control: no-store`.

```json
{
  "dataset_group_id": "DEV",
  "left": {"checklist_id": 1, "prompt_version": "recorded-version-A"},
  "right": {"checklist_id": 1, "prompt_version": "recorded-version-B"},
  "basis": "effective",
  "limit": 200
}
```

This is a structural example, not a claim those prompt versions occur in the private data. Each selector requires a strict positive integer `checklist_id` and permits only `model`, `prompt_version`, `schema_version`, `evidence_validation_version`. Omitted means any recorded value, **explicit null means unknown**, and a string means exact recorded equality. No current provider/prompt defaults fill historical gaps. Non-string, missing or unsafe provenance is withheld as unknown. Identifier strings are capped at150; URLs/credential material/control characters are refused or withheld. Extra fields, coerced IDs/bounds and unsupported bases are rejected. Defaults are `basis: effective`, `limit: 200`; allowed limits are strict integers1–200.

Source scope is **every exact saved revision in the one named dataset**, including historical revisions and sources with neither selected cohort. Ordering is `source_id, revision, id`. If the scope exceeds the requested limit, the API returns422 with the actual revision count and **no partial comparison**. A missing dataset/checklist returns404; an invalid saved checklist snapshot returns409. This version has no cohort pagination or cross-dataset result.

For each revision, each cohort chooses the latest matching **`(created_at DESC, id DESC)`** run. A failed/pending/unresolved latest match remains selected; no older-success fallback. Different revisions, including matching logical source IDs or equal content in another dataset, are never paired together. Version/name changes do not silently relabel older configurations.

## Response v1 and arithmetic contract

Authoritative TypeScript shapes are in `frontend/src/cohortTypes.ts`.

Top-level fields: `version`, `dataset_group_id`, sanitized `left`/`right` retaining omitted/null distinctions, `basis`, `limit`, `selection_policy`, `scope_policy`, `coverage_policy`, `coverage`, `pairs`, `criteria`, `total_difference`, `notice`.

Each pair records `source.{conversation_id, source_id, revision, content_hash, dataset_group_id}` and nullable `left`/`right` manifests. Each side includes exact evaluation ID, conversation/checklist IDs/hash, creation/update identities, execution state, **selected-basis completeness**, separate current `run_completeness`, original/effective/basis availability, exact criterion-coverage validity, nullable saved total plus `numeric/missing/invalid` state, saved scoring version, cache lineage and allowlisted provenance. Provenance includes recorded provider/model/prompt/schema/validation/scoring identifiers, valid stored hashes, bounded generation settings, recorded response models and explicit unknown fields. Conflicting recorded checklist hashes are marked and excluded from comparable aggregates. No transcript, recording URL, raw error, arbitrary metadata, explanation or evidence excerpt is returned by options or aggregates.

Exclusive statuses, in precedence order: `missing_both` / `missing_left` / `missing_right`, `failed`, `pending`, `unresolved`, `invalid`, `incompatible`, `no_numeric_total`, `matched`. `matched` means comparable numeric totals; `paired` independently counts two existing saved IDs. Fixed reason codes preserve overlapping failure, missing, unresolved, invalid, provenance and compatibility conditions. Coverage also reports cached, same-run, unknown-provenance and conflicting-provenance pair counts. Identical filters are disclosed before running and produce self-pairs.

The selected original can be complete while the current effective workflow is unresolved, or the reverse. The selected saved score/answers determine cohort completeness; the other basis does not contaminate it. All-N/A/no-applicable-weight totals remain null and use `no_numeric_total`, rather than being called unresolved or zero. Invalid saved numbers/answer coverage are explicit and never contribute invented zeroes.

For every criterion, transitions contain typed dispositions/values, comparability, count and exact source-revision IDs. All selected revisions remain in the denominator, including unavailable sides. Counts separate answer/disposition, configuration, semantic definition and detail-only changes. Semantic comparability follows the existing pair reader's definition rules; weights/sections remain configuration differences. Raw-point deltas and totals reuse the saved pair reader and recorded score-rule versions, without invoking the scorer. Unknown/different scoring rules block numeric aggregation. N/A, unresolved and unscored flags do not become zero-point observations.

`{count, sum, mean}` summaries use finite Decimal values and nullable sum/mean when there are no eligible pairs. Differences are **candidate minus baseline**, independently bounded for each comparable metric. Shared point-rule compatibility can permit an unchanged criterion's raw-point comparison even when changed checklist snapshots make whole-run totals incompatible. A flag transition stays visible and unscored. Detail-only counts exclude answer/point/configuration changes. These are descriptive historical differences; **higher operator scores are not evidence of evaluator accuracy**. Cached or same-run observations do not establish independent assessments.

## Required coordinator integration

Only the coordinator should make these shared-file changes:

1. In existing `backend/app/insights_api.py`, import `router` from `backend.app.api_cohorts` and call its parent router's `include_router(cohorts_router)`. The child already owns its full prefix; do not add another `/api` or `/insights` prefix.
2. Mount default `CohortComparison` from `frontend/src/CohortComparison.tsx` in the current secondary-tools area. Its only required prop is **`onOpenPair(leftEvaluationId: string, rightEvaluationId: string): void`**. It owns data fetching/types/scoped CSS and its own dataset scope. Queue filters do not apply; the component says so explicitly. No shared type or stylesheet addition is needed.
3. The callback must open **both supplied IDs**, rather than just selecting the candidate and letting the existing comparison choose a default baseline. Either ID can be outside the first history page. Resolve the source from those saved runs if the existing screen needs it. Never launch an evaluation to fill a missing side.
4. The frozen callback carries IDs, not basis. The owned pair preview already fetches the exact requested original/effective basis and verifies source hash, both IDs and both update timestamps before enabling the callback. It makes clear that the existing review workspace owns its own answer-basis selectors. If automatic basis synchronization is desired, coordinate an explicit callback extension; do not silently show effective answers as an original-basis result.
5. Keep the full guarded suites/build and combined browser acceptance with the coordinator, including actual saved pairs, 320px/table scrolling, disclosure/layout and transitions from the existing queue/history/print flows. No preview server or browser was started by this builder, as required by the handoff.

The exact pair preview reads only the existing **GET `/api/evaluations/compare?left_id=...&right_id=...&left_basis=...&right_basis=...`** endpoint. Evidence links target the exact source/run/criterion/message. Changed-run responses are refused and require cohort refresh. Case and pair closing restore keyboard focus; incoming scope/basis/selector changes immediately hide obsolete results. Late responses and errors cannot restore an earlier selection.

## Actual checks and results

Commands ran only in the provided cohort worktree. `$python` below denotes the coordinator-provided absolute interpreter in the original repository's `.venv`; the offline wrapper establishes empty provider/organizer configuration, limit0 and the socket guard.

```powershell
& $python local_data/offline_pytest.py -q backend/tests/test_cohort_comparison.py backend/tests/test_cohort_saved_copy.py
node local_data/check_cohort_contract.mjs
# frontend directory, after dot-sourcing ../local_data/offline.ps1
npm ci --offline --no-audit --no-fund
node node_modules/vitest/vitest.mjs run --maxWorkers=2 src/cohortComparison.test.tsx src/cohortPairPreview.test.tsx
node node_modules/typescript/bin/tsc -b
```

Targeted acceptance: **50 backend tests / 27 client tests passed; TypeScript passed.** Backend retains one existing Starlette/AnyIO deprecation warning. No full combined suite/build is claimed by this lane.

Synthetic coverage includes exact old/new revisions and dataset namespaces; no-success fallback; identical and microsecond timestamp ordering; wildcard/null/exact filters; known answer, N/A, unresolved and flag transitions; original/effective review divergence; all-N/A null totals; added/removed/type/weight/definition changes; unknown scoring versions; cached/same-run lineage; missing/failed/pending overlaps; invalid totals/judgments/criterion coverage; privacy withholding; concurrent review snapshot isolation; strict API inputs; **200 complete pairs accepted and the 201st revision refused**. Client tests cover scope/basis changes, missing sides, explicit limits, stale/error responses, retries, invariant validation, identity drift, evidence routes and callback/focus behavior.

Actual copy: **249 evaluations, 75 revisions, two datasets, all15 tables**. Twenty original/effective and recorded-selector scenarios produced **376 exact-pair checks**, including **226 checks between different run IDs** and **178 distinct ID pairs**. Selected IDs were checked independently against ordered SQL; comparable totals/raw points matched the existing exact-pair reader. The owned client guard also accepted all20 actual server responses containing **1,080 source-pair records**, including missing cases. These counts are checks, not independent judgments or accuracy measurements.

The actual-data test opens the supplied copy through SQLite **`mode=ro`**, without application/Database initialization, budget bootstrap, migration or scorer invocation. Every table plus schema/index SQL fingerprints matched before and after; provider attempts were **zero**. Private evidence: `local_data/cohort_saved_checks.json`, `cohort_client_contract_checks.json`, and sanitized-but-private `cohort_contract_samples.json`. The private bridge script validates those actual responses with the compiled owned client contract; no data is fetched externally. Original main, credentials, reviews, seed and protected files were not edited.

Earlier iterations caught synthetic-fixture revision uniqueness, Decimal formatting/import expectations, a preservation helper's rowid assumption for WITHOUT ROWID index tables, and a client guard syntax error; all were corrected before final acceptance. Actual metadata coverage was inspected rather than assuming balanced configuration membership. No API spending, organizer fetch, schema change, publication or demo work occurred.

## Limits and remaining integration acceptance

- A single dataset above200 exact revisions is refused; arbitrary subcohorts, pagination, cross-dataset totals, charts and exports are outside this version.
- Selectors match the frozen checklist/model/prompt/schema/validation fields. Hashes/generation/response models are displayed as recorded provenance, not additional selector dimensions. Wildcards can intentionally include mixed recorded configurations; unknowns stay visible.
- Cohort results are one read snapshot. Background changes do not continuously poll; refresh explicitly. Exact-pair opening detects an updated run and refuses stale identity. This is not immutable historical-effective replay at an old update timestamp.
- Semantic evidence truth and model accuracy are not established. Validation checks stored answer contracts; this feature does not acquire policy evidence, re-grade, re-score or produce new judgments.
- Shared mounting/exact-ID review integration, full combined suites/build and real browser layout acceptance remain with the coordinator. The component's own original/effective preview is verified; the existing screen's automatic basis synchronization is limited by the frozen two-ID callback.

After handoff, owned-file revisions should address coordinator-reported integration findings only. Do not merge, push, change shared ownership or start the deferred demo.
