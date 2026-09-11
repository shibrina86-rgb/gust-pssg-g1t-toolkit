#!/usr/bin/env python3
"""Alias legacy CJK code slots to existing Hangul glyphs in an OTF/TTF cmap."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from fontTools.ttLib import TTFont


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_font", type=Path)
    parser.add_argument("mapping_json", type=Path)
    parser.add_argument("output_font", type=Path)
    args = parser.parse_args()

    raw = json.loads(args.mapping_json.read_text(encoding="utf-8"))["mapping"]
    mapping = {int(key[2:], 16): int(value[2:], 16) for key, value in raw.items()}
    font = TTFont(args.input_font, recalcTimestamp=False)
    best = font.getBestCmap() or {}
    missing = [cp for cp in mapping.values() if cp not in best]
    if missing:
        raise ValueError(f"input font lacks {len(set(missing))} required Hangul glyphs")
    changed_tables = 0
    for table in font["cmap"].tables:
        if not table.isUnicode() or table.format not in (4, 12, 13):
            continue
        for slot_cp, hangul_cp in mapping.items():
            table.cmap[slot_cp] = best[hangul_cp]
        changed_tables += 1
    if not changed_tables:
        raise ValueError("no supported Unicode cmap table was found")
    args.output_font.parent.mkdir(parents=True, exist_ok=True)
    font.save(args.output_font, reorderTables=False)
    font.close()

    check = TTFont(args.output_font)
    cmap = check.getBestCmap() or {}
    aliased = sum(cmap.get(slot) == cmap.get(hangul) for slot, hangul in mapping.items())
    check.close()
    if aliased != len(mapping):
        raise ValueError(f"alias validation failed: {aliased} != {len(mapping)}")
    print(f"aliases={aliased} cmap_tables={changed_tables} output={args.output_font}")


if __name__ == "__main__":
    main()


