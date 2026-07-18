# Worked examples

Two full outputs to calibrate against. The scenarios are generic; the shape is
the contract.

## Default mode

> **User:** /explain the retry backoff change in this PR

**What it is** — the HTTP client now waits exponentially longer between
retries instead of retrying immediately.

**Context** — the client retries failed requests up to 3 times. Until now all
three retries fired back-to-back, so a rate-limited server got hammered again
within milliseconds and every retry burned against the same outage window.

**Example** — before → after (`src/http/client.py`):

```python
# before
for attempt in range(3):
    resp = session.get(url)
    if resp.ok:
        return resp

# after
for attempt in range(3):
    if attempt:
        time.sleep(2 ** attempt)      # 2s, then 4s
    resp = session.get(url)
    if resp.ok:
        return resp
```

A 429 that previously produced 3 requests in ~50 ms now spreads them over
~6 s — the final attempt lands after the typical rate-limit window resets.

**What this gets you** — rate-limited calls actually succeed on retry instead
of exhausting all attempts inside the outage; upstream sees ~75% fewer
hammer-bursts during incidents.

Want to go deeper — why exponential rather than fixed, and how the jitter
decision was made?

## Options mode

> **User:** show me examples of options A and B for config layering

**Option A — flat file with prefixed keys.** One `config.toml`, scope encoded
in the key name:

```toml
default.timeout = 30
ci.timeout = 120
```

Reads and diffs trivially; every consumer greps one file. But scope rules
live in naming conventions, so nothing stops `ci.timeout` and `CI.timeout`
from coexisting.

**Option B — one file per layer, merged at load.** `config/default.toml` +
`config/ci.toml`, deep-merged in a documented order:

```toml
# config/ci.toml — only the overrides
timeout = 120
```

Layer boundaries are structural, and a layer can be added without touching
the others' files — at the cost of a merge step readers must know about.

**Recommendation: B, because the failure mode of A is silent.** A's prefix
collisions produce wrong-but-valid configs that nothing flags; B's worst
failure (missing layer file) is loud at load time. **Runner-up: A** — and it
stays the right call if there will only ever be two layers, where a merge
engine is more machinery than the problem deserves.

If this feeds a decision: risk is low either way (both reversible in one
sitting); confidence in B is high if a third layer is plausible, medium
otherwise.
