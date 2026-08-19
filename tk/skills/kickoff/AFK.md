# The `afk` and `pack` arguments

Both arguments build the same **package** — the largest set of queue items this session can
run unattended. `afk` fires it with zero interaction: the user typed the command and left.
`pack` shows it once and waits for a single confirmation. Everything else is identical.

## 1. Build the package

`tk-queue pack` (`../../bin/tk-queue`) hands over the candidates: the eligible
items in the queue's own order, and every excluded item with the reason AND the
value that caused it. The filter is the script's — AUTONOMOUS, no Risk, **Env**
absent or naming THIS machine, unclaimed — and the shape it prints is documented
in `tk-queue pack --help`. What it deliberately does not decide is the cut.

**Re-triage before accepting an exclusion.** A Risk the triage finds OBSOLETE (it
names a branch since merged, a migration since run) is cleared on the spot with
`tk-queue edit <id> --risk none`, which is what keeps a stale line from excluding
the item forever; an Env that named a machine the item needed before it was
sliced goes the same way, with `--env none`. An item reported as claimed belongs
to another session — if that session is known to be gone, hand it back with
`tk-queue release <id>`, which prints whose claim it dropped. An item excluded
over a malformed field carries its repair in the `repairs:` block. Re-run `pack`
after any of these.

**Then cut.** Take the eligible in the order printed — priority IS the order of
the file, and `tk-queue bump <id>` is what moves an item to the top — then add
items while the package still fits ONE session: the parent only orchestrates and
verifies, yet each item still costs context to dispatch, monitor and check. Each
candidate line carries its Effort, raw and unsummed. Guidance: stop around 3–6
items or ~2h of summed Effort; leaving an eligible item out beats a session too
long to verify its own work.

**Done when:** the package lists its items with the summed Effort (e.g. "4 items, ~1h45"),
and every item left out is noted with the reason — the eligible ones dropped for size AND
the ones `pack` excluded, which are not eligible at all and would otherwise leave no
trace anywhere.

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
(c) DECISION/BLOCKED/EXTERNAL items untouched, as in a normal kickoff close; (d) items
bound to ANOTHER environment, in a block of their own beside (c), each marked "runs on: X".
(d) is not a variant of (b): those items were never eligible here, so a report shaped only
around (b) drops them silently — and an item nothing on this machine can run is precisely
the one the user has to see, since only they can take it to the machine that runs it.
Settle any
remaining queue changes through `tk-queue` (`add`/`edit`/`done`/`cancel`) last — a DECISION
registered with nobody to ask carries `--deferred afk`, which is the only thing that
distinguishes it from a decision nobody bothered to ask.
**Done when:** the report covers (a)–(d) and `next-steps.md` matches the post-run queue.
