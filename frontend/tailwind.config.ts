import type { Config } from "tailwindcss";

/**
 * Theme-token layer (FE-002).
 *
 * Every value below resolves to a semantic CSS custom property defined in
 * `src/styles/tokens.css`. Components reference Tailwind classes
 * (`bg-surface`, `text-accent`, `rounded-card`, `font-display`) and never
 * raw hex / px values. Themes drop in by swapping the token VALUES (or adding
 * a `[data-theme="..."]` block) in tokens.css only - this config and all
 * component markup stay untouched.
 *
 * The helper wraps each var with a fallback so a missing token degrades
 * loudly-but-safely rather than rendering `transparent`.
 */
const token = (name: string, fallback: string): string =>
  `var(--${name}, ${fallback})`;

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Surfaces
        surface: token("color-surface", "#ffffff"),
        "surface-raised": token("color-surface-raised", "#f5f5f4"),
        "surface-sunken": token("color-surface-sunken", "#e7e5e4"),
        // Text / ink
        ink: token("color-ink", "#1c1917"),
        "ink-muted": token("color-ink-muted", "#57534e"),
        "ink-inverse": token("color-ink-inverse", "#fafaf9"),
        // Brand / interactive
        accent: token("color-accent", "#15803d"),
        "accent-strong": token("color-accent-strong", "#166534"),
        "accent-soft": token("color-accent-soft", "#dcfce7"),
        // Secondary / tertiary accents (multi-accent themes)
        "accent-2": token("color-accent-2", "#7da27a"),
        "accent-2-strong": token("color-accent-2-strong", "#547752"),
        "accent-3": token("color-accent-3", "#e3a72f"),
        "accent-3-strong": token("color-accent-3-strong", "#7a5a18"),
        // Semantic status
        danger: token("color-danger", "#b91c1c"),
        warning: token("color-warning", "#b45309"),
        success: token("color-success", "#15803d"),
        // Structure
        border: token("color-border", "#d6d3d1"),
        ring: token("color-ring", "#15803d"),
        overlay: token("color-overlay", "rgba(0, 0, 0, 0.4)"),
      },
      fontFamily: {
        display: token("font-display", "system-ui, sans-serif").split(", "),
        body: token("font-body", "system-ui, sans-serif").split(", "),
        label: token("font-label", "system-ui, sans-serif").split(", "),
        mono: token("font-mono", "ui-monospace, monospace").split(", "),
      },
      borderRadius: {
        card: token("radius-card", "0.75rem"),
        control: token("radius-control", "0.5rem"),
        pill: token("radius-pill", "9999px"),
      },
      borderWidth: {
        card: token("border-width-card", "1px"),
        control: token("border-width-control", "1px"),
      },
      boxShadow: {
        card: token("shadow-card", "0 1px 3px rgba(0, 0, 0, 0.1)"),
        raised: token("shadow-raised", "0 4px 12px rgba(0, 0, 0, 0.12)"),
      },
      spacing: {
        "tap-min": token("size-tap-min", "44px"),
      },
    },
  },
  plugins: [],
} satisfies Config;
