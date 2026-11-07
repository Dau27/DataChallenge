# Stage 23 — offline quality reporting

Implemented during the user's authorized continuation after the [PDF audit](../audits/2026-11-08/02-post-cohort-print-audit.md). This is optional evaluation tooling, not another required manual-review packet. It changes no stored judgment, scoring rule, model request, application route or frontend. No inference spending; demo deferred.

## Purpose and repository lessons

The [public-repository review](../PUBLIC_HACKATHON_REPOS_2026-11-08.md) found two useful patterns: [report unlabeled when consensus is missing](https://github.com/Nurzhic/CQA-Hackathon/blob/main/backend/app/benchmark_metrics.py), and [require explicitly selected compatible references](https://github.com/erassylls/doomsday/blob/main/lib/calibration.ts). This implementation independently adopts those ideas within our existing source/run/checklist boundaries. No peer code, labels, datasets or claimed accuracy was imported or executed.

A report compares **explicitly selected saved originals** with an optional external reference manifest. The real saved dataset currently has no independent labels supplied to this tool, so its actual output is **unlabeled**, with metrics null. Existing appeals, effective judgments and the archived agent-authored packet are never automatically used as references. Declared reference origin is reported but not independently verified by software. Agreement with supplied labels is not automatically correctness, current-model accuracy or an official project score.

## Usage

Keep selections, references and reports private under ignored local_data. This command needs the existing Python environment and database only: no credentials, provider configuration, server startup, job worker or model call.

Create local_data/quality-selection.json with 1–200 exact saved evaluation IDs copied from the existing review links or saved export. The identifier below is illustrative and must be replaced with an actual selected run:

```json
{
  "format_version": 1,
  "evaluation_ids": ["SAVED_RUN_ID_FROM_REVIEW_LINK"]
}
```

From the repository root:

```powershell
.\.venv\Scripts\python.exe scripts/quality_report.py --database local_data/cqa.sqlite3 --selection local_data/quality-selection.json --output local_data/quality-report.json
```

An existing private backup/copy may be used as the database path. The service opens one read-only/query-only SQLite transaction. It does not construct Database, initialize/migrate tables, bootstrap budget state, read .env or repair a historical record. Output requires a new file in an existing directory; existing files and links are not overwritten. JSON input is limited to 2MiB per manifest, with duplicate keys, unsupported versions, unknown fields and duplicate selections rejected.

One report requires one exact dataset/checklist version and one selected run per exact conversation revision. Missing selected IDs, mixed datasets/checklists and repeated source revisions cause an explicit error. Existing failed/unfinished runs remain selected cases and count as missing predictions when compatible reference labels exist. No fallback to an older successful run or automatic latest-run selection.

## Optional reference contract

Use --references local_data/quality-references.json only when explicit references exist. The example below is illustrative: replace every identity/hash and supply actual labels. All-zero hashes are not usable references. Read conversation_id/source_content_hash from the saved export's source.id/content_hash, and checklist_content_hash from evaluation.checklist.content_hash. The evaluation ID must match the explicitly selected original run.

```json
{
  "format_version": 1,
  "reference_set_id": "YOUR_EXPLICIT_REFERENCE_SET",
  "declared_origin": "working_reference",
  "cases": [
    {
      "evaluation_id": "SAVED_RUN_ID_FROM_REVIEW_LINK",
      "conversation_id": "EXACT_CONVERSATION_REVISION_ID",
      "source_content_hash": "0000000000000000000000000000000000000000000000000000000000000000",
      "checklist_content_hash": "0000000000000000000000000000000000000000000000000000000000000000",
      "judgments": {
        "contact": {"disposition": "assessed", "value": true},
        "needs": {"disposition": "not_applicable", "value": null},
        "consultation": {"disposition": "unresolved", "value": null}
      }
    }
  ]
}
```

Declared origins are independent_human, working_reference or synthetic. The output always preserves origin_independently_verified=false; independent_human is a supplied assertion, not proof performed by this tool. Only mark it when that description is actually justified. No references are supplied/generated on the user's behalf by this stage.

Partial labels are allowed. An omitted criterion is unlabeled; unresolved/null is an abstention; neither becomes N/A or No. Assessed binary/flag labels require strict JSON booleans. Scale labels must be exact saved anchors. N/A must be permitted by the saved criterion and carry null. The tool checks compatibility/type, not whether a human correctly interpreted the source or N/A condition. Invalid dependent labels or mismatched source/checklist identities reject that reference case without creating a score. Unselected reference IDs are listed explicitly and never joined by guesswork.

## Report semantics

- Overall status is unlabeled with metrics=null until at least one compatible definitive label exists. Language/channel/criterion/provenance groups still expose selection coverage. A partial labeled report does not imply that all cases or criteria have references.
- Agreement over all definitive labels counts missing/unresolved predictions as nonmatches. Conditional observed-only agreement and prediction coverage are separate, so failures cannot disappear from the headline denominator.
- N/A has a separate six-cell reference/prediction matrix, including missing predictions. It is distinct from false and abstention. Critical flags retain TP/FP/FN/TN plus missing positive/negative counts; observed precision/recall and all-reference-positive recall use explicit separate denominators.
- Scale error includes assessed pairs only and retains the saved anchor units. Cross-criterion comparisons use mean_absolute_fraction_of_saved_maximum. Raw anchor MAE is withheld when more than one criterion unit is present, so 0–10 and 0–20 anchors are not pooled as comparable raw units. Computed rates/errors round half up to six decimals; saved operator totals remain exact. Total score error is computed only when every reference criterion is definitive and a validated original total exists. The reference total is clearly marked computed_reference_total; no existing score is overwritten and unavailable totals are never zero.
- Case links preserve exact source/run/criterion IDs. No source transcript, explanation, reviewer rationale, audio URL, credentials or arbitrary metadata is serialized. This is a private identity-linked report, not anonymized data.
- Provenance distinguishes recorded provider/model/versions/hashes, known generation settings and response model IDs. Missing metadata remains unknown, without substituting current defaults. Incomplete request identities stay separate per run; a version label alone cannot merge different prompt/schema hashes or generation settings.
- Original validation means schema/source-ID validity and deterministic arithmetic replay, not semantic certification. A historical original that fails today's structural contract is reported as unavailable for comparison and preserved. Unknown raw metadata is withheld.

## Verification

Targeted command in the coordinator worktree, with the absolute root interpreter:

```powershell
& 'C:/Users/user/Desktop/DataChallenge/.venv/Scripts/python.exe' local_data/offline_pytest.py -q backend/tests/test_quality_report.py --tb=short
```

The offline wrapper supplies empty credentials, zero budget and an external-socket guard. Targeted coverage includes known disagreement/total bias, partial labels and abstentions, N/A and critical denominators, custom anchors/weights, failed/missing/unresolved originals, malformed reference types, exact hashes, mixed scopes, duplicate selections/keys, parser size limits, immutable rows, CLI cold reread/no-overwrite/error privacy and prohibited network/DB initialization. Provenance regressions cover same version names with different prompt/schema hashes, generation settings and response model IDs.

Initial synthetic test setup omitted a required cache_key; correcting that fixture produced 47 passes. A subsequent review exposed insufficient provenance grouping: four new regressions failed before the grouping correction, then all 51 targeted tests passed. These failures were not product passes. A golden-case regression then reproduced pooled raw scale units; normalized cross-criterion errors now replace that misleading aggregate. Another regression reproduced negative-zero anchor disagreement; numeric signed zero now compares as the same zero anchor. All 52 final targeted tests passed (10.63s). Intermediate full suites passed 455 and 459; final source acceptance follows below. Repeats were limited to new code changes or demonstrated concerns.

Actual acceptance uses only saved-data copies and **no references**. The real CLI and cold reread passed for 65 selected DEV originals / 520 judgments: status unlabeled, zero independent labels, all group metrics null. Reviewed Kazakh still reports its original 84.62; the unresolved call's original 92.31 is retained separately from its withheld effective total. All 249 individual saved-run checks passed: 197 replayable originals, 51 not-succeeded runs and one historical original failing today's contract. The recovery inspector separately confirms the existing two original/effective assessment-contract warnings, with SQLite integrity and foreign keys valid. No historical row was repaired; this does not mean a new DEV semantic error was discovered. All copy rows/schema/file bytes, main 15 tables/schema and 30 protected files remain unchanged. Provider/network/DB-initialization attempts: zero. Private evidence: ignored local_data/quality_report_20261108.

Source additions are limited to [read-only service](../../backend/app/services/quality_report.py), [CLI](../../scripts/quality_report.py) and [synthetic regressions](../../backend/tests/test_quality_report.py). No schema/dependency/frontend/scorer/evaluator change is needed. Final combined verification/checkpoint is recorded after acceptance. Existing independent accuracy, approved-policy, organizer, recording and public/event gaps remain; this feature does not justify raising the informal 85/100 estimate.

## Final source acceptance

Final socket-guarded full backend suite: **460 passed**, 87.04s; one existing Starlette/AnyIO deprecation warning. Final targeted suite: **52 passed**, 10.63s. Final source's actual CLI/report acceptance repeated successfully in the ignored published evidence folder:65 selected originals / 520 unlabeled judgments,249 individual runs, cold reread parity, zero provider/network/DB-initialization attempts, unchanged copy file bytes/all rows/schema and main/protected data. `compileall`, CLI help and diff check passed. Client source/lockfiles were not changed, so this task's fresh 182-client/one-skipped/production-build/pip checks remain valid; no redundant frontend rerun is claimed. Preservation/mirroring/history-scan/local-checkpoint evidence is recorded in CURRENT_CONTEXT. No remote push or new API spend; demo stays deferred.

Local code checkpoint **0cfa5b4f4dcdce05e2f8ffe7c59349e138a67845** preserves audit checkpoint a0e29b0. Hash-gated mirroring and the root CLI passed independently: all234 Git-visible files match the tested coordinator, all156 prior source files are unchanged and three new source/test/CLI files are added. Main15 tables/schema,249 evaluations,30 protected files and the user's staged index are unchanged; budget_state remains0. Both builder worktrees stay clean. At that checkpoint the final scan passed234 source candidates /475 history blobs /75 Markdown files /359 local links, zero credential/private-path matches and diff check passed. This paragraph is a documentation follow-up; no new suite outcome or official freeze is claimed.
