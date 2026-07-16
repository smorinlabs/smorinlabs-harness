# Component patterns

Every choosable component shape, with when-to-use notes and CSS. Don't invent
new component shapes; if you need something that isn't here, add it to this
file first.

## Buttons

One primary per surface (clay), neutral secondary (outlined on white), ghost
for tertiary actions. Destructive is outlined-in-danger that fills on hover.

```css
.btn {
  appearance: none; border: 1px solid transparent;
  border-radius: var(--r-sm);
  padding: 8px 14px;
  font: inherit; font-size: 14px; font-weight: 500; line-height: 1.2;
  cursor: pointer;
  transition: background 160ms var(--ease-out), border-color 160ms var(--ease-out);
}
.btn-primary   { background: var(--clay); color: var(--ivory); }
.btn-primary:hover   { background: #C76A4B; }
.btn-secondary { background: var(--white); color: var(--slate); border-color: var(--gray-300); }
.btn-secondary:hover { border-color: var(--gray-500); }
.btn-ghost     { background: transparent; color: var(--gray-700); }
.btn-ghost:hover     { color: var(--slate); background: var(--gray-100); }
.btn-danger    { background: var(--white); color: var(--danger); border-color: rgba(176,74,74,.35); }
.btn-danger:hover    { background: var(--danger); color: var(--ivory); }
```

## Badges · status pills

Pill-shaped, dot prefix for vertical alignment, semantic-color tinted bg with
full-color text.

```css
.badge {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 3px 10px; border-radius: 999px;
  font-size: 12px; font-weight: 500; line-height: 1.3;
}
.badge::before {
  content: ""; width: 6px; height: 6px; border-radius: 999px;
  background: currentColor;
}
.badge-draft     { background: var(--gray-100); color: var(--gray-700); }
.badge-in-review { background: rgba(92, 124, 163, .14); color: var(--info); }
.badge-done      { background: rgba(120, 140, 93, .16); color: var(--success); }
.badge-overdue   { background: rgba(176, 74, 74, .14); color: var(--danger); }
.badge-blocked   { background: rgba(199, 142, 63, .14); color: var(--warning); }
```

## Risk tags · for code review and severity

Square (not pill) — visually distinct from status pills.

```css
.risk {
  display: inline-flex; align-items: center;
  padding: 2px 8px; border-radius: var(--r-xs);
  font-size: 11px; font-weight: 500;
  text-transform: uppercase; letter-spacing: .06em;
  border: 1px solid;
}
.risk-safe { color: var(--success); border-color: rgba(120,140,93,.35); background: rgba(120,140,93,.08); }
.risk-look { color: var(--warning); border-color: rgba(199,142,63,.35); background: rgba(199,142,63,.08); }
.risk-attn { color: var(--danger);  border-color: rgba(176,74,74,.35);  background: rgba(176,74,74,.08); }
```

## Cards · six structural treatments

Same content, different emphasis. Pick one per surface; mixing them in a list
is what makes a page feel noisy.

```css
.card {
  background: var(--white);
  border-radius: var(--r-md);
  padding: var(--sp-4);
  transition: box-shadow 200ms var(--ease-out);
}
.card-flat     { background: var(--gray-100); }
.card-outlined { border: 1px solid var(--gray-300); }
.card-elevated { box-shadow: var(--shadow-md); }
.card-elevated:hover { box-shadow: var(--shadow-lg); }
.card-stripe   { border: 1px solid var(--gray-300); border-left: 3px solid var(--clay); }
.card-inset    { background: var(--gray-100); border: 1px solid var(--gray-100);
                 box-shadow: inset 0 1px 0 rgba(20,20,19,.04); }
```

Plus a horizontal row variant for list items:

```css
.card-row {
  display: grid; grid-template-columns: 32px 1fr auto;
  align-items: center; gap: var(--sp-3);
  background: var(--white); border: 1px solid var(--gray-300);
  border-radius: var(--r-sm); padding: var(--sp-2) var(--sp-3);
}
```

## Stat tiles · for status reports

Top-of-document KPI tiles. Three lines: value, key, delta.

```css
.stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: var(--sp-3);
  margin: var(--sp-4) 0;
}
.stat {
  background: var(--white);
  border: 1px solid var(--gray-300);
  border-radius: var(--r-md);
  padding: var(--sp-4);
}
.stat .v { font-size: 32px; line-height: 1.1; font-weight: 500; }
.stat .k { font-size: 13px; color: var(--gray-700); margin-top: 2px; }
.stat .d { font-size: 12px; color: var(--gray-500); margin-top: var(--sp-2);
           font-family: var(--font-mono); }
```

## Callout · for TL;DRs and warnings

```css
.callout {
  background: var(--oat);
  border-left: 3px solid var(--clay);
  padding: var(--sp-4) var(--sp-5);
  border-radius: var(--r-sm);
  color: var(--gray-700);
}
.callout strong { color: var(--slate); }
```

## Table · for data lists

```css
table.tbl { width: 100%; border-collapse: collapse; font-size: 14px; }
.tbl th, .tbl td {
  text-align: left; padding: var(--sp-3);
  border-bottom: 1px solid var(--gray-100);
}
.tbl th {
  font-weight: 500; color: var(--gray-500);
  font-size: 12px; text-transform: uppercase; letter-spacing: .06em;
}
.tbl tr:hover td { background: var(--gray-100); }
```

## Code block

```css
pre.code {
  background: var(--white);
  border: 1px solid var(--gray-300);
  border-radius: var(--r-sm);
  padding: var(--sp-4);
  overflow-x: auto;
  font-family: var(--font-mono); font-size: 13px; line-height: 1.55;
  color: var(--gray-700);
}
.filebar {
  display: flex; justify-content: space-between; align-items: center;
  background: var(--gray-100); border: 1px solid var(--gray-300);
  border-bottom: 0; border-radius: var(--r-sm) var(--r-sm) 0 0;
  padding: 6px var(--sp-3);
  font-family: var(--font-mono); font-size: 12px; color: var(--gray-700);
}
.filebar + pre.code { margin-top: 0; border-radius: 0 0 var(--r-sm) var(--r-sm); }
```

---

This is the complete component catalogue for the theme skill. The toggle /
choice-button component lives in the companion `birchline-html-artifacts`
skill (codesign mode), not here — this skill is theme-only and stays out of
interactivity contracts.
