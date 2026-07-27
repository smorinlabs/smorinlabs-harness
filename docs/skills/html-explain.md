# html-explain

Builds a **read-only explainer page** as a single self-contained HTML file —
a rich explanation of something already settled, where diagrams, annotated
figures, charts, build-up sequences, and small interactive widgets do the
work prose cannot. "Read-only" governs the *contract* (no decision
round-trip, nothing to export back), not the medium: anything HTML can
display is in scope if it makes the subject land.

The distinguishing move is **budgeting the page by difficulty before
drafting**. After outlining the material, the skill rates each section by how
hard it is *intrinsically* — for a reader who was never in the conversation,
assuming it is written well — names what *kind* of hard it is, and allocates
the page so the hardest one or two sections take the clear majority of the
words and nearly all of the figures. Uniform depth, where every section gets
the same treatment regardless of difficulty, is the failure this prevents.

**Triggers on:** wanting an explanation as a shareable *page* rather than
inline chat — "explain the design we just landed", "write up what the tests
showed", "make an explainer for this spec", "deep dive on X as a page",
explainer, walkthrough page, "explain this visually" · **Not for:**
explanations that belong inline in chat (that's the `explain` skill), pages
whose job is to collect a decision (`html-codesign`), or open questions
worked through conversationally (`question-walkthrough`) · **Arguments:**
none — controlled in natural language.

## The gate — it always fires

The skill reads recent context, classifies it, and **confirms the target
before generating** — including when it was invoked explicitly and including
when an argument named the topic. An argument shortens the question from
"what are we doing?" to "confirming this reading"; it never removes it.
Rendering a whole page about the wrong artifact is the expensive, silent
mistake one question prevents.

The confirmation proposes concrete targets mined from context, always
including at least one **adjacent** area — something the material implies
but never covered, since the gap a reader feels is often not the thing they
named:

```
Recent context looks settled rather than open — the retry work landed and
the tests are green. Candidates for the explainer:

  · What the retry refactor actually changed, and why the old shape broke
  · Deep dive: the backoff design decided Tuesday — the mechanism, and
    what it costs under load
  · What the load-test results showed, read against what we expected
  · Adjacent — how this interacts with the circuit breaker. Not discussed,
    but the design implies a question there.

What should the page explain?
```

If recent context is mostly *unanswered* questions, the skill says so and
offers `html-codesign` instead.

## The authoring loop

```
1  triage & confirm the target        ← the gate above
2  outline — read the REAL artifacts (diff, spec, test output, code)
3  difficulty map — rate intrinsic difficulty, budget the page,
     and let the "kind of hard" column select the principles
4  draft, spending that budget
5  critique — clarity defects; hunt the curse of knowledge by name
6  enrich — the medium pass: where is prose working too hard?
7  judge — every figure must trace to a PRE-REGISTERED difficulty
8  whole-page review — arc, budget, density, first-screen test
9  resolve the theme
10 render, then actually look at it
11 deliver
```

Step 3 must precede the draft for two reasons. Critiquing a draft can only
find difficulty *introduced by writing badly*; it cannot find difficulty that
belongs to the subject. And a pre-registered difficulty list means step 7's
enrichments cannot be justified after the fact — a diagram can't be added and
then explained away as "that passage was hard."

## Enrichment is earned, never uniform

Every figure and widget faces a removal test: *take it out — is the passage
meaningfully harder?* If no, it doesn't ship. Interactive controls face a
stricter one: *does **manipulating** it change what the reader understands?*
If the insight arrives from the default state, it's a figure, not a widget.

The skill works up a ladder and stops at the lowest rung that fixes the
specific difficulty — rewriting the prose (free) before signaling before a
real snippet before a table before a static figure before a build-up
sequence before a manipulable model. A good explainer is mostly the cheap
rungs with a few well-chosen figures.

## The canon — advisory, indexed by symptom

Clarity principles ship as **aids, not rules**; the goal is communication,
not compliance. They're indexed by the symptom they fix so they're reachable
when a draft is failing in a particular way, rather than recited up front.

| Layer | Sources | Answers |
|---|---|---|
| Cognitive load | Mayer, Sweller, Shneiderman | How much may be on screen at once |
| Structure | Minto, Heath, Pinker, Feynman, McCloud, Rosling | What order ideas arrive in |
| Encoding | Bertin, Cleveland & McGill, Tufte, Neurath, Ware, Corum | Whether a mark reads as what it claims |
| Interactive form | Victor, Ciechanowski, Case, Red Blob, Distill, Bostock, Lupi | Calibration targets, not rules |

## Closing the delivery

Both page skills in this plugin end the same way, via the shared
`references/delivery-close.md` at the plugin root — the editable source of
truth. Each skill reads its own vendored copy at
`references/_shared/delivery-close.md`, generated from that source by the
pinned harness-kit generator (kept in sync by `gen-check`) — added on top of
each skill's own delivery step, not in place of it.

**The full absolute path, on its own line, every time.** A relative path is
only meaningful from a working directory the reader cannot see, and the
person opening the file is routinely not in the shell that made it. If the
file landed somewhere temporary, the close-out says so plainly — scratch
paths get reaped, which is what makes the save offer below matter.

**Then it asks what you'd like to do next**, as a prose list rather than a
dialog (the path has to stay visible, and prose sharing a turn with
AskUserQuestion may never render). Every offer is strictly conditional:

| Offer | Only when |
|---|---|
| Open it in the browser | the session can actually reach one — never web-hosted, remote, headless, or a display-less sandbox, where the command reports success while nothing opens. In doubt → don't offer |
| Copy the path to the clipboard | same gate — the session runs on your own machine | on a remote session a clipboard write **reports success** into a clipboard you can't reach, a sharper failure than a browser-open that visibly does nothing |
| Add it to `shelf` | that skill is installed. If it isn't, `shelf` is not mentioned at all — not even as a suggestion to install it |
| Where to save it | the file sits somewhere temporary, **or anywhere the agent chose rather than you**. Read from context, never a fixed ranking — see below. Never moved silently |

### The save recommendation is read, not ranked

A fixed order gets this wrong in both directions: it files a design doc that
obviously belongs beside its spec into a general library, and it proposes a
permanent home for a page nobody will open again. So the question is *what is
this page, and where do things like it already live?* — answered with one
recommendation and its reason, plus the runner-up named in a clause.

| The page looks like… | Recommendation |
|---|---|
| something this session has already been saving somewhere | that same place — repeating an established destination beats introducing one |
| a document this repo already has a home for | that home — `docs/`, `docs/decisions/` or `adr/` for a decision record, beside the spec it explains. Convention beats invention |
| durable and repo-bound, but with no existing home | the location fitting the repo's shape, flagged as a *new* home so it's cheap to redirect |
| standalone — research, a comparison, a briefing, or anything with no clean place to live | `shelf`, **if that skill is installed**; if not, say plainly there's no obvious home and ask |
| ephemeral — a throwaway, or a page settling a decision being settled right now | **not saving it.** "This doesn't look like a keeper" is a real recommendation and spares a filing decision |

Those are examples, not a taxonomy — other clear homes exist (a notes vault, a
docs-site content tree, a path the project's own CLAUDE.md names) and the
context in front of you decides.

## How it composes with dataviz

Quantitative charts defer to the `dataviz` skill when it is present — it
carries a runnable colorblind-and-contrast palette validator this skill has
no equivalent for. The boundary is drawn by *what a mark means*, not by what
the artifact is called:

> If a mark's position, length, or area stands for **a number the reader must
> compare** → `dataviz`. If it stands for a **relationship, sequence,
> structure, or state** → this skill.

**The fallback is load-bearing, not decorative.** `dataviz` is compiled into
the Claude Code binary — it has no filesystem presence and does not exist on
Codex at all. Since this plugin ships portable across both tools, the skill
carries a complete standalone encoding reference (including the Okabe–Ito
CVD-safe palette, which needs no validator) for the surfaces where the
delegate is simply absent.

## How it composes with use-html-theme

This skill owns structure, content, and enrichment; the page's *look* comes
from the same cascade `html-codesign` uses. **Birchline ships an explainer
overlay** (`themes/birchline/explain.md`) — its warm-editorial register suits
long-form explanation better than anything else in the plugin. Technical-
minimal and High-contrast-dark derive from their `tokens.md`, which the
cascade handles by design: an explainer's components vary with its subject,
so beyond Birchline there is not yet a fixed vocabulary worth hand-tuning.

## How it relates to html-codesign

The two share one preflight whose editable source is
`references/context-triage.md` at the plugin root, read by each skill as its
vendored `references/_shared/context-triage.md` copy, and sit one step apart:

|  | Open questions | Settled material |
|---|---|---|
| **in chat** | `question-walkthrough` | `explain` |
| **as a page** | `html-codesign` | **`html-explain`** |

They genuinely overlap on one case, and both skills name it rather than
pretend the boundary is clean: **a recently-asked question can go either
way.** Codesign *poses* it for decision, with a recommendation.
`html-explain` *deep-dives* it — what it turns on, what each branch costs —
without asking for a pick. When a request could mean either, both offer both.

## Install

| Mode | When | How |
|---|---|---|
| Plugin (recommended) | Just use it | `/plugin install use-html-theme@smorinlabs-harness` (ships all three skills) |
| Dev symlink | Tweak/iterate | `git clone https://github.com/smorinlabs/smorinlabs-harness` then `ln -s "$(pwd)/smorinlabs-harness/plugins/use-html-theme/skills/html-explain" ~/.claude/skills/html-explain` |
| Direct copy | No marketplace access | copy just `skills/html-explain/` — its shared references travel with it as vendored copies at `references/_shared/`. The one thing that doesn't survive a lone copy: sibling-skill theme paths (`../use-html-theme/...`) |

**Codex:** register the marketplace in `~/.codex/config.toml`. Pure skill —
behavior is identical on Codex and Claude Code, except that `dataviz` is
unavailable there and the built-in encoding fallback takes over.
