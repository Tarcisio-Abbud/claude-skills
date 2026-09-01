---
name: prune
description: "Prune a skill with the writing-for-agents ruler: measure it, then report what to keep, move and drop."
disable-model-invocation: true
argument-hint: "<skill-path> [<output-dir>]"
arguments: skill_path out_dir
---

**Pruning** is subtraction with a ruler beside it: the machine measures, the user decides. The
target skill is never edited. The pass writes to the second argument or, absent, to
`./prune-out/<skill-name>/`; nothing there is committed — add it to that repo's `.gitignore`.
The committed home is `docs/prune/<skill-name>-report.md`, and `docs/prune/<skill-name>.md` for
an own skill's removed material — the pass writes every DROPped sentence and CLAUSE cut there.
The pruning PR copies both from the output directory — the diff the closing review reads. A
private skill's report never enters a public repo's `docs/` — its `.gitignore` allowlists
`docs/prune/*` file by file, the first line of defence. The pre-commit guard is the second.

## Steps

1. **Measure.** Run `../../bin/tk-prune-measure <file> --targets`, relative to this file, on
   every markdown file of the target skill. Its defaults are the ceilings; read them there.
2. **Read the ruler.** Invoke `/mattpocock-skills:writing-for-agents`. Read its
   `SKILL-MECHANICS.md` when frontmatter, invocation or splitting is in play.
3. **Subtract.** For every rule the skill carries, name the run that reaches it. For an own
   skill, date the file against its newest `docs/` report — `git log -1 --format=%cs` on each.
   A file younger than the report carries rules with no run on record.
4. **Tabulate.** A **table unit** is a sentence that instructs, defines a criterion or carries
   inline evidence. So are the `description`, a fenced block a verdict relocates, and an
   **exposition range**: consecutive sentences explaining a rule stated elsewhere. One row each.
5. **Write.** Save the report and every file the pass wrote — pruned copies, and destinations a
   MOVE created — side by side in the output directory, in the shape `REPORT.md` carries.

Step 3 ends when every rule has a named run and the own skill's file is dated. Step 4 ends when
every unit, in every file step 1 read, holds a row. Step 5 ends when the bin reads each written
file inside the targets at its landing address, or names the ceiling it holds and why. The
sibling scan reads every markdown beside the measured file: a report there is a sibling too.

## The table

- **KEEP** names the behaviour that changes against the model's default.
- A sentence whose changed behaviour nobody can name is a **DROP**, reason "suspected no-op".
- Write every DROP and every CLAUSE row so the user reverses it in one edit.
- **MOVE** names the destination from the `REPORT.md` table and the criterion that chose it. It
  lists, grepping the target's plugin, every pointer to the moved content, with its rewrite.
- **DROP** names its reason: duplicate, inline evidence, environment copy, unexercised run.
- A verdict removes or relocates a whole sentence; a rewording is a note, never a verdict.
- A clause cut from a sentence that stays — an instruction or a reason — is neither: it takes
  a CLAUSE row in the table, whose shape `REPORT.md` sets.
- A rewording note touching a defined term quotes the coining line, from any skill of the plugin.
- A verdict never deletes a file, so a file its DROPs emptied is a note too.
- The `description` is rewritten rather than dropped: its row carries the wording replacing it.
  It also names every leading word and branch the rewrite loses.
- An exposition range groups under the rule it explains, its `where` column naming the range.
- A skill inside a skill earns a splitting suggestion, carrying the `SKILL-MECHANICS` criterion
  that decided it and the consumer that would reach it. The split is a slice of its own.
- Every target met, and no DROP, MOVE or CLAUSE in the table: under its path line the report
  carries one line, `nothing to prune`. The pruning pass stops there.

## Ranking the marks

- **KEEP outranks every ceiling.** A sentence that names a behaviour stays, however long.
- A ceiling marks; alone it founds no verdict, and `max words in a sentence` founds none ever.
- Negations and defined terms come with no ceiling: read the listed line before judging it.
- One term defined in two files stays in the file that uses it, and is a DROP in the other.
- Used in neither file, that term is a DROP in both.
- A coined term costs its definition and recruits no prior: define it once, or replace it.

## Whose skill it is

- Read the behaviour behind every KEEP from a third-party skill's text alone.
- A DROP by unexercised run needs a history an own skill has, so no third-party row carries it.
- A third-party skill reaches no site extension of yours, so its pointers to one stay KEEP.
- A plugin cache is read-only. The destination is an upstream PR, or a fork of the marketplace.
- A copy under `.claude/skills/` takes the bare name while the plugin skill stays reachable
  namespaced: a second skill, not a shadow.

## The target's proof comes from outside

Name in the report the proof the target skill can carry, by what a run of it ends in. An
artefact a script can check → a `skill-creator` eval pair, the original as the control arm.
Prose → the reviewed diff of rules. An eval's assertions run once against a deliberately
broken arm before either real arm counts. A set it passes proves nothing: fix them and rerun.

Then hand the user the closing review: `/mattpocock-skills:code-review` over the branch
carrying the pruned file and the report. It finds none of its inputs here; tell the user to
give it three. Standards gets the `writing-for-agents` path; Spec reads the table. The smell
baseline is declared inapplicable: the target is prose.

**Done when:** the report sits at its committed home, and every unit holds the row its verdict
owes. The target's proof is named, and an eval proof names its broken arm.
