# The enrichment ladder — what to reach for, and what it costs

This is the medium pass (skill step 6) and the judgment gate (step 7).

The question is *not* "what could we add?" — in HTML the answer is always
"anything." The question is **"where is prose working too hard, and what is
the cheapest thing that fixes it?"**

## The gate, restated

Every enrichment must trace to a **pre-registered** difficulty — a row in
`difficulty-map.md` rated ●● or higher, or a defect the critique pass found.
Because the map is written before the draft, a figure cannot be justified
after the fact by asserting the passage was hard. Then:

> **Removal test** — take it out. Is the passage meaningfully harder to
> understand? No → it doesn't ship.

> **Widget test** (stricter, for anything interactive) — does *manipulating*
> it change what the reader understands? If the insight arrives from looking
> at the default state, it is a figure, not a widget. Ship the figure.

Uniform enrichment is a failure mode, not thoroughness. A diagram beside an
already-clear paragraph adds load without adding understanding **and buries
the figures doing real work** — the ones that matter no longer stand out.
This is canon L1.1 (coherence) and L1.2 (signaling) colliding: decoration
costs you twice.

## The ladder

Climb only as far as the difficulty requires. Each rung costs more to build,
more to review, and more for the reader to operate.

| # | Rung | Cost | Fixes |
|---|---|---|---|
| 0 | **Rewrite the prose** | free | Almost everything. Always try this first. |
| 1 | **Typographic signaling** — bold the pivot clause, highlight the changed line | ~0 | "I don't know where to look" |
| 2 | **The real artifact inline** — snippet, diff, config, command output | ~0 | "I can't picture what this actually is" |
| 3 | **A table** | low | Parallel structure across cases; comparisons on shared dimensions |
| 4 | **A static figure** — inline SVG diagram, annotated schematic, small multiples | medium | Spatial relations, structure, topology, magnitude comparison |
| 5 | **A build-up sequence** — the same figure in N states, each adding one element | medium-high | A mechanism with parts that must be learned before they interact |
| 6 | **Step- or scroll-driven progression** — reader advances through states | high | A process or transformation where *order* is the point |
| 7 | **A manipulable model** — the reader changes a parameter and the figure responds | highest | A relationship the reader must *feel* — where intuition changes by moving something |

**Rung 0 is not a formality.** An unclear paragraph with a diagram beside it
is two unclear things. Fix the writing first; then see whether the figure is
still needed. Frequently it isn't.

## Matching the difficulty to the rung

| The difficulty is… | Reach for |
|---|---|
| the reader can't tell what matters in a block of code | 1 — signal the line |
| the thing is abstract and never instantiated | 2 — show the real artifact |
| several cases vary along the same dimensions | 3 — table, or 4 as small multiples |
| the parts have a spatial or topological relation | 4 — diagram |
| quantities must be compared | 4 — see `visual-encoding.md` (and `dataviz` if present) |
| there are too many parts to take in at once | 5 — build up, one element per step |
| the order of operations *is* the explanation | 6 — stepped progression |
| the reader must develop intuition for a trade-off | 7 — manipulable model |
| the result is counterintuitive | 2 + 4 — the real numbers, and a figure that shows why |

## When a control genuinely earns its place

Rung 7 is right when **the manipulation is the explanation** — when what the
reader learns comes from watching the output change as they move the input.
A backoff curve whose shape you feel by dragging the jitter factor. A
consensus protocol you understand by killing a node. A layout algorithm that
makes sense once you resize the container.

It is wrong when it merely animates what a caption already said. That is the
common failure: a control that replays a fixed narrative is a figure with
extra steps and worse accessibility.

Practical constraints that come with rung 7 here:

- **Self-contained, vanilla JS.** No CDN, no framework, no build step. If it
  can't be done in inline SVG plus a few dozen lines of plain JS, it is
  probably above this skill's weight and the figure is the right call.
- **Keyboard-operable.** A drag-only control excludes readers.
- **Meaningful default state.** The page must still explain if nobody
  touches anything — many readers won't, and print/PDF never will.
- **Respect `prefers-reduced-motion`.**

## Calibration targets

Not rules — reference implementations. When unsure whether an enrichment is
pulling its weight, compare against how these treat the same problem.

- **Bret Victor** — *Explorable Explanations*, *Up and Down the Ladder of
  Abstraction*. The origin of the reactive document: the reader manipulates
  the model, not the prose. The source of the rung-7 bar.
- **Bartosz Ciechanowski** — *Mechanical Watch*, *GPS*, *Internal Combustion
  Engine*. Current best-in-class long-form. Every concept arrives with a
  manipulable diagram, and each diagram adds exactly one element to the one
  before it — canon L1.6 (pre-training) executed about as well as it can be.
- **Amit Patel / Red Blob Games** — interactive tutorials on pathfinding and
  hex grids. The standard for a diagram embedded *in* the prose rather than
  parked beside it.
- **Nicky Case** — *Parable of the Polygons*, *The Evolution of Trust*.
  Short-loop playable explanations; proof that rung 7 doesn't require scale.
- **Distill.pub** (Chris Olah, Shan Carter; *Communicating with Interactive
  Articles*, *Research Debt*) — the explicit theory of the form, and the
  argument for why bad explanation compounds into a tax on a whole field.
- **Mike Bostock** — animated transitions as explanation; object constancy
  (the reader tracks a mark through a change because it stays the same
  mark).
- **Giorgia Lupi** — data humanism. The counterweight when minimalism
  strips out the thing that made the subject matter to a person.

## Gotchas

- **Don't let the ladder become a plan.** You are not working up it; you are
  finding the lowest rung that fixes each specific difficulty. A good
  explainer is mostly rungs 0–2 with a few well-chosen 4s.
- **One rung-7 widget per page is usually plenty.** They compete for
  attention with each other, and each one the reader skips makes the next
  one likelier to be skipped.
- **A figure that needs a paragraph to explain it has failed.** Annotate the
  figure instead (`visual-encoding.md`, E6).
- **Check enrichment density at the end.** If more than roughly a third of
  the page is figures, re-run the removal test on all of them — that ratio
  usually means enrichment stopped being diagnostic and became a habit.
