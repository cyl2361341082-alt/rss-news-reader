param(
    [switch]$SkipInstall,
    [switch]$SkipFetch,
    [int]$ApiPort = 8000,
    [int]$FrontendPort = 3000
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"
$frontendEnv = Join-Path $frontend ".env.local"

function Require-Command {
    param([string]$Name)

    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command not found: $Name"
    }
}

function Write-Step {
    param([string]$Message)

    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Wait-ForHttpReady {
    param(
        [string]$Url,
        [int]$TimeoutSeconds = 60
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)

    while ((Get-Date) -lt $deadline) {
        try {
            Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 3 | Out-Null
            return $true
        } catch {
            Start-Sleep -Seconds 1
        }
    }

    return $false
}

Require-Command "uv"
Require-Command "npm"

Write-Step "Preparing frontend environment"
Set-Content -Path $frontendEnv -Encoding UTF8 -Value "NEXT_PUBLIC_API_BASE_URL=http://localhost:$ApiPort/api"

if (-not $SkipInstall) {
    Write-Step "Installing backend dependencies with uv"
    Push-Location $backend
    uv sync
    Pop-Location

    Write-Step "Installing frontend dependencies with npm"
    Push-Location $frontend
    npm install
    Pop-Location
}

Write-Step "Initializing backend database"
Push-Location $backend
uv run news init

if (-not $SkipFetch) {
    Write-Step "Running initial ingestion pipeline"
    uv run news run
}
Pop-Location

$backendCommand = "Set-Location '$backend'; uv run news serve-api"
if ($ApiPort -ne 8000) {
    $backendCommand = "$env:RSS_NEWS_READER_API_PORT='$ApiPort'; " + $backendCommand
}

$frontendCommand = "Set-Location '$frontend'; `$env:PORT='$FrontendPort'; npm run dev -- --port $FrontendPort"

Write-Step "Starting backend API on http://localhost:$ApiPort"
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy", "Bypass",
    "-Command", $backendCommand
)

Write-Step "Starting frontend on http://localhost:$FrontendPort"
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy", "Bypass",
    "-Command", $frontendCommand
)

Write-Step "Startup complete"
Write-Host "Frontend: http://localhost:$FrontendPort" -ForegroundColor Green
Write-Host "API: http://localhost:$ApiPort/api" -ForegroundColor Green
Write-Host "Use -SkipInstall to skip dependency installation on subsequent runs." -ForegroundColor DarkGray
Write-Host "Use -SkipFetch to skip the initial news run." -ForegroundColor DarkGray

$frontendUrl = "http://localhost:$FrontendPort"
Write-Step "Waiting for frontend to become available"
if (Wait-ForHttpReady -Url $frontendUrl) {
    Write-Step "Opening browser"
    Start-Process $frontendUrl
} else {
    Write-Host "Frontend did not respond within 60 seconds. Open $frontendUrl manually if needed." -ForegroundColor Yellow
}
