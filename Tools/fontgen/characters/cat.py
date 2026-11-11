"""Kedi karakteri: prosedürel çizim.

Tuval: x 0..2000, y 0..1000 (font birimi). Kedi sağa bakar.
Kendi karakterini eklemek için bu dosyayı kopyalayıp şekilleri değiştir
ya da SVG kareler kullan (bkz. README).
"""
from __future__ import annotations

import math

from shapes import Drawing, capsule, circle, ellipse, polyline, zee

ID = "cat"
NAME = "Kedi"


def _eyes(d: Drawing, cx: float, cy: float, state: str, gap: float = 150):
    for ex in (cx - gap / 2, cx + gap / 2):
        if state == "open":
            d.hole(ellipse(ex, cy, 26, 34))
        elif state == "half":
            d.hole(ellipse(ex, cy - 6, 32, 12))
        else:  # kapalı: aşağı bakan yay
            d.hole(polyline([(ex - 34, cy + 4), (ex, cy - 10), (ex + 34, cy + 4)], 9))


def _tail(base, start_deg, curl_deg, n=8, seg=55, r=42):
    pts = [base]
    a = math.radians(start_deg)
    for _ in range(n):
        x, y = pts[-1]
        pts.append((x + seg * math.cos(a), y + seg * math.sin(a)))
        a -= math.radians(curl_deg)
    return polyline(pts, r)


def _head(d: Drawing, hx: float, hy: float, eyes: str, droop: bool = False):
    d.fill(circle(hx, hy, 205), ellipse(hx, hy - 50, 235, 150))
    if droop:  # kulaklar yana yatık
        d.fill([(hx - 170, hy + 90), (hx - 260, hy + 200), (hx - 60, hy + 170)])
        d.fill([(hx + 170, hy + 90), (hx + 260, hy + 200), (hx + 60, hy + 170)])
    else:
        d.fill([(hx - 160, hy + 110), (hx - 125, hy + 290), (hx - 30, hy + 190)])
        d.fill([(hx + 30, hy + 195), (hx + 130, hy + 290), (hx + 160, hy + 110)])
    _eyes(d, hx, hy + 10, eyes)
    d.hole([(hx - 18, hy - 30), (hx + 18, hy - 30), (hx, hy - 52)])  # burun


def loaf(eyes="open", breath=0.0, wag=0.0, head_dy=0.0) -> Drawing:
    """'Ekmek' pozunda yatan kedi (ekran görüntüsündeki gibi)."""
    d = Drawing()
    d.fill(ellipse(900, 280 + breath / 2, 520, 240 + breath))
    d.fill(ellipse(1240, 60, 95, 50), ellipse(1080, 55, 95, 48))  # ön patiler
    _head(d, 1400, 470 + head_dy, eyes)
    d.fill(_tail((430, 250), 185, 13 + wag))
    return d


def flat(eyes="closed") -> Drawing:
    """Yere serilmiş, yorgun kedi (şarj düşük)."""
    d = Drawing()
    d.fill(ellipse(880, 170, 580, 150))
    d.fill(ellipse(1330, 50, 110, 40))
    _head(d, 1520, 220, eyes, droop=True)
    d.fill(_tail((320, 140), 180, 2, n=7))
    return d


def on_back(kick=0.0) -> Drawing:
    """Sırtüstü yuvarlanan oyuncu kedi."""
    d = Drawing()
    d.fill(ellipse(900, 300, 480, 210))
    for x0, lean in ((720, -1), (860, -0.4), (1000, 0.4), (1140, 1)):
        k = kick if lean > 0 else -kick
        d.fill(capsule(x0, 420, x0 + lean * 70 + k, 700, 48))
        d.fill(circle(x0 + lean * 70 + k, 720, 60))
    hx, hy = 1470, 280
    d.fill(circle(hx, hy, 195), ellipse(hx, hy + 40, 225, 140))
    d.fill([(hx - 150, hy - 100), (hx - 120, hy - 280), (hx - 20, hy - 180)])  # ters kulaklar
    d.fill([(hx + 30, hy - 185), (hx + 130, hy - 280), (hx + 155, hy - 100)])
    for ex in (hx - 75, hx + 75):
        d.hole(ellipse(ex, hy - 5, 26, 34))
    d.hole([(hx - 18, hy + 35), (hx + 18, hy + 35), (hx, hy + 57)])
    d.fill(_tail((440, 260), 200, -6, n=7))
    return d


def walker(cx: float, step: float, facing_right: bool) -> Drawing:
    """Ayakta yürüyen kedi. step: -1..1 bacak salınımı."""
    d = Drawing()
    d.fill(ellipse(cx, 430, 380, 165))
    for lx, phase in ((cx + 250, 1), (cx + 170, -1), (cx - 220, -1), (cx - 300, 1)):
        foot = lx + 70 * step * phase
        d.fill(capsule(lx, 400, foot, 70, 45), ellipse(foot + 20, 45, 70, 35))
    hx, hy = cx + 420, 600
    d.fill(circle(hx, hy, 165), ellipse(hx, hy - 40, 190, 120))
    d.fill([(hx - 130, hy + 85), (hx - 100, hy + 235), (hx - 25, hy + 155)])
    d.fill([(hx + 25, hy + 160), (hx + 105, hy + 235), (hx + 130, hy + 85)])
    for ex in (hx - 60, hx + 60):
        d.hole(ellipse(ex, hy + 10, 22, 30))
    d.fill(_tail((cx - 350, 500), 140, 8 + 4 * step, n=7, seg=50, r=38))
    return d if facing_right else d.mirrored(cx)


# --- Animasyon klipleri (her biri 10 kare, saniyede 1 kare) ---

def clip_tail() -> list[Drawing]:
    frames = []
    for f in range(10):
        wag = 9 * math.sin(2 * math.pi * f / 10)
        frames.append(loaf("closed" if f == 7 else "open", wag=wag))
    return frames


def clip_breathe() -> list[Drawing]:
    frames = []
    for f in range(10):
        b = 18 * math.sin(2 * math.pi * f / 10)
        d = loaf("closed", breath=b, head_dy=-45 + b / 2, wag=-4)
        if f >= 3:
            d.fill(zee(1680, 640 + (f - 3) * 30, 80))
        if f >= 6:
            d.fill(zee(1830, 760 + (f - 6) * 30, 55, 32))
        frames.append(d)
    return frames


def clip_walk() -> list[Drawing]:
    frames = []
    for f in range(10):
        step = 1 if f % 2 == 0 else -1
        if f < 5:
            frames.append(walker(640 + f * 162, step, True))
        else:
            frames.append(walker(1288 - (f - 5) * 162, step, False))
    return frames


def clip_roll() -> list[Drawing]:
    seq = []
    for f in range(10):
        if f in (0, 9):
            seq.append(loaf("open"))
        elif f in (1, 8):
            seq.append(flat("half"))
        else:
            seq.append(on_back(kick=60 * math.sin(math.pi * f / 2)))
    return seq


CLIPS = {
    "tail": ("Kuyruk sallama", clip_tail),
    "breathe": ("Uykuda nefes", clip_breathe),
    "walk": ("Yürüyüş", clip_walk),
    "roll": ("Yuvarlanma", clip_roll),
}

# Ruh hali pozları: harf -> çizim
POSES = {
    "a": ("Uyanık", lambda: loaf("open")),
    "s": ("Uykulu", lambda: loaf("half", head_dy=-25)),
    "z": ("Uyuyor", lambda: loaf("closed", head_dy=-50).fill(zee(1680, 650, 80), zee(1830, 790, 55, 32))),
    "t": ("Yorgun", lambda: flat("closed")),
    "p": ("Oyuncu", lambda: on_back()),
}
