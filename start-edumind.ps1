param(
    [switch]$CheckOnly,
    [switch]$Build,
    [switch]$SkipBuild,
    [switch]$Logs,
    [int]$DockerTimeoutSeconds = 180
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
        throw "Docker Desktop is not available. Run .\setup-edumind-environment.ps1 first."
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

    throw "Docker daemon did not become ready within $TimeoutSeconds seconds."
}

function Invoke-Compose {
    param([string[]]$Arguments)

    $dockerArgs = @("compose") + $Arguments
    & $script:DockerExe @dockerArgs
    if ($LASTEXITCODE -ne 0) {
        throw "docker compose $($Arguments -join ' ') failed with exit code $LASTEXITCODE"
    }
}

function Invoke-ComposePlainBuild {
    param([string[]]$Arguments)

    $dockerArgs = @("compose", "--progress", "plain", "build") + $Arguments
    & $script:DockerExe @dockerArgs
    if ($LASTEXITCODE -ne 0) {
        throw "docker compose --progress plain build $($Arguments -join ' ') failed with exit code $LASTEXITCODE"
    }
}

function Build-ProjectImages {
    Write-Host "[BUILD] Shared backend image"
    Invoke-ComposePlainBuild @("api-gateway")

    Write-Host "[BUILD] Frontend image"
    Invoke-ComposePlainBuild @("frontend")
}

function Read-EnvValue {
    param(
        [string]$Path,
        [string]$Name
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        return $null
    }

    foreach ($line in Get-Content -LiteralPath $Path) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith("#")) {
            continue
        }

        $parts = $trimmed -split "=", 2
        if ($parts.Count -eq 2 -and $parts[0].Trim() -eq $Name) {
            return $parts[1].Trim().Trim('"').Trim("'")
        }
    }

    return $null
}

function Warn-EnvCompatibility {
    $provider = Read-EnvValue -Path $EnvFile -Name "TASK_QUEUE_PROVIDER"
    if ($provider -and $provider.ToLowerInvariant() -ne "celery") {
        Write-Host "[WARN] .env sets TASK_QUEUE_PROVIDER=$provider. The current Docker topology defaults to Celery + Redis."
        Write-Host "[WARN] Use TASK_QUEUE_PROVIDER=celery for the current production-like startup path."
    }
}

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$AppDir = $Root
$EnvFile = Join-Path $AppDir ".env"
$ShouldBuildImages = -not $SkipBuild

if ($Build -and $SkipBuild) {
    throw "Use either -Build or -SkipBuild, not both."
}

Write-Section "EduMind quick start"
Write-Host "Workspace: $Root"
Write-Host "Assumption: setup-edumind-environment.ps1 has already completed."
Write-Host "Check only: $CheckOnly"
Write-Host "Refresh Docker images: $ShouldBuildImages"
if ($Build) {
    Write-Host "[INFO] -Build is kept for compatibility; image refresh is now the default."
}

$script:DockerExe = Find-DockerCli
if (-not $script:DockerExe) {
    throw "Docker CLI was not found. Run .\setup-edumind-environment.ps1 first."
}
if (-not (Test-Path -LiteralPath $EnvFile)) {
    throw "Missing .env. Run .\setup-edumind-environment.ps1 first."
}

Push-Location $Root
try {
    Write-Host ""
    Write-Host "[CHECK] Docker Compose"
    & $script:DockerExe compose version
    if ($LASTEXITCODE -ne 0) {
        throw "Docker Compose plugin is not available. Run .\setup-edumind-environment.ps1 first."
    }

    Warn-EnvCompatibility

    if ($CheckOnly) {
        if (Test-DockerDaemon) {
            Write-Host "[OK] Docker daemon is running."
        } else {
            Write-Host "[WARN] Docker daemon is not running. Normal startup will start Docker Desktop."
        }
    } else {
        Start-DockerDaemon -TimeoutSeconds $DockerTimeoutSeconds
    }

    Write-Host ""
    Write-Host "[CHECK] Compose config"
    Invoke-Compose @("config", "--quiet")

    if ($CheckOnly) {
        Write-Section "Check complete"
        & $script:DockerExe compose config --services
        if ($LASTEXITCODE -ne 0) {
            throw "docker compose config --services failed with exit code $LASTEXITCODE"
        }
        exit 0
    }

    Write-Host ""
    Write-Host "[START] Docker Compose microservices"
    if ($ShouldBuildImages) {
        Build-ProjectImages
    } else {
        Write-Host "[SKIP] Docker image build. Existing local images will be reused."
    }

    $upArgs = @("up", "-d", "--remove-orphans")
    if ($SkipBuild) {
        $upArgs += "--no-build"
    }
    Invoke-Compose $upArgs

    Write-Host ""
    Write-Host "[STATUS]"
    Invoke-Compose @("ps")

    Write-Section "Startup requested"
    Write-Host "Frontend:        http://localhost"
    Write-Host "API Gateway:     http://localhost:5000"
    Write-Host "Gateway health:  http://localhost:5000/health/ready"
    Write-Host "MinIO console:   http://localhost:9001"
    Write-Host "Logs:            docker compose logs -f api-gateway ai-core generation-worker bilibili-bridge"

    if ($Logs) {
        Write-Section "Following logs"
        Invoke-Compose @("logs", "-f", "api-gateway", "ai-core", "generation-worker", "bilibili-bridge")
    }
} finally {
    Pop-Location
}
