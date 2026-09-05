---
name: merge-gate
description: "The merge gate: the digest a pull request is judged on, and the five verdicts of safe-to-merge. Use when a close or a package tail has one to settle."
disable-model-invocation: true
---

# The merge gate — the digest and the five verdicts

The gate runs whenever an inventory holds a pending version-control action: uncommitted work,
an unpushed branch, a PR to open, a PR awaiting merge. Three consumers reach it — step 5 of
`../wrap-up/SKILL.md`, the lane's tail in `../kickoff/AFK.md`, and a merge settled outside
either, which is what invoking this skill directly is for. Its "Done when" is the caller's.

## The digest

**The digest is what the user reads instead of the diff**: it says WHAT is being merged
and whether it MAY be merged. Every PR in the gate gets one, before the menu — including a
PR the verdicts hold back, where the decision is whether the red is worth fixing now.

**In the attended gate, section 3 is PRINTED in the terminal before the menu** — three
lines per item in `../wrap-up/REPORT.md`'s `was/now/gain/risk` mould, sections 1, 2, 4 and 5 left to
the digest the menu carries. A digest sitting in the PR body does NOT discharge this —
that body is not the user's window. Copy the lines from it, name the PR, and carry the
full PR URL `https://github.com/<owner>/<repo>/pull/<n>`; recomposing from the
diff spends a window the user refuses to spend. Write the block for a cold reader: every
identifier resolves on first mention.

Its first half is written from the trail — the PR body, the issue it closes, the verdict
comments — in five sections:

1. **Pointers resolved.** Every citation by number arrives with the sentence it names. A
   verdict citing "recommendation 2" is undecidable while the statements live in another
   artefact: open it and quote the statement inline. A number whose list stays ambiguous
   is reported as unresolved, by its number.
2. **Proposal → verdict → why**, one row per decision, naming where the field contradicted
   the proposal and which side won.
3. **Before/after in practice** — what the rule or the code did, and what it does now.
4. **Choices without data** — the uncertainties the author left scattered, gathered here.
5. **Merge mechanics** — `../../bin/tk-collisions <ref> <ref> ...` merges every pair of
   open branches for real. The forge cannot answer this: its `mergeable` field is blind
   between two PRs. Exit 1 reports a colliding pair.

**A PR with no trail gets a DEGRADED digest, and says so in its first line** — a commit
straight to main, an issue nobody opened. Sections 1 and 2 have no source, so they are
named absent; sections 3 to 5 read off the diff and the repo, which are sources of their
own.

For any PR offered as "merge", the digest adds a per-file summary of the change, the forge
link, the evidence block from step 4 — and the five verdicts of **safe-to-merge**, one
line each:

| # | Verdict | Green when |
|---|---|---|
| 1 | **Tests** | the suite ran on the final tree and passed |
| 2 | **Review** | the review flow ran, and every finding is fixed, or accepted with its justification written down |
| 3 | **Criterion** | the item's criterion was re-run here and passed |
| 4 | **Reversal** | the way back is named in one line (revert, flag, restore) |
| 5 | **Closure** | the PR body carries a closing line under an English keyword the forge honours — `Fixes`, `Closes`, `Resolves` and their `fix`/`fixed` forms, that set and no other — naming **the ticket this item names**, owner half and all, no OTHER closing line in the body, and the PR targets its own repository's default branch. Owner-qualified, the keyword closes ACROSS repositories. `../../bin/tk-closure-check <id> --pr <n>` asks all five and names the ones that failed. The escape is the item naming no ticket, with the digest quoting it to show that — a verdict an agent can satisfy by asserting it is not a verdict |

Five green → merge is the recommended action. Any red → the digest says which one, and the
merge is not offered. A small diff (guidance: ≲150 lines) is still shown whole in the
terminal and a large one gets the link, but the diff is a courtesy: the five verdicts are
what RECOMMEND the merge, and the checked option is what authorizes it.

**Verdict 3 has a second shape: a type-B criterion** ends at proof ready, because the
verdict is the user's, GIVEN rather than inferred. The digest displays the proof and the
one-line claim it carries. The menu then offers the verdict as an option worded to say
what checking it means — "the proof settles it; merge", never a bare "merge". Verdict 3
stays amber until that option is checked, so it is never the recommended-first one.

## Verdict 5, read off the PR body alone

The closing keyword lives in the body alone: a ticket linked any other way stays open
behind a merged PR. **Run `../../bin/tk-closure-check <id> --pr <n>`**, which asks the
five below of the fetched body. Read them here, because the reds are what the digest
reports, and a line that is merely PRESENT proves none of the five. It reads the clone
from the item's own **Repo:** field, so pass `--repo <clone>` when the item names none:

1. **The keyword is one the forge honours.** The set is ENGLISH and closed —
   `close`/`closes`/`closed`, `fix`/`fixes`/`fixed`, `resolve`/`resolves`/`resolved`. A
   Portuguese `Fecha #n` is present, cites the right ticket, and closes NOTHING.
2. **The reference is this item's ticket.** Compare it against the one
   `../../bin/tk-ticket-ref <id>` composes — number from the item's own `Ticket:` field,
   repository and owner from the tracker, which is the PAIR and not two halves checked
   apart. A body copy-pasted from the previous slice carries a well-formed closing line
   for the WRONG ticket.
3. **The owner half is there, and it is the tracker's.** `<repo>#<n>` with no owner
   resolves against the repository the PR sits on, not the tracker — so it closes an
   unrelated issue of that repo, or nothing. An owner naming another account is present,
   well-formed and wrong — the case only an identity check sees. Owner-qualified, the
   keyword crosses repositories, by merge commit and by squash alike.
4. **No OTHER closing line is in the body.** The forge honours EVERY keyword and
   reference it finds, not the first one, so a second closing line closes a second ticket
   on merge — silently, and with no undo. An example line quoted in the body counts: the
   forge does not know it was an example.
5. **The PR targets its own repository's default branch.** That is the condition under
   which the forge fires the keyword at all: a stacked PR merged into its parent branch
   closes nothing, silently. Re-check after any retarget, a step this gate itself
   performs — it turns verdict 5 from green to red without touching the body.

**An item whose `Ticket:` no reader may use is RED, with its remedy named.** `pack` prints
`[?]` where the ticket goes. Provenance is add-only — no `edit --ticket` exists — so the
repair is `tk-queue cancel <id>` and a fresh `add` carrying the right reference. Until
`../../bin/tk-ticket-ref <id>` runs clean the item has no closing line to dispatch with.

## The menu, and what stays behind

**Review fixes rewrite the PR body**, in the same breath as the fix commit: a body still
describing the version before the fixes tells the reviewer what the branch no longer does.

**The question opens with what merges** — one clause per item, identifier resolved, before
any verdict or mechanics. That block scrolls; the question stays under the cursor.

Then ONE multiSelect `AskUserQuestion` with the actions, recommended first — the check IS
the authorization. Execute what was checked, following the project's conventions
(required trailer lines; on the default branch, branch first). Every unchecked action enters the queue as a DECISION
item via the full `add` line, since `--effort` and `--criterion` are required:

```
tk-queue add "<the action>" --class DECISION --deferred "<why it waits for the user>" \
         --effort "<S/M/L + estimate>" --criterion "<A: a command | B: the user's verdict>"
```

A merge carries its digest reference (forge link + review status); any other action
carries the branch/paths involved. It is deferred by choice, not by omission.

**Merging a stack, in this order:** retarget each child PR onto the new base BEFORE
deleting the base branch — deleting it first CLOSES the child — and remove the worktrees
of the branches in play before the merge round, since `--delete-branch` fails on a branch
that is still checked out somewhere.

## A package's accumulated lane: one pull request, one digest per item

`../kickoff/AFK.md` hands this gate a single pull request carrying N tickets, each of them
entering the branch by its own `T<id>` merge commit. One pull request, so the five trail
sections are written once, over the package — and N item digests, because what the user
judges is each item. The five verdicts split accordingly: two over the package, three
per item.

| # | Verdict | Scope | What that item's digest shows |
|---|---|---|---|
| 1 | **Tests** | the package | the suite ran on the branch, not on main: `suite green on <branch> at <tip>, origin/main at <sha>` |
| 2 | **Review** | the package | the one review of the tail's step 2, over the accumulated diff against this pull request's base |
| 3 | **Criterion** | the item | that item's own criterion, re-run on the final tree at the tail's step 3 |
| 4 | **Reversal** | the item | that item's `T<id>` merge commit, by sha and title: `git revert -m 1 <sha>` is the way back |
| 5 | **Closure** | the item | the closing line naming that item's ticket, under the five checks above — one line per ticket, one `tk-closure-check` run per item |

**Verdict 1 names the tree it ran on and where main stood.** The two shas separate a
measurement of what the merge will produce from an older one: the tail merged
`origin/main` before it ran anything, and where it left that merge outstanding, the tree
it read is behind main — which the digest says first, not last.

**`gh pr merge --merge` is a precondition of this merge, and the digest states it as
one.** A squash or a rebase collapses the N merge commits into one, and verdict 4 dies
with them. `--delete-branch` rides with it: step 1 of `../kickoff/AFK.md` reads the remote
for a spec's branch to decide whether that lane is free, so a branch left behind takes its
spec out of every later package. Where the user merges by hand, deleting the branch is
part of the merge, and the digest says so.

**Merge this pull request before the package's solo ones.** `tk-collisions` measures the
pair — this branch against each solo branch of the same package — because all were cut
from the same `origin/main`. Order matters beyond the collision: verdict 1 ran on a tree carrying `origin/main` as it
stood at the tail, so anything merged to main ahead of it leaves that measurement stale.
The remedy is to re-run the tail's merge and its step 3.

**Three shapes end at the same place: this pull request waits for the user, and nothing is
reverted.** Each keeps something different in the digest:

- **A criterion red at the tail's step 3** — the digest lists, in order, the `T<id>`
  merges that landed after that item and the merge of `origin/main`, because a revert of
  that item passes through every one of them.
- **A type-B criterion** — verdict 3 stays amber under the rule above, and the digest
  carries the proof with the one-line claim it was given.
- **A finding no fixer could close** — the digest carries the finding's inventory: what it
  is, where it sits, and what closing it would take.

**The three acts that follow are the user's, and the digest names them as the user's**:
revert the item by the name of its merge commit, drop that item's closing line from the
body so the merge does not close a ticket the revert emptied, and `tk-queue add` the item
back into the queue. Re-running the tail is an interactive request of the user's
too.

## The strict form (unattended)

`afk` runs this gate with no menu, and hardens it:

- **Commit and push before the review; merge after it.** Commit the work to a branch —
  never the default one — and push BEFORE dispatching any review, so a death on the quota
  wall leaves nothing uncommitted. Fix the findings in a follow-up commit, push again, and
  open the PR — or rewrite the body of the one already open — so the body describes the
  branch as it now stands and carries the evidence block.
- **The digest goes into the PR body**, because an unattended session has nobody at the
  gate to read the terminal. A PR the strict verdicts keep from merging carries it there
  too, and its DECISION item points at it as the digest reference.
- **Verdict 2 hardened: every finding FIXED under the fixer cap, QUEUED or PARKED,
  zero accepted** — accepting a finding is human judgment, and those three rungs
  (`../../reference/session-finding.md`) are where one goes instead. A parked finding
  reaches the user in the close's single question. It defers this pull request only
  where it is also a finding no fixer could close. Three cases bind what an
  unattended session may merge, each checked by itself:
  - **A type-B criterion** — verdict 3 cannot turn green without the user, so the item
    ends at an open PR carrying its proof and waits.
  - **A repo whose default branch is consumed as it lands** — a marketplace serving it
    live, a boot script reading it — merges only with the user. Those repos are named in
    the site extension (`~/.claude/tk/wrap-up.md`); a merge decided from a machine with no
    such file, or no such list, is deferred: an unattended merge is authorized by a list
    that was READ, never by the silence of a file that was missing.
  - **A package's accumulated lane** merges as a merge commit or not at all —
    `gh pr merge --merge --delete-branch`, under the precondition its section states. A
    criterion red at the tail's step 3, or a finding no fixer could close, defers the
    whole pull request with its per-item digest; nothing is reverted here, and closed
    items stay closed until the user puts one back.
- Whatever is not merged enters the queue as a DECISION with its digest reference ready.

**Done when:** every pending version-control action was executed or recorded as an
explicit DECISION — none merely implied. Every PR in the gate had its digest before the
menu, its five trail sections present or named absent, each citation-by-number resolved
or named unresolved, and its collision with the other open PRs run for real rather than
read off the forge, and an attended gate printed section 3 and the PR URL. A package's
accumulated lane carried one digest per item, its verdicts split package/item and its
`--merge --delete-branch` precondition stated. Every merged PR's body describes what it
merged, and the user has the summary — what changed, what was verified, what was deferred.
