#!/usr/bin/env python3
"""Read-only structural inventory for common _N1G0000 G1N font files."""

from __future__ import annotations

import argparse
import hashlib
import struct
from pathlib import Path


CHARMAP_BYTES = 0x10000 * 2
GLYPH_RECORD_BYTES = 12


def u16(data: bytes, offset: int) -> int:
    return struct.unpack_from("<H", data, offset)[0]


def u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def inspect(path: Path) -> None:
    data = path.read_bytes()
    if len(data) < 0x24 or data[:8] != b"_N1G0000":
        raise ValueError("not a supported _N1G0000 file")
    declared_size = u32(data, 0x08)
    header_size = u32(data, 0x0C)
    palette_entry_value = u32(data, 0x10)
    atlas_offset = u32(data, 0x14)
    palette_count = u32(data, 0x18)
    table_count = u32(data, 0x1C)
    if declared_size != len(data):
        raise ValueError(f"declared size mismatch: {declared_size} != {len(data)}")
    expected_header = 0x20 + 4 * table_count + 0x40 * palette_count
    if header_size != expected_header:
        raise ValueError(
            f"header equation mismatch: 0x{header_size:X} != 0x{expected_header:X}"
        )
    table_offsets = [u32(data, 0x20 + 4 * index) for index in range(table_count)]
    if not table_offsets or table_offsets[0] != header_size:
        raise ValueError("first table does not begin at header end")
    if table_offsets != sorted(table_offsets) or table_offsets[-1] >= atlas_offset:
        raise ValueError("invalid table/atlas ordering")

    print(f"file={path}")
    print(f"bytes={len(data)}")
    print(f"sha256={hashlib.sha256(data).hexdigest()}")
    print(f"header_size=0x{header_size:X}")
    print(f"palette_entry_value={palette_entry_value}")
    print(f"palette_count={palette_count}")
    print(f"table_count={table_count}")
    print(f"atlas_offset=0x{atlas_offset:X}")
    for index, start in enumerate(table_offsets):
        end = table_offsets[index + 1] if index + 1 < table_count else atlas_offset
        payload = end - start
        if payload < CHARMAP_BYTES or (payload - CHARMAP_BYTES) % GLYPH_RECORD_BYTES:
            raise ValueError(f"table {index} has an unsupported size: 0x{payload:X}")
        record_count = (payload - CHARMAP_BYTES) // GLYPH_RECORD_BYTES
        cmap = [u16(data, start + cp * 2) for cp in range(0x10000)]
        nonzero = sum(value != 0 for value in cmap)
        print(
            f"table[{index}]=0x{start:X}..0x{end:X} "
            f"glyph_records={record_count} nonzero_cmap={nonzero} "
            f"max_glyph_id={max(cmap)}"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("g1n", type=Path)
    args = parser.parse_args()
    inspect(args.g1n)


if __name__ == "__main__":
    main()


