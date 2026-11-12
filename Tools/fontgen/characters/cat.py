"""Kedi: karakalem tarzı, beyaz tüylü, tombul.

Tuval 2000 × 1000 (tek widget) ya da 4000 × 1000 (panorama).
"""
from __future__ import annotations

import math

from sketch import (Drawing, catmull, circle, contour_slice, curve_stroke, ellipse, hatch_along,
                    index_range, stroke, taper, transform)

ID = "cat"
NAME = "Kedi"

# Referans ölçek: başın yarıçapı ~250 birim.


# ----------------------------------------------------------------- baş

def head(cx: float, cy: float, s: float = 1.0, eyes: str = "open", look: float = 0.0,
         tilt: float = 0.0, ears: str = "up", mouth: str = "calm", seed: int = 1) -> Drawing:
    """3/4 önden bakan kedi başı. look: göz bebeği yatay kayma (-1..1)."""
    d = Drawing()
    tf = dict(s=s, rot=tilt, ox=0, oy=0, dx=cx, dy=cy)

    def T(pts):
        if pts and isinstance(pts[0], list):  # şekil listesi
            return [transform(c, **tf) for c in pts]
        return transform(pts, **tf)

    # Kafa: üstte dar, yanaklarda geniş
    skull = catmull([(-150, 170), (0, 205), (150, 175), (230, 60), (245, -40), (190, -130),
                     (60, -185), (-70, -180), (-200, -120), (-250, -20), (-225, 80)], True, 10)
    d.fill(T(skull))
    # Kulaklar
    if ears == "up":
        el = [(-200, 95), (-185, 300), (-60, 185)]
        er = [(80, 195), (195, 300), (215, 75)]
    elif ears == "back":
        el = [(-215, 70), (-300, 200), (-90, 170)]
        er = [(70, 185), (300, 210), (225, 60)]
    else:  # flat (yorgun)
        el = [(-215, 60), (-330, 120), (-110, 150)]
        er = [(80, 170), (320, 140), (230, 50)]
    d.fill(T(catmull(el, True, 6)), T(catmull(er, True, 6)))
    # kulak içi taraması
    for ear, sd in ((el, seed), (er, seed + 7)):
        base = ((ear[0][0] + ear[2][0]) / 2, (ear[0][1] + ear[2][1]) / 2)
        tip = ear[1]
        for k in range(4):
            f = 0.25 + k * 0.13
            sx = base[0] + (ear[0][0] - base[0]) * (0.5 - k * 0.12)
            sy = base[1] + (ear[0][1] - base[1]) * (0.5 - k * 0.12)
            d.cut(T(curve_stroke([(sx, sy + 10), (sx + (tip[0] - sx) * f, sy + (tip[1] - sy) * f),
                                  (sx + (tip[0] - sx) * (f + 0.35), sy + (tip[1] - sy) * (f + 0.35))],
                                 7, 1.5, profile=taper)))
    # Kafa sol kenarı ve kulak çizgisi (vücuttan ayıran kontur)
    d.cut(T(curve_stroke([(-60, 186), (-185, 300), (-200, 95), (-238, 0), (-232, -70), (-200, -120)],
                         12, 6, profile=taper)))
    # Yanak tüyleri (sol, yaka)
    d.cut(hatch_strokes_T(T, [(-225, -90), (-180, -140), (-120, -170), (-60, -182)], 38, 4, seed))

    # Gözler: badem biçimli, parlak noktalı
    for ex, ey, rx, rot in ((-30, 40, 42, 0.25), (120, 46, 39, -0.1)):
        if eyes == "open":
            d.cut(T(ellipse(ex, ey, rx, rx * 0.86, rot)))
            d.fill(T(circle(ex - rx * 0.28 + look * 14, ey + rx * 0.2, rx * 0.2)))
        elif eyes == "half":
            d.cut(T(catmull([(ex - rx, ey - 6), (ex, ey + rx * 0.25), (ex + rx, ey - 2),
                             (ex, ey - rx * 0.42)], True, 8)))
            d.cut(T(curve_stroke([(ex - rx * 1.15, ey + 2), (ex, ey + rx * 0.32), (ex + rx * 1.15, ey + 6)],
                                 8, 4, profile=taper)))
        else:  # kapalı: aşağı bakan yay
            d.cut(T(curve_stroke([(ex - rx * 1.1, ey + 5), (ex - rx * 0.3, ey - rx * 0.45),
                                  (ex + rx * 0.5, ey - rx * 0.4), (ex + rx * 1.15, ey + 8)], 12, 6, profile=taper)))
    # Burun (dolu küçük üçgen) ve ağız
    d.cut(T(catmull([(40, -40), (85, -35), (64, -70)], True, 5)))
    if mouth == "open":
        d.cut(T(ellipse(64, -110, 26, 22)))
    d.cut(T(curve_stroke([(64, -70), (60, -95), (35, -110)], 5, 3)))
    d.cut(T(curve_stroke([(64, -70), (72, -98), (100, -105)], 5, 3)))
    # Bıyık noktaları
    for bx, by in ((10, -88), (0, -105), (115, -85), (125, -100)):
        d.cut(T(circle(bx, by, 4)))
    # Bıyıklar (uzun, ince; kafanın dışına taşar)
    whisk = [
        [(0, -95), (-150, -80), (-330, -60)], [(0, -105), (-160, -110), (-330, -120)],
        [(5, -115), (-140, -140), (-290, -175)],
        [(125, -90), (270, -75), (420, -60)], [(125, -100), (280, -110), (430, -130)],
        [(120, -110), (260, -145), (390, -190)],
    ]
    for w in whisk:
        d.cut(T(curve_stroke(w, 4.5, 1.2)))
    return d


def hatch_strokes_T(T, pts, length, width, seed):
    c = catmull(pts, False, 6)
    return [transform(s, **{}) if T is None else T(s) for s in hatch_along(c, range(1, len(c) - 1), length, width, seed, jitter=0.3,
                                      angle_bias=math.pi)]


# ----------------------------------------------------------------- vücutlar

def loaf(eyes="open", breath=0.0, tail=0.0, head_dy=0.0, look=0.0, tilt=0.0, ears="up",
         x=0.0, seed=3) -> Drawing:
    """Ekmek pozu (referans fotoğraftaki gibi). tail: kuyruk ucu açısı (radyan)."""
    d = Drawing()
    b = breath
    body = catmull([(650 + x, 640 + b), (430 + x, 560 + b * 0.8), (300 + x, 420), (285 + x, 250),
                    (330 + x, 120), (480 + x, 60), (800 + x, 40), (1180 + x, 40), (1420 + x, 70),
                    (1500 + x, 200), (1440 + x, 420), (1200 + x, 600 + b), (950 + x, 660 + b)], True, 12)
    d.fill(body)
    # Kuyruk: arkadan sola uzanan kısa, kalın kuyruk
    tx, ty = 330 + x, 250
    tip = (tx - 240 * math.cos(tail), ty + 40 + 240 * math.sin(tail))
    mid = (tx - 130, ty + 5 + 90 * math.sin(tail))
    tail_c = [(tx + 40, ty - 10), mid, tip]
    d.fill(curve_stroke(tail_c, 115, 62))
    d.cut(curve_stroke([(tx + 30, ty - 62), (mid[0], mid[1] - 52), (tip[0], tip[1] - 30)], 7, 3, profile=taper))
    # Alt kenar gölge taraması (fotoğraftaki yoğun kalem darbeleri)
    d.cut(hatch_along(body, index_range(body, 0.30, 0.62, 1), 55, 6.5, seed, jitter=0.2, angle_bias=-0.35, density=3))
    # Arka üst kenar hafif tarama
    d.cut(hatch_along(body, index_range(body, 0.20, 0.30, 2), 40, 4, seed + 1, jitter=0.3))
    # Arka bacak hatları
    d.cut(curve_stroke([(560 + x, 70), (500 + x, 160), (520 + x, 300), (620 + x, 380)], 7, 2, profile=taper))
    # Ön patiler
    for px in (1150, 1330):
        paw = ellipse(px + x, 70, 120, 48)
        d.fill(paw)
        d.cut(curve_stroke([(px - 118 + x, 95), (px - 110 + x, 40), (px + 30 + x, 24), (px + 112 + x, 50)], 11, 4, profile=taper))
        for k in (-30, 25):
            d.cut(curve_stroke([(px + k + 60 + x, 28), (px + k + 70 + x, 55)], 5, 2))
    # Göğüs yakası taraması
    chest = catmull([(1160 + x, 470), (1120 + x, 330), (1180 + x, 200), (1300 + x, 150)], False, 6)
    d.cut(hatch_along(chest, range(1, len(chest) - 1, 2), 42, 4, seed + 2, jitter=0.35, angle_bias=math.pi))
    # Baş
    d.merge(head(1430 + x, 520 + head_dy + b * 0.5, 1.0, eyes, look, tilt, ears, seed=seed))
    return d


def _ik(hip, foot, l1, l2, bend_dir):
    """İki kemikli bacak: kalçadan ayağa, diz bend_dir (+1/-1) yönünde kırılır."""
    hx, hy = hip
    fx, fy = foot
    dx, dy = fx - hx, fy - hy
    dist = min(math.hypot(dx, dy), l1 + l2 - 1)
    base = math.atan2(dy, dx)
    cos_a = (l1 * l1 + dist * dist - l2 * l2) / (2 * l1 * dist)
    a = math.acos(max(-1, min(1, cos_a)))
    ang = base + bend_dir * a
    knee = (hx + l1 * math.cos(ang), hy + l1 * math.sin(ang))
    real_foot = (hx + dist * math.cos(base), hy + dist * math.sin(base))
    return knee, real_foot


def walker(cx: float, phase: float, run: float = 0.0, facing: int = 1, eyes="open",
           pounce: float = 0.0, seed=5) -> Drawing:
    """Yan görünüş yürüyen/koşan kedi. phase: 0..1 adım döngüsü, run: 0 yürüyüş..1 dörtnala.
    Kedi sağa bakar (facing=1); -1 ise aynalanır. cx: gövde merkezi."""
    d = Drawing()
    L = 440 * (1 + 0.15 * run)
    bob = 22 * math.sin(4 * math.pi * phase) * (0.4 + run)
    by = 470 - 30 * run + bob            # gövde orta çizgisi
    top = by + 200 - 25 * run
    belly = by - 175 + 20 * run
    # Tombul gövde: yuvarlak kalça, dolgun göğüs, sarkık karın
    body = catmull([(cx - L * 1.08, by + 20), (cx - L * 0.95, top - 60), (cx - L * 0.55, top + 5),
                    (cx + L * 0.1, top - 5 + 10 * run), (cx + L * 0.6, top + 10), (cx + L * 0.98, by + 110),
                    (cx + L * 1.0, by - 60), (cx + L * 0.7, belly + 10), (cx + L * 0.1, belly - 15),
                    (cx - L * 0.55, belly + 5), (cx - L * 0.98, by - 110)], True, 12)
    stride = 190 + 140 * run
    legs = []
    for hip_x, off, back in ((cx - L * 0.62, 0.0, True), (cx - L * 0.48, 0.5 if run < 0.5 else 0.12, True),
                             (cx + L * 0.6, 0.5, False), (cx + L * 0.75, 0.0 if run < 0.5 else 0.62, False)):
        a = 2 * math.pi * (phase + off)
        fx = hip_x + stride * math.sin(a) * (1 if back else 1.1)
        fy = 35 + (70 + 120 * run) * max(0.0, math.cos(a))
        hip = (hip_x, by - 60)
        l1, l2 = (200, 200) if back else (185, 185)
        knee, foot = _ik(hip, (fx, fy), l1, l2, -1 if back else 1)
        legs.append((hip, knee, foot, back))
    for i in (1, 3):  # uzak bacaklar
        hip, knee, foot, back = legs[i]
        d.fill(curve_stroke([(hip[0], hip[1] + 40), knee, foot], 150 if back else 110, 75))
        d.fill(ellipse(foot[0] + 28, foot[1] + 6, 58, 30))
        d.cut(curve_stroke([(hip[0] - 55, hip[1] - 30), (knee[0] - 30, knee[1]), (foot[0] - 25, foot[1] + 10)], 8, 4,
                           profile=taper))
    d.fill(body)
    d.cut(hatch_along(body, index_range(body, 0.62, 0.98, 1), 55, 6.5, seed, jitter=0.25, angle_bias=-0.3, density=3))
    for i in (0, 2):  # yakın bacaklar
        hip, knee, foot, back = legs[i]
        d.cut(curve_stroke([(hip[0] - 70, hip[1] + 40), (knee[0] - 50, knee[1]), (foot[0] - 35, foot[1] + 8)], 10, 5,
                           profile=taper))
        d.fill(curve_stroke([(hip[0], hip[1] + 70), knee, foot], 190 if back else 125, 80))
        d.fill(ellipse(foot[0] + 28, foot[1] + 6, 62, 32))
        d.cut(curve_stroke([(foot[0] - 30, foot[1] - 22), (foot[0] + 45, foot[1] - 25), (foot[0] + 88, foot[1] + 4)], 7, 3,
                           profile=taper))
    if True:  # arka bacak kalça hattı
        d.cut(curve_stroke([(cx - L * 0.35, by + 60), (cx - L * 0.55, by - 30), (cx - L * 0.45, belly + 15)], 9, 3,
                           profile=taper))
    # Kuyruk: yukarı kıvrık, koşarken arkaya uzanır
    tb = (cx - L * 1.0, by + 70)
    wave = math.sin(2 * math.pi * phase) * 50
    tail = [tb, (tb[0] - 150, tb[1] + 110 - 90 * run + wave * 0.5),
            (tb[0] - 230 - 140 * run, tb[1] + 300 - 220 * run + wave),
            (tb[0] - 190 - 240 * run, tb[1] + 430 - 330 * run + wave)]
    d.fill(curve_stroke(tail, 95, 55))
    d.cut(curve_stroke([(p[0] + 28, p[1] - 28) for p in tail[1:]], 6, 2, profile=taper))
    # Baş
    hx = cx + L * 0.98
    d.merge(head(hx, by + 200 - 50 * run, 0.85, eyes, look=0.8, tilt=-0.1 * run,
                 ears="back" if run > 0.6 else "up", seed=seed))
    if pounce:
        d = d.transformed(rot=0.22 * pounce, ox=cx - L, oy=40, dy=40 * pounce)
    d = d.transformed(s=0.8, ox=cx, oy=30)
    if facing < 0:
        d = d.transformed(flip=True, ox=cx)
    return d


def on_back(kick=0.0, paw_up=0.0, eyes="open", seed=9) -> Drawing:
    """Sırtüstü yuvarlanan kedi, patileri havada."""
    d = Drawing()
    body = catmull([(420, 300), (520, 110), (900, 50), (1250, 80), (1420, 220), (1380, 420),
                    (1150, 520), (800, 540), (520, 470)], True, 12)
    for i, (x0, base_ang) in enumerate(((620, 2.1), (760, 1.9), (1080, 1.4), (1230, 1.2))):
        k = kick * (1 if i % 2 else -1) + paw_up * (i >= 2)
        a = base_ang + 0.25 * k
        kx, ky = x0 + 150 * math.cos(a), 460 + 150 * math.sin(a)
        fx, fy = kx + 120 * math.cos(a - 1.1), ky + 120 * math.sin(a - 1.1)
        d.fill(curve_stroke([(x0, 430), (kx, ky), (fx, fy)], 130, 85))
        d.fill(circle(fx, fy, 55))
        d.cut(curve_stroke([(fx - 40, fy + 20), (fx, fy + 45), (fx + 40, fy + 22)], 6, 3))
    d.fill(body)
    d.cut(hatch_along(body, index_range(body, 0.05, 0.40, 1), 65, 6, seed, density=2))
    d.cut(curve_stroke([(600, 470), (850, 500), (1100, 470)], 7, 3, profile=taper))  # karın çizgisi
    tail = [(440, 260), (300, 200), (200, 260), (160, 380)]
    d.fill(curve_stroke(tail, 80, 50))
    d.merge(head(1500, 330, 0.9, eyes, look=-0.5, tilt=2.6, seed=seed))
    return d


def curled(breath=0.0, seed=11) -> Drawing:
    """Top gibi kıvrılmış uyuyan kedi."""
    d = Drawing()
    b = breath
    body = catmull([(450, 120), (500, 420 + b), (800, 600 + b), (1150, 580 + b), (1450, 380 + b * 0.5),
                    (1500, 160), (1300, 50), (700, 45)], True, 12)
    d.fill(body)
    d.cut(hatch_along(body, index_range(body, 0.55, 0.98, 1), 70, 7, seed, density=2))
    d.cut(curve_stroke([(650, 330 + b), (850, 470 + b), (1150, 450 + b), (1300, 330)], 8, 3, profile=taper))
    # Kuyruk gövdenin önünden dolanır
    tail = catmull([(1450, 150), (1200, 90), (800, 95), (560, 160)], False, 8)
    d.cut(stroke(tail, 14, 6))
    d.fill(stroke(tail, 95, 60))
    d.cut(stroke([(p[0], p[1] - 40) for p in tail[1:]], 6, 2))
    # Baş kuyruğa gömülü
    d.merge(head(1200, 300 + b * 0.4, 0.82, "closed", tilt=-0.3, ears="up", seed=seed))
    return d


def flat(eyes="half", seed=13) -> Drawing:
    """Yere serilmiş, yorgun kedi."""
    d = Drawing()
    body = catmull([(250, 80), (330, 240), (700, 300), (1150, 280), (1400, 200), (1420, 90), (1000, 40),
                    (500, 40)], True, 12)
    d.fill(body)
    d.cut(hatch_along(body, index_range(body, 0.0, 0.25, 1), 60, 6, seed, density=2))
    d.fill(ellipse(1430, 60, 150, 45), ellipse(1250, 50, 140, 40))
    tail = [(260, 110), (120, 70), (-20, 60)]
    d.fill(curve_stroke(tail, 75, 50))
    d.merge(head(1550, 250, 0.85, eyes, tilt=-0.25, ears="flat", seed=seed))
    return d


# ----------------------------------------------------------------- aksesuarlar

def yarn(cx: float, cy: float, r: float, rot: float, trail: list | None = None) -> Drawing:
    """İp yumağı: dolu top, üzerinde sarım çizgileri, arkasında ip."""
    d = Drawing()
    if trail:
        d.fill(curve_stroke(trail + [(cx, cy - r * 0.6)], 10, 10))
    d.fill(circle(cx, cy, r, 40))
    for k in range(6):
        a = rot + k * math.pi / 6
        pts = [(cx + r * 0.95 * math.cos(a + t) * math.cos(t * 0.3), cy + r * 0.95 * math.sin(a + t) * 0.45 + r * 0.25 * math.sin(t))
               for t in (-1.3, -0.6, 0, 0.6, 1.3)]
        d.cut(curve_stroke(pts, 7, 7, cap=False))
    return d


def mouse(cx: float, phase: float, facing: int = 1, scale: float = 1.0) -> Drawing:
    """Koşan küçük fare."""
    d = Drawing()
    s = scale
    hop = 25 * abs(math.sin(2 * math.pi * phase))
    by = 90 * s + hop
    body = ellipse(cx, by, 120 * s, 70 * s, 0.05)
    d.fill(body)
    d.fill(catmull([(cx + 80 * s, by + 40 * s), (cx + 200 * s, by - 5 * s), (cx + 90 * s, by - 50 * s)], True, 6))
    d.fill(circle(cx + 60 * s, by + 70 * s, 42 * s))  # kulak
    d.cut(circle(cx + 60 * s, by + 70 * s, 22 * s))
    d.cut(circle(cx + 120 * s, by + 20 * s, 11 * s))  # göz
    d.fill(circle(cx + 116 * s, by + 24 * s, 4 * s))
    for k, off in ((0, 0), (1, 0.5)):
        a = math.sin(2 * math.pi * (phase + off)) * 0.6
        d.fill(curve_stroke([(cx - 40 * s + 70 * s * k, by - 40 * s), (cx - 40 * s + 70 * s * k + 50 * s * math.sin(a), 18 * s)], 20 * s, 14 * s))
    tail = [(cx - 115 * s, by), (cx - 220 * s, by + 50 * s + 30 * math.sin(6 * phase)), (cx - 330 * s, by + 10 * s), (cx - 420 * s, by + 60 * s)]
    d.fill(curve_stroke(tail, 14 * s, 5 * s))
    for w in ((cx + 190 * s, by - 2 * s, cx + 270 * s, by + 25 * s), (cx + 190 * s, by - 8 * s, cx + 275 * s, by - 30 * s)):
        d.fill(curve_stroke([(w[0], w[1]), (w[2], w[3])], 4, 2))
    if facing < 0:
        d = d.transformed(flip=True, ox=cx)
    return d


# ----------------------------------------------------------------- klipler

def clip_tail():
    return [loaf("closed" if f == 6 else "open", tail=0.55 * math.sin(2 * math.pi * f / 10),
                 look=(-1 if f in (2, 3) else 1 if f in (7, 8) else 0)) for f in range(10)]


def clip_breathe():
    frames = []
    for f in range(10):
        b = 22 * math.sin(2 * math.pi * f / 10)
        d = curled(breath=b)
        for k in range(min(f // 3, 3)):
            z = 0.6 + 0.25 * k
            d.fill(zee(1500 + k * 120, 620 + k * 110 + (f % 3) * 15, 70 * z))
        frames.append(d)
    return frames


def zee(x, y, size):
    s = size
    return curve_stroke([(x, y + s), (x + s, y + s), (x, y), (x + s, y)], s * 0.22, s * 0.22, steps=1)


def clip_roll():
    seq = []
    for f in range(10):
        if f in (0, 9):
            seq.append(loaf("open", tail=0.2))
        elif f in (1, 8):
            seq.append(flat("open"))
        else:
            seq.append(on_back(kick=math.sin(math.pi * f / 2), paw_up=0.5 * math.sin(math.pi * f / 3)))
    return seq


STAGE = 4000  # panorama tuvali (iki dikdörtgen widget yan yana)


def clip_walk():
    """Panorama: kedi soldan sağa yürür, sağdan geri döner."""
    frames = []
    for f in range(10):
        if f < 5:
            frames.append(walker(700 + f * 650, (f % 2) * 0.5, facing=1))
        else:
            frames.append(walker(3300 - (f - 5) * 650, (f % 2) * 0.5, facing=-1))
    return frames


def clip_mouse():
    """Panorama: fare kaçar, kedi koşarak kovalar; sonra fare geri kaçar, kedi şaşırır."""
    frames = []
    for f in range(10):
        d = Drawing()
        if f <= 5:
            mx = 1500 + f * 520
            cxp = 300 + f * 560
            d.merge(walker(cxp, (f % 2) * 0.5, run=1.0, facing=1))
            if mx < 4200:
                d.merge(mouse(mx, f * 0.5, 1))
        elif f == 6:
            d.merge(walker(3100, 0.0, run=0.0, pounce=1.0, facing=1))  # zıplama, ıskalama
            d.merge(mouse(1900, 0.0, -1))
        elif f == 7:
            d.merge(loaf("open", x=1900, look=-1, tilt=0.1))
            d.merge(mouse(900, 0.5, -1))
        else:
            d.merge(loaf("open", x=1900, look=-1, tilt=0.15 if f == 8 else -0.05))
            d.merge(mouse(200 - (f - 8) * 300, f * 0.5, -1))
        frames.append(d)
    return frames


def clip_yarn():
    """Panorama: yumak yuvarlanır, kedi peşinden koşar ve patiyle vurur."""
    frames = []
    for f in range(10):
        d = Drawing()
        if f < 7:
            bx = 1300 + f * 420
            d.merge(yarn(bx, 115 + 30 * abs(math.sin(f)), 110, f * 0.9,
                         trail=[(bx - 700, 18), (bx - 380, 40), (bx - 160, 25)]))
            d.merge(walker(400 + f * 400, (f % 2) * 0.5, run=0.6 + 0.06 * f, facing=1,
                           pounce=1.0 if f == 6 else 0.0))
        else:
            # yumağı yakaladı: sırtüstü, patiler yumakta
            d.merge(on_back(kick=math.sin(f), paw_up=1.0).transformed(dx=1700))
            d.merge(yarn(2950 + 30 * math.sin(f * 2), 620 + 40 * math.cos(f * 2), 120, f * 1.3,
                         trail=[(3400, 18), (3200, 120), (3050, 400)]))
        frames.append(d)
    return frames


# Klip kimliği -> (başlık, kare üretici, panorama mı)
CLIPS = {
    "tail": ("Kuyruk sallama", clip_tail, False),
    "breathe": ("Uykuda nefes", clip_breathe, False),
    "roll": ("Yuvarlanma", clip_roll, False),
    "walk": ("Yürüyüş", clip_walk, True),
    "mouse": ("Fare kovalama", clip_mouse, True),
    "yarn": ("Yumak kovalama", clip_yarn, True),
}

# Ruh hali -> "Otomatik" modda oynatılacak klip
MOOD_CLIPS = {"awake": "tail", "sleepy": "breathe", "sleeping": "breathe", "tired": "breathe",
              "playful": "yarn"}

# Ruh hali pozları: harf -> (ad, çizim)
POSES = {
    "a": ("Uyanık", lambda: loaf("open")),
    "s": ("Uykulu", lambda: loaf("half", head_dy=-30, tilt=-0.08)),
    "z": ("Uyuyor", lambda: curled().fill(zee(1520, 640, 70), zee(1660, 760, 50))),
    "t": ("Yorgun", lambda: flat("half")),
    "p": ("Oyuncu", lambda: on_back(kick=0.6, paw_up=0.8)),
}
