#!/usr/bin/env python3
"""Probe usable KVM and generate resource-aware Compose configuration."""
import argparse
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import subprocess
import sys

MIB = 1024**2
GIB = 1024**3
IMAGE = "ghcr.io/dockur/windows:6.05@sha256:0cff9eb0e7aee9953e55bc682852ca4fdca233145a58ae1ec94f0b0c01a2ed30"
WORKSPACE_RESERVE = 2 * GIB
SCRATCH_RESERVE = 4 * GIB


def workspace_path():
    return Path(os.environ.get("WINDOWS_WORKSPACE", Path(__file__).resolve().parent.parent)).resolve()


def cgroup_paths(root):
    """Include the current cgroup and its ancestors, where mounted/visible."""
    paths = [root]
    try:
        for line in Path("/proc/self/cgroup").read_text().splitlines():
            if line.startswith("0::"):
                current = (root / line[3:].lstrip("/")).resolve()
                if current.is_relative_to(root.resolve()) and current.exists():
                    while current != root.resolve():
                        paths.append(current)
                        current = current.parent
    except OSError:
        pass
    return paths


def resources(cgroup_root=Path("/sys/fs/cgroup"), meminfo=Path("/proc/meminfo")):
    info = {}
    for line in meminfo.read_text().splitlines():
        key, value = line.split(":", 1)
        info[key] = int(value.split()[0]) * 1024
    total = info["MemTotal"]
    available = info.get("MemAvailable", info.get("MemFree", 0))
    cpus = len(os.sched_getaffinity(0))
    for path in cgroup_paths(cgroup_root):
        try:
            limit = int((path / "memory.max").read_text().strip())
            current = int((path / "memory.current").read_text().strip())
            total = min(total, limit)
            try:
                memory_stats = dict(line.split() for line in (path / "memory.stat").read_text().splitlines())
                reclaimable = int(memory_stats.get("inactive_file", "0"))
            except OSError:
                reclaimable = 0
            available = min(available, max(0, limit - current + reclaimable))
        except (OSError, ValueError):
            pass
        try:
            quota, period = (path / "cpu.max").read_text().split()
            if quota != "max":
                cpus = min(cpus, max(1, math.ceil(int(quota) / int(period))))
        except (OSError, ValueError, ZeroDivisionError):
            pass
    # Legacy cgroup v1 hosts.
    try:
        limit = int((cgroup_root / "memory/memory.limit_in_bytes").read_text())
        usage = int((cgroup_root / "memory/memory.usage_in_bytes").read_text())
        total = min(total, limit)
        available = min(available, max(0, limit - usage))
    except (OSError, ValueError):
        pass
    try:
        quota = int((cgroup_root / "cpu/cpu.cfs_quota_us").read_text())
        period = int((cgroup_root / "cpu/cpu.cfs_period_us").read_text())
        if quota > 0:
            cpus = min(cpus, max(1, math.ceil(quota / period)))
    except (OSError, ValueError, ZeroDivisionError):
        pass
    # Reserve genuinely available memory in addition to the host's current use.
    # Codespaces can terminate high-memory processes before a kernel OOM event.
    reserve = max(2 * GIB, total // 10)
    budget = min(total, available) - reserve
    return {"cpus": cpus, "total": total, "available": available, "ram_mib": budget // MIB}


def check_kvm(device=Path("/dev/kvm")):
    try:
        with device.open("rb+", buffering=0) as kvm:
            if fcntl.ioctl(kvm.fileno(), 0xAE00, 0) != 12:
                raise ValueError("unsupported KVM API")
            vm = fcntl.ioctl(kvm.fileno(), 0xAE01, 0)
            os.close(vm)
    except (OSError, ValueError) as error:
        raise ValueError(
            f"KVM cannot create a VM: {error}. Hardware acceleration must be exposed by the Codespaces host. "
            "Rebuilding scripts or using KVM=N cannot provide high performance. "
            "Check windows-doctor and the Codespace machine's nested-virtualization support."
        ) from error
    tun = Path("/dev/net/tun")
    if not tun.exists() or not stat.S_ISCHR(tun.stat().st_mode):
        raise ValueError("/dev/net/tun is unavailable; a privileged devcontainer is required for VM networking.")
    print("KVM API and VM creation succeeded; TUN is available.")


def size_bytes(value):
    match = re.fullmatch(r"([1-9][0-9]*)([MG])", str(value).upper())
    if not match:
        raise ValueError(f"Invalid size {value!r}; use a whole number followed by M or G.")
    return int(match[1]) * (MIB if match[2] == "M" else GIB)


def filesystem(path):
    """Measure the filesystem containing the actual path, including bind mounts."""
    path = path.resolve()
    existing = path
    while not existing.exists():
        existing = existing.parent
    stats = os.statvfs(existing)
    mount = {"type": "unknown", "mountpoint": "/"}
    for line in Path("/proc/self/mountinfo").read_text().splitlines():
        left, right = line.split(" - ", 1)
        target = re.sub(r"\\([0-7]{3})", lambda m: chr(int(m[1], 8)), left.split()[4])
        if path.is_relative_to(Path(target)) and len(target) >= len(mount["mountpoint"]):
            mount = {"type": right.split()[0], "mountpoint": target}
    return {
        "path": str(path), **mount,
        "device": existing.stat().st_dev, "fsid": stats.f_fsid,
        "total_bytes": stats.f_blocks * stats.f_frsize,
        "available_bytes": stats.f_bavail * stats.f_frsize,
    }


def scratch_path(workspace, setting):
    name = hashlib.sha256(str(workspace.resolve()).encode()).hexdigest()[:12]
    path = Path(setting("SCRATCH_DIR", f"/tmp/windows-dind-{name}"))
    if not path.is_absolute() or path.resolve().is_relative_to(workspace.resolve()):
        raise ValueError("SCRATCH_DIR must be an absolute path outside the persistent workspace.")
    return path.resolve()


def storage_report(workspace, scratch):
    primary = filesystem(workspace / "windows")
    secondary = filesystem(scratch)
    reason = None
    if secondary["type"] in ("tmpfs", "ramfs", "devtmpfs"):
        reason = "Temporary storage is RAM-backed; using it would consume guest RAM."
    elif secondary["type"] == "unknown":
        reason = "Temporary filesystem type could not be determined."
    elif primary["device"] == secondary["device"] or (primary["fsid"] and primary["fsid"] == secondary["fsid"]):
        reason = "Workspace and temporary path share one filesystem; a second image adds no physical capacity."
    primary["reserve_bytes"] = WORKSPACE_RESERVE
    secondary["reserve_bytes"] = SCRATCH_RESERVE
    secondary["eligible"] = reason is None
    secondary["reason"] = reason
    return {"workspace": primary, "scratch": secondary}


def allocated_bytes(disk):
    return disk.stat().st_blocks * 512 if disk.exists() else 0


def scratch_disk(report, path, requested):
    """Never shrink an existing image or double-count shared/RAM-backed capacity."""
    if requested == "off":
        return None
    if not report["eligible"]:
        if requested != "auto":
            raise ValueError(report["reason"])
        return None
    disk = path / "data2.img"
    current = disk.stat().st_size if disk.exists() else 0
    if current and report["available_bytes"] < GIB:
        raise ValueError("Less than 1 GiB is free on the scratch filesystem. Free host space before booting Windows.")
    budget = max(0, allocated_bytes(disk) + report["available_bytes"] - SCRATCH_RESERVE)
    if requested == "auto":
        target = max(math.ceil(current / MIB) * MIB, (budget // MIB) * MIB)
        if target < GIB:
            report["reason"] = "Less than 1 GiB remains after the temporary-storage reserve."
            return None
    else:
        target = size_bytes(requested)
        if target < GIB:
            raise ValueError("DISK2_SIZE must be at least 1G or off.")
        if target < current:
            raise ValueError("DISK2_SIZE cannot shrink the existing scratch disk.")
        if target > budget and target != current:
            raise ValueError("DISK2_SIZE exceeds the temporary filesystem's physical capacity after headroom.")
    report.update({"image": str(disk), "virtual_bytes": target, "allocated_bytes": allocated_bytes(disk),
                   "growth_budget_bytes": max(0, report["available_bytes"] - SCRATCH_RESERVE),
                   "overcommitted": target > allocated_bytes(disk) + report["available_bytes"],
                   "headroom_shortfall_bytes": max(0, target - budget)})
    return f"{math.ceil(target / MIB)}M"


def read_settings(workspace):
    storage = workspace / "windows"
    settings_file = storage / "settings.json"
    settings = json.loads(settings_file.read_text()) if settings_file.exists() else {}
    allowed = {"CPU_CORES", "RAM_SIZE", "DISK_SIZE", "DISK2_SIZE", "SCRATCH_DIR",
               "DISK_CACHE", "DISK_IO", "WINDOWS_IMAGE"}
    if not isinstance(settings, dict) or set(settings) - allowed:
        raise ValueError("settings.json must be an object containing only documented settings.")

    def setting(name, default):
        return os.environ.get(name, settings.get(name, default))
    return setting


def generate(workspace, limits, quiet=False):
    storage = workspace / "windows"
    setting = read_settings(workspace)
    scratch = scratch_path(workspace, setting)
    report = storage_report(workspace, scratch)

    cpu_value = setting("CPU_CORES", "auto")
    cpus = limits["cpus"] if cpu_value == "auto" else int(cpu_value)
    if not 1 <= cpus <= limits["cpus"]:
        raise ValueError(f"CPU_CORES must be between 1 and {limits['cpus']} on this machine.")
    ram_value = setting("RAM_SIZE", "auto")
    ram_mib = limits["ram_mib"] if ram_value == "auto" else size_bytes(ram_value) // MIB
    if not 4096 <= ram_mib <= limits["ram_mib"]:
        raise ValueError(f"RAM_SIZE must fit between 4096M and {limits['ram_mib']}M with host headroom. Free memory or select a larger Codespace.")
    disk = storage / "data.img"
    installing = storage / "microsoft-install.json"
    installation = json.loads(installing.read_text()) if installing.exists() and not (storage / "windows.boot").exists() else None
    if not disk.exists() and not installation:
        raise ValueError("The Windows disk is missing. Run start to prepare the installation.")
    virtual_size = disk.stat().st_size if disk.exists() else 128 * GIB
    if virtual_size == 0:
        raise ValueError("The Windows raw disk is empty.")
    primary = report["workspace"]
    if primary["available_bytes"] < WORKSPACE_RESERVE:
        raise ValueError("Less than 2 GiB is free on the Windows filesystem. Free space before booting Windows.")
    primary.update({"image": str(disk), "virtual_bytes": virtual_size, "allocated_bytes": allocated_bytes(disk),
                    "growth_budget_bytes": primary["available_bytes"] - WORKSPACE_RESERVE})
    primary_budget = allocated_bytes(disk) + primary["growth_budget_bytes"]
    existing_size = math.ceil(virtual_size / MIB) * MIB
    disk_size = setting("DISK_SIZE", "max")
    if disk_size == "max":
        disk_size = f"{max(existing_size, (primary_budget // MIB) * MIB) // MIB}M"
    if disk_size == "keep":
        disk_size = f"{math.ceil(virtual_size / MIB)}M"
    elif size_bytes(disk_size) < virtual_size:
        raise ValueError("DISK_SIZE cannot shrink the existing Windows disk.")
    elif size_bytes(disk_size) > primary_budget and size_bytes(disk_size) > existing_size:
        raise ValueError("DISK_SIZE expansion exceeds the workspace's physical capacity after headroom.")
    primary["virtual_bytes"] = size_bytes(disk_size)
    primary["overcommitted"] = primary["virtual_bytes"] > primary_budget
    secondary_size = scratch_disk(report["scratch"], scratch, setting("DISK2_SIZE", "auto"))
    cache = setting("DISK_CACHE", "none")
    io = setting("DISK_IO", "native")
    if cache not in ("none", "writeback", "directsync", "writethrough") or io not in ("native", "threads", "io_uring"):
        raise ValueError("Unsupported DISK_CACHE or DISK_IO setting.")
    if io == "native" and cache not in ("none", "directsync"):
        raise ValueError("DISK_IO=native requires DISK_CACHE=none or directsync; use threads with writeback.")
    environment = {
        "CPU_CORES": str(cpus), "RAM_SIZE": f"{ram_mib}M", "RAM_CHECK": "Y",
        "DISK_SIZE": str(disk_size), "DISK_FMT": "raw", "DISK_TYPE": "scsi",
        "DISK_CACHE": cache, "DISK_IO": io, "DISK_DISCARD": "unmap", "ALLOCATE": "N",
        "BOOT_MODE": "windows", "TPM": "Y", "KVM": "Y", "HV": "Y",
        "DISPLAY": "web", "DEBUG": "N", "MTU": "1486",
    }
    if installation:
        if not Path(installation["iso"]).is_file():
            raise ValueError("Windows installer media is missing. Run start to restore it.")
        environment.update({"VERSION": "11", "WINDOWS_INSTALL_TEMP": "/windows-dind-installer/unpack"})
    devices = ["/dev/kvm", "/dev/net/tun"]
    if Path("/dev/vhost-net").exists():
        devices.append("/dev/vhost-net")
    runtime = workspace / ".devcontainer/runtime"
    volumes = [f"{storage}:/storage", f"{workspace}:/data",
               f"{runtime / 'entry.sh'}:/usr/local/lib/windows-dind/entry.sh:ro",
               f"{runtime / 'patch-boot.py'}:/usr/local/lib/windows-dind/patch-boot.py:ro"]
    if installation:
        temp = Path(installation["temp"])
        temp.mkdir(parents=True, exist_ok=True, mode=0o700)
        volumes.extend([f"{installation['iso']}:/boot.iso:ro", f"{temp}:/windows-dind-installer"])
    if secondary_size:
        scratch.mkdir(parents=True, exist_ok=True, mode=0o700)
        environment["DISK2_SIZE"] = secondary_size
        volumes.append(f"{scratch}:/storage2")
    config = {"services": {"windows": {
        "container_name": "windows", "image": setting("WINDOWS_IMAGE", IMAGE),
        "labels": {"com.windows-dind.config": "5"},
        "entrypoint": ["/usr/bin/tini", "-s", "/bin/bash", "/usr/local/lib/windows-dind/entry.sh"],
        "environment": environment,
        "ports": ["3389:3389/tcp", "3389:3389/udp", "127.0.0.1:8006:8006/tcp"],
        "devices": devices, "cap_add": ["NET_ADMIN"],
        "volumes": volumes,
        # Codespace resume must run our KVM/resource probes before booting.
        "restart": "no", "stop_grace_period": "2m",
    }}}
    if installation:
        config["services"]["windows"]["env_file"] = [installation["env_file"]]
    temp = storage / "windows.yaml.new"
    temp.write_text(json.dumps(config, indent=2) + "\n")
    temp.replace(storage / "windows.yaml")
    report["scratch"]["enabled"] = secondary_size is not None
    temp = storage / "storage.json.new"
    temp.write_text(json.dumps(report, indent=2) + "\n")
    temp.replace(storage / "storage.json")
    if not quiet:
        print(f"Windows: {cpus} vCPUs, {ram_mib} MiB RAM; KVM required.")
        print(f"Boot disk: {primary['virtual_bytes'] / GIB:.2f} GiB virtual; "
              f"{primary['growth_budget_bytes'] / GIB:.2f} GiB physical growth space after headroom.")
        if primary["overcommitted"]:
            print("The existing sparse boot disk is larger than physical workspace storage. Check host free space before large writes.")
        if secondary_size:
            print(f"Scratch disk: {report['scratch']['virtual_bytes'] / GIB:.2f} GiB virtual, backed by {scratch}.")
            if scratch.is_relative_to(Path("/tmp")):
                print("IMPORTANT: /tmp contents are deleted when the Codespace stops or times out. Back up scratch files first.")
            else:
                print("Scratch storage is outside the persistent workspace; verify its lifecycle and back up important files.")
            if report["scratch"]["overcommitted"]:
                print("The existing scratch disk exceeds current physical capacity; free host space before large writes.")
        else:
            print(f"Scratch disk disabled: {report['scratch']['reason'] or 'DISK2_SIZE=off'}")
    return config


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-kvm", action="store_true")
    parser.add_argument("--resources", action="store_true")
    parser.add_argument("--storage", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    try:
        if args.check_kvm:
            check_kvm()
        elif args.resources:
            print(json.dumps(resources(), indent=2))
        elif args.storage:
            workspace = workspace_path()
            print(json.dumps(storage_report(workspace, scratch_path(workspace, read_settings(workspace))), indent=2))
        else:
            generate(workspace_path(), resources(), args.quiet)
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
