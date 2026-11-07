// @vitest-environment happy-dom
import { afterEach, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import CriterionBreakdown, { type Breakdown } from './CriterionBreakdown';
import type { Conversation } from './types';

afterEach(() => { cleanup(); vi.restoreAllMocks(); });
const row: Conversation = { id: 'SOURCE', source_id: 'TEST_SOURCE', group_id: 'DEV', revision: 1, content_hash: 'HASH',
  language: 'EN', channel: 'agent chat', message_count: 1, audio_available: false,
  evaluation: { id: 'RUN', conversation_id: 'SOURCE', checklist_id: 1, state: 'succeeded', completeness: 'complete',
    total: '100.00', created_at: '2026-11-01', updated_at: '2026-11-01', error: null, cached_from: null } };
function packet(rows = [row], name = 'Intro', basis: 'original' | 'effective' = 'effective'): Breakdown {
  return { checklist_id: 1, checklist_hash: 'CHECKLIST_HASH', basis, total_sources: rows.length, selection_policy: 'TEST latest',
    manifest: rows.map(r => ({ conversation_id: r.id, content_hash: r.content_hash, evaluation_id: r.evaluation?.id ?? null,
      updated_at: r.evaluation?.updated_at ?? null, state: r.evaluation?.state ?? 'not_evaluated' })),
    groups: [{ group_id: 'DEV', total_sources: rows.length, coverage: { succeeded: rows.length, failed: 0, not_evaluated: 0 }, criteria: [{
      criterion_id: 'contact', name, answer_type: 'binary', weight: '10', assessed_count: rows.length,
      buckets: [{ key: 'no', label: 'No', count: rows.length, denominator: rows.length, percentage: '100.00',
        cases: rows.map(r => ({ conversation_id: r.id, source_id: r.source_id, group_id: r.group_id, revision: r.revision, evaluation_id: r.evaluation?.id ?? null, criterion_id: 'contact' })) }] }] }] };
}
const json = (value: Breakdown) => new Response(JSON.stringify(value));
function open() { const details = document.querySelector('details')!; details.open = true; fireEvent(details, new Event('toggle')); }

it('loads only when opened and gives an exact source/run/criterion drilldown with explicit denominator', async () => {
  const fetch = vi.spyOn(globalThis, 'fetch').mockResolvedValue(json(packet()));
  render(<CriterionBreakdown rows={[row]} checklistId={1} />);
  expect(fetch).not.toHaveBeenCalled(); open();
  const cell = await screen.findByRole('button', { name: 'Inspect DEV: Intro: No' });
  expect(cell.textContent).toContain('1 / 1'); expect(cell.textContent).toContain('100.00%');
  expect(JSON.parse(fetch.mock.calls[0][1]!.body as string)).toEqual({ checklist_id: 1, conversation_ids: ['SOURCE'], basis: 'effective' });
  fireEvent.click(cell);
  expect(screen.getByRole('link', { name: 'TEST_SOURCE · revision 1' }).getAttribute('href')).toBe('#conversation/SOURCE?evaluation=RUN&criterion=contact');
  expect(screen.getByText(/do not measure model accuracy/)).toBeDefined();
});

it('switches original/effective basis and hides the previous distribution while waiting', async () => {
  let release: (value: Response) => void = () => {};
  const fetch = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(json(packet()))
    .mockImplementationOnce(() => new Promise(resolve => { release = resolve; }));
  render(<CriterionBreakdown rows={[row]} checklistId={1} />); open();
  fireEvent.click(await screen.findByRole('button', { name: 'Inspect DEV: Intro: No' }));
  fireEvent.change(screen.getByLabelText('Breakdown answer basis'), { target: { value: 'original' } });
  expect(screen.queryByRole('region', { name: 'Breakdown cases' })).toBeNull();
  expect(screen.queryByRole('button', { name: 'Inspect DEV: Intro: No' })).toBeNull();
  await waitFor(() => expect(fetch).toHaveBeenCalledTimes(2));
  release(json(packet([row], 'Original intro', 'original')));
  await screen.findByRole('button', { name: 'Inspect DEV: Original intro: No' });
});

it('ignores obsolete failures after a run review changes the request identity', async () => {
  let reject: (reason: Error) => void = () => {};
  const reviewed = { ...row, evaluation: { ...row.evaluation!, updated_at: '2026-11-02', completeness: 'needs_review', total: null } };
  const fetch = vi.spyOn(globalThis, 'fetch').mockImplementationOnce(() => new Promise((_, fail) => { reject = fail; }))
    .mockResolvedValueOnce(json(packet([reviewed], 'Reviewed intro')));
  const view = render(<CriterionBreakdown rows={[row]} checklistId={1} />); open();
  await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1));
  view.rerender(<CriterionBreakdown rows={[reviewed]} checklistId={1} />);
  await screen.findByRole('button', { name: 'Inspect DEV: Reviewed intro: No' });
  reject(new Error('SYNTHETIC obsolete failure'));
  await waitFor(() => expect(fetch).toHaveBeenCalledTimes(2));
  expect(screen.queryByRole('alert')).toBeNull();
});

it('rejects a mismatched manifest and supports an explicit retry', async () => {
  const wrong = packet(); wrong.manifest[0].content_hash = 'OTHER_REVISION';
  const fetch = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(json(wrong)).mockResolvedValueOnce(json(packet()));
  render(<CriterionBreakdown rows={[row]} checklistId={1} />); open();
  await screen.findByText(/Saved results changed/);
  expect(screen.queryByRole('button', { name: 'Inspect DEV: Intro: No' })).toBeNull();
  fireEvent.click(screen.getByRole('button', { name: 'Retry breakdown' }));
  await screen.findByRole('button', { name: 'Inspect DEV: Intro: No' });
  expect(fetch).toHaveBeenCalledTimes(2);
});

it('ignores an older successful response after the visible source selection changes', async () => {
  let release: (value: Response) => void = () => {};
  const other = { ...row, id: 'OTHER', source_id: 'OTHER_SOURCE', content_hash: 'OTHER_HASH', evaluation: null };
  const fetch = vi.spyOn(globalThis, 'fetch').mockImplementationOnce(() => new Promise(resolve => { release = resolve; }))
    .mockResolvedValueOnce(json(packet([other], 'Current intro')));
  const view = render(<CriterionBreakdown rows={[row]} checklistId={1} />); open();
  await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1));
  view.rerender(<CriterionBreakdown rows={[other]} checklistId={1} />);
  await screen.findByRole('button', { name: 'Inspect DEV: Current intro: No' });
  release(json(packet([row], 'Obsolete intro')));
  await waitFor(() => expect(fetch).toHaveBeenCalledTimes(2));
  expect(screen.queryByText('Obsolete intro')).toBeNull();
  expect(screen.getByText('Current intro')).toBeDefined();
});

it('does not fetch for empty or over-limit scopes and does not silently show a partial result', () => {
  const fetch = vi.spyOn(globalThis, 'fetch');
  const view = render(<CriterionBreakdown rows={[]} checklistId={1} />); open();
  expect(screen.getByText('No visible conversations to analyse.')).toBeDefined();
  view.rerender(<CriterionBreakdown rows={Array.from({ length: 201 }, (_, i) => ({ ...row, id: String(i) }))} checklistId={1} />);
  expect(screen.getByRole('alert').textContent).toContain('No partial breakdown');
  expect(fetch).not.toHaveBeenCalled();
});
