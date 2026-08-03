# The `afk` and `pack` arguments

Both arguments build the same **package** — the largest set of queue items this session can
run unattended. `afk` fires it with zero interaction: the user typed the command and left.
`pack` shows it once and waits for a single confirmation. Everything else is identical.

## 1. Build the package

Eligible: items triaged **AUTONOMOUS** that carry **no Risk line**. Order by
impact/urgency, then add items while the package still fits ONE session: the parent only
orchestrates and verifies — yet each item still costs context to dispatch, monitor and
check. Guidance: stop around 3–6 items or ~2h of summed Effort; leaving an eligible item
out beats a session too long to verify its own work.
**Done when:** the package lists its items with the summed Effort (e.g. "4 items, ~1h45"),
and every eligible item left out is noted with the reason.

## 2. `pack` only: confirm

One multiSelect `AskUserQuestion` listing the package items — the summed Effort in the
question, recommended composition stated — so the user unchecks what they don't want and
confirms once. The check IS the authorization. (`afk` skips this step: invoking it IS the
authorization.)
**Done when:** the confirmed package is fixed.

## 3. Execute

The parent is an **orchestrator**: it dispatches, watches and verifies — it implements
nothing inline.

- **Concurrent-session guard:** before any subagent touches a repo, check
  `git worktree list` (session ids appear in worktree paths) and the `+` marks in
  `git branch -v`. Another live session in the repo → the item stays in the queue,
  untouched, and enters the report.
- One background subagent per item, **in series** — items from one queue usually share a
  repo. Parallel only when two items touch disjoint repos/areas. A code-editing item runs
  in an isolated worktree.
- Pick each subagent's model by the task's nature: mechanical, well-specified work → a
  cheaper model; judgment work → the parent's model; in doubt, the stronger one.
- **Verify by artifact, not by summary:** read the diff / run the tests / check the output
  before marking an item done and dispatching the next. Resolve each item on the spot via
  `tk-queue done <id> --how "<pointer>"` (never hand-edit the queue files — contract in
  `SKILL.md`).

**Done when:** every package item is verified-done or reported-skipped, and the queue
reflects it.

## 4. Report

The user returns to ONE message: (a) what was done, with the verifying evidence; (b)
eligible items left out for size — the ready line to run them is another `/tk:kickoff afk`;
(c) DECISION/BLOCKED/EXTERNAL items untouched, as in a normal kickoff close. Settle any
remaining queue changes through `tk-queue` (`add`/`edit`/`done`/`cancel`) last.
**Done when:** the report covers (a)–(c) and `next-steps.md` matches the post-run queue.
