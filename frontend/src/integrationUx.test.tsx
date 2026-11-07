// @vitest-environment happy-dom
import { createRef } from 'react';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import Conversations from './Conversations';
import SavedExport from './SavedExport';
import CriterionBreakdown from './CriterionBreakdown';
import type { Conversation } from './types';

beforeEach(() => { localStorage.clear(); sessionStorage.clear(); });
afterEach(() => { cleanup(); vi.restoreAllMocks(); localStorage.clear(); sessionStorage.clear(); });
const rows: Conversation[] = ['KZ', 'RU'].map(language => ({ id: language, source_id: `TEST_${language}`, group_id: 'DEV', revision: 1, content_hash: `TEST_${language}`,
  language, channel: 'agent chat', message_count: 2, audio_available: false, evaluation: { id: `RUN_${language}`, conversation_id: language, checklist_id: 1,
    state: 'succeeded', completeness: 'complete', total: '100.00', error: null, cached_from: null, created_at: '', updated_at: '' } }));
const props = { rows, access: null, selectedVersion: 1, completed: 2, needsReview: 0, busy: false,
  run: async (action: () => Promise<void>) => { await action(); }, evaluate: vi.fn(), refresh: vi.fn(), notify: vi.fn() };

it('announces partial visible selection and keeps select-all correct when the view changes', () => {
  render(<Conversations {...props} />);
  const all = screen.getByLabelText('Select all visible conversations') as HTMLInputElement;
  fireEvent.click(screen.getByLabelText('Select TEST_KZ'));
  expect(all.indeterminate).toBe(true);
  expect(all.getAttribute('aria-checked')).toBe('mixed');
  fireEvent.click(all);
  expect(all.checked).toBe(true); expect(all.indeterminate).toBe(false);
  fireEvent.change(screen.getByLabelText('Language filter'), { target: { value: 'RU' } });
  expect(all.checked).toBe(true); expect(all.indeterminate).toBe(false);
  fireEvent.click(screen.getByRole('button', { name: 'Clear selection' }));
  expect(all.checked).toBe(false); expect(all.indeterminate).toBe(false);
});

it('reveals a failed selected-run download even if its tool group was closed while waiting', async () => {
  let reject: (reason: Error) => void = () => {};
  vi.spyOn(globalThis, 'fetch').mockImplementation(() => new Promise((_, fail) => { reject = fail; }));
  render(<Conversations {...props} />);
  fireEvent.click(screen.getByLabelText('Select TEST_KZ'));
  const group = document.querySelector<HTMLDetailsElement>('.queue-tools')!;
  group.open = true;
  fireEvent.click(screen.getByRole('button', { name: 'Selected JSON' }));
  group.open = false;
  reject(new Error('SYNTHETIC export unavailable'));
  await screen.findByText(/The backend is unavailable/);
  expect(group.open).toBe(true);
});

it('reveals a failed per-run export through its parent callback', async () => {
  let reject: (reason: Error) => void = () => {};
  vi.spyOn(globalThis, 'fetch').mockImplementation(() => new Promise((_, fail) => { reject = fail; }));
  const disclosure = createRef<HTMLDetailsElement>();
  render(<details open ref={disclosure}><summary>Saved tools</summary><SavedExport evaluationId="RUN" onError={() => { disclosure.current!.open = true; }} /></details>);
  fireEvent.click(screen.getByRole('button', { name: 'Download JSON' }));
  disclosure.current!.open = false;
  reject(new Error('SYNTHETIC saved export unavailable'));
  await screen.findByText(/The backend is unavailable/);
  expect(disclosure.current!.open).toBe(true);
});

it('does not reveal obsolete export failures after another run is selected', async () => {
  let reject: (reason: Error) => void = () => {};
  vi.spyOn(globalThis, 'fetch').mockImplementation(() => new Promise((_, fail) => { reject = fail; }));
  const onError = vi.fn();
  const view = render(<SavedExport evaluationId="OLD" onError={onError} />);
  fireEvent.click(screen.getByRole('button', { name: 'Download JSON' }));
  view.rerender(<SavedExport evaluationId="NEW" onError={onError} />);
  reject(new Error('SYNTHETIC obsolete failure'));
  await waitFor(() => expect((screen.getByRole('button', { name: 'Download JSON' }) as HTMLButtonElement).disabled).toBe(false));
  expect(onError).not.toHaveBeenCalled();
  expect(screen.queryByRole('alert')).toBeNull();
});

it('distinguishes a pending or failed priority view from an empty queue and can return to normal rows', async () => {
  let reject: (reason: Error) => void = () => {};
  const fetch = vi.spyOn(globalThis, 'fetch').mockImplementation(() => new Promise((_, fail) => { reject = fail; }));
  render(<Conversations {...props} />);
  const group = document.querySelector<HTMLDetailsElement>('.review-priority')!;
  group.open = true;
  fireEvent.change(screen.getByLabelText('Review priority reason'), { target: { value: 'needs_review' } });
  group.open = false;
  expect(screen.getByText('Loading priority view…')).toBeDefined();
  expect(screen.queryByText('No conversations match these filters.')).toBeNull();
  await waitFor(() => expect(fetch).toHaveBeenCalledOnce());
  reject(new Error('SYNTHETIC priority outage'));
  await screen.findByText(/Priority view unavailable/);
  expect(screen.queryByText('No conversations match these filters.')).toBeNull();
  fireEvent.click(screen.getByRole('button', { name: 'Show normal queue' }));
  expect(screen.getByRole('link', { name: 'TEST_KZ' })).toBeDefined();
  expect(screen.queryByText(/Priority view unavailable/)).toBeNull();
});

it('focuses breakdown cases after opening and returns focus to their source bucket on close', async () => {
  const packet = { checklist_id: 1, checklist_hash: 'TEST', basis: 'effective', total_sources: rows.length, selection_policy: 'SYNTHETIC TEST',
    manifest: rows.map(row => ({ conversation_id: row.id, content_hash: row.content_hash, evaluation_id: row.evaluation!.id, updated_at: '', state: 'succeeded' })),
    groups: [{ group_id: 'DEV', total_sources: rows.length, coverage: { complete: rows.length }, criteria: [{ criterion_id: 'contact', name: 'Contact', answer_type: 'binary', weight: '10', assessed_count: rows.length,
      buckets: [{ key: 'yes', label: 'Yes', count: rows.length, denominator: rows.length, percentage: '100.00', cases: rows.map(row => ({ conversation_id: row.id, source_id: row.source_id, group_id: row.group_id, revision: 1, evaluation_id: row.evaluation!.id, criterion_id: 'contact' })) }] }] }] };
  vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify(packet)));
  render(<CriterionBreakdown rows={rows} checklistId={1} />);
  const disclosure = document.querySelector<HTMLDetailsElement>('.criterion-breakdowns')!;
  disclosure.open = true; fireEvent(disclosure, new Event('toggle'));
  const bucket = await screen.findByRole('button', { name: 'Inspect DEV: Contact: Yes' });
  fireEvent.click(bucket);
  expect(document.activeElement).toBe(screen.getByRole('region', { name: 'Breakdown cases' }));
  fireEvent.click(screen.getByRole('button', { name: 'Close cases' }));
  expect(document.activeElement).toBe(bucket);
});
