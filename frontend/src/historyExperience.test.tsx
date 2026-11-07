// @vitest-environment happy-dom
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import App from './App';
import ReviewLink from './ReviewLink';
import SavedComparison from './SavedComparison';
import type { Conversation, EvaluationSummary } from './types';
import seed from '../../config/initial_checklist.json';

vi.mock('./Detail', () => ({ default: () => <section aria-label="Synthetic review"><h1>SYNTHETIC REVIEW</h1><a href="#conversations">Back to review queue</a></section> }));
let originalUrl: string;
beforeEach(() => { originalUrl = location.href; localStorage.clear(); sessionStorage.clear(); location.hash = '#conversations'; });
afterEach(() => { cleanup(); vi.restoreAllMocks(); vi.unstubAllGlobals(); localStorage.clear(); sessionStorage.clear(); history.replaceState(null, '', originalUrl); });
const json = (value: unknown) => new Response(JSON.stringify(value));

it('retains an unsaved queue view, row selection and table position when returning from review', async () => {
  const rows: Conversation[] = ['KZ', 'RU'].map(language => ({ id: language, source_id: `TEST_${language}`, group_id: 'DEV', revision: 1,
    content_hash: `HASH_${language}`, language, channel: 'agent chat', message_count: 2, audio_available: false, evaluation: null }));
  vi.spyOn(globalThis, 'fetch').mockImplementation(async url => {
    const path = String(url);
    return json(path.includes('/conversations') ? rows : path.includes('/checklists') ? [{ id: 1, content_hash: 'SYNTHETIC', snapshot: seed, created_at: '2026-11-08' }]
      : path.includes('/budget') ? { limit_usd: '0', accounted_usd: '0', reserved_usd: '0', overhead_usd: '0', available_usd: '0', ready: false }
        : { provider_configured: false, provider_status: 'Synthetic offline configuration', last_provider_check: null });
  });
  const scrolling = vi.spyOn(window, 'scrollTo').mockImplementation(() => {});
  vi.spyOn(window, 'scrollY', 'get').mockReturnValue(360);
  render(<App />);
  await screen.findByRole('link', { name: 'TEST_KZ' });
  fireEvent.change(screen.getByLabelText('Language filter'), { target: { value: 'KZ' } });
  fireEvent.change(screen.getByLabelText('Search conversation ID'), { target: { value: 'TEST_KZ' } });
  fireEvent.click(screen.getByLabelText('Select TEST_KZ'));
  const table = screen.getByRole('region', { name: 'Conversation review queue' });
  table.scrollTop = 140;
  await act(async () => { location.hash = '#conversation/KZ'; dispatchEvent(new HashChangeEvent('hashchange')); });
  expect(screen.getByRole('region', { name: 'Synthetic review' })).toBeDefined();
  expect(screen.queryByRole('link', { name: 'TEST_KZ' })).toBeNull();
  await act(async () => { location.hash = '#conversations'; dispatchEvent(new HashChangeEvent('hashchange')); });
  expect((screen.getByLabelText('Search conversation ID') as HTMLInputElement).value).toBe('TEST_KZ');
  expect((screen.getByLabelText('Language filter') as HTMLSelectElement).value).toBe('KZ');
  expect((screen.getByLabelText('Select TEST_KZ') as HTMLInputElement).checked).toBe(true);
  expect(screen.getByRole('region', { name: 'Conversation review queue' })).toBe(table);
  expect(table.scrollTop).toBe(140);
  expect(scrolling).toHaveBeenLastCalledWith({ top: 360 });
});

it('copies only the exact saved-run route and omits unrelated URL query parameters', async () => {
  history.replaceState(null, '', '/?unrelated=DO_NOT_COPY#conversations');
  const writeText = vi.fn().mockResolvedValue(undefined);
  vi.stubGlobal('navigator', { clipboard: { writeText } });
  render(<ReviewLink sourceId="SOURCE/2" evaluationId="RUN?2" />);
  fireEvent.click(screen.getByRole('button', { name: 'Copy review link' }));
  await screen.findByText('Copied link to this saved run.');
  expect(writeText).toHaveBeenCalledWith(`${location.origin}/#conversation/SOURCE%2F2?evaluation=RUN%3F2`);
  expect(writeText.mock.calls[0][0]).not.toContain('DO_NOT_COPY');
});

it('provides a focused selectable link when clipboard access is unavailable', async () => {
  vi.stubGlobal('navigator', { clipboard: { writeText: vi.fn().mockRejectedValue(new Error('Clipboard unavailable')) } });
  render(<ReviewLink sourceId="SOURCE" evaluationId="RUN" />);
  fireEvent.click(screen.getByRole('button', { name: 'Copy review link' }));
  const input = await screen.findByRole('textbox', { name: 'Review link' }) as HTMLInputElement;
  expect(document.activeElement).toBe(input);
  expect(input.selectionStart).toBe(0); expect(input.selectionEnd).toBe(input.value.length);
  expect(input.value).toContain('#conversation/SOURCE?evaluation=RUN');
});

it('ignores a late clipboard result after the selected saved run changes', async () => {
  let resolve: () => void = () => {};
  const writeText = vi.fn().mockImplementationOnce(() => new Promise<void>(done => { resolve = done; })).mockResolvedValue(undefined);
  vi.stubGlobal('navigator', { clipboard: { writeText } });
  const view = render(<ReviewLink sourceId="SOURCE" evaluationId="OLD" />);
  fireEvent.click(screen.getByRole('button', { name: 'Copy review link' }));
  view.rerender(<ReviewLink sourceId="SOURCE" evaluationId="NEW" />);
  await act(async () => resolve());
  expect(screen.queryByText('Copied link to this saved run.')).toBeNull();
  fireEvent.click(screen.getByRole('button', { name: 'Copy review link' }));
  await screen.findByText('Copied link to this saved run.');
  expect(writeText.mock.calls[1][0]).toContain('evaluation=NEW');
});

it.each([true, false])('chooses a genuinely earlier comparison baseline using the history key order (identical times: %s)', sameTime => {
  const summary = (id: string, fraction: string): EvaluationSummary => ({ id, conversation_id: 'SOURCE', checklist_id: 1, state: 'succeeded', completeness: 'complete',
    total: '100', error: null, cached_from: null, created_at: `2026-11-08T00:00:00.${fraction}+00:00`, updated_at: '' });
  const runs = [summary('Z', sameTime ? '000200' : '000900'), summary('L', sameTime ? '000200' : '000100'), summary('M', '000200')];
  vi.spyOn(globalThis, 'fetch').mockImplementation(() => new Promise(() => {}));
  render(<SavedComparison runs={runs} currentId="M" sourceId="SOURCE" onEvidence={vi.fn()} />);
  fireEvent.click(screen.getByRole('button', { name: 'Compare saved runs' }));
  expect((screen.getByLabelText('Baseline saved run') as HTMLSelectElement).value).toBe('L');
  expect((screen.getByLabelText('Comparison saved run') as HTMLSelectElement).value).toBe('M');
});
