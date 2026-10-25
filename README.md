# Welcome to windows-dind

This repository includes the required files which allows you to run Windows 11 on GitHub Codespaces.

It installs Tailscale which allows you to Remote Desktop Protocol (RDP) into Windows 11.

It is based on the [dockur/windows](https://github.com/dockur/windows) repository but contains customizations and optimizations for GitHub Codespaces.

## Repaired Codespaces setup

Create the Codespace from **your fork and the branch containing these fixes**. Choose the **4-core/16-GB machine**, the largest CPU/RAM configuration available to this account, with the most storage offered at that size. The old badge and CLI examples pointed to ItzLevvie's upstream repository, so they did not use changes in a fork.

Once the terminal opens, run `start`. This checks working KVM acceleration and prepares a verified Microsoft Windows 11 Pro installation if no Windows disk exists. The author's newest Insider image expired on August 11, 2026, so new installations use supported non-evaluation media. Existing Windows disks are preserved. Open forwarded port **8006** to view setup, then connect using a GitHub CLI TCP tunnel or `start-tailscale`. The installer login is saved privately in `/workspaces/.windows-rdp/credentials.txt`.

For passwords, Windows RDP configuration, an alternative local TCP tunnel, performance settings, and recovery instructions, see [the setup guide](docs/codespaces-setup.md). Run `windows-doctor` to collect VM, KVM, storage, and RDP diagnostics. [The investigation report](docs/investigation.md) explains the original failures and exactly what was tested.

Windows data stays in `windows/` across devcontainer rebuilds. A VM that was running resumes when the Codespace starts; `stop` disables that automatic resume. The first installation needs **20 GiB of temporary staging space**, with installer extraction kept outside the persistent workspace. The script checks capacity and the Microsoft ISO checksum before proceeding. It exposes the maximum usable space on a separate disk-backed `/tmp` filesystem as a scratch drive, leaving host headroom. **Scratch contents are deleted when the Codespace stops or times out.** The boot disk remains in the workspace. Windows activation requires your own valid license.

> [!CAUTION]
> This repository should be used for development and testing purposes only. <br>
> I am not responsible for any issues such as account suspensions or data loss.

## Table of Contents
- [Images](#images)
- [Usage](#usage)
    - [Using the web version of GitHub (recommended)](#using-the-web-version-of-github-recommended)
    - [Using the CLI version of GitHub (alternative)](#using-the-cli-version-of-github-alternative)
- [Commands](#commands)
- [Frequently Asked Questions (FAQ)](#frequently-asked-questions-faq)
    - [Why did you create this repository?](#why-did-you-create-this-repository)
    - [What machine types are available for GitHub Codespaces?](#what-machine-types-are-available-for-github-codespaces)
    - [How many usage hours can I use GitHub Codespaces for free each month?](#how-many-usage-hours-can-i-use-github-codespaces-for-free-each-month)
    - [What regions are available for my GitHub Codespaces?](#what-regions-are-available-for-my-github-codespaces)
    - [How can I change the inactivity timeout for my GitHub Codespaces?](#how-can-i-change-the-inactivity-timeout-for-my-github-codespaces)
    - [Why did you choose Tailscale over Ngrok for Remote Desktop Protocol (RDP)?](#why-did-you-choose-tailscale-over-ngrok-for-remote-desktop-protocol-rdp)
    - [What are the steps to create my own system images?](#what-are-the-steps-to-create-my-own-system-images)
        - [Requirements](#requirements)
        - [Guide](#guide)

## Images

Below are images of Windows 11 running on GitHub Codespaces:

![Image](https://github.com/user-attachments/assets/561bb50d-eee8-46cb-9614-8d5a16a9296c)

![Image](https://github.com/user-attachments/assets/3ec6ea7f-8664-4449-9495-c748ea29aef5)

![Image](https://github.com/user-attachments/assets/3973420c-8732-4740-b280-ecd9aa808f3d)

![Image](https://github.com/user-attachments/assets/e006bcd4-a265-417e-b535-20a1d7036dfc)

## Usage

### Using the web version of GitHub (recommended)

Click on the button below:

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://github.com/codespaces/new)

Select your fork, the repaired branch, and your desired machine size.

> [!NOTE]
> See [Commands](#commands) for a full list of available commands.

---

### Using the CLI version of GitHub (alternative)

Install [GitHub CLI](https://github.com/cli/cli/releases/latest), authenticate, and list the 4-core machines offered for your fork:

```sh
gh api repos/YOUR_GITHUB_USERNAME/dind/codespaces/machines --jq '.machines | map(select(.cpus == 4)) | sort_by(.storage_in_bytes) | reverse | .[] | {name, cpus, memory_in_bytes, storage_in_bytes}'
gh codespace create --repo YOUR_GITHUB_USERNAME/dind --branch YOUR_FIXED_BRANCH --machine standardLinux32gb
gh codespace list --repo YOUR_GITHUB_USERNAME/dind
```

Use the name of the offered 4-core/16-GB machine with the largest storage allocation if it differs from `standardLinux32gb`. Replace the repository and branch with your fork and repaired branch.

## Commands

This repository contains a few helper scripts[^3] to get you started.

[^3]: These helper scripts are located [here](https://github.com/ItzLevvie/dind/tree/main/.devcontainer/helpers).

| Command | Description |
| :-: | :-: |
| start | Starts Windows 11 |
| stop | Stops Windows 11 |
| restart | Restarts Windows 11 |
| /usr/local/bin/kill | Forcefully stops Windows 11; the absolute path avoids Bash's built-in kill |
| reset --yes | Stops the VM and imports a clean copy of the original image, replacing Windows changes |
| remove | Removes the `windows` container |
| rebuild | Performs a full rebuild of your GitHub Codespaces |
| start-tailscale | Starts Tailscale |
| windows-doctor | Reports actual resource limits, KVM availability, VM logs, and the guest RDP listener |

## Frequently Asked Questions (FAQ)

### Why did you create this repository?

This repository was inspired by many different YouTube videos:
1) [Codespaces Windows 11 tutorial and playing](https://www.youtube.com/watch?v=ZxDTzAqBB1c) by [HyperNexus](https://www.youtube.com/@hyrnexs)
2) [Installing Windows 11 on GitHub Codespaces](https://www.youtube.com/watch?v=PQv-1-qI9zg) by [LagLife](https://www.youtube.com/@laglife)
3) [Installing Windows 10 on GitHub Codespaces!](https://www.youtube.com/watch?v=ffdYdsejzrY) by [Nashville](https://www.youtube.com/@MSNashville7)
4) [[PATCHED] How to Create Windows QEMU VM from Codespaces - Free Windows VPS from Codespace](https://www.youtube.com/watch?v=-kzua2uEMC8) by [Paddi's Tech Stuff](https://www.youtube.com/@PaddisTechStuff)
5) [How to Run Windows 10 Cloud PC on your Device using Github Codespace [New Method] [2025].](https://www.youtube.com/watch?v=Sg8m_hyNioI) by [JoyZoneTech](https://www.youtube.com/@JoyZoneTech)
6) [How to Create a Free Windows 10 RDP on GitHub](https://www.youtube.com/watch?v=Pc9FgSvnI90) by [TechXploitz](https://www.youtube.com/@techxploitz)
7) [Windows in a Github Codespace Dev Container](https://www.youtube.com/watch?v=o0c9DexUVpI) by [HashiQube DevOps Lab](https://www.youtube.com/@hashiqube)
8) [Get FREE Windows RDP ✅ | New Github Method](https://www.youtube.com/watch?v=HykF03LxtwA) by [Earnastic](https://www.youtube.com/@earnastic)

This repository was also inspired by many different websites:
1) [Run Windows 10 for free in GitHub codespaces using QEMU](https://www.aih.app/2023/02/04/run-windows-10-for-free-in-github-codespaces-using-qemu/) by [Shreejal Maharjan](https://github.com/shreejalmaharjan-27)

---

### What machine types are available for GitHub Codespaces?

This account's maximum is **4 cores and 16 GB RAM**. The repaired devcontainer requests that size and gives Windows all 4 vCPUs. RAM is measured after existing host use, leaving at least 2 GiB available for the Codespace. The tested automatic allocation was about 12.3 GiB; 13-GiB and 13.6-GiB trials were externally terminated.

Use `gh api repos/YOUR_GITHUB_USERNAME/dind/codespaces/machines` to check the storage allocation actually offered at that size. The usual `standardLinux32gb` allocation is 32 GB of persistent workspace storage. `/tmp` capacity varies by host; inspect `windows-doctor` rather than assuming the old upstream 118-GB figure applies.

The repair uses actual filesystem measurements for its additional scratch disk and requires functional KVM. It cannot increase GitHub's physical disk allocation or supply KVM if the host does not expose it. See the [performance and storage guide](docs/codespaces-setup.md).

---

### How many usage hours can I use GitHub Codespaces for free each month?

GitHub Codespaces has different usage hours based on which plan your GitHub account uses.

Below are the different usage hours for your GitHub Codespaces:

| Machine Type | GitHub Free <br> (120 core hours per month) | GitHub Pro <br> (180 core hours per month) | Microsoft employees and partners <br> (unlimited core hours per month) |
| :-: | :-: | :-: | :-: |
| basicLinux32gb | 60 usage hours | 90 usage hours | unlimited usage hours |
| standardLinux32gb | 30 usage hours | 45 usage hours | unlimited usage hours |
| premiumLinux[^1] | 15 usage hours | 22.5 usage hours | unlimited usage hours |
| largePremiumLinux[^1] | 7.5 usage hours | 11.25 usage hours | unlimited usage hours |
| xLargePremiumLinux[^1][^2] | 3.75 usage hours | 5.625 usage hours | unlimited usage hours |

> [!NOTE]
> If you are on GitHub Free, you can use GitHub Codespaces for free (up to 60 usage hours per month). <br><br>
> After this, you will need to provide your payment details to continue using GitHub Codespaces.

> [!TIP]
> GitHub has a formula to calculate your core hours. <br>
> It is the **number of cores** multiplied by **how many hours you used a particular machine type**. <br><br>
> For example:
> - If you wanted to use `premiumLinux` (8 cores) for 2 hours then you calculate 8 * 2 = 16 core hours <br>
> - If you wanted to use `premiumLinux` (8 cores) for 8 hours then you calculate 8 * 8 = 64 core hours

---

### What regions are available for my GitHub Codespaces?

Your GitHub Codespaces is deployed to one of several Microsoft Azure regions based on the location of your IP address.

Below are the different Microsoft Azure regions available for your GitHub Codespaces:

| Geography | Region | Location |
| :-: | :-: | :-: |
| Asia Pacific | Southeast Asia | Singapore |
| Australia | Australia Central | Canberra |
| Australia | Australia East | New South Wales |
| Europe | West Europe | Netherlands |
| India | Central India | Pune |
| United Kingdom | UK South | London |
| United States | East US | Virginia |
| United States | East US 2 | Virginia |
| United States | West US 2 | Washington |
| United States | West US 3 | Arizona |

---

### How can I change the inactivity timeout for my GitHub Codespaces?

By default, your GitHub Codespaces has an inactivity timeout of 30 minutes.

However, you can extend this inactivity timeout to a maximum of 240 minutes (4 hours) at [GitHub Codespaces — Settings](https://github.com/settings/codespaces) under `Default idle timeout`

---

### Why did you choose Tailscale over Ngrok for Remote Desktop Protocol (RDP)?

Tailscale has the lowest latency because all connections are peer-to-peer (P2P).

Tailscale has [more features](https://tailscale.com/compare) than its competitors.

Ngrok uses a tunnel server which increases the latency for your Remote Desktop Protocol (RDP) connections.

Ngrok requires your payment details to allow TCP connections which is required for Remote Desktop Protocol (RDP) to properly work.

---

### What are the steps to create my own system images?

#### Requirements

- Hyper-V with Secure Boot, Trusted Platform Module (TPM), and Network Adapter (Ethernet) disabled.
- `Windows11_InsiderPreview_EnterpriseVL_x64_en-us_29599_1000.iso` from [Windows Insider Preview — ISOs](https://www.microsoft.com/en-us/software-download/windowsinsiderpreviewiso) is mounted as a DVD Drive on Hyper-V.
- `virtio-win-1.9.57.iso` from [Red Hat Enterprise Linux 10 — AppStream](https://github.com/ItzLevvie/artifacts/releases/latest/download/virtio-win.iso) is mounted as a DVD Drive on Hyper-V.

---

#### Guide

1\) In the Windows 11 Setup where it says `Select language settings`:
- press <kbd>Shift</kbd> + <kbd>F10</kbd>
- type `regedit` and press <kbd>Enter</kbd>

Create three registry entries at `HKEY_LOCAL_MACHINE\SYSTEM\Setup\LabConfig`:
- `BypassSecureBootCheck` with a value of `1`
- `BypassTPMCheck` with a value of `1`
- `BypassRAMCheck` with a value of `1`

> [!IMPORTANT]
> These registry entries are read by Windows 11 Setup from `Windows11_InsiderPreview_EnterpriseVL_x64_en-us_29599_1000.iso\sources\winsetup.dll` which allows you to bypass the system requirements for Windows 11.

---

2\) In the Windows 11 Setup where it says `Select location to install Windows 11`:
- click `Load Driver`
- uncheck `Hide drivers that aren't compatible with this computer's hardware`
- click `Browse`
- select `CD Drive (E:) virtio-win-1.9.57`
- install `vioscsi` from `E:\vioscsi\w11\amd64\vioscsi.inf`

> [!IMPORTANT]
> This installs the required SCSI drivers to allow Windows 11 to boot on QEMU.

---

3\) In the Windows 11 OOBE where it says `Is this the right country or region?`:
- press <kbd>Shift</kbd> + <kbd>F10</kbd>
- type `cd /d E:` and press <kbd>Enter</kbd>
- type `virtio-win-gt-x64.msi` and press <kbd>Enter</kbd>
- type `shutdown /r /t 0` and press <kbd>Enter</kbd>

> [!IMPORTANT]
> This installs all of the required paravirtualized drivers for Windows 11 to work properly on QEMU.

---

4\) In the Windows 11 OOBE where it says `Is this the right country or region?`:
- press <kbd>Shift</kbd> + <kbd>F10</kbd>
- type `regedit` and press <kbd>Enter</kbd>

Create one registry entry at `HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\Dwm`:
- `ForceEffectMode` with a value of `2`

> [!TIP]
> This allows Windows 11 to force Mica and rounded corners. <br>
> This registry entry is read by Windows 11 from `C:\Windows\System32\dwmcore.dll`

---

5\) In the Windows 11 OOBE where it says `Is this the right country or region?`:
- press <kbd>Shift</kbd> + <kbd>F10</kbd>
- type `netsh advfirewall set allprofiles state off` and press <kbd>Enter</kbd>
- type `regedit` and press <kbd>Enter</kbd>

Create one registry entry at `HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Microsoft\Windows NT\Terminal Services`:
- `fDenyTSConnections` with a value of `0`

> [!TIP]
> This enables Remote Desktop Protocol (RDP).

Create one registry entry at `HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Lsa`:
- `LimitBlankPasswordUse` with a value of `0`

> [!TIP]
> This allows you to Remote Desktop Protocol (RDP) into Windows 11 with blank passwords.

---

6\) In the Windows 11 OOBE where it says `Is this the right country or region?`:
- press <kbd>Shift</kbd> + <kbd>F10</kbd>
- type `powercfg /list` and press <kbd>Enter</kbd>
- type `powercfg /setactive e9a42b02-d5df-448d-aa00-03f14749eb61` and press <kbd>Enter</kbd>
- type `powercfg /getactivescheme` and press <kbd>Enter</kbd>
- type `powercfg /change monitor-timeout-ac 0` and press <kbd>Enter</kbd>

> [!TIP]
> This sets the power plan to Ultimate Performance.

---

7\) In the Windows 11 OOBE where it says `Is this the right country or region?`:
- press <kbd>Shift</kbd> + <kbd>F10</kbd>
- type `regedit` and press <kbd>Enter</kbd>

Create one registry entry at `HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Microsoft\Windows\LanmanWorkstation`:
- `AllowInsecureGuestAuth` with a value of `1`

Create one registry entry at `HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\LanmanWorkstation\Parameters`:
- `RequireSecuritySignature` with a value of `0`

> [!TIP]
> This allows you to access SMB shares.

---

8\) In the Windows 11 OOBE where it says `Is this the right country or region?`:
- press <kbd>Shift</kbd> + <kbd>F10</kbd>
- type `regedit` and press <kbd>Enter</kbd>

Create one registry entry at `HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\OOBE`:
- `BypassNRO` with a value of `1`

> [!TIP]
> This allows you to create a local account on Windows 11.

---

9\) In the Windows 11 OOBE where it says `Is this the right country or region?`:
- press <kbd>Shift</kbd> + <kbd>F10</kbd>
- type `cscript //nologo slmgr.vbs /skms azkms.core.windows.net` and press <kbd>Enter</kbd>
- type `shutdown /s /t 0` and press <kbd>Enter</kbd>

> [!TIP]
> This allows you to activate Windows 11 Enterprise for free.

---

10\) Hyper-V will store your VHDX file at `C:\ProgramData\Microsoft\Windows\Virtual Hard Disks\data.vhdx`

You will have to send your VHDX file to your GitHub Codespaces using [GitHub CLI](https://github.com/cli/cli/releases/latest): `gh codespace cp --expand "C:\ProgramData\Microsoft\Windows\Virtual Hard Disks\data.vhdx" remote:/workspaces/github`

---

11\) Your VHDX file will have to be converted to an IMG file for QEMU.

`qemu-img convert -p -O raw -o preallocation=off data.vhdx windows/data.img`
- `-p` forces QEMU to display the progress bar.
- `-O raw` forces QEMU to convert to an IMG file.

---

12\) You can upload your VHDX file to GitHub Releases.

`7z a -mmt$(nproc --all) -mx9 -v1g data.7z data.vhdx`
- `-mmt$(nproc --all)` forces 7-Zip to use all cores.
- `-mx9` forces 7-Zip to use ultra compression.
- `-v1g` forces 7-Zip to split the `data.7z` file into 1 GB chunks.
