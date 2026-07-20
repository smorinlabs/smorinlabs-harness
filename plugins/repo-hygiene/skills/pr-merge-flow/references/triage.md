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

Rate-limited? This read has no REST equivalent — see
`references/browser-fallback.md` for the browser escape hatch and its reset
guard.

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
   - **Valid** — evidence supports it → minimal fix, conventional commit,
     push, reply `Fixed in <sha> — <one line>`, resolve.
   - **Invalid** — evidence refutes it → reply with the concrete reason ("the
     null check on line 38 already guards this"), resolve. Never resolve
     without the reply.
   - **Unclear** — cannot be settled with available evidence → per-mode
     handling in SKILL.md step 4.

Style/naming suggestions with no correctness content: apply when they match
repo conventions and are cheap; otherwise reply why not, and resolve.

## Reply etiquette

- Every resolution carries a reply: what changed (with commit SHA), or why
  the claim does not hold. No silent resolves, ever.
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

Rate-limited? No REST equivalent exists — `references/browser-fallback.md`
clicks **Resolve conversation** in the web UI instead, reply-over-REST first
and verify-after-click always.
