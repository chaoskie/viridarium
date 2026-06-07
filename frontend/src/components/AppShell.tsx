import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";

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
    <div className="flex min-h-screen flex-col bg-surface text-ink">
      <header className="border-b border-border bg-surface-raised">
        <div className="mx-auto flex max-w-5xl flex-col gap-2 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
          <span className="font-display text-lg font-semibold text-accent-strong">
            plant-care
          </span>
          <nav aria-label="Primary">
            <ul className="flex flex-wrap gap-1">
              {NAV_ITEMS.map((item) => (
                <li key={item.to}>
                  <NavLink
                    to={item.to}
                    end={item.to === "/"}
                    className={({ isActive }) =>
                      [
                        "flex min-h-tap-min items-center rounded-control px-3 text-sm font-medium",
                        isActive
                          ? "bg-accent-soft text-accent-strong"
                          : "text-ink-muted hover:text-ink",
                      ].join(" ")
                    }
                  >
                    {item.label}
                  </NavLink>
                </li>
              ))}
            </ul>
          </nav>
        </div>
      </header>

      <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-6">
        {children}
      </main>
    </div>
  );
}
