import { AboutPage, AppShellPage } from "./app-shell.po";
import { PlantsPage } from "./plants.po";
import { expect, expectNoSeriousA11yViolations, test } from "./fixtures";

/**
 * FE-012 design-review evidence for VIRIDARIUM-76: the always-present footer and
 * the /about page (reached via the footer's About link). Captured at both the
 * S25+ and desktop breakpoints into the change's screenshots/ folder, and the
 * /about surface gets an axe-core a11y pass (FE-015).
 */
const OUT = "../specs/changes/about-support/screenshots";

test.describe("about + support @desktop", () => {
  test("footer navigates to the About page", async ({ page }, testInfo) => {
    // Land somewhere, then use the app-wide footer to reach About.
    const plants = new PlantsPage(page);
    await plants.goto("/plants");

    const shell = new AppShellPage(page);
    await shell.footer.scrollIntoViewIfNeeded();
    await shell.footerAboutLink.click();

    const about = new AboutPage(page);
    await expect(about.heading).toBeVisible();
    // Live version rendered from /health (real backend).
    await expect(about.version).toBeVisible();

    // FE-015: the About surface has no serious accessibility violations.
    await expectNoSeriousA11yViolations(page);

    await page.screenshot({
      path: `${OUT}/${testInfo.project.name}-about.png`,
      fullPage: true,
    });
  });
});
