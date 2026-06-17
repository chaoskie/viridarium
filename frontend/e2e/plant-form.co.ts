import type { Locator, Page } from "@playwright/test";

/**
 * Add/Edit plant modal as a component object (FE-013 `.co.ts`). All locators are
 * scoped to the dialog so they don't collide with the same-named filter controls
 * on the Plants page. `acquiredOn` uses a substring match so it survives the
 * label becoming "Acquired on (optional)".
 */
export class PlantFormComponent {
  readonly dialog: Locator;
  readonly nameField: Locator;
  readonly speciesField: Locator;
  readonly acquiredOnField: Locator;
  readonly outerPotMaterial: Locator;
  readonly outerPotSize: Locator;
  readonly submitButton: Locator;
  /** Matches both the create ("Add plant") and edit ("Save changes") submit. */
  readonly saveButton: Locator;

  constructor(page: Page) {
    this.dialog = page.getByRole("dialog");
    this.nameField = this.dialog.getByLabel("Name");
    this.speciesField = this.dialog.getByLabel("Species");
    this.acquiredOnField = this.dialog.getByLabel("Acquired on");
    this.outerPotMaterial = this.dialog.getByLabel("Outer pot material");
    // Substring match - the label is "Outer pot size (cm)".
    this.outerPotSize = this.dialog.getByLabel("Outer pot size");
    this.submitButton = this.dialog.getByRole("button", { name: "Add plant" });
    this.saveButton = this.dialog.getByRole("button", {
      name: /add plant|save changes/i,
    });
  }
}
