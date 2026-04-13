Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"

$projectRoot = Split-Path -Parent $PSScriptRoot
$venvPath = Join-Path $projectRoot ".venv"
$preferredVersions = @("3.13", "3.12")

$pythonArgs = $null
foreach ($version in $preferredVersions) {
    try {
        & py "-$version" --version *> $null
        $pythonArgs = @("py", "-$version")
        break
    } catch {
    }
}

if ($null -eq $pythonArgs) {
    throw "Python 3.13 or 3.12 was not found. Install one of them and rerun this script."
}

if (-not (Test-Path $venvPath)) {
    & $pythonArgs[0] $pythonArgs[1] -m venv $venvPath
}

$venvPython = Join-Path $venvPath "Scripts\python.exe"
$editableTarget = "$($projectRoot)[dev]"

& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -e $editableTarget

Write-Host ""
Write-Host "Environment is ready."
Write-Host "Run the app with: .\scripts\run.ps1"
