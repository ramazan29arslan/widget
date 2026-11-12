#!/usr/bin/env python3
"""Karakter çizimlerinden widget fontlarını üretir.

Her animasyon klibi için bir font:
  0-9 rakamları 10 karelik animasyonun kareleridir.
  Bir 'calt' kuralı, ardından başka rakam ya da ':' gelen her rakamı
  boş (genişliği 0) glife çevirir. Böylece sistemin sayaç metni
  ("1:23:45") ekranda yalnızca SON hanenin karesi olarak görünür ve
  saniyede bir kare ilerler.

Panorama klipleri (4000 birim genişlik, kilit ekranında yan yana iki widget):
  -L  sol yarı, -R  sağ yarı, ayrıca tek widget için küçültülmüş tam sahne.

Her karakter için ayrıca bir poz fontu:
  Harfler (a, s, z, t, p) ruh hali pozlarıdır.

Çıktılar:
  targets/widget/assets/*.ttf
  targets/widget/CharacterCatalog.generated.swift
  src/catalog.generated.ts
"""
from __future__ import annotations

import importlib
import json
import pkgutil
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from pathops import Path as SkPath, PathOp
from sketch import safe_op as op

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "characters"))

FONT_DIR = ROOT / "targets" / "widget" / "assets"
SWIFT_OUT = ROOT / "targets" / "widget" / "CharacterCatalog.generated.swift"
TS_OUT = ROOT / "src" / "catalog.generated.ts"

UPM = 1000
ADVANCE = 2000
ASCENT, DESCENT = 1000, -100
DIGITS = "0123456789"
BLANK_CHARS = ":.    ∶-−"
MOODS = ["awake", "sleepy", "sleeping", "tired", "playful"]


# ----------------------------------------------------------------- glifler

def _box(x0, x1) -> SkPath:
    p = SkPath()
    pen = p.getPen()
    pen.moveTo((x0, -500)); pen.lineTo((x1, -500)); pen.lineTo((x1, 1500)); pen.lineTo((x0, 1500))
    pen.closePath()
    return p


def glyph_variants(path: SkPath, wide: bool):
    """Bir kare için glif(ler): dar klipte tek, panoramada full/L/R."""
    def make(p: SkPath, transform=(1, 0, 0, 1, 0, 0)):
        pen = TTGlyphPen(None)
        p.draw(TransformPen(pen, transform))
        g = pen.glyph()
        return g

    def keep(p: SkPath, x0, x1) -> SkPath:
        # Kesişim işlemi karmaşık yollarda başarısız olabildiği için aralığın dışını çıkarıyoruz.
        p = op(p, _box(-20000, x0), PathOp.DIFFERENCE)
        return op(p, _box(x1, 20000), PathOp.DIFFERENCE)

    if not wide:
        return {"": make(keep(path, 0, ADVANCE))}
    full = make(path, (0.5, 0, 0, 0.5, 0, 15))
    left = make(keep(path, 0, ADVANCE))
    right = make(keep(path, ADVANCE, 2 * ADVANCE), (1, 0, 0, 1, -ADVANCE, 0))
    return {"": full, "-L": left, "-R": right}


def _render_frame(args):
    mod_name, kind, key, index = args
    mod = importlib.import_module(mod_name)
    if kind == "clip":
        _, fn, wide = mod.CLIPS[key]
        frames = _cached_frames(mod, key, fn)
        return glyph_variants(frames[index].to_path(), wide)
    _, fn = mod.POSES[key]
    return glyph_variants(fn().to_path(), False)


_FRAME_CACHE: dict = {}


def _cached_frames(mod, key, fn):
    ck = (mod.__name__, key)
    if ck not in _FRAME_CACHE:
        _FRAME_CACHE[ck] = fn()
    return _FRAME_CACHE[ck]


# ----------------------------------------------------------------- font

def make_font(ps_name: str, glyphs: dict, cmap: dict, fea: str | None, out: Path):
    fb = FontBuilder(UPM, isTTF=True)
    fb.setupGlyphOrder(list(glyphs.keys()))
    fb.setupCharacterMap(cmap)
    fb.setupGlyf({n: g for n, (g, _) in glyphs.items()})
    metrics = {}
    for n, (g, adv) in glyphs.items():
        g.recalcBounds(fb.font["glyf"]) if hasattr(g, "recalcBounds") else None
        metrics[n] = (adv, getattr(g, "xMin", 0) or 0)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=ASCENT, descent=DESCENT)
    fb.setupNameTable({"familyName": ps_name, "styleName": "Regular", "psName": ps_name,
                       "fullName": ps_name, "uniqueFontIdentifier": ps_name})
    fb.setupOS2(sTypoAscender=ASCENT, sTypoDescender=DESCENT, sTypoLineGap=0,
                usWinAscent=ASCENT, usWinDescent=-DESCENT, fsType=0)
    fb.setupPost()
    if fea:
        addOpenTypeFeaturesFromString(fb.font, fea)
    out.parent.mkdir(parents=True, exist_ok=True)
    fb.save(str(out))


def empty():
    return TTGlyphPen(None).glyph()


CLIP_FEA = """
languagesystem DFLT dflt;
languagesystem latn dflt;
@FRAME = [f0 f1 f2 f3 f4 f5 f6 f7 f8 f9];
@NEXT = [f0 f1 f2 f3 f4 f5 f6 f7 f8 f9 blank];
feature calt {
    sub @FRAME' @NEXT by blank;
} calt;
"""


def write_clip_font(ps: str, frames: list):
    glyphs = {".notdef": (empty(), ADVANCE // 4), "blank": (empty(), 0)}
    for i, g in enumerate(frames):
        glyphs[f"f{i}"] = (g, ADVANCE)
    cmap = {ord(c): f"f{c}" for c in DIGITS}
    cmap.update({ord(c): "blank" for c in BLANK_CHARS})
    make_font(ps, glyphs, cmap, CLIP_FEA, FONT_DIR / f"{ps}.ttf")


def write_pose_font(ps: str, poses: dict):
    glyphs = {".notdef": (empty(), ADVANCE // 4), "blank": (empty(), 0)}
    cmap = {ord(" "): "blank"}
    for letter, g in poses.items():
        glyphs[f"pose_{letter}"] = (g, ADVANCE)
        cmap[ord(letter)] = f"pose_{letter}"
    make_font(ps, glyphs, cmap, None, FONT_DIR / f"{ps}.ttf")


# ----------------------------------------------------------------- ana akış

def main(only: set[str] | None = None):
    import characters

    t0 = time.time()
    mods = [importlib.import_module(m.name)
            for m in sorted(pkgutil.iter_modules(characters.__path__), key=lambda m: m.name)
            if not m.name.startswith("_")]
    order = {"cat": 0, "dog": 1, "janissary": 2}
    mods.sort(key=lambda m: order.get(m.ID, 99))

    jobs = []
    for mod in mods:
        if only and mod.ID not in only:
            continue
        for key in mod.CLIPS:
            jobs += [(mod.__name__, "clip", key, i) for i in range(10)]
        jobs += [(mod.__name__, "pose", key, 0) for key in mod.POSES]

    # Aynı klibin kareleri aynı işçiye gitsin diye klip başına grupla
    results = {}
    with ProcessPoolExecutor() as ex:
        for job, res in zip(jobs, ex.map(_render_frame, jobs, chunksize=10)):
            results[job] = res

    catalog = []
    for mod in mods:
        clips = []
        for key, (title, _, wide) in mod.CLIPS.items():
            ps = f"Pati-{mod.ID}-{key}"
            if not only or mod.ID in only:
                variants = [results[(mod.__name__, "clip", key, i)] for i in range(10)]
                for suffix in variants[0]:
                    write_clip_font(ps + suffix, [v[suffix] for v in variants])
            clips.append({"id": key, "title": title, "fontName": ps, "wide": wide,
                          "leftFont": ps + "-L" if wide else None, "rightFont": ps + "-R" if wide else None})
        pose_ps = f"Pati-{mod.ID}-poses"
        if not only or mod.ID in only:
            write_pose_font(pose_ps, {k: results[(mod.__name__, "pose", k, 0)][""] for k in mod.POSES})
        mood_clips = {m: getattr(mod, "MOOD_CLIPS", {}).get(m, clips[0]["id"]) for m in MOODS}
        catalog.append({"id": mod.ID, "name": mod.NAME, "clips": clips, "poseFontName": pose_ps,
                        "poses": list(mod.POSES.keys()), "moodClips": mood_clips})
        print(f"  ✓ {mod.ID}: {len(clips)} klip, {len(mod.POSES)} poz")

    write_swift(catalog)
    write_ts(catalog)
    print(f"→ bitti ({time.time() - t0:.0f} sn)")


def q(s):
    return json.dumps(s, ensure_ascii=False)


def write_swift(catalog):
    lines = ["// BU DOSYA OTOMATİK ÜRETİLİR. Düzenleme: Tools/fontgen/build_fonts.py", "",
             "extension CharacterCatalog {", "    static let all: [PatiCharacter] = ["]
    for c in catalog:
        lines.append("        PatiCharacter(")
        lines.append(f"            id: {q(c['id'])},")
        lines.append(f"            name: {q(c['name'])},")
        lines.append("            clips: [")
        for k in c["clips"]:
            lf = q(k["leftFont"]) if k["leftFont"] else "nil"
            rf = q(k["rightFont"]) if k["rightFont"] else "nil"
            lines.append(f"                AnimationClip(id: {q(k['id'])}, title: {q(k['title'])}, "
                         f"fontName: {q(k['fontName'])}, leftFont: {lf}, rightFont: {rf}),")
        lines.append("            ],")
        lines.append(f"            poseFontName: {q(c['poseFontName'])},")
        lines.append(f"            poses: [{', '.join(q(p) for p in c['poses'])}],")
        mc = ", ".join(f"{q(m)}: {q(v)}" for m, v in c["moodClips"].items())
        lines.append(f"            moodClips: [{mc}]")
        lines.append("        ),")
    lines += ["    ]", "}", ""]
    SWIFT_OUT.write_text("\n".join(lines), encoding="utf-8")


def write_ts(catalog):
    out = ["// BU DOSYA OTOMATİK ÜRETİLİR. Düzenleme: Tools/fontgen/build_fonts.py",
           "import type { PatiCharacter } from './types';", "", "export const FONTS = {"]
    for c in catalog:
        for k in c["clips"]:
            for f in (k["fontName"], k["leftFont"], k["rightFont"]):
                if f:
                    out.append(f"  {q(f)}: require('../targets/widget/assets/{f}.ttf'),")
        out.append(f"  {q(c['poseFontName'])}: require('../targets/widget/assets/{c['poseFontName']}.ttf'),")
    out += ["};", "", "export const CHARACTERS: PatiCharacter[] = ["]
    for c in catalog:
        out += ["  {", f"    id: {q(c['id'])},", f"    name: {q(c['name'])},", "    clips: ["]
        for k in c["clips"]:
            out.append(f"      {{ id: {q(k['id'])}, title: {q(k['title'])}, fontName: {q(k['fontName'])}, "
                       f"wide: {'true' if k['wide'] else 'false'}, leftFont: {q(k['leftFont'])}, "
                       f"rightFont: {q(k['rightFont'])} }},".replace("null", "null"))
        out.append("    ],")
        out.append(f"    poseFontName: {q(c['poseFontName'])},")
        out.append(f"    poses: {json.dumps(c['poses'])},")
        out.append(f"    moodClips: {json.dumps(c['moodClips'])},")
        out.append("  },")
    out += ["];", ""]
    TS_OUT.parent.mkdir(parents=True, exist_ok=True)
    TS_OUT.write_text("\n".join(out), encoding="utf-8")


if __name__ == "__main__":
    main(set(sys.argv[1:]) or None)
