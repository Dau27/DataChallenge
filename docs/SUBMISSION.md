# Organizer submission - Results JSON 1.0

Authority: CQA_Student_Guide_Appendix_Results.pdf, pages 1-3, supplied by the owner on 8 November 2026. This adds a required submission contract to the original guide/checklist. Registered team: **Vector Field**.

Current public scoring release: **6a3d36bb4ddadf3fb4460bd2e0f1216dc1029a89**, followed by a report-only receipt. [Stage35 verification](improvements/35-scoring-private-publication.md). All166 tested source/data files and exact DEV/PROD bytes match the fetched remote. Anonymous access is verified. Saved results remain unchanged; no paid v14 run or official freeze acknowledgment is claimed.

## Required files and current state

| Repository path | Required coverage | Current state |
| --- | --- | --- |
| [results/dev/results.json](../results/dev/results.json) | All 65 DEV dialogs: 60 chats and five calls | Committed and pushed privately in **ed0b96e**: **64 ok / one error**, remote bytes verified |
| [results/prod/results.json](../results/prod/results.json) | Exactly ten organizer control chats, including error records | Real FBroker10, all10ok/zeroerror; reviewed effective judgments privately pushed in dd6b708 and exact remote bytes verified; originals retained |

The owner expressly authorized public release, and the repository is now publicly accessible. Both real files must be committed, pushed and publicly available before stop-code; a local file or commit alone is insufficient. The owner supplied stop-code **13:00**, interpreted in client timezone **Asia/Bishkek**. FBroker access is now provided and processed; Swap3 is saved but must not be evaluated or added to PROD until further instructions. An earlier two-hour estimate is historical. Public visibility and anonymous access are verified; organizer receipt remains unconfirmed.

DEV and PROD now both exist in public main. Independent advertisement/fetch/full-tree/source checks and exact DEV/PROD byte comparisons passed at **dd6b708**; subsequent6a3d36b verification confirms owner-authorized public visibility and anonymous exact-file access. [Control publication receipts](improvements/33-fbroker-control-submission.md), [earlier code/DEV publication](improvements/30-private-submission-push.md). Organizer receipt, independent control labels and official freeze acknowledgment remain separate.

No PROD IDs, judgments or placeholder results were invented: FBroker was fetched from the supplied organizer GET and processed with the initial eight-criterion checklist. The owner authorized up to$0.86 extra estimated model cost; actual added accounting was$0.06653520. Sixteen source-based review replacements preserve all originals; they are not independent labels. [Control receipts](improvements/33-fbroker-control-submission.md). Swap3 is saved but not evaluated/exported. The DEV error preserves p4-ru-005: its reviewed self-introduction remains unclear and its total withheld. Errors must not become invented zero scores or invalid Contact=N/A.

## Exact-format export and validation

Run from the repository root with the existing Python environment. These commands only read saved data; they never load .env, initialize the app/database, fetch organizer data, start jobs or call a model.

```powershell
.\.venv\Scripts\python.exe scripts/export_submission.py export --database local_data/cqa.sqlite3 --group-id DEV --split dev --team-name "Vector Field" --checklist-id 1 --output results/dev/results.json
.\.venv\Scripts\python.exe scripts/export_submission.py validate --database local_data/cqa.sqlite3 --group-id DEV --split dev --team-name "Vector Field" --file results/dev/results.json
```

The DEV file already exists, so a repeated export to that path refuses replacement. Validation can be repeated freely. For a revised export, use a new private candidate path, validate it, preserve the old file privately and deliberately promote the reviewed candidate. Publication uses an atomic no-overwrite file operation; an incomplete temporary file is never published as results.json. The private temporary naming pattern is ignored by Git.

When the real control group has been imported and assessed, use its exact supplied identifier:

```powershell
$controlGroup = 'EXACT_GROUP_ID_FROM_ORGANIZERS'
.\.venv\Scripts\python.exe scripts/export_submission.py export --database local_data/cqa.sqlite3 --group-id $controlGroup --split prod --team-name "Vector Field" --checklist-id 1 --output results/prod/results.json
.\.venv\Scripts\python.exe scripts/export_submission.py validate --database local_data/cqa.sqlite3 --group-id $controlGroup --split prod --team-name "Vector Field" --file results/prod/results.json
```

The group above is a placeholder instruction, not an identifier to guess or execute now. The exporter refuses the wrong record count or missing model provenance instead of fabricating records. Control processing itself needs genuine input and later authorized inference; the current zero-spend instruction does not enable paid calls.

The existing ten SYNTHETIC_TEST_ONLY development records are not the organizer control set. Their count must not be used as a substitute for the ten genuinely released control IDs.

Default selection is the latest saved attempt for each latest source revision and chosen checklist. A failed latest attempt stays an error rather than silently falling back to an older success. To freeze an explicitly reviewed choice, export accepts --selection with the existing version-1 RunSelection manifest of exact evaluation IDs. It requires exactly one compatible run for every current source and never mixes groups/checklists/revisions.

The dedicated exporter reads **effective/final** judgments, including stored reviewer decisions, and preserves all originals. Its output has no extra archival fields. Existing UI JSON/CSV exports remain archival reports; **they are not the organizer format** and must not be renamed to results.json as a substitute.

## Field and scoring contract

One object per file, with schema_version="1.0", team_name, model and results. model.mode is local/external_api/hybrid; the current app's actual adapter is external_api and its recorded model names populate name. Multiple actually recorded models are listed together. Unsent failed jobs do not invent a used model name.

| Internal criterion ID | Required wire criterion_id | Weight | Permitted value |
| --- | --- | --- | --- |
| contact | contact | 10 | true / false |
| needs | discovery | 15 | true / false / null |
| identification | identification | 20 | true / false / null |
| consultation | consultation | 20 | 0 / 5 / 10 / 15 / 20 / null |
| empathy | empathy | 15 | true / false |
| dialogue_management | dialogue | 15 | 0 / 4 / 7 / 10 |
| closing | closure | 5 | true / false / null |
| critical_errors | critical | Unscored | true / false |

Internal IDs and original rubric seed remain unchanged; translation happens only at submission export. Each ok record has these eight criteria exactly once, each with value, nonempty rationale and evidence_turns. Numerical values are raw anchors: dialogue=7 means 7/10, not its weighted 10.5 points. N/A is null only for the four permitted criteria and is justified in rationale.

conversation_id is the organizer's original source ID, never the application's internal UUID. Evidence positions start at 1 in the full original transcript, including client, bot and system turns. Ranges are expanded to real positions and overlapping ranges deduplicated; no operator-only renumbering. Signed recording links and credentials are redacted from rationales; full transcripts and URLs are not appended to this file.

score.final_score is a JSON number, not a string. It matches deterministic anchor weighting, N/A redistribution and two-decimal rounding. score.critical_flag equals the critical criterion's boolean and never automatically zeroes the total. An incomplete/failed/unresolved case retains its ID, status=error, empty criteria, null score and a reason. N/A itself is not an error.

The selected checklist must map to the official eight criteria and stated weights/anchors/N/A availability. Extra nine-criterion demo configurations are not silently truncated. Use the original saved v1 for this batch; the organizer's separate criterion-replacement challenge remains a UI capability check unless they explicitly revise batch-scoring instructions.

## One-hour control window

The appendix requires ten control chats between hour 23 and stop-code at hour 24. This target allocation is an engineering plan, not a measured throughput promise:

| Window | Action |
| --- | --- |
| 0-5 minutes | Obtain exact access/group, import and confirm ten original IDs. Preserve DEV and old source revisions. |
| 5-40 minutes | With later authorized provider access/budget, preview actual costs and submit small batches (initially two), let reservations settle, then continue; monitor terminal states. |
| 40-50 minutes | Resolve legitimate retry/review issues within budget; retain explicit errors for anything that cannot be completed. |
| 50-55 minutes | Export PROD and validate exact IDs/count, eight-criterion values, evidence, totals and JSON. Revalidate DEV. |
| 55-60 minutes | Commit/push both required files, verify remote commit/file contents and public access after the owner changes visibility, record the frozen commit. |

A provider outage or missing permission must be reported honestly. Do not lose records, force uncertain judgments, retry indefinitely or substitute a saved DEV/mock result for control data. The CLI needs no code change for a new already-imported group; after freeze, keep code fixed and use the saved-checklist workflow.

## Budget planning checked without inference

Effective spending ceiling remains **0**; no settings were changed. The reviewed opening task accounting is $4.03490090 plus $0.10 overhead, or $4.13490090 conservatively against the $5 task allowance. That leaves a hypothetical $0.86509910 under that allowance, not a provider account balance or authorization to spend.

A pure calculation used the current6000-token output cap, saved historical gpt-4.1-mini rates and all60 existing DEV chat payloads with the current prompt. The ten largest conservative reservations totaled $1.2110800, above that hypothetical remainder; the two largest totaled $0.2505840, below it. These are worst-case retry/repair reservations, not expected fees or actual control quotes. Recorded DEV mean fees were about$0.00613 per evaluation, but future inputs, unknown usage and provider availability can differ.

After genuine data and separate spending authorization arrive, use the app's free preview on the actual control selections. Start with two at a time and wait for completion/settlement; retry only while the shared guard allows it. Do not disable protection, increase the total allowance automatically, change token limits without validation or interpret the quoted reservation as a charge. If even one case cannot fit, retain a truthful error rather than fabricate a result. Private budget_planning.json records zero provider/network/app initialization attempts for this calculation.

Verification and implementation evidence: [updated all-PDF audit](audits/2026-11-08/04-appendix-submission-audit.md). Core presentation: [DEMO.md](DEMO.md). Official event handling: [CONTROL_AND_FREEZE.md](CONTROL_AND_FREEZE.md).
