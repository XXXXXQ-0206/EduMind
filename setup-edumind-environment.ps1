param(
    [switch]$CheckOnly,
    [switch]$SkipDockerInstall,
    [switch]$SkipGitInstall,
    [switch]$SkipImageBuild,
    [int]$DockerTimeoutSeconds = 240
)

$ErrorActionPreference = "Stop"
$script:DockerExe = $null

function Write-Section {
    param([string]$Text)
    Write-Host ""
    Write-Host "============================================================"
    Write-Host $Text
    Write-Host "============================================================"
}

function Require-Path {
    param(
        [string]$Path,
        [string]$Message
    )
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "$Message`: $Path"
    }
}

function Test-Command {
    param([string]$Name)
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Find-DockerCli {
    $command = Get-Command docker -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }

    $candidates = @()
    if ($env:ProgramFiles) {
        $candidates += (Join-Path $env:ProgramFiles "Docker\Docker\resources\bin\docker.exe")
    }
    if (${env:ProgramFiles(x86)}) {
        $candidates += (Join-Path ${env:ProgramFiles(x86)} "Docker\Docker\resources\bin\docker.exe")
    }

    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path -LiteralPath $candidate)) {
            $dockerCliDir = Split-Path -Parent $candidate
            if ($env:Path -notlike "*$dockerCliDir*") {
                $env:Path = "$dockerCliDir;$env:Path"
            }
            return $candidate
        }
    }

    return $null
}

function Find-DockerDesktop {
    $candidates = @()
    if ($env:ProgramFiles) {
        $candidates += (Join-Path $env:ProgramFiles "Docker\Docker\Docker Desktop.exe")
    }
    if (${env:ProgramFiles(x86)}) {
        $candidates += (Join-Path ${env:ProgramFiles(x86)} "Docker\Docker\Docker Desktop.exe")
    }
    if ($env:LOCALAPPDATA) {
        $candidates += (Join-Path $env:LOCALAPPDATA "Docker\Docker Desktop.exe")
    }

    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path -LiteralPath $candidate)) {
            return $candidate
        }
    }

    return $null
}

function Install-WingetPackage {
    param(
        [string]$Id,
        [string]$Name
    )

    if (-not (Test-Command "winget")) {
        throw "winget is required to install $Name automatically. Install $Name manually, then rerun this script."
    }

    Write-Host "[INSTALL] $Name"
    & winget install --id $Id -e --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) {
        throw "winget failed to install $Name with exit code $LASTEXITCODE"
    }
}

function Ensure-DockerInstalled {
    if (Find-DockerCli) {
        $script:DockerExe = Find-DockerCli
        Write-Host "[OK] Docker CLI: $script:DockerExe"
        return
    }

    if ($SkipDockerInstall -or $CheckOnly) {
        throw "Docker CLI was not found. Install Docker Desktop, then rerun this script."
    }

    Install-WingetPackage -Id "Docker.DockerDesktop" -Name "Docker Desktop"

    $script:DockerExe = Find-DockerCli
    if (-not $script:DockerExe) {
        throw "Docker Desktop was installed, but docker.exe is not visible yet. Restart PowerShell or Windows, then rerun this script."
    }
}

function Ensure-GitInstalled {
    if (Test-Command "git") {
        Write-Host "[OK] Git is installed."
        return
    }

    if ($SkipGitInstall -or $CheckOnly) {
        Write-Host "[WARN] Git is not installed. It is only needed for cloning/updating the repository."
        return
    }

    Install-WingetPackage -Id "Git.Git" -Name "Git"
}

function Test-DockerDaemon {
    $previousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $null = & $script:DockerExe info --format "{{.ServerVersion}}" 2>$null
        return $LASTEXITCODE -eq 0
    } finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }
}

function Start-DockerDaemon {
    param([int]$TimeoutSeconds)

    if (Test-DockerDaemon) {
        Write-Host "[OK] Docker daemon is running."
        return
    }

    $dockerDesktop = Find-DockerDesktop
    if (-not $dockerDesktop) {
        throw "Docker Desktop was not found. Install/start Docker Desktop, then rerun this script."
    }

    Write-Host "[START] Docker Desktop"
    Start-Process -FilePath $dockerDesktop -WindowStyle Hidden | Out-Null

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        Start-Sleep -Seconds 3
        if (Test-DockerDaemon) {
            Write-Host "[OK] Docker daemon is ready."
            return
        }
        Write-Host "[WAIT] Docker daemon is starting..."
    }

    throw "Docker daemon did not become ready within $TimeoutSeconds seconds. Docker Desktop may need a reboot or WSL2 setup."
}

function Invoke-Compose {
    param([string[]]$Arguments)

    $dockerArgs = @("compose") + $Arguments
    & $script:DockerExe @dockerArgs
    if ($LASTEXITCODE -ne 0) {
        throw "docker compose $($Arguments -join ' ') failed with exit code $LASTEXITCODE"
    }
}

function Ensure-EnvFile {
    param(
        [string]$EnvPath,
        [string]$ExamplePath
    )

    if (Test-Path -LiteralPath $EnvPath) {
        Write-Host "[OK] env file: $EnvPath"
        return
    }

    if ($CheckOnly) {
        throw "Missing env file: $EnvPath"
    }

    if (-not (Test-Path -LiteralPath $ExamplePath)) {
        throw "Missing env file and example file: $EnvPath"
    }

    Copy-Item -LiteralPath $ExamplePath -Destination $EnvPath
    Write-Host "[SETUP] Created .env from .env.example."
    Write-Host "[WARN] Review API keys in .env before using AI features."
}

function Assert-ComposeServices {
    param([string[]]$ExpectedServices)

    $services = @(& $script:DockerExe compose config --services)
    if ($LASTEXITCODE -ne 0) {
        throw "docker compose config --services failed with exit code $LASTEXITCODE"
    }

    $missing = @($ExpectedServices | Where-Object { $_ -notin $services })
    if ($missing.Count -gt 0) {
        throw "Compose file is missing services: $($missing -join ', ')"
    }

    Write-Host "[OK] compose topology contains required services."
}

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$AppDir = $Root
$BiliDir = Join-Path $Root "services\bilibili-mcp"
$ComposeFile = Join-Path $Root "docker-compose.yml"
$EnvFile = Join-Path $AppDir ".env"
$EnvExample = Join-Path $AppDir ".env.example"

$RequiredServices = @(
    "postgres",
    "redis",
    "minio",
    "minio-init",
    "identity",
    "learning-content",
    "asset-library",
    "ai-core",
    "bilibili-bridge",
    "media-generation",
    "teaching-content",
    "generation-worker",
    "api-gateway",
    "frontend"
)

Write-Section "EduMind new-machine environment setup"
Write-Host "Workspace: $Root"
Write-Host "Check only: $CheckOnly"
Write-Host "Build images: $(-not $SkipImageBuild)"

Require-Path $AppDir "Missing app directory"
Require-Path $BiliDir "Missing Bilibili MCP directory"
Require-Path $ComposeFile "Missing docker-compose.yml"
Require-Path (Join-Path $Root "deploy\docker\Dockerfile.backend") "Missing backend Dockerfile"
Require-Path (Join-Path $Root "deploy\docker\Dockerfile.frontend") "Missing frontend Dockerfile"
Require-Path (Join-Path $AppDir "backend\api\routes\ai_core.py") "Missing AI Core route"
Require-Path (Join-Path $AppDir "backend\core\celery_app.py") "Missing Celery app"
Require-Path (Join-Path $AppDir "backend\core\celery_tasks.py") "Missing Celery tasks"
Require-Path (Join-Path $AppDir "backend\api\routes\tasks.py") "Missing task progress route"
Require-Path (Join-Path $AppDir "backend\services\bilibiliBridgeServer.js") "Missing Bilibili bridge server"
Require-Path (Join-Path $BiliDir "package.json") "Missing Bilibili MCP package"

Push-Location $Root
try {
    Ensure-GitInstalled
    Ensure-DockerInstalled

    Write-Host ""
    Write-Host "[CHECK] Docker Compose"
    & $script:DockerExe compose version
    if ($LASTEXITCODE -ne 0) {
        throw "Docker Compose plugin is not available. Install Docker Desktop or docker compose v2."
    }

    if ($CheckOnly) {
        if (Test-DockerDaemon) {
            Write-Host "[OK] Docker daemon is running."
        } else {
            Write-Host "[WARN] Docker daemon is not running. Normal setup will start Docker Desktop."
        }
    } else {
        Start-DockerDaemon -TimeoutSeconds $DockerTimeoutSeconds
    }

    Ensure-EnvFile -EnvPath $EnvFile -ExamplePath $EnvExample

    Write-Host ""
    Write-Host "[CHECK] Compose config"
    Invoke-Compose @("config", "--quiet")
    Assert-ComposeServices -ExpectedServices $RequiredServices

    if ($CheckOnly) {
        Write-Section "Check complete"
        Write-Host "Environment prerequisites can be configured on this machine."
        exit 0
    }

    if (-not $SkipImageBuild) {
        Write-Section "Building Docker images"
        Write-Host "This installs Python, Node, frontend, backend, and Bilibili MCP dependencies inside images."
        Invoke-Compose @("build", "api-gateway")
        Invoke-Compose @("build", "frontend")
    }

    Write-Section "Environment setup complete"
    Write-Host "Next command:"
    Write-Host ".\start-edumind.ps1"
} finally {
    Pop-Location
}
