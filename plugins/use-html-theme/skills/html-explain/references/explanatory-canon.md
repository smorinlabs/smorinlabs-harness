# The explanatory canon — aids, indexed by symptom

**These are advisory.** The goal is clear communication, not compliance.
A page that breaks one of these and lands is better than a page that
satisfies all of them and doesn't.

They are indexed by **symptom** rather than listed as a checklist, because
that is how they are actually useful: you reach for one when a draft is
failing in a particular way. Reciting all of them up front produces a page
written against everything and therefore against nothing.

Two layers here — how much may be on screen (cognitive load) and what order
ideas arrive in (structure). Visual encoding is `visual-encoding.md`;
interactive form is `enrichment-ladder.md`.

---

## Symptom index

| The draft feels… | Reach for | Section |
|---|---|---|
| bloated, hard to know what matters | Coherence | L1.1 |
| like the reader won't know where to look | Signaling | L1.2 |
| like it repeats itself between text and figure | Redundancy | L1.3 |
| like the eye ping-pongs between label and thing | Spatial contiguity | L1.4 |
| like one long undifferentiated wall | Segmenting | L1.5 |
| like it throws you into the deep end | Pre-training | L1.6 |
| overwhelming even though each part is simple | Cognitive load budget | L1.7 |
| detailed but you can't see the whole | Overview first | L1.8 |
| like a detective story — conclusion at the end | Answer first | L3.1 |
| abstract, slippery, hard to hold onto | Concreteness | L3.2 |
| like it assumes things the reader doesn't know | Curse of knowledge | L3.3 |
| like it describes rather than shows | Classic style | L3.4 |
| like it names things without explaining them | Mechanism over definition | L3.5 |
| like a sequence of steps that doesn't flow | Closure between frames | L3.6 |
| like a pile of facts with no arc | Narrative | L3.7 |

---

## Layer 1 — Cognitive load: how much may be on screen

The empirically tested layer. **Richard Mayer** (*Multimedia Learning*) ran
the experiments; **John Sweller** (Cognitive Load Theory) supplies the model
underneath — load splits into *intrinsic* (the subject's real difficulty),
*extraneous* (imposed by presentation), and *germane* (spent on actually
learning). You cannot reduce intrinsic load without lying. **Extraneous
load is the entire budget you control, and the target is zero.**

### L1.1 · Coherence — cut what doesn't serve the explanation

Interesting-but-tangential material measurably *hurts* comprehension; it
doesn't merely fail to help. Every section, figure, and aside earns its
place by advancing the explanation or it goes.

This is the most-violated principle in agent-written explainers, because
adding feels productive and cutting doesn't.

### L1.2 · Signaling — mark the part to look at

Don't leave the reader to find the relevant line, region, or moment.
Highlight the changed line in the diff, ring the region of the diagram
under discussion, bold the clause the argument turns on.

### L1.3 · Redundancy — don't say the same thing twice in two media

A caption that restates the sentence above it costs attention and returns
nothing. Caption what the figure *shows that the text doesn't* — or drop
the caption.

Note the asymmetry with L1.2: signaling adds a *pointer*, redundancy adds a
*duplicate*. Pointers help; duplicates don't.

### L1.4 · Spatial contiguity — labels touch what they label

Put the label on the thing. A legend the eye must ferry back and forth to is
a tax paid on every glance. Inline annotation beats a key; a callout on the
diagram beats a numbered list beneath it.

### L1.5 · Segmenting — reader-paced chunks

Break continuous material at conceptual seams and let the reader advance on
their own clock. On a page this means real sections with real headings, and
build-up sequences rather than one final complex diagram.

### L1.6 · Pre-training — name the parts before showing them interact

If a mechanism has four components, introduce the four components first,
then show them working. A reader who is still learning what a thing *is*
cannot simultaneously follow what it *does*.

This is the principle behind the best long-form technical explainers: each
diagram adds exactly one new element to the one before it.

### L1.7 · Cognitive load budget

Intrinsic load is fixed by the subject. Extraneous load is yours to
eliminate. When a passage feels overwhelming despite simple parts, you are
almost always paying extraneous load somewhere — a scattered layout, an
un-pre-trained term, a figure that must be cross-referenced.

**The worked-example effect**: for anything procedural, a single fully
worked case teaches better than an abstract statement of the procedure.
Show the whole worked instance, then generalize.

### L1.8 · Overview first, zoom and filter, details on demand

**Ben Shneiderman's** visual information-seeking mantra, applied as the
page's disclosure architecture. Every section opens with the whole shape
before any part of it. Detail lives behind an affordance — a disclosure, a
hover, a linked section — not inline where it competes with the overview.

---

## Layer 3 — Structure: the order ideas arrive in

### L3.1 · Answer first

**Barbara Minto's** *Pyramid Principle*: lead with the conclusion, then
support it. Every section states its point in the first sentence, then
argues. Never build suspense — the reader is trying to understand
something, not be entertained by a reveal.

### L3.2 · Concreteness

**Chip & Dan Heath** (*Made to Stick*): concrete beats abstract, always.
Every abstraction gets an instance attached in the same breath. This is also
the `explain` skill's house rule, so the two agree — an explanation without
a real example is an assertion.

### L3.3 · The curse of knowledge

The Heaths' name for the root failure: **once you know something, you cannot
imagine not knowing it**, so you compress exactly the step the reader
needed. It is the single most likely thing to go wrong on an agent-written
explainer, because the agent just finished doing the work.

Symptoms to hunt for by name:

- a term of art used before it is defined
- session jargon — "the fix from earlier", "the new approach", "as
  discussed"
- a conclusion whose supporting step was left implicit because it felt
  obvious
- an abstraction with no instance attached

The remedy is structural, not attitudinal: **read the draft as someone who
was never in the conversation**, because that is who opens the file.

### L3.4 · Classic style

**Steven Pinker** (*The Sense of Style*): prose as a window onto the world.
Show the reader the thing; don't describe your description of it. "The
system validates the token" beats "this section discusses the token
validation approach."

### L3.5 · Mechanism over definition

**Feynman's** move: explain how it works, not what it is called. A
definition tells the reader a label; a mechanism lets them predict
behavior. When a reader says an explanation "didn't click," they usually
got definitions where they needed a mechanism.

### L3.6 · Closure between frames

**Scott McCloud** (*Understanding Comics*): in a sequence, the reader
completes the motion *between* the frames. That gap is the explanatory
work — and its size is a design choice. Too small and the sequence is
tedious; too large and the reader falls out. For step-by-step diagrams,
pick the step size deliberately and keep it even.

### L3.7 · Narrative

**Hans Rosling's** lesson: an explanation has an arc, not just sections.
Something was believed, or broken, or unknown; something changed; here is
what is true now. Even a technical writeup reads better with a spine —
tension and resolution beat a flat inventory of facts.

---

## Using this file

In step 3 of the skill, **pick two or three** that match the shape of the
material and name them. In step 4, critique against those. Leave the rest
alone — they'll be in the index next time the draft fails differently.
