import { useEffect, useRef, useState } from 'react';

export default function ReviewLink({ sourceId, evaluationId }: { sourceId: string; evaluationId: string }) {
  const key = JSON.stringify([sourceId, evaluationId]);
  const current = useRef(key); current.current = key;
  const mounted = useRef(true); const manual = useRef<HTMLInputElement>(null);
  const [outcome, setOutcome] = useState<{ key: string; state: 'pending' | 'copied' | 'manual' } | null>(null);
  const state = outcome?.key === key ? outcome.state : null;
  const link = `${location.origin}${location.pathname}#conversation/${encodeURIComponent(sourceId)}?evaluation=${encodeURIComponent(evaluationId)}`;
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; }; }, []);
  useEffect(() => { if (state === 'manual') { manual.current?.focus(); manual.current?.select(); } }, [state]);
  const copy = async () => {
    setOutcome({ key, state: 'pending' });
    try {
      if (!navigator.clipboard?.writeText) throw new Error('Clipboard unavailable');
      await navigator.clipboard.writeText(link);
      if (mounted.current && current.current === key) setOutcome({ key, state: 'copied' });
    } catch {
      if (mounted.current && current.current === key) setOutcome({ key, state: 'manual' });
    }
  };
  return <div className="review-link">
    <button className="secondary" disabled={state === 'pending'} onClick={() => void copy()}>Copy review link</button>
    {state === 'copied' && <small role="status">Copied link to this saved run.</small>}
    {state === 'manual' && <div className="review-link-manual"><label>Review link<input ref={manual} readOnly value={link} /></label><small role="status">Copy the selected link. It opens this saved run in this workspace.</small></div>}
  </div>;
}
