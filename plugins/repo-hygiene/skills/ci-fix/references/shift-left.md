# Shift left — offer the failed check as a hook (step 6b)

The fastest CI fix is the one that never reaches CI. After every job is green
on the pushed commit, and only then, ci-fix offers to run the check that just
failed as a git hook, so the same class of failure is caught at commit or push
time next time.

## When to offer

All of these, else skip with the reason in the report:

- the fixed job's class was code, test, or lint (a workflow-config fix or a
  flake has no check to shift);
- the step-3 parity list shows no hook already running that step's tool;
- the repo has a hook manager (`lefthook.yml` or `.pre-commit-config.yaml`).
  With neither, the offer is to add lefthook with this one hook; a declined
  offer is recorded, never re-asked in the same run.

## Stage from the profile

| The failed step's median (profile `steps`) | Stage | Why |
|---|---|---|
| under the threshold | `pre-commit` | cheap enough to run on every commit |
| over the threshold | `pre-push` | a 10-minute pre-commit hook gets bypassed with `--no-verify` within a week |

## Render the hook

From the inventory's step record: the `run:` command, its `working-directory`,
and its `env`. Narrow to staged files where the tool supports a file list
(`ruff check {staged_files}`, `pytest` on the tests that changed); otherwise
run the command as CI does.

lefthook (`lefthook.yml`):

```yaml
pre-commit:              # or pre-push, per the table
  commands:
    <check-name>:
      glob: "<pattern the step's files match, e.g. '*.py'>"
      run: <the step's run command, {staged_files} where the tool takes files>
```

pre-commit framework (`.pre-commit-config.yaml`):

```yaml
- repo: local
  hooks:
    - id: <check-name>
      name: <check-name>
      entry: <the step's run command>
      language: system
      pass_filenames: <true when the tool takes files>
      stages: [<pre-commit | pre-push>]
```

## The question, the commit, the proof

Ask once, with AskUserQuestion: the check, the stage, and the rendered block,
with "add it" recommended when the stage is `pre-commit` and neutral when it
is `pre-push`. On yes: show the diff, commit as
`chore(hooks): run <check> on <stage>`, push, and run the hook once locally
(`lefthook run pre-commit` / `pre-commit run --all-files --hook-stage <stage>`)
to prove it fires. On no: the report's *Shift left* line says declined.

Never add a hook silently, and never add one for a check that CI itself does
not run — parity means the hook mirrors CI, not the other way round.
