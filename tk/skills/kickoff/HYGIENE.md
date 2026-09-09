# Agent hygiene — handling the runs a package dispatches

Read from step 3 of `AFK.md` beside this file, by the ORCHESTRATOR: every rule below is about a
run seen from OUTSIDE it, and none of them is anything a run does to itself. `tk/bin/tk-hygiene`
shares the word and not the subject — that bin prunes branches in a repository, and nothing here
touches a forge.

The seven rules stand in the order of a run's life: what the dispatch prompt carries, how the
live ones are counted and watched, what a return has to contain, and what is killed before the
lane is declared closed. Six were paid for on 2026-09-06, in one package of 13 lanes, and each
names the defect that bought it; the seventh is the cookbook's, and says so.

Every rule opens with the **Signal** that fires it — the observation in front of the
orchestrator, never the clock. A rule carried without its signal is a rule applied at the wrong
moment, or not at all.

## One scratchpad per lane, named in the prompt

**Signal —** you are composing a dispatch prompt.

Hand the run a `<scratch dir>` no other run's prompt names, and put the path IN the prompt: a
run told nothing writes where the last one wrote. Two lanes shared one scratchpad on
2026-09-06 and each truncated the other's mutation log — 20 minutes lost, and the truncation
read as a failed mutation run rather than as a collision. `LANE-CONTRACT.md` beside this file
owns what the lane then does with the directory; allocating the address stays here, because
only the orchestrator sees both lanes.

## Count the live lanes by ROLE, never by the total

**Signal —** you are about to read a live-agent count and decide from it whether there is room
for the next dispatch.

`ListAgents` answers with every agent this session can address, and a lane is not the only thing
in that answer: one `code-review` run fires two reviewers of its own, and they arrive as
SIBLINGS of the lanes rather than underneath the run that spawned them. Four lanes with one
review running therefore read as six. That is why the total lies — it counts agents, and the
question asked of it was about lanes. Count the rows whose role is the one the lane dispatch
pinned (`../../reference/subagent-policy.md` owns the role names), one row per lane. The
reviewers are still agents and still count against the site's `max-local-subagents`, which
bounds agents and not lanes: the two numbers are read off the same list and answer different
questions.

## Never ask a live agent for its output

**Signal —** a run has not returned and you want to know where it is.

Wait for its notification. Asking a still-running agent for its output dumps ~15k tokens of
transcript JSONL into the orchestrator's context and decides nothing: the run is unfinished, so
what comes back is the middle of it. Measured on 2026-09-06 with `TaskOutput` against a live
agent, and the cost is the transcript itself, so any surface that returns one buys the same
15k. What tells you a live run is in trouble is the next rule, which reads bytes and not
content.

## A stuck run is read OFF its `.output` file, never out of it

**Signal —** a run has been quiet longer than the slice it was given can take.

Where the dispatch lands a run's output in a file, `stat` is the whole check:

```sh
stat -c '%s %y' "<the run's .output file>"
```

Two numbers, both of them the file's and neither of them its content: SIZE in bytes and MTIME.
Frozen for an hour or more, on a slice measured in minutes, the run is dead — the real case was
119 bytes at 20:52 and the same 119 bytes hours later. Then `TaskStop`, and re-dispatch the item
from its last pushed commit. Opening the file instead buys the ~15k tokens the rule above
refuses, and buys them to learn what the two numbers already said. A run whose output lands in
no file is watched by its notification alone.

## Revive by message the run that stopped waiting for a notification

**Signal —** a run comes back `completed` and its work is not there — nothing pushed, no
report, or a last line saying it is waiting on something.

`SendMessage` to that agent resumes it from its own transcript, with everything it had already
done still in hand. Two runs took this on 2026-09-06 — a Sonnet implementer and a second-opinion
— and both finished after one message. A re-dispatch instead pays the whole slice again, so the
message comes first and the re-dispatch only after the message returns nothing.

## An empty or malformed return is a failure, never an approval

**Signal —** a run returns, and the return is empty, or short of what its contract names: the
artifact, the venue signature, the deviation log.

An empty return reads as success — the orchestrator gets no error and nothing to act on — so
it is graded as a failure, explicitly, and named in the report. The remedy is a ladder, cheapest
first: one message to revive it (the rule above), then a re-dispatch, then escalation to the
human with the missing half named. What closes the grading is the ARTIFACT — `git log`, the
diff, the tree — and never the run's own account of it.

This is the one rule here that was not paid for in this house. It comes from the
orchestrator-workers pattern of Anthropic's cookbook, at
https://platform.claude.com/cookbook/patterns-agents-orchestrator-workers, which validates each
worker's response, warns on an empty one and substitutes an explicit error string for it, and
names "workers may return empty or malformed responses" among the pattern's failure modes. That
guard is what crosses, and only it: `FlexibleOrchestrator`, `llm_call` and `extract_xml` are
Messages-API constructs a Claude Code orchestrator cannot call. The ladder is this house's
addition — a placeholder string finishes a page of prose, and a lane's slice still has to be
run by somebody.

## Kill the orphan waiters before the lane is declared closed

**Signal —** the lane's last run is back and you are about to write the lane closed.

A waiter is a background shell polling for a run — an `until … sleep` loop — and it outlives
the agent it watches by hours. Dying, it wakes the parent that is already `completed`, which
costs a turn and repeats a notification already read; that happened three times on 2026-09-06.
So the close carries one step more: kill every waiter whose run has returned, from the session
that started it, and write the lane closed after that.

**Done when:** the close found no waiter alive, every live count of the package was taken by
role, and every return was graded — approved against its artifact, or failed and put on the
ladder above.
