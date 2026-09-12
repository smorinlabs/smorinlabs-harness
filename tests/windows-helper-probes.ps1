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
$payload='{"github_registration_absent":true,"runner_directory":"C:\\fixture","service_name":null,"configuration_finished":true,"runner_id":123,"runner_name":"fusion-ci-fixture"}'
foreach($case in @('partial','mismatch','worker','service-file','service-object')) {
  $raw=$payload | & $executable -NoLogo -NoProfile -NonInteractive -File (Join-Path $PSScriptRoot "windows-retirement-fixture.ps1") -PublicCheckout $public -Case $case
  $result=($raw -join "`n")|ConvertFrom-Json
  if($case -eq 'partial') {
    if($result.result -ne 'pass' -or $result.removed.Count -ne 3){$failures.Add('Partial retirement did not remove the expected fixture paths')}
  } elseif($result.result -ne 'error' -or $result.removed.Count -ne 0) {$failures.Add("Retirement guard failed: $case")}
  $raw
}
if($failures.Count){throw ($failures -join '; ')}
[ordered]@{probe='summary';parser_files=3;selection_cases=4;mode_cases=5;retirement_cases=5;failures=0}|ConvertTo-Json -Compress
