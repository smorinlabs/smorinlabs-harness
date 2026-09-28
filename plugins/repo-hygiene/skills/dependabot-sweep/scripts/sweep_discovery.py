#!/usr/bin/env python3
"""Validation for explicit, read-only discovery and observation evidence.

No network access. Repository grants come only from frozen configuration,
never from permission-shaped fields in supplied GitHub JSON.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import json
import re

from sweep_config import REPOSITORY_AUTHORITY_KEYS
from sweep_core import StoreError

NAME = re.compile(r"^[A-Za-z0-9_.-]+$")
HEAD = re.compile(r"^[0-9a-fA-F]{40}$")


def timestamp(value, label="observed_at") -> float:
    if not isinstance(value, str) or not value:
        raise StoreError(f"{label} must be an ISO8601 timestamp with a timezone")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError("missing timezone")
        return parsed.timestamp()
    except (ValueError, OverflowError) as exc:
        raise StoreError(f"{label} must be an ISO8601 timestamp with a timezone") from exc


def repo_name(value) -> str:
    if not isinstance(value, str) or len(value.split("/")) != 2 \
            or any(not NAME.fullmatch(s) for s in value.split("/")):
        raise StoreError("repository must be owner/name")
    return value


def normalize(items) -> list:
    """Normalize identities, retain creation evidence, and deduplicate PRs."""
    if not isinstance(items, list):
        raise StoreError("discoveries must be a JSON list")
    out, seen = [], set()
    for raw in items:
        if not isinstance(raw, dict):
            raise StoreError("each discovery must be a JSON object")
        item = deepcopy(raw)
        repository = item.get("repository") or {}
        if not isinstance(repository, dict):
            raise StoreError("discovery.repository must be an object")
        if "org" not in item:
            full = repo_name(repository.get("nameWithOwner", ""))
            item["org"], item["repo"] = full.split("/")
        full = repo_name(f"{item.get('org', '')}/{item.get('repo', '')}")
        if repository.get("nameWithOwner") and \
                repository["nameWithOwner"].casefold() != full.casefold():
            raise StoreError("conflicting discovery repository identities")
        if isinstance(item.get("number"), bool) or not isinstance(item.get("number"), int) \
                or item["number"] <= 0:
            raise StoreError("discovery.number must be a positive integer")
        item["pr_created_at"] = item.get("pr_created_at", item.get("createdAt", ""))
        if item["pr_created_at"]:
            timestamp(item["pr_created_at"], "pr_created_at")
        visibility = item.get("visibility", repository.get("visibility", ""))
        if visibility:
            if not isinstance(visibility, str) or visibility.lower() not in ("public", "private", "internal"):
                raise StoreError("repository visibility must be public, private, or internal")
            item["visibility"] = visibility.lower()
        key = (full.casefold(), item["number"])
        if key not in seen:
            out.append(item)
            seen.add(key)
    return out


def frozen_scopes(config) -> list:
    scopes = []
    for scope in config.scopes:
        effective = config.scope_for(scope.login)
        scopes.append({
            "kind": scope.kind, "login": scope.login,
            "visibility": scope.visibility, "repos": sorted(set(scope.repos)),
            "authority": {k: deepcopy(getattr(effective, k))
                          for k in REPOSITORY_AUTHORITY_KEYS},
        })
    return scopes


def coverage(authority: dict) -> list:
    """Exact selectors the supplied inventory must claim to cover."""
    if "discovery_scopes" in authority:
        return [{k: deepcopy(s[k]) for k in ("kind", "login", "visibility", "repos")}
                for s in authority["discovery_scopes"]]
    # Old journals can safely attest only their already frozen repositories.
    return [{"kind": "repo", "login": rid.split("/")[0],
             "visibility": "all", "repos": [rid.split("/")[1]]}
            for rid in sorted(authority.get("repositories", {}))]


def same_coverage(left, right) -> bool:
    return isinstance(left, list) and sorted(json.dumps(s, sort_keys=True) for s in left) \
        == sorted(json.dumps(s, sort_keys=True) for s in right)


def excluded(exclusions: list, rid: str, number: int | None = None,
             url: str = "") -> bool:
    targets = {rid.casefold(), rid.split("/")[0].casefold(),
               (rid.split("/")[0] + "/*").casefold()}
    if number is not None:
        targets.add(f"{rid}#{number}".casefold())
    if url:
        targets.add(url.casefold())
    return any(isinstance(e, str) and e.casefold() in targets for e in exclusions)


def repository_grant(authority: dict, rid: str, visibility: str = "") -> tuple:
    """Return (frozen grant, explanation), never an inferred default grant."""
    aliases = [v for k, v in authority.get("repositories", {}).items()
               if k.casefold() == rid.casefold()]
    if aliases and any(value != aliases[0] for value in aliases[1:]):
        return None, "conflicting case-insensitive repository grants; scope reconciliation required"
    existing = aliases[0] if aliases else None
    if existing is not None and (not isinstance(existing, dict)
            or any(k not in existing for k in REPOSITORY_AUTHORITY_KEYS)):
        return None, "incomplete frozen repository authority; scope reconciliation required"
    scopes = authority.get("discovery_scopes")
    if scopes is None:
        if isinstance(existing, dict) and all(k in existing for k in REPOSITORY_AUTHORITY_KEYS):
            return deepcopy(existing), "existing frozen repository authority"
        return None, "repository has no frozen discovery scope; scope reconciliation required"
    owner, name = rid.split("/")
    matches, missing_visibility = [], False
    for scope in scopes:
        if scope["login"].casefold() != owner.casefold():
            continue
        names = [s.casefold() for s in scope["repos"]]
        if (scope["kind"] == "repo" or names) and name.casefold() not in names:
            continue
        if scope["visibility"] != "all" and visibility != scope["visibility"]:
            # Re-observing an already authorized repo does not need a new
            # visibility claim. An explicit contrary observation does matter.
            if not visibility and existing is not None:
                matches.append(scope["authority"])
            else:
                missing_visibility = not visibility
            continue
        matches.append(scope["authority"])
    if not matches:
        return None, ("repository visibility evidence required for frozen scope"
                      if missing_visibility else "repository is outside frozen discovery scope")
    if any(grant != matches[0] for grant in matches[1:]):
        return None, "overlapping frozen grants disagree; scope reconciliation required"
    return deepcopy(existing if existing is not None else matches[0]), "frozen discovery scope"


def validate_inventory(payload: dict, previous: dict) -> tuple:
    if not isinstance(payload, dict):
        raise StoreError("discovery snapshot must be a JSON object")
    at = timestamp(payload.get("observed_at"))
    if previous and at <= timestamp(previous["observed_at"]):
        raise StoreError("discovery snapshot must be newer than the saved snapshot")
    if not isinstance(payload.get("complete"), bool):
        raise StoreError("discovery snapshot.complete must be explicitly true or false")
    if not isinstance(payload.get("source"), str) or not payload["source"].strip():
        raise StoreError("discovery snapshot.source must identify its read-only evidence")
    if not isinstance(payload.get("coverage"), list):
        raise StoreError("discovery snapshot.coverage must name the exact covered scopes")
    scoped = payload.get("scope_repositories")
    if not isinstance(scoped, list):
        raise StoreError("scope_repositories must be an explicit repository inventory")
    for rid in scoped:
        repo_name(rid)
    inventory = payload.get("repositories")
    if not isinstance(inventory, list):
        raise StoreError("repositories must include the visibility inventory")
    visibility = {}
    for row in inventory:
        if not isinstance(row, dict):
            raise StoreError("each repository inventory entry must be an object")
        rid = repo_name(row.get("nameWithOwner"))
        vis = row.get("visibility", "")
        if not isinstance(vis, str) or vis.lower() not in ("public", "private", "internal"):
            raise StoreError("each repository inventory entry needs visibility evidence")
        key = rid.casefold()
        if key in visibility and visibility[key] != vis.lower():
            raise StoreError("conflicting repository visibility evidence")
        visibility[key] = vis.lower()
    discoveries = normalize(payload.get("discoveries"))
    for item in discoveries:
        rid = f"{item['org']}/{item['repo']}".casefold()
        vis = visibility.get(rid, item.get("visibility", ""))
        if item.get("visibility") and vis != item["visibility"]:
            raise StoreError("discovery and repository visibility evidence disagree")
        item["visibility"] = vis
        if item.get("pr_created_at") and timestamp(item["pr_created_at"]) > at:
            raise StoreError("PR creation cannot follow its discovery observation")
    return discoveries, visibility


def read_only_observation(card, snapshot: dict) -> dict:
    if not isinstance(snapshot, dict):
        raise StoreError("PR observation must be a JSON object")
    at = timestamp(snapshot.get("observed_at"))
    previous = card.latest_observation
    if previous and at <= timestamp(previous["observed_at"]):
        raise StoreError("PR observation must be newer than the saved read-only observation")
    head = snapshot.get("head_sha", "")
    if not isinstance(head, str) or not HEAD.fullmatch(head):
        raise StoreError("PR observation requires a full observed head SHA")
    section = snapshot.get("pull") or {}
    if not isinstance(section, dict) or (section.get("data") is not None
                                         and not isinstance(section["data"], dict)):
        raise StoreError("PR observation pull must contain an object response")
    pull = section.get("data") or {}
    if any(pull.get(k) is not None and not isinstance(pull[k], dict) for k in ("head", "base")):
        raise StoreError("PR observation pull head and base must be objects")
    base_repo = (pull.get("base") or {}).get("repo") or {}
    if not isinstance(base_repo, dict):
        raise StoreError("PR observation base repo must be an object")
    rid = base_repo.get("full_name") or snapshot.get("repository")
    if isinstance(rid, dict):
        rid = rid.get("nameWithOwner")
    number = pull.get("number", snapshot.get("number"))
    if repo_name(rid).casefold() != card.repo_id.casefold() or number != card.number:
        raise StoreError("PR observation identity does not match the card")
    pull_head = (pull.get("head") or {}).get("sha")
    if pull_head and pull_head != head:
        raise StoreError("PR observation has conflicting observed heads")
    return {"observed_at": snapshot["observed_at"], "observed_head": head,
            "snapshot": deepcopy(snapshot)}
