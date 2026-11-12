// App Group: uygulama ile widget arasında ayar ve pil bilgisini paylaşır.
// Ücretli Apple Developer hesabı gerekir (varsayılan: açık).
// Ücretsiz hesapla derlemek için kapat:  PATI_APP_GROUP=0 npx expo prebuild -p ios --clean
const APP_GROUP = 'group.com.ramazan29arslan.pati';

module.exports = ({ config }) => {
  if (process.env.PATI_APP_GROUP !== '0') {
    config.ios = {
      ...config.ios,
      entitlements: {
        ...(config.ios?.entitlements ?? {}),
        'com.apple.security.application-groups': [APP_GROUP],
      },
    };
  }
  return config;
};
