import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { THEME_STORAGE_KEY } from "./themeController";
import { useTheme } from "./useTheme";

function currentDomTheme(): string | null {
  return document.documentElement.getAttribute("data-theme");
}

/** Stub matchMedia so prefers-color-scheme is controllable under jsdom. */
function stubPrefersColorScheme(prefersDark: boolean): void {
  vi.stubGlobal(
    "matchMedia",
    vi.fn().mockImplementation((query: string) => ({
      matches: query.includes("dark") ? prefersDark : false,
      media: query,
      onchange: null,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      addListener: vi.fn(),
      removeListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  );
}

describe("useTheme", () => {
  beforeEach(() => {
    window.localStorage.clear();
    document.documentElement.removeAttribute("data-theme");
    stubPrefersColorScheme(false);
  });

  afterEach(() => {
    window.localStorage.clear();
    document.documentElement.removeAttribute("data-theme");
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("defaults to roman and applies it to the DOM on mount", () => {
    const { result } = renderHook(() => useTheme());
    expect(result.current.theme).toBe("roman");
    expect(currentDomTheme()).toBe("roman");
  });

  it("defaults to dark when the OS prefers a dark scheme (no stored value)", () => {
    stubPrefersColorScheme(true);
    const { result } = renderHook(() => useTheme());
    expect(result.current.theme).toBe("dark");
    expect(currentDomTheme()).toBe("dark");
  });

  it("a stored choice wins over the OS dark preference", () => {
    stubPrefersColorScheme(true);
    window.localStorage.setItem(THEME_STORAGE_KEY, "herbarium");
    const { result } = renderHook(() => useTheme());
    expect(result.current.theme).toBe("herbarium");
    expect(currentDomTheme()).toBe("herbarium");
  });

  it("initialises from a persisted theme", () => {
    window.localStorage.setItem(THEME_STORAGE_KEY, "dark");
    const { result } = renderHook(() => useTheme());
    expect(result.current.theme).toBe("dark");
    expect(currentDomTheme()).toBe("dark");
  });

  it("setTheme applies and persists across the new theme set", () => {
    const { result } = renderHook(() => useTheme());
    for (const theme of ["dark", "herbarium", "roman"] as const) {
      act(() => {
        result.current.setTheme(theme);
      });
      expect(result.current.theme).toBe(theme);
      expect(currentDomTheme()).toBe(theme);
      expect(window.localStorage.getItem(THEME_STORAGE_KEY)).toBe(theme);
    }
  });

  it("cycleTheme advances and wraps through the full set", () => {
    const { result } = renderHook(() => useTheme());
    const order = ["dark", "herbarium", "terracotta", "roman"] as const;
    for (const expected of order) {
      act(() => {
        result.current.cycleTheme();
      });
      expect(result.current.theme).toBe(expected);
    }
    expect(window.localStorage.getItem(THEME_STORAGE_KEY)).toBe("roman");
  });
});
