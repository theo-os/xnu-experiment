#!/bin/sh
# Build an ignored, pinned xnu-8796 tree with only the portable patch subset
# in platform/gs201/common-patches.txt, then any GS201 patches we add.
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
WORK="$ROOT/research/build/gs201"
XNU="$WORK/xnu"
PATCHES="$WORK/reference-patches"
BERGAMOTA="$ROOT/work/Bergamota"
BERGAMOTA_SHA=305b17c3fc38514949d6ecd40e9f45bc5ca49a85
XNU_TAG=xnu-8796.141.3
XNU_SHA=1b191cb58250d0705d8a51287127505aa4bc0789

test -d "$BERGAMOTA/.git" || {
    echo "missing Bergamota checkout at $BERGAMOTA" >&2
    exit 1
}
test "$(git -C "$BERGAMOTA" cat-file -t "$BERGAMOTA_SHA" 2>/dev/null)" = commit || {
    echo "Bergamota object $BERGAMOTA_SHA is unavailable; fetch the repository first" >&2
    exit 1
}

mkdir -p "$WORK"
if [ ! -d "$XNU/.git" ]; then
    git clone -q --branch "$XNU_TAG" https://github.com/apple-oss-distributions/xnu.git "$XNU"
fi
git -C "$XNU" fetch -q origin "refs/tags/$XNU_TAG:refs/tags/$XNU_TAG" 2>/dev/null || true
git -C "$XNU" checkout -q --detach "$XNU_SHA"
git -C "$XNU" reset -q --hard "$XNU_SHA"
git -C "$XNU" clean -fdq
test "$(git -C "$XNU" rev-parse HEAD)" = "$XNU_SHA"

rm -rf "$PATCHES"
mkdir -p "$PATCHES"
git -C "$BERGAMOTA" archive "$BERGAMOTA_SHA" xnu/patches |
    tar -x -C "$PATCHES" --strip-components=2

cd "$XNU"
export MACHINE_CONFIG=SWEET MACOS_VERSION=13.5
for script in "$PATCHES"/*.sh; do
    printf 'stage %s\n' "$(basename "$script")"
    sh "$script"
done

# Strip comments and blank lines from the selected patch numbers.
sed -e 's/#.*//' -e 's/[[:space:]]//g' "$ROOT/platform/gs201/common-patches.txt" |
    while IFS= read -r number; do
        [ -n "$number" ] || continue
        set -- "$PATCHES/$number"-*.patch
        [ "$#" -eq 1 ] && [ -f "$1" ] || {
            echo "expected one patch for $number, found $*" >&2
            exit 1
        }
        if ! git apply --check "$1" 2>"$WORK/apply.err"; then
            echo "patch $number does not apply:" >&2
            cat "$WORK/apply.err" >&2
            exit 1
        fi
        git apply "$1"
        printf 'apply %s\n' "$(basename "$1")"
    done

# GS201-specific patches are intentionally separate from the reference series.
if [ -d "$ROOT/platform/gs201/patches" ]; then
    for patch in "$ROOT"/platform/gs201/patches/*.patch; do
        [ -e "$patch" ] || continue
        if ! git apply --check "$patch" 2>"$WORK/apply.err"; then
            echo "GS201 patch does not apply: $patch" >&2
            cat "$WORK/apply.err" >&2
            exit 1
        fi
        git apply "$patch"
        printf 'apply %s\n' "$(basename "$patch")"
    done
fi

printf '\nGS201 tree ready at %s\n' "$XNU"
git status --short | wc -l | awk '{print $1 " changed/untracked paths"}'
