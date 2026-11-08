import type { QueueFilters as Filters } from './SavedFilters';
import { defaultFilters } from './SavedFilters';
import { label } from './helpers';

export default function QueueFilters({ filters, groups, setField }: {
  filters: Filters; groups: string[]; setField: (key: keyof Filters, value: string) => void;
}) {
  const advanced = ['group', 'language', 'channel', 'status', 'appeals', 'critical'] as const;
  const active = advanced.filter(key => filters[key] !== defaultFilters[key]).length;
  const changed = (Object.keys(defaultFilters) as (keyof Filters)[]).some(key => filters[key] !== defaultFilters[key]);
  const names: Record<keyof Filters, string> = { search: 'Conversation ID', text: 'Transcript', speaker: 'Speaker', group: 'Dataset', language: 'Language', channel: 'Channel', status: 'State', appeals: 'Appeals', critical: 'Critical findings' };
  const displayValue = (key: keyof Filters) => key === 'status' ? label(filters[key]) : filters[key];
  return <div className="queue-filters">
    <div className="queue-search">
      <label>Conversation ID<input aria-label="Search conversation ID" placeholder="Find a conversation…" maxLength={2000} value={filters.search} onChange={e => setField('search', e.target.value)} /></label>
      <label>Transcript text<input aria-label="Search transcript text" placeholder="Search exact words or phrases…" maxLength={200} value={filters.text} onChange={e => setField('text', e.target.value)} /></label>
      <label>Speaker<select aria-label="Transcript speaker filter" value={filters.speaker} onChange={e => setField('speaker', e.target.value)}><option value="all">All speakers</option>{['operator', 'client', 'bot', 'system'].map(s => <option key={s}>{s}</option>)}</select></label>
    </div>
    <div className="filter-options-row">
      <details className="filter-options" open={active > 0}>
        <summary>Filters <span className="filter-count">{active ? `${active} active` : 'Dataset, language, status & more'}</span></summary>
        <div className="filter-options-grid">
          <label>Dataset<select aria-label="Dataset filter" value={filters.group} onChange={e => setField('group', e.target.value)}><option value="">All datasets</option>{groups.map(g => <option key={g}>{g}</option>)}</select></label>
          <label>Language<select aria-label="Language filter" value={filters.language} onChange={e => setField('language', e.target.value)}><option value="">All languages</option>{['RU', 'KZ', 'EN'].map(l => <option key={l}>{l}</option>)}</select></label>
          <label>Channel<select aria-label="Channel filter" value={filters.channel} onChange={e => setField('channel', e.target.value)}><option value="">All channels</option><option>agent chat</option><option>voice call</option></select></label>
          <label>Assessment state<select aria-label="Status filter" value={filters.status} onChange={e => setField('status', e.target.value)}><option value="">All states</option>{['not_evaluated', 'queued', 'running', 'complete', 'needs_review', 'failed', 'interrupted'].map(s => <option value={s} key={s}>{label(s)}</option>)}</select></label>
          <label>Appeals<select aria-label="Pending appeals filter" value={filters.appeals} onChange={e => setField('appeals', e.target.value)}><option value="">Any appeal state</option><option value="pending">Pending appeals</option><option value="none">No pending appeals</option></select></label>
          <label>Critical findings<select aria-label="Critical findings filter" value={filters.critical} onChange={e => setField('critical', e.target.value)}><option value="">Any critical state</option><option value="flagged">Critical findings</option><option value="none">No recorded critical findings</option></select></label>
        </div>
      </details>
      {changed && <button className="text-button clear-filters" onClick={() => (Object.keys(defaultFilters) as (keyof Filters)[]).forEach(key => setField(key, defaultFilters[key]))}>Clear filters</button>}
    </div>
    {changed && <div className="active-filter-chips" role="group" aria-label="Applied filters">
      {(Object.keys(defaultFilters) as (keyof Filters)[]).filter(key => filters[key] !== defaultFilters[key]).map(key => <button className="filter-chip" key={key}
        aria-label={`Remove ${names[key].toLowerCase()} filter`} title={`${names[key]}: ${displayValue(key)}`} onClick={() => setField(key, defaultFilters[key])}>
        <span>{names[key]}: <span className="filter-chip-value">{displayValue(key)}</span></span><span aria-hidden="true">×</span>
      </button>)}
    </div>}
  </div>;
}
