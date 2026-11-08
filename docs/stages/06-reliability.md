# Stage 6 — Reliability and clean start

Status: **PASS for verified local reliability/installation gate**. Full DEV terminal-state report is tracked separately in Stage 5.

Latest accepted source, 8 November: merge 535444d passed 460 backend tests in both installed environments, 182 client tests/one paid opt-in skipped, production build and actual clean setup/startup/restart. [Exact-source evidence](../improvements/24-main-sprint-merge.md). The subsequent [final offline handoff](../improvements/26-judge-readiness.md) changed documentation only and freshly verified recovery of all 15 tables/schema and 249 saved evaluations with zero provider/network/init attempts. Earlier counts below are historical. No paid inference or demo work.

Latest enhancement gate: [shared budget protection](../improvements/01-shared-budget.md) now covers UI, CLI, retries and provider checks with persistent reservations and a default zero limit. Root/isolated-source checks passed 125 backend / 14 client tests and production build without model calls. The earlier checkpoint details below are historical; current source initialization adds only the two budget tables.

Current recheck, 7 November 2026: a clean source snapshot containing the scoring fixes and recording-link correction passed the actual setup script, 94 backend tests, nine client tests, production build, pip check and compileall. It received no real credentials. Fresh home/assets/health returned HTTP 200, with zero conversations/evaluations and the original eight-criterion checklist. Missing-provider requests returned HTTP 503 without creating a result. See [zero-spend readiness](../audits/2026-11-07/06-zero-spend-readiness.md). The details below preserve earlier implementation checkpoints.

- Persistent bounded job runner, original-only cache, explicit retry, startup interruption detection, one output repair and bounded transport retry are implemented.
- Exhausted billing credit is identified and does not trigger repeated automatic retries. Refusal, output limits, malformed assessments and missing credentials never produce a fabricated score.
- Actual full-run rate limits exposed a missing batch circuit break. Fixed it: honor Retry-After, defer server delays above 30 seconds, and stop further batch submission on provider 4xx failures. Actual historical reservations now count only sent requests at their original model rates; unsent hypothetical repairs no longer consume a past-attempt reservation. Unknown usage is still reserved and reported, not fabricated as zero. Latest backend suite: **74 passed**.
- Every provider attempt records known token usage and request latency. Cost is available only with actual usage and identified configured rates; unknown usage is not free usage. The $4 DEV runner reserves worst-case retry/repair cost against the user's $5 balance.
- Review decisions rebuild effective results from immutable originals and ordered audit history inside serialized SQLite transactions. Real original/effective results and four decisions survived backend restart.
- Actual new-criterion/appeal UI integration: `npm run live-smoke` passed against the real provider and private actual DEV input. Ordinary `npm test` skips the paid test.

Clean-start verification actually performed:

1. Cloned private GitHub commit `1b61f55` into ignored `local_data/clean_start_1b61f55`.
2. Ran that checkout's actual `scripts/setup.ps1`: fresh virtual environment, complete Python lockfile install, `npm ci`, production TypeScript/Vite build. All succeeded; npm reported zero vulnerabilities.
3. Launched its fresh backend on loopback port 8001 (8000 was occupied by the real DEV run). Home, JavaScript/CSS assets and health returned HTTP 200. Fresh DB started with zero conversations, one eight-criterion rubric, and no configured provider.
4. Imported ten clearly synthetic fixtures: ten new records; second import ten unchanged; zero fabricated evaluations. Missing-provider check returned HTTP 503.
5. Fresh-checkout tests: **67 backend passed in 5.41s** (one dependency deprecation warning); **7 client passed / 1 paid live test skipped**. `pip check` reported no broken requirements.
6. Stopped the owned clean-start server. It never received the private `.env`, actual DEV payload, or model key, and made no model request.

Final source recheck: pulled pushed implementation checkpoint `799c233` into that isolated checkout; **74 backend tests passed**, production frontend build passed, **7 client tests passed / 1 paid test skipped**. The root launch script also started successfully, returned health HTTP 200 and preserved all 65 DEV states, original/effective scores and six review decisions across restart. Owned servers were stopped after verification; `.\start.ps1` reopens the local application.

Primary-source staged scan found zero occurrences of the locally configured key/signed URL/signature and no tracked private data paths. The repository remains private; public publication/submission is not claimed.

Later browser smoke: the in-app browser surface became available. Inspected queue, dataset/status filters, withheld-total detail, evidence highlighting and saved checklist versions. Verified nine fields and the genuinely new ticket-reference definition in v4. Found/fixed hidden file-input horizontal overflow; final document width equals viewport width (699px) and DEV filter shows 65 rows. Earlier Windows Chrome stop was not bypassed. No independent human reference labels, timed human presentation rehearsals or supplied control/freeze inputs are claimed.
