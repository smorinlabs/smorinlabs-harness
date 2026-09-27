# Evidence: status, support, and measurements

How each claim in a brief shows what supports it. Read this at workflow step 3,
while preparing evidence, and again at step 6, when checking the completed
draft against its sources.

## Evidence status

Make each claim's evidence status clear in words, never as a fabricated
confidence number. Use a source attribution or concise label when needed;
do not prefix every sentence or populate empty evidence categories.
**Verified** means observed directly or established by an executed
test or analysis, with the revision or environment it ran on. A document's
report remains attributed to that document unless independently checked.
**Inferred** means derived from those results, including estimates with their basis;
**Assumed**, or a preference driving the recommendation; **Not verified**, an
unknown or a check still outstanding. A generic "tests pass" never implies
coverage that was not run; name the targeted checks and say what full
validation would add. Tests can establish that an implementation is correct
while whether the behavior is desirable remains the human's call. For timing
and concurrency, give the interaction argument as an inference beside the test.
Material uncertainty stays in the initial view; supporting detail such as diffs,
logs, and traces goes behind the details pointer, and only one level of detail
exists below the initial view.

Simplification preserves the subject, scope, conditions, and status of each
decision-critical claim. Agreed behavior is a requirement, not a validated
implementation. Where components differ, identify each one's permissions,
safeguards, and unknowns. A workflow's declared permissions do not establish
the effective permissions of a separately obtained credential.

Before sending, trace each decision-critical claim back to its support. A label
such as "Verified" does not make a stronger statement follow from its source:

- A documented trigger and an exercised trigger are different evidence. Retain
  the tested actor, event, and conditions; label broader predictions as inferences.
- Registry metadata can establish a declared licence or version. It does not
  establish a tool's mechanism, installation speed, suitability, or legal
  compatibility. Cite support specific to each claim and preserve unverified
  limits. A project ruling establishes the check's scope or the project's
  acceptance decision; it does not establish a general legal conclusion.
- Comparative words are claims too. Do not call an alternative "faster" when
  its speed has not been measured. Describe the known mechanism, or label the
  expected improvement as an inference with its basis. An uncertainty label
  later in the brief does not repair an unqualified comparison in the opening.
- A policy that requires a check does not predetermine every candidate's result.
  An exemption from that check does not approve every tool or waive other
  requirements. Distinguish the named tool's recorded disposition from the
  rule for future tools. A compatible alternative can change implementation
  without changing policy; untested alternatives remain candidates to investigate.
- An overall comparison does not establish a win on each metric. Keep aggregate
  conclusions aggregate unless separate measurements are supplied.
- An omitted check or UI behavior is unknown, not absent. "Not selected",
  "not tested", and "test status not recorded" describe different gaps; carry
  each finding's actual status into summaries and decision records.
- A request interval is not a maximum data age. An age estimate also needs
  assumptions about response time, source freshness, and failures. Remaining
  effects after reversal do not establish a need for manual cleanup.

Derive approval gates from the user's instructions and identified policy, not
from an imagined later stage. If exact patch bytes or other evidence are
unavailable, state the gap and the intended action. Omit unsupported additions;
never fill a template field with invented evidence, effects, or constraints.

## Reporting measurements

For each reported measurement, identify the exact asset measured and its role, the metric,
statistic or denominator, unit, source, and relevant revision/date and conditions.
For a comparison, identify both baseline and candidate. When reporting a
percentage improvement, include the percentage, both absolute values, and the
absolute difference when the sources supply them or support their calculation.
Say whether the percentage is quoted from the source or calculated from supplied
values. Preserve the direction of change; distinguish relative percent change
from percentage-point change. If a baseline or absolute value is missing, state
the gap instead of inventing it or presenting the percentage as independently
checked. Preserve exact quotations and point to the supporting source.
