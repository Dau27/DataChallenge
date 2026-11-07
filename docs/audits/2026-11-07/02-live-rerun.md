# Fresh live evaluation and persistence audit

Historical pre-fix run: the 44 complete / 21 needs-review results below are preserved as the initial audit. The subsequent fix/re-audit has 65 complete accepted results and 26/26 targeted checks; see [current results](C:/Users/user/Desktop/DataChallenge/docs/audits/2026-11-07/05-scoring-reaudit-results.md). The final set includes validated retained runs and selective new inference, with exact versions and all costs disclosed.

Audit date: 7 November 2026. No application code or evaluator prompt was changed. Every paid test used the existing configured OpenAI Responses adapter. All audit writes used a separate SQLite backup under ignored local_data/audit_20261107.

## Fresh DEV run

| Measure | Result |
| --- | ---: |
| Actual organizer records | 65 |
| Languages | 35 RU / 15 KZ / 15 EN |
| Channels | 60 chats / 5 calls |
| Successful executions | 65 |
| Complete assessments with numerical totals | 44 |
| Needs-review assessments with withheld totals | 21 |
| Failed/unstarted executions | 0 |
| Cached assessments | 0 |
| Provider request attempts | 65 |
| Structural output repairs required | 0 |
| Provider/budget stop | Neither |

Configured model: gpt-4.1-mini. Every fresh response recorded the actual model identifier gpt-4.1-mini-2025-04-14. Prompt: operator-context-evidence-v5; schema: dynamic-disposition-evidence-v2; original checklist v1. Cache reuse was explicitly disabled.

The prior saved main-database set remains 59 complete / 6 needs review across a mixed model/configuration history. This audit's 44/21 is a separate fresh single-model result. It does not replace the previous results or imply that withholding fewer scores proves greater correctness.

All 21 incomplete fresh assessments include a contact judgment marked needs_review. Other unresolved criteria overlap with those same conversations:

| Criterion | Assessed | N/A | Needs review |
| --- | ---: | ---: | ---: |
| Contact | 44 | 0 | 21 |
| Needs | 22 | 42 | 1 |
| Identification | 9 | 55 | 1 |
| Consultation | 61 | 3 | 1 |
| Empathy | 57 | 0 | 8 |
| Dialogue management | 62 | 0 | 3 |
| Closing | 42 | 19 | 4 |
| Critical flag | 65 | 0 | 0 |

These counts describe disposition choices, not their correctness. In particular, several contact uncertainties and closing/consultation N/A choices contradict observable transcript facts or the saved conditions.

## Validation and repeatability

A separate audit calculation recomputed weighted totals and section percentages from saved answers, using Decimal arithmetic directly rather than calling the application's score function. It also revalidated the judgment/evidence contracts.

**260 assessment snapshots checked, zero contract/arithmetic/section mismatches:** original and effective snapshots for the 65 prior and 65 fresh evaluations. Existing ordered evidence references and schema validity were checked. Semantic support requires the separate observations in report 03.

Comparison of disposition/value pairs, excluding wording-only explanation changes:

- 50 of 65 conversations changed at least one answer; 108 of 520 criterion answers differed.
- 41 original numerical totals changed, including transitions to/from withheld totals.
- Much of this comparison crosses models or schema versions and is not a pure repeatability test.
- Only 11 pairs matched the recorded provider/model, generation settings, prompt hash, schema hash, request-schema hash and scoring version. Of these, 9 changed at least one disposition/value, with 19 changed criterion answers.

Differences alone do not establish which result is correct. The exact-identity subset is a small repeatability diagnostic. The concrete source-rule contradictions in report 03 are the reason for withholding a scoring-quality pass.

Three positive critical flags in the fresh run were inspected: two off-company paid-service offers and one operator insult. This supports those examples only; it does not establish critical-error recall across the dataset.

## Live configuration, appeal and restart checks

The opt-in existing React DOM integration test passed against the isolated real API:

1. Edited and saved a genuinely new criterion through the editor.
2. Received a new nine-criterion checklist version and a fresh hosted evaluation.
3. Checked that the new ticket-reference criterion returned No for its absence.
4. Submitted and reviewed two agent-attributed appeals in separate UI actions.
5. Preserved the original score 100.00 and effective score 92.31 with decision history.
6. Remounted the detail view and read persisted state.

The audit copy now has eight review decisions because this run added two to the six pre-existing demonstration decisions. These are explicitly agent demonstrations, not independent human judgments.

The server was stopped and restarted on the same audit database. All 65 fresh original assessments and scores matched their saved copies; eight review decisions and the original/effective demonstration scores survived.

A further real API/provider check replaced the contact criterion with a new literal-marker requirement, leaving eight criteria. The absent marker returned assessed/No; the old criterion ID was absent; the run was uncached and saved v1 remained unchanged. This tests the backend/provider replacement path. The actual UI save/evaluation test above adds a criterion; it is not claimed to be a separate browser-operated replacement test.

## Browser and recording checks

Actual in-app browser inspection covered the list/filter path, transcript/result view, evidence highlighting and checklist editor. The saved nine-criterion version was visible and v1 still had eight criteria. At the narrow initial pane the detail stacked; at a 1400-pixel desktop viewport it used separate transcript/assessment columns without horizontal overflow. Temporary viewport controls were reset and audit tabs closed.

All five supplied recording URLs returned HTTP 200 with HTML player pages, rather than direct audio MIME types. For one actual call, the external organizer player loaded a 312.26-second recording, reported readyState 4 with no media error, and advanced to 4.76 seconds during playback before being paused.

The app's Open recording link therefore satisfies the alternative player-link requirement for that checked call. Its inline HTML audio element receives the HTML wrapper URL, which is not a direct playable media resource. This is a presentation defect to tidy, not proof that recordings are unavailable. Playback of every recording and timestamp-to-audio seek alignment were not verified.

## Cost and preservation

| Audit activity | Estimated inference cost |
| --- | ---: |
| 65 fresh DEV evaluations | $0.2939672 |
| Actual new-criterion/appeal UI test | $0.0041804 |
| Actual replacement-criterion test | $0.0037024 |
| Total new audit estimate | **$0.3018500** |

Each of the 67 evaluation calls had reported usage. These are estimates at the configured identified historical text rates, not an invoice or live account-balance check. No new unknown-usage reservation arose. The full batch had a $0.60 additional guard and retained the original $4 application guard/headroom policy.

The prior known application estimate was $0.68292515 and historical unknown-usage reservation $2.38480875. Adding this audit gives $0.98477515 known estimated usage; with the historical reservation and $0.10 overhead, the conservative accounting is $3.46958390, below $4. The reservation is not an asserted charge.

Important for future runs: the audit costs are in a separate database. The main-database-only budget runner does not automatically see them. Until accounting is consolidated, reduce its budget argument to at most **$3.69** to preserve the original $4 combined ceiling, and retain future audit costs separately.

The main database checksum and counts remained unchanged: 75 conversation revisions, 4 checklist versions, 148 evaluations, 6 appeals, 6 reviews. Source/config seed and saved v1 matched. The existing .env was not changed. Private transcripts, signed endpoints, recordings, database backups and raw audit results remain ignored.

## Reproduction evidence

Audit-only private scripts actually run:

- `.venv/Scripts/python.exe local_data/audit_20261107/fresh_audit.py`
- `.venv/Scripts/python.exe local_data/audit_20261107/verify_audit.py`
- `.venv/Scripts/python.exe local_data/audit_20261107/check_restart_replacement.py`

The private directory also contains fresh/baseline results, differences, accounting and preservation checks. It is intentionally not part of the public source tree.
