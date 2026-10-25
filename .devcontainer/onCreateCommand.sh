#!/usr/bin/env bash
set -Eeuo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
workspace=$(dirname -- "$script_dir")
mkdir -p -- "$workspace/windows"
# GitHub CLI starts its own SSH session; provide a server and unique host keys.
install -d -m 0755 /run/sshd
ssh-keygen -A
install -d /usr/local/lib/windows-dind
printf '%s\n' "$workspace" > /usr/local/lib/windows-dind/workspace

for helper in start stop restart kill remove reset rebuild start-tailscale windows-doctor; do
    install -m 0755 "$script_dir/helpers/$helper" "/usr/local/bin/$helper"
done

docker compose version
qemu-img --version
tailscale version
echo 'Run start to prepare and boot Windows, then start-tailscale for RDP.'
