import { fileURLToPath } from "node:url";

import { PlantFormComponent } from "./plant-form.co";
import { PlantsPage } from "./plants.po";
import { test, expect } from "./fixtures";

/**
 * FE-012 design-review evidence for BUG-009 (care timeline crop): upload a
 * deliberately PORTRAIT (taller-than-wide) photo, then capture the plant detail
 * timeline showing it uncropped (object-contain, letterboxed within the height
 * cap) rather than cut to a wide band. Shot at S25+ and desktop.
 */
const OUT = "../bugs/BUG-009-timeline-photo-screenshots";
const FIXTURE = fileURLToPath(
  new URL("./fixtures/sample-photo-portrait.png", import.meta.url),
);

test.describe("timeline renders a portrait photo uncropped @desktop", () => {
  test("portrait photo in the detail timeline", async ({ page }, testInfo) => {
    const name = `Timeline demo ${testInfo.project.name}`;
    const plants = new PlantsPage(page);
    await plants.goto("/plants");

    // Create a plant and upload a portrait photo to it.
    await plants.addPlantButton.click();
    const form = new PlantFormComponent(page);
    await form.dialog.waitFor();
    await form.nameField.fill(name);
    await form.submitButton.click();
    await form.dialog.waitFor({ state: "hidden" });

    await page.getByRole("button", { name: `View photos of ${name}` }).click();
    const dialog = page.getByRole("dialog");
    await dialog.waitFor();
    await dialog.getByLabel(/add a photo/i).setInputFiles(FIXTURE);
    await dialog
      .getByRole("button", { name: `Upload a photo for ${name}` })
      .click();
    await expect(
      dialog.getByRole("button", { name: /view this photo .* at full size/i }),
    ).toBeVisible();
    await page.keyboard.press("Escape");
    await dialog.waitFor({ state: "hidden" });

    // Open the plant's detail timeline; the uploaded photo shows as an entry.
    await page.getByRole("link", { name: `View ${name}'s history` }).click();
    const photoEntry = page.getByTestId("photo-entry").first();
    await expect(photoEntry).toBeVisible();
    await photoEntry.scrollIntoViewIfNeeded();

    await page.screenshot({
      path: `${OUT}/${testInfo.project.name}-timeline-portrait.png`,
    });
  });
});
