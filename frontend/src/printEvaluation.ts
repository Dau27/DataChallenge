import styles from './printEvaluation.css?raw';
import type { Criterion, Evidence } from './types';
import type { Assessment, Judgment, PrintExcerpt, PrintIdentity, PrintScore, SavedPrintPacket } from './printEvaluationTypes';

const record = (v: unknown): v is Record<string, unknown> => !!v && typeof v === 'object' && !Array.isArray(v);
const text = (v: unknown): v is string => typeof v === 'string';
const nullableText = (v: unknown) => v === null || text(v);
const integer = (v: unknown) => typeof v === 'number' && Number.isSafeInteger(v) && v >= 0;
const array = (v: unknown, valid: (item: unknown) => boolean) => Array.isArray(v) && v.every(valid);
const strings = (v: Record<string, unknown>, keys: string[]) => keys.every(k => text(v[k]));
const evidenceValid = (v: unknown) => record(v) && ['support', 'absence', 'context'].includes(String(v.kind))
  && strings(v, ['start_message_id', 'end_message_id']);
const judgmentValid = (v: unknown) => record(v) && ['assessed', 'not_applicable', 'needs_review'].includes(String(v.disposition))
  && (v.value === null || typeof v.value === 'boolean' || (typeof v.value === 'number' && Number.isFinite(v.value)))
  && text(v.explanation) && nullableText(v.na_reason) && nullableText(v.review_reason) && array(v.evidence, evidenceValid);
const assessmentValid = (v: unknown) => v === null || (record(v) && record(v.results) && Object.values(v.results).every(judgmentValid));
const scoreValid = (v: unknown): boolean => v === null || (record(v)
  && nullableText(v.total) && nullableText(v.reason) && text(v.completeness) && text(v.applicable_weight)
  && nullableText(v.raw_subtotal) && record(v.flags) && Object.values(v.flags).every(x => x === null || typeof x === 'boolean')
  && array(v.criteria, x => record(x) && text(x.criterion_id) && nullableText(x.weight)
    && nullableText(x.raw_points) && nullableText(x.normalized_contribution))
  && array(v.sections, x => record(x) && strings(x, ['id', 'title']) && nullableText(x.total) && nullableText(x.reason)
    && (x.applicable_weight === undefined || text(x.applicable_weight)) && (x.raw_subtotal === undefined || nullableText(x.raw_subtotal))));

/** Validate the existing sanitized export contract, without changing any saved value. */
export function validatePrintPacket(value: unknown, expected: PrintIdentity, includeExcerpts: boolean): SavedPrintPacket {
  const invalid = () => { throw new Error('The saved report packet is incomplete or unsupported. Retry after refreshing the saved assessment.'); };
  if (!record(value) || value.export_schema_version !== 1 || !record(value.evaluation) || !record(value.source)
    || !record(value.export_policy) || !record(value.manifest)) return invalid();
  const e = value.evaluation, s = value.source, policy = value.export_policy, manifest = value.manifest;
  if (e.id !== expected.evaluationId || e.updated_at !== expected.updatedAt) {
    throw new Error('The saved run changed or the report belongs to another run. Refresh the saved assessment, then retry.');
  }
  if (policy.credentials_included !== false || policy.recording_urls_included !== false
    || policy.source_excerpts_included !== includeExcerpts || !text(policy.notice) || !integer(policy.redacted_string_occurrences)
    || manifest.schema_version !== 1 || manifest.selected_run_count !== 1 || !text(manifest.generated_at) || !text(manifest.notice)
    || manifest.source_excerpts_included !== includeExcerpts || !array(manifest.answer_sets, text)
    || !(manifest.answer_sets as string[]).includes('original') || !(manifest.answer_sets as string[]).includes('effective')
    || !Array.isArray(manifest.runs) || manifest.runs.length !== 1 || !record(manifest.runs[0])) return invalid();
  if (!strings(s, ['id', 'source_id', 'group_id', 'content_hash', 'language', 'channel']) || !integer(s.revision)
    || !integer(s.message_count) || e.conversation_id !== s.id || !record(e.checklist) || !record(e.checklist.snapshot)
    || !integer(e.checklist.id) || e.checklist_id !== e.checklist.id || !text(e.checklist.content_hash)) return invalid();
  const identity = manifest.runs[0];
  const actualIdentity = { evaluation_id: e.id, updated_at: e.updated_at, conversation_id: s.id, source_id: s.source_id,
    group_id: s.group_id, revision: s.revision, source_hash: s.content_hash,
    checklist_id: e.checklist.id, checklist_hash: e.checklist.content_hash };
  if (Object.entries(actualIdentity).some(([k, v]) => identity[k] !== v)) return invalid();
  const rubric = e.checklist.snapshot;
  if (!text(rubric.name) || !array(rubric.sections, x => record(x) && strings(x, ['id', 'title']))
    || !array(rubric.criteria, x => record(x) && strings(x, ['id', 'name', 'description', 'section_id'])
      && ['binary', 'scale', 'flag'].includes(String(x.answer_type)) && (nullableText(x.weight) || typeof x.weight === 'number')
      && typeof x.na_allowed === 'boolean' && nullableText(x.na_condition)
      && array(x.scale, a => record(a) && (text(a.value) || typeof a.value === 'number') && text(a.description)))) return invalid();
  if (!strings(e, ['id', 'conversation_id', 'created_at', 'updated_at', 'state', 'completeness'])
    || !nullableText(e.cached_from) || !nullableText(e.error) || !record(e.metadata)
    || !assessmentValid(e.original) || !assessmentValid(e.effective) || !scoreValid(e.original_score) || !scoreValid(e.effective_score)
    || !array(e.appeals, a => record(a) && strings(a, ['id', 'criterion_id', 'comment', 'status', 'created_at']))
    || !array(e.reviews, r => record(r) && integer(r.id) && strings(r, ['appeal_id', 'evaluation_id', 'criterion_id', 'action', 'rationale', 'created_at'])
      && r.evaluation_id === e.id && judgmentValid(r.judgment) && r.resulting_score !== null && scoreValid(r.resulting_score))
    || !Array.isArray(e.attempts) || !record(e.usage)) return invalid();
  // A false option must not leave a hidden source-text payload in a printable document.
  if (!includeExcerpts && value.source_excerpts !== undefined) return invalid();
  if (includeExcerpts && !array(value.source_excerpts, x => record(x) && strings(x, ['basis', 'criterion_id'])
    && evidenceValid(x.evidence) && typeof x.range_available === 'boolean'
    && array(x.messages, m => record(m) && strings(m, ['id', 'speaker', 'timestamp', 'text'])))) return invalid();
  return value as unknown as SavedPrintPacket;
}

/** Every dynamic value enters an HTML text node. No packet value becomes markup or a URL. */
export function escapePrintText(value: unknown): string {
  return String(value ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]!));
}
const esc = escapePrintText;
const paragraph = (value: unknown, className = '') => `<p dir="auto"${className ? ` class="${className}"` : ''}>${esc(value)}</p>`;
const unavailable = 'Unavailable';
const scalar = (v: unknown) => v === null || v === undefined ? unavailable : String(v);
const idText = (v: unknown) => `<span class="cqa-report-id">${esc(v)}</span>`;
const totalText = (score: PrintScore | null | undefined) => score?.total == null ? 'No numeric total' : `${score.total} / 100`;
const answer = (j: Judgment | null | undefined) => !j ? 'No saved judgment' : j.disposition === 'not_applicable' ? 'N/A'
  : j.disposition === 'needs_review' ? 'Needs review' : j.value === true ? 'Yes' : j.value === false ? 'No' : scalar(j.value);
function valueTable(caption: string, rows: [string, unknown][]) {
  return `<table><caption>${esc(caption)}</caption><thead><tr><th scope="col">Field</th><th scope="col">Saved value</th></tr></thead><tbody>${rows.map(([k, v]) => `<tr><th scope="row">${esc(k)}</th><td dir="auto">${esc(scalar(v))}</td></tr>`).join('')}</tbody></table>`;
}
function pairTable(caption: string, rows: [string, unknown, unknown][]) {
  return `<table class="cqa-report-pair"><caption>${esc(caption)}</caption><thead><tr><th scope="col">Field</th><th scope="col">Original</th><th scope="col">Effective</th></tr></thead><tbody>${rows.map(([k, a, b]) => `<tr><th scope="row">${esc(k)}</th><td dir="auto">${esc(scalar(a))}</td><td dir="auto">${esc(scalar(b))}</td></tr>`).join('')}</tbody></table>`;
}
function flags(score: PrintScore | null | undefined) {
  if (!score || !Object.keys(score.flags).length) return 'None recorded';
  return Object.entries(score.flags).map(([key, v]) => `${key}: ${v === null ? 'Unresolved' : v ? 'Yes' : 'No'} (unscored)`).join('\n');
}
function scoreRows(score: PrintScore | null): [string, unknown][] {
  return [['Total', totalText(score)], ['Total reason', score ? score.reason ?? 'None recorded' : 'ASSESSMENT_UNAVAILABLE'],
    ['Completeness', score?.completeness], ['Applicable scored weight', score?.applicable_weight],
    ['Raw subtotal', score?.raw_subtotal], ['Flags', flags(score)], ['Scoring version', score?.scoring_version]];
}
function sectionsTable(caption: string, score: PrintScore) {
  if (!score.sections.length) return paragraph('No saved section totals.');
  return `<table><caption>${esc(caption)}</caption><thead><tr><th scope="col">Section</th><th scope="col">Total / reason</th><th scope="col">Applicable weight / raw subtotal</th></tr></thead><tbody>${score.sections.map(s => `<tr><th scope="row">${esc(s.title)}<br>${idText(s.id)}</th><td>${esc(s.total == null ? 'No numeric total' : `${s.total} / 100`)}<br>${esc(s.reason ?? 'No unavailable-total reason')}</td><td>${esc(scalar(s.applicable_weight))} / ${esc(scalar(s.raw_subtotal))}</td></tr>`).join('')}</tbody></table>`;
}
function evidenceList(evidence: Evidence[]) {
  return evidence.length ? `<ul class="cqa-report-evidence">${evidence.map(e => `<li>${esc(e.kind)}: ${idText(e.start_message_id)}–${idText(e.end_message_id)}</li>`).join('')}</ul>` : paragraph('No saved evidence IDs.');
}
function judgmentDetails(title: string, judgment: Judgment | null | undefined) {
  return `<section><h4>${esc(title)}</h4>${!judgment ? paragraph('No saved judgment.') : paragraph(judgment.explanation)
    + (judgment.na_reason !== null ? paragraph(`N/A reason: ${judgment.na_reason}`) : '')
    + (judgment.review_reason !== null ? paragraph(`Review reason: ${judgment.review_reason}`) : '')
    + '<p><strong>Evidence IDs</strong></p>' + evidenceList(judgment.evidence)}</section>`;
}
function excerptBlock(excerpt: PrintExcerpt) {
  return `<article class="cqa-report-excerpt"><h4>${esc(excerpt.basis)} · ${esc(excerpt.criterion_id)} · ${idText(excerpt.evidence.start_message_id)}–${idText(excerpt.evidence.end_message_id)}</h4>
    ${paragraph(`Evidence kind: ${excerpt.evidence.kind}`)}${!excerpt.range_available ? paragraph('Source range unavailable in this saved revision.') : excerpt.messages.length
      ? excerpt.messages.map(m => `<p class="cqa-report-secondary">${idText(m.id)} · ${esc(m.speaker)} · ${esc(m.timestamp)}</p>${paragraph(m.text)}`).join('') : paragraph('No source messages in the exported range.')}</article>`;
}
function criterionBlock(c: Criterion, original: Assessment | null, effective: Assessment | null, originalScore: PrintScore | null, effectiveScore: PrintScore | null) {
  const a = original?.results[c.id], b = effective?.results[c.id];
  const p = [originalScore, effectiveScore].map(score => score?.criteria.find(r => r.criterion_id === c.id));
  const point = (i: number, key: 'raw_points' | 'normalized_contribution') => c.answer_type === 'flag' ? 'Unscored flag' : scalar(p[i]?.[key]);
  const applicable = (i: number, j: Judgment | undefined) => c.answer_type === 'flag' ? 'Unscored flag' : j?.disposition === 'not_applicable'
    ? 'N/A — excluded from denominator' : p[i]?.applicable === undefined ? unavailable : p[i].applicable ? 'Included' : 'Excluded';
  return `<article class="cqa-report-criterion"><h3>${esc(c.name)} · ${idText(c.id)}</h3>${paragraph(c.description)}
    ${paragraph(`Answer type: ${c.answer_type}${c.answer_type === 'flag' ? ' · Unscored flag' : ''}`, 'cqa-report-secondary')}
    ${c.na_allowed ? paragraph(`N/A allowed only when: ${c.na_condition ?? 'No condition recorded'}`) : paragraph('N/A not allowed.', 'cqa-report-secondary')}
    ${c.scale.length ? `<ul>${c.scale.map(a => `<li>${esc(a.value)}: ${esc(a.description)}</li>`).join('')}</ul>` : ''}
    ${pairTable('Saved answers and points', [
      ['Answer', answer(a), answer(b)], ['Disposition', a?.disposition, b?.disposition],
      ['Configured weight', c.answer_type === 'flag' ? 'Unscored flag' : c.weight, c.answer_type === 'flag' ? 'Unscored flag' : c.weight],
      ['Saved calculation weight', p[0]?.weight, p[1]?.weight], ['Denominator membership', applicable(0, a), applicable(1, b)],
      ['Raw points', point(0, 'raw_points'), point(1, 'raw_points')],
      ['Normalized contribution / 100', point(0, 'normalized_contribution'), point(1, 'normalized_contribution')]])}
    ${judgmentDetails('Original explanation', a)}${judgmentDetails('Effective explanation', b)}</article>`;
}
function provenance(packet: SavedPrintPacket) {
  const e = packet.evaluation, m = e.metadata;
  const allowed = ['provider', 'model', 'mode', 'prompt_version', 'prompt_hash', 'schema_version', 'schema_hash', 'scoring_version', 'evidence_validation_version'];
  const metadataRows: [string, unknown][] = allowed.map(k => [k, typeof m[k] === 'string' || typeof m[k] === 'number' ? m[k] : undefined]);
  // Render only known provenance/accounting fields, never arbitrary metadata or request payloads.
  const generation = record(m.generation) ? Object.entries(m.generation).filter(([k, v]) =>
    ['temperature', 'reasoning_effort', 'max_output_tokens', 'top_p', 'seed'].includes(k) && (v === null || ['string', 'number', 'boolean'].includes(typeof v))) : [];
  return `<section><h2>Recorded provenance and usage</h2>${valueTable('Saved provenance', metadataRows.concat([
    ['Cached original from run', e.cached_from ?? 'No cache lineage recorded'],
    ['Generation settings', generation.length ? generation.map(([k, v]) => `${k}: ${v}`).join('\n') : 'Not recorded']]))}
    ${paragraph(e.cached_from ? 'Cached reuse is not an independent assessment. Reviewer changes were not copied as a new original.' : 'This report displays stored results and makes no new assessment.')}
    ${valueTable('Saved request accounting (estimates are not invoices)', [
      ['Request attempts', e.usage.request_attempts], ['Known input tokens', e.usage.input_tokens_known], ['Known output tokens', e.usage.output_tokens_known],
      ['Usage complete', e.usage.usage_complete === true ? 'Yes' : 'No — unknown usage is not zero cost'],
      ['Estimated cost USD', e.usage.estimated_cost_usd], ['Cost rate source', e.usage.cost_rate_source], ['Request latency ms', e.usage.latency_ms]])}
    ${e.attempts.length ? `<table><caption>Saved attempts</caption><thead><tr><th scope="col">Attempt / status</th><th scope="col">Latency ms</th><th scope="col">Input / output tokens</th><th scope="col">Recorded response model</th></tr></thead><tbody>${e.attempts.map(a => {
      const attempt = a as typeof a & { response_model?: string | null };
      return `<tr><th scope="row">${esc(attempt.number)} · ${esc(attempt.status)}</th><td>${esc(scalar(attempt.latency_ms))}</td><td>${esc(scalar(attempt.input_tokens))} / ${esc(scalar(attempt.output_tokens))}</td><td>${esc(scalar(attempt.response_model))}</td></tr>`;
    }).join('')}</tbody></table>` : paragraph('No saved request attempts.')}</section>`;
}

/** Standalone inert HTML, using only an already-sanitized one-run export packet. */
export function renderPrintableEvaluation(value: unknown, expected: PrintIdentity, includeExcerpts = false): string {
  const packet = validatePrintPacket(value, expected, includeExcerpts);
  const e = packet.evaluation, s = packet.source, rubric = e.checklist.snapshot;
  const summaryA = scoreRows(e.original_score), summaryB = scoreRows(e.effective_score);
  const assigned = new Set(rubric.sections.map(section => section.id));
  const sections = [...rubric.sections.map(s => ({ ...s, unassigned: false })), ...(rubric.criteria.some(c => !assigned.has(c.section_id)) ? [{ id: '', title: 'Other saved criteria', unassigned: true }] : [])];
  const sourceIdentity = valueTable('Source, checklist and run identity', [
    ['Source ID / dataset', `${s.source_id} / ${s.group_id}`], ['Source revision', s.revision], ['Conversation revision ID', s.id],
    ['Source content hash', s.content_hash], ['Language / channel', `${s.language} / ${s.channel}`], ['Source messages', s.message_count],
    ['Saved evaluation ID', e.id], ['Run state / completeness', `${e.state} / ${e.completeness}`], ['Created at (recorded)', e.created_at],
    ['Updated at (recorded)', e.updated_at], ['Checklist', `v${e.checklist.id} · ${rubric.name}`], ['Checklist content hash', e.checklist.content_hash],
    ['Export snapshot generated at', packet.manifest.generated_at], ['Known redactions in export', packet.export_policy.redacted_string_occurrences]]);
  const reviews = e.reviews.map(r => `<article><h3>Review decision ${esc(r.id)} · ${idText(r.criterion_id)}</h3>
    ${paragraph(`Action: ${r.action} · appeal ${r.appeal_id} · ${r.created_at}`)}${paragraph(`Rationale: ${r.rationale}`)}
    ${paragraph(`Recorded answer: ${answer(r.judgment)} · disposition: ${r.judgment.disposition}`)}${judgmentDetails('Recorded reviewer judgment', r.judgment)}
    ${valueTable(`Result after decision ${r.id}`, scoreRows(r.resulting_score))}${sectionsTable('Section results after this decision', r.resulting_score)}
    <table><caption>Saved criterion points after this decision</caption><thead><tr><th scope="col">Criterion</th><th scope="col">Weight</th><th scope="col">Raw points</th><th scope="col">Contribution / 100</th></tr></thead><tbody>${r.resulting_score.criteria.map(p => `<tr><th scope="row">${idText(p.criterion_id)}</th><td>${esc(scalar(p.weight))}</td><td>${esc(scalar(p.raw_points))}</td><td>${esc(scalar(p.normalized_contribution))}</td></tr>`).join('')}</tbody></table></article>`).join('');
  const body = `<main class="cqa-report"><header><h1>Saved evaluation report</h1>${paragraph('Original and effective results · one recorded run · no new assessment', 'cqa-report-secondary')}
    <div class="cqa-report-note">${paragraph(packet.export_policy.notice)}${paragraph(`Source evidence excerpts: ${includeExcerpts ? 'included by explicit selection' : 'not included'}. Explanations and review comments may still quote private source text; this report is not anonymous.`)}</div></header>
    ${sourceIdentity}${e.error !== null ? `<section><h2>Saved execution error</h2>${paragraph(e.error)}</section>` : ''}
    <section><h2>Saved totals</h2>${pairTable('Original and effective score snapshots', summaryA.map(([key, v], i) => [key, v, summaryB[i][1]]))}
      ${paragraph('Values are shown exactly as saved; this view does not recalculate scores. N/A removes applicable scored weight. Flags remain unscored. Missing or unresolved totals are not zero.')}
      <h3>Original section results</h3>${e.original_score ? sectionsTable('Original saved sections', e.original_score) : paragraph('Original score snapshot unavailable.')}
      <h3>Effective section results</h3>${e.effective_score ? sectionsTable('Effective saved sections', e.effective_score) : paragraph('Effective score snapshot unavailable.')}</section>
    <section><h2>Criterion judgments</h2>${sections.map(section => `<section><h2>${esc(section.title)}</h2>${rubric.criteria.filter(c => section.unassigned ? !assigned.has(c.section_id) : c.section_id === section.id).map(c => criterionBlock(c, e.original, e.effective, e.original_score, e.effective_score)).join('') || paragraph('No criteria in this saved section.')}</section>`).join('')}</section>
    <section><h2>Appeals and review history</h2>${paragraph(`${e.appeals.length} saved appeal(s) · ${e.reviews.length} saved review decision(s). Anonymous review actions do not establish a verified reviewer identity.`)}
      ${e.appeals.map(a => `<article><h3>Appeal ${idText(a.id)} · ${idText(a.criterion_id)}</h3>${paragraph(`Status: ${a.status} · ${a.created_at}`)}${paragraph(a.comment)}</article>`).join('') || paragraph('No saved appeals.')}
      ${reviews || paragraph('No saved reviewer decisions.')}</section>
    ${provenance(packet)}
    <section><h2>Source evidence excerpts</h2>${includeExcerpts ? (packet.source_excerpts?.map(excerptBlock).join('') || paragraph('No evidence excerpts were available in this packet.')) : paragraph('Not included. Evidence IDs remain in the original/effective judgments and reviewer history above.')}</section>
    <footer class="cqa-report-footer">${paragraph(packet.manifest.notice)}${paragraph('Recording URLs and credentials are excluded by the saved-export policy. Source strings are printed as text; no source HTML or external assets are loaded.')}</footer></main>`;
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="referrer" content="no-referrer"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'; object-src 'none'"><title>Saved evaluation report · ${esc(e.id)}</title><style>${styles}\n@page { size: auto; margin: 14mm; }</style></head><body class="cqa-print-document">${body}</body></html>`;
}
