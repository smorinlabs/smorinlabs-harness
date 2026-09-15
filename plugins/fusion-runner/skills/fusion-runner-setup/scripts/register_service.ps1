#requires -Version 7.4
#requires -PSEdition Core
[CmdletBinding()]
param()
# Protected JSON arrives on stdin. No credentials are accepted as arguments.
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest

function Assert-ProtectedRunnerParent([string]$Path) {
    $item=Get-Item -LiteralPath $Path -Force
    if (-not $item.PSIsContainer) {throw 'The runner parent must be a directory.'}
    for ($ancestor=$item; $null -ne $ancestor; $ancestor=$ancestor.Parent) {
        if ($ancestor.Attributes -band [IO.FileAttributes]::ReparsePoint) {throw 'Runner paths must not traverse a reparse point.'}
    }
    $acl=Get-Acl -LiteralPath $Path
    $trusted=@('S-1-5-18','S-1-5-32-544')
    if ($acl.GetOwner([Security.Principal.SecurityIdentifier]).Value -notin $trusted) {throw 'The runner parent needs a trusted owner.'}
    $write=[Security.AccessControl.FileSystemRights]'Write,Delete,DeleteSubdirectoriesAndFiles,ChangePermissions,TakeOwnership'
    foreach ($rule in @($acl.Access)) {
        $sid=$rule.IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value
        if ($rule.AccessControlType -eq 'Allow' -and ($rule.FileSystemRights -band $write) -and $sid -notin $trusted) {throw 'The runner parent allows an untrusted writer.'}
    }
}

function Get-VerifiedRunnerArchive([string]$Url, [string]$Destination, [string]$Sha256) {
    # Download into administrator-only storage. No bytes from a prior job's
    # directory are used, even when that job left an apparently valid config.cmd.
    $client=[Net.Http.HttpClient]::new()
    $cancel=[Threading.CancellationTokenSource]::new([TimeSpan]::FromSeconds(120))
    $response=$null; $source=$null; $target=$null
    try {
        $response=$client.GetAsync($Url,[Net.Http.HttpCompletionOption]::ResponseHeadersRead,$cancel.Token).GetAwaiter().GetResult()
        [void]$response.EnsureSuccessStatusCode()
        $source=$response.Content.ReadAsStreamAsync($cancel.Token).GetAwaiter().GetResult()
        $target=[IO.File]::Open($Destination,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
        $buffer=[byte[]]::new(65536); $total=0L
        while (($count=$source.ReadAsync($buffer,0,$buffer.Length,$cancel.Token).GetAwaiter().GetResult()) -gt 0) {
            $total+=$count
            if ($total -gt 256MB) {throw 'The runner archive exceeded the 256 MiB download bound.'}
            $target.Write($buffer,0,$count)
        }
        $target.Dispose(); $target=$null
        if ((Get-FileHash -LiteralPath $Destination -Algorithm SHA256).Hash -ine $Sha256) {throw 'The downloaded runner archive does not match the official release SHA-256.'}
    } finally {
        if ($null -ne $target) {$target.Dispose()}
        if ($null -ne $source) {$source.Dispose()}
        if ($null -ne $response) {$response.Dispose()}
        $cancel.Dispose(); $client.Dispose()
    }
}

function Initialize-RunnerDistribution($Request) {
    $architecture=[Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString().ToLowerInvariant()
    $process=[Runtime.InteropServices.RuntimeInformation]::ProcessArchitecture.ToString().ToLowerInvariant()
    if ($architecture -notin @('arm64','x64') -or $process -ne $architecture) {throw 'Use native PowerShell for the supported Windows architecture.'}
    if ($Request.runner_version -notmatch '^[0-9]+\.[0-9]+\.[0-9]+$' -or $Request.runner_archive_sha256 -notmatch '^[a-fA-F0-9]{64}$') {throw 'An official runner version and SHA-256 are required.'}
    $asset="actions-runner-win-$architecture-$($Request.runner_version).zip"
    $url="https://github.com/actions/runner/releases/download/v$($Request.runner_version)/$asset"
    if ($Request.runner_archive_url -cne $url) {throw 'The archive URL must identify the exact official native runner release.'}
    $parent=Join-Path ([Environment]::GetFolderPath('CommonApplicationData')) 'FusionRunnerPrograms'
    $destination=Join-Path $parent $Request.invocation
    if ($Request.runner_directory -ine $destination) {throw 'Use the unused invocation directory under ProgramData\FusionRunnerPrograms.'}
    if (-not (Test-Path -LiteralPath $parent)) {
        $acl=[Security.AccessControl.DirectorySecurity]::new()
        $acl.SetAccessRuleProtection($true,$false)
        $acl.SetOwner([Security.Principal.SecurityIdentifier]::new('S-1-5-32-544'))
        foreach ($sid in @('S-1-5-18','S-1-5-32-544')) {
            $acl.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new([Security.Principal.SecurityIdentifier]::new($sid),'FullControl','ContainerInherit,ObjectInherit','None','Allow'))
        }
        [IO.FileSystemAclExtensions]::Create([IO.DirectoryInfo]::new($parent),$acl)
    }
    Assert-ProtectedRunnerParent $parent
    # Runner.Listener validates read access to every ancestor. Grant this
    # account read/traverse on the parent only, never creation/deletion/write.
    $parentAcl=Get-Acl -LiteralPath $parent
    $parentAcl.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new([Security.Principal.SecurityIdentifier]::new($Request.service_account_sid),'ReadAndExecute','None','None','Allow'))
    Set-Acl -LiteralPath $parent -AclObject $parentAcl
    Assert-ProtectedRunnerParent $parent
    if (Test-Path -LiteralPath $destination) {throw 'The runner invocation directory already exists; never reuse it for elevated registration.'}
    # CreateNew reserves the invocation even after an interrupted extraction.
    $archive=Join-Path $parent "$($Request.invocation).zip"
    Get-VerifiedRunnerArchive $url $archive $Request.runner_archive_sha256
    [IO.Compression.ZipFile]::ExtractToDirectory($archive,$destination)
    Assert-ProtectedRunnerParent $parent
    foreach ($relative in @('config.cmd','bin\Runner.Listener.exe','bin\RunnerService.exe')) {
        if (-not (Test-Path -LiteralPath (Join-Path $destination $relative) -PathType Leaf)) {throw 'The verified archive lacks required runner programs.'}
    }
    # Remove only this newly downloaded staging archive. Keep the installed
    # distribution, earlier working files and all registration receipts.
    Remove-Item -LiteralPath $archive
    return [ordered]@{version=$Request.runner_version;asset=$asset;url=$url;sha256=$Request.runner_archive_sha256;verified=$true}
}

$inputData=[Console]::In.ReadToEnd() | ConvertFrom-Json
$principal=[Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {throw 'An administrator maintenance session is required.'}
if ($inputData.repository -notmatch '^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$') {throw 'Expected one GitHub repository.'}
if ($inputData.invocation -notmatch '^[a-f0-9]{32}$') {throw 'Expected a new invocation identifier.'}
if ($inputData.name -ne "fusion-ci-$($inputData.invocation)") {throw 'Runner name must identify this invocation.'}
if ($inputData.mode -ne 'ephemeral') {throw 'This helper supports one-job ephemeral registration only.'}
foreach ($path in @($inputData.runner_directory,$inputData.receipt_path)) {
    if ($path -notmatch '^[A-Za-z]:\\' -or $path -match '[\r\n]') {throw 'Expected absolute local Windows paths.'}
}
$directory=[IO.Path]::GetFullPath($inputData.runner_directory).TrimEnd('\')
if (Test-Path -LiteralPath $directory) {throw 'The runner directory already exists; use a new invocation directory.'}
if (Get-Process -Name Runner.Listener,Runner.Worker -ErrorAction SilentlyContinue) {throw 'Another runner process is active.'}
$account=Get-LocalUser | Where-Object {$_.SID.Value -eq $inputData.service_account_sid}
if ($null -eq $account) {throw 'The recorded local service account SID was not found.'}
$qualified="$env:COMPUTERNAME\$($account.Name)"
if ($qualified -ine $inputData.service_account) {throw 'Service account name and SID disagree.'}
if (@(Get-LocalGroupMember -SID 'S-1-5-32-544').SID.Value -contains $account.SID.Value) {throw 'The service account must not be an administrator.'}
if ([string]::IsNullOrEmpty($inputData.token) -or [string]::IsNullOrEmpty($inputData.password)) {throw 'Protected registration inputs are missing.'}
$receiptPath=[IO.Path]::GetFullPath($inputData.receipt_path)
if (Test-Path -LiteralPath $receiptPath) {throw 'Use a new guest receipt path; preserve the previous registration evidence.'}
$parent=Get-Item -LiteralPath ([IO.Path]::GetDirectoryName($receiptPath))
if (-not $parent.PSIsContainer -or ($parent.Attributes -band [IO.FileAttributes]::ReparsePoint)) {throw 'Receipt parent must be an existing administrator-controlled directory.'}
$write=[Security.AccessControl.FileSystemRights]'Write,Delete,ChangePermissions,TakeOwnership'
$allowed=@('S-1-5-18','S-1-5-32-544','S-1-3-0',[Security.Principal.WindowsIdentity]::GetCurrent().User.Value)
$receiptAcl=Get-Acl -LiteralPath $parent.FullName
$owner=$receiptAcl.GetOwner([Security.Principal.SecurityIdentifier]).Value
if ($owner -notin @('S-1-5-18','S-1-5-32-544',[Security.Principal.WindowsIdentity]::GetCurrent().User.Value)) {throw 'The receipt directory has an untrusted owner who could rewrite its permissions.'}
foreach ($rule in @($receiptAcl.Access)) {
    $sid=$rule.IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value
    if ($rule.AccessControlType -eq 'Allow' -and ($rule.FileSystemRights -band $write) -and $sid -notin $allowed) {throw 'The guest receipt must not be writable by the CI account or other untrusted users.'}
}
$receipt=[ordered]@{
    schema_version=1; repository=$inputData.repository; invocation=$inputData.invocation
    runner_name=$inputData.name; runner_id=$null; runner_directory=$directory
    service_name=$null; service_account=$qualified; service_account_sid=$account.SID.Value
    ephemeral=($inputData.mode -eq 'ephemeral'); configuration_finished=$false
    phase='preparation-started'; distribution=$null; checked_at=[DateTime]::UtcNow.ToString('o')
    native_architecture=[Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString().ToUpperInvariant()
    process_architecture=[Runtime.InteropServices.RuntimeInformation]::ProcessArchitecture.ToString().ToUpperInvariant()
    labels=@("fusion-ci-$($inputData.invocation)")
}
function Save-Receipt {
    $receipt.checked_at=[DateTime]::UtcNow.ToString('o')
    $temporary="$receiptPath.tmp"
    $receipt | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $temporary -Encoding UTF8
    Move-Item -LiteralPath $temporary -Destination $receiptPath -Force
}
Save-Receipt
$receipt.distribution=Initialize-RunnerDistribution $inputData
$receipt.phase='configuration-started'
Save-Receipt
# Runner CommandSettings consumes and masks these protected process inputs.
$values=@{
    URL="https://github.com/$($inputData.repository)"; NAME=$inputData.name
    LABELS=($receipt.labels -join ','); WORK='_work'
    WINDOWSLOGONACCOUNT=$qualified; WINDOWSLOGONPASSWORD=$inputData.password; TOKEN=$inputData.token
}
try {
    foreach ($key in $values.Keys) {[Environment]::SetEnvironmentVariable("ACTIONS_RUNNER_INPUT_$key",$values[$key],'Process')}
    Push-Location -LiteralPath $directory
    try {
        # Exclusive invocation routing prevents default-label jobs from claiming
        # this registration. It supplements the trusted-repository policy.
        $arguments=@('--unattended','--runasservice','--no-default-labels')
        if ($receipt.ephemeral) {$arguments+='--ephemeral'}
        & .\config.cmd @arguments
        if ($LASTEXITCODE -ne 0) {throw "Runner configuration failed with exit $LASTEXITCODE"}
    } finally {Pop-Location}
} finally {
    foreach ($key in $values.Keys) {[Environment]::SetEnvironmentVariable("ACTIONS_RUNNER_INPUT_$key",$null,'Process')}
    $values.Clear()
    $receipt.configuration_finished=$true
    try {
        if (Test-Path -LiteralPath (Join-Path $directory '.runner')) {
            $registration=Get-Content -LiteralPath (Join-Path $directory '.runner') -Raw | ConvertFrom-Json
            if ($registration.agentName -ne $receipt.runner_name) {throw 'The guest registration identity changed.'}
            $receipt.runner_id=$registration.agentId
            # Persistent .runner files may omit the default false field.
            $ephemeralProperty=$registration.PSObject.Properties['ephemeral']
            $observedEphemeral=($null -ne $ephemeralProperty -and $ephemeralProperty.Value -eq $true)
            $modeMatches=$receipt.ephemeral -eq $observedEphemeral
            $receipt.ephemeral=$observedEphemeral
            $receipt.phase='registered'
            if (-not $modeMatches) {throw 'Observed registration mode differs from the requested mode.'}
        }
    } finally {
        try {
            if (Test-Path -LiteralPath (Join-Path $directory '.service')) {
                $receipt.service_name=(Get-Content -LiteralPath (Join-Path $directory '.service') -Raw).Trim()
            }
        } finally {Save-Receipt; Remove-Variable inputData}
    }
}
$service=Get-CimInstance Win32_Service | Where-Object Name -eq $receipt.service_name
if ($null -eq $service -or ($service.StartName -ine $qualified -and $service.StartName -ine ".\$($account.Name)")) {throw 'The expected service account was not verified.'}
if ($service.State -ne 'Running' -or $service.PathName.Trim('"') -ine (Join-Path $directory 'bin\RunnerService.exe')) {throw 'The running service executable was not verified for this installation.'}
$receipt.phase='service-verified'
Save-Receipt
$receipt | ConvertTo-Json -Depth 5
