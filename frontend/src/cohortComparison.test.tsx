// @vitest-environment happy-dom
import { afterEach, expect, it, vi } from 'vitest';
import { act, cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import CohortComparison from './CohortComparison';
import { cohortOptionsFixture, cohortResultFixture, exactPairFixture } from './cohortTestFixtures';
import { cohortResultMatches } from './cohortTypes';
import type { CohortOptions, CohortRequest, CohortResult } from './cohortTypes';

afterEach(() => { cleanup(); vi.restoreAllMocks(); });
const json = (value: unknown, status = 200) => new Response(JSON.stringify(value), { status });
const open = () => { const panel = document.querySelector('details.cohort-comparison')! as HTMLDetailsElement; panel.open = true; fireEvent(panel, new Event('toggle')); };
function deferred() { let resolve!: (value: Response) => void; const promise = new Promise<Response>(done => { resolve = done; }); return { promise, resolve }; }
function setup(options = cohortOptionsFixture(), response?: (body: CohortRequest) => Promise<Response>) {
  return vi.spyOn(globalThis, 'fetch').mockImplementation(async (input, init) => {
    if (String(input) === '/api/insights/cohorts/options') return json(options);
    if (String(input) === '/api/insights/cohorts/compare') {
      const body = JSON.parse(init!.body as string) as CohortRequest;
      return response ? response(body) : json(cohortResultFixture(body));
    }
    if (String(input).startsWith('/api/evaluations/compare?')) return json(exactPairFixture(cohortResultFixture().pairs[0]));
    throw new Error(`Unexpected synthetic request: ${String(input)}`);
  });
}
async function compare() {
  for (const [side, value] of [['Baseline', 'A'], ['Candidate', 'B']]) {
    const select = await screen.findByRole('combobox', { name: `${side} model` }) as HTMLSelectElement;
    if (select.value === 'any') fireEvent.change(select, { target: { value: JSON.stringify(value) } });
  }
  fireEvent.click(screen.getByRole('button', { name: 'Compare saved cohorts' }));
}

it('loads only when opened, uses its explicit dataset scope and never calls inference', async () => {
  const fetch = setup(); const onOpenPair = vi.fn(); render(<CohortComparison onOpenPair={onOpenPair} />);
  expect(fetch).not.toHaveBeenCalled(); open(); await compare();
  await screen.findByRole('heading', { name: 'Dataset DEV · effective answers' });
  const posted = fetch.mock.calls.find(call => String(call[0]).endsWith('/compare'))!;
  expect(JSON.parse(posted[1]!.body as string)).toEqual({ dataset_group_id: 'DEV', left: { checklist_id: 1, model: 'A' }, right: { checklist_id: 1, model: 'B' }, basis: 'effective', limit: 200 });
  expect(screen.getByText(/queue filters do not apply/)).toBeDefined();
  expect(screen.getByText(/Higher operator scores do not establish/)).toBeDefined();
  expect(screen.getAllByRole('button', { name: /Inspect exact pair/ })).toHaveLength(1);
  expect(onOpenPair).not.toHaveBeenCalled();
  expect(fetch.mock.calls.every(call => String(call[0]).startsWith('/api/insights/cohorts/'))).toBe(true);
});

it('preserves wildcard, unknown and exact metadata selection and clears obsolete results on input change', async () => {
  const fetch = setup(); render(<CohortComparison onOpenPair={vi.fn()} />); open();
  const model = await screen.findByRole('combobox', { name: 'Baseline model' });
  fireEvent.change(model, { target: { value: 'null' } }); await compare();
  await screen.findByRole('heading', { name: 'Dataset DEV · effective answers' });
  expect(JSON.parse(fetch.mock.calls.filter(call => String(call[0]).endsWith('/compare'))[0][1]!.body as string).left.model).toBeNull();
  fireEvent.change(model, { target: { value: JSON.stringify('A') } });
  expect(screen.queryByRole('region', { name: 'Cohort criterion transitions' })).toBeNull();
  await compare(); await screen.findByRole('region', { name: 'Cohort criterion transitions' });
  expect(JSON.parse(fetch.mock.calls.filter(call => String(call[0]).endsWith('/compare'))[1][1]!.body as string).left.model).toBe('A');
  fireEvent.change(screen.getByRole('combobox', { name: 'Cohort dataset' }), { target: { value: 'SYNTHETIC_ONLY' } });
  expect((model as HTMLSelectElement).value).toBe('any');
  expect(screen.queryByRole('region', { name: 'Cohort criterion transitions' })).toBeNull();
});

it('drills into exact transition cases, focuses them and restores the trigger on return', async () => {
  setup(); render(<CohortComparison onOpenPair={vi.fn()} />); open(); await compare();
  const transitions = await screen.findByRole('region', { name: 'Cohort criterion transitions' });
  const button = within(transitions).getByRole('button', { name: /Yes → No/ }); fireEvent.click(button);
  const cases = screen.getByRole('region', { name: 'Cohort exact cases' });
  expect(document.activeElement).toBe(cases);
  expect(within(cases).getByRole('link', { name: 'Open source / saved run' }).getAttribute('href')).toBe('#conversation/C1?evaluation=A_C1');
  expect(within(cases).queryByText('SYNTHETIC_C2')).toBeNull();
  fireEvent.click(screen.getByRole('button', { name: 'Show all cohort cases' }));
  expect(document.activeElement).toBe(button);
  expect(within(cases).getByText('SYNTHETIC_C2')).toBeDefined();
});

it('recovers an options outage and a comparison outage with explicit retries', async () => {
  let optionCalls = 0; let comparisons = 0;
  vi.spyOn(globalThis, 'fetch').mockImplementation(async (url, init) => String(url).endsWith('/options')
    ? ++optionCalls === 1 ? json({ detail: 'SYNTHETIC options outage' }, 503) : json(cohortOptionsFixture())
    : ++comparisons === 1 ? json({ detail: 'SYNTHETIC comparison outage' }, 503) : json(cohortResultFixture(JSON.parse(init!.body as string))));
  render(<CohortComparison onOpenPair={vi.fn()} />); open();
  fireEvent.click(await screen.findByRole('button', { name: 'Retry cohort options' })); await compare();
  fireEvent.click(await screen.findByRole('button', { name: 'Retry cohort comparison' }));
  await screen.findByRole('region', { name: 'Cohort criterion transitions' });
  expect(optionCalls).toBe(2); expect(comparisons).toBe(2);
});

it('ignores late results and errors after the answer basis changes', async () => {
  const old = deferred(); setup(cohortOptionsFixture(), async body => body.basis === 'effective' ? old.promise : json(cohortResultFixture(body)));
  render(<CohortComparison onOpenPair={vi.fn()} />); open(); await compare();
  await screen.findByText('Comparing saved cohorts…');
  fireEvent.change(screen.getByRole('combobox', { name: 'Cohort answer basis' }), { target: { value: 'original' } });
  await compare(); await screen.findByRole('heading', { name: 'Dataset DEV · original answers' });
  await act(async () => old.resolve(json({ detail: 'OBSOLETE_FAILURE' }, 503)));
  expect(screen.queryByText('OBSOLETE_FAILURE')).toBeNull();
  expect(screen.queryByRole('heading', { name: 'Dataset DEV · effective answers' })).toBeNull();
});

it.each(['dataset', 'basis', 'selector', 'source', 'coverage'])('rejects a mismatched %s in a returned result', async mismatch => {
  setup(cohortOptionsFixture(), async body => {
    const result = cohortResultFixture(body);
    if (mismatch === 'dataset') result.dataset_group_id = 'WRONG';
    if (mismatch === 'basis') result.basis = 'original';
    if (mismatch === 'selector') result.left.model = 'WRONG';
    if (mismatch === 'source') result.pairs[0].right!.conversation_id = 'WRONG';
    if (mismatch === 'coverage') result.coverage.matched = 9;
    return json(result);
  });
  render(<CohortComparison onOpenPair={vi.fn()} />); open(); await compare();
  await screen.findByText(/Cohort results do not match/);
  expect(screen.queryByRole('region', { name: 'Cohort criterion transitions' })).toBeNull();
});

it('refuses a dataset above 200 revisions before posting and shows an empty workspace clearly', async () => {
  const options = cohortOptionsFixture(); options.datasets[0].source_revision_count = 201;
  const fetch = setup(options); const view = render(<CohortComparison onOpenPair={vi.fn()} />); open();
  await screen.findByText(/exceeds 200 exact source revisions/);
  expect((screen.getByRole('button', { name: 'Compare saved cohorts' }) as HTMLButtonElement).disabled).toBe(true);
  expect(fetch.mock.calls.filter(call => String(call[0]).endsWith('/compare'))).toHaveLength(0);
  view.unmount(); fetch.mockRestore();
  const empty: CohortOptions = { ...cohortOptionsFixture(), datasets: [], checklists: [] }; setup(empty);
  render(<CohortComparison onOpenPair={vi.fn()} />); open();
  await screen.findByText('No saved source datasets are available.');
});

it('checks an exact pair before handing off its real run IDs and returns focus after closing', async () => {
  setup(); const onOpenPair = vi.fn(); render(<CohortComparison onOpenPair={onOpenPair} />); open(); await compare();
  const trigger = await screen.findByRole('button', { name: 'Inspect exact pair SYNTHETIC_C1 revision 1' }); fireEvent.click(trigger);
  fireEvent.click(await screen.findByRole('button', { name: 'Open these run IDs in review' }));
  expect(onOpenPair).toHaveBeenCalledWith('A_C1', 'B_C1');
  fireEvent.click(screen.getByRole('button', { name: 'Close pair' }));
  expect(document.activeElement).toBe(trigger);
});

it('discloses an identical-filter self-comparison before a request is made', async () => {
  setup(); render(<CohortComparison onOpenPair={vi.fn()} />); open();
  await screen.findByText(/These filters are identical/);
});

it.each(['duplicate_case', 'bad_statistic', 'bad_provenance', 'missing_counts', 'same_selector_different_runs'])('refuses malformed %s contract data', kind => {
  const result = cohortResultFixture();
  const request = { dataset_group_id: result.dataset_group_id, left: result.left, right: result.right, basis: result.basis, limit: result.limit };
  if (kind === 'duplicate_case') result.criteria[0].transitions[1].conversation_ids = ['C1'];
  if (kind === 'bad_statistic') result.total_difference.mean = 'NaN';
  if (kind === 'bad_provenance') result.pairs[0].left!.provenance.response_models = null as unknown as string[];
  if (kind === 'missing_counts') delete (result.criteria[0] as unknown as Record<string, unknown>).definition_changed_count;
  if (kind === 'same_selector_different_runs') { request.right = { ...request.left }; result.right = request.right; }
  expect(cohortResultMatches(result, request)).toBe(false);
});
