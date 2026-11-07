// @vitest-environment happy-dom
// OPT-IN: real local API, real imported DEV input, real paid provider call, real persisted changes.
// No mock data. DOM interaction testing is not a claim of visual/browser verification.
import { expect, it, vi } from 'vitest';
import { cleanup, configure, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import ChecklistEditor from './ChecklistEditor';
import Detail from './Detail';
import { api } from './api';
import type { ChecklistVersion, Conversation, EvaluationDetail, EvaluationSummary } from './types';

const enabled = process.env.CQA_LIVE_SMOKE === '1';

it.skipIf(!enabled)('saves a new criterion through the UI, evaluates real DEV, and persists agent-attributed appeal reviews', async () => {
  configure({ getElementError: message => new Error(message || 'Live UI assertion failed; private DOM omitted') });
  const nativeFetch = globalThis.fetch.bind(globalThis);
  const routing = vi.spyOn(globalThis, 'fetch').mockImplementation((url, options) => nativeFetch(
    typeof url === 'string' && url.startsWith('/api') ? `http://127.0.0.1:8000${url}` : url, options));
  try {
    const versions = await api<ChecklistVersion[]>('/checklists');
    const originalVersion = versions.find(v => v.id === 1)!;
    const rows = await api<Conversation[]>('/conversations');
    const conversation = rows.find(r => r.group_id === 'DEV' && r.source_id === 'p1-ru-001')!;
    expect(conversation).toBeDefined();
    const execute = async (action: () => Promise<void>) => { await action(); };
    let savedId = 0;
    render(<ChecklistEditor version={originalVersion} versions={versions} busy={false} run={execute} onSave={async id => { savedId = id; }} />);
    fireEvent.click(screen.getByRole('button', { name: /Add a criterion/ }));
    const name = screen.getAllByLabelText('Name').at(-1)!;
    const definition = screen.getAllByLabelText('Criterion definition').at(-1)!;
    fireEvent.change(name, { target: { value: 'Ticket reference before closing' } });
    fireEvent.change(definition, { target: { value: 'Yes only if the HUMAN OPERATOR explicitly provides a support ticket or case reference identifier. No if absent. A message ID, account ID, source conversation ID or rubric ID is not a support ticket reference. This is an added demonstration criterion.' } });
    fireEvent.click(screen.getByRole('button', { name: /Save new version/ }));
    await waitFor(() => expect(savedId).toBeGreaterThan(1), { timeout: 15000, onTimeout: error => error });
    cleanup();
    const newVersion = (await api<ChecklistVersion[]>('/checklists')).find(v => v.id === savedId)!;
    expect(originalVersion.snapshot.criteria).toHaveLength(8);
    expect(newVersion.snapshot.criteria).toHaveLength(9);
    const newCriterion = newVersion.snapshot.criteria.at(-1)!;
    const started = await api<{ evaluation_ids: string[] }>('/evaluations', { conversation_ids: [conversation.id], checklist_id: savedId });
    let evaluated: EvaluationDetail | null = null;
    for (let attempt = 0; attempt < 120; attempt++) {
      evaluated = await api<EvaluationDetail>(`/evaluations/${started.evaluation_ids[0]}`);
      if (!['queued', 'running'].includes(evaluated.state)) break;
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    expect(evaluated?.state).toBe('succeeded');
    expect(evaluated?.original?.results[newCriterion.id]).toMatchObject({ disposition: 'assessed', value: false });
    expect(evaluated?.cached_from).toBeNull();

    // Use the first, preserved live run to demonstrate correcting the observed N/A/closure mistakes.
    const savedRuns = await api<EvaluationSummary[]>(`/evaluations?conversation_id=${conversation.id}`);
    const first = savedRuns.filter(e => e.checklist_id === 1 && e.state === 'succeeded').sort((a, b) => a.created_at.localeCompare(b.created_at))[0];
    const before = await api<EvaluationDetail>(`/evaluations/${first.id}`);
    render(<Detail id={conversation.id} initialEvaluation={first.id} selectedVersion={1} busy={false} run={execute} providerReady evaluate={async () => {}} onChange={async () => {}} />);
    await waitFor(() => expect(screen.queryByRole('heading', { name: 'Завершение' })).not.toBeNull(), { timeout: 15000, onTimeout: error => error });

    for (const [title, isNa] of [['Завершение', false], ['Выявление потребности', true]] as const) {
      const card = screen.getByRole('heading', { name: title }).closest('article')!;
      fireEvent.click(within(card).getByRole('button', { name: 'Appeal criterion' }));
      fireEvent.change(within(card).getByLabelText('Appeal comment'), { target: { value: `Agent demonstration review: ${isNa ? 'initial information was sufficient; apply the saved N/A condition' : 'a polite wish alone does not provide the required summary or further-help offer'}. Not an independent human label.` } });
      fireEvent.click(within(card).getByRole('button', { name: 'Submit appeal' }));
      await waitFor(() => expect(within(card).queryAllByRole('button', { name: 'Review appeal' }).length).toBeGreaterThan(0), { timeout: 15000, onTimeout: error => error });
      fireEvent.click(within(card).getAllByRole('button', { name: 'Review appeal' }).at(-1)!);
      fireEvent.change(within(card).getByLabelText('Reviewer action'), { target: { value: 'replace' } });
      if (isNa) {
        fireEvent.change(within(card).getByLabelText('Disposition'), { target: { value: 'not_applicable' } });
        const field = within(card).getAllByRole('textbox').find(element => element.closest('label')?.textContent?.startsWith('N/A justification'))!;
        fireEvent.change(field, { target: { value: 'The initial question and context already identify the needed information, so the saved condition is met.' } });
      } else fireEvent.change(within(card).getByLabelText('Replacement answer'), { target: { value: 'false' } });
      fireEvent.change(within(card).getByLabelText('Criterion explanation'), { target: { value: isNa ? 'Agent review: all information needed to answer was present before the operator response; clarification was not needed.' : 'Agent review: the operator only said you are welcome and wished a good evening; neither a summary nor further-help offer appears.' } });
      fireEvent.change(within(card).getByLabelText('Evidence kind'), { target: { value: isNa ? 'context' : 'absence' } });
      fireEvent.change(within(card).getByLabelText('Start message'), { target: { value: isNa ? 'm0001' : 'm0010' } });
      fireEvent.change(within(card).getByLabelText('End message'), { target: { value: 'm0012' } });
      fireEvent.change(within(card).getByLabelText('Decision rationale'), { target: { value: 'Provisional agent demonstration review against the supplied rubric and stored transcript; not independent human ground truth.' } });
      fireEvent.click(within(card).getByRole('button', { name: /Save decision & recalculate/ }));
      await waitFor(() => expect(within(card).queryByLabelText('Decision rationale')).toBeNull(), { timeout: 15000, onTimeout: error => error });
    }
    const after = await api<EvaluationDetail>(`/evaluations/${first.id}`);
    expect(after.original).toEqual(before.original);
    expect(after.original_score?.total).toBe('100.00');
    expect(after.effective_score?.total).toBe('92.31');
    expect(after.reviews.length).toBeGreaterThanOrEqual(2);
    expect(after.attempts.length).toBe(before.attempts.length);
    cleanup();
    // Recreate the view to verify that the UI consumes saved state, not in-memory form answers.
    render(<Detail id={conversation.id} initialEvaluation={first.id} selectedVersion={1} busy={false} run={execute} providerReady evaluate={async () => {}} onChange={async () => {}} />);
    await waitFor(() => expect(screen.queryAllByText(/92.31/).length).toBeGreaterThan(0), { timeout: 15000, onTimeout: error => error });
  } finally { cleanup(); routing.mockRestore(); }
}, 180000);
