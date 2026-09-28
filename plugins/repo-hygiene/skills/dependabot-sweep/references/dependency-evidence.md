# Dependency and check evidence

The classifier receipt explains what the changed files control and what
validation actually exercised. Read the complete diff and the relevant
installation, generation and workflow entry points before making this receipt.
The evaluator validates its structure and correspondence to observations;
it cannot independently infer every repository's dependency graph from a
classifier's claims. Evidence must name the sources that support those claims.

## Receipt identity

Pass the full JSON receipt with `pr evaluate --receipt PATH`. The existing
`--dependency-only` flag alone supplies no consumer or check evidence and cannot
establish readiness. Version-1 receipts remain readable but require refreshed
evidence before a new merge evaluation.

Version 2 includes these fields:

| Field | Meaning |
| --- | --- |
| `schema_version` | `2` |
| `head_sha`, `base_sha` | Full commits inspected; both must match the observation. |
| `files_digest`, `file_count` | The digest and count from the complete changed-file list. Use `ClassifierReceipt.for_files` in ../scripts/sweep_evaluator.py to calculate these rather than inventing a digest. |
| `dependency_only` | Whether the complete diff is eligible for dependency-only preparation; fixture and source changes still need ordinary review. |
| `classifier`, `at` | Who inspected the change and when. |
| `dependency_evidence` | The complete file, consumer and version mapping below. |
| `check_evidence` | Relevant check applicability and proof below. |

Do not attach an old receipt to a new head, base or file list. Preserve the old
receipt as history and perform a fresh inspection. A changed approval target
still needs the existing exact-commit authorization checks.

## Files, consumers and requested versions

The `dependency_evidence` object contains `complete: true` and these lists:

| List | Required contents |
| --- | --- |
| `files` | Each changed file and the related inputs needed to explain its dependency graph: `path`, `blob_sha`, `role`, `generated_from`. Roles are `manifest`, `lockfile`, `generated_export`, `fixture`, `workflow`, `source`, or `config`. Locks and exports name mapped inputs in `generated_from`. |
| `consumers` | Every affected installation, automation or fixture consumer: `id`, `kind` (`install`, `automation`, `fixture`), mapped `files`, actual `entrypoints`, `usage` and supporting `evidence`. |
| `updates` | Each requested package/action update: `name`, selected exact target `requested`, mapped `files`, supporting `evidence`, and its affected `consumers`. Explain how an exact target was selected when the manifest expresses a range. |

Each update's consumer entry identifies `consumer`, `resolved`, `tested`, and
the `validation` that establishes the tested target. Requested, resolved and
tested versions must agree for an affected executable consumer. Do not omit a
secondary installer because the main test workflow does not use it. The file
relationships must account for every changed dependency file and every real
consumer affected through a lock or generated export.

The current schema selects one exact target per update. It cannot represent
different valid targets for platform-specific or range-constrained consumers
of the same update. Report that limitation as incomplete evidence and route
the change through ordinary review; do not invent identical installed versions.

A generated export can intentionally contain a subset of the dependency graph.
For example, a runtime export may omit a development-only package. Record that
consumer explicitly with `applicability: "excluded"` and an `exclusion` containing
its documented `source` and `reason`. A consumer whose own input was directly
changed cannot be excluded. Set its `resolved` and `tested` to `null` and include
exact-head `validation` proving the package is absent from that consumer. This
cannot excuse a consumer that still installs an older version. At least one
affected executable consumer must validate the requested target. The evidence
must establish why this update does not affect the excluded environment;
absence from one convenient test is not an exclusion.

Validation is one of:

- An observed check: `kind: "check_run"`, `head_sha`, `context`, `producer_id`,
  `run_id`, and `evidence` tying its command/environment to that exact target.
- An observed commit status: `kind: "status"`, `head_sha`, `context`, `creator`,
  `target_url`, and `evidence` tying the external CI log to that exact target.
  The status must currently succeed on the observed commit, with the same
  context, creator and URL. Its applicability record must use
  `producer_id: null`, status proof, dependency coverage, and all of the
  consumer's inputs.
  This does not satisfy a required check bound to an application producer.
- A local validation: `kind: "local"`, `head_sha`, `command`,
  `result: "success"`, and `evidence` containing the observed result. A proposed
  command or passing test from another commit is not local validation.

A fixture consumer needs evidence of how the bytes are used and whether they
are installed, imported or distributed. A fixture path alone proves nothing.
That classification calls for ordinary review and a concrete disposition
recommendation; it does not manufacture an owner veto or establish that the
named vulnerable package is harmless.

Examples of distinct judgments:

- A requirements export changes, but frozen-lock tests install the old version:
  record the untested update and identify the missing consumer validation.
- A generated export still has a development-environment installer: preserve
  that consumer and repair the generation/validation path.
- A fixture manifest is read as duplicate-file test input: describe that use
  and its invariants; do not claim a runtime security remediation from the bump.
- A dependency group crosses a plugin API change: validate the plugin's actual
  integration, including existing snapshots, rather than accepting a successful
  installation as compatibility proof.

## Check applicability

The `check_evidence` object contains `complete: true`, `basis` and `checks`.
The basis identifies the mapped workflow/configuration `files` and `evidence`
used to decide which checks apply. Each check entry identifies:

| Field | Meaning |
| --- | --- |
| `context`, `producer_id` | Check name and the producer expected to report it. |
| `applicability` | `applicable`, `excluded`, or `unknown`. |
| `scope` | `source`, `dependencies`, or `source_and_dependencies`. |
| `paths` | Mapped files to which this coverage judgment applies. |
| `reason`, `evidence` | Why the check applies or does not, with the inspected source. |
| `exclusion` | For an exclusion, its documented `source` and `reason`. |
| `proof` | When needed for a neutral analysis result, exact analysis evidence described below. |

Applicable checks need observed successful execution at the matching commit
from the correct producer. A neutral wrapper is not proof that its underlying
analysis ran. An analysis proof includes `kind: "analysis"`, `head_sha`,
`producer_id`, `id`, `url`, `conclusion: "success"`, and supporting `evidence`.

An existing commit-status check can instead use proof with `kind: "status"`,
`head_sha`, `creator`, `target_url` and `evidence`, matched to the observed
successful status. This preserves legitimate status-only checks; it cannot
satisfy a required check bound to a different application producer.

An explicit path/event exclusion may explain a missing optional scan. Unknown
applicability or missing applicable evidence remains a hold. Do not require
every configured scanner for every PR simply because it exists. Conversely,
a classifier cannot exclude or otherwise waive a repository-required check,
its producer identity, review requirements or other existing merge gates.

The evaluator reports missing, malformed, stale or inconsistent evidence as
`K13` (evidence incomplete), with a recommendation to refresh it. That result
does not claim a demonstrated dependency regression. Actual failed checks retain
their failure attribution and must be diagnosed using the normal baseline
comparison procedure.
