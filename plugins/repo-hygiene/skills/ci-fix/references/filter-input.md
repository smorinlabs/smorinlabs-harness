# The filter input — isolated tests in CI

A `workflow_dispatch` input that carries the failing test IDs into the test
step, so a dispatched run executes only those tests: the remote mirror of
rung 0. This is the one rendering; step 6's offer (`offer-filter` in the
plan) and `optimize.md`'s lever 11 both use it.

Two rules make it safe and honest:

- **The input is data, never code.** Its value reaches the shell through an
  environment variable and is parsed according to the runner's input grammar
  below (for example, newline-separated node IDs or one regex/expression). No `${{ }}`
  inside `run:` (GitHub substitutes that into the script before the shell
  runs it), no `eval`, no unquoted expansion. A dispatch input can only be
  set by someone with write access, but the pattern costs nothing and reads
  the same on every runner.
- **An empty input runs the whole suite.** Push and pull-request runs never
  set the input, so the workflow must behave exactly as before on those
  events. Verify the actual ordinary command and current-revision test
  selection; a historical test count alone cannot prove unchanged coverage.

## The rendering

`on:` gains the trigger and one optional input (block form; `on:` may already
have `workflow_dispatch:` with no inputs — then only `inputs:` is added):

```yaml
on:
  push:
  pull_request:
  workflow_dispatch:
    inputs:
      filter:
        description: "test IDs to run, one per line; empty runs the whole suite"
        required: false
        default: ""
```

The test step reads it through `env:` and splits it on newlines. `mapfile` is
bash: on a Windows runner (`pwsh` by default) add `shell: bash` to the step.

```yaml
      - name: Run tests
        env:
          FILTER: ${{ inputs.filter }}
        run: |
          ARGS=()
          [ -n "$FILTER" ] && mapfile -t ARGS <<< "$FILTER"
          uv run pytest -x "${ARGS[@]}"
```

Per runner, the last line becomes:

| Runner | Last line of the step | Input value the skill sends |
|---|---|---|
| pytest | `uv run pytest -x "${ARGS[@]}"` | node IDs from `failures`, one per line (raw, not shell-quoted: nothing here is parsed by a shell) |
| jest / vitest | `if [ -n "$FILTER" ]; then npx jest -t "$FILTER"; else npx jest; fi` (vitest: `npx vitest run -t "$FILTER"`) | one regex: each name with its metacharacters escaped, joined with `\|`, per `targeted-repro.md` |
| cargo | `cargo test -- "${ARGS[@]}"` (add `--exact` only when a single ID is sent) | test paths, one per line |
| cargo-nextest | `cargo nextest run -E "$FILTER"` when non-empty, else `cargo nextest run` | one expression: `test(=a) \| test(=b)` |
| go | `go test ./... -run "$FILTER"` when non-empty, else `go test ./...` | one anchored regex: `^TestA$\|^TestB$`, subtests as `^TestA$/^sub$` |

The `if` form is used wherever the runner takes a single pattern rather than
a list, so an empty input never becomes an empty pattern (`-t ""` matches
everything in jest but is an error in some runners).

## Dispatching with the input

The input **name** is the one the plan carries in `filter_input` — `filter`
for an input this file rendered, but an existing workflow may narrow its
tests through an input of another name (below). The input **value** is the
shape that runner's row in the table above names: newline-separated IDs for
pytest and cargo, and a single expression for jest, vitest, cargo-nextest,
and go. Sending raw IDs to a runner that expects one expression is how a
filtered run selects nothing and reports green without reproducing anything.

```bash
INPUT=<filter_input from the plan>          # the declared input's name, not always "filter"
VALUE=$(printf '%s\n' "${IDS[@]}")          # pytest, cargo: one ID per line
# jest/vitest: VALUE=$(printf '%s' "$ESCAPED_ALTERNATION")   one -t regex
# nextest:     VALUE='test(=a) | test(=b)'                   one -E expression
# go:          VALUE='^TestA$|^TestB$'                       one anchored -run regex
gh api -X POST "repos/{owner}/{repo}/actions/workflows/<file>/dispatches" \
  -f ref="$(git branch --show-current)" \
  -f "inputs[$INPUT]=$VALUE"
```

`-f` sends the value verbatim, newlines included. Any other input the
workflow marks `required` is passed the same way. Build the expression forms
with the rules in `targeted-repro.md` (metacharacter escaping for jest and
vitest, anchoring for go, `failure_pairs` for nextest) — the same values the
local rung-0 command uses, so the remote run reproduces the local one.

## When the workflow already has an input of another shape

Use it: the inventory's `dispatch_inputs` names it, and the plan carries the
name in `filter_input`. Read the step that consumes it to learn the value
shape (a single pattern, a space-separated list, a file glob) and send that
shape. Never add a second input beside a working one.

## Verify selected tests and the empty-input path

For a filtered run, inspect a supported test report/listing or runner output
and confirm the intended tests ran. Exit 0 with zero selected tests is
`no-selection`: correct the selector. A different matched test also cannot
verify the repair. Preserve binary/test pairs when identifiers are not unique.

For ordinary push/PR CI, verify the unset input preserves the original command,
options, wrapper, package targets and coverage for this revision. Compare
selected tests or collection output against the expected current test set and
investigate unexpected skips. A historical count is supporting evidence only:
tests may have been added or removed, and equal counts can contain different
tests. Use `ci-coverage.md` for final required-check reconciliation.
