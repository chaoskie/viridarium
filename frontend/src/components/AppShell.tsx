import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";

import { ThemeToggle } from "@/components/ThemeToggle";

interface NavItem {
  readonly label: string;
  readonly to: string;
  /** Decorative glyph for the compact mobile bottom bar. */
  readonly glyph: string;
}

// Primary nav for the v1 information architecture (product-spec E2-E4). Labels
// are plain English per D-008 (no Latin functional labels). Only "Today" has a
// real page in the walking skeleton.
const NAV_ITEMS: readonly NavItem[] = [
  { label: "Today", to: "/", glyph: "☀" },
  { label: "Plants", to: "/plants", glyph: "🌿" },
  { label: "Rooms", to: "/rooms", glyph: "▦" },
  { label: "Journal", to: "/journal", glyph: "✒" },
  { label: "Settings", to: "/settings", glyph: "⚙" },
];

interface AppShellProps {
  readonly children: ReactNode;
}

export function AppShell({ children }: AppShellProps): ReactNode {
  return (
    <div className="flex min-h-screen flex-col text-ink">
      <header className="border-b-card border-border bg-surface-raised">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-3 px-4 py-4">
          {/* min-w-0 lets the brand shrink so the row never overflows a narrow
              phone header (BUG-001); the glyph stays fixed, the wordmark truncates
              only as a last resort. */}
          <div className="flex min-w-0 items-center gap-3">
            <span
              aria-hidden="true"
              className="grid min-h-tap-min min-w-tap-min shrink-0 place-items-center rounded-control border-card border-border bg-surface text-xl text-accent-2-strong shadow-raised"
            >
              ❦
            </span>
            {/* Wordmark: Latin allowed as the brand (D-008). Interpunct split. */}
            <span className="truncate font-display text-xl font-semibold uppercase tracking-wide text-ink sm:text-2xl sm:tracking-widest">
              VIRID<span className="text-accent">·ARIVM</span>
            </span>
          </div>

          {/* Tablet+ inline nav. On phone the bottom bar replaces this. */}
          <div className="hidden items-center gap-4 sm:flex">
            <nav aria-label="Primary">
              <ul className="flex flex-wrap items-center gap-1">
                {NAV_ITEMS.map((item) => (
                  <li key={item.to}>
                    <NavLink
                      to={item.to}
                      end={item.to === "/"}
                      className={({ isActive }) =>
                        [
                          "flex min-h-tap-min items-center rounded-control border-control px-3 font-label text-xs font-semibold uppercase tracking-widest",
                          isActive
                            ? "border-border bg-accent-soft text-accent-strong"
                            : "border-transparent text-ink-muted hover:text-ink",
                        ].join(" ")
                      }
                    >
                      {item.label}
                    </NavLink>
                  </li>
                ))}
              </ul>
            </nav>
            <ThemeToggle />
          </div>

          {/* Phone: toggle stays in the header (always reachable, FE-011). */}
          <div className="sm:hidden">
            <ThemeToggle />
          </div>
        </div>

        {/* Greek-key meander divider (Roman / dark motif). */}
        <div
          aria-hidden="true"
          className="meander-rule mx-auto max-w-5xl px-4"
        />
      </header>

      <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-6 pb-28 sm:py-8 sm:pb-8">
        {children}
      </main>

      {/* Phone-only bottom navigation bar (one-handed reach, >=44px taps). */}
      <nav
        aria-label="Primary mobile"
        className="fixed inset-x-0 bottom-0 z-10 border-t-card border-border bg-surface-raised shadow-raised sm:hidden"
      >
        <ul className="mx-auto flex max-w-5xl items-stretch justify-between px-2">
          {NAV_ITEMS.map((item) => (
            <li key={item.to} className="flex-1">
              <NavLink
                to={item.to}
                end={item.to === "/"}
                className={({ isActive }) =>
                  [
                    "flex min-h-tap-min flex-col items-center justify-center gap-0.5 py-2 font-label text-xs font-semibold uppercase tracking-wide",
                    isActive
                      ? "text-accent-strong"
                      : "text-ink-muted hover:text-ink",
                  ].join(" ")
                }
              >
                <span aria-hidden="true" className="text-base leading-none">
                  {item.glyph}
                </span>
                {item.label}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
    </div>
  );
}
