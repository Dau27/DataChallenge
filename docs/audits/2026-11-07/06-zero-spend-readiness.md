# Zero-spend readiness work

Completed 7 November 2026 after the scoring re-audit. Scope: existing recording-access bug, reproducibility, no-inference workflow checks and handoff preparation. No new product features, dependencies or hosted-model requests were added.

## What gets us closer to full readiness

The PDFs specify required behavior and event handoff, without a weighted project-grading scale. The earlier approximate 85/100 was a readiness estimate, not an official score. Completing human validation and delivery evidence is more useful than adding features or inflating that estimate.

| Gap | Work completed now | Still required |
| --- | --- | --- |
| Existing call UI used an HTML player page as audio | Removed the unsupported inline control, retained the working source-player link and absent-recording transcript fallback; two tests and actual browser check passed | Recording access may expire; audio offset mapping remains unverified |
| Latest source had not been clean-installed | Cloned the existing base into an isolated workspace, overlaid current safe source, ran the real setup script with fresh .venv/npm ci and no real .env | Verify the private checkpoint; record the actual official delivery/freeze commit when appropriate |
| Practice could consume credit or alter main data | Credential-free rehearsal helper and copied DB; actual HTTP saved-result/appeal/review/version checks, blocked inference and cold restart passed | Two spoken human rehearsals with actual timings; a new live criterion evaluation was not repeated |
| Independent human accuracy unestablished | Private source-first packet: 15 transcripts, five per language, two calls, 120 blank criterion labels; comparison results stored separately | Qualified reviewer completes/signs labels and resolves disagreements; no blind-holdout claim |
| Demo and control preparation incomplete | Concrete five-minute presenter card, blank timing records, human-review instructions and control/freeze runbook | Organizer identifier/timing, public source handoff, submission confirmation and actual freeze commit |

## Tests and commands actually run

- `scripts/setup.ps1` in ignored local_data/readiness_20261107/clean_source: fresh Python lock install, npm ci and production build passed; npm reported zero vulnerabilities. The real .env and organizer data were not copied into this source installation.
- Clean snapshot `.venv/Scripts/python.exe -m pytest -q`: **94 passed**, one existing Starlette/AnyIO deprecation warning, 7.93 seconds.
- Clean snapshot frontend `npm test`: **nine passed / one paid opt-in skipped**, 2.86 seconds. New checks cover an HTML-player recording link and absent-recording fallback.
- Clean snapshot frontend build: passed, 1.80 seconds; main-workspace build for browser verification also passed, 1.73 seconds.
- Clean snapshot pip check: clean; compileall -q backend scripts: passed.
- Cold fresh backend on port 8001: home/health/JavaScript/CSS HTTP 200; zero conversations/evaluations, one eight-criterion initial checklist. Missing provider returned HTTP 503.
- Private copied-data backend on port 8000: 65 saved DEV results complete. Added an agent-attributed technical appeal, separately confirmed the current judgment, preserved original/effective score and provider attempt list. Saved a nine-criterion rehearsal version; v1 unchanged. Fresh evaluation/provider-check endpoints returned HTTP 503 with no new evaluation row. Review and checklist survived cold restart.
- Actual local browser: source-player link present, opens a separate tab, zero inline audio controls, explanatory help present, evaluation disabled. Playback itself was not repeated; the prior audit verified the external player.
- Initial `git ls-remote origin refs/heads/main`: e84d9df063bffc413458544146a582c73cee3f23. The subsequent private checkpoint/push outcome is recorded in CURRENT_CONTEXT.md; neither checkpoint is an official freeze.
- Reviewed implementation checkpoint **6e16fdd** was committed and fast-forward pushed to the existing private repository; ls-remote matched and status was clean. A documentation-only follow-up records that result, with the tested code unchanged. Current fixes are therefore backed up in GitHub; public visibility/submission remain pending. The staged whitespace check initially caught extra EOF blank lines in seven new Markdown files; those alone were normalized before the successful check/commit.

Private scripts and raw checks are under ignored local_data/readiness_20261107. The technical rehearsal uses copied real data, not fabricated evaluations. It does not establish independent human accuracy or a five-minute spoken presentation.

## Budget and preservation

**New hosted-model requests: zero. Additional inference estimate: $0.00.** The prior $4.13490090 conservative combined accounting remains unchanged. The rehearsal server does not load the real .env, has no model/organizer credential and denies inference. Normal missing-provider checks stopped requests before provider execution. Existing real results remain labeled as saved results.

The review packet starts with all human labels blank. It contains private source transcripts and is excluded from Git. The main database and .env are preserved; checklist/review changes exist only in the rehearsal copy. Existing user work, market analysis and scoring-fix history remain intact.

Exact credential/signed-link/private-path checks passed for current source and reachable Git history; Markdown local links/whitespace and git diff --check passed. All main-database row hashes and the real .env hash match the baseline. The source code matches the clean-tested snapshot. A safe candidate source archive and per-file manifest are in ignored local_data/readiness_20261107 for review; they are not an official freeze. Owned servers were stopped; no listeners remained on 8000/8001/5173.

## Next concrete steps

1. Have a qualified reviewer complete the [human review](../../HUMAN_REVIEW.md); resolve supported corrections through the existing review workflow without model calls.
2. Speak through the [demo card](../../DEMO.md) twice and record actual timings. Saved-result practice is free; a new live criterion/control assessment requires later authorized inference.
3. Verify the recorded private checkpoint/push outcome, then complete public-repository/submission steps. No public visibility change or organizer message was performed here.
4. When official control ID/timing arrive, follow [CONTROL_AND_FREEZE.md](../../CONTROL_AND_FREEZE.md), reconcile budget and record the actual delivered/frozen commit. Do not guess those inputs or claim a guaranteed 100/100.
