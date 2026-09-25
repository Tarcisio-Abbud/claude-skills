# The lane contract — what one lane implementer is handed

A **lane** here is one branch, one worktree, one repository, ONE pull request, and items that
touch no file any other lane touches. It is not the accumulated spec lane of `AFK.md` step 5,
where serial tickets share one branch and the orchestrator merges each of them itself: this
lane has one implementer, it opens its own pull request, and it merges nothing.

`AFK.md` step 3 reaches this file when the package's lanes are disjoint in that sense. The
implementer is handed the block under *The dispatch prompt*, filled in; everything above that
block is what the implementer reads on arrival, and every rule here is written down because a
run that lacked it lost work.

## Inputs, read in this order

1. This file, whole.
2. **`<items file>` — the full text of the lane's items, in a file OUTSIDE the queue.** The live
   queue is off limits to a subagent: the site's hook refuses even the READ, so an item whose
   text nobody copied out is an item the implementer cannot see. Never run `tk-queue` with a
   writing subcommand — `add`, `edit`, `done`, `cancel`, `claim`, `handoff`, `migrate`, `bump`.
   The orchestrator owns the queue.
3. **`<brief file>`, when the lane carries one.** Where the human delegated a design decision to
   `/tk:second-opinion` in `once` mode, the verdict is the implementation **BRIEF**, and the
   brief is what the lane implements — the item's own statement stays as history. Say in the
   commit body where the two differ. The delegation merges nothing and decides no merge: the
   pull request still waits for the user's OK.
4. **`<notes dir>` — the base notes**, written by the one exploration `AFK.md` step 3 ran. Read
   them instead of re-reading the tree; the notes exist so the tree is read once for the package.
5. The repository's own rules where they exist in the worktree — `AGENTS.md`, `CLAUDE.md`,
   `CODING_STANDARDS.md`, `CONTRIBUTING.md` — and `../../reference/slice-rules.md`.
6. For a ticket the lane closes: `export GH_CONFIG_DIR="<the gh config dir>"`, then
   `gh issue view "<n>" -R "<owner>/<repo>" --comments` — body AND comments.

## The worktree is cut from `origin/main`, never the live clone

Two clones on this machine are read LIVE by every session at once, so a checkout in either one
changes what those sessions run. The lane works in a worktree and touches neither.

```sh
git -C "<the lane's repo address>" fetch origin
git -C "<the lane's repo address>" worktree add "<path>/<lane>" -b "lane/<lane>" origin/main
git -C "<path>/<lane>" push -u origin "lane/<lane>"
```

The worktree is cut from `origin/main` — from the branch of the lane it stacks on, where the
package's topology says so, and then from nothing else. When the orchestrator pre-created it,
`cd` into it and skip the recipe.

**One worktree per lane branch, for every role.** A run dispatched onto a lane carries no
`isolation: 'worktree'`. The harness would cut a second worktree, and a `git checkout -B` there
sidesteps git's own refusal to check one branch out twice. The second checkout moves the ref
under the first, whose index then shows the second checkout's commits reversed as staged work.
The reviewer works in the implementer's worktree (`REVIEW-CONTRACT.md`, input 4).

**A scratchpad of its own per lane.** Mutation logs, suite output and drafts go to
`<scratch dir>`, a directory this lane alone writes. One shared scratchpad cost 20 minutes on
2026-09-06: two lanes wrote one mutation log and each truncated the other's.

## Per slice: one slice = one commit, pushed

One item, or one fusion of items, is one slice. Work through them in the order the items file
gives.

1. **Read the item and the code it names.** Item text goes stale, and the code wins; the commit
   body says what was stale.
2. **Write the proof first.** For code that is the test. For prose an agent executes, it is the
   repository's own check that pins the prose — a grep-anchored test, or the size lock
   `tk-prune-measure` reads.
3. **Implement, and let no scope grow.** An adjacent defect goes to the implementer's report and
   to the pull request's *Achados não tratados* section, never into the diff and never into the
   queue.
4. **Run the suite detached, and wait for it in the FOREGROUND.** Keep `<rc>` and `<log>` in
   your scratchpad. Start `rm -f <rc>; (<the suite command>; echo $? > <rc>) > <log> 2>&1 &`.
   Wait with `timeout 590 sh -c 'until [ -s <rc> ]; do sleep 10; done'`. While the wait
   exits 124, re-issue it. Then read `<rc>`. A mutation run, only on a slice that touched an
   anchor, is `timeout 590`, `tk/tests/mutations.py` one `--shard K/4` per call. Each wait and
   each mutation call sets the Bash `timeout` parameter to its 600000 ms cap.
   Never end the turn waiting on a notification: two runs that did returned no pull request and
   no comment. Four live lanes stretch a 2-minute suite to 708 s, past the cap; a wait that
   gives up reports NOT-RUN under a green check.
5. **Commit, and push the commit.** Title `<type>(<scope>): <what>`, body naming the item ids and
   the stale facts corrected, ending with the trailer
   `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>` and `Claude-Session: <session URL>`.
   Push after every commit. In the three quota walls this contract was written under, no commit
   was lost and every uncommitted change was: work that was not pushed did not happen.

## The lane's end: one pull request, never merged by the agent

1. **Open ONE pull request for the lane**, base `main`, not draft. The body is written in
   Portuguese for a cold reader who was not in the session: one section per slice — item ids,
   what changed, how it was verified, what was stale — a section **Achados não tratados** with
   one line per defect seen and not fixed, a section **Risco** where the change writes a
   user-data directory or runs on every session, and the trailer
   `🤖 Generated with [Claude Code](https://claude.com/claude-code)` with `<session URL>`.
2. **Write that body with `gh api -F body=@<file>`**:

   ```sh
   gh api "repos/<owner>/<repo>/pulls/<n>" -X PATCH -F "body=@<abs path to the body file>"
   ```

   `gh pr edit --body` fails on this account against a deprecated Projects API, and `gh api -f`
   writes the literal path instead of the file's contents. The `@` form is `-F` only.
3. **Never merge.** No `gh pr merge`, no local merge into `main`, no branch deletion. The merge
   is the user's, through `../merge-gate/SKILL.md`.
4. **Report to the orchestrator**, at most 40 lines, in Portuguese: the full pull request URL;
   per item DONE, PARTIAL with the reason, or NOT DONE with the reason; the suite numbers; the
   achados não tratados, one line each; and the decisions a human might have taken differently,
   each with the alternative.

## Hard rules

- No new queue items, and no queue writes of any kind.
- No writes to auto-memory, to the wiki or to the vault.
- No `git pull` and no checkout in the live clones; no merge; no branch deletion.
- A criterion that cannot pass from this container is reported as unsatisfiable here, with the
  reason, and never faked. Deliver the rest of the item.
- Ask nobody. Where two readings differ materially, take the one closer to the item's stated
  criterion, say so in the commit body, and go on.

## The dispatch prompt

The block the orchestrator pastes, filled in. It is short because this file carries the rules:
what the prompt adds is the lane's addresses.

```
You are the implementer of lane <lane>, package <package>. You work alone; nobody is watching.
Contract: <path to>/tk/skills/kickoff/LANE-CONTRACT.md — read it whole first; it binds you.
Items: <items file>, their full text. The live queue is off limits, reads included.
Brief: <brief file> — where it differs from an item's statement, the brief is what you implement.
Base notes: <notes dir>, written once for this package. Read them; do not re-read the tree.
Worktree: <path>/<lane>, branch lane/<lane>, cut from origin/main and already pushed.
Suite: <the suite command>, detached and waited on in the FOREGROUND; mutation only on a
touched anchor, `timeout 590` per call; both as per-slice step 4 says.
Scratchpad: <scratch dir>, yours alone.
Contract block, pasted verbatim from tk-contract --role lane-implementer: <the block>
One slice = one commit, pushed. Scope does not grow: an adjacent defect is a line of your report.
At the end: ONE pull request, body in Portuguese with "Achados não tratados". Never merge.
Report back: the pull request URL, per item DONE / PARTIAL / NOT DONE, the suite numbers, the
achados não tratados, and the decisions a human might have taken differently.
```
