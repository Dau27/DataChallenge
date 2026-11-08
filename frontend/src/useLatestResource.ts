import { useCallback, useEffect, useRef, useState } from 'react';

type Scope<T> = { key: string; generation: number; pending?: Promise<T | undefined> };
type Outcome<T> = { scope: Scope<T>; value?: T; error: string; pending: boolean };

// The key must include every input that changes which resource is being read.
// A new scope object also protects A -> B -> A transitions from the first A.
export function useLatestResource<T>(key: string, fetcher: () => Promise<T>, keepValue = false) {
  const current = useRef<Scope<T> | null>(null);
  if (!current.current || current.current.key !== key) current.current = { key, generation: 0 };
  const scope = current.current;
  const mounted = useRef(false);
  const latestFetcher = useRef(fetcher); latestFetcher.current = fetcher;
  const [outcome, setOutcome] = useState<Outcome<T> | null>(null);

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      if (current.current) { current.current.generation++; current.current.pending = undefined; }
    };
  }, []);

  const reload = useCallback((): Promise<T | undefined> => {
    if (!mounted.current || current.current !== scope) return Promise.resolve(undefined);
    if (scope.pending) return scope.pending;
    const generation = ++scope.generation;
    const active = () => mounted.current && current.current === scope && scope.generation === generation;
    const read = latestFetcher.current;
    setOutcome(previous => ({ scope, value: keepValue && previous?.scope === scope ? previous.value : undefined,
      error: '', pending: true }));
    const promise = Promise.resolve().then(() => active() ? read() : undefined).then(value => {
      if (!active()) return undefined;
      setOutcome({ scope, value, error: '', pending: false });
      return value;
    }, error => {
      if (!active()) return undefined;
      setOutcome(previous => ({ scope, value: keepValue && previous?.scope === scope ? previous.value : undefined,
        error: error instanceof Error ? error.message : 'Could not load this resource.', pending: false }));
      throw error;
    }).finally(() => { if (scope.pending === promise) scope.pending = undefined; });
    scope.pending = promise;
    return promise;
  }, [scope, keepValue]);

  useEffect(() => { void reload().catch(() => {}); }, [reload]);
  const visible = outcome?.scope === scope ? outcome : null;
  return { value: visible?.value, error: visible?.error ?? '', pending: visible?.pending ?? true, reload };
}
