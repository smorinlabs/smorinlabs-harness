---
name: session-loose-ends
description: Sweep a session for loose ends and clean them up with per-item consent — the acting sibling of session-recap (which orients and never mutates). Checks four classes — working-state artifacts (uncommitted/unpushed work, stashes, stale worktrees, scratch files), running or zombie processes (uncollected background tasks, lingering Codex jobs, stale watch loops), promises made in the conversation but not done, and light project-tracking drift (stalled in-progress rows, work done but never checked off). Reports every finding with its evidence and a recommendation in BOTH directions (clean vs deliberately keep, with reasons), walks the recommendations one at a time for confirmation, then executes only what was approved and verifies each action. Use when the user asks "any loose ends?", "anything to clean up?", "what's dangling here?", "tie this off", or returns to a thread wanting the actionable state only — NOT a full recap (session-recap) and NOT a deep tracking audit (project-audit).
---

# session-loose-ends

Find what's dangling, show the evidence, recommend keep-or-clean both ways,
confirm item by item, then actually clean — the mutating counterpart to
read-only `session-recap`.

> **NOTHING IS CLEANED WITHOUT ITS EVIDENCE SHOWN AND ITS CONFIRMATION
> GIVEN.** Every action is justified before it's offered and verified after
> it runs. A sweep that deletes on inference is worse than no sweep.

**This skill deliberately declares no `allowed-tools`** — it has to mutate, so
it inherits everything. `session-recap` does declare one (`Bash, Read, Glob,
Grep`), because its contract is read-only. The asymmetry is intentional: don't
"fix" it in a least-privilege audit.

## Workflow

**You gather by where you look; you report by what's owed.** The four sweep
classes below are evidence *sources* — they're good at finding things and bad at
telling the user what to do about them. Step 2 re-sorts every finding onto the
axis that matters: did anyone agree to it, and who has to move next.

1. **Sweep quietly** — gather all four classes before reporting anything;
   every probe degrades gracefully — a skipped or failed probe renders
   `⚠ couldn't check <X> — <probe> unavailable`, visually distinct from a
   verified-clear class; "couldn't check" never folds into "nothing to
   report":
   - **Working state**: `git status --porcelain=v2 --branch` (dirty files,
     ahead/behind), `git stash list`, `git log @{upstream}..HEAD --oneline`
     (unpushed), `git worktree list` (stale/orphaned), scratch files created
     during recent work.
   - **Default-branch freshness** — for repos in the touched set only (see
     below). `git status` reports the **current** branch, so a repo parked on
     a feature branch says nothing about `main`. Ask the default branch
     directly, whatever is checked out:

     ```bash
     d=$(git symbolic-ref --short refs/remotes/origin/HEAD | sed 's|origin/||')
     git rev-list --left-right --count "origin/$d...$d"   # → "<behind>\t<ahead>"
     ```

     **The touched set is earned, not assumed.** A repo enters it only on a
     *verified* event this session: a PR read back from the API as
     `merged=true`, or a push confirmed present on the remote. An attempted
     merge or push that was never verified does not qualify — believing an
     unverified merge is the same failure this check exists to catch. Repos
     never merged-to or pushed-to are out of scope; probing them is noise.

     Read the two numbers as separate findings, because the remedies differ
     and one of them destroys work:

     | State | Class | Remedy |
     |-------|-------|--------|
     | `behind>0, ahead=0` | 🧹 stale | `git pull --ff-only`, or `git fetch origin <d>:<d>` when not checked out |
     | `ahead>0` | 📌 **divergence — never 🧹** | preserve to a branch *first*; `--ff-only` refuses by design and `reset --hard` silently destroys the commits |
     | `0, 0` | clear | name it in the clear-footer |
   - **Processes**: the session task list (uncollected background tasks and
     agents), lingering background shells, Codex companion jobs still
     "running/verifying" after their results were taken (sweep
     `codex-companion status` when that runtime is present — zombies are a
     known failure mode).
   - **Conversation promises**: scan the recent thread for commitments not
     yet done — "I'll do X", deferred follow-ups, questions asked and never
     answered, offered next steps never taken.
   - **Tracking drift (light)**: PROJECTS.md / task rows still `[~]` whose
     work looks finished or abandoned; completed work never checked off.
     Two or more structural drift findings → recommend a `project-audit`
     run instead of fixing piecemeal here.
2. **Classify every finding** — sort what the sweep turned up into the four
   commitment classes, and give each one a class-prefixed ID. **Keep the
   quote or probe output that earned the tag**; no proof, no row.

   | Tag | Test | Proof required |
   |-----|------|----------------|
   | ❓ `D#` | A question was put to the user and never answered, or two approaches were weighed and never chosen | the unanswered question |
   | 📌 `W#` | The user assented (or you stated an intention they didn't refuse) **and** it isn't done | the assent, quoted with its turn |
   | 🧹 `C#` | Something that needs only **clearing**, not work — an artifact or process a probe can see and a command can remove | the probe output |
   | 💡 `S#` | Floated by either party and never assented to | the origin, quoted with its turn |

   **🧹 is checked first and wins ties.** Cleanup is a special case of open
   work: it's unresolved, but nothing has to be *worked on* — it only has to
   be cleared. A merged branch's worktree still exists and a probe still sees
   it, but nobody has to work on it, so it's 🧹. Ask "does this just need
   clearing?" before any other test.

   **Every 🧹 row names its release condition, and the condition is verified
   before the row is offered.** "A probe can see it and a command can remove
   it" says nothing about *when* removal is safe. Every artifact has a moment
   before which deleting it destroys something — a patch file is the only copy
   of work until its PR merges; a branch is the only pointer to commits until
   they land upstream. An artifact whose condition is unmet is reported
   **🟡 Not yet — gated on <what must land first>**; it is never offered for
   cleanup and never batched into "clean all recommended".

   | Artifact | Released by — must be *verified*, never assumed |
   |----------|------------------------------------------------|
   | Worktree on branch `B` | `B`'s PR read back from the API as `merged=true`, or `B` explicitly abandoned by the user |
   | **Local** branch `B` | `B` is an ancestor of `origin/<default>` **and** no worktree holds it |
   | **Remote** branch `B` | `B`'s PR read back as `merged=true` — otherwise it may be someone's in-flight work |
   | Scratch file / patch backing a PR | that PR read back as `merged=true`; until then the file may be the only copy of content not yet upstream |
   | Scratch file backing nothing | immediately — no dependent, no wait |
   | Background job / browser tab | the work it was opened for is complete |

   **Verifying `merged=true` is a probe, not an assumption.** Read it back
   REST-first — GraphQL (`gh pr view` / `gh pr list`) rate-limits on this
   machine — with one probe per endpoint and no retry loops:

   ```bash
   gh api "repos/{owner}/{repo}/pulls?head={owner}:{branch}&state=all"
   ```

   and read `merged_at` on the returned PR. The probe resolves to exactly one
   of five outcomes:

   | Outcome | Verdict |
   |---------|---------|
   | ok — PR found, `merged_at` set | merge confirmed — the release condition above is met |
   | no PR found for head `{owner}:{branch}` | 🔒 Keep (a verified answer for this probe, not a probe failure) |
   | rate-limited | `⚠ couldn't verify — treat as NOT merged, do not clean` (🔒 Keep) |
   | unauthenticated / `gh` missing | `⚠ couldn't verify — treat as NOT merged, do not clean` (🔒 Keep) |
   | unreachable / network error | `⚠ couldn't verify — treat as NOT merged, do not clean` (🔒 Keep) |

   The three probe-failure outcomes (rate-limited / unauthenticated /
   unreachable) are unknown state and render `⚠ couldn't verify — treat as
   NOT merged, do not clean`; a successful probe returning no PR is a
   verified answer — still 🔒 Keep, but knowledge, not ignorance. The user may
   still overrule with their own verification when the item comes up in the
   per-item confirm.

   **Order is load-bearing, not cosmetic:** worktree → local branch → remote
   branch. A worktree holding a branch makes `git branch -d` refuse, so
   removing it first is what makes the next step possible.

   **`git branch -d` is HEAD-relative.** It tests merge-into-**HEAD**, not
   into the default branch, so in a repo parked on a feature branch it reports
   "not fully merged" for branches that are fully merged into `main`. That
   refusal is ambiguous — it means *either* real unmerged commits *or* just an
   unrelated HEAD. Disambiguate explicitly before doing anything:

   ```bash
   git fetch origin
   git merge-base --is-ancestor <branch> origin/<default>   # the question you meant to ask
   ```

   Compare against **`origin/<default>`, never the local one.** The local
   default branch is exactly the thing this skill warns can be stale or
   diverged, so using it reintroduces the bug one line after naming it — a
   branch merged upstream is *not* an ancestor of a local default that hasn't
   pulled, and the check returns a false negative that strands the branch as
   permanently undeletable.

   Escalating to `-D` requires a stronger test than the one `-d` applies —
   confirm the branch is genuinely merged into the *upstream* default rather
   than a stale local one, and record the branch tip first so the reflog can
   recover it.

   **📌 vs 💡 is decided by the record, not by merit.** A good idea you had
   and the user never answered is 💡, full stop. That line is what lets the
   user trust 📌 as a real backlog rather than a wishlist.

3. **Report** — four sections, in this order, split by whether you can act.
   The IDs are a reply grammar: the user can answer `C1 C2 yes, W1 skip`.
   Render only the classes that have items; **nothing found at all → say so
   in one line and stop.** For partial emptiness, close with one dim footer
   naming what came back clear (`— clear: no decisions pending —`) — a
   silently absent class reads as "didn't check".

   Every row still carries its evidence and a recommendation in **both**
   directions. Recommending *keep* is a first-class outcome — unpushed
   commits ahead of a broken remote, a dirty tree mid-experiment, or a
   worktree another session owns are loose ends to *report*, not to remove.

   **Never fence real sweep output.** The skeleton below is shown inside a
   code fence so its raw structure stays legible for documentation; live
   output must render as real markdown tables — fencing suppresses table and
   bold rendering and degrades the report to raw pipes. Wrapped verdict or
   table text takes a hanging indent, aligning under the content column,
   never back under the labels. A `Context:` sub-line never touches the
   decision it explains — it gets a blank line above it (a `<br>` in a
   pipe-table cell, since pipe syntax can't express a true blank line).

   ```
   ## 🧾 Loose ends — <n> findings

   ### 🧹 Cleanup pending — <n>                          · I can act on these
   | ID | Artifact | Evidence | Released by | Recommendation |
   |----|----------|----------|-------------|----------------|
   | C1 | <artifact or process> | <probe output proving it exists> | <the verified event — or ✗ what it still waits on> | 🟢 Clean now — <why safe> / 🟡 Not yet — gated on <what> / 🔒 Keep — <why it survives> |

   ### 📌 Committed · not done — <n>                     · I can act on these
   | ID | Committed work | Proof it was agreed | Next move |
   |----|----------------|---------------------|-----------|
   | W1 | <what was promised> | <who, which turn, quoted> | <the action, or what blocks it> |

   ──────────── below here I can't act — your call ────────────

   ### ❓ Decisions pending — <n>                         · report only
   | ID | The decision | Blocks | My recommendation |
   |----|--------------|--------|-------------------|
   | D1 | <the fork, with its options><br>Context: <the spec, prior turn, or file it traces to> | <what's waiting on it> | <a real pick, and why it wins> |

   ▶ Prompt — paste this to settle the open decisions:
   "Settle D1 — <the fork, with its options>, from today's loose-ends
   sweep — and D2 the same way. Run `/question-walkthrough D1, D2`."

   ### 💡 Suggested · not committed — <n>                 · report only
   | ID | Idea | Where it came from | Size |
   |----|------|--------------------|------|
   | S1 | <the idea> | <who floated it, which turn — and that it went unanswered> | small / medium / large |

   ▶ Prompt — paste this to capture the idea as a project:
   "Capture S1 — <the idea>, floated by <who>, from today's loose-ends
   sweep — as a project. Run `/project-add S1`."
   ```

   ❓ and 💡 are printed, not swallowed: you can't decide for the user or
   accept your own suggestion, but dropping them is how they evaporate. Each
   gets a real recommendation and a copy-pasteable handoff — a ❓ row whose
   recommendation says "needs a decision" has wasted the row.

4. **Confirm one at a time** — walk 🧹 and 📌 with the
   `question-walkthrough` engine (cleanups as options with the
   recommendation first; notes modify actions). Batch-confirm only when the
   user explicitly asks for "clean all recommended", or when they reply in
   ID shorthand, which is consent for exactly the IDs they named.
5. **Execute + verify** — run each approved action, then prove it landed
   (re-run the probe that found it; "no change" is a failure to investigate,
   never success). Re-verify each release condition *at execution time*, not
   just at survey time — a PR can be reverted and a worktree can be re-created
   between the two. Execute git artifacts in dependency order (worktree →
   local branch → remote branch) regardless of the order the user selected
   them in; selection is consent, not a sequence. Close out with **every ID
   accounted for** — cleaned, kept, skipped, or handed off:

   | ID | Finding | Decision | Result |
   |----|---------|----------|--------|
   | C1 | `wt/feat-export` worktree | 🧹 cleaned | ✓ verified — absent from `git worktree list` |
   | W1 | Flip P07-T03 | ⏭ skipped | left `[~]` at your request |
   | D1 D2 | 2 decisions | handed off | `/question-walkthrough D1, D2` |

   Past ~7 executed-and-verified items, collapse the cleaned rows into one
   counted line naming the ID range (`12 cleaned — C1–C12`); skipped, kept,
   and handed-off IDs always stay itemized, however many there are. The
   accounting invariant survives the collapse — the range still names every
   ID, so nothing silently drops out of a sweep grown past a handful.

   An ID that appears in the report and not in the close-out is a dropped
   item, not a completed sweep.

## Red Flags

| Thought | Reality |
|---|---|
| "Dirty tree — obviously stage and commit it" | Maybe it's mid-experiment. Evidence + recommendation, user decides. |
| "`git status` came back clean, so the repo is current" | It reports the *current* branch. A repo sitting on a feature branch says nothing about `main` — ask the default branch directly. |
| "It's behind, so `--ff-only` will fix it" | Only when `ahead=0`. Test divergence before naming the remedy; on a diverged branch `--ff-only` refuses and `reset --hard` destroys commits. |
| "I merged it, so my local default branch is current" | A merge lands on the remote. The local branch is a separate fact, and it is the one that bites next session. |
| "This worktree looks stale, remove it" | It belongs to session X — parallel work. Report it as 🔒 Keep, never offer it for cleanup. |
| "It's just a temp file, deleting it is free" | A patch or scratch file backing an unmerged PR may be the only copy of that work. Free only once the PR is verified merged. |
| "The PR is merged, so the branch and its files are disposable" | *Verified* merged — read back via `gh api` per the merge-verification probe above, never assumed. A merge you believe in but never confirmed is the failure this gate exists to catch. |
| "`git branch -d` refused, so it has unmerged commits" | `-d` tests merge-into-HEAD. On a repo parked on a feature branch it refuses for fully-merged branches. Ask `git merge-base --is-ancestor <branch> origin/<default>` instead — after `git fetch`. |
| "I'll check ancestry against the local default branch" | The local default is the thing this skill says can be stale. A branch merged upstream is not its ancestor until you pull, so the check false-negatives and strands the branch. Always `origin/<default>`. |
| "I'll delete the branch, then remove the worktree" | Wrong order — the worktree makes the deletion refuse. Worktree → local → remote, every time. |
| "The user wants cleanup, skip per-item confirmation" | Per-item is the contract; only an explicit "clean all recommended" batches. |
| "I cleaned it, moving on" | Verify each action landed. A silent no-op is a finding, not a success. |
| "This needs the full recap treatment" | Orientation is session-recap's job. This skill reports only what's actionable. |
| "I can't act on decisions — leave them out" | Print them anyway. You can't decide, but you can recommend and hand off. Omitting is how they evaporate. |
| "They'd probably want this — call it committed" | 📌 requires a quotable assent. No quote → 💡. |
| "Nothing in that class — just leave the heading out" | Omit the body, keep the trace. A silent absence reads as "didn't check". |
| "The sweep found four classes, so report four classes" | Sweep classes are where you looked. The report is sorted by what's owed. |

## See also

- `session-recap` — the read-only orienter ("where was I?"); use it when the
  user needs the story, not the broom. It reports the same four owed classes
  (❓📌🧹💡) with the same IDs, so a recap's `C1` is the item this skill offers
  to clean.
- `question-walkthrough` — the confirmation engine step 4 delegates to, and
  where ❓ Decisions pending hands off.
- `project-add` — where 💡 Suggested hands off; captures an idea as a project
  stub so it survives the session.
- `project-audit` — deep PROJECTS.md drift; this skill hands off rather than
  duplicating its eleven checks.
