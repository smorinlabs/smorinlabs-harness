# Closing the delivery — the path, then what's next

Both page skills in this plugin end here — `html-codesign` after its loop
explanation, `html-explain` after its principles summary.

**This is additive.** It does not replace what either skill's delivery step
already says; it comes after. Nothing here removes the codesign paste-back
loop or the explainer's go-deeper offers.

Read from either skill's directory as `../../references/delivery-close.md`.

## 1. The absolute path — always, on its own line

Print the **full absolute path** to the generated file. Never a relative
path, never "written to the current directory", never just the filename.

```
/Users/<user>/projects/acme/docs/retry-explainer.html
```

Why this is a rule and not a preference: the person opening the file is
often not in the shell that made it. They may be in a file manager, a
different terminal, another machine, or reading the message on a phone. A
relative path is only meaningful from the working directory the agent
happened to be in — which the user cannot see and may not share. `./out.html`
is not an address.

Put it on its own line so it survives copy-paste and is visually findable in
a long message.

**If the file landed somewhere temporary or incidental, say so plainly** — a
scratch directory, a system temp path, a sandbox working directory. Those get
reaped, sometimes on session exit. Naming it is what makes the save offer
below load-bearing rather than decorative.

## 2. Then ask what they'd like to do next

Offer as **plain prose** — a short numbered list the user answers in natural
language. Do **not** raise these through AskUserQuestion by default, for two
reasons: the path must stay visible, and prose sharing a turn with a dialog
may never render at all (the Iron Law in `context-triage.md`). If a dialog is
genuinely wanted, the path must have ended a previous turn *and* be repeated
inside the dialog.

Every offer below is **strictly conditional**. Offering something this
session cannot do, or that the user does not have, is worse than staying
quiet — it costs them a reply to decline.

### Open it in the browser — only when this session can

Offer only when the session can actually reach a browser on the user's own
machine: a local interactive session.

**Do not offer** when the session is web-hosted, remote, headless, running in
CI, or inside a sandbox VM with no display — the command would appear to
succeed and nothing would open, on a machine the user isn't looking at.
**If you can't tell, don't offer.** A silent no-op is worse than no offer.

| Platform | Command |
|---|---|
| macOS | `open "<abs-path>"` |
| Linux | `xdg-open "<abs-path>"` |
| Windows | `explorer "<abs-path>"` |

**Always quote the path.** Generated pages land under directory names
containing spaces often enough — `My Documents`, `Application Support`,
`Google Drive` — that an unquoted template is a latent break: the shell
splits the path into several arguments and the open either fails or targets
something else entirely.

**On Windows use `explorer`, not `start`.** `start` treats its first quoted
argument as the window *title*, so `start "C:\...\page.html"` opens an empty
console window and no page; the cmd.exe-correct form needs an empty title
first (`start "" "C:\...\page.html"`), and in PowerShell `start` is an alias
for `Start-Process`, which parses differently again. `explorer "<abs-path>"`
behaves identically from both shells.

The page is self-contained, so it opens straight from `file://` — no server,
no network.

### Copy the path to the clipboard — same condition as opening it

Offer alongside the browser-open, gated identically: **only when the session
is running on the user's own machine.** Useful whenever they want to paste
the path into a browser bar, a file dialog, a chat message, or another tool.

| Platform | Command |
|---|---|
| macOS | `printf '%s' "<abs-path>" \| pbcopy` |
| Linux (Wayland) | `printf '%s' "<abs-path>" \| wl-copy` |
| Linux (X11) | `printf '%s' "<abs-path>" \| xclip -selection clipboard` |
| Windows | `Set-Clipboard -Value "<abs-path>"` (PowerShell) |

`printf '%s'` rather than `echo`, so no trailing newline rides along into the
clipboard and breaks the paste. Quote the path here too, for the same reason
as above.

**The remote case is worse here than for opening.** A browser-open on the
wrong machine visibly does nothing; a clipboard write on the wrong machine
**reports success** and silently populates a clipboard the user cannot reach.
If the session is remote, web-hosted, or in a sandbox VM, don't offer it —
the path is already printed in the transcript, which they can select.

### Add it to shelf — only when `shelf` is installed

Offer **only if `shelf` is among your available skills.** If it is not
present, do not mention it at all: not as an offer, not as a suggestion to
install it, not as an aside. Recommending a tool the user doesn't have is
noise dressed as helpfulness.

When it is present, say what it buys rather than naming the tool: `shelf`
manages a curated document library, so adding the page files it in the
catalog alongside their other docs and makes it findable later by topic
("what do I have in shelf about retries") instead of by remembering a path.
That is a genuinely different outcome from leaving the file where it is —
which is why it is worth an offer rather than a silent default.

Hand off to the `shelf` skill; never shell out to the CLI from here.

### Where to save it — read the artifact, don't apply a ladder

**When to raise it:** whenever the file sits somewhere temporary, *or*
anywhere **you** chose rather than the user — a default output directory, the
cwd you happened to be in, a path you invented. A location the user named
themselves needs no offer; every other case does, including a perfectly
durable one they never picked.

**There is no ranking.** A fixed order gets this wrong in both directions —
it files a design doc that obviously belongs beside its spec into a general
library, and it proposes a permanent home for a page that nobody will open
again. Ask instead: *what is this page, and where do things like it already
live?* Then recommend **one** destination with its reason, and name the
runner-up in a clause.

Signals worth reading, roughly in the order they tend to settle it:

**This session already has a home.** If artifacts have been going to one
place through this conversation, that is almost certainly the answer.
Repeating an established destination beats introducing a new one, and it
needs no explanation.

**The repo already does this.** The page documents a repo, and that repo has
an established place for this kind of thing — `docs/`, `docs/decisions/` or
`adr/` for a decision record, right beside the spec it explains. Convention
beats invention; follow what the repo already does rather than proposing a
tidier scheme.

**Durable and repo-bound, but no existing home.** It clearly belongs with the
code and will be read again, but nothing like it exists yet. Propose the
location that fits the repo's shape and say it is a new home, so the user can
redirect it cheaply.

**Standalone.** Research, a comparison, a briefing, a landscape review —
something whose value does not depend on any one repo, or something that
simply has no clean place to live. This is where **`shelf`** is the right
answer *if that skill is installed*, because it is a save location and an
index at once. If `shelf` is absent, say plainly that there is no obvious
home and ask.

**Ephemeral.** A throwaway comparison, a page built to settle a decision that
is being settled right now, something superseded the moment it is read.
**Say so and recommend not saving it.** "This doesn't look like a keeper —
leave it in the scratch directory" is a real recommendation, and it spares
the user a filing decision they would otherwise have to make and later
regret. Not everything is an artifact.

**These are examples, not a taxonomy.** Other clear homes exist and will keep
appearing — a notes vault, a team wiki export directory, a docs site's
content tree, a path the project's own CLAUDE.md names. Read the context and
the conventions actually in front of you rather than forcing a fit.

When genuinely nothing fits, ask — but ask with a proposal attached, not an
open question.

**Never move the file silently.** Offer, move on confirmation, then report
the new absolute path in full (rule 1 applies again to the new location).

## 3. Keep each skill's own next moves

The convenience offers go **after** the skill-specific ones, not instead of
them:

- `html-codesign` — the paste-back loop is the point of the artifact; it
  leads.
- `html-explain` — go deeper on a section, add a figure where it was thin,
  restyle under another theme.

## Gotchas

| Thought | Reality |
|---|---|
| "They can see the filename, that's enough" | They may be in another shell, another machine, or on a phone. Absolute or it isn't an address. |
| "I'll offer to open it — worst case nothing happens" | On a web-hosted or headless session that's exactly what happens: a command that reports success while the user stares at an unchanged screen. Don't offer what you can't do. |
| "`shelf` isn't installed, but I'll mention it as an option" | Don't. An offer they can't take costs them a reply and teaches them the offers aren't curated. |
| "The file is in a temp dir, they'll move it if they care" | They can't move what they don't know is temporary. Say it, then offer the save. |
| "I'll put the offers in an AskUserQuestion — it's tidier" | The dialog can eat the path. Prose list by default; a dialog only after the path has ended its own turn. |
| "I moved it somewhere sensible for them" | Never silently. Offer, confirm, then re-print the new absolute path. |
