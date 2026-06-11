import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

/**
 * Contract tests for the entry HTML against the production CSP (SEC-011,
 * VIRIDARIUM-37): the backend serves the built SPA with
 * `script-src 'self'; style-src 'self'`, so index.html must not depend on any
 * external origin or inline script. Violations are invisible in Vite dev (no
 * CSP) and only break the production path.
 */

// vitest runs with the frontend package root as cwd.
const read = (rel: string): string =>
  readFileSync(resolve(process.cwd(), rel), "utf8");

const indexHtml = read("index.html");

describe("entry HTML complies with the strict CSP", () => {
  it("references no external origin", () => {
    expect(indexHtml).not.toMatch(/fonts\.googleapis\.com|fonts\.gstatic\.com/);
    expect(indexHtml).not.toMatch(/(?:href|src)\s*=\s*"https?:\/\//);
  });

  it("contains no inline script (script-src 'self')", () => {
    const scriptTags = indexHtml.match(/<script\b[^>]*>/g) ?? [];
    expect(scriptTags.length).toBeGreaterThan(0);
    for (const tag of scriptTags) {
      expect(tag).toMatch(/\bsrc\s*=/);
    }
  });

  it("loads the pre-paint theme script, mirrored with the controller", () => {
    expect(indexHtml).toContain('src="/theme-init.js"');
    const themeInit = read("public/theme-init.js");
    const controller = read("src/lib/theme/themeController.ts");
    // KEY and the theme list MUST stay in sync with themeController.ts.
    expect(themeInit).toContain('"viridarium.theme"');
    expect(controller).toContain('"viridarium.theme"');
    for (const theme of [
      "roman",
      "dark",
      "herbarium",
      "terracotta",
      "viridian",
    ]) {
      expect(themeInit).toContain(`"${theme}"`);
    }
  });
});
