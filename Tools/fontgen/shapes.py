"""Basit vektör şekil kütüphanesi.

Karakterler doldurulan (fill) ve oyulan (hole) şekillerden oluşur.
Tüm dolgular birleştirilir, sonra delikler çıkarılır (skia-pathops).
Böylece üst üste binen şekillerde sarım (winding) sorunu yaşanmaz.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from pathops import Path, PathOp, op

Point = tuple[float, float]


def ellipse(cx: float, cy: float, rx: float, ry: float, rot: float = 0, n: int = 40) -> list[Point]:
    pts = []
    c, s = math.cos(rot), math.sin(rot)
    for i in range(n):
        t = 2 * math.pi * i / n
        x, y = rx * math.cos(t), ry * math.sin(t)
        pts.append((cx + x * c - y * s, cy + x * s + y * c))
    return pts


def circle(cx: float, cy: float, r: float, n: int = 32) -> list[Point]:
    return ellipse(cx, cy, r, r, 0, n)


def capsule(x1: float, y1: float, x2: float, y2: float, r: float) -> list[list[Point]]:
    """İki nokta arasında yuvarlak uçlu kalın çizgi (bacak, kuyruk parçası)."""
    ang = math.atan2(y2 - y1, x2 - x1)
    nx, ny = -math.sin(ang) * r, math.cos(ang) * r
    body = [(x1 + nx, y1 + ny), (x2 + nx, y2 + ny), (x2 - nx, y2 - ny), (x1 - nx, y1 - ny)]
    return [body, circle(x1, y1, r), circle(x2, y2, r)]


def polyline(points: list[Point], r: float) -> list[list[Point]]:
    out: list[list[Point]] = []
    for a, b in zip(points, points[1:]):
        out += capsule(a[0], a[1], b[0], b[1], r)
    return out


def zee(x: float, y: float, size: float, t: float = 40) -> list[list[Point]]:
    """Uyku için küçük 'Z' harfi."""
    s = size
    return polyline([(x, y + s), (x + s, y + s), (x, y), (x + s, y)], t / 2)


@dataclass
class Drawing:
    fills: list[list[Point]] = field(default_factory=list)
    holes: list[list[Point]] = field(default_factory=list)

    def fill(self, *contours):
        for c in contours:
            if c and isinstance(c[0], list):
                self.fills.extend(c)
            else:
                self.fills.append(c)
        return self

    def hole(self, *contours):
        for c in contours:
            if c and isinstance(c[0], list):
                self.holes.extend(c)
            else:
                self.holes.append(c)
        return self

    def mirrored(self, axis_x: float) -> "Drawing":
        m = lambda cs: [[(2 * axis_x - x, y) for x, y in c] for c in cs]
        return Drawing(m(self.fills), m(self.holes))

    def shifted(self, dx: float, dy: float = 0) -> "Drawing":
        m = lambda cs: [[(x + dx, y + dy) for x, y in c] for c in cs]
        return Drawing(m(self.fills), m(self.holes))

    def to_path(self) -> Path:
        result = Path()
        for c in self.fills:
            result = op(result, _contour_path(c), PathOp.UNION)
        for c in self.holes:
            result = op(result, _contour_path(c), PathOp.DIFFERENCE)
        return result


def _contour_path(points: list[Point]) -> Path:
    p = Path()
    pen = p.getPen()
    pen.moveTo((round(points[0][0]), round(points[0][1])))
    for x, y in points[1:]:
        pen.lineTo((round(x), round(y)))
    pen.closePath()
    return p
