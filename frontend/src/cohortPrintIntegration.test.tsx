// @vitest-environment happy-dom
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import App from './App';
import Detail from './Detail';
import { syntheticPrintPacket } from './printEvaluationFixtures';
import type { EvaluationDetail, EvaluationSummary } from './types';
import type { PagedConversation } from './SavedRunPages';

// The owned cohort component/guards have their own real response tests. This
// seam drives the coordinator's navigation callback; Detail/print/comparison run.
vi.mock('./CohortComparison', () => ({ default: ({ onOpenPair }: { onOpenPair: (left: string, right: string) => void }) =>
  <button onClick={() => onOpenPair('LEFT', 'RIGHT')}>SYNTHETIC open cohort pair</button> }));

const json = (value: unknown, status = 200) => new Response(JSON.stringify(value), { status });
const packet = (id = 'RIGHT', updated = '2026-11-08T00:00:00+00:00', excerpts = false) => syntheticPrintPacket(id, updated, excerpts);
const detail = (id: string) => packet(id).evaluation as unknown as EvaluationDetail;
const summary = (id: string): EvaluationSummary => {
  const { conversation_id, checklist_id, state, completeness, cached_from, total, error, created_at, updated_at } = detail(id);
  return { id, conversation_id, checklist_id, state, completeness, cached_from, total, error, created_at, updated_at };
};
const source: PagedConversation = { id: packet().source.id, group_id: 'SYNTHETIC', source_id: 'SYNTHETIC_CASE', revision: 1,
  content_hash: packet().source.content_hash, snapshot: { language: 'KZ', channel: 'agent chat', audio_url: null,
    transcript: [{ id: 'm0001', speaker: 'operator', timestamp: '00:01', text: 'SYNTHETIC transcript.' },
      { id: 'm0002', speaker: 'client', timestamp: '00:02', text: 'SYNTHETIC reply.' }] },
  evaluations: Array.from({ length: 25 }, (_, i) => summary(`RECENT_${i}`)),
  history_page: { total: 55, start: 1, end: 25, limit: 25, next_cursor: 'NEXT', previous_cursor: null, first_cursor: 'FIRST' } };
const comparison = (left = 'LEFT', right = 'RIGHT') => {
  const side = (id: string) => ({ id, basis: 'effective', state: 'succeeded', completeness: 'needs_review',
    created_at: detail(id).created_at, updated_at: detail(id).updated_at, cached_from: null, metadata: {},
    checklist: detail(id).checklist, score: detail(id).effective_score, usage: detail(id).usage, review_count: 1 });
  return { source: { id: source.id }, left: side(left), right: side(right), total_comparable: false,
    total_difference: null, notice: 'SYNTHETIC exact saved pair.', criteria: [] };
};
const props = { id: source.id, initialEvaluation: 'RIGHT', initialBaseline: 'LEFT', selectedVersion: 8, busy: false, providerReady: false,
  run: async (operation: () => Promise<void>) => { await operation(); }, evaluate: async () => {}, onChange: async () => {} };

function mockApi(change?: (url: URL) => Response | Promise<Response> | undefined) {
  return vi.spyOn(globalThis, 'fetch').mockImplementation(async (input, init) => {
    const url = new URL(String(input), 'http://localhost');
    const overridden = change?.(url); if (overridden) return overridden;
    if (url.pathname.startsWith('/api/conversations/')) return json(source);
    if (url.pathname === '/api/conversations') return json([{ ...source, language: 'KZ', channel: 'agent chat',
      message_count: 2, audio_available: false, evaluation: summary('RIGHT') }]);
    if (url.pathname === '/api/checklists') return json([detail('RIGHT').checklist]);
    if (url.pathname === '/api/access') return json({ provider_configured: false, organizer_configured: false, provider_status: 'SYNTHETIC offline' });
    if (url.pathname === '/api/budget') return json({ limit_usd: '0', accounted_usd: '0', reserved_usd: '0', available_usd: '0', ready: false });
    if (url.pathname === '/api/evaluations/compare') return json(comparison(url.searchParams.get('left_id')!, url.searchParams.get('right_id')!));
    const match = url.pathname.match(/^\/api\/evaluations\/([^/]+)(\/export)?$/);
    if (match) return json(match[2] ? packet(match[1], undefined, url.searchParams.get('include_excerpts') === 'true') : detail(match[1]));
    throw new Error(`Unexpected synthetic request ${init?.method ?? 'GET'} ${url.pathname}`);
  });
}

beforeEach(() => { localStorage.clear(); sessionStorage.clear(); history.replaceState({}, '', '#conversations');
  vi.spyOn(window, 'scrollTo').mockImplementation(() => {}); });
afterEach(() => { cleanup(); vi.restoreAllMocks(); localStorage.clear(); sessionStorage.clear(); });

it('opens both exact cohort IDs outside the first history page without evaluating or paging through other runs', async () => {
  const fetch = mockApi();
  render(<App />);
  fireEvent.click(await screen.findByRole('button', { name: 'SYNTHETIC open cohort pair' }));
  await waitFor(() => expect(location.hash).toContain('baseline=LEFT'));
  const left = await screen.findByLabelText('Baseline saved run') as HTMLSelectElement;
  await waitFor(() => expect(left.value).toBe('LEFT'));
  expect((screen.getByLabelText('Comparison saved run') as HTMLSelectElement).value).toBe('RIGHT');
  expect((screen.getByLabelText('Saved evaluation') as HTMLSelectElement).value).toBe('RIGHT');
  expect(document.querySelector<HTMLDetailsElement>('.assessment-tools')!.open).toBe(true);
  await screen.findByText(/SYNTHETIC exact saved pair\./);
  expect(fetch.mock.calls.every(([url, init]) => !String(url).includes('/evaluations/page') && !init?.body)).toBe(true);
});

it('refuses a pair belonging to different source revisions', async () => {
  mockApi(url => url.pathname === '/api/evaluations/LEFT' ? json({ ...detail('LEFT'), conversation_id: 'OTHER_REVISION' }) : undefined);
  render(<App />);
  fireEvent.click(await screen.findByRole('button', { name: 'SYNTHETIC open cohort pair' }));
  await screen.findByText(/do not belong to the same exact source revision/);
  expect(location.hash).toBe('#conversations');
});

it('ignores delayed pair navigation after leaving the queue', async () => {
  let complete!: (response: Response) => void;
  mockApi(url => url.pathname === '/api/evaluations/LEFT' ? new Promise<Response>(resolve => { complete = resolve; }) : undefined);
  render(<App />);
  fireEvent.click(await screen.findByRole('button', { name: 'SYNTHETIC open cohort pair' }));
  await waitFor(() => expect(complete).toBeDefined());
  await act(async () => { location.hash = '#checklists'; window.dispatchEvent(new HashChangeEvent('hashchange')); });
  await act(async () => { complete(json(detail('LEFT'))); });
  expect(location.hash).toBe('#checklists');
});

it('preserves an unavailable explicit baseline rather than substituting a recent default on reopening', async () => {
  mockApi(url => url.pathname === '/api/evaluations/LEFT' ? json({ detail: 'SYNTHETIC missing baseline' }, 404) : undefined);
  render(<Detail {...props} />);
  await screen.findByText('SYNTHETIC missing baseline');
  const toggle = screen.getByRole('button', { name: 'Compare saved runs' });
  fireEvent.click(toggle); fireEvent.click(toggle);
  expect((screen.getByLabelText('Baseline saved run') as HTMLSelectElement).value).toBe('LEFT');
  expect(screen.getByText(/selected saved run is no longer available/)).toBeDefined();
  expect(screen.getByRole('button', { name: 'Retry cohort baseline' })).toBeDefined();
});

it('mounts the real saved print tool for the selected assessment and discards its preview when selection changes', async () => {
  const fetch = mockApi();
  render(<Detail {...props} />);
  fireEvent.click(await screen.findByRole('button', { name: 'Preview saved report' }));
  await screen.findByTitle('Saved evaluation report preview');
  const frame = screen.getByTitle('Saved evaluation report preview') as HTMLIFrameElement;
  expect(frame.srcdoc).toContain('RIGHT');
  fireEvent.change(screen.getByLabelText('Saved evaluation'), { target: { value: 'RECENT_0' } });
  await waitFor(() => expect((screen.getByLabelText('Saved evaluation') as HTMLSelectElement).value).toBe('RECENT_0'));
  expect(screen.queryByTitle('Saved evaluation report preview')).toBeNull();
  fireEvent.click(await screen.findByRole('button', { name: 'Preview saved report' }));
  await screen.findByTitle('Saved evaluation report preview');
  expect((screen.getByTitle('Saved evaluation report preview') as HTMLIFrameElement).srcdoc).toContain('RECENT_0');
  expect(fetch.mock.calls.some(([url]) => String(url).includes('/RIGHT/export?format=json&include_excerpts=false'))).toBe(true);
  expect(fetch.mock.calls.every(([, init]) => !init?.body)).toBe(true);
});
