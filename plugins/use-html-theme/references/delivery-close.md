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
| macOS | `open <abs-path>` |
| Linux | `xdg-open <abs-path>` |
| Windows | `start <abs-path>` |

The page is self-contained, so it opens straight from `file://` — no server,
no network.

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

### Where to save it

Worth raising whenever the file is somewhere temporary, or somewhere the user
didn't choose. Rank destinations by what they already do:

1. **`shelf`**, if installed — it is a save location *and* an index.
2. **A repo path**, when the page documents that repo — `docs/`,
   `docs/decisions/` for a codesign record, next to the spec it explains.
3. **Ask** — when neither fits, let them name it.

**Never move the file silently.** Offer, then move on confirmation, then
report the new absolute path in full (rule 1 applies again to the new
location).

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
