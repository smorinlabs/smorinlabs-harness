# document-merge

Merges N overlapping markdown documents into M consolidated outputs (M ≤ N)
with zero information loss and full traceability. Every non-trivial synthesis
decision gets a stable `CFL-XXX` id that round-trips between an inline marker
in the merged doc and an entry in `decisions-and-conflicts.md`; every source
line range is mapped to an output section in a topic-to-source map; originals
are SHA-256-snapshotted before the merge, archived byte-identical after, and
re-verified against the baseline. A **lite** path (2 sources, low conflict)
skips the CFL log and validation script for a plain consolidated doc + diff
report; **full** (≥3 sources, or overlapping/conflicting content, or the user
wants traceability) runs the 8-phase workflow and can dispatch one subagent
per output doc via `superpowers:subagent-driven-development`.

**Triggers on:** "merge these docs", "consolidate this research", "combine
into one document", "dedupe these notes", "reconcile overlapping specs",
"build a single source of truth", or any request with two or more overlapping
markdown files that should become one clean output — even without the word
"merge".
**Arguments:** none — tier (lite/full), output count, and archive location are
asked up front.

## Install

| Mode | When | How |
|---|---|---|
| Plugin (recommended) | You just want to use it | `/plugin install document-merge@smorinlabs-harness` |
| Dev symlink | You want to tweak/iterate | `git clone https://github.com/smorinlabs/smorinlabs-harness` then `ln -s "$(pwd)/smorinlabs-harness/plugins/document-merge/skills/document-merge" ~/.claude/skills/document-merge` |
| Direct copy | No marketplace access | copy `plugins/document-merge/skills/document-merge/` into `~/.claude/skills/` |

**Codex:** register the marketplace in `~/.codex/config.toml`
(`[marketplaces.smorinlabs-harness]`) and enable the plugin — or use the
dev-symlink path, also linking into `~/.agents/skills` (Codex's current
skills location).

## Example session

> "I have three overlapping design-note drafts, make me one source of truth"
> → asks for sources, output location, split count, archive location, and
> whether the source dir is git-tracked; snapshots SHA-256 of all three;
> builds the topic-to-source map; merges into one consolidated doc, logging
> two `CFL-XXX` conflicts; runs the coverage audit and validation script (both
> PASS); archives the originals via `git mv` and confirms the post-archive
> diff against the Phase 1 baseline is empty.
