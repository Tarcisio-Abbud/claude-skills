# The `afk` and `pack` arguments

Both build the same **package** — the largest set of queue items this session can run unattended.
`afk` fires it with zero interaction; `pack` shows it once and waits for one confirmation. The
session running a package is an **orchestrator**: it claims, dispatches, verifies and closes, and
implements nothing inline. Every run takes its model, effort and venue from the role table in
`../../reference/subagent-policy.md`, which also fixes the one-line format a departure costs.
While the package runs the orchestrator ALONE writes the queue, and **every `tk-queue` and
`tk-ticket-ref` call below carries `--dir "<queue dir>"`** — the queue dir
`../../reference/queue.md` addresses.
Without it the script resolves from the cwd, which an earlier `cd` retargets to another
project's queue. A `--help` call takes no `--dir`.

**Read `WINDOW.md` beside this file before anything below runs** — the quota wall and the handoff
it demands, the checkpoint invariant, the context threshold at every seam, the five `--state`
contents of an accumulated lane, the two vehicles that open a successor generation, `--budget N`.
Those rules fire at moments the steps below do not choose. Read this file by section, never end
to end: what a step defers is its BODY, not its existence. A session finding, at any step, takes
*A session finding, unattended* below.
A solo item's pull request and the lane's alike take *The fixer cap* below.

## A resumed generation starts here

`RESUME.md` beside this file carries the whole procedure — reset, draft, close, re-dispatch,
and the exits that grade a package it cannot resume. Read it there, whole, before anything
below runs; a generation that built its own package skips it.

## 1. Build the package

`tk-queue pack --dir "<queue dir>"` (`../../bin/tk-queue`) hands over the candidates: eligible
items in queue order, every exclusion with the value that caused it, each item's LANE, Ticket and
`[repo: …]` — filter and line shape in `tk-queue pack --help`. What it does not decide is the
cut. Re-triage before accepting an exclusion: clear an obsolete Risk or Env on the spot
(`tk-queue edit "<id>" --dir "<queue dir>" --risk none`), release a dead session's claim
(`tk-queue release "<id>" --dir "<queue dir>"`), rewrite a legacy class
(`tk-queue edit "<id>" --dir "<queue dir>" --class AUTONOMOUS` — it replaces the whole class
VALUE, annotations included); re-run `pack` after any of these.

**The lane is elected twice, and the remote decides between the calls.** `pack` reads the queue,
never the forge, so ask the remote once per distinct Spec reference of the first report — lanes,
every `avulso (<ref>)` and every `esta é <ref>` exclusion alike — of the repository the items
LAND in (`[repo: …]`; the Spec names the TRACKER, routinely another repo). `<m>`, the reference's
issue half, is what identifies the branch:

```sh
git ls-remote --heads "<the item's repo address>" "refs/heads/spec/<m>-*"   # exit 0 and no line = free
```

A URL or a path, never a remote NAME (`origin` resolves against the queue's own clone and answers
a clean false negative), and read the exit code, not only the output — an unreachable host exits
128, and captured output turns it into "free". A branch that survived its merge still holds the
lane; the report names it, deletion as the repair. An item printed `[repo: ?]`, or with no address
you can supply, leaves the package saying so. Then call `pack` again with every hit —
`tk-queue pack --dir "<queue dir>" --spec-under-way "<repo>#<n>"`, repeatable — and cut from the
SECOND call's list: the lane passes to the deepest spec at the floor of two tickets.

**Cut** from the top of that list until the package fits one session — around 3–6 items or ~2h of
summed Effort, an opening bid step 6's measurement corrects; what multiplies a lane is the number
of correction cycles, not the size of the diff. Recount tickets per Spec among the survivors and
re-apply the floor (the recount only demotes; a spec below the floor takes the solo lane). A
package with an accumulated lane reserves two lines beside the lanes — the review at parity with
the summed lanes, and the tail as one suite plus the lane's N criteria and the merge of
`origin/main` — or its last third is unfunded.

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
the worktree per run below is the second line — a defence, not a check. A package that dies
holding claims leaves them behind: `tk-queue release "<id>" --dir "<queue dir>"` hands one back
without closing it, printing whose claim it drops.

Recount the floor against the CLAIMED items (demote only), then ask the remote once more — step
1's `git ls-remote`, for the lane's spec and every `avulso (<ref>)` alike — BEFORE creating
anything. A branch already there is a sibling running or a package that died: create nothing over
it, take that spec's tickets out on step 1's rung and release their claims. Only then create and
push the accumulated branch, in the repository the items land in — never the cwd (`<slug>`: the
spec's title, lower-cased, each non-alphanumeric run one hyphen):

```sh
git -C "<the lane's repo address>" worktree add "<path>/spec-<m>" -b "spec/<m>-<slug>" origin/main
git -C "<path>/spec-<m>" push -u origin "spec/<m>-<slug>"
```

**One lane, one address**: the `Repo:` field is stored as typed, so two spellings of one repo
are two addresses — where a lane's tickets disagree, the lane has no address and its tickets
leave on the no-address rung. The address names a repository, not a working tree: a URL runs in
its clone on this machine, and an item whose repository has no clone here leaves the package
undispatched, named with the reason.

**Explore the base ONCE, before the first ticket goes out.** One exploration run reads the
tree the lane's tickets name and writes its notes to `<notes dir>` — a scratch directory of
this session's own, OUTSIDE the repository, so the lane commits none of it and the tail
reviews none of it. The distilled contract below covers the ITEM; these notes cover the BASE,
and without them every implementer of the lane reads the same tree again at its own cost. A
package with no accumulated lane skips this: one run reads one base.

The lane is serial: each ticket dispatches into a worktree of its own, cut from
`origin/spec/<m>-<slug>` fetched at that moment, only after the previous ticket's cycle ends.
Both lines below are what put the upstream on the ticket's OWN branch: cut from the lane's
branch without `--no-track` it tracks THAT one, and a bare `push` then writes the ticket's work
in progress into the branch the pull request publishes — refused today only because
`push.default=simple` reads two different names, a defence `push.default=upstream` removes.

```sh
git -C "<the lane's repo address>" worktree add --no-track "<path>/T<id>" -b "spec/<m>/T<id>" "origin/spec/<m>-<slug>"
git -C "<path>/T<id>" push -u origin "spec/<m>/T<id>"
```

Solo items dispatch beside it, in series within one repository; neither lane passes the
local ceiling. An item too big for one subagent's context leaves the package carrying its
briefing (`../verify/SKILL.md` prescribes the form) and its ready-to-paste line.

Each run's prompt carries, produced here and never delegated back: the **contract block** pasted
verbatim from `../../bin/tk-contract --role <row>` — `implementer`, or `implementer-spec` on the
lane, whose `pr = none` cell is what keeps the run from opening the per-ticket pull request — and
the **item's distilled contract**: the item, the memory file behind its `[[slug]]` at one hop,
its handoff; context in none of the three is a missing handoff, named in its own line. A lane
run also gets the path `<notes dir>` of the exploration above, read and never re-run. A solo run
also gets its ticket reference for its PR's closing line, composed HERE by
`../../bin/tk-ticket-ref "<id>" --dir "<queue dir>" --closing-line`, which reads the owner from
the clone the item's **Repo:** field names — pass `--repo <clone>` when the item names none. Exit 3 is the item
that HAS no ticket; exit 1 is a refusal naming the defect and its remedy; exit 2 is a run that
could not be made at all. None of the three is a run dispatched without a reference. Count
each run by the venue signature it returns, never by the flag you passed. On a wave, step 4 —
`AUDIT.md` beside this file — stands between the claim and the first run.

**Done when:** every item is claimed or reported held elsewhere, the lane branch exists and is
pushed before its first ticket goes out, the base was explored once with its notes outside the
repository, and every run carries a generated contract block, that path, and a prompt
self-sufficient without the tracker.

## 4. Audit the spec and the tickets

A package whose items came from a spec and ticket set written in this flow — a **wave** — is
audited before any of it is implemented. The procedure is `AUDIT.md` beside this file: the
three lenses, one verifier per finding, the four outcomes and the REGRILL that halts the
package. Read it there, whole, and hand its block to step 6. Every `--criterion` the audit
reads is anchored by `../verify/SKILL.md`, *The anchor outlives the tree* — one of its three
rotten shapes — and this is where the wording is still cheap to change.

**Done when:** `AUDIT.md`'s own "Done when" holds — the block step 6 is owed names one of its
four states.

## 5. Verify every delivery

The ruler is the item's own criterion and the rite is `../verify/SKILL.md` — read it before the
first item closes. The caller re-runs the proof on the final tree, never taking the run's account
for it; an empty return is a failed attempt; the three attempts and four outcomes are verify's
own. An approved solo item leaves the queue here —
`tk-queue done "<id>" --dir "<queue dir>" --how "<pointer>"` — and an item verify turned into a
DECISION stays, carrying its handoff.

A lane item is verified BEFORE it reaches the shared branch — one cycle per item, every stage the
orchestrator's own work, in order:

1. **Confirm the invariant** in the item's worktree: `git status --porcelain` empty, HEAD equal
   to `@{u}`. A breach is repaired here — commit and push — and reported.
2. **Run the item's criterion AND the whole suite**, tailed, exit codes read from `PIPESTATUS`
   (`tail` hides them).
3. **Green is both.** Approved and proof-ready merge (the lane's PR is not `main`); failed 3×,
   rotten criterion and a red suite are red — a red suite spends one of the same three attempts.
4. **Merge with `--no-ff`, `T<id>` first in the title** — the merge commit is the user's
   `git revert -m 1` handle, the leading `T<id>` what the close and a resumed generation match
   on. A conflict here is a broken invariant, not a merge to resolve: abort, and the item ends as
   a DECISION (`--deferred afk`) naming its pushed branch and the two tips; the lane continues
   from its unchanged tip.
5. **Push the lane's branch** — the checkpoint of `WINDOW.md`'s invariant for the lane.
6. **On the FIRST green merge of the package, open the draft pull request**
   (`gh pr create --draft --base main`). The body is the orchestrator's and nobody else writes
   it: per closed item it gains `Fixes <owner>/<repo>#<n>`, one line per ticket; the spec is
   named WITHOUT a keyword, so only the user closes it. **Ask verdict 5 for that item HERE**,
   against the body just written — `../../bin/tk-closure-check "<id>" --dir "<queue dir>"
   --pr <n>` — and record its answer for the gate's digest. After stage 7 the item's
   **Ticket:** field has left the queue with it. The check then has no subject, and answers
   red for every item of the package.
7. **Close the item last** — `tk-queue done "<id>" --dir "<queue dir>" --how "PR #<n>"`, after
   the push and after the pull request exists: the push before the `done` is what lets a resumed
   generation recover either death shape without losing work or merging an item twice.

A red item never reaches the lane's branch and the lane does not halt for it: its DECISION names
its pushed branch, later tickets cut from the unchanged tip, and the report names it beside them.
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
   `spec/<m>/T<id>` — its worktree recreated as `RESUME.md`'s *Re-dispatch* does, the branch
   having outlived it —
   and merged into the lane again with `T<id>` leading the title. Committed on the lane instead
   it sits outside every merge the item owns, and the user's `git revert -m 1` of that merge
   leaves the correction behind, conflicting against code it no longer patches. A fix spanning
   items, or repairing the lane's own merge of `origin/main`, belongs to no item and stays on the
   lane's branch, named in the digest. A finding nobody here can close goes to the digest, and the pull request waits on
   it. *The fixer cap* decides how many correction cycles this review runs.
3. **The whole suite and every lane criterion, on the final tree**, tip and `origin/main` shas
   recorded for the digest's Tests line. A red criterion is reported with the merges that landed
   after its item, never repaired by reverting; the closed items stay closed.

Then mark the pull request ready and remove the lane's worktree — the gate's `--delete-branch`
fails on a branch still checked out.

**Done when:** every item carries one verify outcome with its evidence block, every lane item
reached the branch by a pushed `T<id>` merge before its `done`, verdict 5 was asked of each
while it was still open, and every red one is absent from
it, the tail ran its three steps on the final tree and left the pull request out of draft with
the worktree removed, and every claim left with its item or was released.

## 6. Measure, and hand the package to the close

Four numbers on one line — **planned × completed × wall clock × context at the cut**, the last from
`../../bin/tk-context` at that seam (no cut this generation: the predecessor's `--state` number;
none at all, `?`). Then the **sensor**: births per merged pull request — the queue IDs born in the
package (the age column of `tk-queue list`; highest − lowest + 1, one queue only, and a sibling's
IDs in the range count too) over its merged pull requests, with `pack`'s open count before and
after. The target is under 2, open not rising. One deviation line per
departure from the role table, and the audit's block. An unclosed item carries the first reason that
applies: **blocked** (another environment, "runs on: X"); **carried** under the dependency gate (a
sibling's claim, owner and moment), the lane gate (a spec's branch on the remote, the pull request's
number or the deletion repair), any other `pack` exclusion (its printed value, and whether it names
a defect in the item), or the effort gate (cut for size, with the ready-to-paste line that runs it).
Items verify ended at proof ready or DECISION owe nothing further.

**Done when:** the measurement and sensor lines, audit block and deviation lines are written, every
unclosed item carries its rung, and the unvisited items are handed over by exclusion.

## 7. Chain the afk wrap-up

Run `../wrap-up/SKILL.md` with its `afk` argument, executed FROM that file: both skills carry
`disable-model-invocation: true`, and reading the file is how the chaining honours the lock. The
close owns committing and pushing before any review, the five verdicts of safe-to-merge, which
items merge unattended, and the closing template.
**Done when:** the wrap-up reached its own "Done when" — or it did not run, and the report names
the step that stopped the package and the state the tree was left in.

## The fixer cap

**A tooling repo — one whose code handles no business data — gets ONE correction cycle per pull
request.** The cap counts per firing of the review, never for the life of the pull request. A review
re-fired whole by *A resumed generation starts here* carries its own cycle. That cycle is a single
`fixer` dispatch, never resumed: findings it leaves unclosed go to ONE item carrying its inventory. A
`fixer` whose batch touches a file outside the slice's diff stops and reports. Whatever a re-review
finds after that cycle enters the queue by `tk-queue add --dir "<queue dir>"`, class per the finding's
nature, as *A session finding, unattended* prescribes. The close's verdict 2 counts a finding queued
this way as handled, never as one no fixer could close, so the pull request does not wait on it.

## A session finding, unattended

Unattended, `../../reference/session-finding.md`'s ladder keeps three rungs. **Fix on the spot** —
a `fixer` under *The fixer cap*. **Queue with a gate** — `tk-queue add --dir "<queue dir>"` at the
moment of discovery. **Park** — a DECISION with `--deferred afk`, its branch pushed and its
handoff written. Either `add` is REFUSED at `max-open-items` past every flag: fold with
`edit --text` or `handoff`, never by closing one. Nothing is discarded, and the package never waits
on a parked finding.

At the close, never mid-package, ONE `AskUserQuestion` batches every parked DECISION; that
question and the close report are the same text. Portuguese, these labels verbatim:

- `O que é:` the item or pull request in plain words, never a bare `T123` or `#n`;
- `O que muda para você:` what each option means for the user;
- `Se você não responder:` the default the agent takes, and when.

**Done when:** every session finding carries its ladder rung in the close, the parked ones in one
question, with the veto `tk-queue cancel "<id>" --dir "<queue dir>" --why "<the veto>"`.