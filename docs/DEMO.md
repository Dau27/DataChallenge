# Five-minute demonstration

Status, 7 November 2026: concrete examples and script prepared; current source installs cleanly. Two timed human presentations are still required. The latest local technical walkthrough used saved real assessments and a copied database with inference disabled; it was not a fresh evaluation or a timed human presentation.

## Presenter card

Select **DEV** and **checklist v1**. The full workspace also contains ten labeled synthetic records; do not describe its 75-row total as the DEV count. DEV has **64 complete results / one needs review**, with the uncertain call's total withheld. The 65 source records include 60 organizer-synthetic chats and five real calls. Outputs retain actual model/prompt provenance; none is a live v13 result. See the [current audit](audits/2026-11-07/09-post-correction-pdf-audit.md).

| Time | Show and say |
| --- | --- |
| 0:00–0:45 | Open p1-ru-001. “We evaluate the human operator using a saved, editable checklist. This is an organizer DEV transcript with preserved roles and timestamps. This result was saved from an actual provider call.” Show v1 and the source revision. |
| 0:45–1:45 | Show needs=N/A and its evidence/reason, closing=No, weights, allowed anchors and the total. Click an evidence ID to highlight the source range. “Code calculates the weighted total; applicable weights change with valid N/A. Critical errors remain a separate flag.” |
| 1:45–2:30 | Briefly show an EN/KZ saved assessment and a call such as p4-ru-001. Open recording uses the source player. Explain that transcript evidence is navigable; audio offset mapping is not verified. |
| 2:30–3:30 | Appeal one criterion, then use the separate reviewer action with a rationale and valid evidence. Show the unchanged original, effective result and history after refresh. Reviews recalculate locally without inference. Use the private rehearsal copy for practice. |
| 3:30–4:30 | Edit a substantive criterion, inspect the change preview/field errors, then save a new version and apply it. Example: require an explicit support ticket reference, excluding message/account IDs. For the zero-spend rehearsal, save the version and inspect a previously evaluated custom version, clearly labeled as an earlier run; do not claim the newly saved version was evaluated. Fresh-change demonstration needs a real inference when separately authorized. |
| 4:30–5:00 | “The saved results include model, prompt, attempts, usage and cost estimates. Current checks: 125 backend tests, 14 client tests, 26 targeted scoring diagnostics and 130 score snapshots with no calculation mismatch. The shared spending guard defaults to paused; pending-appeal and critical filters link to evidence. Independent human accuracy and organizer control testing remain unverified.” |

Historical saved runs can show original 100.00 / reviewed 92.31 for p1-ru-001. Those agent demonstration decisions are not independent human labels. Verify the selected run and checklist before quoting a total; newer results preserve their own original score.

## Zero-spend rehearsal

The private workspace has a database copy and a credential-free helper at `local_data/readiness_20261107/serve_rehearsal.py`. From the project root, run `.venv/Scripts/python.exe local_data/readiness_20261107/serve_rehearsal.py`, then open http://127.0.0.1:8000. It uses the built frontend, copied data and an inference-denying provider. It never loads the real .env. Stop any existing process using that port first. The private helper/data are intentionally absent from a public clone.

Practice source navigation, the recording link, appeals/reviews, version editing and saved-result comparison. Provider controls are disabled in this mode. Saving a checklist or reviewer decision is free; fresh assessment is not part of this rehearsal. The copy already contains a labeled technical rehearsal version/decision; the main database is unchanged.

Run two spoken rehearsals with a stopwatch. Record actual durations and any failure below; blank cells mean not performed. Target at most five minutes for the full required flow. A saved-result rehearsal cannot certify fresh model latency or an unseen criterion.

| Human rehearsal | Date / presenter | Actual duration | Full flow completed? / issue |
| --- | --- | --- | --- |
| 1 | Pending | Not measured | Pending |
| 2 | Pending | Not measured | Pending |

At the official event, use the organizer-supplied control identifier and timing. Follow [control/freeze steps](CONTROL_AND_FREEZE.md). Keep transcripts, signed links and credentials private.
