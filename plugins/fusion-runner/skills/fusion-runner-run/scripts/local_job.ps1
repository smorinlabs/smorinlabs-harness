# Internal standard-account adapter. Input is structured JSON on stdin.
# The caller verifies this script's hash before invoking it. Never elevate it.
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$inputData = [Console]::In.ReadToEnd() | ConvertFrom-Json -AsHashtable
$invocation = [string]$inputData.invocation
if ($invocation -notmatch '^[a-f0-9]{32}$') {throw 'Invalid invocation.'}
$root = Join-Path ([Environment]::GetFolderPath('LocalApplicationData')) 'FusionLocalJobs'
$jobDirectory = Join-Path $root $invocation
$resultPath = Join-Path $jobDirectory 'result.json'
$lease = $null
$process = $null
$stdoutFile = $null
$stderrFile = $null
$canWriteResult = $false
$clock = [Diagnostics.Stopwatch]::StartNew()
$result = [ordered]@{
    schema_version=1; invocation=$invocation; status='preparation-failed'
    snapshot_sha256=$null; spec_sha256=$inputData.spec_sha256
    account_sid=$null; is_administrator=$null; architecture=$null
    exit_code=$null; timed_out=$false; error=$null
    execution_seconds=0; preparation_seconds=0
    stdout_bytes=0; stderr_bytes=0; evidence_sha256=$null
}
function Assert-PlainPath([string]$Path) {
    $node = Get-Item -LiteralPath $Path -Force -ErrorAction Stop
    while ($null -ne $node) {
        if ($node.Attributes -band [IO.FileAttributes]::ReparsePoint) {throw 'Redirected guest path refused.'}
        $node = if ($node -is [IO.DirectoryInfo]) {$node.Parent} else {$node.Directory}
    }
}
function Assert-RelativePath([string]$Path) {
    if (-not $Path -or [IO.Path]::IsPathRooted($Path) -or $Path.Contains('\') -or $Path.Contains(':') -or
        @($Path.Split('/') | Where-Object {$_ -eq '..' -or $_ -eq '.' -or -not $_}).Count) {
        throw 'Noncanonical relative path refused.'
    }
}
try {
    if (-not $IsWindows) {throw 'Native Windows is required.'}
    Assert-PlainPath $jobDirectory
    if (Test-Path -LiteralPath $resultPath) {throw 'Invocation already has a result; collect it instead.'}
    $canWriteResult = $true
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    $result.account_sid = $identity.User.Value
    $result.is_administrator = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    $result.architecture = [Runtime.InteropServices.RuntimeInformation]::ProcessArchitecture.ToString().ToUpperInvariant()
    if ($result.is_administrator -or $result.account_sid -cne $inputData.account_sid -or
        $result.architecture -cne $inputData.architecture -or
        [Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString().ToUpperInvariant() -cne $inputData.architecture) {
        throw 'The exact native standard-account identity is required.'
    }
    $lease = [IO.File]::Open((Join-Path $root 'active.lock'), [IO.FileMode]::OpenOrCreate,
        [IO.FileAccess]::ReadWrite, [IO.FileShare]::None)
    # The host's fixed maintenance query checks services before admission and
    # collection. The standard SSH token cannot enumerate Windows services.
    if (@(Get-Process -Name 'Runner.Listener','Runner.Worker' -ErrorAction SilentlyContinue).Count) {
        throw 'GitHub runner work is present; local execution refused.'
    }
    $archive = Join-Path $jobDirectory 'input.zip'
    if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant() -cne $inputData.archive_sha256) {
        throw 'Archive digest mismatch.'
    }
    $zip = [IO.Compression.ZipFile]::OpenRead($archive)
    try {
        $names = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
        foreach ($entry in $zip.Entries) {
            Assert-RelativePath $entry.FullName
            if (-not $names.Add($entry.FullName)) {throw 'Duplicate archive path.'}
        }
    } finally {$zip.Dispose()}
    $unpacked = Join-Path $jobDirectory 'unpacked'
    if (Test-Path -LiteralPath $unpacked) {throw 'Invocation has already been prepared; inspect it instead of rerunning.'}
    [IO.Compression.ZipFile]::ExtractToDirectory($archive, $unpacked)
    $snapshot = Get-Content -LiteralPath (Join-Path $unpacked 'snapshot.json') -Raw | ConvertFrom-Json -AsHashtable
    $spec = Get-Content -LiteralPath (Join-Path $unpacked 'spec.json') -Raw | ConvertFrom-Json -AsHashtable
    $result.snapshot_sha256 = $snapshot.snapshot_sha256
    if ($snapshot.snapshot_sha256 -cne $inputData.snapshot_sha256) {throw 'Snapshot identity mismatch.'}
    $source = Join-Path $unpacked 'source'
    foreach ($file in $snapshot.files) {
        Assert-RelativePath $file.path
        $path = Join-Path $source $file.path
        Assert-PlainPath $path
        if ((Get-Item -LiteralPath $path).Length -ne $file.bytes -or
            (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -cne $file.sha256) {
            throw 'Transferred source differs from the captured snapshot.'
        }
    }
    $work = $source
    if ($spec.working_directory -ne '.') {
        Assert-RelativePath $spec.working_directory
        $work = Join-Path $source $spec.working_directory
    }
    Assert-PlainPath $work
    $evidence = $null
    if ($spec.evidence.kind -ne 'command') {
        Assert-RelativePath $spec.evidence.path
        $evidence = Join-Path $source $spec.evidence.path
        if (Test-Path -LiteralPath $evidence) {throw 'Evidence path already exists in the snapshot.'}
    }
    $start = [Diagnostics.ProcessStartInfo]::new()
    $start.FileName = Join-Path $PSHOME 'pwsh.exe'
    $start.UseShellExecute = $false
    $start.WorkingDirectory = $work
    $start.RedirectStandardOutput = $true
    $start.RedirectStandardError = $true
    $start.RedirectStandardInput = $true
    foreach ($argument in @('-NoLogo','-NoProfile','-NonInteractive','-File',(Join-Path $unpacked 'command.ps1'))) {
        [void]$start.ArgumentList.Add($argument)
    }
    foreach ($entry in $spec.environment.GetEnumerator()) {$start.Environment[$entry.Key] = [string]$entry.Value}
    $stdoutFile = [IO.File]::Create((Join-Path $jobDirectory 'stdout.log'))
    $stderrFile = [IO.File]::Create((Join-Path $jobDirectory 'stderr.log'))
    $result.preparation_seconds = $clock.Elapsed.TotalSeconds
    $execution = [Diagnostics.Stopwatch]::StartNew()
    $process = [Diagnostics.Process]::Start($start)
    $process.StandardInput.Close()
    $outTask = $process.StandardOutput.BaseStream.CopyToAsync($stdoutFile)
    $errTask = $process.StandardError.BaseStream.CopyToAsync($stderrFile)
    if (-not $process.WaitForExit([int]($spec.timeout_seconds * 1000))) {
        $result.timed_out = $true
        $process.Kill($true)
        if (-not $process.WaitForExit(10000)) {throw 'Timed-out process termination was not confirmed.'}
    }
    if (-not [Threading.Tasks.Task]::WaitAll(@($outTask,$errTask), 10000)) {
        throw 'Output handles remained open after the command finished.'
    }
    $result.execution_seconds = $execution.Elapsed.TotalSeconds
    $result.exit_code = $process.ExitCode
    $stdoutFile.Dispose(); $stdoutFile = $null
    $stderrFile.Dispose(); $stderrFile = $null
    $result.stdout_bytes = (Get-Item -LiteralPath (Join-Path $jobDirectory 'stdout.log')).Length
    $result.stderr_bytes = (Get-Item -LiteralPath (Join-Path $jobDirectory 'stderr.log')).Length
    if ($null -ne $evidence -and (Test-Path -LiteralPath $evidence)) {
        Assert-PlainPath $evidence
        if ((Get-Item -LiteralPath $evidence).Length -gt 8388608) {throw 'Evidence exceeds the 8 MiB bound.'}
        Copy-Item -LiteralPath $evidence -Destination (Join-Path $jobDirectory 'evidence')
        $result.evidence_sha256 = (Get-FileHash -LiteralPath (Join-Path $jobDirectory 'evidence') -Algorithm SHA256).Hash.ToLowerInvariant()
    }
    if (@(Get-Process -Name 'Runner.Listener','Runner.Worker' -ErrorAction SilentlyContinue).Count) {
        throw 'GitHub runner work appeared during local execution; shared execution is not accepted.'
    }
    $result.status = 'completed'
} catch {
    # The tested command's output is in separate logs. Do not echo input objects.
    $result.error = $_.Exception.Message
    if ($null -ne $process -and -not $process.HasExited) {
        try {
            $process.Kill($true)
            if (-not $process.WaitForExit(10000)) {$result.status='process-state-unknown'}
        } catch {$result.status='process-state-unknown'}
    }
} finally {
    if ($null -ne $stdoutFile) {$stdoutFile.Dispose()}
    if ($null -ne $stderrFile) {$stderrFile.Dispose()}
    if ($null -ne $process) {$process.Dispose()}
    if ($null -ne $lease) {$lease.Dispose()}
    if ($canWriteResult) {
        foreach ($stream in @('stdout','stderr')) {
            $log=Join-Path $jobDirectory ($stream + '.log')
            if (Test-Path -LiteralPath $log) {$result[$stream + '_bytes']=(Get-Item -LiteralPath $log).Length}
        }
    }
    $json = $result | ConvertTo-Json -Depth 12 -Compress
    if ($canWriteResult -and -not (Test-Path -LiteralPath $resultPath)) {
        $pending = Join-Path $jobDirectory ('result-' + [Guid]::NewGuid().ToString('N') + '.tmp')
        [IO.File]::WriteAllText($pending, $json, [Text.UTF8Encoding]::new($false))
        [IO.File]::Move($pending, $resultPath, $false)
    }
    [Console]::Out.WriteLine($json)
}
if ($result.status -ne 'completed') {exit 5}
if ($result.timed_out -or $result.exit_code -ne 0) {exit 1}
exit 0
