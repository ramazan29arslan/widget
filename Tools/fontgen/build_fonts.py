#!/usr/bin/env python3
"""Karakter çizimlerinden widget fontlarını üretir.

Her animasyon klibi için bir font:
  0-9 rakamları 10 karelik animasyonun kareleridir.
  Bir 'calt' kuralı, ardından başka rakam ya da ':' gelen her rakamı
  boş (genişliği 0) glife çevirir. Böylece sistemin sayaç metni
  ("1:23:45") ekranda yalnızca SON hanenin karesi olarak görünür ve
  saniyede bir kare ilerler.

Her karakter için ayrıca bir poz fontu:
  Harfler (a, s, z, ...) ruh hali pozlarıdır. Text("z") -> uyuyan kedi.

Çıktılar:
  targets/widget/assets/*.ttf                  (widget fontları)
  targets/widget/CharacterCatalog.generated.swift  (widget kataloğu)
  src/catalog.generated.ts                     (uygulama kataloğu)
"""
from __future__ import annotations

import importlib
import pkgutil
import sys
from pathlib import Path

from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen

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
# Sayaç metninde rakam dışında görülebilecek karakterler -> boş glif
BLANK_CHARS = ":.    ∶-−"


def glyph_from_drawing(drawing):
    path = drawing.to_path()
    pen = TTGlyphPen(None)
    path.draw(pen)
    glyph = pen.glyph()
    xmin = path.bounds[0] if path.bounds else 0
    return glyph, int(xmin)


def empty_glyph():
    return TTGlyphPen(None).glyph()


def make_font(ps_name: str, family: str, glyphs: dict, cmap: dict, fea: str | None, out: Path):
    order = list(glyphs.keys())
    fb = FontBuilder(UPM, isTTF=True)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap(cmap)
    fb.setupGlyf({n: g for n, (g, _, _) in glyphs.items()})
    fb.setupHorizontalMetrics({n: (adv, lsb) for n, (_, adv, lsb) in glyphs.items()})
    fb.setupHorizontalHeader(ascent=ASCENT, descent=DESCENT)
    fb.setupNameTable({"familyName": family, "styleName": "Regular", "psName": ps_name,
                       "fullName": family, "uniqueFontIdentifier": ps_name})
    fb.setupOS2(sTypoAscender=ASCENT, sTypoDescender=DESCENT, sTypoLineGap=0,
                usWinAscent=ASCENT, usWinDescent=-DESCENT, fsType=0)
    fb.setupPost()
    if fea:
        addOpenTypeFeaturesFromString(fb.font, fea)
    out.parent.mkdir(parents=True, exist_ok=True)
    fb.save(str(out))


def blank_entries():
    return {".notdef": (empty_glyph(), ADVANCE // 4, 0), "blank": (empty_glyph(), 0, 0)}


def build_clip_font(char_id: str, clip_id: str, frames) -> str:
    assert len(frames) == 10, f"{char_id}/{clip_id}: tam 10 kare olmalı"
    ps = f"Pati-{char_id}-{clip_id}"
    glyphs = blank_entries()
    for i, d in enumerate(frames):
        g, lsb = glyph_from_drawing(d)
        glyphs[f"f{i}"] = (g, ADVANCE, lsb)
    cmap = {ord(c): f"f{c}" for c in DIGITS}
    cmap.update({ord(c): "blank" for c in BLANK_CHARS})
    frame_cls = " ".join(f"f{i}" for i in range(10))
    fea = f"""
languagesystem DFLT dflt;
languagesystem latn dflt;
@FRAME = [{frame_cls}];
@NEXT = [{frame_cls} blank];
feature calt {{
    sub @FRAME' @NEXT by blank;
}} calt;
"""
    make_font(ps, ps, glyphs, cmap, fea, FONT_DIR / f"{ps}.ttf")
    return ps


def build_pose_font(char_id: str, poses: dict) -> str:
    ps = f"Pati-{char_id}-poses"
    glyphs = blank_entries()
    cmap = {ord(" "): "blank"}
    for letter, (_, fn) in poses.items():
        g, lsb = glyph_from_drawing(fn())
        glyphs[f"pose_{letter}"] = (g, ADVANCE, lsb)
        cmap[ord(letter)] = f"pose_{letter}"
    make_font(ps, ps, glyphs, cmap, None, FONT_DIR / f"{ps}.ttf")
    return ps


def swift_string(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def main():
    import characters

    catalog = []
    for mod_info in sorted(pkgutil.iter_modules(characters.__path__), key=lambda m: m.name):
        mod = importlib.import_module(mod_info.name)
        clips = []
        for clip_id, (title, fn) in mod.CLIPS.items():
            clips.append((clip_id, title, build_clip_font(mod.ID, clip_id, fn())))
            print(f"  ✓ {mod.ID}/{clip_id}")
        pose_font = build_pose_font(mod.ID, mod.POSES)
        print(f"  ✓ {mod.ID}/poses")
        catalog.append((mod.ID, mod.NAME, clips, pose_font, list(mod.POSES.keys())))

    lines = [
        "// BU DOSYA OTOMATİK ÜRETİLİR. Düzenleme: Tools/fontgen/build_fonts.py",
        "",
        "extension CharacterCatalog {",
        "    static let all: [PatiCharacter] = [",
    ]
    for cid, name, clips, pose_font, pose_keys in catalog:
        clip_src = ", ".join(
            f"AnimationClip(id: {swift_string(c)}, title: {swift_string(t)}, fontName: {swift_string(f)})"
            for c, t, f in clips)
        lines += [
            "        PatiCharacter(",
            f"            id: {swift_string(cid)},",
            f"            name: {swift_string(name)},",
            f"            clips: [{clip_src}],",
            f"            poseFontName: {swift_string(pose_font)},",
            f"            poses: [{', '.join(swift_string(k) for k in pose_keys)}]",
            "        ),",
        ]
    lines += ["    ]", "}", ""]
    SWIFT_OUT.parent.mkdir(parents=True, exist_ok=True)
    SWIFT_OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"→ {SWIFT_OUT.relative_to(ROOT)}")
    write_ts(catalog)


def write_ts(catalog):
    import json
    out = [
        "// BU DOSYA OTOMATİK ÜRETİLİR. Düzenleme: Tools/fontgen/build_fonts.py",
        "import type { PatiCharacter } from './types';",
        "",
        "export const FONTS = {",
    ]
    for _, _, clips, pose_font, _ in catalog:
        for font in [f for _, _, f in clips] + [pose_font]:
            out.append(f"  {json.dumps(font)}: require('../targets/widget/assets/{font}.ttf'),")
    out += ["};", "", "export const CHARACTERS: PatiCharacter[] = ["]
    for cid, name, clips, pose_font, pose_keys in catalog:
        out.append("  {")
        out.append(f"    id: {json.dumps(cid)},")
        out.append(f"    name: {json.dumps(name, ensure_ascii=False)},")
        out.append("    clips: [")
        for c, t, f in clips:
            out.append(f"      {{ id: {json.dumps(c)}, title: {json.dumps(t, ensure_ascii=False)}, fontName: {json.dumps(f)} }},")
        out.append("    ],")
        out.append(f"    poseFontName: {json.dumps(pose_font)},")
        out.append(f"    poses: {json.dumps(pose_keys)},")
        out.append("  },")
    out += ["];", ""]
    TS_OUT.parent.mkdir(parents=True, exist_ok=True)
    TS_OUT.write_text("\n".join(out), encoding="utf-8")
    print(f"→ {TS_OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
