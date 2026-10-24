const { jestConfig } = require("@salesforce/sfdx-lwc-jest/config");

module.exports = {
  ...jestConfig,
  // Resolve CSS-only shared LWC modules through the real compiler.
  moduleFileExtensions: [
    ...new Set([...jestConfig.moduleFileExtensions, "css"])
  ],
  modulePathIgnorePatterns: ["<rootDir>/.localdevserver"]
};
