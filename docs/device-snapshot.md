# Connected lynx device snapshot

Read-only `adb` inspection on 2026-10-30. The device was left running, unlocked in Android; no partition was read, written, erased or rebooted. Outputs are kept under ignored `research/device/` because they contain device identifiers. The serial number is deliberately omitted here.

| Property | Observed |
| --- | --- |
| Product / device | Pixel 7a (`lynx_beta` / `lynx`), model `Pixel_7a` |
| Build | Android 17 CANARY, `ZP11.260918.007`; boot image `CP21.260330.011` |
| Bootloader | `lynx-17.0-16268956`; bootloader EL3 `c-tfa` |
| Lock / verification | `flash.locked=0`, `verifiedbootstate=orange`, `veritymode=enforcing`, `device_state=unlocked` |
| Slot | `_b` |
| Hardware | revision `MP1.0`, SKU `GWKK3`, board ID `0x30506`, board revision `0x10000` (`cdt_hwid`) |
| SoC | `gs201`; 8 GiB Samsung LPDDR5; 4 KiB kernel page size |
| Storage | 128 GB Micron UFS; boot device `14700000.ufs` |
| DTBO | index `9`, the MP 1.0 entry |
| Panel | `panel-samsung-s6e3fc5`; kernel command line has `exynos_drm.panel_name=sdc-s6e3fc5` |

The live panel is therefore **Samsung S6E3FC5**, not S6E3FC3. The DTBO overlay carries nodes for all candidates; use the selected DTBO index and live panel property rather than assuming from the overlay alone.

## Mismatch with `work/stock`

The supplied stock set is **not** the firmware installed on this phone:

| | Supplied `work/stock` | Connected phone |
| --- | --- | --- |
| Bootloader | `lynx-17.0-15902555` | `lynx-17.0-16268956` |
| Android build | `CP3A.261005.002.A1` | system `ZP11.260918.007`, boot image `CP21.260330.011` |
| Slot at snapshot | unknown | `_b` |
| Panel | MP 1.0 overlay has all three candidate panel nodes | `s6e3fc5` |

Do not treat AVB results or offsets from the supplied images as verification of the installed boot chain. To compare, obtain the boot images actually installed on slot `_b` through a supported, read-only method and record their hashes. Shell access cannot read them here.

## Live device tree access

`/proc/device-tree` exists but is protected from the `shell` SELinux domain: reading `compatible`, `model` or `chosen/bootargs` returns `Permission denied`. Directory names are listable. The base FDT/sysfs copy at `/sys/firmware/fdt` is also denied. No root exploit or `adb root` was attempted. A live FDT comparison still requires either a permitted read-only path, a debug build with suitable policy, or the bootloader's exported DT/DTBO.

The installed kernel command line (from `/proc/cmdline`) confirms `gs201`, UFS boot, protected KVM, 8 CPUs, 4 KiB page assumptions in Android, `exynos_drm.panel_name=sdc-s6e3fc5`, and FIPS-related UFS ranges. These are Android kernel arguments, **not** an XNU boot contract.

## Boot-chain implications

- The phone is already unlocked and orange. That is the current state, not a recommendation to keep or change it.
- The installed firmware is newer than the supplied factory image. Flashing the older supplied bootloader/AVB set could trigger rollback protection or leave the device in a worse state. Do not flash it.
- `fastboot boot` support for this exact bootloader remains untested. Testing it changes device state and should be an explicit, backed-up decision; no such attempt was made.
- The next hardware evidence to collect is a **live FDT plus the installed `boot`, `init_boot`, `vendor_boot`, `vendor_kernel_boot`, `dtbo` and `vbmeta` images** from this phone, with hashes and slot recorded. Until then, design against the shared GS201 descriptions and the observed properties, not against the mismatched factory archive.

Reproduce the stock-DTB summary with `python3 tools/extract_stock_dtb.py && python3 tools/dtb_summary.py`. Reproduce the device properties with ordinary read-only `adb shell getprop` queries. The parser is not a substitute for hardware documentation.
