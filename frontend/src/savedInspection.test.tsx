// @vitest-environment happy-dom
import { afterEach, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import SavedComparison from './SavedComparison';
import SavedExport from './SavedExport';
import type { Checklist, EvaluationSummary, SavedComparison as Comparison } from './types';
import seed from '../../config/initial_checklist.json';

afterEach(() => { cleanup(); vi.restoreAllMocks(); localStorage.clear(); });
const run = (id: string): EvaluationSummary => ({ id, conversation_id: 'SOURCE', checklist_id: 1, state: 'succeeded', completeness: 'complete',
  total: '100', error: null, cached_from: null, created_at: '2026-11-01T00:00:00Z', updated_at: '2026-11-01T00:00:00Z' });
function comparison(): Comparison {
  const side = { ...run('left'), basis: 'effective' as const, checklist: { id: 1, content_hash: 'HASH', snapshot: seed as Checklist, created_at: '2026-11-01T00:00:00Z' },
    score: null, metadata: { model: 'SAVED_MODEL' }, review_count: 0,
    usage: { request_attempts: 0, input_tokens_known: 0, output_tokens_known: 0, usage_complete: false, estimated_cost_usd: null, cost_rate_source: null, latency_ms: 0 } };
  const cell = { criterion: (seed as Checklist).criteria[0], points: null, judgment: { disposition: 'assessed' as const, value: true, explanation: 'Saved explanation',
    na_reason: null, review_reason: null, evidence: [{ kind: 'support' as const, start_message_id: 'm0001', end_message_id: 'm0001' }] } };
  return { source: { id: 'SOURCE', source_id: 'TEST_ONLY', revision: 1, content_hash: 'SOURCE_HASH' }, left: side, right: { ...side, id: 'right' },
    total_comparable: false, total_difference: null, notice: 'One total is unresolved.',
    criteria: [{ criterion_id: 'contact', change: 'unchanged', changes: [], configuration_changes: [], answer_comparable: true, points_difference: null, left: cell, right: cell }] };
}

it('compares selected saved answer sets, keeps null totals and navigates stored evidence', async () => {
  const requests: string[] = []; const evidence = vi.fn();
  vi.spyOn(globalThis, 'fetch').mockImplementation(async url => { requests.push(String(url)); return new Response(JSON.stringify(comparison())); });
  render(<SavedComparison runs={[run('left'), run('right')]} currentId="right" sourceId="SOURCE" onEvidence={evidence} />);
  expect(requests).toHaveLength(0);
  fireEvent.click(screen.getByRole('button', { name: 'Compare saved runs' }));
  await screen.findByText(/No comparable total difference/);
  fireEvent.click(screen.getByRole('button', { name: 'Baseline evidence contact m0001' }));
  expect(evidence).toHaveBeenCalledWith(comparison().criteria[0].left.judgment!.evidence[0]);
  fireEvent.change(screen.getByLabelText('Baseline answer set'), { target: { value: 'original' } });
  await waitFor(() => expect(requests.at(-1)).toContain('left_basis=original'));
  await screen.findByText(/No comparable total difference/);
  fireEvent.click(screen.getByLabelText('Show changed criteria only'));
  await screen.findByText('No saved differences.');
  expect(requests.every(r => r.startsWith('/api/evaluations/compare?'))).toBe(true);
});

it('hides stale comparisons and offers retry after a read error', async () => {
  let release: ((response: Response) => void) | undefined;
  const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementationOnce(() => new Promise(resolve => { release = resolve; }))
    .mockResolvedValueOnce(new Response(JSON.stringify({ detail: 'Saved read failed' }), { status: 500 }))
    .mockResolvedValue(new Response(JSON.stringify(comparison())));
  render(<SavedComparison runs={[run('left'), run('right')]} currentId="right" sourceId="SOURCE" onEvidence={vi.fn()} />);
  fireEvent.click(screen.getByRole('button', { name: 'Compare saved runs' }));
  await waitFor(() => expect(release).toBeDefined());
  fireEvent.change(screen.getByLabelText('Baseline answer set'), { target: { value: 'original' } });
  await screen.findByText('Saved read failed');
  release!(new Response(JSON.stringify(comparison())));
  expect(screen.queryByText(/No comparable total difference/)).toBeNull();
  fireEvent.click(screen.getByRole('button', { name: 'Retry comparison' }));
  await screen.findByText(/No comparable total difference/);
  expect(fetchMock).toHaveBeenCalledTimes(3);
});

it('downloads both real response blobs with explicit excerpt consent and no POST', async () => {
  const blobs: Blob[] = [];
  vi.spyOn(URL, 'createObjectURL').mockImplementation(blob => { blobs.push(blob as Blob); return 'blob:TEST'; });
  vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => {});
  const click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});
  const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(async () => new Response('{"saved":true}', { headers: { 'Content-Type': 'application/json' } }));
  render(<SavedExport evaluationId="SAVED" />);
  fireEvent.click(screen.getByRole('button', { name: 'Download JSON' }));
  await waitFor(() => expect(click).toHaveBeenCalledTimes(1));
  expect(fetchMock.mock.calls[0][0]).toBe('/api/evaluations/SAVED/export?format=json&include_excerpts=false');
  expect(await blobs[0].text()).toBe('{"saved":true}');
  fireEvent.click(screen.getByLabelText('Include source evidence excerpts'));
  fireEvent.click(screen.getByRole('button', { name: 'Download CSV' }));
  await waitFor(() => expect(click).toHaveBeenCalledTimes(2));
  expect(fetchMock.mock.calls[1][0]).toBe('/api/evaluations/SAVED/export?format=csv&include_excerpts=true');
  expect(fetchMock.mock.calls.every(c => c[1] === undefined)).toBe(true);
});

it('reports export failures and does not download a response after leaving its run', async () => {
  let release: ((response: Response) => void) | undefined;
  const objectURL = vi.spyOn(URL, 'createObjectURL');
  vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(new Response(JSON.stringify({ detail: 'Saved export failed' }), { status: 500 }))
    .mockImplementationOnce(() => new Promise(resolve => { release = resolve; }));
  const view = render(<SavedExport evaluationId="SAVED" />);
  fireEvent.click(screen.getByRole('button', { name: 'Download JSON' }));
  await screen.findByRole('alert');
  expect(screen.getByText(/Saved export failed/)).toBeDefined();
  fireEvent.click(screen.getByRole('button', { name: 'Download CSV' }));
  await waitFor(() => expect(release).toBeDefined());
  view.unmount(); release!(new Response('CSV TEST'));
  await new Promise(resolve => setTimeout(resolve, 10));
  expect(objectURL).not.toHaveBeenCalled();
});
