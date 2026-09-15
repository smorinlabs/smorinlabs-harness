# Replace/extend $checks with the repository's real diagnostic tests. Each ID
# must identify an executed assertion. A missing selection never becomes a pass.
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$PSNativeCommandUseErrorActionPreference = $false
$report = [ordered]@{
    schema_version = 1
    invocation = $env:DIAGNOSTIC_ID
    commit = $env:GITHUB_SHA
    run_id = [long]$env:GITHUB_RUN_ID
    run_attempt = [long]$env:GITHUB_RUN_ATTEMPT
    runner_name = $env:RUNNER_NAME
    architecture = $env:RUNNER_ARCH
    operating_system = $env:RUNNER_OS
    native_architecture = [Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString().ToUpperInvariant()
    process_architecture = [Runtime.InteropServices.RuntimeInformation]::ProcessArchitecture.ToString().ToUpperInvariant()
    is_administrator = $null
    status = 'failed'
    tests = [Collections.Generic.List[object]]::new()
    checked_at = [DateTime]::UtcNow.ToString('o')
}
$destination = Join-Path $env:GITHUB_WORKSPACE 'artifacts'
New-Item -ItemType Directory -Path $destination -Force | Out-Null
$exitCode = 1
try {
    if ($env:DIAGNOSTIC_ID -notmatch '^[a-f0-9]{32}$') {throw 'Invalid diagnostic invocation.'}
    if (-not $IsWindows -or $report.operating_system -ne 'Windows') {throw 'Native Windows is required.'}
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    $report.is_administrator = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    if ($report.is_administrator) {throw 'This diagnostic requires the standard CI account.'}
    foreach ($architecture in @($report.architecture, $report.native_architecture, $report.process_architecture)) {
        if ($architecture -cne $env:DIAGNOSTIC_ARCHITECTURE) {throw 'Runner, OS, process, and expected architectures must agree.'}
    }
    $commit = (& git rev-parse HEAD | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or $commit -cne $report.commit) {throw 'Checkout does not match the dispatched revision.'}
    $selected = ConvertFrom-Json -InputObject $env:DIAGNOSTIC_TEST_IDS -NoEnumerate
    if ($selected -isnot [array] -or @($selected | Where-Object {$_ -isnot [string] -or [string]::IsNullOrWhiteSpace($_)}).Count) {
        throw 'Test selection must be a JSON array of nonempty IDs.'
    }
    if (@($selected | Sort-Object -Unique).Count -ne $selected.Count) {throw 'Duplicate test selection.'}
    $checks = [ordered]@{
        'windows-file-roundtrip' = {
            $scratch = Join-Path $env:RUNNER_TEMP ([Guid]::NewGuid().ToString('N'))
            try {
                New-Item -ItemType Directory -Path $scratch | Out-Null
                $file = Join-Path $scratch 'path with spaces — 世界.txt'
                $value = "Windows CI: café — 世界`r`n"
                [IO.File]::WriteAllText($file, $value, [Text.UTF8Encoding]::new($false))
                if ([IO.File]::ReadAllText($file) -cne $value) {throw 'File round trip changed the payload.'}
            } finally {
                if (Test-Path -LiteralPath $scratch) {Remove-Item -LiteralPath $scratch -Recurse -Force}
            }
        }
        'native-child-exit' = {
            & (Join-Path $PSHOME 'pwsh.exe') -NoProfile -NonInteractive -Command 'exit 7'
            if ($LASTEXITCODE -ne 7) {throw 'Native child exit code was not preserved.'}
            $global:LASTEXITCODE = 0
        }
    }
    $ids = @(if ($selected.Count) {$checks.Keys | Where-Object {$_ -cin $selected}} else {$checks.Keys})
    if (-not $ids.Count -or ($selected.Count -and $ids.Count -ne $selected.Count)) {throw 'Requested test selection was not found; zero or partial execution is not a pass.'}
    foreach ($id in $ids) {
        $test = [ordered]@{id=$id; status='passed'}
        try {& $checks[$id]} catch {$test.status='failed'; $test.error=$_.Exception.Message; Write-Warning "$id failed: $($test.error)"}
        $report.tests.Add($test)
    }
    if (@($report.tests | Where-Object status -eq 'failed').Count -eq 0) {$report.status='passed'; $exitCode=0}
} catch {
    $report.error = $_.Exception.Message
    Write-Warning $report.error
} finally {
    $json = $report | ConvertTo-Json -Depth 6
    $json | Set-Content -LiteralPath (Join-Path $destination 'windows-diagnostic.json') -Encoding utf8
    Write-Output $json
}
exit $exitCode
