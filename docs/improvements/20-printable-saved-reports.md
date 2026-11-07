# Stage 20 — printable saved-evaluation reports

**Builder handoff: implementation and targeted acceptance passed; desktop app preview checked; remaining paper/narrow/stress visual acceptance is pending because Computer Use stopped.** 8 November 2026. No shared-file integration, merge, push, provider request, demo or publication was performed by this builder.

## Worktree and ownership

- Assigned worktree: `C:\Users\user\Desktop\DataChallenge\local_data\sprint_20261108\print`.
- Assigned branch: `sprint-print-20261108`; audited common baseline `d7d8a9d2a93ff5b537e34e689dd63b0e952f0fb3`.
- Read MASTER_CONTEXT, CURRENT_CONTEXT, the eight-hour plan, printable-report plan and canonical root handoff before editing. Implementation began only after the canonical handoff became READY.
- Changes are new print component/renderer/scoped styles/types/fixtures/tests and this report only. Existing Detail, SavedExport, App, API/export sanitation, shared types/styles/configuration and CURRENT_CONTEXT are untouched.

## Exact coordinator integration

Copy or cherry-pick only these new files from this worktree:

1. `frontend/src/PrintableEvaluation.tsx`
2. `frontend/src/printEvaluation.ts`
3. `frontend/src/printEvaluation.css`
4. `frontend/src/printEvaluationTypes.ts`
5. `frontend/src/printEvaluationAssets.d.ts`
6. `frontend/src/printEvaluationFixtures.ts` — clearly labeled synthetic test data only
7. `frontend/src/PrintableEvaluation.test.tsx`
8. `frontend/src/printEvaluation.test.ts`
9. This report.

In `Detail.tsx`, the coordinator adds the import and mounts the component alongside the current SavedExport inside the existing assessment-tools disclosure:

```tsx
import PrintableEvaluation from './PrintableEvaluation';

{evaluation && <PrintableEvaluation
  key={evaluation.id}
  evaluationId={evaluation.id}
  updatedAt={evaluation.updated_at}
/>}
```

These are the frozen props; do not pass an effective score, transcript, simulation or unsanitized EvaluationDetail as the report packet. Retain the selected run's live `updated_at` prop after review/retry refresh. The component reads only the existing `GET /api/evaluations/{encoded-id}/export?format=json&include_excerpts=false|true`. No routes or backend changes are needed. Both answer bases are always included; the user owns the optional excerpt checkbox, initially false.

The component imports its scoped stylesheet. The renderer also embeds that trusted stylesheet into the isolated report document. `@page` exists only inside the report's HTML, so importing this feature does not change global page settings. Parent printing hides only this feature's own controls; it does not hide or select other application content. The explicit print action calls only the preview iframe's print function, never the parent window.

## Delivered behavior

- An explicit **Preview saved report** action reads one saved sanitized export. Preview, optional excerpts, refresh, error retry and **Print / Save as PDF** use native keyboard-accessible controls. Opening focuses the preview heading; closing returns focus to the trigger.
- Printing never runs on mount, fetch completion, an option change or preview load. It requires an enabled print button action after the current report iframe loads.
- ID, update timestamp, both answer bases and excerpt options form the resource identity. Scope/generation guards reject late responses, including A → B → A. A changed identity hides the old preview synchronously. Refresh/retry also hides stale content. The packet's run/update and complete manifest/source/checklist identity must agree before rendering.
- Includes source revision/hash, dataset, language/channel, checklist/run identity, creation/update times, original/effective totals, applicable weights, raw subtotals, section totals, criterion definitions/scale/N/A condition, both judgments, weights/points/contributions, explanations, N/A/review reasons and evidence IDs.
- Includes saved appeals, reviewer rationale/replacement judgment/evidence, resulting totals/sections/criterion points, timestamps and appeal links by ID. No verified reviewer identity is invented.
- Saved decimal strings are displayed without conversion, rounding or score calculation. Zero remains zero; N/A membership and null/unavailable/unresolved totals stay explicit. Flags are labeled unscored. Failed or missing snapshots show their actual unavailable state.
- Known provenance, cache lineage and request accounting are displayed; missing metadata remains unavailable. Cache reuse is not described as an independent assessment. Estimates are not invoices.
- The report relies on the existing backend export's credential/recording-URL redaction, requires its explicit exclusion policy, and renders allowlisted fields only. Arbitrary metadata, request payloads, recording fields or credentials are not serialized into HTML. Excerpts remain an explicit export-policy option. Explanations/review comments can quote private text: the report is not anonymous.
- Dynamic source/checklist/judgment/review values are HTML-escaped text, never active markup, attributes or links. The preview is sandboxed without script permission, has a no-referrer policy and a restrictive CSP. No remote fonts/assets, PDF service or new dependency is used.
- System fonts support RU/KZ/EN, paragraphs preserve newlines, long words wrap, headings stay with following content and table headings repeat on printed pages. Long explanations/excerpts can split across pages rather than being placed in an unsplittable giant table row.

## Actual validation

Commands from the assigned worktree, with `local_data/offline.ps1` first; frontend commands run in its `frontend` directory:

```powershell
npm ci --offline --no-audit --no-fund
node node_modules/vitest/vitest.mjs run --maxWorkers=2 src/printEvaluation.test.ts src/PrintableEvaluation.test.tsx
node frontend/node_modules/typescript/bin/tsc -b frontend
```

- Offline pinned install: **115 existing pinned packages installed**, no dependency/lock changes.
- Owned component/renderer tests: **17 passed**, 2 files, 3.60 seconds. Exact saved strings, reviewed/unresolved and zero/null/N/A/flag states, missing/failed snapshots, scope/update/option races, stale packets, source escaping, excluded fields, provenance, loading/errors/retry/focus/close, explicit child-only printing, iframe errors/retry and print errors passed. Iframe errors use a direct listener because they do not bubble.
- TypeScript project check: **passed**. The coordinator owns the combined production build and full application suites; baseline 309/118 counts are not claimed as fresh feature checks here.
- Initial test attempts exposed Vitest's CSS-import stub and happy-dom's automatic srcdoc load timing, plus an absent emulated parent print function. The final tests read the actual owned stylesheet for serialization assertions, check loading before asynchronous completion, and stub print functions explicitly. Those initial failures were not product passes. A late option request was also made explicitly pending so the test runner could not fall through to an unstubbed fetch. Final targeted run was clean.

Private actual-data acceptance:

```powershell
& 'C:/Users/user/Desktop/DataChallenge/.venv/Scripts/python.exe' local_data/prepare_print_qa.py
# from frontend:
node node_modules/vitest/vitest.mjs run --maxWorkers=1 local_data/actualPrint.test.ts
```

The preparation uses a read-only SQLAlchemy session on the coordinator-provided copy, direct empty Settings and a socket-deny guard; it does not construct/initialize an app database. It exported **249 plain saved-run packets plus three excerpt-enabled actual packets**, with no database-file change or socket request. The private renderer acceptance passed **12 tests**, 10.45 seconds: **252 packets, 2,014 criterion entries, 3,212 original/effective judgments, 12 reviewer judgments and 497 excerpt-message occurrences**. It checked both total cells, exact answers/raw points, explanations, evidence IDs, review rationales/judgments, excerpt text, inert HTML and unchanged packet values. All artifacts remain ignored under the assigned worktree's local_data folders. The final combined targeted run passed **29 tests in three files, 11.52 seconds**, followed by a clean TypeScript project check.

Actual selected cases: English `p1-en-001` (92.31 / 92.31), reviewed Kazakh `p1-kz-012` (original84.62 / effective100.00, two reviews) and unresolved Russian call `p4-ru-005` (original92.31 / effective null, one review). These are existing saved values, not new labels or assessments. A separate long RU/KZ/EN synthetic stress artifact is clearly labeled SYNTHETIC PRINT STRESS ONLY.

## Visual check status and coordinator acceptance

Prepared private standalone HTML from all three actual excerpt packets and the synthetic long-text stress case. Browser Use initially rejected the `file:` URL because its policy permits only HTTP(S); that blocked file access was not bypassed. The user then explicitly authorized this chat to run an isolated copied-data **app** preview, overriding the handoff's coordinator-only preview-server rule. This used normal HTTP app controls and the existing JSON export endpoint, rather than navigating an arbitrary filesystem report.

Ran a private acceptance harness on loopback5189 with the existing backend on loopback8141, using a further disposable database copy, empty credentials, zero budget, a provider-request failure guard, an external-socket guard and read-only HTTP middleware. No existing shared files were edited. The harness distinguishes actual copied runs from its synthetic long-text and outage cases. It imports the real new component and current shared design styles; it does not mock the actual-run export endpoint.

Observed desktop app checks: keyboard Enter opened the preview and focused its heading; the actual English report loaded with scripts/remote assets excluded; the actual reviewed Kazakh run displayed original84.62/effective100.00, both saved review decisions and18 explicitly enabled evidence excerpt ranges. Its report client/scroll widths both measured1006px, without horizontal overflow. Screenshots showed readable controls/report paragraphs and review history. The shared design's column layout affected the excerpt checkbox; the owned scoped rule now explicitly sets a row direction and automatic checkbox width, and the corrected checkbox row was observed. These are limited app-preview checks, not a paper-layout or complete multilingual-glyph certification.

**Computer Use then stopped when it could not determine the native Chrome URL confidently enough to enforce policy.** No further UI input, alternate browser retry or policy bypass was attempted. Native paper preview, A4/Letter pagination/repeated headers, narrow-screen rendering and synthetic long-text visual inspection remain **not run**. Source text/long multilingual serialization passed automated tests, which do not establish paper layout.

The coordinator should finish those remaining visual checks after mounting the component above. Inspect the unresolved Russian case, all three languages' long text, A4/Letter page breaks and repeated headings, a narrow screen and the clearly labeled synthetic stress report. Activate Print / Save as PDF explicitly and cancel after checking paper preview; do not submit a print job or publish. Record actual outcomes here or in the final integration report. An additional product screenshot or print-preview pass is not claimed from the interrupted native action.

## Preservation and teardown

Private `local_data/final_print_check.py` passed: all15 main tables and schema/index fingerprints, all30 protected files and the supplied builder database copy exactly match the coordinator's audited baseline. All249 saved evaluations are preserved. Every original business table in the further preview copy also matches; only the existing app's budget bootstrap was permitted there. No tracked shared file in this builder worktree changed. Both owned preview ports5189/8141 are closed after stopping only their verified Python/Vite/esbuild processes. Private generated packets, HTML, disposable database and acceptance helpers remain ignored; no credentials were copied into the worktree. Hosted/provider requests and added spend remain zero.

## Limits

One run only; bulk printing is deferred. Browser Print / Save as PDF uses the user's installed browser and selected paper/header/footer options; it is not a generated PDF service. Reports can be long when complete explanations, reviews and full evidence ranges are included. A sanitized source quote remains private source material. The component requires the existing version1 single-run export contract and rejects a run updated after the parent's selected-run timestamp until that assessment is refreshed. No independent judgment accuracy, policy verification, secure reviewer identity or data anonymization is claimed.
