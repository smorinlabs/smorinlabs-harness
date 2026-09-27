#!/usr/bin/env python3
"""Configuration for dependabot-sweep, Slice 4.

Resolves the run's scope, mode, repair permissions, and budgets with the
precedence flags > environment > config file > built-in defaults (CLI
Design Standard R5.1). The environment exposes a curated subset only
(DEPENDABOT_SWEEP_CONFIG, DEPENDABOT_SWEEP_STORE, DEPENDABOT_SWEEP_OUTPUT;
R5.4). An explicit --config path replaces discovery (R5.2). Every value
records where it came from, so `run view` can show the origin.

Defaults reproduce the pre-Slice-4 behavior exactly: automated mode with
every repair permitted when auto_fix is true, an unbounded run, a 600 s
observation window, a 20 s poll floor that is never lowered, and a
staleness bound equal to the per-PR budget.

Stdlib only (tomllib).
"""

from __future__ import annotations

import os
import sys
import tomllib
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sweep_protocol import FORBIDDEN_REPAIRS, MODES, REPAIRS, resolve_mode  # noqa: E402

TOOL_ENV_PREFIX = "DEPENDABOT_SWEEP_"
DEFAULT_DIRNAME = "dependabot-sweep"
DEFAULT_FILENAME = "config.toml"  # kept for existing users; see conformance note
SUPPORTED_HOSTS = frozenset({"github"})
SUPPORTED_TOOLS = frozenset({"gh"})
VISIBILITIES = frozenset({"all", "public", "private"})
POLL_FLOOR_MIN_SECS = 20

DEFAULTS_KEYS = ("host", "tool", "auto_fix", "pause_on_conflict", "mode",
                 "repairs", "reviewer_contexts")
BUDGET_KEYS = ("op_timeout_secs", "pr_budget_secs", "run_budget_secs",
               "observation_window_secs", "poll_floor_secs",
               "stale_after_secs")
SCOPE_KEYS = ("visibility", "repos") + DEFAULTS_KEYS[2:]
TOP_LEVEL_KEYS = ("defaults", "budgets", "org", "user")

BUILTIN = {
    "host": "github", "tool": "gh", "auto_fix": True,
    "pause_on_conflict": False, "mode": "automated",
    "repairs": sorted(REPAIRS), "reviewer_contexts": [],
    "op_timeout_secs": 30, "pr_budget_secs": 600, "run_budget_secs": 0,
    "observation_window_secs": 600, "poll_floor_secs": POLL_FLOOR_MIN_SECS,
}


class ConfigError(ValueError):
    """A configuration problem the operator must fix. `code` is the stable
    machine-readable error code (R7.8)."""

    def __init__(self, message: str, code: str = "config_invalid") -> None:
        super().__init__(message)
        self.code = code


@dataclass
class Scope:
    """One sweep scope: a GitHub org or user (by visibility or repo list),
    or an explicit owner/repo list from --repo."""

    kind: str  # org | user | repo
    login: str
    visibility: str = "all"
    repos: list = field(default_factory=list)
    overrides: dict = field(default_factory=dict)


@dataclass
class ScopeConfig:
    """The effective behavior for one scope after its overrides."""

    login: str
    mode: str
    auto_fix: bool
    pause_on_conflict: bool
    repairs: list
    reviewer_contexts: list
    visibility: str
    repos: list


@dataclass
class RunConfig:
    host: str
    tool: str
    mode: str
    auto_fix: bool
    pause_on_conflict: bool
    repairs: list
    reviewer_contexts: list
    op_timeout_secs: int
    pr_budget_secs: int
    run_budget_secs: int
    observation_window_secs: int
    poll_floor_secs: int
    stale_after_secs: int
    scopes: list
    config_path: str = ""
    origin: dict = field(default_factory=dict)
    _flags: dict = field(default_factory=dict, repr=False)

    def scope_for(self, login: str) -> ScopeConfig:
        scope = next((s for s in self.scopes if s.login == login), None)
        if scope is None:
            raise ConfigError(f"scope {login!r} is not configured", "not_found")
        over = scope.overrides
        auto_fix = self.auto_fix if "auto_fix" not in over else bool(over["auto_fix"])
        mode_cfg = over.get("mode", self.mode if self.origin.get("mode") != "default" else BUILTIN["mode"])
        if "mode" in over:
            _check_mode(over["mode"], f'[{scope.kind}."{login}"]')
        mode = _resolve(auto_fix, self._flags, mode_cfg)
        repairs = (_check_repairs(over["repairs"], f'[{scope.kind}."{login}"]')
                   if "repairs" in over else list(self.repairs))
        return ScopeConfig(
            login=login, mode=mode, auto_fix=auto_fix,
            pause_on_conflict=bool(over.get("pause_on_conflict",
                                            self.pause_on_conflict)),
            repairs=repairs,
            reviewer_contexts=list(over.get("reviewer_contexts",
                                            self.reviewer_contexts)),
            visibility=scope.visibility, repos=list(scope.repos))

    def to_authority(self, helper_path: str = "") -> dict:
        """The run-level authority `run create` stores on the header and
        every later command reads back, so no invocation re-derives it."""
        return {
            "mode": self.mode, "repairs": list(self.repairs),
            "approved": [], "holds": [],
            "reviewer_contexts": list(self.reviewer_contexts),
            "pause_on_conflict": self.pause_on_conflict,
            "op_timeout_secs": self.op_timeout_secs,
            "pr_budget_secs": self.pr_budget_secs,
            "run_budget_secs": self.run_budget_secs,
            "observation_window_secs": self.observation_window_secs,
            "poll_floor_secs": self.poll_floor_secs,
            "stale_after_secs": self.stale_after_secs,
            "helper_path": helper_path,
        }


def default_config_path(env: dict) -> str:
    """$XDG_CONFIG_HOME/dependabot-sweep/config.toml, falling back to
    ~/.config (R5.3)."""
    base = env.get("XDG_CONFIG_HOME") or os.path.join(
        env.get("HOME") or os.path.expanduser("~"), ".config")
    return os.path.join(base, DEFAULT_DIRNAME, DEFAULT_FILENAME)


def _check_keys(table: dict, allowed, where: str) -> None:
    unknown = sorted(set(table) - set(allowed))
    if unknown:
        raise ConfigError(f"{where}: unknown key(s) {', '.join(unknown)}; "
                          f"expected any of {', '.join(allowed)}")


def _check_mode(value, where: str) -> str:
    if value not in MODES:
        raise ConfigError(f"{where}: mode must be one of {', '.join(MODES)}, "
                          f"not {value!r}")
    return value


def _check_repairs(value, where: str) -> list:
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        raise ConfigError(f"{where}: repairs must be a list of strings")
    forbidden = FORBIDDEN_REPAIRS & set(value)
    if forbidden:
        raise ConfigError(f"{where}: repairs {sorted(forbidden)} are never a "
                          f"worker repair")
    unknown = set(value) - REPAIRS
    if unknown:
        raise ConfigError(f"{where}: unknown repairs {sorted(unknown)}; "
                          f"expected any of {', '.join(sorted(REPAIRS))}")
    return sorted(set(value))


def _check_int(value, key: str, minimum: int, where: str = "[budgets]") -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ConfigError(f"{where}: {key} must be an integer >= {minimum}, "
                          f"not {value!r}")
    return value


def _resolve(auto_fix: bool, flags: dict, mode_cfg: str) -> str:
    """One mapping only: flags and config feed `resolve_mode`."""
    return resolve_mode(auto_fix=auto_fix and mode_cfg != "inspect",
                        check=bool(flags.get("check")),
                        gated=(mode_cfg == "gated"))


def _scopes_from_flags(flags: dict) -> list:
    scopes = []
    for login in flags.get("org") or []:
        scopes.append(Scope("org", login))
    by_owner: dict = {}
    for spec in flags.get("repo") or []:
        owner, sep, name = spec.partition("/")
        if not sep or not owner or not name or "/" in name:
            raise ConfigError(f"--repo expects owner/name, not {spec!r}")
        by_owner.setdefault(owner, []).append(name)
    for owner, names in by_owner.items():
        scopes.append(Scope("repo", owner, repos=names))
    return scopes


def _scopes_from_config(data: dict) -> list:
    scopes = []
    for kind in ("org", "user"):
        for login, table in (data.get(kind) or {}).items():
            where = f'[{kind}."{login}"]'
            if not isinstance(table, dict):
                raise ConfigError(f"{where}: expected a table")
            _check_keys(table, SCOPE_KEYS, where)
            visibility = table.get("visibility", "all")
            if visibility not in VISIBILITIES:
                raise ConfigError(f"{where}: visibility must be one of "
                                  f"{', '.join(sorted(VISIBILITIES))}")
            scopes.append(Scope(
                kind, login, visibility=visibility,
                repos=list(table.get("repos") or []),
                overrides={k: table[k] for k in DEFAULTS_KEYS[2:]
                           if k in table}))
    return scopes


def load_config(path: str | None, flags: dict | None,
                env: dict | None) -> RunConfig:
    """Resolve the run configuration.

    `path` or `flags["config"]` or DEPENDABOT_SWEEP_CONFIG names the sole
    config file; otherwise the XDG default is discovered. A missing
    discovered file is fine when --org/--repo supply the scope; a missing
    explicit file is an error. Flags beat the file; the file beats the
    built-in defaults.
    """
    flags = dict(flags or {})
    env = dict(env or {})
    explicit = path or flags.get("config") or env.get(TOOL_ENV_PREFIX + "CONFIG")
    resolved = explicit or default_config_path(env)
    data: dict = {}
    config_path = ""
    if os.path.exists(resolved):
        try:
            with open(resolved, "rb") as handle:
                data = tomllib.load(handle)
        except tomllib.TOMLDecodeError as exc:
            raise ConfigError(f"{resolved}: {exc}") from exc
        config_path = resolved
    elif explicit:
        raise ConfigError(f"config file {resolved!r} not found", "not_found")
    _check_keys(data, TOP_LEVEL_KEYS, resolved if config_path else "config")
    defaults = data.get("defaults") or {}
    budgets = data.get("budgets") or {}
    _check_keys(defaults, DEFAULTS_KEYS, "[defaults]")
    _check_keys(budgets, BUDGET_KEYS, "[budgets]")

    origin: dict = {}

    def pick(key: str, table: dict):
        if key in table:
            origin[key] = "config"
            return table[key]
        origin[key] = "default"
        return BUILTIN[key]

    host = pick("host", defaults)
    if host not in SUPPORTED_HOSTS:
        raise ConfigError(f"host {host!r} is not supported in v1 (github "
                          f"only)", "unsupported_host")
    tool = pick("tool", defaults)
    if tool not in SUPPORTED_TOOLS:
        raise ConfigError(f"tool {tool!r} is not supported in v1 (gh only)",
                          "unsupported_tool")

    auto_fix = bool(pick("auto_fix", defaults))
    if flags.get("no_auto_fix"):
        auto_fix, origin["auto_fix"] = False, "flag"
    pause = bool(pick("pause_on_conflict", defaults))
    if "pause_on_conflict" in flags and flags["pause_on_conflict"] is not None:
        pause, origin["pause_on_conflict"] = bool(flags["pause_on_conflict"]), "flag"
    mode_cfg = _check_mode(pick("mode", defaults), "[defaults]")
    if flags.get("mode"):
        mode_cfg, origin["mode"] = _check_mode(flags["mode"], "--mode"), "flag"
    if flags.get("check") or flags.get("no_auto_fix"):
        origin["mode"] = "flag"
    elif origin["mode"] == "default" and origin["auto_fix"] == "config":
        origin["mode"] = "config"
    mode = _resolve(auto_fix, flags, mode_cfg)

    repairs = (_check_repairs(defaults["repairs"], "[defaults]")
               if "repairs" in defaults else list(BUILTIN["repairs"]))
    origin["repairs"] = "config" if "repairs" in defaults else "default"
    reviewers = pick("reviewer_contexts", defaults)
    if not isinstance(reviewers, list) or not all(isinstance(r, str)
                                                    for r in reviewers):
        raise ConfigError("[defaults]: reviewer_contexts must be a list of "
                          "strings")

    op_timeout = _check_int(pick("op_timeout_secs", budgets),
                            "op_timeout_secs", 1)
    pr_budget = _check_int(pick("pr_budget_secs", budgets), "pr_budget_secs", 1)
    run_budget = _check_int(pick("run_budget_secs", budgets),
                            "run_budget_secs", 0)
    window = _check_int(pick("observation_window_secs", budgets),
                        "observation_window_secs", 1)
    poll_floor = _check_int(pick("poll_floor_secs", budgets),
                            "poll_floor_secs", 1)
    if poll_floor < POLL_FLOOR_MIN_SECS:
        poll_floor, origin["poll_floor_secs"] = POLL_FLOOR_MIN_SECS, "clamped"
    if "stale_after_secs" in budgets:
        stale = _check_int(budgets["stale_after_secs"], "stale_after_secs", 0)
        origin["stale_after_secs"] = "config"
    else:
        stale, origin["stale_after_secs"] = pr_budget, "default"

    scopes = _scopes_from_flags(flags)
    if scopes:
        origin["scopes"] = "flag"
    else:
        scopes = _scopes_from_config(data)
        origin["scopes"] = "config"
    if not scopes:
        raise ConfigError("no scope: pass --org or --repo, or configure an "
                          "[org.\"<login>\"] or [user.\"<login>\"] table",
                          "no_scope")

    return RunConfig(
        host=host, tool=tool, mode=mode, auto_fix=auto_fix,
        pause_on_conflict=pause, repairs=repairs,
        reviewer_contexts=list(reviewers), op_timeout_secs=op_timeout,
        pr_budget_secs=pr_budget, run_budget_secs=run_budget,
        observation_window_secs=window, poll_floor_secs=poll_floor,
        stale_after_secs=stale, scopes=scopes, config_path=config_path,
        origin=origin, _flags=flags)
