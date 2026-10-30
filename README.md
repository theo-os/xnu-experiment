# iOS 16 on Pixel 7a (lynx): bring-up

This is an **early research scaffold**, not a bootable port. The target is Pixel 7a / Google Tensor G2 (GS201). The two checkouts in `work/` are references and are not modified by this project.

## Architecture

The intended route is an iOS 16-generation **XNU kernel**, not the Linux kernel running iOS binaries. Linux is the hardware and boot-flow reference; its drivers cannot simply be loaded into XNU. `work/Bergamota` supplies an existing XNU 8796 patch series and iOS 16 bring-up experience, built on [blacktop/darwin-xnu-build](https://github.com/blacktop/darwin-xnu-build). Its Qualcomm-specific loader, register addresses, drivers, device tree, and boot images are **not** valid Pixel implementations.

Reference snapshot inspected:

- Bergamota `37a7a7a917fc09945ed2f7d1ae68b84d4525b4cb`: `xnu/patches/` is the older 8796 series; `docs/IOS16_README.md` describes its earlier iOS 16 setup. Current default build and documentation target a later XNU, so do not assume its current workflow builds 8796.
- Android kernel `af5c65b9547a9f33c5f566430d0434aecab5a8b5`: `google-devices/gs201/dts/` has shared GS201 descriptions. `google-devices/gs201/BUILD.bazel` references `private/devices/google/lynx` for lynx DT overlays and modules, which are not present in this checkout. The lynx module list identifies two candidate panel drivers, not necessarily the panel on a particular device.

Run `python3 tools/reference_inventory.py` to check these local inputs. This does not build, contact a device, or change either checkout.
Stock image findings and the current reference-build investigation are recorded in [docs/stock-boot-investigation.md](docs/stock-boot-investigation.md). Run `python3 tools/inspect_stock.py` for a read-only summary of the supplied Android boot and DTBO headers.
The connected phone is a Pixel 7a on Android 17 CANARY (`ZP11.260918.007`), slot `_b`, hardware MP 1.0, with the S6E3FC5 panel. Its installed firmware is **newer and different** from the supplied `work/stock` archive. Read-only observations and limits are in [docs/device-snapshot.md](docs/device-snapshot.md). The live device tree is not readable from the `shell` domain, so an FDT comparison remains outstanding.

The pinned iOS 16 reference tree is **xnu-8796.141.3** with Bergamota's `ios16` patch snapshot. All 133 patches apply cleanly after the three upstream-source staging scripts run. The build now targets Xcode 27 with pinned `iig-tools` to restore the xnu-8796 IORPC ABI. A complete compile and matching KDK run are still outstanding; the CI workflow is included but unrun. Details: [docs/reference-xnu-build.md](docs/reference-xnu-build.md).

The full Bergamota series is **not** the GS201 build input. After auditing it, only 27 portable patches are retained; hardware and board-specific patches are deferred or replaced. `tools/prepare_gs201_tree.sh` builds that small tree and then applies GS201-only patches from `platform/gs201/patches/`. See [docs/patch-audit.md](docs/patch-audit.md) and [platform/gs201/README.md](platform/gs201/README.md).

## Initial milestones

1. **Establish hardware evidence.** Record device model, Android build, bootloader lock state, exact slot and boot image/header layout, live FDT and reserved memory, and the availability of a non-destructive boot path. Obtain the matching lynx device-specific sources/overlays and stock artifacts legally. Compare the live FDT with the shared GS201 DTS; don't assume addresses or framebuffer state. Keep device identifiers, calibration data, firmware and backups out of version control.
2. **Reproduce the reference build.** Pin a compatible historical 8796 build recipe and its darwin-xnu-build revision, compiler and dependencies; verify patch order and build the unmodified reference kernel before introducing a GS201 configuration. Record output hashes. The current Bergamota workflow is not itself evidence of a working 8796 build.
3. **Boot contract and early observability.** Determine the stock bootloader's accepted image and handoff, exception level, MMU/cache state, memory map, watchdog, and usable diagnostic output. Design a GS201-specific loader and XNU boot-args/Apple Device Tree handoff. First success is a repeatable early kernel marker, not iOS userland. Do not reuse Qualcomm MMIO initialization.
4. **Minimal XNU platform.** Bring up memory, timer, interrupts, and a single CPU; then SMP and a reliable log transport. Port or replace only the platform-independent portions of the reference patches after auditing dependencies. Use the GS201 Linux code as a hardware reference with appropriate license review.
5. **Storage and userland.** Implement and validate read-only storage access first, then a separately provisioned root filesystem and XNU services needed for launchd. An iOS 16 userland, Apple device identity data and firmware must be obtained separately and lawfully; compatibility, code signing, PAC/arm64e and security assumptions require investigation. Nothing here provides or prepares those artifacts.
6. **Display and input, then peripherals.** Investigate a handed-off framebuffer and software rendering before display controller, touch, USB, power, GPU, modem or other drivers. No peripheral is currently supported.

## Safety

Unlocking may erase data and reduce security. Back up data and relevant partitions using a device-appropriate, verified procedure before any experiment. Do not flash, erase `userdata`, or use Bergamota's Poco F1 commands on the Pixel. `fastboot boot` support, recovery options and partition layout must be verified for the exact device and firmware; a failed boot can leave a device unrecoverable. This project currently provides no flashing or boot instructions.
