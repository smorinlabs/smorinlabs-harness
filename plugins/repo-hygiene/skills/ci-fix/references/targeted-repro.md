# Targeted reproduction — useful scope in a suitable environment

Use `validation-contract.md`. Start with failing IDs or the smallest useful
target, then verify affected behavior. Run a complete bundle directly only
when its compatible local total is measured at approximately 30 seconds or
less. Full-step execution requires a reason, not merely an available command
or a duration below ten minutes.

## Extract the failing IDs

```bash
gh api "repos/{owner}/{repo}/actions/runs/<run_id>/jobs?per_page=100" \
  --jq '.jobs[] | select(.conclusion=="failure") | {id, name, failed_steps: [.steps[] | select(.conclusion=="failure") | .name]}'
gh api --allow-escape-sequences "repos/{owner}/{repo}/actions/jobs/<job_id>/logs" > "$SCRATCH/job-<job_id>.log"
python3 <skill-dir>/scripts/extract_failures.py --json "$SCRATCH/job-<job_id>.log"
```

`<run_id>` is the failed run from SKILL.md step 1; the first call yields the
failed job's `id` and its failed step names.

**IDs are data, never shell text.** A contributor controls test names and
parameter IDs, and `$(…)` inside double quotes executes on the maintainer's
machine. Every local command below takes the ID from the script's
`failures_quoted` list verbatim — single-quoted by `shlex.quote` when it
contains anything outside `[A-Za-z0-9_@%+=:,./-]`, bare otherwise — and never
re-interpolates the bare `failures` entry into a shell string. An ID that
still looks like shell syntax after quoting is shown to the user before it
runs. The script strips GitHub's per-line timestamps
and ANSI color, detects the runner, and returns
`{"format": "pytest", "failures": [...], "failures_quoted": [...], "packages": [...]}`;
commands take IDs from `failures_quoted`. Exit 1 means no IDs were recognized — go to *No IDs* below. Force a runner with
`--format pytest|jest|vitest|cargo|nextest|go` when a log mixes tools.

## Map the CI step to a local command

Read the failed step's `run:` line in the workflow. Keep its wrapper (`uv run`,
`npx`, `pnpm`, `just`, `make`, `cargo`, `go`) and narrow the target:

| Runner | CI step looks like | Targeted form | Full scope, only when justified |
|---|---|---|---|
| pytest | `uv run pytest` / `pytest tests` | `uv run pytest -x <id> [<id> …]` — IDs are node IDs, taken from `failures_quoted` | the `run:` line verbatim |
| jest | `npm test` / `npx jest` | `npx jest -t <quoted pattern>` — `-t` is a **regex**, so escape every metacharacter in the name first (`(`, `)`, `[`, `.`, `+`, `*`, `?`, `$`, `^`, `\|`) or a name like `parses (float)` matches nothing and Jest exits 0, a false green; then quote as `failures_quoted` does, with ` › ` replaced by a space | the `run:` line verbatim |
| vitest | `npx vitest run` | an ID is `<file> > <suite> > <name>` (or `<file>` alone for a suite that failed to load): `npx vitest run <quoted file> -t <quoted pattern>` with the last ` > ` segment as the pattern, escaped as for jest; a file-only ID runs `npx vitest run <quoted file>`. **The file is shell-quoted like every other extracted value** — a committed test filename can contain `$(…)`, which would execute here; split the ID yourself and quote each half, never paste the raw ID | the `run:` line verbatim |
| cargo | `cargo test` | `cargo test <module::tests::name> -- --exact` | the `run:` line verbatim |
| cargo-nextest | `cargo nextest run` | `cargo nextest run -E 'test(=<name>)'`; to scope a test to its binary use its own pair from `failure_pairs`, `-E 'binary_id(<id>) & test(=<name>)'` — never a binary from `packages` with a test from `failures`, because the same test name can fail in one binary and pass in another, so the cross product runs a passing test or none; several pairs join with ` \| ` inside one expression | the `run:` line verbatim |
| go | `go test ./...` | `go test <package> -run '^<TestName>$'` — for an ID with `/`, split on it and anchor each segment: `TestParent/sub` → `-run '^TestParent$/^sub$'`; `<package>` from `packages` when present, else the package of the failing file | the `run:` line verbatim |
| just / make wrapper | `just test`, `make test` | inspect the recipe; use its narrowing option/target, or an equivalent inner command preserving setup, environment and options | the recipe |
| lint / format / typecheck | `ruff check .`, `eslint .`, `tsc` | the tool on the files the log names (`ruff check <file>`); select the affected project when the checker supports project boundaries | the `run:` line verbatim |
| build | `cargo build`, `npm run build` | select the affected package/artifact when supported; otherwise state why the complete build is necessary | the `run:` line verbatim |

These are runner forms, not permission to replace the original wrapper.
Keep original configuration, options, package targets and setup. For example,
inspect what `npm test` executes before substituting an `npx jest` command.
The quoting examples target POSIX shells; use native argument passing for
PowerShell or other shells. Never apply `shlex.quote` as PowerShell quoting.

## Establish local execution eligibility

Use the inventory as facts to inspect, not an executable replay plan:

- `condition_state` and `continue_on_error_state` are booleans or `null`
  (unknown). Raw `if`/`continue_on_error` remain available. Only literal
  booleans, including literal boolean expressions, are recognized; arbitrary
  GitHub expressions are not evaluated. Check both job and step conditions.
- Preserve `environment`, tag/branch/path filters, container configuration,
  services, and dependencies. A false guard excludes that execution; an unknown
  guard needs actual context before deciding. A deployment environment is not
  implicit permission to run commands locally.
- `validation_kind: candidate` identifies a simple known check to inspect.
  `inspect` means wrappers, compound commands or shell semantics need reading;
  `not-validation` excludes known publication/setup commands. No label grants
  execution authority. `run` plus `setup: false` alone is never eligibility.
- Verify `effective_shell`, `effective_working_directory`, `effective_env`,
  the toolchain version and architecture against the selected cell. An unset
  Windows shell defaults to PowerShell; a container defaults to `sh`; Linux
  and macOS default to bash when available, otherwise sh. Matrix/unknown runners
  need resolving before choosing defaults.
- Resolve `unresolved_expressions` and other needed context from known values,
  or report `unsupported`. Do not drop inputs/secrets or skip essential actions
  to manufacture a local equivalent. `bad substitution`, exit 127, missing
  artifacts/services and similar preparation errors are not new code defects.
- Inspect prerequisites, including `uses:` actions, without blindly replaying
  them. A Linux runner from `local-runners.md` may provide suitable toolchains
  or services. Availability alone does not establish parity. A portable check
  may run on the host with a stated reason; platform-sensitive behavior needs
  a matching environment.

Only identified, authorized validation enters the selected check set. An
unguarded `npm publish` is excluded even when it is short or authenticated.
A simple pytest command with suitable prerequisites remains eligible. Read
`make`, `just`, npm scripts and compound commands rather than classifying them
by their name or by stripping shell tokens.

## No IDs, widening, and selection evidence

When extraction yields no IDs, read the failure and find a useful file,
module, package or check. A compiler/build command may be indivisible; record
that as `--full-step-reason`. Do not default every extraction failure to the
whole suite.

After editing, rerun the reproducer and checks connected to affected code,
fixtures, shared configuration or dependencies. Widen when needed; do not
repeat a nine-minute suite solely because it is under the former cap. Necessary
long validation uses the harness background mechanism, captured output and a
bounded wait. State the expected cost and distinguish preparation from test time.

For every targeted test run, inspect supported reports/listings or runner
output for the intended IDs. Exit 0 with zero tests is `no-selection`; a
matching count containing different tests is also insufficient. Correct the
selector before claiming a repair or recording success. An unavailable
selection report remains an explicit limitation. Preserve nextest binary/test
pairs and the already-correct runner input grammars in `filter-input.md`.

## Timing — record compatible execution context

Time the actual selected commands. Record successful timings only after
verification, including intended selection. Each sample keeps a hash of a
non-secret execution description, not raw environment values. Write that
JSON with a file tool; the shape is:

```json
{
  "command": "uv run pytest tests/unit",
  "scope": "tests/unit",
  "environment": {
    "runner": "host",
    "os": "linux",
    "arch": "x86_64",
    "shell": "bash",
    "working_directory": ".",
    "toolchain": "python3.12"
  }
}
```

Use the actual command and selected scope, plus relevant image/VM identity,
configuration and service assumptions. Include identifiers or hashes, never
credentials or secret-valued environment contents. A narrowed test and the
whole step need different contexts. The planner's context must describe the
command whose step cost it is estimating; a targeted sample cannot estimate
a different full command.

```bash
LEDGER=$(python3 <skill-dir>/scripts/local_ledger.py path --repo <owner/repo>)
python3 <skill-dir>/scripts/local_ledger.py record --ledger "$LEDGER" \
  --context "$SCRATCH/execution-context.json" \
  --workflow "<workflow name>" --workflow-path "<.github/workflows/file.yml>" \
  --job "<job display name>" --step "<step display name>" \
  --seconds <measured seconds> --conclusion success
```

`record`/`median` require `--context`; `path` writes nothing. The ledger keeps
10 successful samples per workflow/path/job/step/context with timestamps.
A changed command, scope or relevant environment has a different identity.
Legacy samples are preserved but ignored for compatible queries. The planner
without `--context` uses no ledger samples. CI medians and first-container
multipliers remain estimates, never proof of a fast complete bundle.

Record a complete bundle's total separately in the task evidence before using
`--bundle-seconds`: list its checks and preparation, sum sequential costs, or
use a measurement of the actual parallel execution while reporting aggregate
work separately. A timing measurement is not a passing result for changed code.

## Affected neighboring checks (legacy rung 1s)

Choose neighbors because the repair affects them, not because they are fast.
Deduplicate equivalent commands, batch compatible fixes and reuse passes only
when tested code and relevant execution inputs remain compatible.

**Join inventory to profile** by workflow **file path** and the resolved job
name. For a matrix job use the selected cell's `display_name` first; for a
non-matrix job use its explicit name or job `id`. Match the profile's
`workflow_path` and `job`; its decorated `name` is for presentation only.
An unknown/expression-based name is unresolved, not an invitation to borrow
another row. A missing timing row is unmeasured, not missing validation.

Apply the eligibility rules above to each affected command. Reproduce relevant
prerequisites or record why equivalent local verification is unavailable.
Capture outputs and verify selection. A tolerated failure retains its actual
result; it does not verify a claimed repair, even when policy permits CI to
continue. Investigate a new red only after ruling out preparation/selection
errors. Attempt counting is in `fix-loop.md`.
