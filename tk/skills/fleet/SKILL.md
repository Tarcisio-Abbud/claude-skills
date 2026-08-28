---
name: fleet
description: "Fleet run: one command opens the unattended package of EVERY project on this machine — roster from `tk-roster` and the site file, the machine's subagent ceiling divided across the runs, one full orchestrator per project at `--budget 1`, largest first, a slot refilled the moment a run returns, each failure confined to its project, and one consolidated vista at the close. Arg: the load — `afk` (default) or `docs-audit`."
disable-model-invocation: true
argument-hint: "[afk|docs-audit]"
arguments: load
---

A **fleet run** opens the same unattended work in every project on this machine at once. The
session that fires it is the **fleet orchestrator**: it builds the roster, sizes the machine's
ceiling across the runs, dispatches one **project run** per project, and writes one
consolidated report. It implements nothing and edits no code.

Two units, and keeping them apart is what the rest of this file rests on:

- the **fleet's** unit is a PROJECT — its concurrency ceiling counts project runs;
- a **project run's** unit is an ITEM — it is a full orchestrator over its own queue, with the
  whole of `../kickoff/AFK.md` behind it, and it is the only writer of that queue.

**The fleet writes no queue, in any project.** `tk-queue` resolves the queue from the cwd, so a
write from here lands in whatever queue this session's directory encodes to. The single-writer
rule survives the fleet only because every write happens inside the project run that owns it.

## 1. Build the roster

`../../bin/tk-roster`, no flags, no subcommand. It prints four sections, and they are not four
views of one list — each carries a different obligation.

| Section | What the fleet does with it |
|---|---|
| `## roster` | dispatches it: the name, then the directory to open the run in |
| `## not dispatchable` | reports it; never dispatches it |
| `## excluded by the site file` | reports it, naming which list excluded each |
| `` ## `fleet-deny` names no queue on this machine `` | reports it as a **finding**, below |

**Do not build a project's path from its queue name.** The name is the cwd encoded, and the
encoding is one-way: `/w/p/x-y` and `/w/p/x/y` produce the same name. That is why the second
section exists — those projects have a live queue and no trustworthy directory, and the bin
refuses to guess. The fleet refuses with it. Their queues are still readable without a session,
by the `queue:` path the section prints (`tk-queue list --dir <that path>`), when the report is
better for saying what is waiting there.

**The allow/denylist belongs to the site file, not to this skill.** `fleet-allow` (present: only
those enter) and `fleet-deny` (those leave, and it wins over the allow) are read by the bin.
The fleet accepts no list of its own by flag and reimplements no filter: a second answer to
"what does the fleet touch" is a second source of truth, and the one the user edits is the file.

**The fourth section is a finding, not noise.** An unknown key in the site file is ignored on
purpose, so `fleet-denny` reads as an absent list and sweeps everything. An entry that matched
no queue is the only signal that a line exists and is doing nothing. It goes in the report
under its own heading, whatever else the run found.

**Two exits, two meanings.** Exit 1 is a rotten site file: the fleet stops and quotes
`tk_site`'s message from stderr verbatim, because every ceiling below comes from that same
file. Exit 0 with an empty roster is a fact, not a failure: report that there was nothing to
sweep, and stop before dispatching anything.

**Done when:** all four sections were read; the first is the only one that will be dispatched;
the other three are already written into the report.

## 2. Size each project, and order the fleet

**Largest first.** A project's size is the eligible count `tk-queue pack` prints for it. Run it
from the project's own directory, so the queue resolves the documented way instead of from a
path this skill built:

```sh
(cd "<the project's directory>" && python3 <.../tk/bin>/tk-queue pack)
```

Read the `eligible (N of M, in queue order)` line. `N` is the size. **`N = 0` leaves the
project out of the fleet** — there is nothing to dispatch — and into the report with the
exclusions `pack` printed, since a queue that is full of ineligible items is a different story
from an empty one, and only the exclusion values tell them apart.

Order the rest by `N`, descending; ties keep the roster's order. The reason is the wall clock:
the ceiling bounds how many run at once, not how many run in total, so the longest project has
to start earliest or the fleet ends when it ends.

This step only reads: `pack` takes no claim, so a project sized here and never dispatched needs
no release.

**Done when:** every dispatchable project carries an eligible count, the zero ones have left the
fleet with their exclusion values, and the rest are ordered descending.

## 3. Fix the width, and let the block state the ceilings

The **width** `N` is how many project runs are in flight at once. It is the number the fleet
passes as the divisor, and the ceiling it divides is this machine's, read from the site file by
the bin:

```sh
python3 <.../tk/bin>/tk-contract --role fleet-orchestrator --fleet <N>
```

**Every ceiling a prompt states comes out of that block, pasted verbatim.** A hand-written one
is a fork of the policy, and the block itself says it wins wherever it and the surrounding prose
disagree. Where `--fleet N` divides down to nothing the bin says so in words: shrink the width,
which is the move it names.

### What the divisor does not count

The divisor splits the WHOLE ceiling among the project runs. It does not reserve a slot for each
run itself, and a project run is a local subagent like any other. So the machine's real peak is

```
peak = N project runs + the sum of what they dispatch
```

which is larger than the ceiling the divisor divided. The fleet does not fix that arithmetic
here — recomputing it would fork the ceiling away from the bin that owns it. It does two things
instead:

- **Cap the width at `ceiling // 2`, and default to that cap.** Above it, the project runs'
  own slots outnumber the work they dispatch — a fleet spending its memory on coordination.
  Below it is available and costs only wall clock, which is the right trade where a project run
  is known to be heavy.
- **Report the peak.** The measurement line of step 6 carries `peak` beside the other numbers,
  because the site file's own ceiling is written as a calibrable number and this is the run that
  produces the evidence to calibrate it.

**Done when:** the width is fixed at `ceiling // 2` or below; every dispatch below will paste a
block generated at that width; and the peak is being tracked for the report.

## 4. Dispatch, and refill without a barrier

Each project run is dispatched as a **background subagent**, cwd at the project's directory, on
the `fleet-orchestrator` row.

**The prompt names the skill's file, never the command.** `../kickoff/SKILL.md` carries
`disable-model-invocation: true`, so a subagent handed "run `/tk:kickoff afk`" cannot invoke it
and the run dies there (`../dispatch/SKILL.md`, *Mechanism boundaries*). Point it at the path:
"follow `skills/kickoff/AFK.md` of the `tk` plugin, with the `afk` argument". The prompt carries,
in this order:

1. **the contract block**, verbatim from step 3;
2. **the load** — `afk` by default; the argument replaces it (below);
3. **`--budget 1`, explicitly.** A project run is one generation and writes a handoff instead of
   opening a successor. Generations are sequential per package, and a successor opened from
   inside a fleet member would be a second live orchestrator over that queue;
4. **the project's directory**, as the cwd every `tk-queue` call resolves from.

**No barrier between waves.** The width is a ceiling on concurrency, not a batch size: when a
project run returns, its slot is free and the next project in the step-2 order enters
immediately. Waiting for the slowest member of a wave leaves every earlier finisher's slot idle
for exactly as long as that member runs.

**The quota wall belongs to the project run, not to the fleet.** Each run is a full orchestrator
and carries `WINDOW.md`'s rules for itself, at `--budget 1`. What the fleet owes the wall is the
checkpoint below.

### The checkpoint is a completed project, not a wave

With no barrier there is no end of wave to anchor on. The consolidated report is therefore
checkpointed **each time a project run returns**: its section is written then, on disk, before
the next dispatch goes out. A fleet cut off by the quota wall leaves a report covering every
project that finished, and the ones still in flight are named as such.

**Done when:** every dispatchable project has been dispatched or is queued behind a slot; every
in-flight run carries a generated block, a load, `--budget 1` and its own cwd; and the report on
disk covers every run that has returned.

## 5. A project fails alone

**One project's failure is that project's.** A run that returns empty, errors, or reports a
package it could not close does not stop the fleet: its slot frees, its section of the report
says what came back, and the next project enters. The fleet's own stop conditions are two, both
from step 1 — a rotten site file, and an empty roster.

**The fleet never repairs a project run's work.** It holds no context on that project's items,
its criteria or its tree; judging the repair from here is the partial-context verdict the
orchestrator/implementer split exists to prevent. A failed run's section names what returned and
what it left on disk, and the item stays in that project's queue for a session that opens there.

**Verify by artefact, not by summary.** A run's own account of its package is an input, never
the proof. The tree, the queue and the pull requests are what the report is built from — read
them for each returned run, in that run's project.

**Done when:** every failure is confined to its own section, no project's failure ended the
fleet, and no section rests on a run's self-report alone.

## 6. The consolidated report

The fleet closes on **one vista**, and `../../reference/vista.md` is its whole contract — the
five blocks, the closed outcome vocabulary, the outbox it lands in, the gate `tk-vista-check`
and that gate's four states. **Read it and follow it.** It is the consolidated reporter's
contract as much as the package close's, which is why it already answers what "consolidated"
changes in blocks 1, 2 and 5; this step does not restate those readings and must not fork them.

Two things belong to the fleet and to no other reader of that file:

- **Group the cards by project.** The grouping headings are prose and free, and the project is
  the only grouping that lets a reader find one queue's items among eleven queues' worth.
- **Carry the fleet's own numbers beside the blocks**: the **measurement line** — projects
  planned × projects completed × wall clock, plus step 3's `peak` — and one **deviation line**
  per departure from the role table, in `../../reference/subagent-policy.md`'s format. The model
  inherits by that table; a downgrade is legitimate and costs the line.

A red gate does not hold the fleet. The textual report is the close and the vista is its
companion, so a refusal is reported in the state `vista.md` names and the run ends anyway.

**Done when:** the vista satisfies `vista.md` rather than this section's summary of it, its cards
are grouped by project, the gate was run and its state is in the report, and the measurement and
deviation lines are written.

## The load is a parameter

`afk` is the default load and the only one the steps above name. The argument replaces it,
leaving every other mechanic — roster, order, width, refill, isolation, consolidated report —
exactly as written:

| Argument | What each project run is told to do |
|---|---|
| `afk` (default) | follow `../kickoff/AFK.md` with the `afk` argument, at `--budget 1` |
| `docs-audit` | follow `../docs-audit/SKILL.md` |

A load with no queue of its own — `docs-audit` sweeps a codebase, not a queue — changes step 2's
size: order those projects by the roster's own order and say in the report that the fleet was
unordered, rather than sizing them by a count that means nothing for that load.

**A load this table does not name is not a load.** Say so and stop; inventing the prompt for one
is how a fleet dispatches eleven projects into work nobody specified.
