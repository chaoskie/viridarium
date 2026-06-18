import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AboutPage } from "./AboutPage";

function stubHealth(body: unknown, ok = true): void {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok,
      status: ok ? 200 : 503,
      json: () => Promise.resolve(body),
    } as Response),
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("AboutPage", () => {
  // The static tests await the version settle so the mount health-fetch resolves
  // inside act() (no React act warnings).
  it("shows the project description and a thank-you", async () => {
    stubHealth({ status: "ok", version: "1.2.3" });
    render(<AboutPage />);

    expect(
      screen.getByRole("heading", { level: 1, name: /about viridarium/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/open-source, self-hosted plant-care/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/thanks for using viridarium/i),
    ).toBeInTheDocument();
    await screen.findByText(/version 1\.2\.3/i);
  });

  it("includes the maintainer note excerpt with a link to the full README note", async () => {
    stubHealth({ status: "ok", version: "1.2.3" });
    render(<AboutPage />);

    expect(
      screen.getByText(/i am very much the mind behind it/i),
    ).toBeInTheDocument();
    const full = screen.getByRole("link", { name: /full note/i });
    expect(full).toHaveAttribute(
      "href",
      "https://github.com/chaoskie/viridarium#a-note-from-the-maintainer",
    );
    expect(full).toHaveAttribute("target", "_blank");
    expect(full).toHaveAttribute("rel", "noopener noreferrer");
    await screen.findByText(/version 1\.2\.3/i);
  });

  it("links to support (third-party, new tab) and to the source under AGPL-3.0", async () => {
    stubHealth({ status: "ok", version: "1.2.3" });
    render(<AboutPage />);

    const support = screen.getByRole("link", { name: /linktr\.ee\/chaoskie/i });
    expect(support).toHaveAttribute("href", "https://linktr.ee/chaoskie");
    expect(support).toHaveAttribute("target", "_blank");
    expect(support).toHaveAttribute("rel", "noopener noreferrer");

    expect(screen.getByText(/agpl-3\.0/i)).toBeInTheDocument();
    const source = screen.getByRole("link", {
      name: /github\.com\/chaoskie\/viridarium/i,
    });
    expect(source).toHaveAttribute(
      "href",
      "https://github.com/chaoskie/viridarium",
    );
    await screen.findByText(/version 1\.2\.3/i);
  });

  it("states the privacy posture (no outbound connections without explicit approval)", async () => {
    stubHealth({ status: "ok", version: "1.2.3" });
    render(<AboutPage />);

    expect(
      screen.getByText(
        /no outbound connections without your explicit approval/i,
      ),
    ).toBeInTheDocument();
    await screen.findByText(/version 1\.2\.3/i);
  });

  it("shows the live backend version", async () => {
    stubHealth({ status: "ok", version: "1.2.3" });
    render(<AboutPage />);

    await waitFor(() => {
      expect(screen.getByText(/version 1\.2\.3/i)).toBeInTheDocument();
    });
  });

  it("degrades gracefully when the health endpoint is unavailable", async () => {
    stubHealth({}, false);
    render(<AboutPage />);

    await waitFor(() => {
      expect(screen.getByText(/version unavailable/i)).toBeInTheDocument();
    });
    // No crash, no perpetual loading spinner.
    expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
  });
});
