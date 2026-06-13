import { useCallback, useEffect, useId, useState } from "react";
import type { ReactNode } from "react";

import { Button } from "@/components/ui/Button";
import { ApiError } from "@/lib/api/client";
import {
  getSettings,
  updateSettings,
  type AppSettings,
} from "@/lib/api/settings";

// The spec default winter window: Nov 1 - Mar 1 (proposal §FE / ratified default).
const DEFAULT_WINDOW = {
  start_month: 11,
  start_day: 1,
  end_month: 3,
  end_day: 1,
} as const;

// Reuse the established control recipe (LogCareModal / CareScheduleModal) so the
// inputs match the theme tokens; NOT a new ui/ primitive (FE-010/FE-011).
const CONTROL_CLASSES =
  "min-h-tap-min w-full rounded-control border-control border-border bg-surface px-3 py-2 font-body text-base text-ink placeholder:text-ink-muted focus-visible:outline focus-visible:outline-2 focus-visible:outline-ring";

const LABEL_CLASSES =
  "font-label text-xs font-semibold uppercase tracking-widest text-ink-muted";

/** Turn any thrown value (incl. `ApiError`) into a human-readable message. */
function toMessage(err: unknown): string {
  if (err instanceof ApiError) {
    return `The server rejected the request (error ${String(err.status)}). Please check the values and try again.`;
  }
  return "Something went wrong. Please try again.";
}

/** A single month or day number input with its own label (FE-011). */
function NumberField({
  label,
  value,
  min,
  max,
  onChange,
}: {
  readonly label: string;
  readonly value: number;
  readonly min: number;
  readonly max: number;
  readonly onChange: (value: number) => void;
}): ReactNode {
  const id = useId();
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={id} className={LABEL_CLASSES}>
        {label}
      </label>
      <input
        id={id}
        type="number"
        min={min}
        max={max}
        className={CONTROL_CLASSES}
        value={String(value)}
        onChange={(event) => {
          onChange(Number(event.target.value));
        }}
      />
    </div>
  );
}

/**
 * App settings page (US-3.5, AC6): loads the current settings on mount, offers a
 * seasonal-aware on/off toggle plus the winter window as month + day inputs
 * (start, end), a "Return to default" button that resets ONLY the window to
 * Nov 1 - Mar 1 (the toggle is untouched, proposal §FE), and a Save that PUTs the
 * assembled state with inline success/error feedback. Reuses the shared `Button`
 * primitive and the established control classes (FE-010); no new heavy dep.
 */
export function SettingsPage(): ReactNode {
  const [seasonalAware, setSeasonalAware] = useState<boolean>(true);
  const [startMonth, setStartMonth] = useState<number>(
    DEFAULT_WINDOW.start_month,
  );
  const [startDay, setStartDay] = useState<number>(DEFAULT_WINDOW.start_day);
  const [endMonth, setEndMonth] = useState<number>(DEFAULT_WINDOW.end_month);
  const [endDay, setEndDay] = useState<number>(DEFAULT_WINDOW.end_day);

  const [loading, setLoading] = useState<boolean>(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saved, setSaved] = useState<boolean>(false);
  const [saving, setSaving] = useState<boolean>(false);

  const toggleId = useId();

  function applyWindow(window: AppSettings["winter_window"]): void {
    setStartMonth(window.start_month);
    setStartDay(window.start_day);
    setEndMonth(window.end_month);
    setEndDay(window.end_day);
  }

  const load = useCallback(async (): Promise<void> => {
    setLoading(true);
    setLoadError(null);
    setSaved(false);
    try {
      const settings = await getSettings();
      setSeasonalAware(settings.seasonal_aware);
      applyWindow(settings.winter_window);
    } catch (err: unknown) {
      setLoadError(toMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleSave(): Promise<void> {
    setSaveError(null);
    setSaved(false);
    setSaving(true);
    const body: AppSettings = {
      seasonal_aware: seasonalAware,
      winter_window: {
        start_month: startMonth,
        start_day: startDay,
        end_month: endMonth,
        end_day: endDay,
      },
    };
    try {
      const stored = await updateSettings(body);
      setSeasonalAware(stored.seasonal_aware);
      applyWindow(stored.winter_window);
      setSaved(true);
    } catch (err: unknown) {
      setSaveError(toMessage(err));
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="flex flex-col gap-6">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="font-display text-4xl font-extrabold text-ink">
          Settings
        </h1>
      </header>

      {loading ? (
        <p
          className="rounded-card border-card border-border bg-surface-raised p-5 font-label text-sm uppercase tracking-wide text-ink-muted shadow-card"
          aria-live="polite"
        >
          Loading settings...
        </p>
      ) : null}

      {!loading && loadError !== null ? (
        <p
          className="rounded-card border-card border-danger bg-surface-raised p-5 font-body text-base text-danger shadow-card"
          role="alert"
        >
          {loadError}
        </p>
      ) : null}

      {!loading && loadError === null ? (
        <form
          className="flex flex-col gap-6"
          noValidate
          onSubmit={(event) => {
            event.preventDefault();
            void handleSave();
          }}
        >
          <div className="flex flex-col gap-2 rounded-card border-card border-border bg-surface-raised p-5 shadow-card">
            <label
              htmlFor={toggleId}
              className="flex items-center gap-3 font-body text-base text-ink"
            >
              <input
                id={toggleId}
                type="checkbox"
                className="size-5"
                checked={seasonalAware}
                onChange={(event) => {
                  setSeasonalAware(event.target.checked);
                }}
              />
              Seasonal-aware care
            </label>
            <p className="font-body text-sm text-ink-muted">
              When on, schedules switch to their winter cadence (or pause)
              during the window below. When off, every schedule uses its plain
              interval year-round.
            </p>
          </div>

          <fieldset className="flex flex-col gap-4 rounded-card border-card border-border bg-surface-raised p-5 shadow-card">
            <legend className="font-display text-xl font-semibold text-ink">
              Winter window
            </legend>
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
              <NumberField
                label="Start month"
                value={startMonth}
                min={1}
                max={12}
                onChange={setStartMonth}
              />
              <NumberField
                label="Start day"
                value={startDay}
                min={1}
                max={31}
                onChange={setStartDay}
              />
              <NumberField
                label="End month"
                value={endMonth}
                min={1}
                max={12}
                onChange={setEndMonth}
              />
              <NumberField
                label="End day"
                value={endDay}
                min={1}
                max={31}
                onChange={setEndDay}
              />
            </div>
            <div>
              <Button
                variant="ghost"
                onClick={() => {
                  // Resets ONLY the window; the toggle is deliberately untouched.
                  applyWindow(DEFAULT_WINDOW);
                }}
              >
                Return to default
              </Button>
            </div>
          </fieldset>

          {saveError !== null ? (
            <p className="font-body text-sm text-danger" role="alert">
              {saveError}
            </p>
          ) : null}

          {saved ? (
            <p className="font-body text-sm text-accent-strong" role="status">
              Settings saved.
            </p>
          ) : null}

          <div className="flex justify-end">
            <Button type="submit" variant="primary" disabled={saving}>
              {saving ? "Saving..." : "Save"}
            </Button>
          </div>
        </form>
      ) : null}
    </section>
  );
}
