import type { Page } from "@playwright/test";

/**
 * Common base for all page objects (FE-013). Holds the `page` and the single
 * navigation primitive; concrete `.po.ts` subclasses add only locators.
 */
export abstract class BasePage {
  constructor(protected readonly page: Page) {}

  async goto(path: string): Promise<void> {
    await this.page.goto(path);
  }
}
