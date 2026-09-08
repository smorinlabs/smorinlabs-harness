# Representation: showing the change in ASCII text

Which form makes the relevant behavior easiest to judge, and how to draw each
one in plain ASCII. Read this at workflow step 4. Every form here is text: a
downstream tool may render it, this skill never does.

Forms are adapted from three sources and converted to ASCII: the show-me skill
(humanlayer/skills, MIT), the clear-technical-communication artifact catalog
(Steve Morin), and the system-atlas design language (inkboard/system-atlas,
MIT). Attribution and licenses are in `references/framework.md`.

## Assess the difficulty first

- Interacting parts: how many concepts or components must be understood
  together?
- Hidden conditions: does correctness depend on timing, ordering, state,
  boundaries, or assumptions?
- Reasoning effort: can the consequence be seen directly, or must the reader
  mentally simulate events?

Provide the mental simulation when it is necessary to judge the change. Then
ask the one question that decides the channel: would the reader understand
this better by seeing it than by reading it? A conceptual question ("should
sessions auto-extend?") reads; a structural or sequential one ("where does the
stale result overwrite the fresh one?") is seen.

## Change type to form

This table mirrors the one in SKILL.md step 4; edit both together.

| Type of change | Show |
|---|---|
| Mechanical, such as a rename | one descriptive sentence naming the change and its purpose |
| Conditional behavior, such as a validation rule | the same input with the previous and the proposed outcome, as a table |
| Algorithm, such as ranking, scheduling, or retries | a worked example as pseudocode, a whole block, or a table of its steps, plus the boundary case and the rule the algorithm must preserve |
| Timing or state interaction, such as a race | an ordered sequence with the same event order under current and proposed behavior |
| Architectural, such as moving responsibilities | a small system diagram with coded nodes, the baseline first and the change as a delta, one representative operation through it, and the tradeoffs |

For a non-obvious change, the prose around the artifact covers, in order:

1. The relevant starting conditions and the intended behavior.
2. The failure or limitation under the current approach.
3. The proposed mechanism.
4. What happens under the proposed approach with the same starting conditions.
5. Why that mechanism changes the outcome.
6. The property it must preserve, in plain language.
7. The material tradeoff or limit.
8. The evidence that supports the explanation, and any remaining verification.

Choose the smallest example that exposes the actual difficulty. Include
ordinary behavior and the distinguishing boundary case only when both matter.
Keep inputs and event order identical across every comparison. Say whether the
example is illustrative or reproduced from a real run, and whether verification
was performed or is proposed.

## Relationship to form

| Relationship to show | Form |
|---|---|
| Same input, different outcome | Same-input table |
| Logic or an algorithm | Pseudocode |
| Runtime control flow | Call tree |
| UI structure, state, and module boundaries | Component tree |
| File responsibility, or a broad refactor | File tree |
| What changes when the surrounding shape already exists | Diff-shaped delta |
| A copyable target shape, or mostly new code | Whole block |
| Components and how data moves between them | Box-and-arrow |
| Ordered interaction over time | Sequence ladder, or an event table |
| States and what triggers each transition | State diagram |
| Two variants compared line by line | Side-by-side columns |
| The same request under each option | Route per option, or a trace table |
| Rough magnitude on one axis | Bar |

## Rules every diagram follows

- **Budget.** A view shows at most three new structures and one flow. A whole
  system at once reads as noise. The last line of a partial view names what was
  left out: `Unchanged, not shown: cache, auth, billing.`
- **Baseline first, then the delta.** The first view is what the reader already
  knows, the approved baseline. The change arrives as a second view, as a diff,
  or as ghost nodes on the same map.
- **Ghost convention.** Proposed or not yet built is marked, existing is plain.
  In a diff-shaped delta the marker is `+`. In a diagram it is the tag
  `(proposed)` on the node and a dashed edge `- - >`.
- **Code plus name on every node.** A one- or two-letter code and a readable
  name: `[V] validator`. Options then point at the diagram: "Q1.A changes V and
  U; Q1.B changes V only." Prose uses the same codes and names as the diagram.
- **Role word when the role matters.** Add it after the name: `(store)`,
  `(gate)`, `(surface)`, `(job)`. Leave it out when the role does not bear on
  the decision.
- **Two zoom levels at most.** The map, then inside one structure for its steps.
- **One representative payload.** When behavior is the point, trace one input
  through the flow and show its data at the hop that changes.
- **Frame.** A lead-in that says what question the artifact answers, the
  artifact exact and unedited, then a reading of one sentence that says what to
  take from it. An artifact never ships alone, and a reading never grows into a
  second explanation.
- **Labels on arrows.** An unlabeled arrow says that something flows without
  saying what.
- **Two components and one arrow is a sentence.** Write the sentence.
- **Fencing.** Code and pseudocode sit inside fences. A diagram of about ten
  lines or fewer may sit inline in the message; a longer one goes in a fence.
  Tables always use pipes.

## The forms

### Same-input table

```
| Input                              | Today                          | With the fix                        |
|------------------------------------|--------------------------------|-------------------------------------|
| 2024-02-30 through CSV import      | corrected to 2024-03-01 silently | rejected: "day 30 is not valid"    |
| 2024-02-30 through API upload      | corrected to 2024-03-01 silently | rejected with the same message     |
```

### Pseudocode

```text
on(save)
  if content is unchanged
    return cached result
  write new content
  return fresh result
```

### Call tree

```text
submitForm
  createSession
    persistPrompt
    launchAgent
  navigateToSession
```

### Component tree

```text
<SessionPage> (apps/example/src/routes/session.tsx)
  useSessionEvents()
  <SessionToolbar>
    <RunSkillButton> (packages/ui)
```

### File tree

```text
src/
|-- commands/       # parses user actions
|-- sessions/       # owns session state
`-- transport/      # sends API requests
```

### Diff-shaped delta

Use a diff when the point is what changes and the surrounding shape already
exists. Match the diff shape to the topic.

For a component change:

```diff
 <SessionPage>
   useSessionEvents()
   <SessionToolbar>
+    <RunSkillButton />
   <SessionTimeline>
+    <SkillResultCard />
```

For a file-layout change:

```diff
 src/
 |-- commands/
+|   `-- show-me.ts       # expands the slash command
 |-- sessions/
-`-- transport.ts
+`-- transport/
+    |-- client.ts
+    `-- stream.ts
```

For a call-tree change:

```diff
 submitForm
   createSession
     persistPrompt
+    expandSkillMention
     launchAgent
-  navigateToSession
+  navigateToSession
+    subscribeToEvents
```

For a state or control-flow change:

```diff
 on(save)
-  write content
+  if content is unchanged
+    return cached result
+  write new content
+  invalidate cache
```

### Whole block

Show the whole block when most of it is new, when omitted context would hide
ownership or order, or when the reader needs a copyable target shape.

```ts
function expandSkill(command: string): string {
  const skillName = command.slice(1)
  return `use the ${skillName} skill`
}
```

### Box-and-arrow

```
[C] client --HTTP--> [A] api --SQL--> [P] primary db (store)
                       |
                       `--cache read--> [R] redis (store)
Unchanged, not shown: auth, billing.
```

With the change as ghosts on the same map:

```
[C] client --HTTP--> [A] api --enqueue- - > [Q] jobs table (store, proposed)
                       |                       |
                       `--SQL--> [P] primary   `- - > [W] export worker (proposed)
```

### Sequence ladder

```
client          api           worker
  |              |              |
  |-- POST /job ->|              |
  |              |-- enqueue --->|
  |<-- 202 ------|              |
  |              |              |-- process
  |              |<-- done ------|
```

### Event table

Use when the same event order must be compared under two behaviors.

```
| Event                                   | Current behavior                          | Proposed behavior                                   |
|-----------------------------------------|-------------------------------------------|-----------------------------------------------------|
| Search "cat", then "caterpillar"        | both requests run                         | both run; "caterpillar" recorded as latest (seq 2)  |
| "caterpillar" results arrive first      | displays "caterpillar"                    | displays "caterpillar"                              |
| "cat" results arrive later              | overwrites the display with stale "cat"   | seq 1 < 2, response ignored, display kept           |
```

### State diagram

```
idle --start--> running --complete--> done
                  |
                  `--error--> failed --retry--> running
```

### Side-by-side columns

Align the two variants so the differing line sits at the same height.

```
before                        after
-------------------------     -------------------------
git pull                      git pull --ff-only
  merges on divergence          fails on divergence
```

### Route per option

Identical node set, one route per option, letters on the routes.

```
[U] upload --A--> [V] shared validator --> [S] store
[U] upload --B--> [V'] csv-only validator (proposed) --> [S] store
                  [V] shared validator unchanged
```

### Trace table

One representative input, one row per hop, the payload shown at the hop that
changes.

```
| Hop                    | Current                         | Proposed                                  |
|------------------------|---------------------------------|-------------------------------------------|
| request sent           | {q:"cat"}                       | {q:"cat", seq:1}                          |
| response received      | display <- results              | if seq == latest: display <- results      |
| newer request pending  | stale results overwrite         | stale response dropped                    |
```

### Bar

Rough magnitude only; give the value in text beside the bar.

```
p50  ####                 40 ms
p95  ############        120 ms
p99  ####################  340 ms  (about 8x the p50)
```

## Placement

Place each artifact next to the short text it supports, inside the section of
the brief it serves: the same-input table and the event table under "What
changes", the trace table or route map under "What changes" or "What you would
be accepting", a bar under "Evidence". Keep only the calls, files, props,
states, and boundaries needed to answer the question being asked. One form
usually suffices; several are rare; all of them is never right.
