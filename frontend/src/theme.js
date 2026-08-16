import { useCallback, useSyncExternalStore } from "react";
import { readStore, subscribeStore, writeStore } from "./localStore";

const KEY = "sizehive.theme.v1";

export const THEMES = ["system", "light", "dark"];

function prefersDark() {
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ?? false;
}

export function resolveTheme(theme) {
  return theme === "system" ? (prefersDark() ? "dark" : "light") : theme;
}

// The CSS only knows [data-theme="dark"] / default-light, so "system" is
// resolved here and re-resolved when the OS preference flips.
function apply(theme) {
  document.documentElement.dataset.theme = resolveTheme(theme);
}

export function initTheme() {
  const stored = readStore(KEY, "system");
  apply(stored);

  const media = window.matchMedia?.("(prefers-color-scheme: dark)");
  media?.addEventListener("change", () => {
    if (readStore(KEY, "system") === "system") apply("system");
  });
}

export function setTheme(theme) {
  if (!THEMES.includes(theme)) return;
  writeStore(KEY, theme);
  apply(theme);
}

export function useTheme() {
  const subscribe = useCallback((callback) => subscribeStore(KEY, callback), []);
  return useSyncExternalStore(subscribe, () => readStore(KEY, "system"), () => "system");
}
