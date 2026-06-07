import type { ReactNode } from "react";

import { THEMES, THEME_LABELS, type Theme } from "@/lib/theme/themeController";
import { useTheme } from "@/lib/theme/useTheme";

/**
 * Minimal theme selector for the app-shell header. Stands in as the
 * Settings-page placeholder until a real settings surface exists. Renders a
 * segmented control of all themes so switching is one tap (FE-011 tap targets).
 */
export function ThemeToggle(): ReactNode {
  const { theme, setTheme } = useTheme();

  return (
    <div
      role="group"
      aria-label="Theme"
      className="flex items-center gap-1 rounded-pill border-control border-border bg-surface p-1"
    >
      {THEMES.map((option: Theme) => {
        const isActive = option === theme;
        return (
          <button
            key={option}
            type="button"
            onClick={() => setTheme(option)}
            aria-pressed={isActive}
            aria-label={`Use ${THEME_LABELS[option]} theme`}
            className={[
              "min-h-tap-min rounded-pill px-3 font-label text-xs font-bold uppercase tracking-wide transition-colors",
              isActive
                ? "bg-accent text-ink-inverse"
                : "text-ink-muted hover:text-ink",
            ].join(" ")}
          >
            {THEME_LABELS[option]}
          </button>
        );
      })}
    </div>
  );
}
