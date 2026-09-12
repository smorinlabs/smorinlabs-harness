# Behavioral evaluations

Use these twenty-two scenarios to review how the skill handles approvals, facts,
evidence, option identity, and communication. The runner records each CLI
session. A human or an independent agent must review the actual output before
assigning a behavioral verdict. For the context and clarification cases, also
use the independent-reader procedure below to check what a reader can understand
from the generated brief alone.

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

Use `--tool claude` or `--tool codex` for one tool. Omit `--cases` to run all twenty-two.
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

## Context and clarification cases

Cases 1 through 13 retain the existing authorization, evidence, delivery, and
question-ID controls. Cases 14 through 22 add the following coverage. The
`CDC-*` identifiers name review findings; they are grader metadata and are not
part of the project conversations.

| Case | Finding | Behavior under review |
|---|---|---|
| 14 | CDC-13 | Identify the concrete repository and workflow files behind opaque automation labels; explain installed but disabled behavior. |
| 15 | CDC-14 | Restore the relationship between a warehouse project's goal, its stock page, and a refresh component after intervening work. |
| 16 | CDC-15 | Honor design-direction approval while preserving separate authority for implementation, merge, credentials, and activation. |
| 17 | CDC-16 | Answer a confused user's artifact and behavior questions with a concrete example while retaining unchanged question and option IDs. |
| 18 | CDC-17 | Replace rejected enable-switch options with credential detection; preserve association and current write access as two required author checks, and retain the superseded decision as history. |
| 19 | CDC-18 | Preserve per-workflow permissions, distinct token sources, applicable restrictions, and unverified effects when simplifying a security explanation. |
| 20 | CDC-19, CDC-20 | Report both export assets' measured latency and compute charges with baselines and calculated differences; preserve opposing metric directions. |
| 21 | CDC-19, CDC-20 | Attribute a reported latency percentage while retaining missing absolute measurements and unresolved budget compliance. |
| 22 | CDC-19, CDC-20 | Retain documented author restrictions; calculate per-workflow allowance shares from measured usage without substituting invocation shares or predicting future consumption. |

Run the new cases together in fresh sessions:

```sh
uv run --no-project plugins/clear-decision-communication/skills/clear-decision-communication/evals/run_evals.py \
  --tool both --cases 14 15 16 17 18 19 20 21 22 --output /tmp/cdc-context-live --run
```

The input artifacts are fictional project files, conversation excerpts, and
inspection records. Their contents describe the scenario; they do not contain
grader expectations or a model answer. Keep new cases in the existing schema:
`prompt` supplies the task, `files` supplies raw artifacts, and `expectations`
holds the separate grading criteria. The runner stages only the prompt and raw
files alongside the skill snapshot. It copies `name`, `covered_findings`, and
`expectations` into the review records, not the generated session's inputs.

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

Also check source fidelity beyond the listed criteria. A response that meets
its naming or question-ID criteria but makes a material unsupported claim is
an overall semantic failure. Keep the individual criterion results, and explain
the additional failure in the existing summary field. Record minor precision
issues separately; do not present a narrow behavioral success as complete
factual correctness.

For measurement cases, match each value to its exact asset, metric, statistic or
denominator, unit, baseline, candidate, and supplied measurement conditions.
Verify calculated percentages and absolute differences against their inputs.
Keep quoted percentages distinct from independent calculations, and check that
missing absolute values remain explicit gaps. Cases 20 and 22 are positive
controls: evidence that is actually supplied must remain in the brief.

The completed-draft source check is an instruction to the generating agent, not
a separate enforced checker process. Relevant tool events can establish source
access; a statement that verification occurred does not prove that the final
claims are supported. Judge the resulting response against its raw inputs.

The runner always leaves semantic grading at `not_reviewed`. Exit code zero
means its selected processes completed successfully, or preparation completed;
it does not mean the skill passed. Neither keyword matching nor a CLI success
message establishes correct behavior. When a behavior fails, investigate the
cause, revise the skill when a concrete correction is identified, and rerun the
affected case in a new output directory. Retain every earlier attempt. Repeated
failures remain recorded limitations; do not retry unchanged inputs merely to
obtain a passing response.

Process status also covers completion of stdout/stderr capture. A descendant
that keeps an inherited pipe open can exhaust the capture timeout after the CLI
exits; that record retains the CLI's exit code alongside `status: timeout`.
Output that arrives from descendants within the bound is retained. Review any
completed response even when process capture times out; an incomplete capture
does not by itself establish incorrect skill behavior.

## Independent-reader check

Use a fresh reader, either a person or an agent, who has not seen the scenario,
the skill instructions, the authoring conversation, or the grading criteria.
The reader assesses comprehension. A separate reviewer compares the answers
with the scenario afterward to assess accuracy. This prevents familiarity with
the source material from supplying context that the brief omitted.

1. A coordinator extracts the complete final user-facing brief from the captured
   CLI events without rewriting, summarizing, or adding explanatory labels. Keep
   all text and artifacts intended to be visible together. If the proposed
   delivery is a question-tool payload, show only the fields the user would see.
   Record the event or output-line provenance separately. If the user-visible
   boundary cannot be established, mark this check inconclusive.
2. Give the reader only that brief, an opaque response identifier, and the
   neutral questions below. Do not add the case name or number, input files,
   earlier conversation, expected answers, finding IDs, model identity, skill
   revision, or `review.json` as extra context. Preserve any details already
   present in the generated brief. Do not give the same reader another version
   of the same case before recording these answers.
3. Record the reader's answers verbatim before revealing source material. Ask
   the reader to use only the brief, avoid outside research, and say "not
   stated" when the brief does not supply an answer. Do not coach the reader
   toward an intended interpretation.
4. After the answers are fixed, the reviewer reads the raw artifacts and
   expectations and compares them with the brief and the reader's answers.
   Record omitted context, unsupported inferences, incorrect interpretations,
   and any decision the reader could not identify. A confident reconstruction
   is not a pass unless it agrees with the scenario. An accurate statement that
   the reader cannot understand still needs a communication correction.
5. Save the response identifier, brief provenance, reader identity, exact
   questions and answers, and reviewer findings in `reader-review.md` beside the
   case's `review.json`. Reference that file from the existing review summary
   and criterion evidence fields. The reviewer assigns the semantic verdict
   using both the comprehension result and the source comparison. Do not add
   runner fields or treat this manual check as an automated grade.

Give every reader the same neutral questions, without case-specific additions:

- What project or work is this about, and what part of it is being discussed?
- What exists now, and what would change?
- What, if anything, are you being asked to decide or supply?
- What would each response cause next, and what would happen later?
- What are the main consequences, and what remains unknown?
- Which parts could you not determine from the brief?

When comparing skill revisions, retain a separately identified response and
reader record for each version. Reveal the version identities only after the
reader answers are fixed. Keep a source-accuracy finding separate from a
comprehension finding, even when the same sentence causes both.

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

Cases 17 and 18 include a fixed earlier exchange and a simulated latest user
reply. Each still runs as one fresh session producing one response. The runner
does not conduct a live multi-turn conversation, solicit real confusion, resume
a prior generated response, or automatically check persistence of a corrected
decision. A live follow-up audit needs a separate controlled conversation with
the before message, actual reply, and after message retained as distinct
evidence. The independent-reader procedure is also manual; the runner neither
recruits a reader nor produces or grades `reader-review.md`.

Claude runs with read tools, restricted mode, no customizations, and no MCP
servers. Codex runs read-only with user configuration, automatic project-document
loading, host skill discovery, plugins, hooks, memories, and delegation disabled.
Existing authentication and platform-enforced instructions can still affect a
session. Read-only CLI controls are not a security sandbox against hostile models
or executables. These cases assess the explicitly supplied skill, not whether a
plugin is installed correctly or automatically triggers on an ordinary request.
