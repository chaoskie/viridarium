/**
 * Theme controller (FE-002 multi-theme support).
 *
 * Single source of truth for: the set of valid themes, the default, the
 * localStorage key, and the read/apply/persist logic. The inline pre-paint
 * script in index.html mirrors KEY / THEMES / DEFAULT to avoid a theme flash;
 * keep them in sync.
 */

export const THEMES = ["terracotta", "herbarium"] as const;

export type Theme = (typeof THEMES)[number];

export const DEFAULT_THEME: Theme = "terracotta";

export const THEME_STORAGE_KEY = "viridarium.theme";

/** Human labels for the toggle control. */
export const THEME_LABELS: Readonly<Record<Theme, string>> = {
  terracotta: "Terracotta",
  herbarium: "Herbarium",
};

export function isTheme(value: string | null): value is Theme {
  return value !== null && (THEMES as readonly string[]).includes(value);
}

/** Read the persisted theme, falling back to the default. Never throws. */
export function readStoredTheme(): Theme {
  let stored: string | null = null;
  try {
    stored = window.localStorage.getItem(THEME_STORAGE_KEY);
  } catch {
    stored = null;
  }
  return isTheme(stored) ? stored : DEFAULT_THEME;
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
