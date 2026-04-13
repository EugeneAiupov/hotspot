Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"

$projectRoot = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    throw "Virtual environment not found. Run .\scripts\setup_venv.ps1 first."
}

$version = (& $venvPython (Join-Path $PSScriptRoot "version.py") show).Trim()
$appName = "TunnelSpot"
$artifactBase = "$appName-v$version-windows-x64"
$releaseDir = Join-Path $projectRoot "release"
$buildDir = Join-Path $projectRoot "build"
$distDir = Join-Path $projectRoot "dist"
$specPath = Join-Path $projectRoot "$appName.spec"
$builtExe = Join-Path $distDir "$appName.exe"
$versionedExe = Join-Path $releaseDir "$artifactBase.exe"
$zipPath = Join-Path $releaseDir "$artifactBase.zip"
$checksumPath = Join-Path $releaseDir "$artifactBase.sha256"

foreach ($path in @($releaseDir, $buildDir, $distDir)) {
    if (Test-Path $path) {
        Remove-Item -LiteralPath $path -Recurse -Force
    }
}

if (Test-Path $specPath) {
    Remove-Item -LiteralPath $specPath -Force
}

New-Item -ItemType Directory -Force -Path $releaseDir | Out-Null

& $venvPython -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name $appName `
    --add-data "src\tunnelspot\services\powershell_helper.ps1;tunnelspot\services" `
    src\tunnelspot\__main__.py

if (-not (Test-Path $builtExe)) {
    throw "Expected executable was not created: $builtExe"
}

Copy-Item -LiteralPath $builtExe -Destination $versionedExe
Compress-Archive -LiteralPath @($versionedExe, (Join-Path $projectRoot "README.md")) -DestinationPath $zipPath -Force

$hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $versionedExe).Hash.ToLowerInvariant()
Set-Content -LiteralPath $checksumPath -Value "$hash *$(Split-Path -Leaf $versionedExe)" -Encoding ascii

Write-Host "Version: $version"
Write-Host "Executable: $versionedExe"
Write-Host "Archive: $zipPath"
Write-Host "Checksum: $checksumPath"
