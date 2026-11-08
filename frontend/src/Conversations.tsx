import { useEffect, useRef, useState } from 'react';
import { api } from './api';
import type { Access, BudgetStatus, Conversation } from './types';
import { EvaluationAction } from './Budget';
import { label, statusOf } from './helpers';
import type { Run } from './App';
import { useSavedFilters } from './SavedFilters';
import TranscriptMatches from './TranscriptMatches';
import QueueExport from './QueueExport';
import QueueFilters from './QueueFilters';
import QueueViewTools, { useQueueDensity } from './QueueViewTools';
import CriterionBreakdown from './CriterionBreakdown';
import { useReviewPriority } from './ReviewPriority';
import CohortComparison from './CohortComparison';

const reviewHref = (row: Conversation) => {
  const source = `#conversation/${encodeURIComponent(row.id)}`;
  return row.evaluation ? `${source}?evaluation=${encodeURIComponent(row.evaluation.id)}` : source;
};

export default function Conversations({ rows, access, budget, selectedVersion, completed, needsReview, busy, run, evaluate, refresh, notify, onOpenPair }: {
  rows: Conversation[]; access: Access | null; selectedVersion: number; completed: number; needsReview: number;
  busy: boolean; run: Run; evaluate: (ids: string[]) => Promise<void>; refresh: () => Promise<void>; notify: (message: string) => void;
  budget?: BudgetStatus | null;
  onOpenPair?: (leftEvaluationId: string, rightEvaluationId: string) => void;
}) {
  const { filters, setField, controls, warning: filterWarning, external: filtersChangedElsewhere, selectedName, dirty: filtersDirty } = useSavedFilters(selectedVersion);
  const [density, setDensity] = useQueueDensity();
  const { language, channel, status, group, search, appeals, critical, text, speaker } = filters;
  const [groupToImport, setGroupToImport] = useState('DEV');
  const [checked, setChecked] = useState<string[]>([]); const fileRef = useRef<HTMLInputElement>(null);
  const queueTools = useRef<HTMLDetailsElement>(null); const selectAll = useRef<HTMLInputElement>(null);
  const [retrySearch, setRetrySearch] = useState(0);
  const [searchResult, setSearchResult] = useState<{ key: string; rows: Conversation[]; error: string }>({ key: '', rows: [], error: '' });
  const query = text.trim(); const searching = !!query || speaker !== 'all';
  const sourcesKey = JSON.stringify(rows.map(r => [r.id, r.content_hash]));
  const searchKey = JSON.stringify([selectedVersion, query, speaker, sourcesKey, retrySearch]);
  useEffect(() => {
    if (!searching) return;
    let active = true;
    const timer = setTimeout(() => {
      const params = new URLSearchParams({ checklist_id: String(selectedVersion), q: query, speaker });
      void api<Conversation[]>(`/conversations?${params}`).then(data => {
        if (data.some(hit => !rows.some(row => row.id === hit.id && row.content_hash === hit.content_hash))) {
          throw new Error('Source revisions changed. Refresh the queue and retry transcript search.');
        }
        if (active) setSearchResult({ key: searchKey, rows: data, error: '' });
      }).catch(e => { if (active) setSearchResult({ key: searchKey, rows: [], error: e instanceof Error ? e.message : 'Transcript search failed.' }); });
    }, 200);
    return () => { active = false; clearTimeout(timer); };
  }, [searching, selectedVersion, query, speaker, searchKey]);
  const searchPending = searching && searchResult.key !== searchKey;
  const searchError = searching && searchResult.key === searchKey ? searchResult.error : '';
  const hits = new Map(searchResult.rows.map(r => [r.id, r]));
  // Use current queue status/appeals, attaching matches only to the exact returned revision/hash.
  const candidates = !searching ? rows : searchPending || searchError ? [] : rows.filter(r => hits.get(r.id)?.content_hash === r.content_hash)
    .map(r => ({ ...r, search_matches: hits.get(r.id)!.search_matches, search_total_matches: hits.get(r.id)!.search_total_matches }));
  const scoped = candidates.filter(r => (!language || r.language === language) && (!channel || r.channel === channel)
    && (!group || r.group_id === group) && r.source_id.toLowerCase().includes(search.toLowerCase()));
  const baseFiltered = scoped.filter(r => (!status || statusOf(r) === status) && (!appeals || ((r.pending_appeals ?? 0) > 0) === (appeals === 'pending'))
    && (!critical || ((r.critical_findings?.length ?? 0) > 0) === (critical === 'flagged')));
  const priority = useReviewPriority(baseFiltered, selectedVersion);
  const filtered = priority.rows;
  const groups = [...new Set(rows.map(r => r.group_id))];
  const count = (s: string) => rows.filter(r => statusOf(r) === s).length;
  const working = count('queued') + count('running'); const failed = count('failed') + count('interrupted');
  const selectedVisible = checked.filter(id => filtered.some(r => r.id === id));
  const allSelected = filtered.length > 0 && selectedVisible.length === filtered.length;
  const partiallySelected = selectedVisible.length > 0 && !allSelected;
  useEffect(() => { if (selectAll.current) selectAll.current.indeterminate = partiallySelected; }, [partiallySelected]);
  const selectedRunIds = filtered.filter(row => selectedVisible.includes(row.id) && row.evaluation).map(row => row.evaluation!.id);

  const importResult = async (request: Promise<{ actual_records: number; created: number; unchanged: number; group_id: string }>) => {
    const result = await request;
    notify(`${result.group_id}: ${result.actual_records} records validated. ${result.created} new revisions, ${result.unchanged} unchanged. No malformed records were silently dropped.`);
    setChecked([]); await refresh();
  };

  return <>
    <div className="page-heading"><div><h1>Conversations</h1><p>Import, evaluate, and review the evidence behind each result.</p></div>
      <button className="secondary" disabled={busy} onClick={() => void run(refresh)}>↻ Refresh</button></div>
    <div className="stats-row">
      <div className="stat"><span>Imported conversations</span><strong>{rows.length}</strong><small>Latest source revisions</small></div>
      <div className="stat"><span>Complete</span><strong>{completed}</strong><small>With checklist v{selectedVersion || '—'}</small></div>
      <div className="stat"><span>Needs review</span><strong>{needsReview}</strong><small>Unresolved judgments</small></div>
      <div className="stat"><span>Processing / failed</span><strong>{working}<em> / {failed}</em></strong><small>{count('not_evaluated')} not evaluated</small></div>
    </div>
    <details className="panel import-disclosure" open={rows.length === 0}>
      <summary><span>Import conversations</span><small>API or JSON · preserve existing results</small></summary>
    <section className="import-panel" aria-labelledby="import-title">
      <div><h2 id="import-title">Bring in conversations</h2><p>API and JSON imports use the same validation. Existing evidence stays attached to its source revision.</p></div>
      <div className="import-controls"><label>Dataset group<input aria-label="Dataset group to import" value={groupToImport} onChange={e => setGroupToImport(e.target.value)} placeholder="Organizer-supplied group" /></label>
        <button className="secondary" disabled={busy || !access?.organizer_configured || !groupToImport.trim()} onClick={() => void run(() => importResult(api('/import/organizer', { group_id: groupToImport })))}>{busy ? 'Working…' : 'Import from API'}</button>
        <button className="secondary" disabled={busy} onClick={() => fileRef.current?.click()}>Upload JSON</button>
        <input className="visually-hidden" ref={fileRef} type="file" accept=".json,application/json" aria-label="Organizer JSON upload" onChange={e => {
          const file = e.target.files?.[0]; e.target.value = '';
          if (file) void run(async () => { if (file.size > 25_000_000) throw new Error('JSON upload exceeds 25 MB.'); await importResult(api('/import/json', JSON.parse(await file.text()))); });
        }} />
      </div>
      <div className="import-foot"><span>API: {access?.organizer_configured ? 'configured endpoint' : 'not configured'}</span><span>Provider: {access?.model || 'not configured'}</span>
        <button className="text-button" disabled={busy || !access?.provider_configured || !budget?.ready} onClick={() => void run(async () => {
          const result = await api<{ succeeded: boolean; error?: string }>('/access/check-provider', {});
          if (!result.succeeded) throw new Error(result.error || 'Provider check failed.');
          notify('A real structured provider access check succeeded. This is not a conversation assessment.'); await refresh();
        })}>Test provider access</button>
        {access?.last_provider_check && <span>{access.last_provider_check.succeeded ? 'Last check succeeded' : 'Last check failed'}</span>}
      </div>
    </section></details>
    <section className="panel table-panel" data-density={density}>
      <div className="table-toolbar"><h2>Review queue <span className="queue-count">{filtered.length}</span></h2><div className="inline-actions">
        {!!selectedVisible.length && <><span className="selection-count" role="status">{selectedVisible.length} selected</span><button className="text-button" onClick={() => setChecked([])}>Clear selection</button></>}
        <EvaluationAction ids={selectedVisible} version={selectedVersion} providerReady={!!access?.provider_configured} busy={busy} refreshKey={JSON.stringify(budget)}
          label={`Evaluate selected${selectedVisible.length ? ` (${selectedVisible.length})` : ''} →`}
          start={() => void run(async () => { await evaluate(selectedVisible); setChecked([]); })} />
      </div></div>
      <QueueFilters filters={filters} groups={groups} setField={setField} />
      <QueueViewTools rows={scoped} filters={filters} setField={setField} density={density} onDensity={setDensity} unavailable={searchPending || !!searchError} />
      {priority.controls}
      <details ref={queueTools} className="queue-tools" open={!!filterWarning || filtersChangedElsewhere}>
        <summary><span>Saved views & exports</span><span className="disclosure-hint">{selectedName ? `${selectedName}${filtersDirty ? ' · edited' : ''}` : 'Save or restore filters'}{selectedRunIds.length ? ` · ${selectedRunIds.length} saved runs selected` : ''}</span></summary>
        {controls}
        <QueueExport evaluationIds={selectedRunIds} onError={() => { if (queueTools.current) queueTools.current.open = true; }} />
      </details>
      <CriterionBreakdown rows={filtered} checklistId={selectedVersion} />
      {onOpenPair && <CohortComparison onOpenPair={onOpenPair} />}
      {searchPending && <p role="status" className="search-status">Searching saved transcripts…</p>}
      {searchError && <div role="alert" className="search-status"><p>{searchError}</p><button className="secondary" onClick={() => setRetrySearch(retrySearch + 1)}>Retry transcript search</button></div>}
      {priority.pending && <p role="status" className="search-status">Loading priority view…</p>}
      {priority.error && <div role="alert" className="search-status"><p>Priority view unavailable. {priority.error}</p><button className="secondary" onClick={priority.reset}>Show normal queue</button></div>}
      <div className="table-scroll" role="region" aria-label="Conversation review queue" tabIndex={0}><table><thead><tr>
        <th><input ref={selectAll} type="checkbox" aria-label="Select all visible conversations" aria-checked={partiallySelected ? 'mixed' : allSelected} checked={allSelected} onChange={e => setChecked(e.target.checked ? filtered.map(r => r.id) : [])} /></th>
        <th>Conversation</th><th>Language</th><th>Channel</th><th>Assessment</th><th>Score / 100</th><th></th>
      </tr></thead><tbody>{filtered.map(row => <tr key={row.id}>
        <td><input type="checkbox" aria-label={`Select ${row.source_id}`} checked={checked.includes(row.id)} onChange={e => setChecked(e.target.checked ? [...checked, row.id] : checked.filter(id => id !== row.id))} /></td>
        <td><a className="conversation-link" href={reviewHref(row)}>{row.source_id}</a><small>{row.group_id} · revision {row.revision} · {row.message_count} messages</small>
          {searching && <TranscriptMatches key={JSON.stringify([row.id, row.content_hash, query, speaker])} row={row} query={query} speaker={speaker} />}
        </td>
        <td><span className="language-chip">{row.language}</span></td><td>{row.channel === 'voice call' ? '◉ Call' : '◫ Chat'}<small>{row.channel === 'voice call' && (row.audio_available ? 'Recording link available' : 'Recording unavailable')}</small></td>
        <td><span className={`badge ${statusOf(row)}`}>{label(statusOf(row))}</span>{row.evaluation?.cached_from && <small>Cached original</small>}
          {!!row.pending_appeals && <small>{row.pending_appeals} pending appeal(s)</small>}
          {row.pending_review_targets?.map(target => <small key={target.appeal_id}><a href={`#conversation/${target.conversation_id}?evaluation=${target.evaluation_id}&criterion=${target.criterion_id}`}>Review {target.criterion_name}</a></small>)}
          {row.critical_findings?.map(target => <small key={target.criterion_id}><a className="critical-link" href={`#conversation/${row.id}?evaluation=${target.evaluation_id}&criterion=${target.criterion_id}`}>⚑ {target.criterion_name}</a></small>)}
          {priority.renderReasons(row.id)}
        </td>
        <td className="score-cell">{row.evaluation?.total ?? '—'}</td><td><a className="open-link" href={reviewHref(row)}>Open ↗</a></td>
      </tr>)}</tbody></table></div>
      {!filtered.length && !searchPending && !searchError && !priority.pending && !priority.error && <div className="empty"><strong>{rows.length ? 'No conversations match these filters.' : 'Your review queue is empty.'}</strong><p>{rows.length ? 'Adjust a filter to see more conversations.' : 'Import the organizer dataset or upload its JSON response to get started.'}</p></div>}
      <div className="table-foot">{filtered.length} of {rows.length} conversations <span className="table-scroll-hint">Scroll the table sideways for more columns.</span><span>States refer to the selected checklist version. No score means no resolved result.</span></div>
    </section>
  </>;
}
