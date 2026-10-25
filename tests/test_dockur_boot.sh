#!/usr/bin/env bash
# Run inside the pinned dockur image with this repository mounted at /source.
set -Eeuo pipefail
QEMU_DIR=$(mktemp -d)
trap 'rm -rf -- "$QEMU_DIR"' EXIT
isLegacyBoot() { return 1; }
source /run/power.sh

expect_status() {
    local expected=$1 status=0
    bootStatus || status=$?
    [[ "$status" == "$expected" ]] || {
        printf 'Expected boot status %s, got %s\n' "$expected" "$status" >&2
        exit 1
    }
}

generic='BdsDxe: starting Boot0002 "UEFI QEMU QEMU HARDDISK " from PciRoot(0x0)/Pci(0xA,0x0)/Scsi(0x0,0x0)'
printf '%s\n' "$generic" > "$QEMU_PTY"
expect_status 1  # Reproduce the unpatched watchdog's imported-disk rejection.
python3 /source/.devcontainer/runtime/patch-boot.py
before=$(sha256sum /run/power.sh)
python3 /source/.devcontainer/runtime/patch-boot.py
[[ "$before" == "$(sha256sum /run/power.sh)" ]]
source /run/power.sh
expect_status 3

printf '%s\n' 'BdsDxe: starting Boot0003 "Windows Boot Manager" from HD(1,GPT,abc)' > "$QEMU_PTY"
expect_status 3
printf '%s\n' 'BdsDxe: starting Boot0004 "UEFI QEMU QEMU DVD-ROM " from PciRoot(0x0)' > "$QEMU_PTY"
expect_status 4
printf '%s\n' "$generic" 'BdsDxe: failed to start Boot0002 "UEFI QEMU QEMU HARDDISK ": Not Found' > "$QEMU_PTY"
expect_status 5
printf '%s\n' "$generic" 'BdsDxe: No bootable option or device was found.' > "$QEMU_PTY"
expect_status 2
printf '%s\n' "$generic" 'UEFI Interactive Shell' > "$QEMU_PTY"
expect_status 2
printf '%s\n' 'unrecognized firmware output' > "$QEMU_PTY"
expect_status 1
echo 'Pinned dockur boot regression checks passed; known failure paths preserved.'
