import { useEffect, useRef, useState } from 'react';
import { downloadSelectedReports } from './api';
import type { ReportFormat } from './api';

export default function QueueExport({ evaluationIds, onError }: { evaluationIds: string[]; onError?: () => void }) {
  const [excerpts, setExcerpts] = useState(false); const [pending, setPending] = useState(false); const [error, setError] = useState('');
  const mounted = useRef(true); const sequence = useRef(0);
  const selection = JSON.stringify(evaluationIds); const latestSelection = useRef(selection); latestSelection.current = selection;
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; }; }, []);
  useEffect(() => { sequence.current += 1; setPending(false); setError(''); }, [selection]);
  const invalid = evaluationIds.length > 100 || new Set(evaluationIds).size !== evaluationIds.length || evaluationIds.some(id => !id.trim() || id.length > 200);
  const download = async (format: ReportFormat) => {
    if (!evaluationIds.length || invalid) return;
    const token = ++sequence.current;
    const active = () => mounted.current && latestSelection.current === selection && sequence.current === token;
    setPending(true); setError('');
    try { await downloadSelectedReports([...evaluationIds], format, excerpts, active); }
    catch (e) { if (active()) { setError(e instanceof Error ? e.message : 'Selected-run export failed.'); onError?.(); } }
    finally { if (active()) setPending(false); }
  };
  return <section className="saved-export" aria-label="Selected saved-run export">
    <p>Export selected saved runs: <strong>{evaluationIds.length}</strong></p>
    <div className="inline-actions">
      <button className="secondary" disabled={pending || !evaluationIds.length || invalid} onClick={() => void download('json')}>Selected JSON</button>
      <button className="secondary" disabled={pending || !evaluationIds.length || invalid} onClick={() => void download('csv')}>Selected archive CSV</button>
      <button className="secondary" disabled={pending || !evaluationIds.length || invalid} onClick={() => void download('simple_csv')}>Selected simple CSV</button>
    </div>
    <label className="check-label"><input type="checkbox" checked={excerpts} onChange={e => setExcerpts(e.target.checked)} />Include selected source evidence excerpts</label>
    <small>Only selected visible conversations with a saved run are included, up to 100 runs. JSON/archive CSV retain review history; simple CSV contains criterion rows. Source quotations can be sensitive.</small>
    {invalid && <p role="alert">Choose at most 100 unique saved runs.</p>}
    {pending && <p role="status">Preparing selected saved reports…</p>}{error && <p role="alert">{error} Retry an export.</p>}
  </section>;
}
