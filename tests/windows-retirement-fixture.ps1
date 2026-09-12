[CmdletBinding()]
param([Parameter(Mandatory)][string]$PublicCheckout,[ValidateSet('partial','mismatch','worker','service-file','service-object')][string]$Case)
$global:FixtureCase=$Case
$global:Removed=[Collections.Generic.List[string]]::new()
function Get-Process {param($Name,$ErrorAction) if($global:FixtureCase -eq 'worker'){[pscustomobject]@{Name='Runner.Worker'}}}
function Get-CimInstance {param($ClassName) if($global:FixtureCase -eq 'service-object'){[pscustomobject]@{Name='actions.runner.unrecorded';PathName=$global:FixtureNormalizedDirectory+'\RunnerService.exe';State='Stopped'}}}
function Test-Path {param($LiteralPath,$PathType) $name=[IO.Path]::GetFileName($LiteralPath); if($name -eq '.service') {return $global:FixtureCase -eq 'service-file'};return $name -in @('.runner','.credentials','.credentials_rsaparams')}
function Get-Content {param($LiteralPath,[switch]$Raw) $name=[IO.Path]::GetFileName($LiteralPath);if($name -eq '.service'){return 'actions.runner.unrecorded'}; return $(if($global:FixtureCase -eq 'mismatch'){'{"agentId":999,"agentName":"fusion-ci-fixture"}'}else{'{"agentId":123,"agentName":"fusion-ci-fixture"}'})}
function Remove-Item {param($LiteralPath,[switch]$Force) if(-not $Force){throw 'Hidden fixture must require Force'}; $global:Removed.Add([IO.Path]::GetFileName($LiteralPath))}
$global:FixtureNormalizedDirectory=[IO.Path]::GetFullPath('C:\fixture').TrimEnd('\')
try {
  $output=. (Join-Path $PublicCheckout "plugins/fusion-runner/skills/fusion-runner-run/scripts/retire_service.ps1")
  [ordered]@{probe='full-retirement-mocked';case=$Case;result='pass';removed=@($global:Removed);output=($output|ConvertFrom-Json)}|ConvertTo-Json -Compress -Depth 4
} catch {
  [ordered]@{probe='full-retirement-mocked';case=$Case;result='error';removed=@($global:Removed);message=$_.Exception.Message}|ConvertTo-Json -Compress
}
