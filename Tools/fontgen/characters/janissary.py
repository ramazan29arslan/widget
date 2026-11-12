"""Atlı Yeniçeri: at üzerinde, börklü, kılıçlı / sancaklı.

Siluet ağırlıklı karakalem: beyaz dolgu, ince oyuk çizgilerle ayrıntı.
"""
from __future__ import annotations

import math

from sketch import Drawing, catmull, circle, curve_stroke, ellipse, hatch_along, index_range, stroke, taper

ID = "janissary"
NAME = "Atlı Yeniçeri"

GROUND = 30
SCALE = 0.62  # at + süvari tuvale sığsın diye


def _ik(hip, foot, l1, l2, bend):
    hx, hy = hip
    dx, dy = foot[0] - hx, foot[1] - hy
    dist = max(1.0, min(math.hypot(dx, dy), l1 + l2 - 1))
    base = math.atan2(dy, dx)
    a = math.acos(max(-1, min(1, (l1 * l1 + dist * dist - l2 * l2) / (2 * l1 * dist))))
    ang = base + bend * a
    knee = (hx + l1 * math.cos(ang), hy + l1 * math.sin(ang))
    return knee, (hx + dist * math.cos(base), hy + dist * math.sin(base))


def framed(d: Drawing, contours, gap=14):
    """Şekli, çevresine ince siyah boşluk bırakarak çiz (öndeki parçayı arkadakinden ayırır)."""
    for c in contours:
        d.cut(stroke(c + c[:2], gap * 2, gap * 2, cap=False))
    d.fill(*contours)


# ----------------------------------------------------------------- at

def horse(cx: float, gait: str = "stand", phase: float = 0.0, head_drop: float = 0.0,
          rear: float = 0.0, tail_swish: float = 0.0, seed: int = 21) -> tuple[Drawing, dict]:
    """Sağa bakan at. Döndürür: (çizim, bağlantı noktaları {'saddle': (x,y), 'pitch': açı})."""
    d = Drawing()
    gallop = gait == "gallop"
    bob = (35 * math.sin(2 * math.pi * phase) if gallop else 10 * math.sin(4 * math.pi * phase))
    by = 470 + bob
    # Gövde (fıçı)
    body = catmull([(cx - 400, by + 60), (cx - 330, by + 165), (cx - 120, by + 150), (cx + 120, by + 160),
                    (cx + 300, by + 190), (cx + 370, by + 80), (cx + 330, by - 60), (cx + 150, by - 120),
                    (cx - 120, by - 115), (cx - 330, by - 70)], True, 10)
    # Bacak ayarları
    if gait == "walk":
        offs = {"lh": 0.0, "lf": 0.25, "rh": 0.5, "rf": 0.75}
        stride, lift = 150, 70
    elif gallop:
        offs = {"lh": 0.0, "rh": 0.1, "lf": 0.45, "rf": 0.55}
        stride, lift = 300, 170
    else:
        offs = {"lh": 0.0, "rh": 0.0, "lf": 0.0, "rf": 0.0}
        stride, lift = 0, 0
    legs = {}
    for key, hip_x, back in (("lh", cx - 260, True), ("rh", cx - 200, True),
                             ("lf", cx + 240, False), ("rf", cx + 300, False)):
        a = 2 * math.pi * (phase + offs[key])
        fx = hip_x + (stride * (0.65 if back and gallop else 1) * math.sin(a) if stride else (-30 if back else 20) * (1 if key[0] == "l" else -1))
        fy = GROUND + lift * max(0.0, math.cos(a))
        if gallop and key in ("lf", "rf") and math.cos(a) > 0.3:
            fx += 90  # ön bacaklar ileri uzanır
        hip = (hip_x, by - 40)
        l1, l2 = (240, 230) if back else (230, 225)
        knee, foot = _ik(hip, (fx, fy), l1, l2, -1 if back else 1)
        legs[key] = (hip, knee, foot, back)

    def leg(d, key, near):
        hip, knee, foot, back = legs[key]
        w_top = 150 if back else 110
        pts = [(hip[0], hip[1] + 80), knee, foot]
        if near:
            d.cut(curve_stroke([(hip[0] - 70, hip[1] + 40), (knee[0] - 40, knee[1]), (foot[0] - 28, foot[1] + 20)],
                               14, 8))
        d.fill(curve_stroke(pts, w_top, 48))
        d.fill(catmull([(foot[0] - 34, foot[1] + 30), (foot[0] + 38, foot[1] + 30), (foot[0] + 48, foot[1] - 10),
                        (foot[0] - 40, foot[1] - 10)], True, 4))  # toynak
        d.cut(curve_stroke([(foot[0] - 36, foot[1] + 26), (foot[0] + 40, foot[1] + 26)], 7, 7))

    leg(d, "rh", False)
    leg(d, "rf", False)
    # Kuyruk
    sw = tail_swish + (0.5 if gallop else 0.0)
    tail = [(cx - 395, by + 110), (cx - 470 - 80 * sw, by + 40 - 30 * sw),
            (cx - 520 - 160 * sw, by - 120 + 60 * sw), (cx - 510 - 220 * sw, by - 280 + 150 * sw)]
    d.fill(curve_stroke(tail, 70, 110, profile=lambda t: 1 - 0.3 * t))
    for k in range(4):
        d.cut(curve_stroke([(p[0] + 18 * (k - 1.5), p[1] - 10 * k) for p in tail[1:]], 5, 2, profile=taper))
    d.fill(body)
    d.cut(hatch_along(body, index_range(body, 0.0, 0.10, 1), 50, 6, seed, density=2))
    d.cut(hatch_along(body, index_range(body, 0.55, 0.95, 2), 45, 5, seed + 1))
    # Boyun ve baş
    hd = head_drop
    poll = (cx + 540 - 30 * hd, by + 360 - 400 * hd + (30 if gallop else 0))
    neck = catmull([(cx + 130, by + 150), (cx + 330, by + 300 - 110 * hd), (poll[0] - 70, poll[1] + 10),
                    (poll[0] + 70, poll[1] - 70), (cx + 500 - 20 * hd, by + 130 - 170 * hd), (cx + 400, by - 70),
                    (cx + 300, by - 100)], True, 8)
    d.fill(neck)
    ang = -0.95 - 0.6 * hd + (0.25 if gallop else 0)
    mx, my = poll[0] + 270 * math.cos(ang), poll[1] + 270 * math.sin(ang)
    nx, ny = -math.sin(ang), math.cos(ang)
    head = catmull([(poll[0] - 30 * nx, poll[1] - 30 * ny + 20), (poll[0] + 70 * nx, poll[1] + 70 * ny),
                    ((poll[0] + mx) / 2 + 72 * nx, (poll[1] + my) / 2 + 72 * ny), (mx + 58 * nx, my + 58 * ny),
                    (mx + 30 * math.cos(ang), my + 30 * math.sin(ang)), (mx - 60 * nx, my - 60 * ny),
                    ((poll[0] + mx) / 2 - 95 * nx, (poll[1] + my) / 2 - 95 * ny)], True, 8)
    d.fill(head)
    # kulaklar
    for k, (ex, ey) in enumerate(((poll[0] - 10, poll[1] + 20), (poll[0] + 25, poll[1] + 10))):
        d.fill(catmull([(ex - 25, ey), (ex + 5 - 30 * k, ey + 120), (ex + 35, ey)], True, 5))
    # göz, burun deliği, ağız, dizgin
    ex, ey = poll[0] + 90 * math.cos(ang) + 25 * nx, poll[1] + 90 * math.sin(ang) + 25 * ny
    d.cut(ellipse(ex, ey, 22, 15, ang))
    d.cut(ellipse(mx + 12 * nx, my + 12 * ny, 15, 10, ang))
    d.cut(curve_stroke([(mx - 50 * nx - 10 * math.cos(ang), my - 50 * ny - 10 * math.sin(ang)),
                        (mx - 20 * nx - 50 * math.cos(ang), my - 20 * ny - 50 * math.sin(ang))], 6, 3))
    # Yele
    mane_pts = catmull([(poll[0] - 30, poll[1] + 10), (cx + 400, by + 290 - 100 * hd), (cx + 270, by + 170)], False, 6)
    for i, (px, py) in enumerate(mane_pts[:-1]):
        flow = -1.0 if gallop else -0.6
        d.fill(curve_stroke([(px, py), (px - 70, py + 30 * flow), (px - 120, py - 20 + 40 * flow)], 34, 6))
    d.cut(curve_stroke([(poll[0] + 10, poll[1] - 40), (cx + 420, by + 240 - 90 * hd), (cx + 300, by + 100)], 7, 3,
                       profile=taper))
    # Eyer örtüsü
    saddle = (cx - 20, by + 165)
    cloth = catmull([(cx - 210, by + 150), (cx + 150, by + 155), (cx + 160, by - 20), (cx + 20, by - 60),
                     (cx - 190, by - 25)], True, 6)
    d.cut(stroke(cloth + cloth[:2], 16, 16, cap=False))
    for k in range(3):  # örtü süsleri
        d.cut(curve_stroke([(cx - 180 + 40 * k, by - 15 + 15 * k), (cx + 130 - 15 * k, by - 5 + 15 * k)], 6, 6))
    # Dizgin
    d.cut(curve_stroke([(mx - 30 * nx, my - 30 * ny), (cx + 330, by + 330 - 80 * hd), (saddle[0] + 140, saddle[1] + 150)],
                       7, 7, cap=False))
    leg(d, "lh", True)
    leg(d, "lf", True)
    pitch = 0.0
    if rear:
        pitch = 0.55 * rear
        d = d.transformed(rot=pitch, ox=cx - 230, oy=GROUND, dy=0)
        # arka bacaklar zemine dayalı kalsın diye yaklaşık
    s = saddle
    if pitch:
        c, sn = math.cos(pitch), math.sin(pitch)
        s = ((s[0] - (cx - 230)) * c - (s[1] - GROUND) * sn + cx - 230, (s[0] - (cx - 230)) * sn + (s[1] - GROUND) * c + GROUND)
    return d, {"saddle": s, "pitch": pitch, "rein": (cx + 330, by + 330 - 80 * hd)}


# ----------------------------------------------------------------- süvari

def rider(saddle, pitch=0.0, arm: str = "rein", swing: float = 0.0, flag_wave: float = 0.0,
          slump: float = 0.0, seed: int = 31) -> Drawing:
    """Yeniçeri. arm: 'rein' (dizgin), 'sword' (kılıç, swing -1 geri..1 ileri), 'flag' (sancak)."""
    d = Drawing()
    sx, sy = saddle
    lean = pitch * 0.6 - 0.08 + 0.35 * slump
    up = (-math.sin(lean), math.cos(lean))
    fw = (math.cos(lean), math.sin(lean))

    def P(a, b):  # gövde koordinatı: a ileri, b yukarı
        return (sx + fw[0] * a + up[0] * b, sy + fw[1] * a + up[1] * b)

    # bacak (at gövdesinin önünde)
    leg_c = curve_stroke([P(-20, 30), (sx + 110, sy - 90), (sx + 70, sy - 260)], 95, 60)
    boot = catmull([(sx + 30, sy - 230), (sx + 120, sy - 250), (sx + 140, sy - 300), (sx + 30, sy - 300)], True, 4)
    framed(d, leg_c + [boot], 12)
    d.cut(curve_stroke([(sx + 40, sy - 245), (sx + 125, sy - 255)], 6, 6))  # çizme konçu
    # gövde: kaftan
    torso = catmull([P(-95, 0), P(-110, 150), P(-80, 280), P(70, 290), P(95, 140), P(85, 0)], True, 8)
    skirt = catmull([P(-100, 40), P(-180, -70), P(-90, -120), P(60, -60), P(90, 40)], True, 6)
    framed(d, [skirt, torso], 14)
    d.cut(curve_stroke([P(-100, 120), P(0, 105), P(95, 125)], 14, 14))  # kuşak
    d.cut(curve_stroke([P(20, 280), P(10, 150), P(-5, 30)], 6, 3, profile=taper))  # kaftan yakası
    # baş
    hx, hy = P(0, 360)
    face = catmull([(hx - 60, hy - 50), (hx + 70, hy - 55), (hx + 85, hy + 25), (hx + 40, hy + 80), (hx - 60, hy + 70)],
                   True, 6)
    framed(d, [face], 12)
    d.cut(circle(hx + 50, hy + 20, 9))  # göz
    d.cut(curve_stroke([(hx + 25, hy - 18), (hx + 70, hy - 10), (hx + 105, hy - 32)], 11, 4, profile=taper))  # bıyık
    # börk: uzun beyaz keçe külah, arkaya sarkan yatırma
    hat_base_l, hat_base_r = (hx - 75, hy + 60), (hx + 75, hy + 65)
    tilt = 0.3 + 0.2 * slump                  # arkaya yatık
    top = (hx - 20 - 250 * math.sin(tilt), hy + 70 + 250 * math.cos(tilt))
    hat = catmull([hat_base_l, (hx - 95, hy + 140), (top[0] - 50, top[1] - 10), (top[0] + 10, top[1] + 25),
                   (top[0] + 55, top[1] - 25), (hx + 75, hy + 150), hat_base_r], True, 6)
    flap = curve_stroke([(top[0] + 5, top[1] - 10), (top[0] - 90, top[1] - 90), (hx - 175, hy + 40),
                         (hx - 160, hy - 120)], 62, 40)
    band = catmull([(hx - 85, hy + 50), (hx + 85, hy + 55), (hx + 85, hy + 90), (hx - 85, hy + 85)], True, 4)
    framed(d, flap, 10)
    framed(d, [hat], 10)
    framed(d, [band], 8)
    d.cut(catmull([(hx - 10, hy + 92), (hx + 20, hy + 92), (hx + 30, hy + 190), (hx, hy + 200)], True, 4))  # kaşıklık
    d.fill(catmull([(hx - 2, hy + 105), (hx + 15, hy + 105), (hx + 20, hy + 180), (hx + 4, hy + 185)], True, 4))
    # kol + silah
    sh = P(40, 250)
    if arm == "sword":
        a = 1.9 - 1.6 * (swing + 1) / 2        # geri yukarıdan öne aşağı
        el = (sh[0] + 140 * math.cos(a + 0.4), sh[1] + 140 * math.sin(a + 0.4))
        hand = (el[0] + 130 * math.cos(a), el[1] + 130 * math.sin(a))
        framed(d, curve_stroke([sh, el, hand], 60, 45), 10)
        blade = [(hand[0] + k * 50 * math.cos(a) - 0.0025 * (k * 50) ** 2 * math.sin(a),
                  hand[1] + k * 50 * math.sin(a) + 0.0025 * (k * 50) ** 2 * math.cos(a)) for k in range(0, 9)]
        framed(d, stroke(catmull(blade, False, 3), 34, 8), 8)
        d.fill(curve_stroke([(hand[0] - 40 * math.sin(a), hand[1] + 40 * math.cos(a)),
                             (hand[0] + 40 * math.sin(a), hand[1] - 40 * math.cos(a))], 18, 18))  # balçak
    elif arm == "flag":
        hand = (sh[0] + 170, sh[1] - 40)
        framed(d, curve_stroke([sh, (sh[0] + 110, sh[1] - 90), hand], 60, 45), 10)
        pole_top = (hand[0] - 90, sy + 900)
        pole_bot = (hand[0] + 30, hand[1] - 200)
        framed(d, stroke([pole_bot, pole_top], 22, 18), 8)
        w = flag_wave
        fl = [(pole_top[0] - 5, pole_top[1] - 10)]
        top_edge = [(pole_top[0] - 5 - 80 * k, pole_top[1] - 10 + 30 * math.sin(w + k)) for k in range(1, 6)]
        tail_pt = (pole_top[0] - 470, pole_top[1] - 110 + 20 * math.sin(w + 5))
        bot_edge = [(pole_top[0] - 5 - 80 * k, pole_top[1] - 230 + 30 * math.sin(w + k + 0.6)) for k in range(5, 0, -1)]
        flag = catmull(fl + top_edge + [tail_pt, (pole_top[0] - 330, pole_top[1] - 135)] + bot_edge +
                       [(pole_top[0] - 5, pole_top[1] - 230)], True, 4)
        framed(d, [flag], 8)
        # hilal
        mx_, my_ = pole_top[0] - 190, pole_top[1] - 115 + 25 * math.sin(w + 2.5)
        d.cut(circle(mx_, my_, 55))
        d.fill(circle(mx_ + 22, my_ + 6, 46))
        d.fill(pole_top and circle(pole_top[0], pole_top[1] + 10, 18))
    else:  # dizgin
        hand = (sh[0] + 190, sh[1] - 130)
        framed(d, curve_stroke([sh, (sh[0] + 90, sh[1] - 120), hand], 58, 45), 10)
    return d


def scene(cx, gait="stand", phase=0.0, arm="rein", swing=0.0, flag_wave=0.0, head_drop=0.0,
          rear=0.0, slump=0.0, tail_swish=0.0, zzz=False) -> Drawing:
    h, joints = horse(cx, gait, phase, head_drop, rear, tail_swish)
    d = Drawing().merge(h)
    d.merge(rider(joints["saddle"], joints["pitch"], arm, swing, flag_wave, slump))
    if zzz:
        sx, sy = joints["saddle"]
        for k in range(3):
            s = 60 + 20 * k
            x, y = sx + 160 + 110 * k, sy + 520 + 90 * k
            d.fill(curve_stroke([(x, y + s), (x + s, y + s), (x, y), (x + s, y)], s * 0.22, s * 0.22, steps=1))
    return d.transformed(s=SCALE, ox=cx, oy=GROUND)


# ----------------------------------------------------------------- klipler

def clip_guard():
    """Nöbet: at yerinde, kuyruk ve sancak dalgalanır, at başını sallar."""
    return [scene(1000, "stand", arm="flag", flag_wave=f * 0.63, head_drop=0.12 * (1 + math.sin(f * 0.63)) / 2,
                  tail_swish=0.4 * math.sin(f * 1.26)) for f in range(10)]


def clip_march():
    """Panorama: sancakla sefere çıkış, soldan sağa yürüyüş."""
    return [scene(150 + f * 420, "walk", phase=f * 0.5, arm="flag", flag_wave=f * 0.9) for f in range(10)]


def clip_charge():
    """Panorama: kılıç kalkık, dörtnala hücum."""
    return [scene(-150 + f * 470, "gallop", phase=f * 0.5, arm="sword", swing=0.25 + 0.15 * math.sin(f * 3))
            for f in range(10)]


def clip_battle():
    """Savaş: kılıç savurma ve şaha kalkma."""
    seq = []
    rear_curve = [0, 0, 0, 0.3, 0.8, 1.0, 0.8, 0.3, 0, 0]
    swings = [-1, -0.3, 0.6, 1.0, -1, -0.6, 0.4, 1.0, -0.2, -0.8]
    for f in range(10):
        seq.append(scene(1000, "stand", arm="sword", swing=swings[f], rear=rear_curve[f],
                         tail_swish=0.5 * math.sin(f), head_drop=-0.1 * rear_curve[f]))
    return seq


CLIPS = {
    "guard": ("Nöbet", clip_guard, False),
    "battle": ("Savaş", clip_battle, False),
    "march": ("Sefere gidiş", clip_march, True),
    "charge": ("Hücum", clip_charge, True),
}

MOOD_CLIPS = {"awake": "guard", "sleepy": "guard", "sleeping": "guard", "tired": "guard", "playful": "charge"}

POSES = {
    "a": ("Uyanık", lambda: scene(1000, "stand", arm="flag", flag_wave=1.0)),
    "s": ("Uykulu", lambda: scene(1000, "stand", arm="rein", head_drop=0.5, slump=0.4)),
    "z": ("Uyuyor", lambda: scene(1000, "stand", arm="rein", head_drop=0.8, slump=0.8, zzz=True)),
    "t": ("Yorgun", lambda: scene(1000, "stand", arm="rein", head_drop=0.9, slump=0.6)),
    "p": ("Oyuncu", lambda: scene(1000, "stand", arm="sword", swing=-1, rear=1.0)),
}
