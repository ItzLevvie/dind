# Investigation and validation — 2026-10-02

The repaired fork is [amywisconsin12121-gif/dind](https://github.com/amywisconsin12121-gif/dind), based on ItzLevvie commit `76c6eb0034806439b277a657bde751f84eaaf8f2`. Tests used a real Codespace created from this fork, `windows-kvm-4-cores---repaired-vprq6gpgx9x4hw555`. The unrelated dockur/windows Codespace was deleted as requested.

## Actual machine and Windows measurements

GitHub's machines API offered only 2-core/8-GB and 4-core/16-GB configurations, both with 32 GB persistent storage. The test used `standardLinux32gb` with **4 cores and 16 GB RAM**, the largest offered configuration. Its actual region is `UkSouth`.

| Item | Verified result |
| --- | --- |
| Acceleration | `/dev/kvm` API version 12 and successful `KVM_CREATE_VM`; real Windows QEMU uses KVM and host CPU passthrough. |
| CPU | Windows reports four cores and four logical processors, AMD EPYC 7763. |
| Host RAM | 16,770,494,464 bytes, approximately 15.62 GiB. Guest allocation leaves capacity for Linux, Docker, QEMU overhead, the editor, and networking. |
| Persistent filesystem | 33,636,024,320 bytes, approximately 31.32 GiB, shared by the checkout, VM disk, and Docker volume. |
| Separate temporary filesystem | 126,225,022,976 bytes, approximately 117.56 GiB. |
| Added scratch disk | Initially **104.59 GiB**, formatted as NTFS `S:` and load-tested. After the verified Codespace stop/resume cleared `/tmp`, the newly measured maximum was 114,025,299,968 bytes, **106.19 GiB**, with 4 GiB host headroom; it was initialized again as NTFS `S:`. |
| Windows boot disk | 128 GiB virtual sparse raw image. This does not supply 128 GiB persistent physical storage; monitor the host's actual free space. |
| Original guest OS | Windows 11 Enterprise Insider Preview, build 29599.1000, using the author's release 29599-1. Its kernel expiration was **2026-08-11 18:09:44 UTC**, before the test date; Windows displayed an expired-build notification. |
| Replacement | Verified Microsoft Windows 11 Pro 25H2 media, SHA-256 `d141f6030fed50f75e2b03e1eb2e53646c4b21e5386047cb860af5223f102a32`; guest kernel build 26200 reports **SystemExpirationDate = 0**, with no expiration timestamp. Native NLA RDP authenticated to its desktop. |
| Activation | Both tested installations report Windows license status 5 (activation notification), with no remaining grace period. Windows Pro requires your own valid license. |
| Windows configuration | High performance power plan, AC sleep disabled, TRIM enabled, firewall enabled on all profiles, RDP service running, NLA required, password authentication. |
| Native RDP | Authenticated full desktop sessions over an authenticated GitHub CLI TCP tunnel, including a fresh sign-in. FreeRDP was forced to NLA with the server certificate fingerprint pinned and independently confirmed inside Windows. RDP drive redirection works. |

**The scratch disk is temporary. GitHub clears `/tmp` on every Codespace stop or idle timeout.** Windows and account settings stay on the persistent boot disk. Do not treat the scratch disk as a backup. The VM's original 128-GiB C: free-space display exceeds its physical workspace budget.

## Confirmed failures and repairs

| Finding | Evidence and consequence | Repair |
| --- | --- | --- |
| Destructive initialization | Upstream prunes all Docker images during initialization and removes the checkout recursively during onCreate. The author associates pruning with recovery mode in issue 9. | Preserve the checkout, Windows disk, and image cache; install helpers in place. |
| Expired upstream Windows image | Its kernel expiration date was verified both through QEMU and inside Windows; the GUI said the build had expired. The resumed preview stopped after approximately one hour. Docker recorded an exit without a Docker stop/kill request, and the guest recorded an unexpected previous shutdown. These observations do not prove which component initiated that stop. | New installations use checksum-verified, non-evaluation Microsoft Windows 11 Pro media. Existing disks are preserved; the test setup was migrated after a separate installation. |
| Stale restart configuration | Real Docker tests confirmed `compose restart` retains previous resource/environment settings. | Gracefully stop, recompute settings, then reconcile with `compose up -d`. |
| Unsafe reset | Bash resolves bare `kill` to its builtin, which returns usage status 2 without a PID; the old script proceeds to delete the VM disk. | Stop and remove the real service, verify a separate replacement conversion, and atomically rename only after success. |
| Imported UEFI disk rejected | The author's image boots through `UEFI QEMU QEMU HARDDISK`, while the runtime's watchdog only recognized `Windows Boot Manager`. The real accelerated guest was stopped at the watchdog deadline despite valid boot progress. | Patch only that imported-disk state in the pinned runtime; preserve DVD, shell, missing-device, and firmware-failure paths. |
| Externally terminated high-RAM boots | Repeated approximately 13.6-GiB launches received SIGTERM. `strace` recorded `SI_USER`, sender PID 0 outside the container PID namespace, UID 61876; cgroup OOM counters remained zero. The user confirmed they did not stop it. A 13-GiB trial also lost the daemon approximately 39 seconds after startup. A 10-GiB diagnostic allocation ran for over 50 minutes and supported Windows setup and native RDP. The repaired automatic budget selected 12,596 MiB (12.30 GiB). | Budget from genuinely available RAM after existing host use, with at least 2 GiB left available. Do not interpret absence of an OOM event as proof of adequate host memory. The exact external supervisor was not identified. |
| Background daemon lifecycle | Docker and Tailscale processes inherited lifecycle sessions; abrupt daemon loss hid useful diagnostics. | Serialize Docker startup, retain logs, and detach background daemons with `nohup setsid --fork`. |
| Automatic restart uses old RAM | During diagnosis, restoring Docker relaunched the previous high-RAM VM before resource checks could run. | Disable Docker automatic restart. Marked Codespace resume invokes the resource-aware helper. |
| Unchecked image import | Original download/conversion failures could leave success markers or a blank disk, causing the runtime to attempt an unrelated fresh installation. | Pin and verify all five archive SHA-256 digests, validate nonempty imported disk data, check staging space, and preserve the old disk on failures. |
| CPU, RAM, and disk assumptions | Original host-wide CPU/memory queries ignore container quotas; old disk matching measures incorrect mounts and adds a large swap file. | Honor CPU affinity/cgroup quotas, measure the actual filesystems, exclude shared/tmpfs scratch paths, preserve existing images, reserve headroom, and avoid swap and duplicate base disks. |
| Scratch initializer driver mismatch | Inside the real Windows guest, the VirtIO SCSI driver identifies the disk bus as `SAS`. A SCSI-only guard rejects the valid blank disk. | Accept SCSI/SAS while still requiring exact host-plan size, a RAW partition table, and non-boot/non-system status. Permit an explicit plan file path for RDP drive redirection. |
| Startup waits for Tailscale login | Upstream starts interactive login before the VM. | Keep login separate; resume stored state without blocking Windows on expired authentication. |
| Web forwarding used as RDP | Codespaces browser forwarding is HTTP/HTTPS and cannot supply an RDP server URL. | Keep the web console private; use GitHub CLI local TCP forwarding or authenticated Tailscale for native RDP. |
| Runtime changes independently | Upstream uses Debian sid, unpinned tools, and the runtime's latest tag. | Use stable Debian packages, stable Tailscale, and dockur 6.05 pinned to its tested GHCR manifest digest. |
| Diagnostics miss QEMU | The actual QEMU process is named `windows`, so `pgrep qemu-system` returns no process. | Read the runtime's PID file and inspect that process; probe the actual guest IP and RDP listener. |

## Load test of the original imported preview

At the repaired 12,596-MiB allocation, a four-worker SHA-256 workload completed for **60.025 seconds**, processing **5.352 GiB/s** in aggregate. A subsequent **1-GiB write-through scratch-file write**, flushed to the storage device, completed in **2.348 seconds (436 MiB/s)**. Windows, RDP, and the host remained running. These are a baseline and a stability check, not a comparison of cache modes or a promise of sustained disk throughput.

## Codespace stop/resume

The original imported preview stopped gracefully before the first full GitHub Codespace stop. GitHub took approximately six minutes to finish that operation. The same Codespace resumed and its lifecycle helper automatically booted the existing Windows installation. The Windows disk, account credentials, persistent helper scripts, saved benchmark, and persistent test marker survived. The `/tmp` marker was absent and its filesystem ID changed, confirming temporary storage was cleared. The helper created a new blank scratch disk at its measured maximum, **106.19 GiB**, and recomputed RAM to **12,625 MiB (12.33 GiB)**. Native NLA RDP authenticated successfully after recovery.

The replacement Windows 11 Pro installation then passed a separate full Codespace stop/resume. Its RDP certificate and password survived, and a pinned-certificate NLA desktop login succeeded after the restart. The helper automatically restored real KVM, four CPUs, **12,627 MiB RAM (12.33 GiB)**, and a fresh **106.16-GiB temporary disk**. The persistent filesystem now has approximately 18.17 GiB free before the 2-GiB host reserve.

## Verification

- Downloaded and verified all five release 29599-1 archives, totaling **4,421,755,822 bytes**. Extracted the **14,701,035,520-byte** VHDX, converted it, and booted the real Windows installation with KVM. Archive staging is removed after successful import.
- Built the repaired devcontainer with TLS verification enabled. The real Codespace creation completed with working Docker, unique SSH host keys, GitHub CLI SSH access, KVM, VirtIO networking, and the persistent checkout intact.
- Ran **21 regression tests successfully** in the root test container. These cover resource limits and host memory use, independent storage capacity, used-image accounting, preservation and shrink refusal, nonempty disk guards, lifecycle ordering, safe reset, expired Tailscale login, explicit installer bootstrap, private password files, and preservation on a failed Microsoft ISO checksum.
- Ran the imported-UEFI watchdog regression against the pinned real runtime. The test reproduces the original rejection, accepts valid imported-disk progress after patching, preserves all known failure paths, and checks patch idempotence.
- Parsed both PowerShell scripts and checked Bash syntax, ShellCheck, Compose configuration, and patch whitespace.
- Imported a nonempty synthetic VHDX and compared the converted raw disk byte-for-byte. Failed replacement conversion retained the old disk.
- Executed `Configure-Windows.ps1` and `Initialize-Scratch.ps1` inside the real Windows guest. Tested native RDP password authentication and full desktop access, a fresh sign-in, file transfer, and the guest's actual CPU, memory, disk, certificate, firewall, and power-plan state.

The imported preview image's guest SMB client failed authentication to the runtime's host share even though networking and TCP 445 worked. RDP drive redirection was tested as a working transfer path; setup and scratch initialization do not require weakening RDP NLA or disabling the firewall.

Tailscale direct/relayed connectivity and RDP UDP have not been tested because joining the user's tailnet requires their own Tailscale login. TCP RDP is verified. No comparison of all disk cache modes establishes an absolute fastest I/O profile; the default uses VirtIO SCSI, sparse raw files, direct I/O, and TRIM.

## Sources checked

- [ItzLevvie recovery-mode issue and author explanation](https://github.com/ItzLevvie/dind/issues/9#issuecomment-3667570327)
- [ItzLevvie RDP drop report](https://github.com/ItzLevvie/dind/issues/10)
- [Actual Windows image release 29599-1](https://github.com/ItzLevvie/artifacts/releases/tag/29599-1)
- [Pinned dockur 6.05 runtime](https://github.com/dockur/windows/tree/v6.05) and [environment variables](https://github.com/dockur/windows/blob/v6.05/docs/environment.md)
- [GitHub Codespaces machine capacities](https://docs.github.com/en/codespaces/overview)
- [Codespaces temporary-file lifecycle](https://docs.github.com/en/codespaces/developing-in-a-codespace/persisting-environment-variables-and-temporary-files)
- [Codespaces port forwarding](https://docs.github.com/en/codespaces/developing-in-a-codespace/forwarding-ports-in-your-codespace)
- [Docker restart-policy behavior](https://docs.docker.com/engine/containers/start-containers-automatically/)
