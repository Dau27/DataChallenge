import { useRef, useState } from 'react';
import { api } from './api';
import type { ConversationDetail, EvaluationDetail, EvaluationSummary } from './types';
import { useLatestResource } from './useLatestResource';
import './historyPagination.css';

export type HistoryNavigation = { total: number; start: number; end: number; limit: number;
  next_cursor: string | null; previous_cursor: string | null; first_cursor: string | null };
export type PagedConversation = ConversationDetail & { history_page?: HistoryNavigation };
type HistoryPage = HistoryNavigation & { items: EvaluationSummary[]; source: { id: string; content_hash: string } };

export function useSavedRunPages(conversation: PagedConversation | null, selected: EvaluationDetail | null,
  refreshFirst: () => Promise<unknown>, sourcePending: boolean) {
  const id = conversation?.id ?? '';
  const [position, setPosition] = useState({ id, cursor: '' });
  const cursor = position.id === id ? position.cursor : '';
  const page = useLatestResource(JSON.stringify([id, conversation?.content_hash, cursor]), async () => {
    if (!conversation || !cursor) return null;
    const params = new URLSearchParams({ conversation_id: id, limit: '25', cursor });
    const result = await api<HistoryPage>(`/evaluations/page?${params}`);
    if (!result.source || result.source.id !== id || result.source.content_hash !== conversation.content_hash || result.limit !== 25 || result.items.length > 25 ||
        result.items.some(run => run.conversation_id !== id)) throw new Error('Saved history belongs to another source revision. Return to the latest runs.');
    return result;
  });
  const pending = cursor ? page.pending : sourcePending;
  const error = cursor ? page.error : '';
  const navigation = cursor ? page.value : conversation?.history_page;
  const runs = pending || error ? [] : cursor ? page.value?.items ?? [] : conversation?.evaluations ?? [];
  const known = useRef<{ id: string; runs: Map<string, EvaluationSummary> }>({ id, runs: new Map() });
  if (known.current.id !== id) known.current = { id, runs: new Map() };
  for (const run of [...(conversation?.evaluations ?? []), ...runs, ...(selected ? [selected] : [])]) {
    const previous = known.current.runs.get(run.id);
    if (!previous || run.updated_at >= previous.updated_at) {
      // Keep only the public header, never copies of full judgments/history.
      const { id, conversation_id, checklist_id, state, completeness, cached_from, total, error, created_at, updated_at } = run;
      known.current.runs.set(id, { id, conversation_id, checklist_id, state, completeness, cached_from, total, error, created_at, updated_at });
    }
  }
  const controls = conversation?.history_page && <div className="history-pagination" aria-label="Saved run history pages">
    <small role="status">{pending ? 'Loading saved runs…' : error ? 'Saved history unavailable.'
      : `${navigation?.start ?? 0}–${navigation?.end ?? 0} of ${navigation?.total ?? 0} saved runs`}</small>
    <div className="inline-actions">
      <button className="secondary" disabled={pending || !navigation?.previous_cursor} onClick={() => setPosition({ id, cursor: navigation!.previous_cursor! })}>Newer runs</button>
      <button className="secondary" disabled={pending || !navigation?.next_cursor} onClick={() => setPosition({ id, cursor: navigation!.next_cursor! })}>Older runs</button>
      <button className="secondary" disabled={sourcePending && !cursor} onClick={() => {
        setPosition({ id, cursor: '' }); void refreshFirst().catch(() => {});
      }}>Latest runs</button>
    </div>
    {error && <div role="alert"><p>{error}</p><button className="secondary" onClick={() => void page.reload().catch(() => {})}>Retry saved history</button></div>}
    <small>Your selected assessment stays open while you browse. Browsed runs are also available for comparison. Latest runs includes new results.</small>
  </div>;
  return { runs: runs.map(run => known.current.runs.get(run.id) ?? run), knownRuns: [...known.current.runs.values()], controls, pending };
}
