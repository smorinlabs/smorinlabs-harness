# High-contrast-dark components

## Button

```html
<button class="btn btn-primary">Run</button>
<button class="btn btn-secondary">Stop</button>
<button class="btn btn-danger">Delete</button>
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
}
.btn-primary {
  background: var(--accent);
  color: var(--surface);
  border-color: var(--accent);
}
.btn-primary:hover { background: var(--accent-hover); border-color: var(--accent-hover); }
.btn-secondary {
  background: var(--surface-2);
  color: var(--ink);
  border-color: var(--border-strong);
}
.btn-secondary:hover { background: var(--surface-3); }
.btn-danger {
  background: transparent;
  color: var(--danger);
  border-color: var(--danger);
}
.btn-danger:hover { background: rgba(239, 68, 68, 0.1); }
```

## Badge

```html
<span class="badge badge-neutral">v1.2.0</span>
<span class="badge badge-accent">New</span>
<span class="badge badge-success">Up</span>
<span class="badge badge-warning">Degraded</span>
<span class="badge badge-danger">Down</span>
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
  background: var(--surface-2);
  color: var(--ink-muted);
}
.badge-accent  { color: var(--accent);  border-color: var(--accent-soft);  background: var(--accent-soft); }
.badge-success { color: var(--success); border-color: var(--success-border); background: var(--success-bg); }
.badge-warning { color: var(--warning); border-color: var(--warning-border); background: var(--warning-bg); }
.badge-danger  { color: var(--danger);  border-color: var(--danger-border);  background: var(--danger-bg); }
```

## Card

```html
<div class="card">
  <h3>Card title</h3>
  <p>Description.</p>
</div>
```

```css
.card {
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  padding: var(--sp-5);
}
.card h3 { margin: 0 0 var(--sp-2); font-size: var(--fs-h3); font-weight: var(--fw-semibold); color: var(--ink-strong); }
.card p { margin: 0; color: var(--ink-muted); font-size: var(--fs-small); }
```

## Stat tile

```html
<div class="stat">
  <div class="stat-label">RPS</div>
  <div class="stat-value">1,247</div>
  <div class="stat-delta stat-up">+12% vs 1h ago</div>
</div>
```

```css
.stat {
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  padding: var(--sp-4);
}
.stat-label { font-size: var(--fs-caption); color: var(--ink-muted); text-transform: uppercase; letter-spacing: 0.06em; font-weight: var(--fw-medium); }
.stat-value { font-size: 28px; font-weight: var(--fw-semibold); color: var(--ink-strong); font-family: var(--font-mono); margin-top: var(--sp-2); }
.stat-delta { font-size: var(--fs-caption); margin-top: var(--sp-1); }
.stat-up   { color: var(--success); }
.stat-down { color: var(--danger); }
```

## Code block

```html
<pre class="code"><code>$ docker ps --filter status=running</code></pre>
```

```css
.code {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--r-md);
  padding: var(--sp-3) var(--sp-4);
  margin: 0;
  font-family: var(--font-mono);
  font-size: var(--fs-small);
  color: var(--ink);
  overflow-x: auto;
}
```
