import type { Assessment, Calculated, ChecklistVersion, EvaluationDetail, Evidence, Judgment, Message } from './types';

export type PrintIdentity = { evaluationId: string; updatedAt: string };
export type PrintScore = Omit<Calculated, 'criteria' | 'sections'> & {
  scoring_version?: string; unresolved_criteria?: string[];
  criteria: (Calculated['criteria'][number] & { applicable?: boolean; section_id?: string })[];
  sections: (Calculated['sections'][number] & { applicable_weight?: string; raw_subtotal?: string | null })[];
};
export type PrintReview = {
  id: number; appeal_id: string; evaluation_id: string; criterion_id: string; action: string;
  rationale: string; judgment: Judgment; resulting_score: PrintScore; created_at: string;
};
export type PrintEvaluation = Omit<EvaluationDetail, 'metadata' | 'original_score' | 'effective_score' | 'reviews'> & {
  metadata: Record<string, unknown>; original_score: PrintScore | null; effective_score: PrintScore | null;
  reviews: PrintReview[];
};
export type PrintSource = {
  id: string; source_id: string; group_id: string; revision: number; content_hash: string;
  language: string; channel: string; message_count: number;
};
export type PrintExcerpt = {
  basis: string; criterion_id: string; evidence: Evidence; messages: Message[]; range_available: boolean;
};
export type SavedPrintPacket = {
  export_schema_version: 1; source: PrintSource; evaluation: PrintEvaluation;
  export_policy: {
    source_excerpts_included: boolean; recording_urls_included: false; credentials_included: false;
    notice: string; redacted_string_occurrences: number;
  };
  source_excerpts?: PrintExcerpt[];
  manifest: {
    schema_version: 1; generated_at: string; selected_run_count: 1; answer_sets: string[];
    source_excerpts_included: boolean; notice: string;
    runs: {
      evaluation_id: string; updated_at: string; conversation_id: string; source_id: string; group_id: string;
      revision: number; source_hash: string; checklist_id: number; checklist_hash: string;
    }[];
  };
};

export type { Assessment, ChecklistVersion, Judgment };
