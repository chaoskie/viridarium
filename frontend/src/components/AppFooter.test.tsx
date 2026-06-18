import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { AppFooter } from "./AppFooter";

function renderFooter(): void {
  render(
    <MemoryRouter>
      <AppFooter />
    </MemoryRouter>,
  );
}

describe("AppFooter", () => {
  it("links to the About page", () => {
    renderFooter();
    const about = screen.getByRole("link", { name: /about/i });
    expect(about).toHaveAttribute("href", "/about");
  });

  it("links to support and opens it safely in a new tab", () => {
    renderFooter();
    const support = screen.getByRole("link", { name: /support/i });
    expect(support).toHaveAttribute("href", "https://linktr.ee/chaoskie");
    expect(support).toHaveAttribute("target", "_blank");
    expect(support).toHaveAttribute("rel", "noopener noreferrer");
  });
});
