"""Görsellerden (PNG kare / sprite sheet) widget glifi üretir.

Klasör yapısı (Tools/fontgen/art/):

    art/<karakter>/
        character.json          # yalnızca YENİ karakterler için (ad, ruh hali klipleri)
        <klip>/                 # ör. art/cat/walk/
            00.png ... 09.png   # kareler (dosya adı sırasıyla) — 10'dan az ise tekrarlanır
            sheet.png           # YA DA tek bir sprite sheet
            clip.json           # isteğe bağlı ayarlar (aşağıda)
        poses/
            a.png s.png z.png t.png p.png   # uyanık, uykulu, uyuyor, yorgun, oyuncu

clip.json (hepsi isteğe bağlı):
    {
      "title": "Yürüyüş",        # yeni klipler için başlık
      "wide": false,             # true: panorama (iki widget)
      "grid": [5, 2],            # sprite sheet sütun × satır (varsayılan 5 × 2)
      "order": [0,1,2,3,4,5,6,7,8,9],  # karelerin sırası (tekrar edebilir)
      "threshold": 0.72,         # gövde içinde bundan koyu pikseller çizgi olur (0..1)
      "invert": false,           # true: koyu figür (siyah silüet) dolgu olur
      "scale": 1.0,              # sahnede büyüklük
      "offset": [0, 0],          # sahnede kaydırma (font birimi)
      "autocrop": true           # karelerin ortak sınırına kırp
    }

Dönüşüm:
  1. Arka plan: saydam pikseller ya da kenara bağlı, köşe rengine benzeyen bölge.
  2. Figürün açık renkli pikselleri DOLGU (kilit ekranında beyaz), koyu çizgiler OYUK olur.
     Böylece siyah zemin üzerinde beyaz, kalem çizgili bir çizim (referans kedi gibi) birebir aktarılır.
  3. Maske potrace ile vektöre çevrilir (yumuşak Bezier eğrileri).
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import potrace
from PIL import Image
from pathops import FillType, Path as SkPath
from scipy import ndimage as ndi
from skimage import measure, morphology

ART_DIR = Path(os.environ.get("PATI_ART_DIR", Path(__file__).resolve().parent / "art"))
STAGE_H = 1000
GROUND = 20
IMAGE_EXT = (".png", ".webp", ".jpg", ".jpeg")


@dataclass
class ClipArt:
    folder: Path
    options: dict = field(default_factory=dict)

    @property
    def wide(self) -> bool:
        return bool(self.options.get("wide", False))


# ----------------------------------------------------------------- keşif

def art_clips(char_id: str) -> dict[str, ClipArt]:
    root = ART_DIR / char_id
    if not root.is_dir():
        return {}
    out = {}
    for sub in sorted(root.iterdir()):
        if sub.is_dir() and sub.name != "poses" and _images(sub):
            out[sub.name] = ClipArt(sub, _read_json(sub / "clip.json"))
    return out


def art_poses(char_id: str) -> dict[str, Path]:
    root = ART_DIR / char_id / "poses"
    if not root.is_dir():
        return {}
    return {p.stem: p for p in sorted(root.iterdir()) if p.suffix.lower() in IMAGE_EXT and len(p.stem) == 1}


def art_characters() -> dict[str, dict]:
    """character.json içeren klasörler: tamamen görselden oluşan yeni karakterler."""
    if not ART_DIR.is_dir():
        return {}
    out = {}
    for sub in sorted(ART_DIR.iterdir()):
        meta = _read_json(sub / "character.json")
        if sub.is_dir() and meta:
            out[sub.name] = meta
    return out


def _read_json(p: Path) -> dict:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}


def _images(folder: Path) -> list[Path]:
    return sorted(p for p in folder.iterdir() if p.suffix.lower() in IMAGE_EXT)


# ----------------------------------------------------------------- kareler

def load_frames(clip: ClipArt) -> list[Image.Image]:
    files = _images(clip.folder)
    sheet = [p for p in files if p.stem.lower() == "sheet"]
    if sheet:
        img = Image.open(sheet[0]).convert("RGBA")
        cols, rows = clip.options.get("grid", [5, 2])
        cw, ch = img.width // cols, img.height // rows
        frames = [img.crop((c * cw, r * ch, (c + 1) * cw, (r + 1) * ch)) for r in range(rows) for c in range(cols)]
    else:
        frames = [Image.open(p).convert("RGBA") for p in files]
    order = clip.options.get("order")
    if order:
        frames = [frames[i] for i in order]
    if len(frames) != 10:  # 10 kareye yay
        frames = [frames[i * len(frames) // 10] for i in range(10)]
    return frames


# ----------------------------------------------------------------- maske

def masks(frames: list[Image.Image], threshold=0.72, invert=False) -> list[np.ndarray]:
    return [_mask(f, threshold, invert) for f in frames]


def _mask(img: Image.Image, threshold: float, invert: bool) -> np.ndarray:
    """threshold: gövde içinde bundan koyu pikseller kalem çizgisi (oyuk) sayılır."""
    # Küçük görselleri büyüt: ince çizgiler korunur, eğriler yumuşar.
    if max(img.size) < 1600:
        k = 1600 / max(img.size)
        img = img.resize((round(img.width * k), round(img.height * k)), Image.LANCZOS)
    a = np.asarray(img).astype(np.float32) / 255.0
    rgb, alpha = a[..., :3], a[..., 3]
    lum = 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]
    if invert:
        lum = 1.0 - lum
    if alpha.min() < 0.95:
        background = alpha < 0.5
        bg_lum = 0.0
    else:
        border = np.concatenate([lum[0], lum[-1], lum[:, 0], lum[:, -1]])
        bg_lum = float(np.median(border))
        similar = np.abs(lum - bg_lum) < 0.15
        labels = measure.label(similar, connectivity=1)
        edge = set(np.unique(np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]]))) - {0}
        background = np.isin(labels, list(edge))
    figure = ~background
    # Gövde: açık bölgelerin dolu hali (içindeki çizgiler dahil)
    light = figure & (lum > threshold)
    body = ndi.binary_fill_holes(ndi.binary_closing(light, iterations=3))
    # Gövde içinde: açık = dolgu, koyu çizgi = oyuk.
    # Gövde dışında (bıyık, ince tüy): zeminden belirgin açık her şey dolgu.
    outside_ink = figure & ~body & (lum > bg_lum + 0.22)
    m = (body & (lum > threshold)) | outside_ink
    min_area = max(6, int(m.size * 0.00001))
    m = morphology.remove_small_objects(m, max_size=min_area)
    m = ~morphology.remove_small_objects(~m, max_size=max(3, min_area // 2))
    return m


# ----------------------------------------------------------------- vektör

def trace_clip(clip: ClipArt, stage_w: int) -> list[SkPath]:
    o = clip.options
    frames = load_frames(clip)
    ms = masks(frames, o.get("threshold", 0.72), o.get("invert", False))
    return place(ms, stage_w, o)


def trace_poses(paths: dict[str, Path], stage_w: int = 2000, options: dict | None = None) -> dict[str, SkPath]:
    o = options or {}
    keys = list(paths)
    imgs = [Image.open(paths[k]).convert("RGBA") for k in keys]
    same = len({im.size for im in imgs}) == 1
    if same:  # aynı tuval: ortak ölçek
        ms = masks(imgs, o.get("threshold", 0.72), o.get("invert", False))
        return dict(zip(keys, place(ms, stage_w, o)))
    return {k: place(masks([im], o.get("threshold", 0.72), o.get("invert", False)), stage_w, o)[0]
            for k, im in zip(keys, imgs)}


def place(ms: list[np.ndarray], stage_w: int, o: dict) -> list[SkPath]:
    """Maskeleri sahneye yerleştir: ortak kırpma, tabana oturtma, ortalama."""
    h, w = ms[0].shape
    if o.get("autocrop", True):
        union = np.zeros_like(ms[0])
        for m in ms:
            union |= m
        ys, xs = np.nonzero(union)
        if len(xs):
            pad = 2
            x0, x1 = max(0, xs.min() - pad), min(w, xs.max() + pad + 1)
            y0, y1 = max(0, ys.min() - pad), min(h, ys.max() + pad + 1)
            ms = [m[y0:y1, x0:x1] for m in ms]
            h, w = ms[0].shape
    avail_h = STAGE_H - GROUND - 10
    s = min(stage_w / w, avail_h / h) * o.get("scale", 1.0)
    dx = (stage_w - w * s) / 2 + o.get("offset", [0, 0])[0]
    dy = GROUND + o.get("offset", [0, 0])[1]
    return [_trace(m, s, dx, dy, h) for m in ms]


def _trace(mask: np.ndarray, s: float, dx: float, dy: float, h: int) -> SkPath:
    """Maske -> pathops yolu (y ekseni yukarı, font birimi)."""
    if not mask.any():
        return SkPath()
    # potracer koyu pikselleri izler: dolgu = 0
    bm = potrace.Bitmap(~mask)
    curves = bm.trace(turdsize=6, alphamax=1.1, opticurve=True, opttolerance=0.4)
    path = SkPath(fillType=FillType.EVEN_ODD)
    pen = path.getPen()

    def T(p):
        return (dx + p.x * s, dy + (h - p.y) * s)

    for c in curves:
        pen.moveTo(T(c.start_point))
        for seg in c.segments:
            if seg.is_corner:
                pen.lineTo(T(seg.c))
                pen.lineTo(T(seg.end_point))
            else:
                pen.curveTo(T(seg.c1), T(seg.c2), T(seg.end_point))
        pen.closePath()
    path.simplify()
    return path
