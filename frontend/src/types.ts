export type Criterion = {
  id: string; name: string; description: string; section_id: string;
  answer_type: 'binary' | 'scale' | 'flag'; weight: string | number | null;
  na_allowed: boolean; na_condition: string | null;
  scale: { value: string | number; description: string }[];
};
export type Checklist = {
  schema_version: 1; name: string; initial_version_label: string | null;
  source: Record<string, unknown> | null;
  sections: { id: string; title: string }[]; criteria: Criterion[];
  scoring_policy: Record<string, unknown>; source_notes: string[];
};
export type ChecklistVersion = { id: number; content_hash: string; snapshot: Checklist; created_at: string };
export type Evidence = { kind: 'support' | 'absence' | 'context'; start_message_id: string; end_message_id: string };
export type Judgment = {
  disposition: 'assessed' | 'not_applicable' | 'needs_review'; value: boolean | number | null;
  explanation: string; na_reason: string | null; review_reason: string | null; evidence: Evidence[];
};
export type Assessment = { results: Record<string, Judgment> };
export type ComparisonCell = { criterion: Criterion | null; judgment: Judgment | null;
  points: { raw_points: string | null; normalized_contribution: string | null } | null };
export type ComparisonSide = { id: string; basis: 'original' | 'effective'; state: string; error: string | null;
  created_at: string; updated_at: string; cached_from: string | null; checklist: ChecklistVersion;
  score: Calculated | null; metadata: Record<string, unknown>; usage: EvaluationDetail['usage']; review_count: number };
export type SavedComparison = { source: { id: string; source_id: string; revision: number; content_hash: string };
  left: ComparisonSide; right: ComparisonSide; total_comparable: boolean; total_difference: string | null; notice: string;
  criteria: { criterion_id: string; change: string; changes: string[]; configuration_changes: string[];
    answer_comparable: boolean; points_difference: string | null; left: ComparisonCell; right: ComparisonCell }[] };
export type Calculated = {
  total: string | null; reason: string | null; completeness: string; applicable_weight: string;
  raw_subtotal: string | null; flags: Record<string, boolean | null>;
  criteria: { criterion_id: string; weight: string | null; raw_points: string | null; normalized_contribution: string | null }[];
  sections: { id: string; title: string; total: string | null; reason: string | null }[];
};
export type EvaluationSummary = {
  id: string; conversation_id: string; checklist_id: number;
  state: 'queued' | 'running' | 'succeeded' | 'failed' | 'interrupted'; completeness: string;
  total: string | null; error: string | null; cached_from: string | null; created_at: string; updated_at: string;
};
export type TranscriptMatch = { id: string; speaker: string; timestamp: string; snippet: string; highlights?: { start: number; end: number }[] };
export type MatchPage = { source: { id: string; content_hash: string }; query: string; speaker: string; offset: number; limit: number; total_matches: number; matches: TranscriptMatch[] };
export type Conversation = {
  id: string; group_id: string; source_id: string; revision: number; content_hash: string;
  language: string; channel: string; message_count: number; audio_available: boolean;
  evaluation: EvaluationSummary | null;
  pending_appeals?: number;
  pending_review_targets?: { appeal_id: string; conversation_id: string; evaluation_id: string; criterion_id: string; criterion_name: string }[];
  critical_findings?: { evaluation_id: string; criterion_id: string; criterion_name: string }[];
  search_matches?: TranscriptMatch[];
  search_total_matches?: number;
};
export type FieldIssue = { location: (string | number)[]; message: string; label?: string };
export type ChecklistPreview = { valid: boolean; errors: FieldIssue[]; changes: { location: (string | number)[]; label: string; before: unknown; after: unknown }[] };
export type BudgetStatus = { limit_usd: string; opening_accounted_usd: string; accounted_usd: string; reserved_usd: string;
  overhead_usd: string; available_usd: string; ready: boolean; blocked_reason: string | null; estimate_only: true };
export type EvaluationPreview = { required_reservation_usd: string | null; cached: number; active: number;
  new_evaluations: number; affordable: boolean; blocked_reason: string | null; budget: BudgetStatus };
export type Message = { id: string; timestamp: string; speaker: string; text: string };
export type ConversationDetail = {
  id: string; group_id: string; source_id: string; revision: number; content_hash: string;
  snapshot: { language: string; channel: string; audio_url: string | null; transcript: Message[] };
  evaluations: EvaluationSummary[];
};
export type Appeal = { id: string; criterion_id: string; comment: string; status: string; created_at: string };
export type EvaluationDetail = EvaluationSummary & {
  original: Assessment | null; effective: Assessment | null; original_score: Calculated | null; effective_score: Calculated | null;
  checklist: ChecklistVersion;
  metadata: { provider: string; model: string; mode: string; prompt_version: string };
  usage: { request_attempts: number; input_tokens_known: number; output_tokens_known: number; usage_complete: boolean;
    estimated_cost_usd: string | null; cost_rate_source: string | null; latency_ms: number };
  attempts: { number: number; status: string; latency_ms: number; input_tokens: number | null; output_tokens: number | null }[];
  appeals: Appeal[];
  reviews: { id: number; criterion_id: string; action: string; rationale: string; judgment: Judgment; resulting_score: Calculated; created_at: string }[];
};
export type Access = {
  provider_configured: boolean; model: string | null; provider_status: string; organizer_configured: boolean;
  cost_rate_available: boolean; last_provider_check: { succeeded: boolean; error?: string } | null;
};
