---
name: muse-github-setup
description: "Install or update Muse Spark PR reviews with the OpenCode GitHub Action, including optional manually requested fix PRs. Use for 'install Muse reviews', 'set up Muse in GitHub Actions', or 'add the Muse OpenCode action to this repo'. Prepares templates, checks member-only execution protections, provisions or hands off the named CI secret, and verifies the authorized installation. Not for generic OpenCode setup, running a local review, operating an iterative coding loop, or unrelated CI repairs."
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, AskUserQuestion, WebFetch, WebSearch
---

# muse-github-setup

Install organization-member PR feedback and optional manual fix PRs using the upstream OpenCode Action with Meta Muse Spark.

## Workflow

1. **Resolve the request.** Use the named repository or discover it with an
   available `repo-finder` skill. Establish the actual owner/name, visibility,
   default branch, local checkout, and existing authorization. Ask only for a
   missing owner choice. Default to automatic PR feedback; include the manual
   new-PR workflow when requested. A request to review a plan does not authorize
   installation. A request to install does not authorize merge or paid test runs.

2. **Check prerequisites before editing.** Read
   [security and compatibility](references/security.md). Inspect existing
   workflows, OpenCode JSON/JSONC configuration, `AGENTS.md`, `.opencode/`,
   CODEOWNERS, branch rules, and execution policies. The templates require an
   organization-owned GitHub.com repository and GitHub-hosted Ubuntu runners.
   Check the organization's approved team for execution policies. Do not treat
   repository write access or `author_association` as proof of current membership.
   Private memberships need a separately available GitHub organization
   Members-read credential. Identify that prerequisite before enabling anything.
   Inspect who can change workflow files on PR branches. If outside
   collaborators can write, require server-enforced file-path push restrictions
   with member-only bypass before activation. CODEOWNERS does not prevent a
   changed PR workflow from running before merge. Otherwise verify that all
   workflow writers are trusted organization members. Unresolved write access
   is an activation blocker, not an assumed safe default.

3. **Set the model and credential contract.** These templates use
   `model_api/muse-spark-1.3-contributor` at `https://api.meta.ai/v1` and the
   repository Actions secret `META_MUSE_CI_API_KEY`. The provider reads
   `{env:META_MUSE_CI_API_KEY}`. Use a distinct Meta key for each target repository.
   The contributor tier permits Meta to use submitted content for training;
   disclose that when choosing it for a repository. Honor an existing owner
   decision rather than asking again. A restriction against sharing private
   code with that tier requires a new model decision, never a silent fallback.

4. **Prepare the files in an isolated worktree.** Resolve this skill directory
   through its installed path. Run its `scripts/install.py` with the target
   worktree and `--organization` set to the actual owner. Add `--with-fixes` for
   the requested manual workflow. The default prints a plan; `--apply` writes
   local files. It never installs secrets or enables workflows. Review its diff.
   Existing project instructions are preserved and the security section is
   appended. Existing OpenCode settings are preserved; conflicting providers,
   JSONC files, symlinks, or changed managed files require a reviewed merge.
   Do not overwrite those files to force the helper to pass. Adapt project
   guidance in `AGENTS.md` without removing the security constraints. Preserve
   the copied upstream NOTICE.

5. **Provision only the intended secrets.** Read
   [credential provisioning](references/secrets.md). If an installed private
   `repo-secrets` skill supports `--app muse-ci`, delegate just that application
   with the exact repository and `--workflow-root` pointing to this worktree.
   Otherwise perform the documented secure handoff. Never require a private
   repository, invent a 1Password reference, request a secret in chat, or copy
   another repository's key. Metadata presence and successful authentication
   are separate checks. Membership credentials are not Meta credentials.

6. **Review the activation prerequisites.** Use
   [installation and acceptance](references/acceptance.md). Protect the default
   branch and require human review for both workflows, the helper,
   `.opencode/muse-ci/`, root OpenCode config, and the security instructions.
   Scope GitHub workflow execution policies to the exact two workflow paths,
   approved organization team, and their respective events. Confirm active
   enforcement with the API/UI. Unavailable protections are a prerequisite
   failure, not permission to relax the design. Keep `MUSE_CI_ENABLED` unset
   until these checks and credential installation succeed. Do not change
   unrelated Actions policies or install a privileged GitHub App automatically.

7. **Validate within the authorized scope.** Check rendered YAML with
   `actionlint`, run `tests/test_muse_github.py` when developing from the source checkout,
   and inspect the complete diff. Commit or open a PR when authorized; merge
   and activation follow the user's existing scope. With live testing
   authorized, enable the repository variable and run the acceptance matrix.
   Stop after one successful review and, when included, one successful manual
   fix PR; unexpected paid failures require diagnosis before another attempt.
   Never merge or approve the generated fix PR. Report file creation, secret
   presence, policy enforcement, actual review comment, and actual fix PR as
   distinct statuses. A local check cannot establish a live installation.

## Boundaries

- Reviews run automatically on eligible PR events. They are not comment-triggered.
  Their output is feedback, not GitHub approval. The initial profile has no
  model tools and reviews a bounded, immutable diff; it does not run tests.
- Fixes use `workflow_dispatch` from the default branch. OpenCode creates a
  fresh branch and PR. `/oc` commands, issue triage, automatic bugfix labels,
  stale cleanup, approval, and merge are outside these templates.
- The direct upstream Action is SHA-pinned, but its installer, selected CLI,
  and transitive cache action move. Do not describe the runtime as fully pinned.
  Compatibility must be rechecked when those dependencies change.
- Session sharing is disabled. Model and GitHub credentials are restricted
  to the steps that need them. Project code is never executed in the
  credential-bearing agent step. The moving runtime remains a trusted dependency.

## References

- [Security](references/security.md): enforcement, permissions, and upstream limits.
- [Secrets](references/secrets.md): optional private provisioning and public fallback.
- [Acceptance](references/acceptance.md): installation sequence and live evidence.
- [Provenance](references/provenance.md): cookbook and Action source snapshots.
