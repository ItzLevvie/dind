"""Regressions for resource limits and the original destructive lifecycle paths."""
import importlib.util
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("windows_config", ROOT / ".devcontainer/windows-config.py")
config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config)
media_spec = importlib.util.spec_from_file_location("prepare_microsoft", ROOT / ".devcontainer/prepare-microsoft.py")
media = importlib.util.module_from_spec(media_spec)
media_spec.loader.exec_module(media)


class MicrosoftInstallTests(unittest.TestCase):
    def test_missing_disk_requires_an_explicit_prepared_installer(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "windows").mkdir()
            with patch.dict(os.environ, {}, clear=True), self.assertRaisesRegex(ValueError, "missing"):
                config.generate(root, {"cpus": 4, "ram_mib": 12288})

    def test_prepared_installer_boots_without_disk_and_keeps_password_out_of_compose(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            storage = root / "windows"
            storage.mkdir()
            iso = root / "verified.iso"
            iso.write_bytes(b"verified fixture")
            env = root / "private.env"
            env.write_text("PASSWORD=private-fixture-password\n")
            (storage / "microsoft-install.json").write_text(json.dumps({"iso": str(iso), "env_file": str(env), "temp": str(root / "installer")}))
            with patch.dict(os.environ, {}, clear=True):
                service = config.generate(root, {"cpus": 4, "ram_mib": 12288}, quiet=True)["services"]["windows"]
            self.assertEqual(service["environment"]["VERSION"], "11")
            self.assertEqual(service["environment"]["KVM"], "Y")
            self.assertEqual(service["env_file"], [str(env)])
            self.assertIn(str(iso) + ":/boot.iso:ro", service["volumes"])
            self.assertNotIn("private-fixture-password", (storage / "windows.yaml").read_text())
            self.assertFalse((storage / "data.img").exists())

    def test_failed_microsoft_checksum_preserves_existing_windows_on_reset(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            storage = root / "windows"
            storage.mkdir()
            original = storage / "data.img"
            original.write_bytes(b"Windows and user files to preserve")
            cache = root / "cache"
            cache.mkdir()
            def download(args, **kwargs):
                Path(args[-1]).write_bytes(b"bad")
            with patch.object(media, "ISO_BYTES", 3), patch.object(media, "ISO_SHA256", hashlib.sha256(b"yes").hexdigest()), patch.object(media.shutil, "disk_usage", return_value=shutil._ntuple_diskusage(100 * config.GIB, 0, 100 * config.GIB)), patch.object(media.subprocess, "run", side_effect=download), self.assertRaisesRegex(ValueError, "checksum"):
                media.prepare(root, cache, replace=True)
            self.assertEqual(original.read_bytes(), b"Windows and user files to preserve")
            self.assertFalse((storage / "microsoft-install.json").exists())


class ResourceTests(unittest.TestCase):
    def test_host_memory_and_cpu_count_do_not_override_container_limits(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "memory.max").write_text(str(16 * config.GIB))
            (root / "memory.current").write_text(str(config.GIB))
            (root / "memory.stat").write_text("inactive_file 0\n")
            (root / "cpu.max").write_text("400000 100000\n")
            meminfo = root / "meminfo"
            meminfo.write_text("MemTotal: 134217728 kB\nMemAvailable: 125829120 kB\n")
            with patch.object(os, "sched_getaffinity", return_value=set(range(32))):
                limits = config.resources(root, meminfo)
            self.assertEqual(limits["cpus"], 4)
            self.assertEqual(limits["total"], 16 * config.GIB)
            self.assertEqual(limits["ram_mib"], 13 * 1024)

    def test_memory_limit_still_applies_without_optional_memory_stat(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "memory.max").write_text(str(8 * config.GIB))
            (root / "memory.current").write_text(str(config.GIB))
            meminfo = root / "meminfo"
            meminfo.write_text("MemTotal: 134217728 kB\nMemAvailable: 125829120 kB\n")
            self.assertEqual(config.resources(root, meminfo)["ram_mib"], 5 * 1024)

    def test_memory_reserve_is_left_after_existing_host_processes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            meminfo = root / "meminfo"
            meminfo.write_text("MemTotal: 16777216 kB\nMemAvailable: 15204352 kB\n")
            limits = config.resources(root, meminfo)
            # 16 GiB total, 1.5 GiB already used, and 2 GiB still available to Linux.
            self.assertEqual(limits["ram_mib"], 12800)

    def test_config_rejects_overcommit_and_disk_shrink(self):
        with tempfile.TemporaryDirectory(prefix="workspace with spaces ") as directory:
            root = Path(directory)
            storage = root / "windows"
            storage.mkdir()
            with (storage / "data.img").open("wb") as disk:
                disk.truncate(64 * config.GIB)
            limits = {"cpus": 4, "ram_mib": 14 * 1024}
            for setting in ({"CPU_CORES": 8}, {"RAM_SIZE": "16G"}, {"DISK_SIZE": "32G"}):
                (storage / "settings.json").write_text(json.dumps(setting))
                with patch.dict(os.environ, {}, clear=True), self.assertRaises(ValueError):
                    config.generate(root, limits)
            (storage / "settings.json").unlink()
            with patch.dict(os.environ, {}, clear=True):
                generated = config.generate(root, limits)
            env = generated["services"]["windows"]["environment"]
            self.assertEqual(env["RAM_SIZE"], "14336M")
            self.assertEqual(env["DISK_SIZE"], "65536M")
            self.assertEqual(env["KVM"], "Y")
            self.assertEqual(env["DEBUG"], "N")


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="storage with spaces ")
        self.root = Path(self.temp.name)
        self.workspace = self.root / "workspace"
        self.storage = self.workspace / "windows"
        self.storage.mkdir(parents=True)
        self.scratch = self.root / "scratch"
        with (self.storage / "data.img").open("wb") as disk:
            disk.truncate(128 * config.GIB)
        self.primary = {"type": "ext4", "device": 1, "fsid": 1,
                        "total_bytes": 32 * config.GIB, "available_bytes": 18 * config.GIB}
        self.secondary = {"type": "ext4", "device": 2, "fsid": 2,
                          "total_bytes": 118 * config.GIB, "available_bytes": 117 * config.GIB}

    def tearDown(self):
        self.temp.cleanup()

    def generate(self, **settings):
        settings = {"SCRATCH_DIR": str(self.scratch), **settings}
        (self.storage / "settings.json").write_text(json.dumps(settings))

        def probe(path):
            facts = self.primary if path == self.storage else self.secondary
            return {**facts, "path": str(path)}

        with patch.dict(os.environ, {}, clear=True), patch.object(config, "filesystem", side_effect=probe):
            return config.generate(self.workspace, {"cpus": 4, "ram_mib": 14336}, quiet=True)

    def test_maximum_scratch_uses_real_free_space_and_preserves_large_boot_disk(self):
        service = self.generate()["services"]["windows"]
        self.assertEqual(service["environment"]["DISK2_SIZE"], "115712M")
        self.assertEqual(service["environment"]["DISK_SIZE"], "131072M")
        self.assertIn(f"{self.scratch}:/storage2", service["volumes"])
        plan = json.loads((self.storage / "storage.json").read_text())
        self.assertTrue(plan["workspace"]["overcommitted"])
        self.assertEqual(plan["workspace"]["growth_budget_bytes"], 16 * config.GIB)
        self.assertTrue(plan["scratch"]["enabled"])
        self.assertFalse(plan["scratch"]["overcommitted"])

    def test_shared_and_memory_backed_filesystems_do_not_create_extra_capacity(self):
        for changes in ({"device": 1}, {"fsid": 1}, {"type": "tmpfs"}, {"type": "ramfs"}):
            with self.subTest(changes=changes):
                original = self.secondary.copy()
                self.secondary.update(changes)
                service = self.generate()["services"]["windows"]
                self.assertNotIn("DISK2_SIZE", service["environment"])
                self.assertFalse(json.loads((self.storage / "storage.json").read_text())["scratch"]["enabled"])
                self.secondary = original

    def test_used_scratch_disk_is_preserved_when_host_free_space_falls(self):
        self.scratch.mkdir()
        disk = self.scratch / "data2.img"
        with disk.open("wb") as image:
            image.write(b"scratch data to preserve")
            image.truncate(110 * config.GIB)
        self.secondary["available_bytes"] = 41 * config.GIB
        service = self.generate()["services"]["windows"]
        self.assertEqual(service["environment"]["DISK2_SIZE"], "112640M")
        self.assertTrue(json.loads((self.storage / "storage.json").read_text())["scratch"]["overcommitted"])
        with disk.open("rb") as image:
            self.assertEqual(image.read(24), b"scratch data to preserve")
        with self.assertRaisesRegex(ValueError, "cannot shrink"):
            self.generate(DISK2_SIZE="32G")

    def test_scratch_budget_counts_existing_allocated_data(self):
        self.scratch.mkdir()
        disk = self.scratch / "data2.img"
        with disk.open("wb") as image:
            image.truncate(32 * config.GIB)
        self.secondary["available_bytes"] = 41 * config.GIB
        with patch.object(config, "allocated_bytes", side_effect=lambda path: 20 * config.GIB if path == disk else 0):
            service = self.generate()["services"]["windows"]
        # 20 GiB already in the image + 41 GiB free - 4 GiB for the host.
        self.assertEqual(service["environment"]["DISK2_SIZE"], "58368M")

    def test_nearly_full_existing_scratch_disk_fails_without_modifying_it(self):
        self.scratch.mkdir()
        disk = self.scratch / "data2.img"
        disk.write_bytes(b"existing scratch data")
        self.secondary["available_bytes"] = 512 * config.MIB
        with self.assertRaisesRegex(ValueError, "Less than 1 GiB"):
            self.generate()
        self.assertEqual(disk.read_bytes(), b"existing scratch data")

    def test_rejects_expansion_above_physical_capacity_and_low_workspace_space(self):
        for settings in ({"DISK_SIZE": "256G"}, {"DISK2_SIZE": "128G"}):
            with self.subTest(settings=settings), self.assertRaisesRegex(ValueError, "physical capacity"):
                self.generate(**settings)
        self.primary["available_bytes"] = config.GIB
        with self.assertRaisesRegex(ValueError, "Less than 2 GiB"):
            self.generate()

    def test_small_temporary_disk_and_explicit_off_keep_only_the_boot_disk(self):
        service = self.generate(DISK2_SIZE="off")["services"]["windows"]
        self.assertNotIn("DISK2_SIZE", service["environment"])
        self.secondary["available_bytes"] = 4 * config.GIB + 512 * config.MIB
        service = self.generate()["services"]["windows"]
        self.assertNotIn("DISK2_SIZE", service["environment"])
        self.assertFalse(self.scratch.exists())


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="dind regression ")
        self.root = Path(self.temp.name)
        shutil.copytree(ROOT / ".devcontainer", self.root / ".devcontainer")
        storage = self.root / "windows"
        storage.mkdir()
        (storage / "data.img").write_bytes(b"original Windows disk")
        (storage / "windows.yaml").write_text('{"services":{"windows":{"image":"test"}}}')
        mockbin = self.root / "bin"
        mockbin.mkdir()
        self.log = self.root / "commands"
        self.env = dict(os.environ, WINDOWS_WORKSPACE=str(self.root), CALL_LOG=str(self.log),
                        PATH=str(mockbin) + ":" + os.environ["PATH"])
        self.tool("docker", '''printf '%s\\n' "$*" >> "$CALL_LOG"
case "$1 $2" in
  "info ") exit 0;;
  "inspect --format") exit 1;;
esac
exit 0
''')
        # Simulated hardware for lifecycle tests; production's real KVM probe
        # remains covered separately and has no fallback switch.
        (self.root / ".devcontainer/windows-config.py").write_text('''import json,os,sys
from pathlib import Path
if "--check-kvm" not in sys.argv:
    p=Path(os.environ["WINDOWS_WORKSPACE"])/"windows/windows.yaml"
    p.write_text(json.dumps({"services":{"windows":{"image":"test"}}}))
''')

    def tearDown(self):
        self.temp.cleanup()

    def tool(self, name, script):
        target = self.root / "bin" / name
        target.write_text("#!/bin/bash\n" + script)
        target.chmod(0o755)

    def run_helper(self, name, *args):
        return subprocess.run(["bash", str(self.root / ".devcontainer/helpers" / name), *args],
                              env=self.env, capture_output=True, text=True, timeout=10)

    def test_cached_image_without_container_uses_up_and_preserves_disk(self):
        result = self.run_helper("start")
        self.assertEqual(result.returncode, 0, result.stderr)
        commands = self.log.read_text()
        self.assertIn("up --detach --remove-orphans", commands)
        self.assertNotIn(" images", commands)
        self.assertEqual((self.root / "windows/data.img").read_bytes(), b"original Windows disk")
        self.assertTrue((self.root / "windows/.autostart").exists())

    def test_stop_removes_autostart_only_after_success(self):
        marker = self.root / "windows/.autostart"
        marker.touch()
        self.tool("docker", '''case "$*" in
  info) exit 0;;
  *"stop --timeout"*) exit 1;;
esac
''')
        self.assertNotEqual(self.run_helper("stop").returncode, 0)
        self.assertTrue(marker.exists())
        self.tool("docker", 'exit 0\n')
        self.assertEqual(self.run_helper("stop").returncode, 0)
        self.assertFalse(marker.exists())

    def test_repeated_start_does_not_reallocate_a_running_vm(self):
        self.tool("docker", '''printf '%s\\n' "$*" >> "$CALL_LOG"
case "$*" in
  *State.Running*) echo true;;
  *com.windows-dind.config*) echo 5;;
esac
''')
        result = self.run_helper("start")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("already running", result.stdout)
        self.assertNotIn("up --detach", self.log.read_text())

    def test_missing_hardware_stops_before_docker_or_image_import(self):
        (self.root / ".devcontainer/windows-config.py").write_text('import sys; sys.exit(88)\n')
        result = self.run_helper("start")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.log.exists())
        self.assertEqual((self.root / "windows/data.img").read_bytes(), b"original Windows disk")

    def test_reset_stops_container_before_import_and_failed_import_preserves_disk(self):
        (self.root / ".devcontainer/prepare-image.sh").write_text('''#!/bin/bash
printf '%s\\n' IMPORT >> "$CALL_LOG"
exit 1
''')
        result = self.run_helper("reset", "--yes")
        self.assertNotEqual(result.returncode, 0)
        commands = self.log.read_text().splitlines()
        stopped = next(i for i, command in enumerate(commands) if "down --timeout 120" in command)
        self.assertLess(stopped, commands.index("IMPORT"))
        self.assertEqual((self.root / "windows/data.img").read_bytes(), b"original Windows disk")

    def test_resume_does_not_wait_for_expired_tailscale_login(self):
        self.tool("tailscale", '''case "$1" in
  status) printf '{"BackendState":"NeedsLogin"}';;
  up) printf 'UNEXPECTED_LOGIN\\n' >> "$CALL_LOG"; exit 1;;
esac
''')
        self.tool("pgrep", 'exit 0\n')
        self.env.pop("TAILSCALE_AUTHKEY", None)
        result = self.run_helper("start-tailscale", "--resume-only")
        # The daemon's lock/log directory is writable in the devcontainer.
        if "Permission denied" in result.stderr:
            self.skipTest("Tailscale lifecycle test runs as root in the test container")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("needs authentication", result.stdout)
        self.assertFalse(self.log.exists())


@unittest.skipUnless(shutil.which("qemu-img") and shutil.which("qemu-io"), "QEMU tools are installed in the test container")
class ImageImportTests(unittest.TestCase):
    def test_conversion_and_invalid_replacement_keep_verified_bytes(self):
        with tempfile.TemporaryDirectory(prefix="image import with spaces ") as directory:
            root = Path(directory)
            shutil.copytree(ROOT / ".devcontainer", root / ".devcontainer")
            source = root / "source.vhdx"
            subprocess.run(["qemu-img", "create", "-f", "vhdx", str(source), "64M"], check=True, capture_output=True)
            subprocess.run(["qemu-io", "-f", "vhdx", "-c", "write -P 0x5a 0 1M", str(source)], check=True, capture_output=True)
            env = dict(os.environ, WINDOWS_WORKSPACE=str(root), WINDOWS_SOURCE_VHDX=str(source), WINDOWS_IMAGE_CACHE=str(root / "cache"))
            prepare = ["bash", str(root / ".devcontainer/prepare-image.sh")]
            result = subprocess.run(prepare, env=env, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            target = root / "windows/data.img"
            subprocess.run(["qemu-img", "compare", "-f", "vhdx", "-F", "raw", str(source), str(target)], check=True, capture_output=True)
            bad = root / "invalid.vhdx"
            bad.write_bytes(b"invalid VHDX data")
            env["WINDOWS_SOURCE_VHDX"] = str(bad)
            result = subprocess.run(prepare + ["--replace"], env=env, capture_output=True, text=True, timeout=30)
            self.assertNotEqual(result.returncode, 0)
            subprocess.run(["qemu-img", "compare", "-f", "vhdx", "-F", "raw", str(source), str(target)], check=True, capture_output=True)
            self.assertFalse((root / "windows/data.img.partial").exists())
            empty = root / "empty.vhdx"
            subprocess.run(["qemu-img", "create", "-f", "vhdx", str(empty), "64M"], check=True, capture_output=True)
            env["WINDOWS_SOURCE_VHDX"] = str(empty)
            result = subprocess.run(prepare + ["--replace"], env=env, capture_output=True, text=True, timeout=30)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("no readable boot data", result.stderr)
            subprocess.run(["qemu-img", "compare", "-f", "vhdx", "-F", "raw", str(source), str(target)], check=True, capture_output=True)
            self.assertFalse((root / "windows/data.img.partial").exists())


if __name__ == "__main__":
    unittest.main()
