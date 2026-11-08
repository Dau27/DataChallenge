// SYNTHETIC TEST ONLY. No actual source text or judgments belong in this fixture.
import type { SavedPrintPacket } from './printEvaluationTypes';

export function syntheticPrintPacket(id = 'SYNTHETIC_PRINT_RUN', updatedAt = '2026-11-08T00:00:00+00:00', excerpts = false): SavedPrintPacket {
  const evidence = { kind: 'support' as const, start_message_id: 'm0001', end_message_id: 'm0002' };
  const binary = { disposition: 'assessed' as const, value: true, explanation: 'SYNTHETIC English. Русский: проверено. Қазақша: Ә Ғ Қ Ң Ө Ұ Ү Һ І.', na_reason: null, review_reason: null, evidence: [evidence] };
  const na = { ...binary, disposition: 'not_applicable' as const, value: null, na_reason: 'SYNTHETIC no protected action.' };
  const flag = { ...binary, value: false, explanation: 'SYNTHETIC no critical violation.' };
  const unresolved = { ...binary, disposition: 'needs_review' as const, value: null, review_reason: 'SYNTHETIC missing authority.' };
  const original = { results: { contact: binary, identity: na, critical: flag } };
  const effective = { results: { ...original.results, contact: unresolved } };
  const originalScore = {
    total: '100.00', reason: null, completeness: 'complete', applicable_weight: '10.00', raw_subtotal: '10.00', flags: { critical: false },
    scoring_version: 'SYNTHETIC_SCORER', unresolved_criteria: [],
    criteria: [
      { criterion_id: 'contact', section_id: 'quality', weight: '10.00', applicable: true, raw_points: '10.00', normalized_contribution: '100.0000' },
      { criterion_id: 'identity', section_id: 'quality', weight: '20.00', applicable: false, raw_points: null, normalized_contribution: null },
      { criterion_id: 'critical', section_id: 'flags', weight: null, applicable: false, raw_points: null, normalized_contribution: null },
    ],
    sections: [{ id: 'quality', title: 'SYNTHETIC quality', total: '100.00', reason: null, applicable_weight: '10.00', raw_subtotal: '10.00' },
      { id: 'flags', title: 'SYNTHETIC flags', total: null, reason: 'NO_APPLICABLE_SCORED_WEIGHT', applicable_weight: '0', raw_subtotal: '0' }],
  };
  const effectiveScore = { ...originalScore, total: null, reason: 'UNRESOLVED_CRITERIA', completeness: 'needs_review', raw_subtotal: null,
    unresolved_criteria: ['contact'], criteria: originalScore.criteria.map(r => r.criterion_id === 'contact' ? { ...r, raw_points: null, normalized_contribution: null } : r),
    sections: originalScore.sections.map(s => s.id === 'quality' ? { ...s, total: null, reason: 'UNRESOLVED_CRITERIA', raw_subtotal: null } : s) };
  const source = { id: 'SYNTHETIC_SOURCE_REVISION', source_id: 'SYNTHETIC_SOURCE', group_id: 'SYNTHETIC_TEST_ONLY', revision: 2,
    content_hash: 'SYNTHETIC_SOURCE_HASH', language: 'KZ', channel: 'agent chat', message_count: 2 };
  const packet: SavedPrintPacket = {
    export_schema_version: 1, source,
    evaluation: {
      id, updated_at: updatedAt, created_at: '2026-11-07T23:00:00+00:00', conversation_id: source.id, checklist_id: 8,
      state: 'succeeded', completeness: 'needs_review', total: null, error: null, cached_from: 'SYNTHETIC_CACHED_ORIGINAL', original, effective,
      original_score: originalScore, effective_score: effectiveScore,
      checklist: { id: 8, content_hash: 'SYNTHETIC_CHECKLIST_HASH', created_at: '2026-11-07T22:00:00+00:00', snapshot: {
        schema_version: 1, name: 'SYNTHETIC saved rubric', initial_version_label: null, source: null,
        sections: [{ id: 'quality', title: 'SYNTHETIC quality' }, { id: 'flags', title: 'SYNTHETIC flags' }],
        criteria: [
          { id: 'contact', name: 'SYNTHETIC Contact / Байланыс / Контакт', description: 'SYNTHETIC greeting criterion.', section_id: 'quality', answer_type: 'binary', weight: '10.00', na_allowed: false, na_condition: null, scale: [] },
          { id: 'identity', name: 'SYNTHETIC identity', description: 'SYNTHETIC protected action.', section_id: 'quality', answer_type: 'binary', weight: '20.00', na_allowed: true, na_condition: 'SYNTHETIC no protected action.', scale: [] },
          { id: 'critical', name: 'SYNTHETIC critical flag', description: 'SYNTHETIC violation.', section_id: 'flags', answer_type: 'flag', weight: null, na_allowed: false, na_condition: null, scale: [] },
        ], scoring_policy: {}, source_notes: [],
      } },
      metadata: { provider: 'SYNTHETIC_PROVIDER', model: 'SYNTHETIC_MODEL', prompt_version: 'SYNTHETIC_PROMPT', schema_version: 'SYNTHETIC_SCHEMA',
        prompt_hash: 'SYNTHETIC_PROMPT_HASH', schema_hash: 'SYNTHETIC_SCHEMA_HASH', generation: { temperature: 0 } },
      usage: { request_attempts: 1, input_tokens_known: 12, output_tokens_known: 15, usage_complete: false, estimated_cost_usd: null, cost_rate_source: null, latency_ms: 55 },
      attempts: [{ number: 1, status: 'SYNTHETIC_SAVED', latency_ms: 55, input_tokens: 12, output_tokens: 15 }],
      appeals: [{ id: 'SYNTHETIC_APPEAL', criterion_id: 'contact', comment: 'SYNTHETIC appeal comment.', status: 'open', created_at: updatedAt }],
      reviews: [{ id: 4, appeal_id: 'SYNTHETIC_APPEAL', evaluation_id: id, criterion_id: 'contact', action: 'replace', rationale: 'SYNTHETIC reviewer rationale.',
        judgment: unresolved, resulting_score: effectiveScore, created_at: updatedAt }],
    },
    export_policy: { source_excerpts_included: excerpts, recording_urls_included: false, credentials_included: false,
      notice: 'SYNTHETIC stored results and review history, not a new evaluation.', redacted_string_occurrences: 2 },
    manifest: { schema_version: 1, generated_at: updatedAt, selected_run_count: 1, answer_sets: ['original', 'effective'], source_excerpts_included: excerpts,
      notice: 'SYNTHETIC saved selection; not anonymous.', runs: [{ evaluation_id: id, updated_at: updatedAt, conversation_id: source.id,
        source_id: source.source_id, group_id: source.group_id, revision: source.revision, source_hash: source.content_hash, checklist_id: 8, checklist_hash: 'SYNTHETIC_CHECKLIST_HASH' }] },
  };
  if (excerpts) packet.source_excerpts = [{ basis: 'original', criterion_id: 'contact', evidence, range_available: true, messages: [
    { id: 'm0001', speaker: 'operator', timestamp: '00:01', text: 'SYNTHETIC source excerpt. Қазақша: Қош келдіңіз. Русский: Здравствуйте. English: Hello.' },
    { id: 'm0002', speaker: 'client', timestamp: '00:02', text: 'SYNTHETIC source reply.' },
  ] }];
  return packet;
}
