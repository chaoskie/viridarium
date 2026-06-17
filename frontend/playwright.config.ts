import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright acceptance config (ARCH-001 locked stack; TEST-009/010, FE-013/014).
 *
 * Drives the real app against a real backend: the `webServer` array boots FastAPI
 * on a throwaway migrated SQLite DB (`e2e/run-backend.sh`) and serves the
 * production frontend build via `vite preview` with `/api` proxied to the backend
 * (`vite.config.ts` `preview.proxy`) - the production path, not the dev server.
 *
 * The primary project emulates a Samsung Galaxy S25+ (the soak device): a
 * phone-width viewport where the mobile-layout regressions reproduce. A second
 * desktop project exists for the FE-012 design-review screenshots.
 */
// Dedicated acceptance-backend port: deliberately NOT 8000 so the suite never
// collides with a dev backend (`make dev-backend`) or any other local service.
// Override with E2E_BACKEND_PORT if 8799 is taken.
const BACKEND_PORT = process.env.E2E_BACKEND_PORT ?? "8799";
const BACKEND_HEALTH = `http://localhost:${BACKEND_PORT}/api/v1/health`;
const FRONTEND_URL = "http://localhost:4173";
const isCI = Boolean(process.env.CI);

// Release-gated multi-device matrix (set E2E_DEVICE_MATRIX=1). OFF per-PR so the
// PR pipeline stays fast (galaxy-s25-plus + desktop only); the release workflow
// (.github/workflows/device-matrix.yml) turns it on to re-run the width-sensitive
// `@layout` specs across the current top-5 mobile CSS viewports. These are the
// read-only layout checks (overflow / on-screen controls / a11y); the write specs
// stay single-device because the shared SQLite backend runs workers:1.
const deviceMatrix = process.env.E2E_DEVICE_MATRIX === "1";

// Top-5 most common mobile CSS viewport widths (heights are the logical device
// heights). The primary 384x740 (S25+) already covers a tight-height case.
const MATRIX_VIEWPORTS = [
  { name: "mobile-360x800", width: 360, height: 800 },
  { name: "mobile-390x844", width: 390, height: 844 },
  { name: "mobile-393x852", width: 393, height: 852 },
  { name: "mobile-412x915", width: 412, height: 915 },
  { name: "mobile-430x932", width: 430, height: 932 },
] as const;

const matrixProjects = deviceMatrix
  ? MATRIX_VIEWPORTS.map((v) => ({
      name: v.name,
      // Only the read-only, width-sensitive layout specs (no writes -> no extra
      // contention on the shared backend, no duplicate screenshot evidence).
      grep: /@layout/,
      use: {
        ...devices["Galaxy S9+"],
        viewport: { width: v.width, height: v.height },
        deviceScaleFactor: 3,
      },
    }))
  : [];

export default defineConfig({
  testDir: "./e2e",
  // Acceptance specs only; *.po.ts / *.co.ts / fixtures are support files.
  testMatch: /.*\.spec\.ts/,
  // The suite drives a single shared backend on one SQLite file; parallel workers
  // contend on writes ("database is locked"). Run serially - the suite is small.
  fullyParallel: false,
  workers: 1,
  forbidOnly: isCI,
  retries: isCI ? 1 : 0,
  reporter: [["html", { open: "never" }], ["list"]],
  use: {
    baseURL: FRONTEND_URL,
    // Failure-capture artifacts only - ephemeral, never committed (TEST-011).
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "galaxy-s25-plus",
      use: {
        // Mobile Chromium base (isMobile/hasTouch/defaultBrowserType), then the
        // S25+ CSS viewport on top. Width ~384 @ DPR ~3.75; height 740 reflects the
        // *usable* in-browser height (the ~384x832 logical size minus the Samsung
        // Internet/Chrome address bar + system bars) - the condition under which the
        // soak surfaced the clipped, unscrollable add-plant modal (BUG-003).
        ...devices["Galaxy S9+"],
        viewport: { width: 384, height: 740 },
        deviceScaleFactor: 3.75,
      },
    },
    {
      name: "desktop",
      // Only `@desktop`-tagged specs (the FE-012 design-review screenshots) run at
      // desktop width; the mobile-regression specs are untagged and S25+-only.
      grep: /@desktop/,
      use: {
        ...devices["Desktop Chrome"],
        viewport: { width: 1280, height: 800 },
      },
    },
    // Release-gated only: the top-5 mobile-resolution layout matrix (empty per-PR).
    ...matrixProjects,
  ],
  webServer: [
    {
      command: "bash e2e/run-backend.sh",
      url: BACKEND_HEALTH,
      reuseExistingServer: !isCI,
      timeout: 120_000,
      stdout: "pipe",
      stderr: "pipe",
      env: { E2E_BACKEND_PORT: BACKEND_PORT },
    },
    {
      command: "npm run build && npm run preview -- --port 4173 --strictPort",
      url: FRONTEND_URL,
      reuseExistingServer: !isCI,
      timeout: 180_000,
      // The built app's `/api` proxy must point at the same dedicated backend port.
      env: { E2E_BACKEND_PORT: BACKEND_PORT },
    },
  ],
});
