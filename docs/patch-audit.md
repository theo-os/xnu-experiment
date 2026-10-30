# Patch audit: what survives from the Sweet series

The 133-patch Bergamota `ios16` series is a complete **SM7150/beryllium** port. Keeping all of it would import Qualcomm UFS, USB, SPMI/RPMh, Adreno, MDP, touch, battery and Bluetooth drivers that do not match GS201. The series is also layered: many "generic" patches depend on files created by earlier hardware patches, so dropping arbitrary patches is not safe.

The GS201 build now starts from a deliberately small portable subset. The full 133-patch tree remains useful as an architectural reference, not as the build input.

## Applied to the GS201 tree

`platform/gs201/common-patches.txt` selects **27 patches**. `tools/prepare_gs201_tree.sh` starts from clean xnu-8796.141.3, runs the three upstream-source staging scripts, and applies this set. It succeeds today and leaves a 65-path modified tree.

| Area | Patches | Why portable |
| --- | --- | --- |
| Toolchain / arm64 build | 0001, 0002, 0005, 0011 | clang compatibility, UIO backport, non-PAC build, physical-map alignment |
| RNG / trust cache | 0013, 0014, 0015 | no CoreCrypto dependency, kernel PRNG, unavailable-trust-cache path |
| Apple open-source services | 0019, 0020, 0022, 0023, 0024, 0025, 0027, 0029, 0031, 0032, 0033, 0039, 0041 | libpthread, AES, SHA-1/256/384/512, MD5, mockfs/ramdisk, AMFI policy, HFS root, coredump |
| Generic BSD/IOKit diagnostics | 0042, 0048, 0049, 0052, 0070, 0080, 0106 | exec logging, `/dev/null` tee, IOKit trace, HFS rename, PID hibernate, network trace, LaunchServices reset |

The selection has no SM7150/beryllium register addresses. It is a kernel foundation only: it does not include a GS201 machine configuration, boot loader contract, storage, display, input or USB.

## Deferred generic work

These are useful concepts but do not apply on the small base because they depend on Sweet platform services or its master config. They should be **forward-ported into GS201 services**, not copied verbatim:

- AMFI/security: 0035, 0036, 0050, 0064, 0099, 0116.
- Crash/exception diagnostics: 0043, 0044, 0051, 0053, 0066.
- Storage and root setup: 0021, 0026, 0037, 0047, 0057.
- Sampling and console: 0054, 0055.
- HID/identity: 0058, 0059.
- Display framework: 0068, 0119, 0120, 0121, 0122, 0123.

## GS201 replacements required

These patches describe hardware or platform code whose **interfaces and addresses are wrong for GS201**. Reuse ideas where useful, but write new drivers:

| Subsystem | Bergamota patches | GS201 source facts |
| --- | --- | --- |
| Machine config, early console, platform expert, CPU/GIC/timer | 0003, 0004, 0006–0010, 0012, 0016–0018, 0040, 0045, 0065, 0078 | Standard GICv3 at `0x10400000`; architected timer PPI 27 virtual; 8 CPUs; no Qualcomm timer numbering |
| UFS / root storage | 0028, 0030, 0034, 0069, 0077, 0083, 0105 | Samsung Exynos UFS at `0x14700000`, not Qualcomm UFS |
| USB networking | 0072–0076, 0081, 0084, 0087, 0089, 0094, 0098, 0107, 0108, 0110 | Synopsys DWC3 at `0x11210000`, Exynos PHY; not the SM7150 glue |
| Display / GPU / surfaces | 0046, 0056, 0061, 0067, 0079, 0090, 0091, 0096, 0097, 0100, 0126, 0127, 0129 | Samsung DECON/DPU and S6E3FC5 panel; not MDP/Adreno |
| Touch, keys, battery, PMIC | 0060, 0062, 0063, 0071, 0086, 0088, 0092–0095, 0101, 0111–0114, 0130 | Goodix Nottingham touch, S2MPG12/13, MAX77759 charger/fuel gauge |
| Wi-Fi / Bluetooth / GPU firmware | 0103, 0104, 0117, 0118, 0124, 0125, 0128, 0132, 0133, 0136 | GS201 WCN6740/QCA6490 plus Mali-G710; nothing from WCN3990/Adreno 630 |
| Reboot reason | 0137 | Pixel reboot reason path differs from PM8998 PON |

## Beryllium tuning to discard

Patches 0082, 0085–0087, 0089, 0092–0096, 0098, 0101, 0103–0104, 0109, 0111–0114, 0117–0118, 0124–0130, 0132–0133, 0136–0137 are board-specific bring-up and workarounds. They should not be carried into the GS201 tree. Several are still valuable as a checklist of failure modes.

## Rule for new patches

A patch used for the Pixel must either:

1. touch only architecture/BSD/IOKit code with no target addresses, or
2. be explicitly in `platform/gs201/patches/` with GS201 device-tree values and no `sweet_*`/`beryllium_*` assumptions.

Do not re-enable the full series merely to make an unrelated patch apply. Rebase the concept onto the small GS201 base instead.
