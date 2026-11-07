# PDF audit after comparison, exports and saved search

Audit date: 7 November 2026. Audited application: **ad9f1671f41bebcf345801a561224b4ac01211ff**. This task changes documentation only. No model/provider request, organizer fetch, new judgment, main-app launch, recording review or demo work was performed. Added inference: **$0.00**; paid limit remains **0**.

## Verdict and current score

**About 85/100 overall readiness, retained as an informal engineering estimate.** The required prototype workflow is implemented, current arithmetic checks pass, and the optional new features work with actual stored results. This is sufficient as a working prototype, with the validation and submission gaps below still open.

The PDFs do not publish a weighted project-grading rubric. Their 100-point checklist grades individual operators. Therefore 85 is neither an official predicted jury score nor measured model accuracy. New comparison/export/search capabilities improve usability and traceability; they do not justify inventing extra requirement points or claiming the remaining semantic/event gates have passed.

One additional software issue was reproduced: **an already-open saved-run comparison can remain stale after a reviewer updates a selected run**. The persisted effective result and main assessment remain correct; the optional comparison must refresh automatically. This should be fixed before relying on that panel during review.

## PDF authority and requirements

Freshly extracted all **12 pages** of the three supplied PDFs with bundled pypdf. File hashes and every extracted page match the prior source extraction. Freshly rendered guide pages 1/2/4 and all checklist pages; visually inspected checklist pages 1/2 and guide page 4. Reread guide pages 1/2/4 and all checklist text. Guide page 3's endpoint remains private and its import contract is covered by regression tests; no endpoint request was made. Company background remains context, not an authoritative account-policy manual or a separate project marking scheme.

- [Student guide](C:/Users/user/Downloads/CQA_Hackathon_Student_Guide_v3%201.pdf), pages 1-4: product workflow, input contract, control/replacement testing, submission and presentation.
- [Quality checklist](C:/Users/user/Downloads/CQA_Chat_Quality_Checklist%201.pdf), pages 1-3: eight operator criteria, weights, anchors, applicability, evidence and arithmetic.
- [Company context](C:/Users/user/Downloads/Data%202%20%281%29%201.pdf): background only.

| Requirement | Finding and limit |
| --- | --- |
| Import organizer API/JSON; preserve source order, roles and timestamps; RU/KZ/EN | Implemented and regression-tested. Actual DEV: **65** records, **35 RU / 15 KZ / 15 EN**, **60 chats / five calls**. No new access to organizer-held control data is claimed. |
| Edit/add criteria, wording, weights, type, scale and N/A through settings; save configuration | Immutable checklist snapshots, validation/preview and dynamic criteria work. Tests cover changes without evaluator/scorer edits. Historical real custom-criterion execution exists; the organizer's unseen replacement is not validated. |
| Automatic assessment with per-criterion answers, weights, points, explanations, evidence and N/A reasons | Implemented with historical real provider outputs. **130 selected original/effective snapshots** pass current contracts/evidence checks. Valid structure and evidence IDs do not prove every judgment is correct. |
| Proportional numerical scales, N/A redistribution, two-decimal total, sections and separate critical flag | Independent recalculation of the selected 130 snapshots found **zero issues**. Uncertainty still withholds totals; it is not silently converted to N/A. Flags never impose an invented automatic-zero penalty. |
| Open result/transcript, navigate to evidence; provide call playback or source player link | Source revision/message navigation and recording links exist. All five DEV call links are stored. Existing client regressions pass. Playback, link expiry and audio-offset alignment were not rechecked in this audit. |
| Separate criterion appeal and reviewer action, rationale, recalculation, original/decision/final history | Core workflow passes fresh regression checks; **198 saved originals replay exactly** through ordered decisions. Nine appeals/nine decisions preserved. Main result updates correctly; optional open comparison has the freshness issue below. |
| HTML/CSS/JavaScript frontend, suitable boundaries for later Dynamics adaptation | React/TypeScript/Vite build passes. Full Dynamics integration, login and production roles are not prototype requirements. |
| Identify paid model and approximate cost including its calls | Stored model/rate/attempt/usage provenance and cost display exist. Missing usage remains unknown/conservatively reserved. Account balance/invoice and live provider access were not checked. |
| Public repository, README, organizer link handoff and official freeze | README/private source checkpoint exist. Remote main matches the audited application; unauthenticated GitHub metadata returned **404**, so public access is not verified. No visibility change, organizer submission or official freeze was performed. |
| Organizer control processing and on-the-spot replacement criterion | Await actual organizer-held data/criterion and event timing. No guessed control identifier or fabricated success. |
| Maximum five-minute presentation | **Explicitly deferred by the user.** No preparation, rehearsal or presentation in this task. |
| Saved comparison, JSON/CSV, text search and filter presets | Optional improvements, not additional PDF obligations. Fresh copied-data checks passed; limitations and the comparison freshness issue remain explicit. |

## Eight rubric criteria

Initial JSON and saved v1 still match the PDFs: contact **10**, needs **15**, identification **20**, consultation **20**, empathy **15**, dialogue management **15**, closing **5**, critical flag **unscored**. Only needs/identification/consultation/closing allow their exact documented N/A conditions. Consultation anchors remain **20/15/10/5/0**; management **10/7/4/0**. The seed/config bytes are identical.

Contact retains the first-human-response greeting plus self-introduction rule. p4-ru-005 remains unclear after the user's earlier listening check: original Yes/**92.31** preserved, effective contact **needs_review**, total **null**, appeal open. This audit did not invent an introduction or force a No. Needs/consultation corrections for p1-kz-012 remain effective Yes/**20**, yielding **100.00**, with original **84.62** preserved. Identification sequence/general-request rules, empathy, management/content separation, closing evidence guards and critical-flag attribution retain their regression coverage.

All **26 earlier provisional development checks plus three correction checks** still match. These are development evidence, not independent ground truth. No new all-dialogue semantic review or mandatory manual packet exercise was added. Stored accepted provenance stays **56 prompt v10 / eight v11 / one v12**; current prompt **v13 has no live validation**.

## Reproduced comparison freshness issue

Severity: **P2**, optional result-inspection UI. [SavedComparison.tsx](../../../frontend/src/SavedComparison.tsx) keys loading by selected IDs/bases but does not depend on their updated_at/state. [Detail.tsx](../../../frontend/src/Detail.tsx) reloads runs after a saved decision, while keeping this component mounted.

An isolated React diagnostic opened a comparison, then supplied the same run IDs with newer updated_at values. Only the first GET occurred; the earlier comparison remained visible. This is a component-level reproduction of the review-update case, not a new database scoring error. Existing ordinary tests did not cover this transition.

Recommended fix: include the selected runs' revision timestamps/state in the request identity, invalidate visible data on that change, refetch via GET, and retain stale-response rejection. Test both left/right updates, reviewed unresolved totals, and late responses. No inference or schema change is needed. This audit documents the issue and does not modify application code. Until fixed, close/reopen the panel to reload it; if a comparison is already unavailable, its retry also refetches.

## Fresh commands and results

- `.venv/Scripts/python.exe -m pytest -q`: **144 passed**, 20.08 seconds; one existing Starlette/AnyIO deprecation warning. Real OpenAI HTTP is prohibited by the ordinary suite.
- Frontend with CQA_LIVE_SMOKE=0, `npm test`: **27 passed / one paid opt-in skipped**, 5.15 seconds. `npm run build`: **passed**, Vite phase 1.91 seconds. `pip check`: no broken requirements.
- Private audit_saved.py: **65 succeeded, 64 complete / one needs review; 130 validated snapshots; zero arithmetic issues; 198 exact review-history replays; nine appeals/nine decisions; seed rules/weights/anchors match**. Network blocked during these saved-result checks.
- Private verify_features.py on a new copy: **249 self-comparisons, 249 JSON exports, 249 CSV exports**, six multilingual source-text checks and cold reopen passed. Stored results matched detail responses; provider and external HTTP transport forbidden; no copied rows changed.
- Private inspect_adopted_features.py: **65 actual saved-run pairs / 520 criterion pairs**, including **107 answer transitions** and **327 detail-only changes**. These historical versions/reviews are not a controlled accuracy benchmark. Fifteen local search requests had median **181.51 ms**, maximum **293.26 ms**, including in-process HTTP/database/serialization work; one machine/75 records is not a scale guarantee. A broad literal Cyrillic query had 43 rows with more than five matching messages, supporting optional match navigation.
- Private diagnostic: `node node_modules/vitest/vitest.mjs run --config ../local_data/post_features_audit_20261107/vitest.config.ts`: **five checks passed**, including reproduction of the stale comparison behavior. Four copied feature tests are repeated diagnostics, not additional ordinary-suite coverage. Initial npm argument forwarding did not select the private configuration; direct Node invocation did. No source change was made.

## Remaining gaps and priority

1. Fix automatic comparison refresh after review; this is the concrete new software gap and costs no API tokens.
2. Keep the unclear call unresolved until sufficient evidence supports a judgment. Existing audio/user feedback cannot justify a forced answer.
3. Validate against independent multilingual/policy evidence and organizer-held control/replacement inputs when available. A future live v13 assessment requires separate spending authorization; zero-spend software tests cannot establish its judgment accuracy.
4. Complete verified public access, organizer handoff and official freeze under actual event instructions. Current private pushes do not satisfy public submission.
5. Keep the five-minute demo deferred until the user resumes it.

No additional product feature is necessary to satisfy the stated core workflow. Better implementations of the adopted features are proposed separately in the [market follow-up](../../ADOPTED_FEATURE_REVIEW.md); proposals are not implemented fixes or guaranteed grading points.

All main rows, attempts, originals, effective results, checklist versions, appeals and decisions are unchanged. The .env, budget baseline, both original rubric files and 26 archived reference files are preserved, as are all **71 application/configuration/test/launcher source files** captured before the audit. New private backups, PDF extraction/renders, diagnostics and verification stay ignored under local_data/post_features_audit_20261107. No app server or demo session was started.

The copied app's existing Budget constructor creates one initial budget_state row from the reviewed baseline before request testing. Every pre-existing copied row is unchanged; only this expected bootstrap addition is allowed and its coverage/opening/provenance were verified. An initial final-preservation comparison omitted this initialization exception and was corrected. Earlier enhancement documentation attributed the addition to GET /api/budget; code inspection establishes application construction as the cause, and that documentation is corrected. This does not create an inference request, reservation or charge; the main database is untouched.

Final checks passed: all eight main tables, 30 protected files and 71 application source files unchanged; only Markdown changed. Source/history credential/private-path scan found zero matches across 114 candidate files and 234 then-existing historical blobs. All 41 Markdown files/182 local links and git diff --check passed. Private evidence/diagnostics and original PDFs are excluded from Git.
