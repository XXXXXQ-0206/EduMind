param(
    [switch]$CheckOnly,
    [switch]$Build,
    [switch]$SkipBuild,
    [switch]$Logs,
    [switch]$NoDockerWindow,
    [switch]$NoPause,
    [int]$DockerTimeoutSeconds = 180
)

$ErrorActionPreference = "Stop"
$StartScript = Join-Path $PSScriptRoot "start-edumind.ps1"

if (-not (Test-Path -LiteralPath $StartScript)) {
    throw "Missing start script: $StartScript"
}

$arguments = @{
    UseNewFrontend = $true
    DockerTimeoutSeconds = $DockerTimeoutSeconds
}
if ($CheckOnly) { $arguments.CheckOnly = $true }
if ($Build) { $arguments.Build = $true }
if ($SkipBuild) { $arguments.SkipBuild = $true }
if ($Logs) { $arguments.Logs = $true }
if ($NoDockerWindow) { $arguments.NoDockerWindow = $true }
if ($NoPause) { $arguments.NoPause = $true }

& $StartScript @arguments
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
