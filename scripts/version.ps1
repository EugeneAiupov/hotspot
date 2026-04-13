Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"

$projectRoot = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (Test-Path $venvPython) {
    & $venvPython (Join-Path $PSScriptRoot "version.py") @args
    exit $LASTEXITCODE
}

& py -3 (Join-Path $PSScriptRoot "version.py") @args
exit $LASTEXITCODE
