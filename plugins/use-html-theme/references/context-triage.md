# Context triage — the shared preflight

Both HTML page skills in this plugin run this BEFORE generating anything:

- `html-codesign` — a page that **answers** open questions
- `html-explain` — a page that **explains** settled material

They sit one step apart and are easy to confuse, because both are reached
by the same request shape: *"make me an HTML page about what we've been
working on."* This file is the single routing authority; neither skill
re-derives it.

Read from either skill's directory as `../../references/context-triage.md`.

## Why a preflight at all

The failure mode is expensive and silent: a fully-rendered page about the
wrong thing. A codesign page built from questions the user already answered
is worse than useless — it re-litigates settled work. An explainer aimed at
the wrong artifact wastes the whole page. Both take real effort to build and
neither announces its own wrongness.

Confirming costs one question. **Always pay it.**

## Step 1 — Read the recent context

Scan the conversation back to the last clear topic boundary. Where the
conversation is thin, widen to the working tree: recent commits
(`git log --oneline -20`), an open PR, a design doc or spec touched
recently, PROJECTS.md rows in flight.

## Step 2 — Classify what is actually there

Sort the material into two buckets. Count honestly — the counts are the
confidence signal.

**Open forks** — genuinely undecided:

- questions asked and not answered
- options laid out with no pick made
- "should we X or Y", "still need to decide", "open question:"
- TODOs explicitly marked undecided
- a plan blocked on an unanswered dependency

**Settled material** — decided, done, or observed:

- a design proposed or agreed
- an implementation finished or merged
- test results, benchmarks, output
- a spec or plan written and accepted
- a decision made, with its rationale

**A question that was asked AND answered belongs in the settled bucket.**
It is explainer material — a deep dive on how it was resolved — not
codesign material. Never re-pose it.

## Step 3 — Verdict and confidence

| Open forks | Settled material | Verdict | Confidence |
|---|---|---|---|
| several | little | **codesign** | high — say so plainly |
| little | several | **explain** | high — say so plainly |
| several | several | either — present both | low — let the user pick |
| little | little | neither is grounded | none — ask what the target is |

Density is the signal. Several live, unanswered forks in recent context is
strong evidence the user wants them resolved; a run of finished work with
no open forks is strong evidence they want it understood. State the
confidence in the gate — "this looks clearly like X" reads differently from
"this could go either way", and the user should be able to tell which
situation they are in.

## Step 4 — The gate — ALWAYS, no exceptions

Confirm before generating. This fires:

- when the skill was inferred from a natural-language request
- **when the user invoked the skill explicitly** (`/html-codesign`)
- **when the user supplied an argument** naming a topic or direction

An explicit invocation settles *which page type*, not *what goes in it*.
An argument narrows the target but rarely pins the exact set — "codesign
the caching questions" still leaves which caching questions, and whether
the ones you found are the ones meant. So an argument changes the gate's
job from *"what are we doing?"* to *"confirming this reading"*, and it
shortens the question. It never removes it.

Present the gate as ONE AskUserQuestion, with the triage verdict as the
recommended option. Always include:

- the **escape hatch** — a different topic entirely
- the **sibling** — the other page type, when triage leaves any doubt

## The overlap, stated plainly

These genuinely overlap on one case, and both skills should name it rather
than pretend the boundary is clean:

> A recently-asked question can go either way. **codesign** poses it for
> decision, with a recommendation. **html-explain** does a deep dive on
> it — what it turns on, what each branch costs — without asking for a pick.

When a user's request could mean either, offer both and let them choose.
Guessing here is the one place triage most often gets it wrong.

## Gate shapes

Adapt the wording; keep the structure. The point of both is that the user
sees **the actual material** before committing to a page.

### codesign

List every question you would put on the page, each with the ID it will
carry and the recommendation you would argue. Unanswered only.

```
Recent context has 4 open questions. Here's how I'd shape the page:

  sec-01  Should the fallback ship as its own module, or fold into core?
          → I'd argue fold in — one less package to version.
  sec-02  Do we keep the v1 endpoint alive through the migration?
          → I'd argue yes, behind a deprecation header.
  sec-03  Who owns the rotation runbook — platform or on-call?
          → Genuinely neutral; I'd lay out both and not recommend.
  sec-04  Ship behind a flag, or straight to default-on?
          → I'd argue flag — the blast radius is the whole write path.

A codesign page poses each of these with a reasoned recommendation and
lets you pick, skip, or ask back. It doesn't decide for you.

Generate it for these four?
```

Options: **generate** (recommended) · **just answer them here in chat**
(`question-walkthrough`) · **wrong set — these are settled, I want an
explainer** · **different topic entirely**.

### html-explain

Propose targets mined from context. Include at least one **adjacent** area
— something the material implies but never covered — since the gap the user
feels is often not the thing they named.

```
Recent context looks settled rather than open — the retry work landed and
the tests are green. Candidates for the explainer:

  · What the retry refactor actually changed, and why the old shape broke
  · Deep dive: the backoff design decided Tuesday — the mechanism, and
    what it costs under load
  · What the load-test results showed, read against what we expected
  · Adjacent — how this interacts with the circuit breaker. Not discussed,
    but the design implies a question there.

What should the page explain?
```

Options: the strongest candidate (recommended) · a second candidate ·
**these are still open — I want a codesign page instead** · **something
else entirely**.

## Handoff

When the gate routes to the sibling, hand over the triage you already did —
the classified material and counts — so the other skill does not re-scan the
conversation and does not re-ask the user what they just answered.
