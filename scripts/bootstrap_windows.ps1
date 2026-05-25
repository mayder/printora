$ErrorActionPreference = "Stop"

$RootDir = Resolve-Path (Join-Path $PSScriptRoot "..")
$Apply = $args -contains "--apply"
$DataDir = if ($env:PRINTORA_DATA_DIR) { $env:PRINTORA_DATA_DIR } else { Join-Path $env:LOCALAPPDATA "Printora" }
$VenvPython = Join-Path $RootDir "backend\.venv\Scripts\python.exe"
$VenvPip = Join-Path $RootDir "backend\.venv\Scripts\pip.exe"

function Invoke-OrPrint {
    param([scriptblock]$Command, [string]$DryRun)
    if ($Apply) {
        & $Command
    } else {
        Write-Host "DRY-RUN: $DryRun"
    }
}

function Test-PythonSupported {
    param(
        [string]$Command,
        [string[]]$Arguments = @()
    )
    try {
        & $Command @Arguments -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" 2>$null
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    }
}

function Get-CompatiblePython {
    $candidates = @(
        @{ Command = "python"; Arguments = @() },
        @{ Command = "python3"; Arguments = @() },
        @{ Command = "py"; Arguments = @("-3.14") },
        @{ Command = "py"; Arguments = @("-3.13") },
        @{ Command = "py"; Arguments = @("-3.12") },
        @{ Command = "py"; Arguments = @("-3.11") }
    )
    foreach ($candidate in $candidates) {
        if ((Get-Command $candidate.Command -ErrorAction SilentlyContinue) -and (Test-PythonSupported $candidate.Command $candidate.Arguments)) {
            return $candidate
        }
    }
    return $null
}

$Python = Get-CompatiblePython
if (-not $Python) {
    throw "Python 3.11+ não encontrado."
}

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw "npm não encontrado."
}

Write-Host "Sistema detectado: windows"
Write-Host "Data dir: $DataDir"
if (-not $Apply) {
    Write-Host "Modo dry-run. Reexecute com --apply para preparar o ambiente local."
}

Invoke-OrPrint { New-Item -ItemType Directory -Force -Path $DataDir | Out-Null } "New-Item -ItemType Directory -Force -Path '$DataDir'"
Invoke-OrPrint { & $Python.Command @($Python.Arguments + @("-m", "venv", "$RootDir\backend\.venv")) } "$($Python.Command) $($Python.Arguments -join ' ') -m venv '$RootDir\backend\.venv'"
Invoke-OrPrint { & $VenvPython -m pip install --upgrade pip setuptools wheel } "& '$VenvPython' -m pip install --upgrade pip setuptools wheel"
Invoke-OrPrint { & $VenvPip install -e "$RootDir\backend[dev]" } "& '$VenvPip' install -e '$RootDir\backend[dev]'"
Invoke-OrPrint { npm --prefix "$RootDir\frontend" install } "npm --prefix '$RootDir\frontend' install"
Invoke-OrPrint { npm --prefix "$RootDir\frontend" run build } "npm --prefix '$RootDir\frontend' run build"

Write-Host "Ambiente local preparado."
Write-Host "Backend: backend\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8069"
Write-Host "Frontend: npm --prefix frontend run dev"
