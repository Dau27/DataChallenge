// @vitest-environment happy-dom
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { act, cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { defaultFilters, useSavedFilters } from './SavedFilters';

const key = 'cqa-filter-presets-v2';
const oldKey = 'cqa-filter-presets-v1';
const preset = (id: string, name: string, checklist_id = 1, text = '') => ({ id, name, checklist_id, filters: { ...defaultFilters, text } });
const store = (presets = [preset('ONE', 'One')], active_by_checklist: Record<string, string> = { '1': 'ONE' }) => ({ schema_version: 2, presets, active_by_checklist });
function Harness({ version = 1 }: { version?: number }) {
  const { filters, setField, controls } = useSavedFilters(version);
  return <>{controls}<input aria-label="Draft transcript query" value={filters.text} onChange={e => setField('text', e.target.value)} /><output aria-label="Current filters">{JSON.stringify(filters)}</output></>;
}
const get = () => JSON.parse(localStorage.getItem(key)!);
const click = (name: string) => fireEvent.click(screen.getByRole('button', { name }));
const name = (value: string) => fireEvent.change(screen.getByLabelText('Filter preset name'), { target: { value } });
const query = (value: string) => fireEvent.change(screen.getByLabelText('Draft transcript query'), { target: { value } });
beforeEach(() => { localStorage.clear(); sessionStorage.clear(); });
afterEach(() => { cleanup(); vi.restoreAllMocks(); vi.unstubAllGlobals(); localStorage.clear(); sessionStorage.clear(); });

it('migrates all legacy checklist scopes in one payload and retains original recovery keys', () => {
  const legacy = JSON.stringify({ schema_version: 1, presets: [preset('ONE', 'First', 1, 'Қазақша'), preset('TWO', 'Second', 2, 'Русский')] });
  localStorage.setItem(oldKey, legacy); localStorage.setItem('cqa-active-filter-v1:1', 'ONE'); localStorage.setItem('cqa-active-filter-v1:2', 'TWO');
  const network = vi.spyOn(globalThis, 'fetch').mockRejectedValue(new Error('Presets are local only'));
  const view = render(<Harness />);
  expect(get().schema_version).toBe(2);
  expect(get().active_by_checklist).toEqual({ '1': 'ONE', '2': 'TWO' });
  expect(localStorage.getItem(oldKey)).toBe(legacy);
  expect(localStorage.getItem('cqa-active-filter-v1:2')).toBe('TWO');
  expect((screen.getByLabelText('Draft transcript query') as HTMLInputElement).value).toBe('Қазақша');
  view.rerender(<Harness version={2} />);
  expect((screen.getByLabelText('Draft transcript query') as HTMLInputElement).value).toBe('Русский');
  expect(network).not.toHaveBeenCalled();
});

it('separates creating, updating, renaming and duplicating without overwriting another preset', () => {
  localStorage.setItem(key, JSON.stringify(store([preset('ONE', 'One', 1, 'saved'), preset('OTHER', 'Other', 2, 'other scope')], { '1': 'ONE', '2': 'OTHER' })));
  render(<Harness />);
  query('unsaved'); click('Save filters');
  expect(screen.getByRole('alert').textContent).toContain('already exists');
  expect(get().presets.find((p: { id: string }) => p.id === 'ONE').filters.text).toBe('saved');
  click('Update saved filters');
  expect(get().presets.find((p: { id: string }) => p.id === 'ONE').filters.text).toBe('unsaved');
  query('new draft'); name('Renamed'); click('Rename saved filters');
  expect(get().presets.find((p: { id: string }) => p.id === 'ONE').name).toBe('Renamed');
  expect(get().presets.find((p: { id: string }) => p.id === 'ONE').filters.text).toBe('unsaved');
  expect((screen.getByLabelText('Draft transcript query') as HTMLInputElement).value).toBe('new draft');
  click('Duplicate saved filters');
  expect(get().presets.find((p: { name: string }) => p.name === 'Renamed (copy)').filters.text).toBe('unsaved');
  expect(get().presets.find((p: { id: string }) => p.id === 'OTHER')).toEqual(preset('OTHER', 'Other', 2, 'other scope'));
  name('A new preset'); query('current draft'); click('Save filters');
  expect(get().presets.find((p: { name: string }) => p.name === 'A new preset').filters.text).toBe('current draft');
});

it('persists preset and selection with one write and retains storage and current edits on write failure', () => {
  const raw = JSON.stringify(store()); const values = new Map([[key, raw]]); const setItem = vi.fn(() => { throw new Error('Storage full'); });
  vi.stubGlobal('localStorage', { getItem: (k: string) => values.get(k) ?? null, setItem });
  render(<Harness />); query('unsaved'); click('Update saved filters');
  expect(setItem).toHaveBeenCalledTimes(1);
  const [writtenKey, written] = setItem.mock.calls[0] as unknown as [string, string];
  expect(writtenKey).toBe(key); expect(JSON.parse(written).active_by_checklist).toEqual({ '1': 'ONE' });
  expect(JSON.parse(written).presets[0].filters.text).toBe('unsaved');
  expect(values.get(key)).toBe(raw);
  expect((screen.getByLabelText('Draft transcript query') as HTMLInputElement).value).toBe('unsaved');
  expect(screen.getByRole('alert').textContent).toContain('was not saved');
});

it('preserves restored legacy filters if the atomic migration write fails', () => {
  const raw = JSON.stringify({ schema_version: 1, presets: [preset('ONE', 'Legacy', 1, 'restored')] });
  const values = new Map([[oldKey, raw], ['cqa-active-filter-v1:1', 'ONE']]);
  vi.stubGlobal('localStorage', { getItem: (k: string) => values.get(k) ?? null, setItem: () => { throw new Error('Quota'); } });
  render(<Harness />);
  expect((screen.getByLabelText('Draft transcript query') as HTMLInputElement).value).toBe('restored');
  expect(screen.getByRole('alert').textContent).toContain('upgrade could not be saved');
  expect(values.get(oldKey)).toBe(raw); expect(values.has(key)).toBe(false);
});

it('does not replace unsaved edits when another tab changes storage until explicit reload', () => {
  localStorage.setItem(key, JSON.stringify(store([preset('ONE', 'One', 1, 'initial')])));
  render(<Harness />); query('local draft'); name('local name edit');
  localStorage.setItem(key, JSON.stringify(store([preset('ONE', 'Other tab', 1, 'external value')])));
  act(() => { window.dispatchEvent(new StorageEvent('storage', { key })); });
  expect((screen.getByLabelText('Draft transcript query') as HTMLInputElement).value).toBe('local draft');
  expect((screen.getByLabelText('Filter preset name') as HTMLInputElement).value).toBe('local name edit');
  expect((screen.getByRole('button', { name: 'Update saved filters' }) as HTMLButtonElement).disabled).toBe(true);
  expect(screen.getByText(/Reloading replaces local filter/)).toBeDefined();
  click('Reload saved filters');
  expect((screen.getByLabelText('Draft transcript query') as HTMLInputElement).value).toBe('external value');
  expect((screen.getByLabelText('Filter preset name') as HTMLInputElement).value).toBe('Other tab');
});

it('exports only the selected checklist scope and preserves Unicode and all filter fields', async () => {
  localStorage.setItem(key, JSON.stringify(store([preset('ONE', 'Қазақша', 1, 'private query'), preset('TWO', 'Other scope', 2, 'hidden other query')])));
  const blobs: Blob[] = [];
  vi.spyOn(URL, 'createObjectURL').mockImplementation(blob => { blobs.push(blob as Blob); return 'blob:PRESET_TEST'; });
  vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => {});
  const anchor = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});
  render(<Harness />); click('Export saved filters');
  expect(anchor).toHaveBeenCalledOnce();
  const packet = JSON.parse(await blobs[0].text());
  expect(packet).toEqual({ schema_version: 1, kind: 'cqa-filter-presets', checklist_id: 1, presets: [{ name: 'Қазақша', filters: { ...defaultFilters, text: 'private query' } }] });
});

it('previews a local import, discloses search text, renames collisions and persists only on explicit import', async () => {
  localStorage.setItem(key, JSON.stringify(store()));
  render(<Harness />); query('keep current draft');
  const file = new File([JSON.stringify({ schema_version: 1, kind: 'cqa-filter-presets', checklist_id: 1, presets: [{ name: 'One', filters: { ...defaultFilters, text: 'Қазақша imported' } }] })], 'portable.json', { type: 'application/json' });
  fireEvent.change(screen.getByLabelText('Import saved filter file'), { target: { files: [file] } });
  const preview = await screen.findByRole('region', { name: 'Filter import preview' });
  expect(within(preview).getByText(/Search text may contain private source quotations/)).toBeDefined();
  expect(within(preview).getByText('One → One (imported)')).toBeDefined();
  expect(get().presets).toHaveLength(1);
  click('Import previewed filters');
  expect(get().presets).toHaveLength(2);
  expect(get().presets.find((p: { name: string }) => p.name === 'One (imported)').filters.text).toBe('Қазақша imported');
  expect((screen.getByLabelText('Draft transcript query') as HTMLInputElement).value).toBe('keep current draft');
});

it.each([
  { data: '{invalid', message: 'not imported' },
  { data: JSON.stringify({ schema_version: 1, kind: 'cqa-filter-presets', checklist_id: 2, presets: [{ name: 'Other', filters: defaultFilters }] }), message: 'checklist v1' },
  { data: JSON.stringify({ schema_version: 1, kind: 'cqa-filter-presets', checklist_id: 1, presets: [{ name: 'Bad', filters: { ...defaultFilters, speaker: 'admin' } }] }), message: 'invalid or duplicate' },
  { data: 'x'.repeat(100_001), message: '100 KB' },
])('rejects malformed, cross-scope, invalid-field or oversized import without persistence ($message)', async ({ data, message }) => {
  localStorage.setItem(key, JSON.stringify(store())); const initial = localStorage.getItem(key);
  render(<Harness />);
  fireEvent.change(screen.getByLabelText('Import saved filter file'), { target: { files: [new File([data], 'invalid.json')] } });
  await waitFor(() => expect(screen.getByRole('alert').textContent).toContain(message));
  expect(localStorage.getItem(key)).toBe(initial);
  expect(screen.queryByRole('button', { name: 'Import previewed filters' })).toBeNull();
});

it('deleting a migrated preset changes only v2 and does not resurrect the preserved legacy preset', () => {
  const legacy = JSON.stringify({ schema_version: 1, presets: [preset('ONE', 'Legacy')] });
  localStorage.setItem(oldKey, legacy); localStorage.setItem('cqa-active-filter-v1:1', 'ONE');
  const view = render(<Harness />); click('Delete saved filters'); view.unmount(); render(<Harness />);
  expect(get().presets).toEqual([]); expect(localStorage.getItem(oldKey)).toBe(legacy);
  expect(screen.queryByRole('option', { name: 'Legacy' })).toBeNull();
});
