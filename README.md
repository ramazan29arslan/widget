# Pati – kilit ekranında yaşayan karakterler

iPhone kilit ekranına (saatin altındaki satıra) eklenen hareketli karakter widget'ları.
Uygulama **Expo (React Native)** ile yazıldı, widget ise iOS'un zorunlu kıldığı şekilde **SwiftUI/WidgetKit** ile. İkisi tek projede duruyor ve **Mac olmadan EAS Build ile bulutta** derleniyor.

| Kuyruk sallama | Yürüyüş | Uykuda nefes | Yuvarlanma |
|---|---|---|---|
| ![](docs/preview/Pati-cat-tail-fast.gif) | ![](docs/preview/Pati-cat-walk-fast.gif) | ![](docs/preview/Pati-cat-breathe-fast.gif) | ![](docs/preview/Pati-cat-roll-fast.gif) |

Ruh hali pozları (uyanık, oyuncu, uykulu, yorgun, uyuyor):

![](docs/preview/Pati-cat-poses.png)

> Önizlemeler hızlandırılmıştır. Gerçek widget saniyede 1 kare oynar.

## Mac olmadan iPhone'a kurulum

Gereken: Windows/Linux/Mac fark etmez, Node.js 20+, bir [Expo hesabı](https://expo.dev/signup) ve **ücretli Apple Developer Program üyeliği** (yıllık 99 $). Widget içeren bir uygulamayı Mac'siz imzalayıp telefona yüklemenin tek yolu bu.

```bash
git clone https://github.com/ramazan29arslan/widget.git
cd widget
npm install
npm install -g eas-cli
eas login
```

1. `app.json` içinde `ios` bölümüne Apple Team ID'ni ekle: `"appleTeamId": "ABCDE12345"` (developer.apple.com → Membership details).
2. iPhone'unu kaydet: `eas device:create` → çıkan bağlantıyı iPhone'da aç, profili yükle.
3. Derle: `eas build -p ios --profile preview`
   - EAS, Apple hesabına giriş ister; sertifikaları, App Group'u ve widget için gereken her şeyi kendisi oluşturur.
   - 15–25 dakika sonra bir QR kod / bağlantı verir. iPhone'da açıp uygulamayı yükle.
4. iPhone'da **Ayarlar → Gizlilik ve Güvenlik → Geliştirici Modu**'nu aç (ilk kurulumda istenir).
5. Kilit ekranına basılı tut → **Özelleştir** → **Kilit Ekranı** → saatin altındaki alana dokun → **Pati**.

App Store / TestFlight için: `eas build -p ios --profile production` ve ardından `eas submit -p ios`.

> Expo Go ile yalnızca uygulama ekranları açılır; widget ve App Group bağlantısı Expo Go'da çalışmaz. Widget için mutlaka EAS ile derlenmiş sürüm gerekir.

## İki widget türü

**Canlı Pati:** Saniyede bir kare oynayan 10 karelik döngü. Widget ayarlarından karakter ve animasyon seçilir. "Otomatik" seçilirse klip ruh haline göre değişir (uykuluyken nefes alır, akşam yuvarlanır).

**Ruh Hali Pati:** Saate, şarja ve şarj durumuna göre poz değiştirir.

| Durum | Poz |
|---|---|
| 00–06 | Uyuyor |
| 06–08, 13–15, 22–24 | Uykulu |
| 17–20 | Oyuncu |
| Şarjda | Uyuyor (şekerleme) |
| Pil < %20 | Yorgun, yere serilmiş |
| Diğer saatler | Uyanık |

Kurallar iki yerde aynı tutulur: `targets/widget/Mood.swift` (widget) ve `src/mood.ts` (uygulama).

## Animasyon nasıl çalışıyor?

Kilit ekranı widget'ları sürekli animasyon oynatamaz, ama sistemin sayaç metni (`Text(date, style: .timer)`) her saniye kendiliğinden güncellenir. Bu projede:

1. Her animasyon klibi özel bir **font**tur. `0`–`9` rakamları 10 karenin çizimleridir.
2. Fontta bir OpenType `calt` kuralı var: ardından başka rakam veya `:` gelen her rakam, genişliği 0 olan boş bir glife dönüşür.
3. Sayaç `1:23:45` yazdığında ekranda yalnızca son hane (`5`) görünür, yani 5. kare. Bir saniye sonra 6. kare gelir.

Pozlar da aynı yöntemle çizilir: poz fontunda `a`, `s`, `z`, `t`, `p` harfleri birer pozdur. Uygulama aynı fontları `expo-font` ile yükleyip önizleme gösterir.

> ⚠️ Bu yöntem resmi bir animasyon API'si değildir. Gerçek cihazda test edilmeli ve her yeni iOS sürümünde tekrar kontrol edilmelidir. Ruh Hali widget'ı tamamen standart API'lerle çalışır.

## Uygulama ↔ widget iletişimi

`@bacons/apple-targets` paketindeki `ExtensionStorage`, App Group (`group.com.ramazan29arslan.pati`) üzerinden veri yazar:

| Anahtar | Yazan | Anlamı |
|---|---|---|
| `reactToBattery` | Uygulama (anahtar) | 1/0: şarja tepki ver |
| `batteryPercent` | Uygulama (expo-battery) | Son pil yüzdesi, widget okuyamazsa yedek |
| `batteryCharging` | Uygulama | 1/0 |

Bundle ID'yi değiştirirsen App Group adını üç yerde güncelle: `app.json`, `src/widgetBridge.ts`, `targets/widget/SharedSettings.swift`.

## Yeni karakter eklemek

```bash
cd Tools/fontgen
pip install -r requirements.txt
cp characters/cat.py characters/kopek.py   # ID, NAME, çizimler, CLIPS, POSES'u düzenle
python3 build_fonts.py   # fontları + Swift ve TypeScript kataloglarını üretir
python3 test_fonts.py    # sayaç testleri + docs/preview önizlemeleri
```

Kurallar:
- Her klip tam **10 kare** olmalı.
- Tuval 2000 × 1000 font birimidir (2:1, kilit ekranı dikdörtgen widget'ına uygun).
- Kilit ekranı tek renk gösterdiği için çizimler siluet ya da çizgi stilinde olmalı. Delikler (göz, burun) `hole` ile oyulur.
- Ruh hali pozlarında `a s z t p` harflerini kullan. Eksik poz olursa ilk poz gösterilir.

## Klasörler

```
App.tsx, src/          Expo uygulaması (galeri, canlı önizleme, ayarlar)
targets/widget/        SwiftUI widget kodu ve fontlar (apple-targets ile Xcode'a eklenir)
Tools/fontgen/         Çizimden font üreten ve test eden Python araçları
docs/preview/          Üretilen önizlemeler
```

`ios/` klasörü depoda tutulmaz; `npx expo prebuild` ya da EAS Build her seferinde yeniden üretir.

## Yol haritası

- [ ] Gerçek cihazda font/sayaç yönteminin doğrulanması
- [ ] SVG karelerden font üretimi (tasarımcı çizimleri için)
- [ ] Yeni karakterler: köpek, kurbağa, bulut, hayalet
- [ ] Hava durumu ve konuma göre pozlar (WeatherKit)
- [ ] Ücretli karakter paketleri
