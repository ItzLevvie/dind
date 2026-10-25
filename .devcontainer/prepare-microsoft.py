#!/usr/bin/env python3
"""Stage verified retail Windows media without importing an expired preview."""
import argparse
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess

ISO_URL = "https://software-static.download.prss.microsoft.com/dbazure/888969d5-f34g-4e03-ac9d-1f9786c66749/26200.6584.250915-1905.25h2_ge_release_svc_refresh_CLIENT_CONSUMER_x64FRE_en-us.iso"
ISO_SHA256 = "d141f6030fed50f75e2b03e1eb2e53646c4b21e5386047cb860af5223f102a32"
ISO_BYTES = 7736125440


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_json(path, value):
    temporary = path.with_suffix(path.suffix + ".new")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def prepare(workspace, cache, replace=False):
    storage = workspace / "windows"
    storage.mkdir(parents=True, exist_ok=True)
    cache.mkdir(parents=True, exist_ok=True, mode=0o700)
    iso = cache / "windows-11-pro-25h2.iso"
    if not (iso.exists() and iso.stat().st_size == ISO_BYTES and sha256(iso) == ISO_SHA256):
        if shutil.disk_usage(cache).free < ISO_BYTES + 12 * 1024**3:
            raise ValueError("At least 20 GiB of disk-backed installer space is required. Set WINDOWS_IMAGE_CACHE to a suitable filesystem.")
        partial = iso.with_suffix(".iso.partial")
        print("Downloading verified Microsoft Windows 11 Pro installation media...", flush=True)
        subprocess.run(["curl", "--fail", "--location", "--retry", "3", "--retry-all-errors",
                        "--connect-timeout", "30", "--continue-at", "-", ISO_URL,
                        "--output", str(partial)], check=True)
        if partial.stat().st_size != ISO_BYTES or sha256(partial) != ISO_SHA256:
            partial.unlink(missing_ok=True)
            raise ValueError("Microsoft ISO checksum mismatch. The existing Windows disk was preserved.")
        partial.replace(iso)

    # Passwords stay outside the repository and its guest SMB share.
    credentials = Path(os.environ.get("WINDOWS_CREDENTIALS_DIR", "/workspaces/.windows-rdp"))
    credentials.mkdir(parents=True, exist_ok=True, mode=0o700)
    credentials.chmod(0o700)
    login = credentials / "credentials.txt"
    if login.exists():
        found = re.search(r"(?im)^\s*password\s*[:=]\s*(\S+)\s*$", login.read_text())
        if not found:
            raise ValueError("Cannot read the private Windows password; preserve this file or select another WINDOWS_CREDENTIALS_DIR.")
        password = found.group(1)
    else:
        password = "rdp-7" + secrets.token_hex(12)
        login.write_text("Username: .\\codespaces\nPassword: " + password + "\n")
    login.chmod(0o600)
    if not re.fullmatch(r"[A-Za-z0-9!@#%^*_+=.,:-]{12,127}", password):
        raise ValueError("The stored installer password contains unsupported characters or is shorter than 12 characters.")
    environment = credentials / "install.env"
    environment.write_text("USERNAME=codespaces\nPASSWORD=" + password + "\n")
    environment.chmod(0o600)

    if (storage / "data.img").exists():
        if not replace and not (storage / "microsoft-install.json").exists():
            raise ValueError("An existing Windows disk is present. Its contents were preserved.")
    if (storage / "data.img").exists() and replace:
        old = storage / "data.img"
        needed = old.stat().st_blocks * 512 + 2 * 1024**3
        if shutil.disk_usage(cache).free < needed:
            raise ValueError("Insufficient staging space to preserve the previous Windows disk during reset.")
        backup = cache / ("previous-windows-" + datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%f"))
        backup.mkdir(mode=0o700)
        files = [p for p in storage.iterdir() if p.is_file() and (p.name.startswith("data.") or p.name.startswith("windows."))]
        for path in files:
            subprocess.run(["cp", "--sparse=always", "--preserve=mode,timestamps", "--", str(path), str(backup / path.name)], check=True)
        for path in files:
            path.unlink()
        print(f"Previous Windows files retained at {backup}. This is temporary storage; export them before a Codespace stop.")

    atomic_json(storage / "microsoft-install.json", {"source": "Microsoft Windows 11 Pro 25H2",
                "iso": str(iso), "sha256": ISO_SHA256, "env_file": str(environment),
                "temp": str(cache / "installer")})
    print("Verified Windows 11 Pro media ready. Installation runs in the VM; the private login is in " + str(login) + ".")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()
    try:
        cache = Path(os.environ.get("WINDOWS_IMAGE_CACHE", "/tmp/windows-dind-image"))
        cache.mkdir(parents=True, exist_ok=True, mode=0o700)
        with (cache / ".microsoft.lock").open("w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            prepare(Path(os.environ["WINDOWS_WORKSPACE"]), cache, args.replace)
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"ERROR: {error}\n")
