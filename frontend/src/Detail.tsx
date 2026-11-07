import { useCallback, useEffect, useState } from 'react';
import { api } from './api';
import type { BudgetStatus, ConversationDetail, Criterion, EvaluationDetail, Evidence } from './types';
import { EvaluationAction } from './Budget';
import { answerLabel, evidenceMessages, label, points } from './helpers';
import type { Run } from './App';
import ReviewForm from './ReviewForm';
import SavedComparison from './SavedComparison';
import SavedExport from './SavedExport';

export default function Detail({ id, initialEvaluation, initialCriterion = null, initialMessage = null, selectedVersion, busy, run, providerReady, budget, evaluate, onChange }: {
  id: string; initialEvaluation: string | null; selectedVersion: number; busy: boolean; run: Run; providerReady: boolean;
  evaluate: (ids: string[]) => Promise<void>; onChange: () => Promise<void>;
  initialCriterion?: string | null; initialMessage?: string | null; budget?: BudgetStatus | null;
}) {
  const [conversation, setConversation] = useState<ConversationDetail | null>(null);
  const [evaluationId, setEvaluationId] = useState(initialEvaluation ?? '');
  const [evaluation, setEvaluation] = useState<EvaluationDetail | null>(null);
  const [error, setError] = useState(''); const [highlight, setHighlight] = useState<string[]>([]);
  const [appealFor, setAppealFor] = useState(''); const [comment, setComment] = useState('');
  useEffect(() => {
    if (!conversation || !initialMessage) return;
    if (!conversation.snapshot.transcript.some(m => m.id === initialMessage)) { setHighlight([]); return; }
    setHighlight([initialMessage]);
    const message = document.getElementById(`message-${initialMessage}`);
    message?.scrollIntoView({ block: 'center' }); message?.focus({ preventScroll: true });
  }, [conversation, initialMessage]);
  useEffect(() => {
    if (!evaluation || !initialCriterion || (initialEvaluation && evaluation.id !== initialEvaluation)) return;
    const card = document.getElementById(`criterion-${initialCriterion}`);
    card?.scrollIntoView({ block: 'center' }); card?.focus({ preventScroll: true });
  }, [evaluation, initialCriterion, initialEvaluation]);

  useEffect(() => { if (initialEvaluation) setEvaluationId(initialEvaluation); }, [initialEvaluation]);
  const load = useCallback(async () => {
    const detail = await api<ConversationDetail>(`/conversations/${id}`);
    setConversation(detail);
    const selected = evaluationId || detail.evaluations[0]?.id;
    if (selected) {
      const result = await api<EvaluationDetail>(`/evaluations/${selected}`);
      if (result.conversation_id !== id) throw new Error('Evaluation belongs to another conversation revision.');
      setEvaluationId(selected); setEvaluation(result);
    } else setEvaluation(null);
    setError('');
  }, [id, evaluationId]);
  useEffect(() => { void load().catch(e => setError(e.message)); }, [load]);
  const processing = evaluation && ['queued', 'running'].includes(evaluation.state);
  useEffect(() => {
    if (!processing) return;
    const interval = setInterval(() => { void load().catch(e => setError(e.message)); }, 1800);
    return () => clearInterval(interval);
  }, [processing, load]);
  const saved = async () => { await load(); await onChange(); };
  if (!conversation) return <div className="empty" role="status">{error || 'Loading conversation…'}</div>;
  const snapshot = conversation.snapshot;
  const effective = evaluation?.effective;
  const calculated = evaluation?.effective_score;
  const original = evaluation?.original_score;
  const navigateEvidence = (evidence: Evidence) => {
    const range = evidenceMessages(snapshot.transcript, evidence);
    setHighlight(range.map(m => m.id));
    document.getElementById(`message-${range[0]?.id}`)?.scrollIntoView({ block: 'center' });
  };
  const criterionCard = (criterion: Criterion) => {
    const judgment = effective!.results[criterion.id];
    const prior = evaluation!.original!.results[criterion.id];
    const row = calculated!.criteria.find(c => c.criterion_id === criterion.id);
    const changed = JSON.stringify(judgment) !== JSON.stringify(prior);
    return <article className={`panel result-card ${initialCriterion === criterion.id ? 'targeted-criterion' : ''}`} id={`criterion-${criterion.id}`} tabIndex={-1} key={criterion.id}>
      <div className="criterion-head"><div><span className="small-caps">{criterion.answer_type === 'flag' ? 'INDEPENDENT FLAG' : criterion.answer_type === 'scale' ? 'NUMERICAL SCALE' : 'BINARY CRITERION'}</span><h3>{criterion.name}</h3></div>
        <span className={`answer-pill ${judgment.disposition === 'needs_review' ? 'review' : criterion.answer_type === 'flag' && judgment.value === true ? 'flagged' : ''}`}>{answerLabel(judgment.value, judgment.disposition)}</span></div>
      <details className="rubric-definition"><summary>Saved definition & allowed answers</summary><p>{criterion.description}</p>{criterion.na_allowed && <p><strong>N/A:</strong> {criterion.na_condition}</p>}{criterion.scale.map(a => <p key={a.value}><strong>{a.value}</strong> · {a.description}</p>)}</details>
      {criterion.answer_type !== 'flag' && <div className="points-row"><span>Weight <strong>{points(criterion.weight)}</strong></span><span>Raw points <strong>{points(row?.raw_points)}</strong></span><span>Contribution / 100 <strong>{points(row?.normalized_contribution)}</strong></span></div>}
      <p className="explanation">{judgment.explanation}</p>
      {judgment.na_reason && <p className="reason"><strong>N/A reason</strong> {judgment.na_reason}</p>}
      {judgment.review_reason && <p className="reason review"><strong>Missing basis</strong> {judgment.review_reason}</p>}
      <div className="evidence-list">{judgment.evidence.map((evidence, i) => <div key={i}><button className="evidence-button" onClick={() => navigateEvidence(evidence)}>↗ {evidence.start_message_id}{evidence.end_message_id !== evidence.start_message_id ? `–${evidence.end_message_id}` : ''} <span>{evidence.kind}</span></button>
        <blockquote className="evidence-preview">{evidenceMessages(snapshot.transcript, evidence).map(m => m.text).join('\n')}</blockquote></div>)}</div>
      {changed && <div className="change-note">Reviewed · original answer: <strong>{answerLabel(prior.value, prior.disposition)}</strong><details><summary>Inspect preserved original</summary><p>{prior.explanation}</p>{prior.evidence.map((e, i) => <button className="evidence-button" key={i} onClick={() => navigateEvidence(e)}>{e.start_message_id}–{e.end_message_id} · original evidence</button>)}</details></div>}
      <div className="card-actions"><button className="text-button" onClick={() => { setAppealFor(appealFor === criterion.id ? '' : criterion.id); setComment(''); }}>{judgment.disposition === 'needs_review' ? 'Request criterion review' : 'Appeal criterion'}</button></div>
      {appealFor === criterion.id && <form className="appeal-form" onSubmit={event => { event.preventDefault(); void run(async () => {
        await api(`/evaluations/${evaluation!.id}/appeals`, { criterion_id: criterion.id, comment });
        setAppealFor(''); setComment(''); await saved();
      }); }}><label>Appeal comment<textarea required value={comment} onChange={e => setComment(e.target.value)} placeholder="Explain the issue and point to the conversation" /></label><button className="secondary" disabled={busy || !comment.trim()}>Submit appeal</button></form>}
      {evaluation!.appeals.filter(a => a.criterion_id === criterion.id).map(appeal => <ReviewForm key={appeal.id} appeal={appeal} criterion={criterion} evaluation={evaluation!} messages={snapshot.transcript} busy={busy} run={run} onSaved={saved} />)}
    </article>;
  };

  return <>
    <a className="back-link" href="#conversations">← All conversations</a>
    <div className="page-heading detail-heading"><div><div className="eyebrow">CONVERSATION REVIEW</div><h1>{conversation.source_id}</h1><p>{conversation.group_id} · revision {conversation.revision} · {snapshot.language} · {snapshot.channel} · {snapshot.transcript.length} messages</p></div>
      <EvaluationAction ids={[id]} version={selectedVersion} providerReady={providerReady} busy={busy} refreshKey={JSON.stringify(budget)} label={`Evaluate with v${selectedVersion} →`} start={() => void run(() => evaluate([id]))} /></div>
    {error && <div className="banner error" role="alert">{error}</div>}
    <div className="detail-layout"><section className="panel transcript-panel" aria-label="Conversation transcript">
      <div className="transcript-heading"><h2>Transcript</h2><span className="badge">Source revision {conversation.revision}</span></div>
      {initialMessage && !snapshot.transcript.some(m => m.id === initialMessage) && <p role="alert">The linked message is unavailable in this source revision.</p>}
      {snapshot.channel === 'voice call' && <div className="audio-panel">{snapshot.audio_url ? <><a href={snapshot.audio_url} target="_blank" rel="noreferrer">Open recording ↗</a><small>Recording opens in its source player. Evidence links navigate the transcript. Source recording access can expire.</small></> : <p>Recording unavailable. The full provided transcript is available below.</p>}</div>}
      <div className="transcript-scroll">{snapshot.transcript.map(message => <article key={message.id} id={`message-${message.id}`} tabIndex={-1} className={`message ${message.speaker} ${highlight.includes(message.id) ? 'highlighted' : ''}`}>
        <div className="message-meta"><strong>{message.speaker}</strong><span>{message.id} · {message.timestamp}</span></div><p>{message.text}</p>
      </article>)}</div><div className="transcript-foot">Source text and timestamp strings are preserved. Bot and system messages provide context.</div>
    </section><section className="assessment-panel" aria-label="Conversation assessment">
      <div className="assessment-heading"><h2>Assessment</h2><label className="evaluation-picker">Saved run<select aria-label="Saved evaluation" value={evaluationId} onChange={e => { setEvaluation(null); setEvaluationId(e.target.value); }}><option value="" disabled>No saved evaluation</option>{conversation.evaluations.map(e => <option key={e.id} value={e.id}>v{e.checklist_id} · {label(e.state)} · {new Date(e.created_at).toLocaleTimeString()}</option>)}</select></label></div>
      <SavedComparison key={conversation.id} runs={conversation.evaluations} currentId={evaluationId} sourceId={conversation.id} onEvidence={navigateEvidence} />
      {!evaluation && <div className="panel empty"><strong>No saved assessment selected</strong><p>Choose a saved checklist version and evaluate this conversation. Provider configuration is required for a live assessment.</p></div>}
      {evaluation && <>
        <SavedExport key={evaluation.id} evaluationId={evaluation.id} />
        <div className="run-meta"><span className={`badge ${evaluation.state}`}>{evaluation.state}</span><span className="badge">Checklist v{evaluation.checklist_id}</span><span className="badge">{evaluation.cached_from ? 'Cached original assessment' : evaluation.metadata.mode}</span></div>
        {evaluation.error && <div className="banner error"><div><strong>Evaluation {evaluation.state}</strong><p>{evaluation.error}</p></div></div>}
        {['failed', 'interrupted'].includes(evaluation.state) && <button className="secondary" disabled={busy || !providerReady || !budget?.ready} onClick={() => void run(async () => { await api(`/evaluations/${evaluation.id}/retry`, {}); await saved(); })}>Retry saved job</button>}
        {processing && <div className="panel empty" role="status"><strong>{evaluation.state === 'queued' ? 'Queued for evaluation' : 'Evaluating the complete transcript…'}</strong><p>Progress is persisted. You can navigate away and return.</p></div>}
        {effective && calculated && <>
          <div className="panel total-panel"><div><span className="small-caps">EFFECTIVE SCORE / 100</span><div className="total-value">{calculated.total ?? '—'}<small>{calculated.total ? '/ 100' : calculated.reason === 'UNRESOLVED_CRITERIA' ? 'Needs review' : 'No applicable scored weight'}</small></div></div>
            <div className="original-total"><span>Original</span><strong>{original?.total ?? '—'}</strong><small>{evaluation.reviews.length} saved decision(s)</small></div>
            <p>{points(calculated.raw_subtotal)} raw points / {points(calculated.applicable_weight)} applicable weight. Final display rounded to two decimals.</p>
          </div>
          <div className="section-scores">{calculated.sections.map(section => <div key={section.id}><span>{section.title}</span><strong>{section.total == null ? 'No numeric result' : `${section.total}%`}</strong></div>)}</div>
          {evaluation.checklist.snapshot.sections.map(section => <section className="criterion-section" key={section.id}><h2>{section.title}</h2>{evaluation.checklist.snapshot.criteria.filter(c => c.section_id === section.id).map(criterionCard)}</section>)}
          <details className="panel history-panel"><summary>Decision history · {evaluation.reviews.length}</summary>{evaluation.reviews.length ? evaluation.reviews.map(review => <article className="history-item" key={review.id}><strong>Decision {review.id} · {review.criterion_id} · {review.action}</strong><p>{review.rationale}</p><p>Answer: {answerLabel(review.judgment.value, review.judgment.disposition)} · effective total at decision: {review.resulting_score.total ?? 'not calculated'}</p><small>{new Date(review.created_at).toLocaleString()}</small></article>) : <p>No reviewer decisions saved.</p>}</details>
        </>}
        <details className="panel usage-panel"><summary>Model, usage & attempts</summary><p>{evaluation.metadata.provider} · {evaluation.metadata.model} · {evaluation.metadata.prompt_version}</p>
          {evaluation.cached_from && <p>Reused the immutable original from run {evaluation.cached_from}. Reviewer changes were not copied. This run made no model call.</p>}
          <p>{evaluation.usage.request_attempts} request attempts · {evaluation.usage.input_tokens_known} known input tokens · {evaluation.usage.output_tokens_known} known output tokens · {(evaluation.usage.latency_ms / 1000).toFixed(2)}s request latency</p>
          <p>Estimated cost: {evaluation.usage.estimated_cost_usd == null ? 'Unavailable' : `$${evaluation.usage.estimated_cost_usd}`} {evaluation.usage.cost_rate_source && `· ${evaluation.usage.cost_rate_source}`}</p>
          {!evaluation.usage.usage_complete && <p className="muted">Usage is incomplete or no billable request was made. Unknown usage is not reported as zero cost.</p>}
          {evaluation.attempts.map(attempt => <p key={attempt.number}>Attempt {attempt.number}: {attempt.status} · {(attempt.latency_ms / 1000).toFixed(2)}s</p>)}
        </details>
      </>}
    </section></div>
  </>;
}
