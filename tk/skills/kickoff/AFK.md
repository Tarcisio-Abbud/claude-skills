# The `afk` and `pack` arguments

Both build the same **package** — the largest set of queue items this session can run unattended.
`afk` fires it with zero interaction; `pack` shows it once and waits for one confirmation. The
session running a package is an **orchestrator**: it claims, dispatches, verifies and closes, and
implements nothing inline. Every run takes its model, effort and venue from the role table in
`../../reference/subagent-policy.md`, which also fixes the one-line format a departure costs.
While the package runs the orchestrator ALONE writes the queue: `tk-queue` resolves its target
from the cwd, and a run calling `done` from a worktree writes into another project's memory dir
whenever that cwd collides with one.

**Read `WINDOW.md` beside this file before anything below runs** — the quota wall and the handoff
it demands, the checkpoint invariant, the context threshold at every seam, the five `--state`
contents of an accumulated lane, the two vehicles that open a successor generation, `--budget N`.
Those rules fire at moments the steps below do not choose. Read this file by section, never end
to end: what a step defers is its BODY, not its existence. A session finding, at any step, takes
*A session finding, unattended* below.

## A resumed generation starts here

A generation opened by one of `WINDOW.md`'s two vehicles inherits a package mid-flight and builds
none: the claims it inherited are the whole of its work. It runs this section first, once, and
only where the handoff names an accumulated lane; a handoff naming solo items alone goes straight
to step 3's dispatch, and one a planning seam wrote — composed, never claimed — runs step 3 whole
(a `pack` stopped at the cut enters at step 2 first). Of step 3 this section runs the DISPATCH
alone: it does not claim (a second claim of an inherited item is refused, even under the same
label), does not re-run the `git ls-remote` check (the branch it would find is this package's own
lane), and creates no branch.

**Read the handoff whole before anything else** — `tk-queue done "<id>"` deletes the briefing of
the item it closes, and nothing below re-reads the file. Then four beats in order, each reading a
tree the one before it settled:

**Reset.** Where the lane's worktree is gone, recreate it: `git worktree prune`, then
`git worktree add --track -B "spec/<m>-<slug>" "<path>/spec-<m>" "origin/spec/<m>-<slug>"` —
without `--track -B` the HEAD is detached and its push can report `Everything up-to-date` while
the remote never moves. Then:

```sh
git -C "<path>/spec-<m>" fetch --prune origin
git -C "<path>/spec-<m>" reset --hard "origin/spec/<m>-<slug>"
```

`--prune`, because the wrap-up gate merges with `--delete-branch` and a plain fetch keeps the
stale ref — unpruned, this generation resumes a lane already in `main`. Whatever the reset
discards survives on the item's own pushed branch `spec/<m>/T<id>`.

**Draft.** Read `git -C "<path>/spec-<m>" log --merges --oneline "origin/main..HEAD"` (the range
is load-bearing — unbounded, the list carries `main`'s own history) against
`gh pr list --head "spec/<m>-<slug>"`: a `T<id>` merge on the tip with no pull request means the
predecessor died before its `gh pr create` — open it with step 5 stage 6's command and body.

**Close** every item whose merge is on the tip: the leading `T<id>` of each merge title (a title
with none — the tail's merge of `origin/main` — closes nothing), then `tk-queue list` per id. An
item still open AND under an inherited claim closes with `tk-queue done "<id>" --how "PR #<n>"` —
the claim is half the test, since `done` on an item claimed by another owner succeeds silently,
and that item is a sibling's. The tip decides over the handoff's item→merge map wherever they
disagree. Then write a fresh handoff — the closes just deleted the old briefing — and run the
`edit` it prints (`../verify/SKILL.md`, *The item points at the briefing*).

**Re-dispatch** the item in flight from its pushed WIP branch, into its surviving worktree, else
`git worktree add --track -B "spec/<m>/T<id>" "<path>/T<id>" "origin/spec/<m>/T<id>"` — never
`git worktree remove --force`, which discards exactly what the invariant keeps. Never re-dispatch
an id the close just closed or `tk-queue list` no longer shows open: on a stale name the lane
ends with two merges of one item, and `git revert -m 1` on either leaves the other's copy in. An
item the handoff shows green owes no run — it enters step 5's cycle at stage 1. A branch never
pushed, or with no commits past the lane's tip, is dispatched fresh, as step 3 does a ticket.

Then the package carries on: step 3's dispatch sends what the claims still hold, and step 5's
tail runs after the last of them — budget both as work remaining. A death during the tail is
redone, not resumed: merge `origin/main` where `git merge-base --is-ancestor origin/main HEAD`
exits 1; a handoff silent on the review means the review is re-fired whole; the criteria run is
redone whole either way.

The exits grade different objects, so every row that applies runs. Handoff missing, or no
`origin/spec/<m>-<slug>` after the prune while `gh pr list --state all` returns `[]`: stop and
report the branch and the claims — they stay held, so no sibling takes the items. The same absent
ref with a `MERGED` row: the lane is DELIVERED — close its open claimed items from the merge
commit's own `<mergeCommit>^1..<mergeCommit>^2` merges, and the tail does not run. A claim held
by another owner: that item leaves this generation, reported under the dependency gate. Nothing
here reopens an item, reverts a merge or rewrites anything pushed.

## 1. Build the package

`tk-queue pack` (`../../bin/tk-queue`) hands over the candidates: eligible items in queue order,
every exclusion with the value that caused it, each item's LANE, Ticket and `[repo: …]` — filter
and line shape in `tk-queue pack --help`. What it does not decide is the cut. Re-triage before
accepting an exclusion: clear an obsolete Risk or Env on the spot
(`tk-queue edit "<id>" --risk none`), release a dead session's claim (`tk-queue release "<id>"`),
rewrite a legacy class (`tk-queue edit "<id>" --class AUTONOMOUS` — it replaces the whole class
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
`tk-queue pack --spec-under-way "<repo>#<n>"`, repeatable — and cut from the SECOND call's list:
the lane passes to the next spec at the floor of two tickets.

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

**Claim every item before dispatching the first** — `tk-queue claim "<id>" --as afk-host`. A
second claim is REFUSED naming the owner, and that refusal IS the concurrent-session guard: the
item enters the report as held elsewhere. The claim leads because tree signals are blind to a
sibling in the shared main tree; the worktree per run below is the second line — a defence, not a
check. A package that dies holding claims leaves them behind: `tk-queue release "<id>"` hands one
back without closing it, printing whose claim it drops.

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

The lane is serial: each ticket dispatches into a worktree of its own on `spec/<m>/T<id>`, cut
from `origin/spec/<m>-<slug>` fetched at that moment, only after the previous ticket's cycle
ends. Solo items dispatch beside it, in series within one repository; neither lane passes the
local ceiling. An item too big for one subagent's context leaves the package carrying its
briefing (`../verify/SKILL.md` prescribes the form) and its ready-to-paste line.

Each run's prompt carries, produced here and never delegated back: the **contract block** pasted
verbatim from `../../bin/tk-contract --role <row>` — `implementer`, or `implementer-spec` on the
lane, whose `pr = none` cell is what keeps the run from opening the per-ticket pull request — and
the **item's distilled contract**: the item, the memory file behind its `[[slug]]` at one hop,
its handoff; context in none of the three is a missing handoff, named in its own line. A solo run
also gets its ticket reference for its PR's closing line, composed HERE by
`../../bin/tk-ticket-ref <id> --closing-line`, which reads the owner from the clone the item's
**Repo:** field names — pass `--repo <clone>` when the item names none. Exit 3 is the item
that HAS no ticket; exit 1 is a refusal naming the defect and its remedy; exit 2 is a run that
could not be made at all. None of the three is a run dispatched without a reference. Count
each run by the venue signature it returns, never by the flag you passed. On a wave, step 4
stands between the claim and the first run.

**Done when:** every item is claimed or reported held elsewhere, the lane branch exists and is
pushed before its first ticket goes out, and every run carries a generated contract block and a
prompt self-sufficient without the tracker.

## 4. Audit the spec and the tickets

A package whose items came from a spec and ticket set written in this flow — a **wave** — is
audited before any of it is implemented; a package assembled from an aged queue has no spec to
read, and the block owed to step 6 says so. Skipping is allowed only for a wave of at most two
tickets judged mechanical and fully specified — a bet with no hedge, stated in the block with
what was read to judge it — and a wave re-sliced after a REGRILL refuses the bet.

Fire the site's dynamic workflow from this session (`~/.claude/tk/dispatch.md` names the
mechanism; the Agent-tool fallback runs the same graph in series). **Three finders**, one per
lens — **adversarial**, **blast radius**, **contract** — each checking every acceptance criterion
against the decision it cites; an empty return is a failure, never an approval — finding nothing,
a lens lists the attacks it ran. Dedup here, by the DEFECT and not the quoted line. Then **one
verifier per finding**, mandate to refute, default verdict refuted, declaring
`high`/`medium`/`low` confidence: `low`, or a correction that edits spec or ticket, goes to
`verifier-2`; disagreement to `tiebreak`; a verifier that writes gets `isolation: 'worktree'`.
Rows: `audit-finder`, `verifier-1`, `verifier-2`, `tiebreak`. One question stays with the
orchestrator: can the first implement session START — repo, tracker configuration, credentials,
the fixture its criterion runs against?

Exactly one outcome per surviving finding: **resolve here** — the correction fits the spec or the
tickets, the orchestrator edits them recording what the text said before (correcting the audited
documents, not the resolving the session-finding ladder forbids); **backlog** — `tk-queue add`
with the gate named, as *A session finding, unattended* prescribes; **refuted** — one line naming
the verifier and how; **REGRILL** — the spec's own premise is hit, and the package halts with no
run fired. A **rotten criterion** (term: `../verify/SKILL.md`) routes by which document is wrong:
the criterion alone misses the promise → resolve here, through `verifier-2` before it is applied;
criterion and spec agree and together miss → REGRILL.

```sh
tk-queue add "REGRILL: <the promise the audit could not close> — package halted before the first implement" \
  --class DECISION --deferred afk --effort "M (~40min)" \
  --criterion "B: the user re-grills the promise, and the wave is re-sliced from the spec that grill leaves"
tk-queue handoff "<id>" --objective "<what the re-grill has to settle>" \
  --state "<the finding, its verifier's verdict, and where the spec and the tickets stand>" \
  --blockers "<what the package stopped holding, and every claim it released>"
```

Every `<...>` is a metavariable — substitute before running, `<id>` being the id the `add`
printed; the quoting is load-bearing, since a shell reads a bare `<id>` as a redirect. **Then run
the `edit` the handoff prints** (`../verify/SKILL.md`, *The item points at the briefing*),
release what the package was holding per step 3, and hand the halt to step 6.
`../../tests/test_afk_audit.py` proves this recipe and its gate; whether the step ran is what the
block is for.

**Done when:** the block step 6 is owed names one of four states — **ran**, each finding under
its outcome with its verifier's verdict; **skipped**, with the judgement; **partial** — the
lenses delivered and the verifier died: re-dispatch it, else every unverdicted finding goes to
backlog as *unverified by the audit*, counted; or **failed** — a lens nobody could make run, and
the wave is unaudited.

## 5. Verify every delivery

The ruler is the item's own criterion and the rite is `../verify/SKILL.md` — read it before the
first item closes. The caller re-runs the proof on the final tree, never taking the run's account
for it; an empty return is a failed attempt; the three attempts and four outcomes are verify's
own. An approved solo item leaves the queue here — `tk-queue done "<id>" --how "<pointer>"` — and
an item verify turned into a DECISION stays, carrying its handoff.

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
   named WITHOUT a keyword, so only the user closes it.
7. **Close the item last** — `tk-queue done "<id>" --how "PR #<n>"`, after the push and after the
   pull request exists: the push before the `done` is what lets a resumed generation recover
   either death shape without losing work or merging an item twice.

A red item never reaches the lane's branch and the lane does not halt for it: its DECISION names
its pushed branch, later tickets cut from the unchanged tip, and the report names it beside them.
The item's worktree is removed when it leaves the cycle (`git worktree remove`, never `--force`);
its branch stays until the lane's pull request merges.

### The lane's tail

Runs once per package, where an accumulated lane survived, in the lane's worktree. Every exit
ends in one place — the pull request out of draft, carrying `../wrap-up/MERGE-GATE.md`'s per-item
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
   findings and pushes, `T<id>` leading a fix that belongs to one item; a finding nobody here can
   close goes to the digest, and the pull request waits on it. **A tooling repo — one whose code
   handles no business data — gets ONE fixer round per pull request, here and at the close's
   review alike**: whatever a re-review finds after that fixer enters the queue by
   `tk-queue add`, class per the finding's nature, as *A session finding, unattended*
   prescribes, and no second fixer runs in this package. A repository handling business data is
   uncapped.
3. **The whole suite and every lane criterion, on the final tree**, tip and `origin/main` shas
   recorded for the digest's Tests line. A red criterion is reported with the merges that landed
   after its item, never repaired by reverting; the closed items stay closed.

Then mark the pull request ready and remove the lane's worktree — the gate's `--delete-branch`
fails on a branch still checked out.

**Done when:** every item carries one verify outcome with its evidence block, every lane item
reached the branch by a pushed `T<id>` merge before its `done` and every red one is absent from
it, the tail ran its three steps on the final tree and left the pull request out of draft with
the worktree removed, and every claim left with its item or was released.

## 6. Measure, and hand the package to the close

Four numbers on one line — **planned × completed × wall clock × context at the cut**, the last
read from the statusline at that seam (a generation that ran no cut writes its predecessor's
number from `--state`, or `?`). Beside them, the deviation lines — one per departure from the
role table; a deviation with no line is indistinguishable from a slip — and the audit's block.
Items the package did not close carry the first reason that applies: **blocked** (bound to
another environment, "runs on: X"); **carried** under the dependency gate (a sibling's claim,
with owner and moment), the lane gate (a spec's branch on the remote, the pull request's number
or the deletion repair beside it), any other `pack` exclusion (its printed value, and whether it
names a defect in the item), or the effort gate (cut for size, with the ready-to-paste line that
runs it). Items verify ended at proof ready or DECISION owe nothing further. The queue items no
step visited are handed over by class — every class the step-1 filter refuses.

**Done when:** the measurement line, audit block and deviation lines are written, every unclosed
item carries its rung, and the unvisited items are handed over by class.

## 7. Chain the afk wrap-up

Run `../wrap-up/SKILL.md` with its `afk` argument, executed FROM that file: both skills carry
`disable-model-invocation: true`, and reading the file is how the chaining honours the lock. The
close owns committing and pushing before any review, the five verdicts of safe-to-merge, which
items merge unattended, and the closing template.
**Done when:** the wrap-up reached its own "Done when" — or it did not run, and the report names
the step that stopped the package and the state the tree was left in.

## A session finding, unattended

The ladder is `../../reference/session-finding.md`, and unattended it has one rung: **queue with
a gate** — `tk-queue add` at the moment of discovery, the gate in the item's own text, a finding
only the user can judge entering as a DECISION with `--deferred afk`. No discards and no
resolving on the spot — the two rungs that need a human, the second being the hydra's own fuel.
Every finding queued is listed in the close under its gate for the user's veto,
`tk-queue cancel "<id>" --why "<the veto>"`.
**Done when:** the close carries one line per session finding, each matching a queued item with
its gate named — none discarded, none resolved on the spot.
