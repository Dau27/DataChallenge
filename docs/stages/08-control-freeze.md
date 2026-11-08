# Stage 8 — Control and freeze

Status: **not reached; organizer inputs unavailable**.

Owner confirmation, 8 November: organizer control access is unavailable and repository publication must remain deferred. Preparation of [judge documentation and private recovery](../improvements/26-judge-readiness.md) is complete; the control run and public handoff are not current implementation tasks. No additional credential request, guessed dataset, model request, organizer message or official freeze is made.

Preparation is complete in [CONTROL_AND_FREEZE.md](../CONTROL_AND_FREEZE.md): required inputs, safe import/versioning, combined budget reconciliation, actual-commit recording and permitted post-freeze UI actions. No model request was made to prepare it.

- Application supports importing another organizer-supplied dataset group while preserving other signed endpoint parameters.
- Group/source identity is namespaced; changed content preserves older transcript revisions and evidence.
- The frozen application's UI can save new rubric versions and create evaluations without changing code.

No control identifier, official event start/freeze time, or final freeze instruction has been supplied. No group was guessed, no event date was inferred, and no commit has been labeled frozen. No control processing or public submission is claimed.

Next: when organizers provide the control group and timing, import that exact group, account for processing/retry/review states, and record the actual final commit. After an actual code freeze, do not modify application or prompt files to handle a replacement criterion; use the saved-checklist interface.
