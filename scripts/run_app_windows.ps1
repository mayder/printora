$ErrorActionPreference = "Stop"

$RootDir = Resolve-Path (Join-Path $PSScriptRoot "..")
$HostName = if ($env:PRINTORA_HOST) { $env:PRINTORA_HOST } else { "127.0.0.1" }
$Port = if ($env:PRINTORA_PORT) { $env:PRINTORA_PORT } else { "8085" }
$Url = "http://${HostName}:${Port}"
$DataDir = if ($env:PRINTORA_DATA_DIR) { $env:PRINTORA_DATA_DIR } else { Join-Path $env:LOCALAPPDATA "Printora" }
$LogDir = Join-Path $DataDir "logs"
$PidFile = Join-Path $DataDir "printora.pid"
$LogFile = Join-Path $LogDir "app.log"
$ErrorLogFile = Join-Path $LogDir "app.err.log"
$NoOpen = $args -contains "--no-open"
$StatusOnly = $args -contains "--status"
$StopOnly = $args -contains "--stop"
$Foreground = $args -contains "--foreground"

function Show-Usage {
    Write-Host "Uso:"
    Write-Host "  scripts\run_app_windows.ps1              # prepara se precisar, inicia e abre o app"
    Write-Host "  scripts\run_app_windows.ps1 --no-open    # inicia sem abrir navegador"
    Write-Host "  scripts\run_app_windows.ps1 --foreground # mantém o servidor no terminal atual"
    Write-Host "  scripts\run_app_windows.ps1 --status     # mostra status local"
    Write-Host "  scripts\run_app_windows.ps1 --stop       # para o processo iniciado por este runner"
}

foreach ($arg in $args) {
    if ($arg -notin @("--no-open", "--foreground", "--status", "--stop", "-h", "--help")) {
        throw "Argumento inválido: $arg"
    }
    if ($arg -in @("-h", "--help")) {
        Show-Usage
        exit 0
    }
}

function Test-HttpOk {
    try {
        $response = Invoke-WebRequest -Uri "$Url/health" -UseBasicParsing -TimeoutSec 2
        return $response.StatusCode -eq 200
    } catch {
        return $false
    }
}

function Get-RunnerProcess {
    if (-not (Test-Path $PidFile)) {
        return $null
    }
    $processId = (Get-Content $PidFile -ErrorAction SilentlyContinue | Select-Object -First 1)
    if (-not $processId) {
        return $null
    }
    return Get-Process -Id ([int]$processId) -ErrorAction SilentlyContinue
}

function Stop-App {
    $process = Get-RunnerProcess
    if ($process) {
        Stop-Process -Id $process.Id
        Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
        Write-Host "Printora parada."
        return
    }
    Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
    Write-Host "Printora não estava rodando por este runner."
}

if ($StopOnly) {
    Stop-App
    exit 0
}

if ($StatusOnly) {
    if (Test-HttpOk) {
        Write-Host "Printora online em $Url"
    } else {
        Write-Host "Printora offline em $Url"
    }
    exit 0
}

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

if (Test-HttpOk) {
    Write-Host "Printora já está online em $Url"
    if (-not $NoOpen) {
        Start-Process $Url
    }
    exit 0
}

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python não encontrado."
}
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw "npm não encontrado."
}

$VenvPython = Join-Path $RootDir "backend\.venv\Scripts\python.exe"
$VenvPip = Join-Path $RootDir "backend\.venv\Scripts\pip.exe"
$DistIndex = Join-Path $RootDir "frontend\dist\index.html"

if (-not (Test-Path $VenvPython)) {
    python -m venv (Join-Path $RootDir "backend\.venv")
    & $VenvPip install -e "$RootDir\backend[dev]"
}

if (-not (Test-Path (Join-Path $RootDir "frontend\node_modules"))) {
    npm --prefix (Join-Path $RootDir "frontend") install
}

if (-not (Test-Path $DistIndex)) {
    npm --prefix (Join-Path $RootDir "frontend") run build
}

$env:PRINTORA_DATA_DIR = $DataDir
if (-not $env:PRINTORA_MOONRAKER_URL) {
    $env:PRINTORA_MOONRAKER_URL = "http://voron.local:7125"
}

if ($Foreground) {
    $PID | Out-File -FilePath $PidFile -Encoding ascii
    Write-Host "Printora iniciando em $Url"
    Write-Host "Log: terminal atual"
    if (-not $NoOpen) {
        Start-Job -ScriptBlock {
            param($TargetUrl)
            Start-Sleep -Seconds 2
            Start-Process $TargetUrl
        } -ArgumentList $Url | Out-Null
    }
    Push-Location (Join-Path $RootDir "backend")
    try {
        & $VenvPython -m uvicorn app.main:app --host $HostName --port $Port
    } finally {
        Pop-Location
    }
    exit 0
}

$arguments = @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-Command",
    "cd '$RootDir\backend'; `$env:PRINTORA_DATA_DIR='$DataDir'; `$env:PRINTORA_MOONRAKER_URL='$env:PRINTORA_MOONRAKER_URL'; & '$VenvPython' -m uvicorn app.main:app --host '$HostName' --port '$Port'"
)

$process = Start-Process -FilePath "powershell.exe" -ArgumentList $arguments -WindowStyle Hidden -RedirectStandardOutput $LogFile -RedirectStandardError $ErrorLogFile -PassThru
$process.Id | Out-File -FilePath $PidFile -Encoding ascii

for ($i = 0; $i -lt 30; $i++) {
    if ((Test-HttpOk) -and (Get-Process -Id $process.Id -ErrorAction SilentlyContinue)) {
        Write-Host "Printora online em $Url"
        Write-Host "Log: $LogFile"
        if (-not $NoOpen) {
            Start-Process $Url
        }
        exit 0
    }
    if (-not (Get-Process -Id $process.Id -ErrorAction SilentlyContinue)) {
        break
    }
    Start-Sleep -Seconds 1
}

Write-Error "Printora não subiu em $Url. Log: $LogFile"
exit 1
