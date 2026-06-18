import { useEffect, useState } from "react";
import type { ReactNode } from "react";

import { fetchHealth } from "@/lib/api/health";
import { MAINTAINER_NOTE_URL, REPO_URL, SUPPORT_URL } from "@/lib/links";

const SECTION_CLASSES =
  "flex flex-col gap-2 rounded-card border-card border-border bg-surface-raised p-5 shadow-card";

const HEADING_CLASSES = "font-display text-xl font-semibold text-ink";

const LINK_CLASSES =
  "rounded-control font-semibold text-accent-strong underline-offset-2 hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-ring";

/** An external link: new tab, hardened rel, never an app-initiated call. */
function ExternalLink({
  href,
  children,
}: {
  readonly href: string;
  readonly children: ReactNode;
}): ReactNode {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className={LINK_CLASSES}
    >
      {children}
      <span className="sr-only"> (opens in a new tab)</span>
    </a>
  );
}

/**
 * About & support page (VIRIDARIUM-76). Static project info plus the maintainer's
 * support link and a verbatim excerpt of the README note. The only network call
 * is the existing same-origin `GET /health` for the live version; a failed fetch
 * degrades to "version unavailable" (no crash). External links are user-initiated
 * navigations only (PRIN-II / SEC-001).
 */
export function AboutPage(): ReactNode {
  const [version, setVersion] = useState<string | null>(null);
  const [versionFailed, setVersionFailed] = useState(false);

  useEffect(() => {
    let active = true;
    void fetchHealth()
      .then((health) => {
        if (active) {
          setVersion(health.version);
        }
      })
      .catch(() => {
        if (active) {
          setVersionFailed(true);
        }
      });
    return () => {
      active = false;
    };
  }, []);

  return (
    <section className="flex flex-col gap-6">
      <h1 className="font-display text-4xl font-extrabold text-ink">
        About Viridarium
      </h1>

      <div className={SECTION_CLASSES}>
        <p className="font-body text-base text-ink">
          Viridarium is an open-source, self-hosted plant-care app - your plant
          inventory, watering and feeding schedules, and an open API for
          home-automation, all running on hardware you control.
        </p>
      </div>

      <div className={SECTION_CLASSES}>
        <h2 className={HEADING_CLASSES}>From the maintainer</h2>
        <p className="font-body text-base text-ink">
          I built this because the apps already out there didn&apos;t quite meet
          my expectations, and I wanted to make something nice of my own. I own
          a lot of plants, and some of them are wonderfully picky about water
          and moisture. Even though it wasn&apos;t typed out by my own hands, I
          am very much the mind behind it: the functionality, the feel, the
          decisions.
        </p>
        <p className="font-body text-base text-ink">
          <ExternalLink href={MAINTAINER_NOTE_URL}>
            Read the full note in the README →
          </ExternalLink>
        </p>
      </div>

      <div className={SECTION_CLASSES}>
        <h2 className={HEADING_CLASSES}>Support</h2>
        <p className="font-body text-base text-ink">
          If Viridarium helps keep your plants alive, you can support its
          development:{" "}
          <ExternalLink href={SUPPORT_URL}>linktr.ee/chaoskie</ExternalLink>{" "}
          <span className="text-ink-muted">(opens a third-party site)</span>
        </p>
      </div>

      <div className={SECTION_CLASSES}>
        <h2 className={HEADING_CLASSES}>Source &amp; license</h2>
        <p className="font-body text-base text-ink">
          Open source under the GNU AGPL-3.0.{" "}
          <ExternalLink href={REPO_URL}>
            github.com/chaoskie/viridarium
          </ExternalLink>
        </p>
      </div>

      <div className={SECTION_CLASSES}>
        <h2 className={HEADING_CLASSES}>Privacy</h2>
        <p className="font-body text-base text-ink">
          Viridarium collects no analytics and makes no outbound connections
          without your explicit approval. Your data stays on your server.
        </p>
      </div>

      <div className={SECTION_CLASSES}>
        <h2 className={HEADING_CLASSES}>Thanks</h2>
        <p className="font-body text-base text-ink">
          Thanks for using Viridarium - I hope you enjoy it. — chaoskie
        </p>
      </div>

      <p className="font-label text-xs uppercase tracking-widest text-ink-muted">
        {versionFailed
          ? "Version unavailable"
          : version === null
            ? "Version ..."
            : `Version ${version}`}
      </p>
    </section>
  );
}
