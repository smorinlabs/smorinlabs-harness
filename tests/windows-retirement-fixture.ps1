[CmdletBinding()]
param([Parameter(Mandatory)][string]$PublicCheckout,[ValidateSet('partial','mismatch','worker','service-file','service-object','registered','missing-named','registered-other','missing-identity-files','ephemeral-retired','persistent-missing-runner','root')][string]$Case)
$source=[IO.File]::ReadAllText((Join-Path $PublicCheckout 'plugins/fusion-runner/skills/fusion-runner-run/scripts/retire_service.ps1'))
# macOS cannot invoke Windows sc.exe. Replace only that native call; execute
# the complete current guard, deletion-wait and file-removal control flow.
$source=$source.Replace('& "$env:SystemRoot\System32\sc.exe"','Invoke-FixtureSc')
$global:FixtureCase=$Case
$global:Removed=[Collections.Generic.List[string]]::new()
$global:DeletedServices=[Collections.Generic.List[string]]::new()
function Invoke-FixtureSc {param($Operation,$Name) if($Operation -ne 'delete'){throw 'Unexpected sc operation'}; $global:DeletedServices.Add($Name);$global:LASTEXITCODE=0}
function Get-Service { @() }
function Get-Process {param($Name,$ErrorAction) if($global:FixtureCase -eq 'worker'){[pscustomobject]@{Name='Runner.Worker'}}}
function Get-CimInstance {param($ClassName)
    if($global:FixtureCase -in @('registered','registered-other','missing-identity-files','ephemeral-retired','persistent-missing-runner')){[pscustomobject]@{Name='actions.runner.fixture';PathName=$global:FixtureNormalizedDirectory+'\bin\RunnerService.exe';State='Stopped'}}
    if($global:FixtureCase -in @('service-object','missing-named','registered-other')){[pscustomobject]@{Name='actions.runner.unrecorded';PathName=$global:FixtureNormalizedDirectory+'\RunnerService.exe';State='Stopped'}}
}
function Test-Path {param($LiteralPath,$PathType)
    $name=[IO.Path]::GetFileName($LiteralPath)
    if($name -eq '.service') {return $global:FixtureCase -in @('service-file','registered','missing-named','registered-other','ephemeral-retired','persistent-missing-runner')}
    if($global:FixtureCase -in @('missing-identity-files','ephemeral-retired','persistent-missing-runner')){return $false}
    return $name -in @('.runner','.credentials','.credentials_rsaparams')
}
function Get-Content {param($LiteralPath,[switch]$Raw) $name=[IO.Path]::GetFileName($LiteralPath);if($name -eq '.service'){return $(if($global:FixtureCase -eq 'service-file'){'actions.runner.unrecorded'}else{'actions.runner.fixture'})}; return $(if($global:FixtureCase -eq 'mismatch'){'{"agentId":999,"agentName":"fusion-ci-fixture"}'}else{'{"agentId":123,"agentName":"fusion-ci-fixture"}'})}
function Remove-Item {param($LiteralPath,[switch]$Force) if(-not $Force){throw 'Hidden fixture must require Force'}; $global:Removed.Add([IO.Path]::GetFileName($LiteralPath))}
$global:FixtureNormalizedDirectory=[IO.Path]::GetFullPath('C:\fixture').TrimEnd('\')
try {
  $output=. ([scriptblock]::Create($source))
  [ordered]@{probe='full-retirement-mocked';case=$Case;result='pass';removed=@($global:Removed);deleted_services=@($global:DeletedServices);output=($output|ConvertFrom-Json)}|ConvertTo-Json -Compress -Depth 4
} catch {
  [ordered]@{probe='full-retirement-mocked';case=$Case;result='error';removed=@($global:Removed);deleted_services=@($global:DeletedServices);message=$_.Exception.Message}|ConvertTo-Json -Compress
}
