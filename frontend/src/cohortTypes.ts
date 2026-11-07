export const cohortFields = ['model', 'prompt_version', 'schema_version', 'evidence_validation_version'] as const;
export type CohortField = typeof cohortFields[number];
export type CohortBasis = 'original' | 'effective';
export type CohortSelector = { checklist_id: number } & Partial<Record<CohortField, string | null>>;
export type CohortRequest = { dataset_group_id: string; left: CohortSelector; right: CohortSelector; basis: CohortBasis; limit: number };
export type CohortFieldOptions = { values: { value: string; count: number }[]; unknown_count: number };
export type CohortProfile = { checklist_id: number; run_count: number; fields: Record<CohortField, CohortFieldOptions> };
export type CohortOptions = { version: 1; datasets: { dataset_group_id: string; source_revision_count: number; saved_evaluation_count: number; checklists: CohortProfile[] }[];
  checklists: { checklist_id: number; content_hash: string }[]; selector_fields: CohortField[]; unavailable_dataset_identifiers: number;
  unknown_policy: string; selection_policy: string; scope_policy: string; notice: string; max_pairs: 200 };
export const pairStatuses = ['matched', 'missing_left', 'missing_right', 'missing_both', 'failed', 'pending', 'unresolved', 'incompatible', 'no_numeric_total', 'invalid'] as const;
export type CohortPairStatus = typeof pairStatuses[number];
export type CohortStatistic = { count: number; sum: string | null; mean: string | null };
export type CohortAnswer = { disposition: 'assessed' | 'not_applicable' | 'needs_review' | 'unavailable'; value: boolean | string | null; reason: string | null };
export type CohortProvenance = Record<CohortField, string | null> & { provider: string | null; mode: string | null; scoring_version: string | null;
  prompt_hash: string | null; schema_hash: string | null; request_schema_hash: string | null; checklist_hash: string | null;
  unknown_fields: string[]; generation_recorded: boolean; generation: Record<string, number | string | null>; response_models: string[] };
export type CohortSide = { evaluation_id: string; conversation_id: string; checklist_id: number; checklist_hash: string;
  created_at: string; updated_at: string; state: string; completeness: string; run_completeness: string; original_available: boolean; effective_available: boolean; basis_available: boolean; criterion_coverage_valid: boolean;
  total: string | null; total_state: 'numeric' | 'missing' | 'invalid'; score_reason: string | null; saved_scoring_version: string | null; cached: boolean; cached_from: string | null;
  cache_origin_present: boolean; cache_source_matches: boolean | null; provenance: CohortProvenance; provenance_conflict: boolean };
export type CohortPair = { source: { conversation_id: string; source_id: string; revision: number; content_hash: string; dataset_group_id: string };
  left: CohortSide | null; right: CohortSide | null; status: CohortPairStatus; reasons: string[]; total_comparable: boolean; total_difference: string | null;
  criteria: { criterion_id: string; answer_comparable: boolean; left: CohortAnswer; right: CohortAnswer; changes: string[]; points_difference: string | null }[] };
export type CohortTransition = { left: CohortAnswer; right: CohortAnswer; answer_comparable: boolean; count: number; conversation_ids: string[] };
export type CohortCriterion = { criterion_id: string; left_name: string | null; right_name: string | null; left_type: string | null; right_type: string | null;
  denominator: number; answer_comparable_count: number; answer_changed_count: number; disposition_changed_count: number; configuration_changed_count: number; definition_changed_count: number;
  details_only_count: number; unavailable_count: number; transitions: CohortTransition[]; points_difference: CohortStatistic };
export type CohortResult = { version: 1; dataset_group_id: string; left: CohortSelector; right: CohortSelector; basis: CohortBasis; limit: number;
  selection_policy: string; scope_policy: string; coverage_policy: string; notice: string;
  coverage: Record<CohortPairStatus, number> & { source_revisions: number; paired: number; cached_pairs: number; same_run_pairs: number; unknown_provenance_pairs: number; provenance_conflict_pairs: number };
  total_difference: CohortStatistic; pairs: CohortPair[]; criteria: CohortCriterion[] };

export const cohortSelectorKey = (selector: CohortSelector) => JSON.stringify([selector.checklist_id,
  ...cohortFields.map(field => [Object.hasOwn(selector, field), selector[field] ?? null])]);

export function cohortResultMatches(data: CohortResult, request: CohortRequest) {
  try { return resultMatches(data, request); } catch { return false; }
}

function resultMatches(data: CohortResult, request: CohortRequest) {
  if (!data || data.version !== 1 || data.dataset_group_id !== request.dataset_group_id || data.basis !== request.basis || data.limit !== request.limit
      || !data.left || !data.right || cohortSelectorKey(data.left) !== cohortSelectorKey(request.left) || cohortSelectorKey(data.right) !== cohortSelectorKey(request.right)
      || !Array.isArray(data.pairs) || data.pairs.length > request.limit || !Array.isArray(data.criteria) || !data.coverage
      || data.coverage.source_revisions !== data.pairs.length || !statisticValid(data.total_difference, data.pairs.length)) return false;
  const ids = new Set<string>();
  for (const pair of data.pairs) {
    if (!pair.source || typeof pair.source.conversation_id !== 'string' || !pair.source.content_hash || pair.source.dataset_group_id !== request.dataset_group_id
        || ids.has(pair.source.conversation_id) || !pairStatuses.includes(pair.status) || !Array.isArray(pair.criteria)) return false;
    ids.add(pair.source.conversation_id);
    if (pair.left === undefined || pair.right === undefined || typeof pair.total_comparable !== 'boolean') return false;
    if (pair.status === 'missing_both' ? pair.left !== null || pair.right !== null
      : pair.status === 'missing_left' ? pair.left !== null || pair.right === null
      : pair.status === 'missing_right' ? pair.left === null || pair.right !== null : pair.left === null || pair.right === null) return false;
    if (pair.total_comparable !== (pair.status === 'matched') || (pair.total_comparable ? typeof pair.total_difference !== 'string' : pair.total_difference !== null)) return false;
    if (cohortSelectorKey(request.left) === cohortSelectorKey(request.right)
      && (pair.left?.evaluation_id ?? null) !== (pair.right?.evaluation_id ?? null)) return false;
    for (const [side, selector] of [[pair.left, request.left], [pair.right, request.right]] as const) {
      if (side && (!/^[a-zA-Z0-9_.-]{1,200}$/.test(side.evaluation_id) || side.conversation_id !== pair.source.conversation_id
          || side.checklist_id !== selector.checklist_id || !side.provenance || !Array.isArray(side.provenance.unknown_fields) || !Array.isArray(side.provenance.response_models)
          || !['numeric', 'missing', 'invalid'].includes(side.total_state) || typeof side.created_at !== 'string' || typeof side.updated_at !== 'string'
          || typeof side.cached !== 'boolean' || typeof side.provenance_conflict !== 'boolean' || typeof side.criterion_coverage_valid !== 'boolean'
          || typeof side.original_available !== 'boolean' || typeof side.effective_available !== 'boolean'
          || side.basis_available !== (request.basis === 'original' ? side.original_available : side.effective_available)
          || cohortFields.some(field => Object.hasOwn(selector, field) && side.provenance[field] !== selector[field]))) return false;
    }
  }
  return data.coverage.paired === data.pairs.filter(pair => pair.left && pair.right).length
    && data.coverage.cached_pairs === data.pairs.filter(pair => pair.left?.cached || pair.right?.cached).length
    && data.coverage.same_run_pairs === data.pairs.filter(pair => pair.left && pair.right && pair.left.evaluation_id === pair.right.evaluation_id).length
    && data.coverage.provenance_conflict_pairs === data.pairs.filter(pair => pair.left?.provenance_conflict || pair.right?.provenance_conflict).length
    && data.coverage.unknown_provenance_pairs === data.pairs.filter(pair => pair.left?.provenance.unknown_fields.length || pair.right?.provenance.unknown_fields.length).length
    && data.total_difference.count === data.pairs.filter(pair => pair.total_comparable).length
    && pairStatuses.every(status => Number.isSafeInteger(data.coverage[status]) && data.coverage[status] >= 0
      && data.coverage[status] === data.pairs.filter(pair => pair.status === status).length)
    && data.criteria.every(row => Array.isArray(row.transitions) && row.denominator === data.pairs.length
      && ['answer_comparable_count', 'answer_changed_count', 'disposition_changed_count', 'configuration_changed_count', 'definition_changed_count', 'details_only_count', 'unavailable_count']
        .every(key => Number.isSafeInteger(row[key as keyof CohortCriterion]) && Number(row[key as keyof CohortCriterion]) >= 0 && Number(row[key as keyof CohortCriterion]) <= data.pairs.length)
      && statisticValid(row.points_difference, row.answer_comparable_count)
      && row.transitions.every(transition => transition.count === transition.conversation_ids.length
        && transition.conversation_ids.every(id => ids.has(id)))
      && row.transitions.reduce((count, transition) => count + transition.count, 0) === data.pairs.length
      && new Set(row.transitions.flatMap(transition => transition.conversation_ids)).size === data.pairs.length);
}

function statisticValid(value: CohortStatistic, maximum: number) {
  const numeric = (text: string | null) => typeof text === 'string' && text.length <= 2100 && /^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?$/i.test(text);
  return value && Number.isSafeInteger(value.count) && value.count >= 0 && value.count <= maximum
    && (value.count === 0 ? value.sum === null && value.mean === null : numeric(value.sum) && numeric(value.mean));
}
