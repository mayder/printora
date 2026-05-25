param(
    [switch]$Yes
)

$ErrorActionPreference = "Stop"

$RootDir = Resolve-Path (Join-Path $PSScriptRoot "..")
$Port = if ($env:PRINTORA_PORT) { $env:PRINTORA_PORT } else { "8069" }

function Use-Color {
    return $Host.UI.RawUI -and -not [Console]::IsOutputRedirected
}

function Write-Banner {
    Write-Host " ____       _       _" -ForegroundColor Cyan
    Write-Host "|  _ \ _ __(_)_ __ | |_ ___  _ __ __ _" -ForegroundColor Cyan
    Write-Host "| |_) | '__| | '_ \| __/ _ \| '__/ _`` |" -ForegroundColor Cyan
    Write-Host "|  __/| |  | | | | | || (_) | | | (_| |" -ForegroundColor Cyan
    Write-Host "|_|   |_|  |_|_| |_|\__\___/|_|  \__,_|" -ForegroundColor Cyan
}

function Write-SuccessIcon {
    Write-Host "        ______" -ForegroundColor Green
    Write-Host "     .-'      '-." -ForegroundColor Green
    Write-Host '    /  PRINTORA  \' -ForegroundColor Green
    Write-Host "   |     OK       |" -ForegroundColor Green
    Write-Host '    \            /' -ForegroundColor Green
    Write-Host "     '-.______.-'" -ForegroundColor Green
}

function Confirm-Step {
    param([string]$Message)
    if ($Yes -or $env:PRINTORA_ASSUME_YES -eq "1") {
        return $true
    }
    $answer = Read-Host "$Message [s/N]"
    return $answer -match "^(s|sim|y|yes)$"
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

function Find-Python {
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
            return "$($candidate.Command) $($candidate.Arguments -join ' ')".Trim()
        }
    }
    return $null
}

function Install-WingetPackage {
    param([string]$PackageId)
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        throw "winget não encontrado. Instale $PackageId manualmente."
    }
    winget install --id $PackageId -e
}

Write-Banner
Write-Host "Instalador Windows do Printora" -ForegroundColor Cyan

$missing = New-Object System.Collections.Generic.List[string]
if (-not (Find-Python)) { $missing.Add("Python.Python.3.13") }
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { $missing.Add("Git.Git") }
if (-not (Get-Command node -ErrorAction SilentlyContinue) -or -not (Get-Command npm -ErrorAction SilentlyContinue)) { $missing.Add("OpenJS.NodeJS.LTS") }

if ($missing.Count -gt 0) {
    Write-Host "Dependências ausentes: $($missing -join ', ')" -ForegroundColor Yellow
    if (Confirm-Step "Posso instalar essas dependências com winget?") {
        foreach ($package in $missing) {
            Install-WingetPackage $package
        }
        Write-Host "Feche e reabra o PowerShell se algum comando continuar indisponível." -ForegroundColor Yellow
    } else {
        throw "Instalação interrompida. Dependências obrigatórias ausentes."
    }
}

$python = Find-Python
if (-not $python) {
    throw "Python 3.11+ não encontrado."
}
Write-Host "OK: Python compatível: $python" -ForegroundColor Green
if (Get-Command git -ErrorAction SilentlyContinue) { Write-Host "OK: $(git --version)" -ForegroundColor Green }
if (Get-Command node -ErrorAction SilentlyContinue) { Write-Host "OK: Node $(node --version)" -ForegroundColor Green }
if (Get-Command npm -ErrorAction SilentlyContinue) { Write-Host "OK: npm $(npm --version)" -ForegroundColor Green }

Push-Location $RootDir
try {
    $env:PRINTORA_PORT = $Port
    $env:PRINTORA_HOST = "0.0.0.0"
    if (-not (Confirm-Step "Posso preparar o ambiente e configurar o Printora para iniciar com o Windows?")) {
        throw "Instalação interrompida pelo usuário."
    }
    & "$PSScriptRoot\install_printora_windows.ps1" --apply --yes
    Write-SuccessIcon
    Write-Host "OK: Printora instalado." -ForegroundColor Green
    Write-Host "Abra: http://127.0.0.1:$Port"
} catch {
    Write-Host "ATENÇÃO: instalação falhou. Consulte os logs em %LOCALAPPDATA%\Printora\logs." -ForegroundColor Yellow
    throw
} finally {
    Pop-Location
}
