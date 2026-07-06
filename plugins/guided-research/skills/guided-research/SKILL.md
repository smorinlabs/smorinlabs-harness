---
name: guided-research
description: Orchestrates deep research at high-value moments and organizes the results for reuse. Use this skill whenever you are (1) making an architectural decision — choosing between libraries, algorithms, frameworks, or structural approaches; (2) kicking off a new project, major feature, or milestone where the problem domain has established best practices (billing, auth, caching, CLI design, etc.); (3) about to go deep on how a chosen library or technique works for a specific use case; or (4) hitting repeated errors with an unfamiliar API or pattern after a couple of ordinary web searches. Also use it when the user asks for deep research, thorough research, or research on options/best practices/approaches — and consult it during planning phases, before writing PRDs or implementation plans, even if the user doesn't say the word "research." Agents habitually under-research — a couple of shallow web searches at a decision point is usually a signal this skill should have fired.
---

# Guided Research

An orchestration layer around the built-in `/deep-research` skill. It decides **when** deep research is worth doing, **shapes** the research prompt with project constraints, **invokes** the built-in engine, and **organizes** the output into a durable, reusable research tree. It does not reimplement research — the built-in does the searching, verification, and synthesis.

Why this exists: agents bias toward two or three shallow web searches at moments that deserve real investigation. This skill counters that bias with explicit triggers, a value test, and a structure that ensures knowledge gained once is never re-researched.

## The four triggers

1. **Architectural decision** — selecting among libraries, algorithms, frameworks, or structural approaches. A clear decision point; almost always worth researching.
2. **Domain best-practice** — entering a broad feature where the *class* of problem has established wisdom (e.g., "how are billing cancellations and immutable transactions typically handled?", "what are best practices for CLI design?"). Not a library choice — accumulated conventions and pitfalls you need *before* framing the architecture. Usually the first research pass on a big feature, upstream of the architecture decision.
3. **Implementation deep-dive** — how an already-chosen library or technique works for the exact use case at hand.
4. **Error-driven** — repeated failures with an unfamiliar API or pattern after a couple of ordinary web searches. Shallow research has demonstrably failed; go deeper.

## The value test

Every trigger runs through the same question: **is this a high-value point to do deep research?**

Work classification informs the *likelihood* of value but never sets the verdict:

- **Incremental** (extending known patterns/libraries) — least likely to need it. A simple CLI, even brand new, probably doesn't.
- **Expansive** (new surface on known libraries) — more likely, especially if a new subordinate library sneaks in.
- **Exploratory** (new algorithm, technique, library, or domain) — most likely; architecture and best-practice triggers almost always clear the bar here.

The classification is a prior, not a gate: an error-plagued incremental task can still clear the bar despite the low prior.

## Mode gating — what happens when a trigger clears the bar

- **Interactive** (a human is present and engaged): **propose**, don't run. Say what you'd research and why it's high value — e.g., "I think deep research would be high value on topics X and Y. Want me to kick that off?" The user can accept, redirect to a different topic, or pass. If a proposal is declined, record it in the proposal log (see `references/research-tree.md`) and do not re-propose the same research unless circumstances materially change.
- **Autonomous** (long-running task, goal loop, no human in the loop): **auto-run** — but hold a *stricter* value bar than you would for a proposal, since no one is there to veto. Skipping needed research in autonomous mode is the failure this skill exists to prevent: a detailed spec with a research-shaped gap means research the gap and keep moving.
- **By-hand** (the user explicitly invokes research on a topic): run immediately. The value decision was already made by the user.
- **Defer** (autonomous only): when value says yes but budget says no, don't silently skip and don't rabbit-hole — leave a loud flagged note ("Deferred deep research on X — review when available") and continue.

## Budget

- Default **3 deep-research threads per feature/milestone**. A "feature" is the current planning unit — the active plan doc, milestone, or explicitly stated task; when ambiguous, the current user-stated goal.
- Wanting a 4th thread triggers a fresh value check. Clearing it grants a **lease of 2 more**; re-check again after that.
- **Lateral fallback is exempt from all budgets and depth limits**: when a made choice fails or is blocked and you return to research the next-ranked option, that is recovery, not a new thread. It only applies after a choice was actually made and concretely failed — never speculatively.

Defaults here (3-thread budget, +2 lease, 3-level depth ceiling, 25-leaf regroup threshold) are overridable by a project's `research/CONSTRAINTS.md` if it specifies different values.

## Stopping rule

A research thread is **done** when both hold:

1. **You can name the choice** — a specific library/algorithm/pattern, not a category. A *conditional* choice counts ("A under conditions X, B under conditions Y") as long as it is actionable.
2. **A terminal leaf resolves the exact use case** — a synthesized reference complete enough that implementation reads from the leaf, not from a fresh search.

If either fails, the failure names the next narrowing pass. In autonomous mode, cap narrowing at **3 levels deep per thread** (landscape → evaluation → one focused dive); if the test still fails at the ceiling, the question is probably wrong — defer and flag rather than narrow further. Lateral moves to a sibling option don't count against depth.

## Workflow

0. **Check the tree first.** Before evaluating any trigger, check `research/CLAUDE.md` and `research/reference/` for an existing leaf that answers the question (see "Reuse before research"). A current leaf resolves the request with no new research — this applies even to error-driven triggers, where the fix is often a gotcha already documented in a leaf. Only proceed to trigger evaluation if no current leaf covers the need.
1. **Detect** a trigger; apply the value test (informed by work classification); gate by mode.
2. **Shape the prompt in a sub-agent** (keep the main context clean). The shaping sub-agent:
   - Runs light web searches to frame the field.
   - Harvests project constraints, *relevance-filtered*: **stack** always; **target platform** only when specific; **license** only when the user/project declares requirements; **security posture** only when the domain makes it relevant (auth, payments, untrusted input). A constraint that doesn't bind is noise that skews the search. Sources: `research/CONSTRAINTS.md` if present, otherwise the project itself.
   - Selects the per-trigger template from `references/templates.md`.
   - Writes `<NN>-<topic>.framing.md` (its search context) and `<NN>-<topic>.prompt.md` (the final prompt) into the topic's `prompts/` directory — the prompt file is the provenance record and is written *before* execution, so it survives a failed run.
3. **Invoke the built-in `/deep-research`** with the shaped prompt. Make the prompt complete enough to pre-empt the built-in's clarifying questions — in autonomous mode there is no one to answer them; the harvested constraints are those answers, front-loaded. If the built-in is unavailable (older version, bundled skills disabled), fall back to the sub-agent procedure in `references/fallback-research.md` — never silently skip the research.
4. **Normalize the output** into the research tree (`references/research-tree.md` for layout, `references/artifacts.md` for leaf/DECISION formats): write funnel files under `topics/`, promote the terminal leaf to `reference/`, write `DECISION.md` linking prompt → output → leaf, including confidence, the conditional structure if the answer is conditional, why-nots for rejected options, and an explicit ranked runner-up (this is what makes lateral fallback instant later).
5. **Return a thin pointer** to the main conversation: leaf path plus a one-line outcome. Never paste the leaf body back — the file system is the channel; the return is a receipt. Read the leaf from disk only when implementation actually needs it.

## Reuse before research

Before starting any thread, check `research/CLAUDE.md` and `research/reference/` for an existing leaf that answers the question. A current leaf means no new research. A stale leaf (version mismatch, old date) means refresh it: replace the file in `reference/`, update the filename date, and move the superseded copy to `topics/_archive/`.

## Reference files

- `references/templates.md` — the four per-trigger prompt templates and their capture sets. Read when shaping a prompt.
- `references/research-tree.md` — directory layout, naming, CLAUDE.md index spec, proposal log, archive rules. Read when writing outputs or setting up a new tree.
- `references/artifacts.md` — leaf and DECISION.md formats, frontmatter, confidence and conditional-recommendation structure. Read when normalizing results.
- `references/fallback-research.md` — the self-contained research procedure when `/deep-research` is unavailable. Read only in that case.
