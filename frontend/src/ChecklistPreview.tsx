import { useEffect, useState } from 'react';
import { api } from './api';
import type { Checklist, ChecklistPreview, ChecklistVersion, FieldIssue } from './types';

export const fieldId = (path: (string | number)[]) => `draft-${path.join('-') || 'root'}`;
export function useChecklistPreview(version: ChecklistVersion, draft: Checklist) {
  const signature = JSON.stringify(draft);
  const unchanged = signature === JSON.stringify(version.snapshot);
  const [state, setState] = useState<{ signature: string; preview?: ChecklistPreview; error?: string } | null>(null);
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    if (unchanged) return;
    let cancelled = false;
    const timer = setTimeout(() => {
      void api<ChecklistPreview>(`/checklists/${version.id}/preview`, draft).then(
        preview => { if (!cancelled) setState({ signature, preview }); },
        error => { if (!cancelled) setState({ signature, error: error.message }); });
    }, 150);
    return () => { cancelled = true; clearTimeout(timer); };
  }, [signature, version.id, retry]);
  const current = unchanged ? { signature, preview: { valid: true, errors: [], changes: [] } as ChecklistPreview }
    : state?.signature === signature ? state : null;
  return { preview: current?.preview, error: current?.error, pending: !current, retry: () => { setState(null); setRetry(v => v + 1); } };
}

export function FieldErrors({ path, issues }: { path: (string | number)[]; issues: FieldIssue[] }) {
  const messages = issues.filter(e => e.location.join('.') === path.join('.')).map(e => e.message);
  return messages.length ? <small className="field-error" id={`${fieldId(path)}-error`}>{messages.join(' ')}</small> : null;
}

export function ChangePreview({ preview, pending, error, retry }: { preview?: ChecklistPreview; pending: boolean; error?: string; retry: () => void }) {
  const display = (value: unknown) => value === null || value === undefined ? 'Not set' : typeof value === 'object' ? JSON.stringify(value) : String(value);
  return <section className="panel change-preview" aria-label="Checklist change preview" id={fieldId([])} tabIndex={-1}>
    <h2>Preview changes</h2><p>Compared with the saved version. Preview does not save a version or evaluate a conversation.</p>
    {pending && <p role="status">Validating draft…</p>}
    {error && <div role="alert"><p>{error}</p><button className="secondary" onClick={retry}>Retry validation</button></div>}
    {preview && <><strong className={preview.valid ? 'valid-draft' : 'field-error'}>{preview.valid ? 'Configuration valid' : `Fix ${preview.errors.length} configuration error(s) before saving`}</strong>
      {!!preview.errors.length && <ul className="validation-summary">{preview.errors.map((issue, i) => <li key={i}><button className="text-button" onClick={() => {
        const field = document.getElementById(fieldId(issue.location)) ?? document.getElementById(fieldId([]));
        field?.focus(); field?.scrollIntoView({ block: 'center' });
      }}>{issue.label || 'Checklist field'}: {issue.message}</button></li>)}</ul>}
      {!preview.changes.length ? <p>No changes from the saved version.</p> : <div className="table-scroll"><table><thead><tr><th>Changed field</th><th>Saved</th><th>Draft</th></tr></thead><tbody>
        {preview.changes.map((change, i) => <tr key={i}><td>{change.label}</td><td>{display(change.before)}</td><td>{display(change.after)}</td></tr>)}
      </tbody></table></div>}
    </>}
  </section>;
}
