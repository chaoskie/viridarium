import { useCallback, useEffect, useState } from "react";

import {
  applyTheme,
  getInitialTheme,
  nextTheme,
  persistTheme,
  type Theme,
} from "./themeController";

export interface UseThemeResult {
  /** The active theme. */
  readonly theme: Theme;
  /** Set a specific theme (applies + persists). */
  readonly setTheme: (theme: Theme) => void;
  /** Advance to the next theme in the cycle. */
  readonly cycleTheme: () => void;
}

/**
 * Typed theme hook. Initialises from the resolved initial theme (stored choice,
 * else prefers-color-scheme, else Roman - matching the pre-paint inline
 * script), re-applies on mount, and keeps <html data-theme> + localStorage in
 * sync on every change.
 */
export function useTheme(): UseThemeResult {
  const [theme, setThemeState] = useState<Theme>(() => getInitialTheme());

  // Re-assert on mount so the DOM matches state even if the inline script and
  // state ever diverge (e.g. storage changed between paint and hydration).
  useEffect(() => {
    applyTheme(theme);
  }, [theme]);

  const setTheme = useCallback((next: Theme) => {
    applyTheme(next);
    persistTheme(next);
    setThemeState(next);
  }, []);

  const cycleTheme = useCallback(() => {
    setThemeState((current) => {
      const next = nextTheme(current);
      applyTheme(next);
      persistTheme(next);
      return next;
    });
  }, []);

  return { theme, setTheme, cycleTheme };
}
