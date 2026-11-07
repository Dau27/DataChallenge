// @vitest-environment happy-dom
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import ChecklistEditor from './ChecklistEditor';
import Conversations from './Conversations';
import { BudgetSummary, EvaluationAction } from './Budget';
import type { BudgetStatus, Checklist, ChecklistVersion, Conversation } from './types';
import seed from '../../config/initial_checklist.json';

beforeEach(() => sessionStorage.clear());
afterEach(() => { cleanup(); vi.restoreAllMocks(); sessionStorage.clear(); });
const execute = async (action: () => Promise<void>) => { await action(); };
const version = (): ChecklistVersion => ({ id: 1, snapshot: structuredClone(seed) as Checklist, content_hash: 'TEST_ONLY', created_at: 'TEST_ONLY' });
const paused: BudgetStatus = { limit_usd: '0', opening_accounted_usd: '0', accounted_usd: '0', reserved_usd: '0', overhead_usd: '.1', available_usd: '0', ready: false, blocked_reason: 'Paid requests are paused', estimate_only: true };

it('shows a field error and saved/draft difference, blocks invalid save and recovers after correction', async () => {
  const saved = version(); const onSave = vi.fn();
  const requests: { url: string; body: Checklist }[] = [];
  vi.spyOn(globalThis, 'fetch').mockImplementation(async (url, options) => {
    const body = JSON.parse(options!.body as string) as Checklist; requests.push({ url: String(url), body });
    if (!String(url).endsWith('/preview')) return new Response(JSON.stringify({ ...saved, id: 2 }), { status: 201 });
    const valid = Number(body.criteria[0].weight) >= 0;
    return new Response(JSON.stringify({ valid, errors: valid ? [] : [{ location: ['criteria', 0, 'weight'], message: 'Weight must be nonnegative' }],
      changes: [{ location: ['criteria', 'contact', 'weight'], label: 'Contact / Weight', before: '10', after: body.criteria[0].weight }] }));
  });
  render(<ChecklistEditor version={saved} versions={[saved]} busy={false} run={execute} onSave={onSave} />);
  const weight = screen.getAllByLabelText('Weight')[0];
  fireEvent.change(weight, { target: { value: '-1' } });
  await waitFor(() => expect(weight.getAttribute('aria-invalid')).toBe('true'));
  expect(screen.getByText('Weight must be nonnegative')).toBeDefined();
  expect((screen.getByRole('button', { name: /Save new version/ }) as HTMLButtonElement).disabled).toBe(true);
  expect(requests.every(r => r.url.endsWith('/preview'))).toBe(true);
  expect(within(screen.getByRole('region', { name: 'Checklist change preview' })).getByText('-1')).toBeDefined();
  fireEvent.change(weight, { target: { value: '12.5' } });
  await waitFor(() => expect((screen.getByRole('button', { name: /Save new version/ }) as HTMLButtonElement).disabled).toBe(false));
  fireEvent.click(screen.getByRole('button', { name: /Save new version/ }));
  await waitFor(() => expect(onSave).toHaveBeenCalledWith(2));
  expect(requests.filter(r => r.url === '/api/checklists')[0].body.criteria[0].weight).toBe('12.5');
  expect(Number(saved.snapshot.criteria[0].weight)).toBe(10);
  expect(requests.some(r => r.url.includes('evaluations'))).toBe(false);
});

it('ignores a late successful preview for an older draft', async () => {
  let release: ((response: Response) => void) | undefined;
  const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(async (_, options) => {
    const body = JSON.parse(options!.body as string);
    if (body.name === 'First draft') return new Promise<Response>(resolve => { release = resolve; });
    return new Response(JSON.stringify({ valid: false, errors: [{ location: ['name'], message: 'Current draft error' }], changes: [] }));
  });
  const saved = version();
  render(<ChecklistEditor version={saved} versions={[saved]} busy={false} run={execute} onSave={vi.fn()} />);
  fireEvent.change(screen.getByLabelText('Checklist name'), { target: { value: 'First draft' } });
  await waitFor(() => expect(release).toBeDefined());
  fireEvent.change(screen.getByLabelText('Checklist name'), { target: { value: 'Second draft' } });
  await screen.findByText('Current draft error');
  release!(new Response(JSON.stringify({ valid: true, errors: [], changes: [] })));
  await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
  expect((screen.getByRole('button', { name: /Save new version/ }) as HTMLButtonElement).disabled).toBe(true);
});

it('allows a free cached operation while preventing unaffordable paid work', async () => {
  const start = vi.fn(); const urls: string[] = [];
  vi.spyOn(globalThis, 'fetch').mockImplementation(async (url, options) => {
    urls.push(String(url)); const cached = JSON.parse(options!.body as string).conversation_ids[0] === 'CACHED';
    return new Response(JSON.stringify({ required_reservation_usd: cached ? '0' : '.25', cached: cached ? 1 : 0, active: 0,
      new_evaluations: cached ? 0 : 1, affordable: cached, blocked_reason: cached ? null : 'Paid requests are paused', budget: paused }));
  });
  const view = render(<EvaluationAction ids={['NEW']} version={1} providerReady busy={false} label="Evaluate" start={start} />);
  await screen.findByText(/Paid requests are paused/);
  fireEvent.click(screen.getByRole('button', { name: 'Evaluate' })); expect(start).not.toHaveBeenCalled();
  view.rerender(<EvaluationAction ids={['CACHED']} version={1} providerReady busy={false} label="Evaluate" start={start} />);
  await waitFor(() => expect((screen.getByRole('button', { name: 'Evaluate' }) as HTMLButtonElement).disabled).toBe(false));
  fireEvent.click(screen.getByRole('button', { name: 'Evaluate' })); expect(start).toHaveBeenCalledOnce();
  expect(urls.every(url => url === '/api/evaluations/preview')).toBe(true);
});

it('combines pending/critical/dataset/language filters and links to the actual appealed revision', () => {
  const make = (id: string, language: string, pending: boolean, flagged: boolean, group = 'DEV'): Conversation => ({
    id, source_id: `TEST_${id}`, content_hash: 'SYNTHETIC_HASH', group_id: group, revision: 2, language, channel: 'agent chat', message_count: 2, audio_available: false,
    evaluation: null, pending_appeals: pending ? 1 : 0,
    pending_review_targets: pending ? [{ appeal_id: `APPEAL_${id}`, conversation_id: `OLDER_${id}`, evaluation_id: `RUN_${id}`, criterion_id: 'contact', criterion_name: 'Contact' }] : [],
    critical_findings: flagged ? [{ evaluation_id: `RUN_${id}`, criterion_id: 'custom_flag', criterion_name: 'Custom critical flag' }] : [],
  });
  const rows = [make('RU', 'RU', true, false), make('EN', 'EN', false, true), make('KZ', 'KZ', true, true), make('OTHER', 'KZ', true, true, 'OTHER_DATASET')];
  const unexpectedRequest = vi.spyOn(globalThis, 'fetch').mockRejectedValue(new Error('Filters must be local'));
  const props = { rows, access: null, selectedVersion: 1, completed: 0, needsReview: 0, busy: false, run: execute, evaluate: vi.fn(), refresh: vi.fn(), notify: vi.fn() };
  const view = render(<Conversations {...props} />);
  fireEvent.change(screen.getByLabelText('Dataset filter'), { target: { value: 'DEV' } });
  fireEvent.change(screen.getByLabelText('Pending appeals filter'), { target: { value: 'pending' } });
  expect(screen.queryByRole('link', { name: 'TEST_EN' })).toBeNull();
  fireEvent.change(screen.getByLabelText('Critical findings filter'), { target: { value: 'flagged' } });
  expect(screen.queryByRole('link', { name: 'TEST_RU' })).toBeNull();
  expect(screen.queryByRole('link', { name: 'TEST_OTHER' })).toBeNull();
  expect(screen.getByRole('link', { name: 'Review Contact' }).getAttribute('href')).toBe('#conversation/OLDER_KZ?evaluation=RUN_KZ&criterion=contact');
  expect(screen.getByRole('link', { name: /Custom critical flag/ }).getAttribute('href')).toBe('#conversation/KZ?evaluation=RUN_KZ&criterion=custom_flag');
  fireEvent.change(screen.getByLabelText('Language filter'), { target: { value: 'RU' } });
  expect(screen.getByText('No conversations match these filters.')).toBeDefined();
  fireEvent.change(screen.getByLabelText('Language filter'), { target: { value: 'KZ' } });
  view.rerender(<Conversations {...props} rows={rows.map(r => r.id === 'KZ' ? { ...r, pending_appeals: 0, pending_review_targets: [] } : r)} />);
  expect(screen.queryByRole('link', { name: 'TEST_KZ' })).toBeNull();
  expect(unexpectedRequest).not.toHaveBeenCalled();
});

it('labels budget amounts as estimates and keeps recorded and reserved amounts visible', () => {
  render(<BudgetSummary budget={{ ...paused, accounted_usd: '1.25', reserved_usd: '.5' }} />);
  expect(screen.getByText(/Accounted estimates: \$1.2500 · Reserved: \$0.5000/)).toBeDefined();
  expect(screen.getByText(/not an account balance/)).toBeDefined();
});
