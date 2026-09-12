[CmdletBinding()]
param()
# Protected JSON arrives on stdin. No credentials are accepted as arguments.
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$inputData=[Console]::In.ReadToEnd() | ConvertFrom-Json
$principal=[Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {throw 'An administrator maintenance session is required.'}
if ($inputData.repository -notmatch '^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$') {throw 'Expected one GitHub repository.'}
if ($inputData.invocation -notmatch '^[a-f0-9]{32}$') {throw 'Expected a new invocation identifier.'}
if ($inputData.name -ne "fusion-ci-$($inputData.invocation)") {throw 'Runner name must identify this invocation.'}
if ($inputData.mode -notin @('ephemeral','persistent')) {throw 'Unsupported registration mode.'}
foreach ($path in @($inputData.runner_directory,$inputData.receipt_path)) {
    if ($path -notmatch '^[A-Za-z]:\\' -or $path -match '[\r\n]') {throw 'Expected absolute local Windows paths.'}
}
$directory=[IO.Path]::GetFullPath($inputData.runner_directory).TrimEnd('\')
if (-not (Test-Path -LiteralPath (Join-Path $directory 'config.cmd') -PathType Leaf)) {throw 'The prepared runner distribution is missing.'}
foreach ($file in @('.runner','.credentials','.credentials_rsaparams','.service')) {
    if (Test-Path -LiteralPath (Join-Path $directory $file)) {throw "Existing registration state must be retired first: $file"}
}
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
    phase='configuration-started'; checked_at=[DateTime]::UtcNow.ToString('o')
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
$receipt.phase='service-verified'
Save-Receipt
$receipt | ConvertTo-Json -Depth 5
