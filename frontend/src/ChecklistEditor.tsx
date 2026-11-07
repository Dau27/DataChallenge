import { useEffect, useState } from 'react';
import { api } from './api';
import type { Checklist, ChecklistVersion, Criterion } from './types';
import type { Run } from './App';

export default function ChecklistEditor({ version, versions, busy, run, onSave }: {
  version: ChecklistVersion; versions: ChecklistVersion[]; busy: boolean; run: Run; onSave: (id: number) => Promise<void>;
}) {
  const draftKey = `cqa-checklist-draft-${version.id}`;
  const [draft, setDraft] = useState<Checklist>(() => {
    try { const saved = sessionStorage.getItem(draftKey); if (saved) return JSON.parse(saved) as Checklist; } catch { /* Fall back to the immutable saved version. */ }
    return structuredClone(version.snapshot);
  });
  const dirty = JSON.stringify(draft) !== JSON.stringify(version.snapshot);
  useEffect(() => { if (dirty) sessionStorage.setItem(draftKey, JSON.stringify(draft)); else sessionStorage.removeItem(draftKey); }, [draft, dirty, draftKey]);
  const patch = (index: number, values: Partial<Criterion>) => setDraft(current => ({ ...current, criteria: current.criteria.map((c, i) => i === index ? { ...c, ...values } : c) }));
  const changeType = (index: number, type: Criterion['answer_type']) => {
    patch(index, { answer_type: type, weight: type === 'flag' ? null : draft.criteria[index].weight ?? '10',
      scale: type === 'scale' ? [{ value: '1', description: 'Fully meets the criterion' }, { value: '0', description: 'Does not meet the criterion' }] : [],
      ...(type === 'flag' ? { na_allowed: false, na_condition: null } : {}) });
  };
  return <>
    <div className="page-heading"><div><div className="eyebrow">CONFIGURATION</div><h1>Checklist editor</h1><p>Drafts are kept in this browser session. Saving creates a new immutable version.</p></div><button className="primary" disabled={busy || !dirty} onClick={() => void run(async () => { const saved = await api<ChecklistVersion>('/checklists', draft); sessionStorage.removeItem(draftKey); await onSave(saved.id); })}>Save new version →</button></div>
    <div className="editor-layout"><div>
      <section className="panel editor-meta"><div className="inline-actions"><span className="badge">Based on v{version.id}</span><span className={`badge ${dirty ? 'needs_review' : 'complete'}`}>{dirty ? 'Unsaved draft' : 'Saved snapshot'}</span></div>
        <label>Checklist name<input value={draft.name} onChange={e => setDraft({ ...draft, name: e.target.value })} /></label>
        <p>Numerical points = weight × value / maximum allowed scale value. N/A excludes the criterion and redistributes applicable weights. Flags do not affect the score.</p>
      </section>
      <section className="panel section-editor"><div className="table-toolbar"><h2>Sections</h2><button className="text-button" onClick={() => setDraft({ ...draft, sections: [...draft.sections, { id: `section_${crypto.randomUUID()}`, title: 'New section' }] })}>+ Add section</button></div>
        {draft.sections.map((section, i) => <div className="section-row" key={section.id}><input aria-label={`Section ${i + 1} title`} value={section.title} onChange={e => setDraft({ ...draft, sections: draft.sections.map((s, j) => j === i ? { ...s, title: e.target.value } : s) })} /><button className="text-button danger" disabled={draft.criteria.some(c => c.section_id === section.id)} title="Move or remove this section's criteria before removing the section" onClick={() => setDraft({ ...draft, sections: draft.sections.filter(s => s.id !== section.id) })}>Remove</button></div>)}
      </section>
      {draft.criteria.map((criterion, index) => <section className="panel criterion-editor" key={criterion.id}>
        <div className="criterion-editor-title"><span className="ordinal">{String(index + 1).padStart(2, '0')}</span><strong>{criterion.name || 'New criterion'}</strong><button className="text-button danger" onClick={() => setDraft({ ...draft, criteria: draft.criteria.filter((_, i) => i !== index) })}>Remove criterion</button></div>
        <div className="form-grid"><label>Name<input value={criterion.name} onChange={e => patch(index, { name: e.target.value })} /></label>
          <label>Section<select value={criterion.section_id} onChange={e => patch(index, { section_id: e.target.value })}>{draft.sections.map(s => <option key={s.id} value={s.id}>{s.title}</option>)}</select></label>
          <label>Answer type<select value={criterion.answer_type} onChange={e => changeType(index, e.target.value as Criterion['answer_type'])}><option value="binary">Binary · Yes / No</option><option value="scale">Numerical scale</option><option value="flag">Unscored flag</option></select></label>
          <label>Weight<input type="number" min="0" step="any" disabled={criterion.answer_type === 'flag'} value={criterion.weight ?? ''} placeholder={criterion.answer_type === 'flag' ? 'Unscored' : 'Weight'} onChange={e => patch(index, { weight: e.target.value })} /></label>
        </div>
        <label>Criterion definition<textarea rows={3} value={criterion.description} onChange={e => patch(index, { description: e.target.value })} /></label>
        <label className="checkbox-label"><input type="checkbox" disabled={criterion.answer_type === 'flag'} checked={criterion.na_allowed} onChange={e => patch(index, { na_allowed: e.target.checked, na_condition: e.target.checked ? '' : null })} /> Allow N/A under an exact condition</label>
        {criterion.na_allowed && <label>N/A condition<textarea rows={2} value={criterion.na_condition ?? ''} onChange={e => patch(index, { na_condition: e.target.value })} /></label>}
        {criterion.answer_type === 'scale' && <div className="anchor-editor"><h3>Allowed values and anchors</h3><p>Only these values are valid. A nonzero minimum still uses value ÷ maximum.</p>
          {criterion.scale.map((anchor, i) => <div className="anchor-row" key={i}><input type="number" min="0" step="any" aria-label={`Anchor ${i + 1} value for ${criterion.name}`} value={anchor.value} onChange={e => patch(index, { scale: criterion.scale.map((a, j) => j === i ? { ...a, value: e.target.value } : a) })} /><input aria-label={`Anchor ${i + 1} description for ${criterion.name}`} value={anchor.description} onChange={e => patch(index, { scale: criterion.scale.map((a, j) => j === i ? { ...a, description: e.target.value } : a) })} /><button className="text-button danger" onClick={() => patch(index, { scale: criterion.scale.filter((_, j) => j !== i) })}>Remove</button></div>)}
          <button className="text-button" onClick={() => patch(index, { scale: [...criterion.scale, { value: '', description: '' }] })}>+ Add allowed value</button>
        </div>}
        <small className="muted">Stable criterion ID: {criterion.id}</small>
      </section>)}
      <button className="add-criterion" disabled={!draft.sections.length} onClick={() => setDraft({ ...draft, criteria: [...draft.criteria, { id: `criterion_${crypto.randomUUID()}`, name: '', description: '', section_id: draft.sections[0].id, answer_type: 'binary', weight: '10', na_allowed: false, na_condition: null, scale: [] }] })}>+ Add a criterion</button>
    </div><aside className="editor-help"><div className="panel"><h2>Version history</h2><p>Select a saved version using the picker above.</p>{versions.map(v => <div className="version-history" key={v.id}><strong>v{v.id}{v.id === version.id ? ' · selected' : ''}</strong><small>{new Date(v.created_at).toLocaleString()}</small><span>{v.snapshot.criteria.length} criteria</span></div>)}</div>
      <div className="panel"><h2>Saving a version</h2><p>A save includes definitions, weights, anchors, sections, N/A conditions, and the scoring policy.</p><p>Run a new evaluation with the selected saved version to apply changes. Draft changes never alter results.</p><small className="muted">Configuration validation happens on the backend. Unsupported configurations are rejected with details.</small></div>
    </aside></div>
  </>;
}
