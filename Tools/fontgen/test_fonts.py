#!/usr/bin/env python3
"""Fontları doğrular ve önizleme üretir.

1) HarfBuzz ile sayaç metinlerini şekillendirir: yalnızca son hanenin
   karesi görünmeli, diğer her şey genişliği 0 boş glif olmalı.
2) docs/preview/ altına her klip için GIF, panoramalar için sol+sağ
   birleşik GIF ve poz sayfası çizer.
"""
from __future__ import annotations

import sys
from pathlib import Path

import uharfbuzz as hb
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
FONT_DIR = ROOT / "targets" / "widget" / "assets"
PREVIEW = ROOT / "docs" / "preview"
BG, FG = (28, 28, 28), (245, 245, 245)

SAMPLES = ["0:00", "0:07", "0:59", "1:00", "9:58", "12:34", "1:23:45", "23:59:59", "100:00:03"]


def shape(font_path: Path, text: str):
    font = hb.Font(hb.Face(hb.Blob.from_file_path(str(font_path))))
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, {"calt": True})
    names = [font.glyph_to_string(i.codepoint) for i in buf.glyph_infos]
    return names, sum(p.x_advance for p in buf.glyph_positions)


def check_clip(path: Path) -> list[str]:
    errors = []
    for s in SAMPLES:
        names, width = shape(path, s)
        visible = [n for n in names if n != "blank"]
        if visible != [f"f{s[-1]}"] or width != 2000:
            errors.append(f"{path.name} '{s}': görünen={visible} genişlik={width}")
    return errors


def render(path: Path, ch: str, scale=0.16) -> Image.Image:
    font = ImageFont.truetype(str(path), 1000)
    img = Image.new("L", (2000, 1150), 0)
    ImageDraw.Draw(img).text((0, 0), ch, font=font, fill=255)
    img = img.resize((int(2000 * scale), int(1150 * scale)), Image.LANCZOS)
    return Image.composite(Image.new("RGB", img.size, FG), Image.new("RGB", img.size, BG), img)


def save_gif(frames, out: Path, duration):
    frames[0].save(out, save_all=True, append_images=frames[1:], duration=duration, loop=0)


def main():
    PREVIEW.mkdir(parents=True, exist_ok=True)
    for old in PREVIEW.glob("*"):
        old.unlink()
    errors = []
    fonts = sorted(FONT_DIR.glob("*.ttf"))
    for path in fonts:
        ps = TTFont(str(path))["name"].getDebugName(6)
        assert ps == path.stem, f"PostScript adı {ps} != {path.stem}"
        if path.stem.endswith("-poses"):
            letters = [chr(c) for c, g in TTFont(str(path)).getBestCmap().items() if g.startswith("pose_")]
            tiles = [render(path, ch) for ch in letters]
            sheet = Image.new("RGB", (tiles[0].width * len(tiles) + 4 * (len(tiles) - 1), tiles[0].height), (70, 70, 70))
            for i, t in enumerate(tiles):
                sheet.paste(t, (i * (t.width + 4), 0))
            sheet.save(PREVIEW / f"{path.stem}.png")
            continue
        errors += check_clip(path)
        if path.stem.endswith("-R"):
            continue
        if path.stem.endswith("-L"):
            right = path.with_name(path.stem[:-2] + "-R.ttf")
            frames = []
            for d in range(10):
                l, r = render(path, str(d)), render(right, str(d))
                both = Image.new("RGB", (l.width * 2 + 8, l.height), (70, 70, 70))
                both.paste(l, (0, 0))
                both.paste(r, (l.width + 8, 0))
                frames.append(both)
            save_gif(frames, PREVIEW / f"{path.stem[:-2]}-panorama.gif", 400)
        else:
            save_gif([render(path, str(d)) for d in range(10)], PREVIEW / f"{path.stem}.gif", 400)
    if errors:
        print("\n".join(errors))
        sys.exit(1)
    print(f"{len(fonts)} font, tüm sayaç testleri geçti.")


if __name__ == "__main__":
    main()
