import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";

import { THEME_STORAGE_KEY } from "./themeController";
import { useTheme } from "./useTheme";

function currentDomTheme(): string | null {
  return document.documentElement.getAttribute("data-theme");
}

describe("useTheme", () => {
  beforeEach(() => {
    window.localStorage.clear();
    document.documentElement.removeAttribute("data-theme");
  });

  afterEach(() => {
    window.localStorage.clear();
    document.documentElement.removeAttribute("data-theme");
  });

  it("defaults to terracotta and applies it to the DOM on mount", () => {
    const { result } = renderHook(() => useTheme());
    expect(result.current.theme).toBe("terracotta");
    expect(currentDomTheme()).toBe("terracotta");
  });

  it("initialises from a persisted theme", () => {
    window.localStorage.setItem(THEME_STORAGE_KEY, "herbarium");
    const { result } = renderHook(() => useTheme());
    expect(result.current.theme).toBe("herbarium");
    expect(currentDomTheme()).toBe("herbarium");
  });

  it("setTheme applies and persists", () => {
    const { result } = renderHook(() => useTheme());
    act(() => {
      result.current.setTheme("herbarium");
    });
    expect(result.current.theme).toBe("herbarium");
    expect(currentDomTheme()).toBe("herbarium");
    expect(window.localStorage.getItem(THEME_STORAGE_KEY)).toBe("herbarium");
  });

  it("cycleTheme advances and wraps", () => {
    const { result } = renderHook(() => useTheme());
    act(() => {
      result.current.cycleTheme();
    });
    expect(result.current.theme).toBe("herbarium");
    act(() => {
      result.current.cycleTheme();
    });
    expect(result.current.theme).toBe("terracotta");
    expect(window.localStorage.getItem(THEME_STORAGE_KEY)).toBe("terracotta");
  });
});
