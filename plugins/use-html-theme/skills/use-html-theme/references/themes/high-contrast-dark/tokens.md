# High-contrast-dark design tokens

The full `:root` block. Copy verbatim into every High-contrast-dark artifact's
`<style>` block.

```css
:root {
  color-scheme: dark;

  /* Surfaces */
  --surface:        #0A0A0A;
  --surface-2:      #141414;
  --surface-3:      #1F1F1F;
  --border:         #2A2A2A;
  --border-strong:  #3F3F3F;

  /* Ink */
  --ink:            #FAFAFA;
  --ink-strong:     #FFFFFF;
  --ink-muted:      #A3A3A3;
  --ink-subtle:     #71717A;

  /* Accent (single saturated blue) */
  --accent:         #3B82F6;
  --accent-hover:   #60A5FA;
  --accent-soft:    #0F1F3D;

  /* Semantic */
  --success:        #22C55E;
  --warning:        #EAB308;
  --danger:         #EF4444;

  /* Semantic tints (badge backgrounds/borders) */
  --success-bg:     #052E16;
  --success-border: #14532D;
  --warning-bg:     #1F1207;
  --warning-border: #713F12;
  --danger-bg:      #1F0707;
  --danger-border:  #7F1D1D;

  /* Typography */
  --font-sans:      system-ui, -apple-system, "Segoe UI", sans-serif;
  --font-mono:      "JetBrains Mono", "Fira Code", "SF Mono", Menlo, monospace;

  --fs-caption: 12px;
  --fs-small:   13px;
  --fs-body:    14px;
  --fs-h3:      18px;
  --fs-h2:      22px;
  --fs-h1:      28px;

  --lh-tight:   1.25;
  --lh-normal:  1.5;

  --fw-regular: 400;
  --fw-medium:  500;
  --fw-semibold: 600;

  /* Spacing (tighter than light themes) */
  --sp-1: 4px;
  --sp-2: 8px;
  --sp-3: 12px;
  --sp-4: 16px;
  --sp-5: 20px;
  --sp-6: 28px;
  --sp-7: 40px;

  --r-sm:   3px;
  --r-md:   5px;
  --r-lg:   8px;

  /* Shadows are subtle on dark surfaces */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.5);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.6);
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

| Role | Family | Size | Weight |
|------|--------|------|--------|
| H1 | sans | 28 | 600 |
| H2 | sans | 22 | 600 |
| H3 | sans | 18 | 500 |
| Body | sans | 14 | 400 |
| Small | sans | 13 | 400 |
| Caption | sans | 12 | 500 (uppercase, letter-spaced) |
| Code | mono | 13 | 400 |
