// @vitest-environment happy-dom
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import Conversations from './Conversations';
import App from './App';
import { BudgetSummary } from './Budget';
import { defaultFilters } from './SavedFilters';
import type { BudgetStatus, Conversation } from './types';
import seed from '../../config/initial_checklist.json';

beforeEach(() => { localStorage.clear(); sessionStorage.clear(); location.hash = '#conversations'; });
afterEach(() => { cleanup(); vi.restoreAllMocks(); localStorage.clear(); sessionStorage.clear(); });
const rows: Conversation[] = ['KZ', 'RU'].map(language => ({ id: language, source_id: `TEST_${language}`, group_id: 'DEV', revision: 1, content_hash: `TEST_${language}`,
  language, channel: 'agent chat', message_count: 2, audio_available: false, evaluation: { id: `RUN_${language}`, conversation_id: language, checklist_id: 1,
    state: 'succeeded', completeness: 'complete', total: '100.00', error: null, cached_from: null, created_at: '', updated_at: '' } }));
const props = { rows, access: null, selectedVersion: 1, completed: 2, needsReview: 0, busy: false,
  run: async (action: () => Promise<void>) => { await action(); }, evaluate: vi.fn(), refresh: vi.fn(), notify: vi.fn() };
const paused: BudgetStatus = { limit_usd: '0', opening_accounted_usd: '0', accounted_usd: '1.25', reserved_usd: '0', overhead_usd: '.1', available_usd: '0', ready: false, blocked_reason: 'Paid requests are paused', estimate_only: true };

it('clears a restored view without deleting or overwriting its saved preset or result rows', () => {
  const stored = JSON.stringify({ schema_version: 2, presets: [{ id: 'TEST_PRESET', name: 'KZ reviews', checklist_id: 1,
    filters: { ...defaultFilters, language: 'KZ', group: 'DEV' } }], active_by_checklist: { '1': 'TEST_PRESET' } });
  localStorage.setItem('cqa-filter-presets-v2', stored);
  const fetch = vi.spyOn(globalThis, 'fetch');
  const before = structuredClone(rows);
  render(<Conversations {...props} />);
  expect(screen.queryByRole('link', { name: 'TEST_RU' })).toBeNull();
  expect(screen.getByText('2 active')).toBeDefined();
  expect(screen.getByText('KZ reviews', { selector: '.disclosure-hint' })).toBeDefined();
  fireEvent.click(screen.getByRole('button', { name: 'Clear filters' }));
  expect(screen.getByRole('link', { name: 'TEST_RU' })).toBeDefined();
  expect(screen.getByRole('link', { name: 'TEST_KZ' })).toBeDefined();
  expect(screen.getByText('KZ reviews · edited', { selector: '.disclosure-hint' })).toBeDefined();
  expect(localStorage.getItem('cqa-filter-presets-v2')).toBe(stored);
  expect(rows).toEqual(before);
  expect(fetch).not.toHaveBeenCalled();
});

it('reveals preset storage failures and cross-tab conflicts rather than hiding them in a closed tool group', () => {
  localStorage.setItem('cqa-filter-presets-v2', '{invalid');
  const view = render(<Conversations {...props} />);
  expect(screen.getByRole('alert').closest('details')?.open).toBe(true);
  view.unmount(); localStorage.clear();
  render(<Conversations {...props} />);
  expect(document.querySelector<HTMLDetailsElement>('.queue-tools')?.open).toBe(false);
  fireEvent(window, new StorageEvent('storage', { key: 'cqa-filter-presets-v2' }));
  expect(document.querySelector<HTMLDetailsElement>('.queue-tools')?.open).toBe(true);
  expect(screen.getByRole('alert').textContent).toContain('another tab');
});

it('keeps import onboarding open for an empty workspace and provides a selection reset for a populated queue', () => {
  const view = render(<Conversations {...props} rows={[]} />);
  expect(document.querySelector<HTMLDetailsElement>('.import-disclosure')?.open).toBe(true);
  view.rerender(<Conversations {...props} />);
  expect(document.querySelector<HTMLDetailsElement>('.import-disclosure')?.open).toBe(false);
  fireEvent.click(screen.getByLabelText('Select TEST_KZ'));
  expect(screen.getByRole('status').textContent).toBe('1 selected');
  fireEvent.click(screen.getByRole('button', { name: 'Clear selection' }));
  expect((screen.getByLabelText('Select TEST_KZ') as HTMLInputElement).checked).toBe(false);
  expect((screen.getByRole('button', { name: /Evaluate selected/ }) as HTMLButtonElement).disabled).toBe(true);
});

it('keeps the paused spending state visible while retaining the complete estimate explanation in a disclosure', () => {
  render(<BudgetSummary budget={paused} />);
  const summary = document.querySelector('.budget-disclosure > summary');
  expect(summary?.textContent).toContain('Paid requests paused');
  expect(summary?.textContent).toContain('Shared spending limit: $0.00');
  expect(screen.getByText(/Accounted estimates: \$1.2500/)).toBeDefined();
  expect(screen.getByText(/not an account balance/)).toBeDefined();
});

it('moves keyboard focus into the workspace without changing the application hash route', async () => {
  vi.spyOn(globalThis, 'fetch').mockImplementation(async url => {
    const path = String(url);
    const response = path.includes('/checklists') ? [{ id: 1, created_at: '2026-11-07', content_hash: 'TEST', snapshot: seed }]
      : path.includes('/conversations') ? [] : path.includes('/budget') ? paused : { provider_configured: false, provider_status: 'Offline test', last_provider_check: null };
    return new Response(JSON.stringify(response));
  });
  render(<App />);
  await screen.findByText('Offline test. Update the local .env configuration and restart the backend. Imported transcripts remain available.');
  const before = location.hash;
  fireEvent.click(screen.getByRole('link', { name: 'Skip to content' }));
  expect(document.activeElement?.id).toBe('review-content');
  expect(location.hash).toBe(before);
  expect(screen.getByRole('link', { name: /Conversations 0/ }).getAttribute('aria-current')).toBe('page');
});
