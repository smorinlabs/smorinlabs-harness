# Shift left — offer the failed check as a hook (step 6b)

The fastest CI fix is the one that never reaches CI. Once the target job is
green at rung 2 and before the rung-3 push, ci-fix offers to run the check
that just failed as a git hook, so the same class of failure is caught at
commit or push time next time. An accepted offer becomes the marker-free
commit that carries rung 3 (`fix-loop.md`, *Rung 3 after 2d*), so it costs
no extra CI run; a declined one leaves the empty `ci: full run` commit to do
that job.

## When to offer

All of these, else skip with the reason in the report:

- the fixed job's class was code, test, or lint (a workflow-config fix or a
  flake has no check to shift);
- the step-3 parity list shows no hook already running that step's tool;
- the repo has a hook manager (`lefthook.yml` or `.pre-commit-config.yaml`).
  With neither, the offer is to add lefthook with this one hook — only when
  `command -v lefthook` resolves; otherwise the offer names the install
  (`brew install lefthook`, or the platform equivalent) as its first step and
  is made only if the user takes it. A declined offer is recorded, never
  re-asked in the same run.

## Stage from the profile

| The failed step's median (profile `steps`) | Stage | Why |
|---|---|---|
| under the threshold | `pre-commit` | cheap enough to run on every commit |
| over the threshold | `pre-push` | a 10-minute pre-commit hook gets bypassed with `--no-verify` within a week |

## Render the hook

From the inventory's step record: the `run:` command, its `working-directory`
(step or `defaults_run`), and its `env`. Narrow to the changed files only
where the tool takes a file list (`ruff check`, `eslint`, `prettier`);
a test runner gets the CI command unchanged — passing staged source files to
`pytest` collects nothing, exits 5, and blocks every commit. The `glob:` /
`files:` pattern restricts *when* the hook runs, never *what* it runs.

lefthook (`lefthook.yml`):

```yaml
pre-commit:              # or pre-push, per the table
  commands:
    <check-name>:
      glob: "<pattern the step's files match, e.g. '*.py'>"
      root: "<working-directory, when the step has one>"
      run: <the step's run command; {staged_files} on pre-commit, {push_files} on pre-push, only where the tool takes files>
```

pre-commit framework (`.pre-commit-config.yaml`):

```yaml
- repo: local
  hooks:
    - id: <check-name>
      name: <check-name>
      entry: <the step's run command; with a working-directory: bash -c 'cd <dir> && <command>'>
      language: system
      pass_filenames: <true only when the tool takes files>
      files: "<pattern>"
      stages: [<pre-commit | pre-push>]
```

## The question, the commit, the proof

Ask once, with AskUserQuestion: the check, the stage, and the rendered block,
with "add it" recommended when the stage is `pre-commit` and neutral when it
is `pre-push`. On yes: show the diff (a repo with no hook manager gets a new
`lefthook.yml` with this one hook, which is why the skill grants `Write`),
commit as `chore(hooks): run <check> on <stage>` with no skip marker, install
the stage (`lefthook install` / `pre-commit install --hook-type <stage>` —
`pre-commit install` alone installs only `pre-commit`), confirm the hook file
at `"$(git rev-parse --git-path hooks)/<stage>"`, run it once
(`lefthook run <stage>` / `pre-commit run --all-files --hook-stage <stage>`)
to prove it fires, then push: that push is rung 3. On no: the report's
*Shift left* line says declined and the empty `ci: full run` commit carries
rung 3 instead.

Never add a hook silently, and never add one for a check that CI itself does
not run — parity means the hook mirrors CI, not the other way round.
