# Stage 2 — Persistent evaluation slice

Status: **PASS**. Real imported conversation produced a saved assessment, existing evidence ranges, and deterministic backend score.

- Actual DEV payload was validated with the shared parser and imported into local SQLite: 65 new immutable revisions, 0 dropped records. Inspected a RU chat, KZ chat, EN chat, and real call with original timestamps.
- Added SQLAlchemy persistence for conversation revisions, complete checklist versions, evaluation jobs, original/effective results, appeals, and review decisions.
- Added a real OpenAI Responses REST adapter, with a response schema generated from the selected complete rubric. Full transcripts are sent as untrusted data; no model arithmetic or model-written evidence excerpts are accepted.
- Added semantic validation, a single output repair, at most two network attempts per request, explicit refusal/incomplete/failure states, token-attempt accounting, and no fake fallback.
- Added bounded persistent jobs, compatible-original cache reuse, explicit retry, and interrupted-job detection on restart.
- Added typed API operations for access checks, import, transcript inspection, versions, evaluation, appeal, and reviewer decisions. Server fetches only the configured organizer endpoint.
- The initial organization identifier was correctly rejected as a credential. The user subsequently saved an actual key: model listing authenticated (HTTP 200), but inference returned `credit_balance_exhausted` / `insufficient_quota` (HTTP 429). Selected available/documented `gpt-5.4-mini`; real inference still requires funded provider billing.
- The supplied NVIDIA link is a Brev GPU console. Official docs describe GPU/server credit usage, not OpenAI authentication. Browser inspection was blocked by Computer Use because the current Chrome URL could not be verified; browser interaction stopped. No GPU was provisioned and no credit expenditure was claimed.

Command actually run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Outcome: **50 passed in 5.38s**, with one dependency deprecation warning. Integration tests inject a test-only HTTP transport and synthetic transcripts into temporary databases. They do not prove live model quality.

Verified synthetic integration paths: evaluation → evidence validation → deterministic score → saved original → appeal → reviewer replacement → recalculated effective score → restart → preserved history. Changed rubric adds a schema property and misses the old cache. Cached results never copy human decisions.

Later real acceptance: after the user funded API billing, structured access and actual DEV assessment succeeded. A refined RU slice saved score 92.31, 3347 input / 1088 output tokens, one request, estimated $0.00740625 from the identified standard model rates. Initial semantically weak pilot outputs were preserved, not hidden; later prompt changes/agent-attributed reviews are documented in CURRENT_CONTEXT.md. All numerical results are from backend arithmetic, not the model.
