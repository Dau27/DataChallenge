import { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react';
import { api } from './api';
import type { Access, BudgetStatus, ChecklistVersion, Conversation, EvaluationSummary } from './types';
import { BudgetSummary } from './Budget';
import { statusOf } from './helpers';
import Conversations from './Conversations';
import ChecklistEditor from './ChecklistEditor';
import Detail from './Detail';
import { useLatestResource } from './useLatestResource';

export type Run = (operation: () => Promise<void>) => Promise<void>;

export default function App() {
  const [route, setRoute] = useState(location.hash || '#conversations');
  const currentRoute = useRef(route); const queueScroll = useRef(0);
  const pairNavigation = useRef(0);
  const [versions, setVersions] = useState<ChecklistVersion[]>([]);
  const [selectedVersion, setSelectedVersion] = useState(() => {
    try { const saved = Number(sessionStorage.getItem('cqa-selected-version')); return Number.isInteger(saved) && saved > 0 ? saved : 0; }
    catch { return 0; }
  });
  const [access, setAccess] = useState<Access | null>(null);
  const [budget, setBudget] = useState<BudgetStatus | null>(null);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const onHash = () => {
      pairNavigation.current += 1;
      if (!currentRoute.current.startsWith('#conversation/') && !currentRoute.current.startsWith('#checklist')) queueScroll.current = window.scrollY;
      currentRoute.current = location.hash || '#conversations';
      setRoute(currentRoute.current);
    };
    addEventListener('hashchange', onHash);
    return () => removeEventListener('hashchange', onHash);
  }, []);
  const showingQueue = !route.startsWith('#conversation/') && !route.startsWith('#checklist');
  useLayoutEffect(() => {
    document.getElementById('review-content')?.focus({ preventScroll: true });
    window.scrollTo({ top: showingQueue ? queueScroll.current : 0 });
  }, [route, showingQueue]);

  const queue = useLatestResource(String(selectedVersion), async () => {
    const [list, rubric, configuration, spending] = await Promise.all([
      api<Conversation[]>(`/conversations${selectedVersion ? `?checklist_id=${selectedVersion}` : ''}`),
      api<ChecklistVersion[]>('/checklists'), api<Access>('/access'), api<BudgetStatus>('/budget'),
    ]);
    if (selectedVersion && list.some(row => row.evaluation && row.evaluation.checklist_id !== selectedVersion)) {
      throw new Error('Queue results do not match the selected checklist version.');
    }
    return { list, rubric, configuration, spending };
  }, true);
  const rows = queue.value?.list ?? [];
  const refresh = useCallback(async () => { await queue.reload(); }, [queue.reload]);
  useEffect(() => {
    if (!queue.value) return;
    const { rubric, configuration, spending } = queue.value;
    setVersions(rubric); setAccess(configuration);
    setBudget(spending);
    if (rubric.length && !rubric.some(v => v.id === selectedVersion)) setSelectedVersion(rubric[rubric.length - 1].id);
  }, [queue.value, selectedVersion]);
  useEffect(() => { if (selectedVersion) { try { sessionStorage.setItem('cqa-selected-version', String(selectedVersion)); } catch { /* Session preferences are optional. */ } } }, [selectedVersion]);

  const run: Run = async operation => {
    setBusy(true); setError('');
    try { await operation(); } catch (e) { setError(e instanceof Error ? e.message : 'Operation failed.'); }
    finally { setBusy(false); }
  };

  const working = rows.some(r => r.evaluation && ['queued', 'running'].includes(r.evaluation.state));
  useEffect(() => {
    if (!working) return;
    if (queue.pending) return;
    const timer = setTimeout(() => { void refresh().catch(() => {}); }, 2500);
    return () => clearTimeout(timer);
  }, [working, refresh, queue.pending]);

  const selected = versions.find(v => v.id === selectedVersion);
  const detailId = route.startsWith('#conversation/') ? route.slice('#conversation/'.length).split('?')[0] : null;
  const initialEvaluation = new URLSearchParams(route.split('?')[1]).get('evaluation');
  const initialCriterion = new URLSearchParams(route.split('?')[1]).get('criterion');
  const initialMessage = new URLSearchParams(route.split('?')[1]).get('message');
  const initialBaseline = new URLSearchParams(route.split('?')[1]).get('baseline');
  const completed = rows.filter(r => statusOf(r) === 'complete').length;
  const needsReview = rows.filter(r => statusOf(r) === 'needs_review').length;

  const evaluate = async (ids: string[]) => {
    const result = await api<{ evaluation_ids: string[] }>('/evaluations', { conversation_ids: ids, checklist_id: selectedVersion });
    setNotice(`Started ${result.evaluation_ids.length} evaluation(s) with checklist v${selectedVersion}. Compatible original assessments may be reused and labeled cached.`);
    await refresh();
    if (ids.length === 1) location.hash = `conversation/${ids[0]}?evaluation=${result.evaluation_ids[0]}`;
  };

  const openCohortPair = (leftId: string, rightId: string) => {
    const token = ++pairNavigation.current;
    const active = () => pairNavigation.current === token;
    void run(async () => {
      let pair: EvaluationSummary[];
      try {
        pair = await Promise.all([leftId, rightId].map(id => api<EvaluationSummary>(`/evaluations/${encodeURIComponent(id)}`)));
      } catch (error) { if (active()) throw error; return; }
      if (!active()) return;
      const [left, right] = pair;
      if (!left || !right || left.id !== leftId || right.id !== rightId || typeof left.conversation_id !== 'string' || !left.conversation_id || left.conversation_id !== right.conversation_id) {
        throw new Error('The selected cohort runs do not belong to the same exact source revision. Refresh the cohorts.');
      }
      const params = new URLSearchParams({ evaluation: rightId, baseline: leftId });
      location.hash = `conversation/${right.conversation_id}?${params}`;
    });
  };

  return <div className="app-shell">
    <a className="skip-link" href="#review-content" onClick={event => { event.preventDefault(); document.getElementById('review-content')?.focus(); }}>Skip to content</a>
    <aside className="sidebar">
      <a className="brand" href="#conversations"><span className="brand-mark">CQ</span><span>CQA<span className="brand-caption">REVIEW WORKSPACE</span></span></a>
      <div className="nav-caption">WORKSPACE</div>
      <nav aria-label="Main navigation">
        <a href="#conversations" aria-current={!route.startsWith('#checklist') ? 'page' : undefined} className={!route.startsWith('#checklist') ? 'active' : ''}><span aria-hidden="true">◫</span> Conversations <span className="nav-count">{rows.length}</span></a>
        <a href="#checklists" aria-current={route.startsWith('#checklist') ? 'page' : undefined} className={route.startsWith('#checklist') ? 'active' : ''}><span aria-hidden="true">☷</span> Checklist versions</a>
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
      <main id="review-content" tabIndex={-1}>
        <BudgetSummary budget={budget} />
        {(error || queue.error) && <div className="banner error" role="alert"><div><strong>Could not complete the action</strong><p className="pre-line">{error || queue.error}</p></div>
          {error ? <button className="text-button" onClick={() => setError('')} aria-label="Dismiss error">×</button>
            : <button className="secondary" onClick={() => void refresh().catch(() => {})}>Retry refresh</button>}</div>}
        {notice && <div className="banner success" role="status"><span>{notice}</span><button className="text-button" onClick={() => setNotice('')} aria-label="Dismiss notification">×</button></div>}
        {access && (!access.provider_configured || access.last_provider_check?.succeeded === false) && <details className="banner warning provider-disclosure"><summary><strong>Live evaluation needs provider access</strong><span>Saved reviews remain available</span></summary><p>{access.provider_status}. {access.provider_configured ? 'Resolve the provider access or billing issue, then test access again.' : 'Update the local .env configuration and restart the backend.'} Imported transcripts remain available.</p></details>}
        <div hidden={!showingQueue} className="queue-workspace">
          {!queue.value || !selected ? <div className="empty" role="status">{queue.error ? <><p>Conversations could not be loaded for this checklist.</p><button className="secondary" onClick={() => void refresh().catch(() => {})}>Retry conversations</button></> : 'Loading conversations…'}</div>
            : <Conversations key={selected.id} rows={rows} access={access} budget={budget} selectedVersion={selectedVersion} completed={completed} needsReview={needsReview} busy={busy} run={run} evaluate={evaluate} refresh={refresh} notify={setNotice} onOpenPair={openCohortPair} />}
        </div>
        {route.startsWith('#checklist') && selected
          ? <ChecklistEditor key={selected.id} version={selected} versions={versions} busy={busy} run={run} onSave={async id => { await refresh(); setSelectedVersion(id); setNotice(`Saved immutable checklist v${id}. It is selected for future evaluations. Existing assessments retain their original version.`); }} />
          : detailId
            ? <Detail key={detailId} id={detailId} initialEvaluation={initialEvaluation} initialBaseline={initialBaseline} initialCriterion={initialCriterion} initialMessage={initialMessage} selectedVersion={selectedVersion} busy={busy} run={run} providerReady={!!access?.provider_configured} budget={budget} evaluate={evaluate} onChange={refresh} />
            : null}
      </main>
      <footer>CQA prototype <span>Persistent local review · Source transcript evidence · Versioned checklists</span></footer>
    </div>
  </div>;
}
