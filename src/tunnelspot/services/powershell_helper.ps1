param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("status", "configure", "start", "stop")]
    [string]$Action,

    [string]$Ssid,
    [string]$Passphrase,
    [ValidateSet("Auto", "TwoPointFourGigahertz", "FiveGigahertz")]
    [string]$Band = "Auto"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

[Reflection.Assembly]::LoadWithPartialName("System.Runtime.WindowsRuntime") | Out-Null
[Windows.Networking.Connectivity.NetworkInformation, Windows, ContentType = WindowsRuntime] | Out-Null
[Windows.Networking.NetworkOperators.NetworkOperatorTetheringManager, Windows, ContentType = WindowsRuntime] | Out-Null
[Windows.Networking.NetworkOperators.NetworkOperatorTetheringAccessPointConfiguration, Windows, ContentType = WindowsRuntime] | Out-Null
[Windows.Networking.NetworkOperators.NetworkOperatorTetheringOperationResult, Windows, ContentType = WindowsRuntime] | Out-Null
[Windows.Networking.NetworkOperators.TetheringWiFiBand, Windows, ContentType = WindowsRuntime] | Out-Null
[Windows.Networking.NetworkOperators.TetheringOperationStatus, Windows, ContentType = WindowsRuntime] | Out-Null

function Get-AsyncActionMethod {
    return [System.WindowsRuntimeSystemExtensions].GetMethods() |
        Where-Object { $_.ToString() -eq 'System.Threading.Tasks.Task AsTask(Windows.Foundation.IAsyncAction)' } |
        Select-Object -First 1
}

function Get-AsyncOperationMethod {
    return [System.WindowsRuntimeSystemExtensions].GetMethods() |
        Where-Object { $_.ToString() -eq 'System.Threading.Tasks.Task`1[TResult] AsTask[TResult](Windows.Foundation.IAsyncOperation`1[TResult])' } |
        Select-Object -First 1
}

function Invoke-IAsyncAction {
    param([Parameter(Mandatory = $true)][object]$AsyncAction)

    $method = Get-AsyncActionMethod
    $task = $method.Invoke($null, @($AsyncAction))
    $task.GetAwaiter().GetResult() | Out-Null
}

function Invoke-IAsyncOperation {
    param(
        [Parameter(Mandatory = $true)][object]$AsyncOperation,
        [Parameter(Mandatory = $true)][type]$ResultType
    )

    $method = Get-AsyncOperationMethod
    $generic = $method.MakeGenericMethod($ResultType)
    $task = $generic.Invoke($null, @($AsyncOperation))
    return $task.GetAwaiter().GetResult()
}

function Get-HotspotContext {
    $profile = [Windows.Networking.Connectivity.NetworkInformation]::GetInternetConnectionProfile()
    if ($null -eq $profile) {
        throw "No active internet connection detected for sharing."
    }

    return [pscustomobject]@{
        Profile = $profile
        Manager = [Windows.Networking.NetworkOperators.NetworkOperatorTetheringManager]::CreateFromConnectionProfile($profile)
        Capability = [Windows.Networking.NetworkOperators.NetworkOperatorTetheringManager]::GetTetheringCapabilityFromConnectionProfile($profile)
    }
}

function Get-SupportedBands {
    param([Parameter(Mandatory = $true)][object]$Config)

    $bands = [System.Collections.Generic.List[string]]::new()
    $bands.Add("Auto")

    foreach ($candidate in @("TwoPointFourGigahertz", "FiveGigahertz")) {
        try {
            if ($Config.IsBandSupported([Windows.Networking.NetworkOperators.TetheringWiFiBand]::$candidate)) {
                $bands.Add($candidate)
            }
        } catch {
        }
    }

    return $bands.ToArray()
}

function New-Response {
    param(
        [Parameter(Mandatory = $true)][object]$Context,
        [string]$Message,
        [string]$OperationStatus
    )

    $config = $Context.Manager.GetCurrentAccessPointConfiguration()

    return [ordered]@{
        ok = $true
        action = $Action
        message = $Message
        operation_status = $OperationStatus
        profile_name = $Context.Profile.ProfileName
        capability = $Context.Capability.ToString()
        state = $Context.Manager.TetheringOperationalState.ToString()
        ssid = $config.Ssid
        band = $config.Band.ToString()
        supported_bands = @(Get-SupportedBands -Config $config)
        client_count = [int]$Context.Manager.ClientCount
        max_client_count = [int]$Context.Manager.MaxClientCount
    }
}

function Ensure-Capable {
    param([Parameter(Mandatory = $true)][object]$Context)

    if ($Context.Capability.ToString() -ne "Enabled") {
        throw "Mobile Hotspot is not available for the current connection: $($Context.Capability)"
    }
}

function Configure-Hotspot {
    param(
        [Parameter(Mandatory = $true)][object]$Context,
        [Parameter(Mandatory = $true)][string]$RequestedSsid,
        [Parameter(Mandatory = $true)][string]$RequestedPassphrase,
        [Parameter(Mandatory = $true)][string]$RequestedBand
    )

    Ensure-Capable -Context $Context

    $candidateConfig = [Windows.Networking.NetworkOperators.NetworkOperatorTetheringAccessPointConfiguration]::new()
    $candidateConfig.Ssid = $RequestedSsid
    $candidateConfig.Passphrase = $RequestedPassphrase
    $candidateConfig.Band = [Windows.Networking.NetworkOperators.TetheringWiFiBand]::$RequestedBand

    $supportedBands = Get-SupportedBands -Config $Context.Manager.GetCurrentAccessPointConfiguration()
    if ($supportedBands -notcontains $RequestedBand) {
        throw "Wi-Fi adapter does not support band '$RequestedBand'."
    }

    Invoke-IAsyncAction -AsyncAction ($Context.Manager.ConfigureAccessPointAsync($candidateConfig))
}

try {
    $context = Get-HotspotContext

    switch ($Action) {
        "status" {
            $payload = New-Response -Context $context -Message "Status loaded."
        }
        "configure" {
            Configure-Hotspot -Context $context -RequestedSsid $Ssid -RequestedPassphrase $Passphrase -RequestedBand $Band
            $payload = New-Response -Context $context -Message "Hotspot settings applied."
        }
        "start" {
            Ensure-Capable -Context $context
            if ($Ssid -and $Passphrase) {
                Configure-Hotspot -Context $context -RequestedSsid $Ssid -RequestedPassphrase $Passphrase -RequestedBand $Band
            }
            if ($context.Manager.TetheringOperationalState.ToString() -eq "On") {
                $payload = New-Response -Context $context -Message "Hotspot is already on." -OperationStatus "AlreadyOn"
            } else {
                $result = Invoke-IAsyncOperation -AsyncOperation ($context.Manager.StartTetheringAsync()) -ResultType ([Windows.Networking.NetworkOperators.NetworkOperatorTetheringOperationResult])
                if ($result.Status -ne [Windows.Networking.NetworkOperators.TetheringOperationStatus]::Success) {
                    throw "Failed to start hotspot: $($result.Status)"
                }

                $payload = New-Response -Context $context -Message "Hotspot started." -OperationStatus $result.Status.ToString()
            }
        }
        "stop" {
            if ($context.Manager.TetheringOperationalState.ToString() -eq "Off") {
                $payload = New-Response -Context $context -Message "Hotspot is already off." -OperationStatus "AlreadyOff"
            } else {
                $result = Invoke-IAsyncOperation -AsyncOperation ($context.Manager.StopTetheringAsync()) -ResultType ([Windows.Networking.NetworkOperators.NetworkOperatorTetheringOperationResult])
                if ($result.Status -ne [Windows.Networking.NetworkOperators.TetheringOperationStatus]::Success) {
                    throw "Failed to stop hotspot: $($result.Status)"
                }

                $payload = New-Response -Context $context -Message "Hotspot stopped." -OperationStatus $result.Status.ToString()
            }
        }
    }

    $payload | ConvertTo-Json -Compress
    exit 0
} catch {
    $errorPayload = [ordered]@{
        ok = $false
        action = $Action
        error = $_.Exception.Message
    }
    $errorPayload | ConvertTo-Json -Compress
    exit 1
}
