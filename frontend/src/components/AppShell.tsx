import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";

import { ThemeToggle } from "@/components/ThemeToggle";

interface NavItem {
  readonly label: string;
  readonly to: string;
}

// Nav placeholders for the v1 information architecture (product-spec E2-E4).
// Only "Today" has a real page in the walking skeleton.
const NAV_ITEMS: readonly NavItem[] = [
  { label: "Today", to: "/" },
  { label: "Plants", to: "/plants" },
  { label: "Rooms", to: "/rooms" },
  { label: "Journal", to: "/journal" },
  { label: "Settings", to: "/settings" },
];

interface AppShellProps {
  readonly children: ReactNode;
}

export function AppShell({ children }: AppShellProps): ReactNode {
  return (
    <div className="flex min-h-screen flex-col text-ink">
      <header className="border-b-card border-border bg-surface-raised">
        <div className="mx-auto flex max-w-5xl flex-col gap-3 px-4 py-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
            <span
              aria-hidden="true"
              className="grid min-h-tap-min min-w-tap-min place-items-center rounded-control border-card border-border bg-accent text-2xl shadow-raised"
            >
              🪴
            </span>
            <span className="font-display text-2xl font-extrabold tracking-tight text-ink">
              plant<span className="text-accent">keep</span>
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <nav aria-label="Primary">
              <ul className="flex flex-wrap gap-2">
                {NAV_ITEMS.map((item) => (
                  <li key={item.to}>
                    <NavLink
                      to={item.to}
                      end={item.to === "/"}
                      className={({ isActive }) =>
                        [
                          "flex min-h-tap-min items-center rounded-pill border-control px-4 font-label text-sm font-bold",
                          isActive
                            ? "border-border bg-surface text-accent shadow-raised"
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
        </div>
      </header>

      <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-8">
        {children}
      </main>
    </div>
  );
}
