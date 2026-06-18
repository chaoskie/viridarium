import { Link } from "react-router-dom";
import type { ReactNode } from "react";

import { SUPPORT_URL } from "@/lib/links";

/**
 * Slim, app-wide footer (VIRIDARIUM-76). Project name + license, a link to the
 * About page, and the maintainer's Support link. The Support link is a plain
 * user-initiated external navigation (new tab, `rel="noopener noreferrer"`); the
 * app makes no automatic outbound calls (PRIN-II).
 */
export function AppFooter(): ReactNode {
  return (
    <footer className="mx-auto flex w-full max-w-5xl flex-wrap items-center justify-center gap-x-3 gap-y-1 px-4 pb-28 pt-6 text-center font-label text-xs uppercase tracking-widest text-ink-muted sm:pb-6">
      <span>Viridarium</span>
      <span aria-hidden="true">·</span>
      <span>AGPL-3.0</span>
      <span aria-hidden="true">·</span>
      <Link
        to="/about"
        className="rounded-control hover:text-ink focus-visible:outline focus-visible:outline-2 focus-visible:outline-ring"
      >
        About
      </Link>
      <span aria-hidden="true">·</span>
      <a
        href={SUPPORT_URL}
        target="_blank"
        rel="noopener noreferrer"
        aria-label="Support (opens a third-party site in a new tab)"
        className="rounded-control hover:text-ink focus-visible:outline focus-visible:outline-2 focus-visible:outline-ring"
      >
        Support
      </a>
    </footer>
  );
}
