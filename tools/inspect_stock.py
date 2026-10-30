#!/usr/bin/env python3
"""Read boot and DTBO headers only; never modifies or extracts stock images."""
import argparse
import struct
from pathlib import Path


def u32(buf, offset, endian="<"):
    return struct.unpack_from(endian + "I", buf, offset)[0]


def aligned(value, page):
    if not page or page & (page - 1):
        raise ValueError(f"invalid page size {page}")
    return (value + page - 1) & ~(page - 1)


def inspect(path):
    with path.open("rb") as f:
        head = f.read(4096)
    size = path.stat().st_size
    if len(head) < 2128:
        raise ValueError("image too short")
    print(f"\n{path.name}: {size} bytes")
    if head[:8] == b"ANDROID!":
        version = u32(head, 40)
        if version not in (3, 4):
            raise ValueError(f"unsupported Android boot header version {version}")
        kernel, ramdisk, os_version, header_size = struct.unpack_from("<4I", head, 8)
        signature = u32(head, 1580) if version == 4 else 0
        print(f"  Android boot v{version}, header={header_size}, page=4096, os_version=0x{os_version:08x}")
        print(f"  kernel: offset=4096 size={kernel}; ramdisk: offset={4096 + aligned(kernel, 4096)} size={ramdisk}; boot signature size={signature}")
    elif head[:8] == b"VNDRBOOT":
        version, page, kernel_addr, ramdisk_addr, ramdisk = struct.unpack_from("<5I", head, 8)
        if version not in (3, 4):
            raise ValueError(f"unsupported vendor boot header version {version}")
        header_size, dtb_size = struct.unpack_from("<2I", head, 2096)
        dtb_addr = struct.unpack_from("<Q", head, 2104)[0]
        dtb_offset = aligned(header_size, page) + aligned(ramdisk, page)
        print(f"  vendor boot v{version}, header={header_size}, page={page}")
        print(f"  vendor ramdisk: offset={aligned(header_size, page)} size={ramdisk}; DTB: offset={dtb_offset} size={dtb_size}")
        print(f"  legacy header addresses: kernel=0x{kernel_addr:x} ramdisk=0x{ramdisk_addr:x} dtb=0x{dtb_addr:x} (not proven handoff addresses)")
        if version == 4:
            table_size, entries, entry_size, bootconfig = struct.unpack_from("<4I", head, 2112)
            print(f"  ramdisk table: size={table_size} entries={entries} entry_size={entry_size}; bootconfig size={bootconfig}")
    elif head[:4] == b"\xd7\xb7\xab\x1e":
        total, header_size, entry_size, entries, entry_offset, page, version = struct.unpack_from(">7I", head, 4)
        print(f"  DT table: total={total} header={header_size} entry_size={entry_size} entries={entries} entry_offset={entry_offset} page={page} version={version}")
        if total > size or header_size < 32 or entry_size < 32 or entry_offset + entries * entry_size > total:
            raise ValueError("invalid DT table bounds")
    else:
        raise ValueError("unrecognized image magic")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?", type=Path, default=Path(__file__).resolve().parent.parent / "work/stock")
    args = parser.parse_args()
    failed = False
    for name in ("boot", "init_boot", "vendor_boot", "vendor_kernel_boot", "dtbo"):
        try:
            inspect(args.directory / (name + ".img"))
        except (OSError, ValueError, struct.error) as exc:
            print(f"{name}: ERROR: {exc}")
            failed = True
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
