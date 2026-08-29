# The `afk` and `pack` arguments

Both arguments build the same **package** — the largest set of queue items this session can
run unattended. `afk` fires it with zero interaction: the user typed the command and left.
`pack` shows it once and waits for a single confirmation. Everything else is identical.

The session running a package is an **orchestrator**: it claims, dispatches, verifies and
closes, and implements nothing inline. Every run it dispatches takes its model, effort and
venue from the role table in `../../reference/subagent-policy.md` — which also fixes the
one-line format a departure from that table costs.

**Read `WINDOW.md` beside this file before anything below runs**, *A resumed generation starts
here* below included: a resumed generation composes its very first command out of that file's contents. It
holds what the package does when it runs out of window rather than out of work: the checkpoint
invariant, the handoff the quota wall demands and its six contents — plus the five an accumulated
lane carries, four of them new — the scope a resumed package is held to, why auto-continue covers
none of this, what the review lens costs the window and why its tail is what the wall cuts first,
the two vehicles that can open a successor generation, and the `--budget N` generations that carry
a package past the orchestrator's own context ceiling — with the seams that ceiling is read at,
the cut and the `pack` confirm among them. Those rules fire at moments the steps below
do not choose, which is why they are read up front rather than looked up under one.

## What is read, and when

Read this file **by section**, not end to end. Planning a package touches the spine, step 1 and
step 2; a session that took step 4's body before dispatching anything paid 222 lines for a step
it may never reach, and this file is ~87 KB read whole. Reading of that shape is what puts a
`pack` over the planning threshold with nothing dispatched (`WINDOW.md`, *The two planning
seams*). What a step defers is its BODY, never its
existence: the steps still run in order, and none is skipped for not having been read.

**The spine is this section and everything above it, plus `WINDOW.md` whole**, and it is read at package
open whatever the session goes on to do. It carries the rules that fire at moments the steps do
not choose: the quota wall and the handoff it demands, the checkpoint invariant, and the context
threshold at every seam — planning seams included, which is why a session that reads no step body
still holds the rule that stops it. Two more are this file's own: the orchestrator implements
nothing inline, and **it alone writes the queue** while the package runs — step 3, *The vehicle,
and who writes the queue*, carries the failure that rule prevents.

Then one section per step, read where the step is reached:

| At | What is read there |
|---|---|
| resuming a package | *A resumed generation starts here* — before step 1, and instead of it |
| step 1 | *1. Build the package*, and `tk-queue pack --help` |
| step 2 | *2. `pack` only: confirm* |
| step 3 | *3. Claim, then dispatch*, plus `../../reference/subagent-policy.md` and the palette in `../dispatch/SKILL.md` |
| step 4 | *4. Audit the spec and the tickets*, and the site's workflow mechanism in `~/.claude/tk/dispatch.md` |
| step 5 | *5. Verify every delivery*, and `../verify/SKILL.md` before the first item closes |
| step 6 | *6. Measure, and hand the package to the close* |
| step 7 | *7. Chain the afk wrap-up*, executed from `../wrap-up/SKILL.md` |
| a session finding, at any step | *A session finding, unattended* |

**A generation resuming a package that already holds a lane starts at *A resumed generation
starts here*, below, and not at step 1.** It builds no package: the one it inherits is already
built, and what it owes first is the tree.

## A resumed generation starts here

A generation opened by one of `WINDOW.md`'s two vehicles inherits a package mid-flight: the
handoff carries the items, the claims, the lane and the five contents `--state` carries for that
lane, and git carries whatever survived. It builds no package and pulls no new item — the
claims it inherited are the whole of its work, by `WINDOW.md`'s scope rule. This section runs
first and once, and only where the handoff names an accumulated lane; a handoff naming solo items
alone goes straight to step 3's dispatch — the dispatch alone, under the reading two paragraphs
below.

**A handoff a planning seam wrote is the third case, and this section is not its entry.** It
carries a package composed and never claimed (`WINDOW.md`, *The two planning seams*): no claim,
no branch, nothing in flight. Its successor runs step 3 **whole**, the claim included. Where it
enters is decided by the seam that ended its predecessor, which that handoff's `--state` names: a
`pack` stopped at the cut still owes its confirmation and enters at step 2; one stopped at the
confirm was fixed there already and enters at step 3. `afk` has no step 2 and enters at step 3
either way.

The order is fixed — **reset, draft, close, re-dispatch** — because each one reads a tree the one
before it settled. They are named rather than numbered: this file's own steps are numbered, and
two numberings over one page is how a reader lands on the wrong one.

**Read the handoff whole before the reset.** `tk-queue done` deletes the briefing of the item
it closes, and the wall anchors that briefing on the item that was in flight — which is exactly
the item the **close** below finds merged on the tip. Measured in this ticket's rehearsal:
`done T001` printed `handoff-T001.md removed`, and the re-dispatch would have read nothing. Nothing below
re-reads the file, so the whole of it is taken up front.

**What this section runs of step 3, and what it does not.** It runs step 3's **dispatch** — the
vehicle, the prompt, and the lane's serial order — and no other half of that step. It does not
claim: the items are this package's already, and a second `tk-queue claim` is refused even under
the SAME label — measured, `claim T001 --as afk-host` run twice answered `T001 is already claimed
by afk-host` at exit 1, so a generation that claimed would report its whole inherited package as
held elsewhere. It does not re-run step 3's `git ls-remote` check: the branch that check would
find on the remote is this package's own lane, and finding it there evicts the lane's tickets from
the package that owns them. It creates no branch, the lane's branch being what it inherited. Step
1's cut and step 2's confirmation are not its work at all.

**Two preconditions, before the reset can run.** The exit table at the end of this section grades
what the beats FIND; these are what makes a tree there to be found, and a row of that table is the
wrong home for them — measured, `git -C "<path>/spec-<m>" fetch origin` and
`git -C "<path>/spec-<m>" reset --hard "origin/spec/<m>-<slug>"` on a path that is gone both exit
128 with `fatal: cannot change to '<path>/spec-<m>': No such file or directory`, before any row is
consulted.

- **The lane's identity** — its repository address, `spec/<m>-<slug>`, its worktree path and its
  pull request's number — is the first content `--state` carries for a lane (`WINDOW.md`), and
  every command below is composed from it. Where the slug alone was lost,
  `git ls-remote --heads "<the lane's repo address>" 'refs/heads/spec/<m>-*'` names the branch;
  that is the fallback and not the contract. Where the address or the branch cannot be recovered
  at all, the lane takes the exit table's handoff-missing row and nothing below runs.
- **The lane's worktree.** `git -C "<the lane's repo address>" worktree list` names the worktrees
  git still knows. Where the lane's is gone, nothing is lost — the branch is on the remote — and
  it is recreated before the reset, with the report naming the recreation:

  ```sh
  git -C "<the lane's repo address>" worktree prune
  git -C "<the lane's repo address>" worktree add --track -B "spec/<m>-<slug>" "<path>/spec-<m>" "origin/spec/<m>-<slug>"
  ```

  **`--track -B` is not decoration.** Measured: `git worktree add "<path>/spec-<m>"
  "origin/spec/<m>-<slug>"` without it leaves a **detached** HEAD, and a commit made there reaches
  nobody. Its `git push origin "spec/<m>-<slug>"` then fails loudly with `error: src refspec
  spec/<m>-<slug> does not match any` where no local branch of that name exists, and is a silent
  exit-0 `Everything up-to-date` that pushes nothing where one exists at the remote's sha. The
  second shape is the dangerous one: it reports success while the remote's tip never moves.

**Reset** the lane's worktree to the pushed tip.

```sh
git -C "<path>/spec-<m>" fetch --prune origin
git -C "<path>/spec-<m>" reset --hard "origin/spec/<m>-<slug>"
```

**`--prune`, because a delivered lane leaves no branch behind.** `../wrap-up/SKILL.md`'s gate
merges the lane's pull request with `--delete-branch`, and a plain fetch never notices: measured,
after that deletion `git fetch origin` exits 0 and `git rev-parse "origin/spec/<m>-<slug>"` still
answers the stale sha, while `git fetch --prune origin` reports `- [deleted]` and the same
`rev-parse` then exits 128. Unpruned, this generation resets onto a ref for a lane already in
`main` and resumes it; step 5 stage 5 then re-creates on the remote the very branch the merge
deleted, carrying work `main` already holds. Pruned, a ref that survives IS a live lane, and its
absence is what the exit table's delivered row reads.

The pushed tip is the package's only record of the lane, so this discards whatever the predecessor
left unpushed — an item's merge, the tail's merge of `origin/main`, a `fixer`'s commit — and
discarding it is what makes this tree agree with what every later reader sees. The work behind a
discarded merge survives on the item's own pushed branch `spec/<m>/T<id>`, which the re-dispatch or step 5's
cycle merges again.

**Draft** — open the pull request where the tip carries a merge and the forge has none.

`gh pr list -R "<owner>/<code repo>" --state open --json number,headRefName --head
"spec/<m>-<slug>"` answers the second half, and `git -C "<path>/spec-<m>" log --merges --oneline
"origin/main..HEAD"` the first. **The range is part of that command, here and at the close.**
Unbounded, `log --merges` also lists `main`'s whole merge history once the tail has merged
`origin/main`, and no lane item put those merges there.

A tip carrying a `T<id>` merge with no pull request on it means the predecessor died between its
first push and its `gh pr create`. Open it with the command and the body of step 5
stage 6, which owns both; opening it here supplies only the moment, and every item the close writes
needs a `PR #<n>` to point at.

**Close** every item whose merge is already on the tip.

Read `git -C "<path>/spec-<m>" log --merges --oneline "origin/main..HEAD"` and take the leading
`T<id>` of each title — the position step 5 stage 4 puts it in for exactly this reader. **Where a
merge's title carries no leading `T<id>`, the close takes nothing from it and reads the next merge
in the list.** No lane item put that merge there: the tail's merge of `origin/main` is the one that
reaches this range, once a predecessor got as far as the tail. The same reading holds wherever this
file takes a `T<id>` from a merge title, the delivered row's `<mergeCommit>^1..<mergeCommit>^2`
range included. Then ask `tk-queue list` for each id, which answers both halves of the test on one
line: whether the item is still open at all, and whose claim it is under —
`T001  AUTONOMOUS  0d  <the item's text>  [claimed by <owner> since <moment>]`. An item still open
**that an inherited claim names** closes here with `tk-queue done "<id>" --how "PR #<n>"`, which is
a re-close and never a re-run, and an id that list does not show is closed already and takes
nothing. **The claim is the second half of the test because nothing else enforces it**: measured,
`tk-queue done` on an item claimed by another owner closed it at exit 0 with no warning. An id open
under somebody else's claim is a sibling's item, and closing it would take that item out of the
queue with no session alive to notice.

**Read the merges from the tip, never from the item→merge map.** The map stops at the last handoff
its writer got to and the tip does not, so the tip is the one that knows about a death between the
push and the `done` — the death the close exists for. Where the two disagree, the tip decides and
the report names the disagreement.

An item closed here whose section is missing from the pull request's body gets one, naming its
merge and saying that its evidence block died with the generation that verified it. The tail's
step 3 re-runs that item's criterion on the final tree, and that run is what the user's verdict
reads.

**Write a fresh handoff before leaving the close.** `tk-queue done` deletes the briefing of every
item it closes — measured, `done T001` printed `handoff-T001.md removed` — so a generation that
closed and then died leaves the queue holding claimed items and no briefing at all. That state is
the exit table's handoff-missing row: the package stops and the claims are held with nothing alive
to release them. `WINDOW.md` owns the rule that the handoff is refreshed at every seam, and this is
the seam where the artefact is destroyed, so the seam is named here. Run
`tk-queue handoff "<id>" --objective "..." --state "..." --blockers "..."` in that file's own form
— `<id>` being the item still in flight, or with none the head of what the claims still hold —
and put in `--state` the five lane contents rebuilt from the tip this beat just settled, not the
ones the dead handoff carried. Then run the `edit` that command prints on stderr, which is the
item's only discovery path to the briefing.

**Re-dispatch** the item in flight, from its pushed WIP branch.

**The handoff names the item, its branch and the stage — and the handoff is belief, the same way
the item→merge map is.** `WINDOW.md` refreshes it at every seam, so it is written AFTER stage 7's
`done`, and a death between the two leaves it naming an item already merged and closed. So ask the
tip and `tk-queue list` before dispatching anything: an id the close just closed, and any id
`tk-queue list` does not show open, is **not** re-dispatched whatever stage the handoff names.
Dispatched on that stale name, the item is implemented and merged a second time — reproduced, the
lane ended carrying two `T002:` merge commits of one name. Rehearsed through the order above, the
re-dispatch declined the stale id and the lane kept one merge per `T<id>`. No item closes twice,
since the queue refuses the second close (`T002 already left the queue`, exit 1); what the duplicate
destroys is the per-item reversal stage 4's `--no-ff` exists to buy, because `git revert -m 1` on
either merge leaves the other's copy of the work in. The tip is truth and the map is belief on this beat exactly
as on the close.

An id that survives that test is dispatched into a worktree **of** its own branch, never into one
cut fresh from the lane's tip, with the prompt saying what is already committed there — that is
what makes the run continue instead of starting the ticket over. Its cycle then runs from stage 1
of step 5, like any item's.

**Where the item's own worktree survived the death, dispatch into that one.** Step 5 removes an
item's worktree only when the item leaves the cycle, so a hard death leaves it in place with the
branch checked out. Fetch in it and put step 5 stage 1's two questions to it — a clean tree, and a
HEAD equal to its upstream — repairing a breach the way that stage prescribes, by committing and
pushing from here.

**Where it is gone**, cut a new one in the lane's repository:

```sh
git -C "<the lane's repo address>" fetch origin
git -C "<the lane's repo address>" worktree add --track -B "spec/<m>/T<id>" "<path>/T<id>" "origin/spec/<m>/T<id>"
```

Step 3's `-b` form is the wrong command here, because the re-dispatch's branch exists by
definition: measured in the clone the predecessor dispatched from,
`git worktree add "<path>/T<id>" -b "spec/<m>/T<id>" "origin/spec/<m>/T<id>"` returned
`fatal: a branch named 'spec/<m>/T<id>' already exists`. The `--track -B` form above returned
`fatal: 'spec/<m>/T<id>' is already checked out at '<the predecessor's worktree>'` while that
worktree was still registered — which is the surviving-worktree case above, answered by using that
worktree and never by `git worktree remove --force`. Force discards uncommitted work, and what
would make it look harmless is the checkpoint invariant: anything that matters is already pushed.
That is a claim stage 1's two questions VERIFY rather than a fact to assume, and where they fail
the repair is to push, not to force. A worktree git still lists whose directory is gone takes
`git worktree prune`, which discards nothing.

**The stage the handoff names decides whether a run is dispatched at all.** An item that had not
gone green still owes work, and the run resumes it from that branch. An item already verified
green owes none — it died at its merge or its push — so nothing is dispatched, and the item enters
step 5's cycle at stage 1, where the caller re-runs its proof before merging. Dispatching a green
item spends a whole run to re-deliver what its own branch already holds.

A branch with no commits of its own is a run that died before its first push, and two commands
say which shape it is:

```sh
git -C "<the lane's repo address>" ls-remote --heads origin "refs/heads/spec/<m>/T<id>"   # no line = never pushed
git -C "<the lane's repo address>" rev-list --count "origin/spec/<m>-<slug>..origin/spec/<m>/T<id>"   # 0 = pushed at the lane's tip, never committed on
```

Read the exit code of the first as well as its output, on step 1's rule: an unreachable host exits
128 and prints no line either. Nothing anybody could reach was lost in either shape, so the item is
dispatched the way step 3 dispatches a fresh ticket.

**Then the package carries on**: step 3's dispatch — that half of it alone, by the reading at the
top of this section — sends out what the claims still hold, in the queue's
order, and step 5's tail runs after the last of them. **The tail and its review are work remaining,
not work behind** — budget them here the way step 1's cut does, as two lines beside the items, and
a generation that runs out of window before them writes them into `--state` again rather than
dropping them.

### The three deaths this order survives

| The death | What recovers it |
|---|---|
| **Died before the push**, as step 5 stage 7 names it | the reset discards the merge; the item is still open and its own branch still pushed, so it re-enters step 5's cycle at stage 1 and merges once |
| **Died between the push and the `done`**, as that same stage names it | the close, reading the tip's merges |
| **Died during the tail** — the third, which stage 7 does not reach | the three questions below |

**A death during the tail is redone, not resumed.** What says where the tail stopped is the
handoff's tail state read against the tree the reset just produced — the handoff alone can be a step
behind, and the tree alone cannot say what a review returned. Three questions settle it:

- **Does the tip already carry `origin/main`?** `git -C "<path>/spec-<m>" merge-base --is-ancestor
  origin/main HEAD` exits 0 when it does, and the tail's step 1 then writes nothing — run it and
  git answers `Already up to date`. Exit 1 means main is ahead, whether because the merge never
  landed or because the reset discarded it or because main moved since, and step 1 merges it. **Exit
  0 is not "the merge commit exists"**: measured in this ticket's rehearsal, it exits 0 on a lane
  whose `origin/main` never moved and that never merged main at all. What the test settles is
  whether anything is left to merge, which is the only half that changes what runs.
- **Did the review report?** The handoff says, and nothing in the tree does. **A handoff silent on
  the review is read as a review that never reported**, since no tree can correct it and an
  unreviewed lane costs more than a lens fired twice. A review that never reported is re-fired
  whole; one that reported leaves its findings in the handoff, and what runs then is a `fixer` over
  the confirmed findings that are not yet on the tip — never the review a second time.
- **Did the criteria run finish?** It does not matter: it is redone whole. It measures the final
  tree, and either answer above can have moved that tree, so a half-finished run measured a tree
  that is gone.

Nothing in this section reopens an item, reverts a merge or rewrites anything pushed. The machine
reports and the user decides, here as everywhere on the lane.

### Every exit, and where it leaves the object

The rows grade **different objects** — a merge, the item in flight, the forge, the handoff, a
claim — so several apply to one lane at once and **every row that applies runs**. First-match
holds WITHIN one object and nowhere else: two rows about the same merge, or about the same handoff,
cannot both be the one. Worked case: a tip carrying no `T<id>` merge takes the first row, and the
same lane whose handoff names a stale tip takes the stale-handoff row as well. What the beats need
before they can run at all is not graded here — it is the two preconditions above.

| Exit | Where the object ends up | What runs next |
|---|---|---|
| `origin/main..HEAD` carries no `T<id>` merge at all | no item closes and no pull request opens | the re-dispatch; the lane's first green merge opens the draft, under step 5 stage 6 |
| A `T<id>` merge in that range for an item `tk-queue list` does not show | closed already; nothing is written | the next id in the merge list |
| A `T<id>` merge in that range for an id open under no claim of this package | the item stays open and the merge stays on the branch, both untouched | report it beside the lane — inside that range the merge is on the lane's own side, so a sibling pushed onto this branch and the tail's review reads its diff too. Unbounded, the same list also carries `main`'s merge history, whose ids no lane put there and which would take this row on a false diagnosis |
| A merge in that range whose title carries no leading `T<id>` — the tail's own merge of `origin/main` | no item closes and the merge stays where it is | the next merge in the list |
| The item in flight has no pushed branch, or none with commits of its own | the item is open and no tree holds its work | dispatch it fresh, as step 3 does a ticket |
| The draft pull request already exists | nothing to open | the close |
| The handoff names a tip older than the remote's — `git -C "<path>/spec-<m>" rev-parse "origin/spec/<m>-<slug>"` after the pruned fetch, against the sha the map is written under | the tip decides, and the item→merge map is the stale half | resume normally; the report names the gap |
| The handoff is missing, or the pruned fetch left no `origin/spec/<m>-<slug>` and the query below returns `[]` | the package cannot be resumed from here | stop; report the lane's branch, the claims still held and what the remote does show. The claims stay, so no sibling takes the items |
| The pruned fetch left no `origin/spec/<m>-<slug>` and the query below returns a row whose `state` is `MERGED` | the lane is delivered | close any lane item still open, taking its `T<id>` from `git log --merges --oneline "<mergeCommit>^1..<mergeCommit>^2"` — the lane's own side of the merge that landed it on `origin/main` — and report the pull request; the tail does not run |
| A claim the handoff lists is held by another owner — `tk-queue list` prints it as `[claimed by <owner> since <moment>]`, the same line the close reads | that item leaves this generation | report it as carried under the dependency gate (step 6) and resume the rest |

**The handoff-missing row and the delivered row are one observation with opposite outcomes** — no
`origin/spec/<m>-<slug>` after the prune — and one query separates them. They are about the same
object, so first-match would take the earlier one every time; the query is what puts the right one
first:

```sh
gh pr list -R "<owner>/<code repo>" --state all --json number,headRefName,state,mergeCommit --head "spec/<m>-<slug>"
```

`--state all`, not the `--state open` the draft beat uses, which returns `[]` for both. Measured
against this repository: over a merged lane's branch it returned
`[{"headRefName":"…","mergeCommit":{"oid":"3eedd21…"},"number":51,"state":"MERGED"}]`, and over
a branch that never existed it returned `[]`. `mergeCommit` is asked for here because the delivered
row reads its merges from it. Reading the two rows apart is what keeps a delivered lane from
stopping the package with its items claimed forever.

**Done when:** the lane's worktree exists and stands at the pushed tip of a branch a pruned fetch
still shows, the draft pull request exists where the tip carries a merge, every `T<id>` in
`origin/main..HEAD` belongs to an item the queue no longer shows open or to a row above, a fresh
handoff was written after the close and before the re-dispatch, the item in flight is dispatched
from its own branch — or was withheld because the queue no longer shows it open — and the report
names every exit this section took.

## 1. Build the package

`tk-queue pack` (`../../bin/tk-queue`) hands over the candidates: the eligible
items in the queue's own order, and every excluded item with the reason AND the
value that caused it. The filter is the script's — AUTONOMOUS, no Risk, **Env**
absent or naming THIS machine, unclaimed — and the shape it prints is documented
in `tk-queue pack --help`. What it deliberately does not decide is the cut.

**Re-triage before accepting an exclusion.** A Risk the triage finds OBSOLETE (it
names a branch since merged, a migration since run) is cleared on the spot with
`tk-queue edit "<id>" --risk none`, which is what keeps a stale line from excluding
the item forever; an Env that named a machine the item needed before it was
sliced goes the same way, with `--env none`. An item reported as claimed belongs
to another session — if that session is known to be gone, hand it back with
`tk-queue release "<id>"`, which prints whose claim it dropped. An item excluded
over a malformed field carries its repair in the `repairs:` block. Re-run
`tk-queue pack` after any of these.

An exclusion naming a class the filter does not recognise — one written in
another language, which queues older than the contract are full of — takes ONE
command: `tk-queue edit "<id>" --class AUTONOMOUS` reaches the field through the
variants the script already knows (`Classe`, `Esforço`, `Risco`, `Fonte`, …)
and rewrites it in the contract's own name, keeping the item's id, its place in
the order and every other field. What it replaces is the whole class VALUE, so
an annotation riding inside that value goes with it — read the line before
running it on an item whose class carries prose. Reach for `cancel` + `add` only where the field
chain itself cannot be read, and reach knowing the cost: a new id, the place in
the order lost, and any prose past the done-log's title cut gone with it. The
fold the `repairs:` block prints has a limit of its own — it is refused outright
when the item's text carries a field marker inside it.

**The lane is elected TWICE, and the remote decides between the two calls.** `tk-queue pack`
prints a lane beside every eligible item — `spec <ref>` for a ticket implemented on the
accumulated branch of its spec, `avulso (<ref>)` for a lone ticket of a spec under the floor of
two, plain `avulso` for an item that came from no spec at all — and it reads the queue, never the
forge. The one question it cannot ask is whether a spec is already being worked, so the
orchestrator asks the remote here and hands every answer back through a second `tk-queue pack`.

Ask once per DISTINCT Spec reference the first report names — the lanes, every `avulso (<ref>)`,
and the `esta é <ref>` of the lane rung's exclusions alike. The excluded ones are in that list
because the second call can ELECT one of them: a spec nobody asked about is a spec dispatched
over its own open branch. A ticket of a spec already under way is ineligible in either lane: the
solo one would open a second pull request over the same spec's work.

**Ask the remote for the BRANCH, not the forge for the pull request.** The branch is pushed the
moment the lane opens and the pull request only at the first green merge, so a check that asks
about pull requests is blind for the whole window between them — long enough for a sibling
package to build a colliding one. Ask it of the repository the items LAND in, which is the same
repository step 3 opens their worktrees in. The Spec reference names the TRACKER the spec is
filed in, and the two are routinely different repositories — so the address is a field of its
own, `Repo:`, and `tk-queue pack` appends it to the item's own line, after the ticket and
labelled: `… the first ticket of the spec  [ambiente#172]  [repo: https://github.com/owner/code.git]`.
The whole line's shape is in `tk-queue pack --help`, where the suite asserts it.

```sh
git ls-remote --heads "<the item's repo address>" "refs/heads/spec/<m>-*"   # exit 0 and no line = free
```

**A URL or a path, never a remote NAME.** A bare `origin` resolves against the cwd, and the
orchestrator's cwd is the queue's directory, which is routinely a clone of something else: run
from there, `origin` was measured returning exit 0 and no output — a clean false negative that
reads exactly like "no branch". `--repo` accepts only a named list of shapes and `pack` re-checks
it on the way out, so a `[repo: …]` you read here is already one of them — an address you
supplied yourself, for an item carrying none, answers to the same rule.
**And read the exit code, not only the output.** An unreachable host, a wrong URL and a failed
authentication all exit 128 with a `fatal:` line; a check whose output you capture into a
variable turns all three into "free" and admits the item.

**A branch that survived its merge still holds the lane**, because the remote cannot tell a
package being worked from one finished months ago and never deleted — the forge's default. The
answer belongs at the source, and it is written there: the gate of `../wrap-up/SKILL.md` merges a
lane's pull request with `--delete-branch`, so a lane that finished leaves no branch behind. What
still reaches this check is bounded and repairable — a branch merged before that rule existed, and
a merge the user made by hand without deleting — and it costs that spec every package until
somebody deletes the branch. So the report names the branch it found, with the deletion as the
repair, rather than letting the exclusion read as a live lane. Asking the question here instead
was measured costing more than it bought — it needs a clone whose trunk is current, a ref name
step 1 does not yet know, and an exit code of its own, and each of the three was a way to answer
"free" over live work.

**Two shapes of item carry no address to read.** `pack` prints `[repo: ?]` where the item's
`Repo:` field exists and no reader may use it — two in the chain, or a value the shape refuses —
and prints nothing at all where the item never had one. In both cases you supply the address
yourself, as every orchestrator did before the field existed; where you cannot name the code
repository, you cannot dispatch the item either, and it leaves the package saying so rather than
being checked against a guess. Either way the report names it, with the repair: `Repo:` is
written at birth and is no `edit` flag, so a wrong or missing one is `tk-queue cancel` and a
re-add carrying `--repo`. The address is stored exactly as typed, so ask the remote once per
distinct address — two spellings of one repository are two questions with one answer.

`<m>` is the **issue half** of the Spec reference — `171` out of `ambiente#171` — and it is what
identifies the branch, which is why the match is on the prefix rather than on the whole name.

**Then call `pack` a second time, carrying every hit.** The flag is `--spec-under-way
<repo>#<n>`, repeatable, and it is why there are two calls at all:

```sh
tk-queue pack --spec-under-way ambiente#171 --spec-under-way ambiente#144
```

The second call skips those specs when it elects the lane, so the lane passes to the next spec in
queue order that reaches the floor — routinely a spec the first call had excluded behind a lane
nobody could use. It takes every ticket of a skipped spec out of the package, whatever their
count, on the rung it already prints:

    lane de spec ocupada por ambiente#171; declarada em curso por --spec-under-way

**Cut from the SECOND call's list.** The first one elected a lane over a spec you now know is
open, so every line of its eligible block carries a lane that is out of date.

That value is what tells this rung apart from the identically worded one `pack` prints for a
second spec, whose value is `esta é <ref>`: that one read the queue, this one read the remote.
`pack` was told the spec is under way and never why, so the REPORT is where the branch is named,
with the pull request's number when
`gh pr list -R "<owner>/<code repo>" --state open --json number,headRefName` shows one on it.

One spec advances one package per human merge — that is what the rung costs, and naming it in the
report is what keeps the next cut from rediscovering it.

**Where that item lands in the close.** Step 6 groups the items a package did not close by
reason, and its ladder carries the rung: **carried** under the lane gate, with the branch as its
value. It was eligible, and it left over a lane held elsewhere rather than over anything wrong
with the item.

**Then cut.** Take the eligible of the second call in the order printed — priority IS the order of
the file, and `tk-queue bump "<id>"` is what moves an item to the top — then add
items while the package still fits ONE session: the parent only orchestrates and
verifies, yet each item still costs context to dispatch, monitor and check. Each
candidate line carries its Effort, raw and unsummed. Guidance: stop around 3–6
items or ~2h of summed Effort; leaving an eligible item out beats a session too
long to verify its own work.

Those numbers are an opening bid: step 6 measures what this package actually did, and the
next cut reads that line. The shapes behind them were measured against one 5-hour quota
window (2026-08-18) — a survey ≈5% of the window, one implement + review + fix lane
≈15–20%, a full-method second pair of eyes ≈8%. The audit of step 4 is a fixed cost on the
package rather than a per-item one, and the round it has measured is in that step.
What multiplies a lane is the number of correction cycles, not the size of the diff —
budgeting a lane by its diff was measured underestimating by ~3× (2026-08-19).

**Recount by spec after the cut, and re-apply the floor.** `tk-queue pack` computed every lane
over the whole eligible list; the cut is yours and happens afterwards, so an item printed `spec
ambiente#171` can reach a package holding the only ticket of that spec. Dispatched on the label it
was handed, that item opens a branch, a draft pull request and a three-step tail for itself —
the waste the floor of two tickets exists to prevent. Count the tickets per Spec reference among
the items that SURVIVED the cut. A spec that fell below two takes the solo lane, and where the
lane's spec fell below two the package has no accumulated lane at all. The reference is printed
whole, so the recount is arithmetic over the lines already in front of you — no second read of the
queue, no call to the forge.

**The recount answers for the CUT alone, and it only ever demotes.** Every promotion the remote
could earn was made by the second `tk-queue pack` call — before the cut, by the script that owns
the election — and what happens after the cut is arithmetic over FEWER items, which can only take
a spec below the floor. A package whose lane collapses here runs with no accumulated lane, and
the specs still excluded return in a later package on the rung that excluded them.

**Two lines of the cut are not items.** A package with an accumulated lane pays its review once,
over the accumulated diff, and pays a tail after its last ticket merges. Reserve both beside the
lanes rather than inside them: the review line at parity with the summed lanes — the 1.11:1
serialized ratio `WINDOW.md` measures, taken there as the planning number — and the tail line as
one suite, the N criteria of the LANE's items — not the package's, since a solo item pays its
own — and the merge of `origin/main`. Where a lane
item's Effort printed `?`, the sum is a floor and says so; a parity line over an unreadable Effort
is a number nobody can check. A cut that
funds only the lanes has hidden about half of what the package will spend.

The two lines fund one stretch of work: step 5's tail merges `origin/main`, runs that review over
the accumulated diff and then re-runs every lane criterion, in that order. They are two lines
because they are priced differently — the review at parity with the lanes, the rest as one suite,
N criteria and a merge — not because they happen apart. A package planned as though either were
free is a package whose last third is unfunded, and `../wrap-up/SKILL.md`'s per-item digest is
where the result reaches the user.

**Done when:** the package lists its items with the summed Effort (e.g. "4 items, ~1h45") and
the lane each one carries after the recount, the review line and the tail line stand beside them,
every exclusion carries either the command that cleared it or the one-line verdict that it
still holds, and every item left out is noted with the reason — the eligible ones dropped for
size, the ones a spec's branch on the remote took out, the ones whose code repository nobody
could name, AND the ones `tk-queue pack` excluded, which
are not eligible at all and would otherwise leave no trace anywhere.

## 2. `pack` only: confirm

One multiSelect `AskUserQuestion` listing the package items — the summed Effort in the
question, recommended composition stated — so the user unchecks what they don't want and
confirms once. The check IS the authorization. (`afk` skips this step: invoking it IS the
authorization.)
**Done when:** the confirmed package is fixed.

## 3. Claim, then dispatch

### The claim is the first line of the concurrent-session guard

Claim every item of the confirmed package before dispatching the first one:
`tk-queue claim "<id>" --as "<session-or-host label>"`, taken under the exclusive lock the queue
already holds. A second claim is REFUSED, naming the owner and the moment — and that refusal
IS the guard: the item leaves the package untouched and enters the report as held elsewhere.

It leads because the tree signals are blind exactly where the collision happens. A sibling
session working from the shared main tree appears in no `git worktree list` and carries no
`+` in `git branch -v`; on 2026-08-19 one such sibling ran `git pull --ff-only` and landed
the fast-forward on the branch another session had checked out. The tree is the second line
and it is a **defence**, not a check: dispatch every code-editing run into its own worktree,
so a sibling in the shared tree cannot move the ground under it.

A package that dies holding claims leaves them behind — `tk-queue release "<id>"` hands an item
back without closing it, and prints whose claim it dropped.

### The spec lane opens after the claims, and runs in series

The package can lose an item after step 1's recount — the user unchecks one on the `pack` path,
a claim comes back refused — so the floor is asked one last time here, against the items this
package actually holds: count the tickets per Spec reference among the CLAIMED, and a spec that
fell below two drops to the solo lane. It demotes and never promotes, for the reason step 1
gives. This recount is the LAST one, so the lanes it leaves are the ones step 6 hands over —
and a lane that collapsed here takes its two cost lines with it, since a package with no
accumulated lane pays neither the one review nor the tail.

**Then ask the remote once more, before creating anything.** Step 1 asked before the cut and the
claims, and a sibling package can push a spec's branch in the window between — so run step 1's
`git ls-remote` again, on the same terms, for every spec still in the package: the lane's and
every `avulso (<ref>)` one alike, since a solo ticket dispatched over a spec already under way
opens the second pull request the check exists to prevent. Asking BEFORE the branch is created is
what keeps the question answerable: asked after, the check reads the branch this step just pushed
and evicts the package's own lane, every run.

**A branch already there is a package still running, or one that died.** Either way this package
does not create it and does not push over it: force-pushing would destroy the merges a sibling
package is building on. Recovering a dead package's branch is a resumed generation's work, and
*A resumed generation starts here* is where that happens. Here, take that spec's tickets out of the
package on step 1's rung, with the branch as their value, and say in the report that the branch
was found and left untouched.

**The remote cannot tell a sibling's branch from this package's own** — it reads identically for
both — so nothing here asks it to. The discrimination is upstream of this check: a generation
resuming its own lane knows the branch from the handoff that named it and the claims it inherited,
and it never reaches this check, because *A resumed generation starts here* names the dispatch as
the only half of this step it runs. This check therefore runs for a
package being BUILT, where a branch on the remote is always somebody else's. A dead package's
claims outlive it by `WINDOW.md`'s rule, so the same items are refused on the item rung too, and
the two gates agree. **Release each one** — `tk-queue release "<id>"`, which prints whose
claim it dropped. They were claimed at the top of this step, and a claim outlives the package that
took it: an item that leaves still claimed is an item every later package is refused, with no
session alive to explain why.

**Only then create the accumulated branch**, and push it before anything is dispatched from it.
Create it IN the repository the items land in — the `[repo: …]` step 1 read from the lane's
tickets, never the cwd. The orchestrator's cwd is the queue's directory, and a `git worktree add`
run from there opens a branch of the wrong repository, which no later command reports:

```sh
git -C "<the lane's repo address>" worktree add "<path>/spec-<m>" -b "spec/<m>-<slug>" origin/main
git -C "<path>/spec-<m>" push -u origin "spec/<m>-<slug>"
```

**One lane, one address.** The tickets of a spec must name the same repository, and the field
is stored exactly as typed — so two spellings of one repo (`…/r.git` against `…/r/`) are two
addresses to every reader here. Where the lane's tickets disagree, do not pick one: the lane has
no address, and its tickets leave on the rung an item with no address takes.

**A URL is an address, not a working tree.** `git -C` needs a clone on this machine, so where the
field holds a URL the clone of it is what the command runs in. What the field settles is WHICH
repository, which is the half that was being guessed; a clone of it is still yours to have. An
item whose repository has no clone here leaves the package the way an item with no address does:
undispatched, named in the report with the reason.

`<slug>` comes from the spec's own title, lower-cased with each run of non-alphanumerics as one
hyphen. It is there for whoever reads `git branch`; `<m>` is what identifies the branch, which is
why every reader matches the prefix `spec/<m>-`. The push at creation is what makes the branch's
pushed tip exist from the first dispatch onward — the rule below and every later generation read
that ref, and a branch that lives only in this worktree is reachable by neither. Where the recount
left no spec at the floor, this section does not run: the package has no spec branch and every
item takes the solo lane.

**Each ticket of the lane starts from the branch's pushed tip.** Dispatch them one at a time, in
the queue's order, each into a worktree of its own on `spec/<m>/T<id>`, opened in the same
repository the lane's branch was created in, cut from `origin/spec/<m>-<slug>` as it stands at
that moment — `git fetch` first, and read the remote ref
rather than a local copy carried over from the previous dispatch. Serial dispatch is what gives
that tip its meaning: the ticket before it either went green, was merged onto the branch and
pushed, and the tip carries it, or it did not, and the tip is exactly where the previous dispatch
found it. That merge is the orchestrator's own, and step 5 writes the cycle it belongs to —
verify, merge, push, then close. What this step fixes is the starting point: read the pushed tip
at the moment of dispatch. An
implementer cut from a sibling's branch instead re-delivers work the tip already holds, and the
merge behind it applies that work twice.

**The lane is serial; the package is not.** The solo items dispatch beside it, under the rule
below.

### The vehicle, and who writes the queue

The mechanisms are the palette's, in `../dispatch/SKILL.md`; the choice among them here is by
SIZE, and that rule is this step's own. Default: one background subagent per item, in its own
worktree, opened in the repository that item's `[repo: …]` names. **Solo items** dispatch **in
series**, since items from one queue usually share a repo,
and in parallel only across disjoint repos or areas. **The spec lane** is serial by the rule
above whatever the areas say — its tickets share a branch, not merely a repository. Neither lane
goes past the local ceiling the contract block states, and that ceiling counts both together.
An item whose work does not fit one subagent's context is not squeezed into
one: write its briefing with `tk-queue handoff "<id>"` and dispatch it as a session of its own
— and where this machine cannot open one unattended, the item leaves the package carrying
that briefing, and its ready-to-paste line goes in the report.

**Only the orchestrator writes the queue.** `tk-queue` resolves which queue it is writing
from the cwd, and a run in a worktree has a different one: a subagent calling `done` there
writes into ANOTHER project's memory dir whenever that cwd collides with one, and reports
success for it. (With no queue at that path it fails loud instead — the collision is the
dangerous half.) Runs return evidence; the writing happens here.

### The prompt each run receives

Two parts, both produced here and neither delegated back:

- **The contract block**, pasted verbatim from `../../bin/tk-contract --role <row>`: the
  ceilings, that role's model/effort/venue, and the return contract it owes. The row for a run
  executing a package item is `implementer`, or `implementer-spec` where the item is on a spec's
  accumulated lane; any other run takes the row of the role it is
  dispatched as, and a role the table has no row for is a deliberate choice, logged like any
  other deviation. Generate it per dispatch rather than typing it from memory — a hand-written
  block is a fork of the policy. Pass `--fleet N` only when something else shares this
  machine's ceiling and told you N; alone, the whole ceiling is yours.
- **The item's distilled contract**: the interface the work must honour, its invariants, what
  the neighbouring slices consume from it. You hold the map hot and distilling costs once,
  where re-reading costs per dispatch — a prompt that says "read #X, #Y and #Z" bills that
  price on every run, and was measured starting an implementer at ~150k of context — the edge
  of the smart zone — before its first line of code (2026-08-19). Retransmit the item, the
  memory file behind its `[[slug]]` at ONE hop and its handoff; context in none of the three is a
  **missing handoff**, and the prompt says exactly that in its own line, because a gap named
  is cheap and a gap papered over with plausible synthesis sends the run onto invented ground.
- **The item's ticket reference, owner half included**, when the item names a ticket: the
  literal `<owner>/<repo>#<n>` the run is to write into its PR body's closing line. You compose
  it here — the item's `Ticket:` field carries `<repo>#<n>` with **no owner prefix**, by the
  queue's own rule, and the owner is the site's tracker (`git config tk.tracker`, whose value
  is `<owner>/<repo>`). The run cannot compose it: it reaches no tracker, which is the point of
  the line above. Handed a reference with no owner half, the keyword closes an unrelated issue
  of the repo the PR sits on, or nothing at all — so an item whose ticket you cannot resolve is
  dispatched saying so, and its run opens the PR with no closing line rather than a guessed one.
  On the spec lane the resolved reference stays HERE: the run opens no pull request, and the
  orchestrator is what writes the closing lines into the body of the lane's pull request.

**A spec-lane run takes the row `implementer-spec`, not `implementer`.** The two differ in one
cell — `pr = none` against `pr = opens` — and that cell is what decides whether the generated
block carries the "Closing the ticket" section at all. On this lane the orchestrator owns the
branch, the pull request and its body, so the run must not be told to write one; generating the
block from the right row is how it is not told, and it costs no deviation line, because the row
is the default rather than a departure from it. Overriding `implementer` in the prompt instead
was measured failing: the block states that where it and the surrounding prose disagree the block
wins, and the run opens the per-ticket pull request the lane exists to prevent.

The checkpoint invariant is on both rows, and it is load-bearing here: commit and push at every
north star, onto `spec/<m>/T<id>`. That pushed WIP is what a re-dispatch resumes from and what the
orchestrator reads when it verifies by artefact — work left in the implementer's worktree is
reachable by nobody, and a re-dispatch cut from the tip would start the ticket over.

**Count each run by the venue signature it returns, never by the flag you passed** — a
signature that came back local counts against the local ceiling. The measurement behind that
rule is the *Venue* section of that same policy file.

On a wave, the audit of step 4 stands between the claim and the first run: claim and write the
dispatches here, fire them after that step returns — so on a wave this step's "Done when" is
reached only once step 4 has returned and the runs it allowed have gone out.

**Done when:** every package item was claimed — all of them, before the first dispatch — or
reported as held elsewhere; the floor was recounted against the claims and, where a spec still
reaches it, its branch exists and is pushed before its first ticket goes out; and every dispatched
run carries a contract block generated for that dispatch and a prompt self-sufficient without the
tracker — a solo run carrying the ticket reference, owner half resolved here, that it writes into
its own pull request, and a spec-lane run carrying instead the branch it starts from, the branch
it pushes to, and the instruction that it opens no pull request.

## 4. Audit the spec and the tickets

A package whose items came from a spec and a ticket set written in this flow — a **wave** — is
audited before any of it is implemented: three adversarial lenses read the two documents, one
verifier tries to refute each finding, and every survivor leaves by one of four outcomes.
There is no code yet, so this reviews none: `/mattpocock-skills:code-review` still runs per
slice, and the conditional second pair of eyes still runs over delivered code.

**It sits between the claim and the first run.** Step 3 claims the whole package and writes
each dispatch; the first run is fired once this step returns, because a REGRILL halts the
package outright and an item whose ticket the audit rewrote has to be dispatched from the
rewritten one.

It runs by **default** on a wave. The orchestrator may skip it for a wave of at most two
tickets it judges **mechanical and fully specified** — the `implementer` row of
`../../reference/subagent-policy.md` uses those same words for a sonnet downgrade, and they
are no sharper there than here: no field in the queue measures them, so the skip is a
judgement, and the block step 6 is owed carries which two tickets were judged that way and
what was read to judge them.

**Skipping is a bet with no hedge**, and it is stated rather than papered over: the check that
would have found a REGRILL lives inside the step being skipped, so a small wave that skips
cannot discover that it should not have. What narrows the bet is only the two-ticket bound and
the requirement to write down the judgement.

A wave re-sliced after a REGRILL is the one case the bet is refused. Half of that is
mechanical and half is not, and the halves are worth separating. **Mechanical:** an open
REGRILL is a `DECISION`, and step 1's `tk-queue pack` prints every excluded item with the
value that excluded it, so an orchestrator that ran step 1 has the REGRILL in front of it.
**Not mechanical:** nothing ties that item to THIS wave. The handoff the REGRILL wrote is the
only carrier of the link, and a session that did not write it has nothing forcing it to look —
so a wave arriving with no handoff is treated as an ordinary wave, and this guarantee is only
as strong as that reading.

A package assembled from an aged queue rather than from a wave has no spec to read and the
audit does not apply — which is what the block says in that case.

### The workflow

Fire the site's **dynamic workflow** from this session — the palette row is in
`../dispatch/SKILL.md` and the site names the concrete mechanism in `~/.claude/tk/dispatch.md`.
Two departures from that row, both deliberate: it hands the workflow to the user, and the
audit is the one package step that fires one itself, this instruction being the opt-in that
allows it; and the situation it describes is a mass sweep over many items, which the audit is
not. What is borrowed is the mechanism — deterministic control and resume over a fixed graph —
never the row's situation. Running it here rather than inside
a subagent is what keeps the findings where the orchestrator can read them. Where the session
has no such mechanism, run the same graph as Agent-tool dispatches.

**Two paths, and concurrency is ruled differently on each — read the rule for the path you are
on**, because a reader who takes the ceiling rule as general fires three calls in parallel down
the fallback path:

- **On the dynamic workflow**, the prompt carries the ceiling in words — "use at most N
  agents" — with N no larger than the local ceiling in the contract block, and the ceiling
  decides how many finders run at once: three or more, all three together; two, a pair and
  then the third; one, one after another.
- **On the Agent-tool fallback**, the graph is dispatched **in series**, whatever the ceiling
  says. Serial is what that path IS, not a concession the ceiling extracted from it.

**The three lenses are not negotiable on either path.** A dropped lens is a round that did not
happen.

Each run takes its row from `../../reference/subagent-policy.md`: `audit-finder` for the
lenses, then `verifier-1`, `verifier-2` and `tiebreak`. The graph, in order:

1. **Three finders in parallel**, one per lens, each reading spec and tickets whole:
   **adversarial** — break what the spec promises, with the tickets as they stand;
   **blast radius** — which ticket touches a path that deletes or corrupts with no copy;
   **contract** — a promise in the spec that no ticket delivers.
   The lenses are fixed by measurement: on 2026-08-14 the grave findings came from lenses
   aimed at breaking a promise, and generic "review this" reading returned none. Two lines are
   fixed in every finder's prompt — **check each acceptance criterion against the decision it
   cites**, which is where the strongest findings of the round measured below came from, and
   **an empty return is a failure, never an approval: finding nothing, list the attacks you
   ran**, which is what makes a lens that found nothing usable as evidence.
   Each finder returns its findings in one fixed shape, so the dedup below compares like with
   like instead of inventing a format per round: per finding, a **one-line claim**; **where** —
   the document and the line it quotes verbatim; **why it breaks**, one line; and the **lens**
   that found it. Returning nothing, it returns the list of attacks instead.
2. **Dedup here**, by reading the three lists side by side; no agent for it. **`where` is a
   clue, not a key:** two lenses that hit one defect by different routes quote different lines
   of different documents — one the promise in the spec, the other the ticket that fails it —
   and a string comparison keeps them apart, turning corroboration into two findings. Read for
   overlap of the DEFECT, following each `where` to the passage. Where two claims describe one
   defect, record it once and keep both claims and both quotes in its text. This step is
   judgement; the fixed shape above only makes the judgement cheap.
3. **One verifier per finding**, carrying three fixed lines: its mandate is to **refute**, its
   default verdict is *refuted*, and it reads the **real sources** rather than the quotations
   the finding carries. That prompt broke 22% of the finders' findings on that same round.
   It also declares its own **confidence** — `high`, `medium` or `low`, those three words —
   and confidence is the escalation trigger, not severity: a `low` verdict goes to
   `verifier-2`, as does any confirmed finding whose correction would edit the spec or a
   ticket, and the two disagreeing goes to `tiebreak`. There, the four low-confidence verdicts
   were exactly the four the tiebreak decided — two of them real, two refuted.
4. A verifier that **writes** — runs the suite, mutates a source — is dispatched with
   `isolation: 'worktree'`, since a shared tree was measured contaminating reviewers of one
   another (2026-08-14).

**One question stays with the orchestrator rather than becoming a fourth lens: can the first
implement session START?** The three lenses read the two documents against each other, and
none of them asks whether the work can begin at all — on that round a code repo holding no
tracker configuration got past all three, and was caught outside the audit. Ask it once of the
wave, by naming what the first ticket's session needs before its first edit: the repo, the
tracker configuration in it, the credentials, the fixture its criterion runs against. A "no"
is a finding like any other and takes one of the four outcomes below — usually **resolve
here**, and **REGRILL** where the spec assumed the missing thing was there.

One round is measured (2026-08-19, run over this package's own spec and tickets): three Sonnet
finders, ≈280k tokens and 10.5 minutes, returned 11 findings with one of them reached by two
lenses; the verifier plus one effort-high tiebreak, ≈152k tokens and 10.6 minutes, confirmed 7
and refuted 2. It found one real REGRILL — a gap that the spec, its quiz and a human approval
had all let through. **Those minutes are a round with the finders in parallel.** Run in series
the token cost is the same and the wall clock is roughly three times it — derived from the
round's shape, not measured. That is one round and not a distribution, which is why step 6 adds this
package's.

### The four outcomes

Exactly one holds per surviving finding.

| Outcome | Holds when | What it emits |
|---|---|---|
| **Resolve here** | the correction fits inside the spec or the tickets and is unambiguous | the orchestrator edits them directly — editing the spec included, the delta being accepted practice — and records file, field, and what the text said before |
| **Backlog** | the finding is real and correcting it is work of its own | `tk-queue add` at the moment of the verdict, the gate named in the item's own text, exactly as *A session finding, unattended* prescribes below; one only the user can judge is a `DECISION` carrying `--deferred afk` |
| **Refuted** | the verifier broke the finding | one line naming the verifier and how it broke — the finding is gone, and the line is the whole record |
| **REGRILL** | the spec's own premise is what the finding hit | the package halts with no run fired, and the queue takes the decision instead of the work (below) |

**Resolve here** is not the *resolving on the spot* the session-finding ladder below forbids.
That ban is on new work — the hydra, three heads dying and six items born. This corrects the
very documents the audit was pointed at, before anyone works from them, and the work it
prevents is an implementer building from a document known to be wrong.

Every record in that last column goes into the **audit's block**, which is what this step
hands to step 6: one line per finding under its outcome — what was edited, what was queued,
what was refuted. That block is the only address they have, and a record kept in this step's
own reasoning reaches nobody.

*Refuted* is a verifier's verdict that the finding was never real, which is what separates it
from the **discarding** of the session-finding ladder below: that one is a human judgement an
unattended package does not have, and there a real finding nobody can weigh goes to
**backlog** instead.

### A rotten criterion is routed, not chosen

A ticket whose acceptance criterion measures something other than what the ticket promises
carries a **rotten criterion** — the term and its two shapes, *unsatisfiable by construction*
and *satisfiable but wrong*, belong to `../verify/SKILL.md`. Caught here it is the cheapest
finding of the round: the alternative is an implementer spending three attempts against a
broken ruler and the item ending at a DECISION anyway. It is a distinct object from that
file's **failed 3×** — a rotten criterion never executed against a real delivery at all.

Those two shapes say how the criterion is broken. What routes it here is a different
question — which of the two documents is wrong — and the answer is not a choice among the
four outcomes:

- the spec states the promise plainly and only the criterion misses it → **resolve here**,
  rewriting the criterion to measure the promise, recording both the old text and the new.
  It edits a ticket, so the rewrite goes to `verifier-2` **before it is applied**;
- the criterion and the spec agree, and together they miss what the work is for → **REGRILL**.
  Nothing ratified is left to measure against, so no rewrite here can be the right one.

A rotten criterion the verifier does not break stays out of **backlog**: a broken ruler left
standing in a ticket is what the next implementer measures itself against.

What none of this buys is **detection**. Nothing here fires on a rotten criterion by itself —
it is seen when the contract lens happens to compare a criterion against the promise, and the
evidence for it working is one round with one finding. Routing it is settled; catching it is
not, and a round that found none has not shown there were none.

### REGRILL enters the queue through its gate

```sh
tk-queue add "REGRILL: <the promise the audit could not close> — package halted before the first implement" \
  --class DECISION --deferred afk --effort "M (~40min)" \
  --criterion "B: the user re-grills the promise, and the wave is re-sliced from the spec that grill leaves"
tk-queue handoff "<id>" --objective "<what the re-grill has to settle>" \
  --state "<the finding, its verifier's verdict, and where the spec and the tickets stand>" \
  --blockers "<what the package stopped holding, and every claim it released>"
```

Every `<...>` above is a **metavariable**: substitute it before running, and paste nothing as
it stands. `<id>` is the id the `add` printed, and it is quoted for the same reason the prose
placeholders are — unquoted, a shell reads `<id>` as a redirect and the line dies before
`tk-queue` sees it.

**Then run the `edit` the handoff prints.** `tk-queue handoff` warns on stderr, at exit 0, that
the item does not point at `[[handoff-T0NN]]`, and prints the `tk-queue edit --text` that
repairs it, already quoted for the shell and already carrying `--force` where the link would
cross the field ceiling. Run it as printed: the item is the briefing's only discovery path, so
a REGRILL that skips this step parks a decision whose briefing nothing leads to.

`--deferred` is the gate: `--class DECISION` is refused without it, so a REGRILL that reached
the queue reached it carrying the record of why nobody could be asked.
`../../tests/test_afk_audit.py` lifts these commands out of THIS section, runs them against a
throwaway queue both as an argv list and **through a shell**, follows the printed `edit`, and
re-runs the `add` with `--deferred` removed to watch the refusal. It proves the recipe and the
gate. It proves nothing about whether this step ran — that is what the block owed to step 6
is for.

Then release what the package was holding, per step 3, and hand it to step 6: a halted package
still owes its measurement and its close.

A round can also **fail**: a lens came back empty without its list of attacks, or the
mechanism died before the lenses delivered. Re-dispatch that lens. Where it cannot be made to
run, the audit did not run — the block says so and the wave is unaudited.

**A round can also end PARTIAL, and this is the state that must not be called failed:** the
lenses ran and delivered real findings, and the verifier died — silently degraded venue is a
documented mode, which is why step 3 counts a run by the signature it returns. Re-dispatch the
verifier. Where it cannot be made to run, every finding left without a verdict goes to
**backlog** carrying the words *unverified by the audit*, because an unverified finding is
exactly a finding nobody here can weigh; the block reports the round as partial and says how
many findings had no verdict. Calling that round failed would be false — the lenses did run —
and destructive: it throws away findings that were produced.

**Done when:** the block step 6 is owed names exactly one of four states — the audit **ran**,
and every finding it kept carries one of the four outcomes with its verifier's verdict; or it
was **skipped**, with the judgement that skipped it; or it ended **partial**, naming how many
findings went to backlog unverified; or it **failed**, naming the lens that could not be made
to run. A clean round with no findings is the first state and says so in those words.

## 5. Verify every delivery

The ruler is the item's own criterion and the rite belongs to `../verify/SKILL.md` — read it
before the first item closes. What this step owes that file:

- **The caller re-runs the proof**, here, on the final tree — the one measurement the close
  displays rather than repeating. The run's own account of its work is an input to it and never
  a substitute: verify by artefact, not by summary. The spec lane runs that proof twice, and the
  earlier run comes first: the cycle below verifies each item BEFORE its merge, and that earlier
  run decides one thing only — whether the item enters the branch.
- **An empty return is a failed attempt.** A run that comes back with no evidence block did
  not deliver, however confident its prose, and the attempt counts toward the three.
- The three attempts, the four outcomes and the DECISION-plus-handoff a failure writes are
  verify's own; this step supplies the caller they are written for.

An approved item then leaves the queue here — `tk-queue done "<id>" --how "<pointer>"`, in the
form verify prescribes for carrying the evidence block — and an item verify turned into a
DECISION stays, carrying its handoff.

### The spec lane's item cycle: verify, merge, push, close

A solo item is verified on the tree its own pull request carries, and a red one harms nothing but
itself. An item on the **spec lane** shares a branch with every ticket after it, and with the pull
request the user judges. So it is verified BEFORE it reaches that branch. The lane runs one cycle
per item, and those four beats take the seven stages below. Step 3 dispatches the next ticket only
once that cycle has ended: serial order is what makes the branch's pushed tip mean "everything
verified so far, and nothing else". Every stage is the orchestrator's own work — verifying,
merging and pushing are commands, not judgement, so it runs them itself rather than dispatching a
run for them.

**1. Confirm the branch is what you will verify.** The run owed a push at every north star by the
checkpoint invariant, so ask its worktree the two questions that settle it:

```sh
git -C "<the item's worktree>" fetch origin
git -C "<the item's worktree>" status --porcelain      # no output
git -C "<the item's worktree>" rev-parse HEAD "@{u}"   # two identical lines
```

A dirty tree, or a HEAD ahead of its upstream, is a broken invariant, not a detail to work around.
What you would verify is then unreachable by every later reader, including the generation that
resumes this package. Repairing that breach is this stage's job, and not a duty taken from the
run: commit and push that worktree from here before any stage below runs, and say so in the
report. The run that owed it is finished, and re-dispatching it to press one button costs more
than the two commands.

**2. Run the item's criterion AND the whole suite**, in that worktree, tailing both. The tail is
what keeps N items from spending the orchestrator's context on N dumps, and it is also what hides
the exit code — `tail` returns its own — so read the command's status out of `PIPESTATUS`, bash's
array of the statuses of a pipeline:

```sh
<the item's criterion command> 2>&1 | tail -40; echo "criterion: ${PIPESTATUS[0]}"
<the repository's suite command> 2>&1 | tail -40; echo "suite: ${PIPESTATUS[0]}"
```

The suite runs beside the criterion because the branch is shared: an item can satisfy its own
criterion and break a neighbour's, and on this lane that break reaches the next ticket's starting
tree. Both runs are the orchestrator's own, here, under the rule this step opened with.

**3. Green is both, and green is what merges.** Verify's four outcomes decide it:
**approved** (a type-A criterion that passed) and **proof ready** (a type-B artefact with its
claim) are green, and both merge — a type-B item still never merges to `main` unattended, but the
lane's pull request is not `main` and waits for the user whatever it carries. **Failed 3×** and
**rotten criterion** are red. A red suite is red too, and it spends one of the same three
attempts rather than opening a second budget: the item goes back to the implementer either way,
with the tail as its context.

**4. Merge with `--no-ff`, `T<id>` first in the title**, in the lane's worktree:

```sh
git -C "<path>/spec-<m>" merge --no-ff "spec/<m>/T<id>" -m "T<id>: <the item's title>"
```

Neither half is decoration. Without `--no-ff` the first item fast-forwards, and there is then no
merge commit for the user to `git revert -m 1` by name — the whole reason each item enters by one.
The `T<id>` prefix is what a report, and a later generation reading `git log --merges`, matches on,
which is why it leads the title rather than sitting inside it.

**A conflict here is a broken invariant, not a merge to resolve.** The branch was cut from this
tip and nothing else has moved it, so a marker means the ticket started somewhere else. Abort with
`git merge --abort` and leave the lane where it was. The item is green but unmerged, so it ends
where a red one ends rather than at a `done`: `tk-queue edit "<id>" --class DECISION --deferred
afk`, with a handoff naming its own pushed branch and the two tips that would not merge. The lane
then continues from its unchanged tip, exactly as it does past a red item. The one place on this
lane where a marker is expected is the tail's merge of `origin/main`.

**5. Push.** That push is the checkpoint of `WINDOW.md`'s invariant for the lane itself, and it is
what makes every later step — the next dispatch, the close below, a resumed generation — read the
same tip:

```sh
git -C "<path>/spec-<m>" push origin "spec/<m>-<slug>"
```

**6. On the FIRST green merge of the package, open the draft pull request.** Not at branch
creation: the forge refuses a pull request with no commits between the branch and its base, so the
first merge is the earliest moment it can exist. It opens as a draft because the package fills its
body item by item and the review runs once, at the tail.

```sh
gh pr create -R "<owner>/<code repo>" --draft --base main \
  --head "spec/<m>-<slug>" --title "<the spec's title>" --body "<the opening body>"
```

**The body is the orchestrator's, and nobody else writes it.** That is why the lane's runs take
the `implementer-spec` row, whose `pr = none` keeps the closing section out of their contract
block. The body gains, per item closed, the closing line in the shape
`../../reference/subagent-policy.md` prescribes — `Fixes <owner>/<repo>#<n>`, owner half included,
one line per TICKET. The spec itself is named without a keyword: the user closes their own spec
when they judge it delivered, and a keyword on that reference would close it at the merge.

**7. Close the item last** — `tk-queue done "<id>" --how "PR #<n>"`, after the push and after the
pull request exists, with the evidence block in the body under that item's section. Last is the
point: the queue is the only record that survives this session, and the two ways a package dies
here resolve because the push precedes it.

- **Died between the push and the `done`.** The merge is on the pushed tip and the item is still
  open.
- **Died before the push.** The merge existed only in the lane's worktree, and the item is still
  open with its own branch still pushed. A death between the merge and the push is this same
  shape: the push is what makes the merge exist for anybody else.

Neither shape loses work and neither merges an item twice, which is what the order buys. **This
step names the two shapes and nothing more.** The procedure that recovers each of them — which
merges to read, the claim test the close applies before writing, and the handoff that follows it —
has ONE home, *A resumed generation starts here* at the top of this file; a second statement of it
here is a copy to go out of step with that one.

**A red item never reaches the lane's branch.** It ends the way any item ends today — three
attempts, then verify's DECISION carrying its handoff — with one addition: the DECISION names
the item's own pushed branch `spec/<m>/T<id>`, which is where its work stays. Nothing merges it,
so the lane's tip never carries it, and the next ticket is cut from a tip that never did. **The
lane does not halt for it**: the following tickets dispatch from that unchanged tip, so they are
cut from a tree without the red item's work, and the report names the red item beside them so the
reader knows what they did not have.

**The item's worktree goes when the item leaves the cycle** — merged green, or ended as a
DECISION, red or conflicted — and `git worktree remove` is the whole of it. Its **branch stays**
until the lane's pull request merges: the DECISION points at it, and a re-dispatch resumes from
it. A worktree that refuses to be removed is a dirty tree, which stage 1 should already have
caught; read what is in it and never reach for `--force`, which discards exactly the work the
invariant exists to keep.

### The lane's tail: `origin/main`, the review, then every criterion

The lane's last ticket merged and its branch is complete; the tail is what turns that branch into
a pull request the user can judge. It runs once per package, only where step 3's recount left an
accumulated lane, and every step of it is the orchestrator's own work in the lane's worktree.

**Every exit below ends in one place**: the pull request out of draft, carrying the per-item
digest of `../wrap-up/SKILL.md` with what the tail found. That file's gate decides the merge and
the tail never does. No item is reopened, no merge commit is undone and nothing already pushed is
rewritten — the machine reports and the user decides. What an exit changes is what the digest
lists, and nothing else: the steps below run in order whatever the one before them found. A lane
where no item ever went green has no pull request to ready — stage 6 of the cycle opens it at the
first green merge — so the tail does not run at all, and the report says the branch carries
nothing.

**1. Merge `origin/main` into the lane's branch.** This is the only place on the lane where a
conflict marker is expected: every item entered from a branch cut from this very tip, while main
moved on its own.

```sh
git -C "<path>/spec-<m>" fetch origin
git -C "<path>/spec-<m>" merge origin/main
```

- **Git merged it with no marker** — the merge stands, and so does a marker that lives only in a
  file some tool regenerates (a manifest, a lock file): re-run the tool that owns it and the
  marker is gone, which is a regeneration rather than a hand edit.
- **Any other marker** goes to a `fixer` (`../../reference/subagent-policy.md`) dispatched into
  that worktree with BOTH sides as context — the `T<id>` merge commit that wrote the lane's side,
  and main's commit — and it resolves and commits.
- **Then check the merge before pushing it.** `git -C "<path>/spec-<m>" grep -n '^<<<<<<< '`
  returns nothing and the tree is clean; marker-free, push it to `spec/<m>-<slug>`. Otherwise run
  `git -C "<path>/spec-<m>" reset --hard "@{u}"`, which discards the merge this step just made and
  nothing else — it was never pushed, no item's merge commit is inside it, and main's side sits on
  `origin/main` where it always was. The digest then carries the merge as outstanding, and step 2
  reads the same diff either way, since its three dots exclude main's side.

**2. Review the accumulated diff once, against the pull request's base.** Once for the lane, not
once per item: the base is the pull request's, so what the review reads is everything the user is
being asked to merge. The class of that diff picks the flow, under the site's CLAUDE.md:

- **prose an agent follows** — a skill, a CLAUDE.md, a runbook — takes the two axes alone, in one
  round: Standards against `writing-for-agents`, Spec against the package's own subset of tickets,
  the lane's and no others, each one's body AND comments;
- **code, or the data code writes**, takes the lens of `../review/SKILL.md` first, on the committed
  diff, and the two axes after — they read `base...HEAD`, so the lens's correction batch is already
  inside the diff they read.

A `fixer` applies the confirmed findings and pushes. Where a correction belongs to ONE item,
`T<id>` leads its commit title, so the user's revert of that item carries the fix with it. A
finding nobody here can close stops nothing: the tail hands it to the digest in the inventory
shape `../wrap-up/SKILL.md`'s gate names, and the pull request waits for the user on it.

**3. The whole suite and every criterion, on the final tree.** The last measurement before the
gate, and the one the digest displays. Run the repository's suite once, then each LANE item's own
criterion — all of them, not a sample — in the lane's worktree at its pushed tip, under this
step's opening rule: the caller re-runs the proof, and a run's account of it is never the proof.
Record the tip and `origin/main`'s sha beside the result; the digest's Tests line names both.

**The lane's items are already closed**, each by stage 7 at its own merge, and nothing here
reopens one. A criterion that goes red at this step is reported, never repaired by reverting: run
`git log --merges --oneline "<that item's merge>"..HEAD` — the `T<id>` merges that landed after
that item, and the merge of `origin/main` — and hand that list, in order, to that item's digest. A
red suite is the same shape at package scope: the tail reports it and the pull request waits. A
**type-B** criterion ends at proof ready here as it does inside the cycle, and the tail hands that
proof with its one-line claim to that item's digest. What each of those three does to a verdict,
and which acts on a red criterion are the user's, belong to `../wrap-up/SKILL.md`'s gate, and this
file states none of it a second time.

**Then mark the pull request ready for review, and remove the lane's worktree.** The gate merges
with `--delete-branch`, and that flag fails on a branch still checked out somewhere.

**Done when:** every package item carries exactly one verify outcome with its evidence block
in the PR body or on the item, every lane item that reached the branch did so by a `T<id>` merge
commit that was pushed before its `done` and every red one is absent from that branch, the lane's
tail merged `origin/main` or named it outstanding, reviewed the accumulated diff once, ran the
suite and every lane criterion on the final tree with the tip and main's sha recorded and left
the pull request out of draft with its worktree removed, every claim this package took has either
left with its item or been released, and `tk-queue list` shows exactly the items the run left open — every item it
closed gone from that list, every claim it did not close released — or the queue file itself is
gone, and the report says so instead of a criterion nobody could meet.

## 6. Measure, and hand the package to the close

Four numbers on one line, emitted here, where the package hands back: **planned × completed ×
wall clock × context at the cut** — items claimed, items that reached an approved outcome, the
time from first dispatch to last verdict, and the context this session had spent when it reached
the cut, read from the statusline at that seam (`WINDOW.md`, *The two planning seams*). They are what
stops the cut in step 1 from staying a guess: this package's line is the next package's
evidence. The fourth is what turns the ~100k planning threshold into a measured number rather
than a bid, and a generation that ran no cut — one resumed from a handoff — writes there the number its
predecessor left in `--state`, or `?` where the handoff carries none. The deviation lines are emitted beside
them, one per departure from the role table, in that file's format — a deviation with no line
is indistinguishable from a slip. The audit hands over its **block** here, whichever way it
went, in the four states step 4 defines: having **run**, one line per finding under its outcome
plus what the round cost in agents and wall clock; **skipped**, the judgement that skipped it;
**partial**, how many findings were queued unverified; **failed**, the lens that could not be
made to run. Those lines belong to the package and precede the close, whose own report follows
a template this file does not extend.

What the items the package did NOT close owe that template is their **reason**, since it
groups by outcome and by nothing else. Read them in order and the first that applies is the
reason — the convention `tk-queue pack` already uses for its own exclusions:

- an item bound to ANOTHER environment is **blocked**, marked "runs on: X": nothing here can
  execute it, and the user is the only path to the machine that can;
- an item another session holds is **carried** under the dependency gate — whose shape here is
  a sibling session holding it — and its reason is the owner and the moment, printed either by
  `tk-queue pack`'s exclusion or by the claim this package was refused;
- an item a spec's branch on the remote took out is **carried** under the lane gate, and its
  reason is that branch — with the pull request's number beside it where step 1's `gh pr list`
  showed one. Nothing is wrong with the item: it returns in the package after that lane's pull
  request merges and the merge deletes the branch. Where no pull request was found, the reason
  says so and names deleting the branch as the repair, since a branch merged and never deleted
  reads here exactly like a live lane;
- an item `tk-queue pack` excluded for anything else is **carried** too, recording the value
  the filter printed: it was never eligible at all, and "left out" alone reads as a size call
  nobody made. Where that value names a defect in the ITEM rather than a decision about it —
  a field the script cannot read — the reason says so, since "carried" alone reads as a
  deliberate hold and not as a repair waiting;
- an item left out for size is **carried** under the effort gate — cut in step 1, or too big
  to dispatch from here in step 3 — and it carries the ready-to-paste line that runs it:
  another `/tk:kickoff afk` for the cut, and for the one that needed a session of its own,
  the line step 3 already put in the report beside its briefing.

An item verify ended at **proof ready**, and one it turned into a **DECISION**, are carried on
what verify already wrote into them and owe nothing further here: the close is where a
proof-ready item becomes the DECISION that carries its digest reference.

The ladder covers what the package handled. The queue items it never visited are handed over
too, by class — and the classes are not a list to keep by hand: they are every class the step-1
filter refuses, which today is all four that are not AUTONOMOUS. No step of this run looked at
them, and a close shaped only around what the package touched is where they go silent.

**Done when:** the measurement line, the audit's block and the deviation lines are written, and every item the
package did not close carries the first rung that applies to it, and the items it never
visited are handed over by class.

## 7. Chain the afk wrap-up

The package ends by running `../wrap-up/SKILL.md` with its `afk` argument, executed **from
that file**: both skills carry `disable-model-invocation: true`, so an agent cannot fire
`/tk:wrap-up afk` as a command. Reading the file is how the chaining honours that lock
instead of routing around it.

What the close owns from there, and this file therefore does not restate: committing and
pushing before any review is dispatched, the five verdicts of safe-to-merge in their strict
unattended form, which items may merge unattended and which end at an open PR carrying their
proof, and the closing template that step 6's unclosed items enter by their reason.

**Done when:** the wrap-up reached its own "Done when" — or it did not run, and the report
names the step that stopped the package and the state the tree was left in.

## A session finding, unattended

A **session finding** is work this session discovered and did not come for; what separates it
from a pendency is the criterion of the item in hand, and the ladder that triages it lives in
`SKILL.md` beside this file. Unattended, that ladder has exactly one rung left: **queue it
with a gate.** `tk-queue add` at the moment of discovery, the gate named in the item's own
text — human decision · effort · external dependency — and a finding only the user can judge
arrives as a DECISION carrying `--deferred afk`.

The two rungs an unattended session does not have are the two that need a human. **Discarding**
is a judgement ("this will never happen") nobody here can make, so an unattended package
reports no discards. **Resolving on the spot** is the hydra's own fuel: three heads die and
six items are born, which is how a quick job became three weeks. So every finding this package
queued is listed in the close under the gate that kept it, for the user's **veto** on their
return — `tk-queue cancel "<id>" --why "..."` is that veto, and it is one command against a
finding that would otherwise have been lost to nobody's judgement.

**Done when:** the close carries one line per session finding, each matching an item this run
added to the queue with its gate named — none discarded, none resolved on the spot.
