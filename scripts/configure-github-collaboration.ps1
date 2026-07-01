param(
    [Parameter(Mandatory = $true)]
    [string]$GitUserName,

    [Parameter(Mandatory = $true)]
    [string]$GitUserEmail,

    [Parameter(Mandatory = $true)]
    [string]$RepositoryUrl,

    [switch]$UseSsh,
    [switch]$SkipRemoteCheck
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Require-Command {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "$Name is required but was not found in PATH."
    }
}

Require-Command git

$repoRoot = git rev-parse --show-toplevel
Set-Location $repoRoot

if ($RepositoryUrl -notmatch '^(https://github\.com/[^/]+/[^/]+(\.git)?|git@github\.com:[^/]+/[^/]+\.git)$') {
    throw "RepositoryUrl must be a GitHub HTTPS or SSH URL, for example https://github.com/<owner>/<repo>.git"
}

if ($UseSsh -and $RepositoryUrl -notmatch '^git@github\.com:') {
    throw "UseSsh was provided, but RepositoryUrl is not an SSH URL."
}

Write-Step "Setting repository-local Git identity"
git config --local user.name $GitUserName
git config --local user.email $GitUserEmail
git config --local init.defaultBranch main
git config --local core.hooksPath .githooks
git config --local pull.rebase false
git config --local fetch.prune true

Write-Step "Replacing stale origin remote"
$existingOrigin = git remote
if ($existingOrigin -contains "origin") {
    git remote set-url origin $RepositoryUrl
}
else {
    git remote add origin $RepositoryUrl
}

Write-Step "Installing Git LFS filters"
if (Get-Command git-lfs -ErrorAction SilentlyContinue) {
    git lfs install --local
}
else {
    Write-Warning "git-lfs was not found. Install Git LFS before pushing binary assets."
}

Write-Step "Ensuring main and develop branches exist locally"
$currentBranch = git branch --show-current
if ($currentBranch -eq "master") {
    git branch -m master main
}
elseif (-not (git show-ref --verify --quiet refs/heads/main)) {
    git branch main
}

if (-not (git show-ref --verify --quiet refs/heads/develop)) {
    git branch develop main
}

git branch --set-upstream-to=origin/main main 2>$null | Out-Null
git branch --set-upstream-to=origin/develop develop 2>$null | Out-Null

if (-not $SkipRemoteCheck) {
    Write-Step "Checking GitHub remote access"
    git ls-remote --heads origin | Out-Host
}
else {
    Write-Warning "Skipped remote access check."
}

Write-Step "Current Git collaboration configuration"
git config --local --get-regexp "^(user\.name|user\.email|remote\.origin\.url|core\.hooksPath|init\.defaultBranch|pull\.rebase|fetch\.prune)$"
git branch --list

Write-Host ""
Write-Host "Done. If this is a new GitHub repository, push with:" -ForegroundColor Green
Write-Host "  git push -u origin main"
Write-Host "  git push -u origin develop"
Write-Host ""
Write-Host "Current EduMind default:" -ForegroundColor Green
Write-Host "  GitHub user: XXXXXQ-0206"
Write-Host "  Repository:  https://github.com/XXXXXQ-0206/EduMind.git"
