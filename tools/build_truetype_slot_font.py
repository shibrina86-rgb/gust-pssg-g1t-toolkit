#!/usr/bin/env python3
"""Insert donor outlines into a Switch TrueType font and remap legacy slots."""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path

from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont


def load_mapping(path: Path) -> dict[int, int]:
    raw = json.loads(path.read_text(encoding="utf-8"))["mapping"]
    return {int(key[2:], 16): int(value[2:], 16) for key, value in raw.items()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("switch_base", type=Path)
    parser.add_argument("hangul_donor", type=Path)
    parser.add_argument("mapping_json", type=Path)
    parser.add_argument("output_font", type=Path)
    parser.add_argument("--also-unicode", action="store_true")
    args = parser.parse_args()

    target = TTFont(args.switch_base, recalcTimestamp=False)
    donor = TTFont(args.hangul_donor, recalcTimestamp=False)
    if "glyf" not in target:
        raise ValueError("target is not a TrueType glyf font; do not use this tool for CFF OTF")
    mapping = load_mapping(args.mapping_json)
    donor_cmap = donor.getBestCmap() or {}
    donor_glyphs = donor.getGlyphSet()
    scale = target["head"].unitsPerEm / donor["head"].unitsPerEm
    glyph_order = target.getGlyphOrder()

    for index, (slot_cp, hangul_cp) in enumerate(mapping.items()):
        source_name = donor_cmap.get(hangul_cp)
        if source_name is None:
            raise ValueError(f"donor lacks U+{hangul_cp:04X}")
        recording = DecomposingRecordingPen(donor_glyphs)
        donor_glyphs[source_name].draw(recording)
        tt_pen = TTGlyphPen(None)
        quadratic = Cu2QuPen(tt_pen, max_err=max(0.5, scale * 0.5), reverse_direction=True)
        transformed = TransformPen(quadratic, (scale, 0, 0, scale, 0, 0))
        recording.replay(transformed)
        glyph = tt_pen.glyph()
        glyph.recalcBounds(target["glyf"])
        new_name = f"ko_slot_{index:05d}"
        glyph_order.append(new_name)
        target["glyf"][new_name] = deepcopy(glyph)
        width, lsb = donor["hmtx"].metrics[source_name]
        target["hmtx"].metrics[new_name] = (round(width * scale), round(lsb * scale))
        if "vmtx" in target:
            advance = target["head"].unitsPerEm
            top = target["vhea"].ascent - glyph.yMax
            target["vmtx"].metrics[new_name] = (advance, top)
        for table in target["cmap"].tables:
            if table.isUnicode() and table.format in (4, 12, 13):
                table.cmap[slot_cp] = new_name
                if args.also_unicode:
                    table.cmap[hangul_cp] = new_name

    target.setGlyphOrder(glyph_order)
    args.output_font.parent.mkdir(parents=True, exist_ok=True)
    target.save(args.output_font, reorderTables=False)
    target.close()
    donor.close()

    check = TTFont(args.output_font)
    cmap = check.getBestCmap() or {}
    if any(cp not in cmap for cp in mapping):
        raise ValueError("one or more legacy slots are missing after save")
    if args.also_unicode and any(cp not in cmap for cp in mapping.values()):
        raise ValueError("one or more Hangul Unicode entries are missing after save")
    check.close()
    print(f"inserted={len(mapping)} output={args.output_font}")


if __name__ == "__main__":
    main()


