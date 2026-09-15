[CmdletBinding()]
param()
# Call only after a current host-side admission/retirement check. This script
# independently verifies guest identity and refuses every running worker/listener.
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
function Assert-PlainRunnerPath([string]$Path, [bool]$Directory) {
    $item=Get-Item -LiteralPath $Path -Force
    if ([bool]$item.PSIsContainer -ne $Directory) {throw 'The recorded runner path has the wrong file type.'}
    if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {throw 'Runner retirement must not traverse a reparse point.'}
    $current=if ($Directory) {$item.Parent} else {$item.Directory}
    for (; $null -ne $current; $current=$current.Parent) {
        if ($current.Attributes -band [IO.FileAttributes]::ReparsePoint) {throw 'Runner retirement must not traverse a reparse point.'}
    }
}
$request=[Console]::In.ReadToEnd() | ConvertFrom-Json
if ($request.github_registration_absent -isnot [bool] -or $request.github_registration_absent -ne $true) {throw 'Current GitHub retirement evidence is required.'}
if ($request.runner_directory -notmatch '^[A-Za-z]:\\' -or $request.runner_directory -match '[\r\n]') {throw 'An exact installation directory is required.'}
if ($request.runner_directory.TrimEnd('\') -match '^[A-Za-z]:$') {throw 'A filesystem root cannot identify a runner installation.'}
$hasService=-not [string]::IsNullOrEmpty($request.service_name)
if ($hasService -and $request.service_name -notmatch '^actions\.runner\.') {throw 'The exact recorded service identity is required.'}
if (-not $hasService -and $request.configuration_finished -ne $true) {throw 'A service-free partial receipt requires proof that configuration ended.'}
if ($request.runner_id -isnot [long] -and $request.runner_id -isnot [int]) {throw 'An observed numeric runner ID is required.'}
if ($request.runner_id -le 0 -or [string]::IsNullOrWhiteSpace($request.runner_name)) {throw 'The exact runner identity is required.'}
if (Get-Process -Name Runner.Listener,Runner.Worker -ErrorAction SilentlyContinue) {throw 'A runner process remains active.'}
$directory=[IO.Path]::GetFullPath($request.runner_directory).TrimEnd('\')
if ($directory -eq [IO.Path]::GetPathRoot($directory+'\').TrimEnd('\')) {throw 'A filesystem root cannot identify a runner installation.'}
Assert-PlainRunnerPath $directory $true
$services=@(Get-CimInstance Win32_Service)
$service=$services | Where-Object Name -eq $request.service_name
$installationServices=@($services | Where-Object {$_.PathName.StartsWith(('"'+$directory+'\'),[StringComparison]::OrdinalIgnoreCase) -or $_.PathName.StartsWith(($directory+'\'),[StringComparison]::OrdinalIgnoreCase)})
if (@($installationServices | Where-Object Name -ne $request.service_name).Count) {throw 'Another service exists for this installation; recover its exact identity first.'}
if ($service) {
    if ($service.State -ne 'Stopped') {throw 'Stop the exact service behind an admission barrier first.'}
    if (-not $service.PathName.StartsWith(('"'+$directory+'\'),[StringComparison]::OrdinalIgnoreCase) -and
        -not $service.PathName.StartsWith(($directory+'\'),[StringComparison]::OrdinalIgnoreCase)) {throw 'Service executable belongs to another installation.'}
}
$serviceFile=Join-Path $directory '.service'
if (Test-Path -LiteralPath $serviceFile) {Assert-PlainRunnerPath $serviceFile $false}
if ($service -and -not (Test-Path -LiteralPath $serviceFile -PathType Leaf)) {throw 'The named service requires its matching .service identity file before deletion.'}
if (-not $hasService) {
    if (Test-Path -LiteralPath $serviceFile) {throw 'A service identity appeared after this partial receipt; reconcile it first.'}
}
if ((Test-Path -LiteralPath $serviceFile) -and (Get-Content -LiteralPath $serviceFile -Raw).Trim() -ne $request.service_name) {throw 'Service file identity differs.'}
$registrationFile=Join-Path $directory '.runner'
if ($service -and -not (Test-Path -LiteralPath $registrationFile -PathType Leaf) -and $request.ephemeral -ne $true) {throw 'A non-ephemeral service requires its matching .runner identity file before deletion.'}
# A completed ephemeral listener removes .runner and credential files itself.
# The host must still prove its recorded identity and current GitHub absence.
if (Test-Path -LiteralPath $registrationFile) {
    Assert-PlainRunnerPath $registrationFile $false
    $registration=Get-Content -LiteralPath $registrationFile -Raw | ConvertFrom-Json
    if ($registration.agentId -ne $request.runner_id -or $registration.agentName -ne $request.runner_name) {throw 'Guest registration identity differs.'}
}
if ($service) {
    Assert-PlainRunnerPath $directory $true
    & "$env:SystemRoot\System32\sc.exe" delete $request.service_name | Out-Null
    if ($LASTEXITCODE -ne 0) {throw 'Service deletion failed.'}
    $deadline=[DateTime]::UtcNow.AddSeconds(30)
    while (Get-Service | Where-Object Name -eq $request.service_name) {
        if ([DateTime]::UtcNow -ge $deadline) {throw 'Service deletion remains pending; preserve its registration files and inspect open service handles.'}
        Start-Sleep -Milliseconds 500
    }
}
# These files belong to the retired registration. Checkouts, caches, markers and
# the prepared runner distribution are retained for subsequent diagnostic jobs.
foreach ($name in @('.runner','.credentials','.credentials_rsaparams','.service')) {
    $path=Join-Path $directory $name
    Assert-PlainRunnerPath $directory $true
    if (Test-Path -LiteralPath $path) {Assert-PlainRunnerPath $path $false; Remove-Item -LiteralPath $path -Force}
}
[ordered]@{runner_id=$request.runner_id;service_name=$request.service_name;registration_files_removed=$true;working_files_preserved=$true}|ConvertTo-Json
