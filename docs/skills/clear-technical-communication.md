# clear-technical-communication

A reader-centered technical-communication skill that aggressively catches the
failures sentence simplification alone misses: absent purpose or context,
undefined identifiers and notation, hidden causal logic, mixed facts and
proposals, multidimensional comparisons trapped in prose, unsupported
exclusions or estimates, false choices, owner dumping, and decision requests
without consequences or recommendations. It catches the opposite failure too:
precise names stripped out or left unexplained, code and diagrams dropped in
without a frame, and mechanisms asserted with no concrete example. It audits
against the four ISO 24495-1 reader outcomes (relevant, findable,
understandable, usable), uses selected ASD-STE100 mechanics for sentence and
terminology control, and then rewrites the communication without inventing
missing facts.

Its governing principle is that **every embedded artifact carries a frame**: the
artifact supplies precision, the prose supplies meaning, and neither ships
alone. A verbatim technical name is reproduced exactly and paired with a
description at first use; established domain terms are defined at first use;
only invented local metaphors are replaced. Quotations, commands, and captured
output are never restyled. The bundled common errors catalog gives detection
signals, prescribed corrections, and compact before/after examples; a companion
artifact-forms reference covers the diagram catalog and selection rule,
annotation markers, before-and-after pairs, counterexamples, and units with
reference scale; two full worked examples cover coverage-matrix prose and
owner-decision requests.

**Triggers on:** "make this draft clearer", "this message is not
understandable", "rewrite this technical message", "review this for clarity", "make this decision
request actionable"; and proactively before dense artifacts such as design
summaries, plans, status reports, handoffs, comparisons, or owner-decision
requests are sent. It does not teach the underlying subject (`explain`),
prototype artifact form (`design-by-elements`), conduct decisions
(`question-walkthrough`), or render reader-only actions (`reader-steps`).
**Arguments:** optional `[target]` identifying the text, file, diff, commit, or
report to review or rewrite.

## Install

| Mode | When | How |
|---|---|---|
| Plugin (recommended) | You just want to use it | `/plugin install clear-technical-communication@smorinlabs-harness` |
| Dev symlink | You want to tweak/iterate | `git clone https://github.com/smorinlabs/smorinlabs-harness` then `ln -s "$(pwd)/smorinlabs-harness/plugins/clear-technical-communication/skills/clear-technical-communication" ~/.claude/skills/clear-technical-communication` |
| Direct copy | No marketplace access | copy `plugins/clear-technical-communication/skills/clear-technical-communication/` into `~/.claude/skills/` |

**Codex:** register the marketplace in `~/.codex/config.toml`
(`[marketplaces.smorinlabs-harness]`) and enable the plugin — or use the
dev-symlink path, also linking into `~/.agents/skills` (Codex's current
skills location).

## Example session

> "These three owner questions are hard to understand. Review them and rewrite
> the decision request."
> → identifies the intended owner and blocked work; scans the common-errors
> catalog; removes process chatter and opaque noun piles; glosses requirement
> IDs; turns every item into the same Context / Constraint / Decision / Options
> and effects / Recommendation / Response structure; flags missing option
> analysis rather than inventing it; and returns the usable decision request
> before the diagnostic findings.
