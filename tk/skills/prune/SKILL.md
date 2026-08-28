---
name: prune
description: "Prune a skill with the writing-for-agents ruler: measure it, then report what to keep, move and drop."
disable-model-invocation: true
argument-hint: "<skill-path> [<output-dir>]"
arguments: skill_path out_dir
---

**Pruning** is subtraction with a ruler beside it: the machine measures, the user decides.
Nothing is written in place. The output directory is the second argument, default
`./prune-out/<skill-name>/` under the cwd. Add that path to `.gitignore` when the cwd is a
repo — a pruning report belongs outside the history.

## Steps

1. **Measure.** Run `../../bin/tk-prune-measure <file> --targets` on every markdown file of
   the target skill's directory. The ceilings are the bin's own defaults; read them there.
2. **Read the ruler.** Invoke `/mattpocock-skills:writing-for-agents`. Read its
   `SKILL-MECHANICS.md` when frontmatter, invocation or splitting is in play.
3. **Subtract.** Name, for each mechanism the skill carries, the path it serves. For an own
   skill, name also whether that path runs today.
4. **Tabulate.** Write one row per sentence that instructs or defines a criterion.
5. **Write.** Save the pruned file and the report to the output directory, in the shape
   `REPORT.md` beside this file carries.

Step 4 ends when every instructing sentence of the target holds a row. Step 5 ends when the
bin reads the pruned file inside the targets, or the report names the ceiling it holds and why.

## The table

- **KEEP** names the behaviour that changes against the model's default.
- A sentence whose changed behaviour nobody can name is a **DROP**, reason "suspected no-op".
- Write every DROP row so that the user reverses it in one edit.
- **MOVE** names the destination and the criterion that chose it, from the `REPORT.md` table.
- **DROP** names its reason: duplicate, evidence, environment cache, unexercised path.
- The target skill's `description` holds a row of its own.
- Exposition groups under the rule it explains, one row for the group.

## Reading the numbers

- A mark on **max words in a sentence** is reported, and alone it founds no DROP.
- **Sentences over 30 words** carries the long-sentence signal, and it does found one.
- Negations and defined terms come with no ceiling: read the listed line before judging it.
- One term defined in two files of a directory is one meaning to gather into one place.

## Vocabulary

A coined term costs its definition and recruits no prior. Found it under one heading, or
replace it with a word the model already holds.

## Third-party skills

- Read the behaviour behind every KEEP from the target skill's text alone.
- Leave "runs today" blank: DROP by unexercised path needs a history only an own skill has.
- Skip site extensions; a third-party skill carries none of this site's.
- A plugin cache is read-only. The destination is an upstream PR, or a fork of the marketplace.
- A copy under `.claude/skills/` takes the bare name while the plugin skill stays reachable
  namespaced: a second skill, not a shadow.
- Evidence pulled out of a third-party skill stays in the report, and reaches no repo of yours.

## Own skills

Evidence pulled out of an own skill — dates, counts, war stories — goes to `docs/` of its
repo, one file per skill. The report on a private skill stays out of a public repo.

## Suggest, never execute

A skill inside a skill earns a splitting suggestion, carrying the `SKILL-MECHANICS` criterion
that decided it and the consumer that would reach it. The split is a slice of its own.
A contract the script's `--help` should carry earns a ticket on the bin. That sentence stays
KEEP until the help carries it, which keeps a pruning branch to prose alone.

## Nothing to prune

Every target met, and the table holding no DROP and no MOVE: write the one line "nothing to
prune", and stop.

## The proof comes from outside

Name in the report the proof the target skill can carry:

- output a script can check → a `skill-creator` eval pair, the original as the control arm;
- output that is prose → the reviewed diff of rules.

Then hand the user the closing run: `/mattpocock-skills:code-review` over the pruned file.
Its Standards sources carry the path of `writing-for-agents`, and its Spec axis reads the
table. Tell them to declare the smell baseline inapplicable, since the target is prose.

**Done when:** the report sits at the path its first line names, the table covers every
instructing sentence, and the proof is named.
