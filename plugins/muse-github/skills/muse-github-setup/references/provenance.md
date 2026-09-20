# Source snapshots

Researched on 2026-09-19. These links establish the inspected implementation,
not future runtime behavior.

| Source | Revision and use |
|---|---|
| [Meta cookbook recipe](https://github.com/meta-models/meta-model-cookbook/tree/c5a9882b4c7f3900e9c93122249d37317c8abff4/03_use_cases/11_github_repo_agent) | Meta Platforms, Inc. and affiliates; MIT; `c5a9882b4c7f3900e9c93122249d37317c8abff4`; provider and workflow starting point |
| [OpenCode Action](https://github.com/anomalyco/opencode/blob/a97622c801f4ca571530ddc51076af659a9c32cd/github/action.yml) | `a97622c801f4ca571530ddc51076af659a9c32cd`, release `v1.18.31`; direct action invocation, installer, cache and inputs |
| [Actual GitHub runner](https://github.com/anomalyco/opencode/blob/a97622c801f4ca571530ddc51076af659a9c32cd/packages/opencode/src/cli/cmd/github.handler.ts) | PR branch fetch/checkout, default-agent behavior, manual fresh-branch/PR path, write checks |
| [Config loader](https://github.com/anomalyco/opencode/blob/a97622c801f4ca571530ddc51076af659a9c32cd/packages/opencode/src/config/config.ts) | Project discovery and plugin loading; inline configuration alone does not suppress project plugins |
| [Instruction loader](https://github.com/anomalyco/opencode/blob/a97622c801f4ca571530ddc51076af659a9c32cd/packages/opencode/src/session/instruction.ts) | Disable project instructions during CI; supply trusted instructions explicitly |
| [Meta tier policy](https://dev.meta.ai/docs/pricing-rate-limits) | Contributor model pricing and submitted-content use; verify again when installing |

The cookbook's inspected tree did not include the `.opencode/` profiles its
walkthrough described. The restricted profiles and helpers here are locally
maintained additions. This is an adaptation of Meta's recipe, not a Meta-issued
Action or an unmodified cookbook copy. It runs Muse Spark through OpenCode;
it does not run the Muse Code CLI.

The copied `.opencode/muse-ci/NOTICE` retains the cookbook's MIT notice.
The upstream OpenCode Action is referenced, not copied. The root provider's
secret name and model are deliberately changed to the project-specific CI key
and contributor tier. Global root instructions and existing OpenCode settings
are merged with care, while CI uses isolated profiles from a trusted revision.
