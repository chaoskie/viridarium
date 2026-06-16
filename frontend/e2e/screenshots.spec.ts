import { PlantFormComponent } from "./plant-form.co";
import { PlantsPage } from "./plants.po";
import { test } from "./fixtures";

/**
 * Curated design-review screenshots (FE-012), committed to the change folder as
 * evidence - distinct from the ephemeral failure captures (TEST-011). The
 * `@desktop` tag makes these the only specs the desktop project runs; the mobile
 * project (untagged, runs everything) also captures them, so each surface is shot
 * at both the S25+ and desktop breakpoints.
 */
const OUT = "../bugs/mobile-soak-screenshots";

test.describe("design-review screenshots @desktop", () => {
  test("Today header sits within the viewport", async ({ page }, testInfo) => {
    await page.goto("/");
    await page.screenshot({
      path: `${OUT}/${testInfo.project.name}-today-header.png`,
    });
  });

  test("Add-plant modal fits and scrolls", async ({ page }, testInfo) => {
    const plants = new PlantsPage(page);
    await plants.goto("/plants");
    await plants.addPlantButton.click();
    const form = new PlantFormComponent(page);
    await form.dialog.waitFor();
    await page.screenshot({
      path: `${OUT}/${testInfo.project.name}-add-plant-modal.png`,
    });
  });

  test("Long values wrap on the plants list", async ({ page }, testInfo) => {
    const plants = new PlantsPage(page);
    await plants.goto("/plants");
    await plants.addPlantButton.click();
    const form = new PlantFormComponent(page);
    await form.nameField.fill(`Wisteria${"x".repeat(60)}`);
    await form.submitButton.click();
    await form.dialog.waitFor({ state: "hidden" });
    await page.screenshot({
      path: `${OUT}/${testInfo.project.name}-plants-long-value.png`,
      fullPage: true,
    });
  });
});
