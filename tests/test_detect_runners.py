"""tests/test_detect_runners.py — survey this machine for a way to run Linux CI steps.

detect_runners.py answers one question: when a `runs-on: ubuntu-*` job cannot
run on this host, what is already here that could run it? It is read-only —
it never starts a VM, pulls an image, or installs anything — and it ranks by
**readiness before fidelity**, because something already running costs nothing
to use, while the most faithful tool in the world is useless if it needs a
1 GB download first. When nothing is available it names the easiest thing to
install for this host rather than the best one.

Every probe runs against shim binaries on an isolated PATH, so the tests
describe the machine rather than depending on this one.
"""

import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "plugins/repo-hygiene/skills/ci-fix/scripts/detect_runners.py"

assert SCRIPT.is_file(), f"detect_runners.py not found at {SCRIPT}"

LIMA_STOPPED = json.dumps(
    {"name": "agent-fork", "status": "Stopped", "arch": "aarch64", "vmType": "vz"}
)
LIMA_RUNNING = json.dumps(
    {"name": "ubuntu", "status": "Running", "arch": "aarch64", "vmType": "vz"}
)


def shim(bin_dir, name, stdout="", code=0, stderr="", sleep=0):
    """An executable that fakes one tool's response."""
    bin_dir.mkdir(parents=True, exist_ok=True)
    p = bin_dir / name
    body = "#!/bin/sh\n"
    if sleep:
        # absolute path: PATH is the shim dir only, so a bare `sleep` is not found
        body += f"/bin/sleep {sleep}\n"
    for line in stdout.splitlines():
        body += f"printf '%s\\n' {json.dumps(line)}\n"
    if stderr:
        body += f"printf '%s\\n' {json.dumps(stderr)} >&2\n"
    body += f"exit {code}\n"
    p.write_text(body)
    p.chmod(0o755)
    return p


def run(bin_dir, *args, env=None, host_os="darwin", host_arch="arm64"):
    """PATH is the shim dir ONLY — prepending would let real binaries answer."""
    e = {
        "PATH": str(bin_dir),
        "HOME": str(bin_dir.parent),
        "CI_FIX_FAKE_OS": host_os,
        "CI_FIX_FAKE_ARCH": host_arch,
        **(env or {}),
    }
    return subprocess.run(
        [sys.executable, str(SCRIPT), *[str(a) for a in args]],
        capture_output=True,
        text=True,
        env=e,
        check=False,
    )


def detect(bin_dir, *args, **kw):
    out = run(bin_dir, "--json", *args, **kw)
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout)


def config(bin_dir, tmp_path, *args, **kw):
    """Render the TOML and parse it back, so the file itself is under test."""
    dest = tmp_path / "runners.toml"
    out = run(bin_dir, "--out", dest, *args, **kw)
    assert out.returncode == 0, out.stderr
    return tomllib.loads(dest.read_text()), dest


# ------------------------------------------------------------ nothing present


def test_a_bare_machine_recommends_the_easiest_install_not_the_best_tool(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    d = detect(bin_dir)
    assert d["preference"] == []
    assert d["recommended"] is None
    assert d["recommend_install"]["runner"] == "podman"
    assert "brew install podman" in d["recommend_install"]["command"]
    assert "easiest" in d["recommend_install"]["reason"].lower()
    assert all(r["readiness"] == "absent" for r in d["runners"].values())


def test_a_bare_linux_host_is_told_it_needs_no_vm(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    d = detect(bin_dir, host_os="linux", host_arch="x86_64")
    assert d["recommend_install"]["runner"] == "podman"
    assert "no virtual machine" in d["recommend_install"]["reason"].lower()
    assert "brew" not in d["recommend_install"]["command"]


# --------------------------------------------------- readiness beats fidelity


def test_a_running_docker_outranks_an_absent_act(tmp_path):
    bin_dir = tmp_path / "bin"
    shim(bin_dir, "docker", "29.5.2|aarch64|linux")
    d = detect(bin_dir)
    assert d["preference"][0] == "docker"
    assert d["recommended"]["runner"] == "docker"
    assert d["recommended"]["readiness"] == "ready"
    assert "already running" in d["recommended"]["reason"]
    assert d["runners"]["act"]["readiness"] == "absent"
    assert "recommend_install" not in d or d["recommend_install"] is None


def test_podman_leads_docker_when_both_are_ready(tmp_path):
    """Within one readiness tier the fidelity order decides, and podman leads
    the runtimes: rootless, no licence, same CLI as docker (owner, 2026-09-10)."""
    bin_dir = tmp_path / "bin"
    shim(bin_dir, "docker", "29.5.2|aarch64|linux")
    shim(bin_dir, "podman", "5.6.0|aarch64")
    d = detect(bin_dir)
    assert d["preference"] == ["podman", "docker"]
    assert d["recommended"]["runner"] == "podman"


def test_a_stopped_podman_and_a_stopped_docker_offer_podman_first(tmp_path):
    bin_dir = tmp_path / "bin"
    shim(bin_dir, "docker", "", code=1, stderr="Cannot connect to the Docker daemon")
    shim(bin_dir, "podman", "", code=125, stderr="Cannot connect to Podman")
    d = detect(bin_dir)
    assert d["recommend_start"]["runner"] == "podman"
    assert "podman machine start" in d["recommend_start"]["command"]


def test_act_leads_only_when_a_runtime_is_ready_for_it(tmp_path):
    bin_dir = tmp_path / "bin"
    shim(bin_dir, "act", "act version 0.2.90")
    shim(bin_dir, "docker", "29.5.2|aarch64|linux")
    d = detect(bin_dir)
    assert d["runners"]["act"]["readiness"] == "ready"
    assert d["preference"][:2] == ["act", "docker"]
    assert d["recommended"]["runner"] == "act"


def test_act_without_a_runtime_cannot_be_ready(tmp_path):
    """act drives a container runtime; alone it can run nothing."""
    bin_dir = tmp_path / "bin"
    shim(bin_dir, "act", "act version 0.2.90")
    d = detect(bin_dir)
    assert d["runners"]["act"]["readiness"] == "needs_start"
    assert "runtime" in d["runners"]["act"]["detail"]
    assert d["preference"] == []  # nothing is ready
    assert d["recommended"] is None


def test_a_ready_runner_outranks_a_stopped_one_whatever_the_fidelity_order(tmp_path):
    bin_dir = tmp_path / "bin"
    shim(bin_dir, "podman", "5.6.0|aarch64")
    shim(bin_dir, "docker", "", code=1, stderr="Cannot connect to the Docker daemon")
    shim(bin_dir, "limactl", LIMA_STOPPED)
    d = detect(bin_dir)
    assert d["runners"]["podman"]["readiness"] == "ready"
    assert d["runners"]["docker"]["readiness"] == "needs_start"
    assert d["runners"]["lima"]["readiness"] == "needs_start"
    assert d["preference"][0] == "podman"  # ready, though docker leads on fidelity
    assert d["recommended"]["runner"] == "podman"


def test_nothing_ready_but_something_installed_recommends_starting_it(tmp_path):
    bin_dir = tmp_path / "bin"
    shim(bin_dir, "limactl", LIMA_STOPPED)
    d = detect(bin_dir)
    assert d["preference"] == []
    assert d["recommended"] is None
    assert d["recommend_start"]["runner"] == "lima"
    assert "limactl start agent-fork" in d["recommend_start"]["command"]
    assert "recommend_install" not in d or d["recommend_install"] is None


# --------------------------------------------------------------- per-runner


def test_docker_reports_its_version_and_arch(tmp_path):
    bin_dir = tmp_path / "bin"
    shim(bin_dir, "docker", "29.5.2|aarch64|linux")
    r = detect(bin_dir)["runners"]["docker"]
    assert (
        r["readiness"] == "ready"
        and r["version"] == "29.5.2"
        and r["arch"] == "aarch64"
    )


def test_docker_present_but_daemon_down_names_the_start_command(tmp_path):
    bin_dir = tmp_path / "bin"
    shim(bin_dir, "docker", "", code=1, stderr="Cannot connect to the Docker daemon")
    r = detect(bin_dir)["runners"]["docker"]
    assert r["readiness"] == "needs_start"
    assert r["start_command"]
    assert "daemon" in r["detail"].lower()


def test_podman_without_a_machine_needs_a_start(tmp_path):
    bin_dir = tmp_path / "bin"
    shim(bin_dir, "podman", "", code=125, stderr="Cannot connect to Podman")
    r = detect(bin_dir)["runners"]["podman"]
    assert r["readiness"] == "needs_start"
    assert "podman machine start" in r["start_command"]


def test_lima_reads_jsonl_not_a_json_array(tmp_path):
    """limactl list --json emits one object per line; json.load would raise."""
    bin_dir = tmp_path / "bin"
    shim(bin_dir, "limactl", LIMA_STOPPED + "\n" + LIMA_RUNNING)
    r = detect(bin_dir)["runners"]["lima"]
    assert r["readiness"] == "ready"
    assert r["running_vm"] == "ubuntu"
    assert sorted(v["name"] for v in r["vms"]) == ["agent-fork", "ubuntu"]


def test_lima_with_only_stopped_vms_offers_the_cheapest_start(tmp_path):
    bin_dir = tmp_path / "bin"
    shim(bin_dir, "limactl", LIMA_STOPPED)
    r = detect(bin_dir)["runners"]["lima"]
    assert r["readiness"] == "needs_start"
    assert r["running_vm"] is None
    assert "limactl start agent-fork" in r["start_command"]


def test_lima_installed_with_no_vms_offers_to_create_one(tmp_path):
    bin_dir = tmp_path / "bin"
    shim(bin_dir, "limactl", "")
    r = detect(bin_dir)["runners"]["lima"]
    assert r["readiness"] == "needs_start"
    assert r["vms"] == []
    assert "template://ubuntu" in r["start_command"]


def test_devcontainer_is_surveyed_but_never_recommended_alone(tmp_path):
    bin_dir = tmp_path / "bin"
    shim(bin_dir, "devcontainer", "0.80.0")
    d = detect(bin_dir)
    assert d["runners"]["devcontainer"]["readiness"] == "needs_start"
    assert d["recommended"] is None


def test_a_hanging_probe_is_unavailable_not_a_hang(tmp_path):
    """`docker info` with Docker Desktop mid-shutdown hangs; every probe is bounded."""
    bin_dir = tmp_path / "bin"
    shim(bin_dir, "docker", "29.5.2|aarch64|linux", sleep=5)
    d = detect(bin_dir, "--probe-timeout", "1")
    assert d["runners"]["docker"]["readiness"] == "needs_start"
    assert "timed out" in d["runners"]["docker"]["detail"].lower()


# ------------------------------------------------------------------ the file


def test_toml_is_valid_and_carries_the_survey(tmp_path):
    bin_dir = tmp_path / "bin"
    shim(bin_dir, "docker", "29.5.2|aarch64|linux")
    shim(bin_dir, "limactl", LIMA_STOPPED)
    cfg, dest = config(bin_dir, tmp_path)
    assert cfg["schema"] == 1
    assert cfg["preference"] == ["docker"]
    assert cfg["host"]["os"] == "darwin" and cfg["host"]["arch"] == "arm64"
    assert cfg["recommended"]["runner"] == "docker"
    assert cfg["runners"]["docker"]["readiness"] == "ready"
    assert cfg["runners"]["lima"]["readiness"] == "needs_start"
    assert dest.read_text().startswith("#")  # a header explains how to regenerate it


def test_arch_note_fires_when_the_host_is_not_the_ci_arch(tmp_path):
    bin_dir = tmp_path / "bin"
    shim(bin_dir, "docker", "29.5.2|aarch64|linux")
    cfg, _ = config(bin_dir, tmp_path)
    assert cfg["host"]["ci_arch"] == "x86_64"
    assert "x86_64" in cfg["host"]["arch_note"]
    other = tmp_path / "x86"
    other.mkdir()
    cfg2, _ = config(
        bin_dir, other, host_arch="x86_64"
    )  # own path: a fresh file is reused by design
    assert cfg2["host"]["arch_note"] == ""


def test_a_fresh_file_is_reused_and_refresh_re_detects(tmp_path):
    bin_dir = tmp_path / "bin"
    shim(bin_dir, "docker", "29.5.2|aarch64|linux")
    _, dest = config(bin_dir, tmp_path)
    dest.write_text("# sentinel\nschema = 1\npreference = []\n")

    out = run(bin_dir, "--out", dest)
    assert out.returncode == 0
    assert "sentinel" in dest.read_text(), "a fresh file must be reused, not rewritten"

    out = run(bin_dir, "--out", dest, "--refresh")
    assert out.returncode == 0
    assert "sentinel" not in dest.read_text()
    assert tomllib.loads(dest.read_text())["preference"] == ["docker"]


def test_a_stale_file_is_re_detected_without_refresh(tmp_path):
    bin_dir = tmp_path / "bin"
    shim(bin_dir, "docker", "29.5.2|aarch64|linux")
    _, dest = config(bin_dir, tmp_path)
    dest.write_text("# sentinel\n")
    old = 60 * 60 * 48
    os.utime(dest, (dest.stat().st_atime - old, dest.stat().st_mtime - old))
    run(bin_dir, "--out", dest)
    assert "sentinel" not in dest.read_text()


def test_the_default_path_is_under_the_config_home(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    out = run(bin_dir, "path", env={"XDG_CONFIG_HOME": str(tmp_path / "cfg")})
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == str(tmp_path / "cfg" / "ci-fix" / "runners.toml")
    assert not (tmp_path / "cfg").exists(), "path must not write anything"


def test_detection_never_starts_anything(tmp_path):
    """The survey is read-only: a probe that mutates would show up here."""
    bin_dir = tmp_path / "bin"
    marker = tmp_path / "started"
    for name in ("docker", "podman", "limactl", "act"):
        shim(bin_dir, name, "", code=1)
    (bin_dir / "limactl").write_text(
        f'#!/bin/sh\ncase "$*" in *start*) : > {marker} ;; esac\nprintf "%s\\n" {json.dumps(LIMA_STOPPED)}\n'
    )
    (bin_dir / "limactl").chmod(0o755)
    detect(bin_dir)
    assert not marker.exists(), "detection must never start a VM"


# --------------------------------------------------------- the owner's choice


def test_a_pinned_runner_overrides_the_ranking_and_survives_refresh(tmp_path):
    """ "Can be recorded": a hand-written choice outranks the survey's own order."""
    bin_dir = tmp_path / "bin"
    shim(bin_dir, "docker", "29.5.2|aarch64|linux")
    shim(bin_dir, "podman", "5.6.0|aarch64")
    cfg, dest = config(bin_dir, tmp_path)
    assert cfg["recommended"]["runner"] == "podman"  # the default order

    dest.write_text(dest.read_text().replace('pinned = ""', 'pinned = "docker"'))
    out = run(bin_dir, "--out", dest, "--refresh")
    assert out.returncode == 0, out.stderr
    cfg = tomllib.loads(dest.read_text())
    assert cfg["pinned"] == "docker", "the pin must survive a re-survey"
    assert cfg["recommended"]["runner"] == "docker"
    assert "pinned in runners.toml" in cfg["recommended"]["reason"]


def test_a_pin_on_something_not_ready_is_reported_not_silently_ignored(tmp_path):
    bin_dir = tmp_path / "bin"
    shim(bin_dir, "docker", "29.5.2|aarch64|linux")
    shim(bin_dir, "podman", "", code=125, stderr="Cannot connect to Podman")
    _, dest = config(bin_dir, tmp_path)
    dest.write_text(dest.read_text().replace('pinned = ""', 'pinned = "podman"'))
    run(bin_dir, "--out", dest, "--refresh")
    cfg = tomllib.loads(dest.read_text())
    assert cfg["pinned_unavailable"]["runner"] == "podman"
    assert "podman machine start" in cfg["pinned_unavailable"]["start_command"]
    assert cfg["recommended"]["runner"] == "docker"  # falls through to what is ready
