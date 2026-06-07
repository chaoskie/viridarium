import { useEffect, useState } from "react";
import type { ReactNode } from "react";

import { fetchHealth } from "@/lib/api/health";

type HealthState =
  | { readonly kind: "loading" }
  | { readonly kind: "ok"; readonly status: string }
  | { readonly kind: "error" };

export function HealthBadge(): ReactNode {
  const [state, setState] = useState<HealthState>({ kind: "loading" });

  useEffect(() => {
    let active = true;

    fetchHealth()
      .then((health) => {
        if (active) {
          setState({ kind: "ok", status: health.status });
        }
      })
      .catch(() => {
        if (active) {
          setState({ kind: "error" });
        }
      });

    return () => {
      active = false;
    };
  }, []);

  return (
    <div
      className="rounded-card border-card border-border bg-surface-raised p-5 shadow-card"
      aria-live="polite"
    >
      <h2 className="font-label text-xs font-bold uppercase tracking-wide text-ink-muted">
        Backend status
      </h2>
      <p className="mt-1 text-base">
        {state.kind === "loading" && (
          <span className="text-ink-muted">Checking...</span>
        )}
        {state.kind === "ok" && (
          <span className="font-medium text-success">
            Healthy ({state.status})
          </span>
        )}
        {state.kind === "error" && (
          <span className="font-medium text-danger">Unreachable</span>
        )}
      </p>
    </div>
  );
}
