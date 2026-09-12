[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateSet('ARM64', 'X64')]
    [string] $ExpectedArchitecture
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$PSNativeCommandUseErrorActionPreference = $false

$report = [ordered]@{
    schemaVersion = 1
    checkedAt = [DateTime]::UtcNow.ToString('o')
    status = 'failed'
    commit = $env:GITHUB_SHA
    runUrl = "$env:GITHUB_SERVER_URL/$env:GITHUB_REPOSITORY/actions/runs/$env:GITHUB_RUN_ID"
    runnerName = $env:RUNNER_NAME
    runnerArchitecture = $env:RUNNER_ARCH
    expectedArchitecture = $ExpectedArchitecture
    hostedImageOS = $env:ImageOS
    hostedImageVersion = $env:ImageVersion
    checks = [System.Collections.Generic.List[string]]::new()
}
$scratch = $null
$reportDirectory = Join-Path $env:GITHUB_WORKSPACE 'artifacts'
New-Item -ItemType Directory -Path $reportDirectory -Force | Out-Null

try {
    if (-not $IsWindows -or $env:RUNNER_OS -ne 'Windows') {
        throw 'This smoke test requires a Windows GitHub Actions job.'
    }
    $cpuArchitectures = @(Get-CimInstance Win32_Processor | Select-Object -ExpandProperty Architecture -Unique)
    if ($cpuArchitectures.Count -ne 1) { throw 'Processor architecture is ambiguous.' }
    $nativeArchitecture = switch ($cpuArchitectures[0]) {
        9 { 'X64' }
        12 { 'ARM64' }
        default { throw "Unsupported processor architecture: $($cpuArchitectures[0])" }
    }
    $report.nativeArchitecture = $nativeArchitecture
    $report.runtimeOSArchitecture = [Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString()
    $report.processArchitecture = [Runtime.InteropServices.RuntimeInformation]::ProcessArchitecture.ToString()
    if ($nativeArchitecture -ne $ExpectedArchitecture -or $env:RUNNER_ARCH -ne $ExpectedArchitecture) {
        throw 'Guest, runner, and requested architectures do not agree.'
    }
    if ($report.processArchitecture -ine $ExpectedArchitecture) {
        throw 'PowerShell is running under architecture emulation.'
    }
    $report.checks.Add('native-windows-and-runner-architecture')

    $os = Get-CimInstance Win32_OperatingSystem
    $windows = Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion'
    $report.windowsCaption = $os.Caption
    $report.windowsVersion = $os.Version
    $report.windowsBuild = "$($windows.CurrentBuildNumber).$($windows.UBR)"
    $report.windowsDisplayVersion = $windows.DisplayVersion
    $report.windowsEdition = $windows.EditionID
    $report.powerShellVersion = $PSVersionTable.PSVersion.ToString()
    $report.dotnetRuntime = [Runtime.InteropServices.RuntimeInformation]::FrameworkDescription
    $principal = [Security.Principal.WindowsPrincipal]::new([Security.Principal.WindowsIdentity]::GetCurrent())
    $report.isAdministrator = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    $report.gitVersion = (& git --version | Out-String).Trim()
    if ($LASTEXITCODE -ne 0) { throw 'Git is unavailable in the runner environment.' }
    $actualCommit = (& git rev-parse HEAD | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or $actualCommit -ne $env:GITHUB_SHA) {
        throw 'Checkout does not match the dispatched commit.'
    }
    $report.checks.Add('git-and-exact-commit-checkout')

    $scratch = Join-Path $env:RUNNER_TEMP ("fusion-smoke-" + [Guid]::NewGuid().ToString('N'))
    $source = Join-Path $scratch 'path with spaces — 世界'
    New-Item -ItemType Directory -Path $source | Out-Null
    $payload = Join-Path $source 'unicode.txt'
    [IO.File]::WriteAllText($payload, "Windows CI: café — 世界`r`n", [Text.UTF8Encoding]::new($false))
    $expectedHash = (Get-FileHash -LiteralPath $payload -Algorithm SHA256).Hash
    $archive = Join-Path $scratch 'roundtrip.zip'
    Compress-Archive -LiteralPath $payload -DestinationPath $archive
    $restored = Join-Path $scratch 'restored'
    Expand-Archive -LiteralPath $archive -DestinationPath $restored
    if ((Get-FileHash -LiteralPath (Join-Path $restored 'unicode.txt') -Algorithm SHA256).Hash -ne $expectedHash) {
        throw 'Windows file/archive round trip changed the payload.'
    }
    $report.checks.Add('windows-file-permissions-unicode-spaces-and-zip')

    Add-Type -TypeDefinition @'
using System.Runtime.InteropServices;
public static class FusionWindowsProbe {
    [DllImport("kernel32.dll", ExactSpelling = true)]
    public static extern uint GetCurrentProcessId();
    public static int Add(int left, int right) { return left + right; }
}
'@
    if ([FusionWindowsProbe]::Add(19, 23) -ne 42 -or [FusionWindowsProbe]::GetCurrentProcessId() -ne $PID) {
        throw 'Compiled C# or native Windows API execution failed.'
    }
    $report.checks.Add('csharp-compile-and-native-windows-api')

    $childShell = Join-Path $PSHOME 'pwsh.exe'
    & $childShell -NoProfile -NonInteractive -Command 'exit 7'
    if ($LASTEXITCODE -ne 7) { throw 'Native child exit code was not preserved.' }
    $global:LASTEXITCODE = 0
    $report.checks.Add('native-child-process-exit-status')
    $report.status = 'passed'
} catch {
    $report.error = $_.Exception.Message
    throw
} finally {
    if ($scratch -and (Test-Path -LiteralPath $scratch)) {
        Remove-Item -LiteralPath $scratch -Recurse -Force
    }
    $json = $report | ConvertTo-Json -Depth 5
    $json | Set-Content -LiteralPath (Join-Path $reportDirectory 'windows-smoke.json') -Encoding utf8
    Write-Output $json
    if ($env:GITHUB_STEP_SUMMARY) {
        @(
            '### Windows compatibility smoke'
            ''
            '| Observation | Value |'
            '| --- | --- |'
            "| Result | $($report.status) |"
            "| Runner architecture | $($report.runnerArchitecture) |"
            "| Windows | $($report['windowsCaption']) |"
            "| Windows build | $($report['windowsBuild']) |"
            "| Hosted image version | $($report.hostedImageVersion) |"
            "| PowerShell | $($report['powerShellVersion']) |"
            "| Git | $($report['gitVersion']) |"
            "| Administrator token | $($report['isAdministrator']) |"
            ''
            'Passing establishes these operations on this commit and environment. It does not establish equivalence of all installed tools, Windows editions, or CPU architectures.'
        ) | Add-Content -LiteralPath $env:GITHUB_STEP_SUMMARY -Encoding utf8
    }
}
