import { fileURLToPath } from "node:url";

import { PlantFormComponent } from "./plant-form.co";
import { PlantsPage } from "./plants.po";
import { test, expect } from "./fixtures";

/**
 * FE-012 design-review evidence for BUG-008 (photo gallery crop + full view):
 * upload a deliberately WIDE photo, capture the cropped-square thumbnail grid,
 * then open the full uncropped image. Committed to the bug evidence folder
 * (distinct from ephemeral failure captures, TEST-011). Shot at both the S25+
 * and desktop breakpoints (mobile project runs everything; `@desktop` adds the
 * desktop project).
 */
const OUT = "../bugs/BUG-008-photo-gallery-screenshots";
const FIXTURE = fileURLToPath(new URL("./fixtures/sample-photo.png", import.meta.url));

test.describe("photo gallery thumbnails + full view @desktop", () => {
  test("grid thumbnail then full uncropped image", async ({
    page,
  }, testInfo) => {
    // Per-project name: both projects share one backend in a run (workers:1),
    // so a fixed name would collide and break strict-mode locators.
    const name = `Gallery demo ${testInfo.project.name}`;
    const plants = new PlantsPage(page);
    await plants.goto("/plants");

    // Create a plant to own the photo.
    await plants.addPlantButton.click();
    const form = new PlantFormComponent(page);
    await form.dialog.waitFor();
    await form.nameField.fill(name);
    await form.submitButton.click();
    await form.dialog.waitFor({ state: "hidden" });

    // Open its photo gallery and upload the wide fixture image.
    await page.getByRole("button", { name: `View photos of ${name}` }).click();
    const dialog = page.getByRole("dialog");
    await dialog.waitFor();
    await dialog
      .getByLabel(/add a photo/i)
      .setInputFiles(FIXTURE);
    await dialog.getByRole("button", { name: `Upload a photo for ${name}` }).click();

    // The thumbnail (a "view full size" button) appears once the upload lands.
    const viewButton = dialog.getByRole("button", {
      name: /view this photo .* at full size/i,
    });
    await expect(viewButton).toBeVisible();
    await page.screenshot({
      path: `${OUT}/${testInfo.project.name}-grid.png`,
    });

    // Open the full, uncropped image.
    await viewButton.click();
    await expect(
      dialog.getByRole("img", { name: /photo, full size/i }),
    ).toBeVisible();
    await page.screenshot({
      path: `${OUT}/${testInfo.project.name}-full-view.png`,
    });
  });
});
