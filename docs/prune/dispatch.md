# What the `dispatch` pruning pass removed

Every sentence the first real `/tk:prune` pass took out of `tk/skills/dispatch/SKILL.md`, kept
verbatim so that any DROP is reversed in one edit. The verdicts, their reasons and the numbers
are in `dispatch-report.md` beside this file.

`tk-prune-measure` reported **inline evidence: 0** on the original, so this file holds no dated
measurement pulled out of the skill — the material a pass on this file had to preserve is the
dropped prose itself. The skill's own rule stands either way: own-skill evidence goes one file
per skill, and this is that file.

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

## DROP — suspected no-op

A claim about a sibling skill, changing no decision the reading agent makes.

> `../fleet/SKILL.md` dispatches every one of its project runs on that route.

## Clauses removed from a surviving sentence

A table unit is a whole sentence, so none of these carries a verdict of its own — the sentence
holding each one stayed. They are recorded here for the same reason a DROP is: one edit puts any
of them back. The report's defect list says why the skill has no verdict for them.

The research row named a fallback the file already states for every row ("If a mechanism doesn't
exist in the session, use the nearest neighbour"), inside the row's own parentheses.

> fallback: a background subagent with that same contract

The reason behind the generation rule, where the rule itself and its pointer both survive.

> because a generation succeeds the session rather than running inside it

The site-extension paragraph's tail, superseded by the pointer to the README section that owns
the extension-file contract.

> — they name the site's concrete commands for the palette rows marked "(site extensions name
> it)".

## MOVE — out of the file

The whole `loop.md` contract section, now `tk/skills/dispatch/LOOP.md`, reached from the palette
row that dispatches a queue of slices. Its text is unchanged apart from the two rewordings noted
below; the fenced template inside it is byte-identical.

## MOVE — inside the file

The routine contract, out of the `/schedule` palette row and into the recipes section beside the
`/goal` one. The row measured 44 words, the file's longest sentence.

> | Recurring (routine, not a one-off item) | `/schedule` (cloud) or local cron — draft the
> COMPLETE routine: it runs without a human and without permission prompts, so the prompt is
> self-contained, with the done criterion embedded and a recommended model (mechanical routine
> → smaller model) | the agent |

## Notes — rewordings, carrying no verdict

Wording trimmed to bring a unit under the 25-word ceiling. Each detail below is gone from the
skill and recorded here; none of them was judged.

- `/loop` "(5 keystrokes)", from the `loop.md` contract's opening sentence.
- "one **full** orchestrator per project at `--budget 1`" in the fleet bullet, now "one
  orchestrator per project"; `../fleet/SKILL.md` owns the budget.
- "one-shot package run by an orchestrator + background subagents, context-isolated", now "one
  orchestrator plus background subagents, each context-isolated".
- "the way to the destination isn't visible", in the foggy-effort row.
- "knowledge bases", in the research row's list of external sources.
- "in the repo", in the research row's cited-file clause.
- "one full orchestrator", "WITHOUT" and "dynamic workflow" recased or respelled where the row
  read the same either way.
