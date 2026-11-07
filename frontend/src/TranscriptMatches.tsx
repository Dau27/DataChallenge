import { useEffect, useState, type ReactNode } from 'react';
import { api } from './api';
import type { Conversation, MatchPage, TranscriptMatch } from './types';

function Snippet({ match }: { match: TranscriptMatch }) {
  // API offsets count Unicode source code points, including characters outside the BMP.
  const chars = Array.from(match.snippet); const parts: ReactNode[] = []; let cursor = 0;
  for (const [i, span] of (match.highlights ?? []).entries()) {
    if (!Number.isInteger(span.start) || !Number.isInteger(span.end) || span.start < cursor || span.end <= span.start || span.end > chars.length) continue;
    parts.push(chars.slice(cursor, span.start).join(''), <mark key={i}>{chars.slice(span.start, span.end).join('')}</mark>);
    cursor = span.end;
  }
  parts.push(chars.slice(cursor).join(''));
  return <p>{parts}</p>;
}

export default function TranscriptMatches({ row, query, speaker }: { row: Conversation; query: string; speaker: string }) {
  const [offset, setOffset] = useState(0); const [retry, setRetry] = useState(0);
  const [result, setResult] = useState<{ key: string; page: MatchPage | null; error: string }>({ key: '', page: null, error: '' });
  const key = JSON.stringify([row.id, row.content_hash, query, speaker, offset, retry]);
  useEffect(() => {
    if (!offset) return;
    let active = true;
    const params = new URLSearchParams({ q: query, speaker, offset: String(offset), limit: '5' });
    void api<MatchPage>(`/conversations/${encodeURIComponent(row.id)}/matches?${params}`).then(page => {
      if (page.source.id !== row.id || page.source.content_hash !== row.content_hash || page.query !== query.trim() || page.speaker !== speaker || page.offset !== offset) {
        throw new Error('Search page belongs to a different source or query. Refresh the queue.');
      }
      if (active) setResult({ key, page, error: '' });
    }).catch(e => { if (active) setResult({ key, page: null, error: e instanceof Error ? e.message : 'Match loading failed.' }); });
    return () => { active = false; };
  }, [key, offset, row.id, row.content_hash, query, speaker]);
  const initial = offset === 0; const current = result.key === key;
  const pending = !initial && !current; const error = !initial && current ? result.error : '';
  const matches = initial ? row.search_matches ?? [] : !pending && !error ? result.page?.matches ?? [] : [];
  const total = initial ? row.search_total_matches ?? 0 : current && result.page ? result.page.total_matches : row.search_total_matches ?? 0;
  return <div className="search-snippets" role="region" aria-label={`Transcript matches for ${row.source_id}`}>
    <small>{pending ? 'Loading matching messages…' : error ? 'Matching messages unavailable.' : `${matches.length ? offset + 1 : 0}–${offset + matches.length} of ${total} matching message(s)`}</small>
    {pending && <p role="status">Loading match page…</p>}
    {error && <div role="alert"><p>{error}</p><button className="secondary" onClick={() => setRetry(retry + 1)}>Retry match page</button></div>}
    {matches.map(match => <div key={match.id}>
      <a href={`#conversation/${row.id}?message=${encodeURIComponent(match.id)}${row.evaluation ? `&evaluation=${encodeURIComponent(row.evaluation.id)}` : ''}`}>{match.id} · {match.speaker} · {match.timestamp}</a><Snippet match={match} />
    </div>)}
    {total > 5 && <div className="match-navigation">
      <button className="secondary" aria-label={`Previous matches for ${row.source_id}`} disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - 5))}>Previous matches</button>
      <button className="secondary" aria-label={`Next matches for ${row.source_id}`} disabled={pending || !!error || offset + 5 >= total} onClick={() => setOffset(offset + 5)}>Next matches</button>
    </div>}
  </div>;
}
