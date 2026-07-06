# Per-trigger prompt templates

Each trigger type asks a differently shaped question and captures different information. The shaping sub-agent selects the matching template, fills it with the harvested constraints and light-search framing, and writes the result as the `.prompt.md` handed to `/deep-research`.

Universal rules across all templates:

- **Ground in constraints.** Always state the stack. Include target platform only when it's specific, license only when declared, security posture only when the domain makes it relevant. Recommendations that ignore real constraints are wasted threads; constraints that don't bind are noise that skews results.
- **Recommend, don't just list.** Every template ends by asking for a recommendation with reasoning. Research that dumps options without resolving is research that didn't finish. When the honest answer is conditional, say so explicitly: "A is best under conditions X; B under conditions Y; C is high-quality and overlaps in Z." A conditional recommendation is a valid resolution — a forced single winner that hides real tradeoffs is not.
- **Currency check.** Every template asks: is what you're finding *current*? Best practices go stale, errors trace to recent changes, algorithms get superseded. For libraries this is formalized as the recent-bugs-vs-plan item below.
- **State confidence.** Findings should carry an explicit confidence level and its basis ("cross-checked against source code" vs. "single blog post, unverified"). Confidence should be highest — and must be stated — at the terminal leaf, since that's what gets built against.
- **Surface conflicts.** When sources disagree, state the disagreement; don't silently pick one. In autonomous mode, irreconcilable conflict or low confidence at the leaf is a defer trigger — don't build on shaky research unattended.
- **Stay on the question.** Include a scope line restating the exact question so the research doesn't wander.
- **State assumptions.** Note what the research assumed about the use case, so a future reader knows whether the leaf transfers to their situation.

## 1. Best-practice / domain-pattern — shaped as a survey

For: entering a broad feature where the problem class has established wisdom.

Prompt shape:
- What class of problem is this? (e.g., billing cancellations with immutable transactions; CLI interface design)
- What are the established conventions and canonical patterns for this problem class?
- What are the known pitfalls and anti-patterns — the mistakes teams commonly make?
- What has changed recently — is yesterday's best practice today's anti-pattern anywhere?
- Given constraints {stack, ...}, which conventions apply directly and which need adaptation?
- Recommend the set of principles to design against, with reasoning.

Capture: conventions, canonical patterns, anti-patterns, applicability to our constraints.

## 2. Architecture / library selection — shaped as problem-to-solution matching (two levels)

For: choosing among libraries or structural approaches.

Prompt shape — level one, the problem:
- What *type* of problem are we solving? State it precisely.
- Does a library/tool solve this exact problem, or does nothing fit directly (requiring composition of pieces or a build-vs-buy call)?

Level two, the candidates (when libraries exist):
- What are the candidate options? For each, capture the standard set:
  - **Fit precision** — solves the exact problem vs. general-but-close. An obscure library that fits exactly can beat a popular one that almost fits.
  - **Popularity** — what's most used for this problem set. A weighted signal, never decisive on its own.
  - **Maintenance status** — actively maintained vs. deprecated/sunset. Choosing a dying library is a slow-motion mistake; surface it loudly.
  - **Recent-bugs-vs-plan** — is there anything recent (regression, breaking change, open critical bug) that changes *our specific plan right now*? This is what a static popularity/maintenance read misses.
  - **Integration cost** — what adopting it requires given our stack; a perfect library that forces a rewrite isn't perfect.
  - **License / security** — only when those constraints were declared or the domain makes them relevant. A license mismatch is a hard gate, not a preference.
- Recommend, with reasoning and a ranked runner-up. Conditional recommendations welcome.

## 3. Algorithm / approach selection — shaped as bidirectional technique comparison

For: choosing an algorithm or technical approach rather than a packaged library.

Prompt shape:
- What are we optimizing for? (speed, memory, simplicity, accuracy, ...)
- **Bottom-up:** how has this *exact* problem been solved? There may or may not be direct prior art — say which.
- **Top-down:** how have *similar or analogous* problems been solved? When the exact case is unstudied, borrow patterns from the nearest studied ones.
- For each candidate approach: tradeoffs against our optimization goals and constraints; is it the current best-known technique or has it been superseded?
- Recommend, with reasoning and a ranked runner-up. Conditional recommendations welcome.

## 4. Implementation deep-dive — shaped as use-case mastery

For: an already-chosen library or technique that needs to be understood for the exact use case.

Prompt shape:
- The chosen thing and its pinned version.
- Our exact use case, stated concretely.
- How does it work *for this use case* — the relevant API surface, the idiomatic usage, configuration that matters?
- Gotchas, edge cases, and version-specific behavior relevant to us.
- A minimal example for our use case (to be validated — see artifacts.md).
- Anything recent (bugs, changes, deprecations in this version range) that affects our plan?

Capture: the terminal leaf content — API specifics, validated example, gotchas, version pins.

## 5. Error-driven — shaped as diagnosis

For: repeated failures with an unfamiliar API or pattern after ordinary searches failed.

Prompt shape:
- The observed symptoms: exact errors, stack traces, versions in play.
- What we've already tried and what happened.
- What we were attempting (the intent behind the failing code).
- What is the likely failure signature → resolution path? Is this a known issue, a version mismatch, a misuse of the API, or a recent regression?
- What information gets us past these errors — and what should we verify before retrying?

Capture: the diagnosis, the resolution path, and (if it generalizes) a leaf documenting the gotcha so it is never re-hit.

Note this template starts from *observed symptoms*, not a blank field — include the concrete evidence, not a paraphrase of it.
