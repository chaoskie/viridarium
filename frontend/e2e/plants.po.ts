import type { Locator, Page } from "@playwright/test";

import { BasePage } from "./base.po";

/** Plants page locators (FE-013/014). */
export class PlantsPage extends BasePage {
  readonly heading: Locator;
  readonly addPlantButton: Locator;

  constructor(page: Page) {
    super(page);
    this.heading = page.getByRole("heading", { name: "Plants", level: 1 });
    this.addPlantButton = page.getByRole("button", { name: "Add plant" });
  }

  /** The list row for a plant, located by its visible name. */
  card(name: string): Locator {
    return this.page.getByRole("listitem").filter({ hasText: name });
  }
}
