[CmdletBinding()]
param(
    [string]$VggtSource = "D:\大创\111\tmp\vggt-main\vggt-main",
    [string]$Weights,
    [switch]$CopyWeights
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$sourceLink = Join-Path $repoRoot "third_party\vggt"
$modelDirectory = Join-Path $repoRoot "models\vggt"
$modelTarget = Join-Path $modelDirectory "model.safetensors"

if (-not $Weights) {
    $Weights = Join-Path $VggtSource "model.safetensors"
}

if (-not (Test-Path -LiteralPath (Join-Path $VggtSource "vggt") -PathType Container)) {
    throw "VGGT source not found under: $VggtSource"
}
if (-not (Test-Path -LiteralPath $Weights -PathType Leaf)) {
    throw "VGGT weights not found: $Weights"
}

New-Item -ItemType Directory -Path (Split-Path -Parent $sourceLink) -Force | Out-Null
New-Item -ItemType Directory -Path $modelDirectory -Force | Out-Null

if (-not (Test-Path -LiteralPath $sourceLink)) {
    New-Item -ItemType Junction -Path $sourceLink -Target $VggtSource | Out-Null
}

if (-not (Test-Path -LiteralPath $modelTarget)) {
    if ($CopyWeights) {
        Copy-Item -LiteralPath $Weights -Destination $modelTarget
    }
    else {
        try {
            New-Item -ItemType HardLink -Path $modelTarget -Target $Weights | Out-Null
        }
        catch {
            Copy-Item -LiteralPath $Weights -Destination $modelTarget
        }
    }
}

Write-Host "VGGT source: $sourceLink"
Write-Host "VGGT weights: $modelTarget"
Write-Host "Run: .\.venv\Scripts\pile-meter.exe doctor"
