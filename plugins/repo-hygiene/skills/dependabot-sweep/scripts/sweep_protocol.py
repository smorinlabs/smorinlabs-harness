#!/usr/bin/env python3
"""Dispatcher -> worker handoff protocol for dependabot-sweep, Slice 2.

A Tasking record carries exactly what one worker attempt may do to one
repository: assigned cards, mode, repairs, approvals, holds, and one
absolute deadline per PR. `render_brief` fills templates/agent-brief.md
from it and refuses to leave a placeholder. `helper_command` binds the
merge wrapper to a card's approved head and deadline. `helper_outcome`
maps a helper exit to the worker's next step using literal reason strings, and
never fabricates a merged record: exit 0 means "verify", not "merged".

Stdlib only. The helper (gh_merge.py) is unchanged: it is transport.
"""

from __future__ import annotations

import os
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sweep_core import Store  # noqa: E402

MODES = {
    "inspect": "discover, diagnose, and recommend; no repository mutation "
               "and no merge",
    "automated": "authorized repair and observation; merge when the five "
                 "checks pass; no interactive prompts, genuine owner "
                 "decisions become NEEDS_OWNER records",
    "gated": "complete authorized preparation; merge only the approved PRs "
             "listed here, after a fresh refresh",
}
# Separate repair permissions (F06): each is granted on its own. Repository
# settings are never a worker repair, whatever the caller asks.
REPAIRS = frozenset({"branch_update", "lockfile", "code_repair",
                     "major_migration", "replacement_pr"})
FORBIDDEN_REPAIRS = frozenset({"repo_settings"})
READ_ONLY_ACTIONS = frozenset({"observe", "diagnose"})
MERGE_ACTIONS = frozenset({"merge", "enqueue"})
# The one executor per merge path. The helper refuses queue-required
# targets, so a queue merge is always pr-merge-flow's enqueue.
EXECUTORS = {"put": "sweep_merge.py", "queue": "pr-merge-flow enqueue"}
MERGE_WRAPPER = Path(__file__).resolve().with_name("sweep_merge.py")
DEFAULT_TEMPLATE = (Path(__file__).resolve().parent.parent / "templates"
                    / "agent-brief.md")
PLACEHOLDER = re.compile(r"\{\{[A-Z_]+\}\}")


@dataclass
class Tasking:
    """One worker attempt's exact authority over one repository."""

    attempt_id: str
    repo_id: str
    card_ids: list
    cards: list
    mode: str
    merge_allowed: bool
    approved: list = field(default_factory=list)
    holds: list = field(default_factory=list)
    repairs: list = field(default_factory=list)
    deadlines: dict = field(default_factory=dict)
    op_timeout_secs: int = 30
    pause_on_conflict: bool = False
    progress_log: str = ""
    helper_path: str = ""
    lease_holder: str = ""
    scope_fixed: bool = True
    cutoff: str = ""
    run_deadline_epoch: float = 0.0
    reviewer_contexts: list = field(default_factory=list)

    @classmethod
    def from_store(cls, store: Store, record: dict, mode: str, repairs,
                   op_timeout_secs: int, progress_log: str, helper_path: str,
                   approved=(), holds=(), pause_on_conflict: bool = False,
                   reviewer_contexts=()
                   ) -> "Tasking":
        """Build from a `schedule()` tasking record plus the run's authority.

        inspect never merges and never repairs; automated merges when
        allowed; gated merges only the approved card ids. Repository
        settings are never a repair, whatever the caller asks.
        """
        if mode not in MODES:
            raise ValueError(f"unknown mode {mode!r}; expected one of "
                             f"{', '.join(MODES)}")
        forbidden = FORBIDDEN_REPAIRS & set(repairs or ())
        if forbidden:
            raise ValueError(f"repairs {sorted(forbidden)} are never a "
                             f"worker repair")
        unknown = set(repairs or ()) - REPAIRS
        if unknown:
            raise ValueError(f"unknown repairs {sorted(unknown)}; expected "
                             f"any of {', '.join(sorted(REPAIRS))}")
        card_ids = list(record["card_ids"])
        for label, ids in (("approved", approved), ("holds", holds)):
            stray = [i for i in ids if i not in card_ids]
            if stray:
                raise ValueError(f"{label} references unassigned cards "
                                 f"{stray}")
        cards = []
        for card_id in card_ids:
            card = store.cards[card_id]
            cards.append({"id": card.id, "org": card.org, "repo": card.repo,
                          "number": card.number, "url": card.url,
                          "title": card.title, "head_sha": card.head_sha,
                          "human_id": card.human_id,
                          "state": card.state.value,
                          "reason_code": card.reason_code,
                          "deadline_epoch": card.deadline_epoch})
        header = store.header
        return cls(
            attempt_id=record["attempt_id"], repo_id=record["repo_id"],
            card_ids=card_ids, cards=cards, mode=mode,
            merge_allowed=mode != "inspect",
            approved=list(approved) if mode == "gated" else [],
            holds=list(holds),
            repairs=[] if mode == "inspect" else sorted(set(repairs or ())),
            deadlines={c["id"]: c["deadline_epoch"] for c in cards},
            op_timeout_secs=int(op_timeout_secs),
            pause_on_conflict=bool(pause_on_conflict),
            progress_log=progress_log, helper_path=helper_path,
            lease_holder=record["attempt_id"],
            scope_fixed=header.scope_fixed if header else True,
            cutoff=header.cutoff if header else "",
            run_deadline_epoch=header.deadline_epoch if header else 0.0,
            reviewer_contexts=list(reviewer_contexts))

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Tasking":
        known = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in data.items() if k in known})

    def card(self, card_id: str) -> dict:
        for card in self.cards:
            if card["id"] == card_id:
                return card
        raise KeyError(f"{card_id} is not assigned to {self.attempt_id}")


def _epoch(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else str(value)


def _listing(ids: list) -> str:
    return ", ".join(ids) if ids else "none"


def render_brief(tasking: Tasking, template_path=None) -> str:
    """Fill the brief template from the tasking. Raises if any `{{VAR}}`
    would survive, so a template/renderer drift can never reach a worker."""
    template = Path(template_path or DEFAULT_TEMPLATE).read_text(
        encoding="utf-8")
    owner, repo = tasking.repo_id.split("/", 1)
    pr_lines = []
    for card in tasking.cards:
        deadline = card.get("deadline_epoch") or 0
        pr_lines.append(
            f"- {card['human_id']} [{card['id']}] head "
            f"{card.get('head_sha') or '?'} · "
            f"GH_MERGE_DEADLINE_EPOCH={_epoch(deadline) if deadline else 'unset'}")
    values = {
        "ATTEMPT_ID": tasking.attempt_id, "OWNER": owner, "REPO": repo,
        "PR_COUNT": str(len(tasking.cards)), "PR_LIST": "\n".join(pr_lines),
        "MODE": tasking.mode, "MODE_RULE": MODES[tasking.mode],
        "MERGE_ALLOWED": "true" if tasking.merge_allowed else "false",
        "APPROVED": (_listing(tasking.approved) if tasking.mode == "gated"
                     else "not applicable"),
        "HOLDS": _listing(tasking.holds),
        "REPAIRS": _listing(tasking.repairs),
        "REVIEWER_CONTEXTS": _listing(tasking.reviewer_contexts),
        "PAUSE_ON_CONFLICT": "true" if tasking.pause_on_conflict else "false",
        "SCOPE": _scope_line(tasking),
        "RUN_DEADLINE": (_epoch(tasking.run_deadline_epoch)
                         if tasking.run_deadline_epoch else "unset"),
        "OP_TIMEOUT": str(tasking.op_timeout_secs),
        "MERGE_WRAPPER": str(MERGE_WRAPPER),
        "HELPER": tasking.helper_path, "LOG": tasking.progress_log,
    }
    text = template
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    leftover = PLACEHOLDER.search(text)
    if leftover:
        raise ValueError(f"brief has an unfilled placeholder "
                         f"{leftover.group(0)}")
    return text


def _scope_line(tasking: Tasking) -> str:
    if tasking.scope_fixed:
        at = tasking.cutoff or "run start"
        return (f"fixed snapshot taken at {at}; a question about some PRs "
                f"never narrows it, and later arrivals are reported, not "
                f"worked")
    return ("evolving backlog; new arrivals join with new ids, and a "
            "question about some PRs never narrows it")


def resolve_mode(auto_fix: bool = True, check: bool = False,
                 gated: bool = False) -> str:
    """Map invocation flags to one mode. `--no-auto-fix` and `--check`
    keep their historical meaning (triage only, no mutation), and beat
    `gated`: an inspect run never merges."""
    if check or not auto_fix:
        return "inspect"
    return "gated" if gated else "automated"


def executor_for(merge_path: str) -> str:
    """The single executor for a READY card's merge path."""
    if merge_path not in EXECUTORS:
        raise ValueError(f"no executor for merge path {merge_path!r}")
    return EXECUTORS[merge_path]


def authorize(tasking: Tasking, action: str, card_id: str,
              now: float) -> tuple:
    """May this attempt take `action` on this card now?

    Read-only actions are always allowed. Every mutation is refused on an
    owner hold (K16), after the card's or run's deadline (K14), and in
    inspect mode. merge/enqueue need automated mode or a gated approval,
    and are refused for a card already in the merge queue. A repair needs
    its own permission. Returns (allowed, reason).
    """
    card = tasking.card(card_id)
    if action in READ_ONLY_ACTIONS:
        return True, "read-only"
    if action not in MERGE_ACTIONS and action not in REPAIRS:
        return False, f"{action!r} is not a worker action"
    if tasking.mode == "inspect":
        return False, "inspect mode performs no mutation"
    if card_id in tasking.holds:
        return False, "K16 owner hold in effect"
    deadline = min((d for d in (card.get("deadline_epoch"),
                                tasking.run_deadline_epoch) if d),
                   default=0)
    if deadline and now > deadline:
        return False, "K14 budget exhausted; observation only"
    if action in MERGE_ACTIONS:
        if card.get("state") == "WAITING" and card.get("reason_code") == "K10":
            return False, ("already in the merge queue; queue acceptance is "
                           "pending, observe only")
        if tasking.mode == "gated" and card_id not in tasking.approved:
            return False, "K16 gated mode: not approved"
        return True, f"{tasking.mode} merge"
    if action not in tasking.repairs:
        return False, f"repair {action} not permitted"
    return True, f"repair {action} permitted"


def helper_command(tasking: Tasking, card_id: str) -> tuple:
    """argv and environment for one wrapper invocation, bound to the
    card's approved/classified head and the earlier of the card's and
    run's absolute deadlines. Never substitute a freshly fetched head or
    recompute a deadline here. The wrapper refuses an absent/invalid head."""
    card = tasking.card(card_id)
    argv = ["python3", str(MERGE_WRAPPER), "--expected-head",
            card.get("head_sha") or "", "--helper-path", tasking.helper_path,
            "--", card["org"], card["repo"],
            str(card["number"]), "merge", tasking.progress_log,
            "--assert-trivial"]
    env = {"GH_MERGE_OP_TIMEOUT": str(tasking.op_timeout_secs),
           "GH_PROMPT_DISABLED": "1"}
    deadline = min((d for d in (card.get("deadline_epoch"),
                                tasking.run_deadline_epoch) if d),
                   default=0)
    if deadline:
        env["GH_MERGE_DEADLINE_EPOCH"] = _epoch(deadline)
    return argv, dict(sorted(env.items()))


# Literal substrings from gh_merge.py -> (reason code, hold state). Order
# matters: the first match wins, so specific literals precede general ones.
# test_helper_reason_literals_exist_in_helper_source pins each literal to
# the helper's source text.
HELPER_REASONS = (
    ("checks pending", "K01", "WAITING"),
    ("required checks not green", "K01", "WAITING"),
    ("failing checks", "K04", "BLOCKED"),
    ("no longer mergeable", "K13", "WAITING"),
    ("not mergeable: state=", "K09", "BLOCKED"),
    ("merge queue required", "K12", "BLOCKED"),
    ("change requests outstanding", "K07", "BLOCKED"),
    ("unresolved review threads", "K07", "BLOCKED"),
    ("inline review comments need human reading", "K07", "BLOCKED"),
    ("triviality not asserted", "K13", "BLOCKED"),
    ("too large to verify", "K13", "BLOCKED"),
    ("exceed one page", "K13", "BLOCKED"),
    ("unreadable", "K13", "BLOCKED"),
    ("empty diff", "K13", "BLOCKED"),
    ("head changed", "K13", "WAITING"),
    ("merge not applied", "K13", "WAITING"),
    ("per-PR budget exceeded", "K14", "WAITING"),
    ("transport failure", "K17", "WAITING"),
    ("truncated response", "K17", "WAITING"),
    ("credential acquisition failed", "K12", "BLOCKED"),
    ("PR is a draft", "K09", "BLOCKED"),
    ("-> HTTP", "K09", "BLOCKED"),
)
# GitHub's documented mergeable_state values (REST pulls, 2026-09-22) that
# the helper echoes after "not mergeable: state=". Conflict-shaped states
# are mechanical conflicts; the rest are policy gates.
MERGEABLE_STATE_REASONS = {
    "dirty": ("K02", "BLOCKED"), "behind": ("K02", "BLOCKED"),
    "blocked": ("K09", "BLOCKED"), "has_hooks": ("K09", "BLOCKED"),
    "unstable": ("K01", "WAITING"), "unknown": ("K13", "WAITING"),
    "draft": ("K09", "BLOCKED"),
}
# The PR left the open state under us: observe, never infer.
HELPER_VERIFY = ("PR is not open", "PR closed during preflight")
DEFERRED_PREFIXES = ("DEFERRED (transport, safe: nothing submitted): ",
                     "DEFERRED: ")


def helper_outcome(exit_code: int, stdout: str) -> dict:
    """The worker's next step after one helper run.

    0  -> {"next": "verify"}: GET the PR and record merged only from that
          fresh evidence (check 5). Never a merged record from exit 0 alone.
    10 -> {"next": "hold", ...} with the helper's literal reason mapped to
          a code and hold state, or {"next": "verify"} when the PR left the
          open state. A queue-required refusal is a wrong-executor or
          evaluator disagreement (K12), never queue acceptance (K10).
    11 -> {"next": "unknown", "op_note": ...}: quarantine, never retry.
    12 or anything else -> hold K12 (worker/configuration failure).
    """
    lines = [line.strip() for line in (stdout or "").splitlines()
             if line.strip()]
    last = lines[-1] if lines else ""
    if exit_code == 0:
        return {"next": "verify", "helper_line": last}
    if exit_code == 11:
        return {"next": "unknown",
                "op_note": " | ".join(lines) or "helper exit 11 with no "
                                                 "output"}
    if exit_code == 10:
        reason = last
        for prefix in DEFERRED_PREFIXES:
            if reason.startswith(prefix):
                reason = reason[len(prefix):]
                break
        if any(literal in reason for literal in HELPER_VERIFY):
            return {"next": "verify", "helper_line": last}
        for literal, code, state in HELPER_REASONS:
            if literal not in reason:
                continue
            if literal == "not mergeable: state=":
                value = reason.split("state=", 1)[1].strip()
                code, state = MERGEABLE_STATE_REASONS.get(value, (code, state))
            reason_line = f"helper deferred: {reason}"
            if literal == "merge queue required":
                reason_line += (
                    "; helper/evaluator disagreement or wrong executor; "
                    "fresh policy re-evaluation required before choosing "
                    "a merge executor")
            return {"next": "hold", "reason_code": code, "state": state,
                    "reason_line": reason_line}
        return {"next": "hold", "reason_code": "K13", "state": "BLOCKED",
                "reason_line": f"helper deferred: {reason}"}
    return {"next": "hold", "reason_code": "K12", "state": "BLOCKED",
            "reason_line": f"helper exit {exit_code}: "
                           f"{last or 'no output'}"}
