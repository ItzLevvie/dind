# Run once per new scratch disk, in an elevated Windows PowerShell window.
# Codespaces clears /tmp (and this drive's contents) on every stop/idle timeout.
#Requires -RunAsAdministrator
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateRange(1, 255)]
    [int]$DiskNumber,
    [ValidatePattern('^[D-Zd-z]$')]
    [string]$DriveLetter = 'S',
    [string]$PlanPath = '\\host.lan\Data\windows\storage.json'
)
$ErrorActionPreference = 'Stop'
$plan = Get-Content $PlanPath -Raw | ConvertFrom-Json
if (-not $plan.scratch.enabled) { throw 'The host storage plan has no enabled scratch disk.' }
$disk = Get-Disk -Number $DiskNumber
if ($disk.IsBoot -or $disk.IsSystem -or $disk.PartitionStyle -ne 'RAW') {
    throw 'Only a blank, non-boot, non-system disk can be initialized. Existing partitions are preserved.'
}
# The VirtIO SCSI driver reports SAS on the tested Windows image.
if ($disk.BusType -notin @('SCSI', 'SAS') -or $disk.Size -ne $plan.scratch.virtual_bytes) {
    throw 'The selected disk does not match the configured VirtIO SCSI scratch disk size.'
}
if (Get-Volume -DriveLetter $DriveLetter -ErrorAction SilentlyContinue) {
    throw "Drive letter $DriveLetter is already in use. Choose a free letter."
}
if (Get-PSDrive -Name $DriveLetter -ErrorAction SilentlyContinue) {
    throw "Drive letter $DriveLetter is already mapped. Choose a free letter."
}
if ($plan.scratch.path.StartsWith('/tmp/')) {
    Write-Host 'This drive is TEMPORARY. Its contents are deleted when the Codespace stops or times out.'
} else {
    Write-Host 'This drive is outside the persistent workspace. Verify its storage lifecycle and back up important files.'
}
if ($disk.IsOffline) { Set-Disk -Number $DiskNumber -IsOffline $false }
if ($disk.IsReadOnly) { Set-Disk -Number $DiskNumber -IsReadOnly $false }
Initialize-Disk -Number $DiskNumber -PartitionStyle GPT -PassThru |
    New-Partition -UseMaximumSize -DriveLetter $DriveLetter |
    Format-Volume -FileSystem NTFS -NewFileSystemLabel 'TEMPORARY SCRATCH' -Confirm:$false | Out-Null
Write-Host "Scratch drive $($DriveLetter.ToUpper()): is ready. Back up important files into persistent storage."
