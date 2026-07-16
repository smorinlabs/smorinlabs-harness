# Technical-minimal components

Minimal vocabulary: button, badge, card, code block, table. Copy snippets
verbatim and recombine.

## Button

```html
<button class="btn btn-primary">Save changes</button>
<button class="btn btn-secondary">Cancel</button>
<button class="btn btn-ghost">Learn more</button>
```

```css
.btn {
  display: inline-flex;
  align-items: center;
  gap: var(--sp-2);
  padding: var(--sp-2) var(--sp-4);
  font-family: var(--font-sans);
  font-size: var(--fs-small);
  font-weight: var(--fw-medium);
  line-height: 1;
  border-radius: var(--r-md);
  border: 1px solid transparent;
  cursor: pointer;
  transition: background 120ms, border-color 120ms;
}
.btn-primary {
  background: var(--accent);
  color: var(--on-accent);
}
.btn-primary:hover { background: var(--accent-hover); }
.btn-secondary {
  background: var(--surface);
  color: var(--ink);
  border-color: var(--border-strong);
}
.btn-secondary:hover { background: var(--surface-2); }
.btn-ghost {
  background: transparent;
  color: var(--ink-muted);
}
.btn-ghost:hover { color: var(--ink); background: var(--surface-2); }
```

## Badge

```html
<span class="badge badge-neutral">v1.2.0</span>
<span class="badge badge-accent">New</span>
<span class="badge badge-success">Stable</span>
<span class="badge badge-warning">Beta</span>
<span class="badge badge-danger">Deprecated</span>
```

```css
.badge {
  display: inline-block;
  padding: 2px var(--sp-2);
  font-size: var(--fs-caption);
  font-weight: var(--fw-medium);
  line-height: 1.4;
  border-radius: var(--r-sm);
  border: 1px solid var(--border);
}
.badge-neutral { background: var(--surface-2); color: var(--ink-muted); }
.badge-accent  { background: var(--accent-soft); color: var(--accent); border-color: var(--accent-soft); }
.badge-success { background: var(--success-bg); color: var(--success); border-color: var(--success-border); }
.badge-warning { background: var(--warning-bg); color: var(--warning); border-color: var(--warning-border); }
.badge-danger  { background: var(--danger-bg);  color: var(--danger);  border-color: var(--danger-border); }
```

## Card

```html
<div class="card">
  <h3>Card title</h3>
  <p>Description of the card content. Keep it tight.</p>
</div>
```

```css
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  padding: var(--sp-5);
  box-shadow: var(--shadow-sm);
}
.card h3 {
  margin: 0 0 var(--sp-2) 0;
  font-size: var(--fs-h3);
  font-weight: var(--fw-semibold);
}
.card p {
  margin: 0;
  color: var(--ink-muted);
  font-size: var(--fs-small);
}
```

## Code block

```html
<pre class="code"><code>npm install @vercel/next</code></pre>
```

```css
.code {
  background: var(--surface-3);
  border: 1px solid var(--border);
  border-radius: var(--r-md);
  padding: var(--sp-3) var(--sp-4);
  margin: 0;
  font-family: var(--font-mono);
  font-size: var(--fs-small);
  overflow-x: auto;
  color: var(--ink-strong);
}
.code code { background: none; padding: 0; }
```

## Table

```html
<table class="tbl">
  <thead>
    <tr><th>Name</th><th>Status</th><th>Version</th></tr>
  </thead>
  <tbody>
    <tr><td>api-gateway</td><td><span class="badge badge-success">Healthy</span></td><td>1.4.0</td></tr>
  </tbody>
</table>
```

```css
.tbl {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--fs-small);
}
.tbl th, .tbl td {
  text-align: left;
  padding: var(--sp-3) var(--sp-4);
  border-bottom: 1px solid var(--border);
}
.tbl th {
  font-weight: var(--fw-semibold);
  color: var(--ink-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  font-size: var(--fs-caption);
}
.tbl tr:last-child td { border-bottom: none; }
```
