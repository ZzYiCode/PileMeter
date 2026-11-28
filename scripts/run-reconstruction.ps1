[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Images,
    [int]$MaxImages = 6,
    [ValidateSet("auto", "cuda", "cpu")]
    [string]$Device = "auto"
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$executable = Join-Path $repoRoot ".venv\Scripts\pile-meter.exe"

if (-not (Test-Path -LiteralPath $executable -PathType Leaf)) {
    throw "Python environment not found. Create .venv and install backend[api,reconstruction] first."
}

Push-Location $repoRoot
try {
    & $executable reconstruct --images $Images --max-images $MaxImages --device $Device
}
finally {
    Pop-Location
}
