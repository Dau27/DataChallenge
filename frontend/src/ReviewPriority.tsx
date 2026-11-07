import { useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import { api } from './api';
import type { Conversation } from './types';

type ReasonCode = 'open_appeal' | 'needs_review' | 'critical_true' | 'critical_unknown' | 'failed' | 'interrupted' | 'not_evaluated' | 'in_progress';
type Target = { conversation_id: string; evaluation_id: string | null; criterion_id: string | null; criterion_name: string | null; appeal_id?: string };
type Reason = { code: ReasonCode; label: string; since: string | null; targets: Target[] };
type Item = { conversation_id: string; source_id: string; group_id: string; evaluation_id: string | null; state: string;
  reasons: Reason[]; flag_counts: { true: number; false: number; unknown: number }; configured_flags: number; oldest_reason_at: string | null };
type Packet = { checklist_id: number; basis: 'effective'; counts: Record<ReasonCode, number>; items: Item[]; notice: string;
  manifest: { conversation_id: string; content_hash: string; evaluation_id: string | null; updated_at: string | null; state: string }[] };
type Emphasis = 'normal' | 'appeals' | 'unresolved' | 'critical' | 'failed' | 'oldest';
const labels: Record<ReasonCode, string> = { open_appeal: 'Open appeals', needs_review: 'Unresolved or unavailable judgments', critical_true: 'Recorded critical findings',
  critical_unknown: 'Critical status unknown', failed: 'Failed evaluations', interrupted: 'Interrupted evaluations', not_evaluated: 'Not evaluated', in_progress: 'In progress' };
const ordering: Record<Emphasis, string> = { normal: 'Normal queue order', appeals: 'Open appeals first', unresolved: 'Unresolved judgments first',
  critical: 'Recorded critical findings first', failed: 'Failed or interrupted first', oldest: 'Oldest recorded reason first' };
const hasReason = (item: Item, code: ReasonCode) => item.reasons.some(reason => reason.code === code);
const compare = (a: string, b: string) => a < b ? -1 : a > b ? 1 : 0;
const timestamp = (value: string | null) => { const parsed = value ? Date.parse(value) : NaN; return Number.isFinite(parsed) ? parsed : Number.POSITIVE_INFINITY; };
const href = (target: Target) => `#conversation/${encodeURIComponent(target.conversation_id)}${target.evaluation_id
  ? `?evaluation=${encodeURIComponent(target.evaluation_id)}${target.criterion_id ? `&criterion=${encodeURIComponent(target.criterion_id)}` : ''}` : ''}`;

export function useReviewPriority(rows: Conversation[], checklistId: number): { rows: Conversation[]; controls: ReactNode; renderReasons: (id: string) => ReactNode; pending: boolean; error: string; reset: () => void } {
  const [open, setOpen] = useState(false); const [emphasis, setEmphasis] = useState<Emphasis>('normal');
  const [reasonFilter, setReasonFilter] = useState<ReasonCode | 'any'>('any'); const [retry, setRetry] = useState(0);
  const [state, setState] = useState<{ key: string; packet?: Packet; error?: string } | null>(null);
  const scopeKey = JSON.stringify([checklistId, rows.map(row => [row.id, row.content_hash, row.evaluation?.id ?? null,
    row.evaluation?.updated_at ?? null, row.evaluation?.state ?? 'not_evaluated', row.evaluation?.completeness,
    row.pending_appeals ?? 0, row.pending_review_targets ?? [], row.critical_findings ?? []])]);
  const key = JSON.stringify([scopeKey, retry]);
  const activeView = emphasis !== 'normal' || reasonFilter !== 'any';
  const requested = open || activeView;
  const validScope = checklistId > 0 && rows.length <= 200;
  useEffect(() => {
    if (!requested || !validScope) return;
    let active = true;
    void api<Packet>('/insights/review-priority', { checklist_id: checklistId, conversation_ids: rows.map(row => row.id) }).then(packet => {
      if (packet.checklist_id !== checklistId || packet.basis !== 'effective' || packet.manifest.length !== rows.length
        || packet.items.length !== rows.length || new Set(packet.items.map(item => item.conversation_id)).size !== rows.length
        || packet.manifest.some((entry, index) => { const row = rows[index]; return !row || entry.conversation_id !== row.id
          || entry.content_hash !== row.content_hash || entry.evaluation_id !== (row.evaluation?.id ?? null)
          || entry.updated_at !== (row.evaluation?.updated_at ?? null) || entry.state !== (row.evaluation?.state ?? 'not_evaluated'); })
        || packet.items.some(item => !rows.some(row => row.id === item.conversation_id))) {
        throw new Error('Saved results changed. Refresh the queue and retry priority analysis.');
      }
      if (active) setState({ key, packet });
    }).catch(error => { if (active) setState({ key, error: error instanceof Error ? error.message : 'Priority analysis failed.' }); });
    return () => { active = false; };
  }, [key, requested, validScope]);
  const current = state?.key === key ? state : null;
  const packet = current?.packet;
  const lookup = new Map(packet?.items.map(item => [item.conversation_id, item]) ?? []);
  let visible = rows;
  if (activeView) {
    visible = !packet || !validScope ? [] : rows.filter(row => reasonFilter === 'any' || hasReason(lookup.get(row.id)!, reasonFilter));
    if (emphasis !== 'normal') {
      const selected = (item: Item) => emphasis === 'appeals' ? hasReason(item, 'open_appeal') : emphasis === 'unresolved' ? hasReason(item, 'needs_review')
        : emphasis === 'critical' ? hasReason(item, 'critical_true') : emphasis === 'failed' ? hasReason(item, 'failed') || hasReason(item, 'interrupted') : true;
      visible = [...visible].sort((a, b) => {
        const left = lookup.get(a.id)!; const right = lookup.get(b.id)!;
        return Number(selected(right)) - Number(selected(left))
          || (timestamp(left.oldest_reason_at) - timestamp(right.oldest_reason_at) || 0)
          || compare(a.group_id, b.group_id) || compare(a.source_id, b.source_id) || compare(a.id, b.id);
      });
    }
  }
  const controls = <><details className="review-priority" open={open} onToggle={event => setOpen(event.currentTarget.open)}>
    <summary><span>Review priority</span><span className="disclosure-hint">{activeView ? `${ordering[emphasis]}${reasonFilter !== 'any' ? ` · ${labels[reasonFilter]}` : ''}` : 'Explain and prioritise saved review states'}</span></summary>
    <div hidden={!open}>
    <p>Uses the selected checklist and current filtered conversations. Effective results only; reasons do not change scores or resolve reviews.</p>
    <div className="inline-actions"><label>Priority order<select aria-label="Review priority order" value={emphasis} onChange={event => setEmphasis(event.target.value as Emphasis)}>
      {(Object.keys(ordering) as Emphasis[]).map(value => <option key={value} value={value}>{ordering[value]}</option>)}
    </select></label><label>Review reason<select aria-label="Review priority reason" value={reasonFilter} onChange={event => setReasonFilter(event.target.value as ReasonCode | 'any')}>
      <option value="any">Any reason or no reason</option>{(Object.keys(labels) as ReasonCode[]).map(code => <option key={code} value={code}>{labels[code]}</option>)}
    </select></label><button className="text-button" disabled={!activeView} onClick={() => { setEmphasis('normal'); setReasonFilter('any'); }}>Reset priority view</button></div>
    {!validScope && <p role="alert">Narrow the queue to at most 200 conversations and select a saved checklist before using review priority.</p>}
    {requested && validScope && !current && <p role="status">Loading current review reasons…{activeView ? ' The priority view is waiting for this selection.' : ''}</p>}
    {current?.error && <div role="alert"><p>{current.error}</p><button className="secondary" onClick={() => setRetry(value => value + 1)}>Retry priority analysis</button></div>}
    {packet && <><p>{packet.notice}</p><div className="priority-counts">{(Object.keys(labels) as ReasonCode[]).map(code => <span key={code}>{labels[code]}: <strong>{packet.counts[code]}</strong></span>)}</div>
      <small>Reason counts are conversations and can overlap. {ordering[emphasis]}; ties use oldest recorded reason, dataset, source ID and revision ID. Unknown critical status is kept separate from false. No configured flags means no critical-status assessment.</small></>}
    </div></details>{!open && activeView && <div className="priority-active-status" role={current?.error || !validScope ? 'alert' : 'status'}>
    <p>Priority view: {ordering[emphasis]}{reasonFilter !== 'any' ? ` · ${labels[reasonFilter]}` : ''}.
      {!validScope ? ' Narrow the queue to at most 200 conversations and select a saved checklist.'
        : current?.error ? ` ${current.error} Results are withheld until retry or reset.`
          : !packet ? ' Loading current reasons; priority results are temporarily withheld.' : ` Showing ${visible.length} of ${rows.length} conversations.`}</p>
    <button className="text-button" onClick={() => setOpen(true)}>Edit priority view</button>
    {current?.error && <button className="secondary" onClick={() => setRetry(value => value + 1)}>Retry priority analysis</button>}
    <button className="text-button" onClick={() => { setEmphasis('normal'); setReasonFilter('any'); }}>Reset priority view</button>
  </div>}</>;
  const renderReasons = (id: string) => {
    const item = lookup.get(id);
    if (!item || !validScope) return null;
    return <div className="priority-reasons">{item.reasons.map(reason => <div key={reason.code}><small><strong>{reason.label}</strong>{reason.since && <> · since <time dateTime={reason.since}>{reason.since.slice(0, 10)}</time></>}</small>
      {reason.targets.map((target, index) => <small key={target.appeal_id ?? `${target.evaluation_id}-${target.criterion_id}-${index}`}><a href={href(target)}>{target.criterion_name || 'Open saved review'}{target.conversation_id !== id ? ' · earlier revision' : ''}</a></small>)}
    </div>)}<small>{item.configured_flags ? `Critical flags: ${item.flag_counts.true} true · ${item.flag_counts.false} false · ${item.flag_counts.unknown} unknown` : 'No critical flags configured'}</small></div>;
  };
  return { rows: visible, controls, renderReasons,
    pending: activeView && validScope && !current,
    error: activeView ? !validScope ? 'Narrow the queue to at most 200 conversations and select a saved checklist.' : current?.error ?? '' : '',
    reset: () => { setEmphasis('normal'); setReasonFilter('any'); } };
}
