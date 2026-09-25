# The `afk` and `pack` arguments

Both build the same **package** — the largest set of queue items this session runs unattended.
`afk` fires it with zero interaction; `pack` shows it once and waits for one confirmation. The
session running a package is an **orchestrator**: it claims, dispatches, verifies and closes,
implementing nothing inline. Every run takes its model, effort and venue from the role table in
`../../reference/subagent-policy.md`, which also fixes the one-line format a departure costs.
While the package runs the orchestrator ALONE writes the queue, and **every `tk-queue` and
`tk-ticket-ref` call below carries `--dir "<queue dir>"`** — the queue dir
`../../reference/queue.md` addresses.
Without it the script resolves from the cwd, which an earlier `cd` retargets. A `--help` call
takes no `--dir`.

**Read `WINDOW.md` beside this file before anything below runs** — the quota wall and its
handoff, the checkpoint invariant, the seam's context threshold, the five `--state` contents of
an accumulated lane, the two vehicles that open a successor generation, `--budget N`.
Those rules fire at moments the steps below do not choose. Read this file by section, never end
to end: what a step defers is its BODY, not its existence. A session finding, at any step, takes
*A session finding, unattended* below.
A solo item's pull request and the lane's take *The fixer cap* below.

## A resumed generation starts here

`RESUME.md` beside this file carries the whole procedure — reset, draft, close, re-dispatch,
and the exits that grade a package it cannot resume. Read it there, whole, before anything
below runs; a generation that built its own package skips it.

## 1. Build the package

**The tracker import of `ROOT-CAUSE.md` beside this file runs first, whatever the count**; above
20 eligible candidates that file owns this step's cut, at or below 20 the cut below stands.

`tk-queue pack --dir "<queue dir>"` (`../../bin/tk-queue`) hands over the candidates: eligible
items in queue order, every exclusion with the value that caused it, each item's LANE, Ticket and
`[repo: …]` — filter and line shape in `tk-queue pack --help`. It does not decide the
cut. Re-triage before accepting an exclusion: clear an obsolete Risk or Env on the spot
(`tk-queue edit "<id>" --dir "<queue dir>" --risk none`), release a dead session's claim
(`tk-queue release "<id>" --dir "<queue dir>"`), rewrite a legacy class
(`tk-queue edit "<id>" --dir "<queue dir>" --class AUTONOMOUS` — it replaces the whole class
VALUE, annotations included); re-run `pack` after any of these.

**The lane is elected twice, and the remote decides between the calls.** `pack` reads the queue,
never the forge, so ask the remote once per distinct Spec reference of the first report — lanes,
every `avulso (<ref>)` and every `esta é <ref>` exclusion alike — of the repository the items
LAND in (`[repo: …]`; the Spec names the TRACKER, routinely another repo). `<m>`, the reference's
issue half, identifies the branch:

```sh
git ls-remote --heads "<the item's repo address>" "refs/heads/spec/<m>-*"   # exit 0 and no line = free
```

A URL or a path, never a remote NAME (`origin` resolves against the queue's own clone, a clean
false negative), and read the exit code, not only the output — an unreachable host exits 128,
which captured output turns into "free". A branch that survived its merge still holds the
lane; the report names it, deletion as the repair. An item printed `[repo: ?]`, or with no address
you can supply, leaves the package saying so. Then call `pack` again with every hit —
`tk-queue pack --dir "<queue dir>" --spec-under-way "<repo>#<n>"`, repeatable — and cut from the
SECOND call's list: the lane passes to the deepest spec at the floor of two tickets. The same
second call also takes `--blocked "<repo>#<n>"`, repeatable, for a candidate's own **Ticket:**
the caller found blocked on the tracker: the item leaves the package with its spec's count,
so a spec whose second ticket is blocked drops under the floor.

**Cut** from the top of that list until the package fits one session — around 3–6 items or ~2h of
summed Effort, an opening bid step 6's measurement corrects; what multiplies a lane is its
correction cycles. Recount tickets per Spec among the survivors and re-apply the floor (the
recount only demotes; a spec below the floor takes the solo lane). A package with an
accumulated lane reserves two more lines — the review at parity with the summed lanes, and
the tail as one suite plus the lane's N criteria and the merge of `origin/main` — or its
last third is unfunded.

**Done when:** the package lists its items with summed Effort and each one's lane after the
recount, the review and tail lines stand beside them, and every exclusion and item left out
carries its reason.

## 2. `pack` only: confirm

One multiSelect `AskUserQuestion` listing the package items, summed Effort in the question; the
check IS the authorization. (`afk` skips this step: invoking it IS the authorization.)
**Done when:** the confirmed package is fixed.

## 3. Claim, then dispatch

**Claim every item before dispatching the first** —
`tk-queue claim "<id>" --dir "<queue dir>" --as afk-host`. A second claim is REFUSED naming the
owner, and that refusal IS the concurrent-session guard: the item enters the report as held
elsewhere. The claim leads because tree signals are blind to a sibling in the shared main tree;
the worktree per run is a defence, not a check. A dead package leaves its claims
behind: `tk-queue release "<id>" --dir "<queue dir>"` hands one back without
closing it.

Recount the floor against the CLAIMED items (demote only), then ask the remote once more — step
1's `git ls-remote`, for the lane's spec and every `avulso (<ref>)` alike — BEFORE creating
anything. A branch already there is a sibling running or a package that died: create nothing over
it, take that spec's tickets out on step 1's rung and release their claims. Only then create and
push the accumulated branch, in the repository the items land in — never the cwd (`<slug>`: the
spec's title, lower-cased, each non-alphanumeric run one hyphen; generic under the exit rule
below):

```sh
git -C "<the lane's repo address>" worktree add "<path>/spec-<m>" -b "spec/<m>-<slug>" origin/main
git -C "<path>/spec-<m>" push -u origin "spec/<m>-<slug>"
```

**One lane, one address**: the `Repo:` field is stored as typed, so two spellings of one repo
are two addresses — where a lane's tickets disagree, the lane has no address and its tickets
leave on the no-address rung. The address names a repository, not a working tree: a URL runs in
its clone on this machine, and an item whose repository has no clone here leaves the package
undispatched, named with the reason.

**Explore the base ONCE, before the first ticket goes out.** One run reads the tree the lane's
tickets name and writes its notes to `<notes dir>`, this session's own scratch directory
OUTSIDE the repository, so neither the lane nor the tail carries it. The distilled contract
below covers the ITEM, these notes the BASE. A package with no accumulated lane skips this.

The lane is serial: each ticket dispatches into a worktree of its own, cut from
`origin/spec/<m>-<slug>` fetched at that moment, only after the previous ticket's cycle ends.
Both lines below put the upstream on the ticket's OWN branch: without `--no-track` it tracks the
lane's, and a bare `push` then writes work in progress into the branch the pull request
publishes.

```sh
git -C "<the lane's repo address>" worktree add --no-track "<path>/T<id>" -b "spec/<m>/T<id>" "origin/spec/<m>-<slug>"
git -C "<path>/T<id>" push -u origin "spec/<m>/T<id>"
```

Solo items dispatch beside it, in series within one repository; neither lane passes the
local ceiling. An item too big for one subagent's context leaves the package carrying its
briefing (form in `../verify/SKILL.md`) and its ready-to-paste line.

A lane with its own branch and pull request dispatches under `LANE-CONTRACT.md` beside this file.

Every run dispatched here is handled under `HYGIENE.md` beside this file.

**An item that cites a code line is checked before its run is composed** — where the fix
already exists, it does not dispatch. `STALE.md` beside this file owns the check.

Each run's prompt carries, produced here and never delegated back: the **contract block** pasted
verbatim from `../../bin/tk-contract --role <row>` — `implementer`, `implementer-spec` on the
accumulated lane, whose `pr = none` cell withholds the per-ticket pull request, or
`lane-implementer` for a lane that opens its own pull request — and
the **item's distilled contract**: the item, the memory file behind its `[[slug]]` at one hop,
its handoff; context in none of the three is a missing handoff, named in its own line.
**A public repository adds the exit rule.** `gh repo view --json isPrivate -q .isPrivate`, run
in the item's clone before any branch is named, decides: any answer but `true` is public. On a
public repository the distilled contract restates all three in generic terms, never their raw
text. The same holds for commit messages, pull request titles and bodies, and branch names, the
lane's `<slug>` included: no project, company or person names, no money values. It binds every
run there, fixers and mergers too, and this session's draft pull request. A lane run also gets
`<notes dir>` from the exploration above, read and never re-run. A solo run
also gets its ticket reference for its PR's closing line, composed HERE by
`../../bin/tk-ticket-ref "<id>" --dir "<queue dir>" --closing-line`, which reads the owner from
the clone the item's **Repo:** field names — pass `--repo <clone>` when the item names none.
Exit 1 refuses, naming the defect and its remedy, and exit 2 could not compose the run: neither
dispatches. Exit 3, an item with no ticket, dispatches saying so, with no closing line. Count
each run by the venue signature it returns, never by the flag you passed. On a wave, step 4 —
`AUDIT.md` beside this file — stands between the claim and the first run.

### The vehicle: one workflow per package

Fire the site's dynamic workflow from this session (`~/.claude/tk/dispatch.md` names the
mechanism; the Agent-tool fallback runs the same graph in series). One script per package and
one `agent()` per run: the lane is a serial loop — the item's implementer, then the
`lane-merger` of step 5 — the solo items run beside it, and the tail closes the graph. A fleet
project run (`../fleet/SKILL.md` §4) takes the fallback until a package here measures the
workflow on that path.

**Every `agent()` takes its `model` and `effort` from `args`, never from a literal in the
script** — a literal is the fork `../../bin/tk-contract` exists to prevent. The orchestrator
fills both from the role table: `model` always, `effort` by OMITTING the key where the row
reads `session`. No contract is copied into the script either — the block above reaches it
verbatim through `args`, and the lane contract above reaches it as a path. Pass `args` as the
object itself, never as a string field: composed into one, every key parses as absent.

An `agent()` whose role owes the checkpoint invariant carries no `isolation: 'worktree'` — it
works in the worktree already checked out on its branch, named by path.

`WINDOW.md`'s "The tick" owns the quota axis, `max-local-opus`; concurrent runs count against
`max-local-subagents`, the RAM axis. **Read it before each local dispatch:**
`../../bin/tk-ram` prints what the cgroup fits now, `LEDGER.md` takes that line, and
exit 2 falls back on the site key. Where the harness's own cap — `min(16, nproc - 2)` — is
smaller, the difference stays UNUSED: weigh a second workflow beside the first, never Agent
runs whose return lands in this session's context.

**Arm the tick before the turn that dispatches the first run ends** — `WINDOW.md`, *The tick*.

**The script stops dispatching at the first `null` and hands back what it holds.** A `null` is
the wall or a skip, never one of the three attempts `../verify/SKILL.md` counts. The launch is
a seam of its own: `WINDOW.md` refreshes the handoff right after it, and reads the quota
between the launch and the return.

**Done when:** every item is claimed or reported held elsewhere, the lane branch exists and is
pushed before its first ticket goes out, the base was explored once with its notes outside the
repository, every cited code line was checked before its run, and every run carries a generated
contract block, that path, and a prompt self-sufficient without the tracker. On a public
repository the exit rule binds every run. The vehicle's script names no model, effort or
contract of its own.

## 4. Audit the spec and the tickets

A package whose items came from a spec and ticket set written in this flow — a **wave** — is
audited before any of it is implemented. The procedure is `AUDIT.md` beside this file: the
three lenses, one verifier per finding, the four outcomes and the REGRILL that halts the
package. Read it there, whole, and hand its block to step 6. Its *Two orchestrators, one wave*
locks the spec against a package in another queue, and its *What the lenses read* scopes the
lenses to this package's tickets. Every `--criterion` the audit reads is anchored by
`../verify/SKILL.md`, *The anchor outlives the tree*, and the wording is still cheap to change
here.

**Done when:** `AUDIT.md`'s own "Done when" holds — the block step 6 is owed names one of its
four states.

## 5. Verify every delivery

The ruler is the item's own criterion and the rite is `../verify/SKILL.md` — read it before the
first item closes. **A solo item's final tree is the MERGE, never the tip alone**: the caller
re-runs the criterion and the whole suite on its tip merged with the fetched `origin/main`, in a
throwaway worktree nothing pushes — the tree its pull request merges. A conflict there is a
finding this step reports, not a merge to resolve: the item ends as a DECISION naming both tips.
An empty return is a failed attempt; the
three attempts and four outcomes are verify's own. An approved solo item leaves the queue here —
`tk-queue done "<id>" --dir "<queue dir>" --how "<pointer>"` — and an item verify turned into a
DECISION stays, carrying its handoff.

**The package's handoff hangs on the item that closes LAST** — `done` deletes the briefing of
the item it closes, so a head-item handoff dies at the first close. Before each `done`, run
`ls "<queue dir>"/handoff-T*.md`; where the closing item holds the briefing, rewrite it on the
item that now closes last.

A lane holding its own pull request takes the cold review of `REVIEW-CONTRACT.md` beside this file.

A lane item is verified BEFORE it reaches the shared branch — one cycle per item, in order —
while the orchestrator runs stages 1–5 itself. Stages 1–5 may run inside the workflow as one
`lane-merger` run, never the run that implemented the item; stages 6 and 7 are the
orchestrator's own, on the workflow's return. Delegated, the guarantee holds only as far as the
merger's own green, and *Before the first `done`* below catches a red item already merged:

1. **Confirm the invariant** in the item's worktree: `git status --porcelain` empty, HEAD equal
   to `@{u}`. A breach is repaired here — commit and push — and reported.
2. **Run the item's criterion AND the whole suite**, tailed, exit codes read from `PIPESTATUS`
   (`tail` hides them).
3. **Green is both.** Approved and proof-ready merge (the lane's PR is not `main`); failed 3×,
   rotten criterion and a red suite are red — a red suite spends one of the same three attempts.
4. **Merge with `--no-ff`, `T<id>` first in the title** — the merge commit is the user's
   `git revert -m 1` handle, the leading `T<id>` what the close and a resumed generation match on.
   A conflict here is a broken invariant, not a merge to resolve: abort, and the item ends as
   a DECISION (`--deferred afk`) naming its pushed branch and the two tips; the lane continues
   from its unchanged tip.
5. **Push the lane's branch** — the checkpoint of `WINDOW.md`'s invariant for the lane.
6. **On the first green merge the orchestrator SEES — on the workflow's return, or in the first
   cycle where it dispatches by Agent — open the draft pull request**
   (`gh pr create --draft --base main`). The body is the orchestrator's and nobody else writes
   it: per closed item it gains `Fixes <owner>/<repo>#<n>`, one line per ticket; the spec is
   named WITHOUT a keyword, so only the user closes it. **Ask verdict 5 for that item HERE**,
   against the body just written — `../../bin/tk-closure-check "<id>" --dir "<queue dir>"
   --pr <n>` — and record its answer for the gate's digest. After stage 7 the item's
   **Ticket:** field has left the queue with it. The check then has no subject, and answers
   red for every item of the package.
7. **Close the item last** — `tk-queue done "<id>" --dir "<queue dir>" --how "PR #<n>"`, after
   the push and once the pull request exists.

**Before the first `done` the remote is what is true, and a merger's report is not.** Read
`git log --merges origin/spec/<m>-<slug>` on the fetched tip, then run ONCE, by script with the
exit codes read and a timeout well above 120 s, the whole suite and the criterion of every item
that tip carries. Red there is a false green a merger returned: that item becomes a DECISION
naming the sha of its merge, and it is never closed. The tail's suite does not answer this — it
runs after the `done`s.

A red item never reaches the lane's branch while the orchestrator runs those stages, and the lane
does not halt either way: its DECISION names its pushed branch — the sha of its merge where a
delegated merger already merged it red — and later tickets cut from the unchanged tip.
The item's worktree is removed when it leaves the cycle (`git worktree remove`, never `--force`);
its branch stays until the lane's pull request merges.

### The lane's tail

Runs once per package, where an accumulated lane survived, in the lane's worktree. Every exit
ends in one place — the pull request out of draft, carrying `../merge-gate/SKILL.md`'s per-item
digest; that gate decides the merge, and nothing here reopens an item, reverts a merge or
rewrites anything pushed. In order:

1. **Merge `origin/main`** — the lane's one expected conflict site. A marker in a file a tool
   regenerates is re-run away; any other goes to a `fixer` with both sides as context. Check
   before pushing (`git grep -n '^<<<<<<< '`); a merge that cannot ship is dropped with
   `git reset --hard "@{u}"` — never pushed — and the digest carries it as outstanding.
2. **Review the accumulated diff once, against the pull request's base.** Prose an agent follows
   takes `../review/SKILL.md` §1's rule, handing over the inputs of
   `../../reference/slice-rules.md` "Before the PR", Spec reading the lane's own tickets, body
   AND comments; code takes the lens first, the two axes after. A `fixer` applies confirmed
   findings and pushes. A fix belonging to ONE item is committed on that item's own branch
   `spec/<m>/T<id>` — its worktree recreated as `RESUME.md`'s *Re-dispatch* does — and merged
   into the lane again with `T<id>` leading the title. Committed on the lane instead
   it sits outside every merge the item owns, and the user's `git revert -m 1` leaves the
   correction behind. A fix spanning
   items, or repairing the lane's own merge of `origin/main`, belongs to no item and stays on the
   lane's branch, named in the digest. A finding no fixer could close goes to the digest, and the
   pull request waits on it. Every other finding goes to *The fixer cap*. The cap decides how
   many correction cycles this review runs.
3. **The whole suite and every lane criterion, on the final tree**, tip and `origin/main` shas
   recorded for the digest's Tests line. A red criterion is reported with the merges that landed
   after its item, never repaired by reverting; the closed items stay closed.

Then mark the pull request ready and remove the lane's worktree — the gate's `--delete-branch`
fails on a branch still checked out.

### The sweep over the union

Runs once per package, after the last item is verified and BEFORE step 6 measures. `UNION.md`
beside this file carries it whole. It is FIXED, and a package with no accumulated lane runs it.

**Done when:** every item carries one verify outcome with its evidence block, the solo ones
proved over the merge with `origin/main`, every lane item reached the branch by a pushed
`T<id>` merge before its `done`, verdict 5 was asked of each while it was still open, the tip
carried the whole suite and every merged item's criterion before the first `done`, and every
red one is absent from it, the tail ran its three steps on the final tree and left the pull
request out of draft with the worktree removed, `UNION.md`'s own "Done when" holds, and every
claim left with its item or was released.

## 6. Measure, and hand the package to the close

Four numbers on one line — **planned × completed × wall clock × context at the cut**, the last from
`../../bin/tk-context` at that seam (no cut this generation: the predecessor's `--state` number;
none at all, `?`). Then the **sensor**: births per merged pull request — the queue IDs born in the
package (the age column of `tk-queue list`; highest − lowest + 1, one queue only, and a sibling's
IDs in the range count too) over its merged pull requests, with `pack`'s open count before and
after. The target is under 2, open not rising. One deviation line per departure from the role
table, and the audit's block. One **skip line** per ticket `ROOT-CAUSE.md`'s import left out as
already an item, naming the queue that holds it. An unclosed item carries the first reason that
applies: **blocked** (another environment, "runs on: X"); otherwise **new** when the package
created the item and **carried** when it predates the package, each under the dependency gate (a
sibling's claim or live audit comment, owner and moment), the lane gate (a spec's branch on the
remote, the pull request's number or the deletion repair), any other `pack` exclusion (its
printed value, and whether it names a defect in the item), or the effort gate (cut for size, with
the ready-to-paste line that runs it).
An item step 3 found already fixed takes the **already resolved** rung, with the sha and date.
Items verify ended at proof ready or DECISION owe nothing further.

**Done when:** the measurement and sensor lines, audit block, skip and deviation lines are written, every
unclosed item carries its rung, and the unvisited items are handed over by exclusion.

## 7. Chain the afk wrap-up

Run `../wrap-up/SKILL.md` with its `afk` argument, executed FROM that file: both skills carry
`disable-model-invocation: true`, and reading the file is how the chaining honours the lock. The
close owns committing and pushing before any review, the five verdicts of safe-to-merge, which
items merge unattended, and the closing template.

The package's closing report states, literally, `wrap-up afk: rodou` or
`wrap-up afk: nao rodou (<motivo>)` — no Stop hook catches the skip on every machine, and
`<motivo>` covers a legitimate skip (a concurrent guard, the quota wall) as much as an omission.
**Done when:** the wrap-up reached its own "Done when" — or it did not run, and the report names
the step that stopped the package and the state the tree was left in.

## The fixer cap

**A tooling repo — one whose code handles no business data — gets ONE correction cycle per pull
request.** The cap counts per firing of the review, never for the life of the pull request. A review
re-fired whole by *A resumed generation starts here* carries its own cycle. That cycle is a single
`fixer` dispatch, never resumed. A `fixer` whose batch touches a file outside the slice's diff stops
and reports. What the spent cycle leaves unclosed, and whatever a re-review finds after it, take
`FINDINGS.md` beside this file, inventory and all. The pull request exists by then, so the
destination that fits is its second — a line in that body, under "Achados não tratados". The
close's verdict 2 counts the finding by the destination that took it, never as one no fixer could
close, so the pull request does not wait on it. It waits only on a finding no fixer could close.

## A session finding, unattended

`FINDINGS.md` beside this file owns where the finding goes — the three destinations, the one
exit that leaves the package without code, and the close's single question.
Read it there, whole, at the moment of discovery. No new queue item is born while the package
runs.
