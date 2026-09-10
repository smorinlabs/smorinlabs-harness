# The filter input — isolated tests in CI

A `workflow_dispatch` input that carries the failing test IDs into the test
step, so a dispatched run executes only those tests: the remote mirror of
rung 0. This is the one rendering; step 6's offer (`offer-filter` in the
plan) and `optimize.md`'s lever 11 both use it.

Two rules make it safe and honest:

- **The input is data, never code.** Its value reaches the shell through an
  environment variable and is split on newlines into an array. No `${{ }}`
  inside `run:` (GitHub substitutes that into the script before the shell
  runs it), no `eval`, no unquoted expansion. A dispatch input can only be
  set by someone with write access, but the pattern costs nothing and reads
  the same on every runner.
- **An empty input runs the whole suite.** Push and pull-request runs never
  set the input, so the workflow must behave exactly as before on those
  events. The rung-3 run proves it: its test count in the log matches the
  profile's, and the report says so.

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

```bash
gh api -X POST "repos/{owner}/{repo}/actions/workflows/<file>/dispatches" \
  -f ref="$(git branch --show-current)" \
  -f "inputs[filter]=$(printf '%s\n' "${IDS[@]}")"     # IDS: the raw failures list
```

`-f` sends the value verbatim, newlines included. Any other input the
workflow marks `required` is passed the same way.

## When the workflow already has an input of another shape

Use it: the inventory's `dispatch_inputs` names it, and the plan carries the
name in `filter_input`. Read the step that consumes it to learn the value
shape (a single pattern, a space-separated list, a file glob) and send that
shape. Never add a second input beside a working one.

## Verifying the empty-input path (rung 3)

After the marker-free commit runs, fetch the test step's log from the rung-3
run and compare the test count with a profiled run of the same job (the
profile's slowest-step line, or the summary line in a sampled run's log). A
smaller count means the input leaked into push runs; fix before done.
