# Stage 34 - automated rubric scoring corrections

8 November 2026. Repairs the judgment-generation and validation causes behind the 16 source-based control corrections. No new feature, model request, saved-result replacement or repository visibility change.

## Changes

| Error family | Corrections | Implemented repair |
| --- | --- | --- |
| Needs versus N/A | 4 | Separate a clear topic from sufficient initial facts; check newly elicited site/currency, missing request and refused diagnostic clarification |
| Dialogue anchors | 4 | Explicit customer re-asking caused by wording/order conflicts with 7/10; later clarification does not erase the 4-point event |
| Closing | 3 | Distinguish generic glad-to-help from a specific confirmed outcome or next-step recap; require farewell; an earlier ordinary answer cannot manufacture a closing recap |
| Consultation | 3 | Inventory requests, retain unanswered secondary details despite deferral, use the incorrect-key-recommendation anchor, and keep unrelated critical misconduct separate |
| Identification | 1 | Account-specific disclosure plus explicit absence of verification contradicts N/A/Yes |
| Critical disclosure | 1 | The same unverified disclosure must be considered for the separate flag, without an invented total-score penalty |

The prompt now explicitly covers these distinctions. The wire schema requests evidence and factual explanation **before applicability and decision**, avoiding an initial N/A commitment. Existing exclusive decision branches, complete transcript, evidence validation and deterministic arithmetic remain intact.

Added conservative source/answer contradiction checks. They reject conflicts and request repair; they never silently choose replacement values. Multiple detected conflicts are returned together to the existing single repair attempt. A response still invalid after repair fails without saving a score. Existing shared reservation, retry and zero-budget safeguards remain unchanged.

New semantic checks require the exact initial description, answer type, anchors and N/A condition. Renamed IDs and changed weights retain the checks; edited semantics disable assumptions about the initial rule. There are no conversation-ID overrides or lookup tables of reviewed answers. Generic RU/KZ/EN source patterns are intentionally bounded, not a complete language-understanding system.

Provenance is now prompt **literal-rubric-evidence-v14**, schema **observations-before-applicability-v8**, evidence validation **source-rubric-contradictions-v3**. Future cache identity changes; no existing evaluation, provenance or checklist is rewritten. The saved control run remains honestly attributed to v13.

## Verification actually performed

- Focused evaluator/safety/regression tests: **84 passed**. Includes 16 isolated synthetic error patterns, corrected counterparts, renamed/edited criteria, already-supplied context, ordinary follow-ups, prior verification, future checks, negated recommendations and both repair-success/failure paths.
- Final complete backend run: **538 passed / one private-copy test skipped**. External sockets and main-database initialization were blocked; both attempt counters remained zero. The earlier 532-pass run preceded the final negation/aggregation refinements and is not the final certification.
- Read-only replay on a fresh consistent private backup: **16/16 original conflicts rejected; 16/16 reviewed replacements accepted; all 10 complete effective control assessments accepted**. Each correction was isolated so another error could not mask it. No live inference occurred.
- Dependency check: **No broken requirements found**. Frontend and dependencies are unchanged; historical 184-client/build acceptance was not rerun or relabeled as new evidence.
- Preservation: every row/hash in all **15 tables and schema**, **259 evaluations**, **25 appeals**, **25 decisions**, both budget tables and **30 protected files** unchanged. Fresh private backup passes SQLite quick_check. DEV and PROD bytes match their previously published hashes; SWAP still has zero evaluations. HEAD and staged changes are unchanged.
- Authenticated read-only GitHub metadata confirms **private=true / visibility=private**. No commit, push or visibility operation was performed in this task.

The separate saved-copy cohort regression also **passed** on the fresh259-evaluation/88-source backup:22 scenarios,396 exact pair checks,226 comparisons of different runs and all15 tables/schema preserved. Its isolated copy changes only the legacy fixture's expected snapshot counts from249/75 to259/88. Provider, external-socket and main-database-initialization attempts remained zero. This resolves the unavailable-copy skip for the current saved data without altering the tracked test or main database.

Final source/history/Markdown scan passed:256 candidate files,564 then-reachable history blobs,90 Markdown files and472 local links; zero credential/private-path matches and clean diff check. Only the existing Starlette/AnyIO deprecation warning was reported by tests.

## Commands and receipts

Executed from the repository root using the existing .venv Python:

```powershell
.\.venv\Scripts\python.exe -m pytest -q backend/tests/test_rubric_contradictions.py backend/tests/test_evaluator_context.py backend/tests/test_validation_safety.py --tb=short
.\.venv\Scripts\python.exe local_data/scoring_guard_fix_20261108/run_backend.py
.\.venv\Scripts\python.exe local_data/scoring_guard_fix_20261108/replay.py
.\.venv\Scripts\python.exe local_data/scoring_guard_fix_20261108/verify_preservation.py
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe local_data/scoring_guard_fix_20261108/github_preflight.py after
.\.venv\Scripts\python.exe local_data/scoring_guard_fix_20261108/prepare_cohort.py
.\.venv\Scripts\python.exe local_data/scoring_guard_fix_20261108/run_cohort.py
.\.venv\Scripts\python.exe local_data/scoring_guard_fix_20261108/final_checks.py
```

The initial gh command was unavailable in PATH; the existing credential-safe GitHub metadata reader succeeded instead. No credential values were displayed. Private baseline/backup, JUnit, network guards, per-correction replay and preservation receipts are under ignored local_data/scoring_guard_fix_20261108. Raw transcripts and credentials remain outside Git.

## Limits and next step

This is regression verification against the same assistant-reviewed cases, **not independent labels, measured accuracy or proof that the hosted model will now produce every correct answer**. No new v14 model run is claimed. Semantic variants outside the bounded checks still depend on the provider and review workflow. The unresolved DEV call introduction remains unresolved.

The tested fixes are local and uncommitted on main, based on the last verified private publication 04e06aa. Publish them only through the existing private, tested delivery process when requested, respecting the organizer freeze. Do not regenerate submitted results, evaluate SWAP or spend on a model without a new instruction. Keep the repository private.
