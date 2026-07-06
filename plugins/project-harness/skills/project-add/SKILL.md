---
name: project-add
description: Captures a project idea in at most four questions asked one at a time (the fourth is optional — open questions and notes), picks the next available P## from the local trunk (always max+1), and writes the idea stub from templates/project-idea.md plus the trunk row in a single atomic git commit. Refuses to scope or decompose — points at project-refine if depth is wanted.
when_to_use: When the user says "I had an idea", "capture this", "add a project for...", or any phrasing that signals a new project to register on the trunk.
arguments: [seed]
argument-hint: "[seed-title]"
allowed-tools: Read Edit Write Bash
---

# project-add

**Core principle:** capture is the cheapest part of project work and
the part most often skipped. The skill exists to make capture so
low-friction that there is no reason not to do it.

## Iron Law

> **NO MORE THAN FOUR QUESTIONS, WITH THE FOURTH OPTIONAL.**
> Friction kills idea capture. If the user wants depth, that is
> `project-refine`'s job. The fourth question is the open-questions/
> notes capture — the user can press enter to skip it entirely, and
> when skipped the resulting file omits both sections.
>
> No exceptions: not "just one clarifying question", not "I'll combine
> two questions into one phrasing", not "the user clearly wants depth
> already". Four is the cap; three is the floor (Q4 is skippable).
>
> Violating the letter of this rule is violating the spirit of it.

## When to use

- *"I had an idea — let's add it."*
- *"Capture: rate-limit the OpenAI client per provider."*
- *"Add an idea about config profiles."*
- *"New project: ..."*

## What it does

The skill follows the **one-question-at-a-time** convention from
`_conventions.md` §6 — ask one question, wait for the answer,
*re-evaluate*, then decide whether the next question is needed.
Never list multiple questions in a single message.

If invoked positionally with a seed (e.g.
`/project-add "Rate-limit OpenAI client"`), the seed populates
Q1's default but **does not skip Q1**. The Red Flag *"the user
may want to phrase it differently for the trunk than they did
in chat"* still applies — confirm the phrasing, then continue
to Q2. The Iron Law of four questions (Q4 optional) runs in full
regardless of how the skill was invoked.

The four questions, in order:

1. *"What's the title?"* (free text)
2. *"One-sentence description?"* (free text → trunk row description).
   **Soft cap at ~80 chars.** If the answer is longer, the skill
   responds with one short follow-up: *"Trunk descriptions read best
   under 80 chars (this is N). Want to shorten, or keep as-is?"* and
   waits. The follow-up is part of question 2.
3. *"Anything else to capture? Open questions on lines starting with
   `Q:`, notes anywhere else. Press enter to skip."* (free text,
   multi-line, **optional**). The skill parses the answer:
   - Lines starting with `Q:` (or `q:`) become items in
     `### Open questions` as bullets.
   - All other non-empty content becomes the body of `### Notes`.
   - If the user pressed enter (empty answer), both sections are
     omitted from the resulting file.

   This question always asks — it's the canonical place to capture
   the volatile context around the idea (half-formed thoughts,
   unknowns, examples) before that context evaporates. The four-
   question cap from the Iron Law accommodates it; the optional
   nature keeps friction low when there's nothing to add.
4. *"Capture as just an idea, or refine it now?"* — multiple choice:
   - `idea` — leave as `[?]`, exit
   - `refine later` — leave as `[?]`, exit (functionally same as `idea`,
     but signals the user plans to come back)
   - `refine now` — leave as `[?]`, exit with a pointer to
     `project-refine`

After the fourth answer, run the **atomic ID reservation**:

1. Read `PROJECTS.md` → find the largest existing `P##` → next ID is
   `P<max+1>`. **Always max+1.** Even if the user said *"add P34"*
   and the local max is P32, the skill uses P33. The immortal-ID
   property (no gaps, IDs never reused) is what lets cross-references
   stay stable; honoring user-picked IDs would compromise that. The
   skill mentions which ID it picked in the confirmation line so the
   user can see the difference if it matters.
2. The max is computed from the **local** trunk only. The skill does
   not `git pull` first. Two parallel sessions on different machines
   can theoretically pick the same ID and clash at merge time; that
   shows up as a merge conflict in `PROJECTS.md` and one of the
   project files, which the user resolves by renumbering one. The
   skill mentions this in the commit message indirectly — the
   commit is local-only.
3. If `PROJECTS.md` doesn't exist (fresh repo), copy
   `templates/PROJECTS.md` from the plugin to the repo root first,
   then proceed. Mention this to the user in one line.
4. Compute a kebab-case slug from the title. Use camelCase for the
   *rough* part if the title is awkward in kebab — the trailing
   hyphen is the canonical idea marker, so the camelCase variant is
   cosmetic.
5. Write `projects/P<NN>-<slug>-.md` (the trailing hyphen is required
   by the idea convention) using `templates/project-idea.md` from
   the plugin as the source. The template has:
   - `# P{{N}} — {{title}}` heading
   - `{{description}}` line
   - Optional `### Open questions` section with `{{open_questions}}`
   - Optional `### Notes` section with `{{notes}}`
   - HTML-comment breadcrumb pointing at `project-refine` for
     promotion

   Do a literal string-replace of `{{N}}`, `{{title}}`,
   `{{description}}`, `{{open_questions}}`, `{{notes}}` with the
   user's answers. Then **strip empty sections**: if
   `{{open_questions}}` is empty, remove the entire `### Open
   questions` heading and its placeholder line (and the trailing
   blank line); same for `### Notes`. The breadcrumb comment
   stays regardless. Idea state stays minimal-by-default — no
   `### Tests & Tasks`, no `### Scope`, no `**References**`. That
   is `project-refine`'s job.
6. Append the trunk row to the *Project index* section of
   `PROJECTS.md`. Use the standard markdown-link format:
   `- [?] **P<NN>** — [<title>](projects/P<NN>-<slug>-.md)`
   The title is a markdown link to the per-project file. The
   legacy `→ projects/...` arrow form is drift — external tools
   (markdown linters, doc generators, AI agents reading the repo
   without project-harness loaded) cannot parse the arrow as a
   link.
7. `git add PROJECTS.md projects/P<NN>-<slug>-.md`.
8. `git commit -m "docs(projects): capture P<NN> — <title>"`.
9. Print a one-line confirmation that includes the picked ID:
   `P34 — Rate-limit OpenAI client. Idea status. Committed locally as <sha>.`
   The word *"locally"* signals to the user that the commit is on
   their machine and may collide if another machine has captured a
   project since their last pull.
10. If the user chose `refine now`, append:
    `Run \`project-refine P34\` to scope.` Do not invoke it yourself.

## What it deliberately does not do

- Does not ask follow-up questions about scope, references, tasks, or
  open questions. Those belong in `project-refine`.
- Does not require a polished description. Capture first, refine when
  the user is ready.
- Does not pre-populate `### Tests & Tasks`, `### Scope`, or any
  other sectional boilerplate. The trailing-hyphen filename + minimal
  body is the canonical idea-state per the companion proposal §6.3.
- Does not invoke `project-refine` even when the user picks `refine
  now`. The user runs the next skill themselves.

## Red Flags

| Thought | Reality |
|---------|---------|
| "I should ask about scope while I'm here" | Four-question cap. Stop. Scope is `project-refine`'s job. |
| "The description is vague, I'll ask for more detail" | Capture first; refine later. The cap is the cap. |
| "I'll list all four questions in one message to be efficient" | One question per message. Re-evaluate after each answer per `_conventions.md` §6. |
| "Q4 is optional, I'll just skip it without asking" | No. Q4 always asks. The optionality is in the user's answer — pressing enter skips it cleanly. Skipping the prompt itself loses the user's chance to capture context. |
| "I'll add a `### Tests & Tasks` placeholder so it's ready for refine" | No. Idea files contain title + description only. The empty section is itself drift `project-audit` will flag. |
| "Two ideas at once — let me batch them" | One project per invocation. Atomic commit per project. Run the skill twice. |
| "User said 'add P34', I'll use that ID" | No. Always max+1. Honoring user-picked IDs creates gaps that compromise the immortal-ID property. |
| "I'll `git pull` first to be safe" | No. The skill is local-only by design. If the user wants to sync, they pull before invoking. |

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "The user clearly wants depth, I'll ask follow-ups" | They will get depth in `project-refine`. The cap survives "obviously wants depth" cases. |
| "Four is arbitrary" | Four (with Q4 optional) is the cap for low-friction capture *plus* room for the volatile-context capture (open questions, notes) that idea state benefits from. Lowering loses information; raising kills capture. |
| "I'll skip the commit, the user can commit later" | Atomic commit is what reserves the ID. Without it, two parallel sessions can pick the same `P##` and clash at merge time. |
| "I already know the title, I'll skip Q1" | Confirm anyway. The user may want to phrase it differently for the trunk than they did in chat. |
| "User wants P34 specifically, the immortal-ID rule is being pedantic" | The rule is what makes cross-references stable for years. Gaps look small now and are confusing later. |
| "The description is 90 chars, that's fine" | Ask. The 80-char soft cap is one short follow-up; the user can keep it as-is. Letting it slide trains the model to skip the cap silently. |

## See also

- `_conventions.md` §6 — one-question-at-a-time, iteratively.
- `project-refine` — when the user picks `refine now` or asks for
  depth after capture.
- `project-next` — when the user wants to *find* an existing project
  rather than create a new one.
- `templates/PROJECTS.md` — used as bootstrap when no `PROJECTS.md`
  exists yet.
