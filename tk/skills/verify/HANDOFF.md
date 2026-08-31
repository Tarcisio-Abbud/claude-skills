# The handoff the third failure writes

The three-step sequence `SKILL.md` (*Three attempts, then the queue*) reaches on the third
failed attempt at the hard gate. It routes the item out of the package, in this order:

1. Write the handoff with the script, never by hand: `tk-queue handoff <id> --objective "..."
   --state "..." --blockers "..." [--skills "..."] [--pitfalls "..."]`. It writes
   `handoff-T00N.md` beside the queue files. The **attempt history** goes in `--state` — per
   attempt: what changed, the command, the exit code and the tail of the output.
2. `tk-queue edit <id> --class DECISION --deferred "<why the decision could not be asked> —
   [[handoff-T00N]]"`. An unattended session has no one to ask, so it passes `--deferred "afk —
   [[handoff-T00N]]"`. An item already near its size ceiling takes `--force`.
3. `tk-queue release <id>` when the item was claimed, so the dead package's ownership dies with
   it.

Step 2 writes the `[[handoff-T00N]]` pointer itself. That is the one case where `SKILL.md`,
*The item points at the briefing*, is already answered.
