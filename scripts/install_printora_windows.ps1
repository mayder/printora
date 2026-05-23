$ErrorActionPreference = "Stop"

$Apply = $args -contains "--apply"
$Yes = $args -contains "--yes" -or $env:PRINTORA_ASSUME_YES -eq "1"

if (-not $Apply) {
    & "$PSScriptRoot\bootstrap_windows.ps1"
    & "$PSScriptRoot\install_printora_autostart_windows.ps1"
    exit 0
}

if (-not $Yes) {
    throw "--apply exige --yes."
}

& "$PSScriptRoot\bootstrap_windows.ps1" --apply
& "$PSScriptRoot\install_printora_autostart_windows.ps1" --apply --yes
Write-Host "Printora instalado e configurado para iniciar automaticamente."
