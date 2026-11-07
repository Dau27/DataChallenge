// @vitest-environment happy-dom
import { afterEach, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import TranscriptMatches from './TranscriptMatches';
import type { Conversation, TranscriptMatch } from './types';

afterEach(() => { cleanup(); vi.restoreAllMocks(); });
const match = (n: number): TranscriptMatch => ({ id: `m${String(n).padStart(4, '0')}`, speaker: 'operator', timestamp: '00:00', snippet: '👋 И\u0306 original source', highlights: [{ start: 2, end: 4 }] });
const row: Conversation = { id: 'SOURCE', source_id: 'TEST_ONLY', content_hash: 'HASH', group_id: 'DEV', revision: 1, language: 'RU', channel: 'agent chat', message_count: 8, audio_available: false, evaluation: null,
  search_matches: [1, 2, 3, 4, 5].map(match), search_total_matches: 8 };
const page = (matches = [6, 7, 8].map(match)) => ({ source: { id: row.id, content_hash: row.content_hash }, query: 'й', speaker: 'operator', offset: 5, limit: 5, total_matches: 8, matches });

it('highlights original Unicode text and pages every matching message with exact links', async () => {
  const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify(page())));
  const view = render(<TranscriptMatches row={row} query="й" speaker="operator" />);
  expect(view.container.querySelector('mark')?.textContent).toBe('И\u0306');
  expect(fetchMock).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole('button', { name: 'Next matches for TEST_ONLY' }));
  await screen.findByText('6–8 of 8 matching message(s)');
  expect(screen.getByRole('link', { name: 'm0006 · operator · 00:00' }).getAttribute('href')).toBe('#conversation/SOURCE?message=m0006');
  expect((screen.getByRole('button', { name: 'Next matches for TEST_ONLY' }) as HTMLButtonElement).disabled).toBe(true);
  expect(fetchMock.mock.calls[0][0]).toBe('/api/conversations/SOURCE/matches?q=%D0%B9&speaker=operator&offset=5&limit=5');
  fireEvent.click(screen.getByRole('button', { name: 'Previous matches for TEST_ONLY' }));
  expect(screen.getByText('1–5 of 8 matching message(s)')).toBeDefined();
  expect(fetchMock).toHaveBeenCalledTimes(1);
});

it('hides unavailable pages, retries and ignores late pages after returning to initial matches', async () => {
  let release: ((response: Response) => void) | undefined;
  vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(new Response(JSON.stringify({ detail: 'Page read failed' }), { status: 500 }))
    .mockImplementationOnce(() => new Promise(resolve => { release = resolve; }));
  render(<TranscriptMatches row={row} query="й" speaker="operator" />);
  fireEvent.click(screen.getByRole('button', { name: 'Next matches for TEST_ONLY' }));
  await screen.findByText('Page read failed');
  expect(screen.queryByRole('link', { name: 'm0001 · operator · 00:00' })).toBeNull();
  fireEvent.click(screen.getByRole('button', { name: 'Retry match page' }));
  await waitFor(() => expect(release).toBeDefined());
  fireEvent.click(screen.getByRole('button', { name: 'Previous matches for TEST_ONLY' }));
  release!(new Response(JSON.stringify(page())));
  await screen.findByText('1–5 of 8 matching message(s)');
  expect(screen.queryByRole('link', { name: 'm0006 · operator · 00:00' })).toBeNull();
});

it('rejects a page from another source revision', async () => {
  vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({ ...page(), source: { id: row.id, content_hash: 'OTHER' } })));
  render(<TranscriptMatches row={row} query="й" speaker="operator" />);
  fireEvent.click(screen.getByRole('button', { name: 'Next matches for TEST_ONLY' }));
  await screen.findByText(/different source or query/);
  expect(screen.queryByRole('link', { name: 'm0006 · operator · 00:00' })).toBeNull();
});
