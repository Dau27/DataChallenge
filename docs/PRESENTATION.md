# Vector Field - five-minute presentation

An editable six-slide deck is attached to the presentation-creation reply in this chat. It includes speaker notes and a native scoring table. You can export it as PowerPoint from the viewer. No video recording was started or required by the supplied guide.

**Target: 4:30, with 30 seconds of buffer.** The 447-word narration below is a script, not a measured spoken rehearsal. Read the narration; use action/source notes as prompts rather than reciting them. Chat waiting time is not presenter delivery time.

Keep the application available: the slides support the required evidence/appeal/checklist demonstration. They do not replace the organizer's live criterion-replacement check or actual control inference. Keep the repository private until the owner's event publication; the rehearsal uses saved results with inference disabled.

The existing private rehearsal copy already contains the demonstrated review and v6. Show their saved history honestly; prepare another fresh copy if a new appeal/save is needed. Never overwrite prior practice or main results. [Guarded setup and presenter card](DEMO.md).

## 1. Conversation Quality Analytics - 0:00-0:30

Action: Show the cover, then open the saved p1-ru-001 / checklist v1 example.

We are Vector Field. Our app evaluates human operator performance in Russian, Kazakh and English. It connects each judgment to the source, calculates the score deterministically and supports appeals with the original result retained. Today we will use real saved DEV results, with fresh inference disabled.

## 2. Judgments linked to source - 0:30-1:20

Action: In the app, show Contact, Needs=N/A and click the source reference to highlight m0010.

This saved example asks where to find a tariff. The source includes customer, bot, system and human turns, but we assess the human operator. Contact is Yes: the first human reply greets the customer and introduces Alina. Every judgment carries an explanation and a source interval. Needs is N/A because the conversation already supplies enough information for an answer. N/A needs a reason; it is not a zero. Click the evidence in the application to highlight message m0010.

## 3. Deterministic scoring - 1:20-1:55

Action: Explain the editable score table: applicable weight 65, points 60, final 92.31.

The language model supplies judgments; code calculates the score. In this saved case, Needs and Identification are not applicable. The remaining weights total 65 and earned points total 60. Multiplying 60 divided by 65 by 100 gives 92.31 after final rounding. Numerical criteria use their raw anchor divided by the maximum anchor, then the configured weight. Critical violations are a separate boolean flag. An unresolved judgment withholds the total rather than inventing a zero.

## 4. Review with the original retained - 1:55-2:50

Action: Show the saved copied-data review: original 100, effective 92.31 and Decision history. Identify it as an existing demonstration review.

A reviewer can challenge one criterion. This older saved run awarded Closing and originally scored 100. The checked ending contains a polite farewell, but no recap or offer of further help. We submitted a comment, then used a separate reviewer action with a rationale and the checked interval m0010–m0012. The effective total becomes 92.31 while the original 100 remains visible. The history records what changed and why. Recalculation is local and needs no model call.

## 5. Checklist changes through the UI - 2:50-3:55

Action: Show saved v6 and its new criterion; then explicitly show historical evaluated v2. Fresh v6 inference stays disabled.

Checklist changes are configuration. We can change a definition, answer type, weight, numeric anchors and N/A condition through the editor. A preview points to field errors before saving. Here we added a concrete rule: the human operator must provide a support ticket reference before closing. Saving created immutable version 6 and preserved old results. Version 6 has not been evaluated during this rehearsal. Separately, historical version 2 already contains a real evaluated ticket-reference criterion; it returned No and cites m0010–m0012. This is historical proof, not a fresh result for today's configuration.

## 6. Saved results and submission - 3:55-4:30

Action: Summarize DEV: 64 ok / one error, historical model cost and remaining actual control/public/freeze gates.

We retain 65 DEV conversations: 64 complete and one unclear call requiring review. The required Results JSON is committed and privately verified; the unclear case is an explicit error, with no fabricated score. The selected DEV set used gpt-4.1-mini and averaged about $0.00613 per evaluation at recorded rates, including recorded retries. Those are historical estimates, not a current quote or account balance. Genuine control acceptance, final public handoff and the official freeze remain pending.

## Scope and evidence

Values and the source excerpt come from saved DEV run 43314e09e15541cd94a9423908b01394. The review screenshot is from a disposable real-app walkthrough; the v6 screenshot is a saved configuration with no evaluation. Historical v2 run ef2606e7198248189a3eebcd0abc49d6 is separate. All originals remain preserved.

DEV Results JSON contains 65 original IDs: 64 ok and one explicit error for p4-ru-005. Historical mean cost about $0.00613 applies to the selected gpt-4.1-mini DEV evaluations at recorded rates, including recorded retries/repairs; it is not a current price quote or account balance. Coverage and passing software tests do not establish independent judgment accuracy.

[Presentation acceptance report](improvements/32-presentation-deck.md), [PDF/appendix audit](audits/2026-11-08/04-appendix-submission-audit.md), [submission contract](SUBMISSION.md).
