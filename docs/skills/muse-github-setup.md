# muse-github-setup

Install Muse Spark PR feedback through the upstream OpenCode GitHub Action.
The optional manual workflow creates a fresh fix branch and PR for human review.
Automatic reviews are triggered by eligible organization-member PR events,
not by comments. Neither workflow approves or merges PRs.

**Triggers on:** "install Muse reviews", "set up Muse in GitHub Actions", and
"add the Muse OpenCode action to this repo".
**Arguments:** none; name the repository and whether manual fix PRs are wanted
in ordinary language.

The defaults are `model_api/muse-spark-1.3-contributor` and a distinct repository
secret named `META_MUSE_CI_API_KEY`. Contributor-tier content may be used for
training. The skill discloses that choice before repository activation and
honors an existing owner decision. A compatible private `repo-secrets` skill
can provision the key; other users receive a secure manual setup path followed
by a secret-name check. No private plugin is required.

The template enforces current membership checks, same-repository PRs,
restricted tools, trusted configuration, disabled session sharing, and runtime
limits. The installer also requires GitHub execution policies for the exact
workflow paths and approved organization team. It requires verified restrictions
on who can modify workflow files before
those PR workflows execute. CODEOWNERS alone does not supply that boundary.
Reviews inspect a bounded diff
with no model tools. Fixes can read/edit regular files but do not execute project
code while credentials are present. Read the
[security limits](../../plugins/muse-github/skills/muse-github-setup/references/security.md)
before enabling either workflow. In particular, the upstream Action is pinned
but installs a moving CLI, and a stale comment cannot be retracted atomically.

## Install the skill

| Mode | Use |
|---|---|
| Plugin | Add `/plugin marketplace add smorinlabs/smorinlabs-harness`, then `/plugin install muse-github@smorinlabs-harness` |
| Development | Clone `https://github.com/smorinlabs/smorinlabs-harness`, then run `ln -s "$(pwd)/smorinlabs-harness/plugins/muse-github/skills/muse-github-setup" ~/.claude/skills/muse-github-setup` from its parent directory |
| Direct copy | Copy `plugins/muse-github/skills/muse-github-setup/` from the clone into `~/.claude/skills/muse-github-setup/` |

For Codex, use the same development/copy mode with `~/.agents/skills` instead
of `~/.claude/skills`, or register this repository as the local
`smorinlabs-harness` marketplace as described in the root README. Installing the
skill does not install or activate a workflow in any repository.

## Example

> Install Muse reviews in this organization's repository, with manual fix PRs.

The skill inspects the repository and authorization, prepares both workflows in
a worktree, preserves existing configuration, resolves credentials and execution
protections, and performs only the authorized activation and acceptance steps.
It distinguishes authored files, local validation, secret presence, and live
review/fix results. It never assumes a successful local check proves a live run.

## Provenance

Adapted on 2026-09-19 from Meta Platforms, Inc. and affiliates'
[MIT-licensed cookbook](https://github.com/meta-models/meta-model-cookbook/tree/c5a9882b4c7f3900e9c93122249d37317c8abff4/03_use_cases/11_github_repo_agent),
with a copied license notice and newly authored restrictive profiles/helpers.
The [source record](../../plugins/muse-github/skills/muse-github-setup/references/provenance.md)
lists exact revisions and the differences from the recipe.
