import { useRef, useState, useEffect } from 'react';
import { downloadSavedReport } from './api';

export default function SavedExport({ evaluationId }: { evaluationId: string }) {
  const [excerpts, setExcerpts] = useState(false); const [pending, setPending] = useState(false); const [error, setError] = useState('');
  const mounted = useRef(true);
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; }; }, []);
  const download = async (format: 'json' | 'csv') => {
    setPending(true); setError('');
    try { await downloadSavedReport(evaluationId, format, excerpts, () => mounted.current); }
    catch (e) { if (mounted.current) setError(e instanceof Error ? e.message : 'Export failed.'); }
    finally { if (mounted.current) setPending(false); }
  };
  return <section className="panel saved-export" aria-label="Saved report export">
    <div className="inline-actions"><button className="secondary" disabled={pending} onClick={() => void download('json')}>Download JSON</button>
      <button className="secondary" disabled={pending} onClick={() => void download('csv')}>Download CSV</button></div>
    <label className="check-label"><input type="checkbox" checked={excerpts} onChange={e => setExcerpts(e.target.checked)} />Include source evidence excerpts</label>
    <small>Exports include original/effective answers and review history. Explanations may quote source text. Recording links and credentials are excluded.</small>
    {pending && <p role="status">Preparing saved report…</p>}{error && <p role="alert">{error} Retry a download.</p>}
  </section>;
}
