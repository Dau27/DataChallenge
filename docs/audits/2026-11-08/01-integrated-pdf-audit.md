# Integrated PDF audit — 8 November 2026

## Verdict

**About 85/100 readiness, retained as an informal engineering estimate.** The required prototype workflow is implemented and passes fresh software/saved-data checks. It is sufficient as a working prototype; independent judgment correctness and the organizer/event acceptance gates remain open.

The PDFs provide a 100-point **operator** checklist, not weighted project-grading criteria. This estimate is not an official jury prediction, model-accuracy percentage or average operator result. Additional analytics, search and history features improve usability without establishing extra official points or closing the semantic-validation gap.

Audit scope: current combined local source on main, whose published HEAD is still **5b726f9**. The UI, semantic guards, backend limits, insights, pagination and indexed-search changes remain working changes. The other two chats were idle and reported completed work when inspected. This audit independently checked the current source and fixed the issues below; it did not merge, publish, change repository visibility or perform an official freeze.

**Final results: 309 backend / 118 client passed; one paid opt-in skipped; production build and pip check passed. Zero model/provider requests / $0.00 added inference. All saved originals, the full main index/schema and protected files are preserved. Demo remains deferred.**

## PDF authority

Freshly extracted all **12 pages** of the three original Downloads PDFs using bundled pypdf. Their file hashes and every page text match prior extractions. Rendered guide pages 1/2/4 and all checklist pages; visually inspected checklist pages 1/2 and guide page 4. Reread complete relevant guide/checklist text. The signed organizer endpoint on guide page 3 remained in ignored private extraction and was not printed or requested.

- `CQA_Hackathon_Student_Guide_v3 1.pdf`, pp. 1–4: required workflow, input format, control/replacement challenge, public repository/freeze and presentation.
- `CQA_Chat_Quality_Checklist 1.pdf`, pp. 1–3: initial operator criteria, anchors, N/A, weighting, rounding and evidence rules.
- `Data 2 (1) 1.pdf`, five pages: company background; not an authoritative brokerage/account policy manual or project grading scheme.

PDF instructions were treated as acceptance criteria for this audit, not permission to publish private source/data, contact organizers, enable paid inference or resume the deferred demo.

## Reproduced mistakes and fixes

### Extreme weights passed validation but could not be scored

**P2 configuration edge, repaired.** A finite draft weight of `1e1000000` was marked valid by the checklist preview but raised Decimal `Overflow` in the scorer. The audit reproduced this using a synthetic assessment only. No saved version/result was changed to demonstrate it.

Added a field validator in [domain.py](../../../backend/app/domain.py): zero remains valid; positive weights must be in **1e-100 through 1e100**. This is a documented engineering arithmetic bound, not a PDF weight rule. Unsupported magnitudes now produce an error at `criteria / index / weight`, and cannot be saved. The supported range leaves normal integer/fractional/relative weights unchanged. Initial rubric files, scale anchors, arithmetic formula, rounding and scoring version remain unchanged.

[Ten regressions](../../../backend/tests/test_weight_boundaries.py) pass: overflow/underflow magnitudes and both range boundaries; preview/save rejection with no version/provider mutation; normal and extreme supported weights; zero weights; all-zero totals remaining unavailable. The post-fix private diagnostic confirms unsupported inputs are rejected while an ordinary small fractional weight still scores correctly.

### Ordinary client test execution needed bounded concurrency

The first full client run timed out in a five-second saved-filter integration test: **117 passed / one timed out / one paid test skipped**. Its focused rerun passed all eight tests. The complete suite then passed with two workers, without changing assertions or test timeouts.

Set the ordinary `npm test` script to **`vitest run --maxWorkers=2`** in [package.json](../../../frontend/package.json). This supplies a documented resource default for the shared Windows environment. The final ordinary command passed **118 tests / one skipped**. No application filtering behavior, live-test opt-in or dependency version was changed for this timing issue.

Only these three non-Markdown paths were changed by the audit: `backend/app/domain.py`, the new `backend/tests/test_weight_boundaries.py`, and `frontend/package.json`. Every other captured source file matches its audit-start hash.

## Requirements matrix

| PDF requirement | Current evidence and remaining limit |
| --- | --- |
| Organizer GET/JSON import; roles/order/timestamps; RU/KZ/EN | Implemented, validated and tested. Actual organizer DEV retains 65 records: 35 RU / 15 KZ / 15 EN, 60 supplied synthetic chats / five real calls. No organizer fetch was made by this audit. |
| Add/change criteria, wording, weights, answer types, scale and N/A settings through the interface | Immutable editor/save, field errors and preview are implemented. Custom configurations have synthetic regression coverage. The actual organizer replacement challenge remains unperformed. |
| Evaluate a selected conversation against a saved configuration | Real saved DEV assessments and provider/job integration exist; execution/retry/cache/budget safeguards are tested. New model calls remain paused. Current prompt/validation behavior is not newly validated by hosted inference. |
| Per-criterion answer, weight, points, explanation and linked evidence | Implemented. 130 selected original/effective snapshots validate and match deterministic and independent arithmetic. Evidence presence/range checks do not prove semantic truth. |
| Missing-action evidence and N/A justification | Supported through explicit evidence ranges, applicability/missing-basis reasons and validation. Remaining adversarial semantic cases are described below. |
| Scale × weight, N/A redistribution, two-place total rounding | Initial anchors and weights match the PDF. Independent selected-score/section checks find zero mismatches. Empty applicable weight and unresolved totals remain explicitly unavailable. |
| Critical violations marked separately | Unscored flags remain separate; no automatic-zero penalty is invented. Priority/breakdown tools distinguish true, false and unknown. |
| Transcript and call recording/player access | Exact-message links and all five supplied recording links are preserved. No audio playback or new self-introduction judgment was performed. |
| Criterion appeal, reviewer rationale/decision, recalculation and original/final preservation | Implemented; regression tests cover persistence, concurrency and replay. All 198 stored original-plus-review histories replay exactly. Nine appeals/nine decisions remain, with one open appeal. |
| Sections when configured | Per-section results retain the same applicability/rounding rules; selected snapshots independently reconcile. |
| HTML/CSS/JavaScript and future Dynamics adaptation | React/TypeScript builds to the required browser stack with separate API boundaries. Full Dynamics integration and production authentication are not PDF requirements. |
| Paid-model identity and approximate assessment cost | Saved model/prompt identity, attempts, token usage and rate-based estimates are exposed. Unknown usage is not represented as a zero bill. No billing/balance query or fresh price claim was made. |
| Unseen control transcripts and organizer-proposed replacement | Still awaiting organizer-held inputs/acceptance. An offline fixture or existing DEV result cannot establish this gate. |
| Public Git repository, README, final commit/freeze and organizer handoff | README/setup exist. Anonymous [repository access](https://github.com/Dau27/DataChallenge) returned 404; public availability remains unverified. Remote main still resolves to 5b726f9, before the current local updates. No public/event handoff or official freeze is claimed. |
| Five-minute demonstration | Explicitly deferred by the user. No preparation, rehearsal or presentation was performed by this task. |

## Operator rubric and saved correctness

The initial configuration still has the eight PDF criteria: Contact **10**, Needs **15**, Identification **20**, Consultation **20**, Empathy **15**, Dialogue management **15**, Closing **5**, and unscored Critical errors. Consultation anchors remain **20/15/10/5/0**; management anchors **10/7/4/0**. N/A remains permitted only for Needs, Identification, Consultation and Closing under their saved conditions.

Contact requires the first human response to greet in the customer's language and introduce the operator. Bot/system messages remain context. Identification is about confirmed identity before protected action, not a blanket requirement for general questions. Consultation and dialogue clarity remain separate. Closing requires recap/further-help plus farewell. The excluded three-minute threshold, tags and attachments were not introduced.

Fresh read-only checks:

- **65 succeeded selected DEV assessments: 64 complete / one needs review.**
- **130 original/effective snapshots** pass structural/source-evidence validation, exact scorer replay and an independently implemented total/section calculation. Zero arithmetic mismatches.
- **198 histories** reconstructed from immutable originals plus ordered reviewer decisions equal stored effective judgments.
- The earlier **26 provisional development checks plus three source-correction checks** still match. These are development checks, not independent labels or measured accuracy.
- p1-kz-012 retains original **84.62**, reviewed **100.00**, effective Needs Yes and Consultation 20.
- p4-ru-005 retains original Contact Yes/**92.31**, effective Contact **needs_review**, total **null**, with its appeal open. Prior user listening found the introduction unclear; this audit did not force a Yes or No.
- Selected stored provenance remains **56 prompt v10 / eight v11 / one v12**, all recorded as **gpt-4.1-mini**. Current v13/source-validation behavior has no new live evaluation in this audit.

## What the semantic checks establish

The offline boundary harness again matched all **31 expected outcomes**: five unsupported cases rejected, **14 unsupported/unverifiable cases still accepted**, and 12 controls. Its injected response can still drive a complete synthetic job to a high score despite an incorrect/unsupported substantive judgment. This is a validator-boundary demonstration, not a new hosted-model output or a measured DEV error rate.

Remaining cases include fabricated source events, answer/explanation contradictions, unsupported policy truth and arbitrary changed natural-language rules. Citation adequacy is not proof of factual correctness. Reviewer decisions remain an explicit human authority boundary; model-only heuristics were not silently imposed on historical reviewer judgments. Approved policy/account material or independent adjudication is needed for stronger correctness claims.

The removed 15-dialog manual reference exercise was not reinstated. Organizer control testing remains an organizer-input-dependent acceptance step, not permission to fabricate labels or request additional paid calls.

## Fresh execution and other-chat verification

| Command/check actually run | Result |
| --- | --- |
| Bundled Python `extract_pdfs.py` plus targeted UTF-8 reads and rendered-page inspection | 12 page texts and all three PDF hashes unchanged; initial console encoding was corrected for readable inspection |
| Initial guarded ordinary backend suite | **299 passed**, 85.64 s; zero attempted external connections |
| Weight-boundary regression suite | **10 passed**, 2.10 s; synthetic temporary databases, no model calls |
| Final guarded ordinary backend suite | **309 passed**, 63.52 s; existing Starlette/AnyIO deprecation warning only; zero attempted external connections |
| Final frontend `CQA_LIVE_SMOKE=0; npm test` | **118 passed / one paid opt-in skipped**, 29.17 s; assertions/timeouts unchanged |
| `npm run build` | TypeScript and production bundle passed; Vite 1.90 s |
| `.venv/Scripts/python.exe -m pip check` | No broken requirements |
| Private `audit_saved.py` | 130 selected snapshots / 198 history replays / all initial rubric checks passed |
| `scripts/audit_validation_gaps.py --saved-db ... --output ...` | 31 expected diagnostic outcomes; zero outbound requests; saved/protected preservation passed |
| Private `verify_features.py`, fresh actual-data copy | **249 comparisons and 249 exports in each of three formats**, 100 selected runs in all three formats, **80 history pages / 900 indexed-search page parity checks**, **152 criterion distributions / 375 priority-source checks**, **394 identity + 394 changed-weight scenarios**, cold reopen passed |
| Private `finalize.py` | Main **15 tables plus schema/index**, all 249 evaluations and 30 protected files unchanged; only the declared audit code paths differ |

The earlier other-chat report's **88 history pages / 912 search checks** included one additional, explicitly synthetic 55-run source on its disposable copy. This audit used the 75 actual stored sources only; the different counts are expected. Current history/index regressions also cover longer synthetic histories and boundary cases. The other chat's completed comparison ordering, preset initialization, deep links, page retention, exact-message search and queue restoration changes were preserved and included in the fresh suites.

No browser was launched for this audit. Prior browser results in [history/design verification](../../improvements/18-history-design-integration.md) and [review integration](../../improvements/16-review-experience-integration.md) were reviewed as prior evidence, not represented as freshly rerun browser tests.

Two historical critical-flag judgment bases remain explicitly unavailable for weight simulation under current generic validation because they contain placeholder missing-basis reasons. Their originals are preserved. This is an optional saved-scenario limitation, not a changed current DEV score.

## Preservation and remaining work

The audit began with a private SQLite backup and source/protected-file hashes. Main preservation includes all **15 current tables**, covering the eight original business tables and derived search structures, plus the schema/history indexes. Every main row and all 30 protected files match the audit baseline: .env, budget baseline, both rubric files and 26 archived private references.

Copied feature requests changed no rows after app initialization. The copy gained only the existing Budget constructor's expected baseline accounting row; no evaluation, appeal, review, reservation or source was added. No main app server, index rebuild, organizer fetch, recording playback, provider access check or model call was started. Private evidence remains ignored under `local_data/pdf_audit_20261108`. Application changes stay local; no unrelated work was staged or overwritten.

Final source/history scan passed for **190 candidate files / 387 then-reachable historical blobs**, with zero credential/private-path matches. All **59 Markdown documents / 283 local links** and `git diff --check` passed. Final preservation also verifies that the copied accounting bootstrap amount, coverage and provenance exactly match the reviewed baseline. No dependency version, original checklist or saved judgment changed.

Remaining priorities:

1. Independent multilingual/substantive correctness and approved policy evidence, including future validation of the exact current configuration when inputs/spending are authorized.
2. Organizer-held unseen control transcripts and the actual replacement-criterion acceptance test.
3. Keep the unclear call unresolved until adequate source evidence exists; do not turn uncertainty into a fabricated result.
4. Review and commit the combined tested source, verify public repository access, organizer handoff and the actual official freeze process under the event instructions.
5. Keep the demo deferred until the user explicitly resumes it.

No additional product feature is required to complete the stated core workflow. This audit improves input-validation/test reliability and confirms saved arithmetic and integration; it does not close the external or semantic gates by adding more UI.
