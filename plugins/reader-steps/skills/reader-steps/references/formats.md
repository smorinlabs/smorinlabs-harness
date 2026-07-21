# Worked renders

Every form the block takes, at each point on the scale ladder. Copy the shape,
not the content.

## One step — inline form

> **▶ Your step · ⌨️** Run `claude setup-token` — it needs an interactive
> terminal the agent doesn't have.
>   ✓ prints a token starting `sk-ant-oat…`; paste it back and I'll set the
> repo secret.

No frame, no count (`1 of 1` is noise), no tag, no divider, no footer. What
survives: it's yours (▶), where (icon inline — no divider to carry it), what,
how you know, and why it's yours.

## Two to three steps, one surface — light form

> **YOUR STEPS ▼ · 0/2**
> Done by me: the CI workflow is committed and pushed.
>
> **▶ 1 · ⌨️ Get a token** — `claude setup-token`
>   ✓ prints `sk-ant-oat…`
> **2 · ⌨️ Paste the token back here** so I can set `CLAUDE_CODE_OAUTH_TOKEN`
>   ✓ I confirm the secret landed
>
> Start with ▶ 1.

Rules and dividers drop out; one bold header line and a one-line footer carry
the frame. Plain numbers — a tag disambiguates across turns and concurrent
blocks, and at this size there is nothing to disambiguate from. Surface icons
move onto the step lines.

## Four or more steps, or two or more surfaces — full block

> ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
> **YOUR STEPS ▼ · release-bot · 0/4 · `[P26-T03]` · tag RB**
> ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
> **Completes:** `[P26-T03]` "Wire release-bot for demo-repo" (PROJECTS.md) —
> closing this unblocks the first automated release PR.
> **Done so far by me:** workflow committed, App drafted.
>
> — 🌐 in the browser · install the app on the repo —
>
> **▶ RB.1 · Give the App access to the repo**
>   `github.com/settings/apps/example-release-bot` → **Install App** → select
> `example-org/demo-repo`
>   ✓ repo settings list the app
>
> — ⌨️ in `~/c/demo-repo` · add the secrets, then trigger —
>
> **RB.2 · Store the key in 1Password**
>   `op item create --category "API Credential" --title release-bot-key --file key.pem`
>   ✓ prints the item UUID
>
> **RB.3 · Put the key in the repo's secrets**
>   `gh secret set RELEASE_BOT_KEY --repo example-org/demo-repo < key.pem`
>   📱 if prompted: approve the **GitHub** push notification on your phone
>   ✓ exits 0
>
> **RB.4 · Make the workflow run once**
>   `git commit --allow-empty -m "chore: trigger" && git push`
>   ✓ green **release-please** check on the commit
> ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
> **▲ That's all 4 — start with ▶ RB.1.** When RB.4 is green, I cut the
> release PR.

Note RB.3: the phone approval is a reactive line *inside* the step that
triggers it, not a fifth sequential step.

Note the addresses: RB.1 carries the literal URL rather than "your app's
settings page", and the terminal divider carries `~/c/demo-repo` once for all
three steps that share it — which is what lets RB.2's relative `key.pem` and
RB.4's repo context (commit + push from the right checkout) mean something.

## Eight or more steps — map and stop points

Adds three things to the full block: a `Map:` line (a one-glance table of
contents, so the job reads as finite), a `Stop points:` line (where the reader
can walk away safely — an unbroken long block silently implies "all of this,
now"), and step ranges on the dividers so the map's references land.

> ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
> **YOUR STEPS ▼ · new-mac bootstrap · 0/12 · `[P08-T02]` · tag NM**
> ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
> **Completes:** `[P08-T02]` "Bootstrap the new laptop" — after this,
> `just update` runs clean on the new machine.
> **Done so far by me:** dotfiles pushed, Brewfile exported.
> **Map:** 🖐️ NM.1–2 hardware · 🖥️ NM.3–4 system · ⌨️ NM.5–8 install ·
> 🌐 NM.9–10 auth · 📱 NM.11 approve · ⌨️ NM.12 verify
> **Stop points:** you can stop after NM.8 or NM.11 and resume cold.
>
> — 🖐️ at the machine · NM.1–2 · get it powered and online —
>
> **▶ NM.1 · Wire it for setup**
>   Power adapter and Ethernet — Wi-Fi setup over a captive portal is the
> usual failure.
>   ✓ charging indicator on, link light active
>
> *(… groups continue: 🖥️ system settings, ⌨️ toolchain, 🌐 auth, 📱 approve …)*
>
> — ⌨️ in `~/c/dotfiles` · NM.12 · verify —
>
> **NM.12 · Prove the machine is converged**
>   `/opt/homebrew/bin/just update`
>   ✓ ends with "All tools and configurations updated"
> ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
> **▲ That's all 12 — start with ▶ NM.1.** Tell me when NM.12 is green.

## Divider forms

| Form | Use |
|---|---|
| `— 🌐 in the browser · install the app on the repo —` | **Default.** Merged: one line, intent inside the rule. |
| `— 🌐 in the browser · NM.9–10 · authorize the CLIs —` | 8+ steps: adds the range the map references. |
| `— 🌐 in the browser —` then `Install the app and confirm access:` | Only when the intent needs more than ~6 words. |

## Step interior

**Default** — outcome title, literal below, ✓ below that:

> **RB.1 · Give the App access to the repo**
>   `github.com/settings/apps/example-release-bot` → **Install App** → select `example-org/demo-repo`
>   ✓ repo settings list the app

**Escalation** — `Done when:` first, for steps whose success is ambiguous or
expensive to get wrong:

> **RB.1 · Give the App access to the repo**
>   **Done when:** the repo's settings list the app under "Installed GitHub Apps"
>   How: `github.com/settings/apps/example-release-bot` → **Install App** → select `example-org/demo-repo`

Titles echoing the button label (`Install the App` above a line reading
`→ **Install App**`) are the redundancy this rule exists to prevent.

## Addresses

**Shared directory → the divider carries it once.** Four steps in one repo do
not repeat `cd` four times:

> — ⌨️ in `~/c/demo-repo` · add the secrets, then trigger —

**Mixed directories → the step carries its own**, and the divider stays
generic:

> — ⌨️ in the terminal · publish from two repos —
>
> **▶ PB.1 · Cut the library release**
>   in `~/c/mylib`: `uv build && uv publish`
>   ✓ the new version appears on PyPI
>
> **PB.2 · Point the app at it**
>   in `~/c/myapp`: `uv add mylib@latest`
>   ✓ `uv.lock` shows the version from PB.1

**Executable not confirmed on PATH → give the full path.** Both forms are
correct; the difference is whether you checked:

| Write | When |
|---|---|
| `gh secret set …` | You ran `command -v gh` this session and it resolved |
| `~/.local/bin/skillsmith list` | You didn't check, or the tool ships outside the usual PATH |
| `uv run ruff check .` | A runner makes PATH irrelevant — prefer this when one exists |

**Placeholders say where their value comes from**, in the step that uses them:

> **▶ TK.1 · Give the workflow a token to push with**
>   `gh secret set RELEASE_TOKEN --repo <owner>/<repo> --body '<token>'`
>   `<owner>/<repo>` is the repo from TK.0; `<token>` is the value printed by
> `claude setup-token` — it is shown once and not recoverable.
>   ✓ `gh secret list` shows `RELEASE_TOKEN`

**When you can't source the address, say so** rather than inventing one:

> **▶ AP.1 · Install the App on the repo**
>   Your App's install page — from `github.com/settings/apps`, open the App,
> then **Install App**. (I don't have its numeric ID, so I can't deep-link it.)
>   ✓ the repo's settings list it under **Installed GitHub Apps**

## Navigation depth

**Breadcrumb** (default, up to ~3 hops):

> **▶ SE.1 · Let this machine accept SSH**
>   **System Settings** ▸ **General** ▸ **Sharing** ▸ toggle **Remote Login** on
>   ✓ the toggle shows blue; `ssh localhost` connects

**Hop per line** (chain longer than ~3 hops, or a hop carries a caveat):

> **▶ SE.1 · Let this machine accept SSH**
>   1. Open **System Settings** (Apple menu ▸ **System Settings…**)
>   2. Sidebar: **General** ▸ **Sharing**
>   3. Toggle **Remote Login** on
>   4. Click its **ⓘ** ▸ set **Allow access for** to your user, not **All users**
>   ✓ toggle blue; `ssh localhost` connects

Hop 4 is why the promotion rule exists: its caveat would vanish inside a
breadcrumb.

## Turn two and later — the scoreboard

> ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
> **YOUR STEPS ▼ · release-bot · 1/4 · tag RB**
> ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
> ✅ **RB.1 · Give the App access** — done (app listed in repo settings)
>
> — ⌨️ in `~/c/demo-repo` · add the secrets, then trigger —
>
> **▶ RB.2 · Store the key in 1Password**
>   `op item create --category "API Credential" --title release-bot-key --file key.pem`
>   ✓ prints the item UUID
> ⬜ **RB.3 · Put the key in the repo's secrets**
> ⬜ **RB.4 · Make the workflow run once**
> ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
> **▲ You're on ▶ RB.2 — 3 remain.**

Done steps collapse to one line with their outcome, the live step keeps full
detail, pending steps dim to one-liners. When the last confirms, say so:
"all 4 reader steps confirmed."
