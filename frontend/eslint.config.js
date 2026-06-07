import js from "@eslint/js";
import globals from "globals";
import tseslint from "typescript-eslint";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import prettier from "eslint-config-prettier";

export default tseslint.config(
  { ignores: ["dist", "coverage", "node_modules"] },
  {
    files: ["**/*.{ts,tsx}"],
    extends: [
      js.configs.recommended,
      ...tseslint.configs.recommendedTypeChecked,
    ],
    languageOptions: {
      ecmaVersion: 2022,
      globals: globals.browser,
      parserOptions: {
        projectService: true,
        tsconfigRootDir: import.meta.dirname,
      },
    },
    plugins: {
      "react-hooks": reactHooks,
      "react-refresh": reactRefresh,
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      "react-refresh/only-export-components": [
        "warn",
        { allowConstantExport: true },
      ],
      // FE-004: ban escape-hatch types.
      "@typescript-eslint/no-explicit-any": "error",
      "@typescript-eslint/no-restricted-types": [
        "error",
        {
          types: {
            object: "Use a precise object shape instead of `object`.",
            "{}": "Use a precise object shape or `Record<string, unknown>`.",
          },
        },
      ],
    },
  },
  // FE-008: a file inside a feature MUST NOT import from a different feature.
  // The composition root (App.tsx) and shared dirs are free to mount features.
  {
    files: ["src/features/**/*.{ts,tsx}"],
    ignores: ["src/features/**/*.test.{ts,tsx}"],
    rules: {
      "no-restricted-imports": [
        "error",
        {
          patterns: [
            {
              // Cross-module imports use the `@/` alias (see tsconfig paths +
              // vite resolve.alias). A feature may only reach shared code
              // (`@/lib`, `@/components`), never another feature.
              group: ["@/features/*", "@/features/*/**"],
              message:
                "Feature isolation (FE-008): import shared code from @/lib or @/components, not another feature.",
            },
          ],
        },
      ],
    },
  },
  // Config + setup files run in Node and are not part of the typed app graph.
  {
    files: ["*.config.{js,ts}", "vitest.setup.ts"],
    extends: [tseslint.configs.disableTypeChecked],
    languageOptions: {
      globals: globals.node,
      parserOptions: { projectService: false },
    },
  },
  prettier,
);
