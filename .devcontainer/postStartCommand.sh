#!/usr/bin/env bash
set -Eeuo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
# Reinstall helpers after a rebuild and keep the workspace and Windows disk intact.
bash "$script_dir/onCreateCommand.sh"
# shellcheck source=helpers/common.sh
source "$script_dir/helpers/common.sh"
ensure_docker

# Restore a VM which was running when Codespaces stopped. A deliberate stop
# removes this marker and does not cause an automatic restart.
if [[ -f "$storage/.autostart" ]]; then
    if ! /usr/local/bin/start; then
        echo 'Windows could not resume. Run windows-doctor in the terminal to inspect the failure.' >&2
    fi
fi
if [[ -s "$storage/tailscale/tailscaled.state" || -s "$workspace/.devcontainer/tailscale/tailscaled.state" ]]; then
    if ! /usr/local/bin/start-tailscale --resume-only; then
        echo 'Tailscale could not resume. Run start-tailscale in the terminal; see /run/windows-dind/tailscale.log.' >&2
    fi
fi
