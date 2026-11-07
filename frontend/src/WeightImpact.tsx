import { useEffect, useState } from 'react';
import { api } from './api';
import type { Calculated, Checklist, ChecklistVersion, FieldIssue } from './types';

type SavedRun = { id: string; conversation_id: string; checklist_id: number; checklist_hash: string;
  source_id: string; group_id: string; revision: number; content_hash: string; created_at: string; updated_at: string };
type RunPage = { checklist_id: number; checklist_hash: string; total: number; offset: number; limit: number; runs: SavedRun[] };
type ScoreRow = { weight: string | null; applicable: boolean; raw_points: string | null; normalized_contribution: string | null };
type Preview = { eligible: boolean; simulation: true; notice: string; checklist_id: number; checklist_hash: string;
  evaluation_id: string; basis: string; updated_at?: string; reasons: string[]; errors: FieldIssue[];
  source?: { id: string; content_hash: string; source_id: string; group_id: string; revision: number };
  original_score?: Calculated; simulated_score?: Calculated; total_difference?: string | null;
  criteria?: { criterion_id: string; name: string; answer_type: string; disposition: string; value: unknown;
    original: ScoreRow; simulated: ScoreRow }[] };

const show = (value: unknown) => value === null || value === undefined ? '—' : String(value);
// Round the decimal text, avoiding binary-float rounding at a half-way digit.
const contribution = (value: string | null) => {
  if (value === null) return '—';
  const match = /^([+-]?)(\d+)(?:\.(\d*))?(?:[eE]([+-]?\d+))?$/.exec(value);
  if (!match) return value;
  const fraction = match[3] ?? ''; const exponent = Number(match[4] ?? '0');
  if (!Number.isSafeInteger(exponent) || Math.abs(exponent) > 1000) return value;
  const digits = BigInt(match[2] + fraction); const shift = exponent - fraction.length + 4;
  const factor = 10n ** BigInt(Math.abs(shift));
  const rounded = shift >= 0 ? digits * factor : (digits + factor / 2n) / factor;
  const formatted = rounded.toString().padStart(5, '0');
  return `${match[1] === '-' && rounded !== 0n ? '-' : ''}${formatted.slice(0, -4)}.${formatted.slice(-4)}`;
};
const judgmentLabel = (row: NonNullable<Preview['criteria']>[number]) => {
  if (row.disposition !== 'assessed') return row.disposition === 'not_applicable' ? 'N/A' : 'Needs review';
  if (row.answer_type === 'binary') return row.value === true ? 'Yes' : row.value === false ? 'No' : show(row.value);
  if (row.answer_type === 'flag') return row.value === true ? 'Flagged' : row.value === false ? 'Not flagged' : show(row.value);
  return show(row.value);
};
const runName = (run: SavedRun) => `${run.group_id} / ${run.source_id} · revision ${run.revision} · ${run.id}`;

export default function WeightImpact({ version, draft }: { version: ChecklistVersion; draft: Checklist }) {
  const versionKey = JSON.stringify([version.id, version.content_hash]);
  const [open, setOpen] = useState(false); const [opening, setOpening] = useState(0);
  const [offset, setOffset] = useState(0); const [refresh, setRefresh] = useState(0); const [retry, setRetry] = useState(0);
  const [basis, setBasis] = useState<'original' | 'effective'>('effective');
  const [selection, setSelection] = useState<{ key: string; run: SavedRun } | null>(null);
  const [page, setPage] = useState<{ key: string; data?: RunPage; error?: string } | null>(null);
  const [result, setResult] = useState<{ key: string; data?: Preview; error?: string } | null>(null);
  const pageKey = JSON.stringify([versionKey, opening, offset, refresh]);
  const currentPage = page?.key === pageKey ? page : null;
  const selected = selection?.key === versionKey ? selection.run : null;
  const draftKey = JSON.stringify(draft);
  const requestKey = JSON.stringify([pageKey, selected?.id, selected?.updated_at, basis, draftKey, retry]);
  const current = result?.key === requestKey && currentPage?.data ? result : null;

  useEffect(() => {
    if (!open) return;
    let active = true;
    void api<RunPage>(`/insights/weight-preview/runs?checklist_id=${version.id}&offset=${offset}&limit=100`).then(data => {
      if (data.checklist_id !== version.id || data.checklist_hash !== version.content_hash || data.offset !== offset
        || !Array.isArray(data.runs) || data.runs.some(run => run.checklist_id !== version.id || run.checklist_hash !== version.content_hash)) {
        throw new Error('Saved runs do not match this checklist version. Refresh the saved runs.');
      }
      if (!active) return;
      setPage({ key: pageKey, data });
      setSelection(previous => {
        if (previous?.key === versionKey) {
          const updated = data.runs.find(run => run.id === previous.run.id);
          return updated ? { key: versionKey, run: updated } : previous;
        }
        return data.runs[0] ? { key: versionKey, run: data.runs[0] } : null;
      });
    }).catch(error => { if (active) setPage({ key: pageKey, error: error instanceof Error ? error.message : 'Saved runs could not be loaded.' }); });
    return () => { active = false; };
  }, [open, pageKey, versionKey, version.id, version.content_hash, offset]);

  useEffect(() => {
    if (!open || !currentPage?.data || !selected) return;
    let active = true;
    const timer = setTimeout(() => {
      void api<Preview>('/insights/weight-preview', { checklist_id: version.id, evaluation_id: selected.id, basis, draft }).then(data => {
        if (data.checklist_id !== version.id || data.checklist_hash !== version.content_hash || data.evaluation_id !== selected.id || data.basis !== basis
          || (data.eligible && (data.updated_at !== selected.updated_at || data.source?.id !== selected.conversation_id || data.source?.content_hash !== selected.content_hash))) {
          throw new Error('The saved run changed or does not match this selection. Refresh saved runs before previewing.');
        }
        if (active) setResult({ key: requestKey, data });
      }).catch(error => { if (active) setResult({ key: requestKey, error: error instanceof Error ? error.message : 'Weight preview failed.' }); });
    }, 150);
    return () => { active = false; clearTimeout(timer); };
  }, [open, requestKey, !!currentPage?.data, version.id, selected?.id]);

  const options = currentPage?.data?.runs ?? [];
  const visibleOptions = selected && !options.some(run => run.id === selected.id) ? [selected, ...options] : options;
  const packet = current?.data;
  return <details className="panel weight-impact" onToggle={event => {
    const expanded = event.currentTarget.open;
    setOpen(expanded);
    if (expanded) { setOpening(value => value + 1); setOffset(0); }
  }}>
    <summary><span>Weight-impact preview</span><span className="disclosure-hint">Fixed saved judgments · no model calls</span></summary>
    {open && <div className="weight-impact-content">
      <p>Simulate criterion weight changes on a saved run. Definitions, scales, N/A rules and all other fields must stay unchanged. This does not save or evaluate anything.</p>
      <div className="inline-actions"><button className="secondary" onClick={() => { setOffset(0); setRefresh(value => value + 1); }}>Refresh saved runs</button>
        <label>Judgment basis<select aria-label="Weight preview judgment basis" value={basis} onChange={event => setBasis(event.target.value as typeof basis)}><option value="effective">Effective judgments</option><option value="original">Original judgments</option></select></label></div>
      {!currentPage && <p role="status">Loading saved runs…</p>}
      {currentPage?.error && <div role="alert"><p>{currentPage.error}</p><button className="secondary" onClick={() => setRefresh(value => value + 1)}>Retry saved runs</button></div>}
      {currentPage?.data && <>
        {!currentPage.data.total ? <p>No successful saved runs exist for checklist v{version.id}. A new evaluation is not started by this preview.</p> : <>
          <label>Saved run<select aria-label="Weight preview saved run" value={selected?.id ?? ''} onChange={event => {
            const run = visibleOptions.find(item => item.id === event.target.value); if (run) setSelection({ key: versionKey, run });
          }}>{!selected && <option value="">Select a saved run</option>}{visibleOptions.map(run => <option key={run.id} value={run.id}>{runName(run)}</option>)}</select></label>
          <div className="inline-actions"><small>Showing runs {currentPage.data.total ? offset + 1 : 0}–{offset + options.length} of {currentPage.data.total}. Saved selection stays available across pages.</small>
            <button className="secondary" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - 100))}>Previous saved runs</button>
            <button className="secondary" disabled={offset + options.length >= currentPage.data.total} onClick={() => setOffset(offset + 100)}>Next saved runs</button></div>
          {selected && !current && <p role="status">Calculating fixed-judgment scenario…</p>}
          {current?.error && <div role="alert"><p>{current.error}</p><button className="secondary" onClick={() => setRetry(value => value + 1)}>Retry weight preview</button></div>}
          {packet && <><p className="scenario-notice">{packet.notice}</p>
            {!packet.eligible && <div role="status"><strong>Weight preview unavailable</strong><ul>{packet.reasons.map(reason => <li key={reason}>{reason}</li>)}</ul>
              {!!packet.errors.length && <ul>{packet.errors.map((issue, index) => <li key={index}>{issue.label || issue.location.join(' / ')}: {issue.message}</li>)}</ul>}</div>}
            {packet.eligible && packet.original_score && packet.simulated_score && <>
              <p>{packet.source?.group_id} / {packet.source?.source_id} · revision {packet.source?.revision} · checklist v{packet.checklist_id} · {basis} judgments</p>
              <dl className="scenario-totals"><div><dt>Saved total</dt><dd>{show(packet.original_score.total)}</dd></div><div><dt>Simulated total</dt><dd>{show(packet.simulated_score.total)}</dd></div>
                <div><dt>Difference in points</dt><dd>{show(packet.total_difference)}</dd></div><div><dt>Applicable weight</dt><dd>{packet.original_score.applicable_weight} → {packet.simulated_score.applicable_weight}</dd></div></dl>
              {packet.simulated_score.reason && <p>Score withheld: {packet.simulated_score.reason}. Unresolved judgments remain unresolved.</p>}
              <div className="table-scroll"><table><thead><tr><th>Criterion</th><th>Saved judgment</th><th>Weight</th><th>Raw points</th><th>Contribution / 100</th></tr></thead><tbody>
                {packet.criteria?.map(row => <tr key={row.criterion_id}><th scope="row">{row.name}{row.answer_type === 'flag' && <small>Unscored flag</small>}</th><td>{judgmentLabel(row)}</td>
                  <td>{show(row.original.weight)} → {show(row.simulated.weight)}</td><td>{show(row.original.raw_points)} → {show(row.simulated.raw_points)}</td><td>{contribution(row.original.normalized_contribution)} → {contribution(row.simulated.normalized_contribution)}</td></tr>)}
              </tbody></table></div><small>N/A excludes scored weight; flags do not affect totals. Contributions use the applicable denominator and are rounded to four decimal places for display only; rounded values may not sum exactly. Saved values, raw points and totals remain unchanged. Uncertain judgments remain unresolved.</small>
            </>}
          </>}
        </>}
      </>}
    </div>}
  </details>;
}
