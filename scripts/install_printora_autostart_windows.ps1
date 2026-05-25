$ErrorActionPreference = "Stop"

$RootDir = Resolve-Path (Join-Path $PSScriptRoot "..")
$Apply = $args -contains "--apply"
$Yes = $args -contains "--yes" -or $env:PRINTORA_ASSUME_YES -eq "1"
$TaskName = "Printora"
$Port = if ($env:PRINTORA_PORT) { $env:PRINTORA_PORT } else { "8069" }
$DataDir = if ($env:PRINTORA_DATA_DIR) { $env:PRINTORA_DATA_DIR } else { Join-Path $env:LOCALAPPDATA "Printora" }
$Runner = Join-Path $RootDir "scripts\run_app_windows.ps1"

Write-Host "Printora autostart Windows"
Write-Host "mode=$(if ($Apply) { 'apply' } else { 'plan' })"
Write-Host "root_dir=$RootDir"
Write-Host "data_dir=$DataDir"
Write-Host "port=$Port"
Write-Host "task=$TaskName"
Write-Host "runner=$Runner"

if (-not $Apply) {
    exit 0
}

if (-not $Yes) {
    throw "--apply exige --yes."
}

if (-not (Test-Path $Runner)) {
    throw "Runner ausente: $Runner"
}

New-Item -ItemType Directory -Force -Path $DataDir | Out-Null
$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$Runner`" --no-open" `
    -WorkingDirectory $RootDir
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet `
    -RestartCount 999 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -AllowStartIfOnBatteries `
    -DisallowStartIfOnBatteries:$false

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Force | Out-Null
Start-ScheduledTask -TaskName $TaskName
Write-Host "Autostart do Printora configurado no Agendador de Tarefas."
