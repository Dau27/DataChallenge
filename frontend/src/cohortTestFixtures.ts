// Explicitly synthetic cohort/component fixtures. Never imported by application code.
import type { CohortOptions, CohortPair, CohortRequest, CohortResult, CohortSide } from './cohortTypes';
import type { SavedComparison } from './types';

export const cohortOptionsFixture = (): CohortOptions => ({ version: 1, max_pairs: 200,
  datasets: [{ dataset_group_id: 'DEV', source_revision_count: 2, saved_evaluation_count: 3, checklists: [{ checklist_id: 1, run_count: 3,
    fields: { model: { values: [{ value: 'A', count: 2 }, { value: 'B', count: 1 }], unknown_count: 0 },
      prompt_version: { values: [{ value: 'p1', count: 3 }], unknown_count: 0 }, schema_version: { values: [{ value: 's1', count: 3 }], unknown_count: 0 },
      evidence_validation_version: { values: [], unknown_count: 3 } } }] },
    { dataset_group_id: 'SYNTHETIC_ONLY', source_revision_count: 2, saved_evaluation_count: 0, checklists: [] }],
  checklists: [{ checklist_id: 1, content_hash: 'CHECKLIST' }, { checklist_id: 2, content_hash: 'CHECKLIST2' }],
  selector_fields: ['model', 'prompt_version', 'schema_version', 'evidence_validation_version'], unavailable_dataset_identifiers: 0,
  unknown_policy: 'SYNTHETIC unknown policy', selection_policy: 'SYNTHETIC latest exact revision', scope_policy: 'SYNTHETIC all revisions; no truncation', notice: 'Historical differences, not accuracy.' });

export function cohortSideFixture(id: string, source: string, selector: CohortRequest['left'], total = '100.00'): CohortSide {
  return { evaluation_id: id, conversation_id: source, checklist_id: selector.checklist_id, checklist_hash: 'CHECKLIST',
    created_at: '2026-11-08T00:00:00+00:00', updated_at: '2026-11-08T00:00:00+00:00', state: 'succeeded', completeness: 'complete', run_completeness: 'complete',
    original_available: true, effective_available: true, basis_available: true, criterion_coverage_valid: true, total, total_state: 'numeric', score_reason: null, saved_scoring_version: 'score1',
    cached: false, cached_from: null, cache_origin_present: false, cache_source_matches: null, provenance_conflict: false,
    provenance: { provider: 'SYNTHETIC', model: Object.hasOwn(selector, 'model') ? selector.model! : 'A', prompt_version: Object.hasOwn(selector, 'prompt_version') ? selector.prompt_version! : 'p1',
      schema_version: Object.hasOwn(selector, 'schema_version') ? selector.schema_version! : 's1', evidence_validation_version: Object.hasOwn(selector, 'evidence_validation_version') ? selector.evidence_validation_version! : null,
      mode: 'TEST/MOCK', scoring_version: 'score1', prompt_hash: null, schema_hash: null, request_schema_hash: null, checklist_hash: null,
      unknown_fields: ['evidence_validation_version', 'prompt_hash', 'schema_hash', 'request_schema_hash', 'checklist_hash'], generation_recorded: false, generation: {}, response_models: [] } };
}
export const cohortRequestFixture = (): CohortRequest => ({ dataset_group_id: 'DEV', left: { checklist_id: 1, model: 'A' }, right: { checklist_id: 1, model: 'B' }, basis: 'effective', limit: 200 });
export function cohortResultFixture(request = cohortRequestFixture()): CohortResult {
  const yes = { disposition: 'assessed' as const, value: true, reason: null };
  const no = { disposition: 'assessed' as const, value: false, reason: null };
  const missing = { disposition: 'unavailable' as const, value: null, reason: 'missing_run' };
  const pair = (id: string, missingRight = false): CohortPair => ({ source: { conversation_id: id, source_id: `SYNTHETIC_${id}`, revision: 1, content_hash: `HASH_${id}`, dataset_group_id: request.dataset_group_id },
    left: cohortSideFixture(`A_${id}`, id, request.left), right: missingRight ? null : cohortSideFixture(`B_${id}`, id, request.right, '0.00'),
    status: missingRight ? 'missing_right' : 'matched', reasons: missingRight ? ['CANDIDATE_RUN_MISSING'] : [], total_comparable: !missingRight, total_difference: missingRight ? null : '-100.00',
    criteria: [{ criterion_id: 'contact', answer_comparable: !missingRight, left: yes, right: missingRight ? missing : no, changes: missingRight ? [] : ['answer', 'points'], points_difference: missingRight ? null : '-1' }] });
  return { version: 1, ...request, selection_policy: 'Latest matching (created_at DESC, id DESC)', scope_policy: 'Every exact revision in selected dataset', coverage_policy: 'SYNTHETIC exclusive coverage',
    notice: 'Historical differences, not evaluator accuracy.',
    coverage: { matched: 1, missing_left: 0, missing_right: 1, missing_both: 0, failed: 0, pending: 0, unresolved: 0, incompatible: 0, no_numeric_total: 0, invalid: 0,
      source_revisions: 2, paired: 1, cached_pairs: 0, same_run_pairs: 0, unknown_provenance_pairs: 2, provenance_conflict_pairs: 0 },
    total_difference: { count: 1, sum: '-100.00', mean: '-100.00' }, pairs: [pair('C1'), pair('C2', true)],
    criteria: [{ criterion_id: 'contact', left_name: 'SYNTHETIC Contact', right_name: 'SYNTHETIC Contact', left_type: 'binary', right_type: 'binary', denominator: 2,
      answer_comparable_count: 1, answer_changed_count: 1, disposition_changed_count: 0, configuration_changed_count: 0, definition_changed_count: 0, details_only_count: 0, unavailable_count: 1,
      transitions: [{ left: yes, right: no, answer_comparable: true, count: 1, conversation_ids: ['C1'] }, { left: yes, right: missing, answer_comparable: false, count: 1, conversation_ids: ['C2'] }],
      points_difference: { count: 1, sum: '-1', mean: '-1' } }] };
}

export function exactPairFixture(pair: CohortPair, basis: 'original' | 'effective' = 'effective'): SavedComparison {
  const criterion = { id: 'contact', name: 'SYNTHETIC Contact', description: 'SYNTHETIC fixture rule', section_id: 'test', answer_type: 'binary' as const, weight: 1, na_allowed: false, na_condition: null, scale: [] };
  const judgment = (value: boolean) => ({ disposition: 'assessed' as const, value, explanation: 'SYNTHETIC only', na_reason: null, review_reason: null,
    evidence: [{ kind: 'support' as const, start_message_id: 'm0001', end_message_id: 'm0001' }] });
  const side = (run: CohortSide): SavedComparison['left'] => ({ id: run.evaluation_id, basis, state: run.state, error: null, created_at: run.created_at,
    updated_at: run.updated_at, cached_from: null, checklist: { id: 1, content_hash: 'CHECKLIST', created_at: '', snapshot: { schema_version: 1, name: 'SYNTHETIC',
      initial_version_label: null, source: null, source_notes: [], scoring_policy: {}, sections: [{ id: 'test', title: 'SYNTHETIC' }], criteria: [criterion] } },
    score: null, metadata: { mode: 'TEST/MOCK' }, usage: { request_attempts: 0, input_tokens_known: 0, output_tokens_known: 0, usage_complete: false, estimated_cost_usd: null, cost_rate_source: null, latency_ms: 0 }, review_count: 0 });
  return { source: { id: pair.source.conversation_id, source_id: pair.source.source_id, content_hash: pair.source.content_hash, revision: pair.source.revision },
    left: side(pair.left!), right: side(pair.right!), total_comparable: true, total_difference: '-100.00', notice: 'SYNTHETIC historical difference',
    criteria: [{ criterion_id: 'contact', change: 'changed', changes: ['answer', 'points'], configuration_changes: [], answer_comparable: true, points_difference: '-1',
      left: { criterion, judgment: judgment(true), points: { raw_points: '1', normalized_contribution: '100' } },
      right: { criterion, judgment: judgment(false), points: { raw_points: '0', normalized_contribution: '0' } } }] };
}
