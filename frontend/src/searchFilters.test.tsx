// @vitest-environment happy-dom
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import Conversations from './Conversations';
import Detail from './Detail';
import type { Conversation, ConversationDetail } from './types';

beforeEach(() => { localStorage.clear(); sessionStorage.clear(); });
afterEach(() => { cleanup(); vi.restoreAllMocks(); vi.unstubAllGlobals(); localStorage.clear(); sessionStorage.clear(); });
const row = (id: string, language = 'KZ'): Conversation => ({ id, source_id: `TEST_${id}`, content_hash: `HASH_${id}`, group_id: 'DEV', revision: 2,
  language, channel: 'agent chat', message_count: 3, audio_available: false, pending_appeals: 1, critical_findings: [{ evaluation_id: 'RUN', criterion_id: 'flag', criterion_name: 'Flag' }],
  evaluation: { id: 'RUN', conversation_id: id, checklist_id: 1, state: 'succeeded', completeness: 'complete', total: '100', error: null, cached_from: null, created_at: '', updated_at: '' } });
const rows = [row('KZ'), row('RU', 'RU')];
const props = { rows, access: null, selectedVersion: 1, completed: 2, needsReview: 0, busy: false, run: async (action: () => Promise<void>) => { await action(); },
  evaluate: vi.fn(), refresh: vi.fn(), notify: vi.fn() };
const hits = () => rows.map(r => ({ ...r, search_total_matches: 1, search_matches: [{ id: 'm0002', speaker: 'operator', timestamp: '00:01', snippet: `${r.language} source excerpt` }] }));

it('combines text, speaker and queue filters, saves/restores exact checklist-scoped presets and deletes only the preset', async () => {
  const urls: string[] = [];
  vi.spyOn(globalThis, 'fetch').mockImplementation(async (url, options) => {
    urls.push(String(url)); expect(options).toBeUndefined(); return new Response(JSON.stringify(hits()));
  });
  const view = render(<Conversations {...props} />);
  fireEvent.change(screen.getByLabelText('Search transcript text'), { target: { value: 'source' } });
  fireEvent.change(screen.getByLabelText('Transcript speaker filter'), { target: { value: 'operator' } });
  fireEvent.change(screen.getByLabelText('Language filter'), { target: { value: 'KZ' } });
  fireEvent.change(screen.getByLabelText('Pending appeals filter'), { target: { value: 'pending' } });
  fireEvent.change(screen.getByLabelText('Critical findings filter'), { target: { value: 'flagged' } });
  expect(screen.queryByText('No conversations match these filters.')).toBeNull();
  await screen.findByText('KZ source excerpt');
  expect(screen.queryByText('RU source excerpt')).toBeNull();
  expect(screen.getByRole('link', { name: 'm0002 · operator · 00:01' }).getAttribute('href')).toBe('#conversation/KZ?message=m0002&evaluation=RUN');
  expect(urls.at(-1)).toContain('q=source&speaker=operator');
  fireEvent.change(screen.getByLabelText('Filter preset name'), { target: { value: 'KZ pending' } });
  fireEvent.click(screen.getByRole('button', { name: 'Save filters' }));
  fireEvent.change(screen.getByLabelText('Language filter'), { target: { value: 'RU' } });
  expect(screen.getByText('Unsaved filter changes')).toBeDefined();
  view.unmount();
  const restored = render(<Conversations {...props} />);
  expect((screen.getByLabelText('Language filter') as HTMLSelectElement).value).toBe('KZ');
  expect((screen.getByLabelText('Search transcript text') as HTMLInputElement).value).toBe('source');
  expect((screen.getByLabelText('Filter preset name') as HTMLInputElement).value).toBe('KZ pending');
  await screen.findByText('KZ source excerpt');
  restored.rerender(<Conversations {...props} selectedVersion={2} />);
  await waitFor(() => expect((screen.getByLabelText('Search transcript text') as HTMLInputElement).value).toBe(''));
  expect(screen.queryByRole('option', { name: 'KZ pending' })).toBeNull();
  restored.rerender(<Conversations {...props} />);
  await screen.findByText('KZ source excerpt');
  fireEvent.click(screen.getByRole('button', { name: 'Delete saved filters' }));
  expect((screen.getByLabelText('Search transcript text') as HTMLInputElement).value).toBe('');
  expect(JSON.parse(localStorage.getItem('cqa-filter-presets-v2')!).presets).toEqual([]);
  expect(rows).toHaveLength(2);
  expect(urls.every(u => u.startsWith('/api/conversations?'))).toBe(true);
});

it('ignores late search responses, blocks stale selection while pending/error and distinguishes errors from no matches', async () => {
  let release: ((response: Response) => void) | undefined;
  const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementationOnce(() => new Promise(resolve => { release = resolve; }))
    .mockResolvedValueOnce(new Response(JSON.stringify({ detail: 'Search read failed' }), { status: 500 }))
    .mockResolvedValue(new Response('[]'));
  render(<Conversations {...props} />);
  fireEvent.click(screen.getByLabelText('Select TEST_KZ'));
  fireEvent.change(screen.getByLabelText('Search transcript text'), { target: { value: 'first' } });
  expect(screen.queryByLabelText('Select TEST_KZ')).toBeNull();
  expect((screen.getByRole('button', { name: /Evaluate selected/ }) as HTMLButtonElement).disabled).toBe(true);
  await waitFor(() => expect(release).toBeDefined());
  fireEvent.change(screen.getByLabelText('Search transcript text'), { target: { value: 'second' } });
  await screen.findByText('Search read failed');
  expect(screen.queryByText('No conversations match these filters.')).toBeNull();
  release!(new Response(JSON.stringify(hits())));
  expect(screen.queryByText('KZ source excerpt')).toBeNull();
  fireEvent.click(screen.getByRole('button', { name: 'Retry transcript search' }));
  await screen.findByText('No conversations match these filters.');
  expect(fetchMock).toHaveBeenCalledTimes(3);
});

it.each(['{broken', '{"schema_version":1,"presets":[{"id":"bad","name":"Bad","checklist_id":1,"filters":{}}]}'])('handles invalid saved presets without applying partial filters (%s)', value => {
  localStorage.setItem('cqa-filter-presets-v1', value);
  render(<Conversations {...props} />);
  expect(screen.getByRole('alert').textContent).toContain('could not be restored');
  expect(screen.getByRole('link', { name: 'TEST_KZ' })).toBeDefined();
  fireEvent.change(screen.getByLabelText('Language filter'), { target: { value: 'RU' } });
  expect(screen.queryByRole('link', { name: 'TEST_KZ' })).toBeNull();
});

it('keeps filters functional when browser storage is blocked and reports save failure', () => {
  const blocked = () => { throw new Error('Storage blocked'); };
  vi.stubGlobal('localStorage', { getItem: blocked, setItem: blocked, removeItem: blocked });
  render(<Conversations {...props} />);
  expect(screen.getByRole('alert').textContent).toContain('could not be restored');
  expect(screen.getByRole('link', { name: 'TEST_KZ' })).toBeDefined();
  fireEvent.change(screen.getByLabelText('Filter preset name'), { target: { value: 'Test' } });
  fireEvent.click(screen.getByRole('button', { name: 'Save filters' }));
  expect(screen.getByRole('alert').textContent).toContain('was not saved');
});

it('reports a changed source revision instead of showing stale snippets', async () => {
  vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify([{ ...hits()[0], content_hash: 'OTHER' }])));
  render(<Conversations {...props} />);
  fireEvent.change(screen.getByLabelText('Search transcript text'), { target: { value: 'source' } });
  await screen.findByText(/Source revisions changed/);
  expect(screen.queryByText('KZ source excerpt')).toBeNull();
  expect(screen.queryByText('No conversations match these filters.')).toBeNull();
});

it.each(['m0002', 'missing'])('opens the exact transcript message or explains its absence (%s)', async target => {
  const conversation: ConversationDetail = { id: 'SOURCE', source_id: 'TEST_ONLY', content_hash: 'HASH', group_id: 'DEV', revision: 2, evaluations: [],
    snapshot: { language: 'EN', channel: 'agent chat', audio_url: null, transcript: [
      { id: 'm0001', speaker: 'client', timestamp: '00:00', text: 'First source message' },
      { id: 'm0002', speaker: 'operator', timestamp: '00:01', text: 'Second source message' }] } };
  vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify(conversation)));
  render(<Detail id="SOURCE" initialEvaluation={null} initialMessage={target} selectedVersion={1} busy={false} run={props.run} providerReady={false} evaluate={props.evaluate} onChange={props.refresh} />);
  await screen.findByText('Second source message');
  if (target === 'missing') {
    await screen.findByText('The linked message is unavailable in this source revision.');
    expect(document.querySelector('.message.highlighted')).toBeNull();
  } else {
    await waitFor(() => expect(document.querySelector('.message.highlighted')?.id).toBe('message-m0002'));
    expect(document.activeElement?.id).toBe('message-m0002');
  }
});
