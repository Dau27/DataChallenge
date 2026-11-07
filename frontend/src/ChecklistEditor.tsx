import { useEffect, useState } from 'react';
import { api, ApiError } from './api';
import type { Checklist, ChecklistVersion, Criterion, FieldIssue } from './types';
import { ChangePreview, FieldErrors, fieldId, useChecklistPreview } from './ChecklistPreview';
import type { Run } from './App';
import WeightImpact from './WeightImpact';

export default function ChecklistEditor({ version, versions, busy, run, onSave }: {
  version: ChecklistVersion; versions: ChecklistVersion[]; busy: boolean; run: Run; onSave: (id: number) => Promise<void>;
}) {
  const draftKey = `cqa-checklist-draft-${version.id}`;
  const [draft, setDraft] = useState<Checklist>(() => {
    try { const saved = sessionStorage.getItem(draftKey); if (saved) return JSON.parse(saved) as Checklist; } catch { /* Fall back to the immutable saved version. */ }
    return structuredClone(version.snapshot);
  });
  const dirty = JSON.stringify(draft) !== JSON.stringify(version.snapshot);
  const validation = useChecklistPreview(version, draft);
  const [saveErrors, setSaveErrors] = useState<{ draft: string; issues: FieldIssue[] } | null>(null);
  const issues = [...(validation.preview?.errors ?? []), ...(saveErrors?.draft === JSON.stringify(draft) ? saveErrors.issues : [])];
  const field = (path: (string | number)[], label?: string) => ({ id: fieldId(path), 'aria-label': label,
    'aria-invalid': issues.some(e => e.location.join('.') === path.join('.')),
    'aria-describedby': issues.some(e => e.location.join('.') === path.join('.')) ? `${fieldId(path)}-error` : undefined });
  const errors = (path: (string | number)[]) => <FieldErrors path={path} issues={issues} />;
  useEffect(() => { if (dirty) sessionStorage.setItem(draftKey, JSON.stringify(draft)); else sessionStorage.removeItem(draftKey); }, [draft, dirty, draftKey]);
  const patch = (index: number, values: Partial<Criterion>) => setDraft(current => ({ ...current, criteria: current.criteria.map((c, i) => i === index ? { ...c, ...values } : c) }));
  const changeType = (index: number, type: Criterion['answer_type']) => {
    patch(index, { answer_type: type, weight: type === 'flag' ? null : draft.criteria[index].weight ?? '10',
      scale: type === 'scale' ? [{ value: '1', description: 'Fully meets the criterion' }, { value: '0', description: 'Does not meet the criterion' }] : [],
      ...(type === 'flag' ? { na_allowed: false, na_condition: null } : {}) });
  };
  return <>
    <div className="page-heading"><div><div className="eyebrow">CONFIGURATION</div><h1>Checklist editor</h1><p>Drafts are kept in this browser session. Saving creates a new immutable version.</p></div><button className="primary" disabled={busy || !dirty || !validation.preview?.valid || validation.pending || !!validation.error} onClick={() => void run(async () => {
      try { const saved = await api<ChecklistVersion>('/checklists', draft); sessionStorage.removeItem(draftKey); await onSave(saved.id); }
      catch (error) { if (error instanceof ApiError) setSaveErrors({ draft: JSON.stringify(draft), issues: error.issues }); throw error; }
    })}>Save new version →</button></div>
    <ChangePreview {...validation} />
    <WeightImpact version={version} draft={draft} />
    <div className="editor-layout"><div id={fieldId(['criteria'])} tabIndex={-1}>{errors(['criteria'])}
      <section className="panel editor-meta"><div className="inline-actions"><span className="badge">Based on v{version.id}</span><span className={`badge ${dirty ? 'needs_review' : 'complete'}`}>{dirty ? 'Unsaved draft' : 'Saved snapshot'}</span></div>
        <label>Checklist name<input {...field(['name'], 'Checklist name')} value={draft.name} onChange={e => setDraft({ ...draft, name: e.target.value })} />{errors(['name'])}</label>
        <p>Numerical points = weight × value / maximum allowed scale value. N/A excludes the criterion and redistributes applicable weights. Flags do not affect the score.</p>
      </section>
      <section className="panel section-editor" id={fieldId(['sections'])} tabIndex={-1}><div className="table-toolbar"><h2>Sections</h2><button className="text-button" onClick={() => setDraft({ ...draft, sections: [...draft.sections, { id: `section_${crypto.randomUUID()}`, title: 'New section' }] })}>+ Add section</button></div>{errors(['sections'])}
        {draft.sections.map((section, i) => <div className="section-row" key={section.id}><div className="section-title-field"><input {...field(['sections', i, 'title'], `Section ${i + 1} title`)} value={section.title} onChange={e => setDraft({ ...draft, sections: draft.sections.map((s, j) => j === i ? { ...s, title: e.target.value } : s) })} />{errors(['sections', i, 'title'])}</div><button className="text-button danger" disabled={draft.criteria.some(c => c.section_id === section.id)} title="Move or remove this section's criteria before removing the section" onClick={() => setDraft({ ...draft, sections: draft.sections.filter(s => s.id !== section.id) })}>Remove</button></div>)}
      </section>
      {draft.criteria.map((criterion, index) => <section className="panel criterion-editor" key={criterion.id} id={fieldId(['criteria', index])} tabIndex={-1}>
        <div className="criterion-editor-title"><span className="ordinal">{String(index + 1).padStart(2, '0')}</span><strong>{criterion.name || 'New criterion'}</strong><button className="text-button danger" onClick={() => setDraft({ ...draft, criteria: draft.criteria.filter((_, i) => i !== index) })}>Remove criterion</button></div>
        {errors(['criteria', index])}
        <div className="form-grid"><label>Name<input {...field(['criteria', index, 'name'], 'Name')} value={criterion.name} onChange={e => patch(index, { name: e.target.value })} />{errors(['criteria', index, 'name'])}</label>
          <label>Section<select {...field(['criteria', index, 'section_id'], 'Section')} value={criterion.section_id} onChange={e => patch(index, { section_id: e.target.value })}>{draft.sections.map(s => <option key={s.id} value={s.id}>{s.title}</option>)}</select>{errors(['criteria', index, 'section_id'])}</label>
          <label>Answer type<select {...field(['criteria', index, 'answer_type'], 'Answer type')} value={criterion.answer_type} onChange={e => changeType(index, e.target.value as Criterion['answer_type'])}><option value="binary">Binary · Yes / No</option><option value="scale">Numerical scale</option><option value="flag">Unscored flag</option></select>{errors(['criteria', index, 'answer_type'])}</label>
          <label>Weight<input {...field(['criteria', index, 'weight'], 'Weight')} type="number" min="0" step="any" disabled={criterion.answer_type === 'flag'} value={criterion.weight ?? ''} placeholder={criterion.answer_type === 'flag' ? 'Unscored' : 'Weight'} onChange={e => patch(index, { weight: e.target.value })} />{errors(['criteria', index, 'weight'])}</label>
        </div>
        <label>Criterion definition<textarea {...field(['criteria', index, 'description'], 'Criterion definition')} rows={3} value={criterion.description} onChange={e => patch(index, { description: e.target.value })} />{errors(['criteria', index, 'description'])}</label>
        <label className="checkbox-label"><input type="checkbox" disabled={criterion.answer_type === 'flag'} checked={criterion.na_allowed} onChange={e => patch(index, { na_allowed: e.target.checked, na_condition: e.target.checked ? '' : null })} /> Allow N/A under an exact condition</label>
        {criterion.na_allowed && <label>N/A condition<textarea {...field(['criteria', index, 'na_condition'], 'N/A condition')} rows={2} value={criterion.na_condition ?? ''} onChange={e => patch(index, { na_condition: e.target.value })} />{errors(['criteria', index, 'na_condition'])}</label>}
        {criterion.answer_type === 'scale' && <div className="anchor-editor" {...field(['criteria', index, 'scale'])} tabIndex={-1}><h3>Allowed values and anchors</h3><p>Only these values are valid. A nonzero minimum still uses value ÷ maximum.</p>{errors(['criteria', index, 'scale'])}
          {criterion.scale.map((anchor, i) => <div className="anchor-row" key={i}><div className="anchor-value-field"><input {...field(['criteria', index, 'scale', i, 'value'], `Anchor ${i + 1} value for ${criterion.name}`)} type="number" min="0" step="any" value={anchor.value} onChange={e => patch(index, { scale: criterion.scale.map((a, j) => j === i ? { ...a, value: e.target.value } : a) })} />{errors(['criteria', index, 'scale', i, 'value'])}</div><div className="anchor-description-field"><input {...field(['criteria', index, 'scale', i, 'description'], `Anchor ${i + 1} description for ${criterion.name}`)} value={anchor.description} onChange={e => patch(index, { scale: criterion.scale.map((a, j) => j === i ? { ...a, description: e.target.value } : a) })} />{errors(['criteria', index, 'scale', i, 'description'])}</div><button className="text-button danger" onClick={() => patch(index, { scale: criterion.scale.filter((_, j) => j !== i) })}>Remove</button></div>)}
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
