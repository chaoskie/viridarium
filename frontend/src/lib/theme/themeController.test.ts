import { afterEach, beforeEach, describe, expect, it } from "vitest";

import {
  DEFAULT_THEME,
  THEME_STORAGE_KEY,
  applyTheme,
  isTheme,
  nextTheme,
  persistTheme,
  readStoredTheme,
} from "./themeController";

describe("themeController", () => {
  beforeEach(() => {
    window.localStorage.clear();
    document.documentElement.removeAttribute("data-theme");
  });

  afterEach(() => {
    window.localStorage.clear();
    document.documentElement.removeAttribute("data-theme");
  });

  describe("default", () => {
    it("falls back to the terracotta default when nothing is stored", () => {
      expect(DEFAULT_THEME).toBe("terracotta");
      expect(readStoredTheme()).toBe("terracotta");
    });

    it("ignores an invalid stored value and uses the default", () => {
      window.localStorage.setItem(THEME_STORAGE_KEY, "neon-disco");
      expect(readStoredTheme()).toBe("terracotta");
    });
  });

  describe("persistence", () => {
    it("reads back a previously persisted theme", () => {
      persistTheme("herbarium");
      expect(window.localStorage.getItem(THEME_STORAGE_KEY)).toBe("herbarium");
      expect(readStoredTheme()).toBe("herbarium");
    });
  });

  describe("applying", () => {
    it("sets data-theme on the document root", () => {
      applyTheme("herbarium");
      expect(document.documentElement.getAttribute("data-theme")).toBe(
        "herbarium",
      );
      applyTheme("terracotta");
      expect(document.documentElement.getAttribute("data-theme")).toBe(
        "terracotta",
      );
    });
  });

  describe("switching", () => {
    it("cycles terracotta -> herbarium -> terracotta", () => {
      expect(nextTheme("terracotta")).toBe("herbarium");
      expect(nextTheme("herbarium")).toBe("terracotta");
    });
  });

  describe("isTheme", () => {
    it("guards valid and invalid values", () => {
      expect(isTheme("terracotta")).toBe(true);
      expect(isTheme("herbarium")).toBe(true);
      expect(isTheme("nope")).toBe(false);
      expect(isTheme(null)).toBe(false);
    });
  });
});
