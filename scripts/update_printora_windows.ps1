$ErrorActionPreference = "Stop"

$Mode = ""
$TargetTag = ""
$RunId = ""
$PreviousPath = ""
$DbBackupPath = ""

function Write-Usage {
    Write-Host "Uso:"
    Write-Host "  powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\update_printora_windows.ps1 --Plan --Tag vX.Y.Z"
    Write-Host "  powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\update_printora_windows.ps1 --Apply --Tag vX.Y.Z"
    Write-Host "  powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\update_printora_windows.ps1 --Rollback --PreviousPath C:\Printora.previous-update-..."
}

for ($i = 0; $i -lt $args.Count; $i++) {
    switch ($args[$i]) {
        "--Plan" { $Mode = "plan" }
        "-Plan" { $Mode = "plan" }
        "--Apply" { $Mode = "apply" }
        "-Apply" { $Mode = "apply" }
        "--Rollback" { $Mode = "rollback" }
        "-Rollback" { $Mode = "rollback" }
        "--Tag" { $i++; $TargetTag = $args[$i] }
        "-Tag" { $i++; $TargetTag = $args[$i] }
        "--RunId" { $i++; $RunId = $args[$i]; $env:PRINTORA_UPDATE_RUN_ID = $RunId }
        "-RunId" { $i++; $RunId = $args[$i]; $env:PRINTORA_UPDATE_RUN_ID = $RunId }
        "--run-id" { $i++; $RunId = $args[$i]; $env:PRINTORA_UPDATE_RUN_ID = $RunId }
        "--PreviousPath" { $i++; $PreviousPath = $args[$i] }
        "-PreviousPath" { $i++; $PreviousPath = $args[$i] }
        "--previous-path" { $i++; $PreviousPath = $args[$i] }
        "--DbBackup" { $i++; $DbBackupPath = $args[$i] }
        "-DbBackup" { $i++; $DbBackupPath = $args[$i] }
        "--db-backup" { $i++; $DbBackupPath = $args[$i] }
        "-h" { Write-Usage; exit 0 }
        "--help" { Write-Usage; exit 0 }
        default { throw "Argumento inválido: $($args[$i])" }
    }
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$DefaultRootDir = Resolve-Path (Join-Path $ScriptDir "..")
$RootDir = if ($env:ROOT_DIR) { $env:ROOT_DIR } else { $DefaultRootDir.Path }
$LocalAppData = if ($env:LOCALAPPDATA) { $env:LOCALAPPDATA } else { Join-Path $HOME "AppData\Local" }
$DataDir = if ($env:PRINTORA_DATA_DIR) { $env:PRINTORA_DATA_DIR } else { Join-Path $LocalAppData "Printora" }
$DbPath = if ($env:PRINTORA_DB_PATH) { $env:PRINTORA_DB_PATH } else { Join-Path $DataDir "printora.db" }
$BackupDir = if ($env:PRINTORA_BACKUP_DIR) { $env:PRINTORA_BACKUP_DIR } else { Join-Path $DataDir "backups" }
$NextDir = if ($env:PRINTORA_NEXT_DIR) { $env:PRINTORA_NEXT_DIR } else { "$RootDir.next" }
$Port = if ($env:PRINTORA_PORT) { $env:PRINTORA_PORT } else { "8069" }
$HealthUrl = if ($env:PRINTORA_HEALTH_URL) { $env:PRINTORA_HEALTH_URL } else { "http://127.0.0.1:$Port/health" }
$VersionUrl = if ($env:PRINTORA_VERSION_URL) { $env:PRINTORA_VERSION_URL } else { "http://127.0.0.1:$Port/openapi.json" }
$UpdateRemoteUrl = if ($env:PRINTORA_UPDATE_REMOTE_URL) { $env:PRINTORA_UPDATE_REMOTE_URL } else { "" }
$LogDir = Join-Path $DataDir "logs"
$UpdateRunId = if ($env:PRINTORA_UPDATE_RUN_ID) { $env:PRINTORA_UPDATE_RUN_ID } else { "" }

function ConvertTo-CompactJson($Value) {
    $Value | ConvertTo-Json -Depth 8 -Compress
}

function Fail-Json([string]$Message) {
    ConvertTo-CompactJson @{ status = "failed"; error = $Message }
    exit 1
}

function Require-Command([string]$Name) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        Fail-Json "comando obrigatório não encontrado: $Name"
    }
}

function Test-SafePath([string]$PathValue, [string]$Label) {
    if ([string]::IsNullOrWhiteSpace($PathValue)) { Fail-Json "$Label vazio" }
    $full = [System.IO.Path]::GetFullPath($PathValue)
    $root = [System.IO.Path]::GetPathRoot($full)
    if ($full.TrimEnd('\') -eq $root.TrimEnd('\')) { Fail-Json "$Label não pode ser raiz: $full" }
}

function Test-Tag {
    if ([string]::IsNullOrWhiteSpace($TargetTag)) { Fail-Json "--Tag é obrigatório" }
    if ($TargetTag -notmatch '^v[0-9]+\.[0-9]+\.[0-9]+([.-][A-Za-z0-9]+)*$') {
        Fail-Json "tag inválida: $TargetTag"
    }
}

function Get-RemoteUrl {
    if ($UpdateRemoteUrl) { return Convert-RemoteUrl $UpdateRemoteUrl }
    $remote = & git -C $RootDir remote get-url origin 2>$null
    if ($LASTEXITCODE -ne 0) { return "" }
    return ($remote | Select-Object -First 1)
}

function Convert-RemoteUrl([string]$RemoteUrl) {
    if ($RemoteUrl -match '^https://github[.]com/[^/]+/[^/]+/releases/tag/') {
        return (($RemoteUrl -replace '/releases/tag/.*$', '') + '.git')
    }
    return $RemoteUrl
}

function Test-RemoteTag([string]$RemoteUrl) {
    if ([string]::IsNullOrWhiteSpace($RemoteUrl)) { Fail-Json "remote origin não configurado" }
    & git ls-remote --exit-code --tags $RemoteUrl "refs/tags/$TargetTag" *> $null
    return $LASTEXITCODE -eq 0
}

function Validate-CommonPlanInputs {
    Require-Command "git"
    Require-Command "python"
    Require-Command "npm"
    Test-SafePath $RootDir "RootDir"
    if (-not (Test-Path $RootDir -PathType Container)) { Fail-Json "diretório do projeto não existe: $RootDir" }
    if ((-not (Test-Path $DbPath -PathType Leaf)) -and (-not (Test-Path $DataDir -PathType Container))) {
        Fail-Json "banco SQLite ou data dir não existe: $DbPath"
    }
    Test-Tag
    $remote = Get-RemoteUrl
    if (-not (Test-RemoteTag $remote)) { Fail-Json "tag alvo não encontrada no repositório remoto: $TargetTag" }
}

function Get-Steps {
    @(
        @{ key = "validate_environment"; title = "Validar PowerShell, Git, Python, npm, projeto, data dir e tag remota" },
        @{ key = "backup_database"; title = "Criar backup obrigatório do printora.db" },
        @{ key = "backup_project"; title = "Preservar pasta atual como Printora.previous-update-<timestamp>" },
        @{ key = "checkout_release"; title = "Clonar release alvo em Printora.next" },
        @{ key = "preserve_venv"; title = "Preservar backend\.venv quando possível" },
        @{ key = "install_backend"; title = "Instalar backend editable sem dependências" },
        @{ key = "apply_schema"; title = "Inicializar backend para aplicar SQL idempotente" },
        @{ key = "build_frontend"; title = "Instalar dependências frontend quando necessário e buildar" },
        @{ key = "restart_app"; title = "Reiniciar pelo runner Windows com ExecutionPolicy Bypass no processo" },
        @{ key = "validate_health"; title = "Validar /health" }
    )
}

function Print-PlanJson {
    ConvertTo-CompactJson @{
        status = "planned"
        mode = "plan"
        target_tag = $TargetTag
        environment = "windows"
        root_dir = $RootDir
        data_dir = $DataDir
        database_path = $DbPath
        remote_url = Get-RemoteUrl
        execution_policy_scope = "process"
        will_modify_files = $false
        steps = Get-Steps
    }
}

function Get-TimestampUtc {
    (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
}

function Get-BackendPython {
    $nextPython = Join-Path $NextDir "backend\.venv\Scripts\python.exe"
    $rootPython = Join-Path $RootDir "backend\.venv\Scripts\python.exe"
    if (Test-Path $nextPython) { return $nextPython }
    if (Test-Path $rootPython) { return $rootPython }
    return "python"
}

function Backup-Database([string]$Timestamp) {
    New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null
    $backupPath = Join-Path $BackupDir "printora.db.before-update-$Timestamp"
    if (Test-Path $DbPath -PathType Leaf) {
        Copy-Item $DbPath $backupPath -Force
    } else {
        $backupPath = "$backupPath.empty-db-placeholder"
        New-Item -ItemType File -Force -Path $backupPath | Out-Null
    }
    return $backupPath
}

function Clone-TargetRelease([string]$RemoteUrl) {
    if (Test-Path $NextDir) { Fail-Json "diretório de próxima versão já existe: $NextDir" }
    & git clone --depth 1 --branch $TargetTag $RemoteUrl $NextDir
}

function Preserve-Venv {
    $rootVenv = Join-Path $RootDir "backend\.venv"
    $nextVenv = Join-Path $NextDir "backend\.venv"
    if ((Test-Path $rootVenv -PathType Container) -and (-not (Test-Path $nextVenv))) {
        Copy-Item $rootVenv $nextVenv -Recurse
    }
}

function Install-Backend {
    Push-Location $NextDir
    try {
        & (Get-BackendPython) -m pip install -e backend --no-deps
    } finally {
        Pop-Location
    }
}

function Apply-Schema {
    Push-Location $NextDir
    try {
        $env:PRINTORA_DATA_DIR = $DataDir
        @"
from app.config import get_settings
from app.database import initialize_database

settings = get_settings()
initialize_database(settings.database_path)
"@ | & (Get-BackendPython) -
    } finally {
        Pop-Location
    }
}

function Build-FrontendIfNeeded {
    $distIndex = Join-Path $NextDir "frontend\dist\index.html"
    if (Test-Path $distIndex -PathType Leaf) { return }
    $frontendDir = Join-Path $NextDir "frontend"
    npm --prefix $frontendDir install
    npm --prefix $frontendDir run build
}

function Get-PreviousPath([string]$Timestamp) {
    $parent = Split-Path -Parent $RootDir
    $name = Split-Path -Leaf $RootDir
    Join-Path $parent "$name.previous-update-$Timestamp"
}

function Move-Preserving([string]$Source, [string]$Target) {
    Test-SafePath $Source "Source"
    Test-SafePath $Target "Target"
    if (-not (Test-Path $Source)) { Fail-Json "origem não existe: $Source" }
    if (Test-Path $Target) { Fail-Json "destino já existe: $Target" }
    Move-Item $Source $Target
}

function Replace-Project([string]$PreviousProjectPath) {
    Move-Preserving $RootDir $PreviousProjectPath
    Move-Preserving $NextDir $RootDir
}

function Restart-App {
    $runner = Join-Path $RootDir "scripts\run_app_windows.ps1"
    if (-not (Test-Path $runner -PathType Leaf)) { Fail-Json "runner Windows não encontrado: $runner" }
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $runner --stop *> $null
    $env:PRINTORA_DATA_DIR = $DataDir
    $env:PRINTORA_PORT = $Port
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $runner --no-open
}

function Validate-Health {
    for ($i = 0; $i -lt 30; $i++) {
        try {
            $response = Invoke-WebRequest -Uri $HealthUrl -UseBasicParsing -TimeoutSec 2
            if ($response.StatusCode -eq 200 -and (Test-RunningVersion)) { return }
        } catch {
            Start-Sleep -Seconds 1
        }
    }
    Fail-Json "Printora não respondeu com a versão $TargetTag em $HealthUrl"
}

function Test-RunningVersion {
    try {
        $payload = Invoke-RestMethod -Uri $VersionUrl -TimeoutSec 2
        $actual = [string]$payload.info.version
        $expected = $TargetTag.TrimStart("v")
        return $actual.TrimStart("v") -eq $expected
    } catch {
        return $false
    }
}

function Mark-RunSucceeded([string]$RunIdValue, [string]$DbBackup, [string]$PreviousProjectPath) {
    if ([string]::IsNullOrWhiteSpace($RunIdValue)) { return }
    if (-not (Test-Path $DbPath -PathType Leaf)) { return }
    $env:PRINTORA_MARK_RUN_ID = $RunIdValue
    $env:PRINTORA_MARK_DB_PATH = $DbPath
    $env:PRINTORA_MARK_BACKUP_DB_PATH = $DbBackup
    $env:PRINTORA_MARK_PREVIOUS_PATH = $PreviousProjectPath
    $env:PRINTORA_MARK_CURRENT_PATH = $RootDir
    @"
import os
import sqlite3

db_path = os.environ["PRINTORA_MARK_DB_PATH"]
run_id = int(os.environ["PRINTORA_MARK_RUN_ID"])
backup_db_path = os.environ["PRINTORA_MARK_BACKUP_DB_PATH"]
previous_path = os.environ["PRINTORA_MARK_PREVIOUS_PATH"]
current_path = os.environ["PRINTORA_MARK_CURRENT_PATH"]

with sqlite3.connect(db_path) as connection:
    connection.execute("""
        UPDATE app_update_runs
        SET status = 'succeeded',
            finished_at = CURRENT_TIMESTAMP,
            backup_db_path = ?,
            backup_project_path = ?,
            previous_project_path = ?,
            current_project_path = ?,
            error_message = NULL
        WHERE id = ?
    """, (backup_db_path, previous_path, previous_path, current_path, run_id))
    connection.execute("""
        UPDATE app_update_steps
        SET status = 'succeeded',
            started_at = COALESCE(started_at, CURRENT_TIMESTAMP),
            finished_at = CURRENT_TIMESTAMP
        WHERE run_id = ?
    """, (run_id,))
"@ | python -
}

function Apply-Update {
    Validate-CommonPlanInputs
    $remote = Get-RemoteUrl
    $timestamp = Get-TimestampUtc
    $previousProjectPath = Get-PreviousPath $timestamp
    $dbBackup = Backup-Database $timestamp
    Clone-TargetRelease $remote
    Preserve-Venv
    Install-Backend
    Apply-Schema
    Build-FrontendIfNeeded
    Replace-Project $previousProjectPath
    Restart-App
    Validate-Health
    Mark-RunSucceeded $UpdateRunId $dbBackup $previousProjectPath
    ConvertTo-CompactJson @{
        status = "succeeded"
        mode = "apply"
        target_tag = $TargetTag
        backup_db_path = $dbBackup
        previous_project_path = $previousProjectPath
        current_project_path = $RootDir
        health_url = $HealthUrl
    }
}

function Rollback-Update {
    if ([string]::IsNullOrWhiteSpace($RunId) -and [string]::IsNullOrWhiteSpace($PreviousPath)) {
        Fail-Json "--Rollback exige --RunId ou --PreviousPath"
    }
    if ([string]::IsNullOrWhiteSpace($PreviousPath)) {
        Fail-Json "--RunId ainda exige --PreviousPath neste script standalone"
    }
    Test-SafePath $RootDir "RootDir"
    Test-SafePath $PreviousPath "PreviousPath"
    if (-not (Test-Path $PreviousPath -PathType Container)) { Fail-Json "previous-path não existe: $PreviousPath" }
    $timestamp = Get-TimestampUtc
    $currentBackup = Join-Path (Split-Path -Parent $RootDir) "$((Split-Path -Leaf $RootDir)).failed-update-$timestamp"
    if (Test-Path $RootDir) {
        Move-Preserving $RootDir $currentBackup
    }
    Move-Preserving $PreviousPath $RootDir
    if (-not [string]::IsNullOrWhiteSpace($DbBackupPath)) {
        if (-not (Test-Path $DbBackupPath -PathType Leaf)) { Fail-Json "backup de banco não existe: $DbBackupPath" }
        New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null
        if (Test-Path $DbPath -PathType Leaf) {
            Copy-Item $DbPath (Join-Path $BackupDir "printora.db.before-rollback-$timestamp") -Force
        }
        Copy-Item $DbBackupPath $DbPath -Force
    }
    Restart-App
    Validate-Health
    Mark-RunSucceeded $UpdateRunId $DbBackupPath $PreviousPath
    ConvertTo-CompactJson @{
        status = "rolled_back"
        mode = "rollback"
        run_id = $RunId
        restored_project_path = $RootDir
        preserved_failed_project_path = $currentBackup
        restored_db_backup_path = $DbBackupPath
        health_url = $HealthUrl
    }
}

try {
    if ([string]::IsNullOrWhiteSpace($Mode)) { Fail-Json "modo obrigatório: --Plan, --Apply ou --Rollback" }
    switch ($Mode) {
        "plan" {
            Validate-CommonPlanInputs
            Print-PlanJson
        }
        "apply" {
            Apply-Update
        }
        "rollback" {
            Rollback-Update
        }
        default {
            Fail-Json "modo inválido"
        }
    }
} catch {
    if ($Mode -eq "apply" -and -not [string]::IsNullOrWhiteSpace($UpdateRunId) -and (Test-Path $DbPath -PathType Leaf)) {
        $env:PRINTORA_MARK_RUN_ID = $UpdateRunId
        $env:PRINTORA_MARK_DB_PATH = $DbPath
        $env:PRINTORA_MARK_ERROR_MESSAGE = "update_printora_windows.ps1 falhou: $($_.Exception.Message)"
        @"
import os
import sqlite3

db_path = os.environ["PRINTORA_MARK_DB_PATH"]
run_id = int(os.environ["PRINTORA_MARK_RUN_ID"])
message = os.environ["PRINTORA_MARK_ERROR_MESSAGE"]

with sqlite3.connect(db_path) as connection:
    connection.execute("UPDATE app_update_runs SET status = 'failed', finished_at = CURRENT_TIMESTAMP, error_message = ? WHERE id = ? AND status = 'running'", (message, run_id))
    connection.execute("UPDATE app_update_steps SET status = 'failed', started_at = COALESCE(started_at, CURRENT_TIMESTAMP), finished_at = CURRENT_TIMESTAMP, log_excerpt = COALESCE(log_excerpt, ?) WHERE run_id = ? AND status IN ('pending', 'running')", (message[:4000], run_id))
"@ | python - 2>$null
    }
    Fail-Json $_.Exception.Message
}
