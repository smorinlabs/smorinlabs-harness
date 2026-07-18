# The iteration loop

The page's back-channel to the agent is plain text — an export or a re-prompt
pasted into any chat. No live connection, no runtime, no host requirements:
that is what makes the loop work identically from Claude Code, Codex, or a
stakeholder's browser.

## The three re-prompt buttons

Each composes a message and puts it on the clipboard (also shown in a panel
for manual copy). The user pastes it into whatever chat they share with the
agent.

**Questions first** — the reader can't answer yet; answer before deciding:

```
Before I decide "{title}": sec-01 (ctx-01): {question} · sec-04: {question}
— answer these (expand the contexts if needed), then I'll continue deciding.
```

Respond by answering each `q-NN` (quote the id back) and, where the answer
belongs in the page, regenerating with expanded context bodies — surviving
IDs unchanged.

**Another draft** — iterate on the options themselves:

```
Make a v2 of "{title}". Keep these picks: {selected ids}. I skipped
{sec ids} — drop or re-frame those. Replace the unselected options in each
section with fresh alternatives. Reuse every surviving ID; only new options
get new IDs. Re-author each section's context for the v2.
```

**Here are my answers** — the decision is made; proceed:

```
Here are my answers for "{title}" — selected: {selected ids}.
Skipped: {sec ids}. Notes — {id: value · id: value}.
Open questions — {sec: question}. Proceed using exactly these choices.
```

(Skipped/notes/questions clauses are omitted when empty.)

Pasting an export works too. Slim (the page's default) is the right thing
to paste back to the agent — it carries the decision without re-sending
contexts the agent already holds. Full is for human records, not for the
loop.

## Rules for generating a v2

1. **Reuse every surviving ID.** A choice that carries over keeps its exact
   ID — same section number, same letter — even if siblings were removed.
2. **Mint new IDs only for new content**, taking the next unused letter in
   that section (`ch-01-d` after `c`), never re-lettering survivors.
3. **Sections keep their numbers.** Add new sections at the end; removing a
   section retires its number (don't renumber the rest).
4. **Selections carry forward.** A surviving choice keeps the `selected`
   state from the user's export unless they said otherwise.
5. **Re-author every context.** The v2 input spec requires a context
   envelope per section (validator-enforced), and the rich body is
   re-authored in the page — never copy a v1 context forward blindly.
   Write fresh context that reflects what v1 decided: what's now locked,
   what the remaining trade-off is, and an updated recommendation.
6. **Honor skips.** A section the user skipped (`skipped: true`) was
   *deliberately not decided* — drop it from the v2, or re-frame it with
   the user's cues. Never re-ask it unchanged.
7. **Answer open questions first.** Any `open_question` in the export gets
   answered (quote the `q-NN` back) before or alongside the v2 — an
   unanswered question usually explains a skip or a missing pick.
8. **Re-validate.** The v2 spec goes through `validate_spec.py` before
   rendering, same as v1.
9. **Say what changed.** Alongside the v2, summarize in chat: kept / replaced
   / added / dropped, by ID — that's the diff the stable IDs exist to make
   possible.

## When an export comes back

Exports are `codesign-answers` documents (references/export-formats.md),
not input specs. Treat each answer's `selected` entries and `note` text as
the user's decision record. If they returned MD instead, the ✓ lines and
note blockquotes carry the same information. Quote IDs back when confirming
("locking in ch-01-a and ch-02-a") so the record stays precise.
