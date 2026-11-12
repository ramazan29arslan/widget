// Ücretsiz Apple hesabı App Groups'u desteklemez. Bu yüzden App Group varsayılan olarak kapalı.
// Ücretli Apple Developer hesabında açmak için:  PATI_APP_GROUP=1 npx expo prebuild -p ios --clean
// Kapalıyken widget pili kendisi okur; yalnızca uygulamadaki "şarja tepki ver" ayarı widget'a ulaşmaz.
const APP_GROUP = 'group.com.ramazan29arslan.pati';

module.exports = ({ config }) => {
  if (process.env.PATI_APP_GROUP === '1') {
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
