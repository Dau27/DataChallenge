// All service access is centralized for later Dynamics 365 HTML-component embedding.
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
    throw new Error(Array.isArray(detail)
      ? detail.map((e: { location?: string[]; message?: string; msg?: string }) => `${(e.location ?? []).join(' → ')}: ${e.message ?? e.msg}`).join('\n')
      : typeof detail === 'string' ? detail : `Request failed (${response.status}).`);
  }
  return result as T;
}
