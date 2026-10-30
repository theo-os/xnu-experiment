#!/usr/bin/env python3
"""Summarize root properties of extracted FDTs and DTBO table identity fields."""
import argparse
import struct
from pathlib import Path

MAGIC = b"\xd0\x0d\xfe\xed"


def u32(b, off):
    return struct.unpack_from(">I", b, off)[0]


def parse_string(strings, offset):
    if offset >= len(strings):
        raise ValueError("bad property name offset")
    end = strings.find(b"\0", offset)
    if end < 0:
        raise ValueError("unterminated property name")
    return strings[offset:end].decode("ascii", "replace")

def parse_fdt(blob, found=None):
    if blob[:4] != MAGIC:
        raise ValueError("not an FDT")
    total, struct_off, str_off = struct.unpack_from(">3I", blob, 4)
    str_size, struct_size = struct.unpack_from(">2I", blob, 32)
    if total > len(blob) or struct_off + struct_size > total or str_off + str_size > total:
        raise ValueError("invalid FDT bounds")
    strings = blob[str_off:str_off + str_size]
    pos = struct_off
    end = struct_off + struct_size
    depth = 0
    root_props = {}
    path = []
    while pos + 4 <= end:
        token = u32(blob, pos)
        pos += 4
        if token == 1:  # FDT_BEGIN_NODE
            nul = blob.find(b"\0", pos, end)
            if nul < 0:
                raise ValueError("unterminated node name")
            name = blob[pos:nul].decode("ascii", "replace")
            path.append(name)
            depth += 1
            pos = (nul + 1 + 3) & ~3
        elif token == 2:  # FDT_END_NODE
            if not path:
                raise ValueError("unbalanced node")
            path.pop()
            depth -= 1
        elif token == 3:  # FDT_PROP
            if pos + 8 > end:
                raise ValueError("truncated property")
            length, name_off = struct.unpack_from(">2I", blob, pos)
            pos += 8
            value = blob[pos:pos + length]
            if len(value) != length or pos + length > end:
                raise ValueError("truncated property value")
            pos = (pos + length + 3) & ~3
            if name_off >= len(strings):
                raise ValueError("bad property name offset")
            name = parse_string(strings, name_off)
            if depth == 1:
                root_props[name] = value
            if found is not None and name in ("model", "board_id", "board_rev"):
                found.setdefault(name, value)
        elif token == 4:  # FDT_NOP
            continue
        elif token == 9:  # FDT_END
            break
        else:
            raise ValueError(f"unknown FDT token {token:#x}")
    return root_props


def hex32(value):
    return f"0x{struct.unpack('>I', value)[0]:x}" if len(value) == 4 else printable(value)


def printable(value):
    if value.endswith(b"\0") and b"\0" not in value[:-1]:
        text = value[:-1].decode("ascii", "replace")
        if text.isprintable():
            return f'"{text}"'
    if len(value) in (4, 8):
        vals = struct.unpack(">" + "I" * (len(value) // 4), value)
        return "<" + " ".join(f"0x{x:x}" for x in vals) + ">"
    return value.hex()


def dtbo_entries(path):
    blob = path.read_bytes()
    if blob[:4] != b"\xd7\xb7\xab\x1e":
        raise ValueError("not an Android DT table")
    _total, _header, entry_size, count, entry_off, _page, _version = struct.unpack_from(">7I", blob, 4)
    if count > 10000 or entry_off + count * entry_size > len(blob):
        raise ValueError("invalid DT table bounds")
    entries = []
    for i in range(count):
        size, off, ident, rev = struct.unpack_from(">4I", blob, entry_off + i * entry_size)
        if off + size > len(blob):
            raise ValueError(f"invalid DTBO entry {i}")
        found = {}
        props = parse_fdt(blob[off:off + size], found)
        entries.append((i, size, ident, rev, props, found))
    return entries


def main():
    root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dtb-dir", type=Path, default=root / "research/stock/dtb")
    parser.add_argument("--dtbo-image", type=Path, default=root / "work/stock/dtbo.img")
    args = parser.parse_args()
    failed = False
    for path in sorted(args.dtb_dir.glob("vendor-*.dtb")):
        try:
            props = parse_fdt(path.read_bytes())
            print(f"\n{path.name}")
            for key in ("model", "compatible", "board_id", "board_rev"):
                if key in props:
                    print(f"  {key}: {printable(props[key])}")
        except (OSError, ValueError, struct.error) as exc:
            print(f"{path.name}: ERROR: {exc}")
            failed = True
    table = args.dtbo_image
    if table.exists():
        try:
            for i, size, ident, rev, _props, found in dtbo_entries(table):
                model = printable(found["model"]) if "model" in found else "?"
                board_id = hex32(found["board_id"]) if "board_id" in found else "?"
                board_rev = hex32(found["board_rev"]) if "board_rev" in found else "?"
                print(f"dtbo[{i}] size={size} id={board_id} rev={board_rev} table_id=0x{ident:x} table_rev=0x{rev:x} model={model}")
        except (OSError, ValueError, struct.error) as exc:
            print(f"dtbo summary: ERROR: {exc}")
            failed = True
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
