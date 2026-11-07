// All service access is centralized for later Dynamics 365 HTML-component embedding.
import type { FieldIssue } from './types';
export class ApiError extends Error {
  constructor(message: string, public status: number, public issues: FieldIssue[] = []) { super(message); }
}
export type ReportFormat = 'json' | 'csv' | 'simple_csv';
async function downloadReport(path: string, filename: string, active: () => boolean) {
  let response: Response;
  try { response = await fetch(`/api${path}`); }
  catch { throw new Error('The backend is unavailable. Start the local server, then retry.'); }
  if (!response.ok) {
    const result = await response.json().catch(() => null);
    throw new Error(typeof result?.detail === 'string' ? result.detail : `Export failed (${response.status}).`);
  }
  const blob = await response.blob();
  if (!active()) return;
  const url = URL.createObjectURL(blob); const link = document.createElement('a');
  link.href = url; link.download = filename;
  document.body.appendChild(link);
  try { link.click(); } finally { link.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000); }
}
export async function downloadSavedReport(id: string, format: ReportFormat, excerpts: boolean, active: () => boolean) {
  const stem = `cqa-${id.replace(/[^a-zA-Z0-9_-]/g, '').slice(0, 80) || 'saved'}`;
  const filename = format === 'simple_csv' ? `${stem}-criteria.csv` : `${stem}.${format}`;
  return downloadReport(`/evaluations/${encodeURIComponent(id)}/export?format=${format}&include_excerpts=${excerpts}`, filename, active);
}
export async function downloadSelectedReports(ids: string[], format: ReportFormat, excerpts: boolean, active: () => boolean) {
  if (!ids.length || ids.length > 100 || ids.some(id => !id.trim() || id.length > 200) || new Set(ids).size !== ids.length) {
    throw new Error('Select between 1 and 100 unique saved runs to export.');
  }
  const params = new URLSearchParams({ format, include_excerpts: String(excerpts) });
  ids.forEach(id => params.append('evaluation_id', id));
  const filename = format === 'simple_csv' ? 'cqa-selected-criteria.csv' : `cqa-selected.${format}`;
  return downloadReport(`/evaluations/export-batch?${params}`, filename, active);
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
