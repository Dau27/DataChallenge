# CURRENT_CONTEXT — verified implementation state, 2026-11-07

## Outcome

Working local CQA application: import → immutable checklist version → real hosted assessment → source evidence → criterion appeal → separate reviewer action → deterministic recalculation → preserved original/effective results. React/TypeScript/Vite, FastAPI/Pydantic, SQLAlchemy/SQLite. No prior application existed; no user code was replaced.

GitHub repository: https://github.com/Dau27/DataChallenge (private). Source is committed/pushed in checkpoints; final documentation push is in progress at this update. No public publication, event submission or official code freeze is claimed.

All 65 actual DEV records have saved successful assessments against checklist v1:

| State | Count |
| --- | ---: |
| Complete with numerical result | 59 |
| Needs review, final total withheld | 6 |
| Latest failed/interrupted/unstarted | 0 |
| Total | 65 |

Counts verified from actual data: 35 RU / 15 KZ / 15 EN; 60 chats / 5 calls. Five original audio links are available. Transcript navigation and player/link are implemented; actual recording playback and audio-offset mapping are not claimed. No intonation/diction inference.

Ten additional clearly labeled SYNTHETIC_TEST_ONLY diagnostic records exist locally, so the all-datasets UI shows 75 conversations. Select dataset DEV and checklist v1 for the 65-record DEV result set. Dataset/status filters and withheld totals were checked in the real browser.

## Verified gates

- Stage 0 PASS: inspected repository/environment first; extracted actual organizer endpoint from supplied guide; real organizer GET and backend API import succeeded. One transcript rendered; actual structured provider request succeeded after the user funded billing.
- Stage 1 PASS: original rubric copied byte for byte; strict models and Decimal arithmetic tests. SHA-256 source/copy: 913445BC3A3BBBB486AD2C124BEEBBACCF493F23E868B4212EEC7EF648500747.
- Stage 2 PASS: actual imported conversations produced persisted structured judgments, existing ordered evidence ranges, and code-calculated scores. No fake model fallback exists.
- Stage 3 PASS: real React editor interaction saved a genuinely new ticket-reference criterion; actual provider evaluated it without changing application code. Old checklist snapshots preserved. Browser inspected all three views, saved v4's nine criteria, evidence highlighting and responsive layout; fixed hidden upload-input overflow (final document/viewport widths both 699px).
- Stage 4 PASS: actual appeal/review UI actions persisted. First original score 100.00 remains preserved; effective score is 92.31 after agent-attributed demonstration reviews. Six decisions/history survived restart. Reviewer operations make no model call. No claim of secure demo roles or independent human labels.
- Stage 5 PASS for full processing/accounting: all 65 succeeded; 59 complete / 6 needs review. Reran scorer and evidence validation on all 65 immutable originals: zero mismatches/issues. Independent human semantic validation remains outstanding.
- Stage 6 PASS: bounded jobs, caching, repair/retry, server-directed backoff, quota failures, budget guard, restart handling, clean installation, launch script and final browser checks verified.
- Stage 7 prepared: README, private GitHub source and five-minute script exist. Two timed human presentation rehearsals, public visibility/submission and independent human quality review are not performed.
- Stage 8 not reached: no organizer control identifier or official event start/freeze instruction supplied. No guessed control ID/time or falsely labeled frozen commit.

Per-stage Markdown reports: docs/stages/00-access.md through 08-control-freeze.md. Demo script: docs/DEMO.md.

## Actual verification commands and outcomes

- Initial rg/directory/ancestor AGENTS.md inspection: only MASTER_CONTEXT.md and initial_checklist.json existed; no ancestor AGENTS.md. git status initially reported no Git repository. Python 3.12.6, Node 22.11.0, npm 11.0.0 available.
- Created .venv; installed pinned requirements.in; captured full requirements.lock. npm package-lock.json pins client dependencies.
- .venv/Scripts/python.exe -m pytest -q: latest **74 passed**, one Starlette/AnyIO deprecation warning (not suppressed).
- npm test: **7 passed / 1 opt-in paid live test skipped**. npm run build: TypeScript/Vite passed. npm audit: **0 vulnerabilities**. Initial vulnerable Vite/Vitest pins were upgraded to compatible 6.4.5/4.1.12.
- npm run live-smoke: **1 passed** against the actual local API, actual DEV input, actual hosted provider and persistent database. Passed again with final gpt-4.1-mini/schema v2 (8.86s test duration). Adds substantive criterion, evaluates it, appeals/reviews original, reloads saved results. This is a real-network DOM integration test; later browser smoke was also completed.
- Fresh clone of GitHub checkpoint 1b61f55 under ignored local_data/clean_start_1b61f55: ran its actual scripts/setup.ps1; fresh Python lock install, npm ci and build succeeded. Cold backend on port 8001 returned home/assets/health HTTP 200. Empty DB/initial eight criteria verified. Imported ten synthetic fixtures, then ten unchanged; missing-provider HTTP 503 and no fake assessment. Fresh environment: 67 backend tests then-current, 7 client passed/1 live skipped, pip check clean. Latest source recheck follows final code push.
- Actual POST /api/import/organizer with DEV: HTTP 200, 65 validated, 0 new revisions, 65 unchanged. JSON and API share the parser.
- scripts/select_reference.py: private selection of 15 actual DEV examples, 9 development/6 holdout, two calls. No labels; all human_reviewed false.
- scripts/behavior_checks.py with gpt-5.4-mini: final prompt v5 run **10 succeeded / 13 of 13 provisional checks matched**. Expectations are agent-authored diagnostics, not human ground truth or accuracy. Earlier v3/v4 disagreements were documented, not hidden.
- scripts/run_dev.py --budget-usd 4.00 --checklist 1 --only-missing: final report all 65 succeeded, no budget/provider stop. Existing successes retained their original model metadata.
- Independent saved-data rescore: 65 validated, zero mismatches/issues. Private report local_data/final_DEV_verification.json.
- .\start.ps1 -SkipBuild: actual launcher started the app on port 8000. After restart: 65 succeeded, 59 complete/6 needs review; original 100.00/effective 92.31/six decisions preserved; zero queued/running jobs. Owned servers were then stopped for teardown. Run .\start.ps1 to reopen.
- compileall, pip check and git diff --check passed. Exact local key/signed URL/signature and tracked-private-path scans passed before checkpoint pushes; final scan repeated at final push.

## Provider, cost and recovery provenance

Current local provider: OpenAI Responses, gpt-4.1-mini, no reasoning parameter, max output 6000, concurrency 2, prompt operator-context-evidence-v5, schema dynamic-disposition-evidence-v2. Full transcripts and saved rubric are supplied as untrusted conversation data. No tools, hidden reasoning request, model arithmetic, or silent truncation.

Latest DEV model distribution: 14 gpt-5.4-mini, 8 gpt-5-mini, 43 gpt-4.1-mini. This operational mix is NOT a single-model benchmark. Every assessment stores its own model, prompt/schema/settings, rates, usage and attempts.

Identified standard text rates verified from official model pages: gpt-5.4-mini $0.75/$4.50, gpt-5-mini $0.25/$2.00, gpt-4.1-mini $0.40/$1.60 per million input/output tokens. All input at uncached rate gives a conservative estimate, not an invoice.

- Selected latest DEV assessments: $0.35675655 total, approximately $0.00549 per conversation across the actual model mix.
- All recorded known application evaluation usage including pilots/diagnostics/repairs/latest live smoke: $0.68292515.
- 36 historical jobs have unreported usage; conservative budget reservation is $2.38480875, NOT an asserted charge or zero cost. Plus $0.10 overhead reserve, the guard remained below $4 against the authorized $5 task budget. Unrelated account usage is outside this guard.

Actual failures handled honestly:

1. Initial organization ID was rejected as a credential. Later real key authenticated /v1/models, but inference returned credit_balance_exhausted/insufficient_quota. User funding restored access.
2. Primary gpt-5.4-mini reached actual RPD 50 (Retry-After 1728s). First full pass: 14 succeeded, 19 failed rate-limited, 32 not started. Preserved report; did not fill scores. Fixed server-directed backoff and batch circuit breaker.
3. gpt-5-mini passed real checks/KZ assessment but returned intermittent model_not_found. Preserved failures and one interrupted in-flight job during restart; configured available gpt-4.1-mini after a genuine successful RU assessment.
4. Eleven gpt-4.1-mini assessments failed validation after one repair. Schema v2 encodes allowed per-criterion dispositions, consistent value/reason types, actual evidence-ID enums and resolved-evidence minimums; repair receives safe specific feedback. Retried only unfinished items; all 11 saved valid assessments. Old failures remain inspectable.
5. Historical reservations use actual SENT attempts at ORIGINAL model rates/settings. At most two new jobs are submitted after reserving both worst-case four-attempt bounds. Unknown usage is not called free.

## Semantic / external limitations

- Structural/schema/evidence-ID validity does not prove judgment truth. First live pilot over-awarded needs and closing; original preserved, prompt clarified, explicitly agent-attributed demonstration reviews recorded.
- Some remaining needs-review labels can be overconservative: one contact finding cites missing introduction, which the rubric could resolve as No from transcript facts. Review UI can resolve it. No independent human accuracy, policy verification or automatic disciplinary decision is claimed.
- Real call recording links exist; player/link and transcript inspection implemented. Actual playback/seek alignment not verified.
- Initial Windows Chrome Computer Use stopped on URL-confidence enforcement. Later the supported in-app browser became available, and app smoke/read-only account checks completed there. No bypass of the Windows block occurred.
- Separate user-requested account check found complimentary-daily-token enrollment in the signed-in UI; exact allowance was not displayed. Account cost API returned 403. Private account observations are only in ignored local_data/account_check_private.json. User then requested logout: confirmed logout and verified a protected billing route showed the email sign-in form. No account privacy setting/payment/access changes were made.
- No control data, official freeze, public deployment/publication or event submission is claimed.

## Next concrete step

Run .\start.ps1, select checklist v1 and dataset DEV, and review the six withheld totals with source evidence and appropriate authority. Then perform independent reference review and two timed presentation rehearsals. When organizers supply control/freeze inputs, import that exact group through the existing UI and record the actual final frozen commit; do not patch code/prompts after a real freeze. Keep private .env, payloads, recordings and SQLite untracked.
