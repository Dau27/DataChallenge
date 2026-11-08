import { useEffect, useRef, useState } from 'react';
import { api } from './api';
import type { Conversation } from './types';

type Case = { conversation_id: string; source_id: string; group_id: string; revision: number; evaluation_id: string | null; criterion_id: string };
type Bucket = { key: string; label: string; count: number; denominator: number; percentage: string; cases: Case[] };
type CriterionRow = { criterion_id: string; name: string; answer_type: 'binary' | 'scale' | 'flag'; weight: string | null; assessed_count: number; buckets: Bucket[] };
export type Breakdown = { checklist_id: number; checklist_hash: string; basis: 'original' | 'effective'; total_sources: number; selection_policy: string;
  manifest: { conversation_id: string; content_hash: string; evaluation_id: string | null; updated_at: string | null; state: string }[];
  groups: { group_id: string; total_sources: number; coverage: Record<string, number>; criteria: CriterionRow[] }[] };

export default function CriterionBreakdown({ rows, checklistId }: { rows: Conversation[]; checklistId: number }) {
  const [open, setOpen] = useState(false); const [basis, setBasis] = useState<'original' | 'effective'>('effective'); const [retry, setRetry] = useState(0);
  const scopeKey = JSON.stringify(rows.map(row => [row.id, row.content_hash, row.evaluation?.id ?? null, row.evaluation?.updated_at ?? null,
    row.evaluation?.state ?? 'not_evaluated', row.evaluation?.completeness, row.evaluation?.total,
    row.pending_appeals, row.pending_review_targets, row.critical_findings]));
  const key = JSON.stringify([checklistId, scopeKey, basis, retry]);
  const [state, setState] = useState<{ key: string; data?: Breakdown; error?: string } | null>(null);
  const [selection, setSelection] = useState<{ key: string; groupId: string; criterionId: string; bucketKey: string } | null>(null);
  const casesPanel = useRef<HTMLElement>(null); const caseTrigger = useRef<HTMLButtonElement | null>(null);
  const limited = rows.length > 200;
  useEffect(() => {
    if (!open || !rows.length || limited) return;
    let active = true;
    void api<Breakdown>('/insights/breakdown', { checklist_id: checklistId, conversation_ids: rows.map(row => row.id), basis }).then(data => {
      if (!data || !Array.isArray(data.manifest) || !Array.isArray(data.groups) || data.checklist_id !== checklistId || data.basis !== basis || data.total_sources !== rows.length || data.manifest.length !== rows.length
        || data.manifest.some((item, i) => item.conversation_id !== rows[i].id || item.content_hash !== rows[i].content_hash
          || item.evaluation_id !== (rows[i].evaluation?.id ?? null) || item.updated_at !== (rows[i].evaluation?.updated_at ?? null)
          || item.state !== (rows[i].evaluation?.state ?? 'not_evaluated'))) {
        throw new Error('Saved results changed. Refresh the queue before inspecting breakdowns.');
      }
      if (active) setState({ key, data });
    }).catch(error => { if (active) setState({ key, error: error instanceof Error ? error.message : 'Could not load criterion breakdowns.' }); });
    return () => { active = false; };
  }, [open, key, limited]);
  const current = state?.key === key ? state : null;
  const group = selection?.key === key ? current?.data?.groups.find(item => item.group_id === selection.groupId) : undefined;
  const criterion = group?.criteria.find(item => item.criterion_id === selection?.criterionId);
  const bucket = criterion?.buckets.find(item => item.key === selection?.bucketKey);
  useEffect(() => {
    if (bucket && casesPanel.current) { casesPanel.current.scrollIntoView({ block: 'nearest' }); casesPanel.current.focus({ preventScroll: true }); }
  }, [bucket]);
  return <details className="criterion-breakdowns insight-tools" onToggle={event => setOpen(event.currentTarget.open)}>
    <summary><span>Criterion breakdowns</span><span className="disclosure-hint">Saved answers and coverage · {rows.length} visible conversations</span></summary>
    {open && <div className="insight-content">
      <p>One latest run per visible conversation, for checklist v{checklistId}. Datasets stay separate. These distributions describe saved judgments; they do not measure model accuracy.</p>
      <label>Answer basis<select aria-label="Breakdown answer basis" value={basis} onChange={event => setBasis(event.target.value as typeof basis)}><option value="effective">Effective judgments</option><option value="original">Original judgments</option></select></label>
      {limited ? <p role="alert">Narrow the queue to at most 200 conversations. No partial breakdown is shown.</p> : !rows.length ? <p>No visible conversations to analyse.</p>
        : current?.error ? <div role="alert"><p>{current.error}</p><button className="secondary" onClick={() => setRetry(value => value + 1)}>Retry breakdown</button></div>
          : !current?.data ? <p role="status">Loading saved criterion breakdowns…</p> : <>
            {current.data.groups.map(dataset => <section key={dataset.group_id} className="breakdown-dataset" aria-label={`Dataset ${dataset.group_id} breakdown`}>
              <h3>Dataset {dataset.group_id} · {dataset.total_sources} conversations</h3>
              <p className="coverage-summary">Execution coverage: {Object.entries(dataset.coverage).map(([state, count]) => `${state.replaceAll('_', ' ')}: ${count}`).join(' · ')}</p>
              <div className="table-scroll"><table><thead><tr><th>Criterion</th><th>Saved answer distribution</th></tr></thead><tbody>{dataset.criteria.map(item => <tr key={item.criterion_id}>
                <td><strong>{item.name}</strong><small>{item.answer_type === 'flag' ? 'Unscored flag · unknown is not a clean result' : `Weight ${item.weight} · ${item.assessed_count} assessed`}</small></td>
                <td><div className="breakdown-buckets">{item.buckets.map(cell => <button className="secondary breakdown-count" key={cell.key} disabled={!cell.count}
                  aria-label={`Inspect ${dataset.group_id}: ${item.name}: ${cell.label}`}
                  onClick={event => { caseTrigger.current = event.currentTarget; setSelection({ key, groupId: dataset.group_id, criterionId: item.criterion_id, bucketKey: cell.key }); }}>
                  <span>{cell.label}</span><strong>{cell.count} / {cell.denominator}</strong><small>{cell.percentage}%</small>
                </button>)}</div></td>
              </tr>)}</tbody></table></div>
            </section>)}
            <p>Each percentage uses all selected conversations in its dataset. N/A, unresolved judgments, unavailable results and execution failures remain visible; missing answers are never passes.</p>
            {bucket && criterion && group && <section ref={casesPanel} tabIndex={-1} className="panel breakdown-cases" aria-label="Breakdown cases">
              <div className="table-toolbar"><h3>{group.group_id}: {criterion.name} · {bucket.label} ({bucket.count})</h3><button className="text-button" onClick={() => { setSelection(null); caseTrigger.current?.focus(); }}>Close cases</button></div>
              <ul>{bucket.cases.map(item => <li key={item.conversation_id}><a href={`#conversation/${encodeURIComponent(item.conversation_id)}${item.evaluation_id ? `?evaluation=${encodeURIComponent(item.evaluation_id)}&criterion=${encodeURIComponent(item.criterion_id)}` : ''}`}>
                {item.source_id} · revision {item.revision}{item.evaluation_id ? '' : ' · no saved run'}</a></li>)}</ul>
            </section>}
          </>}
    </div>}
  </details>;
}
