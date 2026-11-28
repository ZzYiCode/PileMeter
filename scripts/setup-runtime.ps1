[CmdletBinding()]
param(
    [switch]$SkipVggt,
    [string]$VggtSource = "D:\大创\111\tmp\vggt-main\vggt-main"
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$venvDirectory = Join-Path $repoRoot ".venv"
$python = Join-Path $venvDirectory "Scripts\python.exe"

if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    & python -m venv $venvDirectory
}

& $python -m pip install torch==2.13.0 --index-url https://download.pytorch.org/whl/cu130
$backendSpec = "{0}[api,reconstruction,dev]" -f (Join-Path $repoRoot "backend")
& $python -m pip install -e $backendSpec

Push-Location (Join-Path $repoRoot "frontend")
try {
    npm install
}
finally {
    Pop-Location
}

if (-not $SkipVggt) {
    & (Join-Path $PSScriptRoot "setup-vggt.ps1") -VggtSource $VggtSource
}

Write-Host "Runtime ready."
Write-Host "Run: .\.venv\Scripts\pile-meter.exe doctor"
