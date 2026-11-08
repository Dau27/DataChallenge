// @vitest-environment happy-dom
import { afterEach, expect, it, vi } from 'vitest';
import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import { Component, type ReactNode } from 'react';
import CohortPairPreview, { cohortAnswerLabel } from './CohortPairPreview';
import { cohortResultFixture, exactPairFixture } from './cohortTestFixtures';

afterEach(() => { cleanup(); vi.restoreAllMocks(); });
const json = (value: unknown, status = 200) => new Response(JSON.stringify(value), { status });
const pair = () => cohortResultFixture().pairs[0];

it('uses the selected original basis and exact source/run identity for preview and evidence links', async () => {
  const selected = pair(); const fetch = vi.spyOn(globalThis, 'fetch').mockResolvedValue(json(exactPairFixture(selected, 'original')));
  const onOpenPair = vi.fn(); render(<CohortPairPreview pair={selected} basis="original" onClose={vi.fn()} onOpenPair={onOpenPair} />);
  const evidence = await screen.findByRole('link', { name: 'Baseline evidence m0001–m0001' });
  expect(evidence.getAttribute('href')).toBe('#conversation/C1?evaluation=A_C1&criterion=contact&message=m0001');
  expect(String(fetch.mock.calls[0][0])).toContain('left_basis=original&right_basis=original');
  expect(screen.getByRole('heading', { name: 'Exact saved pair · original answers' })).toBeDefined();
  fireEvent.click(screen.getByRole('button', { name: 'Open these run IDs in review' }));
  expect(onOpenPair).toHaveBeenCalledWith('A_C1', 'B_C1');
});

it.each(['left', 'right', 'revision', 'revision_number', 'checklist', 'updated', 'basis'])('refuses a mismatched %s before allowing the review callback', async mismatch => {
  const selected = pair(); const response = exactPairFixture(selected);
  if (mismatch === 'left') response.left.id = 'WRONG';
  if (mismatch === 'right') response.right.id = 'WRONG';
  if (mismatch === 'revision') response.source.content_hash = 'WRONG';
  if (mismatch === 'revision_number') response.source.revision += 1;
  if (mismatch === 'checklist') response.left.checklist.id += 1;
  if (mismatch === 'updated') response.right.updated_at = '2026-11-09';
  if (mismatch === 'basis') response.left.basis = 'original';
  vi.spyOn(globalThis, 'fetch').mockResolvedValue(json(response));
  const onOpenPair = vi.fn(); render(<CohortPairPreview pair={selected} basis="effective" onClose={vi.fn()} onOpenPair={onOpenPair} />);
  await screen.findByText(/Saved pair changed/);
  expect(screen.queryByRole('button', { name: 'Open these run IDs in review' })).toBeNull();
  expect(onOpenPair).not.toHaveBeenCalled();
});

class MalformedPacketBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  render() { return this.state.failed ? <p role="alert">SYNTHETIC_RENDER_CRASH</p> : this.props.children; }
}

it.each(['evidence', 'value', 'changes', 'total'])('reports malformed pair %s without a renderer crash or review callback', async kind => {
  const selected = pair(); const response = exactPairFixture(selected);
  const malformed = response as unknown as { total_difference: unknown; criteria: { changes: unknown; left: { judgment: { evidence: unknown; value: unknown } } }[] };
  if (kind === 'evidence') malformed.criteria[0].left.judgment.evidence = 'not an evidence array';
  if (kind === 'value') malformed.criteria[0].left.judgment.value = { invalid: 'SYNTHETIC' };
  if (kind === 'changes') malformed.criteria[0].changes = null;
  if (kind === 'total') malformed.total_difference = { invalid: 'SYNTHETIC' };
  vi.spyOn(console, 'error').mockImplementation(() => {});
  vi.spyOn(globalThis, 'fetch').mockResolvedValue(json(response));
  const onOpenPair = vi.fn();
  render(<MalformedPacketBoundary><CohortPairPreview pair={selected} basis="effective" onClose={vi.fn()} onOpenPair={onOpenPair} /></MalformedPacketBoundary>);
  const alert = await screen.findByRole('alert');
  expect(alert.textContent).toContain('Saved pair data is invalid');
  expect(screen.queryByText('SYNTHETIC_RENDER_CRASH')).toBeNull();
  expect(onOpenPair).not.toHaveBeenCalled();
});

it('retries a temporary pair failure and never displays raw saved errors', async () => {
  const selected = pair(); const response = exactPairFixture(selected); response.left.error = 'PRIVATE SAVED ERROR https://example.invalid/token=NO';
  vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(json({ detail: 'SYNTHETIC outage' }, 503)).mockResolvedValueOnce(json(response));
  render(<CohortPairPreview pair={selected} basis="effective" onClose={vi.fn()} onOpenPair={vi.fn()} />);
  fireEvent.click(await screen.findByRole('button', { name: 'Retry exact pair' }));
  await screen.findByRole('button', { name: 'Open these run IDs in review' });
  expect(screen.queryByText(/PRIVATE SAVED ERROR/)).toBeNull();
});

it('ignores a late pair response when a different saved pair is selected', async () => {
  let release!: (response: Response) => void;
  const first = pair(); const second = structuredClone(first); second.right!.evaluation_id = 'NEW_RUN';
  vi.spyOn(globalThis, 'fetch').mockImplementationOnce(() => new Promise<Response>(resolve => { release = resolve; })).mockResolvedValueOnce(json(exactPairFixture(second)));
  const onOpenPair = vi.fn(); const view = render(<CohortPairPreview pair={first} basis="effective" onClose={vi.fn()} onOpenPair={onOpenPair} />);
  await screen.findByText('Loading exact saved pair…');
  view.rerender(<CohortPairPreview pair={second} basis="effective" onClose={vi.fn()} onOpenPair={onOpenPair} />);
  await screen.findByRole('button', { name: 'Open these run IDs in review' });
  await act(async () => release(json(exactPairFixture(first))));
  fireEvent.click(screen.getByRole('button', { name: 'Open these run IDs in review' }));
  expect(onOpenPair).toHaveBeenCalledWith('A_C1', 'NEW_RUN');
});

it('keeps unknown flags, N/A and unavailable values distinct from No', () => {
  expect(cohortAnswerLabel({ disposition: 'needs_review', value: null, reason: null }, 'flag')).toBe('Needs review');
  expect(cohortAnswerLabel({ disposition: 'unavailable', value: null, reason: null }, 'flag')).toBe('Unavailable');
  expect(cohortAnswerLabel({ disposition: 'not_applicable', value: null, reason: null })).toBe('N/A');
  expect(cohortAnswerLabel({ disposition: 'assessed', value: false, reason: null }, 'flag')).toBe('Not flagged');
});
