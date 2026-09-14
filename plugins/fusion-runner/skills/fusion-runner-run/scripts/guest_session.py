"""Protected native SSH/SFTP for an explicitly configured Windows account.

Internal library used by the local Windows adapter. Requires pexpect 4.9.0
on the Mac. It has no VM discovery, installation, power, or registration side
effects. Access files stay private; passwords only enter a hidden SSH prompt.
"""
from __future__ import annotations

import base64
import ipaddress
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile
import time


class GuestError(RuntimeError):
    pass


def load_access(path):
    if path is None:
        raise GuestError("provide the owner-only access file from the configured image/access provider")
    path = Path(path)
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_mode & 0o077 or info.st_uid != os.getuid():
        raise GuestError("access file must be an owner-only regular file")
    data = json.loads(path.read_text(encoding="utf-8"))
    required = ("address", "username", "password", "host_public_key", "account_sid")
    if not isinstance(data, dict) or any(not isinstance(data.get(k), str) or not data[k] for k in required):
        raise GuestError("access file needs address, username, password, host_public_key and account_sid")
    if any(c in data["password"] for c in "\r\n\0"):
        raise GuestError("password cannot contain a terminal newline or NUL")
    # An observed IP avoids hostname resolution changing the selected guest.
    try:
        ipaddress.ip_address(data["address"])
    except ValueError:
        raise GuestError("access address must be the observed guest IP") from None
    if not re.fullmatch(r"[A-Za-z0-9_. @\\-]+", data["username"]):
        raise GuestError("unsupported account name")
    if not re.fullmatch(r"S-1-(?:\d+-)+\d+", data["account_sid"]):
        raise GuestError("invalid expected account SID")
    key = data["host_public_key"].split()
    if len(key) != 2 or key[0] not in ("ssh-ed25519", "ssh-rsa", "ecdsa-sha2-nistp256"):
        raise GuestError("provide one authenticated OpenSSH public host key")
    try:
        base64.b64decode(key[1], validate=True)
    except ValueError:
        raise GuestError("invalid host key encoding") from None
    port = data.get("port", 22)
    if type(port) is not int or not 1 <= port <= 65535:
        raise GuestError("invalid SSH port")
    return dict(data, port=port)


def ps_literal(value):
    if any(c in str(value) for c in "\r\n\0"):
        raise GuestError("a Windows resource path contains a control character")
    return "'" + str(value).replace("'", "''") + "'"


def sftp_quote(value):
    if any(c in str(value) for c in "\r\n\0"):
        raise GuestError("an SFTP resource path contains a control character")
    value = str(value).replace("\\", "/")
    if re.match(r"^[A-Za-z]:/", value):
        value = "/" + value
    for character in ('"', '*', '?', '[', ']'):
        value = value.replace(character, "\\" + character)
    return '"' + value + '"'


class SSH:
    def __init__(self, access):
        self.access = access
        self.temporary = None
        self.child = None

    def __enter__(self):
        import pexpect

        a = self.access
        self.temporary = tempfile.TemporaryDirectory(prefix="fusion-local-ssh-")
        root = Path(self.temporary.name)
        root.chmod(0o700)
        self.socket = root / "control"
        known = root / "known_hosts"
        host = a["address"] if a["port"] == 22 else f"[{a['address']}]:{a['port']}"
        known.write_text(f"{host} {a['host_public_key']}\n", encoding="utf-8")
        known.chmod(0o600)
        user = a["username"].replace("\\", "\\\\")
        self.options = [
            "-F", "/dev/null", "-o", "StrictHostKeyChecking=yes",
            "-o", f"UserKnownHostsFile={known}", "-o", "GlobalKnownHostsFile=/dev/null",
            "-o", "PreferredAuthentications=password", "-o", "PubkeyAuthentication=no",
            "-o", "NumberOfPasswordPrompts=1", "-o", "ForwardAgent=no",
            "-o", "ClearAllForwardings=yes", "-o", "ConnectTimeout=15",
            "-o", "ServerAliveInterval=10", "-o", "ServerAliveCountMax=2",
            "-o", f"ControlPath={self.socket}", "-o", f'User="{user}"',
            "-o", f"Port={a['port']}",
        ]
        self.child = pexpect.spawn("/usr/bin/ssh", self.options + ["-M", "-N", "-T", a["address"]],
                                   encoding="utf-8", timeout=20)
        entered = False
        deadline = time.monotonic() + 25
        try:
            while time.monotonic() < deadline:
                if self.socket.exists() and subprocess.run(
                    self._args("-O", "check"), capture_output=True, timeout=3, check=False
                ).returncode == 0:
                    return self
                event = self.child.expect_exact(["password: ", pexpect.EOF, pexpect.TIMEOUT], timeout=0.2)
                if event == 1:
                    # Vendor output can include account/configuration data.
                    raise GuestError("SSH authentication failed; verify the pinned guest identity and account access")
                if event == 0:
                    if entered or not self.child.waitnoecho(timeout=3):
                        raise GuestError("SSH did not provide a protected password prompt")
                    self.child.sendline(a["password"])
                    entered = True
            raise GuestError("SSH authentication exceeded its deadline")
        except BaseException:
            self.close()
            raise

    def _args(self, *options):
        return ["/usr/bin/ssh", *self.options, "-o", "BatchMode=yes", *options, self.access["address"]]

    def powershell(self, code, *, input_data=None, timeout=60):
        encoded = base64.b64encode(code.encode("utf-16le")).decode("ascii")
        command = "& 'C:\\Program Files\\PowerShell\\7\\pwsh.exe' -NoLogo -NoProfile -NonInteractive -EncodedCommand " + encoded + "; exit $LASTEXITCODE"
        return subprocess.run(self._args("-T") + [command], input=input_data,
                              capture_output=True, timeout=timeout, check=False)

    def copy(self, source, destination, *, download=False, timeout=120):
        operation = "get" if download else "put"
        completed = subprocess.run(
            ["/usr/bin/sftp", *self.options, "-o", "BatchMode=yes", "-b", "-", self.access["address"]],
            input=f"{operation} {sftp_quote(source)} {sftp_quote(destination)}\n".encode(),
            capture_output=True, timeout=timeout, check=False,
        )
        if completed.returncode:
            raise GuestError("SFTP transfer failed; the invocation is retained for inspection")

    def probe(self, architecture, *, require_idle=True):
        response = self.powershell(r"""
$ErrorActionPreference='Stop'
$id=[Security.Principal.WindowsIdentity]::GetCurrent()
$principal=[Security.Principal.WindowsPrincipal]::new($id)
[ordered]@{
  username=$id.Name; account_sid=$id.User.Value
  is_administrator=$principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
  os_arch=[Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString().ToUpperInvariant()
  process_arch=[Runtime.InteropServices.RuntimeInformation]::ProcessArchitecture.ToString().ToUpperInvariant()
  is_windows=$IsWindows; powershell=$PSVersionTable.PSVersion.ToString()
  work_root=(Join-Path ([Environment]::GetFolderPath('LocalApplicationData')) 'FusionLocalJobs')
  runner_processes=@(Get-Process -Name 'Runner.Listener','Runner.Worker' -ErrorAction SilentlyContinue).Count
  runner_services=@(Get-Service | Where-Object Name -like 'actions.runner.*').Count
  local_processes=@(Get-CimInstance Win32_Process -Filter "Name='pwsh.exe'" | Where-Object {$_.CommandLine -like '*FusionLocalJobs*command.ps1*'}).Count
} | ConvertTo-Json -Compress
""")
        if response.returncode:
            raise GuestError("Windows account probe failed")
        result = json.loads(response.stdout.decode("utf-8-sig"))
        if (result.get("account_sid") != self.access["account_sid"] or result.get("is_administrator") is not False
                or result.get("is_windows") is not True or result.get("os_arch") != architecture
                or result.get("process_arch") != architecture):
            raise GuestError("local execution requires the exact standard account and matching native Windows architecture")
        if require_idle and result.get("runner_processes") != 0:
            raise GuestError("a GitHub runner process is present; local execution requires an idle unregistered guest")
        if require_idle and result.get("runner_services") != 0:
            raise GuestError("a GitHub runner service is present; reconcile its registration before local execution")
        if require_idle and result.get("local_processes") != 0:
            raise GuestError("a previous local command is still running; inspect its invocation before starting another")
        return result

    def close(self):
        try:
            if self.child is not None and self.child.isalive():
                try:
                    if self.socket.exists():
                        subprocess.run(self._args("-O", "exit"), capture_output=True, timeout=5, check=False)
                finally:
                    self.child.close(force=True)
        finally:
            if self.temporary is not None:
                self.temporary.cleanup()

    def __exit__(self, *_):
        self.close()
