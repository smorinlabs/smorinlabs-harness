# Technical-minimal design tokens

The full `:root` block. Copy verbatim into every Technical-minimal artifact's
`<style>` block.

```css
:root {
  color-scheme: light;

  /* Surfaces */
  --surface:        #FFFFFF;
  --surface-2:      #FAFAFA;
  --surface-3:      #F4F4F5;
  --border:         #E4E4E7;
  --border-strong:  #D4D4D8;

  /* Ink */
  --ink:            #18181B;
  --ink-strong:     #09090B;
  --ink-muted:      #71717A;
  --ink-subtle:     #A1A1AA;

  /* Accent (single blue) */
  --accent:         #2563EB;
  --accent-hover:   #1D4ED8;
  --accent-soft:    #EFF6FF;
  --on-accent:      #FFFFFF;

  /* Semantic */
  --success:        #16A34A;
  --warning:        #D97706;
  --danger:         #DC2626;

  /* Semantic tints (badge backgrounds/borders) */
  --success-bg:     #F0FDF4;
  --success-border: #DCFCE7;
  --warning-bg:     #FFFBEB;
  --warning-border: #FEF3C7;
  --danger-bg:      #FEF2F2;
  --danger-border:  #FEE2E2;

  /* Typography */
  --font-sans:      -apple-system, "SF Pro Text", Inter, system-ui, sans-serif;
  --font-mono:      "SF Mono", "JetBrains Mono", Menlo, monospace;

  /* Type scale */
  --fs-caption: 12px;
  --fs-small:   13px;
  --fs-body:    15px;
  --fs-h3:      18px;
  --fs-h2:      22px;
  --fs-h1:      30px;
  --fs-display: 40px;

  --lh-tight:   1.25;
  --lh-normal:  1.5;
  --lh-loose:   1.65;

  --fw-regular: 400;
  --fw-medium:  500;
  --fw-semibold: 600;

  /* Spacing */
  --sp-1: 4px;
  --sp-2: 8px;
  --sp-3: 12px;
  --sp-4: 16px;
  --sp-5: 24px;
  --sp-6: 32px;
  --sp-7: 48px;
  --sp-8: 64px;

  /* Radii */
  --r-sm:   4px;
  --r-md:   6px;
  --r-lg:   8px;
  --r-xl:   12px;
  --r-pill: 999px;

  /* Shadows (neutral, not warm-tinted) */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.04);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.06);
  --shadow-lg: 0 12px 32px rgba(0, 0, 0, 0.08);
}

html, body {
  background: var(--surface);
  color: var(--ink);
  font-family: var(--font-sans);
  font-size: var(--fs-body);
  line-height: var(--lh-normal);
  font-weight: var(--fw-regular);
  margin: 0;
}
```

## Type roles

| Role | Family | Size | Line height | Weight |
|------|--------|------|-------------|--------|
| Display | sans | 40 | 1.25 | 600 |
| H1 | sans | 30 | 1.25 | 600 |
| H2 | sans | 22 | 1.3 | 600 |
| H3 | sans | 18 | 1.4 | 500 |
| Body | sans | 15 | 1.5 | 400 |
| Small | sans | 13 | 1.5 | 400 |
| Caption | sans | 12 | 1.5 | 500 (uppercase, letter-spaced) |
| Code | mono | 13 | 1.5 | 400 |
