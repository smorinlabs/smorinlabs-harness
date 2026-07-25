# Visual encoding — the delegation carve, and the standalone fallback

Two jobs here. First, decide whether a given visual belongs to `dataviz` or
to this skill. Second — when `dataviz` is unavailable, which is often —
encode it correctly without it.

## The delegation rule

**Draw the boundary by what the mark means, not by what the artifact is
called.**

> If a mark's **position, length, or area stands for a number the reader
> must compare** → that is `dataviz`.
> If it stands for a **relationship, sequence, structure, or state** → it is
> this skill's.

"Charts go to dataviz" is the wrong rule. A hand-annotated timeline is
chart-shaped but conceptual; a stat tile has no plot but encodes magnitude.
Ask what the reader is being asked to *do* with the mark.

| `dataviz` owns | This skill owns |
|---|---|
| bar, line, area, dot, heatmap | flow, architecture, sequence, state diagrams |
| stat tiles / hero numbers | annotated schematics, cutaways, exploded views |
| dashboards, small-multiple *charts* | 2×2s, hierarchies, narrative timelines |
| categorical / sequential / diverging / status color | process and step sequences |
| chart hover, tooltip, filter behavior | interactive explanatory models |
| chart legends, table views, chart dark mode | figure composition, captions, page layout |

**When `dataviz` is present and the visual is quantitative, use it.** It
carries a runnable colorblind-and-contrast validator this skill has no
equivalent for, plus a maintained anti-pattern catalog. Do not reimplement
it. Do not second-guess it.

## Why the fallback is load-bearing

`dataviz` is **compiled into the Claude Code binary**. It has no filesystem
presence; it materializes at a versioned temp path only when invoked. That
means:

1. **It does not exist on Codex** — this plugin's skills are placed at
   `~/.agents/skills`, and `dataviz` cannot be there.
2. Its version is pinned to whatever Claude Code build is running.
3. Its palette validator is a Node script at that ephemeral path — nothing
   here can call it.

This plugin ships as *portable across Claude Code and Codex*. So on roughly
half the surfaces this skill runs on, the delegate is simply absent.
**Check for it, use it when present, fall through silently when not — and
never remove this fallback on the grounds that the delegate exists.**

---

# The standalone encoding rules

Complete enough to build a correct quantitative figure with no delegate.

## E1 · Match the visual variable to the reader's task

**Jacques Bertin** (*Sémiologie Graphique*, 1967) catalogued the visual
variables — position, size, value (lightness), texture, color hue,
orientation, shape — and, crucially, what each is *good for*. A variable is
**selective** (lets you pick out a group), **ordered** (reads as a
sequence), or **quantitative** (supports reading a ratio).

Pick the encoding from what the reader must do with it:

| Reader's task | Use | Avoid |
|---|---|---|
| compare magnitudes precisely | position, length | area, color |
| spot members of a category | hue, shape | lightness |
| follow an order (low→high) | lightness, size, position | hue |
| read a ratio ("twice as big") | length from a zero baseline | area, angle |

## E2 · The accuracy ranking

**Cleveland & McGill's** graphical-perception experiments put numbers on
Bertin's intuitions. In decreasing order of accuracy:

1. position on a common scale
2. position on identical, non-aligned scales
3. length
4. angle / slope
5. area
6. volume, curvature
7. shading, color saturation

**Give the quantity that matters the most accurate encoding available.**
Color carries category or emphasis — never a magnitude the reader must
read off precisely.

Corollaries worth stating outright:

- Pie charts encode with angle and area (4 and 5). Two or three slices is
  survivable; more is not. A bar chart is nearly always better.
- Bubble size is area. Use it for "big vs small," never for "how much
  bigger."
- **Never a dual-axis chart.** Two y-scales invite an invented correlation.
  Two measures of different scale → two charts, small multiples, or index
  both to a common base.

## E3 · Data-ink, and the small multiple

**Edward Tufte**: delete every mark that doesn't carry information. Grid
lines recede or vanish; axes lose their boxes; no 3-D on 2-D data; no
gradient fills that mean nothing; no chartjunk.

And the move that solves more explainer problems than any other: the
**small multiple**. When the question is "how does this vary across N
cases," repeat one small chart N times with a shared scale. The reader
learns the grammar once and applies it N times — which is exactly the
cognitive-load win Mayer's pre-training principle predicts. Reach for it
before reaching for one complex chart with N series.

**Sparklines** — word-sized, axis-free trend marks inline in prose — are the
other Tufte tool this skill under-uses. A trend mentioned in a sentence can
often just sit *in* the sentence.

## E4 · Repeat symbols; never scale them

The **Isotype** rule (Otto and Marie Neurath, Gerd Arntz): to show more, use
more identical symbols — never one bigger symbol. Scaling a pictogram
encodes with area, which lands at rank 5 and is read wrongly and
inconsistently (readers split between judging height and judging area).

## E5 · One pop-out per view

**Colin Ware's** perception work: preattentive attributes — a lone
saturated mark among grays, one different shape, one outlier position — are
found in constant time, before conscious attention. That is a powerful
signaling tool (canon L1.2) and it has a hard limit: **two competing
pop-outs cancel each other.** If everything is emphasized, nothing is.

## E6 · Annotation is the graphic

**Jonathan Corum** (NYT science graphics): a chart plus a paragraph beneath
it is two artifacts pretending to be one. The finding belongs *on* the
figure — the labeled peak, the arrow to the crossover, the shaded region
with its name. This is Mayer's spatial contiguity (L1.4) stated as a
graphics-desk rule.

## E7 · Color, without a validator

`dataviz` computes this. Without it, do not eyeball it — **use a published
palette that was already validated**, and change nothing about it.

**Okabe–Ito** is the default choice: eight hues designed explicitly to stay
distinguishable under the common color-vision deficiencies.

| Name | Hex |
|---|---|
| Black | `#000000` |
| Orange | `#E69F00` |
| Sky blue | `#56B4E9` |
| Bluish green | `#009E73` |
| Yellow | `#F0E442` |
| Blue | `#0072B2` |
| Vermillion | `#D55E00` |
| Reddish purple | `#CC79A7` |

Rules that come with it:

- **Assign in fixed order, never cycled.** A ninth series is never a
  generated hue — fold it into "Other," facet into small multiples, or cut.
- **Color follows the entity, not its rank.** Filtering out a series must
  not repaint the survivors.
- **Sequential = one hue, light→dark. Diverging = two hues with a neutral
  gray midpoint.** Never a rainbow; never a hue at the diverging midpoint.
- **Never color alone.** Pair hue with a direct label, a shape, or a
  texture — for CVD readers, for print, and for forced-colors mode.
- **Text wears text tokens**, never the series color. A colored mark
  *beside* a label carries the identity; the label itself stays ink.
- Yellow `#F0E442` is very light — do not put it on a light surface as a
  thin line or small text. On light backgrounds prefer the darker six.

If the active theme supplies its own categorical order, prefer it — but
apply the "never color alone" rule regardless, since theme palettes are
tuned for aesthetics rather than for CVD separation.

## E8 · Look at it

None of the above catches label collisions, overflow, or a legend that ran
off the edge. **Render the figure and actually look at it** before shipping.
