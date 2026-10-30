#!/usr/bin/env python3
"""Check the reference trees without modifying them or accessing a device."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
REPOS = {
    "Bergamota": ("work/Bergamota", "37a7a7a917fc09945ed2f7d1ae68b84d4525b4cb"),
    "Linux": ("work/android_kernel_google_tensynos", "af5c65b9547a9f33c5f566430d0434aecab5a8b5"),
}
REQUIRED = (
    "work/Bergamota/xnu/patches",
    "work/Bergamota/docs/IOS16_README.md",
    "work/android_kernel_google_tensynos/google-devices/gs201/dts/gs201.dtsi",
    "work/android_kernel_google_tensynos/google-devices/gs201/BUILD.bazel",
    "work/android_kernel_google_tensynos/google-devices/gs201/vendor_ramdisk.modules.devices",
)


def main():
    missing = False
    for path in REQUIRED:
        exists = (ROOT / path).exists()
        print(f"{'OK' if exists else 'MISSING'} {path}")
        missing |= not exists
    for name, (path, expected) in REPOS.items():
        try:
            sha = subprocess.check_output(
                ["git", "-C", str(ROOT / path), "rev-parse", "HEAD"],
                stderr=subprocess.DEVNULL, text=True,
            ).strip()
        except (OSError, subprocess.CalledProcessError):
            print(f"UNKNOWN {name} revision")
            continue
        print(f"{'MATCH' if sha == expected else 'DIFFERENT'} {name} revision {sha}")
    lynx = ROOT / "work/android_kernel_google_tensynos/private/devices/google/lynx"
    print(f"{'PRESENT' if lynx.is_dir() else 'NOT PRESENT'} Linux private lynx source at {lynx.relative_to(ROOT)}")
    return int(missing)


if __name__ == "__main__":
    sys.exit(main())
