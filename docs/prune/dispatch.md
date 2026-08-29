# What the `dispatch` pruning pass removed

Every sentence, clause and wording the first real `/tk:prune` pass took out of
`tk/skills/dispatch/SKILL.md`, verbatim, so that any one of them is put back in one edit. The
verdicts, their reasons and the numbers are in `dispatch-report.md` beside this file.

`tk-prune-measure` reported **inline evidence: 0** on the original. `prune/REPORT.md` defines
this file as the `docs/` file of inline evidence, so with nothing of that kind to hold it is
used here for the prose the pass removed instead — outside the contract, and filed as a ticket
on the tracker rather than patched. `dispatch-report.md` §6 carries the ticket; this paragraph
is the only place the argument is written.

Three kinds of removal are recorded, and they are not equal. A **DROP** is a verdict on a whole
sentence. A **clause** is an instruction or a reason taken out of a sentence that stayed, which
the skill has no verdict for — the reason it can go missing, and the reason all of them are
listed here. A **rewording** loses neither, and is listed so the diff has no unexplained words.

## DROP — duplicate

Three sentences said the `disable-model-invocation` lock three times. The pruned file keeps one
rule and one instruction; these two are the copies.

> The same lock rules out dispatching such a skill to a subagent **by name**: a prompt
> reading "run `/implement`" reaches an agent that cannot invoke it, and the run dies there.

> Pointing a subagent at the FILE works, for the reason the scheduled fire above works — the lock
> is on invoking the command, and it does not reach a file being read.

The palette row on tickets and the paragraph closing the boundaries section carried the same
dispatch twice. The row stayed.

> Tickets published on the issue tracker are dispatched by the site's per-ticket flow, one
> ticket per fresh session — the tracker is their source of truth.

## Clauses removed from a surviving sentence

Four, after the correction batch put a fifth back. None carries a verdict of its own: the
sentence holding each one stayed.

**1. The research row's fallback**, a duplicate of the rule the file states for every row ("If a
mechanism doesn't exist in the session, use the nearest neighbour").

> fallback: a background subagent with that same contract

**2. The reason behind the generation rule**, where the rule and its pointer both survive and
`../kickoff/WINDOW.md` owns the reason.

> because a generation succeeds the session rather than running inside it

**3. The `/goal` recipe's example of a constraint.** The recipe still names "the constraints";
the illustration went.

> (without touching other tests)

**4. Where the locked skill's file sits.** The pruned rule names the plugin instead.

> in the plugin's install folder

**5. Restored, not removed: `(no polling)`**, from the Monitor row. It is the instruction that
separates Monitor from an interval `/loop`, and the first pass demoted it to a wording trim with
no record at all. The cold review found it; the row now reads "a script streaming state, not
polling". It is listed here because its disappearance is the evidence for the ticket on this
whole class.

## MOVE — out of the file

The whole `loop.md` contract section, now `tk/skills/dispatch/LOOP.md`, reached from the palette
row that dispatches a queue of slices and from the four-dispatchers list. Its fenced template is
byte-identical; its three prose sentences were reworded, and those rewordings are listed below.

## MOVE — inside the file

The routine contract, out of the `/schedule` palette row and into the recipes section beside the
`/goal` one. The row measured 44 words, the file's longest sentence.

> | Recurring (routine, not a one-off item) | `/schedule` (cloud) or local cron — draft the
> COMPLETE routine: it runs without a human and without permission prompts, so the prompt is
> self-contained, with the done criterion embedded and a recommended model (mechanical routine
> → smaller model) | the agent |

The first pass narrowed the model rule while moving it, to "a smaller model for mechanical
work", which is silent about every other routine. The correction batch restored the source's
shape: "a model recommended — the smaller one for mechanical work".

## Rewordings, carrying no verdict

Neither an instruction nor a reason is lost in any of these. They are listed so that no word in
the diff is unexplained.

| where | original | now |
|---|---|---|
| the lock rule | "Scheduled fires only execute model-invocable skills" | "reachable by FILE only", which covers the scheduled fire and the subagent in one clause |
| the opening | "the complete command/prompt", "ready-to-fire line/prompt" | "the complete command", "ready-to-fire line" |
| the queue pointer | "(contract: `../kickoff/SKILL.md`, relative to this file)" | "(contract: `../kickoff/SKILL.md`)" |
| the four-dispatchers lead | "has four dispatchers, by presence and scope:" | "has four dispatchers:" |
| the ticket row | "the site's per-ticket implementation flow" | "the site's per-ticket flow" |
| site extensions | "`.claude/tk/dispatch.md` (project root)" | "`.claude/tk/dispatch.md`" |
| the fleet bullet | "one **full** orchestrator per project at `--budget 1`" | "one orchestrator per project"; `../fleet/SKILL.md` owns the budget |
| the afk bullet | "one-shot package run by an orchestrator + background subagents, context-isolated" | "one orchestrator plus background subagents, each context-isolated" |
| the `/loop` bullet | "context accumulates across iterations" | "context accumulating (contract: `LOOP.md`)" |
| the foggy row | "the way to the destination isn't visible, too big for one session" | "too big for one session" |
| the research row | "external sources (docs, APIs, knowledge bases)", "a cited markdown file in the repo" | "external sources (docs, APIs)", "a cited markdown file" |
| `LOOP.md`, opening | "it turns `/loop` (5 keystrokes) into the dispatcher" | "turning `/loop` into the dispatcher" |
| `LOOP.md`, middle | "When dispatching a queue of slices for the first time in a project, create the file; on later runs, check it still matches the contract" | "Create the file the first time you dispatch a project's queue this way, and check on every later dispatch that it still matches the contract" |
| `LOOP.md`, closing | "the file belongs to the project (versionable)" | "the file belongs to the project and is versioned there" |

## What the correction batch changed after the cold review

The pruned file was not final when the review read it. These are the edits the review's findings
produced, listed so that the diff and this file stay in step.

- the `description` rewritten a second time, to carry the leading word `Dispatch` and the
  user-facing triggers `delegating`, `scheduling`, `automating` — still 30 words;
- `generation` restored to its defining property, "What no subagent can open", and with it
  "rather than a subagent", which the first pass had dropped;
- the claim about `../fleet/SKILL.md` restored as a requirement on the reader, "Take the same
  route for every project of a fleet dispatch", instead of being DROPped;
- `(no polling)` restored, as above;
- the model rule restored to its unnarrowed shape, as above;
- `LOOP.md` given a second pointer, in the four-dispatchers list, where a reader arriving from
  `../kickoff/SKILL.md` lands;
- the two recipes merged into one paragraph under their heading, which is what paid for the
  lines the restorations cost. The file is still 60.
