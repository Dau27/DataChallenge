// @vitest-environment happy-dom
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import QueueExport from './QueueExport';
import SavedExport from './SavedExport';
import { downloadSelectedReports } from './api';

beforeEach(() => { localStorage.clear(); });
afterEach(() => { cleanup(); vi.restoreAllMocks(); localStorage.clear(); });
function downloads() {
  const blobs: Blob[] = []; const filenames: string[] = [];
  vi.spyOn(URL, 'createObjectURL').mockImplementation(blob => { blobs.push(blob as Blob); return 'blob:SYNTHETIC'; });
  vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => {});
  vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(function (this: HTMLAnchorElement) { filenames.push(this.download); });
  return { blobs, filenames };
}

it('keeps selected exports disabled for empty, duplicate or excessive selections without any request', () => {
  const fetchMock = vi.spyOn(globalThis, 'fetch').mockRejectedValue(new Error('No request expected'));
  const view = render(<QueueExport evaluationIds={[]} />);
  expect((screen.getByRole('button', { name: 'Selected JSON' }) as HTMLButtonElement).disabled).toBe(true);
  fireEvent.click(screen.getByRole('button', { name: 'Selected JSON' }));
  view.rerender(<QueueExport evaluationIds={['SAVED', 'SAVED']} />);
  expect((screen.getByRole('button', { name: 'Selected archive CSV' }) as HTMLButtonElement).disabled).toBe(true);
  expect(screen.getByRole('alert').textContent).toContain('unique');
  view.rerender(<QueueExport evaluationIds={Array.from({ length: 101 }, (_, i) => `SAVED_${i}`)} />);
  expect((screen.getByRole('button', { name: 'Selected simple CSV' }) as HTMLButtonElement).disabled).toBe(true);
  expect(fetchMock).not.toHaveBeenCalled();
});

it('downloads exactly the selected saved IDs with explicit excerpts and CSV extensions', async () => {
  const saved = downloads(); const requests: { url: string; options?: RequestInit }[] = [];
  vi.spyOn(globalThis, 'fetch').mockImplementation(async (url, options) => {
    requests.push({ url: String(url), options }); return new Response('SYNTHETIC_SAVED_REPORT');
  });
  render(<QueueExport evaluationIds={['SAVED_B', 'SAVED_A']} />);
  fireEvent.click(screen.getByRole('button', { name: 'Selected JSON' }));
  await waitFor(() => expect(saved.filenames).toHaveLength(1));
  const first = new URL(requests[0].url, 'http://localhost');
  expect(first.pathname).toBe('/api/evaluations/export-batch');
  expect(first.searchParams.getAll('evaluation_id')).toEqual(['SAVED_B', 'SAVED_A']);
  expect(first.searchParams.get('include_excerpts')).toBe('false');
  fireEvent.click(screen.getByLabelText('Include selected source evidence excerpts'));
  fireEvent.click(screen.getByRole('button', { name: 'Selected simple CSV' }));
  await waitFor(() => expect(saved.filenames).toHaveLength(2));
  expect(new URL(requests[1].url, 'http://localhost').searchParams.get('format')).toBe('simple_csv');
  expect(new URL(requests[1].url, 'http://localhost').searchParams.get('include_excerpts')).toBe('true');
  expect(saved.filenames).toEqual(['cqa-selected.json', 'cqa-selected-criteria.csv']);
  expect(await saved.blobs[1].text()).toBe('SYNTHETIC_SAVED_REPORT');
  expect(requests.every(r => r.options === undefined)).toBe(true);
});

it('invalidates pending downloads when the visible selection changes and preserves a newer download', async () => {
  const saved = downloads(); let release: ((response: Response) => void) | undefined;
  vi.spyOn(globalThis, 'fetch').mockImplementationOnce(() => new Promise(resolve => { release = resolve; }))
    .mockResolvedValue(new Response('NEW_SELECTION_ONLY'));
  const view = render(<QueueExport evaluationIds={['OLD']} />);
  fireEvent.click(screen.getByRole('button', { name: 'Selected JSON' }));
  await waitFor(() => expect(release).toBeDefined());
  view.rerender(<QueueExport evaluationIds={['NEW']} />);
  await waitFor(() => expect((screen.getByRole('button', { name: 'Selected JSON' }) as HTMLButtonElement).disabled).toBe(false));
  fireEvent.click(screen.getByRole('button', { name: 'Selected JSON' }));
  await waitFor(() => expect(saved.blobs).toHaveLength(1));
  release!(new Response('OLD_SELECTION_MUST_NOT_DOWNLOAD'));
  await new Promise(resolve => setTimeout(resolve, 10));
  expect(saved.blobs).toHaveLength(1); expect(await saved.blobs[0].text()).toBe('NEW_SELECTION_ONLY');
});

it('shows selected export failures, allows retry and ignores a response after unmount', async () => {
  const saved = downloads(); let release: ((response: Response) => void) | undefined;
  vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(new Response(JSON.stringify({ detail: 'One selected saved run is unavailable' }), { status: 404 }))
    .mockImplementationOnce(() => new Promise(resolve => { release = resolve; }));
  const view = render(<QueueExport evaluationIds={['SAVED']} />);
  fireEvent.click(screen.getByRole('button', { name: 'Selected archive CSV' }));
  await screen.findByText(/One selected saved run is unavailable/);
  expect(saved.blobs).toHaveLength(0);
  fireEvent.click(screen.getByRole('button', { name: 'Selected archive CSV' }));
  await waitFor(() => expect(release).toBeDefined());
  view.unmount(); release!(new Response('LATE_REPORT'));
  await new Promise(resolve => setTimeout(resolve, 10));
  expect(saved.blobs).toHaveLength(0);
});

it('offers a simple criterion CSV for one saved run without changing archival download controls', async () => {
  const saved = downloads(); const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response('FLAT_CRITERIA'));
  render(<SavedExport evaluationId="SAVED" />);
  expect(screen.getByRole('button', { name: 'Download CSV' })).toBeDefined();
  fireEvent.click(screen.getByRole('button', { name: 'Download simple CSV' }));
  await waitFor(() => expect(saved.filenames).toEqual(['cqa-SAVED-criteria.csv']));
  expect(fetchMock.mock.calls[0][0]).toBe('/api/evaluations/SAVED/export?format=simple_csv&include_excerpts=false');
  expect(screen.getByText(/Simple CSV contains criterion rows/)).toBeDefined();
});

it('cancels a single-run download when its run prop changes without unmounting', async () => {
  const saved = downloads(); let release: ((response: Response) => void) | undefined;
  vi.spyOn(globalThis, 'fetch').mockImplementation(() => new Promise(resolve => { release = resolve; }));
  const view = render(<SavedExport evaluationId="OLD" />);
  fireEvent.click(screen.getByRole('button', { name: 'Download simple CSV' }));
  await waitFor(() => expect(release).toBeDefined());
  view.rerender(<SavedExport evaluationId="NEW" />);
  release!(new Response('OLD_REPORT'));
  await new Promise(resolve => setTimeout(resolve, 10));
  expect(saved.blobs).toHaveLength(0);
});

it('rejects invalid helper selections before fetching, including blank IDs', async () => {
  const fetchMock = vi.spyOn(globalThis, 'fetch').mockRejectedValue(new Error('No request expected'));
  for (const ids of [[], [' '], ['A', 'A'], ['x'.repeat(201)]]) {
    await expect(downloadSelectedReports(ids, 'json', false, () => true)).rejects.toThrow('unique saved runs');
  }
  expect(fetchMock).not.toHaveBeenCalled();
});
