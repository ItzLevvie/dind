# Windows setup and performance

Use this fork's repaired default branch when creating or rebuilding a Codespace. Back up an existing `windows/data.img` before applying the repair to an existing workspace. The original `onCreateCommand.sh` deletes the checkout, so inspect and back up a failed Codespace before rerunning its original lifecycle commands.

The devcontainer includes an OpenSSH server with per-container host keys so `gh codespace ssh` and `gh codespace logs` can inspect it. Connect from a computer authenticated to GitHub with `gh codespace ssh --codespace YOUR_CODESPACE_NAME`.

1. Open the Codespace terminal and run `start`.
2. Open port 8006 from the Ports panel. Keep that browser console private. A new installation uses verified Microsoft Windows 11 Pro media and creates the `codespaces` account with a strong password, saved outside the repository in `/workspaces/.windows-rdp/credentials.txt`. Windows activation requires your own license. The original upstream Insider image expired on August 11, 2026 and is unsuitable for continued use.
3. In an elevated Windows PowerShell window, run:

   ```powershell
   powershell -ExecutionPolicy Bypass -File "\\host.lan\Data\.devcontainer\windows\Configure-Windows.ps1"
   ```

   This prompts for your Windows account password, enables RDP with Network Level Authentication, enables its firewall rules, restores the Windows firewall, and selects the High performance power plan with no AC sleep. If the shared folder is unavailable, copy the script through the browser console instead.
4. Run `start-tailscale` in the Codespace terminal and finish the displayed login. Install Tailscale on your computer and sign in to the same tailnet. Connect your Remote Desktop client to the displayed IPv4 address, port 3389. Use your Windows username and password; `\.YourUserName` explicitly selects a local Windows account.

Windows startup does not wait for a Tailscale login. Persistent Tailscale state is stored in `windows/tailscale/`; existing state in `.devcontainer/tailscale/` is migrated when present. Both locations are ignored by Git. If login expires during a Codespace restart, the terminal opens and asks you to run `start-tailscale` again. You can optionally provide `TAILSCALE_AUTHKEY` as a Codespaces secret scoped to this fork. Do not commit that key.

## RDP through a local TCP tunnel

On your own computer, with GitHub CLI authenticated for Codespaces:

```sh
gh codespace ports forward 3389:13389 --codespace YOUR_CODESPACE_NAME
```

Keep that command running and point your Remote Desktop client to `127.0.0.1:13389`. This method carries RDP TCP. Tailscale also permits the published RDP UDP port, and a direct Tailscale connection can reduce latency. Use `tailscale ping YOUR_COMPUTER_NAME` to see whether the path is direct or relayed. A browser's `https://...app.github.dev` URL cannot be used as an RDP server address.

## Performance settings

The devcontainer requests a minimum of **4 cores, 16 GB RAM, and 32 GB storage**. Use the 4-core machine: it is the highest CPU/RAM configuration available to this account. The defaults use all CPUs available within affinity and cgroup limits and leave the greater of 2 GiB or 10% of effective host memory **available after Linux's existing memory use**. Guest RAM therefore depends on the actual host load; inspect the allocation printed by `start`. Giving Windows all 16 GiB leaves no room for Linux, QEMU overhead, Docker, the editor, or Tailscale. On the tested Codespace, 13-GiB and 13.6-GiB trials were externally terminated. A 10-GiB diagnostic profile ran for over 50 minutes, and the repaired automatic allocation passed the CPU/disk load test. The repaired automatic budget selected 12,596 MiB (approximately 12.30 GiB) for the load test, and 12,625 MiB (12.33 GiB) after the tested Codespace resume. CPU host passthrough and Hyper-V enlightenments come from the pinned dockur QEMU runtime. Disks use sparse raw format, VirtIO SCSI, direct I/O, and TRIM. No 16-GiB swap file or duplicate raw base disk is created.

KVM is required and its API must actually create a VM; an existing device filename alone is insufficient. `DEBUG=N` prevents dockur's debug mode from silently falling back to slow software emulation. If the host does not expose nested virtualization, scripts cannot supply it. `windows-doctor` reports the actual probe failure. Machine availability and acceleration must be checked on your own Codespace.

List the 4-core machines offered for your fork, largest persistent storage first:

```sh
gh api repos/YOUR_GITHUB_USERNAME/dind/codespaces/machines --jq '.machines | map(select(.cpus == 4)) | sort_by(.storage_in_bytes) | reverse | .[] | {name, cpus, memory_in_bytes, storage_in_bytes}'
```

Select the offered 4-core/16-GB machine with the greatest `storage_in_bytes`, and a region close to the RDP client. Scripts cannot enlarge GitHub's physical workspace allocation. Temporary disk capacity is separate and must be measured inside the Codespace; the old upstream table's 118-GB figure is not guaranteed for your machine.

To override resource settings, copy `.devcontainer/settings.example.json` to `windows/settings.json`, edit it, and run `restart`. `CPU_CORES` and `RAM_SIZE` can be `auto` or explicit values such as `4` and `12G`. The configuration rejects CPU/RAM overcommit and disk shrink. `DISK_SIZE=max` uses the primary disk's allocated bytes plus free workspace space, leaving 2 GiB for host files; it preserves any larger existing virtual disk. `keep` preserves the existing size without growth. Explicit expansion cannot exceed physical capacity after headroom.

`DISK_CACHE=none` with `DISK_IO=native` is the default. `writeback` with `threads` is available for workload-specific testing; it uses host cache and can lose buffered writes after an abrupt host stop. A baseline stress/write test is documented in the investigation; no comparison establishes a fastest cache mode. Keep the default until a benchmark on your actual machine supports a change.

## Maximum usable disk capacity

The Windows boot disk remains in persistent `windows/data.img`. ItzLevvie's image has a **128-GiB virtual disk**, but a sparse image does not supply 128 GiB of physical storage. On a 32-GB workspace, C: can report more free space than the host can hold. `start` prints actual host growth space, and `windows-doctor` reports current filesystem capacity. Leave the reserved host space free; filling an oversized C: image can exhaust the workspace.

`DISK2_SIZE=auto` exposes an additional scratch drive when `/tmp` is a separate, disk-backed filesystem. It sizes this image from allocated image bytes plus actual free space, leaving 4 GiB for system files. VM image pulls and initial Windows import finish before the final measurement. No second disk is created if `/tmp` shares the workspace's filesystem or is a tmpfs consuming RAM. On this account's tested 4-core Codespace, the separate temporary filesystem was 117.56 GiB in total and the initial scratch disk was 104.59 GiB. It was initialized and mounted inside Windows as `S:`. After the tested stop/resume cleared `/tmp`, the fresh maximum increased to 106.19 GiB; the actual capacity is recomputed at each start.

**Codespaces deletes `/tmp` whenever the Codespace stops, including an idle timeout. Everything on this scratch drive is then lost.** Keep installed Windows and important files on persistent workspace storage or back them up outside the Codespace. A devcontainer rebuild alone may retain `/tmp`; stopping the Codespace does not. See [GitHub's temporary-file lifecycle documentation](https://docs.github.com/en/codespaces/developing-in-a-codespace/persisting-environment-variables-and-temporary-files).

After Windows starts, view the disks in an elevated PowerShell window:

```powershell
Get-Disk | Format-Table Number, FriendlyName, PartitionStyle, Size, IsBoot, IsSystem
```

Initialize only the blank secondary disk whose size matches the scratch size printed by `start`. It is normally disk 1:

```powershell
powershell -ExecutionPolicy Bypass -File "\\host.lan\Data\.devcontainer\windows\Initialize-Scratch.ps1" -DiskNumber 1
```

The script checks the selected disk against the host's storage plan, refuses boot/system disks and disks with existing partitions, and creates an NTFS `S:` volume labeled `TEMPORARY SCRATCH`. Use `-DriveLetter T` if S: is already occupied. If the host share is unavailable, copy both this script and the generated `windows/storage.json` into Windows or an RDP redirected drive, then pass `-PlanPath` with that JSON file's Windows path. Repeat initialization when `/tmp` has been cleared. If an existing scratch disk grows, extend its partition through Windows Disk Management; the script deliberately preserves existing partitions.

`DISK2_SIZE=off` disables attachment without deleting an existing image. An explicit size such as `100G` must fit the measured capacity. `SCRATCH_DIR` can select another absolute disk-backed path outside the workspace. Paths outside `/workspaces` do not carry the workspace's persistence guarantee; check that filesystem's lifecycle before placing important files there. Existing images are never shrunk or removed automatically when host space decreases. The generated `windows/storage.json` records both virtual sizes and physical growth budgets.

## Startup, storage, and recovery

Use `stop` for graceful shutdown, `restart` to apply settings and boot again, and `remove` to remove the VM container while retaining Windows files. Bash reserves the name `kill`; to force-stop the VM, invoke `/usr/local/bin/kill` explicitly. `reset --yes` discards Windows changes and starts a new Microsoft Windows 11 Pro installation. Download and checksum failures preserve the old disk. A reset retains previous disk files in temporary staging for recovery; export that backup before stopping the Codespace.

Codespace resume uses the persistent `.autostart` marker and the `start` helper, which checks KVM and measures CPU, RAM, and storage before boot. Docker's automatic restart policy is disabled: during actual testing, it restored an interrupted container with its old RAM settings before the helper could recompute them. VM startup and recovery go through the helper. A guest shutdown or runtime failure leaves the container stopped until `start` or the next marked Codespace resume.

Microsoft ISO downloads resume and are checked against a pinned SHA-256 digest. Media and extraction use `/tmp/windows-dind-image` by default, keeping installer extraction outside the persistent workspace. Allow at least 20 GiB of disk-backed staging space. If `/tmp` is small or a tmpfs, select a suitable filesystem with `WINDOWS_IMAGE_CACHE=/path/to/cache start`. A custom existing VHDX can still be imported using `WINDOWS_SOURCE_VHDX=/path/to/data.vhdx start` before the first boot; choose a supported Windows build. `WINDOWS_SOURCE=itzlevvie` explicitly selects the author's archived, expired preview and is intended only for legacy investigation. Its five archive digests and safe conversion checks are retained.

Run `windows-doctor` after startup. It checks guest TCP port 3389 directly rather than mistaking Docker's host listener for a ready Windows RDP service. A successful port probe still requires an actual RDP client login to verify credentials. If KVM works but RDP is closed, complete OOBE and run the Windows configuration script. If RDP disconnects after inactivity, check the Codespace's state and configured idle timeout. This repair does not bypass Codespaces' idle timeout.
