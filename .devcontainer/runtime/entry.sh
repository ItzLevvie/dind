#!/usr/bin/env bash
set -Eeuo pipefail
python3 /usr/local/lib/windows-dind/patch-boot.py
exec /run/entry.sh "$@"
