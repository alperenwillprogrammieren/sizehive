// A tiny reactive wrapper around localStorage.
//
// Everything in Paket 1 (Merkliste, gespeicherte Suchen, zuletzt angesehen,
// Theme) is client-side only — there are no user accounts (see CLAUDE.md).
// React components still need to re-render when one of these collections
// changes from *another* component, so each key gets its own subscriber set
// and is exposed through useSyncExternalStore.
//
// The parsed value is cached per key so getSnapshot() returns a
// referentially stable object between writes, which useSyncExternalStore
// requires (returning a fresh JSON.parse() result every call would loop).

const listeners = new Map(); // key -> Set<callback>
const cache = new Map(); // key -> last parsed value

function read(key, fallback) {
  if (cache.has(key)) return cache.get(key);
  let value = fallback;
  try {
    const raw = window.localStorage.getItem(key);
    if (raw !== null) value = JSON.parse(raw);
  } catch {
    value = fallback; // corrupt entry or storage disabled — fall back, don't crash
  }
  cache.set(key, value);
  return value;
}

function emit(key) {
  const subs = listeners.get(key);
  if (subs) for (const callback of [...subs]) callback();
}

export function readStore(key, fallback) {
  return read(key, fallback);
}

export function writeStore(key, value) {
  cache.set(key, value);
  try {
    window.localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // Quota exceeded or private mode: keep the in-memory value so the
    // current session still works, just without persistence.
  }
  emit(key);
}

export function subscribeStore(key, callback) {
  if (!listeners.has(key)) listeners.set(key, new Set());
  listeners.get(key).add(callback);

  // Cross-tab: another tab wrote this key, so drop the cache and re-read.
  const onStorage = (event) => {
    if (event.key === key || event.key === null) {
      cache.delete(key);
      callback();
    }
  };
  window.addEventListener("storage", onStorage);

  return () => {
    listeners.get(key)?.delete(callback);
    window.removeEventListener("storage", onStorage);
  };
}
