# Market feature options for the current CQA application

Implementation follow-up, 7 November 2026: the user selected the first three stages, now implemented and tested with zero inference spend. See the [comparison, export and search stage reports](improvements/README.md). The research-only statements below describe the earlier checkpoint; the optional later features remain proposals. Demo execution remains deferred.

Research date: 7 November 2026, Asia/Bishkek. Inspected repository: ec4c943. This refresh examines ten representative platforms through official product/help documentation and updates the [earlier market survey](MARKET_ANALYSIS.md) for the features we have since implemented.

**Recommendation: add saved-run comparison and evidence exports first, then transcript-text search with saved filters.** All three can use real stored data with zero additional inference and fit the existing architecture. Weight-impact simulation and criterion breakdowns are useful follow-ons. Policy-grounded evaluation is promising later, when approved documents and an authorized inference test are available.

This report is analysis and a proposed sequence, not a claim of implemented features. No code, scores, model requests or demo work were performed. The manual reference-labeling exercise remains archived. These are product improvements, not new submission requirements or guaranteed grading points.

## Market capabilities and approaches

Features below are documented vendor capabilities. Transfer recommendations are our engineering inference; proprietary internals and accuracy claims were not independently tested.

| Platform | Documented approach | Transfer to our product |
| --- | --- | --- |
| **Zendesk QA** | Conversation workbench with saved filters, feedback and disputes; calibration is separated from operational scores. Its documented review-export API excludes voice transcripts/dashboard data. [Conversations](https://support.zendesk.com/hc/en-us/articles/7043661945370-Using-the-Conversations-view), [calibration](https://support.zendesk.com/hc/en-us/articles/7043724530842-Setting-up-calibration-in-Zendesk-QA), [export](https://support.zendesk.com/hc/en-us/articles/7043724806810-Exporting-data-from-Zendesk-QA) | Saved views and portable result reports. Preserve the distinction between operational results and experimental/reference comparisons. No mandatory calibration program is needed. |
| **NiCE CXone** | Configurable Auto Score prompt profiles, testing on up to five transcripts, and publication before live selection; the platform manages the model. [Configuration workflow](https://help.nicecxone.com/content/genaiprompteditor/configureqmautoscoreprompt.htm) | Controlled configuration and visible version changes. We already have immutable versions/structural preview; compare saved outcomes next. New semantic tests still require inference. |
| **Amazon Connect Customer** | Versioned forms, sections/questions, weighted scoring, preview/validation/activation and analytics/GenAI automation. Model-version selection is associated with form versions in the documented workflow. [Evaluation forms](https://docs.aws.amazon.com/connect/latest/adminguide/create-evaluation-forms.html) | Keep evaluation configuration/provenance explicit. A fixed-judgment weight simulation is a useful derivative design, not a free new semantic evaluation. |
| **Observe.AI** | Evidence-backed Auto QA, keyword/phrase/logic rules, disputes and staged automation through suggestions, form completion and submission, connected to coaching. [Auto QA](https://www.observe.ai/post-interaction/auto-qa) | Evidence and reviewer control already overlap with our product. Improve inspection/reporting before considering a larger visual rule builder. |
| **Level AI** | Custom/hybrid scorecards, timestamped evidence and reasoning, reviewer corrections and performance drill-downs; it describes a proprietary QA-GPT model approach. [Quality assurance](https://thelevel.ai/product/quality-assurance-contact-center) | Preserve the finding → source → correction path. Our unresolved state and original/effective history are a sound foundation; no provider replacement is needed for these improvements. |
| **CallMiner** | Ingestion and conversation analytics with search/filtering/classification, quality scoring and coaching. ASR feeds searchable text alongside digital interactions. [Conversation analytics](https://callminer.com/conversation-analytics/conversation-analytics) | Search the supplied transcripts and open exact matches. Literal retrieval does not require new transcription, embeddings or a generative search service. |
| **evaluagent** | Context Engine associates company information and uploaded policies/knowledge with scorecard items. [Context Engine](https://www.evaluagent.com/news-press/evaluagent-launches-context-engine/) | Approved, versioned policy excerpts can support factual judgments. Company background alone cannot establish account/fee rules. |
| **Verint** | Form/question validation, form conversion and answer validation across conversation, screen and CRM information; results feed operational workflows. [Automated QM guide](https://www.verint.com/guides/automated-quality-management/) | Separate conversation evidence from authoritative business/account facts. Only available approved sources can supply that authority; do not reconstruct a CRM to imitate the suite. |
| **Kaizo** | Evidence-linked coaching cards drafted from ratings, edited by managers, with agent responses and follow-up history. [Coaching workflow](https://www.kaizo.com/platform/coaching/) | Later, tie reviewed recommendations to actual findings. Automatic drafting would add inference; inspection/export is the better first investment. |
| **Cresta** | Behavior/process/outcome evaluation, coaching connections, human calibration and appeals; broader capabilities include real-time guidance and outcome analysis. [Quality management](https://cresta.com/cresta-quality-management) | Source-linked follow-up can be incremental. Custom models, live assistance and outcome correlations require data/integration work beyond the best immediate additions. |

Sources were checked on the research date. The Zendesk export article's indexed official content was readable, but direct opening redirected to sign-in; authenticated access/plan eligibility was not tested. No vendor trial, account connection or customer-data upload was used. Features may depend on license/region. Interaction coverage is not accuracy, and these sources establish no RU/KZ/EN benchmark for our rubric.

The main market pattern is a complete loop: configurable evaluation → evidence → review/correction → retrieval/reporting → follow-up. We already implement the central evaluation/review loop. The most practical expansion is to make stored results easier to inspect and use.

## Repository baseline: avoid duplicating working features

Already implemented: immutable transcript/checklist snapshots; RU/KZ/EN assessment; strict evidence references; Decimal scoring and N/A redistribution; separate critical flags; source-linked explanations; N/A/missing-basis reasons; appeals/reviews/history; recording links; budget reservations/preflight; checklist differences/field errors; pending-appeal/critical filters; dataset/language/channel/status filters and **conversation-ID search**.

The detail view already selects one saved run and inspects its original/effective answers. The editor already previews configuration changes. Neither currently provides a two-run comparison or a weight-based score simulation. No download/export route or transcript-text search is present in the inspected API/UI.

Evidence: [snapshots](../backend/app/db.py), [routes](../backend/app/main.py), [list/search](../frontend/src/Conversations.tsx), [detail/history](../frontend/src/Detail.tsx), [configuration preview](../frontend/src/ChecklistPreview.tsx), [scorer](../backend/app/services/scoring.py).

Read-only counts: **249 saved evaluations, five checklist versions and 168 successful DEV evaluations**. All 65 DEV conversation revisions have multiple saved successes across stored history. Comparison/export can therefore be implemented and tested against real saved data without purchasing new calls.

## Ranked additions

Effort is relative scope, not a deadline: S = small route/view extension; M = coordinated API/UI and compatibility handling; L = additional source contracts and validation dependencies. API cost means incremental inference, not a vendor subscription quotation.

| Priority | Feature | Practical value | Effort | Inference cost |
| --- | --- | --- | --- | --- |
| **1** | **Compare two saved evaluations** | Identify answer, N/A, evidence, point and configuration changes | M; existing snapshots; no new persistence required | **$0** |
| **2** | **Evidence/report export** | Download traceable results for audit or handoff | S–M; JSON/CSV first | **$0** |
| **3** | **Transcript-text search + saved filters** | Find conversations and exact messages behind an issue | S–M; extends existing ID search | **$0** for literal search |
| **4** | **Weight-impact preview** | Understand arithmetic effects of weight changes on fixed saved judgments | M; strict weight-only compatibility guard | **$0**, explicitly a simulation |
| **5** | **Criterion breakdown table** | See Yes/No/N/A/unresolved counts for the selected dataset/checklist | S–M; derived aggregation | **$0** |
| **Later** | **Approved policy references** | Supply a trustworthy basis for genuinely factual judgments | L; approved documents, citations and evaluator/cache changes | Fresh inference/testing needed for real grounding |

### 1. Saved-run comparison

Compare **two different saved runs**, rather than duplicating the current within-run original/effective view. Show criterion-level disposition/value, points, evidence and explanation alongside checklist/model/prompt/schema identity, execution state and usage. Offer explicit original/effective selection.

Require the same conversation revision for a direct comparison. Match stable criterion IDs; show additions/removals and definition/scale changes. A different rubric is not evidence of improved operator behavior, and incompatible/null totals must not produce a misleading numeric improvement.

Implementation: a read-only comparison service/route alongside [main.py](../backend/app/main.py) and a small view linked from [Detail.tsx](../frontend/src/Detail.tsx). Reuse saved snapshots; do not create jobs, copy reviewer decisions to another run or mutate history.

Acceptance: copied real saved runs, N/A transitions, unresolved/failed runs, changed scales/criteria and original/effective selection. Assert no provider invocation or database change. This is the recommended first stage.

### 2. Evidence/report export

Start with JSON and criterion-row CSV. Include source revision/hash, checklist version/snapshot, original/effective answers and calculated results, evidence IDs, review history and actual model/usage provenance. Unresolved values stay null/unavailable; flags remain unscored. Make transcript-excerpt inclusion explicit. Exclude credentials, organizer endpoints and signed recording URLs.

Use one consistent saved snapshot for both formats. A printable HTML layout can follow; no summarizing call or PDF service is necessary. The feature must produce real downloadable artifacts, not merely expose the existing API response.

Acceptance: exact stored-value/Decimal-string round-trip, RU/KZ/EN Unicode, CSV commas/newlines/formula-like cells, missing usage and preserved historical criteria/reviews. No evaluation or review row should be created.

### 3. Transcript-text search and saved filters

Add literal keyword/phrase matching in source message text, a speaker selector, source-derived snippets and exact-message links. Compose with current dataset/version/language/channel/status/appeal/critical filters. Save presets in local storage or URL state initially; no team-login system is needed.

For this dataset, a bounded backend search is sufficient. Consider SQLite full-text indexing only when scale justifies it; avoid embeddings/vector services for the first implementation. This is literal retrieval, not semantic search or new scoring.

Acceptance: RU/KZ/EN matching, empty/no-hit cases, safe literal handling, combined filters, correct source revision/message targets and refresh persistence. Search snippets must never replace the full transcript in provider input.

### 4–5. Low-cost follow-ons

**Weight preview:** permit only validated weight changes with all judgment-relevant fields unchanged. Apply the existing scorer to selected saved original/effective answers, clearly labeled as a fixed-judgment scenario. Definition/type/scale/N/A changes and added/removed criteria disable this path and require a new actual assessment. Preserve unresolved totals. Never save a simulated result as successful hosted inference.

**Criterion breakdowns:** show counts and denominators for a selected rubric/dataset, separating execution failures from judgment uncertainty. Link counts to actual conversations. These are descriptive operator-result distributions, not model accuracy, employee rankings or project grades. Do not silently combine rubric versions or the separate synthetic-test dataset.

### Later: approved policy references

Attach an approved document revision, effective date, criterion association, excerpt and verifiable citation ID. Account-specific facts still need authorized account data. Include context hashes in future evaluator/cache identity; preserve earlier no-context results.

Additional immutable source records can fit the current architecture without a general RAG platform. However, an upload/storage screen alone is not a completed grounding feature. Acceptance needs approved material, a real grounded evaluation when spending is authorized, citation checks and missing/conflicting-source handling. No policy is invented, and this cannot be claimed as a completed zero-inference quality improvement today.

## Vendor patterns to adapt carefully

- NiCE's sample greeting profile includes extra components and a customer-speaks-first cap. They are example vendor rules, not our initial rubric; copying them would recreate scoring defects. Borrow the configuration workflow only. [Profile example](https://help.nicecxone.com/content/genaiprompteditor/configureqmautoscoreprompt.htm)
- Amazon documents a fallback where uncertain generative answers can become N/A and be excluded from scoring. Our missing-basis state must remain needs_review with a withheld total; uncertainty must not silently remove weight. [Answer mapping](https://docs.aws.amazon.com/connect/latest/adminguide/generative-ai-performance-evaluations.html)
- Vendor coverage, emotion and outcome claims do not establish correctness on our cases. A generated confidence percentage is not calibrated accuracy.
- Automatic coaching, live telephony assistance, screen capture, predictive CSAT, CRM reconstruction and proprietary model training are lower-priority expansions. They add data, inference or infrastructure needs. The archived manual calibration exercise is not being reinstated.

## Implementation sequence and gates

1. Build/test read-only saved-run comparison on copied real data.
2. Reuse its saved-result/provenance contract for real export downloads.
3. Extend transcript retrieval and saved filter presets.
4. Select weight simulation/criterion breakdowns only if useful; defer policy-driven inference until source/budget prerequisites exist.

The first three fit FastAPI, SQLAlchemy/SQLite and React/TypeScript. Keep the provider and immutable scoring/review contracts. Existing initialization uses create_all rather than a migration framework: adding columns to existing tables needs explicit migration/backup work. Prefer derived read-only features first.

Every stage must preserve originals, checklist versions and decisions; use actual stored data; run relevant regression checks; and block unintended Provider.request calls. Zero-spend functional checks cannot establish final-prompt semantic accuracy. These features improve usability and traceability, not correctness by themselves; known applicability concerns remain separate.

## Work actually performed

Inspected models/routes, scorer and list/detail/editor views plus earlier reports. Searched/opened official current sources for ten products; read main SQLite in mode=ro for counts. Recorded a private preservation baseline before documentation edits. No vendor trial, account connection, customer upload, organizer/provider request, application change, key change, app launch or demo task. No application suite was rerun for this research. Added inference spend: **$0.00**, paid limit **0**.

The first concrete recommendation is **saved-run comparison**, followed by **evidence export**. These are proposed implementation stages, not features implemented by this research.

Research checks passed: ten platforms / 13 official source URLs; main rows, .env, budget baseline and all 26 archived reference files unchanged. Source/history credential/private-path scan, 36 Markdown documents / 152 local links and git diff --check passed. These checks validate the research artifact and preservation, not vendor accuracy or unimplemented feature behavior.
