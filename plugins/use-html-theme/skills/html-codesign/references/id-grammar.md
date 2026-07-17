# ID grammar

Every referenceable element gets a stable, prefixed ID. The contract: a person
reading an export can type "change `ch-02-b` to the compact option" in ANY
chat with the agent, and the reference resolves without pasting the whole
file. IDs survive round-trips through Markdown export, JSON export, chat, and
regeneration — that is what makes v1 → v2 a diff instead of a fresh blob.

## Grammar

```
sec-{NN}-{slug}   sections     sec-01-direction, sec-02-extras
ch-{NN}-{letter}  choices      ch-01-a, ch-01-b, ch-02-a
note-{NN}         section note note-01, note-02
ctx-{NN}          context      ctx-01, ctx-02 (one per section, NN matches)
note-overall      page note    (exactly one, in `feedback`)
```

Four prefixes only. A pick-any choice IS the include/exclude toggle — no
separate `tog-` type; stat tiles and illustrations are content, not
choosables, so they carry no contract IDs. Collapsed summary rows are pure
view state and carry no IDs either.

## Rules

1. **Lowercase, hyphen-separated.** No underscores, no camelCase.
2. **Zero-padded section numbers.** `sec-01`, not `sec-1` — sorts correctly
   up to 99 sections.
3. **Choice letters run a, b, c…** More than ~5 choices in one section means
   the decision needs splitting, not more letters.
4. **Slugs are kebab-case nouns** — `direction`, `extras`, `date-range`.
5. **Stability beats tidiness.** Across drafts, an ID that survives keeps its
   letter even if earlier letters vanished. Never compact `ch-01-b` into
   `ch-01-a` because `a` was dropped; new choices take the next unused
   letter.

## How an ID flows

```
spec JSON (id: "ch-01-a")
  → DOM (data-id="ch-01-a")
  → user toggles it
  → Export MD:  - **`ch-01-a` ✓ Focused — one hero number**
  → user pastes into chat: "keep ch-01-a, swap ch-02-b"
  → agent regenerates, ch-01-a keeps its ID in v2
```

## Parsing IDs from chat

- `ch-02-b` → choice b in section 02
- `sec-03` (bare, no slug) → the whole of section 03
- `note-01` → section 01's note value
- `ctx-02` → section 02's context block ("expand ctx-02's argument" = give
  a fuller version of that context/recommendation)
- Bare letters ("option b in the second section") → resolve to `ch-02-b` and
  echo the resolved ID back in your reply so the record stays precise.
