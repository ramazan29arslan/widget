# Görselden karakter yapmak

Bu klasöre koyduğun PNG kareler otomatik olarak widget fontuna çevrilir. Görseli olan klip, kodla çizilen sürümün yerine geçer. Görseli olmayan klipler kodla çizilen hâliyle kalır; yani tek tek değiştirebilirsin.

```
art/cat/
  tail/      kuyruk sallama          (tek widget)
  breathe/   uykuda nefes            (tek widget)
  roll/      yuvarlanma              (tek widget)
  walk/      yürüyüş                 (panorama, 4 kare)
  mouse/     fare kovalama           (panorama)
  yarn/      yumak kovalama          (panorama)
  poses/     a.png s.png z.png t.png p.png
             uyanık, uykulu, uyuyor, yorgun, oyuncu
```

Her klip klasörüne şunlardan **birini** koy:

- `00.png … 09.png`: 10 ayrı kare. Daha az kare verirsen (ör. 4) 10'a yayılır.
- `sheet.png`: 5 sütun × 2 satırlık tek bir sprite sheet. Farklı bir düzen için `clip.json` içine `"grid": [4, 2]` yaz.

## Görsel kuralları

Referans fotoğraftaki kedi birebir bu kurallara uyuyor:

1. **Zemin siyah ya da saydam olsun.** Araç, kenarlara değen zemin rengini otomatik siler.
2. **Figür beyaz ya da açık renk, çizgiler koyu olsun.** Açık alanlar kilit ekranında beyaz görünür; koyu kalem çizgileri, gözler ve tarama oyuk olur. Siyah zemin üstündeki açık bıyıklar da korunur.
3. **Tüm kareler aynı boyutta olsun ve karakter aynı ölçekte kalsın.** Araç kareleri ortak sınıra göre kırpar; karakter karelerde yer değiştirirse bu hareket korunur.
4. **Yan görünüş, yüz sağa baksın.** Panorama sahnelerinde karakter soldan sağa ilerler.
5. **En az 800 piksel genişlik.** Küçük görseller otomatik büyütülür, ama büyük görsel daha temiz sonuç verir.
6. **Panorama klipleri** (walk, mouse, yarn) için kareler yaklaşık **4:1** oranında olsun, örneğin 2400 × 600. Karakter kare kare soldan sağa ilerlesin.

Beyaz zemin üzerinde siyah çizgili görseller de çalışır, ama dış çizginin kapalı olması gerekir; yoksa zemin içeri sızar. Siyah silüet tarzı görseller için `clip.json` içine `"invert": true` yaz.

## Ayarlar (`clip.json`, isteğe bağlı)

```json
{
  "title": "Yürüyüş",
  "wide": true,
  "grid": [5, 2],
  "order": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
  "threshold": 0.72,
  "invert": false,
  "scale": 1.0,
  "offset": [0, 0],
  "autocrop": true
}
```

- `threshold`: Bundan koyu pikseller çizgi sayılır. Çizgiler kayboluyorsa değeri artır (0.8), gövde lekeleniyorsa azalt (0.6).
- `order`: Kareleri yeniden sırala ya da tekrar et, örneğin `[0,1,2,3,4,4,3,2,1,0]` ile ileri-geri döngü yaparsın.

## Yapay zekâ ile kare üretmek

En iyi sonuç için önce **tek bir referans kedi** görseli belirle; örneğin elindeki ekmek pozundaki kedi. Sonra her karede aynı karakteri iste. ChatGPT'de referans görseli ekleyip ister; Midjourney'de `--cref` kullan.

Örnek istem (İngilizce daha tutarlı sonuç verir):

```
Sprite sheet, 10 frames in a 5×2 grid, equal cell size, solid black background.
The same chubby white British Shorthair cat as the reference image, pencil sketch style:
white fur, fine black ink outline, light cross-hatching on the belly and lower edges,
long thin whiskers, black almond eyes. Side view, facing right, full body, same scale
in every frame. Animation: <HAREKET>.
No text, no shadows on the ground, no color.
```

`<HAREKET>` örnekleri:

- **tail:** `lying in loaf pose, tail swishing left and right, blinks once`
- **breathe:** `curled up asleep, body gently rising and falling`
- **roll:** `rolls from loaf pose onto its back with paws in the air and back again`
- **walk:** `walk cycle moving left to right across a wide 4:1 frame`
- **mouse:** `chasing a small mouse across a wide 4:1 frame, pounces at the end`
- **yarn:** `chasing a rolling ball of yarn across a wide 4:1 frame, catches it`
- **poses:** Her pozu ayrı tek görsel olarak üret: `sitting alert`, `sleepy half-closed eyes`, `asleep curled`, `exhausted lying flat`, `playful on its back`.

Sprite sheet'teki kareler birbirini tutmazsa her kareyi referansla tek tek üret ve `00.png … 09.png` olarak kaydet.

## Üretmek ve kontrol etmek

```bash
cd Tools/fontgen
pip install -r requirements.txt
python3 build_fonts.py cat   # yalnızca kediyi yeniden üret
python3 test_fonts.py        # docs/preview altına GIF önizlemeleri
```

Görselleri sohbette Claude'a göndermen de yeterli; klasörlere yerleştirip fontları o üretir.

## Yeni karakter (yalnızca görselden)

`art/<id>/character.json` oluştur:

```json
{ "name": "Tavşan", "moodClips": { "awake": "hop", "sleeping": "sleep", "playful": "run" } }
```

Ardından `art/<id>/hop/`, `art/<id>/run/` (panorama için içine `clip.json` ile `{"wide": true}`) ve `art/<id>/poses/` klasörlerine görsellerini koy.
