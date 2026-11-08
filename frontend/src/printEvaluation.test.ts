// @vitest-environment happy-dom
import { expect, it, vi } from 'vitest';
import { renderPrintableEvaluation, validatePrintPacket } from './printEvaluation';
import { syntheticPrintPacket } from './printEvaluationFixtures';

// Vitest stubs CSS imports; use the actual owned stylesheet for serialization assertions.
vi.mock('./printEvaluation.css?raw', async () => {
  const { readFile } = await import('node:fs/promises');
  return { default: await readFile('src/printEvaluation.css', 'utf8') };
});

function rendered(packet = syntheticPrintPacket(), excerpts = false) {
  const html = renderPrintableEvaluation(packet, { evaluationId: packet.evaluation.id, updatedAt: packet.evaluation.updated_at }, excerpts);
  return { html, doc: new DOMParser().parseFromString(html, 'text/html') };
}

it('renders exact saved decimal strings, both bases, N/A membership, flags and complete reviewer history without mutation', () => {
  const packet = syntheticPrintPacket();
  packet.evaluation.original_score!.total = '77.777700';
  packet.evaluation.original_score!.criteria[0].raw_points = '7.123456789012345678901234567890';
  const before = structuredClone(packet);
  const { doc } = rendered(packet);
  const content = doc.body.textContent!;
  for (const expected of ['77.777700 / 100', '7.123456789012345678901234567890', '100.0000', '10.00', '20.00', 'N/A',
    'N/A — excluded from denominator', 'Unscored flag', 'No numeric total', 'UNRESOLVED_CRITERIA', 'NO_APPLICABLE_SCORED_WEIGHT',
    'SYNTHETIC missing authority.', 'SYNTHETIC reviewer rationale.', 'SYNTHETIC appeal comment.', 'Result after decision 4',
    'SYNTHETIC_SOURCE_HASH', 'SYNTHETIC_CHECKLIST_HASH', 'SYNTHETIC_CACHED_ORIGINAL', 'm0001', 'm0002']) expect(content).toContain(expected);
  expect(content).toContain('Original explanation'); expect(content).toContain('Effective explanation');
  expect(content).toContain('Recorded reviewer judgment'); expect(content).toContain('critical: No (unscored)');
  expect(packet).toEqual(before);
});

it('keeps missing and failed snapshots explicit, without inventing a zero result or judgment', () => {
  const packet = syntheticPrintPacket();
  Object.assign(packet.evaluation, { state: 'failed', completeness: 'incomplete', original: null, effective: null,
    original_score: null, effective_score: null, reviews: [], error: 'SYNTHETIC stored failure.' });
  const { doc } = rendered(packet);
  expect(doc.body.textContent).toContain('ASSESSMENT_UNAVAILABLE');
  expect(doc.body.textContent).toContain('No saved judgment');
  expect(doc.body.textContent).toContain('SYNTHETIC stored failure.');
  expect(doc.body.textContent).not.toContain('0 / 100');
});

it('retains zero-weight and unresolved flag nulls, while a saved zero total remains a numeric zero', () => {
  const packet = syntheticPrintPacket();
  packet.evaluation.original_score!.total = '0.00';
  Object.assign(packet.evaluation.effective_score!, { total: null, applicable_weight: '0', raw_subtotal: '0', reason: 'NO_APPLICABLE_SCORED_WEIGHT', flags: { critical: null } });
  const { doc } = rendered(packet);
  expect(doc.body.textContent).toContain('0.00 / 100');
  expect(doc.body.textContent).toContain('No numeric total');
  expect(doc.body.textContent).toContain('critical: Unresolved (unscored)');
});

it('includes evidence excerpts only by explicit policy/option and keeps review-range availability', () => {
  const hidden = rendered();
  expect(hidden.doc.body.textContent).not.toContain('SYNTHETIC source excerpt.');
  const packet = syntheticPrintPacket(undefined, undefined, true);
  packet.source_excerpts!.push({ ...structuredClone(packet.source_excerpts![0]), basis: 'review:4', messages: [], range_available: false });
  const { doc } = rendered(packet, true);
  expect(doc.body.textContent).toContain('SYNTHETIC source excerpt.');
  expect(doc.body.textContent).toContain('review:4');
  expect(doc.body.textContent).toContain('Source range unavailable in this saved revision.');
  expect(doc.body.textContent).toContain('not anonymous');
  expect(() => rendered(packet, false)).toThrow();
});

it('escapes malicious source, checklist, explanation and reviewer text and emits no active elements or remote assets', () => {
  const packet = syntheticPrintPacket(undefined, undefined, true);
  const malicious = '</style><script>window.pwned=1</script><img src="https://example.invalid/track" onerror="alert(1)"><svg onload="alert(2)">& "quote" \'single\'';
  packet.evaluation.original!.results.contact.explanation = malicious;
  packet.evaluation.checklist.snapshot.criteria[0].name = malicious;
  packet.evaluation.reviews[0].rationale = malicious;
  packet.source_excerpts![0].messages[0].text = malicious;
  const { html, doc } = rendered(packet, true);
  expect(doc.querySelectorAll('script,img,svg,iframe,object,embed,a,link,form').length).toBe(0);
  expect(doc.querySelector('[onload],[onerror],[src],[href]')).toBeNull();
  expect(doc.querySelector('meta[http-equiv="Content-Security-Policy"]')?.getAttribute('content')).toContain("default-src 'none'");
  expect(doc.body.textContent).toContain(malicious);
  expect(html).not.toContain('<script>'); expect(html).toContain('&lt;script&gt;');
});

it('excludes unexpected recording/credential fields and displays only allowed provenance/accounting', () => {
  const packet = syntheticPrintPacket() as ReturnType<typeof syntheticPrintPacket> & { audio_url?: string; credentials?: string };
  packet.audio_url = 'PRIVATE_AUDIO_URL'; packet.credentials = 'PRIVATE_CREDENTIAL';
  Object.assign(packet.source, { audio_url: 'PRIVATE_AUDIO_URL' });
  Object.assign(packet.evaluation.metadata, { api_key: 'PRIVATE_CREDENTIAL', request: 'PRIVATE_REQUEST', generation: { temperature: 0, authorization: 'PRIVATE_AUTH' } });
  const { html } = rendered(packet);
  for (const privateValue of ['PRIVATE_AUDIO_URL', 'PRIVATE_CREDENTIAL', 'PRIVATE_AUTH', 'PRIVATE_REQUEST']) expect(html).not.toContain(privateValue);
  expect(html).toContain('SYNTHETIC_MODEL'); expect(html).toContain('SYNTHETIC_SCHEMA_HASH');
});

it('rejects stale, mismatched, unsanitized and malformed packets with safe errors', () => {
  const packet = syntheticPrintPacket(), expected = { evaluationId: packet.evaluation.id, updatedAt: packet.evaluation.updated_at };
  expect(() => validatePrintPacket(packet, { ...expected, evaluationId: 'OTHER' }, false)).toThrow('another run');
  expect(() => validatePrintPacket(packet, { ...expected, updatedAt: 'NEWER' }, false)).toThrow('saved run changed');
  const mutations = [
    (p: any) => { p.export_schema_version = 2; },
    (p: any) => { p.export_policy.credentials_included = true; },
    (p: any) => { p.export_policy.recording_urls_included = true; },
    (p: any) => { p.manifest.runs[0].source_hash = 'OTHER'; },
    (p: any) => { p.manifest.runs[0].checklist_id = 999; },
    (p: any) => { p.evaluation.conversation_id = 'OTHER'; },
    (p: any) => { p.evaluation.checklist.snapshot.criteria[0].name = null; },
    (p: any) => { p.evaluation.original.results.contact.evidence = [null]; },
    (p: any) => { p.source_excerpts = []; },
  ];
  for (const mutate of mutations) { const changed = structuredClone(packet); mutate(changed); expect(() => validatePrintPacket(changed, expected, false)).toThrow('incomplete or unsupported'); }
});

it('preserves very long RU/KZ/EN text, newlines and long tokens and supplies wrapping and repeated print headings', () => {
  const packet = syntheticPrintPacket();
  const long = ('SYNTHETIC русский текст\nҚазақша ӘҒҚҢӨҰҮҺІ English.\n' + 'x'.repeat(240) + '\n').repeat(80);
  packet.evaluation.original!.results.contact.explanation = long;
  const { html, doc } = rendered(packet);
  expect(doc.body.textContent).toContain(long);
  expect(html).toContain('overflow-wrap: anywhere'); expect(html).toContain('table-header-group');
  expect(html).toContain('break-after: avoid-page'); expect(html).toContain('white-space: pre-wrap');
  expect(doc.querySelectorAll('thead').length).toBeGreaterThan(8);
  expect(html).not.toMatch(/<style>[^]*?body\s*\{[^]*?display:\s*none/);
});

it('renders criteria with an unknown section once without confusing a real section ID', () => {
  const packet = syntheticPrintPacket();
  packet.evaluation.checklist.snapshot.sections[0].id = '__unsectioned';
  packet.evaluation.checklist.snapshot.criteria[0].section_id = '__unsectioned';
  const { doc } = rendered(packet);
  expect(doc.querySelectorAll('.cqa-report-criterion').length).toBe(3);
  expect(doc.body.textContent).toContain('Other saved criteria');
});
