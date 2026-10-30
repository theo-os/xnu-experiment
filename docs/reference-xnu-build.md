# Pinned iOS 16 XNU reference tree

Goal: establish a reproducible xnu-8796 source tree before adding any GS201 code.

This page records the **full-series validation** used to prove the historical recipe works. The actual GS201 tree uses only 27 portable patches and is prepared by `tools/prepare_gs201_tree.sh`; see [patch-audit.md](patch-audit.md).

| Input | Pin |
| --- | --- |
| XNU | `apple-oss-distributions/xnu` tag `xnu-8796.141.3`, commit `1b191cb58250d0705d8a51287127505aa4bc0789` |
| Build script | `blacktop/darwin-xnu-build` commit `663906528d1cd5ea8fde7de6f16de73db9511549` |
| Bergamota series | branch `ios16`, commit `305b17c3fc38514949d6ecd40e9f45bc5ca49a85`, `xnu/patches/` |
| Staged libpthread | `a6c70ca0e544347a0377babf748f831577ec24f9` (libpthread-514.100.2) |
| Staged BearSSL | `7bea48e5e850ab4cafbe68d3765cdaba13a86d6f` |
| Staged HFS | `31d5ec238dfab485e78a9a30b8b92d13e8914f03` (hfs-627.100.6) |
| iig replacement | `theo-os/iig-tools` commit `96c1ece6be1ceb6ee2fec6c434d080edc10da2b1` |

The series snapshot contains 133 `.patch` files and three staging scripts. The staging scripts fetch the three upstream source trees, not patches. Their combined SHA-256 manifest hash is `50379888bd656b943dde9b9ebae93d01aa37faf7af686f5c31c4bde1d7afc3c3`.

## What was verified locally

On macOS 27.2 / Xcode 27.1, the source was cloned at the exact XNU tag. After running the three staging scripts, **all 133 Bergamota patches applied cleanly in filename order**, together with the applicable darwin-xnu-build patches. The worktree ended with 137 changed/untracked paths, 2,035 insertions and 162 deletions in tracked files, plus 153 staged upstream source files.

darwin-xnu-build patch outcomes:

- Applied: `kas_info.patch`, `machine_routines.patch`, `skywalk_ventura.patch`, `syntax_checker_ventura.patch`.
- Skipped by its normal "does not apply" rule: `iobuffermemd_monterey.patch`, `skywalk_sonoma.patch`, `syntax_checker_sonoma.patch` (they target other macOS releases or are already upstream for 13.5).
- Skipped: `TrustCache.patch`, because the `EXTERNAL_HEADERS/TrustCache/*` files already exist in xnu-8796.141.3.

No **complete** compile or link has been recorded. Xcode 27 itself is usable if `iig` is replaced: Apple's newer `iig` emits the `IORPC.kernelContent` ABI that xnu-8796 does not have. `theo-os/iig-tools` at the pin above generates the older kernel-side ABI. A local Xcode 27 build passed host-tool preparation and iig generation, then was stopped manually because the verbose compiler output was unmanageable; that is not evidence of a compile failure. The CI workflow uses the pinned iig-tools and must produce the first complete artifact and hash.

## Reproduce the source tree

```sh
# ignored working area
mkdir -p research/build
git init -q research/build/dxb
git -C research/build/dxb fetch -q --depth 1 \
  https://github.com/blacktop/darwin-xnu-build \
  663906528d1cd5ea8fde7de6f16de73db9511549
git -C research/build/dxb checkout -q FETCH_HEAD

git clone -q --branch xnu-8796.141.3 \
  https://github.com/apple-oss-distributions/xnu.git research/build/xnu
git -C research/build/xnu worktree add --detach ../xnu-ios16 \
  1b191cb58250d0705d8a51287127505aa4bc0789

mkdir -p research/build/patches-8796-ios16
git -C work/Bergamota archive 305b17c xnu/patches |
  tar -x -C research/build/patches-8796-ios16 --strip-components=2

cd research/build/xnu-ios16
export MACHINE_CONFIG=SWEET MACOS_VERSION=13.5
for script in ../patches-8796-ios16/*.sh; do bash "$script"; done
for patch in ../dxb/patches/*.patch ../patches-8796-ios16/*.patch; do
  git apply --check "$patch" 2>/dev/null && git apply "$patch"
done
git status --short
```

The loops intentionally ignore patches that do not apply to 13.5, matching darwin-xnu-build. For this pin, no Bergamota patch was skipped.

## Build with Xcode 27 and iig-tools

`.github/workflows/reference-xnu.yml` runs on the `xcode-27` runner. It fetches the same pins, builds the pinned `iig-tools`, verifies that its output contains no `kernelContent`, and exports it as `IIG` for darwin-xnu-build. It has **not been run yet**. The build writes its full verbose log to `build.log` and prints only the tail to the workflow console; the log is uploaded with the kernel artifact.

A local build needs Xcode 27, the 13.5 KDK, and the iig replacement:

```sh
iig="$PWD/research/build/iig"
c++ -std=c++17 -O2 -Wall -Wno-unused-function \
  -Iresearch/build/iig-tools/include \
  research/build/iig-tools/src/main.cpp \
  research/build/iig-tools/src/parse.cpp \
  research/build/iig-tools/src/codegen.cpp \
  -o "$iig"

cd research/build/dxb
cp ../../work/Bergamota/xnu/patches/* patches/   # pinned 13.5-compatible snapshot
IIG="$iig" MACOS_VERSION=13.5 KERNEL_CONFIG=DEVELOPMENT \
  MACHINE_CONFIG=SWEET ARCH_CONFIG=ARM64 ./build.sh > ../build.log 2>&1
tail -n 200 ../build.log
```

Do not claim reproducibility until a CI run or local build produces an artifact and records its hash and compiler version.

## Remaining reference gaps

- The SWEET machine configuration, UFS/HFS root, framebuffer and input drivers are Qualcomm/beryllium-specific. They are useful architecture examples, not GS201 implementations.
- No GS201 XNU machine configuration, interrupt controller, timer, UFS or display code exists yet.
- The next tree-level work is a minimal `GS201` machine configuration and platform bring-up, not importing the beryllium hardware patches wholesale.
