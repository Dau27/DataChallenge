// @vitest-environment happy-dom
import { afterEach, expect, it, vi } from 'vitest';
import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import type { Conversation } from './types';
import { useReviewPriority } from './ReviewPriority';

afterEach(() => { cleanup(); vi.restoreAllMocks(); });
const source = (id: string): Conversation => ({ id, source_id: `SYNTHETIC_${id}`, group_id: 'DEV', revision: 1, content_hash: `HASH_${id}`,
  language: 'EN', channel: 'agent chat', message_count: 2, audio_available: false, evaluation: { id: `RUN_${id}`, conversation_id: id,
    checklist_id: 1, state: 'succeeded', completeness: 'complete', total: '100.00', error: null, cached_from: null, created_at: '2026-01-01', updated_at: '2026-01-01' } });
const codes = ['open_appeal', 'needs_review', 'critical_true', 'critical_unknown', 'failed', 'interrupted', 'not_evaluated', 'in_progress'];
const reason = (code: string, id: string, since = '2026-01-01') => ({ code, label: code === 'open_appeal' ? 'Open appeal' : 'Critical status unknown', since,
  targets: [{ conversation_id: `${id}_OLD`, evaluation_id: 'OLD_RUN', criterion_id: 'contact', criterion_name: 'Contact' }] });
function packet(rows: Conversation[], reasons: Record<string, ReturnType<typeof reason>[]> = {}) {
  return { checklist_id: 1, basis: 'effective', notice: 'SYNTHETIC recorded states, not a risk score.',
    manifest: rows.map(row => ({ conversation_id: row.id, content_hash: row.content_hash, evaluation_id: row.evaluation?.id ?? null,
      updated_at: row.evaluation?.updated_at ?? null, state: row.evaluation?.state ?? 'not_evaluated' })),
    counts: Object.fromEntries(codes.map(code => [code, Object.values(reasons).filter(items => items.some(item => item.code === code)).length])),
    items: rows.map(row => ({ conversation_id: row.id, source_id: row.source_id, group_id: row.group_id, evaluation_id: row.evaluation?.id,
      state: row.evaluation?.state, reasons: reasons[row.id] ?? [], configured_flags: 1,
      flag_counts: { true: 0, false: (reasons[row.id] ?? []).some(r => r.code === 'critical_unknown') ? 0 : 1,
        unknown: (reasons[row.id] ?? []).some(r => r.code === 'critical_unknown') ? 1 : 0 },
      oldest_reason_at: reasons[row.id]?.[0]?.since ?? '2026-01-01' })) };
}
function Harness({ rows, version = 1 }: { rows: Conversation[]; version?: number }) {
  const priority = useReviewPriority(rows, version);
  return <>{priority.controls}<div>{priority.rows.map(row => <article key={row.id} data-testid="row">{row.source_id}{priority.renderReasons(row.id)}</article>)}</div></>;
}
const openTools = () => { const details = document.querySelector('details')!; details.open = true; fireEvent(details, new Event('toggle')); };
const order = () => screen.queryAllByTestId('row').map(row => row.textContent?.slice(0, 11));

it('does not fetch or change the queue until priority tools are requested', () => {
  const fetch = vi.spyOn(globalThis, 'fetch'); const rows = [source('A'), source('B')]; const before = structuredClone(rows);
  render(<Harness rows={rows} />);
  expect(fetch).not.toHaveBeenCalled(); expect(order()).toEqual(['SYNTHETIC_A', 'SYNTHETIC_B']); expect(rows).toEqual(before);
});

it('sorts and filters the existing rows with explicit reasons and exact older-revision targets', async () => {
  const rows = [source('A'), source('B')];
  vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify(packet(rows, { A: [reason('critical_unknown', 'A')], B: [reason('open_appeal', 'B', '2025-01-01')] }))));
  render(<Harness rows={rows} />); openTools(); await screen.findByText('SYNTHETIC recorded states, not a risk score.');
  fireEvent.change(screen.getByLabelText('Review priority order'), { target: { value: 'appeals' } });
  expect(order()).toEqual(['SYNTHETIC_B', 'SYNTHETIC_A']);
  const old = screen.getAllByRole('link', { name: /Contact · earlier revision/ })[0];
  expect(old.getAttribute('href')).toBe('#conversation/B_OLD?evaluation=OLD_RUN&criterion=contact');
  fireEvent.change(screen.getByLabelText('Review priority reason'), { target: { value: 'critical_unknown' } });
  expect(order()).toEqual(['SYNTHETIC_A']); expect(screen.getByText('Critical flags: 0 true · 0 false · 1 unknown')).toBeDefined();
  fireEvent.click(screen.getByRole('button', { name: 'Reset priority view' }));
  expect(order()).toEqual(['SYNTHETIC_A', 'SYNTHETIC_B']);
});

it('hides obsolete priority results and ignores late successes and errors after scope changes', async () => {
  let resolveOld: (value: Response) => void = () => {}; let resolveNew: (value: Response) => void = () => {};
  vi.spyOn(globalThis, 'fetch').mockImplementationOnce(() => new Promise(resolve => { resolveOld = resolve; }))
    .mockImplementationOnce(() => new Promise(resolve => { resolveNew = resolve; }));
  const old = [source('OLD')]; const next = [source('NEW')]; const view = render(<Harness rows={old} />);
  openTools(); fireEvent.change(screen.getByLabelText('Review priority order'), { target: { value: 'appeals' } });
  expect(screen.queryAllByTestId('row')).toHaveLength(0);
  view.rerender(<Harness rows={next} />);
  await act(async () => { resolveNew(new Response(JSON.stringify(packet(next)))); });
  expect(order()).toEqual(['SYNTHETIC_N']);
  await act(async () => { resolveOld(new Response(JSON.stringify(packet(old)))); });
  expect(order()).toEqual(['SYNTHETIC_N']); expect(screen.queryByRole('alert')).toBeNull();
});

it('rejects a mismatched manifest and retries without showing stale targets', async () => {
  const rows = [source('A')]; const bad = packet(rows); bad.manifest[0].evaluation_id = 'OTHER_RUN';
  vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(new Response(JSON.stringify(bad)))
    .mockResolvedValueOnce(new Response(JSON.stringify(packet(rows))));
  render(<Harness rows={rows} />); openTools();
  fireEvent.change(screen.getByLabelText('Review priority reason'), { target: { value: 'open_appeal' } });
  await screen.findByText('Saved results changed. Refresh the queue and retry priority analysis.');
  expect(screen.queryAllByTestId('row')).toHaveLength(0);
  fireEvent.click(screen.getByRole('button', { name: 'Retry priority analysis' }));
  await screen.findByText('SYNTHETIC recorded states, not a risk score.');
  fireEvent.click(screen.getByRole('button', { name: 'Reset priority view' }));
  expect(order()).toEqual(['SYNTHETIC_A']);
});

it('invalidates results when the selected run changes and suppresses obsolete failures', async () => {
  let reject: (error: Error) => void = () => {};
  const old = [source('A')]; const changed = structuredClone(old); changed[0].evaluation!.updated_at = '2026-02-01';
  const fetch = vi.spyOn(globalThis, 'fetch').mockImplementationOnce(() => new Promise((_, fail) => { reject = fail; }))
    .mockResolvedValueOnce(new Response(JSON.stringify(packet(changed))));
  const view = render(<Harness rows={old} />); openTools();
  fireEvent.change(screen.getByLabelText('Review priority order'), { target: { value: 'oldest' } });
  view.rerender(<Harness rows={changed} />);
  await screen.findByText('SYNTHETIC recorded states, not a risk score.');
  await act(async () => { reject(new Error('SYNTHETIC obsolete failure')); });
  expect(fetch).toHaveBeenCalledTimes(2); expect(screen.queryByRole('alert')).toBeNull(); expect(order()).toEqual(['SYNTHETIC_A']);
});

it('blocks oversized scope rather than silently truncating it', async () => {
  const fetch = vi.spyOn(globalThis, 'fetch');
  render(<Harness rows={Array.from({ length: 201 }, (_, i) => source(String(i)))} />); openTools();
  await waitFor(() => expect(screen.getByRole('alert').textContent).toContain('at most 200'));
  expect(fetch).not.toHaveBeenCalled();
});

it('keeps active filters, pending status and failures visible when the disclosure is closed', async () => {
  let reject: (error: Error) => void = () => {};
  const rows = [source('A')];
  vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(new Response(JSON.stringify(packet(rows))))
    .mockImplementationOnce(() => new Promise((_, fail) => { reject = fail; }));
  const view = render(<Harness rows={rows} />); openTools();
  await screen.findByText('SYNTHETIC recorded states, not a risk score.');
  fireEvent.change(screen.getByLabelText('Review priority reason'), { target: { value: 'open_appeal' } });
  const details = document.querySelector('details')!; details.open = false; fireEvent(details, new Event('toggle'));
  expect(screen.getByRole('status').textContent).toContain('Showing 0 of 1 conversations');
  view.rerender(<Harness rows={[source('NEW')]} />);
  expect(screen.getByRole('status').textContent).toContain('temporarily withheld');
  await act(async () => { reject(new Error('SYNTHETIC new-source failure')); });
  expect(screen.getByRole('alert').textContent).toContain('The backend is unavailable');
  expect(screen.queryAllByTestId('row')).toHaveLength(0);
  fireEvent.click(screen.getByRole('button', { name: 'Reset priority view' }));
  expect(order()).toEqual(['SYNTHETIC_N']);
});
