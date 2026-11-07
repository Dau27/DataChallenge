import { useEffect, useRef, useState } from 'react';

export type QueueFilters = { search: string; group: string; language: string; channel: string; status: string; appeals: string; critical: string; text: string; speaker: string };
export const defaultFilters: QueueFilters = { search: '', group: '', language: '', channel: '', status: '', appeals: '', critical: '', text: '', speaker: 'all' };
type Preset = { id: string; name: string; checklist_id: number; filters: QueueFilters };
type Store = { schema_version: 2; presets: Preset[]; active_by_checklist: Record<string, string> };
type State = { version: number; store: Store; selected: string; filters: QueueFilters; warning: string; message: string; external: boolean };
type ImportPreview = { fileName: string; checklist: number; presets: { name: string; originalName: string; filters: QueueFilters }[] };
const storageKey = 'cqa-filter-presets-v2';
const legacyKey = 'cqa-filter-presets-v1';
const activeKey = (version: number) => `cqa-active-filter-v1:${version}`;
const emptyStore = (): Store => ({ schema_version: 2, presets: [], active_by_checklist: {} });
const enums: Partial<Record<keyof QueueFilters, string[]>> = {
  language: ['', 'RU', 'KZ', 'EN'], channel: ['', 'agent chat', 'voice call'],
  status: ['', 'not_evaluated', 'queued', 'running', 'complete', 'needs_review', 'failed', 'interrupted'],
  appeals: ['', 'pending', 'none'], critical: ['', 'flagged', 'none'], speaker: ['all', 'operator', 'client', 'bot', 'system'],
};
const equalFilters = (a: QueueFilters, b: QueueFilters) => (Object.keys(defaultFilters) as (keyof QueueFilters)[]).every(k => a[k] === b[k]);
function validFilters(value: unknown): value is QueueFilters {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return false;
  const data = value as Record<string, unknown>;
  return Object.keys(data).length === Object.keys(defaultFilters).length && (Object.keys(defaultFilters) as (keyof QueueFilters)[])
    .every(k => typeof data[k] === 'string' && (data[k] as string).length <= (k === 'text' ? 200 : 2000) && (!enums[k] || enums[k]!.includes(data[k] as string)));
}
function validName(value: unknown): value is string { return typeof value === 'string' && !!value.trim() && value.length <= 80; }
function validatePresets(value: unknown): Preset[] {
  if (!Array.isArray(value) || value.length > 50) throw new Error('Invalid saved filters');
  const ids = new Set<string>();
  for (const p of value) {
    if (!p || typeof p.id !== 'string' || !p.id || p.id.length > 100 || ids.has(p.id) || !validName(p.name) ||
      !Number.isSafeInteger(p.checklist_id) || p.checklist_id < 1 || !validFilters(p.filters)) throw new Error('Invalid saved filters');
    ids.add(p.id);
  }
  return value;
}
function validateStore(value: unknown): Store {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error('Invalid saved filters');
  const data = value as Store;
  if (data.schema_version !== 2) throw new Error('Unsupported saved-filter version');
  const presets = validatePresets(data.presets);
  if (!data.active_by_checklist || typeof data.active_by_checklist !== 'object' || Array.isArray(data.active_by_checklist)) throw new Error('Invalid saved selection');
  for (const [version, id] of Object.entries(data.active_by_checklist)) {
    if (!/^[1-9]\d*$/.test(version) || !Number.isSafeInteger(Number(version)) || typeof id !== 'string' ||
      (id && !presets.some(p => p.id === id && p.checklist_id === Number(version)))) throw new Error('Invalid saved selection');
  }
  return { schema_version: 2, presets, active_by_checklist: { ...data.active_by_checklist } };
}
function readStore(): { store: Store; migrated: boolean } {
  const raw = localStorage.getItem(storageKey);
  if (raw !== null) return { store: validateStore(JSON.parse(raw)), migrated: false };
  const old = localStorage.getItem(legacyKey);
  if (old === null) return { store: emptyStore(), migrated: false };
  const legacy = JSON.parse(old);
  if (legacy?.schema_version !== 1) throw new Error('Unsupported saved-filter version');
  const presets = validatePresets(legacy.presets); const active: Record<string, string> = {};
  for (const version of new Set(presets.map(p => p.checklist_id))) {
    const selected = localStorage.getItem(activeKey(version));
    if (selected && presets.some(p => p.checklist_id === version && p.id === selected)) active[String(version)] = selected;
  }
  return { store: { schema_version: 2, presets, active_by_checklist: active }, migrated: true };
}
function persist(store: Store) { localStorage.setItem(storageKey, JSON.stringify(validateStore(store))); }
function stateFor(version: number, store: Store, warning = '', message = ''): State {
  const selected = store.active_by_checklist[String(version)] ?? '';
  const active = store.presets.find(p => p.id === selected && p.checklist_id === version);
  return { version, store, selected: active?.id ?? '', filters: { ...(active?.filters ?? defaultFilters) }, warning, message, external: false };
}
function load(version: number): State {
  try {
    const { store, migrated } = readStore();
    if (migrated) {
      try { persist(store); }
      catch { return stateFor(version, store, 'Saved filters were restored, but their upgrade could not be saved. Previous settings are retained.'); }
    }
    return stateFor(version, store);
  } catch {
    return stateFor(version, emptyStore(), 'Saved filters could not be restored. Filters still work; browser storage may be unavailable or invalid.');
  }
}
function uniqueName(name: string, names: Set<string>, suffix: string): string {
  if (!names.has(name)) return name;
  for (let i = 1; ; i++) {
    const tail = ` (${suffix}${i > 1 ? ` ${i}` : ''})`; const candidate = name.slice(0, 80 - tail.length) + tail;
    if (!names.has(candidate)) return candidate;
  }
}

export function useSavedFilters(version: number) {
  const [state, setState] = useState(() => load(version)); const [name, setName] = useState('');
  const [preview, setPreview] = useState<ImportPreview | null>(null); const input = useRef<HTMLInputElement>(null); const importSequence = useRef(0);
  useEffect(() => {
    importSequence.current++; setPreview(null);
    const loaded = load(version); setState(loaded); setName(loaded.store.presets.find(p => p.id === loaded.selected)?.name ?? '');
    return () => { importSequence.current++; };
  }, [version]);
  useEffect(() => {
    const changed = (event: StorageEvent) => {
      if (event.key === null || event.key === storageKey || event.key === legacyKey || event.key?.startsWith('cqa-active-filter-v1:')) setState(s => ({ ...s, external: true, message: '' }));
    };
    window.addEventListener('storage', changed);
    return () => window.removeEventListener('storage', changed);
  }, []);
  const current = state.version === version ? state : stateFor(version, state.store);
  const active = current.store.presets.find(p => p.id === current.selected && p.checklist_id === version);
  const dirty = !equalFilters(current.filters, active?.filters ?? defaultFilters);
  const setField = (key: keyof QueueFilters, value: string) => setState(s => ({ ...s, filters: { ...s.filters, [key]: value }, message: '' }));
  const warn = (warning: string) => setState(s => ({ ...s, warning, message: '' }));
  const reload = () => {
    const loaded = load(version); setState(loaded); setName(loaded.store.presets.find(p => p.id === loaded.selected)?.name ?? ''); setPreview(null);
  };
  const choose = (id: string) => {
    if (current.external) return;
    let preset = current.store.presets.find(p => p.id === id && p.checklist_id === version);
    let store = current.store; let warning = '';
    try {
      store = readStore().store;
      preset = store.presets.find(p => p.id === id && p.checklist_id === version);
      if (id && !preset) throw new Error('Preset removed');
      store = { ...store, active_by_checklist: { ...store.active_by_checklist, [version]: preset?.id ?? '' } }; persist(store);
    } catch { warning = 'Selection could not be saved in this browser. The current view is temporary.'; }
    setName(preset?.name ?? ''); setState({ ...stateFor(version, store, warning), selected: preset?.id ?? '', filters: { ...(preset?.filters ?? defaultFilters) } }); setPreview(null);
  };
  const writePreset = (action: 'create' | 'update' | 'rename' | 'duplicate') => {
    if (current.external || version < 1) return;
    try {
      const store = readStore().store; const saved = store.presets.find(p => p.id === current.selected && p.checklist_id === version);
      if (action !== 'create' && !saved) throw new Error('The selected preset no longer exists. Reload saved filters.');
      if (!validFilters(current.filters)) throw new Error('Current filters exceed the supported limits.');
      const names = new Set(store.presets.filter(p => p.checklist_id === version && (action !== 'rename' || p.id !== saved?.id)).map(p => p.name));
      let nextName = action === 'update' ? saved!.name : name.trim();
      if (action === 'duplicate') nextName = uniqueName(saved!.name, names, 'copy');
      if (!validName(nextName)) throw new Error('Enter a preset name of 1–80 characters.');
      if (action !== 'update' && names.has(nextName)) throw new Error('That preset name already exists. Choose a new name or use Update saved filters.');
      const preset: Preset = { id: action === 'create' || action === 'duplicate' ? crypto.randomUUID() : saved!.id,
        name: nextName, checklist_id: version, filters: { ...(action === 'rename' || action === 'duplicate' ? saved!.filters : current.filters) } };
      const next: Store = { schema_version: 2, presets: [...store.presets.filter(p => p.id !== preset.id), preset], active_by_checklist: { ...store.active_by_checklist, [version]: preset.id } };
      if (next.presets.length > 50) throw new Error('The browser supports at most 50 saved presets.');
      persist(next);
      const loaded = stateFor(version, next, '', action === 'rename' ? 'Saved filter renamed. Unsaved filter edits were retained.' : action === 'duplicate' ? 'Saved filter duplicated from its saved values.' : 'Filter preset saved.');
      if (action === 'rename') loaded.filters = { ...current.filters };
      setState(loaded); setName(preset.name); setPreview(null);
    } catch (e) { warn(`Filter preset was not saved. ${e instanceof Error ? e.message : 'Check browser storage.'}`); }
  };
  const remove = () => {
    if (current.external) return;
    try {
      const store = readStore().store;
      const next: Store = { ...store, presets: store.presets.filter(p => p.id !== current.selected || p.checklist_id !== version), active_by_checklist: { ...store.active_by_checklist, [version]: '' } };
      persist(next); setState(stateFor(version, next, '', 'Saved filter deleted. Other checklist presets were retained.')); setName(''); setPreview(null);
    } catch { warn('Filter preset could not be deleted from browser storage.'); }
  };
  const exportFile = () => {
    try {
      const presets = current.store.presets.filter(p => p.checklist_id === version).map(p => ({ name: p.name, filters: p.filters }));
      const blob = new Blob([JSON.stringify({ schema_version: 1, kind: 'cqa-filter-presets', checklist_id: version, presets }, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob); const anchor = document.createElement('a'); anchor.href = url; anchor.download = `cqa-filters-v${version}.json`;
      document.body.appendChild(anchor); try { anchor.click(); } finally { anchor.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000); }
    } catch { warn('Saved-filter file could not be exported. Retry the download.'); }
  };
  const inspectFile = async (file: File) => {
    const sequence = ++importSequence.current; setPreview(null);
    try {
      if (file.size > 100_000) throw new Error('Preset files must be at most 100 KB.');
      const data = JSON.parse(await file.text());
      if (sequence !== importSequence.current) return;
      if (!data || data.schema_version !== 1 || data.kind !== 'cqa-filter-presets' || data.checklist_id !== version ||
        !Array.isArray(data.presets) || !data.presets.length || data.presets.length > 50 || Object.keys(data).some(k => !['schema_version','kind','checklist_id','presets'].includes(k))) throw new Error(`Use a saved-filter file for checklist v${version}.`);
      const store = readStore().store; const names = new Set(store.presets.filter(p => p.checklist_id === version).map(p => p.name)); const importedNames = new Set<string>();
      const presets = data.presets.map((p: { name: unknown; filters: unknown }) => {
        if (!p || !validName(p.name) || !validFilters(p.filters) || importedNames.has(p.name.trim()) || Object.keys(p).some(k => !['name','filters'].includes(k))) throw new Error('The file contains an invalid or duplicate preset.');
        importedNames.add(p.name.trim()); const nextName = uniqueName(p.name.trim(), names, 'imported'); names.add(nextName);
        return { name: nextName, originalName: p.name.trim(), filters: { ...p.filters } };
      });
      if (store.presets.length + presets.length > 50) throw new Error('Import would exceed the 50-preset limit.');
      setPreview({ fileName: file.name, checklist: version, presets }); setState(s => ({ ...s, warning: '', message: '' }));
    } catch (e) { if (sequence === importSequence.current) warn(`Filter file was not imported. ${e instanceof Error ? e.message : 'Invalid JSON.'}`); }
  };
  const importFile = () => {
    if (!preview || preview.checklist !== version || current.external) return;
    try {
      const store = readStore().store;
      if (preview.presets.some(p => store.presets.some(existing => existing.checklist_id === version && existing.name === p.name))) throw new Error('Saved presets changed. Select the file again to preview its new names.');
      const presets = preview.presets.map(p => ({ id: crypto.randomUUID(), name: p.name, checklist_id: version, filters: p.filters }));
      const next: Store = { ...store, presets: [...store.presets, ...presets] }; persist(next);
      setState(s => ({ ...s, store: next, warning: '', message: `${presets.length} preset(s) imported. Current filters were retained; choose an imported preset to apply it.` })); setPreview(null);
    } catch (e) { warn(`Filter file was not imported. ${e instanceof Error ? e.message : 'Check browser storage.'}`); }
  };
  const controls = <div className="saved-filter-controls">
    <label>Saved filters · checklist v{version}<select aria-label="Saved filters" value={current.selected} disabled={current.external} onChange={e => choose(e.target.value)}>
      <option value="">Default filters</option>{current.store.presets.filter(p => p.checklist_id === version).map(p => <option key={p.id} value={p.id}>{p.name}</option>)}</select></label>
    <label>Preset name<input aria-label="Filter preset name" maxLength={80} value={name} onChange={e => setName(e.target.value)} placeholder="e.g. KZ pending reviews" /></label>
    <button className="secondary" disabled={!name.trim() || version < 1 || current.external} onClick={() => writePreset('create')}>Save filters</button>
    <button className="secondary" disabled={!active || !dirty || current.external} onClick={() => writePreset('update')}>Update saved filters</button>
    <button className="secondary" disabled={!active || !name.trim() || name.trim() === active.name || current.external} onClick={() => writePreset('rename')}>Rename saved filters</button>
    <button className="secondary" disabled={!active || current.external} onClick={() => writePreset('duplicate')}>Duplicate saved filters</button>
    <button className="secondary" disabled={!current.selected || current.external} onClick={remove}>Delete saved filters</button>
    <button className="secondary" disabled={!current.store.presets.some(p => p.checklist_id === version) || current.external} onClick={exportFile}>Export saved filters</button>
    <button className="secondary" disabled={version < 1 || current.external} onClick={() => input.current?.click()}>Choose filter file</button>
    <input className="visually-hidden" ref={input} type="file" accept="application/json,.json" aria-label="Import saved filter file" onChange={e => {
      const file = e.target.files?.[0]; e.target.value = ''; if (file) void inspectFile(file);
    }} />
    {dirty && <small>Unsaved filter changes</small>}{state.warning && <p role="alert">{state.warning}</p>}{state.message && <p role="status">{state.message}</p>}
    {current.external && <div role="alert"><p>Saved filters changed in another tab. Reloading replaces local filter and name edits.</p><button className="secondary" onClick={reload}>Reload saved filters</button></div>}
    {preview && <section aria-label="Filter import preview"><h3>Import preview: {preview.fileName}</h3>
      <p>{preview.presets.length} preset(s) for checklist v{preview.checklist}. Confirm this workspace uses that checklist. Existing presets will not be overwritten.</p>
      <p>Included fields: conversation ID, dataset, language, channel, status, appeal state, critical state, transcript search text and speaker. Search text may contain private source quotations.</p>
      {preview.presets.map(p => <details key={p.name}><summary>{p.originalName === p.name ? p.name : `${p.originalName} → ${p.name}`}</summary><pre style={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>{JSON.stringify(p.filters, null, 2)}</pre></details>)}
      <button className="secondary" disabled={current.external} onClick={importFile}>Import previewed filters</button><button className="secondary" onClick={() => setPreview(null)}>Cancel filter import</button>
    </section>}
    <small>Save filters creates a new preset. Update replaces selected filter values; rename keeps unsaved edits; duplicate copies saved values.</small>
    <small>Stored only in this browser. Default filters clears the view. Preset files include dataset names and search text; export only what you intend to keep.</small>
  </div>;
  return { filters: current.filters, setField, controls };
}
