// @vitest-environment happy-dom
import { afterEach, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import WeightImpact from './WeightImpact';
import type { Checklist, ChecklistVersion } from './types';
import seed from '../../config/initial_checklist.json';

afterEach(() => { cleanup(); vi.restoreAllMocks(); });
const version: ChecklistVersion = { id: 1, content_hash: 'CHECKLIST_HASH', created_at: '2026-11-07', snapshot: seed as Checklist };
const run = (id: string) => ({ id, conversation_id: `SOURCE_${id}`, checklist_id: 1, checklist_hash: 'CHECKLIST_HASH',
  source_id: `TEST_${id}`, group_id: 'SYNTHETIC_TEST_ONLY', revision: 1, content_hash: `HASH_${id}`, updated_at: 'UPDATED_1', created_at: '2026-11-07' });
const page = (id = 1) => ({ checklist_id: id, checklist_hash: id === 1 ? 'CHECKLIST_HASH' : 'SECOND_HASH', total: 2, offset: 0, limit: 100, runs: [run('A'), run('B')] });
const score = (total: string | null) => ({ total, reason: total === null ? 'UNRESOLVED_CRITERIA' : null, completeness: total === null ? 'needs_review' : 'complete',
  applicable_weight: '30', raw_subtotal: '20', flags: {}, criteria: [], sections: [] });
const row = { weight: '10', applicable: true, raw_points: '5', normalized_contribution: '16.6667' };
const preview = (id = 'A', name = 'CURRENT_SAVED_JUDGMENT', basis = 'effective', total: string | null = '66.67') => ({
  eligible: true, simulation: true, notice: 'Fixed-judgment simulation only. No model evaluation, saved result or checklist is changed.',
  checklist_id: 1, checklist_hash: 'CHECKLIST_HASH', evaluation_id: id, updated_at: 'UPDATED_1', basis, reasons: [], errors: [],
  source: { id: `SOURCE_${id}`, source_id: `TEST_${id}`, group_id: 'SYNTHETIC_TEST_ONLY', revision: 1, content_hash: `HASH_${id}` },
  original_score: score(total), simulated_score: score(total), total_difference: total === null ? null : '0.00',
  criteria: [{ criterion_id: 'TEST', name, answer_type: 'scale', disposition: 'assessed', value: .5, original: row, simulated: row }],
});
const respond = (value: unknown) => new Response(JSON.stringify(value));
const open = () => fireEvent.click(screen.getByText('Weight-impact preview'));

it('does no work while collapsed and displays an explicit fixed-judgment scenario when opened', async () => {
  const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(async url => respond(String(url).includes('/runs?') ? page() : preview()));
  render(<WeightImpact version={version} draft={version.snapshot} />);
  expect(fetchMock).not.toHaveBeenCalled();
  open();
  await screen.findByText('CURRENT_SAVED_JUDGMENT');
  expect(screen.getByText(/No model evaluation, saved result or checklist is changed/)).toBeDefined();
  expect(screen.getAllByText('66.67', { selector: 'dd' })).toHaveLength(2);
  expect(screen.getByText(/Showing runs 1–2 of 2/)).toBeDefined();
  const post = fetchMock.mock.calls.find(([, init]) => init?.method === 'POST');
  expect(JSON.parse(String(post?.[1]?.body))).toEqual({ checklist_id: 1, evaluation_id: 'A', basis: 'effective', draft: version.snapshot });
  expect(fetchMock.mock.calls.every(([url]) => String(url).startsWith('/api/insights/weight-preview'))).toBe(true);
});

it('does not allow a late response to replace an explicitly selected saved run', async () => {
  let release: ((response: Response) => void) | undefined;
  const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(async (url, init) => {
    if (String(url).includes('/runs?')) return respond(page());
    const payload = JSON.parse(String(init?.body));
    return payload.evaluation_id === 'A' ? new Promise(resolve => { release = resolve; }) : respond(preview('B'));
  });
  render(<WeightImpact version={version} draft={version.snapshot} />); open();
  await waitFor(() => expect(release).toBeDefined());
  fireEvent.change(screen.getByLabelText('Weight preview saved run'), { target: { value: 'B' } });
  await screen.findByText('CURRENT_SAVED_JUDGMENT');
  release!(respond(preview('A', 'OBSOLETE_SAVED_JUDGMENT')));
  await waitFor(() => expect(fetchMock.mock.calls.filter(([, init]) => init?.method === 'POST').length).toBe(2));
  expect(screen.queryByText('OBSOLETE_SAVED_JUDGMENT')).toBeNull();
  expect((screen.getByLabelText('Weight preview saved run') as HTMLSelectElement).value).toBe('B');
});

it('hides previous arithmetic immediately when the draft changes and ignores obsolete errors', async () => {
  let reject: ((error: Error) => void) | undefined;
  vi.spyOn(globalThis, 'fetch').mockImplementation(async (url, init) => {
    if (String(url).includes('/runs?')) return respond(page());
    const payload = JSON.parse(String(init?.body));
    return payload.draft.criteria[0].weight === '77' ? new Promise((_, fail) => { reject = fail; }) : respond(preview());
  });
  const view = render(<WeightImpact version={version} draft={version.snapshot} />); open();
  await screen.findByText('CURRENT_SAVED_JUDGMENT');
  const changed = structuredClone(version.snapshot); changed.criteria[0].weight = '77';
  view.rerender(<WeightImpact version={version} draft={changed} />);
  expect(screen.queryByText('CURRENT_SAVED_JUDGMENT')).toBeNull();
  await waitFor(() => expect(reject).toBeDefined());
  view.rerender(<WeightImpact version={version} draft={version.snapshot} />);
  await screen.findByText('CURRENT_SAVED_JUDGMENT');
  reject!(new Error('OBSOLETE_FAILURE'));
  await waitFor(() => expect(screen.queryByText(/OBSOLETE_FAILURE/)).toBeNull());
});

it('shows eligibility reasons and field errors without treating a changed definition as evaluated', async () => {
  vi.spyOn(globalThis, 'fetch').mockImplementation(async url => respond(String(url).includes('/runs?') ? page() : {
    ...preview(), eligible: false, reasons: ['Only criterion weights may change.'], errors: [{ location: ['criteria', 0, 'weight'], label: 'Contact / Weight', message: 'Must be nonnegative' }],
  }));
  render(<WeightImpact version={version} draft={version.snapshot} />); open();
  await screen.findByText('Weight preview unavailable');
  expect(screen.getByText('Only criterion weights may change.')).toBeDefined();
  expect(screen.getByText('Contact / Weight: Must be nonnegative')).toBeDefined();
  expect(screen.queryByText('Simulated total')).toBeNull();
});

it('keeps unresolved totals withheld and separates original/effective bases', async () => {
  const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(async (url, init) => {
    if (String(url).includes('/runs?')) return respond(page());
    return respond(preview('A', 'UNCERTAIN_JUDGMENT', JSON.parse(String(init?.body)).basis, null));
  });
  render(<WeightImpact version={version} draft={version.snapshot} />); open();
  await screen.findByText(/Score withheld: UNRESOLVED_CRITERIA/);
  fireEvent.change(screen.getByLabelText('Weight preview judgment basis'), { target: { value: 'original' } });
  expect(screen.queryByText('UNCERTAIN_JUDGMENT')).toBeNull();
  await screen.findByText('UNCERTAIN_JUDGMENT');
  expect(JSON.parse(String(fetchMock.mock.calls.at(-1)?.[1]?.body)).basis).toBe('original');
});

it('rejects mismatched run provenance and supports retry without a new evaluation', async () => {
  let valid = false;
  const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(async url => respond(String(url).includes('/runs?') ? page() : {
    ...preview(), updated_at: valid ? 'UPDATED_1' : 'OBSOLETE_REVISION',
  }));
  render(<WeightImpact version={version} draft={version.snapshot} />); open();
  await screen.findByText(/The saved run changed or does not match/);
  expect(screen.queryByText('CURRENT_SAVED_JUDGMENT')).toBeNull();
  valid = true; fireEvent.click(screen.getByRole('button', { name: 'Retry weight preview' }));
  await screen.findByText('CURRENT_SAVED_JUDGMENT');
  expect(fetchMock.mock.calls.every(([url]) => !String(url).includes('/evaluations'))).toBe(true);
});

it('does not let old version options select a run for a different checklist', async () => {
  let release: ((response: Response) => void) | undefined;
  vi.spyOn(globalThis, 'fetch').mockImplementation(async url => {
    if (String(url).includes('checklist_id=1')) return new Promise(resolve => { release = resolve; });
    return respond({ ...page(2), total: 0, runs: [] });
  });
  const view = render(<WeightImpact version={version} draft={version.snapshot} />); open();
  await waitFor(() => expect(release).toBeDefined());
  const other = { ...version, id: 2, content_hash: 'SECOND_HASH' };
  view.rerender(<WeightImpact version={other} draft={other.snapshot} />);
  await screen.findByText(/No successful saved runs exist for checklist v2/);
  release!(respond(page()));
  await waitFor(() => expect(screen.queryByLabelText('Weight preview saved run')).toBeNull());
});

it('exposes all saved runs through bounded pagination instead of silently dropping the remainder', async () => {
  vi.spyOn(globalThis, 'fetch').mockImplementation(async url => {
    if (String(url).includes('/runs?')) return respond(String(url).includes('offset=100') ? { ...page(), offset: 100, total: 101, runs: [run('LAST')] }
      : { ...page(), total: 101, runs: Array.from({ length: 100 }, (_, index) => run(index === 0 ? 'A' : `ROW_${index}`)) });
    return respond(preview());
  });
  render(<WeightImpact version={version} draft={version.snapshot} />); open();
  await screen.findByText(/Showing runs 1–100 of 101/);
  fireEvent.click(screen.getByRole('button', { name: 'Next saved runs' }));
  await screen.findByText(/Showing runs 101–101 of 101/);
  expect(screen.getByRole('option', { name: /TEST_LAST/ })).toBeDefined();
  expect((screen.getByLabelText('Weight preview saved run') as HTMLSelectElement).value).toBe('A');
});

it('rounds only contribution display and labels boolean judgments without altering exact scenario values', async () => {
  const base = preview();
  const exactTotal = '66.67000000000000000001'; const exactRaw = '7.0000000000000000000001';
  const packet = { ...base, original_score: score(exactTotal), simulated_score: score(exactTotal), criteria: [
    { ...base.criteria[0], name: 'Precise scale',
      original: { ...row, raw_points: exactRaw, normalized_contribution: '16.666666666666666666666666666666666666666666666667' },
      simulated: { ...row, raw_points: exactRaw, normalized_contribution: '1.234450000000000000000000000000000000000000000001' } },
    ...[{ name: 'Binary yes', value: true, type: 'binary' }, { name: 'Binary no', value: false, type: 'binary' },
      { name: 'Flag true', value: true, type: 'flag' }, { name: 'Flag false', value: false, type: 'flag' }].map(item => ({
      ...base.criteria[0], criterion_id: item.name, name: item.name, answer_type: item.type, value: item.value,
      original: { ...row, normalized_contribution: null }, simulated: { ...row, normalized_contribution: null },
    })),
    { ...base.criteria[0], criterion_id: 'ROUNDING_CARRY', name: 'Rounding carry',
      original: { ...row, normalized_contribution: '99.99995' }, simulated: { ...row, normalized_contribution: '1E-7' } },
  ] };
  const before = JSON.stringify(packet); const draftBefore = JSON.stringify(version.snapshot);
  const freeze = <T,>(value: T): T => {
    if (value && typeof value === 'object') { Object.freeze(value); Object.values(value).forEach(freeze); }
    return value;
  };
  freeze(packet);
  const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(async url => {
    if (String(url).includes('/runs?')) return respond(page());
    const response = respond({}); vi.spyOn(response, 'json').mockResolvedValue(packet); return response;
  });
  render(<WeightImpact version={version} draft={version.snapshot} />); open();
  const precise = (await screen.findByText('Precise scale')).closest('tr')!;
  expect(within(precise).getByText('16.6667 → 1.2345')).toBeDefined();
  expect(within(precise).getByText(`${exactRaw} → ${exactRaw}`)).toBeDefined();
  expect(screen.getAllByText(exactTotal, { selector: 'dd' })).toHaveLength(2);
  for (const [name, label] of [['Binary yes', 'Yes'], ['Binary no', 'No'], ['Flag true', 'Flagged'], ['Flag false', 'Not flagged']]) {
    expect(within(screen.getByText(name).closest('tr')!).getByRole('cell', { name: label })).toBeDefined();
  }
  expect(within(screen.getByText('Rounding carry').closest('tr')!).getByText('100.0000 → 0.0000')).toBeDefined();
  expect(screen.getByText(/rounded to four decimal places for display only/)).toBeDefined();
  expect(JSON.stringify(packet)).toBe(before);
  expect(JSON.stringify(version.snapshot)).toBe(draftBefore);
  expect(JSON.parse(String(fetchMock.mock.calls.find(([, init]) => init?.method === 'POST')?.[1]?.body)).draft).toEqual(version.snapshot);
});
