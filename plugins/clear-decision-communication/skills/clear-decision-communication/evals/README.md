# Behavioral evaluations

Use these thirteen scenarios to review how the skill handles approvals, facts,
evidence, option identity, and communication. The runner records each CLI
session. A human or an independent agent must review the actual output before
assigning a behavioral verdict.

## Run the scenarios

Requirements: macOS or Linux, Python 3.12 or later, `uv`, and an installed,
authenticated `claude` or `codex` CLI. Run these commands from the repository's
root directory. Process capture uses POSIX process groups and selectable pipes;
native Windows execution is not supported. Scenario input paths use relative,
forward-slash paths; Windows drives and backslashes are rejected on every host.
The runner uses Python's standard library and selects no model, effort, or
provider. CLI compatibility is based on the installed tools' help; an unsupported
flag is a process error, not a skill failure.

First prepare the inputs and review records without invoking either CLI:

```sh
uv run --no-project plugins/clear-decision-communication/skills/clear-decision-communication/evals/run_evals.py \
  --output /tmp/cdc-prepared
```

Then run a small selection in fresh sessions on both tools:

```sh
uv run --no-project plugins/clear-decision-communication/skills/clear-decision-communication/evals/run_evals.py \
  --tool both --cases 1 2 4 --output /tmp/cdc-live --run
```

Use `--tool claude` or `--tool codex` for one tool. Omit `--cases` to run all thirteen.
Model calls use the existing account's authentication and may consume its usage
allowance. Each call defaults to a 120-second runtime limit and a combined
1,048,576-byte stdout/stderr limit. Change those bounds with `--timeout` and
`--max-output-bytes` when warranted. Timeouts, output overflow, and interruption
terminate the spawned process group. There is no automatic retry.

`--output` must name a directory that does not exist. The runner refuses to reuse
an existing directory, including a preparation directory. Choose a new path for
each run so old evidence and grading cannot be silently overwritten. The chosen
directory is retained until you remove it; copy it elsewhere if your temporary
directory is periodically cleared.

## Review the results

The output directory contains a hashed snapshot of `SKILL.md` and `references/`,
plus a manifest of the selected cases. Every mode retains each case's exact
prompt, raw input files, process record, and separate `review.json` expectations.
Prepare mode records `status: not_run` and makes no CLI call. With `--run`, the
runner also retains tool-version output, stdout events, and stderr.

Read the entire response and relevant tool events. In `review.json`, set
`semantic_verdict` to `pass`, `fail`, or `inconclusive`; identify the reviewer;
and give evidence for each criterion's `met` value. Cite output lines or exact
response excerpts and explain their significance. Keep process problems separate
from incorrect decisions. A timeout may leave too little evidence to grade.

The runner always leaves semantic grading at `not_reviewed`. Exit code zero
means its selected processes completed successfully, or preparation completed;
it does not mean the skill passed. Neither keyword matching nor a CLI success
message establishes correct behavior. When a behavior fails, revise the skill
and run that case again in a new output directory.

Process status also covers completion of stdout/stderr capture. A descendant
that keeps an inherited pipe open can exhaust the capture timeout after the CLI
exits; that record retains the CLI's exit code alongside `status: timeout`.
Output that arrives from descendants within the bound is retained. Review any
completed response even when process capture times out; an incomplete capture
does not by itself establish incorrect skill behavior.

## Scope and limitations

Each case starts in a separate temporary working directory containing only the
skill snapshot and its raw scenario inputs. Expected answers, finding IDs, case
names, earlier outputs, and grading instructions are excluded from that context.
The temporary directory is removed after the case. The durable input copy remains
available for review.

The cases simulate the next reply and immediate action. They do not merge code,
change accounts, delete workspaces, send messages, or exercise native question
dialogs. In the interface scenario, a proposed tool payload can be reviewed for
schema compatibility, but this does not establish actual dialog rendering.

Claude runs with read tools, restricted mode, no customizations, and no MCP
servers. Codex runs read-only with user configuration, automatic project-document
loading, host skill discovery, plugins, hooks, memories, and delegation disabled.
Existing authentication and platform-enforced instructions can still affect a
session. Read-only CLI controls are not a security sandbox against hostile models
or executables. These cases assess the explicitly supplied skill, not whether a
plugin is installed correctly or automatically triggers on an ordinary request.
