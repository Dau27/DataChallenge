import { useEffect, useState } from 'react';
import { api } from './api';
import { answerLabel, label, points } from './helpers';
import type { ComparisonCell, ComparisonSide, EvaluationSummary, Evidence, SavedComparison as Comparison } from './types';

function Result({ cell, side, criterionId, onEvidence }: { cell: ComparisonCell; side: string; criterionId: string; onEvidence: (e: Evidence) => void }) {
  if (!cell.criterion) return <span>Criterion absent</span>;
  if (!cell.judgment) return <span>No saved answer</span>;
  const j = cell.judgment;
  return <div className="comparison-answer"><strong>{answerLabel(j.value, j.disposition)}</strong>
    <small>{cell.criterion.answer_type === 'flag' ? 'Unscored flag' : `${cell.points?.raw_points ?? '—'} raw points · weight ${cell.criterion.weight} · ${points(cell.points?.normalized_contribution)} contribution / 100`}</small>
    <p>{j.explanation}</p>{j.na_reason && <p>N/A: {j.na_reason}</p>}{j.review_reason && <p>Missing basis: {j.review_reason}</p>}
    {j.evidence.map((e, i) => <button className="evidence-button" key={i} aria-label={`${side} evidence ${criterionId} ${e.start_message_id}`} onClick={() => onEvidence(e)}>{e.start_message_id}–{e.end_message_id}</button>)}
  </div>;
}

function Provenance({ side, title }: { side: ComparisonSide; title: string }) {
  return <section className="comparison-provenance"><strong>{title}: {side.score?.total ?? 'No numeric total'}</strong>
    <small>{side.state} · {side.basis} · checklist v{side.checklist.id} · {side.id}</small>
    {side.score?.reason && <p>{label(side.score.reason)}</p>}{side.error && <p>{side.error}</p>}
    <small>{String(side.metadata.model ?? 'Model unavailable')} · {String(side.metadata.prompt_version ?? 'Prompt unavailable')}</small>
    <details><summary>{title} provenance</summary><p>Saved {new Date(side.created_at).toLocaleString()} · updated {new Date(side.updated_at).toLocaleString()}</p>
      <p>{side.review_count} saved review decision(s){side.cached_from ? ` · cached from ${side.cached_from}` : ''}</p>
      <p>Estimated cost: {side.usage.estimated_cost_usd == null ? 'Unavailable' : `$${side.usage.estimated_cost_usd}`}; {side.usage.request_attempts} attempt(s)</p>
      <pre>{JSON.stringify(side.metadata, null, 2)}</pre><p>Checklist hash: {side.checklist.content_hash}</p>
    </details>
  </section>;
}

export default function SavedComparison({ runs, currentId, sourceId, onEvidence }: {
  runs: EvaluationSummary[]; currentId: string; sourceId: string; onEvidence: (e: Evidence) => void;
}) {
  const [open, setOpen] = useState(false);
  const [left, setLeft] = useState(''); const [right, setRight] = useState('');
  const [leftBasis, setLeftBasis] = useState<'original' | 'effective'>('effective');
  const [rightBasis, setRightBasis] = useState<'original' | 'effective'>('effective');
  const [result, setResult] = useState<Comparison | null>(null); const [error, setError] = useState('');
  const [pending, setPending] = useState(false); const [retry, setRetry] = useState(0); const [changedOnly, setChangedOnly] = useState(false);
  const key = [left, right, leftBasis, rightBasis].join('|'); const [loadedKey, setLoadedKey] = useState('');
  useEffect(() => {
    if (!open || !left || !right) return;
    let active = true; setPending(true); setError(''); setResult(null);
    const params = new URLSearchParams({ left_id: left, right_id: right, left_basis: leftBasis, right_basis: rightBasis });
    void api<Comparison>(`/evaluations/compare?${params}`).then(data => {
      if (data.source.id !== sourceId) throw new Error('Comparison source revision does not match this transcript.');
      if (active) { setResult(data); setLoadedKey(key); }
    }).catch(e => { if (active) setError(e instanceof Error ? e.message : 'Comparison failed.'); })
      .finally(() => { if (active) setPending(false); });
    return () => { active = false; };
  }, [open, left, right, leftBasis, rightBasis, sourceId, key, retry]);
  const runLabel = (run: EvaluationSummary) => `v${run.checklist_id} · ${label(run.state)} · ${new Date(run.created_at).toLocaleString()} · ${run.id.slice(0, 8)}`;
  return <section className="panel saved-comparison">
    <button className="secondary" aria-expanded={open} onClick={() => {
      if (!open) { setLeft(runs.find(r => r.id !== currentId)?.id ?? currentId); setRight(currentId || runs[0]?.id || ''); }
      setOpen(!open);
    }} disabled={!runs.length}>Compare saved runs</button>
    {open && <div role="region" aria-label="Saved-run comparison">
      <p>Inspect stored answers without evaluating again. Both runs must use this exact source revision.</p>
      <div className="comparison-controls">
        <label>Baseline saved run<select aria-label="Baseline saved run" value={left} onChange={e => setLeft(e.target.value)}>{runs.map(r => <option key={r.id} value={r.id}>{runLabel(r)}</option>)}</select></label>
        <label>Baseline answer set<select aria-label="Baseline answer set" value={leftBasis} onChange={e => setLeftBasis(e.target.value as typeof leftBasis)}><option value="effective">Effective</option><option value="original">Original</option></select></label>
        <label>Comparison saved run<select aria-label="Comparison saved run" value={right} onChange={e => setRight(e.target.value)}>{runs.map(r => <option key={r.id} value={r.id}>{runLabel(r)}</option>)}</select></label>
        <label>Comparison answer set<select aria-label="Comparison answer set" value={rightBasis} onChange={e => setRightBasis(e.target.value as typeof rightBasis)}><option value="effective">Effective</option><option value="original">Original</option></select></label>
      </div>
      {error && <div role="alert"><p>{error}</p><button className="secondary" onClick={() => setRetry(retry + 1)}>Retry comparison</button></div>}
      {(pending || (!error && loadedKey !== key)) && <p role="status">Loading saved comparison…</p>}
      {result && loadedKey === key && !pending && <>
        <div className="comparison-totals"><Provenance side={result.left} title="Baseline" /><Provenance side={result.right} title="Comparison" /></div>
        <p>{result.total_comparable ? `Saved total difference: ${result.total_difference}` : 'No comparable total difference.'} {result.notice}</p>
        <label className="check-label"><input type="checkbox" checked={changedOnly} onChange={e => setChangedOnly(e.target.checked)} />Show changed criteria only</label>
        <div className="table-scroll"><table className="comparison-table"><thead><tr><th>Criterion / changes</th><th>Baseline answer</th><th>Comparison answer</th></tr></thead><tbody>
          {result.criteria.filter(r => !changedOnly || r.change !== 'unchanged').map(r => <tr key={r.criterion_id}>
            <td><strong>{r.right.criterion?.name ?? r.left.criterion?.name ?? r.criterion_id}</strong><small>{r.criterion_id} · {r.change}</small>
              <p>{r.changes.map(label).join(', ') || 'No saved difference'}</p>{!!r.configuration_changes.length && <p>Configuration: {r.configuration_changes.join(', ')}</p>}
              {!r.answer_comparable && <small>Answers unavailable or definitions differ.</small>}
              {r.points_difference != null && <small>Raw-point difference: {r.points_difference}</small>}
              {!!r.configuration_changes.length && <details><summary>Saved definitions</summary><pre>{JSON.stringify({ baseline: r.left.criterion, comparison: r.right.criterion }, null, 2)}</pre></details>}
            </td><td><Result cell={r.left} side="Baseline" criterionId={r.criterion_id} onEvidence={onEvidence} /></td>
            <td><Result cell={r.right} side="Comparison" criterionId={r.criterion_id} onEvidence={onEvidence} /></td>
          </tr>)}
        </tbody></table></div>
        {changedOnly && result.criteria.every(r => r.change === 'unchanged') && <p>No saved differences.</p>}
      </>}
    </div>}
  </section>;
}
