/**
 * Theme controller (FE-002 multi-theme support).
 *
 * Single source of truth for: the set of valid themes, the default, the
 * localStorage key, and the read/resolve/apply/persist logic. The inline
 * pre-paint script in index.html mirrors KEY / THEMES / DEFAULT and the
 * prefers-color-scheme precedence to avoid a theme flash; keep them in sync.
 *
 * Default + first-load precedence (D-008):
 *   1. a valid stored choice always wins;
 *   2. else, if the OS prefers a dark scheme, use "dark";
 *   3. else, the Roman default.
 */

export const THEMES = [
  "roman",
  "dark",
  "herbarium",
  "terracotta",
  "viridian",
] as const;

export type Theme = (typeof THEMES)[number];

export const DEFAULT_THEME: Theme = "roman";

export const THEME_STORAGE_KEY = "viridarium.theme";

/** Human labels for the toggle control. */
export const THEME_LABELS: Readonly<Record<Theme, string>> = {
  roman: "Roman",
  dark: "Dark",
  herbarium: "Herbarium",
  terracotta: "Terracotta",
  viridian: "Viridian",
};

export function isTheme(value: string | null): value is Theme {
  return value !== null && (THEMES as readonly string[]).includes(value);
}

/**
 * Read the persisted theme, or `null` when nothing valid is stored. Never
 * throws. Distinct from the resolved initial theme: callers that need the
 * prefers-color-scheme fallback use `getInitialTheme()`.
 */
export function readStoredTheme(): Theme | null {
  let stored: string | null = null;
  try {
    stored = window.localStorage.getItem(THEME_STORAGE_KEY);
  } catch {
    stored = null;
  }
  return isTheme(stored) ? stored : null;
}

/** Whether the OS reports a dark color-scheme preference. Never throws. */
export function systemPrefersDark(): boolean {
  try {
    return (
      typeof window.matchMedia === "function" &&
      window.matchMedia("(prefers-color-scheme: dark)").matches
    );
  } catch {
    return false;
  }
}

/**
 * The theme to use on first paint / mount: a stored choice wins; else the OS
 * dark preference selects "dark"; else the Roman default. Mirrors index.html.
 */
export function getInitialTheme(): Theme {
  const stored = readStoredTheme();
  if (stored !== null) {
    return stored;
  }
  return systemPrefersDark() ? "dark" : DEFAULT_THEME;
}

/** Apply a theme to the document root (sets data-theme on <html>). */
export function applyTheme(theme: Theme): void {
  document.documentElement.setAttribute("data-theme", theme);
}

/** Persist the chosen theme. Never throws (private mode / disabled storage). */
export function persistTheme(theme: Theme): void {
  try {
    window.localStorage.setItem(THEME_STORAGE_KEY, theme);
  } catch {
    // Storage unavailable: in-memory selection still applies for the session.
  }
}

/** The next theme in the cycle, wrapping around. */
export function nextTheme(theme: Theme): Theme {
  const index = THEMES.indexOf(theme);
  const next = THEMES[(index + 1) % THEMES.length];
  // THEMES is non-empty, so this is always defined; assert for the type.
  return next ?? DEFAULT_THEME;
}
