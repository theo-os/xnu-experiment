# GS201 / lynx platform work

Current scope: build a minimal xnu-8796 tree for the Pixel 7a without importing the SM7150/beryllium board port.

## Prepare the tree

```sh
tools/prepare_gs201_tree.sh
```

This creates `research/build/gs201/xnu` at `xnu-8796.141.3`, stages Apple's paired libpthread/BearSSL/HFS sources, applies the 27 portable patches in `common-patches.txt`, then applies any `platform/gs201/patches/*.patch` in filename order. It fails closed if a selected patch stops applying. See [docs/patch-audit.md](../../docs/patch-audit.md) for what was excluded.

## GS201 facts already established

- 8 CPUs, standard GICv3: distributor `0x10400000`, redistributors `0x10440000`; virtual timer INTID 27.
- Architected timer and PSCI 1.0; no Qualcomm timer numbering workaround.
- UFS at `0x14700000`, boot device `14700000.ufs`.
- USB: Synopsys DWC3 at `0x11210000`, Exynos USB PHY.
- Display: Samsung DECON/DPU, panel `s6e3fc5` on the connected MP 1.0 device.
- PMIC family: S2MPG12/S2MPG13; charger/fuel gauge MAX77759; touch Goodix Nottingham.
- The connected phone's live FDT is not readable from the `shell` domain. The supplied factory DTBs are for older firmware than the installed bootloader.

## Patch policy

- Reference patches never go directly into `platform/gs201/patches/` if they contain SM7150/beryllium addresses or assume `sweet_*` devices.
- New GS201 patches should be based on the small tree and carry their own device-tree keys.
- Do not add UFS, USB, touch, display or PMIC drivers just to satisfy a generic patch; define the GS201 service first.

## Next implementation steps

1. Add a minimal `MASTER.arm64.gs201` and `GS201.h`: 8 CPUs, 16 KiB pages, GICv3 Group 1, standard PPI 27, no PAC, open-source arm asm/pmap.
2. Add a GS201 platform expert that matches the GS201 device tree and does not require Apple SoC kexts.
3. Add the boot-CPU and GIC/timer path, with an early output route that does not assume the Poco F1 framebuffer address.
4. Establish the loader/boot-args/ADT contract and the first observable marker before adding storage or userland.
5. Only then add UFS, HFS root, display, touch and USB as separate GS201 drivers.
