// @vitest-environment happy-dom
// Regression coverage for result identity, selection and late responses.
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import Detail from './Detail';
import App from './App';
import type { ChecklistVersion, Conversation, ConversationDetail, EvaluationDetail } from './types';

beforeEach(() => { sessionStorage.clear(); localStorage.clear(); location.hash = '#conversations'; });
afterEach(() => { cleanup(); vi.restoreAllMocks(); vi.useRealTimers(); sessionStorage.clear(); localStorage.clear(); });

const rubric: ChecklistVersion = { id: 1, content_hash: 'SYNTHETIC_RUBRIC', created_at: '2026-11-07T00:00:00Z', snapshot: {
  schema_version: 1, name: 'SYNTHETIC audit rule', initial_version_label: null, source: null, source_notes: [], scoring_policy: {},
  sections: [{ id: 'audit', title: 'SYNTHETIC audit section' }], criteria: [{ id: 'audit_rule', name: 'SYNTHETIC criterion',
    description: 'The operator writes AUDIT.', section_id: 'audit', answer_type: 'binary', weight: 1,
    na_allowed: false, na_condition: null, scale: [] }],
} };
const summaries = ['RUN_A', 'RUN_B'].map(id => ({ id, conversation_id: 'SYNTHETIC_CONV', checklist_id: 1,
  state: 'succeeded' as const, completeness: 'complete', total: '100.00', error: null, cached_from: null,
  created_at: '2026-11-07T00:00:00Z', updated_at: '2026-11-07T00:00:00Z' }));
const conversation: ConversationDetail = { id: 'SYNTHETIC_CONV', group_id: 'SYNTHETIC_AUDIT_ONLY', source_id: 'SYNTHETIC_SOURCE',
  revision: 1, content_hash: 'SYNTHETIC_CONTENT', evaluations: summaries,
  snapshot: { language: 'EN', channel: 'agent chat', audio_url: null,
    transcript: [{ id: 'm0001', timestamp: '00:00', speaker: 'operator', text: 'SYNTHETIC AUDIT.' }] } };
function saved(id: string, explanation: string): EvaluationDetail {
  const judgment = { disposition: 'assessed' as const, value: true, explanation, na_reason: null, review_reason: null,
    evidence: [{ kind: 'support' as const, start_message_id: 'm0001', end_message_id: 'm0001' }] };
  const assessment = { results: { audit_rule: judgment } };
  const calculated = { total: '100.00', reason: null, completeness: 'complete', applicable_weight: '1', raw_subtotal: '1',
    flags: {}, criteria: [{ criterion_id: 'audit_rule', weight: '1', raw_points: '1', normalized_contribution: '100' }],
    sections: [{ id: 'audit', title: 'SYNTHETIC audit section', total: '100.00', reason: null }] };
  return { ...summaries.find(r => r.id === id)!, original: assessment, effective: assessment,
    original_score: calculated, effective_score: calculated, checklist: rubric,
    metadata: { provider: 'SYNTHETIC', model: 'SYNTHETIC', mode: 'TEST/MOCK', prompt_version: 'SYNTHETIC' },
    usage: { request_attempts: 0, input_tokens_known: 0, output_tokens_known: 0, usage_complete: false,
      estimated_cost_usd: null, cost_rate_source: null, latency_ms: 0 }, attempts: [], appeals: [], reviews: [] };
}
const props = { id: conversation.id, initialEvaluation: 'RUN_A', selectedVersion: 1, busy: false,
  run: async (action: () => Promise<void>) => { await action(); }, providerReady: false,
  evaluate: async () => {}, onChange: async () => {} };
const json = (value: unknown) => new Response(JSON.stringify(value), { headers: { 'Content-Type': 'application/json' } });
function deferred() {
  let resolve!: (value: Response) => void;
  const promise = new Promise<Response>(r => { resolve = r; });
  return { promise, resolve };
}

it('keeps the newly selected saved run when an older assessment finishes late', async () => {
  const older = deferred(); const newer = deferred(); let aCalls = 0;
  const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(async url => {
    const path = String(url).replace(/\?history_limit=25$/, '');
    if (path === '/api/conversations/SYNTHETIC_CONV') return json(conversation);
    if (path === '/api/evaluations/RUN_A') return ++aCalls === 1 ? older.promise : json(saved('RUN_A', 'SYNTHETIC older assessment'));
    if (path === '/api/evaluations/RUN_B') return newer.promise;
    throw new Error(`Unexpected request: ${path}`);
  });
  render(<Detail {...props} />);
  const selector = await screen.findByRole('combobox', { name: 'Saved evaluation' });
  await waitFor(() => expect(aCalls).toBe(1));
  fireEvent.change(selector, { target: { value: 'RUN_B' } });
  await waitFor(() => expect(fetchMock.mock.calls.some(c => String(c[0]) === '/api/evaluations/RUN_B')).toBe(true));
  await act(async () => { newer.resolve(json(saved('RUN_B', 'SYNTHETIC newly selected assessment'))); });
  await screen.findByText('SYNTHETIC newly selected assessment');
  expect((selector as HTMLSelectElement).value).toBe('RUN_B');
  await act(async () => { older.resolve(json(saved('RUN_A', 'SYNTHETIC older assessment'))); });
  expect((selector as HTMLSelectElement).value).toBe('RUN_B');
  expect(screen.queryByText('SYNTHETIC older assessment')).toBeNull();
  expect(screen.getByText('SYNTHETIC newly selected assessment')).toBeDefined();
});

it('ignores a late failure from a previously selected assessment', async () => {
  const older = deferred();
  vi.spyOn(globalThis, 'fetch').mockImplementation(async url => {
    if (String(url).split('?')[0] === '/api/conversations/SYNTHETIC_CONV') return json(conversation);
    if (String(url) === '/api/evaluations/RUN_A') return older.promise;
    if (String(url) === '/api/evaluations/RUN_B') return json(saved('RUN_B', 'SYNTHETIC current answer'));
    throw new Error(`Unexpected request: ${String(url)}`);
  });
  render(<Detail {...props} />);
  fireEvent.change(await screen.findByRole('combobox', { name: 'Saved evaluation' }), { target: { value: 'RUN_B' } });
  await screen.findByText('SYNTHETIC current answer');
  await act(async () => { older.resolve(new Response(JSON.stringify({ detail: 'SYNTHETIC obsolete error' }), { status: 503 })); });
  expect(screen.queryByText('SYNTHETIC obsolete error')).toBeNull();
  expect(screen.getByText('SYNTHETIC current answer')).toBeDefined();
});

it('ignores the first A response after selecting A, B and A again', async () => {
  const older = deferred(); const middle = deferred(); let aCalls = 0;
  vi.spyOn(globalThis, 'fetch').mockImplementation(async url => {
    if (String(url).split('?')[0] === '/api/conversations/SYNTHETIC_CONV') return json(conversation);
    if (String(url) === '/api/evaluations/RUN_A') return ++aCalls === 1 ? older.promise : json(saved('RUN_A', 'SYNTHETIC latest A'));
    if (String(url) === '/api/evaluations/RUN_B') return middle.promise;
    throw new Error(`Unexpected request: ${String(url)}`);
  });
  render(<Detail {...props} />);
  const selector = await screen.findByRole('combobox', { name: 'Saved evaluation' });
  await waitFor(() => expect(aCalls).toBe(1));
  fireEvent.change(selector, { target: { value: 'RUN_B' } });
  fireEvent.change(selector, { target: { value: 'RUN_A' } });
  await screen.findByText('SYNTHETIC latest A');
  await act(async () => {
    older.resolve(json(saved('RUN_A', 'SYNTHETIC obsolete first A')));
    middle.resolve(json(saved('RUN_B', 'SYNTHETIC obsolete B')));
  });
  expect(screen.getByText('SYNTHETIC latest A')).toBeDefined();
  expect(screen.queryByText('SYNTHETIC obsolete first A')).toBeNull();
  expect(screen.queryByText('SYNTHETIC obsolete B')).toBeNull();
});

it('hides a previous result when the selected load fails and retries the selected identity', async () => {
  let bCalls = 0;
  vi.spyOn(globalThis, 'fetch').mockImplementation(async url => {
    if (String(url).split('?')[0] === '/api/conversations/SYNTHETIC_CONV') return json(conversation);
    if (String(url) === '/api/evaluations/RUN_A') return json(saved('RUN_A', 'SYNTHETIC previous answer'));
    if (String(url) === '/api/evaluations/RUN_B') return ++bCalls === 1
      ? new Response(JSON.stringify({ detail: 'SYNTHETIC selected load failed' }), { status: 503 })
      : json(saved('RUN_B', 'SYNTHETIC retried answer'));
    throw new Error(`Unexpected request: ${String(url)}`);
  });
  render(<Detail {...props} />);
  await screen.findByText('SYNTHETIC previous answer');
  fireEvent.change(screen.getByRole('combobox', { name: 'Saved evaluation' }), { target: { value: 'RUN_B' } });
  await screen.findByText('SYNTHETIC selected load failed');
  expect(screen.queryByText('SYNTHETIC previous answer')).toBeNull();
  fireEvent.click(screen.getByRole('button', { name: 'Retry saved assessment' }));
  await screen.findByText('SYNTHETIC retried answer');
  expect(bCalls).toBe(2);
});

it('honors route selection changes on the mounted conversation and rejects a wrong source', async () => {
  const older = deferred();
  vi.spyOn(globalThis, 'fetch').mockImplementation(async url => {
    if (String(url).split('?')[0] === '/api/conversations/SYNTHETIC_CONV') return json(conversation);
    if (String(url) === '/api/evaluations/RUN_A') return older.promise;
    if (String(url) === '/api/evaluations/RUN_B') return json({ ...saved('RUN_B', 'SYNTHETIC wrong source'), conversation_id: 'OTHER_SOURCE' });
    throw new Error(`Unexpected request: ${String(url)}`);
  });
  const { rerender } = render(<Detail {...props} />);
  await screen.findByRole('combobox', { name: 'Saved evaluation' });
  rerender(<Detail {...props} initialEvaluation="RUN_B" />);
  await screen.findByText('Evaluation belongs to another conversation revision.');
  await act(async () => { older.resolve(json(saved('RUN_A', 'SYNTHETIC old route'))); });
  expect(screen.queryByText('SYNTHETIC old route')).toBeNull();
  expect(screen.queryByText('SYNTHETIC wrong source')).toBeNull();
  expect((screen.getByRole('combobox', { name: 'Saved evaluation' }) as HTMLSelectElement).value).toBe('RUN_B');
});

it('rejects a transcript from another revision before loading any saved assessment', async () => {
  const fetch = vi.spyOn(globalThis, 'fetch').mockResolvedValue(json({ ...conversation, id: 'OTHER_SOURCE' }));
  render(<Detail {...props} />);
  await screen.findByText('Transcript belongs to another conversation revision.');
  expect(fetch).toHaveBeenCalledTimes(1);
  expect(screen.queryByRole('combobox', { name: 'Saved evaluation' })).toBeNull();
});

it('does not publish or start another request when an assessment fails after unmount', async () => {
  const pending = deferred();
  const fetch = vi.spyOn(globalThis, 'fetch').mockImplementation(async url => {
    if (String(url).split('?')[0] === '/api/conversations/SYNTHETIC_CONV') return json(conversation);
    if (String(url) === '/api/evaluations/RUN_A') return pending.promise;
    throw new Error(`Unexpected request: ${String(url)}`);
  });
  const { unmount } = render(<Detail {...props} />);
  await waitFor(() => expect(fetch.mock.calls.some(c => String(c[0]) === '/api/evaluations/RUN_A')).toBe(true));
  unmount();
  await act(async () => { pending.resolve(new Response(JSON.stringify({ detail: 'SYNTHETIC late failure' }), { status: 503 })); });
  expect(fetch).toHaveBeenCalledTimes(2);
  expect(screen.queryByRole('alert')).toBeNull();
});

it('deduplicates a slow queue poll and manual refresh and stops polling when complete', async () => {
  vi.useFakeTimers();
  const pending = deferred(); let reads = 0;
  const row = { id: 'SYNTHETIC_POLL', group_id: 'SYNTHETIC', source_id: 'SYNTHETIC_POLL', revision: 1, content_hash: 'HASH',
    language: 'EN', channel: 'agent chat', message_count: 1, audio_available: false,
    evaluation: { ...summaries[0], conversation_id: 'SYNTHETIC_POLL', state: 'running', total: null } };
  sessionStorage.setItem('cqa-selected-version', '1');
  vi.spyOn(globalThis, 'fetch').mockImplementation(async url => {
    if (String(url) === '/api/conversations?checklist_id=1') return ++reads === 1 ? json([row]) : pending.promise;
    if (String(url) === '/api/checklists') return json([rubric]);
    if (String(url) === '/api/access') return json({ provider_configured: false, organizer_configured: false, provider_status: 'SYNTHETIC' });
    if (String(url) === '/api/budget') return json(null);
    throw new Error(`Unexpected request: ${String(url)}`);
  });
  await act(async () => { render(<App />); });
  expect(screen.getByText('SYNTHETIC_POLL')).toBeDefined();
  await act(async () => { await vi.advanceTimersByTimeAsync(2500); });
  expect(reads).toBe(2);
  fireEvent.click(screen.getByRole('button', { name: /Refresh$/ }));
  await act(async () => { await vi.advanceTimersByTimeAsync(10000); });
  expect(reads).toBe(2);
  await act(async () => { pending.resolve(json([{ ...row, evaluation: { ...row.evaluation, state: 'succeeded', total: '100.00' } }])); });
  await act(async () => { await vi.advanceTimersByTimeAsync(10000); });
  expect(reads).toBe(2);
  expect(screen.getByText('100.00')).toBeDefined();
});

it('rejects a wrong run ID even when its conversation matches', async () => {
  vi.spyOn(globalThis, 'fetch').mockImplementation(async url => {
    if (String(url).split('?')[0] === '/api/conversations/SYNTHETIC_CONV') return json(conversation);
    if (String(url) === '/api/evaluations/RUN_A') return json(saved('RUN_B', 'SYNTHETIC mismatched run payload'));
    throw new Error(`Unexpected request: ${String(url)}`);
  });
  render(<Detail {...props} />);
  await screen.findByText('Assessment does not match the selected saved run.');
  expect(screen.queryByText('SYNTHETIC mismatched run payload')).toBeNull();
  expect((screen.getByRole('combobox', { name: 'Saved evaluation' }) as HTMLSelectElement).value).toBe('RUN_A');
});

it('keeps the current checklist queue when an older refresh finishes late', async () => {
  const older = deferred(); let oldCalls = 0;
  const secondRubric = { ...rubric, id: 2, content_hash: 'SYNTHETIC_RUBRIC_2' };
  const thirdRubric = { ...rubric, id: 3, content_hash: 'SYNTHETIC_RUBRIC_3' };
  const row = (source_id: string, version: number): Conversation => ({ id: source_id, group_id: 'SYNTHETIC_AUDIT_ONLY', source_id,
    revision: 1, content_hash: source_id, language: 'EN', channel: 'agent chat', message_count: 1, audio_available: false,
    evaluation: { ...summaries[0], conversation_id: source_id, checklist_id: version } });
  sessionStorage.setItem('cqa-selected-version', '1');
  vi.spyOn(globalThis, 'fetch').mockImplementation(async url => {
    const path = String(url).replace(/\?history_limit=25$/, '');
    if (path === '/api/conversations?checklist_id=1') return json([row('SYNTHETIC_VERSION_1', 1)]);
    if (path === '/api/conversations?checklist_id=2') { oldCalls++; return older.promise; }
    if (path === '/api/conversations?checklist_id=3') return json([row('SYNTHETIC_VERSION_3', 3)]);
    if (path === '/api/checklists') return json([thirdRubric, secondRubric, rubric]);
    if (path === '/api/access') return json({ provider: 'SYNTHETIC', model: null, provider_configured: false, organizer_configured: false, provider_status: 'SYNTHETIC' });
    if (path === '/api/budget') return json(null);
    throw new Error(`Unexpected request: ${path}`);
  });
  render(<App />);
  await screen.findByText('SYNTHETIC_VERSION_1');
  const picker = screen.getByRole('combobox', { name: 'Selected checklist version' });
  fireEvent.change(picker, { target: { value: '2' } });
  await waitFor(() => expect(oldCalls).toBe(1));
  expect((picker as HTMLSelectElement).disabled).toBe(false);
  fireEvent.change(picker, { target: { value: '3' } });
  await screen.findByText('SYNTHETIC_VERSION_3');
  await act(async () => { older.resolve(json([row('SYNTHETIC_VERSION_2', 2)])); });
  expect((picker as HTMLSelectElement).value).toBe('3');
  expect(screen.queryByText('SYNTHETIC_VERSION_2')).toBeNull();
  expect(screen.getByText('SYNTHETIC_VERSION_3')).toBeDefined();
});
