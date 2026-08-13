# Artifact forms

Forms available beyond prose, lists, and tables, and the rule for choosing among
them. Every form here is subject to the frame in `SKILL.md`: state why the
artifact is present, show it exactly, and state what the reader should take from
it.

## Diagrams

### When a diagram earns its place

Use a text diagram only when the reader must hold **three or more relationships
at once**. Two components and one arrow is a sentence; write the sentence.

This mirrors the heuristic that governs tables — three or more items with shared
fields or dimensions — so one threshold covers both forms. A diagram below the
threshold costs vertical space and reading time without reducing inference.

Do not draw a diagram to decorate a section, to restate a list, or to show a
sequence the reader will never need to reproduce.

### Selection: relationship to form

| Relationship to show | Form |
|---|---|
| Components and how data moves between them | Box-and-arrow |
| Containment, hierarchy, file layout | Indented tree |
| Ordered interaction over time | Sequence ladder |
| States and what triggers each transition | State diagram |
| Layout, proportion, or structure of a region | Box sketch |
| Two variants compared | Side-by-side columns |
| Magnitude or position on one axis | Bar or number line |

### Box-and-arrow

Label the arrows, not only the boxes. An unlabeled arrow states that something
flows without saying what.

```
[Client] ──HTTP──> [API] ──SQL──> [Primary DB]
                     │
                     └──cache read──> [Redis]
```

### Indented tree

Use for containment and file layout. Keep one item per line and annotate only
the entries the reader must act on.

```
plugins/
├── clear-technical-communication/
│   ├── plugin.meta.toml          <- version lives here
│   └── skills/
│       └── clear-technical-communication/
│           ├── SKILL.md
│           └── references/
└── other-plugin/
```

### Sequence ladder

Use when order over time is the point. Columns are participants; time runs down.

```
Client          API           Worker
  │              │              │
  ├─ POST /job ─>│              │
  │              ├─ enqueue ───>│
  │<─ 202 ───────┤              │
  │              │              ├─ process
  │              │<─ done ──────┤
```

### State diagram

Label every transition with what triggers it. An unlabeled transition hides the
condition, which is usually the part the reader needs.

```
idle ──start──> running ──complete──> done
                  │
                  └──error──> failed ──retry──> running
```

### Box sketch

Use for layout and proportion, not for precise dimensions.

```
┌─────────────────────────────┐
│ header                      │
├──────────┬──────────────────┤
│ sidebar  │ content          │
│          │                  │
└──────────┴──────────────────┘
```

### Side-by-side comparison

Align the two variants so the differing line sits at the same height in both
columns. Misaligned columns force the reader to search for the difference.

```
before                        after
─────────────────────────     ─────────────────────────
git pull                      git pull --ff-only
  merges on divergence          fails on divergence
```

### Bar or number line

Use for rough magnitude, never for precise values. Give the value in text
alongside the bar.

```
p50  ▏████░░░░░░░░░░░░░░░░   40ms
p95  ▏████████████░░░░░░░░  120ms
p99  ▏████████████████████  340ms
```

## Annotation markers

Mark parts of an artifact and reference the marks in prose. Do not describe a
position, such as "the third line" or "the box on the right"; positions shift
when the artifact is edited, and the reader must count to follow along.

```
[Client] ──> [Queue] ──> [Worker] ──> [DB]
              (1)          (2)
```

> (1) Unbounded — grows without limit under load.
> (2) Fixed pool of four workers.

Markers also work inside code:

```python
def handler(event):
    payload = parse(event)      # (1) raises on malformed input
    return dispatch(payload)    # (2) retried up to three times
```

## Surface-appropriate rendering

Choose the form the reader's surface can actually render.

| Form | Terminal | GitHub | Rendered page |
|---|---|---|---|
| ASCII diagram | renders | renders | renders |
| Mermaid | raw text | renders | renders |

ASCII is the universal fallback. Use Mermaid only when the destination is known
to render it and the diagram is complex enough to justify the risk. A Mermaid
block that reaches a terminal is worse than no diagram, because the reader sees
syntax where a picture was promised.

## Before-and-after pairs

Show the same thing in two states rather than describing the change. Keep both
states aligned and change one thing at a time, so the difference is
attributable to a single cause.

```
before: git pull
after:  git pull --ff-only
```

> The change makes a divergent history fail loudly instead of creating a merge
> commit.

Boundary against `explain`: here a before-and-after pair states a change
precisely inside a communication artifact — a rewrite, a configuration
migration, a diff. In `explain`, a before-and-after pair is a teaching device
for building understanding. Same shape, different job.

## Counterexamples

Pair a definition or boundary with a case that does not qualify. A
counterexample sharpens a boundary faster than more description does, and is the
cheapest way to prevent one specific misreading.

> A verbatim technical name is one that appears in code, a command, an API, or a
> specification: `--ff-only` qualifies. `the fast-forward-only flag` does not —
> it is a description of that name, not the name itself.

Use a counterexample when a definition has a near neighbor that readers
routinely confuse with it. Do not add one to a definition with no plausible
misreading.

## Units and reference scale

Never state a bare number. Give the unit and a comparison point that makes the
value interpretable.

| Instead of | Write |
|---|---|
| `200ms` | `200ms, roughly 3x the p50` |
| `it grew a lot` | `it grew from 40 to 340 rows, an 8.5x increase` |
| `the file is large` | `the file is 2,900 lines, about 4x the next largest` |

This rule is distinct from the `Unsupported estimate` row in
`references/common-errors.md`. That row governs where a number came from: its
source, calculation, or confidence. This rule governs whether the reader can
interpret the number once given. A number can have a sound basis and still be
uninterpretable without a reference scale.
