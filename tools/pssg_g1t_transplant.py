#!/usr/bin/env python3
"""Inspect or safely transplant same-sized G1T blocks between PSSG files."""

from __future__ import annotations

import argparse
import hashlib
import re
import struct
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class G1TBlock:
    name: str
    offset: int
    total_size: int
    header_size: int
    texture_count: int
    platform: int


def parse_blocks(data: bytes) -> list[G1TBlock]:
    blocks: list[G1TBlock] = []
    position = 0
    while True:
        offset = data.find(b"GT1G", position)
        if offset < 0:
            break
        if offset + 28 > len(data):
            break
        _, _, total, header, count, platform, _ = struct.unpack_from(
            "<4s4sIIIII", data, offset
        )
        if total < 28 or offset + total > len(data) or not 1 <= count <= 64:
            position = offset + 4
            continue
        nearby = data[max(0, offset - 160) : offset]
        names = list(re.finditer(rb"[A-Za-z0-9_-]+\.g1t", nearby, re.I))
        if not names:
            raise ValueError(f"G1T at 0x{offset:X} has no nearby resource name")
        name = names[-1].group().decode("ascii")
        blocks.append(G1TBlock(name, offset, total, header, count, platform))
        position = offset + total
    return blocks


def inspect(path: Path) -> None:
    data = path.read_bytes()
    blocks = parse_blocks(data)
    print(f"file={path}")
    print(f"bytes={len(data)}")
    print(f"sha256={hashlib.sha256(data).hexdigest()}")
    print(f"g1t_blocks={len(blocks)}")
    for block in blocks:
        print(
            f"{block.name}\toffset=0x{block.offset:X}\tsize={block.total_size}"
            f"\theader={block.header_size}\ttextures={block.texture_count}"
            f"\tplatform=0x{block.platform:X}"
        )


def transplant(switch_path: Path, source_path: Path, output_path: Path) -> None:
    switch_data = switch_path.read_bytes()
    source_data = source_path.read_bytes()
    destinations = parse_blocks(switch_data)
    sources = parse_blocks(source_data)

    if not destinations:
        raise ValueError("Switch PSSG contains no recognized G1T blocks")
    if len(destinations) != len(sources):
        raise ValueError(
            f"block count mismatch: Switch={len(destinations)}, source={len(sources)}"
        )
    source_by_name = {block.name: block for block in sources}
    if len(source_by_name) != len(sources):
        raise ValueError("duplicate resource names in source PSSG")

    output = bytearray(switch_data)
    for destination in destinations:
        source = source_by_name.get(destination.name)
        if source is None:
            raise ValueError(f"missing source resource: {destination.name}")
        source_shape = (source.total_size, source.header_size, source.texture_count)
        destination_shape = (
            destination.total_size,
            destination.header_size,
            destination.texture_count,
        )
        if source_shape != destination_shape:
            raise ValueError(f"incompatible G1T structure: {destination.name}")
        payload = bytearray(
            source_data[source.offset : source.offset + source.total_size]
        )
        struct.pack_into("<I", payload, 20, 0x10)
        output[
            destination.offset : destination.offset + destination.total_size
        ] = payload

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(output)
    verified = output_path.read_bytes()
    verified_blocks = parse_blocks(verified)

    if len(verified) != len(switch_data):
        raise ValueError("output PSSG size changed")
    if [item.name for item in verified_blocks] != [item.name for item in destinations]:
        raise ValueError("resource order changed")
    if any(item.platform != 0x10 for item in verified_blocks):
        raise ValueError("one or more G1T blocks are not Switch platform 0x10")

    print(f"transplanted={len(verified_blocks)}")
    print(f"bytes={len(verified)} (unchanged)")
    print(f"sha256={hashlib.sha256(verified).hexdigest()}")


def main() -> None:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    inspect_parser = commands.add_parser("inspect")
    inspect_parser.add_argument("pssg", type=Path)
    transplant_parser = commands.add_parser("transplant")
    transplant_parser.add_argument("switch_pssg", type=Path)
    transplant_parser.add_argument("source_pssg", type=Path)
    transplant_parser.add_argument("output_pssg", type=Path)
    args = parser.parse_args()

    if args.command == "inspect":
        inspect(args.pssg)
    else:
        transplant(args.switch_pssg, args.source_pssg, args.output_pssg)


if __name__ == "__main__":
    main()


