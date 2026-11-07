# Independent human review

Latest source correction: p4-ru-005 contact is needs_review, with its original Yes/92.31 preserved and effective total withheld. Review the noisy m0017 opening recording, then resolve its existing open appeal with evidence. The KZ needs/consultation corrections are explicitly agent-attributed; they do not mark any independent labels complete. [Correction report](audits/2026-11-07/08-zero-spend-scoring-corrections.md).

Status: packet prepared; human adjudication has not occurred. This is the principal remaining validation gap. Automated tests and 26 targeted agent diagnostics do not establish model accuracy.

The private workspace packet is under `local_data/readiness_20261107/human_review/`:

- `START_HERE.md`: source definitions and the 15 selected transcripts, without model verdicts.
- `review_template.json`: 120 blank criterion labels, five conversations per language, including two calls.
- `saved_model_comparison.json`: actual saved model results, to open after the first human pass.

These transcripts informed development. They are not an untouched holdout or a statistical accuracy benchmark. Reading them without model answers reduces anchoring; it does not reverse their prior use in development. Review files contain organizer data and must remain private.

A reviewer qualified for the language and applicable brokerage context should:

1. Read the saved rubric and source messages before opening model results. Judge only human operator actions; bots and system events provide context.
2. For all eight criteria, record assessed / not_applicable / needs_review, an allowed value where assessed, the exact source message range, rationale and any authoritative policy reference. Leave unavailable material policy unresolved rather than inventing a fact. N/A must satisfy its saved condition.
3. Add their identity/date and mark only actually completed labels human_reviewed. Do not alter the source text or the model result to erase a disagreement.
4. Compare with the saved model results. Record disagreements by criterion, including No/N/A, critical flags and whether the cited evidence supports the finding. A second qualified reviewer should resolve ambiguous disagreements where possible.
5. If a correction is accepted, use the existing appeal/reviewer workflow to preserve the original and recalculate. This step needs no model API call. Update the report with counts actually reviewed, agreement counts and unresolved cases, with the small development-sample limitation.

No organizer accuracy threshold was supplied. The completion gate is a signed, source-grounded review with explicit disagreements and limitations, rather than an invented pass percentage. An agent cannot provide the independent human sign-off.
