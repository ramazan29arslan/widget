/** @type {import('@bacons/apple-targets/app.plugin').ConfigFunction} */
module.exports = (config) => ({
  type: "widget",
  name: "PatiWidget",
  displayName: "Pati",
  deploymentTarget: "17.0",
  frameworks: ["SwiftUI", "WidgetKit", "AppIntents"],
  // Ana uygulamanın app.json'daki App Group'unu kullan (ExtensionStorage ile paylaşım)
  entitlements: {
    "com.apple.security.application-groups":
      config.ios.entitlements["com.apple.security.application-groups"],
  },
});
