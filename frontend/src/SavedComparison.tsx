import { useEffect, useState } from 'react';
import { api } from './api';
import { answerLabel, label, points } from './helpers';
import type { ComparisonCell, ComparisonSide, EvaluationSummary, Evidence, SavedComparison as Comparison } from './types';
import { savedRunLabel } from './savedRunLabel';

type Difference = 'all' | 'answers' | 'points' | 'configuration' | 'details';
const detailChanges = new Set(['explanation', 'evidence', 'na_reason', 'review_reason']);
function matchesDifference(row: Comparison['criteria'][number], filter: Difference) {
  if (filter === 'all') return true;
  if (filter === 'answers') return row.changes.some(c => c === 'answer' || c === 'availability');
  if (filter === 'configuration') return row.change === 'added' || row.change === 'removed' || row.changes.includes('configuration');
  if (filter === 'points') return row.changes.includes('points');
  return row.changes.length > 0 && row.changes.every(c => detailChanges.has(c));
}

function initialPair(runs: EvaluationSummary[], currentId: string) {
  const target = runs.find(r => r.id === currentId) ?? runs[0];
  if (!target) return { left: '', right: '' };
  const time = Date.parse(target.created_at);
  const earlier = runs.filter(r => r.id !== target.id && r.state === 'succeeded' && r.checklist_id === target.checklist_id
    && Number.isFinite(time) && (r.created_at < target.created_at || (r.created_at === target.created_at && r.id < target.id)))
    .sort((a, b) => a.created_at === b.created_at ? a.id === b.id ? 0 : a.id > b.id ? -1 : 1 : a.created_at > b.created_at ? -1 : 1);
  return { left: earlier[0]?.id ?? runs.find(r => r.id !== target.id)?.id ?? target.id, right: target.id };
}

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
      <p>Prompt hash: {String(side.metadata.prompt_hash ?? 'Unavailable')}<br />Schema hash: {String(side.metadata.schema_hash ?? 'Unavailable')}</p>
      <p>Recorded response model(s): {Array.isArray(side.metadata.response_models) && side.metadata.response_models.length
        ? side.metadata.response_models.join(', ') : 'Unavailable'}</p>
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
  const [outcome, setOutcome] = useState<{ key: string; result: Comparison | null; error: string }>({ key: '', result: null, error: '' });
  const [retry, setRetry] = useState(0); const [changedOnly, setChangedOnly] = useState(false); const [difference, setDifference] = useState<Difference>('all');
  const selected = [left, right].map(id => runs.find(r => r.id === id));
  // A review keeps the run ID but changes its revision. Keying the visible result by that
  // revision hides it during the render before the effect starts the replacement GET.
  const key = JSON.stringify([sourceId, left, right, leftBasis, rightBasis, retry,
    ...selected.map(r => r ? [r.updated_at, r.state, r.completeness, r.total, r.cached_from] : null)]);
  const result = outcome.key === key ? outcome.result : null;
  const error = outcome.key === key ? outcome.error : '';
  const pending = outcome.key !== key;
  const selectionAvailable = selected.every(Boolean);
  useEffect(() => {
    if (!open || !left || !right) return;
    if (!selectionAvailable) { setOutcome({ key, result: null, error: 'A selected saved run is no longer available. Choose another saved run.' }); return; }
    let active = true;
    const params = new URLSearchParams({ left_id: left, right_id: right, left_basis: leftBasis, right_basis: rightBasis });
    void api<Comparison>(`/evaluations/compare?${params}`).then(data => {
      if (data.source.id !== sourceId) throw new Error('Comparison source revision does not match this transcript.');
      if (active) setOutcome({ key, result: data, error: '' });
    }).catch(e => { if (active) setOutcome({ key, result: null, error: e instanceof Error ? e.message : 'Comparison failed.' }); });
    return () => { active = false; };
  }, [open, left, right, leftBasis, rightBasis, sourceId, key, selectionAvailable]);
  const runLabel = savedRunLabel;
  const visible = result?.criteria.filter(r => (!changedOnly || r.change !== 'unchanged') && matchesDifference(r, difference)) ?? [];
  return <section className="panel saved-comparison">
    <button className="secondary" aria-expanded={open} onClick={() => {
      if (!open) {
        const defaults = initialPair(runs, currentId);
        if (!runs.some(r => r.id === left)) setLeft(defaults.left);
        if (!runs.some(r => r.id === right)) setRight(defaults.right);
        // Reopening also refreshes a previously loaded result, while retaining valid choices.
        setRetry(r => r + 1);
      }
      setOpen(!open);
    }} disabled={!runs.length}>Compare saved runs</button>
    {open && <div role="region" aria-label="Saved-run comparison">
      <p>Inspect stored answers without evaluating again. Both runs must use this exact source revision.</p>
      <small>The initial baseline prefers the most recent earlier successful run with the same checklist among loaded runs. Browse saved-run pages to make older runs available. Your selections stay in place when results update.</small>
      <div className="comparison-controls">
        <label>Baseline saved run<select aria-label="Baseline saved run" value={left} onChange={e => setLeft(e.target.value)}>{runs.map(r => <option key={r.id} value={r.id}>{runLabel(r)}</option>)}</select></label>
        <label>Baseline answer set<select aria-label="Baseline answer set" value={leftBasis} onChange={e => setLeftBasis(e.target.value as typeof leftBasis)}><option value="effective">Effective</option><option value="original">Original</option></select></label>
        <label>Comparison saved run<select aria-label="Comparison saved run" value={right} onChange={e => setRight(e.target.value)}>{runs.map(r => <option key={r.id} value={r.id}>{runLabel(r)}</option>)}</select></label>
        <label>Comparison answer set<select aria-label="Comparison answer set" value={rightBasis} onChange={e => setRightBasis(e.target.value as typeof rightBasis)}><option value="effective">Effective</option><option value="original">Original</option></select></label>
      </div>
      {error && <div role="alert"><p>{error}</p><button className="secondary" onClick={() => setRetry(retry + 1)}>Retry comparison</button></div>}
      {pending && <p role="status">Loading saved comparison…</p>}
      {result && <>
        <div className="comparison-totals"><Provenance side={result.left} title="Baseline" /><Provenance side={result.right} title="Comparison" /></div>
        <p>{result.total_comparable ? `Saved total difference: ${result.total_difference}` : 'No comparable total difference.'} {result.notice}</p>
        {result.left.score && result.right.score && result.left.score.applicable_weight !== result.right.score.applicable_weight && <p>Applicable scored weight changed from {result.left.score.applicable_weight} to {result.right.score.applicable_weight}. Each saved contribution uses its own applicable-weight denominator.</p>}
        <label className="check-label"><input type="checkbox" checked={changedOnly} onChange={e => setChangedOnly(e.target.checked)} />Show changed criteria only</label>
        <label>Difference filter<select aria-label="Comparison difference filter" value={difference} onChange={e => setDifference(e.target.value as Difference)}>
          <option value="all">All criteria ({result.criteria.length})</option>
          <option value="answers">Answers / dispositions ({result.criteria.filter(r => matchesDifference(r, 'answers')).length})</option>
          <option value="points">Points ({result.criteria.filter(r => matchesDifference(r, 'points')).length})</option>
          <option value="configuration">Definitions ({result.criteria.filter(r => matchesDifference(r, 'configuration')).length})</option>
          <option value="details">Evidence / explanation only ({result.criteria.filter(r => matchesDifference(r, 'details')).length})</option>
        </select></label><small>Answer, point and definition counts can overlap. Unavailable answers count as answer changes.</small>
        <div className="table-scroll"><table className="comparison-table"><thead><tr><th>Criterion / changes</th><th>Baseline answer</th><th>Comparison answer</th></tr></thead><tbody>
          {visible.map(r => <tr key={r.criterion_id}>
            <td><strong>{r.right.criterion?.name ?? r.left.criterion?.name ?? r.criterion_id}</strong><small>{r.criterion_id} · {r.change}</small>
              <p>{r.changes.map(label).join(', ') || 'No saved difference'}</p>{!!r.configuration_changes.length && <p>Configuration: {r.configuration_changes.join(', ')}</p>}
              {!r.answer_comparable && <small>Answers unavailable or definitions differ.</small>}
              {r.changes.includes('answer') && (r.right.criterion ?? r.left.criterion)?.answer_type === 'flag' && <small>This flag change is unscored.</small>}
              {r.points_difference != null && <small>Raw-point difference: {r.points_difference}</small>}
              {!!r.configuration_changes.length && <details><summary>Saved definitions</summary><pre>{JSON.stringify({ baseline: r.left.criterion, comparison: r.right.criterion }, null, 2)}</pre></details>}
            </td><td><Result cell={r.left} side="Baseline" criterionId={r.criterion_id} onEvidence={onEvidence} /></td>
            <td><Result cell={r.right} side="Comparison" criterionId={r.criterion_id} onEvidence={onEvidence} /></td>
          </tr>)}
        </tbody></table></div>
        {changedOnly && result.criteria.every(r => r.change === 'unchanged') && <p>No saved differences.</p>}
        {!visible.length && !(changedOnly && result.criteria.every(r => r.change === 'unchanged')) && <p>No criteria match this difference filter.</p>}
      </>}
    </div>}
  </section>;
}
