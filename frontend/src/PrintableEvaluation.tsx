import { useEffect, useId, useRef, useState } from 'react';
import { api } from './api';
import { useLatestResource } from './useLatestResource';
import { renderPrintableEvaluation } from './printEvaluation';
import type { PrintIdentity } from './printEvaluationTypes';
import './printEvaluation.css';

/** The coordinator mounts this alongside SavedExport for the exact selected saved run. */
export default function PrintableEvaluation({ evaluationId, updatedAt }: PrintIdentity) {
  const [open, setOpen] = useState(false);
  const [includeExcerpts, setIncludeExcerpts] = useState(false);
  const [loaded, setLoaded] = useState<number | null>(null);
  const [printError, setPrintError] = useState<{ token: number; message: string } | null>(null);
  const [frameError, setFrameError] = useState<number | null>(null);
  const trigger = useRef<HTMLButtonElement>(null), heading = useRef<HTMLHeadingElement>(null), frame = useRef<HTMLIFrameElement>(null);
  const sequence = useRef(0);
  const previewId = useId(), noticeId = useId();
  const key = JSON.stringify([open, evaluationId, updatedAt, 'original+effective', includeExcerpts]);
  const report = useLatestResource(key, async () => {
    if (!open) return null;
    const token = ++sequence.current;
    const packet = await api<unknown>(`/evaluations/${encodeURIComponent(evaluationId)}/export?format=json&include_excerpts=${includeExcerpts}`);
    return { token, html: renderPrintableEvaluation(packet, { evaluationId, updatedAt }, includeExcerpts) };
  });
  const visible = open ? report.value : null;
  const ready = !!visible && !report.pending && loaded === visible.token && frameError !== visible.token;
  useEffect(() => { if (open) heading.current?.focus(); }, [open]);
  useEffect(() => {
    const node = frame.current;
    if (!node || !visible) return;
    // iframe error events do not bubble; listen directly rather than relying on delegation.
    const failed = () => setFrameError(visible.token);
    node.addEventListener('error', failed);
    return () => node.removeEventListener('error', failed);
  }, [visible?.token]);
  const print = () => {
    if (!ready || !visible || !frame.current?.contentWindow) return;
    setPrintError(null);
    try { frame.current.contentWindow.focus(); frame.current.contentWindow.print(); }
    catch { setPrintError({ token: visible.token, message: 'The browser could not open printing. Retry, or use your browser’s print command while the report preview has focus.' }); }
  };
  return <section className="cqa-print-tool" aria-label="Printable saved evaluation">
    <button ref={trigger} type="button" className="secondary" aria-expanded={open} aria-controls={previewId}
      disabled={!evaluationId || !updatedAt} onClick={() => {
        setOpen(v => !v);
        if (open) trigger.current?.focus();
      }}>{open ? 'Close print preview' : 'Preview saved report'}</button>
    {open && <div id={previewId} className="cqa-print-preview">
      <h3 ref={heading} tabIndex={-1}>Print preview · original and effective</h3>
      <label className="cqa-print-option"><input type="checkbox" checked={includeExcerpts} aria-describedby={noticeId}
        onChange={event => setIncludeExcerpts(event.target.checked)} />Include source evidence excerpts</label>
      <p id={noticeId} className="cqa-print-notice">Excerpts are optional. Explanations and review comments may quote private source text, so this report is not anonymous. Recording links and credentials are excluded.</p>
      <div className="cqa-print-actions"><button type="button" className="secondary" disabled={!ready} onClick={print}>Print / Save as PDF</button>
        <button type="button" className="secondary" disabled={report.pending} onClick={() => void report.reload().catch(() => {})}>Refresh print preview</button></div>
      <p className="cqa-print-notice">Printing opens only after you activate Print / Save as PDF. Choose paper size and browser headers/footers in the print dialog. Saved values are not recalculated.</p>
      {report.pending && <p role="status">Preparing saved print report…</p>}
      {report.error && <div className="cqa-print-error" role="alert"><p>{report.error}</p><button type="button" className="secondary" onClick={() => void report.reload().catch(() => {})}>Retry print preview</button></div>}
      {printError && visible?.token === printError.token && <div className="cqa-print-error" role="alert">{printError.message}</div>}
      {visible && frameError === visible.token && <div className="cqa-print-error" role="alert"><p>The browser could not load the report preview. Retry the preview in this browser.</p>
        <button type="button" className="secondary" onClick={() => void report.reload().catch(() => {})}>Retry print preview</button></div>}
      {visible && <><iframe key={visible.token} ref={frame} title="Saved evaluation report preview" className="cqa-print-frame"
        sandbox="allow-same-origin allow-modals" referrerPolicy="no-referrer" srcDoc={visible.html}
        onLoad={() => { setFrameError(null); setLoaded(visible.token); }} />
        {!ready && frameError !== visible.token && <p role="status">Loading printable pages…</p>}</>}
    </div>}
  </section>;
}
