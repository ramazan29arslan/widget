"""Köpek: kedinin gövde çizimlerini kullanır, başı ve oyuncağı farklıdır.

cat.py'nin bağımsız bir kopyası yüklenir ve içindeki `head` fonksiyonu köpek başıyla
değiştirilir; böylece yürüme, uyuma, yuvarlanma pozları köpeğe uyarlanır.
"""
from __future__ import annotations

import importlib.util
import math
from pathlib import Path

from sketch import Drawing, catmull, circle, curve_stroke, ellipse, hatch_along, transform

ID = "dog"
NAME = "Köpek"

_spec = importlib.util.spec_from_file_location("_cat_for_dog", Path(__file__).with_name("cat.py"))
base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(base)


def dog_head(cx, cy, s=1.0, eyes="open", look=0.0, tilt=0.0, ears="up", mouth="calm", seed=1) -> Drawing:
    d = Drawing()
    tf = dict(s=s, rot=tilt, ox=0, oy=0, dx=cx, dy=cy)

    def T(pts):
        if pts and isinstance(pts[0], list):
            return [transform(c, **tf) for c in pts]
        return transform(pts, **tf)

    skull = catmull([(-180, 140), (0, 200), (170, 150), (230, 30), (215, -90), (120, -150), (-60, -160),
                     (-200, -100), (-240, 20)], True, 10)
    flop = 0.6 if ears == "back" else 1.0 if ears == "flat" else 0.0

    def ear_shape(side, x0):
        return catmull([(x0 - 40 * side, 150), (x0 + side * (110 + 60 * flop), 120),
                        (x0 + side * (150 + 80 * flop), -80 + 60 * flop), (x0 + side * 80, -150 + 40 * flop),
                        (x0 + side * 10, 40)], True, 8)

    far_ear = ear_shape(1, 150)       # arkadaki kulak: kafanın arkasında kalır
    d.fill(T(far_ear))
    d.cut(T(curve_stroke(far_ear + far_ear[:2], 18, 18, cap=False)))
    d.fill(T(skull))
    snout = catmull([(60, -20), (250, -10), (330, -70), (320, -160), (220, -205), (80, -190)], True, 8)
    d.fill(T(snout))
    d.cut(T(curve_stroke([(70, -15), (40, -100), (90, -185)], 8, 3)))  # yanak çizgisi
    near_ear = ear_shape(-1, -150)    # öndeki kulak
    d.cut(T(curve_stroke(near_ear + near_ear[:2], 26, 26, cap=False)))
    d.fill(T(near_ear))
    d.cut(T(curve_stroke([(-190, 100), (-240, -20), (-220, -100)], 7, 2)))
    # Gözler
    for ex, ey, r in ((-40, 50, 36), (110, 55, 33)):
        if eyes == "open":
            d.cut(T(circle(ex, ey, r)))
            d.fill(T(circle(ex - r * 0.3 + look * 10, ey + r * 0.3, r * 0.25)))
        elif eyes == "half":
            d.cut(T(ellipse(ex, ey - 8, r * 1.05, r * 0.4)))
        else:
            d.cut(T(curve_stroke([(ex - r, ey), (ex, ey - r * 0.5), (ex + r, ey)], 11, 5)))
    # Burun
    d.cut(T(catmull([(250, -40), (335, -50), (330, -105), (270, -110)], True, 6)))
    d.fill(T(circle(285, -60, 9)))
    # Ağız ve dil
    d.cut(T(curve_stroke([(300, -110), (290, -160), (230, -190), (150, -185)], 8, 4)))
    if mouth == "open" or eyes == "open":
        tongue = catmull([(210, -190), (270, -190), (275, -270), (235, -290), (205, -250)], True, 6)
        d.cut(T(curve_stroke(tongue + tongue[:2], 16, 16, cap=False)))
        d.fill(T(tongue))
        d.cut(T(curve_stroke([(240, -200), (240, -255)], 5, 2)))
    # Kaş tüyleri
    for ex in (-40, 110):
        d.cut(T(curve_stroke([(ex - 40, 105), (ex, 118), (ex + 35, 108)], 7, 3)))
    return d


base.head = dog_head


def ball(cx, cy, r, rot):
    d = Drawing()
    d.fill(circle(cx, cy, r, 40))
    for k in (-1, 1):
        pts = [(cx + r * math.cos(rot + k * 0.9 + t) * 0.95, cy + r * math.sin(rot + k * 0.9 + t) * 0.95)
               for t in (-0.9, -0.45, 0, 0.45, 0.9)]
        d.cut(curve_stroke([(cx + (x - cx) * 0.6, cy + (y - cy) * 0.6) if i in (1, 2, 3) else (x, y)
                            for i, (x, y) in enumerate(pts)], 9, 9))
    return d


def clip_fetch():
    """Panorama: top yuvarlanır, köpek koşup yakalar, kuyruk sallar."""
    frames = []
    for f in range(10):
        d = Drawing()
        if f < 7:
            bx = 1500 + f * 380
            d.merge(ball(bx, 100 + 40 * abs(math.sin(f * 1.3)), 85, f))
            d.merge(base.walker(450 + f * 390, (f % 2) * 0.5, run=0.9, facing=1, pounce=1.0 if f == 6 else 0.0))
        else:
            d.merge(base.loaf("open", x=1700, tail=0.6 * math.sin(f * 2.5)))
            d.merge(ball(3350, 100, 85, 0))
        frames.append(d)
    return frames


CLIPS = {
    "tail": ("Kuyruk sallama", lambda: [base.loaf("open", tail=0.7 * math.sin(2 * math.pi * f / 5),
                                                    look=(1 if f in (3, 4) else 0)) for f in range(10)], False),
    "breathe": ("Uykuda nefes", base.clip_breathe, False),
    "roll": ("Yuvarlanma", base.clip_roll, False),
    "walk": ("Yürüyüş", base.clip_walk, True),
    "fetch": ("Top getirme", clip_fetch, True),
}

MOOD_CLIPS = {"awake": "tail", "sleepy": "breathe", "sleeping": "breathe", "tired": "breathe", "playful": "fetch"}

POSES = {k: (title, fn) for k, (title, fn) in base.POSES.items()}
