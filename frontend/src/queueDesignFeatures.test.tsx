// @vitest-environment happy-dom
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, within } from '@testing-library/react';
import Conversations from './Conversations';
import type { Conversation } from './types';

beforeEach(() => { localStorage.clear(); sessionStorage.clear(); });
afterEach(() => { cleanup(); vi.restoreAllMocks(); vi.unstubAllGlobals(); localStorage.clear(); sessionStorage.clear(); });
const row = (id: string, language: string, needsReview = false, pending = 0, flagged = false): Conversation => ({ id, source_id: `TEST_${id}`, group_id: id === 'OTHER' ? 'OTHER' : 'DEV', revision: 1, content_hash: `HASH_${id}`,
  language, channel: 'agent chat', message_count: 2, audio_available: false, pending_appeals: pending,
  critical_findings: flagged ? [{ evaluation_id: `RUN_${id}`, criterion_id: 'flag', criterion_name: 'Flag' }] : [],
  evaluation: { id: `RUN_${id}`, conversation_id: id, checklist_id: 1, state: 'succeeded', completeness: needsReview ? 'needs_review' : 'complete', total: needsReview ? null : '100.00', error: null, cached_from: null, created_at: '', updated_at: '' } });
const rows = [row('KZ_DONE', 'KZ'), row('KZ_REVIEW', 'KZ', true, 2), row('RU_REVIEW', 'RU', true, 1, true), row('OTHER', 'KZ', true, 1, true)];
const props = { rows, access: null, selectedVersion: 1, completed: 1, needsReview: 3, busy: false,
  run: async (action: () => Promise<void>) => { await action(); }, evaluate: vi.fn(), refresh: vi.fn(), notify: vi.fn() };

it('counts quick views within current source filters and changes only the review filters', () => {
  const fetch = vi.spyOn(globalThis, 'fetch');
  render(<Conversations {...props} />);
  fireEvent.change(screen.getByLabelText('Dataset filter'), { target: { value: 'DEV' } });
  fireEvent.change(screen.getByLabelText('Language filter'), { target: { value: 'KZ' } });
  const views = within(screen.getByRole('group', { name: 'Quick review views' }));
  expect(views.getByRole('button', { name: 'All in view 2' })).toBeDefined();
  expect(views.getByRole('button', { name: 'Needs review 1' })).toBeDefined();
  fireEvent.click(views.getByRole('button', { name: 'Critical findings 0' }));
  expect(screen.getByText('No conversations match these filters.')).toBeDefined();
  fireEvent.click(views.getByRole('button', { name: 'Pending appeals 1' }));
  expect((screen.getByLabelText('Status filter') as HTMLSelectElement).value).toBe('');
  expect((screen.getByLabelText('Critical findings filter') as HTMLSelectElement).value).toBe('');
  expect((screen.getByLabelText('Pending appeals filter') as HTMLSelectElement).value).toBe('pending');
  expect(screen.getByRole('link', { name: 'TEST_KZ_REVIEW' })).toBeDefined();
  expect(screen.queryByRole('link', { name: 'TEST_KZ_DONE' })).toBeNull();
  fireEvent.click(views.getByRole('button', { name: 'All in view 2' }));
  expect((screen.getByLabelText('Dataset filter') as HTMLSelectElement).value).toBe('DEV');
  expect((screen.getByLabelText('Language filter') as HTMLSelectElement).value).toBe('KZ');
  expect(screen.getByRole('link', { name: 'TEST_KZ_DONE' })).toBeDefined();
  expect(fetch).not.toHaveBeenCalled();
});

it('removes only the chosen chip and preserves literal underscores in the search label', () => {
  render(<Conversations {...props} />);
  fireEvent.change(screen.getByLabelText('Dataset filter'), { target: { value: 'DEV' } });
  fireEvent.change(screen.getByLabelText('Language filter'), { target: { value: 'KZ' } });
  fireEvent.change(screen.getByLabelText('Search conversation ID'), { target: { value: 'CASE_A_B' } });
  const chips = within(screen.getByRole('group', { name: 'Applied filters' }));
  expect(chips.getByText('CASE_A_B')).toBeDefined();
  fireEvent.click(chips.getByRole('button', { name: 'Remove language filter' }));
  expect((screen.getByLabelText('Language filter') as HTMLSelectElement).value).toBe('');
  expect((screen.getByLabelText('Dataset filter') as HTMLSelectElement).value).toBe('DEV');
  expect((screen.getByLabelText('Search conversation ID') as HTMLInputElement).value).toBe('CASE_A_B');
});

it('retains compact layout after remount without changing selected rows, filters, or saved results', () => {
  const before = structuredClone(rows);
  const view = render(<Conversations {...props} />);
  fireEvent.click(screen.getByLabelText('Select TEST_KZ_DONE'));
  fireEvent.change(screen.getByLabelText('Language filter'), { target: { value: 'KZ' } });
  fireEvent.change(screen.getByLabelText('Queue row spacing'), { target: { value: 'compact' } });
  expect(document.querySelector('.table-panel')?.getAttribute('data-density')).toBe('compact');
  expect((screen.getByLabelText('Select TEST_KZ_DONE') as HTMLInputElement).checked).toBe(true);
  expect((screen.getByLabelText('Language filter') as HTMLSelectElement).value).toBe('KZ');
  expect(rows).toEqual(before);
  view.unmount(); render(<Conversations {...props} />);
  expect((screen.getByLabelText('Queue row spacing') as HTMLSelectElement).value).toBe('compact');
});

it('keeps row spacing usable when browser storage is unavailable', () => {
  const blocked = () => { throw new Error('Storage blocked'); };
  vi.stubGlobal('localStorage', { getItem: blocked, setItem: blocked, removeItem: blocked, clear: () => {} });
  render(<Conversations {...props} />);
  expect((screen.getByLabelText('Queue row spacing') as HTMLSelectElement).value).toBe('comfortable');
  fireEvent.change(screen.getByLabelText('Queue row spacing'), { target: { value: 'compact' } });
  expect(document.querySelector('.table-panel')?.getAttribute('data-density')).toBe('compact');
  expect(screen.getByRole('link', { name: 'TEST_KZ_DONE' })).toBeDefined();
});

it('withholds quick-view counts while transcript matching is pending and allows the search chip to cancel', async () => {
  let release: ((value: Response) => void) | undefined;
  vi.spyOn(globalThis, 'fetch').mockImplementation(() => new Promise(resolve => { release = resolve; }));
  render(<Conversations {...props} />);
  fireEvent.change(screen.getByLabelText('Search transcript text'), { target: { value: 'pending search' } });
  const views = within(screen.getByRole('group', { name: 'Quick review views' }));
  expect((views.getByRole('button', { name: 'All in view —' }) as HTMLButtonElement).disabled).toBe(true);
  fireEvent.click(screen.getByRole('button', { name: 'Remove transcript filter' }));
  expect((views.getByRole('button', { name: 'All in view 4' }) as HTMLButtonElement).disabled).toBe(false);
  expect(screen.getByRole('link', { name: 'TEST_RU_REVIEW' })).toBeDefined();
  release?.(new Response('[]'));
});
