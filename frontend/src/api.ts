// All service access is centralized for later Dynamics 365 HTML-component embedding.
import type { FieldIssue } from './types';
export class ApiError extends Error {
  constructor(message: string, public status: number, public issues: FieldIssue[] = []) { super(message); }
}
export async function downloadSavedReport(id: string, format: 'json' | 'csv', excerpts: boolean, active: () => boolean) {
  let response: Response;
  try { response = await fetch(`/api/evaluations/${encodeURIComponent(id)}/export?format=${format}&include_excerpts=${excerpts}`); }
  catch { throw new Error('The backend is unavailable. Start the local server, then retry.'); }
  if (!response.ok) {
    const result = await response.json().catch(() => null);
    throw new Error(typeof result?.detail === 'string' ? result.detail : `Export failed (${response.status}).`);
  }
  const blob = await response.blob();
  if (!active()) return;
  const url = URL.createObjectURL(blob); const link = document.createElement('a');
  link.href = url; link.download = `cqa-${id.replace(/[^a-zA-Z0-9_-]/g, '').slice(0, 80) || 'saved'}.${format}`;
  document.body.appendChild(link);
  try { link.click(); } finally { link.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000); }
}
export async function api<T>(path: string, body?: unknown): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`/api${path}`, body === undefined ? undefined : {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
    });
  } catch {
    throw new Error('The backend is unavailable. Start the local server, then retry.');
  }
  const result = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = result?.detail;
    throw new ApiError(Array.isArray(detail)
      ? detail.map((e: { location?: string[]; message?: string; msg?: string }) => `${(e.location ?? []).join(' → ')}: ${e.message ?? e.msg}`).join('\n')
      : typeof detail === 'string' ? detail : `Request failed (${response.status}).`, response.status,
      Array.isArray(detail) ? detail.map((e: FieldIssue) => ({ ...e, location: e.location?.[0] === 'body' ? e.location.slice(1) : e.location ?? [] })) : []);
  }
  return result as T;
}
