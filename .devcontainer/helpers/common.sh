#!/usr/bin/env bash
set -Eeuo pipefail

if [[ -n "${WINDOWS_WORKSPACE:-}" ]]; then
    workspace=$WINDOWS_WORKSPACE
elif [[ -f /usr/local/lib/windows-dind/workspace ]]; then
    IFS= read -r workspace < /usr/local/lib/windows-dind/workspace
else
    workspace=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
fi
storage="$workspace/windows"
mkdir -p -- "$storage"
compose_file="$storage/windows.yaml"
export WINDOWS_WORKSPACE="$workspace"
unset DOCKER_HOST DOCKER_CONTEXT DOCKER_TLS DOCKER_TLS_VERIFY DOCKER_CERT_PATH
export DOCKER_HOST=unix:///var/run/docker.sock

fail() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

vm_lock() {
    exec 9> "$storage/.vm.lock"
    flock -n 9 || fail 'Another Windows lifecycle command is running.'
}

ensure_docker() {
    # Use the local daemon, even if a shell has selected a remote Docker context.
    unset DOCKER_HOST DOCKER_CONTEXT DOCKER_TLS DOCKER_TLS_VERIFY DOCKER_CERT_PATH
    export DOCKER_HOST=unix:///var/run/docker.sock
    docker info >/dev/null 2>&1 && return 0
    [[ $(id -u) == 0 ]] || fail 'Docker is unavailable. Reopen the devcontainer as root.'
    mkdir -p /run/windows-dind
    (
        flock -w 60 8 || exit 1
        docker info >/dev/null 2>&1 && exit 0
        if ! pgrep -x dockerd >/dev/null; then
            rm -f /var/run/docker.pid
            # Lifecycle and SSH shells can terminate their process group on exit.
            # Start a separate session so the daemon survives that cleanup.
            nohup setsid --fork dockerd > /run/windows-dind/docker.log 2>&1 </dev/null 8>&- 9>&- &
        fi
        for ((attempt=0; attempt<60; attempt++)); do
            docker info >/dev/null 2>&1 && exit 0
            sleep 1
        done
        tail -n 50 /run/windows-dind/docker.log >&2 || true
        exit 1
    ) 8> /run/windows-dind/docker.lock || fail 'Docker did not become ready. See /run/windows-dind/docker.log.'
}

configure() { python3 "$workspace/.devcontainer/windows-config.py"; }
prepare_vm() {
    # Pull before measuring the final disk budget: images may share /tmp's disk.
    python3 "$workspace/.devcontainer/windows-config.py" --quiet
    compose pull --policy missing windows
    configure
}
preflight() { python3 "$workspace/.devcontainer/windows-config.py" --check-kvm; }
compose() { docker compose --project-name windows --file "$compose_file" "$@"; }

require_config() {
    [[ -s "$compose_file" ]] || fail 'Windows is not configured yet. Run start first.'
}

check_boot_data() {
    local result=0
    cmp --silent --bytes=102400 "$1" /dev/zero || result=$?
    [[ "$result" == 1 ]] || fail "Disk $1 has no readable boot data. Its contents were preserved; import a valid Windows VHDX or use reset --yes."
}

show_access() {
    echo 'Windows is starting. Open forwarded port 8006 to finish setup.'
    echo "For RDP from your computer: gh codespace ports forward 3389:13389 --codespace ${CODESPACE_NAME:-YOUR_CODESPACE_NAME}"
    echo 'Then connect your Remote Desktop client to 127.0.0.1:13389 with your Windows credentials.'
    echo 'For a Tailscale connection, run start-tailscale and use its IPv4 address on port 3389.'
    echo 'Use windows-doctor to check the VM, KVM, disk space, and RDP listener.'
}
