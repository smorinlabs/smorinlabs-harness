"""Compare additional diagnostic feedback costs; required final CI is retained."""
from __future__ import annotations

import math

LOCAL_PHASES = ("snapshot_s", "transfer_s", "setup_s", "checks_s", "collect_s")
REMOTE_PHASES = ("submit_s", "queue_s", "setup_s", "checks_s", "collect_s")


def total(phases, names):
    if not isinstance(phases, dict):
        raise ValueError("phase timings must be an object")
    values = []
    incomplete = False
    for name in names:
        value = phases.get(name)
        if value is None:
            incomplete = True
            continue
        if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value) or value < 0:
            raise ValueError("phase timings must be finite nonnegative seconds or null")
        values.append(value)
    return None if incomplete else sum(values)


def choose(costs, context, power_state):
    if costs is not None and not isinstance(costs, dict):
        raise ValueError("cost evidence must be an object")
    compatible = bool(costs and costs.get("schema_version") == 1 and costs.get("context") == context)
    costs = costs if compatible else {}
    local_names = LOCAL_PHASES + (() if power_state == "running" else ("startup_s",))
    local = total(costs.get("local", {}), local_names)
    remote = total(costs.get("remote", {}), REMOTE_PHASES) if costs.get("remote_available") is True else None
    if local is None:
        decision, reason = "measure", "no compatible complete local estimate; use one bounded informative check, then retain its phase timings"
    elif remote is None:
        decision, reason = "local", "local cost is known; no suitable measured CI alternative was supplied"
    elif local < remote:
        decision, reason = "local", "local diagnostic feedback is cheaper for this scope and current VM state"
    else:
        decision, reason = "remote", "the suitable CI alternative costs no more than local preparation and execution"
    return {"decision": decision, "reason": reason, "compatible_costs": compatible,
            "local_seconds": local, "remote_seconds": remote, "power_state": power_state,
            "evidence_source": costs.get("source", "unmeasured"),
            "required_ci": "ordinary required CI still runs after the validated push; it is not counted as avoided"}
