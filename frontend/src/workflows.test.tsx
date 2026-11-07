// @vitest-environment happy-dom
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import ChecklistEditor from './ChecklistEditor';
import ReviewForm from './ReviewForm';
import Detail from './Detail';
import type { Checklist, ChecklistVersion, ConversationDetail, EvaluationDetail, Judgment, Message } from './types';
import seed from '../../config/initial_checklist.json';

beforeEach(() => sessionStorage.clear());
afterEach(() => { cleanup(); vi.restoreAllMocks(); sessionStorage.clear(); });

it.each(['https://example.test/recording/player?id=SYNTHETIC', null])('uses the source player link or transcript fallback for a call, without treating HTML as audio (%s)', async audioUrl => {
  const conversation: ConversationDetail = { id: 'TEST_CALL', source_id: 'SYNTHETIC_CALL', group_id: 'TEST_ONLY', revision: 1, content_hash: 'TEST_HASH', evaluations: [],
    snapshot: { language: 'EN', channel: 'voice call', audio_url: audioUrl,
      transcript: [{ id: 'm0001', speaker: 'operator', timestamp: '00:00', text: 'SYNTHETIC call transcript' }] } };
  vi.spyOn(globalThis, 'fetch').mockImplementation(async () => new Response(JSON.stringify(conversation)));
  const { container } = render(<Detail id={conversation.id} initialEvaluation={null} selectedVersion={1} busy={false} run={async action => { await action(); }} providerReady={false} evaluate={async () => {}} onChange={async () => {}} />);
  await screen.findByText('SYNTHETIC call transcript');
  expect(container.querySelector('audio')).toBeNull();
  if (audioUrl) {
    const link = screen.getByRole('link', { name: /Open recording/ });
    expect(link.getAttribute('href')).toBe(audioUrl);
    expect(link.getAttribute('target')).toBe('_blank');
    expect(link.getAttribute('rel')).toBe('noreferrer');
  } else {
    expect(screen.queryByRole('link', { name: /Open recording/ })).toBeNull();
    expect(screen.getByText(/Recording unavailable/)).toBeDefined();
  }
});

it('adds a genuinely new criterion through the editor and saves a complete new snapshot', async () => {
  const original = structuredClone(seed) as Checklist;
  const version: ChecklistVersion = { id: 1, snapshot: original, content_hash: 'SYNTHETIC_TEST_HASH', created_at: '2026-11-01T00:00:00Z' };
  const onSave = vi.fn(async () => {});
  const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(async url => new Response(JSON.stringify(
    String(url).endsWith('/preview') ? { valid: true, errors: [], changes: [] } : { ...version, id: 2 }), { status: String(url).endsWith('/preview') ? 200 : 201 }));
  render(<ChecklistEditor version={version} versions={[version]} busy={false} run={async action => { await action(); }} onSave={onSave} />);
  fireEvent.click(screen.getByRole('button', { name: /Add a criterion/ }));
  const names = screen.getAllByLabelText('Name');
  fireEvent.change(names[names.length - 1], { target: { value: 'SYNTHETIC: ticket reference' } });
  const definitions = screen.getAllByLabelText('Criterion definition');
  fireEvent.change(definitions[definitions.length - 1], { target: { value: 'The operator states a ticket reference before closing.' } });
  await waitFor(() => expect((screen.getByRole('button', { name: /Save new version/ }) as HTMLButtonElement).disabled).toBe(false));
  fireEvent.click(screen.getByRole('button', { name: /Save new version/ }));
  await waitFor(() => expect(onSave).toHaveBeenCalledWith(2));
  const posted = JSON.parse(fetchMock.mock.calls.find(call => String(call[0]) === '/api/checklists')![1]!.body as string);
  expect(posted.criteria).toHaveLength(9);
  expect(posted.criteria[8].description).toBe('The operator states a ticket reference before closing.');
  expect(posted.criteria[8].id).not.toBe('contact');
  expect(posted.scoring_policy).toEqual(seed.scoring_policy);
  expect(original.criteria).toHaveLength(8); // saved source snapshot was never edited in place
});

it('preserves an unsaved checklist draft when leaving and returning to its version', () => {
  const version = { id: 1, snapshot: structuredClone(seed) as Checklist, content_hash: 'TEST', created_at: '2026-11-01T00:00:00Z' };
  const props = { version, versions: [version], busy: false, run: async (action: () => Promise<void>) => { await action(); }, onSave: async () => {} };
  const first = render(<ChecklistEditor {...props} />);
  fireEvent.change(screen.getByLabelText('Checklist name'), { target: { value: 'SYNTHETIC unsaved draft' } });
  first.unmount();
  render(<ChecklistEditor {...props} />);
  expect((screen.getByLabelText('Checklist name') as HTMLInputElement).value).toBe('SYNTHETIC unsaved draft');
});

it('requires a separate reviewer action and rationale before posting a decision', async () => {
  const criterion = (structuredClone(seed) as Checklist).criteria[0];
  const judgment: Judgment = { disposition: 'assessed', value: false, explanation: 'SYNTHETIC TEST missing introduction', na_reason: null, review_reason: null,
    evidence: [{ kind: 'absence', start_message_id: 'm0001', end_message_id: 'm0001' }] };
  const evaluation: EvaluationDetail = { id: 'TEST_EVAL', updated_at: 'TEST_REVISION', conversation_id: 'TEST_CONVERSATION', checklist_id: 1,
    state: 'succeeded', completeness: 'complete', total: '90.00', error: null, cached_from: null, created_at: '2026-11-01T00:00:00Z',
    original: { results: { contact: judgment } }, effective: { results: { contact: judgment } }, original_score: null, effective_score: null,
    checklist: { id: 1, snapshot: structuredClone(seed) as Checklist, content_hash: 'TEST', created_at: '2026-11-01T00:00:00Z' },
    metadata: { provider: 'TEST_ONLY', model: 'TEST_ONLY', mode: 'TEST/MOCK', prompt_version: 'TEST_ONLY' }, attempts: [], appeals: [], reviews: [],
    usage: { request_attempts: 0, input_tokens_known: 0, output_tokens_known: 0, usage_complete: false, estimated_cost_usd: null, cost_rate_source: null, latency_ms: 0 },
  };
  const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({ id: 1 }), { status: 201 }));
  const onSaved = vi.fn(async () => {});
  const messages: Message[] = [{ id: 'm0001', speaker: 'operator', timestamp: '00:00', text: 'SYNTHETIC TEST transcript' }];
  render(<ReviewForm appeal={{ id: 'TEST_APPEAL', criterion_id: 'contact', comment: 'SYNTHETIC TEST appeal', status: 'open', created_at: '2026-11-01T00:00:00Z' }} criterion={criterion} evaluation={evaluation} messages={messages} busy={false} run={async action => { await action(); }} onSaved={onSaved} />);
  expect(fetchMock).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole('button', { name: 'Review appeal' }));
  expect(screen.getByRole('button', { name: /Save decision/ }).hasAttribute('disabled')).toBe(true);
  fireEvent.change(screen.getByLabelText('Decision rationale'), { target: { value: 'SYNTHETIC TEST: confirmed after reading original evidence.' } });
  fireEvent.click(screen.getByRole('button', { name: /Save decision/ }));
  await waitFor(() => expect(onSaved).toHaveBeenCalledOnce());
  expect(fetchMock.mock.calls[0][0]).toBe('/api/appeals/TEST_APPEAL/decision');
  expect(JSON.parse(fetchMock.mock.calls[0][1]!.body as string)).toMatchObject({ action: 'confirm', judgment: null, expected_updated_at: 'TEST_REVISION' });
});

it('retracts an unsupported positive with a missing basis instead of forcing a scored answer', async () => {
  const checklist = structuredClone(seed) as Checklist;
  const judgment: Judgment = { disposition: 'assessed', value: true, explanation: 'SYNTHETIC unsupported introduction', na_reason: null, review_reason: null,
    evidence: [{ kind: 'support', start_message_id: 'm0001', end_message_id: 'm0001' }] };
  const evaluation: EvaluationDetail = { id: 'TEST_EVAL', updated_at: 'TEST_REVISION', conversation_id: 'TEST_CALL', checklist_id: 1,
    state: 'succeeded', completeness: 'complete', total: '100.00', error: null, cached_from: null, created_at: '2026-11-01T00:00:00Z',
    original: { results: { contact: judgment } }, effective: { results: { contact: judgment } }, original_score: null, effective_score: null,
    checklist: { id: 1, snapshot: checklist, content_hash: 'TEST', created_at: '2026-11-01T00:00:00Z' },
    metadata: { provider: 'TEST_ONLY', model: 'TEST_ONLY', mode: 'TEST/MOCK', prompt_version: 'TEST_ONLY' }, attempts: [], appeals: [], reviews: [],
    usage: { request_attempts: 0, input_tokens_known: 0, output_tokens_known: 0, usage_complete: false, estimated_cost_usd: null, cost_rate_source: null, latency_ms: 0 } };
  const before = structuredClone(evaluation);
  const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({ id: 1 }), { status: 201 }));
  const onSaved = vi.fn(async () => {});
  render(<ReviewForm appeal={{ id: 'TEST_APPEAL', criterion_id: 'contact', comment: 'SYNTHETIC uncertain ASR', status: 'open', created_at: '2026-11-01T00:00:00Z' }}
    criterion={checklist.criteria[0]} evaluation={evaluation} messages={[{ id: 'm0001', speaker: 'operator', timestamp: '00:00', text: 'SYNTHETIC company [unintelligible] hello' }]}
    busy={false} run={async action => { await action(); }} onSaved={onSaved} />);
  fireEvent.click(screen.getByRole('button', { name: 'Review appeal' }));
  fireEvent.change(screen.getByLabelText('Reviewer action'), { target: { value: 'replace' } });
  fireEvent.change(screen.getByLabelText('Disposition'), { target: { value: 'needs_review' } });
  expect(screen.queryByLabelText('Replacement answer')).toBeNull();
  expect((screen.getByLabelText('Missing basis') as HTMLTextAreaElement).required).toBe(true);
  expect(screen.getByText(/final total will be withheld/)).toBeDefined();
  fireEvent.change(screen.getByLabelText('Missing basis'), { target: { value: 'Recording review needed: opening ASR is unintelligible.' } });
  fireEvent.change(screen.getByLabelText('Criterion explanation'), { target: { value: 'Self-introduction cannot be established from this source.' } });
  fireEvent.change(screen.getByLabelText('Decision rationale'), { target: { value: 'SYNTHETIC retraction after source inspection' } });
  fireEvent.click(screen.getByRole('button', { name: /Save decision/ }));
  await waitFor(() => expect(onSaved).toHaveBeenCalledOnce());
  expect(fetchMock).toHaveBeenCalledOnce();
  expect(fetchMock.mock.calls[0][0]).toBe('/api/appeals/TEST_APPEAL/decision');
  expect(JSON.parse(fetchMock.mock.calls[0][1]!.body as string)).toMatchObject({ action: 'replace', expected_updated_at: 'TEST_REVISION',
    judgment: { disposition: 'needs_review', value: null, na_reason: null, review_reason: 'Recording review needed: opening ASR is unintelligible.' } });
  expect(evaluation).toEqual(before);
});
