"""Run actual PowerShell semantics and mocked lifecycle inverse controls.

These checks need PowerShell 7 but do not pretend macOS mocks validate Windows
services. A Windows job still must verify actual service startup and retirement.
"""
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest


def test_windows_script_contracts():
    executable = os.environ.get('P45_PWSH') or shutil.which('pwsh')
    if not executable:
        pytest.skip('PowerShell 7 is unavailable; run with P45_PWSH pointing to its executable')
    result = subprocess.run([executable, '-NoLogo', '-NoProfile', '-NonInteractive',
                             '-File', str(Path(__file__).with_name('windows-helper-probes.ps1'))],
                            text=True, capture_output=True, timeout=60, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    rows = [json.loads(line) for line in result.stdout.splitlines() if line.startswith('{')]
    assert rows[-1] == {'probe': 'summary', 'parser_files': 3, 'selection_cases': 4,
                        'mode_cases': 5, 'retirement_cases': 15, 'service_cases': 4, 'failures': 0}


def test_retirement_path_guard_uses_real_directory_ancestors(tmp_path):
    executable = os.environ.get('P45_PWSH') or shutil.which('pwsh')
    if not executable:
        pytest.skip('PowerShell 7 is unavailable')
    directory = tmp_path / 'real' / 'child'
    directory.mkdir(parents=True)
    (directory / '.credentials').write_text('fixture')
    (tmp_path / 'redirect').symlink_to(directory, target_is_directory=True)
    source = Path(__file__).resolve().parents[1] / 'plugins/fusion-runner/skills/fusion-runner-run/scripts/retire_service.ps1'
    script = tmp_path / 'paths.ps1'
    script.write_text('''param($Source,$Root)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$tokens=$null;$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile($Source,[ref]$tokens,[ref]$errors)
$function=$ast.Find({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq 'Assert-PlainRunnerPath'},$true)
. ([scriptblock]::Create($function.Extent.Text))
Assert-PlainRunnerPath (Join-Path $Root 'real/child') $true
Assert-PlainRunnerPath (Join-Path $Root 'real/child/.credentials') $false
$refused=$false
try {Assert-PlainRunnerPath (Join-Path $Root 'redirect') $true} catch {$refused=$true}
if(-not $refused){throw 'Redirected directory was accepted'}
Write-Output 'normal-directory-and-file-pass; redirected-directory-refused'
''')
    result = subprocess.run([executable, '-NoLogo', '-NoProfile', '-NonInteractive', '-File',
                             str(script), str(source), str(tmp_path)], capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'normal-directory-and-file-pass; redirected-directory-refused' in result.stdout
