import { useRef, useState, useEffect } from 'react';
import { downloadSavedReport } from './api';
import type { ReportFormat } from './api';

export default function SavedExport({ evaluationId }: { evaluationId: string }) {
  const [excerpts, setExcerpts] = useState(false); const [pending, setPending] = useState(false); const [error, setError] = useState('');
  const mounted = useRef(true); const selected = useRef(evaluationId); const sequence = useRef(0);
  selected.current = evaluationId;
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; }; }, []);
  useEffect(() => { sequence.current += 1; setPending(false); setError(''); }, [evaluationId]);
  const download = async (format: ReportFormat) => {
    const token = ++sequence.current;
    const active = () => mounted.current && selected.current === evaluationId && sequence.current === token;
    setPending(true); setError('');
    try { await downloadSavedReport(evaluationId, format, excerpts, active); }
    catch (e) { if (active()) setError(e instanceof Error ? e.message : 'Export failed.'); }
    finally { if (active()) setPending(false); }
  };
  return <section className="panel saved-export" aria-label="Saved report export">
    <div className="inline-actions"><button className="secondary" disabled={pending} onClick={() => void download('json')}>Download JSON</button>
      <button className="secondary" disabled={pending} onClick={() => void download('csv')}>Download CSV</button>
      <button className="secondary" disabled={pending} onClick={() => void download('simple_csv')}>Download simple CSV</button></div>
    <label className="check-label"><input type="checkbox" checked={excerpts} onChange={e => setExcerpts(e.target.checked)} />Include source evidence excerpts</label>
    <small>JSON and archival CSV include original/effective answers and review history. Simple CSV contains criterion rows for spreadsheets. Explanations may quote source text. Recording links and credentials are excluded.</small>
    {pending && <p role="status">Preparing saved report…</p>}{error && <p role="alert">{error} Retry a download.</p>}
  </section>;
}
