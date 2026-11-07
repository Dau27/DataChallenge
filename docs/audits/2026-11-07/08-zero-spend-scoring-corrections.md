# Source-grounded scoring corrections without inference

Completed 7 November 2026, following [PDF audit 07](07-updated-pdf-reaudit.md). Scope: its three N/A, consultation and self-introduction findings. **No paid request, new evaluation or organizer fetch was made. Originals are preserved.**

## Saved corrections

| Case / criterion | Preserved original | Effective correction and source |
| --- | --- | --- |
| p1-kz-012 / needs | N/A, with an initial-sufficiency explanation | **Yes**. At m0010/m0012 the human asks for the bond/ticker and rejection message needed to identify the failed order. Knowing the general problem did not supply those necessary case details. |
| p1-kz-012 / consultation | 10, despite its explanation identifying a correct next step | **20**. At m0012 the operator specifies the information needed to identify the order and send it for checking; m0014 restates the customer's next step. The saved 20 anchor permits a correct next step. The customer's deferral does not turn this into a partial answer. |
| p4-ru-005 / contact | Yes, claiming a personal self-introduction at m0017 | **Needs review**, with a named missing basis. The noisy first human turn contains a greeting/company wording but does not establish a personal introduction. Recording review or qualified interpretation is required. Neither an invented name nor a definite No is substituted. |

The Kazakh original total remains **84.62**. Its effective total becomes **87.50** after the needs correction and **100.00** after consultation. The call's original **92.31** remains stored; its effective total is **withheld**, with reason UNRESOLVED_CRITERIA. These are operator scores, not project grades.

All three corrections are labeled **AGENT_SOURCE_REVIEW_NOT_INDEPENDENT** in saved comments/rationales. They are provisional source reviews authorized by the user, not independent human reference labels or new model outputs. Unrelated criteria are unchanged.

## Acceptance gates

| Gate | Work completed | Result |
| --- | --- | --- |
| 1 — Corrective behavior | Reviewer replacement can retract an unsupported answer into the existing needs_review state with a genuine missing-basis reason. Recalculation withholds the total and keeps the appeal open. Confirm cannot approve unresolved uncertainty; a supported replacement can later resolve it. The form exposes this existing disposition and explains its effect. | Synthetic HTTP/restart and client regressions pass |
| 2 — Rubric guidance | Prompt v13 distinguishes necessary case details from a clear topic; actionable deferred follow-up from a material omission; company greetings from personal introductions; and noisy ASR from a clear omission. Changed saved definitions still override initial-rubric guidance. | Guidance updated; **not live-model validated** |
| 3 — Safe application | Made a private SQLite backup and per-row/per-column preservation manifest. Applied the three corrections through appeal/review services to a copy, verified local API/restart and zero-budget blocking twice, then applied the same corrections to the main database. | Passed; no external requests |
| 4 — Saved-data audit | Validated 130 selected DEV original/effective snapshots; independently recomputed global/section totals and flags. Replayed original plus ordered review history for all 198 saved assessments with originals. | Zero mismatches |

The public judgment contract, scoring formula, source rubric and configured anchors are unchanged. This corrects existing scoring/review behavior without adding another product feature or model service. Prompt identity changes invalidate incompatible future inference cache reuse; saved results remain readable and paid requests remain paused.

## Tests and commands actually run

- `.venv/Scripts/python.exe -m pytest backend/tests/test_scoring_corrections.py -q`: **2 passed** after correcting the synthetic channel value to the existing voice call contract. Covers sequential N/A/scale corrections, preservation, zero-key/zero-budget review, missing-reason rejection, unresolved confirmation rejection, pending appeal, later resolution and restart. Provider.request is blocked during corrections.
- Frontend with CQA_LIVE_SMOKE=0: `npm test -- --run src/workflows.test.tsx`: **6 passed**. New form regression verifies a null value, explicit missing basis, unchanged original and a single review-only request.
- `.venv/Scripts/python.exe -m pytest -q`: **127 passed**, 22.71 seconds; one existing Starlette/AnyIO deprecation warning.
- Frontend with CQA_LIVE_SMOKE=0: `npm test`: **15 passed / one paid opt-in skipped**, 5.49 seconds. `npm run build`: passed, Vite phase 2.29 seconds.
- `.venv/Scripts/python.exe -m pip check`: no broken requirements. `compileall -q backend scripts` and `git diff --check`: passed. No dependency changes or paid smoke test.
- Private apply_corrections and verify modules: copied-data corrections, API/restart and budget checks passed before main corrections; main read-only verification passed afterward. Windows asyncio's internal loopback socket was allowed while external connections were blocked. An initially mistyped local check URL was corrected before accepting the gate; no provider call resulted.

The ordinary backend fixture forbids real OpenAI HTTP. Copied-data checks confirmed both explicit provider checking and fresh evaluation return HTTP 409 at the zero limit. Main corrections invoke local review services only, with socket connections forbidden.

## Preservation and current state

- **65 DEV execution states succeeded: 64 complete / one needs review**, zero failed/interrupted/unstarted. Completeness is separate from execution success.
- **249 evaluations remain**, with no new inference records. Nine appeals/nine decisions include the three new corrections. The call's appeal stays open and appears in pending-review filtering.
- Every pre-existing row is unchanged except authorized effective/effective_score/updated_at fields in the two targets and the call's completeness. Originals, original scores, attempt histories, metadata, old decisions, transcripts and checklist versions match the before manifest.
- The real .env, private budget baseline and initial rubric bytes/saved v1 are unchanged. Additive budget tables were created; main accounting initializes on app startup as tested on the copy.
- **26/26 earlier provisional development checks still match**, plus the three corrective checks above. They are not a blind benchmark or independent accuracy measurement.
- Stored provenance remains **56 v10 / eight v11 / one v12**. No result was relabeled v13; **zero live v13 evaluations were run**.
- Added model requests: **0**. Added inference estimate: **$0.00**. Configured limit: **0**. Prior combined conservative accounting remains **$4.13490090**, not an invoice or checked account balance.

Private backups, correction logs, original case snapshots and verification manifests remain ignored in local_data/scoring_review_20261107. They are not published. Reports 01–07 retain historical findings; this report supersedes their current-completeness claims.

## Remaining limitation and next step

Review the p4-ru-005 opening recording with a qualified reviewer, then replace the pending contact judgment through its same open appeal. Its total must remain withheld until that basis exists. Independent labels, hidden control/replacement-criterion validation, a timed five-minute human demonstration and public/event handoff remain outstanding. The earlier informal readiness estimate of about 85/100 is not upgraded to an official grade or accuracy claim. Future prompt behavior remains unverified without new inference, which was intentionally not purchased.

Final source/history credential/private-path scan and Markdown link checks passed: 95 safe candidate files, 31 Markdown documents and 110 local links. Main preservation was rechecked after corrections. Source and reports are checkpointed privately; original data/backups remain ignored. No public visibility or submission change is made.
