# Security and compatibility

The templates implement a conservative starting policy. An installation must
verify GitHub enforcement and the installed OpenCode runtime before claiming
the workflow is ready. Configuration permissions are controls in a trusted
agent runtime, not an operating-system sandbox.

## Who can run

| Surface | Required policy |
|---|---|
| Automatic review | Open, non-draft, same-repository PR into the default branch; PR author, original actor, and rerun actor are current human organization members with repository write access |
| Manual fix | `workflow_dispatch` on the default branch; original actor and rerun actor satisfy the same member and write checks |
| GitHub platform | Active workflow execution policies for the exact review and fix paths, allowing an approved organization team and only the corresponding event |
| Excluded initially | Fork PRs, bots, outside collaborators, comment triggers, personal-owner repositories, self-hosted runners |

The helper checks current membership with `GET /orgs/ORG/members/USER` and
repository permission separately. GitHub may hide private membership from the
repository token. Use an existing authorized credential with organization
Members read access as `MUSE_CI_GITHUB_MEMBERS_TOKEN`; otherwise membership checks
fail closed. That credential is exposed only to the trusted authorization step,
never to OpenCode. A lookup error does not become an eligible actor.

GitHub workflow execution protections are available for all public repositories
and private repositories on Team/Enterprise. Inspect the actual target plan and
policy. A YAML `if` can be changed in a PR, so it cannot serve as the primary
boundary against a repository collaborator. Platform policies apply before
workflow execution. Protect the configuration with branch rules and CODEOWNERS
as well. Those merge protections do not prevent PR-branch workflow changes
from running. An outside writer could remove the helper call in this same
workflow, then a later member push could satisfy the platform actor policy.
Protecting only the triggering actor does not close that case.

Before activation, verify either that all workflow writers are trusted human
organization members, or that an active server-enforced push ruleset blocks
changes to `.github/workflows/**/*` for everyone except the approved member
team. Do not grant a broad write-role bypass. Include the helper and CI profiles
in the protected paths as well. Inspect existing open PRs for earlier workflow
changes before enabling a newly added restriction. The installer must report
unverified access or unavailable enforcement as a blocker. It must not revoke
collaborator access or change an organization-wide rule without authorization.

Push rulesets are documented for private/internal repositories on supported
plans. Do not promise them for a public repository. A public repo with outside
writers needs an equivalent verified restriction or a revised architecture;
the current installer keeps these workflows disabled in that case. Likewise,
path-scoped policies do not stop a writer from introducing a different workflow
that reads repository secrets. This design trusts approved workflow writers;
it does not revoke their ordinary GitHub powers.

Source: [GitHub execution protections](https://docs.github.com/en/actions/how-tos/administer/control-workflow-execution).
The additional write boundary is described by
[GitHub push rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets#restrict-file-paths).

## Runtime controls

| Control | Review | Manual fix |
|---|---|---|
| Token | `contents: read`, `pull-requests: write` | `contents: write`, `pull-requests: write` |
| Model tools | All denied; supplied diff only | File read/edit only; protected configuration denied; credential-like tracked files block preparation |
| Base | Event's exact base/head commits | Dispatch's exact default-branch commit |
| Output | Feedback comment linked to a run summary recording the input SHA | New `opencode/dispatch-...` branch and PR |
| Job limit | 10 minutes; newer PR run cancels older | 15 minutes; one running fix per repository |

Both profiles disable sharing, snapshots, formatters, language servers, shell,
web tools, subagents, and external skills. Disabling shell alone would not
prevent a language server or formatter from executing project-controlled code.
The helper copies the trusted base profile and root instructions into a fresh
runner-temporary directory, disables project config discovery, and supplies
fresh XDG configuration/data/cache paths. Existing project plugins and custom
tools are not loaded. The workflows must remain on fresh GitHub-hosted runners;
this setup does not isolate a reused runner's home directory.

`default_agent` is explicit because the inspected GitHub runner omits the
Action's `agent` input when it sends the model prompt. The global permission
rules also apply to its default agent. The installer preserves root
`opencode.json` for normal discovery, but CI uses its separate trusted profile.

Review input is a complete textual diff limited to 60,000 bytes, not a
silently truncated diff. Credential-like changes are refused for human review.
The case-insensitive filename policy includes `.env*`, key/certificate stores,
`.npmrc`, `.pypirc`, `.netrc`, `.git-credentials`, `credentials`, `credentials.json`,
and conventional SSH private-key names. Binary changes and context outside the diff
need human inspection. The model cannot load PR instruction files as agent
configuration or read beyond the supplied diff. Changed instructions can appear
in that diff as untrusted data. It cannot execute a project plugin because it
has no tools and project discovery is disabled. GitHub's live PR title/comments still reach the model
through the stock Action; treat them as untrusted context, not code evidence.

The helper creates a local branch at the event SHA before OpenCode starts.
The inspected runner's later fetch updates remote refs, while checkout of the
existing local branch retains the original commit. Offline tests advance a
remote branch and exercise that exact sequence. The final check detects an
advanced PR and marks the run failed. It cannot retract a comment already
posted by the stock runner. The prompt requests the SHA in the comment, but
model compliance is not guaranteed. The trusted helper records the input and
final PR SHAs in the run summary, which the stock comment links to. That summary
is the authoritative commit record. Concurrency cancels older runs where
possible. Do not claim atomic current-head publication.

The fix profile edits regular project files. Preparation refuses symlinks,
submodules, and any tracked credential-like file before the model step. This
includes nonsecret example files with those names: the starting policy is
deliberately conservative. Before activation, inspect the target repository's
actual secret-file conventions and extend the helper's `sensitive()` predicate
for additional names. Filename rules cannot identify secrets embedded in
arbitrarily named source files; inspect that separately. Do not activate a
manual fix workflow with unreviewed secret paths. It starts from the trusted
default branch, disables hooks, formatters and language servers, and leaves
test execution to ordinary PR CI. Protected-path tool permissions are the
preventive control; the final diff check is diagnostic and runs after the stock
Action may already have pushed. A GitHub token with PR-write permission can do
more than post comments, so configuration and human branch protection remain
necessary. These profiles never intentionally approve or merge.

Git authentication uses `gh auth git-credential` with a step-scoped token.
Checkout does not persist credentials. Neither a token value nor a private
1Password reference is written into repository configuration.

## Dependency limits

The direct `anomalyco/opencode/github` action is pinned to
`a97622c801f4ca571530ddc51076af659a9c32cd`. At that revision it chooses the latest
CLI, runs the upstream installer, and uses `actions/cache@v4`. This is the
accepted direct-Action tradeoff. It does not pin the entire runtime. Refresh
source inspection and credential-free compatibility checks before activation
or updating templates. Do not replace it with a custom installer silently.
The credentials supplied to this composite Action are inherited by its version
lookup, cache, and installer steps as well as the final OpenCode command.
Trust in those upstream components is therefore part of the accepted boundary.
Isolating credentials from setup and pinning every nested dependency would
require an upstream capability or a separately approved wrapper/vendor design.

Source: [inspected Action](https://github.com/anomalyco/opencode/blob/a97622c801f4ca571530ddc51076af659a9c32cd/github/action.yml),
[GitHub runner](https://github.com/anomalyco/opencode/blob/a97622c801f4ca571530ddc51076af659a9c32cd/packages/opencode/src/cli/cmd/github.handler.ts),
[OpenCode permissions](https://opencode.ai/docs/permissions/).
