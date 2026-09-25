# A resumed generation starts here

Read from the section of the same name in `AFK.md` beside this file, which a session reaches
through `SKILL.md`, *A session opening on a package handoff*. **Every step number below is
`AFK.md`'s.**

A generation opened by one of `WINDOW.md`'s two vehicles inherits a package mid-flight and builds
none: the claims it inherited are the whole of its work. It runs this file first, once, and
only where the handoff names an accumulated lane; a handoff naming solo items alone goes straight
to step 3's dispatch, and one a planning seam wrote — composed, never claimed — runs step 3 whole
(a `pack` stopped at the cut enters at step 2 first). Of step 3 this file runs the DISPATCH
alone: it does not claim (a second claim of an inherited item is refused, even under the same
label), does not re-run the `git ls-remote` check (the branch it would find is this package's own
lane), and creates no branch.

**Read the handoff whole before anything else** — `tk-queue done "<id>" --dir "<queue dir>"`
deletes the briefing of the item it closes, and nothing below re-reads the file. Then four beats
in order, each reading a tree the one before it settled:

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
with none — the tail's merge of `origin/main` — closes nothing), then
`tk-queue list --dir "<queue dir>"` per id. An item still open AND under an inherited claim
closes with `tk-queue done "<id>" --dir "<queue dir>" --how "PR #<n>"` — the claim is half the
test, since `done` on an item claimed by another owner succeeds silently, and that item is a
sibling's. The tip decides over the handoff's item→merge map wherever they disagree. Then write
a fresh handoff — the closes just deleted the old briefing — and run the `edit` it prints
(`../verify/SKILL.md`, *The item points at the briefing*).

**Re-dispatch** the item in flight from its pushed WIP branch, into its surviving worktree, else
`git worktree add --track -B "spec/<m>/T<id>" "<path>/T<id>" "origin/spec/<m>/T<id>"` — never
`git worktree remove --force`, which discards exactly what the invariant keeps. Never re-dispatch
an id the close just closed or `tk-queue list --dir "<queue dir>"` no longer shows open: on a
stale name the lane ends with two merges of one item, and `git revert -m 1` on either leaves the
other's copy in. An item the handoff shows green owes no run — it enters step 5's cycle at stage
1. A branch never pushed, or with no commits past the lane's tip, is dispatched fresh, as step 3
does a ticket.

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
