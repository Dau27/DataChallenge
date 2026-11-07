# Provisional packet review and organizer requirements

Archived development record: the user subsequently removed this exercise from delivery and demo plans. Private evidence is retained unchanged. No further packet labeling is assigned, and demo work is explicitly deferred. See the [scope amendment](12-delivery-scope-cleanup.md).

Completed 7 November 2026, Asia/Bishkek. The user delegated the judgments to the agent and asked whether a manual packet is required by the organizers. **This is optional development QA, not an organizer-mandated human-labeling deliverable. No API spending or application regrading occurred.**

## What the organizers actually require

Rechecked the unchanged student guide pages 1/2/4 and checklist page 3 against their recorded PDF hashes. The guide requires a working configurable evaluation system, evidence-linked results, an appeal and separate reviewer decision, control processing, a criterion replacement through the interface, a five-minute presentation, README/open repository/submission and a frozen commit.

**It does not require the team to manually label 15 dialogues or submit 120 reference labels.** The jury judges the frozen solution; organizers provide control transcripts and the replacement-criterion check. We must process and demonstrate those inputs through our system. Demonstrating the reviewer role is different from preparing a manually graded benchmark beforehand. The guide does not promise a labeled ground-truth dataset.

The 15-case sample comes from [MASTER_CONTEXT.md, section 11](../../../MASTER_CONTEXT.md#11-validation-and-evidence-of-completion), our implementation specification's pragmatic development diagnostic. It explicitly permits provisional agent labels when no independent human labels exist, provided they are not called ground truth or accuracy. That internal check is now documented without making a manual human packet a submission blocker.

Source: [Student guide](C:/Users/user/Downloads/CQA_Hackathon_Student_Guide_v3%201.pdf) and [operator checklist](C:/Users/user/Downloads/CQA_Chat_Quality_Checklist%201.pdf). Background material supplies no additional manual-labeling requirement.

## Actual outcome

| Measure | Result |
| --- | --- |
| Source dialogues reviewed | **15: five RU, five KZ, five EN; two RU calls included** |
| Provisional agent criterion decisions | **120 / 120** |
| Independent human criterion labels | **0** |
| Agent review totals | 12 numerical / three withheld for missing material policy or market-access evidence |
| Disposition/value pairs matching current saved effective judgments | 105 |
| Provisional disagreements | **15 across 10 dialogues** |
| Application scores/results changed | **0** |
| Paid/provider calls and API cost added | **0 / $0.00** |

The 105 matches and 15 differences are descriptive comparison counts between agent judgments, **not measured accuracy, an official score, or 15 proven model errors**. The first case, p1-en-001, receives agent Contact=Yes from m0010 and Needs=N/A from the context available before the human's substantive answer. Its consultation is separately held for the material login-policy claim.

## Method and preserved evidence

Started with a complete-source first review card and separate blank working packet. When the user asked the agent to decide, recorded that as delegation, not as a human Yes/No label. No human-reviewed flag was set. All 15 transcript hashes/messages and the saved rubric match the original packet and immutable database revisions.

Read all 15 sources and wrote all 120 agent decisions, explanations, existing ordered evidence ranges, N/A reasons or named missing bases **before loading the current saved evaluation answers**. Validated exact criterion coverage, types, anchors, evidence and the current source-evidence guard. Deterministic scoring and independent Decimal calculations were checked.

The first source pass and SHA-256 freeze remain preserved in ignored local_data/guided_review_20261107. That first comparison had 104 identical pairs and 16 differences. A subsequent source-rule self-check corrected one agent closing judgment for p4-ru-002: the investigation-result summary at m0064-m0067 plus farewell at m0071 satisfies the rubric; requiring a separate final recap sentence would add a rule absent from it. The original agent No, post-comparison timing and rationale are retained in the revision log. Final artifacts therefore have 105 identical pairs and 15 differences. This revision is disclosed rather than presented as a wholly blind final benchmark.

The original human template and separate blank human working copy remain unchanged. Final provisional decisions, calculated results, uncertainty notes, comparison snapshots, delegation responses and revision history are private. No source transcript, private recording link or personal data is added to GitHub. No new hosted inference or audio review was performed.

## Provisional differences worth retaining

| Source | Criteria differing from saved effective judgment | Source-based concern / limitation |
| --- | --- | --- |
| p4-ru-001 | Needs, consultation, dialogue management | Agent counts initial human elicitation of an unformulated request; needs policy authority for service/manager claims; uses the customer's explicit request to explain a vague technical-support term for clarity. Elicitation/clarity boundaries are provisional. |
| p1-ru-002 | Needs | The human asks where tariff names were compared before advising; source supports applicable clarification rather than initial-sufficiency N/A. |
| p4-ru-002 | Contact, consultation | First customer response has an introduction but no explicit greeting; later greeting is internal. Instrument-specific exchange/OTC eligibility lacks a clear identifier/authoritative rule. Callback-greeting interpretation needs qualification. |
| p1-ru-003 | Needs, empathy, closing | Human asks app versus web. Politeness and relevant navigation are assessed separately from the unanswered fee question. Agent treats the final repeated location instruction plus farewell as a recap; that boundary is not independently adjudicated. Consultation remains partial at 10. |
| p1-kz-003 | Needs | Human elicits missing currency/transfer time for the investigation, which conflicts with saved initial-sufficiency N/A. |
| p1-kz-004 | Needs | Request and update-navigation context are sufficient; no necessary missing fact is identified to justify No. |
| p1-kz-005 | Dialogue management | Vague/wrong initial path makes the client seek clarification before the corrected path works. The agent chooses the 4 anchor; 4-versus-7 interpretation remains provisional. |
| p1-en-001 | Consultation | Closed-account login retention/reuse is a material policy claim not established by the source or customer thanks. This is uncertainty, not proof of an incorrect workaround. |
| p1-en-002 | Needs | Human provides web/app navigation without asking for missing context; answering helpfully does not itself establish clarification. |
| p1-en-005 | Needs | Client volunteers currency; the human supplies general navigation and currency selection rather than eliciting a missing fact. |

Difference counts by criterion: Contact 1, Needs 7, Identification 0, Consultation 3, Empathy 1, Dialogue 2, Closing 1, Critical errors 0. Several are judgment-boundary or missing-authority issues; no automatic regrading is justified by agreement counts alone. Prior development diagnostics are not evidence that all other saved judgments are semantically correct.

## Commands and preservation checks

- Private start_review module: source/seed checks and separate working copy prepared. A missing Windows timezone database was handled by resuming without overwriting labels and using the client timezone's current UTC+06:00 offset.
- agent_review module: 120 provisional decisions across all 15 sources validated and frozen before saved-answer comparison.
- compare_review module: current saved effective/original answers read in SQLite read-only mode; initial comparison and actual delegation responses retained.
- finalize_review module: one explicit source-rule revision, full judgment validation and independent recalculation; no main-data write.
- Preservation assertions: every main row, .env, private budget baseline and original review template unchanged. All human labels remain blank/unreviewed. Application code and dependency locks unchanged; prior application-suite outcomes were not rerun or relabeled as fresh tests.

Main DEV stays **64 complete / one needs review**. The earlier ambiguous p4-ru-005 recording remains unresolved and is outside this packet. No independent qualification/sign-off or official model-accuracy result is claimed.

## Practical priority

Retain this provisional QA only as archived development evidence. It is excluded from active delivery/demo plans; do not assign additional manual labels or treat the packet as a submission gate. Demo work is deferred until the user resumes it. Applicability concerns remain available for a separately requested targeted correction; they do not authorize further work here. Paid requests stay paused.
