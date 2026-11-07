import { useRef, useState } from 'react';
import { api } from './api';
import type { Access, Conversation } from './types';
import { label, statusOf } from './helpers';
import type { Run } from './App';

export default function Conversations({ rows, access, selectedVersion, completed, needsReview, busy, run, evaluate, refresh, notify }: {
  rows: Conversation[]; access: Access | null; selectedVersion: number; completed: number; needsReview: number;
  busy: boolean; run: Run; evaluate: (ids: string[]) => Promise<void>; refresh: () => Promise<void>; notify: (message: string) => void;
}) {
  const [language, setLanguage] = useState(''); const [channel, setChannel] = useState('');
  const [status, setStatus] = useState(''); const [group, setGroup] = useState('');
  const [search, setSearch] = useState(''); const [groupToImport, setGroupToImport] = useState('DEV');
  const [checked, setChecked] = useState<string[]>([]); const fileRef = useRef<HTMLInputElement>(null);
  const filtered = rows.filter(r => (!language || r.language === language) && (!channel || r.channel === channel) && (!status || statusOf(r) === status)
    && (!group || r.group_id === group) && r.source_id.toLowerCase().includes(search.toLowerCase()));
  const groups = [...new Set(rows.map(r => r.group_id))];
  const count = (s: string) => rows.filter(r => statusOf(r) === s).length;
  const working = count('queued') + count('running'); const failed = count('failed') + count('interrupted');
  const selectedVisible = checked.filter(id => filtered.some(r => r.id === id));

  const importResult = async (request: Promise<{ actual_records: number; created: number; unchanged: number; group_id: string }>) => {
    const result = await request;
    notify(`${result.group_id}: ${result.actual_records} records validated. ${result.created} new revisions, ${result.unchanged} unchanged. No malformed records were silently dropped.`);
    setChecked([]); await refresh();
  };

  return <>
    <div className="page-heading"><div><div className="eyebrow">CONVERSATION QUALITY</div><h1>Conversations</h1><p>Import, evaluate, and review the evidence behind each result.</p></div>
      <button className="secondary" disabled={busy} onClick={() => void run(refresh)}>↻ Refresh</button></div>
    <div className="stats-row">
      <div className="stat"><span>Imported conversations</span><strong>{rows.length}</strong><small>Latest source revisions</small></div>
      <div className="stat"><span>Complete</span><strong>{completed}</strong><small>With checklist v{selectedVersion || '—'}</small></div>
      <div className="stat"><span>Needs review</span><strong>{needsReview}</strong><small>Unresolved judgments</small></div>
      <div className="stat"><span>Processing / failed</span><strong>{working}<em> / {failed}</em></strong><small>{count('not_evaluated')} not evaluated</small></div>
    </div>
    <section className="panel import-panel" aria-labelledby="import-title">
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
        <button className="text-button" disabled={busy || !access?.provider_configured} onClick={() => void run(async () => {
          const result = await api<{ succeeded: boolean; error?: string }>('/access/check-provider', {});
          if (!result.succeeded) throw new Error(result.error || 'Provider check failed.');
          notify('A real structured provider access check succeeded. This is not a conversation assessment.'); await refresh();
        })}>Test provider access</button>
        {access?.last_provider_check && <span>{access.last_provider_check.succeeded ? 'Last check succeeded' : 'Last check failed'}</span>}
      </div>
    </section>
    <section className="panel table-panel">
      <div className="table-toolbar"><h2>Review queue <span className="muted">{filtered.length}</span></h2><div className="inline-actions">
        <button className="primary" disabled={busy || !access?.provider_configured || !selectedVisible.length || !selectedVersion} onClick={() => void run(async () => { await evaluate(selectedVisible); setChecked([]); })}>Evaluate selected{selectedVisible.length ? ` (${selectedVisible.length})` : ''} →</button>
      </div></div>
      <div className="filters"><input aria-label="Search conversation ID" placeholder="Search conversation ID…" value={search} onChange={e => setSearch(e.target.value)} />
        <select aria-label="Dataset filter" value={group} onChange={e => setGroup(e.target.value)}><option value="">All datasets</option>{groups.map(g => <option key={g}>{g}</option>)}</select>
        <select aria-label="Language filter" value={language} onChange={e => setLanguage(e.target.value)}><option value="">All languages</option>{['RU', 'KZ', 'EN'].map(l => <option key={l}>{l}</option>)}</select>
        <select aria-label="Channel filter" value={channel} onChange={e => setChannel(e.target.value)}><option value="">All channels</option><option>agent chat</option><option>voice call</option></select>
        <select aria-label="Status filter" value={status} onChange={e => setStatus(e.target.value)}><option value="">All states</option>{['not_evaluated', 'queued', 'running', 'complete', 'needs_review', 'failed', 'interrupted'].map(s => <option value={s} key={s}>{label(s)}</option>)}</select>
      </div>
      <div className="table-scroll"><table><thead><tr>
        <th><input type="checkbox" aria-label="Select all visible conversations" checked={filtered.length > 0 && selectedVisible.length === filtered.length} onChange={e => setChecked(e.target.checked ? filtered.map(r => r.id) : [])} /></th>
        <th>Conversation</th><th>Language</th><th>Channel</th><th>Assessment</th><th>Score / 100</th><th></th>
      </tr></thead><tbody>{filtered.map(row => <tr key={row.id}>
        <td><input type="checkbox" aria-label={`Select ${row.source_id}`} checked={checked.includes(row.id)} onChange={e => setChecked(e.target.checked ? [...checked, row.id] : checked.filter(id => id !== row.id))} /></td>
        <td><a className="conversation-link" href={`#conversation/${row.id}`}>{row.source_id}</a><small>{row.group_id} · revision {row.revision} · {row.message_count} messages</small></td>
        <td><span className="language-chip">{row.language}</span></td><td>{row.channel === 'voice call' ? '◉ Call' : '◫ Chat'}<small>{row.channel === 'voice call' && (row.audio_available ? 'Recording link available' : 'Recording unavailable')}</small></td>
        <td><span className={`badge ${statusOf(row)}`}>{label(statusOf(row))}</span>{row.evaluation?.cached_from && <small>Cached original</small>}</td>
        <td className="score-cell">{row.evaluation?.total ?? '—'}</td><td><a className="open-link" href={`#conversation/${row.id}`}>Open ↗</a></td>
      </tr>)}</tbody></table></div>
      {!filtered.length && <div className="empty"><strong>{rows.length ? 'No conversations match these filters.' : 'Your review queue is empty.'}</strong><p>{rows.length ? 'Adjust a filter to see more conversations.' : 'Import the organizer dataset or upload its JSON response to get started.'}</p></div>}
      <div className="table-foot">{filtered.length} of {rows.length} conversations <span>States refer to the selected checklist version. No score means no resolved result.</span></div>
    </section>
  </>;
}
