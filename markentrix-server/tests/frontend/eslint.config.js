import globals from "globals";
export default [{ files: ["js/**/*.js"], languageOptions: { sourceType: "module", ecmaVersion: 2023, globals: { ...globals.browser } },
  rules: { "no-undef": "error", "no-unused-vars": ["warn", { args: "none", caughtErrors: "none" }], "no-redeclare": "error", "no-dupe-keys": "error", "no-unreachable": "error", "eqeqeq": ["warn", "smart"] } }];
