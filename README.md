# Conversation Quality Analytics

Local-first Freedom Broker CQA prototype: **import → saved checklist → operator evaluation → source evidence → appeal → reviewer decision → preserved original and effective score**.

The application uses React/TypeScript/Vite, FastAPI/Pydantic, SQLAlchemy/SQLite, a configured OpenAI Responses provider, and deterministic Decimal arithmetic. No login is required; appeal submission and reviewer decisions are separate anonymous demo actions.

## Current verified state

- Organizer DEV access works locally: actual response/import contained **65 records: 35 RU, 15 KZ, 15 EN; 60 chats and 5 calls**. Private payloads and the signed endpoint are excluded from Git.
- Domain, persistence, retry/cache/restart, appeals, and configuration behavior have automated tests with clearly synthetic inputs and injected HTTP test transports.
- The real provider gate passed after the user resolved an honestly reported exhausted-credit block. `gpt-5.4-mini` produced saved real DEV assessments. A refined example used 3347 input / 1088 output tokens and cost an estimated $0.00740625 at identified standard rates.
- Opt-in live React DOM/API test passed: add a substantive criterion → save new version → actual model evaluation; submit appeal → separate agent-attributed review → original/effective scores → reload. This is functional DOM integration, not visual/browser QA.
- Ten explicitly synthetic hosted-model diagnostics currently match 13/13 provisional checks; these are agent-authored diagnostics, not human-reviewed accuracy. Full DEV processing is being verified; see CURRENT_CONTEXT.md for the final accounted states and application cost.
- See [CURRENT_CONTEXT.md](CURRENT_CONTEXT.md) for commands actually run, exact current outcomes, and blockers. Per-stage reports are in [docs/stages](docs/stages).

## Windows quick start

Requires Python 3.12+, Node 22+ (tested with 22.11.0), npm, and Git.

```powershell
git clone https://github.com/Dau27/DataChallenge.git
cd DataChallenge
.\scripts\setup.ps1
```

The setup script creates an isolated `.venv`, installs the full Python lockfile and `npm ci` lockfile, builds the frontend, and creates `.env` only if it does not exist. It never replaces an existing `.env`.

Edit the ignored `.env` locally:

```dotenv
OPENAI_API_KEY=<actual model API key, never an organization ID>
OPENAI_MODEL=<a model available to your account with Responses structured output>
ORGANIZER_API_URL=<actual signed organizer endpoint from the guide>
```

No model name, model access, credit balance, or price is assumed. An organization ID, Brev console URL, or Brev compute balance does not authenticate an OpenAI model request. [Brev credits cover running GPU environments and storage](https://docs.nvidia.com/brev/guides/console-reference); using them for inference requires a separately configured model server. No Brev environment is created by this application.

```powershell
.\start.ps1
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). API documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs). The built frontend and API share one local origin. Use one backend process; do not use multiple Uvicorn workers against this job runner. Stop with Ctrl+C. Restart after changing `.env`; requests already in flight are not claimed to survive a process restart.

If local PowerShell execution policy blocks scripts, use the equivalent commands below without changing your machine's policy:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
cd frontend
npm ci
npm run build
cd ..
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:create_app --factory --host 127.0.0.1 --port 8000 --no-access-log
```

For frontend development, run `npm run dev` inside `frontend` with the backend on port 8000; Vite's port 5173 proxy forwards `/api`. Production-style local usage needs only the backend process after building.

## Use the workflow

1. In Conversations, import `DEV` from the configured API or upload the organizer JSON envelope. The same parser validates either source. Other groups must use the organizer-supplied identifier.
2. Inspect a conversation and the exact provided roles/timestamps. Calls offer a recording player/link if a source URL exists. Expired/absent audio does not fabricate a recording or automatic seek mapping.
3. Select a saved checklist version, test provider access, then evaluate one conversation before submitting a batch. Missing credentials produce a visible blocker, never a fake assessment.
4. Open a saved run. Click evidence IDs to highlight its original transcript range. Inspect N/A reasons, points, section percentages, separate flags, and any missing basis requiring review.
5. Appeal a criterion with a comment. In a separate action, review the appeal, confirm/replace the answer, and save a rationale. Valid replacements need evidence. Review changes recalculate locally without a model call and preserve the original.
6. Edit a criterion or add a genuinely new requirement, save a new version, select it, and create another evaluation. Existing results retain their old snapshot. Changes invalidate incompatible cache reuse.

The UI reports states for the selected checklist version: not evaluated, queued, running, complete, needs review, failed, interrupted. Successful HTTP inference and assessment completeness are separate concepts. Unsupported factual claims needing an unavailable authoritative source must request review, rather than invent company policy.

## Scoring and evidence

The original rubric seed is preserved unchanged at `config/initial_checklist.json`. Runtime criteria are configuration-driven; eight fixed response fields are not hardcoded.

For applicable scored criteria: binary Yes/No = 1/0; numerical fraction = selected allowed anchor / maximum configured anchor. Raw points = weight × fraction. Total = 100 × applicable raw points / applicable weights. Valid N/A excludes both numerator and denominator. Flags have no numerical penalty. Unresolved criteria block the final total; zero applicable positive weight returns null with a reason.

Only the final percentage is rounded to two decimal places, using ROUND_HALF_UP (an engineering convention; the source does not prescribe tie-breaking). Sections use their own applicable weighted percentage, not an unweighted average to compute the global result. Numerical scales with nonzero minima still divide by their maximum.

Provider output is validated for exact criterion coverage, strict answer types, discrete allowed values, N/A conditions, explanations, and existing ordered evidence ranges. Schema validity and existing evidence IDs do not prove that an assessment is substantively correct. Excerpts are rendered from stored source messages, never model-generated quotes.

## Persistence and recovery

- SQLite defaults to ignored `local_data/cqa.sqlite3`; WAL and serialized write transactions protect imports/reviews/job claims.
- Identity includes dataset group and source ID. All evaluation-relevant fields are hashed. Changed content creates a revision; unchanged reimports reuse the immutable revision.
- Checklist saves create immutable complete snapshots. Original judgments are never overwritten by reviews.
- At most one output-repair call; each network request has at most two attempts. Refusals, malformed output, oversized input, outages and incomplete responses remain visible. Transcripts are never silently truncated.
- Configurable bounded concurrency defaults to 2. Abandoned running jobs become interrupted at startup; queued jobs resume. Retry preserves all attempts. Changed model/settings require a new evaluation.
- Cache identity includes source content, complete checklist, prompt/schema/scoring versions, provider/model and generation settings. Only original model assessments are cached; reused results are labeled.
- Token usage and request latency include all recorded attempts. Estimated cost needs actual complete usage plus configured input/output rates and an identified rate source. Otherwise it is unavailable. Unknown usage is not free usage.

Provider contract: [official Responses structured-output documentation](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses). The adapter uses `text.format` JSON Schema, no tools, and `store: false`.

## Validation and helper commands

```powershell
.\.venv\Scripts\python.exe -m pytest -q
cd frontend
npm test
npm run build
npm audit
cd ..
.\.venv\Scripts\python.exe scripts\preflight.py
```

Preflight prints configuration status only. It exits nonzero when a model cannot run. Keys and private endpoint values are never printed.

Import saved private JSON (idempotent; no running server needed):

```powershell
.\.venv\Scripts\python.exe scripts\import_json.py local_data\dev.json
```

Once an actual provider is configured and the local server is running, run the first real saved slice:

```powershell
.\.venv\Scripts\python.exe scripts\live_slice.py --source-id p1-ru-001 --checklist 1
```

The script writes full results under ignored `local_data/live_runs/` and reports actual terminal state/usage. `--fresh` bypasses cache and makes another billable call. No synthetic fallback exists. A needs-review result can be a successful execution with no final score; resolve the missing basis in review.

Optional diagnostics after the real slice passes:

```powershell
.\.venv\Scripts\python.exe scripts\select_reference.py
.\.venv\Scripts\python.exe scripts\behavior_checks.py
.\.venv\Scripts\python.exe scripts\run_dev.py --budget-usd 4.00 --checklist 1
```

Reference selection writes an ignored private manifest with development/holdout splits and `human_reviewed: false`. Behavioral checks submit the clearly synthetic multilingual fixtures to the actual hosted provider and can incur charges; expectations are provisional agent-authored checks, not independent labels or benchmark accuracy. Their report is private under `local_data/`. These diagnostics are not a substitute for actual DEV processing.

The DEV runner caps its guard at $4 to leave headroom below the user's $5 balance. It includes earlier application evaluation costs, reserves four maximum attempts before a new job, retains a conservative reservation for unknown usage, and reports every record's actual state. This does not account for unrelated account usage. The opt-in `npm run live-smoke` (inside frontend) makes a real paid evaluation and saves real versions/appeals; ordinary `npm test` skips that test.

## Data handling and submission

`.env*`, local data, recordings, PDFs, databases, logs, dependencies and build outputs are ignored. Only explicitly synthetic fixtures belong in public Git. Source PDFs remain in their original supplied location; redistribution permission is not assumed. Do not expose real conversations in an unauthenticated public deployment.

The GitHub repository starts private as a reversible default. Public visibility, event submission, control-group identifier, official event timing and freeze commit must be recorded when actually performed/supplied. No event start or freeze is inferred from wall-clock time. [Demo script](docs/DEMO.md) describes the required flow and honest limitations.
