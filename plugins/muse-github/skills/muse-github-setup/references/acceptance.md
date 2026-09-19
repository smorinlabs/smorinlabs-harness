# Installation and acceptance

## Prepare and activate

1. Verify the exact repository and scope. Work in an isolated worktree based on
   the current default branch. Read existing configuration before applying the
   installer. `scripts/install.py WORKTREE --organization OWNER [--with-fixes]`
   prints the local plan; append `--apply` to write it. `WORKTREE` and `OWNER`
   come from repository discovery. Resolve the script from the installed skill.
2. Inspect every new or changed file. Run `actionlint` on the rendered workflows.
   Preserve existing project instructions, OpenCode settings, CODEOWNERS entries,
   and unrelated changes. Add human ownership for `.github/workflows/opencode-*.yml`,
   `.github/scripts/muse_ci.py`, `.opencode/muse-ci/`, `opencode.json`, and the
   security section of `AGENTS.md`. CODEOWNERS alone is not enforcement; confirm
   branch rules require those reviews and protect the default branch from the bot.
   Read back repository collaborator roles and workflow-path push restrictions.
   Require the write boundary in [security](security.md): all workflow writers
   are trusted organization members, or server-enforced file-path restrictions
   block outside writers with bypass limited to the approved member team.
   Inspect pending PRs for earlier workflow changes. Do not rely on merge-time
   review to stop a modified workflow running from a PR branch.
3. Configure active GitHub workflow execution policies for
   `.github/workflows/opencode-pr-review.yml` with `pull_request`, and when used,
   `.github/workflows/opencode-fix-pr.yml` with `workflow_dispatch`. Select the
   owner's approved organization team. Inspect the resulting policy with
   [GitHub's Actions policies API](https://docs.github.com/en/rest/actions/policies)
   or **Settings > Actions > Policies**. Exact API payloads must follow the
   current schema, not guessed identifiers. Verify scope, enforcement status,
   team identity, event restrictions, and inherited policies. Record the policy
   IDs and the read-back evidence. Do not enable the workflow on an unsupported
   repository plan or substitute broad repository write roles for membership.
4. Install the distinct Meta key and resolve private-membership read access as
   described in [secrets](secrets.md). Read back secret names. Never read values.
5. Land configuration on the protected default branch through the repository's
   normal human review process when authorized. The setup PR's base does not yet
   contain the trusted helper, so that PR is not a valid end-to-end test. Keep
   `MUSE_CI_ENABLED` unset during this bootstrap. Before activating, compare the
   installed upstream runtime with [the inspected source](provenance.md), run
   available credential-free configuration checks, and preserve the result.
6. With activation and paid testing authorized, set the repository variable
   `MUSE_CI_ENABLED` to `true`. Open a small, eligible same-repository PR. Inspect
   the actual run, reviewed SHA, and feedback comment. Run the manual fix workflow
   only when it is in scope. Do not merge its generated PR.

The manual workflow needs GitHub's setting permitting Actions to create pull
requests. Request that repository setting only when necessary and authorized.
GitHub's current `GITHUB_TOKEN` behavior can put workflows from bot-created PRs
into an approval-required state. Verify the actual state and provide the
maintainer's specific approval step when needed. Do not promise all CI starts
automatically or add a broad App token solely to avoid that approval.
Source: [workflows triggered by workflows](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow#triggering-a-workflow-from-a-workflow).

## Evidence to collect

| Scenario | Expected evidence |
|---|---|
| Eligible member opens/updates a small PR | Successful review run and feedback comment linked to the run summary recording the exact input SHA; no code changes |
| Fork PR, bot, or draft | Model step does not run and incurs no model call |
| Outside collaborator with repository write | Platform execution policy blocks the workflow; repository role alone does not qualify |
| Outside writer changes this workflow, then a member pushes | Server-enforced path restriction prevents the workflow edit; without that restriction or a verified member-only writer model, activation remains blocked |
| Rerun by someone outside the approved team | Platform blocks it or the authorization check fails before model credentials are used |
| Private membership cannot be verified | Authorization fails; no model call; identifies missing member-read access |
| Missing Meta secret | Installation remains incomplete; no repeated paid retries |
| Rapid PR update | Old run is cancelled or fails the final stale-head check; its run summary records the old input SHA even if the model omitted it from its comment |
| Malicious PR OpenCode plugin/config | Project discovery disabled and review has no model tools; configuration comes from the protected base |
| Member manually requests a fix | Fresh runner-created branch, ordinary-file diff, and new PR for human review; no approval/merge |
| CI on generated fix PR | Actual check state recorded; maintainer approves pending workflows if GitHub requires it |

Use offline fixtures for unsafe negative cases when possible. Never recruit an
outside collaborator, grant access, or expose a real secret just to exercise a
negative test. Live GitHub policy behavior remains a separate acceptance check.
Bound paid testing to the authorized runs; a failed run is evidence to diagnose,
not permission to loop indefinitely.

## Status vocabulary

- **Authored:** files and instructions exist in a worktree.
- **Locally validated:** deterministic helper tests, workflow lint, and package checks passed.
- **Installed:** reviewed files landed and prerequisites/secret names were read back.
- **Live review verified:** the actual authorized run produced feedback linked to its recorded input SHA.
- **Live fix verified:** the actual manual run created the intended branch and PR.

Do not collapse those states into "working". Secret presence cannot establish
Meta authentication. Static permissions cannot establish the moving runtime's
behavior. Document failures and skipped live checks explicitly.
