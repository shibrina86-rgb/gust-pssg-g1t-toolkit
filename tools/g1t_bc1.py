#!/usr/bin/env python3
"""Extract and rebuild a common fixed-header BC1 G1T texture variant."""

from __future__ import annotations

import argparse
import io
import struct
from pathlib import Path

from PIL import Image


DDS_HEADER_SIZE = 128
G1T_DATA_OFFSET = 64


def dds_header(width: int, height: int) -> bytes:
    linear_size = ((width + 3) // 4) * ((height + 3) // 4) * 8
    flags = 0x1 | 0x2 | 0x4 | 0x1000 | 0x80000
    header = b"DDS " + struct.pack("<I", 124)
    header += struct.pack("<I", flags)
    header += struct.pack("<III", height, width, linear_size)
    header += struct.pack("<I", 0) + struct.pack("<I", 1) + b"\0" * 44
    header += struct.pack("<I", 32) + struct.pack("<I", 4) + b"DXT1" + b"\0" * 20
    header += struct.pack("<IIIII", 0x1000, 0, 0, 0, 0)
    return header


def read_g1t(path: Path) -> tuple[bytes, int, int, bytes]:
    data = path.read_bytes()
    if len(data) < G1T_DATA_OFFSET or data[:4] != b"GT1G":
        raise ValueError(f"not a supported G1T: {path}")
    if data[37] != 0x59:
        raise ValueError(f"expected BC1 type 0x59: {path}")
    width, height = struct.unpack_from("<II", data, 56)
    raw = data[G1T_DATA_OFFSET:]
    expected = ((width + 3) // 4) * ((height + 3) // 4) * 8
    if len(raw) != expected:
        raise ValueError(f"BC1 length mismatch: {path} ({len(raw)} != {expected})")
    return data, width, height, raw


def extract_one(path: Path, output: Path) -> None:
    _, width, height, raw = read_g1t(path)
    image = Image.open(io.BytesIO(dds_header(width, height) + raw)).convert("RGBA")
    image = image.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)


def rebuild_one(original: Path, edited_png: Path, output: Path, platform: int) -> None:
    data, width, height, original_raw = read_g1t(original)
    image = Image.open(edited_png).convert("RGBA")
    if image.size != (width, height):
        raise ValueError(f"image size changed: {edited_png} {image.size} != {(width, height)}")
    image = image.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    buffer = io.BytesIO()
    image.save(buffer, format="DDS", pixel_format="DXT1")
    encoded = buffer.getvalue()
    if encoded[:4] != b"DDS ":
        raise ValueError("Pillow did not emit DDS")
    raw = encoded[DDS_HEADER_SIZE:]
    if len(raw) != len(original_raw):
        raise ValueError(f"encoded size changed: {len(raw)} != {len(original_raw)}")
    rebuilt = bytearray(data)
    rebuilt[G1T_DATA_OFFSET:] = raw
    struct.pack_into("<I", rebuilt, 20, platform)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(rebuilt)
    if len(rebuilt) != len(data):
        raise ValueError("G1T size changed")


def parse_platform(value: str) -> int:
    return int(value, 0)


def main() -> None:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    extract = commands.add_parser("extract")
    extract.add_argument("input_dir", type=Path)
    extract.add_argument("output_dir", type=Path)
    extract.add_argument("--glob", default="*.g1t")
    rebuild = commands.add_parser("rebuild")
    rebuild.add_argument("original_dir", type=Path)
    rebuild.add_argument("edited_dir", type=Path)
    rebuild.add_argument("output_dir", type=Path)
    rebuild.add_argument("--glob", default="*.g1t.png")
    rebuild.add_argument("--platform", type=parse_platform, default=0x10)
    args = parser.parse_args()

    if args.command == "extract":
        files = sorted(args.input_dir.glob(args.glob))
        for source in files:
            extract_one(source, args.output_dir / f"{source.name}.png")
        print(f"extracted={len(files)}")
    else:
        files = sorted(args.edited_dir.glob(args.glob))
        for edited in files:
            original_name = edited.name.removesuffix(".png")
            original = args.original_dir / original_name
            rebuild_one(original, edited, args.output_dir / original_name, args.platform)
        print(f"rebuilt={len(files)}")


if __name__ == "__main__":
    main()


