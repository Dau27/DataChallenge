// @vitest-environment happy-dom
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import PrintableEvaluation from './PrintableEvaluation';
import { syntheticPrintPacket } from './printEvaluationFixtures';

beforeEach(() => {
  // Unit tests never navigate an iframe; real document/print layout is checked separately.
  (window as unknown as { happyDOM: { settings: { disableIframePageLoading: boolean } } }).happyDOM.settings.disableIframePageLoading = true;
});
afterEach(() => { cleanup(); vi.restoreAllMocks(); vi.unstubAllGlobals(); });
const response = (packet: unknown) => ({ ok: true, json: async () => packet }) as Response;
const identity = { evaluationId: 'SYNTHETIC_PRINT_RUN', updatedAt: '2026-11-08T00:00:00+00:00' };
const deferred = () => { let resolve!: (r: Response) => void; const promise = new Promise<Response>(r => { resolve = r; }); return { promise, resolve }; };
const openPreview = () => fireEvent.click(screen.getByRole('button', { name: 'Preview saved report' }));
async function preview() { return await screen.findByTitle('Saved evaluation report preview') as HTMLIFrameElement; }

it('fetches only the existing sanitized JSON export after an explicit open and prints only after another explicit action', async () => {
  const fetch = vi.spyOn(globalThis, 'fetch').mockResolvedValue(response(syntheticPrintPacket()));
  render(<PrintableEvaluation {...identity} />);
  expect(fetch).not.toHaveBeenCalled();
  openPreview();
  expect((screen.getByRole('button', { name: 'Print / Save as PDF' }) as HTMLButtonElement).disabled).toBe(true);
  const iframe = await preview();
  expect(fetch).toHaveBeenCalledTimes(1);
  expect(fetch.mock.calls[0][0]).toBe('/api/evaluations/SYNTHETIC_PRINT_RUN/export?format=json&include_excerpts=false');
  expect(iframe.getAttribute('sandbox')).toBe('allow-same-origin allow-modals');
  expect(iframe.srcdoc).toContain('SYNTHETIC_SOURCE_HASH');
  const print = vi.fn(), focus = vi.fn();
  Object.defineProperty(iframe, 'contentWindow', { configurable: true, value: { print, focus } });
  fireEvent.load(iframe);
  expect(print).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole('button', { name: 'Print / Save as PDF' }));
  expect(focus).toHaveBeenCalledOnce(); expect(print).toHaveBeenCalledOnce();
});

it('invalidates immediately on excerpt changes and ignores an older response when options return to A', async () => {
  const a = deferred(), b = deferred(), latest = deferred();
  const fetch = vi.spyOn(globalThis, 'fetch').mockImplementation(() => new Promise(() => {}))
    .mockReturnValueOnce(a.promise).mockReturnValueOnce(b.promise).mockReturnValueOnce(latest.promise);
  render(<PrintableEvaluation {...identity} />); openPreview();
  await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1));
  fireEvent.click(screen.getByLabelText('Include source evidence excerpts'));
  await waitFor(() => expect(fetch).toHaveBeenCalledTimes(2));
  fireEvent.click(screen.getByLabelText('Include source evidence excerpts'));
  await waitFor(() => expect(fetch).toHaveBeenCalledTimes(3));
  a.resolve(response(syntheticPrintPacket())); b.resolve(response(syntheticPrintPacket(undefined, undefined, true)));
  await Promise.resolve(); expect(screen.queryByTitle('Saved evaluation report preview')).toBeNull();
  latest.resolve(response(syntheticPrintPacket()));
  const iframe = await preview(); expect(iframe.srcdoc).not.toContain('SYNTHETIC source excerpt.');
  fireEvent.click(screen.getByLabelText('Include source evidence excerpts'));
  expect(screen.queryByTitle('Saved evaluation report preview')).toBeNull();
  expect((screen.getByRole('button', { name: 'Print / Save as PDF' }) as HTMLButtonElement).disabled).toBe(true);
  await waitFor(() => expect(fetch).toHaveBeenCalledTimes(4));
});

it('rejects a stale update or wrong run, then retries safely without clearing the selected run', async () => {
  const fetch = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(response(syntheticPrintPacket('OTHER'))).mockResolvedValueOnce(response(syntheticPrintPacket()));
  render(<PrintableEvaluation {...identity} />); openPreview();
  expect((await screen.findByRole('alert')).textContent).toContain('another run');
  expect(screen.queryByTitle('Saved evaluation report preview')).toBeNull();
  fireEvent.click(screen.getByRole('button', { name: 'Retry print preview' }));
  await preview(); expect(fetch).toHaveBeenCalledTimes(2);
});

it('hides the old preview on same-run review updates and ignores older run/update responses', async () => {
  const a = deferred(), b = deferred(), c = deferred();
  const fetch = vi.spyOn(globalThis, 'fetch').mockReturnValueOnce(a.promise).mockReturnValueOnce(b.promise).mockReturnValueOnce(c.promise);
  const view = render(<PrintableEvaluation {...identity} />); openPreview();
  await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1));
  view.rerender(<PrintableEvaluation {...identity} updatedAt="NEW_UPDATE" />);
  await waitFor(() => expect(fetch).toHaveBeenCalledTimes(2));
  a.resolve(response(syntheticPrintPacket()));
  b.resolve(response(syntheticPrintPacket(identity.evaluationId, 'NEW_UPDATE')));
  expect((await preview()).srcdoc).toContain('NEW_UPDATE');
  view.rerender(<PrintableEvaluation evaluationId="NEXT_RUN" updatedAt="NEXT_UPDATE" />);
  expect(screen.queryByTitle('Saved evaluation report preview')).toBeNull();
  await waitFor(() => expect(fetch).toHaveBeenCalledTimes(3));
  c.resolve(response(syntheticPrintPacket('NEXT_RUN', 'NEXT_UPDATE')));
  expect((await preview()).srcdoc).toContain('NEXT_RUN');
});

it('offers network/server error retry, supports focus and close/reopen without printing', async () => {
  const fetch = vi.spyOn(globalThis, 'fetch').mockRejectedValueOnce(new Error('offline'))
    .mockResolvedValueOnce(response(syntheticPrintPacket())).mockResolvedValueOnce(response(syntheticPrintPacket()));
  render(<PrintableEvaluation {...identity} />);
  const trigger = screen.getByRole('button', { name: 'Preview saved report' }); trigger.focus(); openPreview();
  expect(document.activeElement).toBe(screen.getByRole('heading', { name: 'Print preview · original and effective' }));
  expect((await screen.findByRole('alert')).textContent).toContain('backend is unavailable');
  fireEvent.click(screen.getByRole('button', { name: 'Retry print preview' }));
  const iframe = await preview();
  const print = vi.fn(); Object.defineProperty(iframe, 'contentWindow', { configurable: true, value: { print, focus: vi.fn() } });
  fireEvent.load(iframe); expect(print).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole('button', { name: 'Close print preview' }));
  expect(document.activeElement).toBe(trigger); expect(screen.queryByTitle('Saved evaluation report preview')).toBeNull();
  openPreview(); await preview(); expect(fetch).toHaveBeenCalledTimes(3); expect(print).not.toHaveBeenCalled();
});

it('does not accept a late response after closing or unmounting', async () => {
  const pending = deferred(); vi.spyOn(globalThis, 'fetch').mockReturnValue(pending.promise);
  const view = render(<PrintableEvaluation {...identity} />); openPreview();
  fireEvent.click(screen.getByRole('button', { name: 'Close print preview' }));
  view.unmount(); pending.resolve(response(syntheticPrintPacket()));
  await Promise.resolve(); expect(screen.queryByTitle('Saved evaluation report preview')).toBeNull();
});

it('keeps browser print failures visible and retryable, and does not print the whole parent window', async () => {
  vi.spyOn(globalThis, 'fetch').mockResolvedValue(response(syntheticPrintPacket()));
  const parentPrint = vi.fn(); vi.stubGlobal('print', parentPrint);
  render(<PrintableEvaluation {...identity} />); openPreview(); const iframe = await preview();
  const childPrint = vi.fn().mockImplementationOnce(() => { throw new Error('SYNTHETIC sandbox failure'); });
  Object.defineProperty(iframe, 'contentWindow', { configurable: true, value: { print: childPrint, focus: vi.fn() } });
  fireEvent.load(iframe); fireEvent.click(screen.getByRole('button', { name: 'Print / Save as PDF' }));
  expect(screen.getByRole('alert').textContent).toContain('could not open printing');
  fireEvent.click(screen.getByRole('button', { name: 'Print / Save as PDF' }));
  expect(childPrint).toHaveBeenCalledTimes(2); expect(parentPrint).not.toHaveBeenCalled();
});

it('offers retry when the browser fails to load the current iframe and keeps printing disabled', async () => {
  const fetch = vi.spyOn(globalThis, 'fetch').mockResolvedValue(response(syntheticPrintPacket()));
  render(<PrintableEvaluation {...identity} />); openPreview(); const iframe = await preview();
  fireEvent.error(iframe);
  expect(screen.getByRole('alert').textContent).toContain('could not load the report preview');
  expect((screen.getByRole('button', { name: 'Print / Save as PDF' }) as HTMLButtonElement).disabled).toBe(true);
  fireEvent.click(screen.getByRole('button', { name: 'Retry print preview' }));
  await waitFor(() => expect(fetch).toHaveBeenCalledTimes(2));
  expect(await preview()).not.toBe(iframe);
});
