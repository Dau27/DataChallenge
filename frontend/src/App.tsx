import { useCallback, useEffect, useState } from 'react';
import { api } from './api';
import type { Access, BudgetStatus, ChecklistVersion, Conversation } from './types';
import { BudgetSummary } from './Budget';
import { statusOf } from './helpers';
import Conversations from './Conversations';
import ChecklistEditor from './ChecklistEditor';
import Detail from './Detail';

export type Run = (operation: () => Promise<void>) => Promise<void>;

export default function App() {
  const [route, setRoute] = useState(location.hash || '#conversations');
  const [versions, setVersions] = useState<ChecklistVersion[]>([]);
  const [selectedVersion, setSelectedVersion] = useState(() => {
    try { const saved = Number(sessionStorage.getItem('cqa-selected-version')); return Number.isInteger(saved) && saved > 0 ? saved : 0; }
    catch { return 0; }
  });
  const [rows, setRows] = useState<Conversation[]>([]);
  const [access, setAccess] = useState<Access | null>(null);
  const [budget, setBudget] = useState<BudgetStatus | null>(null);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const onHash = () => setRoute(location.hash || '#conversations');
    addEventListener('hashchange', onHash);
    return () => removeEventListener('hashchange', onHash);
  }, []);

  const refresh = useCallback(async () => {
    const [list, rubric, configuration, spending] = await Promise.all([
      api<Conversation[]>(`/conversations${selectedVersion ? `?checklist_id=${selectedVersion}` : ''}`),
      api<ChecklistVersion[]>('/checklists'), api<Access>('/access'), api<BudgetStatus>('/budget'),
    ]);
    setRows(list); setVersions(rubric); setAccess(configuration);
    setBudget(spending);
    if (rubric.length && !rubric.some(v => v.id === selectedVersion)) setSelectedVersion(rubric[rubric.length - 1].id);
  }, [selectedVersion]);
  useEffect(() => { if (selectedVersion) { try { sessionStorage.setItem('cqa-selected-version', String(selectedVersion)); } catch { /* Session preferences are optional. */ } } }, [selectedVersion]);

  const run: Run = async operation => {
    setBusy(true); setError('');
    try { await operation(); } catch (e) { setError(e instanceof Error ? e.message : 'Operation failed.'); }
    finally { setBusy(false); }
  };

  useEffect(() => { void refresh().catch(e => setError(e.message)); }, [refresh]);
  const working = rows.some(r => r.evaluation && ['queued', 'running'].includes(r.evaluation.state));
  useEffect(() => {
    if (!working) return;
    const interval = setInterval(() => { void refresh().catch(e => setError(e.message)); }, 2500);
    return () => clearInterval(interval);
  }, [working, refresh]);

  const selected = versions.find(v => v.id === selectedVersion);
  const detailId = route.startsWith('#conversation/') ? route.slice('#conversation/'.length).split('?')[0] : null;
  const initialEvaluation = new URLSearchParams(route.split('?')[1]).get('evaluation');
  const initialCriterion = new URLSearchParams(route.split('?')[1]).get('criterion');
  const initialMessage = new URLSearchParams(route.split('?')[1]).get('message');
  const completed = rows.filter(r => statusOf(r) === 'complete').length;
  const needsReview = rows.filter(r => statusOf(r) === 'needs_review').length;

  const evaluate = async (ids: string[]) => {
    const result = await api<{ evaluation_ids: string[] }>('/evaluations', { conversation_ids: ids, checklist_id: selectedVersion });
    setNotice(`Started ${result.evaluation_ids.length} evaluation(s) with checklist v${selectedVersion}. Compatible original assessments may be reused and labeled cached.`);
    await refresh();
    if (ids.length === 1) location.hash = `conversation/${ids[0]}?evaluation=${result.evaluation_ids[0]}`;
  };

  return <div className="app-shell">
    <aside className="sidebar">
      <a className="brand" href="#conversations"><span className="brand-mark">CQ</span><span>CQA<span className="brand-caption">REVIEW WORKSPACE</span></span></a>
      <div className="nav-caption">WORKSPACE</div>
      <nav aria-label="Main navigation">
        <a href="#conversations" className={!route.startsWith('#checklist') ? 'active' : ''}><span>◫</span> Conversations <span className="nav-count">{rows.length}</span></a>
        <a href="#checklists" className={route.startsWith('#checklist') ? 'active' : ''}><span>☷</span> Checklist versions</a>
      </nav>
      <div className="sidebar-note"><span className="small-caps">REVIEW WITH CONTEXT</span><p>Every judgment links back to the conversation. Every revision keeps its history.</p></div>
      <div className="local-label"><span className="dot" /> Local workspace <small>Anonymous demo actions</small></div>
    </aside>
    <div className="workspace">
      <header className="topbar"><span className="breadcrumb">Workspace <span>/</span> {detailId ? 'Conversation review' : route.startsWith('#checklist') ? 'Checklist editor' : 'Conversations'}</span>
        <label className="version-picker">Evaluate with <select aria-label="Selected checklist version" value={selectedVersion} onChange={e => setSelectedVersion(Number(e.target.value))} disabled={busy}>
          {!versions.length && <option value={0}>Loading…</option>}
          {versions.map(v => <option key={v.id} value={v.id}>v{v.id} · {v.snapshot.name}</option>)}
        </select></label>
      </header>
      <main>
        <BudgetSummary budget={budget} />
        {error && <div className="banner error" role="alert"><div><strong>Could not complete the action</strong><p className="pre-line">{error}</p></div><button className="text-button" onClick={() => setError('')} aria-label="Dismiss error">×</button></div>}
        {notice && <div className="banner success" role="status"><span>{notice}</span><button className="text-button" onClick={() => setNotice('')} aria-label="Dismiss notification">×</button></div>}
        {access && (!access.provider_configured || access.last_provider_check?.succeeded === false) && <div className="banner warning"><div><strong>Live evaluation needs provider access</strong><p>{access.provider_status}. {access.provider_configured ? 'Resolve the provider access or billing issue, then test access again.' : 'Update the local .env configuration and restart the backend.'} Imported transcripts remain available.</p></div></div>}
        {route.startsWith('#checklist') && selected
          ? <ChecklistEditor key={selected.id} version={selected} versions={versions} busy={busy} run={run} onSave={async id => { await refresh(); setSelectedVersion(id); setNotice(`Saved immutable checklist v${id}. It is selected for future evaluations. Existing assessments retain their original version.`); }} />
          : detailId
            ? <Detail key={detailId} id={detailId} initialEvaluation={initialEvaluation} initialCriterion={initialCriterion} initialMessage={initialMessage} selectedVersion={selectedVersion} busy={busy} run={run} providerReady={!!access?.provider_configured} budget={budget} evaluate={evaluate} onChange={refresh} />
            : <Conversations rows={rows} access={access} budget={budget} selectedVersion={selectedVersion} completed={completed} needsReview={needsReview} busy={busy} run={run} evaluate={evaluate} refresh={refresh} notify={setNotice} />}
      </main>
      <footer>CQA prototype <span>Persistent local review · Source transcript evidence · Versioned checklists</span></footer>
    </div>
  </div>;
}
