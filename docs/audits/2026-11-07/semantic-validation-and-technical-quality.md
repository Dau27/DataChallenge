# Semantic validation and technical product-quality audit

Date: 7 November 2026. Scope: the current local implementation, alongside the separate comparison/export/search refinement task. The starting Git checkpoint was `589d7a4`; that task's uncommitted changes were present. This audit does not certify that concurrent task's final build.

## Implementation follow-up — prioritized fixes completed

The fixes are applied to the shared working tree on top of merged checkpoint `c49da39`. They were first implemented/tested in an isolated checkout, then integrated only after verifying that the destination files had no concurrent unstaged edits. The latest design, Compare & export disclosure, and the other chat's export/search/preset refinements were preserved. Concurrent edits to the queue/export controls and their integration tests were left to their owning chat. This task did not stage, commit or push changes.

Implemented:

- **T1–T3, UI consistency:** [a shared resource loader](../../../frontend/src/useLatestResource.ts) keys data and errors by resource identity, rejects obsolete successes/failures, handles A → B → A selections, and deduplicates overlapping reads. [Detail](../../../frontend/src/Detail.tsx) verifies both the run ID and conversation revision, hides the previous assessment during a new load, retains an explicit selection, and offers retry. [App](../../../frontend/src/App.tsx) keeps queue results tied to the selected checklist and verifies returned evaluation checklist IDs. Polls wait for the preceding read instead of overlapping it. The existing layout/accessibility changes remain present.
- **Safe semantic checks:** N/A reasons reject the same placeholders as missing-basis reasons, including surrounding whitespace/separators. For the exact initial contact, consultation, closing and critical-flag definitions, positive human-action judgments require an operator citation; positive contact also cites the first human response. The existing courtesy-only closing check remains. Validation failures use the existing one-repair path or remain failed without an invented result.
- **Changed-rule boundaries:** these source checks are scoped by exact definition and answer type, not criterion ID/name. A rename preserves applicable protection; a genuinely changed definition does not inherit an unrelated initial-rule assumption. Negative/absence and N/A judgments can still cite relevant client/system context. These checks establish citation adequacy, not general semantic truth.
- **T4, scale precision:** unrepresentable anchors are rejected before saving an immutable version, with a field-specific preview/save error. Ordinary decimal anchors such as `0.1`/`0.2` round-trip through schema, decoder and scoring. No existing version is rewritten.
- **Cache provenance:** evidence validation is versioned as `source-initial-human-evidence-v2`; incompatible old cache identities are not reused as newly validated outputs. Original model/prompt metadata, the scoring formula, response shape, rubric seeds and paid limit remain unchanged.

The original 19 unsupported/unverified probes now produce **five rejections and 14 remaining acceptances**. Fixed probes: **NA-05, CONS-03, EVID-01, EVID-02, EVID-03**. All **12 controls** retain their intended outcomes. The 14 remaining cases include fabricated source events, explanation/value contradictions, unsupported policy truth and arbitrary edited natural-language rules. They are documented limitations, not claimed fixed by a larger keyword list. The reviewer remains an explicit authority boundary; model-only source guards are not silently imposed on prior reviewer decisions.

### Verification of the combined working tree

- Full backend: **207 passed**, one existing Starlette/AnyIO deprecation warning. The 34 new safety tests cover roles, first-human boundaries, supported RU/KZ/EN citations, absence/N/A context, changed definitions, placeholders, repair/failure persistence, cache identity and scale precision.
- Full frontend: **77 passed / one paid opt-in skipped**. Ten new freshness regressions cover late success/error, rapid reselection, route changes, wrong run/source IDs, retry, unmount and deduplicated polling/manual refresh. The former audit-only defect probes now import these assertions of corrected behavior.
- TypeScript/Vite production build: **passed**. `pip check`: **clean**.
- Final offline boundary harness: **31 expected outcomes matched**, five unsupported probes rejected, 14 remaining accepted; precision failure blocked before configuration save. Injected job/reviewer checks remain synthetic and in memory. **Zero outbound/model requests** in the harness.
- Selected DEV: **130/130 original/effective snapshots validate and exactly recalculate**, including the strengthened source-citation checks; **64 complete / one needs review** remains unchanged.
- Historical compatibility sweep: **396 original/effective snapshots inspected**; **394 validate and exactly recalculate**. Two old snapshots already fail the preceding placeholder-uncertainty rule; they are retained unchanged. **Zero previously accepted historical snapshots gained a new validation rejection.**

Actual final commands:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -u scripts/audit_validation_gaps.py --saved-db local_data/cqa.sqlite3 --output local_data/validation_fixes_20261107/final-root-audit.json
cd frontend
$env:CQA_LIVE_SMOKE='0'
npm test
npm run build
```

New regression sources: [frontend freshness](../../../frontend/src/freshness.test.tsx), [backend safety](../../../backend/tests/test_validation_safety.py). Existing synthetic transport fixtures were corrected to cite their actual operator turn; domain-only fixtures retain their previous default. No real conversation was edited to make a test pass.

Before/after main-table and protected-file fingerprints match the baseline recorded before implementation. The private SQLite backup, integration snapshots, final audit output and compatibility results are under ignored `local_data/validation_fixes_20261107/`. All **249 main evaluations**, originals/effective results, reviews, appeals, credentials, both seeds and the budget baseline are preserved. Added paid inference remains **$0.00**. Prompt v13 still has no new live validation; no accuracy percentage is inferred from these tests. Demo work remains deferred.

The subsequent [backend follow-up](backend-performance-and-limits.md) addresses T5's full-history loading cost and adds import-stream limits while preserving saved results. T6 prompt/schema-efficiency recommendations remain open. The original audit below records the **pre-fix** findings and measurements.

## Original audit outcome — before these fixes

**The main quality gap is that a structurally valid judgment can still be unsupported by its source.** Offline probes reproduced **19 accepted unsupported or unverified judgments**, with **12 control checks** behaving as expected. The unsupported probes also conform to the subset of generated provider-schema keywords checked by the audit harness. These are deliberately constructed counterexamples, not 19 newly discovered errors in saved DEV results and not a measured model error rate.

One partial-consultation probe reached the real job claim/evaluate/score/persist path as **succeeded, complete, 100.00**, using an isolated **one-criterion synthetic checklist** and an injected static response. No hosted inference occurred. Three separate reviewer-path probes were also accepted while retaining their synthetic originals.

Technical diagnostics reproduced **two asynchronous UI races** and **one missing run-identity check** outside the comparison panel being fixed by the other chat. A separate custom-scale precision edge case is reproducible. Historical-data loading also has a measured growth cost, although it remains manageable at the current dataset size.

**Saved results are preserved.** The selected 65 DEV results remain **64 complete / one needs review**. All **130 original/effective snapshots** validate and recalculate exactly; the narrow source-evidence guard accepts all 130. All eight main database tables, `.env`, both seed files and the budget baseline are unchanged. Added paid inference: **$0.00**; outbound requests in the semantic/performance harness: **zero**. Demo and delivery work remain deferred.

## Scope and reproducibility

New files owned by this audit:

- [Offline semantic/persistence/performance harness](../../../scripts/audit_validation_gaps.py).
- [Isolated UI diagnostics](../../../tests/audits/technical_freshness.audit.test.tsx).
- [Dedicated diagnostic Vitest configuration](../../../tests/audits/vitest.audit.config.mjs).
- This report.

No existing application, test, configuration, report index or `CURRENT_CONTEXT.md` was edited. In particular, the other chat retains ownership of its comparison/export/search/preset work and its report updates. No Git staging, commit, push, publication, server launch or organizer request was performed here.

Commands actually run successfully from the repository root:

```powershell
.\.venv\Scripts\python.exe -u scripts/audit_validation_gaps.py --saved-db local_data/cqa.sqlite3 --profile-history --output local_data/validation_bottleneck_audit_20261107/audit-final.json

$env:CQA_LIVE_SMOKE='0'
node frontend/node_modules/vitest/vitest.mjs run --config tests/audits/vitest.audit.config.mjs

.\.venv\Scripts\python.exe -m pytest backend/tests/test_evaluator_context.py backend/tests/test_scoring_corrections.py backend/tests/test_scoring.py -q -p no:cacheprovider
```

Results: **31 semantic/control probes matched their expected outcomes; three UI diagnostics passed; 54 existing backend tests passed** with one existing Starlette/AnyIO deprecation warning. A precision diagnostic and synthetic job/reviewer integration checks also passed. The dedicated audit tests intentionally reproduce current defects; a passing diagnostic does **not** mean a defect is fixed. Convert them to assertions of the intended behavior when implementing the fixes, rather than adding the current defect expectations unchanged to the ordinary suite.

The Python harness blocks socket connections and the real `Provider.request`. Its injected `StaticProvider` returns explicitly synthetic JSON without HTTP. It opens the real SQLite source with `mode=ro` and `query_only=ON`. All job/reviewer writes and amplified history exist only in separate in-memory databases. The UI tests replace `fetch` with synthetic responses and reject unexpected paths. Private JSON evidence and source fingerprints are under ignored `local_data/validation_bottleneck_audit_20261107/`.

## What validation currently establishes

[Provider decoding](../../../backend/app/services/evaluator.py) checks exact criterion coverage, exclusive decision branches, strict applicability flags and consistency between the flag and selected branch. [Domain validation](../../../backend/app/domain.py) checks dispositions, strict types, configured scale membership, N/A permission/reasons, non-placeholder uncertainty reasons, and ordered existing evidence IDs. [Scoring](../../../backend/app/services/scoring.py) calculates the configured arithmetic deterministically.

The additional source check in `validate_source_evidence` rejects a narrow case: a positive binary answer with the **exact initial closing description**, whose cited operator messages contain only recognized courtesy/farewell phrases. It does not generally establish applicability, consultation completeness, factual correctness, role attribution, or explanation/answer agreement.

The generated schema's `na_condition_met` is another model assertion. Checking that it agrees with the chosen N/A branch does not establish that the condition occurred. A schema-compatible response can be consistently wrong.

### N/A: six accepted probes

| Probe | Source/answer mismatch that still passes |
| --- | --- |
| NA-01 | The human asks for a necessary missing platform, but the response claims initial information was sufficient and returns Needs N/A. |
| NA-02 | A sufficiently specific initial request receives instructions without clarification, but Needs is Yes rather than the seed's N/A. |
| NA-03 | A concrete customer request is present, but Consultation is N/A with a claim that no request was formulated. |
| NA-04 | A complete normal closing is visible, but Closing is N/A with a fabricated premature interruption. |
| NA-05 | An N/A reason of `none` passes the nonblank check. The analogous uncertainty placeholder is rejected. |
| NA-06 | The synthetic human explicitly discloses private account data without verification, but Identification is N/A on a claim that only general instructions were given. |

Effect: false N/A can remove an applicable criterion's weight; false applicability can add a criterion that should be excluded. The arithmetic then accurately calculates a score from the wrong judgment. For a checklist with no other applicable weight, an accepted N/A produces a null total; it does not necessarily inflate every score.

### Consultation: four accepted probes

| Probe | Source/answer mismatch that still passes |
| --- | --- |
| CONS-01 | The operator answers one of two material questions. The explanation explicitly acknowledges the omission, yet the value is the maximum 20. |
| CONS-02 | The explanation states the entire request was answered and success confirmed, yet the value is 0. |
| CONS-03 | A bot answers while the human refuses to answer; bot evidence supports a maximum human consultation score. |
| CONS-04 | An official fee-policy assertion receives maximum credit without any authoritative policy source. This proves unverified correctness can pass, not that the assertion is factually false. |

CONS-01 also passed the normal `Jobs` claim/evaluation/persistence path in memory. An invalid semantic input was saved with a mathematically correct maximum total for its isolated checklist. No fake result was added to the main database.

### Changed criteria: four accepted probes

| Probe | Gap reproduced |
| --- | --- |
| RULE-01 | A meaning-preserving English paraphrase of the compound closing definition accepts courtesy-only evidence because the exact-description guard no longer applies. |
| RULE-02 | A new criterion requires literal marker `AUDIT-CASE-42`; a positive answer passes when the marker is absent. |
| RULE-03 | An edited N/A condition requires a specific system disconnect event; N/A passes without that event. |
| RULE-04 | A changed consultation maximum anchor requires an absent literal marker; its allowed numeric value still passes. |

The controls establish both boundaries: renaming only the closing ID keeps its existing guard, while a genuinely changed goodbye-only definition correctly accepts goodbye without a recap. Applying the old compound rule to every edited criterion would therefore create a new defect. Configuration changes must retain exact snapshot/cache identity; semantic checks need explicit applicability to the saved definition.

### Evidence and uncertainty: five accepted probes

| Probe | Gap reproduced |
| --- | --- |
| EVID-01 | Human contact receives credit supported only by a bot greeting/introduction. |
| EVID-02 | A customer insult produces a positive operator critical-violation flag. |
| EVID-03 | Positive initial closing cites only a client message. The source check skips rejection because its cited operator-message list is empty. |
| EVID-04 | A visible greeting is withheld for an invented, non-placeholder policy requirement. Naming a missing basis is not proof that it is actually needed. |
| EVID-05 | Unrelated operator text, such as a code, passes positive closing because it is not entirely on the courtesy blacklist. |

These show why increasing a courtesy keyword list cannot serve as a general multilingual semantic validator. Evidence existence, evidence precision, speaker attribution and actual support are separate properties.

### Controls that remain effective

Ten rejection controls reproduced existing protections: initial-rule courtesy-only closing, forbidden N/A, integer-as-boolean, unconfigured scale value, contradictory N/A flag/branch, nonexistent evidence, reversed evidence, placeholder uncertainty, obsolete criterion coverage, and renamed-ID initial closing. Two supported acceptance controls passed: an intentionally changed goodbye-only definition and a genuine help offer plus farewell under the initial definition.

The small fixture checker covers only the JSON Schema keywords emitted by the current `output_schema`, and fails on an unknown emitted keyword. It is not an independent general-purpose schema validator or evidence of hosted-provider enforcement. Its purpose is to rule out malformed synthetic response shapes as the explanation for the 19 semantic acceptances.

## Reviewer boundary and saved-data evidence

[Reviewer decisions](../../../backend/app/services/reviews.py) call domain validation and scoring, but do not call `validate_source_evidence`. In memory, reviewer replacements accepted NA-01, CONS-01 and the initial courtesy-only closing that the evaluator rejects. All three retained their original assessment. Human review is an authority boundary, so it may intentionally have different controls; the product should make that distinction explicit. A narrow provable inconsistency can be shown as a reviewer warning with a recorded override rationale rather than assuming every model-specific rejection must automatically block the reviewer.

Read-only verification of current DEV selected successes found:

- 65 conversations; **64 complete / one needs review**.
- **130/130** structural snapshots valid and deterministic recalculations exactly equal to stored scores.
- **130/130** accepted by the narrow current source guard.
- Accepted prompt lineage unchanged: **56 v10 / eight v11 / one v12**; this does not validate v13 behavior.
- In the already documented corrected `p1-kz-012`, both the old original (**Needs N/A, Consultation 10, total 84.62**) and reviewed effective result (**Needs assessed, Consultation 20, total 100.00**) pass current validation. The earlier review is preserved; this audit made no new saved judgment.

This is direct evidence of the validation boundary, not an independent relabeling exercise. No new all-dialogue semantic accuracy claim or mandatory manual-review packet is introduced. The unclear call remains unresolved.

## Technical findings that affect product quality

### T1: late assessment responses can revert a selected saved run

**Priority: P2, reproduced.** In [Detail.tsx](../../../frontend/src/Detail.tsx), `load` has no current-request identity or cleanup guard. The diagnostic starts loading run A, selects B, resolves B, then resolves the older A request. The panel returns to A and the saved-run selector also reverts. This is a race in the main assessment screen, separate from `SavedComparison`.

Fix acceptance: retain the explicit selection; hide any assessment whose request identity no longer matches it; ignore late successes and failures; verify response `id` and `conversation_id`. Cover rapid selection, polling, review reload, unmount and failed replacement loads. A monotonic request sequence or equivalent identity guard should protect every state commit; cancellation can additionally avoid work.

### T2: late queue responses can show another checklist's results

**Priority: P2, reproduced.** [App.tsx](../../../frontend/src/App.tsx) publishes all four `Promise.all` responses without checking the checklist/request identity. With v1 loaded, select v2 and then v3; let v3 finish first and v2 finish later. The picker remains v3 while the queue shows v2's returned row/results.

Fix acceptance: key the visible queue and its response commits by selected checklist and refresh generation; suppress stale errors too. Preserve the last result only with an explicit matching identity/loading state. Avoid overlapping periodic refreshes when a prior refresh is still outstanding.

### T3: detail response identity is only partially checked

**Priority: P3 defensive consistency gap, reproduced.** A request for run A that receives run B from the same conversation is accepted. The selector remains A while B's explanation is displayed. The current backend was not observed returning the wrong ID; this diagnostic establishes the missing client boundary check. Verify the requested run ID as well as the conversation revision. This complements T1 rather than replacing request-order protection.

### T4: valid custom Decimal anchors can become unreachable numeric answers

**Priority: P3 edge case, reproduced.** A checklist accepts anchors `0.10000000000000000001` and `0.10000000000000000002`. Generated provider-schema values both become the float `0.1`; the decoded answer `0.1` equals neither saved Decimal anchor and is rejected after repair. The initial integer-anchor rubric is unaffected.

Fix acceptance: either reject unsupported numeric precision before saving with a specific field error, or preserve an agreed numeric representation throughout schema construction, decoding and scoring. Test distinct-anchor round trips and large/noninteger values. Changing only the decoder would not fix the schema's earlier float collapse.

### T5: queue and budget refresh costs grow with history

**Priority: P3 at the present size; measured scaling concern.** [The queue endpoint](../../../backend/app/main.py) loads all conversation revisions and full evaluation objects before selecting latest results in Python. [Budget status](../../../backend/app/services/budget.py) also validates historical coverage. Full JSON judgments and attempt histories are therefore loaded for views that mainly need summaries.

The final diagnostic copied SQLite to RAM and retained the same **75 returned conversations**, multiplying only historical evaluation rows. Three trials per case measured route-function work, excluding HTTP, response-model serialization and browser rendering:

| Historical evaluation rows | Median queue time | Observed minimum–maximum |
| ---: | ---: | ---: |
| 249 | 99.09 ms | 94.29–132.66 ms |
| 1,245 | 459.29 ms | 452.31–487.51 ms |
| 4,980 | 2,240.28 ms | 2,218.55–2,483.00 ms |

At the current size, literal search measured **150.54 ms** median and budget status **91.00 ms**. These are one-machine RAM-copy diagnostics with duplicated history, not a production-capacity forecast. Existing root/detail polling intervals are 2.5/1.8 seconds while processing; history growth can make overlapping work and stale responses more likely.

Recommended direction: query latest summaries with SQL filtering/projections, load full assessments only on demand, use bounded queue pagination when needed, and make refreshes independent of unrelated history. Retain historical budget reconciliation; optimize it with a validated read model/incremental ledger rather than removing accounting safeguards.

### T6: request overhead and regression attribution

Earlier read-only measurements in this chat found historical accepted DEV jobs spent a median **5.31 seconds** in recorded provider calls, excluding queue/backoff; median successful-request input was **10,602 tokens**. Current v13 payload sizing, without sending requests, found median **32,242 characters**, with instructions plus schema accounting for **74.6%**. These are different cohorts/units; character share is not a token-savings or latency forecast.

Reducing repeated instructions/schema content may improve efficiency, but prompt/schema edits can change judgments. First measure component sizes and test complete source retention, criterion coverage and cache-identity changes. Offline shape/replay checks cannot establish behavioral parity for a changed prompt. Keep prompt-version diagnostics separate from UI/arithmetic test success.

## Recommended implementation sequence

1. **Fix T1/T2 and add the T3 identity check after the other chat's checkpoint.** These are bounded product-correctness changes with synthetic acceptance tests and no inference requirement. They should not share simultaneous edits with that task's UI integration.
2. **Harden objectively checkable semantic boundaries.** Reject placeholder N/A explanations consistently; detect unsupported speaker attribution for explicit positive human-action checks; cover empty operator citations in the existing closing guard. Test supported multilingual examples and genuine rule changes before enabling a guard. Keep absence/context evidence valid where the saved criterion calls for it.
3. **Make applicability/completeness claims auditable.** Use precise, source-linked observations for the condition or omitted request when a supported rule permits it. Explicit machine-checkable rules can enforce literal events/markers. Arbitrary natural-language changes remain model/reviewer judgments; do not claim a universal semantic verifier or attach an old rule based only on an unchanged criterion ID.
4. **Address T4 and T5 without changing saved snapshots.** Validate representable custom anchors before save, then introduce lightweight latest-result queries and bounded refresh work. Compare outputs byte-for-byte where appropriate, preserve cross-revision appeal targets, and retain the full accounting audit.
5. **Optimize request overhead only with versioned evidence.** Protect the full transcript, changed criteria and model provenance. Report output-contract tests separately from any future authorized model-behavior validation.

The 19 accepted probes are a useful starting set for future rejection/review regressions, but not every case admits a safe general deterministic fix. A mere non-placeholder reason or a model-generated structured observation still needs source support. No changes to stored originals, effective results, provider configuration or paid limits are proposed as part of this audit.

## Preservation and remaining limits

Before/after logical row fingerprints match for all eight main tables: **75 conversation revisions, five checklist versions, 249 evaluations, nine appeals, nine review decisions, one provider-access check, zero budget-state rows and zero budget-reservation rows**. In-memory profiling bootstrapped its own copied budget state only. Protected-file hashes and the audited domain/evaluator/scoring/reviewer/job source hashes are unchanged.

At the original audit checkpoint, this report added diagnostics and recommendations only; the main UI races were still open. The implementation follow-up above supersedes that state. No current-prompt inference, independent labels, organizer-held control evaluation, submission preparation or demo work was performed. Test counts from concurrent tasks are kept separate from the checks actually run in each phase.
