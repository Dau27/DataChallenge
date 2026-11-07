import { useState } from 'react';
import { api } from './api';
import type { Appeal, Criterion, EvaluationDetail, Judgment, Message } from './types';
import type { Run } from './App';
import { answerLabel } from './helpers';

export default function ReviewForm({ appeal, criterion, evaluation, messages, busy, run, onSaved }: {
  appeal: Appeal; criterion: Criterion; evaluation: EvaluationDetail; messages: Message[];
  busy: boolean; run: Run; onSaved: () => Promise<void>;
}) {
  const original = evaluation.original!.results[criterion.id];
  const effective = evaluation.effective!.results[criterion.id];
  const [action, setAction] = useState<'confirm' | 'replace'>(effective.disposition === 'needs_review' ? 'replace' : 'confirm');
  const [disposition, setDisposition] = useState<'assessed' | 'not_applicable'>('assessed');
  const [value, setValue] = useState(String(effective.value ?? (criterion.answer_type === 'scale' ? criterion.scale[0]?.value : true)));
  const [explanation, setExplanation] = useState(''); const [naReason, setNaReason] = useState('');
  const [rationale, setRationale] = useState('');
  const [kind, setKind] = useState<'support' | 'absence' | 'context'>('support');
  const [start, setStart] = useState(effective.evidence[0]?.start_message_id ?? messages[0].id);
  const [end, setEnd] = useState(effective.evidence[0]?.end_message_id ?? messages[0].id);
  const [expanded, setExpanded] = useState(false);
  return <div className="review-form">
    <div className="review-summary"><div><strong>Appeal · {appeal.status}</strong><p>{appeal.comment}</p><small>{new Date(appeal.created_at).toLocaleString()}</small></div>
      {appeal.status === 'open' && <button className="secondary" onClick={() => setExpanded(!expanded)}>{expanded ? 'Close review' : 'Review appeal'}</button>}</div>
    {expanded && appeal.status === 'open' && <form onSubmit={event => { event.preventDefault(); void run(async () => {
      const judgment: Judgment | null = action === 'confirm' ? null : {
        disposition, value: disposition === 'not_applicable' ? null : criterion.answer_type === 'scale' ? Number(value) : value === 'true',
        explanation, na_reason: disposition === 'not_applicable' ? naReason : null, review_reason: null,
        evidence: [{ kind, start_message_id: start, end_message_id: end }],
      };
      await api(`/appeals/${appeal.id}/decision`, { action, rationale, judgment, expected_updated_at: evaluation.updated_at });
      await onSaved(); setExpanded(false);
    }); }}>
      <div className="review-context"><span>Original: <strong>{answerLabel(original.value, original.disposition)}</strong></span><span>Current: <strong>{answerLabel(effective.value, effective.disposition)}</strong></span><p>{effective.explanation}</p></div>
      <p className="muted">This anonymous demo review is a separate action from appeal submission. It does not establish a secure reviewer identity.</p>
      <label>Reviewer action<select value={action} onChange={e => setAction(e.target.value as 'confirm' | 'replace')}><option value="confirm" disabled={effective.disposition === 'needs_review'}>Confirm current answer</option><option value="replace">Replace / resolve answer</option></select></label>
      {action === 'replace' && <>
        <label>Disposition<select value={disposition} onChange={e => setDisposition(e.target.value as 'assessed' | 'not_applicable')}><option value="assessed">Assessed</option>{criterion.na_allowed && <option value="not_applicable">N/A — only if the saved condition holds</option>}</select></label>
        {disposition === 'assessed' ? <label>Replacement answer<select value={value} onChange={e => setValue(e.target.value)}>{criterion.answer_type === 'scale'
          ? criterion.scale.map(a => <option key={a.value} value={a.value}>{a.value} · {a.description}</option>)
          : <><option value="true">Yes</option><option value="false">No</option></>}</select></label>
          : <label>N/A justification <small>{criterion.na_condition}</small><textarea required value={naReason} onChange={e => setNaReason(e.target.value)} /></label>}
        <label>Criterion explanation<textarea required value={explanation} onChange={e => setExplanation(e.target.value)} /></label>
        <div className="form-grid"><label>Evidence kind<select value={kind} onChange={e => setKind(e.target.value as typeof kind)}><option>support</option><option>absence</option><option>context</option></select></label>
          <label>Start message<select value={start} onChange={e => setStart(e.target.value)}>{messages.map(m => <option key={m.id} value={m.id}>{m.id} · {m.speaker} · {m.timestamp}</option>)}</select></label>
          <label>End message<select value={end} onChange={e => setEnd(e.target.value)}>{messages.map(m => <option key={m.id} value={m.id}>{m.id} · {m.speaker} · {m.timestamp}</option>)}</select></label></div>
      </>}
      <label>Decision rationale<textarea required value={rationale} onChange={e => setRationale(e.target.value)} placeholder="Why this answer is confirmed or replaced" /></label>
      <button className="primary" disabled={busy || !rationale.trim()}>Save decision & recalculate</button>
    </form>}
  </div>;
}
