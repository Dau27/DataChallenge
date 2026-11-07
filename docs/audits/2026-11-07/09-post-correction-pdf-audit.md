# PDF audit after the zero-spend scoring corrections

Follow-up: [call recording review](10-call-recording-review.md) verified the dataset audio and extracted its opening. The user's listening response and inconclusive local recognition did not establish an introduction, so the existing needs_review/withheld total remains unchanged.

Audit date: 7 November 2026. Audited application commit: **3309844daf54c2a8b45a8aa291f68ecab99af741**. This audit changes documentation only. **No model request, organizer fetch, recording playback, judgment change or paid test was made.**

## Verdict and current score

**Approximately 85/100 overall readiness, as an informal engineering estimate.** The required prototype workflow is implemented and the identified supported scoring errors are corrected. General judgment accuracy and event delivery remain unverified, so the solution is not yet a fully validated submission.

This is not an official grade, calculated project score or accuracy percentage. The PDFs do not supply weighted project-grading criteria: their 100-point checklist scores individual operators. There is no defensible formula that turns passing tests, 64 completed conversations or a corrected operator score of 100 into a project grade. The earlier estimate is retained because the corrections remove known contradictions without resolving the principal validation and delivery gaps.

## Source and evidence recheck

Freshly extracted all **12 pages** of the supplied PDFs using bundled pypdf. All three file hashes and page texts match the previous source extraction. Reread guide pages 1/2/4 and all checklist pages; visually re-inspected the unchanged renders of checklist pages 1/2 and guide page 4. Guide page 3 and its signed endpoint were handled privately; no organizer request was sent. Background remains company context rather than authoritative product policy or additional grading weights.

- [Student guide](C:/Users/user/Downloads/CQA_Hackathon_Student_Guide_v3%201.pdf): required workflow, data and delivery.
- [Quality checklist](C:/Users/user/Downloads/CQA_Chat_Quality_Checklist%201.pdf): operator definitions, anchors, N/A, evidence and arithmetic.
- [Company background](C:/Users/user/Downloads/Data%202%20%281%29%201.pdf): context only.

## Checklist criteria

| Criterion / PDF rule | Current audit finding |
| --- | --- |
| Contact, weight 10: human greets in the customer's language and introduces themselves in the first response | The unsupported p4-ru-005 positive is retracted. Its noisy m0017 cannot establish a personal introduction: contact is needs_review, with a specific missing recording/interpretation basis. No invented name or definite No. |
| Needs, weight 15: clarify necessary missing details; N/A only if initially sufficient | Re-inspected p1-kz-012 m0010/m0012. The operator requests ticker and rejection text to identify the failed order. Effective Yes and removal of N/A match that source-based interpretation. |
| Identification, weight 20: verified before protected action; N/A for general requests | Saved types/N/A permissions and sequence/general-guidance regression coverage pass. This audit does not independently establish external account policies or relabel other judgments. |
| Consultation, weight 20: anchors 20/15/10/5/0; correct next step qualifies for 20 | Re-inspected p1-kz-012 m0012/m0014. Specific requested details plus checking/referral path support the effective 20; customer deferral alone does not justify 10. Original 10 remains preserved. |
| Empathy, weight 15: polite response to the actual inconvenience | Initial definition/type/weight and saved contracts match. No new independent semantic labels were produced. |
| Dialogue management, weight 15: anchors 10/7/4/0; clarity distinct from consultation | Configured anchors and proportional scale contributions match. Existing separation tests pass; a content omission is not automatically a clarity penalty. No three-minute reaction threshold is added. |
| Closing, weight 5: recap or further-help offer, plus goodbye; N/A for premature interruption | Existing courtesy-only evidence guard and repair regressions pass. All selected snapshots pass current source-evidence validation; this narrow guard is not proof of every closing judgment's truth. |
| Critical errors: separate unscored flag for the three specified human violations | Saved flags and arithmetic validate. No automatic zero-total penalty, bot attribution or requirement for customer acceptance was added. |

The initial seed/config bytes and saved checklist v1 still match. All eight IDs, answer types, weights, N/A permissions and both numeric anchor sets were checked against the source. Source-grounded corrections remain explicitly agent-attributed, not independent human labels.

## Required workflow and delivery

| Guide requirement | Status and limits |
| --- | --- |
| Import DEV/API or JSON; preserve roles/timestamps; RU/KZ/EN | Implemented. Saved DEV has 65 records: 35 RU/15 KZ/15 EN, 60 organizer-synthetic chats/five real calls. No new endpoint access was claimed. |
| Editable definitions, weights, types, scales and N/A; new criterion through settings | Implemented with immutable saved versions, validation and preview. Current regression tests pass; earlier real custom-criterion evidence is historical. Organizer's unseen replacement is not tested. |
| Automatic operator assessment with criterion answers, points, explanations, N/A reasons and evidence | Implemented with historical real provider outputs. 130 selected original/effective snapshots validate; evidence-ID validity is not a semantic accuracy guarantee. |
| Scale weighting, N/A redistribution, two decimals and section totals | Independent global/section/flag checks of all 130 snapshots have zero mismatches. Unresolved source review withholds a total instead of silently excluding its weight. |
| Detail navigation and call recording access | Transcript evidence navigation and source-player link exist. Previous player playback evidence is historical; playback/audio-offset mapping was not rechecked here. Speech recognition and intonation scoring are not required. |
| Separate appeal and reviewer action; rationale; original/decision/final result | Implemented and freshly regression-tested. Replayed all 198 saved assessments with originals through their ordered review histories: exact match. The uncertain call's appeal remains open. |
| HTML/CSS/JavaScript frontend adaptable later to Dynamics | React/TypeScript build passes. Actual Dynamics integration and secure login are not prototype requirements. |
| Paid model name and approximate assessment cost including all calls | Stored model/rate/attempt/usage metadata and cost accounting exist. Unknown historical usage retains a conservative reservation. The ledger is not an invoice or current account balance. |
| Open Git repository, clear README and link submission before stop-code | README/setup exist; authenticated remote matched the audited commit. Fresh unauthenticated repository lookup returned 404: public accessibility is not established. Publication/submission remain incomplete. |
| Full demonstration within five minutes | Script/examples exist; human timing records remain blank. A saved-result technical walkthrough does not verify a timed demonstration or new inference latency. |
| Organizer control processing, criterion replacement and official freeze | Awaiting organizer-only control ID/timing/instructions. No control result, submission receipt or official frozen commit is fabricated. |

The shared budget, preview and review filters are useful reliability improvements, not extra points specified by the PDFs. Independent labels and two human rehearsals are our engineering safeguards; the guide itself requires the presentation to fit five minutes.

## Fresh checks actually run

- `.venv/Scripts/python.exe -m pytest -q`: **127 passed**, 22.57 seconds; one existing Starlette/AnyIO warning. Ordinary tests block real OpenAI HTTP.
- Frontend with CQA_LIVE_SMOKE=0: `npm test`: **15 passed / one paid opt-in skipped**, 5.71 seconds. `npm run build`: passed, Vite phase 2.14 seconds.
- `pip check`: no broken requirements. `git diff --check`: passed.
- Private read-only audit: **65 succeeded, 64 complete / one needs review**, zero latest failed/interrupted/unstarted; **130 snapshots**, **zero arithmetic/contract issues**, **198 original-plus-review replays matched**, **26 earlier development checks plus three correction checks matched**.
- Main counts remain **249 evaluations / nine appeals / nine decisions**. All database rows, original results, .env and private budget baseline are unchanged during this audit.
- Stored inference provenance remains **56 v10 / eight v11 / one v12**. The application prompt is v13, with **no live v13 evaluations**. No inference metadata was relabeled.
- Independent review packet still has **zero marked-reviewed labels**. This audit rechecks the corrected cases and software contracts; it does not establish source accuracy for all 520 criterion judgments.

Paid limit remains **0**. Added model requests: **0**; added inference estimate: **$0.00**. Prior conservative combined accounting remains **$4.13490090**. No account balance or live provider access was checked. New private extraction, verification and preservation records are in ignored local_data/post_correction_pdf_audit_20261107; previous audit evidence is retained.

## Remaining gaps, in order

1. Qualified recording/interpretation review of p4-ru-005 m0017, followed by evidence-based resolution of its existing contact appeal. Its final total must remain withheld meanwhile.
2. Independent multilingual/policy-grounded review and unseen control/replacement-criterion validation. Current corrected diagnostics are development evidence. The revised v13 prompt's live behavior remains unverified; another paid run was intentionally excluded.
3. A timed five-minute human demonstration, including criterion change/application. The prepared two-rehearsal engineering gate is still pending.
4. Verified public repository access and organizer link submission, then actual control processing and a recorded official freeze when organizers supply inputs and timing.

No additional product features are required to close these gaps. Current completeness and test counts were reconciled in the demo/control notes; prior reports preserve historical results.
