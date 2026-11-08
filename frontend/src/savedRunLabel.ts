import { label } from './helpers';
import type { EvaluationSummary } from './types';

export function savedRunLabel(run: Pick<EvaluationSummary, 'id' | 'checklist_id' | 'state' | 'completeness' | 'created_at'>) {
  const date = new Date(run.created_at);
  const time = Number.isFinite(date.getTime()) ? date.toLocaleString() : 'Date unavailable';
  const status = run.state === 'succeeded' ? label(run.completeness) : label(run.state);
  return `v${run.checklist_id} · ${status} · ${time} · ${run.id.slice(0, 8)}`;
}
