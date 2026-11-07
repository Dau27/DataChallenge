# Stage 1 — Shared budget protection

Status: **PASS**, 7 November 2026. New hosted-model requests: **0**.

## Completed

- Added one persistent backend budget shared by UI evaluation, retries, provider checks and the command-line runner. Direct provider requests require a budget-backed recorder; an unreserved adapter request is rejected before HTTP.
- Enqueue uses serialized SQLite transactions to reserve the entire batch before it starts. Concurrent callers cannot reserve the same remaining funds twice. Each conversation reserves up to four attempts for network retry/output repair; access checks reserve two attempts.
- Every attempted send is recorded before HTTP and checked against its reservation and attempt count. Settlement releases unsent allowance, records known usage at the reservation's rates, and retains conservative costs for unknown usage. Restart recovery preserves started unknown requests and handles abandoned reservations. A retry after a rate/settings change must create a new evaluation rather than mix cost provenance.
- Added cache-aware read-only cost preview, a visible spending summary and HTTP 409/BUDGET_BLOCKED responses. Compatible cached reuse requires no paid reservation. Saved-result navigation, previews and review work while paid requests are paused.
- The CLI now asks the same backend budget for preflight and accounting; it no longer builds a separate main-database-only total. Backend enqueue rechecks atomically after preview, including a possible race with another caller.

## Defaults and existing history

BUDGET_LIMIT_USD defaults to **0**, so this implementation cannot silently enable paid requests. The existing .env was not edited. A later deliberate configuration change is required before new paid work. BUDGET_OVERHEAD_USD defaults to 0.10. BUDGET_BASELINE_PATH defaults to ignored local_data/budget_baseline.json; blank uses that default.

The reviewed private opening baseline reconciles both existing databases by evaluation ID, including the preceding isolated audit, actual known usage and the frozen 36-job unknown-usage reservation. Opening accounted estimates are **$4.03490090**; with the separate $0.10 overhead, combined accounting remains **$4.13490090**. This is not a bill or account balance. No new account check was performed.

Baseline coverage fingerprints the original attempt prefixes and metadata. New guarded requests have their own ledger entries; the covered history is not counted again. Changed/uncovered history or an invalid/missing baseline with prior requests blocks paid work. A fresh database without provider history starts at zero recorded usage. External/unrelated account use still requires explicit reconciliation; this application is not a provider account-wide hard billing cap. The baseline is imported once into that database's persistent budget state.

Storage adds only budget_state and budget_reservations through the existing create_all initialization; existing tables/columns and saved assessments are unchanged. A SQLite backup was made before verification. This turn exercised the additive initialization in copies and temporary databases, preserving the main database exactly. Private baseline/backup data are excluded from Git.

## Verification

The final backend suite includes **13 new budget tests**: zero-limit blocking without sends/jobs, standalone adapter rejection, two-instance concurrency, batch rollback, settlement, free cached reuse/review, unknown-cost restart retention, blocked retries, changed-rate rejection, repeated access-check accounting, crash handling, request/attempt bounds and valid/invalid historical baselines.

All **125 backend tests** passed with one existing Starlette/AnyIO deprecation warning. Real OpenAI HTTP transport is explicitly forbidden in the ordinary backend suite. Client tests cover an unaffordable operation and free cached reuse; the paid opt-in test was skipped.

Actual local HTTP against a copied DEV database returned HTTP 409 for a new uncached evaluation and provider check, without creating a new evaluation/reservation. A compatible saved v12 result preview was affordable at zero cost. All 249 copied evaluation rows and all 65 selected DEV results were retained. The real CLI was run from an isolated source copy with a dummy credential: --only-missing read 65 existing results; a regular run stopped all 65 at budget preflight. No real provider call occurred. Budget state survived a cold restart.

An initial regression run exposed an incorrect recomputation of the source hash; the guard now uses the original stored, namespaced conversation hash. Final regression tests passed. Provider payload semantics, evaluator identity and deterministic scoring formula did not change.

Next: retain the zero limit until new inference is explicitly authorized; review any new external costs before enabling it. Independent human semantic validation remains separate.
