import { useEffect, useRef } from 'react';
import { api } from './api';
import type { SavedComparison } from './types';
import { useLatestResource } from './useLatestResource';
import type { CohortAnswer, CohortBasis, CohortPair } from './cohortTypes';

export function cohortAnswerLabel(answer: CohortAnswer, type?: string | null) {
  if (answer.disposition === 'not_applicable') return 'N/A';
  if (answer.disposition === 'needs_review') return 'Needs review';
  if (answer.disposition === 'unavailable') return 'Unavailable';
  return typeof answer.value === 'boolean' ? type === 'flag' ? answer.value ? 'Flagged' : 'Not flagged' : answer.value ? 'Yes' : 'No' : answer.value ?? 'Unavailable';
}

export default function CohortPairPreview({ pair, basis, onClose, onOpenPair }: {
  pair: CohortPair; basis: CohortBasis; onClose: () => void; onOpenPair: (leftId: string, rightId: string) => void;
}) {
  const panel = useRef<HTMLElement>(null);
  const left = pair.left; const right = pair.right;
  const key = JSON.stringify([pair.source.conversation_id, pair.source.content_hash, left?.evaluation_id, left?.updated_at, right?.evaluation_id, right?.updated_at, basis]);
  const comparison = useLatestResource(key, async () => {
    if (!left || !right) throw new Error('Both exact saved runs are required.');
    const query = new URLSearchParams({ left_id: left.evaluation_id, right_id: right.evaluation_id, left_basis: basis, right_basis: basis });
    const result = await api<SavedComparison>(`/evaluations/compare?${query}`);
    if (!result || !result.left || !result.right || !result.source || result.source.id !== pair.source.conversation_id || result.source.content_hash !== pair.source.content_hash
        || result.left.id !== left.evaluation_id || result.right.id !== right.evaluation_id || result.left.updated_at !== left.updated_at || result.right.updated_at !== right.updated_at
        || result.left.basis !== basis || result.right.basis !== basis || !Array.isArray(result.criteria)) {
      throw new Error('Saved pair changed. Refresh the cohort comparison before inspecting this pair.');
    }
    return result;
  });
  useEffect(() => { panel.current?.scrollIntoView({ block: 'nearest' }); panel.current?.focus({ preventScroll: true }); }, [key]);
  return <section className="cohort-pair-preview" ref={panel} tabIndex={-1} aria-label="Exact cohort pair">
    <div className="cohort-section-heading"><h4>Exact saved pair · {basis} answers</h4><button className="text-button" onClick={onClose}>Close pair</button></div>
    <p>{pair.source.source_id} · revision {pair.source.revision} · dataset {pair.source.dataset_group_id}</p>
    <p className="cohort-identity">Baseline {left?.evaluation_id ?? 'missing'} → Candidate {right?.evaluation_id ?? 'missing'}</p>
    {comparison.pending ? <p role="status">Loading exact saved pair…</p> : comparison.error ? <div role="alert"><p>{comparison.error}</p>
      <button className="secondary" onClick={() => void comparison.reload().catch(() => {})}>Retry exact pair</button></div> : comparison.value && <>
      <p>{comparison.value.total_comparable ? `Saved total difference: ${comparison.value.total_difference}` : 'No comparable numeric total for this pair.'}</p>
      <div className="table-scroll" role="region" aria-label="Exact pair criterion comparison" tabIndex={0}><table><thead><tr><th>Criterion</th><th>Baseline</th><th>Candidate</th><th>Saved raw-point difference</th></tr></thead>
        <tbody>{comparison.value.criteria.map(row => <tr key={row.criterion_id}>
          <td>{row.right.criterion?.name ?? row.left.criterion?.name ?? row.criterion_id}<small>{row.changes.join(', ') || 'Unchanged'}</small></td>
          {([['left', row.left], ['right', row.right]] as const).map(([side, cell]) => <td key={side}>
            {cell.judgment ? cohortAnswerLabel({ disposition: cell.judgment.disposition, value: typeof cell.judgment.value === 'number' ? String(cell.judgment.value) : cell.judgment.value, reason: null }, cell.criterion?.answer_type) : 'Unavailable'}
            {cell.judgment?.evidence.map((evidence, index) => <a key={index} className="cohort-evidence" href={`#conversation/${encodeURIComponent(pair.source.conversation_id)}?evaluation=${encodeURIComponent((side === 'left' ? left : right)!.evaluation_id)}&criterion=${encodeURIComponent(row.criterion_id)}&message=${encodeURIComponent(evidence.start_message_id)}`}>
              {side === 'left' ? 'Baseline' : 'Candidate'} evidence {evidence.start_message_id}–{evidence.end_message_id}</a>)}
          </td>)}
          <td>{row.points_difference ?? 'Not comparable'}</td>
        </tr>)}</tbody></table></div>
      <p>This preview uses {basis} answers. The review workspace has its own original/effective selectors.</p>
      <button className="secondary" onClick={() => { if (left && right) onOpenPair(left.evaluation_id, right.evaluation_id); }}>Open these run IDs in review</button>
    </>}
  </section>;
}
