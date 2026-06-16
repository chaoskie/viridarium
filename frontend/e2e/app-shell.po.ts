import type { Locator, Page } from "@playwright/test";

import { BasePage } from "./base.po";

/**
 * App-shell header locators (FE-013/014). The theme `<select>` is rendered twice
 * (a phone instance and a tablet+ instance, one CSS-hidden per breakpoint), so
 * `themeSelect` intersects the label match with `:visible` to get the active one.
 */
export class AppShellPage extends BasePage {
  readonly themeSelect: Locator;
  readonly wordmark: Locator;

  constructor(page: Page) {
    super(page);
    this.themeSelect = page.getByLabel("Theme").and(page.locator(":visible"));
    this.wordmark = page.getByText("VIRID", { exact: false });
  }
}
