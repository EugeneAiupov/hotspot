# TunnelSpot

`TunnelSpot` is a Windows desktop app built with Python and `PySide6`. It lets you:

- manage a local Wi-Fi hotspot from the desktop
- route connected devices through the PC's current internet connection, including an active VPN tunnel
- generate a strong hotspot password
- store the password securely in Windows Credential Manager

## Why this approach

This project does **not** rely on the old `netsh wlan hostednetwork` flow. On modern Windows systems that feature is often unavailable even though Mobile Hotspot still works. TunnelSpot uses the Windows tethering API through a PowerShell helper.

## Requirements

- Windows 10/11
- Wi-Fi adapter that supports Mobile Hotspot
- Python `3.13` preferred, `3.12` also supported
- PowerShell available in `PATH`

## Setup

```powershell
.\scripts\setup_venv.ps1
```

## Run

```powershell
.\scripts\run.ps1
```

## Versioning

Single source of truth for the app version:

- `src/tunnelspot/__init__.py`

Show the current version:

```powershell
.\scripts\version.ps1 show
```

Bump the patch version:

```powershell
.\scripts\version.ps1 bump patch
```

Set an explicit version:

```powershell
.\scripts\version.ps1 set 0.2.0
```

## Build EXE

```powershell
.\scripts\build_exe.ps1
```

The build output lands in `release/`:

- `TunnelSpot-vX.Y.Z-windows-x64.exe`
- `TunnelSpot-vX.Y.Z-windows-x64.zip`
- `TunnelSpot-vX.Y.Z-windows-x64.sha256`

## GitHub Actions

- Every push to `main` or `master` runs lint, tests, builds the Windows `.exe`, and uploads it as a workflow artifact.
- Pushing a version tag like `v0.1.0` also publishes a GitHub Release with the versioned `.exe`, `.zip`, and checksum file.
- The workflow validates that the git tag matches `src/tunnelspot/__init__.py`.

Typical release flow:

```powershell
.\scripts\version.ps1 bump patch
git add .
git commit -m "Release v$(.\scripts\version.ps1 show)"
git tag "v$(.\scripts\version.ps1 show)"
git push
git push origin "v$(.\scripts\version.ps1 show)"
```

## Test

```powershell
.\scripts\test.ps1
```

## Security notes

- The hotspot password is stored through `keyring`, which uses the Windows credential store on this platform.
- The app config file stores only non-secret settings such as SSID and selected band.
- Password validation is restricted to printable ASCII to stay inside Windows hotspot requirements.

## Current limits

- This project targets Windows only.
- Starting a hotspot can still fail if Wi-Fi is disabled, the adapter is busy, or Windows reports limited connectivity.
- Mobile Hotspot can conflict with other Wi-Fi Direct scenarios.
