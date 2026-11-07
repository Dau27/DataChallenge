# Conversation Quality Analytics

Local-first Freedom Broker CQA prototype: **import → saved checklist → operator evaluation → source evidence → appeal → reviewer decision → preserved original and effective score**.

The application uses React/TypeScript/Vite, FastAPI/Pydantic, SQLAlchemy/SQLite, a configured OpenAI Responses provider, and deterministic Decimal arithmetic. No login is required; appeal submission and reviewer decisions are separate anonymous demo actions.

## Current verified state

- **Market feature research refreshed:** ten platforms rechecked against the current build. Recommended next additions are saved-run comparison, evidence exports and transcript-text search with saved filters; all can use existing data without new inference. These are proposals, not implemented features. [Feature options and acceptance gates](docs/MARKET_FEATURE_OPTIONS.md). Demo deferral and zero-spend limits remain in force.

- **Delivery scope updated:** the manual reference-review exercise is removed from delivery and demo plans. Private evidence is retained. **Five-minute demo work is deferred at the user's request.** [Scope update](docs/audits/2026-11-07/12-delivery-scope-cleanup.md).

- **Call recording follow-up:** verified and excerpted the actual dataset audio. The introduction remains unclear in local recognition and the user's listening check; original Yes/92.31 preserved, contact needs_review and final total withheld. No database changes or paid API calls. [Recording review](docs/audits/2026-11-07/10-call-recording-review.md).

- **Latest PDF audit after corrections:** core workflow and arithmetic pass; **64 DEV complete / one awaiting recording review**. Fresh **127 backend / 15 client tests and build pass**. Informal readiness remains about **85/100**, with independent accuracy, live v13/unseen control validation, timed demo and public/event handoff still unverified. No model calls or data changes. [Current audit](docs/audits/2026-11-07/09-post-correction-pdf-audit.md).

- **Latest source corrections:** fixed the flagged KZ N/A and consultation judgments through attributed review; retracted the uncertain call introduction to needs_review with its total withheld. Originals are unchanged. **64 DEV complete / one awaiting recording review; 127 backend / 15 client tests and build pass**, zero added inference. [Correction report](docs/audits/2026-11-07/08-zero-spend-scoring-corrections.md). Independent scoring accuracy remains unverified.
- **Three requested improvements implemented:** shared server-side budget protection, checklist change preview with field errors, and pending-appeal/critical-finding filters. **125 backend / 14 client tests** pass; the paid opt-in test is skipped. Build, copied-data browser/HTTP, isolated-source and restart checks passed with **zero added model calls**. [Stage reports](docs/improvements/README.md).
- **Earlier paid scoring fix/re-audit:** reached **65 complete DEV results**, **26/26 targeted provisional checks** and **94 backend tests**. The latest source correction above now withholds one uncertain total. N/A/answer consistency and source closing validation remain implemented; old outputs and exact versions/costs are preserved in [audit reports](docs/audits/2026-11-07/README.md). No market features were added.
- Organizer DEV access works locally: actual response/import contained **65 records: 35 RU, 15 KZ, 15 EN; 60 chats and 5 calls**. Private payloads and the signed endpoint are excluded from Git.
- Domain, persistence, retry/cache/restart, appeals, and configuration behavior have automated tests with clearly synthetic inputs and injected HTTP test transports.
- The real provider gate passed after the user resolved an honestly reported exhausted-credit block. `gpt-5.4-mini` produced saved real DEV assessments. A refined example used 3347 input / 1088 output tokens and cost an estimated $0.00740625 at identified standard rates.
- Opt-in live React DOM/API test passed: add a substantive criterion → save new version → actual model evaluation; submit appeal → separate agent-attributed review → original/effective scores → reload. This is functional DOM integration, not visual/browser QA.
- The initial DEV processing set had 59 complete / 6 needs review. The paid defect-fix audit reached 65 complete; the latest zero-spend correction has **64 complete / one needs review**, with zero calculation/evidence-reference mismatches. Earlier outputs and failures remain in history; no mock/fabricated fallback was used.
- Accepted post-fix DEV assessment estimate: **$0.3983244**. The entire fix/re-audit, including unsuccessful trials/repairs/custom diagnostic, estimated **$0.6271780**. All known application/task usage including the separate prior audit is **$1.61195315**; historical unknown usage is conservatively reserved separately. This is not an invoice. Each result retains its actual model/prompt/schema/rate snapshot.
- Ten explicitly synthetic gpt-5.4-mini diagnostics match 13/13 provisional checks; these are agent-authored diagnostics, not human-reviewed accuracy. In-app browser smoke verified the main views/evidence. Semantic accuracy remains unverified; demo execution is deferred and organizer control awaits inputs. See CURRENT_CONTEXT.md and per-stage reports.
- See [CURRENT_CONTEXT.md](CURRENT_CONTEXT.md) for commands actually run, exact current outcomes, and blockers. Per-stage reports are in [docs/stages](docs/stages).
- Earlier zero-spend handoff checks passed a fresh setup, **94 backend / nine client tests**, copied-data review/version persistence and the corrected recording link. No new inference was used. The [readiness report](docs/audits/2026-11-07/06-zero-spend-readiness.md) preserves that evidence; the [deferred demo](docs/DEMO.md) and [control/freeze runbook](docs/CONTROL_AND_FREEZE.md) describe remaining delivery steps.

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

**Paid requests are paused by default:** BUDGET_LIMIT_USD=0. Saved results, draft preview and manual review remain available. Compatible cached reuse is free. This task left the real .env unchanged and made no model request. Before later authorized inference, deliberately configure a positive shared ceiling and identified rates; the budget is estimates/reservations, not a provider account balance.

The current private workspace includes a reviewed ignored opening baseline at local_data/budget_baseline.json covering both prior databases and unknown usage. It is imported once into the persistent budget state. Missing/invalid coverage of recorded provider history blocks paid requests. A fresh database without provider history starts at zero recorded usage; other account use still needs explicit reconciliation. SQLite initialization adds budget_state and budget_reservations without changing old columns/results. See [budget details](docs/improvements/01-shared-budget.md).

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

The UI reports states for the selected checklist version: not evaluated, queued, running, complete, needs review, failed, interrupted. It initially selects the original saved checklist and retains later explicit selections in browser session storage. Select v1 to inspect the initial DEV run. Successful HTTP inference and assessment completeness are separate concepts. Unsupported factual claims needing an unavailable authoritative source must request review, rather than invent company policy.

## Scoring and evidence

The original rubric seed is preserved unchanged at `config/initial_checklist.json`. Runtime criteria are configuration-driven; eight fixed response fields are not hardcoded.

For applicable scored criteria: binary Yes/No = 1/0; numerical fraction = selected allowed anchor / maximum configured anchor. Raw points = weight × fraction. Total = 100 × applicable raw points / applicable weights. Valid N/A excludes both numerator and denominator. Flags have no numerical penalty. Unresolved criteria block the final total; zero applicable positive weight returns null with a reason.

Only the final percentage is rounded to two decimal places, using ROUND_HALF_UP (an engineering convention; the source does not prescribe tie-breaking). Sections use their own applicable weighted percentage, not an unweighted average to compute the global result. Numerical scales with nonzero minima still divide by their maximum.

Provider output is validated for exact criterion coverage, strict answer types, discrete allowed values, N/A conditions, explanations, and existing ordered evidence ranges. Schema validity and existing evidence IDs do not prove that an assessment is substantively correct. Excerpts are rendered from stored source messages, never model-generated quotes.

## Persistence and recovery

- SQLite defaults to ignored `local_data/cqa.sqlite3`; WAL and serialized write transactions protect imports/reviews/job claims.
- Identity includes dataset group and source ID. All evaluation-relevant fields are hashed. Changed content creates a revision; unchanged reimports reuse the immutable revision.
- Checklist saves create immutable complete snapshots. Original judgments are never overwritten by reviews.
- At most one output-repair call; each network request has at most two attempts. Valid server Retry-After minimums are respected; delays over 30 seconds defer the job. Batch recovery stops on provider 4xx failures. Refusals, malformed output, oversized input, outages and incomplete responses remain visible. Transcripts are never silently truncated.
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

Preflight prints configuration status and the configured spending ceiling only; it makes no provider request and does not verify budget affordability or inference. It exits nonzero for missing/unusable provider configuration. Keys and private endpoint values are never printed.

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
.\.venv\Scripts\python.exe scripts\behavior_checks.py
.\.venv\Scripts\python.exe scripts\run_dev.py --budget-usd 4.00 --checklist 1
```

Behavioral checks submit the clearly synthetic multilingual fixtures to the actual hosted provider and can incur charges; expectations are provisional agent-authored checks, not independent labels or benchmark accuracy. Their report is private under `local_data/`. These diagnostics are not a substitute for actual DEV processing.

The DEV runner retains its additional $4 CLI ceiling and now preflights through the same persistent backend budget used by UI evaluations, retries and provider checks. The reviewed opening baseline includes prior isolated-audit costs and unknown-usage reservations; new operations reserve worst-case attempts atomically and reconcile actual/unknown usage. `--only-missing` preserves existing successes. Unrelated account activity is outside this ledger. The opt-in `npm run live-smoke` makes a real paid evaluation and saves versions/appeals; ordinary `npm test` skips it. The normal backend suite explicitly rejects real OpenAI HTTP transport. No opt-in paid test was run for these improvements.

## Data handling and submission

`.env*`, local data, recordings, PDFs, databases, logs, dependencies and build outputs are ignored. Only explicitly synthetic fixtures belong in public Git. Source PDFs remain in their original supplied location; redistribution permission is not assumed. Do not expose real conversations in an unauthenticated public deployment.

The GitHub repository starts private as a reversible default. Public visibility, event submission, control-group identifier, official event timing and freeze commit must be recorded when actually performed/supplied. No event start or freeze is inferred from wall-clock time. [Demo script](docs/DEMO.md) describes the required flow and honest limitations.
