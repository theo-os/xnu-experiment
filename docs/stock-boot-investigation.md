# Lynx stock boot investigation

Offline inspection of `work/stock`, no device accessed. The factory metadata says board `lynx`, bootloader `lynx-17.0-15902555`, Android build `CP3A.261005.002.A1`, and requires a `vendor_kernel_boot` partition. These images may not match the firmware or active slot on a particular phone. The factory `fastboot-info.txt` is an update recipe, **not** evidence that temporary boot works or a recommendation to flash it.

Reproduce the header inspection with `python3 tools/inspect_stock.py`; inspect AVB using `avbtool info_image --image work/stock/boot.img` (substitute other images). Sizes and offsets below are bytes.

| Image | Observed header / contents | AVB |
| --- | --- | --- |
| boot | Android v4, 4096-byte pages; kernel offset 4096, size 16637222; no ramdisk or v4 boot signature | Footer; signed SHA256_RSA4096 embedded vbmeta; original size 16658432 |
| init_boot | Android v4; no kernel; ramdisk offset 4096, size 2714527 | Footer; signed SHA256_RSA4096 embedded vbmeta; original size 2719744 |
| vendor_boot | Vendor v4, 2048-byte pages; vendor ramdisk size 24130254; DTB size 0 | Footer; embedded vbmeta algorithm NONE; original size 24139776 |
| vendor_kernel_boot | Vendor v4, 2048-byte pages; vendor ramdisk size 6177592; DTB offset 6182912, size 886583 | Footer; embedded vbmeta algorithm NONE; original size 7071744 |
| dtbo | Android DT table, 10 entries, total size 1092287 | Footer; embedded vbmeta algorithm NONE; original size 1092287 |

The v4 boot signature field is distinct from the AVB footer. `vbmeta.img` is signed with SHA256_RSA4096, flags 0; it chains `boot` at rollback-index location 2 and `init_boot` at 4, plus `vbmeta_system` at 1 and `vbmeta_vendor` at 3. It directly contains hash descriptors for `dtbo`, `vendor_boot` and `vendor_kernel_boot` (and other partitions). The standalone unsigned embedded vbmeta on those vendor images is therefore **not** proof that the stock chain accepts modifications: the top-level signed descriptors cover their original content. A new AVB footer alone does not make a modified image trusted by a locked bootloader.

`avbtool verify_image` succeeded separately for the five footer-bearing images above, using each image's embedded key or unsigned metadata as applicable. This establishes local consistency, **not** trust in an externally authenticated Google key, verification of the complete top-level chain, or behavior on the device. Rollback policy and unlocked-state behavior remain device-dependent. Do not alter vbmeta flags, keys or rollback indices as a shortcut.

SHA-256 of full supplied images, to identify this snapshot:

```text
f4c930e52f6f297d034416425a6c3a0f9c17fac8ce8eeabcab2748a7ffe8a775  boot.img
4c4c71545f4be554efa6148c52229f7f88aa5fb4a2e05838f9bdca482e4eaffb  init_boot.img
bfcdf43cf609247d0232181cf983c376a40e95b03c6651b2250c6dd8087d247a  vendor_boot.img
cccc3f28653e9e316ad7d40d0c9a3e6118363de35f65d87cb521e10dde0946b9  vendor_kernel_boot.img
58abf2abe62e05ea3eb33241c52dd36e01975eefd26fb294a820665f2dba6317  dtbo.img
9c784d3870398c0d9f94237f5daf54be9deb20ff932c8346ceed49881aa949db  vbmeta.img
```

## DTBO entries

The table has 10 overlays. Each overlay's root `board_id`/`board_rev` matches the table entry fields:

| Index | Table ID | Revision | Model |
| --- | --- | --- | --- |
| 0 | `0x30501` | `0x10000` | GS201 Lynx DEV 1.0 |
| 1 | `0x30502` | `0x10000` | GS201 Lynx PROTO 1.0 |
| 2 | `0x30502` | `0x10100` | GS201 Lynx PROTO 1.1 |
| 3 | `0x30503` | `0x10000` | GS201 Lynx EVT 1.0 |
| 4 | `0x30503` | `0x10100` | GS201 Lynx EVT 1.1 |
| 5 | `0x30503` | `0x10001` | GS201 Lynx EVT 1.0 Wingboard |
| 6 | `0x30504` | `0x10000` | GS201 Lynx DVT 1.0 |
| 7 | `0x30504` | `0x10001` | GS201 Lynx DVT 1.0, GAIN 1 calibration |
| 8 | `0x30505` | `0x10000` | GS201 Lynx PVT 1.0 |
| 9 | `0x30506` | `0x10000` | GS201 Lynx MP 1.0 |

The connected retail phone reports DTBO index **9** (MP 1.0), board ID `0x30506` and revision `0x10000`, so this archive's MP overlay is the relevant one. Every overlay contains the same candidate panel nodes (`s6e3fc3-l10`, `s6e3fc3-p10`, `s6e3fc5`); the live phone selects `panel-samsung-s6e3fc5`. See [device-snapshot.md](device-snapshot.md).

## Open questions

- What does the phone's final live FDT contain? This archive gives the candidate base and MP overlay, not the merged runtime tree. `/proc/device-tree` and `/sys/firmware/fdt` are denied to the `shell` domain, so no live copy has been read. Decode the installed slot's DTBs once a permitted read-only path exists, then compare.
- Does this exact bootloader support `fastboot boot`, and which images does it combine for that path? The vendor boot header addresses are legacy fields, not evidence of runtime load addresses. Confirm actual exception level, MMU/cache state, memory reservations, and observability before designing a loader. No reboot or fastboot attempt was made.
- The supplied factory archive does **not** match the connected phone's newer installed firmware or bootloader. Its AVB results cannot verify the installed chain, and it must not be flashed as a shortcut. The phone is currently unlocked, on slot `_b`; that is an observation, not a recommendation.

## XNU reference build

The pinned xnu-8796 source tree and all 133 Bergamota `ios16` patches were applied successfully locally after staging Apple's paired libpthread, BearSSL and HFS sources. A local Xcode 27 run got through host tools and `iig` generation using pinned `iig-tools`, then was stopped because of excessive verbose output; no complete build exists. A pinned, unrun CI workflow is at `.github/workflows/reference-xnu.yml`. Full pins, outcomes and remaining gaps are in [reference-xnu-build.md](reference-xnu-build.md).
