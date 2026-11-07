# Stage 2 — Checklist preview and field errors

Status: **PASS**, 7 November 2026. New hosted-model requests: **0**.

## Completed

- Added read-only draft preview against a selected saved checklist. It shows saved/draft differences for definitions, weights, answer types, scales/anchors, N/A rules, sections, additions/removals, order and other changed configuration fields.
- Preview runs the existing strict backend domain validation. It returns field locations and readable criterion/field labels without echoing private request inputs in error objects.
- The editor associates errors with inputs and provides a linked error summary. Invalid, pending or unavailable validation blocks Save. Backend save validation remains authoritative.
- Late preview responses for earlier drafts are ignored; an old valid response cannot enable saving the current invalid draft. Existing draft preservation and immutable version behavior remain in place.
- Structural preview never evaluates a conversation, alters a saved checklist, or treats an old answer as a result under changed semantics.

## Verification

Nine backend scenarios cover changed definitions, weights, type, N/A condition, scale, section, criterion add/remove and order. Six invalid cases check field locations for weight, missing N/A condition, invalid/duplicate scale values, missing section and empty section title; direct invalid saves still return HTTP 422. These tests prove previews create no versions/evaluations or provider calls.

Client tests exercise saved-versus-draft display, accessible field errors, blocked invalid save, correction and immutable save, stale-response rejection and retained browser drafts. The final suite passed **125 backend / 14 client tests**; the production TypeScript/Vite build passed.

Actual browser verification on a copied database changed weight 10 to -1: the input became invalid, the preview showed the change and Save was disabled. Correcting it to 12.5 and renaming the checklist enabled a real UI save of technical version v6. The original v1 remained unchanged. This diagnostic version exists only in the copy and was not evaluated. Its saved-state screenshot is private at local_data/improvements_20261107/checklist-preview.png. The version survived cold restart.

An early invalid-section test returned a checklist-level location; this was corrected to the affected criterion's section field. An early build also caught test-fixture typing errors, which were corrected before the passing production build. No rubric seed or model verdict was changed.

Next: use preview when preparing organizer criterion changes. New semantic assessments still require a later real, authorized provider run.
