import { useState } from 'react';
import type { Conversation } from './types';
import type { QueueFilters } from './SavedFilters';
import { statusOf } from './helpers';

export type QueueDensity = 'comfortable' | 'compact';
const densityKey = 'cqa-queue-density-v1';
export function useQueueDensity() {
  const [density, setDensity] = useState<QueueDensity>(() => {
    try { return localStorage.getItem(densityKey) === 'compact' ? 'compact' : 'comfortable'; }
    catch { return 'comfortable'; }
  });
  const choose = (next: QueueDensity) => {
    setDensity(next);
    try { localStorage.setItem(densityKey, next); } catch { /* The current layout still works when storage is unavailable. */ }
  };
  return [density, choose] as const;
}

export default function QueueViewTools({ rows, filters, setField, density, onDensity, unavailable }: {
  rows: Conversation[]; filters: QueueFilters; setField: (key: keyof QueueFilters, value: string) => void;
  density: QueueDensity; onDensity: (value: QueueDensity) => void; unavailable: boolean;
}) {
  const views = [
    { name: 'All in view', status: '', appeals: '', critical: '', count: rows.length },
    { name: 'Needs review', status: 'needs_review', appeals: '', critical: '', count: rows.filter(r => statusOf(r) === 'needs_review').length },
    { name: 'Pending appeals', status: '', appeals: 'pending', critical: '', count: rows.filter(r => (r.pending_appeals ?? 0) > 0).length },
    { name: 'Critical findings', status: '', appeals: '', critical: 'flagged', count: rows.filter(r => !!r.critical_findings?.length).length },
  ];
  return <div className="queue-view-bar">
    <div className="quick-review-views" role="group" aria-label="Quick review views">
      {views.map(view => <button key={view.name} className="quick-view" aria-pressed={filters.status === view.status && filters.appeals === view.appeals && filters.critical === view.critical}
        disabled={unavailable} title="Use this review view within the current search, dataset, language and channel."
        onClick={() => { setField('status', view.status); setField('appeals', view.appeals); setField('critical', view.critical); }}>
        {view.name}<span>{unavailable ? '—' : view.count}</span>
      </button>)}
    </div>
    <label className="row-density">Row spacing<select aria-label="Queue row spacing" value={density} onChange={e => onDensity(e.target.value as QueueDensity)}>
      <option value="comfortable">Comfortable</option><option value="compact">Compact</option>
    </select></label>
  </div>;
}
