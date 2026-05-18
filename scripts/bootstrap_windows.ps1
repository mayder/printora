$ErrorActionPreference = "Stop"

$RootDir = Resolve-Path (Join-Path $PSScriptRoot "..")
$Apply = $args -contains "--apply"
$DataDir = if ($env:MAYDER_PRINT_LAB_DATA_DIR) { $env:MAYDER_PRINT_LAB_DATA_DIR } else { Join-Path $env:LOCALAPPDATA "MayderPrintLab" }

function Invoke-OrPrint {
    param([string]$Command)
    if ($Apply) {
        Invoke-Expression $Command
    } else {
        Write-Host "DRY-RUN: $Command"
    }
}

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python não encontrado."
}
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw "npm não encontrado."
}

Write-Host "Sistema detectado: windows"
Write-Host "Data dir: $DataDir"
if (-not $Apply) {
    Write-Host "Modo dry-run. Reexecute com --apply para preparar o ambiente local."
}

Invoke-OrPrint "New-Item -ItemType Directory -Force -Path '$DataDir'"
Invoke-OrPrint "python -m venv '$RootDir\backend\.venv'"
Invoke-OrPrint "& '$RootDir\backend\.venv\Scripts\pip.exe' install -e '$RootDir\backend[dev]'"
Invoke-OrPrint "npm --prefix '$RootDir\frontend' install"
Invoke-OrPrint "npm --prefix '$RootDir\frontend' run build"

Write-Host "Ambiente local preparado."
Write-Host "Backend: backend\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8085"
Write-Host "Frontend: npm --prefix frontend run dev"
