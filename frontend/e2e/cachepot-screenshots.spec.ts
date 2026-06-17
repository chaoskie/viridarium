import { PlantFormComponent } from "./plant-form.co";
import { PlantsPage } from "./plants.po";
import { test } from "./fixtures";

/**
 * FE-012 design-review evidence for the plant-cachepot change: the add-plant form
 * with the new "Outer / decorative pot" section filled, captured at both the S25+
 * and desktop breakpoints into the change's screenshots/ folder.
 */
const OUT = "../specs/changes/plant-cachepot/screenshots";

test.describe("plant-cachepot screenshots @desktop", () => {
  test("add-plant outer (decorative) pot section", async ({
    page,
  }, testInfo) => {
    const plants = new PlantsPage(page);
    await plants.goto("/plants");
    await plants.addPlantButton.click();

    const form = new PlantFormComponent(page);
    await form.dialog.waitFor();
    await form.nameField.fill("Cachepot demo");
    await form.outerPotMaterial.selectOption("ceramic");
    await form.outerPotSize.fill("18");
    await form.outerPotMaterial.scrollIntoViewIfNeeded();

    await page.screenshot({
      path: `${OUT}/${testInfo.project.name}-add-plant-outer-pot.png`,
    });
  });
});
