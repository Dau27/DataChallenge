# Post-integration PDF audit — 8 November 2026

## Verdict

**About 85/100 informal readiness, unchanged.** The required persistent prototype workflow is implemented and supported by fresh checks. It is not fully proven ready for organizer acceptance: independent judgment accuracy, organizer-held control/replacement inputs and public/event delivery remain open. Cohort comparison, printing and recovery improve inspection and reliability; they do not earn defined extra jury points or establish scoring accuracy.

The supplied PDFs define a 100-point **operator checklist**, not a weighted project-grading scheme. This estimate is engineering judgment, not an official jury score, an accuracy percentage or an average operator score. No new model evaluation, provider-access check, organizer fetch, paid API request or demo work was performed. **Added inference spend: $0.00. Demo deferred.**

Audited baseline: combined local checkpoint **c0f0763**, including recovery and latest cohort **28818fa** / print **be951f3** handoffs. Both other chats were checked idle, their assigned worktrees clean and their accepted commits retained. Shared main working source matched that checkpoint before this audit; root main's older commit/index and concurrent work were preserved. The small reproduced defect below was fixed in the coordinator and mirrored after acceptance. No remote push, publication or visibility change.

## Source authority

Reread and freshly extracted all 12 original PDF pages with bundled pypdf; all file hashes and extracted page texts match prior evidence. Rendered guide pages 1/2/4 and checklist pages 1/2/3; visually inspected the checklist arithmetic page and guide delivery page. The signed endpoint on guide page 3 stayed private and was not requested. An initial console-encoding problem was corrected with UTF-8; the private page texts were intact.

- **G1–G4:** CQA_Hackathon_Student_Guide_v3 1.pdf, pages 1–4: workflow, editable/replacement checklist, RU/KZ/EN, evidence, recording access, appeals/review, control data, public repository/freeze, cost and presentation.
- **C1–C3:** CQA_Chat_Quality_Checklist 1.pdf, pages 1–3: eight criteria, weights/anchors, N/A, rounding, evidence and exclusions.
- Data 2 (1) 1.pdf: company background, not authoritative brokerage-policy guidance or a project grade sheet.

Document content supplies acceptance criteria. It does not authorize publishing private data, sending organizer messages, changing account visibility, spending on inference or starting the deferred demo. Peer repository documentation does not amend the supplied rubric or define a missing organizer submission schema.

## Requirements matrix

| Requirement | Current evidence / limit |
| --- | --- |
| Organizer GET or supplied JSON; input roles/timestamps; RU/KZ/EN [G1/G3] | Validated immutable imports. Existing DEV: 65 conversations, 35 RU / 15 KZ / 15 EN, 60 chats / five calls. No new external fetch. |
| Edit/add wording, weights, answer types, anchors and N/A through UI [G2] | Saved immutable versions, field errors and preview implemented. Arbitrary configuration has offline coverage; actual organizer criterion replacement remains unperformed. |
| Evaluate selected source with saved checklist [G1/G2] | Real stored assessments plus provider/jobs/cache/retry/budget integration. New paid requests paused. Current v13 configuration has no new hosted validation. |
| Per-criterion answer/points/weight/reason and linked evidence [G2/C3] | Implemented; structural/evidence and independent arithmetic checks passed for 130 selected snapshots. A correct citation range does not prove the judgment true. |
| Missing-action interval and justified N/A [G2/C1/C3] | Explicit absence/context evidence and applicability reasons supported. Remaining semantic boundaries are disclosed below. |
| Weighted anchors, N/A redistribution, two-decimal total, no applicable weight [C2] | Deterministic Decimal scorer and independent total/section replay agree. Unresolved/empty totals stay unavailable. |
| Critical flag separate; excluded three-minute/tag/attachment rules [C1/C2] | Preserved. No automatic-zero penalty, extra voice rule or excluded timing threshold introduced. |
| Transcript and call-player access [G2/G4] | Message evidence links and all five existing recording links retained. Embedded seeking is optional; a player link meets the supplied requirement. No new listening judgment. |
| Criterion appeal, separate review with reason, recalculation, originals/final [G2] | Implemented. All 198 histories replay; nine appeals/nine decisions, one open. Source snapshots remain immutable. |
| Section results when configured [G2] | Independently reconcile under the same applicability/rounding rules. |
| HTML/CSS/JS; structure for later Dynamics adaptation [G1] | React/TypeScript production build passes; API boundary exists. Actual CRM deployment/host bridge is not proven or required now. |
| Paid-model name and approximate whole-assessment cost [G4] | Recorded model/prompt/attempt/token/rate provenance and cost estimates retained. Unknown usage is not presented as a zero invoice; no fresh pricing/balance claim. |
| Organizer control and criterion-replacement challenge [G1/G4] | Await organizer-held inputs. Existing DEV results and synthetic tests are not substitutes. |
| Public repository, clear README, final commit/freeze/handoff [G4] | Setup/README and local checkpoint exist. Anonymous repository access again returned 404: public availability unverified. Current local work is ahead of root/remote main; no public/event handoff or official freeze claimed. |
| Five-minute demonstration [G4] | Deferred by explicit user instruction. Not rehearsed or prepared. |

## Saved rubric/results and semantic limits

Initial checklist copies match each other, saved v1 and PDF weights: Contact10, Needs15, Identification20, Consultation20, Empathy15, Dialogue management15, Closing5; Critical errors unscored. Consultation anchors20/15/10/5/0 and management10/7/4/0 are unchanged. N/A remains limited to the four allowed criteria and their explicit conditions. Bot/system events remain context for human-operator evaluation.

Fresh raw read-only checks confirmed **65 selected DEV runs: 64 complete / one needs review**; all **130 original/effective snapshots** pass source/structure checks, scorer replay and independent total/section arithmetic, with zero arithmetic mismatches. All **198 original-plus-review histories** reconstruct exactly. The earlier 26 provisional development checks and three source corrections still match; these are not independent labels.

Reviewed p1-kz-012 remains84.62 original /100.00 effective. p4-ru-005 preserves original Contact Yes/92.31, effective Contact needs_review / unavailable total and its open appeal. Prior user listening found the introduction unclear. This audit does not replace that uncertainty with a guessed answer. Selected stored prompts remain56 v10 /eight v11 /one v12, recorded as gpt-4.1-mini; current v13 behavior is not a newly measured live result.

The zero-network boundary harness reproduced all31 expected outcomes: five unsupported probes rejected, **14 unsupported/unverifiable probes still accepted**, 12 controls. An injected synthetic response can still persist a complete high-score result with unsupported substantive reasoning. This is a validator boundary, not a fresh model output or measured DEV error rate. Independent references and approved product-policy material are needed to assess substantive correctness; adding broad text heuristics or treating existing reviews/model labels as independent truth would overstate confidence.

## Reproduced defect and correction

**P2 saved-comparison robustness:** the cohort owner had hardened oversized generation numbers in its own provenance reader, but the shared exact-run comparison reader still called math.isfinite on an arbitrarily large historical integer. A synthetic saved max_output_tokens of10**400 raised OverflowError and prevented review comparison. This was reproduced through the mounted route before fixing it: one failure /four controls passed.

The shared reader now omits unrepresentable optional generation metadata without changing the stored record, source, rubric, arithmetic or original/effective result. Five new regressions cover the overflowing integer, malformed number/bool/list/reasoning values and valid recorded values. All five pass, with all saved synthetic rows unchanged; the related comparison/cohort suite passes78 tests. This is a display-reader correction, not a scoring revision or a new feature.

## Commands and results actually run

| Check | Outcome |
| --- | --- |
| Bundled `extract_pdfs.py` | 12 unchanged pages extracted; relevant pages rendered/inspected |
| Private `audit_saved.py` | 130 selected snapshots /198 histories /initial rubric passed |
| Guarded coordinator `local_data/offline_pytest.py -q` before fix | 403 passed, 79.22s |
| New regression before fix | One failed /four passed; oversized metadata crash reproduced |
| Targeted comparison/cohort tests after fix | 78 passed, 14.23s |
| Guarded full backend after fix | **408 passed**, 76.62s; existing Starlette/AnyIO deprecation warning only |
| `CQA_LIVE_SMOKE=0; npm test` | **182 passed /one paid opt-in skipped**, 40.78s; client source unchanged by this audit |
| `npm run build` | TypeScript/production build passed, Vite2.21s |
| Root `.venv/Scripts/python.exe -m pip check` | No broken requirements |
| Private `verify_features.py` | 249 comparisons;249 exports in each JSON/CSV/simple CSV format;three 100-run batch formats;788 weight scenarios;152 criterion distributions;375 priority checks;80 history pages;900 indexed-search checks; cold reopen passed |
| Private `verify_cohorts.py` through mounted app | 20 actual cohort scenarios /376 exact pairs /249 JSON exports +three excerpt packets passed on a new data copy |
| `scripts/audit_validation_gaps.py --saved-db ... --output ...` | 31 documented boundary outcomes reproduced, no outbound request or saved-row change |

Private evidence and execution-start backup: ignored local_data/post_integration_audit_20261108. Each app was initialized only on a separate copy with empty credentials and budget zero. Copies receive the expected one-row budget bootstrap; the main DB remains uninitialized by this task with budget_state empty. Full-table/schema, protected-file and source/index preservation checks accompany the stage checkpoint. No browser work was retried; the earlier exact-ID/narrow/native-print-preview acceptance remains historical, and A4/Letter plus long multilingual paper pagination remain unverified optional print acceptance.

## Public-repository feature review and autonomous continuation

The [52-repository research](../../PUBLIC_HACKATHON_REPOS_2026-11-08.md) was reread against the integrated app. Cohort comparison, printable reports and recovery are already implemented; rebuilding them adds no value. Public primary-source pages for [explicit unlabeled metrics](https://github.com/Nurzhic/CQA-Hackathon/blob/main/backend/app/benchmark_metrics.py) and [explicit-reference calibration](https://github.com/erassylls/doomsday/blob/main/lib/calibration.ts) were rechecked. Their source demonstrates patterns, not verified superiority or official reference truth. Raw-file browser fetches were unavailable; the visible source pages and previously hash-verified inert snapshots supplied the evidence. No peer code/tests/data/model was executed or imported.

The strongest remaining fit is a bounded offline quality report over **explicitly selected saved originals and separately supplied references**. It must stay unlabeled when references are absent, show coverage/abstentions/missing predictions, retain exact source/checklist/provenance identity and never promote appeal-adjusted scores, agent labels or peer labels into independent truth. This can improve evaluation discipline without changing any score or spending on inference. It is optional tooling, not a reinstated mandatory manual-review packet.

Following the user's instruction to continue after this audit, the next accepted stage is that CLI/service/report work, followed by regression/preservation checks and updated documentation. Recording seeking needs reliable offset mapping; knowledge grounding needs approved material; an organizer-specific submission adapter needs the exact authoritative format. Those prerequisites are not fabricated. Model juries/routing, live support, leaderboard identity guesses and extra voice grading remain outside scope. [Continuation stages and boundaries](../../plans/2026-11-08-offline-continuation.md).

The remaining gaps in the verdict stay open until there is actual evidence. Demo preparation remains deferred even during autonomous continuation.

## Completed continuation after this audit

The optional [offline quality report](../../improvements/23-offline-quality-report.md) is now implemented and tested. Final combined backend passed **460 tests**; 52 new feature cases and real saved-data/CLI acceptance passed. Client source remains identical to the182-test/build snapshot above. Actual 65 DEV originals / 520 judgments are correctly **unlabeled**, with zero independent reference labels and no accuracy number. All 249 individual saved-run checks passed, including explicit historical unavailable states. Exact reference identity, original basis, missing/abstained denominators, provenance hashes/settings/response IDs and normalized scale units are enforced. No stored result, rubric or evaluator was changed by this feature. It improves evaluation discipline while leaving the informal **about 85/100** verdict and external/semantic gaps unchanged. No inference spending, demo work or publication.
