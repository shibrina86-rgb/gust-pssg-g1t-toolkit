#!/usr/bin/env python3
"""Print a compact structural inventory for OTF/TTF files."""

from __future__ import annotations

import argparse
from pathlib import Path

from fontTools.ttLib import TTFont


def inspect(path: Path) -> None:
    font = TTFont(path, lazy=True)
    cmap = font.getBestCmap() or {}
    print(f"file={path}")
    print(f"sfnt={font.sfntVersion!r}")
    print(f"outline={'glyf' if 'glyf' in font else 'CFF' if 'CFF ' in font else 'other'}")
    print(f"upm={font['head'].unitsPerEm}")
    print(f"glyphs={len(font.getGlyphOrder())} cmap={len(cmap)}")
    print(f"hangul_syllables={sum(0xAC00 <= cp <= 0xD7A3 for cp in cmap)}")
    print(f"compat_jamo={sum(0x3131 <= cp <= 0x318E for cp in cmap)}")
    print(f"cjk={sum(0x4E00 <= cp <= 0x9FFF for cp in cmap)}")
    print(
        "cmap_tables="
        + repr(
            [(table.format, table.platformID, table.platEncID, len(table.cmap))
             for table in font['cmap'].tables]
        )
    )
    print(f"vertical_metrics={'vmtx' in font}")
    font.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("fonts", type=Path, nargs="+")
    args = parser.parse_args()
    for index, path in enumerate(args.fonts):
        if index:
            print()
        inspect(path)


if __name__ == "__main__":
    main()


