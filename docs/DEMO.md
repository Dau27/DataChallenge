# Five-minute demonstration

**Resumed by the owner on 8 November 2026.** Preparation and zero-spend technical rehearsal are active. The repository stays private until the owner makes it public at the deadline. Organizer control data remain unavailable. No paid inference is authorized by this rehearsal.

## Presenter card

Use the fresh private rehearsal copy, not the original workspace. Start with **DEV / checklist v1 / p1-ru-001**. The DEV set has 65 conversations: 60 organizer-synthetic chats and five real calls, 35 RU / 15 KZ / 15 EN. The workspace's 75 source revisions also include ten explicitly synthetic development records. Current selected DEV results are 64 complete and one needs review; an unclear call's total remains withheld.

The times below are a presentation allocation, not measured rehearsal results. Target 4:30-4:45 and keep a buffer below the five-minute maximum.

| Target time | Action | Suggested narration |
| --- | --- | --- |
| 0:00-0:35 | Open p1-ru-001, show checklist v1 and saved-run identity. | "This prototype evaluates the human operator in Russian, Kazakh and English. We import a transcript, select a saved checklist and retain the assessment. This is a real saved DEV evaluation, rather than a fresh model request." |
| 0:35-1:45 | Show needs=N/A, its reason and evidence; click an evidence range. Show Closing=No, total 92.31 and separate critical flag. | "Each judgment has an answer, weight, points, explanation and source evidence. N/A has an explicit applicability reason. Code calculates the total, redistributes applicable weights and rounds the final percentage. Critical violations are a separate flag. Missing actions point to the interval that was checked." |
| 1:45-2:55 | Open the specifically prepared older saved RU run with original 100. Appeal Closing, then separately replace it with No, cite m0010-m0012 and explain the missing recap/further-help offer. Save; show original 100 / effective 92.31 and history. | "An appeal records the disputed criterion and comment. The reviewer separately reads the source, supplies evidence and a rationale, and confirms or replaces the answer. This example's ending has a polite wish but lacks the required recap or offer of further help. The total recalculates locally. The original remains unchanged, and the decision survives reopening." |
| 2:55-4:15 | From v1 add a substantive support-ticket-reference criterion, inspect preview/field errors and save a new version. Then select the earlier real custom-checklist v2 assessment, clearly labeling it historical. | "Checklist changes are configuration, not code changes. We can edit definitions, weights, answer types, scales and N/A rules. Here we add an explicit support-case reference requirement. Saving creates an immutable new version. This rehearsal blocks inference, so that newly saved version has not been evaluated. This separate earlier real custom-checklist run demonstrates that an added criterion was evaluated; it is not a fresh result for today's draft." |
| 4:15-4:45 | Show saved model/attempt/usage metadata and paused budget. | "Each saved assessment retains its actual model, configuration and usage. The selected DEV set used gpt-4.1-mini and averaged about $0.00613 per evaluation at recorded rates, including retries and repairs. Fresh inference is paused here. Our latest checks passed503 backend cases plus the private saved-data case, and184 client tests. The required DEV JSON is validated; independent scoring accuracy and actual control acceptance remain unverified." |
| 4:45-5:00 | Buffer / finish. | Use only if necessary; do not open optional dashboards during the main flow. |

The new appeal/decision is an agent or presenter demonstration on a disposable copy, not an independent reference label. Do not change a judgment merely to create a dramatic score delta; use the source-supported closing correction above. If a rehearsal copy already contains that correction, reset only by preparing another new copy, or show its saved history and clearly say so.

## Zero-spend technical acceptance

Fresh production build passed. Three actual React DOM-to-local-API checks passed (no response mocks): RU/KZ/EN and call/unresolved evidence; real appeal/replacement/reload/comparison; and field errors plus a new nine-criterion version. The workflow made 37 actual API requests, preserved original 100 while recalculating the rehearsal result to 92.31, and refused fresh evaluation with HTTP 503 without creating a new assessment. The decision and version survived a cold restart.

Those initial checks were functional DOM verification, not spoken timing. The subsequent actual in-app browser walkthrough also verified evidence, a separately submitted appeal/reviewer decision (original100/effective92.31), change preview, immutable v6 save and the historical v2 ticket-reference judgment. It caught a queue-link bug (v1 row opened a newer diagnostic v5); both links now pin the displayed evaluation. Full frontend184/one paid opt-in skipped, final seven regressions and production build passed. The [new appendix adapter audit](audits/2026-11-08/04-appendix-submission-audit.md) adds44 submission tests and full backend503 plus the separately executed private-copy test. [Rehearsal evidence](improvements/28-demo-verification.md). None of these are measured spoken timings or fresh paid inference.

## Run the private rehearsal

The ignored task folder local_data/demo_verification_20261108 contains presenter.sqlite3, the guarded server, start/stop helpers and presenter-card.md with exact source/run links. The presenter copy now retains the observed agent practice decision/v6 save; use a new copy for a fresh unreviewed demonstration. Helpers/data are intentionally absent from a source clone. The server uses explicit credential-free settings and never reads the real .env. It binds only to localhost, blocks provider/external requests and automatically stops after30minutes. Use documented port8000: an initial8765 rehearsal correctly failed the app's browser-Origin protection; no security guard was weakened.

From the repository root, when port8000 is free:

```powershell
.\.venv\Scripts\python.exe local_data/demo_verification_20261108/start_demo.py presenter.sqlite3
```

Open [the private rehearsal](http://127.0.0.1:8000). Use the private presenter card to select the precise older appeal target; a newer saved run already has the correct Closing=No answer and must not be misrepresented as the unreviewed example. The launcher refuses an occupied port rather than stopping another process.

Stop only the owned rehearsal:

```powershell
.\.venv\Scripts\python.exe local_data/demo_verification_20261108/stop_demo.py
```

The completed DOM tests used rehearsal_retry.sqlite3; the browser used presenter.sqlite3. Both are isolated from main. To reset practice without overwriting either copy, create/verify a new private recovery bundle from main, restore to a new file inside the rehearsal folder (for example human-rehearsal-1.sqlite3), then run start_demo.py with that filename. [Backup/recovery commands](OPERATIONS.md). Keep full databases, source links and cards private. Do not expose them in a public unauthenticated deployment.

## Event boundary and timed rehearsals

A fresh evaluation after today's criterion change remains outside the zero-spend rehearsal. At the event, genuinely apply the changed checklist to the supplied data with authorized model access/budget. A saved result or successful configuration save does not complete that fresh-evaluation step. The existing application has earlier real custom-checklist evidence; this task does not claim a new v13/control run.

Two spoken practices are an engineering recommendation. Record real durations below; blank/unmeasured rows must not be presented as passed.

| Spoken rehearsal | Presenter / date | Measured duration | Required flow completed? |
| --- | --- | --- | --- |
| 1 | Pending | Not measured | Pending |
| 2 | Pending | Not measured | Pending |

Backup examples for questions: p1-en-001 (English); p1-kz-012 (preserved 84.62 original / 100 effective review); p4-ru-001 (recording-player link); p4-ru-005 (unclear self-introduction and withheld total). Link presence was checked; external player availability and intelligibility were not newly tested. Use optional comparison/export tools only after the core flow or if asked.

At the deadline the owner will handle public repository visibility. Official freeze timing/commit, organizer control/replacement acceptance and submission follow [the event procedure](CONTROL_AND_FREEZE.md). No public release, paid inference, organizer submission or official freeze was performed during this rehearsal.
