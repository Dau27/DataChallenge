// @vitest-environment happy-dom
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import Conversations from './Conversations';
import type { Conversation } from './types';

beforeEach(() => { localStorage.clear(); sessionStorage.clear(); });
afterEach(() => { cleanup(); vi.restoreAllMocks(); localStorage.clear(); sessionStorage.clear(); });
const row = (id: string, language: string, saved = true): Conversation => ({ id, source_id: `TEST_${id}`, content_hash: `HASH_${id}`, group_id: 'DEV', revision: 1,
  language, channel: 'agent chat', message_count: 2, audio_available: false, evaluation: saved ? { id: `RUN_${id}`, conversation_id: id, checklist_id: 1,
    state: 'succeeded', completeness: 'complete', total: '100.00', error: null, cached_from: null, created_at: '', updated_at: '' } : null });
const rows = [row('KZ', 'KZ'), row('RU', 'RU'), row('NEW', 'EN', false)];
const props = { rows, access: null, selectedVersion: 1, completed: 2, needsReview: 0, busy: false, run: async (action: () => Promise<void>) => { await action(); },
  evaluate: vi.fn(), refresh: vi.fn(), notify: vi.fn() };

it('exports only currently visible selected saved runs, excluding hidden and unstarted rows', async () => {
  const click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});
  vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:TEST'); vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => {});
  const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response('{}'));
  render(<Conversations {...props} />);
  fireEvent.click(screen.getByLabelText('Select all visible conversations'));
  fireEvent.change(screen.getByLabelText('Language filter'), { target: { value: 'KZ' } });
  const controls = within(screen.getByRole('region', { name: 'Selected saved-run export' }));
  fireEvent.click(controls.getByRole('button', { name: 'Selected JSON' }));
  await waitFor(() => expect(click).toHaveBeenCalledOnce());
  const request = new URL(String(fetchMock.mock.calls[0][0]), 'http://test.invalid');
  expect(request.pathname).toBe('/api/evaluations/export-batch');
  expect(request.searchParams.getAll('evaluation_id')).toEqual(['RUN_KZ']);
  fireEvent.change(screen.getByLabelText('Language filter'), { target: { value: 'EN' } });
  expect((controls.getByRole('button', { name: 'Selected JSON' }) as HTMLButtonElement).disabled).toBe(true);
  expect(fetchMock).toHaveBeenCalledTimes(1);
});

it('disables selected exports while text search is pending rather than using stale selected rows', async () => {
  let release: ((response: Response) => void) | undefined;
  vi.spyOn(globalThis, 'fetch').mockImplementation(() => new Promise(resolve => { release = resolve; }));
  render(<Conversations {...props} />);
  fireEvent.click(screen.getByLabelText('Select TEST_KZ'));
  fireEvent.change(screen.getByLabelText('Search transcript text'), { target: { value: 'source' } });
  const button = within(screen.getByRole('region', { name: 'Selected saved-run export' })).getByRole('button', { name: 'Selected JSON' });
  expect((button as HTMLButtonElement).disabled).toBe(true);
  await waitFor(() => expect(release).toBeDefined()); release!(new Response('[]'));
  await screen.findByText('No conversations match these filters.');
  expect((button as HTMLButtonElement).disabled).toBe(true);
});
