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

`../../bin/tk-roster`, no flags, no subcommand. It prints up to four sections, and they are not
four views of one list — each carries a different obligation. A section with nothing to say is
absent rather than empty, and an absent one needs no line in the report.

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

**The allow/denylist belongs to the site file (`~/.claude/tk/env`), not to this skill.**
`fleet-allow` (present: only
those enter) and `fleet-deny` (those leave, and it wins over the allow) are read by the bin.
The fleet accepts no list of its own by flag and reimplements no filter: a second answer to
"what does the fleet touch" is a second source of truth, and the one the user edits is the file.

**The fourth section is a finding, not noise.** An unknown key in the site file is ignored on
purpose, so `fleet-denny` reads as an absent list and sweeps everything. An entry that matched
no queue is the only signal that a line exists and is doing nothing. It goes in the report
under its own heading, whatever else the run found.

**Two exits, two meanings.** Exit 1 is a rotten site file: the fleet stops and quotes
`tk-roster`'s own stderr verbatim, because every ceiling below comes from that same file. Exit 0 with an empty roster is a fact, not a failure: report that there was nothing to
sweep, and stop before dispatching anything.

**Done when:** every section the bin printed was read; `## roster` is the only one that will be
dispatched; every other one it printed is already written into the report.

## 2. Size each project, and order the fleet

**Largest first.** A project's size is the **eligible count** `tk-queue pack` prints for it. Run it
from the project's own directory, so the queue resolves the documented way instead of from a
path this skill built:

```sh
(cd "<the project's directory>" && python3 <.../tk/bin>/tk-queue pack)
```

Read the `eligible (<count> of <total>, in queue order)` line. **An eligible count of zero leaves
the project out of the fleet** — there is nothing to dispatch — and into the report with one line
per exclusion REASON, not one per excluded item: a queue full of ineligible items is a different
story from an empty one, and the reason classes are what tell them apart without reprinting
two dozen lines.

Order the rest by eligible count, descending; ties keep the roster's order. The reason is the wall clock:
the ceiling bounds how many run at once, not how many run in total, so the longest project has
to start earliest or the fleet ends when it ends.

This step only reads: `pack` takes no claim, so a project sized here and never dispatched needs
no release.

**Done when:** every dispatchable project carries an eligible count, the zero ones have left the
fleet with their exclusion reasons, and the rest are ordered descending.

## 3. Fix the width, and let the block state the ceilings

The **width** `W` is how many project runs are in flight at once. It is the number the fleet
passes as the divisor, and the ceiling it divides is this machine's, read from the site file by
the bin.

**Read the ceiling first, with no divisor.** `--fleet` takes the width as input, so the width
cannot be chosen from a block generated at it. Omit the flag and the block states the whole
ceiling, which is the number the cap below is computed from:

```sh
python3 <.../tk/bin>/tk-contract --role fleet-orchestrator                 # states the ceiling
python3 <.../tk/bin>/tk-contract --role fleet-orchestrator --fleet <W>     # the block to paste
```

**Every ceiling a prompt states comes out of the second block, pasted verbatim.** A hand-written
one is a fork of the policy, and the block itself says it wins wherever it and the surrounding
prose disagree. Where `--fleet W` divides down to nothing the bin says so in words: shrink the
width, which is the move it names.

### What the divisor does not count

The divisor splits the WHOLE ceiling among the project runs. It does not reserve a slot for each
run itself, and a project run is a local subagent like any other. So the machine's real peak is

```
peak = W project runs + the most any of them had dispatched at one moment
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
  produces the evidence to calibrate it. It is what the runs OBSERVABLY held at once, taken from
  their returns — the permitted share is what they were allowed, and calibrating a ceiling
  against a permission measures the permission.

**Done when:** the ceiling was read from a block generated with no divisor; the width is fixed at
`ceiling // 2` or below; every dispatch below will paste a block generated at that width; and the
observed peak is being tracked for the report.

## 4. Dispatch, and refill without a barrier

Each project run is dispatched as a **background subagent**, cwd at the project's directory, on
the `fleet-orchestrator` row.

**The prompt names the skill's file, never the command.** `../kickoff/SKILL.md` carries
`disable-model-invocation: true`, so a prompt reading "run `/tk:kickoff afk`" reaches an agent
that cannot invoke it and the run dies there. What the lock stops is the COMMAND; it does not
reach a file being read, which is the route `../dispatch/SKILL.md` already documents under
*Mechanism boundaries*.

The prompt carries, in this order:

1. **the contract block**, verbatim from step 3;
2. **the load, as an ABSOLUTE path on this machine.** "`skills/kickoff/SKILL.md` of the `tk`
   plugin" is how a human says it and not something a run can open: the path is relative, and
   this machine holds both an installed plugin copy and any worktree the fleet is running from.
   Resolve it here and paste the resolved path, so the run follows the copy the fleet meant;
3. **the load's own flags** — the table below says what each load carries, and a load whose skill
   reads no flag is handed none. For `afk` the flag is **`--budget 1`, explicitly**: a project run
   is one generation and writes a handoff instead of opening a successor, since a successor
   opened from inside a project run would be a second live orchestrator over that queue;
4. **the project's directory**, as the run's FIRST instruction — every `tk-queue` call resolves
   its queue from the cwd, and no dispatch mechanism here sets a subagent's cwd for it. It is
   carried as an instruction the run obeys, which is why it leads the dispatch rather than
   trailing it.

**No barrier between waves.** The width is a ceiling on concurrency, not a batch size: when a
project run returns, its slot is free and the next project in the step-2 order enters
immediately. Waiting for the slowest project run of a wave leaves every earlier finisher's slot idle
for exactly as long as that member runs.

**The quota wall belongs to the project run, not to the fleet.** Each run is a full orchestrator
and carries `WINDOW.md`'s rules for itself, at `--budget 1`. What the fleet owes the wall is the
checkpoint below.

### The checkpoint is a completed project, not a wave

With no barrier there is no end of wave to anchor on. The **textual report** is therefore
checkpointed **each time a project run returns**: that project's section is appended to it, on
disk, before the next dispatch goes out. The vista of step 6 is written once, at the close, from
that file — checkpointing the page instead would rewrite five blocks per return to protect
prose that a plain append protects. A fleet cut off by the quota wall leaves the textual report
covering every project that finished, with the ones still in flight named as such.

**Done when:** every dispatchable project has been dispatched or is queued behind a slot; every
in-flight run carries a generated block, an absolute load path, that load's flags and its own
working directory; and the textual report on disk covers every run that has returned.

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

## 6. The consolidated vista

The close has two artefacts. The **textual report** is the close itself — the one step 4 has been
appending to since the first return, on the template in `../wrap-up/SKILL.md`, *The closing
template*, which is also where block 1's four counts come from. The **vista** is its companion,
and `../../reference/vista.md` is that page's whole contract: the five blocks, the closed
outcome vocabulary, the outbox it lands in, the gate `tk-vista-check` and that gate's four
states. **Read it and follow it.** It is the consolidated reporter's contract as much as the
package close's, which is why it already answers what "consolidated" changes in blocks 1, 2
and 5; this step does not restate those readings and must not fork them.

Three things belong to the fleet and to no other reader of that file:

- **The package's name is `fleet`**, so the file is `<outbox>/vista-fleet-<YYYY-MM-DD>.html`.
  `vista.md` derives that name from a package's anchor or first item, and a fleet run has no
  package and no anchor — it has one run over many queues, and the run is what the name says.
- **Keep `vista.md`'s grouping, and name the project on every card.** Block 2 groups by
  OUTCOME, and that is not this step's to change. What eleven queues add is the ambiguity of a
  bare item id, which the card's own text resolves by naming its project.
- **Carry the fleet's own numbers beside the blocks**: the **measurement line** — projects
  planned × projects completed × wall clock, plus step 3's observed `peak` — and one **deviation
  line** per departure from the role table, in `../../reference/subagent-policy.md`'s format.
  **Planned is the count that entered step 4**, the dispatchable projects with work, never the
  roster's own total: the roster measures the machine and the fleet measures what it ran. The
  clock starts at the first dispatch. The model inherits by the role table; a downgrade is
  legitimate and costs the line.

A red gate does not hold the fleet: the textual report is the close, so a refusal is reported in
the state `vista.md` names and the run ends anyway.

**Done when:** the textual report is complete on the wrap-up template; the vista satisfies
`vista.md` rather than this section's summary of it, with every card naming its project; the gate
was run and its state is in the report; and the measurement and deviation lines are written.

## The load is a parameter

`afk` is the default load and the only one the steps above name. The argument replaces it,
leaving every other mechanic — roster, order, width, refill, isolation, consolidated report —
exactly as written:

| Argument | What each project run is told to do | Flags it carries |
|---|---|---|
| `afk` (default) | follow `../kickoff/SKILL.md` with the `afk` argument | `--budget 1` |
| `docs-audit` | follow `../docs-audit/SKILL.md` | none |

**The `afk` load enters at `../kickoff/SKILL.md`, not at `AFK.md`.** `AFK.md` is a continuation:
kickoff's own steps 1–3 gather the agenda and check what is still real, and only then does the
`afk` argument switch to that file. A run pointed straight at `AFK.md` packages items nobody
verified against reality, which is the one check the unattended path cannot afford to skip.

A load with no queue of its own — `docs-audit` sweeps a codebase, not a queue — changes step 2's
size: order those projects by the roster's own order and say in the report that the fleet was
unordered, rather than sizing them by a count that means nothing for that load.

**A load this table does not name is not a load.** Say so and stop; inventing the prompt for one
is how a fleet dispatches eleven projects into work nobody specified.
