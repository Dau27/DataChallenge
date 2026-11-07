# Market analysis and incremental development plan for CQA

Current-build refresh: [market feature options](MARKET_FEATURE_OPTIONS.md) rechecks ten platforms after budget protection, checklist preview and review filters were implemented. It ranks remaining zero-inference additions and preserves manual-packet removal/demo deferral. The survey below retains its earlier baseline.

Research date: 7 November 2026. Scope: 14 conversation quality and contact centre platforms, plus one adjacent evaluation tool. This is an analysis of documented capabilities and their fit with the inspected repository, rather than a hands-on accuracy benchmark or a procurement quotation.

## Main conclusion

Keep the current application and strengthen its evaluation and review workflow. Its React/FastAPI architecture, immutable conversation and checklist snapshots, evidence references, deterministic scoring, persistent jobs, and original-versus-effective results already provide the right foundation for this task.

The most valuable additions are:

1. Independent criterion-level calibration and repeatable regression evaluation.
2. A prioritised review queue with explicit reasons for uncertainty and disagreement.
3. Previewing a checklist change against saved examples before using it broadly.
4. Approved, versioned policy context for questions that cannot be settled from a transcript.
5. Structured coaching feedback, followed later by assignment and follow-up tracking.

These are incremental changes. Real-time assistance, speech recognition, desktop recording, customer-facing AI agents, and workforce management would create a different scope and should not drive the next iteration.

The competitive opportunity is a focused, auditable workflow for the exact Freedom Broker rubric across RU/KZ/EN, with transparent uncertainty and cost accounting. It is a positioning hypothesis until qualified reviewers validate the judgments. Multilingual support, AI scoring, and appeals alone are already available elsewhere.

## Our actual starting point

Repository inspection and the existing verification record establish the following baseline:

| Capability | Existing implementation | Practical implication |
| --- | --- | --- |
| Ingestion | Organizer API and JSON share validation; source revisions are immutable and imports are idempotent | Additional sources can be adapters rather than a new ingestion system |
| Rubric configuration | Saved versions contain criteria, weights, answer types, scale anchors and N/A conditions | We already have the configurable scorecard foundation |
| Evaluation | Full transcript and rubric sent to one configured hosted provider; dynamic structured output; validation and bounded repair | Improve judgment quality around the existing provider boundary |
| Evidence | Validated message ranges, source transcript inspection, absence/context/support distinctions | Evidence presentation does not need replacing |
| Scoring | Backend Decimal arithmetic; permitted N/A exclusion; critical flags separate; unresolved criteria withhold the total | Preserve this contract when borrowing vendor features |
| Review | Criterion appeals, separate confirm/replace action, rationale, ordered history and recalculation | Calibration and reviewer work queues can reuse domain validation and scoring |
| Reliability | Persistent jobs, cache identity, retry/backoff, interrupted-job handling and budget reservations | No immediate need for a new distributed processing stack |
| Production controls | Anonymous demo actions and local-first operation | Authentication, organisational access and retention are additional production work |

The recorded real DEV result is **65 successful executions: 59 complete scored assessments and 6 needing review**. The latest set mixes three models and is not a controlled model comparison. The 15 selected real reference examples have no independent human labels. Synthetic diagnostics and 74 backend tests establish useful software checks; they do not establish real-world judgment accuracy. The demonstration conversation's 92.31/100 is an operator score, not a score for our product.

Local implementation references:

- [Specification](C:/Users/user/Desktop/DataChallenge/MASTER_CONTEXT.md)
- [Verified implementation context](C:/Users/user/Desktop/DataChallenge/CURRENT_CONTEXT.md)
- [Data persistence](C:/Users/user/Desktop/DataChallenge/backend/app/db.py)
- [Contracts and judgment validation](C:/Users/user/Desktop/DataChallenge/backend/app/domain.py)
- [Provider, schema and cache identity](C:/Users/user/Desktop/DataChallenge/backend/app/services/evaluator.py)
- [Deterministic scoring](C:/Users/user/Desktop/DataChallenge/backend/app/services/scoring.py)
- [Jobs](C:/Users/user/Desktop/DataChallenge/backend/app/services/jobs.py)
- [Appeal decisions](C:/Users/user/Desktop/DataChallenge/backend/app/services/reviews.py)

## Market structure and vendor approaches

The useful comparison is how platforms turn a conversation into an evaluation, establish trust in it, and turn it into action. Public feature descriptions establish product behaviour; they generally do not disclose enough to reproduce proprietary model training, retrieval, or calibration algorithms.

### Specialist enterprise conversation intelligence

| Platform | Documented features and approach | Fit for our application |
| --- | --- | --- |
| **Observe.AI** | Combines automated evaluation with configurable keyword/phrase/logic rules, evidence, calibration, acknowledgement/disputes, and coaching. Its rollout model progresses from suggestions through filled forms to automatic submission. This makes automation a controlled workflow rather than just a generated score. [Auto QA](https://www.observe.ai/post-interaction/auto-qa) | Adopt staged automation and better calibration. Evidence and disputes already overlap with our workflow. A sophisticated visual rule builder has lower value than clear criterion instructions and tested outcomes at our scale. |
| **Cresta** | Evaluates situational behaviours, process adherence and outcomes; describes bespoke behaviour detectors with human calibration. Links scorecard findings to coaching and examines relationships between behaviours and inferred business outcomes. [Quality Management](https://cresta.com/cresta-quality-management) | Borrow the connection between a failed criterion, a teachable moment and follow-up. Outcome correlations require actual operational data and sufficient observations; our transcripts alone cannot establish sales uplift or causality. Custom detector training is unnecessary now. |
| **Level AI** | Supports custom and hybrid scorecards, evidence-backed suggestions, manual review, calibration, dispute handling and corrections. Describes QA-GPT as a proprietary LLM approach; human and automated answers can feed one evaluation. [Quality Assurance](https://thelevel.ai/product/quality-assurance-contact-center) | Our needs-review state and replacement decisions are a useful starting point for hybrid review. Add proactive review assignment and human-only applicability where justified. Corrections should become reviewed calibration examples, not silently retrain or rewrite old assessments. |
| **CallMiner** | Uses conversation analytics, automated or hybrid quality forms, prioritised contacts for manual review, agent/supervisor dashboards and coaching. Its wider suite adds screen recording and live guidance. [Quality management](https://callminer.com/solutions/quality-management) | Prioritised review and recurring criterion trends are realistic additions. Screen capture and live guidance need new data and integrations; they contribute little to a transcript-provided hackathon evaluation. |

### Support QA and performance workflows

| Platform | Documented features and approach | Fit for our application |
| --- | --- | --- |
| **Zendesk QA** | Separates automatic quality scores (AQS) from manual internal quality scores (IQS), tracks human/AI agreement, modifications, category trends and root causes. Its documentation says AQS is an unweighted average of automatic category scores; several manual scorecard settings do not affect AQS. [Dashboard and scoring definitions](https://support.zendesk.com/hc/en-us/articles/9019507481242-Understanding-the-AutoQA-dashboard-in-Zendesk-QA) | Borrow agreement and root-cause views. Do not substitute AQS for our required weighted scoring or interpret a vendor's “auto-reviewed” count as every criterion being resolved. Our original/effective comparison should remain explicit. |
| **Rippit, formerly MaestroQA** | The September 2026 announcement describes a move from sampled manual QA toward configurable AI agents operating across conversation data, while retaining rubrics, scores and calibration history. Current materials also describe ingestion, operational-data enrichment and cross-conversation analysis. [Rebrand and product direction](https://www.rippit.com/news/maestroqa-is-now-rippit), [How it works](https://www.rippit.com/how-it-works) | Borrow reusable analysis definitions and structured findings that can be aggregated later. A general conversational BI interface would broaden our scope substantially. Earlier MaestroQA feature pages can redirect to Rippit, so evaluate current workflows rather than relying on old comparison lists. |
| **evaluagent** | Offers configurable automated QA, manual calibration and coaching. Its Context Engine attaches company information and uploaded policies/product/compliance documents to scorecard line items to evaluate factual correctness against business knowledge. [Context Engine](https://www.evaluagent.com/news-press/evaluagent-launches-context-engine/), [Feature and plan breakdown](https://www.evaluagent.com/pricing/) | Policy context is especially relevant to our unresolved factual questions. Start with small approved documents explicitly attached to criteria and version them. Generic company background is not evidence for a brokerage fee or an account-specific fact. |
| **Kaizo** | AutoQA provides editable ratings and notes. Its documented coaching feedback separates the observed event, its assessment and an actionable recommendation; a criterion can be previewed on previously rated tickets. [Rating workflow](https://support.kaizo.com/hc/en-us/articles/15402725870749--Auto-QA-Rating), [Structured coaching feedback](https://support.kaizo.com/hc/en-us/articles/37567790821533--Release-Structured-Coaching-Feedback-in-AutoQA) | This is a close fit for a small enhancement to our detail view. Keep the recommendation separate from the scored judgment, require an evidence link, and let a reviewer edit it before sharing. Previewing criterion changes is also highly transferable. |

### Contact centre and workforce suites

| Platform | Documented features and approach | Fit for our application |
| --- | --- | --- |
| **NiCE CXone** | Auto Score has configurable prompt profiles, testing on up to five transcript segments, generated reasoning/highlights and publication before live selection. Model choice is managed by NiCE rather than individually selected in each prompt profile. [Auto Score prompt configuration](https://help.nicecxone.com/content/genaiprompteditor/configureqmautoscoreprompt.htm) | Borrow a draft → preview → publish experience. We already save immutable checklist versions; adding preview and an activation pointer is incremental. Keep provider configuration governed separately from scorecard editing. |
| **Verint** | QM Intelligence combines manual/automatic QM, explainable findings, question validation and form conversion. Its answer-validation approach compares information spoken, shown or entered in business systems, distinguishing matches, mismatches and missing information. [Automated QM capabilities](https://www.verint.com/guides/automated-quality-management/) | Borrow validation before publishing and explicit missing-information treatment. Cross-system answer validation needs trusted CRM/account snapshots. It cannot be reproduced by asking our model to guess whether an answer sounds plausible. |
| **Genesys Cloud** | Provides forms, calibration, disputes and coaching alongside AI scoring. Documentation describes reasons for suggested answers and historical agreement monitoring; its current scoring controls use a recent-submission window and can hide unreliable suggestions. [Quality management](https://help.genesys.cloud/articles/about-quality-management/), [Automated scoring controls](https://help.genesys.cloud/articles/automated-scoring-options-in-evaluation-forms/) | Borrow measured reliability per criterion and visibility controls. Our tiny, unlabeled set cannot justify copying Genesys's thresholds. Human overrides are useful feedback but are not automatically unbiased ground truth. |
| **Amazon Connect / Contact Lens evaluations** | Evaluation forms support question-level automation using categories/rules, generative AI or conversation metrics, with assisted or automatic submission. Forms also offer model-version selection and previewing forthcoming evaluation configurations. [Evaluation form and automation documentation](https://docs.aws.amazon.com/connect/latest/adminguide/create-evaluation-forms.html) | Adopt the separation of deterministic facts from semantic judgments and controlled evaluator versions. We already separate arithmetic and model judgments. Moving telephony and evaluation into Connect is unnecessary for our current input and would introduce platform dependencies. |

### Regional alternatives

| Platform | Documented features and approach | Fit for our application |
| --- | --- | --- |
| **Yandex SpeechSense** | Combines voice/chat analysis, semantic tags, summaries, metadata, related-dialog navigation and reporting. Its documented checklist workflow is manual, with weighted criteria and N/A; that must be distinguished from its AI analysis features. Yandex explicitly announced SpeechSense Kazakh support in March 2025. [Dialogs](https://aistudio.yandex.ru/en/docs/speechsense/concepts/dialogs), [Checklists](https://aistudio.yandex.ru/en/docs/speechsense/concepts/checklists), [Kazakhstan update](https://yandex.cloud/ru-kz/blog/posts/2025/04/speechkit-speechsense-update-2025) | A relevant RU/KZ comparison candidate. Borrow related-dialog grouping and clear role/metadata handling when source identifiers exist. Documented Kazakh support does not establish agreement on our eight criteria or equivalent functionality in every language. |
| **3iTech / 3i TouchPoint Analytics** | Describes omnichannel analysis, checklist configuration, keyword and AI checks, highlighted findings, shared comments, calibration and LLM forms. Offers cloud/on-premise deployments and lists Freedom Bank Kazakhstan as a customer reference. [Product and deployment details](https://3itech.ru/products/rechevaya-analitika) | Locally relevant benchmark for review and deployment expectations. The Freedom Bank reference concerns a different organisation/use case from our Freedom Broker prototype; it proves neither shared systems nor rubric accuracy. Verify exact RU/KZ/EN feature coverage with real examples. Do not infer cheap self-hosted model inference from a CPU-compatible application deployment claim. |

### Adjacent evaluation infrastructure

Langfuse provides datasets, application experiments and annotation queues. Its documentation separates inputs/expected outputs, the application variation being tested, and scoring functions. It can wrap existing application code rather than replacing the application. [Offline evaluation](https://langfuse.com/docs/evaluation/get-started/offline)

For us, the first implementation can be private JSON reference labels plus a local comparison command. An optional Langfuse integration becomes worthwhile when multiple people need experiment comparisons and trace navigation. It should remain an observability/evaluation sidecar, not the source of truth for operator scores or appeals.

## What these approaches teach us

### Coverage, correctness and action are separate problems

Automating more conversations solves sampling coverage. It does not prove semantic correctness, eliminate bias, or ensure coaching improves service. Our 65 successful executions are a processing result; the six withheld totals are a separate completeness result. A future report should show at least four distinct measures: processed conversations, resolved judgments, agreement with adjudicated labels, and reviewer workload.

A single headline “AI accuracy” number hides different failure modes. False critical flags, unsupported favourable scores, incorrect N/A and evidence that does not support a conclusion need separate counts.

### Hybrid evaluation is the most transferable design

Deterministic code should handle facts that are truly derivable, validation and arithmetic. The model should handle contextual interpretation. Humans should resolve ambiguous standards and unavailable business context.

A keyword match is weak evidence for empathy, resolution or a compound closing requirement. A timestamp calculation is only valid when timestamps and the desired rule actually support it. The initial rubric excludes a three-minute first-response penalty; importing a vendor's timer-based example must not introduce that penalty.

Review must preserve the original machine assessment. Our current original/effective split and decision history already support this principle. A calibration label is a different object: it represents an adjudicated reference judgment, not every operational override.

### Business knowledge is different from conversation evidence

A transcript can establish what the operator said, omitted, clarified or promised. It may not establish the correct brokerage fee, whether a transfer really completed or what a customer's account permitted at that time.

Policy documents can resolve policy questions; account facts require an appropriately authorised system snapshot. A general brochure cannot substitute for either. The model should cite transcript evidence and policy references separately. When no required authority exists, retain a reasoned needs-review state rather than award an unsupported answer.

### Turn findings into small, reviewable actions

The useful coaching unit is a criterion, an evidence excerpt, an explanation and a concrete next action. A generic paragraph about being more empathetic adds little. Tracking an assigned action and a later follow-up can be valuable after reliable agent/team identifiers exist.

Root-cause labels should distinguish agent behaviour, ambiguous policy, missing context, model error and transcript limitations. A low quality score by itself does not prove the operator caused the customer's problem.

### Version changes need experiments

A scorecard edit, prompt change, model change or policy update can move scores without operator behaviour changing. Our cache already distinguishes conversation, checklist and evaluator identity. Extend that discipline to policy versions, reference-label versions and experiment records. Compare versions on identical saved examples before adoption; never overwrite earlier assessments.

## Feasibility without reconstruction

Effort estimates below are planning judgments in focused engineer-days, assuming the current code and a local demonstration deployment. They exclude waiting for reviewers, policy approval, vendor access and production security work. They are not vendor implementation promises.

| Addition | Current foothold and necessary change | Effort / disruption | Recommendation |
| --- | --- | --- | --- |
| Human reference labels and comparison report | Extend the existing reference selection and diagnostic scripts; store adjudicated labels, provenance, evidence and rubric hash privately | 1–3 days plus expert review; low | First |
| Prioritised review queue | Query incomplete evaluations, open appeals and critical flags; add reason filters, owner/status and age | 1–2 days for local queue; low | First |
| Checklist preview and version comparison | Reuse saved conversations/evaluations; add test selection, cost preview, results diff and publish pointer | 2–4 days; low to medium | Next |
| Reason taxonomy and root-cause summary | Add structured review reason codes beside existing explanations; aggregate with denominators | 1–2 days; low | Next |
| Approved policy snapshots | Add policy versions and criterion associations; supply selected excerpts; validate policy citations; expand cache identity | 3–5 days; medium; needs authoritative documents | Next when documents exist |
| Structured coaching draft | Add a separate feedback contract/view linked to judgment and evidence; reviewer edits; no automatic sending | 1–2 days; low | After calibration |
| Coaching assignment and follow-up | New action records, due dates, owner and outcome; requires real agent identity metadata | 3–5 days; medium | Later pilot |
| Criterion/language/model trends | Aggregate comparable evaluations; expose sample counts, unknown usage and exclusions | 1–3 days; low | After labels and consistent cohorts |
| CRM/source adapter | New adapter into existing normalised conversation model; sidecar metadata for external IDs and trusted facts | 2–5 days per bounded integration after access; medium | Only for a named business need |
| Langfuse export | Optional experiment/trace adapter with privacy controls | 1–3 days for narrow export; low to medium | Optional |
| Authentication, RBAC, retention and redaction | Identity provider integration, object-level checks, data lifecycle and tested redaction with evidence mapping | Multi-stage production work; medium to high | Required before shared production use; outside current demo scope |
| Real-time assistance, ASR, screen recording | Streaming/event pipeline, recording/consent controls, new source data and latency requirements | High; separate subsystem | Defer |

The first three additions fit the current stack. Their engineering subtotal is roughly 4–9 focused days, plus independent labeling and review. This range is not a promise to achieve production accuracy within that time.

### Concrete extension points

**Calibration.** Add reference-example and reference-judgment storage separate from `Review`. Record conversation revision, checklist hash, criterion, expected disposition/value, evidence, author, adjudicator and split. Reuse `validate_judgment` and the deterministic scorer. Blind labeling should hide AI scores initially; otherwise agreement can be inflated by anchoring. A local comparison command should consume saved results without paying for inference.

**Review queue.** Start with a query endpoint and a view reusing the existing detail page. Show failed execution separately from successful-but-incomplete evaluation. Prioritise by explicit business rules such as critical finding, pending appeal, missing policy and age; do not present a model-generated numeric confidence as a calibrated probability. Initial assignment can remain a local demo feature; it does not create secure roles.

**Checklist preview.** Keep browser drafts and immutable saved versions. Save a candidate version, select a few representative saved conversations, run bounded evaluations, and show criterion/disposition/score differences and usage. Existing caching applies only to identical evaluation identity. Broad activation can be a new pointer; historical versions remain selectable. Costs must be visible before an uncached run.

**Policy context.** Keep the organizer import contract stable. Store policy versions and associations in new tables or a validated sidecar, not arbitrary extra keys added to a strict source payload. Include policy content hashes, applicability dates/region/product and criterion associations in evaluation metadata and cache keys. Add a policy citation contract rather than misusing transcript message IDs. Start with bounded approved excerpts; add retrieval only after corpus size and measured retrieval failures justify it. The specification explicitly excludes a vector database from the present scope.

**Coaching.** Preserve `Assessment` and scoring semantics. Introduce a separate versioned feedback object linked to the effective decision and source evidence. A deterministic template can provide an initial draft without another paid model request. Any later generated recommendation needs schema validation and review; it must not invent a policy or automatically change a score.

**Storage and workers.** New tables are feasible, but SQLAlchemy does not make an existing database migrate itself. The app currently uses `create_all`, SQLite PRAGMAs and `BEGIN IMMEDIATE`. Existing-column changes need an explicit migration/backup plan. PostgreSQL or distributed workers would require transaction/claim/lease changes and integration testing; they are not a one-line connection-string swap. None is required for 65 conversations and two local workers.

**Private data.** Redaction must preserve an authorised way to resolve evidence to the original transcript. Masking text can change semantic meaning and content hashes; version the redaction procedure and test both. External telemetry should not automatically receive raw conversations, signed audio URLs or account identifiers.

## Proposed acceptance-gated sequence

These are future implementation gates, not completed features or new organizer requirements.

| Stage | Deliverable | Acceptance gate |
| --- | --- | --- |
| A — Establish judgment quality | Independently label the existing 15 selected real examples; adjudicate disagreements; separate development and held-out use | Complete criterion coverage, source evidence, rubric identity and reviewer provenance. Report disagreements and unresolved policy questions. Do not claim population accuracy from this small set |
| B — Make review operational | Review queue and structured reason codes, retaining existing appeal/history behaviour | Every unresolved/appealed item is discoverable; filter counts reconcile; resolving a criterion uses the existing scorer and preserves the original; local queue refresh survives reload |
| C — Safely change evaluation | Preview and comparison for candidate checklist/evaluator versions | Old evaluations unchanged, new identities correctly cached, criterion-level regressions visible, no hidden paid calls; thresholds and blockers agreed before inspecting held-out outcomes |
| D — Add grounded policy checks | Approved policy snapshots attached to selected criteria | Correct policy/version is cited; contradictory/outdated/missing-policy cases are tested; changed context invalidates cache; transcript omissions still produce No when rubric requires it |
| E — Close the improvement loop | Reviewed coaching draft and, when identities exist, assignments/follow-up | Each action traces to a criterion and evidence; edits are preserved; no unsupported outcome claim or unrequested external message |

Before changing prompts against the current six held-out examples, record whether their contents or labels have already informed development. If they have, retire that holdout designation and reserve fresh examples. Six items are a diagnostic check, not a statistically reliable language benchmark.

For calibration, report agreement for disposition and answer separately, exact agreement on configured scale anchors, critical-flag false positives/negatives, N/A confusions, evidence correctness, unresolved rate and human time per review. Break down counts by language, criterion, channel and evaluator version; small slices should remain visible as counts. Human-human disagreement establishes how clear the rubric itself is.

## Commercial and operational feasibility

Published examples show different billing units. They should not be compared as if each buys an identical evaluation:

| Product | Published commercial signal checked on the research date | What it means for us |
| --- | --- | --- |
| Zendesk QA | Listed as a $35/agent/month add-on, paid annually, on Zendesk's Contact Center pricing page | This is not a complete stand-alone contact centre price; confirm base plan, volume and feature eligibility. [Pricing](https://www.zendesk.com/pricing/contact-center/) |
| evaluagent | AutoQM & Improvement starts at $35/user/month; broader bundle starts at $65; conversation-based pricing is also offered | Seat count, usage allowances, onboarding and scope still need confirmation. [Pricing](https://www.evaluagent.com/pricing/) |
| Rippit | Free tier lists 100 agent runs/month and introductory AI credits; Starter $185/month and Growth $495/month, with separate AI-credit consumption | An agent run is a workflow execution, not necessarily one conversation. A free offer does not establish suitability for private organizer data or export compatibility. [Pricing](https://www.rippit.com/pricing) |
| Yandex SpeechSense | Subscription and service-based pricing; audio duration, chat characters and assistant/model processing are distinct billing components | Estimate with our actual text/audio volumes and contracting region; do not assume a chat includes every AI operation. [Pricing policy](https://aistudio.yandex.ru/en/docs/speechsense/pricing) |
| Enterprise suites and other specialists | Reviewed product materials establish capabilities, but do not provide a comparable complete configuration price for our workload | Obtain a scoped quote including integrations, retention, language coverage, evaluator seats, AI usage, support and export |

Our recorded selected DEV assessments have an estimated inference cost of **$0.35675655 for 65 conversations**, about **$0.00549 each**, across a mixed model/workload set. This is historical usage-based estimation, not a current price guarantee or complete service cost. All recorded known application usage is approximately $0.68; historical unreported usage remains unknown and was budget-reserved rather than called free.

A meaningful total-cost model is:

`model inference + ingestion/ASR if needed + hosting/storage + reviewer time + integration maintenance + security/operations + vendor licensing`.

For the current task, transcripts are already supplied, so adding paid ASR duplicates an input we have. A self-hosted GPU inference service introduces deployment, monitoring and model-validation work; a small GPU credit balance does not make that route cheaper in total. Our immediate costs are more likely to be affected by unnecessary reruns and unavailable expert labels than by the deterministic scorer.

Building our focused workflow is presently more feasible than migrating to a commercial platform. Buying becomes reasonable if the organisation prioritises established connectors, secure workforce access, recording, support commitments and large-scale operations. Run a bounded comparison before either migration or substantial infrastructure investment.

## How to test vendors or our next version fairly

Use the same frozen rubric, conversations, policies and adjudicated labels. Require per-criterion outputs, evidence and an export format that can be checked by our scorer. Include:

- RU, KZ, EN and code-switched examples, with real reviewers able to judge each language.
- Bot introductions followed by human operators, transfers, multiple customer requests and missing operator actions.
- N/A eligibility, empathy without ritual apology, compound closing requirements and separate clarity/completeness.
- Unsupported fee statements, outdated or wrong-region policies and account questions without authoritative account data.
- Critical flags evaluated independently of total score.
- Long conversations, repeated imports, model/version changes and unavailable-provider behaviour.
- Appeals, reviewer replacement, original-result preservation and export/replay of decisions.

Compare judgment/evidence quality, uncertainty, reviewer time, cost per completed evaluation, latency and failure recovery. Do not equate lower unresolved rate with better quality: unjustified confident answers are worse than honest missing-context findings. Conversely, treating an observable omission as unknowable needlessly increases review work.

Obtain explicit answers on data processing location, retention/deletion, subprocessor use, training use, access controls and exports before a production pilot. Do not upload private organizer conversations to free trials merely because signup is available. Published case studies and vendor accuracy claims are not a substitute for this comparison.

## Product direction

The closest workflow references are **Level AI, evaluagent, Kaizo and Zendesk QA**. **Observe.AI, Cresta and CallMiner** are useful references for coaching and operational maturity. **NiCE, Verint, Genesys and Amazon Connect** show controlled evaluation configuration within larger operations. **Yandex and 3iTech** are important regional comparison candidates. These groupings describe learning value for our scope, not an independently measured quality ranking.

Our next concrete step is Stage A: obtain independent labels for the selected real examples and resolve the six current review cases using evidence and appropriate policy authority. Then add the review queue and checklist preview. This develops the working product without replacing its architecture or changing the required scoring rules.

## Completed work and verification

- Inspected the implementation specification, context, domain/database/evaluator/review/job code, reference-selection and diagnostic scripts, and stage reports.
- Researched 14 direct platforms and Langfuse using official product, help, documentation, pricing and announcement pages linked alongside the findings.
- Distinguished vendor-described features from our engineering proposals and planning estimates; no paid vendor trial, accuracy benchmark, new application feature or production integration is claimed.
- Produced this report and updated CURRENT_CONTEXT.md. The research used no paid inference and accessed no private vendor account.
- Software test results above are the existing recorded baseline. Application tests were not rerun for this documentation-only change; documentation checks are recorded in CURRENT_CONTEXT.md.
