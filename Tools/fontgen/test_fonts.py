#!/usr/bin/env python3
"""Fontları doğrular ve önizleme üretir.

1) HarfBuzz ile sayaç metinlerini şekillendirir: yalnızca son hanenin
   karesi görünmeli, diğer her şey genişliği 0 boş glif olmalı.
2) docs/preview/ altına her klip için GIF ve poz sayfası çizer.
"""
from __future__ import annotations

import sys
from pathlib import Path

import uharfbuzz as hb
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
FONT_DIR = ROOT / "Shared" / "Fonts"
PREVIEW = ROOT / "docs" / "preview"

SAMPLES = ["0:00", "0:07", "0:59", "1:00", "9:58", "12:34", "1:23:45", "23:59:59", "100:00:03"]


def shape(font_path: Path, text: str):
    blob = hb.Blob.from_file_path(str(font_path))
    face = hb.Face(blob)
    font = hb.Font(face)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, {"calt": True})
    names = [font.glyph_to_string(i.codepoint) for i in buf.glyph_infos]
    width = sum(p.x_advance for p in buf.glyph_positions)
    return names, width


def check_clip(path: Path) -> list[str]:
    errors = []
    for s in SAMPLES:
        names, width = shape(path, s)
        visible = [n for n in names if n != "blank"]
        want = f"f{s[-1]}"
        if visible != [want] or width != 2000:
            errors.append(f"{path.name} '{s}': görünen={visible} genişlik={width} (beklenen [{want}], 2000)")
    return errors


def render(path: Path, ch: str, scale=0.18) -> Image.Image:
    size = 1000
    font = ImageFont.truetype(str(path), size)
    img = Image.new("L", (2000, 1150), 0)
    ImageDraw.Draw(img).text((0, 0), ch, font=font, fill=255)
    img = img.resize((int(2000 * scale), int(1150 * scale)), Image.LANCZOS)
    bg = Image.new("RGB", img.size, (52, 22, 30))
    fg = Image.new("RGB", img.size, (246, 222, 228))
    return Image.composite(fg, bg, img)


def main():
    PREVIEW.mkdir(parents=True, exist_ok=True)
    errors = []
    for path in sorted(FONT_DIR.glob("*.ttf")):
        ps = TTFont(str(path))["name"].getDebugName(6)
        assert ps == path.stem, f"PostScript adı {ps} != {path.stem}"
        if path.stem.endswith("-poses"):
            letters = [chr(c) for c, g in TTFont(str(path)).getBestCmap().items() if g.startswith("pose_")]
            tiles = [render(path, ch) for ch in letters]
            sheet = Image.new("RGB", (tiles[0].width * len(tiles), tiles[0].height))
            for i, t in enumerate(tiles):
                sheet.paste(t, (i * t.width, 0))
            sheet.save(PREVIEW / f"{path.stem}.png")
        else:
            errors += check_clip(path)
            frames = [render(path, str(d)) for d in range(10)]
            frames[0].save(PREVIEW / f"{path.stem}.gif", save_all=True,
                           append_images=frames[1:], duration=1000, loop=0)
            # Hızlandırılmış sürüm: hareketin akışını görmek için
            frames[0].save(PREVIEW / f"{path.stem}-fast.gif", save_all=True,
                           append_images=frames[1:], duration=250, loop=0)
        print(f"  ✓ {path.name}")
    if errors:
        print("\n".join(errors))
        sys.exit(1)
    print(f"Tüm sayaç testleri geçti ({len(SAMPLES)} örnek × klip).")


if __name__ == "__main__":
    main()
