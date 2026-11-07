import { useEffect, useState } from 'react';
import { api } from './api';
import type { BudgetStatus, EvaluationPreview } from './types';

export function BudgetSummary({ budget }: { budget: BudgetStatus | null }) {
  if (!budget) return null;
  return <section className="panel budget-summary" aria-label="Shared spending budget">
    <strong>Shared spending limit: ${Number(budget.limit_usd).toFixed(2)}</strong>
    <span>Accounted estimates: ${Number(budget.accounted_usd).toFixed(4)} · Reserved: ${Number(budget.reserved_usd).toFixed(4)} · Overhead reserve: ${Number(budget.overhead_usd).toFixed(2)}</span>
    <span>Available for new reservations: ${Number(budget.available_usd).toFixed(4)}</span>
    <small>{budget.blocked_reason || 'New paid work must fit this budget before it can start.'} Saved results and reviews remain available. These estimates and reservations are not an account balance.</small>
  </section>;
}

export function EvaluationAction({ ids, version, providerReady, busy, label, start, refreshKey }: {
  ids: string[]; version: number; providerReady: boolean; busy: boolean; label: string; start: () => void;
  refreshKey?: string;
}) {
  const signature = JSON.stringify({ ids, version, providerReady, refreshKey });
  const [result, setResult] = useState<{ signature: string; preview?: EvaluationPreview; error?: string } | null>(null);
  useEffect(() => {
    if (!ids.length || !version || !providerReady) return;
    let cancelled = false;
    void api<EvaluationPreview>('/evaluations/preview', { conversation_ids: ids, checklist_id: version }).then(
      preview => { if (!cancelled) setResult({ signature, preview }); },
      error => { if (!cancelled) setResult({ signature, error: error.message }); });
    return () => { cancelled = true; };
  }, [signature]); // Signature covers selection, version and provider readiness.
  const current = result?.signature === signature ? result : null;
  const preview = current?.preview;
  return <div className="evaluation-action">
    <button className="primary" disabled={busy || !providerReady || !ids.length || !preview?.affordable} onClick={start}>{label}</button>
    {!!ids.length && providerReady && <small role="status">{current?.error || (preview ? <>
      {preview.required_reservation_usd !== null && <>Reserve up to ${Number(preview.required_reservation_usd).toFixed(4)} · </>}
      {preview.cached} cached · {preview.active} already processing · {preview.new_evaluations} new
      {preview.blocked_reason && <> · {preview.blocked_reason}</>}
    </> : 'Checking cost and cache compatibility…')}</small>}
  </div>;
}
