# project-audit focus rules (v1)

The 3 rules `--focus` (the default mode of `project-audit`) uses
to pick candidate projects. A project is a candidate iff its trunk
glyph is `[ ]` or `[~]` AND at least one rule matches. `[x]`,
`[-]`, `[>]`, and `[?]` are never candidates.

| ID | Rule |
|---|---|
| `out-of-order` | `[ ]`/`[~]` project sits below a higher-numbered `[x]` project |
| `straggler` | `[~]` project has ≥1 and ≤2 unchecked tasks |
| `recent` | Project is among the lowest 3 incomplete projects with P-number above `H` (the high-water mark = max P-number among `[x]`/`[-]`/`[>]`); if `H` is undefined, the lowest 3 incomplete projects overall |

A project may match multiple rules; report all matched tags.
Findings are walked `out-of-order` > `straggler` > `recent`, with
ties broken by ascending P-number.

---

## `out-of-order`

**Definition:** Project P has glyph `[ ]` or `[~]` AND there
exists at least one project P' with a higher P-number and glyph
`[x]`.

**Drift example:**
- Trunk shows `[x] **P10**`, `[x] **P11**`, but `[~] **P07**` is
  still open. P07 is an out-of-order candidate — likely the user
  finished it and forgot to flip the trunk glyph.

**Common cause:** Trunk-glyph flip forgotten when the last task
landed, especially when later projects shipped first.

---

## `straggler`

**Definition:** Project glyph is `[~]` AND the per-project file
has ≥1 unchecked task AND ≤2 unchecked tasks total (counting
both `T` and `TS` rows).

**Drift example:**
- `projects/P21-foo.md` has 7 of 8 tasks `[x]`. P21 is a
  straggler candidate — either the last task is a real loose end
  or the user closed it without flipping the checkbox.

**Common cause:** Final task landed but the checkbox wasn't
flipped; or the project really does have one open thread.

---

## `recent`

**Definition:** Let `H` = the highest P-number among projects
with glyph `[x]`, `[-]`, or `[>]` (the *high-water mark* of
settled work — stragglers do NOT count toward `H`). The `recent`
candidates are the 3 lowest-numbered `[ ]`/`[~]` projects with
P-number > `H`. If `H` is undefined (no settled projects exist),
the rule selects the 3 lowest-numbered `[ ]`/`[~]` projects
overall.

**Drift examples:**
- Trunk has `[x] P1`–`[x] P5` and `[ ] P6`, `[~] P7`, `[ ] P8`,
  `[ ] P9`. `H = 5`. Recent candidates: P6, P7, P8.
- Trunk has `[x] P1`–`[x] P4`, `[~] P5`, `[x] P6`–`[x] P10`,
  `[ ] P11`, `[~] P12`, `[ ] P13`, `[ ] P14`. `H = 10` (P5 is
  `[~]`, doesn't count). Recent candidates: P11, P12, P13. P5
  is also flagged separately by `out-of-order`.
- Trunk has only `[ ] P1`, `[~] P2`, `[ ] P3`, `[ ] P4`. `H` is
  undefined. Recent candidates: P1, P2, P3.

**Common cause:** The leading edge of active work — typos,
missing references blocks, unflipped checkboxes, and
TDD-ordering slips accumulate in the projects you're currently
editing.
