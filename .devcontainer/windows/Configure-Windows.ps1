# Run in an elevated Windows PowerShell window after completing Windows setup.
# A password is required for an account that previously had a blank password.
#Requires -RunAsAdministrator
[CmdletBinding()]
param([string]$UserName = $env:USERNAME)
$ErrorActionPreference = 'Stop'

$password = Read-Host "Set the RDP password for $UserName" -AsSecureString
if ($password.Length -eq 0) { throw 'Enter a nonempty password for RDP.' }
Set-LocalUser -Name $UserName -Password $password
$user = Get-LocalUser -Name $UserName
$rdpGroup = Get-LocalGroup -SID 'S-1-5-32-555'
$memberSids = @(Get-LocalGroupMember -Group $rdpGroup | ForEach-Object { $_.SID.Value })
if ($memberSids -notcontains $user.SID.Value) {
    Add-LocalGroupMember -Group $rdpGroup -Member $user
}
Set-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server' -Name fDenyTSConnections -Value 0
Set-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp' -Name UserAuthentication -Value 1
Set-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\Lsa' -Name LimitBlankPasswordUse -Value 1
Enable-NetFirewallRule -Name 'RemoteDesktop-UserMode-In-TCP', 'RemoteDesktop-UserMode-In-UDP'
Set-NetFirewallProfile -Profile Domain,Private,Public -Enabled True
Set-Service -Name TermService -StartupType Automatic
Start-Service -Name TermService

# High performance with no sleep while the Codespace is running.
powercfg /setactive SCHEME_MIN
if ($LASTEXITCODE -ne 0) { throw 'Could not select the High performance power plan.' }
powercfg /change standby-timeout-ac 0
powercfg /change monitor-timeout-ac 0

# Permit NTFS TRIM so deleted files can release blocks in the sparse host image.
fsutil behavior set DisableDeleteNotify NTFS 0
if ($LASTEXITCODE -ne 0) { throw 'Could not enable NTFS TRIM.' }

Write-Host "RDP enabled for $UserName with NLA and a password. High performance power plan selected."
