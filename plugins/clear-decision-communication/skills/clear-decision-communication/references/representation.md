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
| Conditional behavior, such as a validation rule | the same input with the previous and the proposed outcome, as a table (F1) |
| Algorithm, such as ranking, scheduling, or retries | a worked example as pseudocode (F2), a whole block (F7), or a table of its steps, plus the boundary case and the rule the algorithm must preserve |
| Timing or state interaction, such as a race | an ordered sequence with the same event order under current and proposed behavior (F9 or F10), or a span chart (F16) when overlap in time is the fact |
| Architectural, such as moving responsibilities | a small system diagram with coded nodes (F8, F17, or F18), the baseline first and the change as a delta, one representative operation through it, and the tradeoffs |

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
| Same input, different outcome | F1 Same-input table |
| Logic or an algorithm | F2 Pseudocode |
| Runtime control flow | F3 Call tree |
| UI structure, state, and module boundaries | F4 Component tree |
| File responsibility, or a broad refactor | F5 File tree |
| What changes when the surrounding shape already exists | F6 Diff-shaped delta |
| A copyable target shape, or mostly new code | F7 Whole block |
| Components and how data moves between them | F8 Box-and-arrow |
| Ordered interaction over time | F9 Sequence ladder, or F10 Event table |
| States and what triggers each transition | F11 State diagram |
| Two variants compared line by line | F12 Side-by-side columns |
| The same request under each option | F13 Route per option, or F14 Trace table |
| Rough magnitude on one axis | F15 Bar |
| Duration and overlap on a time axis | F16 Span chart |
| Where something sits in a vertical stack, and where a limit cuts it | F17 Layer stack |
| Ownership, boundaries, and what is shared between paths | F18 Containment boxes |
| Branching conditions in evaluation order | F19 Decision tree |
| One measured value against its limit | F20 Threshold on a scale |
| Any hierarchy that is not files: a design space, a plan, ownership, configuration | F21 Tree |

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

### F1 Same-input table

```
| Input                              | Today                          | With the fix                        |
|------------------------------------|--------------------------------|-------------------------------------|
| 2024-02-30 through CSV import      | corrected to 2024-03-01 silently | rejected: "day 30 is not valid"    |
| 2024-02-30 through API upload      | corrected to 2024-03-01 silently | rejected with the same message     |
```

### F2 Pseudocode

```text
on(save)
  if content is unchanged
    return cached result
  write new content
  return fresh result
```

### F3 Call tree

```text
submitForm
  createSession
    persistPrompt
    launchAgent
  navigateToSession
```

### F4 Component tree

```text
<SessionPage> (apps/example/src/routes/session.tsx)
  useSessionEvents()
  <SessionToolbar>
    <RunSkillButton> (packages/ui)
```

### F5 File tree

```text
src/
|-- commands/       # parses user actions
|-- sessions/       # owns session state
`-- transport/      # sends API requests
```

### F6 Diff-shaped delta

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

### F7 Whole block

Show the whole block when most of it is new, when omitted context would hide
ownership or order, or when the reader needs a copyable target shape.

```ts
function expandSkill(command: string): string {
  const skillName = command.slice(1)
  return `use the ${skillName} skill`
}
```

### F8 Box-and-arrow

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

### F9 Sequence ladder

```
client          api           worker
  |              |              |
  |-- POST /job ->|              |
  |              |-- enqueue --->|
  |<-- 202 ------|              |
  |              |              |-- process
  |              |<-- done ------|
```

### F10 Event table

Use when the same event order must be compared under two behaviors.

```
| Event                                   | Current behavior                          | Proposed behavior                                   |
|-----------------------------------------|-------------------------------------------|-----------------------------------------------------|
| Search "cat", then "caterpillar"        | both requests run                         | both run; "caterpillar" recorded as latest (seq 2)  |
| "caterpillar" results arrive first      | displays "caterpillar"                    | displays "caterpillar"                              |
| "cat" results arrive later              | overwrites the display with stale "cat"   | seq 1 < 2, response ignored, display kept           |
```

### F11 State diagram

```
idle --start--> running --complete--> done
                  |
                  `--error--> failed --retry--> running
```

### F12 Side-by-side columns

Align the two variants so the differing line sits at the same height.

```
before                        after
-------------------------     -------------------------
git pull                      git pull --ff-only
  merges on divergence          fails on divergence
```

### F13 Route per option

Identical node set, one route per option, letters on the routes.

```
[U] upload --A--> [V] shared validator --> [S] store
[U] upload --B--> [V'] csv-only validator (proposed) --> [S] store
                  [V] shared validator unchanged
```

### F14 Trace table

One representative input, one row per hop, the payload shown at the hop that
changes.

```
| Hop                    | Current                         | Proposed                                  |
|------------------------|---------------------------------|-------------------------------------------|
| request sent           | {q:"cat"}                       | {q:"cat", seq:1}                          |
| response received      | display <- results              | if seq == latest: display <- results      |
| newer request pending  | stale results overwrite         | stale response dropped                    |
```

### F15 Bar

Rough magnitude only; give the value in text beside the bar.

```
p50  ####                 40 ms
p95  ############        120 ms
p99  ####################  340 ms  (about 8x the p50)
```

### F16 Span chart

Duration and overlap on a time axis. Use when overlap is the fact: a race, a
dual-write window, two phases that must not coincide. Unit on the axis, the
same events under current and proposed behavior, the moment the outcomes
diverge marked.

```
time (s)       0    2    4    6    8   10
request 1      |---------------------->|        "ca"
request 2           |-------->|                 "cat", newer
current shown                cat       ca   <-- (1) stale result overwrites
proposed shown               cat       cat  <-- (2) seq 1 < 2, response dropped
(1) the bug; (2) the fix. Illustrative order; the new test forces it.
```

### F17 Layer stack

Where something sits in a vertical stack and where a limit cuts it. Draw the
limit as a line between layers, code the layers so options can point at them,
mark moved or new work with `(new)`, and show today and proposed side by side.

```
today                              proposed (Q1.A)
+-------------------+              +-------------------+
| [U] browser       |              | [U] browser       |
+-------------------+              +-------------------+
| [G] gateway       |              | [G] gateway       |
=== 30 s cap =======               === 30 s cap =======
| [W] web process   |              | [W] web process   |
|   runs the export |              |   enqueues only   |
+-------------------+              +-------------------+
| [D] database      |              | [D] database      |
+-------------------+              | [J] jobs (new)    |
                                   +-------------------+
                                   | [X] worker (new)  |  <-- the 48 s runs here, below the cap
                                   +-------------------+
Unchanged, not shown: auth, billing, the report renderer.
```

### F18 Containment boxes

Ownership, boundaries, and what is shared between paths. A shared component is
one box that spans the paths, never a box drawn twice; the changed element is
marked; nesting stops at two levels so edges never cross. Also the form for
layout and proportion of a screen or a page region.

```
+-- [C] CSV import path --------++-- [A] API upload path --------+
|  parse rows                   ||  parse body                   |
+-------------------------------++-------------------------------+
|  [V] shared validator: date check   <-- (1) the fix changes this line |
+-------------------------------++-------------------------------+
|  store rows                   ||  store record                 |
+-------------------------------++-------------------------------+
(1) one function; both paths above it reach it, which is why Q1.A changes A too.
```

### F19 Decision tree

Branching conditions in evaluation order, for a recommendation that depends on
more than one condition. The root is a fact the reader can check, every leaf is
an option ID with its consequence, the recommended leaf is marked, and depth
stops at two questions. One condition needs only the sensitivity sentence.

```
Q: does any API caller rely on silent date correction?   (checkable: API request logs, one day)
|-- yes --> Q1.B keep the fix to CSV        callers unaffected; validator logic duplicated
`-- no  --> Q: must API changes carry a notice period?
            |-- yes --> Q1.A with a changelog entry   both paths fixed after the notice
            `-- no  --> Q1.A  (Recommended)         both paths fixed now
```

### F20 Threshold on a scale

One measured value against its limit, when the gap is the deciding fact. The
axis carries its unit and round ticks, the limit and the measurement each carry
a source, and the proposed value sits on the same line so the reader sees the
gap close.

```
export p95 (s)   0        10        20        30        40        50
                 |---------|---------|---------|---------|---------|
limit                                          ^ 30 s gateway (config, gateway.yaml)
today                                                        ^ 48 s (production logs, 2026-09-01)
proposed Q1.A         ^ under 1 s to enqueue; the 48 s runs off-request
```

### F21 Tree

The file-tree connectors for any hierarchy that is not files: a design space
with its pruned branches, a plan's phases and tasks, ownership, configuration
keys, an option and its sub-options. One item per line; annotate only the lines
the reader must act on; mark pruned, proposed, blocked, or done branches in
words at the end of the line.

```
queue backend
|-- database table            <-- Q1.A, one migration, no new service
|-- Redis list                (pruned: no persistence guarantee, constraint 2)
`-- managed queue service     (pruned: needs a vendor contract, out of scope)
```

```
Phase 2: exports to background workers
|-- Task 3: worker skeleton          done, commit 2c1d0e9
|-- Task 4: health check endpoint    blocked on the jobs_status index (Q1)
`-- Task 5: retire the sync path     not started
```

## Placement

Place each artifact next to the short text it supports, inside the section of
the brief it serves: the same-input table and the event table under "What
changes", the trace table or route map under "What changes" or "What you would
be accepting", a bar under "Evidence". Keep only the calls, files, props,
states, and boundaries needed to answer the question being asked. One form
usually suffices; several are rare; all of them is never right.
