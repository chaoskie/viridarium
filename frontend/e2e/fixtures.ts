import { test as base, expect } from "@playwright/test";
import type { Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

/**
 * Shared acceptance fixtures (TEST-010, FE-015).
 *
 * `failOnConsoleError` is an auto-fixture that fails any test whose page emits a
 * page error or an error-level console message. Warnings are ignored. Allowlist a
 * known-benign pattern by adding to `ALLOWED_CONSOLE_ERROR` with a justification.
 */
const ALLOWED_CONSOLE_ERROR: readonly RegExp[] = [
  // (none yet) - add `/pattern/` here with an inline reason if a benign error appears.
];

function isAllowed(text: string): boolean {
  return ALLOWED_CONSOLE_ERROR.some((pattern) => pattern.test(text));
}

export const test = base.extend<{ failOnConsoleError: void }>({
  failOnConsoleError: [
    async ({ page }, use) => {
      const errors: string[] = [];
      page.on("console", (message) => {
        if (message.type() === "error" && !isAllowed(message.text())) {
          errors.push(`console.error: ${message.text()}`);
        }
      });
      page.on("pageerror", (error) => {
        if (!isAllowed(error.message)) {
          errors.push(`pageerror: ${error.message}`);
        }
      });
      await use();
      expect(errors, `page emitted errors:\n${errors.join("\n")}`).toEqual([]);
    },
    { auto: true },
  ],
});

export { expect };

/**
 * Assert no serious/critical accessibility violations on the current page
 * (FE-015 a11y space). Minor/moderate impacts are reported but not failed here.
 */
export async function expectNoSeriousA11yViolations(page: Page): Promise<void> {
  const results = await new AxeBuilder({ page }).analyze();
  const serious = results.violations.filter(
    (violation) =>
      violation.impact === "serious" || violation.impact === "critical",
  );
  const summary = serious
    .map((violation) => `${violation.id}: ${violation.help}`)
    .join("\n");
  expect(serious, `serious a11y violations:\n${summary}`).toEqual([]);
}

/** True when the document is wider than its own viewport (horizontal overflow, FE-011). */
export async function hasHorizontalOverflow(page: Page): Promise<boolean> {
  return page.evaluate(() => {
    const doc = document.documentElement;
    return doc.scrollWidth > doc.clientWidth;
  });
}
