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
from dataclasses import dataclass
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from pathops import Path as SkPath, PathOp
from sketch import safe_op as op

import art

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
# Kilit ekranında iki widget arasındaki boşluk (font birimi, ≈ 10 pt).
# Sağ parça bu kadar sağdan kesilir; böylece aradan geçen karakter bölünüp
# esnemek yerine bir direğin arkasından geçiyormuş gibi görünür.
SEAM_GAP = 140
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
        p.draw(TransformPen(Cu2QuPen(pen, max_err=1.0), transform))
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
    r0 = ADVANCE + SEAM_GAP
    right = make(keep(path, r0, r0 + ADVANCE), (1, 0, 0, 1, -r0, 0))
    return {"": full, "-L": left, "-R": right}


# ----------------------------------------------------------------- kayıt

@dataclass
class Clip:
    title: str
    wide: bool
    fn: object = None            # kodla çizim: () -> [Drawing × 10]
    art: object = None           # art.ClipArt (görsel kaynak varsa öncelikli)


@dataclass
class Character:
    id: str
    name: str
    clips: dict
    mood_clips: dict
    poses: dict                  # harf -> (başlık, çizim fonksiyonu | None)
    art_poses: dict              # harf -> görsel dosyası


def registry() -> list[Character]:
    """Kodla çizilen karakterler + art/ klasöründeki görseller (görsel varsa onu kullanır)."""
    import characters

    chars: dict[str, Character] = {}
    for m in sorted(pkgutil.iter_modules(characters.__path__), key=lambda m: m.name):
        if m.name.startswith("_"):
            continue
        mod = importlib.import_module(m.name)
        clips = {k: Clip(t, w, fn) for k, (t, fn, w) in mod.CLIPS.items()}
        chars[mod.ID] = Character(mod.ID, mod.NAME, clips, dict(getattr(mod, "MOOD_CLIPS", {})),
                                  dict(mod.POSES), {})
    for cid, meta in art.art_characters().items():
        if cid not in chars:
            chars[cid] = Character(cid, meta.get("name", cid), {}, dict(meta.get("moodClips", {})), {}, {})
        else:
            chars[cid].mood_clips.update(meta.get("moodClips", {}))
    for cid, ch in chars.items():
        for key, ca in art.art_clips(cid).items():
            old = ch.clips.get(key)
            title = ca.options.get("title") or (old.title if old else key)
            wide = ca.options.get("wide", old.wide if old else False)
            ca.options["wide"] = wide
            ch.clips[key] = Clip(title, wide, old.fn if old else None, ca)
        ch.art_poses = art.art_poses(cid)
        for k in ch.art_poses:
            if k not in ch.poses:
                ch.poses[k] = (POSE_TITLES.get(k, k), None)
    order = {"cat": 0, "dog": 1, "janissary": 2}
    return sorted((c for c in chars.values() if c.clips), key=lambda c: (order.get(c.id, 99), c.id))


POSE_TITLES = {"a": "Uyanık", "s": "Uykulu", "z": "Uyuyor", "t": "Yorgun", "p": "Oyuncu"}
_REG: dict | None = None
_CACHE: dict = {}


def _char(cid) -> Character:
    global _REG
    if _REG is None:
        _REG = {c.id: c for c in registry()}
    return _REG[cid]


def _render_frame(args):
    cid, kind, key, index = args
    ch = _char(cid)
    if kind == "clip":
        clip = ch.clips[key]
        ck = (cid, key)
        if ck not in _CACHE:
            if clip.art:
                _CACHE[ck] = art.trace_clip(clip.art, 2 * ADVANCE if clip.wide else ADVANCE)
            else:
                _CACHE[ck] = [d.to_path() for d in clip.fn()]
        return glyph_variants(_CACHE[ck][index], clip.wide)
    if key in ch.art_poses:
        ck = (cid, "poses")
        if ck not in _CACHE:
            _CACHE[ck] = art.trace_poses(ch.art_poses, options=art.pose_options(cid))
        return glyph_variants(_CACHE[ck][key], False)
    _, fn = ch.poses[key]
    return glyph_variants(fn().to_path(), False)


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
    t0 = time.time()
    chars = registry()
    todo = [c for c in chars if not only or c.id in only]
    jobs = []
    for ch in todo:
        for key in ch.clips:
            jobs += [(ch.id, "clip", key, i) for i in range(10)]
        jobs += [(ch.id, "pose", key, 0) for key in ch.poses]
    # Aynı klibin kareleri aynı işçiye gitsin (görsel izleme klip başına bir kez yapılır)
    results = {}
    with ProcessPoolExecutor() as ex:
        for job, res in zip(jobs, ex.map(_render_frame, jobs, chunksize=10)):
            results[job] = res

    catalog = []
    for ch in chars:
        clips = []
        build = not only or ch.id in only
        for key, clip in ch.clips.items():
            ps = f"Pati-{ch.id}-{key}"
            if build:
                variants = [results[(ch.id, "clip", key, i)] for i in range(10)]
                for suffix in variants[0]:
                    write_clip_font(ps + suffix, [v[suffix] for v in variants])
            clips.append({"id": key, "title": clip.title, "fontName": ps, "wide": clip.wide,
                          "leftFont": ps + "-L" if clip.wide else None,
                          "rightFont": ps + "-R" if clip.wide else None})
        pose_ps = f"Pati-{ch.id}-poses"
        if build:
            write_pose_font(pose_ps, {k: results[(ch.id, "pose", k, 0)][""] for k in ch.poses})
        mood_clips = {m: ch.mood_clips.get(m, clips[0]["id"]) for m in MOODS}
        catalog.append({"id": ch.id, "name": ch.name, "clips": clips, "poseFontName": pose_ps,
                        "poses": list(ch.poses.keys()), "moodClips": mood_clips})
        src = sum(1 for c in ch.clips.values() if c.art)
        print(f"  ✓ {ch.id}: {len(clips)} klip ({src} görselden), {len(ch.poses)} poz"
              f"{' (görselden)' if ch.art_poses else ''}")

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
