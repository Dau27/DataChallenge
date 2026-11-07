# Current implementation context — 2026-11-07

## Latest state (authoritative; historical checkpoints follow below)

Working React/TypeScript + FastAPI/Pydantic + SQLAlchemy/SQLite application. Real organizer import, real hosted evaluations, transcript evidence, dynamic saved checklist versions, appeals, and persistent original/effective results are implemented and exercised.

- GitHub: private https://github.com/Dau27/DataChallenge . Domain checkpoint pushed as `ec3cbb4`; later implementation push pending at this checkpoint. No public publication/event submission claimed.
- Actual DEV: 65 imported records, 35 RU / 15 KZ / 15 EN; 60 chats / 5 calls. Unchanged reimport: 0 new / 65 unchanged. Private payloads, signed endpoint, key, SQLite and extracted PDFs are ignored.
- Real OpenAI key now authenticates. Initial `credit_balance_exhausted` / `insufficient_quota` block was resolved by user funding. Structured provider check succeeded: 38 input / 13 output tokens.
- Model: `gpt-5.4-mini`, verified in actual model list and official docs. Identified standard-rate estimates configured locally: $0.75/million input, $4.50/million output. All input charged at the uncached rate is a conservative estimate, not an invoice.
- User has only $5. `scripts/run_dev.py` guards at most $4 application spending, includes previous evaluation/diagnostic usage, reserves worst-case four-attempt cost before each new job, and leaves overhead headroom. This does not control unrelated account usage.
- Current evaluator: prompt `operator-context-evidence-v5`, medium reasoning, 6000 maximum output tokens, concurrency 2. Every prompt/settings change invalidates cache. Old assessments/versions preserved.
- Local server command: `.venv/Scripts/python.exe -m uvicorn backend.app.main:create_app --factory --host 127.0.0.1 --port 8000 --no-access-log`. Local app serves at http://127.0.0.1:8000 . Restarted after prompt/settings changes.

### Current gates

| Stage | Observed acceptance |
| --- | --- |
| 0 access | PASS: actual DEV, actual transcript rendered in DOM component integration, actual structured provider request succeeded. |
| 1 domain | PASS: initial 32 arithmetic/validation tests; broader backend suite 66 passed before the new budget test. |
| 2 real slice | PASS: saved real RU assessment, valid evidence IDs, code-computed score. Refined run 92.31, 3347 input / 1088 output tokens, estimated $0.00740625, one request. |
| 3 UI/config | PASS functional DOM/API integration: added a genuinely new ticket-reference criterion through React editor, saved immutable version, actual model evaluated it as No. No application-code change. Visual/browser QA is separate and unverified. |
| 4 appeals | PASS: real persisted agent-attributed reviews through React detail UI. Original 100.00 preserved; effective 92.31. Review made no model request. History remains inspectable after backend restart. |
| 5 validation | IN PROGRESS: full DEV processing pending. Ten synthetic real-provider diagnostics executed; v4 matched 12/13 provisional checks, with a content-completeness/clarity disagreement. v5 rerun running. Labels are agent-authored, not human ground truth. |
| 6 reliability | Retry/repair/cache/restart/usage/quota tests pass. Final clean install and lockfile/build verification pending. |
| 7 demo | README, launch scripts, five-minute script prepared. Two timed human presentation rehearsals/public submission not performed. |
| 8 control/freeze | Not reached: no organizer control identifier or official event start/freeze supplied. No guessed dates/IDs/frozen commit. |

### Latest checks actually run

- Backend: `.venv/Scripts/python.exe -m pytest -q` → **66 passed in 5.35s**, one Starlette/AnyIO deprecation warning. New budget test added afterward, rerun pending.
- Frontend: `npm run build` passed; `npm test` → **7 passed** before adding opt-in live test. `npm audit` → **0 vulnerabilities** after compatible Vite 6.4.5 / Vitest 4.1.12 upgrades.
- `npm run live-smoke` → **1 passed in 8.69s**, actual local API/DEV/provider/database and React DOM interactions. Earlier attempts failed on test-origin setup (before mutation), then on a multiple-match final assertion after real workflow completion. Fixed and reran. This is not visual/browser verification.
- `scripts/behavior_checks.py`: v3 10 succeeded / 11 of 13 provisional matches; v4 10 succeeded / 12 of 13. v5 currently running. No benchmark accuracy or independent human agreement claimed.
- `scripts/select_reference.py` → 15 private examples: 9 development / 6 holdout, two calls; all `human_reviewed: false`, no labels.
- `python -m pip check`: no broken requirements. `compileall`, `git diff --check`, PowerShell AST parsing of setup/start scripts passed.

### Limitations and next concrete steps

- First real pilot was structurally valid but over-awarded needs/closing. Kept it immutable; refined prompt and performed explicitly agent-attributed demonstration reviews. Structural evidence validation is not proof of semantic truth.
- Computer Use stopped Brev console inspection because Chrome's URL could not be verified. Browser interaction stopped and completion summary sent. No alternative UI automation bypassed the block. Local preview opening was queued, not visually verified. No GPU/Brev credits/access changes were made; user chose hosted OpenAI key.
- No independent human reference labels, fabricated policies, audio offset mapping, model accuracy claim, public submission or freeze claim.
- Latest additions: v5 hosted diagnostics finished with all 10 executions succeeded and 13/13 provisional checks matching. Backend now **67 passed in 5.45s**, including the budget-bound test. Actual restart check preserved original 100.00, effective 92.31, four appeals and four decisions. Staged scan found no private values or private data paths.
- Running: `scripts/run_dev.py --budget-usd 4.00 --checklist 1` on all 65 real DEV records. Final build/client tests are running. Next: collect actual full-run statuses/cost; clean-install from safe pushed source; update reports and push.
- Remaining external/manual items: browser visual review, independent human semantic review, timed presentation rehearsals, public submission choice, organizer control/freeze inputs.

## Historical checkpoints (superseded by latest state above)

## Verified starting state — 2026-11-07

- Read `MASTER_CONTEXT.md` and `initial_checklist.json` before implementation.
- Repository directory contained only those two files. `git status --short` reported that this is not a Git repository. No existing application or user edits were replaced.
- No applicable ancestor `AGENTS.md` found. Python 3.12.6, Node 22.11.0, npm 11.0.0 and Git are available.
- No provider key/model or organizer endpoint is present in the process environment. No `.env`, PDFs, saved DEV JSON, or recordings were present in this directory. No real transcript or live inference has been obtained.
- User has been asked to configure the ignored `.env` or identify private local inputs. Implementation continues independently; missing access does not authorize synthetic live results.
- Checked official OpenAI Responses structured-output documentation: `https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses` and `https://developers.openai.com/api/reference/resources/responses/methods/create`. Adapter will use REST `text.format` with generated JSON Schema, `store: false`, no tools, and backend arithmetic. No model identifier or prices are assumed.

## Acceptance gates

- Stage 0 access: BLOCKED for real data/provider; environment inspection complete.
- Stage 1 domain: PASSED, 32 deterministic tests; see `docs/stages/01-domain.md`.
- Stage 2 real vertical slice: NOT VERIFIED; depends on real data and provider credentials.
- Later stages: not yet verified. No tests or live calls claimed as passed.

## Commands actually run

- `rg --files ...`, `Get-ChildItem -Force`, `Get-Content MASTER_CONTEXT.md`, `Get-Content initial_checklist.json`, ancestor `AGENTS.md` lookups.
- `git status --short` → no Git repository.
- `python --version`, `node --version`, `npm --version`, `python -m pip --version` → available.
- `python -m pip show fastapi pydantic sqlalchemy httpx openai pytest uvicorn python-dotenv` → base environment has FastAPI/Pydantic/SQLAlchemy/httpx/uvicorn; other packages absent. Isolated environment will be used.
- Environment inspection printed candidate variable names only, never secret values.

## Next concrete step

Create isolated dependencies, copy the original rubric unchanged to `config/initial_checklist.json`, implement strict scoring/import models, and run the arithmetic/validation gate before implementing evaluation.

## Update — domain gate / GitHub / source documents

- Created private repository `https://github.com/Dau27/DataChallenge` via the authenticated GitHub API (HTTP 201); credential was obtained in memory from Git Credential Manager and was not printed or written. Private visibility is the reversible default; no public submission claimed.
- User supplied the three PDF paths in Downloads. Original PDFs remain outside the repository. Extracted text and links are stored under ignored `local_data/source_review/`. Guide and checklist contents agree with the initial seed. Background PDF extraction succeeded, but console printing hit a Windows encoding error; rerun with UTF-8 before relying on its contents.
- Created `.venv`; `python -m pip install -r requirements.in` succeeded. Captured full dependency pins in `requirements.lock`.
- Rubric source/copy SHA-256 are identical: `913445BC3A3BBBB486AD2C124BEEBBACCF493F23E868B4212EEC7EF648500747`.
- Implemented strict rubric/import/assessment contracts and decimal scoring. First scoring run: 31 passed, 1 failed because a test compared `60.0` to the string `60`; arithmetic was correct. Changed assertion to Decimal equality; rerun pending.
- Organizer DEV link was found in the guide annotation; private endpoint extraction and access check are next. No provider credential found yet.

## Access/domain verified outcome

- `.venv/Scripts/python.exe -m pytest backend/tests/test_scoring.py -q` → 32 passed in 0.12s after correcting the numeric-format assertion.
- Actual organizer GET → HTTP 200, 65/65 records; language counts RU 35 / KZ 15 / EN 15; 60 chats / 5 calls. Stored under ignored `local_data/dev.json`; signed endpoint in ignored `.env`.
- Read the background PDF after enabling UTF-8 output; it is company context only, not policy authority.
- Stage reports: `docs/stages/00-access.md` (provider/display still pending), `docs/stages/01-domain.md` (passed).
- Next: persistent immutable imports, generated-schema evaluation adapter, bounded jobs and transcript/result UI. Real evaluation remains blocked by missing OPENAI_API_KEY and OPENAI_MODEL.

## Update — persistent backend and real import

- First stage checkpoint committed/pushed to private GitHub `main`: `ec3cbb4`.
- Actual DEV import using the implemented `ImportEnvelope`/`import_payload`: 65 created, 0 unchanged/dropped. RU/KZ/EN chat samples and a call inspected; timestamps preserved (including 7-digit ISO fractional seconds).
- Implemented `config.py`, SQLAlchemy database, importer, provider adapter, jobs, review service, and FastAPI app factory/API. One local process, bounded thread concurrency; no Redis or mock endpoint.
- `.venv/Scripts/python.exe -m pytest -q` → **50 passed in 5.38s**, one Starlette/AnyIO deprecation warning. Scoring + synthetic HTTP integration tests cover revisions, atomic failures, caching, retries, generated schemas, persistent appeals/reviews, restart, and absent credentials.
- User put an organization ID in `OPENAI_API_KEY`; detected by prefix without exposing the value. No real provider request sent. `OPENAI_MODEL` remains empty.
- User supplied a Brev organization-console link. Opened official NVIDIA docs. Brev credits fund GPU compute/storage; using them requires an actual inference server. Computer Use blocked console inspection because it could not verify Chrome's current URL; stopped browser interaction and sent its completion summary. No provisioning, access changes, billing actions, or credit use performed.
- `docs/stages/02-evaluation-slice.md` records implemented scope and the blocked real-inference gate.
- Frontend React/TypeScript views implemented; dependency installation/build and browser verification still pending. Next concrete step: run frontend build/tests, serve the application, verify real transcript display and configuration/review UI, document all remaining live-access limitations.
