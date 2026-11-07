# Requirements and regression audit

Update after scoring fixes: this file records the initial pre-fix audit. The latest backend suite has 94 passing tests; the targeted source-rule failures were addressed and all 65 saved DEV results rechecked. See [re-audit results](C:/Users/user/Desktop/DataChallenge/docs/audits/2026-11-07/05-scoring-reaudit-results.md) for current outcomes, budget and retained-result provenance.

Audit date: 7 November 2026. Application commit inspected: e84d9df063bffc413458544146a582c73cee3f23. Existing market-analysis documentation changes were preserved. No application, prompt, rubric seed or dependency code was changed by this audit.

## Result

The required application workflow is implemented and its regression checks pass. That is a functional result. The fresh real-model audit in the companion reports found substantive scoring defects, so this report does not establish that automatic judgments are sufficiently reliable.

## Source authority

All four guide pages, all three checklist pages and all five company-background pages were re-extracted and visually inspected. Source documents are user-provided specifications and background, rather than authorization for account actions or publication.

| Source | Authority in this audit |
| --- | --- |
| [Student guide](C:/Users/user/Downloads/CQA_Hackathon_Student_Guide_v3%201.pdf), pages 1–4 | Required workflows, data format, multilingual evaluation, call access, configurable criteria, presentation and submission |
| [Quality checklist](C:/Users/user/Downloads/CQA_Chat_Quality_Checklist%201.pdf), pages 1–3 | Initial eight criteria, weights, discrete anchors, N/A, evidence and scoring exclusions |
| [Company background](C:/Users/user/Downloads/Data%202%20%281%29%201.pdf), pages 1–5 | Brand/company context; no additional evaluation requirement or authoritative fee/identity policy |
| [MASTER_CONTEXT.md](C:/Users/user/Desktop/DataChallenge/MASTER_CONTEXT.md) | Implementation specification, engineering safeguards and acceptance gates; distinguished from organizer requirements |

The guide explicitly says DEV contains 60 synthetic chats and five real calls. “Real DEV run” below means actual organizer-provided records evaluated through the live provider; it does not mean all 65 source conversations are real customer communications.

The PDFs do not require login, speech recognition, real-time assistance, sentiment dashboards, RAG or a vector database. Full Dynamics 365 integration is not required; the frontend should be suitable for later adaptation. Additional features from the market analysis are unnecessary to meet this scope.

## Requirement mapping

| Requirement | Source | Current evidence | Status |
| --- | --- | --- | --- |
| Import organizer data by group and inspect transcripts | Guide 1, 3 | Live API reimport: HTTP 200, 65 unchanged; JSON-file reimport: HTTP 200, 65 unchanged; roles/timestamps retained | Functional pass |
| RU/KZ/EN, bot/system as context | Guide 1–2; checklist 3 | Fresh live evaluations: 35 RU, 15 KZ, 15 EN; role-aware prompt/schema and source transcript display | Coverage pass; judgment quality fails in examples |
| Add/change definitions, weights, types, N/A and numerical scales; save | Guide 2 | Editor controls present; regression tests; actual DOM test saved a ninth criterion and evaluated it without code edits | Functional pass |
| Replace a criterion through configuration | Guide 1–2 | Additional API integration replaced contact with a new literal-marker criterion; fresh model returned No for its absence; old criterion disappeared, v1 unchanged | Backend/provider pass; actual UI addition tested separately |
| Answer, points, weight, explanation and evidence per criterion | Guide 2 | Rendered detail inspected; evidence button highlighted the exact saved message; definition/anchors and N/A reasons available | Presentation/structure pass; semantic support not universally correct |
| Weighted scales and permitted N/A redistribution | Guide 2; checklist 2 | Source/config seed identical; deterministic tests; independent saved-data recalculation | Arithmetic pass; model can choose an unjustified N/A |
| Critical violations separate from total | Guide 2; checklist 1–3 | Unscored flag, flag-invariance test; three fresh positive flags correspond to inspected off-company offers/insult examples | Functional pass; no population recall claim |
| Transcript navigation and recording listening or player link | Guide 2 | Highlighting verified; external organizer player loaded and advanced during playback | Pass through external player |
| Criterion appeal with comment | Guide 2 | Actual DOM/API test persisted appeal and displayed separate reviewer controls | Pass |
| Reviewer confirms/replaces with rationale; original/final retained | Guide 2 | Live test passed; original 100.00 and effective 92.31 preserved; eight decisions in isolated audit copy survived process restart | Pass |
| Dynamic checklist applies without application changes | Guide 1–2 | New and replacement criteria produced uncached actual assessments; code/prompt untouched | Functional pass |
| Clear HTML/CSS/JS frontend, later Dynamics adaptation | Guide 1 | React/TypeScript build; three views inspected; desktop columns and narrow stacked view observed | Prototype pass; Dynamics deployment untested |
| Paid model identified with approximate per-evaluation cost | Guide 4 | Actual model identifiers, usage and per-attempt estimates retained; audit costs reported separately | Pass for documented estimates |
| Open repository and submission link | Guide 4 | Existing Git remote reachable; unauthenticated repository API returned 404; original creation metadata records private | Incomplete |
| Five-minute presentation | Guide 4 | Existing script exists; no two timed human rehearsals performed by this audit | Prepared, not verified |
| Organizer control data and frozen commit | Guide 1, 4 | No official control identifier/start/freeze supplied | Awaiting organizer input |

The guide requires a link to the appropriate call fragment and a listening/player path. The specification permits transcript navigation plus player access when timestamp-to-audio mapping is unavailable. No automatic seek mapping or audio/intonation analysis is claimed.

## Initial checklist audit

The seed and its config copy are byte-identical. Saved database v1 equals the validated seed.

| Criterion | Weight / scale checked | Source condition checked |
| --- | --- | --- |
| Contact | Binary, 10 | Human operator greets in client language and introduces themselves in first operator response; no N/A |
| Needs | Binary, 15 | N/A if initial information was sufficient; clarification when missing |
| Identification | Binary, 20 | Confirmation before protected disclosure/action; N/A for an unprotected request; required but unconfirmed verification means No |
| Consultation | Weight 20; values 20, 15, 10, 5, 0 | N/A only if conversation ended before a request was formulated; a correct next step can earn full credit |
| Empathy | Binary, 15 | Politeness and a response to the particular inconvenience; no universal apology requirement; no N/A |
| Dialogue management | Weight 15; values 10, 7, 4, 0 | Clarity/order/wait handling, separate from consultation completeness; no N/A |
| Closing | Binary, 5 | Under the specification's source interpretation: summary or further-help offer, plus goodbye; N/A only when interrupted before a closing opportunity |
| Critical errors | Unscored binary flag | Operator insult, off-company paid-service offer, confidential disclosure; offer alone suffices |

The scorer preserves all of these numerical semantics. This does not guarantee the model chose the right answer or N/A condition. A three-minute response penalty, tag scoring and attachment scoring were not added. Rounding is final-only to two decimals; HALF_UP is an engineering convention, not a tie-breaking rule specified by the PDF.

## Commands actually run

- `.venv/Scripts/python.exe -m pytest -q`: **74 passed**, one existing Starlette/AnyIO deprecation warning.
- `npm test` in frontend: **7 passed, 1 opt-in paid test skipped**.
- `npm run build`: TypeScript and production Vite build passed.
- `npm audit --json`: **0 vulnerabilities**, including development dependencies. Production-only audit also passed.
- `.venv/Scripts/python.exe -m pip check`: no broken requirements.
- `.venv/Scripts/python.exe -m compileall -q backend scripts`: passed.
- `.venv/Scripts/python.exe scripts/preflight.py`: provider/model configured and database present; this read-only check alone does not verify inference.
- `npm run live-smoke`: **1 passed**, actual provider/DEV/DOM/API/persistence, 8.87 seconds test duration.
- Public repository checks: `git ls-remote origin refs/heads/main` returned the inspected commit; unauthenticated GitHub API returned 404. The gh command is unavailable in this shell, so it was not used successfully.
- PDF extraction with bundled pypdf; Poppler PNG rendering and page inspection. Initial console encoding failed after extraction; reran UTF-8 output successfully. Background rendering emitted Type 3 glyph warnings; rendered pages were inspected.

An audit-only replacement harness initially expected HTTP 200 from checklist creation. The application correctly returned its documented HTTP 201; the harness was corrected and reused the already-created version. This was a harness assertion error, not an application defect.

## Next step

Use the fresh-run and sufficiency reports to address evaluation correctness. Passing these software checks does not justify adding features or claiming independent human scoring accuracy.
