# Archived optional reference review

Archived from active delivery/demo plans on 7 November 2026 at the user's request. Existing private files and review history are retained unchanged. No packet labeling or sign-off is assigned as a delivery gate. The application appeal/reviewer workflow remains in scope. See the [delivery-scope update](audits/2026-11-07/12-delivery-scope-cleanup.md).

Latest source correction: p4-ru-005 contact is needs_review, with its original Yes/92.31 preserved and effective total withheld. Review the noisy m0017 opening recording, then resolve its existing open appeal with evidence. The KZ needs/consultation corrections are explicitly agent-attributed; they do not mark any independent labels complete. [Correction report](audits/2026-11-07/08-zero-spend-scoring-corrections.md).

[Recording follow-up](audits/2026-11-07/10-call-recording-review.md): the actual dataset audio was retrieved and a short unfiltered opening clip provided. The user reported the introduction is unclear; local recognition did not establish it. The appeal remains open. Obtain clearer audio or qualified interpretation before assigning Yes/No; the agent did not directly hear the recording and no independent packet label was marked complete.

Status: the user delegated the judgments to the agent. [Provisional review completed](audits/2026-11-07/11-guided-human-review.md): **120 agent decisions / zero independent human labels**, with originals preserved. Fifteen disposition/value differences remain provisional; they are not an accuracy score or 15 proven bugs. The original human template is still blank. **The organizer PDFs do not require a manually labeled 15-dialogue packet**; this is an internal diagnostic from MASTER_CONTEXT.md, not a submission blocker.

The private workspace packet is under `local_data/readiness_20261107/human_review/`:

- `START_HERE.md`: source definitions and the 15 selected transcripts, without model verdicts.
- `review_template.json`: 120 blank criterion labels, five conversations per language, including two calls.
- `saved_model_comparison.json`: actual saved model results, to open after the first human pass.

These transcripts informed development. They are not an untouched holdout or a statistical accuracy benchmark. Reading them without model answers reduces anchoring; it does not reverse their prior use in development. Review files contain organizer data and must remain private.

The following retained procedure is reference only, for use if this optional study is explicitly resumed:

1. Read the saved rubric and source messages before opening model results. Judge only human operator actions; bots and system events provide context.
2. For all eight criteria, record assessed / not_applicable / needs_review, an allowed value where assessed, the exact source message range, rationale and any authoritative policy reference. Leave unavailable material policy unresolved rather than inventing a fact. N/A must satisfy its saved condition.
3. Add their identity/date and mark only actually completed labels human_reviewed. Do not alter the source text or the model result to erase a disagreement.
4. Compare with the saved model results. Record disagreements by criterion, including No/N/A, critical flags and whether the cited evidence supports the finding. A second qualified reviewer should resolve ambiguous disagreements where possible.
5. If a correction is accepted, use the existing appeal/reviewer workflow to preserve the original and recalculate. This step needs no model API call. Update the report with counts actually reviewed, agreement counts and unresolved cases, with the small development-sample limitation.

No organizer accuracy threshold was supplied. A future independent study would need actual reviewer attribution, source-grounded decisions and explicit limitations. That is not a submission requirement. An agent cannot provide independent human sign-off.
