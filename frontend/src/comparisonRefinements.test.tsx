// @vitest-environment happy-dom
import { afterEach, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import SavedComparison from './SavedComparison';
import type { Checklist, EvaluationSummary, SavedComparison as Comparison } from './types';
import seed from '../../config/initial_checklist.json';

afterEach(() => { cleanup(); vi.restoreAllMocks(); });
const run = (id: string, changes: Partial<EvaluationSummary> = {}): EvaluationSummary => ({ id, conversation_id: 'SOURCE', checklist_id: 1,
  state: 'succeeded', completeness: 'complete', total: '100.00', error: null, cached_from: null,
  created_at: id === 'right' ? '2026-11-02T00:00:00Z' : '2026-11-01T00:00:00Z', updated_at: '2026-11-02T00:00:00Z', ...changes });
const runs = [run('right'), run('left')];
function comparison(notice = 'SAVED_RESULT'): Comparison {
  const side = { ...run('left'), basis: 'effective' as const, checklist: { id: 1, content_hash: 'HASH', snapshot: seed as Checklist, created_at: '2026-11-01T00:00:00Z' },
    score: null, metadata: { model: 'TEST_MODEL', prompt_hash: 'a'.repeat(64), schema_hash: 'b'.repeat(64), response_models: ['TEST_DATED_MODEL'] }, review_count: 0,
    usage: { request_attempts: 1, input_tokens_known: 0, output_tokens_known: 0, usage_complete: false, estimated_cost_usd: null, cost_rate_source: null, latency_ms: 0 } };
  return { source: { id: 'SOURCE', source_id: 'TEST_ONLY', revision: 1, content_hash: 'SOURCE_HASH' }, left: side, right: { ...side, id: 'right' },
    total_comparable: false, total_difference: null, notice, criteria: [] };
}
const props = { runs, currentId: 'right', sourceId: 'SOURCE', onEvidence: vi.fn() };

it.each(['left', 'right'])('refreshes and immediately hides the old comparison after %s receives a reviewed revision', async selected => {
  let release: ((response: Response) => void) | undefined;
  const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(new Response(JSON.stringify(comparison('BEFORE_REVIEW'))))
    .mockImplementationOnce(() => new Promise(resolve => { release = resolve; }));
  const view = render(<SavedComparison {...props} />);
  fireEvent.click(screen.getByRole('button', { name: 'Compare saved runs' }));
  await screen.findByText(/BEFORE_REVIEW/);
  const updated = runs.map(r => r.id === selected ? { ...r, updated_at: '2026-11-03T00:00:00Z', completeness: 'needs_review', total: null } : r);
  view.rerender(<SavedComparison {...props} runs={updated} />);
  expect(screen.queryByText(/BEFORE_REVIEW/)).toBeNull();
  expect(screen.getByRole('status').textContent).toContain('Loading saved comparison');
  await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
  release!(new Response(JSON.stringify(comparison('AFTER_REVIEW_WITHHELD_TOTAL'))));
  await screen.findByText(/AFTER_REVIEW_WITHHELD_TOTAL/);
  expect(screen.getAllByText(/No numeric total/)).toHaveLength(2);
  expect((screen.getByLabelText('Baseline saved run') as HTMLSelectElement).value).toBe('left');
  expect((screen.getByLabelText('Comparison saved run') as HTMLSelectElement).value).toBe('right');
});

it('ignores a late response for an older run revision and refetches on state-only changes', async () => {
  let release: ((response: Response) => void) | undefined;
  const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementationOnce(() => new Promise(resolve => { release = resolve; }))
    .mockResolvedValueOnce(new Response(JSON.stringify(comparison('CURRENT_REVISION'))));
  const view = render(<SavedComparison {...props} />);
  fireEvent.click(screen.getByRole('button', { name: 'Compare saved runs' }));
  await waitFor(() => expect(release).toBeDefined());
  view.rerender(<SavedComparison {...props} runs={runs.map(r => r.id === 'right' ? { ...r, state: 'failed' } : r)} />);
  await screen.findByText(/CURRENT_REVISION/);
  release!(new Response(JSON.stringify(comparison('OBSOLETE_REVISION'))));
  await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
  expect(screen.queryByText(/OBSOLETE_REVISION/)).toBeNull();
});

it('does not reload for unrelated runs or identical run objects and retains explicit choices on refresh/reopen', async () => {
  const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(async () => new Response(JSON.stringify(comparison())));
  const withOther = [...runs, run('other', { checklist_id: 2 })];
  const view = render(<SavedComparison {...props} runs={withOther} />);
  fireEvent.click(screen.getByRole('button', { name: 'Compare saved runs' }));
  await screen.findByText(/SAVED_RESULT/);
  view.rerender(<SavedComparison {...props} runs={withOther.map(r => r.id === 'other' ? { ...r, updated_at: '2026-11-04T00:00:00Z' } : { ...r })} />);
  expect(fetchMock).toHaveBeenCalledTimes(1);
  fireEvent.change(screen.getByLabelText('Baseline saved run'), { target: { value: 'other' } });
  await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
  fireEvent.click(screen.getByRole('button', { name: 'Compare saved runs' }));
  fireEvent.click(screen.getByRole('button', { name: 'Compare saved runs' }));
  await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));
  expect((screen.getByLabelText('Baseline saved run') as HTMLSelectElement).value).toBe('other');
});

it('defaults to the nearest earlier successful compatible run while leaving other runs selectable', async () => {
  const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(async () => new Response(JSON.stringify(comparison())));
  render(<SavedComparison {...props} runs={[run('right'), run('failed', { state: 'failed', created_at: '2026-11-01T23:00:00Z' }),
    run('other-rubric', { checklist_id: 2, created_at: '2026-11-01T22:00:00Z' }),
    run('future', { created_at: '2026-11-03T00:00:00Z' }), run('left'), run('older', { created_at: '2026-10-01T00:00:00Z' })]} />);
  fireEvent.click(screen.getByRole('button', { name: 'Compare saved runs' }));
  await screen.findByText(/SAVED_RESULT/);
  expect((screen.getByLabelText('Baseline saved run') as HTMLSelectElement).value).toBe('left');
  expect(within(screen.getByLabelText('Baseline saved run')).getAllByRole('option')).toHaveLength(6);
  expect(String(fetchMock.mock.calls[0][0])).toContain('left_id=left&right_id=right');
});

it('separates decision/point/definition changes from details-only changes without another request', async () => {
  const data = comparison();
  const cell = { criterion: (seed as Checklist).criteria[0], points: null, judgment: null };
  data.criteria = [
    { criterion_id: 'answer_row', change: 'changed', changes: ['answer', 'points', 'explanation'], configuration_changes: [] },
    { criterion_id: 'detail_row', change: 'changed', changes: ['explanation', 'evidence'], configuration_changes: [] },
    { criterion_id: 'definition_row', change: 'changed', changes: ['configuration'], configuration_changes: ['description'] },
    { criterion_id: 'unchanged_row', change: 'unchanged', changes: [], configuration_changes: [] },
  ].map(row => ({ ...row, answer_comparable: true, points_difference: null, left: cell, right: cell }));
  const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify(data)));
  render(<SavedComparison {...props} />);
  fireEvent.click(screen.getByRole('button', { name: 'Compare saved runs' }));
  await screen.findByText(/SAVED_RESULT/);
  const filter = screen.getByLabelText('Comparison difference filter');
  expect(within(filter).getByRole('option', { name: 'Answers / dispositions (1)' })).toBeDefined();
  expect(within(filter).getByRole('option', { name: 'Evidence / explanation only (1)' })).toBeDefined();
  fireEvent.change(filter, { target: { value: 'details' } });
  expect(screen.getByText(/detail_row ·/)).toBeDefined(); expect(screen.queryByText(/answer_row ·/)).toBeNull();
  fireEvent.change(filter, { target: { value: 'answers' } });
  expect(screen.getByText(/answer_row ·/)).toBeDefined(); expect(screen.queryByText(/detail_row ·/)).toBeNull();
  fireEvent.change(filter, { target: { value: 'configuration' } });
  expect(screen.getByText(/definition_row ·/)).toBeDefined(); expect(screen.queryByText(/answer_row ·/)).toBeNull();
  fireEvent.change(filter, { target: { value: 'points' } });
  expect(screen.getByText(/answer_row ·/)).toBeDefined();
  expect(fetchMock).toHaveBeenCalledTimes(1);
  fireEvent.click(screen.getByText('Baseline provenance'));
  expect(screen.getAllByText(/Recorded response model\(s\): TEST_DATED_MODEL/)).toHaveLength(2);
});

it('hides the prior result after a reviewed revision fails to load and retries only the current revision', async () => {
  const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(new Response(JSON.stringify(comparison('OLDER_LOADED_RESULT'))))
    .mockResolvedValueOnce(new Response(JSON.stringify({ detail: 'Review comparison read failed' }), { status: 500 }))
    .mockResolvedValueOnce(new Response(JSON.stringify(comparison('CURRENT_RETRY_RESULT'))));
  const view = render(<SavedComparison {...props} />);
  fireEvent.click(screen.getByRole('button', { name: 'Compare saved runs' }));
  await screen.findByText(/OLDER_LOADED_RESULT/);
  view.rerender(<SavedComparison {...props} runs={runs.map(r => r.id === 'left' ? { ...r, updated_at: '2026-11-04T00:00:00Z' } : r)} />);
  expect(screen.queryByText(/OLDER_LOADED_RESULT/)).toBeNull();
  await screen.findByText('Review comparison read failed');
  expect(screen.queryByText(/OLDER_LOADED_RESULT/)).toBeNull();
  fireEvent.click(screen.getByRole('button', { name: 'Retry comparison' }));
  await screen.findByText(/CURRENT_RETRY_RESULT/);
  expect(fetchMock).toHaveBeenCalledTimes(3);
});
