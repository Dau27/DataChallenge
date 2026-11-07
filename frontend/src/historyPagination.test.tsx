// @vitest-environment happy-dom
import { afterEach, expect, it, vi } from 'vitest';
import { act, cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import Detail from './Detail';
import type { EvaluationDetail, EvaluationSummary } from './types';
import type { PagedConversation } from './SavedRunPages';
import { useSavedRunPages } from './SavedRunPages';

afterEach(() => { cleanup(); vi.restoreAllMocks(); });
const row = (i: number): EvaluationSummary => ({ id: `RUN_${i}`, conversation_id: 'SOURCE', checklist_id: 1,
  state: 'succeeded', completeness: 'complete', cached_from: null, total: '100.00', error: null,
  created_at: `2026-01-01T00:${String(Math.floor(i / 60)).padStart(2,'0')}:${String(i % 60).padStart(2,'0')}+00:00`, updated_at: '2026-01-02T00:00:00+00:00' });
const navigation = (second = false) => ({ total: 55, start: second ? 26 : 1, end: second ? 50 : 25, limit: 25,
  next_cursor: second ? 'THIRD' : 'SECOND', previous_cursor: second ? 'FIRST' : null, first_cursor: 'FIRST' });
const first: PagedConversation = { id: 'SOURCE', group_id: 'SYNTHETIC', source_id: 'SYNTHETIC_SOURCE', revision: 1,
  content_hash: 'CONTENT_HASH', evaluations: Array.from({ length: 25 }, (_, i) => row(i)), history_page: navigation(),
  snapshot: { language: 'EN', channel: 'agent chat', audio_url: null,
    transcript: [{ id: 'm0001', speaker: 'operator', timestamp: '00:00', text: 'SYNTHETIC transcript.' }] } };
const second = { ...navigation(true), items: Array.from({ length: 25 }, (_, i) => row(i+25)), source: { id: 'SOURCE', content_hash: 'CONTENT_HASH' } };
function assessment(i = 54): EvaluationDetail {
  const judgment = { disposition: 'assessed' as const, value: true, explanation: `SYNTHETIC saved answer ${i}`, na_reason: null,
    review_reason: null, evidence: [{ kind: 'support' as const, start_message_id: 'm0001', end_message_id: 'm0001' }] };
  const result = { results: { custom: judgment } };
  const calculated = { total: '100.00', reason: null, completeness: 'complete', applicable_weight: '1', raw_subtotal: '1', flags: {},
    criteria: [{ criterion_id: 'custom', weight: '1', raw_points: '1', normalized_contribution: '100' }],
    sections: [{ id: 'section', title: 'SYNTHETIC section', total: '100.00', reason: null }] };
  return { ...row(i), original: result, effective: result, original_score: calculated, effective_score: calculated,
    checklist: { id: 1, content_hash: 'RUBRIC', created_at: '', snapshot: { schema_version: 1, name: 'SYNTHETIC', initial_version_label: null,
      source: null, source_notes: [], scoring_policy: {}, sections: [{ id: 'section', title: 'SYNTHETIC section' }],
      criteria: [{ id: 'custom', name: 'SYNTHETIC rule', description: 'SYNTHETIC custom rule.', section_id: 'section', answer_type: 'binary',
        weight: 1, na_allowed: false, na_condition: null, scale: [] }] } },
    metadata: { provider: 'SYNTHETIC', model: 'SYNTHETIC', mode: 'TEST/MOCK', prompt_version: 'SYNTHETIC' }, attempts: [], appeals: [], reviews: [],
    usage: { request_attempts: 0, input_tokens_known: 0, output_tokens_known: 0, usage_complete: false, estimated_cost_usd: null, cost_rate_source: null, latency_ms: 0 } };
}
const props = { id: 'SOURCE', initialEvaluation: 'RUN_54', selectedVersion: 1, busy: false, providerReady: false,
  run: async (action: () => Promise<void>) => { await action(); }, evaluate: async () => {}, onChange: async () => {} };
const json = (value: unknown, status = 200) => new Response(JSON.stringify(value), { status });
function deferred() { let resolve!: (response: Response) => void; const promise = new Promise<Response>(r => { resolve = r; }); return { resolve, promise }; }

it('loads bounded pages, pins deep-linked selections and retains comparison choices across pages', async () => {
  let sourceReads = 0;
  const fetch = vi.spyOn(globalThis, 'fetch').mockImplementation(async value => {
    const url = new URL(String(value), 'http://localhost');
    if (url.pathname === '/api/conversations/SOURCE') { expect(url.searchParams.get('history_limit')).toBe('25'); sourceReads++; return json(first); }
    if (url.pathname === '/api/evaluations/page') { expect(url.searchParams.get('conversation_id')).toBe('SOURCE'); expect(url.searchParams.get('limit')).toBe('25'); return json(second); }
    if (url.pathname.startsWith('/api/evaluations/RUN_')) return json(assessment(Number(url.pathname.split('_').pop())));
    if (url.pathname === '/api/evaluations/compare') return new Promise<Response>(() => {});
    throw new Error(`Unexpected synthetic request ${url.pathname}`);
  });
  const before = structuredClone(first);
  render(<Detail {...props} />);
  await screen.findByText('SYNTHETIC saved answer 54');
  const selector = screen.getByRole('combobox', { name: 'Saved evaluation' });
  expect((selector as HTMLSelectElement).value).toBe('RUN_54');
  expect(within(selector).getAllByRole('option').length).toBeLessThanOrEqual(27);
  await screen.findByText('1–25 of 55 saved runs');
  fireEvent.click(screen.getByRole('button', { name: 'Compare saved runs' }));
  fireEvent.change(screen.getByRole('combobox', { name: 'Baseline saved run' }), { target: { value: 'RUN_0' } });
  fireEvent.click(screen.getByRole('button', { name: 'Older runs' }));
  await screen.findByText('26–50 of 55 saved runs');
  expect((selector as HTMLSelectElement).value).toBe('RUN_54');
  expect(screen.getByText('SYNTHETIC saved answer 54')).toBeDefined();
  expect((screen.getByRole('combobox', { name: 'Baseline saved run' }) as HTMLSelectElement).value).toBe('RUN_0');
  expect(within(selector).getAllByRole('option').length).toBeLessThanOrEqual(27);
  fireEvent.change(selector, { target: { value: 'RUN_30' } });
  await screen.findByText('SYNTHETIC saved answer 30');
  fireEvent.click(screen.getByRole('button', { name: 'Latest runs' }));
  await screen.findByText('1–25 of 55 saved runs');
  expect((selector as HTMLSelectElement).value).toBe('RUN_30');
  expect(sourceReads).toBe(2); expect(fetch.mock.calls.some(c => String(c[0]).includes('cursor=SECOND'))).toBe(true);
  expect(first).toEqual(before);
});

it('shows page failures without clearing the assessment and retries only that page', async () => {
  let pages = 0;
  vi.spyOn(globalThis, 'fetch').mockImplementation(async value => {
    const path = String(value);
    if (path.startsWith('/api/conversations/')) return json(first);
    if (path.startsWith('/api/evaluations/page')) return ++pages === 1 ? json({ detail: 'SYNTHETIC page failed' }, 503) : json(second);
    return json(assessment());
  });
  render(<Detail {...props} />);
  await screen.findByText('SYNTHETIC saved answer 54');
  fireEvent.click(screen.getByRole('button', { name: 'Older runs' }));
  await screen.findByText('SYNTHETIC page failed');
  expect(screen.getByText('SYNTHETIC saved answer 54')).toBeDefined();
  fireEvent.click(screen.getByRole('button', { name: 'Retry saved history' }));
  await screen.findByText('26–50 of 55 saved runs'); expect(pages).toBe(2);
});

it('allows return to latest during a slow page and ignores its late response', async () => {
  const pending = deferred();
  const fetch = vi.spyOn(globalThis, 'fetch').mockImplementation(async value => {
    if (String(value).startsWith('/api/conversations/')) return json(first);
    if (String(value).startsWith('/api/evaluations/page')) return pending.promise;
    return json(assessment());
  });
  render(<Detail {...props} />);
  await screen.findByText('SYNTHETIC saved answer 54');
  fireEvent.click(screen.getByRole('button', { name: 'Older runs' }));
  await waitFor(() => expect(fetch.mock.calls.some(c => String(c[0]).startsWith('/api/evaluations/page'))).toBe(true));
  fireEvent.click(screen.getByRole('button', { name: 'Latest runs' }));
  await screen.findByText('1–25 of 55 saved runs');
  await act(async () => { pending.resolve(json(second)); });
  expect(screen.queryByText('26–50 of 55 saved runs')).toBeNull();
  expect(screen.getByText('SYNTHETIC saved answer 54')).toBeDefined();
});

it('rejects a page from another source revision and keeps the selected run', async () => {
  vi.spyOn(globalThis, 'fetch').mockImplementation(async value => {
    if (String(value).startsWith('/api/conversations/')) return json(first);
    if (String(value).startsWith('/api/evaluations/page')) return json({ ...second, source: { id: 'WRONG', content_hash: 'WRONG' } });
    return json(assessment());
  });
  render(<Detail {...props} />);
  await screen.findByText('SYNTHETIC saved answer 54');
  fireEvent.click(screen.getByRole('button', { name: 'Older runs' }));
  await screen.findByText('Saved history belongs to another source revision. Return to the latest runs.');
  expect((screen.getByRole('combobox', { name: 'Saved evaluation' }) as HTMLSelectElement).value).toBe('RUN_54');
});

it('updates a visible older-page header after the selected assessment refreshes', async () => {
  const failed = { ...assessment(30), state: 'failed' as const, total: null };
  const oldPage = { ...second, items: second.items.map(run => run.id === failed.id ? failed : run) };
  vi.spyOn(globalThis, 'fetch').mockResolvedValue(json(oldPage));
  function View({ selected }: { selected: EvaluationDetail }) {
    const history = useSavedRunPages(first, selected, async () => {}, false);
    return <>{history.controls}<output aria-label="Run status">{history.runs.find(run => run.id === selected.id)?.state}</output></>;
  }
  const { rerender } = render(<View selected={failed} />);
  fireEvent.click(screen.getByRole('button', { name: 'Older runs' }));
  await screen.findByText('failed');
  rerender(<View selected={{ ...assessment(30), updated_at: '2026-01-04T00:00:00+00:00' }} />);
  expect(screen.getByLabelText('Run status').textContent).toBe('succeeded');
});
