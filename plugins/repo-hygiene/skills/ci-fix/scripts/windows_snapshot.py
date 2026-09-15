"""Capture current Git worktree bytes without copying Git credentials/history."""
from __future__ import annotations

import fnmatch
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import zipfile

MAX_BYTES = 256 * 1024 * 1024
MAX_FILES = 25000


class SnapshotError(ValueError):
    pass


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def relative_path(name):
    if not isinstance(name, str) or not name or "\\" in name or any(ord(c) < 32 for c in name):
        raise SnapshotError("unsupported Windows path in snapshot or specification")
    path = PurePosixPath(name)
    if path.is_absolute() or str(path) != name or any(p in (".", "..", ".git") for p in path.parts):
        raise SnapshotError("snapshot paths must be relative, canonical and outside .git")
    for part in path.parts:
        if part.endswith((".", " ")) or any(c in part for c in '<>:"|?*'):
            raise SnapshotError("a source path cannot be represented on Windows")
        if re.fullmatch(r"(?i)(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?", part) or part.casefold() == ".git":
            raise SnapshotError("a source path uses a reserved Windows name")
    return name


def git(root, *args):
    p = subprocess.run(["git", "-C", str(root), *args], capture_output=True, check=False, timeout=30)
    if p.returncode:
        raise SnapshotError("cannot inspect the selected Git worktree")
    return p.stdout


def file_names(root, excludes):
    root = Path(root).resolve()
    if Path(git(root, "rev-parse", "--show-toplevel").decode().strip()).resolve() != root:
        raise SnapshotError("repository must name the Git worktree root")
    names = set(git(root, "ls-files", "--cached", "--others", "--exclude-standard", "-z").decode().split("\0")) - {""}
    modes = {}
    for row in git(root, "ls-files", "--stage", "-z").decode().split("\0"):
        if row:
            header, name = row.split("\t", 1)
            mode, _, stage = header.split()
            if stage != "0":
                raise SnapshotError("resolve Git conflicts before capturing local execution")
            modes[name] = mode
    selected, excluded, seen = [], [], {}
    for name in sorted(names):
        if any(fnmatch.fnmatchcase(name, pattern) for pattern in excludes):
            excluded.append(name)
            continue
        relative_path(name)
        if modes.get(name) == "160000":
            raise SnapshotError("submodules need an explicit prepared snapshot; this adapter does not flatten them")
        path = root / name
        if not path.exists() and not path.is_symlink():
            continue  # A tracked worktree deletion must remain a deletion.
        for prefix in [PurePosixPath(name), *PurePosixPath(name).parents]:
            if str(prefix) == ".":
                continue
            normalized = str(prefix).casefold()
            if normalized in seen and seen[normalized] != str(prefix):
                raise SnapshotError("source paths collide on a case-insensitive Windows filesystem")
            seen[normalized] = str(prefix)
        for part in [path, *list(path.parents)[:len(PurePosixPath(name).parts)-1]]:
            if part.is_symlink():
                raise SnapshotError("symlink sources need a verified Windows equivalent")
        if not stat.S_ISREG(path.lstat().st_mode):
            raise SnapshotError("only regular source files are supported")
        selected.append(name)
    if not selected or len(selected) > MAX_FILES:
        raise SnapshotError("snapshot must contain between 1 and 25000 files")
    return selected, excluded


def contents(root, excludes):
    names, excluded = file_names(root, excludes)
    records, blobs, total = [], {}, 0
    for name in names:
        path = Path(root) / name
        before = path.stat()
        if before.st_size + total > MAX_BYTES:
            raise SnapshotError("snapshot exceeds the 256 MiB bound; narrow explicit source exclusions")
        with path.open("rb") as stream:
            value = stream.read(MAX_BYTES - total + 1)
        if total + len(value) > MAX_BYTES:
            raise SnapshotError("snapshot exceeds the 256 MiB bound")
        after = path.stat()
        if (before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_ino, after.st_size, after.st_mtime_ns):
            raise SnapshotError("source changed during capture; repeat snapshot planning")
        if value.startswith(b"version https://git-lfs.github.com/spec/v1\n"):
            raise SnapshotError("materialize Git LFS files before local execution")
        total += len(value)
        records.append({"path": name, "bytes": len(value), "sha256": hashlib.sha256(value).hexdigest()})
        blobs[name] = value
    return {"files": records, "excluded": excluded, "bytes": total}, blobs


def capture(root, destination, spec):
    excludes = spec.get("snapshot_exclude", [])
    manifest, blobs = contents(root, excludes)
    if contents(root, excludes)[0] != manifest:
        raise SnapshotError("source changed during snapshot capture")
    snapshot = dict(manifest, schema_version=1, snapshot_sha256=digest(manifest))
    with zipfile.ZipFile(destination, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, value in blobs.items():
            archive.writestr("source/" + name, value)
        archive.writestr("snapshot.json", json.dumps(snapshot, ensure_ascii=False))
        archive.writestr("spec.json", json.dumps(spec, ensure_ascii=False))
        # Match GitHub's pwsh run-step error/child-exit behavior.
        command = "$ErrorActionPreference='Stop'\n" + spec["command"] + "\n"
        command += "if (Test-Path -LiteralPath variable:\\LASTEXITCODE) { exit $LASTEXITCODE }\n"
        archive.writestr("command.ps1", command.encode("utf-8"))
    return snapshot


def matches(root, snapshot, excludes):
    try:
        return digest(contents(root, excludes)[0]) == snapshot["snapshot_sha256"]
    except (OSError, SnapshotError):
        return False
