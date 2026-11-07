# Improving the market-inspired features already implemented

Research and repository review: **7 November 2026, Asia/Almaty**, application **ad9f167**. This follows the [PDF audit](audits/2026-11-07/13-post-features-pdf-audit.md). No application code, judgment, database result or provider configuration was changed. Model spend **$0.00**. Demo remains deferred.

## Assessment

Our application now follows the same broad workflow as established QA tools: configure criteria, evaluate, inspect evidence, dispute/review, then find and export results. We implement a useful local prototype of that workflow, not an enterprise replacement. Commercial platforms also offer team administration, channel/CRM integration, assignments, coaching and operational analytics. The PDFs do not require those systems.

The best next work is to improve the adopted features' clarity and consistency. All recommendations below fit the current FastAPI/SQLite/React structure. None requires rebuilding the evaluator or buying inference. They are recommendations, not changes implemented by this report.

Vendor facts come from official documentation/public product pages rechecked for this task. Proposed adaptations and effort estimates are our engineering inference. No trials, authenticated vendor accounts or customer-data uploads were used; plan availability, proprietary internals and claimed accuracy were not tested. Market coverage claims do not establish correctness on our RU/KZ/EN rubric.

## Market comparison

| Adopted capability | Market approach | Our current implementation | Best incremental improvement |
| --- | --- | --- | --- |
| Saved evaluation comparison | NiCE lets users test prompt profiles on up to five transcripts before publishing. Amazon associates selected GenAI versions with form versions and warns that scores under different scoring modes are not directly comparable. [NiCE workflow](https://help.nicecxone.com/content/genaiprompteditor/configureqmautoscoreprompt.htm), [Amazon forms](https://docs.aws.amazon.com/connect/latest/adminguide/create-evaluation-forms.html) | Exact-revision comparison, original/effective choices, saved definitions/points/evidence/provenance and compatibility guards. This adapts the inspect-before-adoption pattern; the sources do not establish an identical two-model comparison feature. | Refresh on reviewed-run changes first. Then separate answer changes from explanation/evidence differences, expose stored pipeline hashes, and choose a compatible successful baseline by default. |
| JSON/CSV reports | Zendesk exports reviews/comments at workspace or account scope, with date filters and pagination; its Export API excludes voice transcripts and dashboard metrics. [Export documentation](https://developer.zendesk.com/documentation/qa/exporting-data/) | Real per-run downloads include both score sets, checklist/source identity, review history and optional provided transcript excerpts, including call transcripts. Scalar CSV formula protection and private URL/credential filtering are present. | Keep the lossless format; add a simple criterion-only CSV and bounded selected/filtered-run export. A manifest should freeze the included run IDs and revision timestamps. |
| Transcript search and saved views | Zendesk supports editable/duplicable public/private filters. CallMiner describes search, filtering/classification and searchable voice transcription across channels. [Filter management](https://support.zendesk.com/hc/en-us/articles/9147011738650-Editing-and-managing-filters-in-Zendesk-QA), [CallMiner overview](https://callminer.com/conversation-analytics/conversation-analytics) | Literal Unicode text/speaker search over supplied transcripts, exact-message links, five snippets per conversation, all queue filters and checklist-scoped browser presets. | Highlight the literal match and navigate all matching messages; clarify preset update versus save-as, support portable preset files, and reduce repeated retrieval work before considering indexing. |
| Checklist preview and field errors | Amazon separates structural validation errors from GenAI content warnings and provides preview/activation steps. [Form validation](https://docs.aws.amazon.com/connect/latest/adminguide/create-evaluation-forms.html) | Deterministic draft differences and field errors; immutable validated save. No claim of semantic model validation. | State which changes invalidate previous judgment applicability, and prominently show whether the selected evaluator/configuration has actually been tested. Any rule-based advisory must be labeled as advisory. |
| Pending appeals, critical findings and reviewer control | Observe.AI describes evidence-backed QA, keyword/phrase/logic rules, disputes and staged automation. [Auto QA](https://www.observe.ai/post-interaction/auto-qa) | Separate appeal/review actions, preserved original/effective history, older-revision appeal links and effective unscored flags. | Add explicit unknown/unassessed flag filtering and show pending items' age/reason from existing metadata. Keep source navigation and reviewer judgment central. |
| Shared budget protection | These cited QA workflow pages do not establish a comparable user-supplied API budget guard. This is our engineering control rather than an asserted copy of a vendor feature. | Shared persisted reservations, cost preflight, preserved attempt/rate provenance and default zero limit. | Improve inspection of known versus unknown cost coverage in comparison/export; retain backend enforcement and avoid presenting estimates as an account balance. |

Commercial breadth does not mean a stronger implementation of our particular rubric. Our guards deliberately preserve N/A versus uncertainty, immutable originals and unscored critical flags. Our provided call-transcript excerpts are useful for this dataset; that does not imply overall superiority to Zendesk's broader product.

## 1. Comparison: freshness, useful differences and provenance

**First fix the reproduced P2 freshness gap.** In [SavedComparison.tsx](../frontend/src/SavedComparison.tsx), include both selected runs' updated_at/state in the request identity. When either changes after review, invalidate the visible result, refetch the existing GET and ignore late responses from the older identity. This needs no provider request, new persistence or scoring change. Add a regression that updates either run while the panel remains open; a reviewed null total must also refresh correctly.

Then make the existing differences easier to interpret:

- Add separate views/counts for answer/disposition changes, point changes, definition changes, and evidence/explanation-only changes. Keep an all-differences view. Current changed-only mode includes every explanatory rewording.
- Prefer the nearest earlier successful run with the same saved checklist as the initial baseline; keep failed or incompatible runs available for intentional inspection. Never silently switch the user's explicit selection.
- Expose the prompt/schema hashes and actual recorded response-model identity when available. These are already saved/exportable; the comparison's metadata whitelist currently omits prompt_hash/schema_hash. Unknown historical fields should display unavailable.
- Explain changes in normalized contributions caused by N/A denominators, and distinguish a critical flag transition from a numeric score change. Preserve all current same-source and compatibility guards.

Evidence for this priority: 65 actual historical run pairs yielded **520 criterion pairs**, **107 answer transitions** and **327 rows changed only in explanation/evidence/reasons**. This is a usability signal and historical variance, not 107 proven errors or an accuracy calculation. Prompts/models/reviews differ across that history.

Acceptance: review updates both sides without stale display; detail-only changes can be hidden independently; unknown provenance remains unknown; incompatible/null totals never gain a delta; originals/reviews remain unchanged; Provider.request forbidden. Relative effort: **small** for freshness/filtering, **small-to-medium** for richer difference explanations.

## 2. Exports: convenient analysis without losing the audit record

The present [export service](../backend/app/services/exports.py) already preserves typed JSON, Decimal strings, nulls, flags and history. Its mixed-record CSV is rich but cumbersome for ordinary spreadsheet analysis. Improve usability without replacing the existing archival formats:

1. Offer a simple criterion table with one row per run/basis/criterion and explicit disposition, answer label, raw value, weight, points, total availability and source/version IDs. Keep current nested JSON/history export available.
2. Export an explicitly selected, bounded set of saved run IDs. If adding filtered export, reuse a validated queue-filter contract server-side and freeze the exact selected revisions; do not accidentally export all datasets or silently choose another checklist.
3. Include an export manifest with generation time, format/schema version, run IDs/updated_at, source/checklist hashes, included bases and excerpt/redaction policy. Most per-run identity already exists. Add build identity only when known; never invent it.
4. Preserve a single read snapshot across a batch. Retain Unicode, formula protection, private-field filtering and opt-in excerpts in every derived format. An export can contain sensitive source quotations even with credentials removed; do not label it anonymized.

Acceptance: exported IDs equal the explicit selection; shared source IDs in different dataset groups stay distinct; all values reconcile to that read snapshot, including concurrent review, missing usage, N/A and unresolved totals. No jobs or ledger entries are created. Relative effort: **small** for a simple CSV, **medium** for batch/filter consistency. No paid summarization/PDF service or new provider integration is needed.

## 3. Search and presets: complete match navigation and predictable persistence

Current [search](../backend/app/services/search.py) returns five source-based snippets plus the full matching-message count. A broad Cyrillic query in the audit had **43 conversation rows with additional matches beyond those shown**. Ordinary users can open the complete transcript, but better match navigation would save work.

- Highlight the exact literal match with React text/mark elements, using offsets mapped to original Unicode text. Do not inject HTML or replace source text with normalized/generated text.
- Add next/previous match or a bounded page of message matches. Preserve source revision/hash, transcript order and full counts when moving beyond the first five.
- Optimize pure speaker searches and avoid building source-offset maps/snippets for every match after the visible limit. Reduce full historical evaluation loading in the queue query while retaining older pending-appeal links. Benchmark before adding an index.
- Give presets distinct update/save-as/rename actions. Use a versioned, validated persistence record that can migrate older preset schemas. Saving the preset and active selection in one record avoids a partial write if browser storage fails between the current two writes. Add multi-tab change handling and explicit missing-dataset/version messages.
- Portable preset JSON can support another browser without introducing accounts or a backend synchronization service. Treat saved search text as potentially private; sharing a preset should be explicit, with a clear included-fields preview.

Fifteen audit requests over the actual 75-record copy had median **181.51 ms**, maximum **293.26 ms**, measured through TestClient. This includes database loading and serialization; it is not a production benchmark or a promise about larger datasets. A 200 ms client debounce is additional. These measurements support targeted local optimization before index/schema complexity.

Acceptance: the same RU/KZ/EN/NFC/casefold/literal-punctuation results and total counts; all matches remain reachable on their actual revision; old preset schemas migrate without losing valid entries; storage failures cannot claim successful persistence; late results do not reappear. Relative effort: **small-to-medium**. Embeddings, ASR, semantic-search APIs and a vector database are unnecessary for these refinements.

## Order and boundaries

1. **Fix comparison freshness** and add its regression: a known defect in an adopted feature.
2. **Improve comparison signal and simple CSV usability** using stored data.
3. **Complete match navigation and preset persistence**, then measure query loading again.
4. Consider batch export, unknown-flag filters and clearer configuration/cost provenance if users need them.

All can be implemented incrementally with **$0 additional model inference**. None proves model judgment accuracy or replaces organizer control/replacement testing. Keep independent validation separate from the archived manual packet; do not reinstate that packet as a delivery requirement. Do not import a vendor's automatic-fail penalty, time threshold, greeting cap or uncertain-to-N/A behavior when it conflicts with our PDFs. Full CRM reconstruction, authentication/team permissions and new AI scoring/coaching are outside these refinements.

No recommendation in this report was implemented during the audit. Current software issue, remaining submission gaps and preservation evidence are recorded in the [audit report](audits/2026-11-07/13-post-features-pdf-audit.md). Demo execution remains explicitly deferred.
