#!/usr/bin/env python3
"""dependabot-sweep orchestrator CLI, Slice 4.

The commands the sweep skill runs to create a run, schedule worker
attempts, render their briefs, collect outcome records, reconcile after a
restart, observe and evaluate one PR read-only, and render the report and
approval set. Noun-verb per the CLI Design Standard v1.4.14 (minimal tier;
see references/cli-interface.md and references/cli-conformance.md).

This CLI never merges and never mutates GitHub. Merges belong to the
worker's transport (gh_merge.py or pr-merge-flow); `pr observe` only reads.

Exit codes: 0 success, 1 runtime error, 2 usage, 3 not found, 4
authentication required, 5 precondition failed, 130 interrupted.

Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gh_merge  # noqa: E402
import sweep_config as cfg  # noqa: E402
import sweep_coordinator as coord  # noqa: E402
import sweep_evaluator as ev  # noqa: E402
import sweep_observe as observe  # noqa: E402
import sweep_patience as patience  # noqa: E402
import sweep_protocol as proto  # noqa: E402
import sweep_report as report  # noqa: E402
from sweep_core import (  # noqa: E402
    LeaseError, State, Store, StoreError, TransitionError, utc_now,
)

TOOL = "dependabot-sweep"
SCRIPTS_DIR = Path(__file__).resolve().parent
HELPER_PATH = str(SCRIPTS_DIR / "gh_merge.py")
# scripts/ -> dependabot-sweep/ -> skills/ -> repo-hygiene/.claude-plugin
PLUGIN_JSON = SCRIPTS_DIR.parents[2] / ".claude-plugin" / "plugin.json"
ENV_STORE = cfg.TOOL_ENV_PREFIX + "STORE"
ENV_SESSION = cfg.TOOL_ENV_PREFIX + "SESSION"
ENV_OUTPUT = cfg.TOOL_ENV_PREFIX + "OUTPUT"
TARGET_RE = re.compile(r"^([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)#(\d+)$")

EXIT_OK, EXIT_ERROR, EXIT_USAGE, EXIT_NOT_FOUND = 0, 1, 2, 3
EXIT_AUTH, EXIT_CONFLICT, EXIT_INTERRUPT = 4, 5, 130


def version() -> str:
    try:
        with open(PLUGIN_JSON, encoding="utf-8") as handle:
            return str(json.load(handle)["version"])
    except (OSError, ValueError, KeyError):
        return "0.0.0+unknown"


class CliError(Exception):
    """A failure with a stable machine-readable code and exit status."""

    def __init__(self, message: str, code: str = "error",
                 exit_code: int = EXIT_ERROR) -> None:
        super().__init__(message)
        self.code, self.exit_code = code, exit_code


class UsageError(Exception):
    def __init__(self, message: str, parser: argparse.ArgumentParser) -> None:
        super().__init__(message)
        self.parser = parser


class Formatter(argparse.RawDescriptionHelpFormatter):
    """Help in the standard's structure (R7.5): a `Usage:` line, then
    sections, then examples from the epilog."""

    def _format_usage(self, usage, actions, groups, prefix):
        return super()._format_usage(usage, actions, groups,
                                     "Usage: " if prefix is None else prefix)


class Parser(argparse.ArgumentParser):
    """argparse with the standard's MUSTs: no prefix abbreviation (R3.10)
    and usage errors that the caller renders (R7.8, R7.9)."""

    def __init__(self, *args, **kwargs) -> None:
        kwargs.setdefault("allow_abbrev", False)
        kwargs.setdefault("formatter_class", Formatter)
        super().__init__(*args, **kwargs)

    def error(self, message: str) -> None:  # type: ignore[override]
        raise UsageError(message, self)


def _output_options(parser: argparse.ArgumentParser, root: bool) -> None:
    default = None if root else argparse.SUPPRESS
    parser.add_argument("-o", "--output", choices=("table", "json"),
                        default=default, metavar="FORMAT",
                        help="output format: table (default) or json")
    parser.add_argument("--json", action="store_true", default=default,
                        help="shorthand for --output json")


def build_parser() -> Parser:
    root = Parser(
        prog=TOOL,
        description=f"{TOOL}: orchestrate one Dependabot sweep run from a "
                    f"durable record store. Never merges.",
        epilog="Examples:\n"
               f"  {TOOL} --store run.jsonl run create --run-id RUN-01 "
               "--file discoveries.json\n"
               f"  {TOOL} --store run.jsonl attempt create --model sol -o json\n"
               f"  {TOOL} --store run.jsonl brief view AGT-001.1\n"
               f"  {TOOL} pr observe acme/web#12 -o json | "
               f"{TOOL} pr evaluate acme/web#12 --file - --mode inspect")
    root.add_argument("-V", "--version", action="store_true",
                      help="print version and exit")
    root.add_argument("-v", "--verbose", action="count", default=0,
                      help="more diagnostics on stderr (repeatable)")
    root.add_argument("-q", "--quiet", action="store_true",
                      help="suppress non-essential diagnostics")
    root.add_argument("--debug", action="store_true",
                      help="maximum diagnostics, including tracebacks")
    root.add_argument("--config", metavar="PATH",
                      help="config file; replaces discovery "
                           f"(default $XDG_CONFIG_HOME/{cfg.DEFAULT_DIRNAME}/"
                           f"{cfg.DEFAULT_FILENAME}, env "
                           f"{cfg.TOOL_ENV_PREFIX}CONFIG)")
    root.add_argument("--store", metavar="PATH",
                      help=f"the run's JSONL record store (env {ENV_STORE})")
    root.add_argument("--session", metavar="ID",
                      help=f"this coordinator session's id (env {ENV_SESSION})")
    _output_options(root, root=True)
    nouns = root.add_subparsers(dest="noun", metavar="<noun>")

    def noun(name: str, help_text: str):
        parser = nouns.add_parser(name, help=help_text, allow_abbrev=False,
                                  formatter_class=Formatter)
        return parser, parser.add_subparsers(dest="verb", metavar="<verb>")

    def verb(verbs, name: str, help_text: str, examples: str):
        parser = verbs.add_parser(
            name, help=help_text, description=help_text,
            epilog="Examples:\n" + examples, allow_abbrev=False,
            formatter_class=Formatter)
        _output_options(parser, root=False)
        return parser

    _, run_verbs = noun("run", "the sweep run: create, view, describe, "
                               "reconcile, finish")
    p = verb(run_verbs, "create",
             "Create a run: header, authority from config, one card per "
             "discovered PR.",
             f"  {TOOL} --store run.jsonl run create --run-id RUN-01 "
             "--file discoveries.json\n"
             f"  gh search prs --app dependabot --state open --owner acme "
             f"--json number,title,url,repository | {TOOL} --store run.jsonl "
             "run create --run-id RUN-01 --file -")
    p.add_argument("--run-id", required=True, help="stable run identifier")
    p.add_argument("--file", required=True, metavar="PATH",
                   help="discoveries as JSON (coordinator shape or gh search "
                        "--json output); - reads stdin")
    p.add_argument("--mode", choices=tuple(proto.MODES),
                   help="override configured modes; auto_fix=false or "
                        "--no-auto-fix still forces inspect")
    p.add_argument("--no-auto-fix", action="store_true",
                   help="triage only: inspect mode, no repair, no merge")
    p.add_argument("--pause-on-conflict", action="store_true", default=None,
                   help="override configured pause settings: stop a "
                        "repository at its first conflict")
    p.add_argument("--evolving", action="store_true",
                   help="evolving backlog: later arrivals join the scope")
    p.add_argument("--cutoff", metavar="ISO8601",
                   help="discovery instant (default: now)")
    p.add_argument("--authorization", metavar="TEXT",
                   help="the user's authorizing words or record id")
    verb(run_verbs, "view", "Show the run header, counts, and authority.",
         f"  {TOOL} --store run.jsonl run view -o json")
    verb(run_verbs, "describe", "Render the full report from the store.",
         f"  {TOOL} --store run.jsonl run describe")
    p = verb(run_verbs, "reconcile",
             "Reconcile dead attempts and quarantined repositories against "
             "fresh observations before any new mutation.",
             f"  {TOOL} --store run.jsonl run reconcile --file observed.json "
             "--live AGT-001.1")
    p.add_argument("--file", required=True, metavar="PATH",
                   help='JSON {card id: {"merged": bool|null, "commit", '
                        '"at"}}; - reads stdin')
    p.add_argument("--live", action="append", default=[], metavar="ATTEMPT",
                   help="attempt id known to still run (repeatable)")
    p = verb(run_verbs, "finish",
             "Record the stop reason and the one explicit continuation.",
             f"  {TOOL} --store run.jsonl run finish --continuation none\n"
             f"  {TOOL} --store run.jsonl run finish --continuation scheduled "
             "--ref cron:sweep-nightly --verified-at 2026-09-22T18:00:00Z")
    p.add_argument("--continuation", required=True,
                   choices=patience.CONTINUATION_KINDS)
    p.add_argument("--ref", default="", help="watcher or invocation reference")
    p.add_argument("--verified-at", default="", metavar="ISO8601",
                   help="when the continuation was verified running")
    p.add_argument("--discovery-incomplete", action="store_true",
                   help="discovery capped out; the run is incomplete")

    _, attempt_verbs = noun("attempt", "worker attempts: create (schedule), "
                                       "collect (outcome records)")
    p = verb(attempt_verbs, "create",
             "Expire dead work, then issue one tasking per free repository.",
             f"  {TOOL} --store run.jsonl attempt create --model sol -o json\n"
             f"  {TOOL} --store run.jsonl attempt create --wake PR-004")
    p.add_argument("--model", default="", help="worker model label")
    p.add_argument("--wake", action="append", default=[], metavar="CARD",
                   help="hold card whose resume trigger fired (repeatable)")
    p = verb(attempt_verbs, "collect",
             "Apply one worker's outcome records; the whole batch is "
             "validated before any record changes.",
             f"  {TOOL} --store run.jsonl attempt collect AGT-001.1 --file "
             "outcomes.jsonl")
    p.add_argument("attempt_id", metavar="ATTEMPT")
    p.add_argument("--file", required=True, metavar="PATH",
                   help="outcome records as JSON lines; - reads stdin")

    _, brief_verbs = noun("brief", "the rendered worker brief")
    p = verb(brief_verbs, "view", "Render an attempt's brief from the "
                                  "template and the run's authority.",
             f"  {TOOL} --store run.jsonl brief view AGT-001.1")
    p.add_argument("attempt_id", metavar="ATTEMPT")
    p.add_argument("--progress-log", metavar="PATH",
                   help="helper progress log (default <store>.progress.log)")

    _, card_verbs = noun("card", "PR cards in the store")
    verb(card_verbs, "list", "List every card with state and reason.",
         f"  {TOOL} --store run.jsonl card list -o json")
    p = verb(card_verbs, "view", "Show one card.",
             f"  {TOOL} --store run.jsonl card view PR-003")
    p.add_argument("card_id", metavar="CARD")

    _, pr_verbs = noun("pr", "one pull request on GitHub, read-only")
    p = verb(pr_verbs, "observe",
             "Fetch one full observation (pull, files, reviews, threads, "
             "checks, suites, statuses, queue, policy). Read-only.",
             f"  {TOOL} pr observe acme/web#12 -o json > obs.json\n"
             f"  {TOOL} --store run.jsonl pr observe PR-003 -o json")
    p.add_argument("target", metavar="TARGET",
                   help="card id (with --store) or owner/repo#number")
    p = verb(pr_verbs, "evaluate",
             "Run the five checks on an observation and print the outcome "
             "record a worker would return.",
             f"  {TOOL} pr evaluate acme/web#12 --file obs.json "
             "--dependency-only --classifier alice --mode inspect\n"
             f"  {TOOL} --store run.jsonl pr evaluate PR-003 --file obs.json "
             "--attempt AGT-001.1 --dependency-only")
    p.add_argument("target", metavar="TARGET",
                   help="card id (with --store) or owner/repo#number")
    p.add_argument("--file", required=True, metavar="PATH",
                   help="observation JSON from `pr observe -o json`; - reads "
                        "stdin")
    p.add_argument("--dependency-only", action="store_true",
                   help="attest that the diff is dependency-only; recorded "
                        "as a receipt bound to this head and file set")
    p.add_argument("--classifier", default="operator",
                   help="who makes the attestation (default operator)")
    p.add_argument("--mode", choices=tuple(proto.MODES),
                   help="authority mode when no store is given "
                        "(default inspect)")
    p.add_argument("--attempt", metavar="ATTEMPT",
                   help="the attempt holding the repository lease")
    p.add_argument("--reviewer-context", action="append", default=[],
                   metavar="CONTEXT",
                   help="status context of a reviewer bot (repeatable)")

    _, approval_verbs = noun("approval", "owner decisions")
    verb(approval_verbs, "list", "Render the approval set: every NEEDS_OWNER "
                                 "card, most consequential first.",
         f"  {TOOL} --store run.jsonl approval list")
    return root


# --- Context and helpers -----------------------------------------------------

class Context:
    def __init__(self, args: argparse.Namespace, argv: list) -> None:
        self.args = args
        self.machine = _machine_requested(args, argv)
        self.quiet = bool(args.quiet) and not args.debug
        self.store_path = args.store or os.environ.get(ENV_STORE, "")
        self.session = args.session or os.environ.get(ENV_SESSION, "")
        self.config_path = args.config

    def emit(self, data, human: str) -> None:
        if self.machine:
            sys.stdout.write(json.dumps(data, indent=2, sort_keys=True) + "\n")
        else:
            sys.stdout.write(human if human.endswith("\n") else human + "\n")

    def note(self, text: str) -> None:
        if not self.quiet:
            sys.stderr.write(text.rstrip("\n") + "\n")

    def store(self) -> Store:
        if not self.store_path:
            raise CliError(f"--store PATH (or {ENV_STORE}) is required for "
                           f"this command", "usage", EXIT_USAGE)
        if not os.path.exists(self.store_path):
            raise CliError(f"store {self.store_path!r} not found",
                           "not_found", EXIT_NOT_FOUND)
        return Store.load(self.store_path, session=self.session)


def _machine_requested(args: argparse.Namespace, argv: list) -> bool:
    if getattr(args, "json", False) or getattr(args, "output", None) == "json":
        return True
    env = os.environ.get(ENV_OUTPUT, "")
    if env == "json" and not getattr(args, "output", None):
        return True
    return any(token in ("--json", "-ojson", "--output=json") for token in argv) \
        or any(a == "-o" and b == "json" for a, b in zip(argv, argv[1:])) \
        or any(a == "--output" and b == "json" for a, b in zip(argv, argv[1:]))


def _read_text(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    try:
        with open(path, encoding="utf-8") as handle:
            return handle.read()
    except FileNotFoundError:
        raise CliError(f"file {path!r} not found", "not_found",
                       EXIT_NOT_FOUND) from None


def _read_json(path: str):
    text = _read_text(path)
    if not text.strip():
        raise CliError(f"{path}: empty input", "usage", EXIT_USAGE)
    try:
        return json.loads(text)
    except ValueError as exc:
        raise CliError(f"{path}: invalid JSON ({exc})", "invalid_input") from exc


def _read_jsonl(path: str) -> list:
    records = []
    for number, line in enumerate(_read_text(path).splitlines(), start=1):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except ValueError as exc:
            raise CliError(f"{path}:{number}: invalid JSON ({exc})",
                           "invalid_input") from exc
    if not records:
        raise CliError(f"{path}: no outcome records", "usage", EXIT_USAGE)
    return records


def normalize_discoveries(items) -> list:
    """Accept the coordinator's discovery shape or `gh search prs --json
    number,title,url,repository` output."""
    if not isinstance(items, list):
        raise CliError("discoveries must be a JSON list", "invalid_input")
    out = []
    for item in items:
        if "repository" in item and "org" not in item:
            full = (item["repository"] or {}).get("nameWithOwner", "")
            owner, _, name = full.partition("/")
            if not owner or not name:
                raise CliError(f"discovery {item!r}: repository."
                               f"nameWithOwner must be owner/name",
                               "invalid_input")
            item = {"org": owner, "repo": name, "number": item.get("number"),
                    "url": item.get("url", ""), "title": item.get("title", ""),
                    "owner": owner, "head_sha": item.get("head_sha", ""),
                    "base_ref": item.get("base_ref", "")}
        for key in ("org", "repo", "number"):
            if not item.get(key):
                raise CliError(f"discovery {item!r} is missing {key!r}",
                               "invalid_input")
        out.append(item)
    return out


def _authority(store: Store, repo_id: str | None = None) -> dict:
    authority = dict((store.header.authority if store.header else {}) or {})
    if not authority:
        raise CliError("run header has no authority; recreate the run with "
                       "`run create`", "precondition_failed", EXIT_CONFLICT)
    return (cfg.authority_for_repo(authority, repo_id)
            if repo_id is not None else authority)


def _card(store: Store, card_id: str):
    card = store.cards.get(card_id)
    if card is None:
        raise CliError(f"card {card_id!r} not found; run `card list`",
                       "not_found", EXIT_NOT_FOUND)
    return card


def _counts(store: Store) -> dict:
    counts = {s.value.lower(): 0 for s in State}
    for card_id in store.header.scope_ids:
        counts[store.cards[card_id].state.value.lower()] += 1
    counts["selected"] = len(store.header.scope_ids)
    counts["delivered"] = coord.delivery_counts(store)
    return counts


def _store_or_none(ctx: Context) -> Store | None:
    """The named store, loaded (missing file exits 3); None only when no
    store was named at all, which is the storeless dry run."""
    return ctx.store() if ctx.store_path else None


def _resolve_target(ctx: Context, target: str, store: Store | None):
    """(owner, repo, number, card or None). With a store the target must be
    a card in it, so lease and quarantine are always checked; owner/repo#N
    is accepted only for the storeless dry run."""
    if store is not None:
        card = store.cards.get(target)
        if card is None:
            raise CliError(f"card {target!r} not found in {ctx.store_path}; "
                           f"with --store the target must be a card id (see "
                           f"`card list`)", "not_found", EXIT_NOT_FOUND)
        return card.org, card.repo, card.number, card
    match = TARGET_RE.match(target)
    if not match:
        raise CliError(f"target {target!r} must be a card id (with --store) "
                       f"or owner/repo#number", "usage", EXIT_USAGE)
    return match.group(1), match.group(2), int(match.group(3)), None


def _token() -> str:
    try:
        return gh_merge.get_token()
    except gh_merge.DefinitiveFailure as exc:
        raise CliError(f"{exc}; set GH_MERGE_TOKEN or run `gh auth login`",
                       "auth_required", EXIT_AUTH) from exc


# --- Commands ---------------------------------------------------------------

def cmd_run_create(args, ctx: Context) -> None:
    if not ctx.store_path:
        raise CliError(f"--store PATH (or {ENV_STORE}) is required",
                       "usage", EXIT_USAGE)
    if os.path.exists(ctx.store_path):
        raise CliError(f"store {ctx.store_path!r} already exists; choose a "
                       f"new path or continue that run", "precondition_failed",
                       EXIT_CONFLICT)
    discoveries = normalize_discoveries(_read_json(args.file))
    flags = {"config": ctx.config_path, "mode": args.mode,
             "no_auto_fix": args.no_auto_fix,
             "pause_on_conflict": args.pause_on_conflict,
             "org": sorted({d["org"] for d in discoveries})}
    run_config = cfg.load_config(ctx.config_path, flags, dict(os.environ))
    authority = run_config.to_authority(
        HELPER_PATH, repositories=[f"{d['org']}/{d['repo']}" for d in discoveries])
    store = Store(ctx.store_path, session=ctx.session)
    header = coord.create_run(
        store, args.run_id, mode=run_config.mode,
        authorization=args.authorization or f"{TOOL} run create",
        discoveries=discoveries, scope_fixed=not args.evolving,
        cutoff=args.cutoff or utc_now())
    header.authority = authority
    store.set_header(header)
    if run_config.run_budget_secs:
        coord.start_run_clock(store, run_config.run_budget_secs)
    label = report.authority_label(header)
    ctx.note(f"created {args.run_id}: {len(discoveries)} card(s), "
             f"{label}, config "
             f"{run_config.config_path or 'built-in defaults'}")
    lines = [f"{header.run_id} {label}: {len(header.scope_ids)} "
             f"selected card(s); store {ctx.store_path}"]
    lines.extend(report.repository_authority_lines(header))
    ctx.emit(header.to_dict(), "\n".join(lines))


def cmd_run_view(args, ctx: Context) -> None:
    store = ctx.store()
    header = store.header.to_dict()
    header["counts"] = _counts(store)
    header["attempts"] = len(store.diary)
    lines = [f"{store.header.run_id} {report.authority_label(store.header)} "
             f"stop_reason={store.header.stop_reason or 'running'}",
             f"selected {header['counts']['selected']}; "
             f"merged {header['counts']['merged']}; "
             f"delivered {header['counts']['delivered']['total']}; "
             f"attempts {header['attempts']}"]
    if "repositories" in store.header.authority:
        lines.extend(report.repository_authority_lines(store.header))
    else:
        lines.append(
            f"authority: mode {store.header.authority.get('mode', '?')}, "
            f"repairs {', '.join(store.header.authority.get('repairs', [])) or 'none'}")
    ctx.emit(header, "\n".join(lines))


def cmd_run_describe(args, ctx: Context) -> None:
    store = ctx.store()
    text = report.render_report(store)
    ctx.emit({"header": store.header.to_dict(),
              "cards": [c.to_dict() for c in store.cards.values()],
              "attempts": [a.to_dict() for a in store.diary.values()],
              "issues": [i.to_dict() for i in store.issues.values()],
              "report": text}, text)


def cmd_run_reconcile(args, ctx: Context) -> None:
    store = ctx.store()
    observed = _read_json(args.file)
    if not isinstance(observed, dict):
        raise CliError("observed must be a JSON object keyed by card id",
                       "invalid_input")
    stale = _authority(store).get("stale_after_secs")
    summary = coord.reconcile(store, observed, set(args.live),
                              stale_after_secs=stale)
    ctx.emit(summary, "\n".join(f"{key}: {', '.join(value) or 'none'}"
                                for key, value in summary.items()))


def cmd_run_finish(args, ctx: Context) -> None:
    store = ctx.store()
    continuation = patience.continuation(args.continuation, args.ref,
                                         args.verified_at)
    ending = coord.finish_run(store, continuation,
                              discovery_complete=not args.discovery_incomplete)
    ctx.emit({"stop_reason": ending, "continuation": continuation},
             f"{store.header.run_id} ended {ending}; continuation "
             f"{continuation['kind']}"
             f"{' ' + continuation['ref'] if continuation['ref'] else ''}")


def cmd_attempt_create(args, ctx: Context) -> None:
    store = ctx.store()
    authority = _authority(store)
    expired = coord.expire(store)
    if expired:
        ctx.note(f"expired before dispatch: {', '.join(expired)}")
    taskings = coord.schedule(store, model=args.model,
                              pr_budget_secs=authority.get("pr_budget_secs"),
                              wake=tuple(args.wake))
    ctx.emit(taskings, "\n".join(
        f"{t['attempt_id']} {t['repo_id']}: {', '.join(t['card_ids'])}"
        for t in taskings) or "nothing to schedule")


def cmd_attempt_collect(args, ctx: Context) -> None:
    store = ctx.store()
    results = _read_jsonl(args.file)
    outcome = coord.apply_outcome(store, args.attempt_id, results)
    ctx.emit(outcome, f"{args.attempt_id}: applied "
                      f"{', '.join(outcome['applied']) or 'none'}; pending "
                      f"{', '.join(outcome['pending']) or 'none'}")


def _tasking(store: Store, ctx: Context, attempt_id: str,
             progress_log: str | None) -> proto.Tasking:
    attempt = store.diary.get(attempt_id)
    if attempt is None:
        raise CliError(f"attempt {attempt_id!r} not found", "not_found",
                       EXIT_NOT_FOUND)
    card_ids = list(attempt.assigned)
    repo_id = store.cards[card_ids[0]].repo_id if card_ids else ""
    authority = _authority(store, repo_id)
    record = {"attempt_id": attempt_id, "repo_id": repo_id,
              "card_ids": card_ids}
    return proto.Tasking.from_store(
        store, record, mode=authority["mode"], repairs=authority["repairs"],
        op_timeout_secs=authority["op_timeout_secs"],
        progress_log=progress_log or ctx.store_path + ".progress.log",
        helper_path=authority.get("helper_path") or HELPER_PATH,
        approved=[i for i in authority.get("approved", []) if i in card_ids],
        holds=[i for i in authority.get("holds", []) if i in card_ids],
        pause_on_conflict=authority.get("pause_on_conflict", False),
        reviewer_contexts=authority.get("reviewer_contexts", []))


def cmd_brief_view(args, ctx: Context) -> None:
    store = ctx.store()
    tasking = _tasking(store, ctx, args.attempt_id, args.progress_log)
    ctx.emit(tasking.to_dict(), proto.render_brief(tasking))


def cmd_card_list(args, ctx: Context) -> None:
    store = ctx.store()
    cards = sorted(store.cards.values(), key=lambda c: c.id)
    ctx.emit([c.to_dict() for c in cards], "\n".join(
        f"{c.id} {c.state.value:<11} {c.human_id} "
        f"{c.reason_code + ' ' if c.reason_code else ''}{c.reason_line}".rstrip()
        for c in cards) or "no cards")


def cmd_card_view(args, ctx: Context) -> None:
    store = ctx.store()
    card = _card(store, args.card_id)
    lines = [f"{card.human_id} [{card.id}] -- {card.state.value}",
             f"head {card.head_sha or '?'} base {card.base_ref or '?'}",
             f"reason: {card.reason_code} {card.reason_line}".rstrip(),
             f"severity {card.severity}, confidence {card.confidence}",
             f"action: {card.action or 'none'} (owner "
             f"{card.action_owner or 'unassigned'}; resume "
             f"{card.resume_trigger or 'n/a'})",
             f"attempts: {', '.join(card.attempts) or 'none'}"]
    if card.state == State.MERGED:
        lines.append(f"merged {card.merge_commit} at {card.merged_at}")
    ctx.emit(card.to_dict(), "\n".join(lines))


def cmd_pr_observe(args, ctx: Context) -> None:
    store = _store_or_none(ctx)
    owner, repo, number, card = _resolve_target(ctx, args.target, store)
    authority = (store.header.authority if store and store.header else {}) or {}
    token = _token()
    observation = observe.fetch_observation(
        owner, repo, number, token,
        op_timeout=authority.get("op_timeout_secs", 30),
        deadline_epoch=(card.deadline_epoch if card and card.deadline_epoch
                        else None))
    data = observe.observation_to_dict(observation)
    if card is not None:
        data["card_id"] = card.id
    sections = ", ".join(
        f"{name}={'ok' if _ok(getattr(observation, name)) else 'unreadable'}"
        for name in observe.SECTION_NAMES)
    ctx.emit(data, f"{owner}/{repo}#{number} head "
                   f"{observation.head_sha[:12] or '?'} at "
                   f"{observation.observed_at}\n{sections}\npolicy "
                   f"{'known' if observation.policy.known else 'unknown: ' + observation.policy.reason}; "
                   f"required checks "
                   f"{', '.join(c.context for c in observation.policy.required_checks) or 'none'}")


def _ok(section: dict) -> bool:
    status = section.get("status")
    return status is not None and 200 <= status < 300 and not section.get(
        "truncated")


def cmd_pr_evaluate(args, ctx: Context) -> None:
    store = _store_or_none(ctx)
    owner, repo, number, card = _resolve_target(ctx, args.target, store)
    payload = _read_json(args.file)
    try:
        observation = observe.observation_from_dict(payload)
    except (KeyError, TypeError) as exc:
        raise CliError(f"observation is missing {exc}; use `pr observe -o "
                       f"json`", "invalid_input") from exc
    files = observation.files.get("data") or []
    receipt = ev.ClassifierReceipt.for_files(
        observation.head_sha, files, dependency_only=args.dependency_only,
        classifier=args.classifier, at=utc_now())
    notes = []
    if store is not None and card is not None:
        authority = _authority(store, card.repo_id)
        auth = ev.Authority(mode=authority["mode"],
                            repairs=frozenset(authority["repairs"]),
                            owner_hold=card.id in authority.get("holds", []),
                            approved=card.id in authority.get("approved", []),
                            deadline_epoch=card.deadline_epoch or None)
        lease = store.leases.get(card.repo_id)
        tracking = ev.Tracking(
            lease_held=bool(args.attempt) and lease.state == "held"
            and lease.holder == args.attempt,
            repo_quarantined=lease.state == "quarantined")
        reviewers = set(authority.get("reviewer_contexts", []))
        card_id = card.id
    else:
        auth = ev.Authority(mode=args.mode or "inspect")
        tracking = ev.Tracking(lease_held=True, repo_quarantined=False)
        reviewers = set()
        notes.append("dry run without a store: lease and quarantine not "
                     "checked")
        card_id = f"{owner}/{repo}#{number}"
    reviewers |= set(args.reviewer_context)
    result = ev.evaluate(observation, receipt, auth, tracking,
                         now=time.time(), reviewer_contexts=reviewers)
    evaluation = {
        "head_sha": result.head_sha, "state": result.state.value,
        "reason_code": result.reason_code, "reason_line": result.reason_line,
        "severity": result.severity, "confidence": result.confidence,
        "merge_path": result.merge_path,
        "checks": [asdict(c) for c in result.checks],
        "evidence": result.evidence, "notes": result.notes + notes,
        "resolved": result.resolved,
    }
    lines = [f"{owner}/{repo}#{number} -> {result.state.value}"
             f"{' (merge via ' + result.merge_path + ')' if result.merge_path != 'none' else ''}",
             f"  {result.reason_code + ' ' if result.reason_code else ''}"
             f"{result.reason_line}".rstrip()]
    for check in result.checks:
        mark = {True: "pass", False: "FAIL", None: "skip"}[check.passed]
        lines.append(f"  {check.name:<9} {mark}"
                     f"{'  ' + check.reason_line if check.reason_line else ''}")
    for note in result.notes + notes:
        lines.append(f"  note: {note}")
    ctx.emit({"target": card_id, "evaluation": evaluation,
              "outcome": result.to_outcome(card_id),
              "receipt": asdict(receipt)}, "\n".join(lines))


def cmd_approval_list(args, ctx: Context) -> None:
    store = ctx.store()
    needy = [store.cards[i].to_dict() for i in store.header.scope_ids
             if store.cards[i].state == State.NEEDS_OWNER]
    ctx.emit(needy, report.render_approval(store))


COMMANDS = {
    ("run", "create"): cmd_run_create,
    ("run", "view"): cmd_run_view,
    ("run", "describe"): cmd_run_describe,
    ("run", "reconcile"): cmd_run_reconcile,
    ("run", "finish"): cmd_run_finish,
    ("attempt", "create"): cmd_attempt_create,
    ("attempt", "collect"): cmd_attempt_collect,
    ("brief", "view"): cmd_brief_view,
    ("card", "list"): cmd_card_list,
    ("card", "view"): cmd_card_view,
    ("pr", "observe"): cmd_pr_observe,
    ("pr", "evaluate"): cmd_pr_evaluate,
    ("approval", "list"): cmd_approval_list,
}


# --- Entry point -------------------------------------------------------------

def _report_error(machine: bool, code: str, message: str) -> None:
    if machine:
        sys.stderr.write(json.dumps({"error": {"code": code,
                                               "message": message}}) + "\n")
    else:
        text = message[0].lower() + message[1:] if message else "unknown error"
        sys.stderr.write(f"error: {text.rstrip('.')}\n")


def _find_parser(root: Parser, argv: list) -> argparse.ArgumentParser:
    """The deepest command parser argv names, for usage on a bare noun."""
    parser = root
    for action in root._subparsers._group_actions:  # noqa: SLF001
        for token in argv:
            if token in action.choices:
                parser = action.choices[token]
                sub = getattr(parser, "_subparsers", None)
                if sub:
                    for inner in sub._group_actions:  # noqa: SLF001
                        for later in argv[argv.index(token) + 1:]:
                            if later in inner.choices:
                                return inner.choices[later]
                return parser
    return parser


def main(argv: list | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    root = build_parser()
    machine = _machine_requested(argparse.Namespace(), argv)
    try:
        if not argv:
            root.print_help(sys.stdout)
            return EXIT_OK
        try:
            args = root.parse_args(argv)
        except SystemExit as exc:  # --help
            return int(exc.code or 0)
        if args.version:
            sys.stdout.write(f"{TOOL} {version()}\n")
            return EXIT_OK
        if not args.noun:
            root.print_help(sys.stdout)
            return EXIT_OK
        if not getattr(args, "verb", None):
            if machine:
                _report_error(True, "usage", f"{args.noun} needs a verb")
            else:
                _find_parser(root, argv).print_usage(sys.stderr)
                sys.stderr.write(f"error: '{args.noun}' needs a verb; see "
                                 f"'{TOOL} {args.noun} --help'\n")
            return EXIT_USAGE
        ctx = Context(args, argv)
        COMMANDS[(args.noun, args.verb)](args, ctx)
        return EXIT_OK
    except UsageError as exc:
        if machine:
            _report_error(True, "usage", str(exc))
        else:
            exc.parser.print_usage(sys.stderr)
            sys.stderr.write(f"error: {exc}\n")
        return EXIT_USAGE
    except CliError as exc:
        _report_error(machine, exc.code, str(exc))
        return exc.exit_code
    except cfg.ConfigError as exc:
        _report_error(machine, exc.code, str(exc))
        return EXIT_NOT_FOUND if exc.code == "not_found" else EXIT_ERROR
    except StoreError as exc:
        _report_error(machine, "store_error", str(exc))
        return EXIT_ERROR
    except TransitionError as exc:
        _report_error(machine, "transition_refused", str(exc))
        return EXIT_ERROR
    except LeaseError as exc:
        _report_error(machine, "lease_refused", str(exc))
        return EXIT_ERROR
    except gh_merge.AmbiguousFailure as exc:
        _report_error(machine, "transport", str(exc))
        return EXIT_ERROR
    except gh_merge.DefinitiveFailure as exc:
        _report_error(machine, "github_error", str(exc))
        return EXIT_ERROR
    except ValueError as exc:
        _report_error(machine, "invalid", str(exc))
        return EXIT_ERROR
    except KeyboardInterrupt:
        _report_error(machine, "interrupted", "interrupted")
        return EXIT_INTERRUPT
    finally:
        for stream in (sys.stdout, sys.stderr):
            try:
                stream.flush()
            except (OSError, ValueError):
                pass


if __name__ == "__main__":
    sys.exit(main())
