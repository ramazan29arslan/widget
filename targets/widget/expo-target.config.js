/** @type {import('@bacons/apple-targets/app.plugin').ConfigFunction} */
module.exports = (config) => {
  // App Group yalnızca app.config.js'de açıldıysa (PATI_APP_GROUP=1) widget'a da eklenir.
  const groups = config.ios?.entitlements?.["com.apple.security.application-groups"];
  return {
    type: "widget",
    name: "PatiWidget",
    displayName: "Pati",
    deploymentTarget: "17.0",
    frameworks: ["SwiftUI", "WidgetKit", "AppIntents"],
    ...(groups ? { entitlements: { "com.apple.security.application-groups": groups } } : {}),
  };
};
