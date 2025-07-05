# Welcome to windows-dind

This repository includes the required files which allows you to run Windows 11 on GitHub Codespaces.

It installs Tailscale which allows you to Remote Desktop Protocol (RDP) into Windows 11.

It is based on the [dockur/windows](https://github.com/dockur/windows) repository but contains customizations and optimizations for GitHub Codespaces.

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

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/ItzLevvie/dind?machine=standardLinux32gb)

> [!NOTE]
> See [Commands](#commands) for a full list of available commands.

---

### Using the CLI version of GitHub (alternative)

1) Install [GitHub CLI](https://github.com/cli/cli/releases/latest)
2) Type `gh codespace create --idle-timeout 4h --retention-period 720h --repo ItzLevvie/dind --machine standardLinux32gb` in Command Prompt or PowerShell.
3) This will allow you to create the GitHub Codespaces based on the files from this repository:
    ```
    C:\Users\codespaces>gh codespace create --idle-timeout 4h --retention-period 720h --repo ItzLevvie/dind --machine xLargePremiumLinux
      ✓ Codespaces usage for this repository is paid for by microsoft
    congenial-goldfish-5ggv6rrqpx7c7pj
    ```
4) Type `gh codespace view --repo ItzLevvie/dind --json billableOwner,createdAt,devcontainerPath,displayName,environmentId,idleTimeoutMinutes,lastUsedAt,location,machineDisplayName,machineName,name,owner,prebuild,repository,retentionExpiresAt,retentionPeriodDays,state` in Command Prompt or PowerShell.
5) This will allow you to see the status of your GitHub Codespaces:
    ```
    C:\Users\codespaces>gh codespace view --repo ItzLevvie/dind --json billableOwner,createdAt,devcontainerPath,displayName,environmentId,idleTimeoutMinutes,lastUsedAt,location,machineDisplayName,machineName,name,owner,prebuild,repository,retentionExpiresAt,retentionPeriodDays,state
    ? Choose codespace: ItzLevvie/dind [main]: congenial goldfish
    {
      "billableOwner": {
        "login": "microsoft",
        "type": "Organization"
      },
      "createdAt": "2025-03-25T18:29:21+00:00",
      "devcontainerPath": ".devcontainer/devcontainer.json",
      "displayName": "congenial goldfish",
      "environmentId": "b1f7729a-c417-47cd-a4ce-811cf3952b8c",
      "idleTimeoutMinutes": 240,
      "lastUsedAt": "2025-03-25T18:29:21+00:00",
      "location": "UkSouth",
      "machineDisplayName": "32 cores, 128 GB RAM, 128 GB storage",
      "machineName": "xLargePremiumLinux",
      "name": "congenial-goldfish-5ggv6rrqpx7c7pj",
      "owner": "ItzLevvie",
      "prebuild": false,
      "repository": "ItzLevvie/dind",
      "retentionExpiresAt": "",
      "retentionPeriodDays": 30,
      "state": "Available"
    }
    ```
6) When it says `"state": "Available"` — you can access your GitHub Codespaces at [GitHub Codespaces — Dashboard](https://github.com/codespaces):
    ![Image](https://github.com/user-attachments/assets/eab700ae-18d1-4d3b-9c74-932b5bf8ab79)

> [!NOTE]
> See [Commands](#commands) for a full list of available commands.

---

### Commands

This repository contains a few helper scripts[^3] to get you started.

[^3]: These helper scripts are located [here](https://github.com/ItzLevvie/dind/tree/main/.devcontainer/helpers).

| Command | Description |
| :-: | :-: |
| start | Starts Windows 11 |
| stop | Stops Windows 11 |
| restart | Restarts Windows 11 |
| kill | Forcefully stops Windows 11 |
| reset | Resets Windows 11 to a clean state <br><br> Note: This will only work if the `/tmp/github/windows/data.img` file exists |
| remove | Removes the `windows` container |
| rebuild | Performs a full rebuild of your GitHub Codespaces |

## Frequently Asked Questions (FAQ)

### Why did you create this repository?

This repository was inspired by many different YouTube videos:
1) [Codespaces Windows 11 tutorial and playing](https://www.youtube.com/watch?v=ZxDTzAqBB1c) by [HyperNexus](https://www.youtube.com/@hyrnexs)
2) [Installing Windows 11 on GitHub Codespaces](https://www.youtube.com/watch?v=PQv-1-qI9zg) by [LagLife](https://www.youtube.com/@laglife)
3) [Installing Windows 10 on GitHub Codespaces!](https://www.youtube.com/watch?v=ffdYdsejzrY) by [Nashville](https://www.youtube.com/@MSNashville7)
4) [[PATCHED] How to Create Windows QEMU VM from Codespaces - Free Windows VPS from Codespace](https://www.youtube.com/watch?v=-kzua2uEMC8) by [Paddi's Tech Stuff](https://www.youtube.com/@PaddisTechStuff)
5) [How to Run Windows 10 Cloud PC on your Device using Github Codespace [New Method] [2025].](https://www.youtube.com/watch?v=Sg8m_hyNioI) by [JoyZoneTech](https://www.youtube.com/@JoyZoneTech)
6) [How to Create a Free Windows 10 RDP on GitHub](https://www.youtube.com/watch?v=Pc9FgSvnI90) by [TechXploitz](https://www.youtube.com/@techxploitz)

This repository was also inspired by many different websites:
1) [Run Windows 10 for free in GitHub codespaces using QEMU](https://www.aih.app/2023/02/04/run-windows-10-for-free-in-github-codespaces-using-qemu/)

---

### What machine types are available for GitHub Codespaces?

GitHub Codespaces has many different machine types which you can choose based on your needs.

It uses the [AMD EPYC™ 7763](https://www.amd.com/en/products/processors/server/epyc/7003-series/amd-epyc-7763.html) (Milan) CPU which delivers the best performance as seen in [Performance Benchmarks of Cloud Machines (December 2023)](https://bas.codes/posts/cloudbench2312).

Previously, GitHub Codespaces used [Intel® Xeon® Platinum 8370C](https://azure.microsoft.com/en-us/blog/upgrade-your-infrastructure-with-the-latest-dv5ev5-azure-vms-in-preview/) (Ice Lake), [Intel® Xeon® Platinum 8272CL](https://azure.microsoft.com/en-us/blog/new-general-purpose-and-memoryoptimized-azure-virtual-machines-with-intel-now-available/) (Cascade Lake), and [Intel® Xeon® Platinum 8168](https://azure.microsoft.com/en-us/blog/fv2-vms-are-now-available-the-fastest-vms-on-azure/) (Skylake) CPUs.

Below are the different machine types available for your GitHub Codespaces:

| Machine Type | Core | RAM | Storage <br> (`/workspaces`) | Storage <br> (`/tmp`) | Price |
| :-: | :-: | :-: | :-: | :-: | :-: |
| basicLinux32gb | 2 cores <br> (1 core / 2 threads) | 8 GB | 32 GB | 44 GB | $0.18 per hour |
| standardLinux32gb | 4 cores <br> (2 cores / 4 threads) | 16 GB | 32 GB | 118 GB | $0.36 per hour |
| premiumLinux[^1] | 8 cores <br> (4 cores / 8 threads) | 32 GB | 64 GB | 265 GB | $0.72 per hour |
| largePremiumLinux[^1] | 16 cores <br> (8 cores / 16 threads) | 64 GB | 128 GB | 560 GB | $1.44 per hour |
| xLargePremiumLinux[^1][^2] | 32 cores <br> (16 cores / 32 threads) | 128 GB | 128 GB | 1.2 TB | $2.88 per hour |

[^1]: Contact [GitHub Support](https://support.github.com/) to access these machine types.
[^2]: This machine type is not available as of February 2025.

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

Tailscale has more features than its competitors.

Ngrok uses a tunnel server which increases the latency for your Remote Desktop Protocol (RDP) connections.

Ngrok requires your payment details to allow TCP connections which is required for Remote Desktop Protocol (RDP) to properly work.

---

### What are the steps to create my own system images?

#### Requirements

- Hyper-V with Secure Boot, Trusted Platform Module (TPM), and Network Adapter (Ethernet) disabled.
- `Windows11_InsiderPreview_EnterpriseVL_x64_en-us_27881.iso` from [Windows Insider Preview — ISOs](https://www.microsoft.com/en-us/software-download/windowsinsiderpreviewiso) is mounted as a DVD Drive on Hyper-V.
- `virtio-win.iso` from [Red Hat Enterprise Linux 10 — AppStream](https://github.com/ItzLevvie/artifacts/releases/latest/download/virtio-win.iso) is mounted as a DVD Drive on Hyper-V.

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
> These registry entries are read by Windows 11 Setup from `Windows11_InsiderPreview_EnterpriseVL_x64_en-us_27881.iso\sources\winsetup.dll` which allows you to bypass the system requirements for Windows 11.

---

2\) In the Windows 11 Setup where it says `Select location to install Windows 11`:
- click `Load Driver`
- uncheck `Hide drivers that aren't compatible with this computer's hardware`
- click `Browse`
- select `CD Drive (E:) virtio-win-1.9.47`
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

12\) You can upload your VHDX file to GitHub Releases

`7z a -mmt32 -mx9 -v1g data.7z data.vhdx`
- `-mmt32` forces 7-Zip to use 32 cores.
- `-mx9` forces 7-Zip to use ultra compression.
- `-v1g` forces 7-Zip to split the `data.7z` file into 1 GB chunks.
