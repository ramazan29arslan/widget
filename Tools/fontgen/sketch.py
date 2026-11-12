"""Karakalem tarzı vektör çizim motoru.

Kilit ekranı tek renk gösterir: beyaz = dolgu, siyah = oyuk (şeffaf).
Bir çizim, sırayla uygulanan katmanlardan oluşur:
    fill(...)  -> beyaz ekle
    cut(...)   -> siyah çizgi/oyuk (göz, bıyık, tüy taraması)
Sonraki bir fill, önceki cut'ın üzerine yeniden beyaz çizebilir.

Koordinatlar font birimidir, y yukarı doğrudur.
"""
from __future__ import annotations

import math
import random

from pathops import FillType, Path, PathOp, op

Pt = tuple[float, float]


# ---------------------------------------------------------------- geometri

def catmull(points: list[Pt], closed: bool = True, steps: int = 10) -> list[Pt]:
    """Noktalardan geçen yumuşak eğri (Catmull-Rom)."""
    n = len(points)
    if n < 3:
        return list(points)
    out: list[Pt] = []
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        p0 = points[(i - 1) % n] if closed else points[max(i - 1, 0)]
        p1 = points[i]
        p2 = points[(i + 1) % n] if closed else points[i + 1]
        p3 = points[(i + 2) % n] if closed else points[min(i + 2, n - 1)]
        for s in range(steps):
            t = s / steps
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
                       + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
                       + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y))
    if not closed:
        out.append(points[-1])
    return out


def ellipse(cx, cy, rx, ry, rot=0.0, n=48) -> list[Pt]:
    c, s = math.cos(rot), math.sin(rot)
    return [(cx + rx * math.cos(t) * c - ry * math.sin(t) * s,
             cy + rx * math.cos(t) * s + ry * math.sin(t) * c)
            for t in (2 * math.pi * i / n for i in range(n))]


def circle(cx, cy, r, n=32) -> list[Pt]:
    return ellipse(cx, cy, r, r, 0, n)


def stroke(points: list[Pt], w0: float, w1: float | None = None, profile=None,
           cap: bool = True) -> list[list[Pt]]:
    """Kalınlığı w0'dan w1'e değişen çizgi. profile(t)->çarpan verilirse o kullanılır."""
    if w1 is None:
        w1 = w0
    n = len(points)
    if n < 2:
        return []
    left, right = [], []
    for i, (x, y) in enumerate(points):
        a = points[max(i - 1, 0)]
        b = points[min(i + 1, n - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1
        t = i / (n - 1)
        w = (w0 + (w1 - w0) * t) * (profile(t) if profile else 1)
        nx, ny = -dy / d * w / 2, dx / d * w / 2
        left.append((x + nx, y + ny))
        right.append((x - nx, y - ny))
    shapes = [left + right[::-1]]
    if cap:
        if w0 > 1:
            shapes.append(circle(points[0][0], points[0][1], w0 / 2, 12))
        if w1 > 1:
            shapes.append(circle(points[-1][0], points[-1][1], w1 / 2, 12))
    return shapes


def curve_stroke(ctrl: list[Pt], w0, w1=None, steps=8, profile=None, cap=True):
    return stroke(catmull(ctrl, closed=False, steps=steps), w0, w1, profile, cap)


def taper(t: float) -> float:
    """Kalem darbesi: uçlarda incelen, ortada kalın."""
    return 0.25 + 0.75 * math.sin(math.pi * t)


def offset_along(contour: list[Pt], i: int, dist: float) -> tuple[Pt, Pt]:
    """Kapalı kontur üzerinde i. noktadan içeri doğru dist kadar giden doğrultu."""
    n = len(contour)
    a, b = contour[(i - 1) % n], contour[(i + 1) % n]
    dx, dy = b[0] - a[0], b[1] - a[1]
    d = math.hypot(dx, dy) or 1
    return contour[i], (-dy / d * dist, dx / d * dist)


def signed_area(c: list[Pt]) -> float:
    return 0.5 * sum(c[i][0] * c[(i + 1) % len(c)][1] - c[(i + 1) % len(c)][0] * c[i][1]
                     for i in range(len(c)))


def transform(c: list[Pt], dx=0.0, dy=0.0, s=1.0, rot=0.0, ox=0.0, oy=0.0, flip=False) -> list[Pt]:
    """(ox,oy) etrafında ölçekle/döndür, sonra kaydır. flip: x ekseninde ayna."""
    cs, sn = math.cos(rot), math.sin(rot)
    out = []
    for x, y in c:
        x, y = (x - ox) * s, (y - oy) * s
        if flip:
            x = -x
        x, y = x * cs - y * sn, x * sn + y * cs
        out.append((x + ox + dx, y + oy + dy))
    return out


# ---------------------------------------------------------------- çizim

class Drawing:
    def __init__(self):
        self.layers: list[tuple[str, list[list[Pt]]]] = []

    def _add(self, kind: str, items):
        contours = []
        for it in items:
            if not it:
                continue
            if isinstance(it[0], (list, tuple)) and it and isinstance(it[0][0], (list, tuple)):
                contours.extend(it)  # şekil listesi
            else:
                contours.append(it)
        if self.layers and self.layers[-1][0] == kind:
            self.layers[-1][1].extend(contours)
        else:
            self.layers.append((kind, contours))
        return self

    def fill(self, *items):
        return self._add("fill", items)

    def cut(self, *items):
        return self._add("cut", items)

    def merge(self, other: "Drawing", **tf):
        for kind, cs in other.layers:
            self._add(kind, [transform(c, **tf) for c in cs] if tf else cs)
        return self

    def transformed(self, **tf) -> "Drawing":
        d = Drawing()
        for kind, cs in self.layers:
            d.layers.append((kind, [transform(c, **tf) for c in cs]))
        return d

    def to_path(self) -> Path:
        result = Path()
        for kind, contours in self.layers:
            layer = _union(contours)
            result = safe_op(result, layer, PathOp.UNION if kind == "fill" else PathOp.DIFFERENCE)
        return result


def _contour_path(c: list[Pt]) -> Path | None:
    if len(c) < 3 or abs(signed_area(c)) < 1:
        return None
    if signed_area(c) < 0:
        c = c[::-1]
    p = Path(fillType=FillType.WINDING)
    pen = p.getPen()
    pen.moveTo((round(c[0][0], 1), round(c[0][1], 1)))
    for x, y in c[1:]:
        pen.lineTo((round(x, 1), round(y, 1)))
    pen.closePath()
    return p


def _union(contours: list[list[Pt]]) -> Path:
    """Konturları birleştir. Toplu birleştirme başarısız olursa tek tek dener, bozuk olanı atlar."""
    p = Path(fillType=FillType.WINDING)
    pen = p.getPen()
    for c in contours:
        cp = _contour_path(c)
        if cp is not None:
            cp.draw(pen)
    try:
        p.simplify()
        return p
    except Exception:
        result = Path()
        for c in contours:
            cp = _contour_path(c)
            if cp is None:
                continue
            try:
                cp.simplify()
                result = op(result, cp, PathOp.UNION)
            except Exception:
                continue
        return result


def safe_op(a: Path, b: Path, kind) -> Path:
    try:
        return op(a, b, kind)
    except Exception:
        return a if kind != PathOp.INTERSECTION else Path()


def _contours(path: Path) -> list[list[Pt]]:
    from fontTools.pens.recordingPen import RecordingPen
    rec = RecordingPen()
    path.draw(rec)
    out, cur = [], []
    for verb, pts in rec.value:
        if verb == "moveTo":
            cur = [pts[0]]
        elif verb == "lineTo":
            cur.append(pts[0])
        elif verb in ("qCurveTo", "curveTo"):
            cur.extend(pts)
        elif verb in ("closePath", "endPath"):
            if cur:
                out.append(cur)
            cur = []
    return out


# ---------------------------------------------------------------- tarama

def hatch_along(contour: list[Pt], indices, length: float, width: float, seed: int,
                jitter: float = 0.35, angle_bias: float = 0.0, density: int = 1):
    """Kontur boyunca içe doğru kısa kalem darbeleri (tüy/gölge taraması)."""
    rng = random.Random(seed)
    out = []
    n = len(contour)
    for i in indices:
        for _ in range(density):
            j = i + rng.uniform(-0.5, 0.5)
            k = int(j) % n
            frac = j - int(j)
            a, b = contour[k], contour[(k + 1) % n]
            px, py = a[0] + (b[0] - a[0]) * frac, a[1] + (b[1] - a[1]) * frac
            _, (nx, ny) = offset_along(contour, k, 1)
            ang = math.atan2(ny, nx) + angle_bias + rng.uniform(-jitter, jitter)
            L = length * rng.uniform(0.55, 1.15)
            bend = rng.uniform(-0.25, 0.25)
            pts = [(px + math.cos(ang + bend * s) * L * s, py + math.sin(ang + bend * s) * L * s)
                   for s in (0, 0.33, 0.66, 1.0)]
            out += stroke(catmull(pts, False, 3), width, width * 0.15, cap=False)
    return out


def contour_slice(contour: list[Pt], t0: float, t1: float) -> list[Pt]:
    """Kapalı konturun t0..t1 (0..1) arası parçası (açık eğri)."""
    n = len(contour)
    i0, i1 = int(t0 * n), int(t1 * n)
    if i1 <= i0:
        i1 += n
    return [contour[i % n] for i in range(i0, i1 + 1)]


def index_range(contour, t0, t1, step=1):
    n = len(contour)
    i0, i1 = int(t0 * n), int(t1 * n)
    if i1 <= i0:
        i1 += n
    return [i % n for i in range(i0, i1, step)]
