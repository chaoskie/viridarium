import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { AppSettings } from "@/lib/api/settings";

import { SettingsPage } from "./SettingsPage";

const DEFAULT_SETTINGS: AppSettings = {
  seasonal_aware: true,
  winter_window: { start_month: 11, start_day: 1, end_month: 3, end_day: 1 },
};

const NON_DEFAULT_SETTINGS: AppSettings = {
  seasonal_aware: false,
  winter_window: { start_month: 5, start_day: 1, end_month: 9, end_day: 1 },
};

function okJson(status: number, body: unknown): Response {
  return {
    ok: true,
    status,
    json: () => Promise.resolve(body),
  } as Response;
}

function fail(status: number): Response {
  return {
    ok: false,
    status,
    json: () => Promise.resolve({ detail: "boom" }),
  } as Response;
}

/** Resolve the toggle, asserting it is a checkbox. */
function toggle(): HTMLInputElement {
  return screen.getByLabelText<HTMLInputElement>(/seasonal/i);
}

function startMonth(): HTMLInputElement {
  return screen.getByLabelText<HTMLInputElement>(/start month/i);
}
function startDay(): HTMLInputElement {
  return screen.getByLabelText<HTMLInputElement>(/start day/i);
}
function endMonth(): HTMLInputElement {
  return screen.getByLabelText<HTMLInputElement>(/end month/i);
}
function endDay(): HTMLInputElement {
  return screen.getByLabelText<HTMLInputElement>(/end day/i);
}

function save(): void {
  fireEvent.click(screen.getByRole("button", { name: /save/i }));
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("SettingsPage", () => {
  it("loads and displays the current values on mount (F-5)", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(okJson(200, NON_DEFAULT_SETTINGS));
    vi.stubGlobal("fetch", fetchMock);

    render(<SettingsPage />);

    await waitFor(() => {
      expect(toggle()).not.toBeChecked();
    });
    expect(startMonth().value).toBe("5");
    expect(startDay().value).toBe("1");
    expect(endMonth().value).toBe("9");
    expect(endDay().value).toBe("1");

    // A single GET fired on mount.
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [path, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(path).toBe("/api/v1/settings");
    expect(init.method ?? "GET").toBe("GET");
  });

  it("edits and saves: PUT called with the assembled body (F-6)", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(okJson(200, DEFAULT_SETTINGS))
      .mockResolvedValueOnce(
        okJson(200, {
          seasonal_aware: false,
          winter_window: {
            start_month: 12,
            start_day: 15,
            end_month: 3,
            end_day: 1,
          },
        }),
      );
    vi.stubGlobal("fetch", fetchMock);

    render(<SettingsPage />);

    await waitFor(() => {
      expect(toggle()).toBeChecked();
    });

    fireEvent.click(toggle());
    fireEvent.change(startMonth(), { target: { value: "12" } });
    fireEvent.change(startDay(), { target: { value: "15" } });
    save();

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledTimes(2);
    });

    const [path, init] = fetchMock.mock.calls[1] as [string, RequestInit];
    expect(path).toBe("/api/v1/settings");
    expect(init.method).toBe("PUT");
    expect(JSON.parse(init.body as string)).toEqual({
      seasonal_aware: false,
      winter_window: {
        start_month: 12,
        start_day: 15,
        end_month: 3,
        end_day: 1,
      },
    });

    // Inline success feedback shown.
    await waitFor(() => {
      expect(screen.getByRole("status")).toBeInTheDocument();
    });
  });

  it("'Return to default' resets ONLY the window inputs, not the toggle (F-7)", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(okJson(200, NON_DEFAULT_SETTINGS))
      .mockResolvedValueOnce(
        okJson(200, {
          seasonal_aware: false,
          winter_window: {
            start_month: 11,
            start_day: 1,
            end_month: 3,
            end_day: 1,
          },
        }),
      );
    vi.stubGlobal("fetch", fetchMock);

    render(<SettingsPage />);

    await waitFor(() => {
      expect(toggle()).not.toBeChecked();
    });

    fireEvent.click(screen.getByRole("button", { name: /return to default/i }));

    // Window reset to Nov 1 - Mar 1.
    expect(startMonth().value).toBe("11");
    expect(startDay().value).toBe("1");
    expect(endMonth().value).toBe("3");
    expect(endDay().value).toBe("1");
    // The toggle is UNTOUCHED (still off).
    expect(toggle()).not.toBeChecked();

    save();

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledTimes(2);
    });
    const [, init] = fetchMock.mock.calls[1] as [string, RequestInit];
    expect(JSON.parse(init.body as string)).toEqual({
      seasonal_aware: false,
      winter_window: {
        start_month: 11,
        start_day: 1,
        end_month: 3,
        end_day: 1,
      },
    });
  });

  it("surfaces a save error inline and keeps the form editable (F-8)", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(okJson(200, DEFAULT_SETTINGS))
      .mockResolvedValueOnce(fail(422));
    vi.stubGlobal("fetch", fetchMock);

    render(<SettingsPage />);

    await waitFor(() => {
      expect(toggle()).toBeChecked();
    });

    save();

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
    // The form stays editable: the Save button is still present.
    expect(screen.getByRole("button", { name: /save/i })).toBeInTheDocument();
  });

  it("surfaces a load error inline without throwing (F-9)", async () => {
    const fetchMock = vi.fn().mockResolvedValue(fail(500));
    vi.stubGlobal("fetch", fetchMock);

    render(<SettingsPage />);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
  });
});
