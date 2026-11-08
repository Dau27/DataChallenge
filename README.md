# Conversation Quality Analytics

**Team: Vector Field.** Organizer submission: [DEV results](results/dev/results.json), [format and control-hour procedure](docs/SUBMISSION.md).

A working Freedom Broker CQA prototype for evaluating **human operator performance** in Russian, Kazakh and English. Reviewers can trace each judgment to the conversation, challenge a criterion, and save a reasoned decision while retaining the original assessment.

**Core workflow:** import → select a saved checklist → evaluate → inspect evidence → appeal → review → recalculate and preserve the final result.

The required product workflow is implemented and tested. Repository access remains private until the owner releases it at the deadline. The real **FBroker control set has been processed:10 validated final records**, with originals retained and source-based review recorded. **Swap3 is saved but unevaluated**, awaiting further instructions. [Control report](docs/improvements/33-fbroker-control-submission.md). Organizer acceptance, public handoff and official freeze remain pending. The [presentation](docs/PRESENTATION.md) and [demo guide](docs/DEMO.md) are ready; actual spoken rehearsal is still uncompleted.

## What judges can assess

| Requirement | What the application provides |
| --- | --- |
| Configurable evaluation | Add/change criteria, wording, weights, answer types, numerical anchors and N/A rules in the UI. Preview field errors and save a new checklist version. |
| Multilingual operator assessment | Import organizer JSON or fetch a supplied dataset group. Evaluate the human operator; bot/system turns provide context. |
| Explainable results | Per-criterion answer, points, weight, reason and clickable source evidence. Missing actions cite the checked interval; N/A includes a reason. |
| Correct scoring | Deterministic weighted arithmetic, N/A redistribution, section percentages, two-decimal total and a separate critical-violation flag. |
| Appeals and review | Save a criterion-level appeal/comment. A separate reviewer action confirms or changes the answer with a reason. Recalculate locally and retain original, decision and final result. |
| Calls and persistence | Inspect transcripts and open the supplied recording player link. Saved sources, checklist versions, assessments and review history survive restart. |
| Organizer Results JSON 1.0 | Offline export/validation of all original IDs, canonical criteria, full-transcript evidence positions and honest error records. DEV65 prepared; genuine control10 pending. |

The HTML/CSS/JavaScript frontend has a separate API boundary for later Dynamics 365 adaptation. Registration is unnecessary for this prototype; appeal and review are separate actions rather than production access-controlled roles.

Additional saved-data tools include exact-run and cohort comparison, criterion breakdowns, review-priority filters, weight-impact preview, JSON/CSV export, transcript search with saved filters, printable reports and private backup/recovery. They support inspection without requiring another model evaluation.

## Run locally on Windows

Requires **Python 3.12+, Node.js 22+, npm and Git**. Use an authorized checkout or a privately supplied source copy; the repository is not being made public at this stage.

From the repository root:

```powershell
.\scripts\setup.ps1
.\start.ps1
```

Open [the application](http://127.0.0.1:8000) or [API documentation](http://127.0.0.1:8000/docs). Stop with Ctrl+C. Setup installs the pinned dependencies, builds the frontend and creates `.env` from `.env.example` only when it does not already exist. It preserves an existing configuration.

**For review without API spending**, keep `BUDGET_LIMIT_USD=0` in the ignored `.env` and restart after changing configuration. Saved-result navigation, evidence, comparisons, exports and local review do not require fresh inference. Provider checks, Evaluate and Retry can call a paid model when enabled; they are outside the present zero-spend review.

A new checkout starts without the private DEV/control payloads, database, credentials or recordings. Use an authorized private data handoff or upload a supplied organizer JSON file. An empty workspace is not a failed import or a fabricated evaluation. Committed fixtures are explicitly synthetic development cases.

New evaluations additionally require `OPENAI_API_KEY`, an accessible `OPENAI_MODEL`, identified input/output cost rates and deliberate budget authorization. `ORGANIZER_API_URL` is needed only for organizer fetching; JSON upload is also supported. Keep all actual values in `.env`, never in source or browser code. See [operations and configuration](docs/OPERATIONS.md) for manual startup, private review copies and recovery.

## Inspect a saved result

1. Select the intended dataset and checklist version in Conversations. For the existing initial DEV assessments, select **DEV / checklist v1**.
2. Open a conversation and a saved run. Inspect the operator's turns, criterion judgments, N/A explanations, section results and total. Click evidence to locate its source interval; calls also expose the supplied recording link.
3. Inspect original and effective results and the saved appeal/reviewer rationale. To exercise new appeal, decision or checklist-save actions while preserving an existing workspace, use a disposable private database copy as described in [operations](docs/OPERATIONS.md).
4. Open Compare saved runs or cohort comparison to inspect exact saved versions. An incompatible definition or withheld total does not produce a misleading numeric delta. Exports retain selected run identities and indicate the chosen basis.

These steps inspect existing data. A saved result, cached reuse or local review is not presented as a fresh model inference. Applying a newly changed criterion requires a new authorized evaluation; saving the configuration alone does not prove that step.

## Scoring rules

The initial eight-criterion rubric is in [config/initial_checklist.json](config/initial_checklist.json). Runtime evaluation follows the selected saved configuration.

For an applicable weighted criterion, Yes earns its full weight and No earns zero. A scale answer earns `weight × selected anchor / maximum anchor`. For example, dialogue management at 7/10 with weight 15 earns 10.5 points before N/A redistribution.

```text
total = 100 × sum(applicable criterion points) / sum(applicable weights)
```

Valid N/A removes the criterion's points and weight from that calculation. Round the final percentage to two decimal places. With no applicable positive weight, no total is calculated. An unresolved criterion withholds the final total. Critical errors are flagged separately without an invented numerical penalty. The excluded three-minute first-response threshold, tags and attachments are not scored.

Evidence excerpts come from saved transcript messages. Validation checks allowed answers, anchors, N/A rules and evidence ranges, but a valid reference does not by itself prove a judgment is correct.

## Verified evidence and limits

| Evidence | Recorded outcome |
| --- | --- |
| Backend acceptance | **503 passed / one private-copy case skipped** in the full guarded run; that exact private case then **passed separately** on an isolated saved-data copy |
| Frontend acceptance | **184 passed, one paid opt-in skipped**; TypeScript and production build passed |
| Installation and persistence | Actual clean setup, empty/saved-data startup, restart, backup/restore and CLI handoff passed |
| Private saved DEV results | **65 conversations: 35 RU / 15 KZ / 15 EN; 60 chats and five calls. 64 complete / one needs review** |
| Final offline recovery check | Fresh private bundle verified and restored; all **15 tables/schema and 249 historical evaluations** preserved; zero provider/network attempts |
| Required DEV submission | **65 original IDs / 64 ok / one explicit error**, validated against the new appendix and the original API transcript ordering |

Tested implementation commit **ed0b96e** adds the organizer submission adapter and fixes queue links to open the exact saved run displayed for the selected checklist. It and the DEV file were pushed to the private repository; independent advertisement, fresh fetch, complete-tree and all 163 tested source/data blob checks passed. The [publication report](docs/improvements/30-private-submission-push.md) records exact verification. The counts above are actual acceptance of these changes; no new model evaluation was run for publication. Earlier tested merge `535444d9e8e905c24413faf70f98c1b52da6eac6` retains clean-install/recovery evidence; the [updated audit](docs/audits/2026-11-08/04-appendix-submission-audit.md) records current scope and limits. The 249 historical evaluations include previous attempts and revisions; they are not 249 separate DEV conversations.

Independent judgment accuracy has **not** been measured. The offline quality report correctly remains unlabeled for 65 selected originals / 520 judgments. One call's self-introduction is unclear, so its effective total is withheld and the original retained. Saved DEV results predate the current v13 prompt; no fresh v13 or organizer-control result is claimed. The PDFs do not define a weighted project-grade formula, and earlier informal readiness estimates are not official jury scores.

### Model and cost

The provider adapter uses OpenAI Responses structured output; each result retains its actual model, prompt/configuration and usage provenance. The selected DEV65 used **gpt-4.1-mini**: **72 recorded requests**, estimated total **$0.3983244**, averaging **about $0.00613 per evaluation**, including recorded retries/repairs. The observed range was $0.0048448-$0.016662 at the saved rates. These are historical usage estimates, not a current price quote, invoice or fixed cost for every dialogue. Earlier gpt-5.4-mini vertical-slice evidence is retained in the stage reports.

Whole-evaluation accounting includes recorded requests, retries and repairs. Estimates require complete usage and identified rates; unknown usage is not treated as free. The shared budget covers UI evaluation, CLI runs, retries and provider checks. The budget is an application spending guard, not a provider account balance. **No new inference spending was incurred during final offline preparation.**

## Required result files

The organizer appendix requires **results/dev/results.json** for all65 DEV dialogs and **results/prod/results.json** for exactly10 real control chats. Both now exist in Results JSON1.0 for Vector Field: [DEV](results/dev/results.json) has64ok/one explicit unclear-call error; [PROD](results/prod/results.json) has10ok/zeroerrors. PROD uses saved effective judgments after16 source-based reviewer corrections, with every model original retained. This is not a claim of organizer labels or independent accuracy. SWAP is excluded.

Use the dedicated offline [submission commands](docs/SUBMISSION.md). Existing UI JSON/CSV downloads are archival reports and do not match the organizer contract. Both actual result files must be committed, pushed and available in the public repository before stop-code. Export/validation incur no inference cost; control assessment needs actual data and later authorized provider access/budget.

## Remaining event steps

| Item | Current status |
| --- | --- |
| Public repository and organizer link handoff | Repository stays private. DEV/PROD are prepared for private publication; owner must complete public access and organizer receipt before stop-code |
| Organizer control data and replacement-criterion challenge | FBroker10 processed and validated; Swap3 saved with zero evaluations. Additional criterion instructions and organizer acceptance remain pending |
| Official frozen commit | Await official event timing/instruction; the tested checkpoint is not an official freeze |
| At-most-five-minute presentation | Technical screen flow verified in 4:52; owner confirmed no spoken pass and paused rehearsal. Spoken timing and fresh authorized changed-criterion inference remain pending |

Optional A4/Letter and long multilingual paper-layout checks remain deferred and unverified. They do not block the specified core workflow. The [latest four-PDF audit](docs/audits/2026-11-08/04-appendix-submission-audit.md) incorporates the new appendix; earlier no-submission-schema statements predate that material. See the [control/freeze procedure](docs/CONTROL_AND_FREEZE.md).

## Tests and technical details

Ordinary checks run without paid inference:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
Push-Location frontend
npm test
npm run build
Pop-Location
```

The normal backend suite blocks real provider transport, and the paid frontend test is opt-in. Do not run `npm run live-smoke` or hosted diagnostic/batch scripts during a zero-spend check.

The app uses React/TypeScript/Vite, FastAPI/Pydantic, SQLAlchemy/SQLite and deterministic Decimal scoring. One backend process serves the compiled frontend and API on loopback. Credentials, downloaded full data, recordings, databases, private backups and source PDFs remain outside Git. Only the prescribed result summaries are prepared for repository submission under the appendix; archival review exports can contain additional private conversation content and should remain private.

For detailed evidence and development history, see [final offline preparation](docs/improvements/26-judge-readiness.md), [tested merge/handoff](docs/improvements/24-main-sprint-merge.md), [stage reports](docs/stages/README.md), [feature reports](docs/improvements/README.md) and [CURRENT_CONTEXT.md](CURRENT_CONTEXT.md).
