# Project policy and a named development tool

This example adapts the owner's preferred rewrite from a research session for
the planned `rs-launch-blueprint` Rust project template. PR review clarified
the recommendation's rationale, stable option ID, and alternative's status.
Package versions, declared licences, and project constraints below are
attributed to that session's research records;
this is neither a fresh registry check nor a general legal conclusion.

The form restores the project, proposed command, alternative tool, and policy
scope before asking for a choice. The recommendation names its action before
its ID. The closing preserves each option's different effect. The excerpt is
a complete ordinary-text brief, not an instruction to answer Q4 now.

```text
`rs-launch-blueprint`, the planned Rust project template, needs a setup command for contributors to install development tools. R42, the installation research record, proposes an `install-tool` recipe in `Justfile`, the planned file of development commands.

The proposed recipe uses `cargo install --locked <name>@<version>`. This is the Rust package manager's command for compiling and installing a tool from source. `<name>` and `<version>` identify the selected tool and its version.

The alternative is `cargo-binstall` 1.23.0, an existing installer that can download ready-to-run development tools. Its own declared licence is `GPL-3.0-only`. In this proposal, the installer runs separately on the contributor's machine and is never linked into the shipped application or library.

The project fixes its repository licence as `MIT OR Apache-2.0`. Its rule says "candidate crates must be compatible". Crates are Rust packages. R42 leaves the treatment of separately run development tools to your decision.

**Q4. Should `rs-launch-blueprint` apply its `MIT OR Apache-2.0` licence-compatibility check to standalone development tools such as `cargo-binstall`?**

**I recommend applying the check and keeping the `cargo install` proposal (Q4.A).** This retains R42's conservative interpretation while setup performance remains unmeasured. The research also identifies `cargo-quickinstall` 0.3.53, another prebuilt-tool installer, as a candidate to investigate if compiling tools proves too slow.

- **Q4.A (Recommended) Apply the compatibility check to standalone development tools.** Keep `cargo-binstall` excluded under R42's recorded interpretation and retain the proposed `cargo install` recipe. Future tools in this class must undergo the same check.
- **Q4.B Exempt standalone development tools from this compatibility check.** Record that exemption and revise R42 to recommend `cargo-binstall`. The exemption would also apply to future tools that run separately and are never linked into the shipped application or library.
- **Q4.C Defer the policy decision.** Keep the proposed `cargo install` recipe and leave the policy question open.

**Evidence and limits:** R42 records registry checks from 10 September 2026: `cargo-binstall` declares `GPL-3.0-only`; `cargo-quickinstall` declares `MIT OR Apache-2.0`. Those checks establish declared licences. They do not establish installation speed. Setup time and `cargo-quickinstall`'s suitability for the eventual tool list remain unverified.

**Reply with A, B, or C.** Choosing A or B records the policy and updates the research recommendation accordingly. Choosing C leaves the policy unanswered. The template's implementation has not started; these actions update the research records.
```

Do not copy the facts, policy interpretation, or approval stage into another
case. Obtain its own sources. This example illustrates writing; reproducing it
is not evidence that the skill handles unfamiliar situations. The evaluation
suite uses different tools and policies to test transfer.
