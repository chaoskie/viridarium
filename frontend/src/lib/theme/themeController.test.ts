import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  DEFAULT_THEME,
  THEME_STORAGE_KEY,
  applyTheme,
  getInitialTheme,
  isTheme,
  nextTheme,
  persistTheme,
  readStoredTheme,
} from "./themeController";

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

describe("themeController", () => {
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

  describe("default", () => {
    it("uses the roman default", () => {
      expect(DEFAULT_THEME).toBe("roman");
    });

    it("readStoredTheme returns null when nothing valid is stored", () => {
      expect(readStoredTheme()).toBeNull();
      window.localStorage.setItem(THEME_STORAGE_KEY, "neon-disco");
      expect(readStoredTheme()).toBeNull();
    });
  });

  describe("getInitialTheme - first-load precedence (D-008)", () => {
    it("falls back to roman when nothing stored and OS prefers light", () => {
      stubPrefersColorScheme(false);
      expect(getInitialTheme()).toBe("roman");
    });

    it("falls back to dark when nothing stored and OS prefers dark", () => {
      stubPrefersColorScheme(true);
      expect(getInitialTheme()).toBe("dark");
    });

    it("a stored choice always wins over the OS preference", () => {
      stubPrefersColorScheme(true);
      persistTheme("herbarium");
      expect(getInitialTheme()).toBe("herbarium");

      persistTheme("roman");
      expect(getInitialTheme()).toBe("roman");
    });
  });

  describe("persistence", () => {
    it("reads back a previously persisted theme across the full set", () => {
      for (const theme of [
        "roman",
        "dark",
        "herbarium",
        "terracotta",
        "viridian",
      ] as const) {
        persistTheme(theme);
        expect(window.localStorage.getItem(THEME_STORAGE_KEY)).toBe(theme);
        expect(readStoredTheme()).toBe(theme);
      }
    });
  });

  describe("applying", () => {
    it("sets data-theme on the document root", () => {
      applyTheme("dark");
      expect(document.documentElement.getAttribute("data-theme")).toBe("dark");
      applyTheme("roman");
      expect(document.documentElement.getAttribute("data-theme")).toBe("roman");
    });
  });

  describe("switching", () => {
    it("cycles roman -> dark -> herbarium -> terracotta -> viridian -> roman", () => {
      expect(nextTheme("roman")).toBe("dark");
      expect(nextTheme("dark")).toBe("herbarium");
      expect(nextTheme("herbarium")).toBe("terracotta");
      expect(nextTheme("terracotta")).toBe("viridian");
      expect(nextTheme("viridian")).toBe("roman");
    });
  });

  describe("isTheme", () => {
    it("guards valid and invalid values", () => {
      expect(isTheme("roman")).toBe(true);
      expect(isTheme("dark")).toBe(true);
      expect(isTheme("herbarium")).toBe(true);
      expect(isTheme("terracotta")).toBe(true);
      expect(isTheme("nope")).toBe(false);
      expect(isTheme(null)).toBe(false);
    });
  });
});
