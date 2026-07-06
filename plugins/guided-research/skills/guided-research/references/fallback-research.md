# Fallback research procedure

Use only when the built-in `/deep-research` skill is unavailable (older Claude Code version, bundled skills disabled, or a non-Claude-Code harness). The point of the fallback is that research still happens — silently downgrading to two web searches at a moment the skill decided was high-value defeats its purpose.

Run the research in an **isolated sub-agent** (Task tool / equivalent) so the reading volume never touches the main context. The sub-agent receives the shaped `.prompt.md` and follows this procedure:

## Procedure

1. **Survey primary sources widely** — official documentation, actual source code, issue trackers, changelogs, benchmarks. Not just the top blog results; those are tertiary.
2. **Weight by source quality:** primary (official docs, source, changelogs) > secondary (maintainer posts, established references) > tertiary (blogs, SEO content). A claim that only exists in tertiary sources is low-confidence by definition.
3. **Cross-check every load-bearing claim against ≥2 independent sources.** When sources disagree, record the disagreement — don't silently pick a side.
4. **For libraries, read the actual API/source for the relevant surface**, not just prose about it. Fill the template's capture set (fit precision, popularity, maintenance, recent-bugs-vs-plan, integration cost, and license/security when they bind).
5. **Run the multi-round narrowing:** each pass more specific than the last, re-applying the stopping rule (name the choice; terminal leaf resolves the use case) after every pass. Respect the depth ceiling in autonomous mode. Independent options within a round may fan out as parallel sub-agents.
6. **Synthesize** into the funnel output and, at the terminus, the leaf — with explicit confidence and basis, per `artifacts.md`. Validate the minimal example by running it where feasible.
7. **Write everything to disk and return only a thin pointer** — leaf path plus a one-line outcome. The return value lands in the main context verbatim, so a verbose return defeats the isolation; the file system is the channel, the return is a receipt.
