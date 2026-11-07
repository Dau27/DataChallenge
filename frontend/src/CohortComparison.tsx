import { useEffect, useRef, useState } from 'react';
import { api } from './api';
import { useLatestResource } from './useLatestResource';
import CohortPairPreview, { cohortAnswerLabel } from './CohortPairPreview';
import { cohortFields, cohortResultMatches, cohortSelectorKey, pairStatuses } from './cohortTypes';
import type { CohortBasis, CohortCriterion, CohortField, CohortOptions, CohortPair, CohortRequest, CohortResult, CohortSelector, CohortSide } from './cohortTypes';
import './cohortComparison.css';

const fieldNames: Record<CohortField, string> = { model: 'model', prompt_version: 'prompt version', schema_version: 'schema version', evidence_validation_version: 'validation version' };
const statusNames = { matched: 'Comparable totals', missing_left: 'Baseline missing', missing_right: 'Candidate missing', missing_both: 'Both missing',
  failed: 'Failed / interrupted', pending: 'Pending', unresolved: 'Unresolved', incompatible: 'Incompatible totals', no_numeric_total: 'No numeric total', invalid: 'Invalid / unavailable answers' };

function criterionKind(row: CohortCriterion) {
  if (row.left_type !== row.right_type) return `${row.left_type ?? 'absent'} → ${row.right_type ?? 'absent'}`;
  return row.left_type === 'flag' ? 'Unscored flag' : row.left_type ?? 'Unavailable definition';
}

function optionsValid(data: CohortOptions) {
  try {
    if (!data || data.version !== 1 || data.max_pairs !== 200 || !Array.isArray(data.datasets) || !Array.isArray(data.checklists)
        || !Number.isSafeInteger(data.unavailable_dataset_identifiers) || data.unavailable_dataset_identifiers < 0) return false;
    if (new Set(data.datasets.map(dataset => dataset.dataset_group_id)).size !== data.datasets.length) return false;
    return data.datasets.every(dataset => {
      if (typeof dataset.dataset_group_id !== 'string' || !Number.isSafeInteger(dataset.source_revision_count) || dataset.source_revision_count < 0 || !Array.isArray(dataset.checklists)) return false;
      return dataset.checklists.every(profile => {
        if (!profile.fields || !Number.isSafeInteger(profile.run_count) || profile.run_count < 0) return false;
        return cohortFields.every(field => {
          const options = profile.fields[field];
          return Array.isArray(options?.values) && Number.isSafeInteger(options.unknown_count) && options.unknown_count >= 0
            && options.values.every(item => typeof item.value === 'string' && item.value.length <= 150 && Number.isSafeInteger(item.count) && item.count >= 0)
            && options.values.reduce((count, item) => count + item.count, options.unknown_count) === profile.run_count;
        });
      }) && dataset.checklists.reduce((count, profile) => count + profile.run_count, 0) === dataset.saved_evaluation_count;
    }) && data.checklists.every(version => Number.isSafeInteger(version.checklist_id) && version.checklist_id > 0);
  } catch { return false; }
}

function RunIdentity({ side }: { side: CohortSide | null }) {
  if (!side) return <span>Missing</span>;
  return <div className="cohort-run-identity"><strong>{side.state} · {side.completeness}</strong><small>{side.evaluation_id}</small>
    {side.run_completeness !== side.completeness && <small>Current effective workflow: {side.run_completeness}</small>}
    {side.basis_available && !side.criterion_coverage_valid && <small>Saved answer coverage does not match this checklist.</small>}
    <small>Saved {new Date(side.created_at).toLocaleString()}</small><small>{side.basis_available ? `Saved total: ${side.total_state === 'invalid' ? 'invalid saved value' : side.total ?? 'unavailable'}` : 'Answer set unavailable'}</small>
    {side.cached && <small>Cached reuse{side.cached_from ? ` from ${side.cached_from}` : ' · origin ID withheld'}{side.cache_origin_present ? '' : ' · origin unavailable'}</small>}
    {side.provenance_conflict && <small>Recorded checklist hash conflicts with the saved version. Excluded from comparable aggregates.</small>}
    <details><summary>Recorded configuration</summary><dl><dt>Checklist</dt><dd>v{side.checklist_id} · {side.checklist_hash}</dd><dt>Saved score rules</dt><dd>{side.saved_scoring_version ?? 'Unknown'}</dd>
      {(['provider', 'model', 'prompt_version', 'schema_version', 'evidence_validation_version', 'scoring_version', 'prompt_hash', 'schema_hash', 'request_schema_hash', 'checklist_hash'] as const).map(field => <div key={field}><dt>{field.replaceAll('_', ' ')}</dt><dd>{side.provenance[field] ?? 'Unknown'}</dd></div>)}
      <dt>Generation</dt><dd>{side.provenance.generation_recorded ? JSON.stringify(side.provenance.generation) : 'Unknown'}</dd>
      <dt>Recorded response models</dt><dd>{side.provenance.response_models.join(', ') || 'Unknown'}</dd><dt>Updated</dt><dd>{side.updated_at}</dd></dl></details>
  </div>;
}

export default function CohortComparison({ onOpenPair }: { onOpenPair: (leftEvaluationId: string, rightEvaluationId: string) => void }) {
  const [open, setOpen] = useState(false);
  const options = useLatestResource(open ? 'cohort-options-open' : 'cohort-options-closed', async () => {
    if (!open) return null;
    const result = await api<CohortOptions>('/insights/cohorts/options');
    if (!optionsValid(result)) throw new Error('Recorded cohort options are unavailable. Refresh the options.');
    return result;
  }, true);
  const [datasetId, setDatasetId] = useState(''); const [left, setLeft] = useState<CohortSelector>({ checklist_id: 0 });
  const [right, setRight] = useState<CohortSelector>({ checklist_id: 0 }); const [basis, setBasis] = useState<CohortBasis>('effective');
  const dataOptions = options.value;
  const dataset = dataOptions?.datasets.find(item => item.dataset_group_id === datasetId) ?? dataOptions?.datasets[0];
  const firstVersion = dataset?.checklists[0]?.checklist_id ?? dataOptions?.checklists[0]?.checklist_id ?? 0;
  const selectedLeft = dataOptions?.checklists.some(version => version.checklist_id === left.checklist_id) ? left : { checklist_id: firstVersion };
  const selectedRight = dataOptions?.checklists.some(version => version.checklist_id === right.checklist_id) ? right : { checklist_id: firstVersion };
  const request: CohortRequest = { dataset_group_id: dataset?.dataset_group_id ?? '', left: selectedLeft, right: selectedRight, basis, limit: 200 };
  const inputKey = JSON.stringify(request);
  const [submission, setSubmission] = useState<{ key: string; request: CohortRequest; epoch: number } | null>(null);
  const active = open && submission?.key === inputKey ? submission : null;
  const comparison = useLatestResource(active ? JSON.stringify([active.key, active.epoch]) : `no-cohort-result:${inputKey}:${open}`, async () => {
    if (!active) return null;
    const result = await api<CohortResult>('/insights/cohorts/compare', active.request);
    if (!cohortResultMatches(result, active.request)) throw new Error('Cohort results do not match this dataset, configuration or answer basis. Refresh and retry.');
    return result;
  });
  const result = active ? comparison.value : null;
  const [caseSelection, setCaseSelection] = useState<{ key: string; ids: string[]; title: string } | null>(null);
  const [selectedPair, setSelectedPair] = useState<{ key: string; pair: CohortPair } | null>(null);
  const cases = useRef<HTMLElement>(null); const caseTrigger = useRef<HTMLButtonElement | null>(null); const pairTrigger = useRef<HTMLButtonElement | null>(null);
  const resultKey = active ? JSON.stringify([active.key, active.epoch]) : '';
  const currentCases = caseSelection?.key === resultKey ? caseSelection : null;
  const currentPair = selectedPair?.key === resultKey ? selectedPair.pair : null;
  const visiblePairs = result?.pairs.filter(pair => !currentCases || currentCases.ids.includes(pair.source.conversation_id)) ?? [];
  useEffect(() => { if (currentCases) { cases.current?.scrollIntoView({ block: 'nearest' }); cases.current?.focus({ preventScroll: true }); } }, [currentCases]);
  const resetResult = () => { setSubmission(null); setCaseSelection(null); setSelectedPair(null); };
  const compare = () => { setCaseSelection(null); setSelectedPair(null); setSubmission(previous => ({ key: inputKey, request, epoch: (previous?.epoch ?? 0) + 1 })); };
  const oversized = (dataset?.source_revision_count ?? 0) > 200;
  const selectCases = (event: React.MouseEvent<HTMLButtonElement>, ids: string[], title: string) => {
    caseTrigger.current = event.currentTarget; setCaseSelection({ key: resultKey, ids, title }); setSelectedPair(null);
  };
  const cohortControls = (title: 'Baseline' | 'Candidate', selector: CohortSelector, setSelector: (value: CohortSelector) => void) => {
    const profile = dataset?.checklists.find(item => item.checklist_id === selector.checklist_id);
    return <fieldset className="cohort-selector"><legend>{title} cohort</legend>
      <label>Checklist<select aria-label={`${title} checklist`} value={selector.checklist_id} onChange={event => { resetResult(); setSelector({ checklist_id: Number(event.target.value) }); }}>
        {dataOptions?.checklists.map(version => <option key={version.checklist_id} value={version.checklist_id}>v{version.checklist_id} · {profile?.checklist_id === version.checklist_id ? `${profile.run_count} saved runs` : 'saved version'}</option>)}
      </select></label>
      {cohortFields.map(field => <label key={field}>Recorded {fieldNames[field]}<select aria-label={`${title} ${fieldNames[field]}`}
        value={Object.hasOwn(selector, field) ? JSON.stringify(selector[field]) : 'any'} onChange={event => {
          const next = { ...selector }; if (event.target.value === 'any') delete next[field]; else next[field] = JSON.parse(event.target.value) as string | null;
          resetResult(); setSelector(next);
        }}><option value="any">Any recorded value</option><option value="null">Unknown / withheld ({profile?.fields[field].unknown_count ?? 0})</option>
        {profile?.fields[field].values.map(item => <option key={item.value} value={JSON.stringify(item.value)}>Recorded: {item.value} ({item.count})</option>)}
      </select></label>)}
    </fieldset>;
  };
  return <details className="cohort-comparison insight-tools" onToggle={event => {
    const next = event.currentTarget.open; setOpen(next);
    if (!next) { setCaseSelection(null); setSelectedPair(null); }
  }}>
    <summary><span>Saved-run cohorts</span><span className="disclosure-hint">Compare historical configurations · no new evaluation</span></summary>
    {open && <div className="cohort-content">
      <p className="cohort-notice">Historical differences, not evaluator accuracy. Higher operator scores do not establish a better evaluator. Cached reuse is not an independent assessment.</p>
      <div className="cohort-section-heading"><h3>Compare one dataset at a time</h3><button className="secondary" disabled={options.pending} onClick={() => { resetResult(); void options.reload().catch(() => {}); }}>Refresh recorded options</button></div>
      {options.pending && <p role="status">Loading recorded cohort options…</p>}
      {options.error && <div role="alert"><p>{options.error}</p><button className="secondary" onClick={() => void options.reload().catch(() => {})}>Retry cohort options</button></div>}
      {dataOptions && dataOptions.unavailable_dataset_identifiers > 0 && <p>{dataOptions.unavailable_dataset_identifiers} dataset identifier(s) are invalid or withheld and cannot be selected.</p>}
      {dataOptions && !dataOptions.datasets.length && <p>{dataOptions.unavailable_dataset_identifiers ? 'No selectable saved source datasets are available.' : 'No saved source datasets are available.'}</p>}
      {dataset && <>
        <div className="cohort-scope-controls"><label>Dataset<select aria-label="Cohort dataset" value={dataset.dataset_group_id} onChange={event => {
          resetResult(); setDatasetId(event.target.value); setLeft({ checklist_id: 0 }); setRight({ checklist_id: 0 });
        }}>{dataOptions!.datasets.map(item => <option key={item.dataset_group_id} value={item.dataset_group_id}>{item.dataset_group_id} · {item.source_revision_count} exact revisions</option>)}</select></label>
          <label>Answer basis<select aria-label="Cohort answer basis" value={basis} onChange={event => { resetResult(); setBasis(event.target.value as CohortBasis); }}><option value="effective">Effective judgments</option><option value="original">Original judgments</option></select></label></div>
        <p>Includes all {dataset.source_revision_count} exact source revisions in {dataset.dataset_group_id}, including historical revisions and missing evaluations. This tool has its own scope; queue filters do not apply.</p>
        <div className="cohort-selectors">{cohortControls('Baseline', selectedLeft, setLeft)}{cohortControls('Candidate', selectedRight, setRight)}</div>
        <p>Any recorded value includes unknowns. Unknown / withheld selects missing, invalid or withheld metadata. The latest matching saved run is selected by creation time and ID; failed runs never fall back to an older success.</p>
        {cohortSelectorKey(selectedLeft) === cohortSelectorKey(selectedRight) && <p className="cohort-notice">These filters are identical. Each matching saved run will be compared with itself. Select a different recorded configuration to inspect historical changes.</p>}
        {oversized && <p role="alert">This dataset exceeds 200 exact source revisions. Select a smaller dataset; no partial comparison will be shown.</p>}
        <button className="secondary" disabled={oversized || options.pending || !selectedLeft.checklist_id || !selectedRight.checklist_id || !!active && comparison.pending} onClick={compare}>Compare saved cohorts</button>
      </>}
      {active && comparison.pending && <p role="status">Comparing saved cohorts…</p>}
      {active && comparison.error && <div role="alert"><p>{comparison.error}</p><button className="secondary" onClick={compare}>Retry cohort comparison</button></div>}
      {result && <div className="cohort-result">
        <h3>Dataset {result.dataset_group_id} · {result.basis} answers</h3>
        <div className="cohort-coverage" role="group" aria-label="Cohort coverage">
          {pairStatuses.map(status => <button className="secondary" key={status} disabled={!result.coverage[status]} onClick={event => selectCases(event,
            result.pairs.filter(pair => pair.status === status).map(pair => pair.source.conversation_id), statusNames[status])}>
            <span>{statusNames[status]}</span><strong>{result.coverage[status]}</strong></button>)}
        </div>
        <p>{result.coverage.paired} / {result.coverage.source_revisions} revisions have both saved runs · {result.coverage.cached_pairs} contain cached reuse · {result.coverage.same_run_pairs} compare the same run · {result.coverage.unknown_provenance_pairs} contain unknown provenance · {result.coverage.provenance_conflict_pairs} have conflicting checklist provenance.</p>
        <p>Mean saved total difference: <strong>{result.total_difference.mean ?? 'Unavailable'}</strong> across {result.total_difference.count} comparable numeric pairs. All differences are candidate minus baseline.</p>
        <details><summary>Selection and coverage rules</summary><p>{result.selection_policy}</p><p>{result.scope_policy}</p><p>{result.coverage_policy}</p><p>Coverage states are exclusive. Pair reasons retain overlapping missing, failure, unresolved and compatibility conditions.</p></details>
        <div className="table-scroll" role="region" aria-label="Cohort criterion transitions" tabIndex={0}><table><thead><tr><th>Criterion / compatibility</th><th>Saved transitions · count / all revisions</th><th>Comparable raw points</th></tr></thead>
          <tbody>{result.criteria.map((criterion: CohortCriterion) => <tr key={criterion.criterion_id}><td><strong>{criterion.right_name ?? criterion.left_name ?? criterion.criterion_id}</strong>
            <small>{criterion.criterion_id} · {criterionKind(criterion)}</small>
            <small>{criterion.answer_comparable_count} answer-comparable · {criterion.answer_changed_count} answer changes · {criterion.disposition_changed_count} disposition changes</small>
            <small>{criterion.configuration_changed_count} configuration changes, including {criterion.definition_changed_count} definition changes · {criterion.details_only_count} details-only changes · {criterion.unavailable_count} unavailable</small></td>
            <td><div className="cohort-transitions">{criterion.transitions.map((transition, index) => <button className="secondary" key={index} onClick={event => selectCases(event, transition.conversation_ids,
              `${criterion.right_name ?? criterion.left_name ?? criterion.criterion_id}: ${cohortAnswerLabel(transition.left, criterion.left_type)} → ${cohortAnswerLabel(transition.right, criterion.right_type)}`)}>
              <span>{cohortAnswerLabel(transition.left, criterion.left_type)} → {cohortAnswerLabel(transition.right, criterion.right_type)}</span><strong>{transition.count} / {criterion.denominator}</strong>
              {!transition.answer_comparable && <small>Answer comparison unavailable / incompatible</small>}</button>)}</div></td>
            <td>Mean Δ {criterion.points_difference.mean ?? 'unavailable'}<small>{criterion.points_difference.count} comparable point pairs</small></td></tr>)}</tbody></table></div>
        <p>N/A, unresolved and unavailable answers stay visible. Meaning or answer-rule changes block answer comparability; changed point rules block point differences. Weight and section changes are configuration changes. Point means use only comparable saved points. Detail-only counts exclude answer, point and configuration changes.</p>
        <section className="cohort-cases" ref={cases} tabIndex={-1} aria-label="Cohort exact cases">
          <div className="cohort-section-heading"><h4>{currentCases ? `${currentCases.title} · ${visiblePairs.length} cases` : `Exact cases · ${visiblePairs.length}`}</h4>
            {currentCases && <button className="text-button" onClick={() => { setCaseSelection(null); setSelectedPair(null); caseTrigger.current?.focus(); }}>Show all cohort cases</button>}</div>
          <div className="table-scroll" role="region" aria-label="Exact cohort case list" tabIndex={0}><table><thead><tr><th>Exact source revision</th><th>Baseline run</th><th>Candidate run</th><th>Coverage / total difference</th><th>Inspect</th></tr></thead>
            <tbody>{visiblePairs.map(pair => <tr key={pair.source.conversation_id}><td><strong>{pair.source.source_id}</strong><small>Revision {pair.source.revision} · {pair.source.dataset_group_id}</small><small>{pair.source.content_hash}</small></td>
              <td><RunIdentity side={pair.left} /></td><td><RunIdentity side={pair.right} /></td><td>{statusNames[pair.status]}<small>{pair.total_comparable ? `Saved total Δ ${pair.total_difference}` : 'No comparable total'}</small><small>{pair.reasons.map(reason => reason.toLowerCase().replaceAll('_', ' ')).join(' · ')}</small></td>
              <td>{pair.left && pair.right ? <button className="secondary" aria-label={`Inspect exact pair ${pair.source.source_id} revision ${pair.source.revision}`} onClick={event => {
                pairTrigger.current = event.currentTarget; setSelectedPair({ key: resultKey, pair });
              }}>Inspect pair</button> : <span>Both saved runs required</span>}
                <a className="cohort-evidence" href={`#conversation/${encodeURIComponent(pair.source.conversation_id)}${pair.left || pair.right ? `?evaluation=${encodeURIComponent((pair.left ?? pair.right)!.evaluation_id)}` : ''}`}>Open source / saved run</a></td>
            </tr>)}</tbody></table></div>
        </section>
        {currentPair && <CohortPairPreview pair={currentPair} basis={basis} onOpenPair={onOpenPair} onClose={() => { setSelectedPair(null); pairTrigger.current?.focus(); }} />}
      </div>}
    </div>}
  </details>;
}
