# Local operations

This is the technical companion to the [judge-facing README](../README.md). Current owner instructions keep repository access private, paid inference paused and the presentation deferred. Organizer control data are unavailable.

## Configuration and startup

The ignored `.env` is loaded locally. Environment variables take precedence. `.env.example` lists every supported setting and starts with `BUDGET_LIMIT_USD=0`. Setup preserves an existing `.env`; it does not reset that file's budget. Restart the backend after changing settings.

If PowerShell script policy blocks the launch scripts, use these equivalent commands from the repository root without changing machine policy:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
if (-not (Test-Path -LiteralPath '.env')) { Copy-Item -LiteralPath .env.example -Destination .env }
Push-Location frontend
npm ci
npm run build
Pop-Location
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:create_app --factory --host 127.0.0.1 --port 8000 --no-access-log
```

The conditional copy preserves any existing `.env`. A credential-free application can start with empty provider configuration. To enforce a zero-spend process, set the budget to zero; do not run provider-access checks or evaluation commands.

Use one Uvicorn process: the persistent job runner is designed for one application process. Frontend development uses `npm run dev` in frontend; Vite's port 5173 proxies `/api` to the backend on 8000. Normal built usage only needs port 8000. Stop owned servers with Ctrl+C.

The [preflight script](../scripts/preflight.py) reports local configuration and whether the database file exists. It makes no provider request and prints no key or signed endpoint. Missing provider configuration returns exit 1; this is expected for credential-free inspection, not a live-access test.

## Inspect a disposable private workspace

Reviewing saved results does not require paid inference. Appeals, decisions and checklist saves write local data; use a copy to exercise them while preserving an existing workspace.

From the repository root, choose new private paths. The following commands refuse an existing bundle or recovery target:

```powershell
.\.venv\Scripts\python.exe scripts/workspace_backup.py create --database local_data/cqa.sqlite3 --destination local_data/review-bundle
.\.venv\Scripts\python.exe scripts/workspace_backup.py verify --bundle local_data/review-bundle
.\.venv\Scripts\python.exe scripts/workspace_backup.py restore --bundle local_data/review-bundle --target local_data/review.sqlite3 --active-database local_data/cqa.sqlite3
```

Use the actual configured active database path when different. Restoring never replaces the active file. Verify the copy, then start it in a separate PowerShell session with explicit process-local settings:

```powershell
$env:DATABASE_PATH='local_data/review.sqlite3'
$env:OPENAI_API_KEY=''
$env:OPENAI_MODEL=''
$env:ORGANIZER_API_URL=''
$env:BUDGET_LIMIT_USD='0'
.\start.ps1 -SkipBuild
```

Stop this server and close that shell before reopening the normal workspace. Do not reuse an already occupied port. This process cannot perform new provider evaluations; it can inspect saved runs and save local review/checklist changes. Recorded results retain their provenance. Nothing here grants a missing control dataset or creates new inference evidence.

Bundles are unencrypted full private SQLite copies, including transcripts and recording URL references. They exclude `.env`, external budget-baseline files, media, archived references and browser filter presets; preserve those separately. Keep bundles under ignored `local_data` or another protected private directory. Checksums detect damage relative to a trusted manifest, not malicious replacement of both files. See [backup/recovery limits](improvements/21-backup-recovery.md).

## Data import and offline reports

With an authorized saved organizer JSON file:

```powershell
.\.venv\Scripts\python.exe scripts/import_json.py local_data/dev.json
```

This writes imported source revisions to the configured database but performs no inference. Unchanged reimports are idempotent; changed content creates a revision. Organizer fetching additionally needs the private endpoint and exact supplied group identifier. Do not guess a control group.

The [quality-report command](improvements/23-offline-quality-report.md) reads explicit saved originals and optional separately identified references. It needs no server, credentials, database initialization or model call. Use real saved evaluation IDs in a selection manifest and a new output path. Without independent labels it reports coverage with metrics unavailable; archived agent judgments or reviewer changes are not automatically ground truth.

## Persistence, scoring and budget behavior

- The default database is ignored `local_data/cqa.sqlite3`. SQLite WAL and serialized write transactions protect imports, review decisions and job claims. Old source revisions, full checklist snapshots and original judgments are retained.
- The cache includes source content, full checklist, prompt/schema/scoring versions, provider/model and generation settings. Only original assessments are cached; compatible reuse is labeled. A changed configuration requires a new evaluation rather than silently reusing an incompatible result.
- Work concurrency defaults to two. Startup marks abandoned running jobs interrupted and can resume queued jobs; a zero budget and absent credentials prevent new paid requests. Retry preserves previous attempts. Transcripts are never silently truncated.
- The provider adapter uses Responses JSON Schema with no tools and `store: false`. There is at most one output-repair request and at most two transport attempts per request. Long Retry-After delays defer jobs; provider 4xx failures stop batch processing. Refusals, outages and malformed/incomplete output remain visible.
- Scoring uses Decimal. Only the final percentage is rounded to two decimals with ROUND_HALF_UP, an engineering tie convention not prescribed by the PDF. Section percentages use their own applicable weights; the global score is not the unweighted section average. Nonzero-minimum scales still divide by their configured maximum.
- Cost requires actual complete token usage, input/output rates and an identified rate source. Recorded requests, retry/repair attempts and latency remain attributable. Unknown usage is not free usage. Historical rates are preserved rather than silently replaced with today's prices.
- Shared persistent reservations cover UI, CLI, retry and provider checks. The private opening baseline reconciles prior/unknown application usage; invalid or incomplete coverage blocks spending. A fresh database has no recorded history. External account activity is outside this ledger. [Budget implementation](improvements/01-shared-budget.md).

## Saved-data tools

The queue reports state for the selected checklist: not evaluated, queued, running, complete, needs review, failed or interrupted. Select exact v1 for the original DEV set; later explicit selections persist in browser session storage. Successful HTTP inference is distinct from a complete assessment.

Run comparison fixes source-revision identity and independent original/effective bases. Incompatible definitions and missing totals do not produce numeric deltas. Cohorts show coverage and compatible transitions before exact-pair drilldown. Weight-impact previews change weights for fixed saved judgments; they are hypothetical calculations, not new assessments.

JSON/archival CSV retain saved identities and original/effective review context; simple CSV provides criterion rows. Selected export is bounded to 100 exact runs. Excerpts require explicit selection, but explanations/comments may already contain source text. Credentials/recording URLs are excluded or redacted and CSV formula protection applies; exports still need private handling. Search is literal with speaker/filter controls; saved filter presets are browser-local. Print reports use isolated saved packets; A4/Letter and long multilingual paper QA remain deferred and unverified.

Paid scripts such as live_slice.py, behavior_checks.py, run_dev.py and `npm run live-smoke` are excluded from the present offline final stage. Model access, rates, allowed data handling and a positive spending ceiling require a deliberate later configuration. The documented CLI DEV ceiling is an additional guard, not a provider balance.
