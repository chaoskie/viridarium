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
      <label
        htmlFor={selectId}
        className="font-label text-xs font-semibold uppercase tracking-widest text-ink-muted"
      >
        Theme
      </label>
      <select
        id={selectId}
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
