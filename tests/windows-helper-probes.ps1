[CmdletBinding()]
param([string]$PublicCheckout=(Split-Path -Parent $PSScriptRoot))
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$public=$PublicCheckout
$failures=[Collections.Generic.List[string]]::new()
$files=@(
  "$public/plugins/fusion-runner/skills/fusion-runner-setup/scripts/register_service.ps1",
  "$public/plugins/fusion-runner/skills/fusion-runner-run/scripts/retire_service.ps1",
  "$public/plugins/repo-hygiene/skills/ci-fix/references/examples/windows-diagnostic.ps1")
foreach($file in $files) {
  $tokens=$null;$errors=$null
  [void][Management.Automation.Language.Parser]::ParseFile($file,[ref]$tokens,[ref]$errors)
  if($errors.Count){$failures.Add("Parser: $file")}
  [ordered]@{probe='parser';file=$file;error_count=$errors.Count}|ConvertTo-Json -Compress
}
$diagnostic=Get-Content -LiteralPath "$public/plugins/repo-hygiene/skills/ci-fix/references/examples/windows-diagnostic.ps1"
$selectionCode=($diagnostic | Where-Object {$_ -match '^    \$ids =|^    if \(-not \$ids.Count'}) -join "`n"
$checks=[ordered]@{'windows-file-roundtrip'={};'native-child-exit'={}}
foreach ($selection in @('[]','["windows-file-roundtrip"]','["windows-file-roundtrip","native-child-exit"]','["missing"]')) {
  try {
    $selected=ConvertFrom-Json -InputObject $selection -NoEnumerate
    . ([scriptblock]::Create($selectionCode))
    if($selection -eq '["missing"]'){$failures.Add('Missing selection unexpectedly accepted')}
    [ordered]@{probe='fixed-actual-selection';selection=$selection;result='pass';ids=@($ids)}|ConvertTo-Json -Compress
  } catch {
    if($selection -ne '["missing"]' -or $_.Exception.Message -notlike 'Requested test selection was not found*'){$failures.Add("Selection: $selection")}
    [ordered]@{probe='fixed-actual-selection';selection=$selection;result='error';message=$_.Exception.Message}|ConvertTo-Json -Compress
  }
}
$registrationCode=Get-Content -LiteralPath "$public/plugins/fusion-runner/skills/fusion-runner-setup/scripts/register_service.ps1"
$modeCode=($registrationCode | Where-Object {$_ -match '^            \$(ephemeralProperty|observedEphemeral|modeMatches|receipt\.ephemeral|receipt\.phase)=' -or $_ -match '^            if \(-not \$modeMatches\)'}) -join "`n"
foreach ($sample in @(
 @{name='persistent-omitted';intent=$false;json='{"agentId":123,"agentName":"fixture"}'},
 @{name='persistent-false';intent=$false;json='{"agentId":123,"agentName":"fixture","ephemeral":false}'},
 @{name='ephemeral-true';intent=$true;json='{"agentId":123,"agentName":"fixture","ephemeral":true}'},
 @{name='ephemeral-omitted';intent=$true;json='{"agentId":123,"agentName":"fixture"}'},
 @{name='persistent-true';intent=$false;json='{"agentId":123,"agentName":"fixture","ephemeral":true}'})) {
  try {
    $registration=$sample.json|ConvertFrom-Json
    $receipt=@{ephemeral=$sample.intent}
    . ([scriptblock]::Create($modeCode))
    if($sample.name -in @('ephemeral-omitted','persistent-true')){$failures.Add("Mode mismatch accepted: $($sample.name)")}
    [ordered]@{probe='fixed-actual-ephemeral';sample=$sample.name;result='pass';ephemeral=$receipt.ephemeral}|ConvertTo-Json -Compress
  } catch {
    if($sample.name -notin @('ephemeral-omitted','persistent-true') -or $_.Exception.Message -ne 'Observed registration mode differs from the requested mode.'){$failures.Add("Mode: $($sample.name)")}
    [ordered]@{probe='fixed-actual-ephemeral';sample=$sample.name;result='error';message=$_.Exception.Message}|ConvertTo-Json -Compress
  }
}

$executable=[Environment]::ProcessPath
$request=@{github_registration_absent=$true;runner_directory='C:\fixture';service_name=$null;configuration_finished=$true;runner_id=123;runner_name='fusion-ci-fixture';ephemeral=$true}
foreach($case in @('partial','mismatch','worker','service-file','service-object','registered','missing-named','registered-other','missing-identity-files','ephemeral-retired','persistent-missing-runner','root')) {
  $request.runner_directory=if($case -eq 'root'){'C:\'}else{'C:\fixture'}
  $request.service_name=if($case -in @('registered','missing-named','registered-other','missing-identity-files','ephemeral-retired','persistent-missing-runner')){'actions.runner.fixture'}else{$null}
  $request.ephemeral=$case -ne 'persistent-missing-runner'
  $payload=$request|ConvertTo-Json -Compress
  $raw=$payload | & $executable -NoLogo -NoProfile -NonInteractive -File (Join-Path $PSScriptRoot "windows-retirement-fixture.ps1") -PublicCheckout $public -Case $case
  $result=($raw -join "`n")|ConvertFrom-Json
  if($case -eq 'partial') {
    if($result.result -ne 'pass' -or $result.removed.Count -ne 3){$failures.Add('Partial retirement did not remove the expected fixture paths')}
  } elseif($case -in @('registered','ephemeral-retired')) {
    $expectedFiles=if($case -eq 'registered'){4}else{1}
    if($result.result -ne 'pass' -or $result.removed.Count -ne $expectedFiles -or $result.deleted_services.Count -ne 1 -or $result.deleted_services[0] -ne 'actions.runner.fixture'){$failures.Add('Registered retirement did not remove exactly its service and remaining files')}
  } elseif($result.result -ne 'error' -or $result.removed.Count -ne 0 -or $result.deleted_services.Count -ne 0) {$failures.Add("Retirement guard failed: $case")}
  $raw
}
$registrationSource=$registrationCode -join "`n"
$serviceCode=$registrationSource.Substring($registrationSource.LastIndexOf('$service=Get-CimInstance'))
$directory=[IO.Path]::GetFullPath('C:\fixture');$qualified='VM\ci';$account=[pscustomobject]@{Name='ci'}
function Save-Receipt {}
function Get-CimInstance {param($ClassName) $script:FixtureService}
foreach($case in @('running','stopped','wrong-path','wrong-account')) {
  $receipt=@{service_name='actions.runner.fixture';phase='registered'}
  $script:FixtureService=[pscustomobject]@{Name='actions.runner.fixture';StartName=$qualified;State='Running';PathName=(Join-Path $directory 'bin\RunnerService.exe')}
  if($case -eq 'stopped'){$script:FixtureService.State='Stopped'}
  if($case -eq 'wrong-path'){$script:FixtureService.PathName='C:\other\bin\RunnerService.exe'}
  if($case -eq 'wrong-account'){$script:FixtureService.StartName='VM\other'}
  $refused=$false
  try {. ([scriptblock]::Create($serviceCode))|Out-Null} catch {$refused=$true}
  if($refused -ne ($case -ne 'running')){$failures.Add("Service verification failed: $case")}
}
if($failures.Count){throw ($failures -join '; ')}
[ordered]@{probe='summary';parser_files=3;selection_cases=4;mode_cases=5;retirement_cases=12;service_cases=4;failures=0}|ConvertTo-Json -Compress
