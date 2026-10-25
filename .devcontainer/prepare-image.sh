#!/usr/bin/env bash
set -Eeuo pipefail
# shellcheck source=helpers/common.sh
source "$(dirname -- "${BASH_SOURCE[0]}")/helpers/common.sh"

if [[ -s "$storage/data.img" && "${1:-}" != --replace ]]; then
    if [[ -f "$storage/microsoft-install.json" && ! -f "$storage/windows.boot" ]]; then
        # A verified installer may not yet have partitioned the new disk.
        python3 "$workspace/.devcontainer/prepare-microsoft.py"
        exit 0
    fi
    check_boot_data "$storage/data.img"
    echo 'Keeping the existing Windows disk.'
    # Migrate an existing disk whose first-run marker was never written.
    [[ -e "$storage/windows.boot" ]] || printf 'data.img\n' > "$storage/windows.boot"
    exit 0
fi

# The author's newest preview expired on 2026-08-11. New installations use
# verified, non-evaluation Microsoft media; existing Windows disks are retained.
if [[ -z "${WINDOWS_SOURCE_VHDX:-}" && "${WINDOWS_SOURCE:-microsoft}" == microsoft ]]; then
    exec python3 "$workspace/.devcontainer/prepare-microsoft.py" "$@"
fi
[[ -n "${WINDOWS_SOURCE_VHDX:-}" || "${WINDOWS_SOURCE:-microsoft}" == itzlevvie ]] || fail 'WINDOWS_SOURCE must be microsoft or itzlevvie.'

cache=${WINDOWS_IMAGE_CACHE:-/tmp/windows-dind-image}
mkdir -p -- "$cache"
exec 7> "$cache/.download.lock"
flock -n 7 || fail 'Another Windows image import is running.'
source_image=${WINDOWS_SOURCE_VHDX:-}
partial="$storage/data.img.partial"
trap 'rm -f -- "$partial"' EXIT

if [[ -z "$source_image" && -s "$cache/data.vhdx" && -f "$cache/.extracted-29599-1" ]]; then
    source_image="$cache/data.vhdx"
fi

if [[ -z "$source_image" ]]; then
    available=$(df --output=avail --block-size=1 "$cache" | tail -n 1)
    cached=$(du --bytes --summarize "$cache" | cut -f 1)
    ((available + cached >= 19 * 1024 * 1024 * 1024)) || fail 'At least 19 GiB of staging capacity is required for this Windows release. Set WINDOWS_IMAGE_CACHE to a larger disk-backed filesystem or free scratch space.'
    release=https://github.com/ItzLevvie/artifacts/releases/download/29599-1
    while read -r digest filename; do
        [[ -n "$digest" ]] || continue
        if [[ -f "$cache/$filename" ]] && printf '%s  %s\n' "$digest" "$cache/$filename" | sha256sum --check --status -; then
            continue
        fi
        rm -f -- "$cache/$filename"
        if ! { [[ -f "$cache/$filename.partial" ]] && printf '%s  %s\n' "$digest" "$cache/$filename.partial" | sha256sum --check --status -; }; then
            echo "Downloading $filename (resumable)..."
            curl --fail --location --retry 3 --retry-all-errors --connect-timeout 30 \
                --continue-at - "$release/$filename" --output "$cache/$filename.partial"
        fi
        if ! printf '%s  %s\n' "$digest" "$cache/$filename.partial" | sha256sum --check --status -; then
            rm -f -- "$cache/$filename.partial"
            fail "Checksum mismatch for $filename. The existing Windows disk was preserved; retry start."
        fi
        mv -f -- "$cache/$filename.partial" "$cache/$filename"
    done < "$workspace/.devcontainer/image.sha256"

    # Read the exact extraction size rather than assuming the VHDX will fit.
    listing=$(7z l -slt "$cache/data.7z.001")
    extracted_size=$(printf '%s\n' "$listing" | python3 -c '
import sys
for block in sys.stdin.read().split("\n\n"):
    fields = dict(line.split(" = ", 1) for line in block.splitlines() if " = " in line)
    if fields.get("Path") == "data.vhdx":
        print(fields["Size"])
        break
else:
    raise SystemExit("The archive does not contain data.vhdx")')
    [[ "$extracted_size" =~ ^[0-9]+$ ]] || fail 'Cannot determine VHDX extraction size.'
    available=$(df --output=avail --block-size=1 "$cache" | tail -n 1)
    ((available >= extracted_size + 1024 * 1024 * 1024)) || fail 'The VHDX does not fit in staging. Set WINDOWS_IMAGE_CACHE to a larger filesystem.'
    7z x -y "$cache/data.7z.001" "-o$cache" data.vhdx
    touch "$cache/.extracted-29599-1"
    source_image="$cache/data.vhdx"
fi

[[ -s "$source_image" ]] || fail "VHDX source not found: $source_image"
image_info=$(qemu-img info --output=json "$source_image")
read -r required virtual_size < <(printf '%s' "$image_info" | python3 -c '
import json,sys
x=json.load(sys.stdin)
if x["format"] != "vhdx":
    raise SystemExit("The source must be a VHDX image")
print(x["actual-size"], x["virtual-size"])')

rm -f -- "$partial"
available=$(df --output=avail --block-size=1 "$storage" | tail -n 1)
((available >= required + 2 * 1024 * 1024 * 1024)) || fail 'Insufficient workspace space for a sparse raw disk and 2 GiB headroom. The old Windows disk is intact.'

qemu-img convert -p -f vhdx -O raw -o preallocation=off -S 4k "$source_image" "$partial"
actual_size=$(qemu-img info --output=json -f raw "$partial" | python3 -c 'import json,sys; print(json.load(sys.stdin)["virtual-size"])')
[[ "$actual_size" == "$virtual_size" ]] || fail 'The converted disk has an unexpected size. The old Windows disk was preserved.'
check_boot_data "$partial"
mv -f -- "$partial" "$storage/data.img"
printf 'data.img\n' > "$storage/windows.boot"

if [[ -z "${WINDOWS_SOURCE_VHDX:-}" ]]; then
    rm -f -- "$cache/data.vhdx" "$cache/.extracted-29599-1" "$cache"/data.7z.00[1-5]
fi
echo 'Windows image imported successfully.'
