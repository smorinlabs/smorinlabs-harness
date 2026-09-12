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
                        'mode_cases': 5, 'retirement_cases': 12, 'service_cases': 4, 'failures': 0}
