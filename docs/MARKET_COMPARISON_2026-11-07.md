# Market comparison and next feature choices

**Implementation follow-up, 8 November:** the first three additions are now implemented and tested: [criterion breakdowns](improvements/13-criterion-breakdowns.md), [review priority](improvements/14-review-priority.md), [weight-impact preview](improvements/15-weight-impact-preview.md). [Final verification](improvements/16-insights-verification.md) records actual saved-data coverage, 283 backend/107 client checks and zero inference spend. The proposals below preserve their research-time status; subsequent implementation is described by those reports.

Research refreshed **7 November 2026**, against merged implementation **c49da39** and documentation checkpoint **5b726f9**. The shared workspace also contains later UI-consistency, semantic-validation and export-disclosure changes owned by other chats. Those changes were inspected as working changes, not certified as a new release by this research.

**Recommendation:** extend the existing application with criterion breakdowns, explicit review prioritization and a tightly constrained weight-impact preview. These can use saved data with **zero additional inference** and retain FastAPI, SQLite, React, the provider adapter and the scorer. Cohort comparison and visible validation coverage are the next reliability-oriented additions. Approved policy grounding has greater potential to improve factual judgments, but needs authoritative material and subsequent behavioral validation.

This is research and a proposed backlog, not feature implementation or a new PDF grade. Public vendor documentation establishes advertised workflows; it does not establish comparative accuracy on our rubric. No trials, authenticated vendor accounts, price quotations or customer-data uploads were used. Availability can depend on plan and region. Feasibility and priorities below are engineering assessments.

## What we already have

The application already implements configurable immutable checklists; RU/KZ/EN transcript evaluation; deterministic Decimal arithmetic and N/A handling; separate critical flags; explanations and message-linked evidence; original/effective results; criterion appeals and reviewer history; call recording links; shared budget reservations; draft field errors and change previews; saved-run comparison; JSON, archival CSV and simple CSV exports; bounded selected-run exports; literal transcript search with all-match navigation; and portable browser-local saved filters.

The merged design also provides a readable review queue, disclosed secondary tools, keyboard navigation and responsive styling. Recommending comparison, export or saved search as entirely new features would repeat work already completed.

These capabilities cover the central evaluation/evidence/review workflow. The principal gaps relative to commercial products are aggregate analysis, operational follow-up, validation coverage and authoritative business context. Enterprise identity, CRM integration and coaching administration are wider product scope, not additional requirements inferred from the PDFs.

## Representative alternatives

| Alternative | Documented approach | Comparison with our solution | Pattern worth adopting |
| --- | --- | --- | --- |
| **Zendesk QA** | Category/language breakdowns, score trends and conversation drilldowns; automated and manual review metrics are distinguished. [AutoQA dashboard](https://support.zendesk.com/hc/en-us/articles/9019507481242-Understanding-the-AutoQA-dashboard-in-Zendesk-QA) | We inspect individual results well but have limited aggregate criterion reporting. | Criterion distributions and coverage counts that open the exact underlying cases. |
| **NiCE CXone** | Quality-performance drilldowns; configurable prompt profiles tested on sample transcripts before publication. [Performance](https://help.nice-incontact.com/Content/qmanalytics/monitor/qualityperformance.htm), [prompt testing](https://help.nicecxone.com/content/genaiprompteditor/configureqmautoscoreprompt.htm) | Our checklists are versioned and structurally previewed; saved comparisons exist, but structural validity is not behavioral validation. | Visible configuration-test coverage and explicit baseline/candidate review. |
| **Amazon Connect** | Form sections, question weights, preview/validation and a model-version selection tied to a saved form version. [Evaluation forms](https://docs.aws.amazon.com/connect/latest/adminguide/create-evaluation-forms.html) | We already preserve rubric and provider provenance; we lack a fixed-judgment weight scenario view. | Explain weight and N/A denominator effects, and show whether the exact evaluation configuration has evidence of testing. |
| **Observe.AI** | Rule-based configuration, evidence-backed automated evaluations, disputes and coaching workflows. [Auto QA](https://www.observe.ai/post-interaction/auto-qa) | We already have evidence, appeals and review history; follow-up from accepted findings is less developed. | A small reviewed-finding action card, without automatic coaching judgments. |
| **CallMiner** | Automated/manual quality scoring, dashboards and prioritized contact lists for review. [Quality management](https://callminer.com/solutions/quality-management) | Our pending-appeal and critical-finding filters are useful, but do not provide a unified, explained review priority. | Transparent triage based on existing recorded states, with direct evidence links. |
| **evaluagent** | Company context and policy/product/compliance documents attached to scorecard items. [Context Engine](https://www.evaluagent.com/news-press/evaluagent-launches-context-engine/) | Transcript evidence cannot establish a fee, account fact or policy that was never supplied. | Approved, versioned policy references when those sources become available. |
| **Langfuse** | Experiment comparison with aggregate measures, individual-case inspection and dataset/evaluator/version metadata. [Experiment comparison](https://langfuse.com/docs/evaluation/experiments/compare-experiments) | An engineering evaluation platform rather than an operator-QA replacement. Our pairwise saved-run comparison supplies much of the underlying data. | Cohort-level differences and reproducible compatibility/coverage checks over existing saved runs. |

Our local workflow, preserved originals and budget controls are practical strengths for this project. This comparison provides no basis to claim better model accuracy, language coverage or enterprise scalability than these products.

## Ranked additions

Effort is relative engineering scope: **S** is a localized extension; **M** requires coordinated backend/client work and edge-case handling; **L** adds new source contracts and validation dependencies. These are not delivery-time promises. All items remain proposals.

| Priority | Addition | Value | Effort | Additional model spend |
| --- | --- | --- | --- | --- |
| **1** | Criterion and coverage breakdown | Locate recurring weak, excluded and unresolved criteria; open supporting cases | S–M | **$0** using stored results |
| **2** | Explained review-priority queue | Surface existing appeals, uncertainty, critical findings and failed work clearly | S–M | **$0** |
| **3** | Weight-impact preview | Explain a weight change's arithmetic effect on fixed saved judgments | M | **$0**; simulation only |
| **4** | Cohort comparison and configuration-test coverage | Inspect historical answer transitions and reveal missing exact-configuration validation | M | **$0** for stored comparisons; fresh model behavior remains untested |
| **5** | Reviewed-finding follow-up cards | Turn an accepted finding into a traceable, editable action | M | **$0** for manually authored content |
| **Later** | Approved policy grounding | Supply an authoritative basis for factual evaluation | L | Real grounded evaluations and validation need future authorization |

### 1. Criterion and coverage breakdown

Start with a compact table derived from the selected dataset/checklist, with an explicit original/effective basis. Show binary Yes/No counts, scale-answer distributions, N/A, needs-review, critical true/false/unknown and execution coverage. Display denominators next to percentages. Keep synthetic data separate unless explicitly selected.

Use one defined selection policy: the latest run for the selected checklist on each latest source revision. A failed latest run must remain a failure count rather than silently falling back to an older success. Show missing/unstarted cases separately. Do not merge different checklist definitions under matching criterion IDs.

Reuse saved-result readers and add an aggregation service/API plus a small table. Clicking a cell should return the exact source/run/criterion set; aggregate counts and drilldown must come from the same snapshot. Existing summaries cannot substitute for criterion-level applicability.

**Proposed acceptance:** hand-check synthetic counts and fractions, original/effective differences, absent runs, N/A/unresolved/flag states, duplicate histories and checklist boundaries; then verify copied saved data and no provider/database mutations. These tests were not run or implemented by this research.

### 2. Explained review priority

Extend the existing queue rather than creating a second review system. Add explicit reason labels and a transparent sort/filter policy for open appeals, unresolved criteria, recorded critical findings and failed/interrupted work. Keep critical true, false and unknown distinct; an unevaluated conversation is not a clean pass. Show age and a stable tie-breaker where appropriate.

Let users choose the queue emphasis instead of inventing a hidden risk score. Every reason opens the specific saved run/criterion. Do not automatically resolve appeals, approve judgments or penalize operators. This is an in-application operational aid; it does not reinstate the removed 15-dialog organizer/reference-labeling exercise.

**Proposed acceptance:** identical reason counts and target links across refreshes, latest-revision/history boundaries, null flags, multiple open appeals, saved-view compatibility and no state-changing GET requests.

### 3. Weight-impact preview

Extend the current checklist preview with an explicitly labeled **fixed-judgment simulation**. Reuse the deterministic scorer over selected saved original/effective answers. Show old/new total, per-criterion contribution and the applicable denominator, retaining null totals for unresolved cases.

Permit only weight changes after validating that every other field is unchanged. Changes to wording, answer types, scales, N/A rules, criteria or sections must disable reuse. Never turn a simulated result into a successful evaluation or imply that new wording has been understood by a model. Do not suggest weights that merely maximize the project's score.

**Proposed acceptance:** identity draft, valid weight changes, N/A redistribution, all-N/A and unresolved results, critical flags, Decimal rounding and refusal after any non-weight change. No saved result, checklist or review is changed by preview.

### 4. Cohort comparison and honest test coverage

Build on existing pairwise comparison to inspect multiple matched source revisions. Make baseline/candidate selection explicit; retain exact run IDs and configuration hashes. Separate answer/disposition changes, points, definition changes and explanation-only differences. Missing or incompatible pairs remain visible and are never counted as passes. A changed operator-quality score is a historical difference, not proof that one evaluator is more accurate.

Alongside configuration preview, distinguish structural checks, deterministic/offline regression checks, existing saved-run coverage and live evaluation of the exact configuration. Report each status separately; passing frontend/backend tests does not make a model configuration semantically validated. Do not manufacture a confidence percentage or promote the latest run automatically.

This borrows a testing workflow without requiring a Langfuse deployment, new annotator assignments or the removed manual packet. Comparing new prompts with no saved candidate outputs still requires a future real evaluation; offline infrastructure cannot supply that evidence.

### 5. Reviewed-finding follow-up

If operational follow-up becomes useful, attach an editable action, owner label, due date and status to an accepted reviewer finding. Cite the source/run/criterion and preserve the originating decision. Start with manually entered actions and local persistence; any new table requires an explicit migration and backup strategy.

No new owner/account identities should be inferred from speaker labels. The present anonymous workflow cannot authenticate assignments or acknowledgements. Avoid a full coaching/LMS/employee-ranking system unless the product scope changes.

### Later: policy-grounded factual evaluation

Require approved policy material with document revision, effective date, criterion association and citations. Company background from the supplied PDF is not a brokerage policy manual or account record. Missing or conflicting material must remain visible as a lack of basis.

A small immutable reference store can fit the current architecture; a vector database or general retrieval platform is not required for a bounded set of documents. Nevertheless, storing uploaded files alone would not complete grounding. Evaluator/cache identity, context relevance, citations and behavior on missing/conflicting sources would need validation, including real hosted evaluations when authorized. Existing originals stay unchanged.

## Patterns to avoid copying

- Vendor greeting templates and scoring formulas do not override the supplied rubric. NiCE's example greeting rules are different from ours; borrow the testing workflow, not its score thresholds. [NiCE example](https://help.nicecxone.com/content/genaiprompteditor/configureqmautoscoreprompt.htm)
- Amazon documents an uncertain-answer fallback to N/A with weight redistribution. Our missing-basis state must remain needs_review rather than silently gaining points through exclusion. [Amazon answer mapping](https://docs.aws.amazon.com/connect/latest/adminguide/generative-ai-performance-evaluations.html)
- Vendor interaction-coverage and marketing-accuracy claims do not establish truth on our cases. Automated/manual agreement is not independent ground truth unless the reference judgments are qualified.
- Real-time assistance, ASR, sentiment prediction, multi-model judging, screen recording, broad CRM integration and employee leaderboards add infrastructure/data/scope without resolving the current validation gap. Transcripts are already supplied; full Dynamics integration is not a PDF requirement.
- Search indexing and thinner queue queries become useful if saved history grows. Extend the existing readers after measurement rather than adding a search service or vector store now.

## Work performed and limits

Read current Git status/history, `CURRENT_CONTEXT.md`, `MASTER_CONTEXT.md`, earlier market reports, API/storage/scoring/client contracts and the concurrent semantic/technical audit. Searched/opened official public sources for the seven alternatives above. Initial shell inspection used a Windows-incompatible wildcard for one `rg` argument; subsequent file-specific reads supplied the relevant evidence.

Only this report and its context/index pointers were authored by the research task. No product feature, scoring judgment, provider configuration, credential or saved result was changed. No app server, model request, organizer fetch, vendor trial or demo was started. Application tests were not rerun for documentation-only research; previously reported **173 backend / 63 client / one skipped** belong to merged c49da39, not a new certification of concurrent working changes.

Read-only preservation checks passed against the research baseline across all eight main tables, 249 evaluations and 30 protected files. Source/history credential/private-path scan, 49 Markdown documents / 227 local links and `git diff --check` also passed. Private evidence is under ignored `local_data/market_refresh_20261107`; commands and outcomes are recorded in `CURRENT_CONTEXT.md`.

The next concrete action, if implementation is requested, is **criterion and coverage breakdown with exact-case drilldown**, followed by **explained review priority** and **weight-impact preview**. Finish the existing concurrent fixes' acceptance first. These changes can improve usability and traceability without rebuilding the application or spending on inference; they do not replace independent correctness validation. **Demo remains deferred.**
