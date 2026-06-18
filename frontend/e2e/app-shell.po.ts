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
  /** The app-wide footer landmark and its two links (VIRIDARIUM-76). */
  readonly footer: Locator;
  readonly footerAboutLink: Locator;
  readonly footerSupportLink: Locator;

  constructor(page: Page) {
    super(page);
    this.themeSelect = page.getByLabel("Theme").and(page.locator(":visible"));
    this.wordmark = page.getByText("VIRID", { exact: false });
    this.footer = page.getByRole("contentinfo");
    this.footerAboutLink = this.footer.getByRole("link", { name: "About" });
    this.footerSupportLink = this.footer.getByRole("link", {
      name: /support/i,
    });
  }
}

/** About page locators (FE-013). */
export class AboutPage extends BasePage {
  readonly heading: Locator;
  readonly version: Locator;

  constructor(page: Page) {
    super(page);
    this.heading = page.getByRole("heading", {
      level: 1,
      name: /about viridarium/i,
    });
    this.version = page.getByText(/version /i);
  }
}
