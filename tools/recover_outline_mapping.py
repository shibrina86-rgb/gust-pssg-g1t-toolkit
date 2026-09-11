#!/usr/bin/env python3
"""Recover changed Unicode-slot to Hangul mappings by exact outline matching."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.ttLib import TTFont


def signature(font: TTFont, glyph_name: str) -> str:
    glyphs = font.getGlyphSet()
    pen = DecomposingRecordingPen(glyphs)
    glyphs[glyph_name].draw(pen)
    return repr(pen.value)


def cp_label(codepoint: int) -> str:
    return f"U+{codepoint:04X}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("original_font", type=Path)
    parser.add_argument("patched_font", type=Path)
    parser.add_argument("hangul_donor", type=Path)
    parser.add_argument("output_json", type=Path)
    args = parser.parse_args()

    original = TTFont(args.original_font, recalcTimestamp=False)
    patched = TTFont(args.patched_font, recalcTimestamp=False)
    donor = TTFont(args.hangul_donor, recalcTimestamp=False)
    original_cmap = original.getBestCmap() or {}
    patched_cmap = patched.getBestCmap() or {}
    donor_cmap = donor.getBestCmap() or {}

    donor_lookup: dict[str, list[int]] = {}
    for cp in range(0xAC00, 0xD7A4):
        name = donor_cmap.get(cp)
        if name is not None:
            donor_lookup.setdefault(signature(donor, name), []).append(cp)

    changed: list[int] = []
    for cp in sorted(set(original_cmap) & set(patched_cmap)):
        if signature(original, original_cmap[cp]) != signature(patched, patched_cmap[cp]):
            changed.append(cp)

    mapping: dict[int, int] = {}
    unmatched: list[int] = []
    ambiguous: dict[int, list[int]] = {}
    for target_cp in changed:
        matches = donor_lookup.get(signature(patched, patched_cmap[target_cp]), [])
        if len(matches) == 1:
            mapping[target_cp] = matches[0]
        elif not matches:
            unmatched.append(target_cp)
        else:
            ambiguous[target_cp] = matches

    result = {
        "mapping": {cp_label(key): cp_label(value) for key, value in mapping.items()},
        "unmatched": [cp_label(cp) for cp in unmatched],
        "ambiguous": {
            cp_label(key): [cp_label(value) for value in values]
            for key, values in ambiguous.items()
        },
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    original.close()
    patched.close()
    donor.close()
    print(f"changed={len(changed)} matched={len(mapping)} unmatched={len(unmatched)} ambiguous={len(ambiguous)}")


if __name__ == "__main__":
    main()


