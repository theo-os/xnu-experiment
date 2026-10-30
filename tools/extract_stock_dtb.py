#!/usr/bin/env python3
"""Extract retained stock DTB/DTBO copies into research/stock for offline analysis."""
import argparse
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FDT_MAGIC = b"\xd0\x0d\xfe\xed"
DTBO_MAGIC = b"\xd7\xb7\xab\x1e"


def within(path, offset, size):
    if offset < 0 or size < 0 or offset + size > path.stat().st_size:
        raise ValueError("invalid image bounds")


def extract_vendor_dtbs(path, outdir):
    blob = path.read_bytes()
    if blob[:8] != b"VNDRBOOT":
        raise ValueError("not an Android vendor boot image")
    version, page, _kernel, _ramdisk_address, ramdisk_size = struct.unpack_from("<5I", blob, 8)
    if version not in (3, 4) or not page or page & (page - 1):
        raise ValueError(f"unsupported vendor boot header {version}")
    header_size, dtb_size = struct.unpack_from("<2I", blob, 2096)
    offset = ((header_size + page - 1) & ~(page - 1)) + ((ramdisk_size + page - 1) & ~(page - 1))
    within(path, offset, dtb_size)
    data = blob[offset:offset + dtb_size]
    outdir.mkdir(parents=True, exist_ok=True)
    pos = count = 0
    while pos + 8 <= len(data) and data[pos:pos + 4] == FDT_MAGIC:
        total = struct.unpack_from(">I", data, pos + 4)[0]
        if total < 40 or pos + total > len(data):
            raise ValueError(f"invalid FDT at offset {pos}")
        (outdir / f"vendor-{count:02d}.dtb").write_bytes(data[pos:pos + total])
        print(f"vendor-{count:02d}.dtb: {total} bytes")
        pos += total
        count += 1
    if pos != len(data):
        raise ValueError(f"{len(data) - pos} unexplained bytes after vendor DTB data")


def extract_dtbo(path, outdir):
    blob = path.read_bytes()
    if blob[:4] != DTBO_MAGIC:
        raise ValueError("not an Android DT table")
    _total, _header, entry_size, count, entry_offset, _page, _version = struct.unpack_from(">7I", blob, 4)
    if count > 10000 or entry_offset + count * entry_size > len(blob):
        raise ValueError("invalid DT table bounds")
    outdir.mkdir(parents=True, exist_ok=True)
    for i in range(count):
        size, offset, ident, rev = struct.unpack_from(">4I", blob, entry_offset + i * entry_size)
        within(path, offset, size)
        (outdir / f"dtbo-{i:02d}.dtb").write_bytes(blob[offset:offset + size])
        print(f"dtbo-{i:02d}.dtb: {size} bytes, id=0x{ident:x}, rev=0x{rev:x}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stock", type=Path, default=ROOT / "work/stock")
    parser.add_argument("--out", type=Path, default=ROOT / "research/stock")
    args = parser.parse_args()
    try:
        extract_vendor_dtbs(args.stock / "vendor_kernel_boot.img", args.out / "dtb")
        extract_dtbo(args.stock / "dtbo.img", args.out / "dtbo")
    except (OSError, ValueError, struct.error) as exc:
        print(f"ERROR: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
