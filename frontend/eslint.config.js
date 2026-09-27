import js from "@eslint/js";
import tseslint from "typescript-eslint";
import globals from "globals";

export default tseslint.config(
  { ignores: ["dist/**", "node_modules/**", "src/*.jsx"] },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ["src/**/*.{ts,tsx}"],
    languageOptions: { globals: globals.browser },
    rules: { "@typescript-eslint/no-non-null-assertion": "off" },
  },
  {
    files: [
      "*.js",
      "*.mjs",
      "scripts/**/*.mjs",
      "worker/**/*.js",
      "tests/**/*.mjs",
    ],
    languageOptions: { globals: globals.node },
  },
);
