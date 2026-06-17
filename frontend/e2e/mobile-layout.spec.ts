import { AppShellPage } from "./app-shell.po";
import {
  expect,
  expectNoSeriousA11yViolations,
  hasHorizontalOverflow,
  test,
} from "./fixtures";

/**
 * Galaxy S25+ app-shell regressions from the soak (BUG-001, BUG-002). Untagged =>
 * runs on the `galaxy-s25-plus` project only (the desktop project greps `@desktop`).
 */
test.describe("mobile app shell", () => {
  test("opens at 1.0 scale with no horizontal overflow (BUG-001)", async ({
    page,
  }) => {
    await page.goto("/");

    // The document must not be wider than its viewport - the overflow that makes
    // Android fit-to-width and read as "zoomed" (FE-011: no horizontal scroll).
    expect(await hasHorizontalOverflow(page)).toBe(false);

    const scale = await page.evaluate(() => window.visualViewport?.scale ?? 1);
    expect(scale).toBe(1);
  });

  test("keeps the theme selector fully on-screen (BUG-002)", async ({
    page,
  }) => {
    await page.goto("/");
    const shell = new AppShellPage(page);

    await expect(shell.themeSelect).toBeVisible();
    const box = await shell.themeSelect.boundingBox();
    const viewportWidth = page.viewportSize()?.width ?? 0;

    expect(box, "theme select should have a layout box").not.toBeNull();
    if (box !== null) {
      expect(box.x).toBeGreaterThanOrEqual(0);
      expect(box.x + box.width).toBeLessThanOrEqual(viewportWidth);
    }
  });

  test("Today view has no serious accessibility violations (FE-015)", async ({
    page,
  }) => {
    await page.goto("/");
    await expectNoSeriousA11yViolations(page);
  });
});
