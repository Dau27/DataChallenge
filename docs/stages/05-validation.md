# Stage 5 — Validation

Latest scoring fix/re-audit, 2026-11-07: **65 complete accepted DEV results, 26/26 targeted provisional checks, 94 backend tests, zero independent calculation mismatches across 130 accepted original/effective snapshots**. Earlier 44/21 and 59/6 sets remain historical records. The accepted set retains 56 validated v10 runs plus eight v11 and one v12; do not claim a uniform final-prompt benchmark or independent human accuracy. See [re-audit results](../audits/2026-11-07/05-scoring-reaudit-results.md). No new product features were added.

Status: **PASS for the full DEV processing/accounting gate**. Independent human quality validation remains outstanding.

- Backend suite: latest **74 passed**, one Starlette/AnyIO deprecation warning. Includes decimal arithmetic, strict scales/N/A/flags, exact coverage/evidence, atomic imports, immutable revisions, configuration/cache changes, retry/repair bounds, refusal/output limits, quota, persistent reviews, restart, Retry-After, disposition-specific provider schemas and concurrent budget guards.
- Client suite: **7 passed**. Covers evidence range navigation, truthful answer/status display, adding a substantive criterion through the editor, draft retention, and separate reasoned review submission.
- Public fixtures contain ten explicitly synthetic multilingual behavioral cases: bot greeting, general information/adequate initial details, late verification, partial consultation versus clarity, interrupted closure, summary without goodbye, outside-company paid offer, customer insult, transcript injection, and unsupported fee claims.
- Expectations are **provisional agent-authored**, not independent human labels. Actual-provider diagnostics ran after the real slice. Final v5/gpt-5.4-mini run: ten succeeded, 13/13 provisional checks matched. Earlier v3/v4 disagreements were documented and fixed; no benchmark accuracy or independent human agreement rate is claimed.
- A private reference-selection script prepares up to five actual DEV items per language, with a development/holdout split and calls represented. Selected items have no labels and explicitly have `human_reviewed: false`.
- Final actual DEV: **65 succeeded executions, 59 complete scored assessments, 6 needs-review assessments with no final total; zero latest failed/interrupted/unstarted records**. Includes all 35 RU / 15 KZ / 15 EN, 60 chats / 5 calls.
- Independently reran the deterministic scorer and evidence-range validation against all 65 saved original snapshots: **zero mismatches/issues**. This verifies persistence/arithmetic/contracts, not semantic truth.
- Model distribution: 14 gpt-5.4-mini, 8 gpt-5-mini, 43 gpt-4.1-mini. Earlier failed/interrupted runs remain in history. Results are not presented as a single-model benchmark.
- Selected latest DEV assessment estimate: **$0.35675655 total**, approximately **$0.00549 per conversation** across that operational model mix. All recorded application evaluation usage including diagnostics, pilots and repairs: approximately **$0.683**. Failed/rejected/interrupted requests with unreported usage retain a conservative **$2.38480875 reservation**, not an asserted actual charge. The $4 guard was not exceeded.

Live access findings:

- Actual GET `/v1/models` returned HTTP 200 with the supplied key.
- Selected `gpt-5.4-mini` from that model list and verified its official Responses/structured-output support.
- Actual inference returned HTTP 429. Further safe error inspection identified `type=insufficient_quota`, `code=credit_balance_exhausted`. Provider response text and the key were not printed.
- User funding resolved the initial exhausted-credit block; actual structured access and real RU/KZ assessment slices succeeded with measured usage/cost.
- Actual primary-model limit: 50 requests/day for gpt-5.4-mini, with Retry-After 1728 seconds. Batch halted conservatively. Recovery used available gpt-5-mini after a real structured check/KZ assessment, but intermittent model_not_found responses were recorded. A real gpt-4.1-mini RU slice then succeeded; unfinished records were processed under that configured model. Every result retains its own model and rate snapshot.
- Rate/backoff recovery now honors server minimums, defers long waits, stops the batch on provider 4xx failures, and preserves actual attempt/rate reservations under the user's $5 balance. Unknown usage remains unavailable rather than zero.
- Eleven assessments initially failed semantic/schema checks after the single repair and received no fabricated scores. Tightened the generated schema to encode each criterion's allowed dispositions and their consistent value/reason types, constrain evidence IDs to the actual transcript and require resolved evidence; repair now receives safe specific validation feedback. Retried only failures; all 11 produced valid saved assessments, including genuine unresolved workflow states.
- Browser inspection confirmed the DEV filter shows 65 rows, the needs-review filter shows six, and an unresolved result withholds its total and links evidence to the source message. One unresolved contact judgment overuses review for a missing introduction that the rubric could resolve as No; model judgment quality therefore still needs independent review. No human-reviewed accuracy is claimed.
- Actual backend organizer reimport returned HTTP 200: 65 records, 0 new revisions, 65 unchanged. No records were lost or silently dropped.

Next step: reviewer resolves the six withheld totals using evidence/appropriate authority; obtain independent human reference labels if benchmarking; rehearse the presentation and wait for organizer control/freeze inputs. Browser smoke checks are now complete; broader cross-device testing is not claimed.
