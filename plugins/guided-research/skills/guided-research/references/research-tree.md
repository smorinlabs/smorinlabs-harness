# The research tree

All research lives in a per-project `research/` directory, split by **lifecycle**: durable knowledge in `reference/`, disposable exploration in `topics/`. The split exists because the two kinds of output have opposite fates — leaves get re-read for months; funnels are scaffolding that got you to a decision and then mostly go quiet.

```
research/
  CLAUDE.md                          # the map — always read first
  CONSTRAINTS.md                     # optional: project constraints + overrides for skill defaults
  reference/                         # DURABLE leaves — the reusable library
    tokio-spawn-blocking-2026-07-05.md
    hnsw-algorithm-2026-06-12.md
  topics/                            # DISPOSABLE funnels — exploratory work
    <feature-or-decision>/
      prompts/
        00-landscape.prompt.md       # exact prompt handed to /deep-research (provenance)
        00-landscape.framing.md      # shaping sub-agent's light-search context
      00-landscape.md                # research output: broad, all options
      01-<finalist>.md               # narrower evaluation
      DECISION.md                    # the hinge: choice, why-nots, runner-up, links out to leaves
    _archive/                        # superseded leaves and retired funnels
```

## reference/ — the durable leaf pool

- **Flat, one file per concept.** A leaf is one specific piece of knowledge (an API, an algorithm, a pattern), findable by name — so a leaf discovered while researching feature A is trivially reusable in feature F. Don't nest leaves under the decisions that produced them; that re-encodes the lineage the split exists to escape.
- **Naming: `<library-or-concept>-<YYYY-MM-DD>.md`.** The concept name is the stable identity; the date means *last verified*. Library-or-concept naming (not problem naming) because the leaf's value is the specific knowledge — the problem-to-solution mapping lives in the funnel's DECISION, not the leaf.
- **One live leaf per concept.** On refresh: write the new version with today's date, delete the old file from `reference/`, and move the superseded copy to `topics/_archive/`. Never leave two dated copies of the same concept competing in the pool.
- **Regroup trigger: ~25 leaves.** Stay flat until then — premature grouping recreates the nesting problem. Past ~25, a flat directory stops being scannable and existing leaves get missed (causing re-research, the exact failure this tree prevents). When regrouping, use the natural axis that has emerged (language, then domain), and update CLAUDE.md.

## topics/ — the disposable funnels

- One directory per feature/decision. Files numbered by narrowing order (`00-`, `01-`, ...): each level more specific than the last, converging on implementation.
- `prompts/` holds provenance: for every research pass, the exact `.prompt.md` handed to the engine and the `.framing.md` context that shaped it, paired by prefix. The prompt is written *before* execution so the record exists even if the run fails — when something goes wrong, the first question is "what did we actually ask?"
- **DECISION.md** closes each funnel (format in `artifacts.md`). It links prompt → output → promoted leaf, so the full audit chain runs from a line of code back to the original framed question.
- Rejected branches stay in the funnel, marked rejected in frontmatter — they're the fallback material if the chosen option later fails.
- `_archive/` receives superseded leaves (on refresh) and whole funnels that are fully retired. Leaves' backlinks to archived prompts still resolve.

## CLAUDE.md — the index

An index, not prose. It must let an agent answer "does research already exist for this?" in one read. Contents:

1. **The rule, stated up front:** prefer terminal leaves in `reference/`; check here before starting any research thread; only revisit exploratory funnels when reopening a decision.
2. **Leaf index:** one line per leaf — concept, date, version pin if any, one-phrase summary.
3. **Funnel index:** one line per topic — status (open / decided / retired), the decision if made, link to DECISION.md.
4. **Proposal log:** research that was proposed and declined — topic, date, one-line reason if given. Consult before proposing: don't re-propose declined research unless circumstances have materially changed (new errors, new requirements, the user reopens the topic). This is the interactive-mode counterpart of the autonomous defer flag.
5. **Defer log:** research deferred in autonomous mode, awaiting review.

Update CLAUDE.md whenever a leaf is added/refreshed, a DECISION is written, a proposal is declined, or a thread is deferred. A stale index silently defeats the whole reuse system.

## CONSTRAINTS.md — optional project grounding

If present, the shaping sub-agent reads it for: stack, target platforms (when specific), license requirements, security posture notes, and any overrides to the skill's defaults (thread budget, lease size, depth ceiling, regroup threshold). Absent this file, harvest the stack from the project itself and leave the other constraints out unless the user states them.
