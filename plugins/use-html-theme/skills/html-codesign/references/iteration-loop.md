# The iteration loop

The page's back-channel to the agent is plain text — an export or a re-prompt
pasted into any chat. No live connection, no runtime, no host requirements:
that is what makes the loop work identically from Claude Code, Codex, or a
stakeholder's browser.

## The two re-prompt buttons

Both compose a message and put it on the clipboard (also shown in a panel for
manual copy). The user pastes it into whatever chat they share with the agent.

**Another draft** — iterate on the options themselves:

```
Make a v2 of "{title}". Keep these picks: {selected ids}. Replace the
unselected options in each section with fresh alternatives. Reuse every
surviving ID; only new options get new IDs.
```

**Here are my answers** — the decision is made; proceed:

```
Here are my answers for "{title}" — selected: {selected ids}.
Notes: {non-empty note values, id-prefixed}.
Proceed using exactly these choices.
```

Pasting the full MD or JSON export works too and carries strictly more
information; the buttons are the low-friction path.

## Rules for generating a v2

1. **Reuse every surviving ID.** A choice that carries over keeps its exact
   ID — same section number, same letter — even if siblings were removed.
2. **Mint new IDs only for new content**, taking the next unused letter in
   that section (`ch-01-d` after `c`), never re-lettering survivors.
3. **Sections keep their numbers.** Add new sections at the end; removing a
   section retires its number (don't renumber the rest).
4. **Selections carry forward.** A surviving choice keeps the `selected`
   state from the user's export unless they said otherwise.
5. **Re-validate.** The v2 spec goes through `validate_spec.py` before
   rendering, same as v1.
6. **Say what changed.** Alongside the v2, summarize in chat: kept / replaced
   / added, by ID — that's the diff the stable IDs exist to make possible.

## When an export comes back

Treat the JSON's `selected` values and note texts as the user's decision
record. If they returned MD instead, the ✓/✗ marks and blockquoted notes
carry the same information. Quote IDs back when confirming ("locking in
ch-01-a and ch-02-a") so the record stays precise.
