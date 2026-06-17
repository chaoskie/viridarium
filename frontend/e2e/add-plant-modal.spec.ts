import { PlantFormComponent } from "./plant-form.co";
import { PlantsPage } from "./plants.po";
import { expect, hasHorizontalOverflow, test } from "./fixtures";

/**
 * Galaxy S25+ add-plant regressions from the soak (BUG-003 modal scroll, BUG-005
 * long-value display overflow). Untagged => `galaxy-s25-plus` project only.
 */
test.describe("add-plant on mobile", () => {
  test("the Name field is reachable in the modal (BUG-003)", async ({
    page,
  }) => {
    const plants = new PlantsPage(page);
    await plants.goto("/plants");
    await plants.addPlantButton.click();

    const form = new PlantFormComponent(page);
    await expect(form.dialog).toBeVisible();

    // The first field must be reachable (scrolled to if the form overflows) and
    // usable - the bug was that Name/Species sat above the viewport with no scroll.
    await form.nameField.scrollIntoViewIfNeeded();
    await expect(form.nameField).toBeInViewport();
    await form.nameField.fill("Repro Monstera");
    await expect(form.nameField).toHaveValue("Repro Monstera");
  });

  test("a long unbroken value does not overflow the layout (BUG-005)", async ({
    page,
  }) => {
    const plants = new PlantsPage(page);
    await plants.goto("/plants");
    await plants.addPlantButton.click();

    const form = new PlantFormComponent(page);
    // A spaceless string within the 120-char name cap (input is already guarded);
    // the defect is purely render-side wrapping.
    const longName = `Aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa${Date.now()}`;
    await form.nameField.fill(longName);
    await form.submitButton.click();

    await expect(form.dialog).toBeHidden();
    await expect(plants.card(longName)).toBeVisible();
    expect(await hasHorizontalOverflow(page)).toBe(false);
  });
});
