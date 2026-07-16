# Birchline design tokens · v1

The single source of truth. Copy the `:root` block below into the `<style>` tag
of every Birchline HTML artifact. Don't substitute, don't extend without adding
to this file first.

## Required head tags

Every artifact must declare its color scheme. Without this, iOS auto-darkens
the page in dark-mode browsers and slate text becomes invisible on the inverted
background.

```html
<meta name="color-scheme" content="light">
```

## CSS variables — copy verbatim

```css
:root {
  color-scheme: light;            /* belt + suspenders with the meta tag */

  /* Brand */
  --clay:    #D97757;             /* one per surface, never three */
  --slate:   #141413;             /* primary text */
  --ivory:   #FAF9F5;             /* page background */
  --oat:     #E3DACC;             /* nested surfaces, callout bg */

  /* Neutrals · warm-tinted */
  --white:    #FFFFFF;            /* card surfaces */
  --gray-100: #F0EEE6;            /* tables, code bg, secondary surfaces */
  --gray-300: #D1CFC5;            /* borders */
  --gray-500: #87867F;            /* metadata, captions */
  --gray-700: #3D3D3A;            /* secondary text */

  /* Semantic · use as 12–16% tint backgrounds, full color text */
  --success: #788C5D;             /* sage */
  --warning: #C78E3F;             /* amber */
  --danger:  #B04A4A;             /* brick */
  --info:    #5C7CA3;             /* slate-blue */

  /* Spacing · 4-based, 8 steps */
  --sp-1: 4px;  --sp-2: 8px;
  --sp-3: 12px; --sp-4: 16px;
  --sp-5: 24px; --sp-6: 32px;
  --sp-7: 48px; --sp-8: 64px;

  /* Radius */
  --r-xs: 4px;  --r-sm: 8px;
  --r-md: 12px; --r-lg: 20px;

  /* Elevation · slate-tinted, never pure black */
  --shadow-sm: 0 1px 2px rgba(20,20,19,.06);
  --shadow-md: 0 4px 10px rgba(20,20,19,.08);
  --shadow-lg: 0 12px 28px rgba(20,20,19,.12);

  /* Motion */
  --ease-out:    cubic-bezier(.16, 1, .3, 1);
  --ease-spring: cubic-bezier(.34, 1.56, .64, 1);

  /* Type families · serif for hero, sans for everything else */
  --font-sans:  "Söhne", "Geist", ui-sans-serif, system-ui, sans-serif;
  --font-serif: "Tiempos", "Source Serif 4", Georgia, serif;
  --font-mono:  "Berkeley Mono", "JetBrains Mono", ui-monospace, monospace;
}
```

## Type scale

| Role    | Family | Size  | Line | Weight | Notes |
| ------- | ------ | ----- | ---- | ------ | ----- |
| Display | serif  | 48    | 1.10 | 600    | Page hero only |
| H1      | serif  | 32–40 | 1.15 | 600    | One per page · serif gives editorial gravitas |
| H2      | sans   | 24    | 1.30 | 500    | Section heads |
| H3      | sans   | 18    | 1.35 | 500    | Subsections |
| Body    | sans   | 16    | 1.55 | 430    | Variable-font weight |
| Small   | sans   | 14    | 1.50 | 430    | Annotations |
| Caption | sans   | 12    | 1.40 | 500    | Uppercase, .08em letter-spacing |

## The italic-clay accent · hero pattern

Wrap one phrase in your hero H1 with `<span class="accent">…</span>` to render
it in serif italic clay. Use sparingly — one per page hero, never on a section
heading.

```css
.accent {
  font-family: var(--font-serif);
  font-style:  italic;
  color:       var(--clay);
  font-weight: inherit;
}
```

```html
<h1>The unreasonable <span class="accent">effectiveness</span> of HTML</h1>
<h1>Wiring a <span class="accent">design system</span> into a skill</h1>
<h1>Q3 <span class="accent">retrospective</span></h1>
```

## Recommended Google Fonts import (free fallback families)

The `--font-sans` / `--font-serif` stacks above list the paid families
(Söhne, Tiempos) first per the source design system; the shipped
`example.html` reverses the order so the Google-Fonts-available
fallbacks (Geist, Source Serif 4) load first, since most environments
won't have Söhne/Tiempos licensed locally.

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;430;500;600&family=Source+Serif+4:ital,wght@0,400;0,500;0,600;1,400;1,500&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
```

## Provenance

- All hex values verbatim from `thariqs.github.io/html-effectiveness/05-design-system.html`.
- Easings + durations verbatim from `07-prototype-animation.html`.
- Serif hero pattern observed on the index page hero ("The unreasonable
  *effectiveness* of HTML").
- `color-scheme: light` is mandatory because iOS auto-darkens otherwise — this
  is a real bug that surfaced during skill development.
