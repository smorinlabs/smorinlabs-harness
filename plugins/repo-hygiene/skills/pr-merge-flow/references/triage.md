# Thread triage — queries, rubric, etiquette

## Collect unresolved threads (one GraphQL query per cycle)

REST cannot see thread resolution state; this read and the resolve mutation
are GraphQL's only two jobs in this skill.

```bash
gh api graphql -f query='
query($owner:String!,$repo:String!,$n:Int!){
  repository(owner:$owner,name:$repo){
    pullRequest(number:$n){
      reviewThreads(first:100){
        nodes{ id isResolved isOutdated path line
          comments(first:10){ nodes{ databaseId author{login} body url } } } } } } }' \
  -f owner="$OWNER" -f repo="$REPO" -F n="$N" \
  --jq '.data.repository.pullRequest.reviewThreads.nodes | map(select(.isResolved|not))'
```

Caps: `reviewThreads(first:100)` / `comments(first:10)` truncate on very
large PRs — paginate via `endCursor` when a PR approaches 100 threads.

Rate-limited? Take the inventory and its ids from REST
(`…/pulls/{n}/comments?per_page=100` — the field is `id`, not `databaseId`;
same integer, different name) and get `isResolved` from the thread's own
rendered state per `references/browser-fallback.md`.

Also gather PR-level review bodies and issue comments via REST
(`…/pulls/{n}/reviews`, `…/issues/{n}/comments`) — bots sometimes put
findings there. Those have no thread to resolve, so they are answered with a
reply comment instead. (Diff-anchored `…/pulls/{n}/comments` entries belong
to the threads already collected above — never handle them separately.)

## Reply to a thread

Replies target the thread's top comment by its `databaseId` (from the query
above) — `gh pr comment` posts an issue comment, NOT a thread reply:

```bash
gh api "repos/$OWNER/$REPO/pulls/$N/comments/$COMMENT_ID/replies" \
  -f body='Fixed in <sha> — <one line>'
```

**Mind the endpoint asymmetry.** Posting a reply includes the PR number
(`…/pulls/{n}/comments/{id}/replies`), but reading one single comment does
**not** (`…/pulls/comments/{id}`). Appending an id to the list route returns
404, which reads exactly like a deleted comment — it is not. Confirm a
disappearance against a fresh paginated list before treating a thread as gone.

**Identifiers differ per surface** — REST `id` / GraphQL `databaseId` /
page `#discussion_r<id>` are the same integer, while the thread node id
(`PRRT_…`) that `resolveReviewThread` needs exists only in GraphQL. The full
correlation table, with prefixes and the consequences, is in
`references/browser-fallback.md`. Never carry an identifier across surfaces
without checking it against that table.

**The ID bridge is mandatory.** A reply is impossible without a real comment
id; never infer one from page text or ordering. GraphQL calls it `databaseId`
and REST calls it `id` — same integer, and `id` is what
`…/comments/{comment_id}/replies` takes. When GraphQL is rate-limited, take the
inventory and its ids from REST
(`gh api --paginate "…/pulls/{n}/comments?per_page=100"`, top-level =
`in_reply_to_id == null`; one page is not the inventory) —
the browser reads state and clicks controls but never supplies an ID. No ID,
no reply, and therefore no resolve.

**Replies are idempotent.** Before posting, list the thread's comments and skip
if one is already authored by us against that top comment. A retry after a
failed resolve re-attempts only the resolve.

## Bot roster

Treat as AI reviewers: any account of type `Bot`, and specifically the usual
set — `claude[bot]`, Codex (`chatgpt-codex-connector`), `greptile-apps[bot]`,
`copilot-pull-request-reviewer[bot]`, `coderabbitai[bot]`, and similar.
Human-authored threads go through the same rubric with more benefit of the
doubt — see the etiquette rules below for how refuting them differs.

## Verdict rubric

1. **Restate** the claim as something checkable ("dereference before null
   check at `src/x.ts:42`").
2. **Verify before believing** — strongest available evidence, in order: run
   a test or the failing scenario that encodes the claim; reproduce by
   execution; trace the code path by reading; only then reasoned judgment.
   Note which level was reached in the reply.
3. **Verdicts**
   - **Invalid** — evidence refutes it → reply with the concrete reason ("the
     null check on line 38 already guards this"), resolve. Never resolve
     without the reply.
   - **Valid** — evidence supports it → classify scope and value below
     before writing any code.
   - **Unclear** — cannot be settled with available evidence → per-mode
     handling in SKILL.md step 4.

## Scope and value classification (valid findings only)

| Class | Test | Action |
|---|---|---|
| **Small in-scope bug** | Defect in code this PR touched; the fix corrects lines rather than adding a mechanism; no new invariant | Minimal fix, conventional commit, push, reply `Fixed in <sha> — <one line>`, resolve |
| **Valid, out of scope** | Hardening/robustness/feature beyond the PR's stated goal, or a defect that predates the PR | Create the tracked item at the repo's `defer-target` first, reply `Deferred to <ref> — <one line>`, resolve |
| **Below the value floor** | See the table below | Reply `Declining — <one line>`, resolve |
| **Architectural** | Asks for a new mechanism, redesign, or trust-boundary change | Post one design-question comment; mark the thread **escalated** — it stays open and holds the merge at the gate; only the user closes it |

Classification signals that proved reliable: CodeRabbit's `Heavy lift` tag ≈
architectural; redesign imperatives ("define/introduce/restructure…",
"compute the fixed-point mapping", "define an allowlist or sandbox
boundary"); a fix that would add more lines than it touches leans out of
scope.

### The value floor

A commit is never free: each one carries measured ~7% regression risk, draws
a fresh reviewer wave on its new surface, and spends cycle budget. A small
fix earns a commit only when its value clears that floor. The test: **would
a maintainer, holding the repo's conventions, ask for this change
unprompted?**

| Finding | Disposition |
|---|---|
| Functional bug — behavior is wrong | Fix |
| Real typo — wrong word, command, or meaning in shipped text | Fix |
| Style/lint a repo convention or CI gate actually enforces | Fix (the gate would fail — functionally a bug) |
| Arbitrary style — reviewer taste, no convention behind it | Decline: "style-only; no repo convention requires this" |
| Contradicts a repo convention | Refute citing the convention — bots accept this and have formally withdrawn findings |
| Arguable value with real blast radius (e.g. "remove redundant guard" on a safety-critical path) | Decline citing risk asymmetry — arguable upside, unarguable regression cost |

Never defer a valueless finding — style noise in the tracker buries real
deferrals. Decline it.

### Three hard rules

- A finding against code added during this review → ask first whether
  **reverting the earlier fix to spec semantics** closes it more cheaply
  than extending it.
- "It extends the PR's own principle" is a **defer signal**, not a fix
  mandate.
- Arrival cycle never changes the class — a ship-breaking P1 in cycle 4 is
  still a fix; a style nit in cycle 1 is still a decline. (Trajectory rules:
  `references/convergence.md`.)

## Deferral destinations

Detect once per run, first match wins; record as `defer-target` in
`.claude/pr-merge-flow.local.md`:

1. `PROJECTS.md` / `projects/` in the repo → a task row in the owning
   project, per its conventions.
2. Issue references in recent commits/PRs, or a non-empty `gh issue list`
   → a GitHub issue.
3. A configured external tracker (e.g. Linear) → that tracker.
4. No evidence → **ask the user once**, save the answer.

A deferral without a created, referenced artifact is a silent drop, not a
deferral. The end-of-run report lists every deferral with its reference —
in every mode.

## Reply etiquette

- Every resolution carries a reply: what changed (with commit SHA), why the
  claim does not hold, `Deferred to <ref> — <one line>`, or
  `Declining — <one line>`. No silent resolves, ever.
- One reply per thread; no debates with bots — state the evidence once.
- **Human authors**: never auto-post a refutation in `--auto` mode — leave
  the thread open and downgrade the run to a ready-report naming it. In
  `confirm`/`ready` modes, gate refutations of human comments on the user.

## Resolve mutation

```bash
gh api graphql -f query='
mutation($t:ID!){ resolveReviewThread(input:{threadId:$t}){ thread{ id isResolved } } }' \
  -f t="$THREAD_ID"
```

Batch: resolve after the push that fixes a batch of threads, one pass per
cycle, keeping GraphQL call count minimal.

Rate-limited? REST has no substitute, but the browser does — click that
thread's **Resolve conversation** after anchoring to its own
`#discussion_r<id>`, per `references/browser-fallback.md`. Never pick a
Resolve button out of an enumerated list; identity comes from the anchor.
