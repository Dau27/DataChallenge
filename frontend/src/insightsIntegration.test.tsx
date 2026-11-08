// @vitest-environment happy-dom
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { act, cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import Conversations from './Conversations';
import type { Conversation } from './types';

beforeEach(() => { localStorage.clear(); sessionStorage.clear(); });
afterEach(() => { cleanup(); vi.restoreAllMocks(); localStorage.clear(); sessionStorage.clear(); });

const source = (id: string, saved = true): Conversation => ({ id, source_id: `SYNTHETIC_${id}`, group_id: 'DEV', revision: 1,
  content_hash: `HASH_${id}`, language: 'EN', channel: 'agent chat', message_count: 2, audio_available: false,
  evaluation: saved ? { id: `RUN_${id}`, conversation_id: id, checklist_id: 1, state: 'succeeded', completeness: 'complete',
    total: '100.00', error: null, cached_from: null, created_at: '2026-11-01', updated_at: '2026-11-01' } : null });
const reasonCodes = ['open_appeal', 'needs_review', 'critical_true', 'critical_unknown', 'failed', 'interrupted', 'not_evaluated', 'in_progress'];
function priorityPacket(rows: Conversation[]) {
  return { checklist_id: 1, basis: 'effective', notice: 'SYNTHETIC priority states; no risk score or score change.',
    manifest: rows.map(row => ({ conversation_id: row.id, content_hash: row.content_hash, evaluation_id: row.evaluation?.id ?? null,
      updated_at: row.evaluation?.updated_at ?? null, state: row.evaluation?.state ?? 'not_evaluated' })),
    counts: Object.fromEntries(reasonCodes.map(code => [code, ['open_appeal', 'critical_unknown', 'not_evaluated'].includes(code) ? 1 : 0])),
    items: rows.map(row => ({ conversation_id: row.id, source_id: row.source_id, group_id: row.group_id, evaluation_id: row.evaluation?.id ?? null,
      state: row.evaluation?.state ?? 'not_evaluated', configured_flags: 1,
      flag_counts: { true: 0, false: row.evaluation ? 1 : 0, unknown: row.evaluation ? 0 : 1 }, oldest_reason_at: '2026-11-01',
      reasons: row.id === 'A' ? [{ code: 'open_appeal', label: 'Open appeal', since: '2026-11-01',
        targets: [{ conversation_id: row.id, evaluation_id: row.evaluation!.id, criterion_id: 'contact', criterion_name: 'Contact', appeal_id: 'APPEAL_A' }] }]
        : row.evaluation ? [] : ['critical_unknown', 'not_evaluated'].map(code => ({ code, label: code, since: '2026-11-01', targets: [] })) })) };
}

it('keeps the real queue selection and exports aligned with priority filtering, pending/error withholding and reset', async () => {
  const rows = [source('A'), source('B'), source('NEW', false)];
  rows[0].pending_appeals = 1;
  rows[0].pending_review_targets = [{ appeal_id: 'APPEAL_A', conversation_id: 'A', evaluation_id: 'RUN_A', criterion_id: 'contact', criterion_name: 'Contact' }];
  const original = structuredClone(rows);
  let resolveFirst: (response: Response) => void = () => {};
  let rejectRefresh: (reason: Error) => void = () => {};
  let priorityRequests = 0;
  const downloadClick = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});
  vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:SYNTHETIC_PRIORITY_EXPORT');
  vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => {});
  const fetch = vi.spyOn(globalThis, 'fetch').mockImplementation(url => {
    const path = String(url);
    if (path === '/api/insights/review-priority') {
      priorityRequests += 1;
      return priorityRequests === 1 ? new Promise(resolve => { resolveFirst = resolve; })
        : new Promise((_, reject) => { rejectRefresh = reject; });
    }
    if (path.startsWith('/api/evaluations/export-batch?')) return Promise.resolve(new Response('{}'));
    throw new Error(`Unexpected network route in synthetic integration test: ${path}`);
  });
  const props = { rows, access: null, selectedVersion: 1, completed: 2, needsReview: 0, busy: false,
    run: async (action: () => Promise<void>) => { await action(); }, evaluate: vi.fn(), refresh: vi.fn(), notify: vi.fn() };
  const view = render(<Conversations {...props} />);
  const queue = within(screen.getByRole('region', { name: 'Conversation review queue' }));
  fireEvent.click(screen.getByLabelText('Select all visible conversations'));
  const savedTools = document.querySelector<HTMLDetailsElement>('.queue-tools')!;
  savedTools.open = true; fireEvent(savedTools, new Event('toggle'));
  const exports = within(screen.getByRole('region', { name: 'Selected saved-run export' }));
  const download = exports.getByRole('button', { name: 'Selected JSON' }) as HTMLButtonElement;
  expect(exports.getByText('2', { selector: 'strong' })).toBeDefined();
  expect(screen.getByText('3 selected')).toBeDefined();

  const priority = document.querySelector<HTMLDetailsElement>('.review-priority')!;
  priority.open = true; fireEvent(priority, new Event('toggle'));
  fireEvent.change(screen.getByLabelText('Review priority reason'), { target: { value: 'open_appeal' } });
  await waitFor(() => expect(priorityRequests).toBe(1));
  expect(queue.queryByRole('link', { name: 'SYNTHETIC_A' })).toBeNull();
  expect(download.disabled).toBe(true);
  fireEvent.click(download);
  expect(fetch.mock.calls.filter(([url]) => String(url).includes('/export-batch?'))).toHaveLength(0);

  await act(async () => { resolveFirst(new Response(JSON.stringify(priorityPacket(rows)))); });
  expect(queue.getByRole('link', { name: 'SYNTHETIC_A' })).toBeDefined();
  expect(queue.queryByRole('link', { name: 'SYNTHETIC_B' })).toBeNull();
  expect(queue.queryByRole('link', { name: 'SYNTHETIC_NEW' })).toBeNull();
  expect((queue.getByLabelText('Select SYNTHETIC_A') as HTMLInputElement).checked).toBe(true);
  expect(screen.getByText('1 selected')).toBeDefined();
  expect(exports.getByText('1', { selector: 'strong' })).toBeDefined();
  expect(download.disabled).toBe(false);
  fireEvent.click(download);
  await waitFor(() => expect(downloadClick).toHaveBeenCalledOnce());
  const requests = fetch.mock.calls.filter(([url]) => String(url).includes('/export-batch?'));
  expect(requests).toHaveLength(1);
  const exported = new URL(String(requests[0][0]), 'http://test.invalid');
  expect(exported.pathname).toBe('/api/evaluations/export-batch');
  expect(exported.searchParams.getAll('evaluation_id')).toEqual(['RUN_A']);
  expect(exported.searchParams.get('format')).toBe('json');

  const refreshed = structuredClone(rows);
  refreshed[0].evaluation!.updated_at = '2026-11-02';
  view.rerender(<Conversations {...props} rows={refreshed} />);
  expect(download.disabled).toBe(true);
  expect(queue.queryByRole('link', { name: 'SYNTHETIC_A' })).toBeNull();
  await waitFor(() => expect(priorityRequests).toBe(2));
  await act(async () => { rejectRefresh(new Error('SYNTHETIC refresh unavailable')); });
  expect(screen.getAllByText(/The backend is unavailable/).length).toBeGreaterThan(0);
  expect(download.disabled).toBe(true);
  fireEvent.click(download);
  expect(fetch.mock.calls.filter(([url]) => String(url).includes('/export-batch?'))).toHaveLength(1);

  fireEvent.click(screen.getByRole('button', { name: 'Reset priority view' }));
  for (const row of rows) expect(queue.getByRole('link', { name: row.source_id })).toBeDefined();
  expect((screen.getByLabelText('Select all visible conversations') as HTMLInputElement).checked).toBe(true);
  expect(screen.getByText('3 selected')).toBeDefined();
  expect(exports.getByText('2', { selector: 'strong' })).toBeDefined();
  expect(download.disabled).toBe(false);
  expect(rows).toEqual(original);
});
