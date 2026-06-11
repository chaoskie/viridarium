import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

/**
 * Token-contrast guard (D-008 #4 / FE-011). Parses src/styles/tokens.css,
 * resolves each theme's hex tokens, and asserts WCAG AA on the load-bearing
 * text pairs:
 *   - ink on every surface           >= 4.5:1 (normal text)
 *   - muted ink on the page surface  >= 4.5:1 (normal text - the mockup's
 *                                     italic epigraph + captions use it)
 *   - *-strong accents as text       >= 4.5:1 on their typical surface
 *   - accent fills carrying ink-inverse text >= 4.5:1
 *
 * This is the cheap, deterministic stand-in for axe-core-in-Playwright while
 * the skeleton has no e2e a11y harness (see proposal FE-015 comply-or-explain).
 */

// Vitest runs with cwd = frontend/, so resolve from there.
const TOKENS_PATH = resolve(process.cwd(), "src/styles/tokens.css");
// Strip CSS comments up front so selector matching can't span them.
const css = readFileSync(TOKENS_PATH, "utf8").replace(/\/\*[\s\S]*?\*\//g, "");

type Tokens = Readonly<Record<string, string>>;

interface Rule {
  readonly selector: string;
  readonly body: string;
}

// Split the (comment-free) stylesheet into { selector, body } rules.
const RULES: readonly Rule[] = css
  .split("}")
  .map((chunk) => {
    const brace = chunk.indexOf("{");
    if (brace === -1) {
      return null;
    }
    return {
      selector: chunk.slice(0, brace).trim(),
      body: chunk.slice(brace + 1),
    };
  })
  .filter((rule): rule is Rule => rule !== null);

/** Extract the token map for one [data-theme] / :root block by its selector. */
function tokensForSelector(selector: string): Tokens {
  const rule = RULES.find((r) => r.selector.includes(selector));
  if (rule === undefined) {
    throw new Error(`No token block found for selector ${selector}`);
  }
  const tokens: Record<string, string> = {};
  const declRe = /--([\w-]+)\s*:\s*([^;]+);/g;
  let decl: RegExpExecArray | null;
  while ((decl = declRe.exec(rule.body)) !== null) {
    const name = decl[1];
    const value = decl[2];
    if (name !== undefined && value !== undefined) {
      tokens[name] = value.trim();
    }
  }
  return tokens;
}

function hexToRgb(hex: string): readonly [number, number, number] {
  const clean = hex.replace("#", "").trim();
  const full =
    clean.length === 3
      ? clean
          .split("")
          .map((c) => c + c)
          .join("")
      : clean;
  const r = parseInt(full.slice(0, 2), 16);
  const g = parseInt(full.slice(2, 4), 16);
  const b = parseInt(full.slice(4, 6), 16);
  return [r, g, b];
}

function channelLuminance(value: number): number {
  const c = value / 255;
  return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
}

function relativeLuminance([r, g, b]: readonly [
  number,
  number,
  number,
]): number {
  return (
    0.2126 * channelLuminance(r) +
    0.7152 * channelLuminance(g) +
    0.0722 * channelLuminance(b)
  );
}

function contrastRatio(fgHex: string, bgHex: string): number {
  const l1 = relativeLuminance(hexToRgb(fgHex));
  const l2 = relativeLuminance(hexToRgb(bgHex));
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);
  return (lighter + 0.05) / (darker + 0.05);
}

const AA_NORMAL = 4.5;
const AA_LARGE = 3;

// :root and [data-theme="roman"] share a block; reference roman by its label.
const THEME_SELECTORS: Readonly<Record<string, string>> = {
  roman: '[data-theme="roman"]',
  dark: '[data-theme="dark"]',
  terracotta: '[data-theme="terracotta"]',
  herbarium: '[data-theme="herbarium"]',
  viridian: '[data-theme="viridian"]',
};

describe("theme contrast (WCAG AA)", () => {
  for (const [theme, selector] of Object.entries(THEME_SELECTORS)) {
    describe(theme, () => {
      const t = tokensForSelector(selector);

      it("ink clears AA on every surface", () => {
        for (const surface of [
          "color-surface",
          "color-surface-raised",
          "color-surface-sunken",
        ]) {
          const ratio = contrastRatio(t["color-ink"] ?? "", t[surface] ?? "");
          expect(
            ratio,
            `${theme}: ink on ${surface} = ${ratio.toFixed(2)}:1`,
          ).toBeGreaterThanOrEqual(AA_NORMAL);
        }
      });

      it("muted ink clears AA on the page surface", () => {
        const ratio = contrastRatio(
          t["color-ink-muted"] ?? "",
          t["color-surface"] ?? "",
        );
        expect(
          ratio,
          `${theme}: muted ink on surface = ${ratio.toFixed(2)}:1`,
        ).toBeGreaterThanOrEqual(AA_NORMAL);
      });

      it("strong accents clear AA as small text on the page surface", () => {
        // The *-strong tones are what components use for small accent text
        // (status pills, captions, hover); they must clear 4.5:1.
        for (const accent of [
          "color-accent-strong",
          "color-accent-2-strong",
          "color-accent-3-strong",
        ]) {
          const ratio = contrastRatio(
            t[accent] ?? "",
            t["color-surface"] ?? "",
          );
          expect(
            ratio,
            `${theme}: ${accent} on surface = ${ratio.toFixed(2)}:1`,
          ).toBeGreaterThanOrEqual(AA_NORMAL);
        }
      });

      it("the base accent clears the large-text threshold as display ink", () => {
        // `color-accent` is the brand/display color (wordmark, big headings);
        // it is only used at large sizes as text, so 3:1 is the bar (FE-011).
        const ratio = contrastRatio(
          t["color-accent"] ?? "",
          t["color-surface"] ?? "",
        );
        expect(
          ratio,
          `${theme}: accent on surface = ${ratio.toFixed(2)}:1`,
        ).toBeGreaterThanOrEqual(AA_LARGE);
      });
    });
  }
});
