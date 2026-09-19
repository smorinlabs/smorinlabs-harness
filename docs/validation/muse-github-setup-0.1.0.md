# Muse GitHub setup 0.1.0 — local validation

Date: 2026-09-19. Scope: author the public installer/templates, integrate with
the optional private credential provisioner, and validate locally. No target
repository was activated, real credential installed, paid model run made, or
live skill placement changed.

## Delivered behavior

`muse-github-setup`, in the new `muse-github` plugin, installs automatic diff-based
PR feedback and optional manual fix PRs. The templates use
`model_api/muse-spark-1.3-contributor` and `META_MUSE_CI_API_KEY`, with a distinct
key per target repository. A compatible private `repo-secrets --app muse-ci`
provider can detect the setup worktree and provision that key; otherwise the
skill provides a secure handoff and name-presence check.

The direct upstream Action is pinned at
`a97622c801f4ca571530ddc51076af659a9c32cd`. Its installer/CLI remain moving
dependencies by deliberate design. No replacement installer was authored.

## Deterministic checks

| Check | Result and scope |
|---|---|
| `uv run pytest -q tests/test_muse_github.py` | 24 passed; preservation/conflicts/idempotence, actors/membership, stale inputs, exact-commit checkout, isolated configuration preparation, case variants, size limits, and event/token separation |
| `actionlint` on both templates | Passed |
| `harness-kit gen` and `gen --check` | Passed; both manifests and marketplace entry generated |
| System skill-creator `quick_validate.py` | Passed for the new skill |
| Private integration contract | Both actual public workflow templates return true through the private structural detector |
| Independent installer fixture | Plan writes nothing; apply preserves instructions, existing provider/model/plugin/agent settings and unrelated `.opencode` files; repeat apply changes zero files |

The commit test uses a local bare remote. After freezing the PR branch at one
SHA, it advances the remote and executes the inspected runner's fetch/checkout
sequence. The worktree stays at the earlier SHA while the remote ref advances.
This proves the tested Git behavior, not atomic GitHub comment publication.
All fixtures use synthetic credentials and no GitHub, Meta, or 1Password calls.

## Installed OpenCode probe

The local binary reported `1.18.27`. In disposable directories with fresh XDG
paths, a synthetic Meta key, and no real credentials in the child environment:

- `opencode debug config` loaded both profiles with the intended default agent,
  disabled sharing/language servers/formatters, and permission maps.
- An untrusted project config selected a fixture agent when project discovery
  was enabled. With `OPENCODE_DISABLE_PROJECT_CONFIG=true`, the trusted agents
  remained selected. This inverse control proves the flag mattered in this binary.
- `opencode debug agent muse-review` and `muse-fix` returned the effective
  agents. Inspection of merged rules confirmed 16 expected decisions: shell,
  web, subagents and outside directories denied; review file access denied;
  ordinary fix-file read/edit allowed; credential-like read and workflow edit denied.

These are configuration-loading and effective-rule checks, not model-driven
tool executions. They do not establish behavior of the Action's future CLI,
the inspected `1.18.31` runtime, GitHub policies, or live review/fix runs.
No model inference was used for the probes.

## Skill-quality gate

| Layer | Result |
|---|---|
| Content, triggers, privacy, tool grants | Pass; no name collision among 183 distinct installed names; adjacent CI/iteration/credential skills remain separate |
| Documentation | Pass; guide, README, source/license record, fallback, prerequisites and acceptance limits present |
| Harness conventions | Pass; metadata and generated manifests agree |
| Static loading | No errors on Claude or Codex. Claude warns that the generator's existing `_generated` field is ignored. Codex checks the manifest only. Tool versions are newer than the verifier's recorded baselines |
| Session-backed/live acceptance | Not run; outside local authoring scope |

Independent review found and verified corrections for outside-writer edits to
PR workflow YAML before a member-triggered run, case-sensitive credential-path
rules, and JSON expansion exceeding Linux's single-environment-value limit.
The first is now an explicit verified installation prerequisite rather than
an unsupported YAML-only guarantee.

The final review corrected the SHA claim: prompts cannot guarantee a model
writes a particular label. The helper records prepared/verified commits in the
trusted run summary. The stock Action links its comment to that run. Model
wording is requested; the helper's commit record is authoritative.

**Verdict:** locally validated and ready for review. Live acceptance remains
pending a target repository and authorization for its settings, credentials,
activation, and paid test run.
