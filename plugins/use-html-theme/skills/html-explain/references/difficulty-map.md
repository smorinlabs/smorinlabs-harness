# The difficulty map — decide where the emphasis goes, before drafting

This is skill step 3. It runs **after the outline and before any prose**.

## Why it must come before the draft

There are two different kinds of hard, and only one of them is findable by
critiquing a draft:

| | The question | Knowable | Fixed by |
|---|---|---|---|
| **Intrinsic** | Which parts of the *subject* are hard? | from the outline, before writing | where you spend words and figures |
| **Extraneous** | Which parts did *my writing* make hard? | only after drafting | rewriting |

The clarity critique (step 5) catches extraneous difficulty. It cannot
catch intrinsic difficulty, because a beautifully-written paragraph about a
genuinely hard idea reads fine to its author and still loses the reader.

Deciding emphasis before drafting also closes the obvious loophole in
"enrich only where comprehension breaks": a **pre-registered** difficulty
list means a figure cannot be justified after the fact. Step 7's removal
test checks each enrichment against this map. No entry here, no figure
there.

## The output

A short table — one row per outline section. Keep it working-notes terse;
it is scaffolding, not a deliverable.

| Section | Hard? | Kind of hard | Budget | Likely remedy |
|---|---|---|---|---|
| Why retries broke | ●●● | counterintuitive — the obvious fix makes it worse | 40% | real numbers + figure showing why the prior fails |
| The backoff formula | ●● | parameter trade-off | 25% | manipulable curve (rung 7) |
| Where it's wired in | ● | just plumbing | 10% | one snippet |
| Rollout | ○ | trivial | 5% | one sentence |

Three columns do the real work.

### Rating — be honest and be spiky

Rate intrinsic difficulty only: how hard is this **for a reader who was
never in this conversation**, assuming it is written well.

A map where everything is ●● is a map that wasn't made. Real subjects are
spiky — usually one or two genuinely hard ideas surrounded by context that
is merely unfamiliar. **Find the spike.** If you can't identify which part
is hardest, you don't understand the subject well enough to explain it yet;
go back to the artifacts.

### Kind of hard — this is what picks the remedy

"Hard" is not one thing, and each kind has a different fix. This table is
the reason the map is worth making:

| Kind | Signature | Reach for |
|---|---|---|
| **Many interacting parts** | can't hold it all at once | pre-training (L1.6) → build-up sequence (rung 5) |
| **Unfamiliar prerequisite** | reader lacks a concept the rest needs | pre-training; define before first use |
| **Counterintuitive result** | the reader's prior is actively wrong | concreteness (L3.2) + real numbers + show *why* the prior fails |
| **Long causal chain** | A→B→C→D, thread easily lost | answer first (L3.1) + segmenting (L1.5) |
| **Many similar cases** | tedious; they blur together | small multiples (E3) or a table (rung 3) |
| **Dense quantitative** | numbers that must be compared | encoding rules (E1/E2); `dataviz` if present |
| **Spatial or structural** | prose can't hold the shape | diagram (rung 4) |
| **Parameter trade-off** | needs a *felt* sense of a relationship | manipulable model (rung 7) |
| **Invisible mechanism** | happens where you can't watch it | annotated schematic; make the hidden visible |
| **Not actually hard** | familiar, mechanical | one sentence; resist explaining it |

### Budget — the emphasis decision

Allocate the page. The top one or two rows should take **the clear
majority** of the words and nearly all of the figures.

**The failure mode this exists to prevent is uniform depth** — explaining
every section at the same level of detail. It is the default outcome, it
feels thorough, and it is the most common reason an explainer doesn't land:
the hard part got the same treatment as the trivial part, so the reader
spent their attention evenly on something that wasn't evenly hard.

Compressing an easy section to one sentence is not a gap. It is the budget
being spent correctly.

## Selecting the principles

The **Kind of hard** column already names them. Collect the distinct
principles across the rows, take the two or three that recur, and write
against those. That is step 3's principle selection — derived, not chosen
in the abstract.

## What carries forward

- **To the draft (step 4)** — the budget, as a target shape.
- **To the critique (step 5)** — the ratings: re-read the ●●● sections
  hardest, since that is where a reader will actually fall out.
- **To enrichment (steps 6–7)** — the pre-registered list. Every figure and
  widget must trace to a row rated ●● or higher.

## Gotchas

- **Don't show this table to the reader.** It is your scaffolding. A page
  that announces "this next part is the hard one" is fine; a page that
  publishes its own difficulty ratings is talking about itself instead of
  its subject.
- **Difficulty is not importance.** Something can be critical and easy — say
  it once, clearly, and move on. Budget follows difficulty, not stakes.
- **Re-rate after the draft if the shape changed.** If drafting revealed
  that a ● section was hiding a ●●● idea, update the map and re-budget
  rather than quietly bolting a figure onto it.
