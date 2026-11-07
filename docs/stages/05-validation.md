# Stage 5 — Validation

Status: deterministic/integration validation passed; live semantic validation and full DEV inference remain blocked by provider billing.

- Backend suite: **66 passed in 5.80s**, one Starlette/AnyIO deprecation warning. Includes decimal arithmetic, strict scales/N/A/flags, exact coverage/evidence, atomic import failures, immutable revisions, dynamic configuration/cache changes, retry/repair bounds, refusal/output-limit handling, exhausted quota, persistent appeals, stale decisions, and restart recovery.
- Client suite: **7 passed**. Covers evidence range navigation, truthful answer/status display, adding a substantive criterion through the editor, draft retention, and separate reasoned review submission.
- Public fixtures contain ten explicitly synthetic multilingual behavioral cases: bot greeting, general information/adequate initial details, late verification, partial consultation versus clarity, interrupted closure, summary without goodbye, outside-company paid offer, customer insult, transcript injection, and unsupported fee claims.
- Expectations are **provisional agent-authored**, not independent human labels. The actual-provider behavioral runner is prepared but has not been run because the real provider slice must pass first.
- A private reference-selection script prepares up to five actual DEV items per language, with a development/holdout split and calls represented. Selected items have no labels and explicitly have `human_reviewed: false`.
- Current actual DEV state: 65 imported records, all accounted for as **not evaluated**. No completed/resolved/failed evaluation totals are invented.

Live access findings:

- Actual GET `/v1/models` returned HTTP 200 with the supplied key.
- Selected `gpt-5.4-mini` from that model list and verified its official Responses/structured-output support.
- Actual inference returned HTTP 429. Further safe error inspection identified `type=insufficient_quota`, `code=credit_balance_exhausted`. Provider response text and the key were not printed.
- Exhausted credit now produces an explicit error with no automatic retry or fabricated result. Separate temporary rate limits retain bounded retries.

Next step: fund/enable billing for the key's OpenAI project, run the first real DEV slice, inspect evidence/semantics, then run the reference diagnostics and all DEV records. No accuracy target or human agreement rate has been claimed.
