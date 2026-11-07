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
export type Conversation = {
  id: string; group_id: string; source_id: string; revision: number; content_hash: string;
  language: string; channel: string; message_count: number; audio_available: boolean;
  evaluation: EvaluationSummary | null;
};
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
