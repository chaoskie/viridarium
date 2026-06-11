/*
 * Pre-paint theme application (avoids a flash of the wrong theme). Served
 * same-origin from the dist root so the strict CSP (`script-src 'self'`,
 * SEC-011) passes on the production path (VIRIDARIUM-37). Loaded as a
 * blocking script in <head> so it runs before the bundle.
 *
 * Mirrors src/lib/theme/themeController.ts. Precedence (D-008): a stored
 * choice always wins; else honor the OS prefers-color-scheme (dark -> dark);
 * else the Roman default. KEY + valid values MUST match the controller (the
 * entry-html-csp test pins this).
 */
(function () {
  var KEY = "viridarium.theme";
  var THEMES = ["roman", "dark", "herbarium", "terracotta", "viridian"];
  var DEFAULT = "roman";
  var stored;
  try {
    stored = window.localStorage.getItem(KEY);
  } catch (e) {
    stored = null;
  }
  var theme;
  if (THEMES.indexOf(stored) >= 0) {
    theme = stored;
  } else {
    var prefersDark = false;
    try {
      prefersDark =
        window.matchMedia &&
        window.matchMedia("(prefers-color-scheme: dark)").matches;
    } catch (e) {
      prefersDark = false;
    }
    theme = prefersDark ? "dark" : DEFAULT;
  }
  document.documentElement.setAttribute("data-theme", theme);
})();
