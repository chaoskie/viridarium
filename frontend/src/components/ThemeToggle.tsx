import { useId } from "react";
import type { ChangeEvent, ReactNode } from "react";

import { THEMES, THEME_LABELS, isTheme } from "@/lib/theme/themeController";
import { useTheme } from "@/lib/theme/useTheme";

/**
 * Theme selector for the app-shell header. A native <select> (one tap, fully
 * keyboard/AT accessible, comfortably tall) - chosen over a segmented button
 * row because four themes crowd a 390px-wide phone header. Stays reachable on
 * every breakpoint (FE-011). Stands in as the Settings-page placeholder until a
 * real settings surface exists.
 */
export function ThemeToggle(): ReactNode {
  const { theme, setTheme } = useTheme();
  const selectId = useId();

  function handleChange(event: ChangeEvent<HTMLSelectElement>): void {
    const value = event.target.value;
    if (isTheme(value)) {
      setTheme(value);
    }
  }

  return (
    <div className="flex items-center gap-2">
      {/*
        The text label is hidden on phones to keep the header within a ~384px
        viewport (BUG-001/002); the select keeps an always-present accessible name
        via aria-label. On tablet+ the visible label returns.
      */}
      <label
        htmlFor={selectId}
        className="hidden font-label text-xs font-semibold uppercase tracking-widest text-ink-muted sm:block"
      >
        Theme
      </label>
      <select
        id={selectId}
        aria-label="Theme"
        value={theme}
        onChange={handleChange}
        className="min-h-tap-min rounded-control border-control border-border bg-surface px-3 font-label text-xs font-semibold uppercase tracking-widest text-ink focus:outline-none focus:ring-2 focus:ring-ring"
      >
        {THEMES.map((option) => (
          <option key={option} value={option}>
            {THEME_LABELS[option]}
          </option>
        ))}
      </select>
    </div>
  );
}
