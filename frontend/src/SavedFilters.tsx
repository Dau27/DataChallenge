import { useEffect, useState } from 'react';

export type QueueFilters = { search: string; group: string; language: string; channel: string; status: string; appeals: string; critical: string; text: string; speaker: string };
export const defaultFilters: QueueFilters = { search: '', group: '', language: '', channel: '', status: '', appeals: '', critical: '', text: '', speaker: 'all' };
type Preset = { id: string; name: string; checklist_id: number; filters: QueueFilters };
const storageKey = 'cqa-filter-presets-v1';
const activeKey = (version: number) => `cqa-active-filter-v1:${version}`;
const enums: Partial<Record<keyof QueueFilters, string[]>> = {
  language: ['', 'RU', 'KZ', 'EN'], channel: ['', 'agent chat', 'voice call'],
  status: ['', 'not_evaluated', 'queued', 'running', 'complete', 'needs_review', 'failed', 'interrupted'],
  appeals: ['', 'pending', 'none'], critical: ['', 'flagged', 'none'], speaker: ['all', 'operator', 'client', 'bot', 'system'],
};
function validFilters(value: unknown): value is QueueFilters {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return false;
  const data = value as Record<string, unknown>;
  return Object.keys(data).length === Object.keys(defaultFilters).length && (Object.keys(defaultFilters) as (keyof QueueFilters)[])
    .every(k => typeof data[k] === 'string' && (data[k] as string).length <= (k === 'text' ? 200 : 2000) && (!enums[k] || enums[k]!.includes(data[k] as string)));
}
function readPresets(): Preset[] {
  const raw = localStorage.getItem(storageKey);
  if (!raw) return [];
  const data = JSON.parse(raw);
  if (data?.schema_version !== 1 || !Array.isArray(data.presets) || data.presets.length > 50) throw new Error('Invalid saved filters');
  const ids = new Set<string>();
  for (const p of data.presets) {
    if (!p || typeof p.id !== 'string' || !p.id || p.id.length > 100 || ids.has(p.id) || typeof p.name !== 'string' || !p.name.trim() || p.name.length > 80 ||
      !Number.isSafeInteger(p.checklist_id) || p.checklist_id < 1 || !validFilters(p.filters)) throw new Error('Invalid saved filters');
    ids.add(p.id);
  }
  return data.presets;
}
function load(version: number) {
  try {
    const presets = readPresets(); const selected = localStorage.getItem(activeKey(version)) ?? '';
    const preset = presets.find(p => p.id === selected && p.checklist_id === version);
    return { version, presets, selected: preset?.id ?? '', filters: { ...(preset?.filters ?? defaultFilters) }, warning: '' };
  } catch {
    return { version, presets: [] as Preset[], selected: '', filters: { ...defaultFilters }, warning: 'Saved filters could not be restored. Filters still work; browser storage may be unavailable or invalid.' };
  }
}

export function useSavedFilters(version: number) {
  const [state, setState] = useState(() => load(version)); const [name, setName] = useState('');
  useEffect(() => { const loaded = load(version); setState(loaded); setName(loaded.presets.find(p => p.id === loaded.selected)?.name ?? ''); }, [version]);
  const current = state.version === version ? state : { ...state, filters: { ...defaultFilters }, selected: '' };
  const setField = (key: keyof QueueFilters, value: string) => setState(s => ({ ...s, filters: { ...s.filters, [key]: value } }));
  const choose = (id: string) => {
    const preset = state.presets.find(p => p.id === id && p.checklist_id === version);
    let warning = '';
    try { localStorage.setItem(activeKey(version), preset?.id ?? ''); } catch { warning = 'Selection could not be saved in this browser.'; }
    setName(preset?.name ?? ''); setState(s => ({ ...s, selected: preset?.id ?? '', filters: { ...(preset?.filters ?? defaultFilters) }, warning }));
  };
  const save = () => {
    if (!name.trim() || version < 1) return;
    try {
      // Read again to preserve other checklist presets, including changes from another tab.
      const presets = readPresets(); const existing = presets.find(p => p.checklist_id === version && p.name === name.trim());
      const preset: Preset = { id: existing?.id ?? crypto.randomUUID(), name: name.trim(), checklist_id: version, filters: { ...current.filters } };
      const next = [...presets.filter(p => p.id !== preset.id), preset];
      if (next.length > 50) throw new Error('Preset limit');
      localStorage.setItem(storageKey, JSON.stringify({ schema_version: 1, presets: next }));
      localStorage.setItem(activeKey(version), preset.id);
      setState(s => ({ ...s, presets: next, selected: preset.id, warning: '' })); setName(preset.name);
    } catch { setState(s => ({ ...s, warning: 'Filter preset was not saved. Check browser storage or the 50-preset limit.' })); }
  };
  const remove = () => {
    try {
      const next = readPresets().filter(p => p.id !== current.selected || p.checklist_id !== version);
      localStorage.setItem(storageKey, JSON.stringify({ schema_version: 1, presets: next })); localStorage.removeItem(activeKey(version));
      setState({ version, presets: next, selected: '', filters: { ...defaultFilters }, warning: '' }); setName('');
    } catch { setState(s => ({ ...s, warning: 'Filter preset could not be deleted from browser storage.' })); }
  };
  const active = current.presets.find(p => p.id === current.selected && p.checklist_id === version);
  const dirty = active && JSON.stringify(active.filters) !== JSON.stringify(current.filters);
  const controls = <div className="saved-filter-controls">
    <label>Saved filters · checklist v{version}<select aria-label="Saved filters" value={current.selected} onChange={e => choose(e.target.value)}>
      <option value="">Default filters</option>{current.presets.filter(p => p.checklist_id === version).map(p => <option key={p.id} value={p.id}>{p.name}</option>)}</select></label>
    <label>Preset name<input aria-label="Filter preset name" maxLength={80} value={name} onChange={e => setName(e.target.value)} placeholder="e.g. KZ pending reviews" /></label>
    <button className="secondary" disabled={!name.trim() || version < 1} onClick={save}>Save filters</button>
    <button className="secondary" disabled={!current.selected} onClick={remove}>Delete saved filters</button>
    {dirty && <small>Unsaved filter changes</small>}{state.warning && <p role="alert">{state.warning}</p>}
    <small>Stored only in this browser. Choosing Default filters clears the current view.</small>
  </div>;
  return { filters: current.filters, setField, controls };
}
