# Illustration examples

Five inline-SVG patterns. Each is symbolic-not-literal: low-fi wireframes that
represent what *kind* of content lives inside a section, never the actual
content.

**Default to no illustration.** Add one only when it replaces a paragraph of
explanatory prose — when a reader scanning the page benefits from a small
thumbnail more than from another paragraph.

## Construction principles

These are the rules the five examples follow. Useful both for reading the
existing examples and for guidance if you ever need to compose a sixth.

1. **Symbolic, not literal.** Represent what *kind* of content lives inside,
   never the actual content. Gray bars stand in for text; clay ovals for hero
   images; small colored squares for palettes.
2. **Brand tokens only.** Fill / stroke from the palette. No gradients, no
   shading, no opacity tricks. Differentiate by hue, not intensity.
3. **Hairline borders, generous radii.** Strokes 1.5px slate. Outer shapes
   `rx="4"–"10"`, inner elements `rx="1.5"–"3"`.
4. **Soft slate-tinted shadows.** Each "object" gets a `feDropShadow` with
   `flood-color="#141413"` and `flood-opacity="0.06"–"0.10"`. Never pure black.
5. **One purposeful tilt at most.** A 3–5° rotation reserved for the inferior
   or informal half of a comparison. Never tilt both objects in a pair.
6. **Bars represent text, varied widths.** Use `rx="1.5"`, height `3`, widths
   between 30% and 90% of the container.
7. **One handcrafted element per drawing.** Most strokes are mechanically
   perfect. Exactly one element gets a slight irregularity (e.g.,
   `rotate(-2)` on an ellipse). Signals "made, not generated."
8. **File-tab labels are stickers.** When labeling a kind-of-file (`.MD`,
   `.HTML`, `.PR`), use a small rounded rectangle sticking up from the
   top-left, monospace text inside.

## The five examples

The actual SVG sources live in `illustrations/` (in this theme folder). Read the file to
copy its source into your artifact.

### 1. `01-differentiated-trio.svg`

**Three cards side by side, one different on three axes** (fill + content
color + extra element). Use when comparing alternatives where one is the
recommendation. The differentiated card carries the clay accent and a small
extra mark; the other two are matched gray.

Typical use: "we evaluated three approaches and recommend approach B" type
sections, where you want the reader to clock the recommendation at a glance.

### 2. `02-variant-grid.svg`

**Four palette / layout / tone directions in a 2×2 grid**, each combining
fill + accent. Use for design-direction exploration where the four options
are roughly equally weighted.

Typical use: visual direction options for a marketing site, four onboarding
flow concepts, four error-state treatments.

### 3. `03-timeline-composite.svg`

**Vertical line with clay → sage → gray dots, text bars to the right,
mockup card on the side.** Use for implementation plans with multiple
content types — a sequence with phases that have different kinds of work.

Typical use: rollout plan with discovery → build → ship phases, project
timeline with mixed deliverables (code + docs + comms).

### 4. `04-format-comparison.svg`

**Two paper documents side by side — one tilted and flat, one upright and
structured.** The structured one shows brand-palette swatches inside (the
doubly-meta move). Use when the whole argument is "this format beats that
format."

Typical use: before/after diagrams, "we used to do it this way, now we do
it that way" sections, side-by-side critique of two approaches.

### 5. `05-single-preview.svg`

**A solo upright document** — the right half of the comparison, alone.
Use when there's no comparison to make and a thumbnail would help orient
the reader to what's inside the section.

Typical use: section headers for artifact catalogs, "here's what one of
these looks like" preview cards.

## How to embed

Read the SVG file from `illustrations/` (in this theme folder), paste the markup directly
into your HTML. Adjust position with margins / wrapper divs as needed.
Don't modify the construction (colors, stroke widths, radii); only adjust
positions if the layout demands it.

```html
<div class="illustration">
  <!-- inline contents of 01-differentiated-trio.svg here -->
</div>
```

```css
.illustration {
  margin: var(--sp-5) 0;
  /* width-constrain if you want it inset rather than full-bleed */
}
```

## Cases NOT covered by this catalogue

- **Data-flow diagrams** (boxes connected by clay-dashed arrows for realtime,
  solid for sync) — closer to structured diagrams than thumbnails.
- **Annotated flowcharts** (deploy-pipeline style with happy-path and
  failure-path branches) — same family as data-flow.
- **Animated illustrations** — out of scope; everything here is static.

If you need one of the above, the theme tokens still apply (clay + slate +
hairline strokes + slate-tinted shadows). But you're composing fresh — the
catalogue won't have a template to copy.
