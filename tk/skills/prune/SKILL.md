---
name: prune
description: "Prune a skill with the writing-for-agents ruler: measure it, then report what to keep, move and drop."
disable-model-invocation: true
argument-hint: "<skill-path> [<output-dir>]"
arguments: skill_path out_dir
---

**Pruning** is subtraction with a ruler beside it: the machine measures, the user decides.
Nothing is written in place. The report and the pruned files go to the second argument, or to
`./prune-out/<skill-name>/` under the cwd when it is absent. When that path lands inside a
repo, add it to that repo's `.gitignore` — a pruning report belongs outside the history.

## Steps

1. **Measure.** Run `../../bin/tk-prune-measure <file> --targets` on every markdown file of
   the target skill's directory. The ceilings are the bin's own defaults; read them there.
2. **Read the ruler.** Invoke `/mattpocock-skills:writing-for-agents`. Read its
   `SKILL-MECHANICS.md` when frontmatter, invocation or splitting is in play.
3. **Subtract.** For every rule the skill carries, name the run that reaches it. For an own
   skill, say also whether such a run has happened since the rule was written.
4. **Tabulate.** Write one row per sentence that instructs or defines a criterion.
5. **Write.** Save every pruned file and the report to the output directory, in the shape
   `REPORT.md` beside this file carries.

Step 3 ends when every rule has a named run. Step 4 ends when every instructing sentence of
every file step 1 read holds a row. Step 5 ends when the bin reads each pruned file inside the
targets, or the report names the ceiling it holds and why.

## The table

- **KEEP** names the behaviour that changes against the model's default.
- A sentence whose changed behaviour nobody can name is a **DROP**, reason "suspected no-op".
- Write every DROP row so that the user reverses it in one edit.
- **MOVE** names the destination from the `REPORT.md` table and the criterion that chose it.
- **DROP** names its reason: duplicate, evidence, environment cache, unexercised run.
- A verdict removes or relocates a whole sentence, and rewording is a split suggestion.
- The target skill's `description` is the one field pruned in place: its row carries the
  wording that replaces it.
- Exposition groups under the rule it explains: one row, its line column naming the range.

## Ranking the marks

- **KEEP outranks every ceiling.** A sentence that names a behaviour stays, however long.
- A ceiling marks; alone it founds no verdict, and `max words in a sentence` founds none ever.
- Negations and defined terms come with no ceiling: read the listed line before judging it.
- One term defined in two files stays in the file that uses it, and is a DROP in the other.
- Used in neither file, that term is a DROP in both.

## Vocabulary

A coined term costs its definition and recruits no prior. Define it under one heading, or
replace it with a word the model already holds.

## Whose skill it is

- Read the behaviour behind every KEEP from a third-party skill's text alone.
- Leave "runs today" blank there: a DROP by unexercised run needs a history an own skill has.
- A third-party skill reaches no site extension of yours, so its pointers to one stay KEEP.
- A plugin cache is read-only. The destination is an upstream PR, or a fork of the marketplace.
- A copy under `.claude/skills/` takes the bare name while the plugin skill stays reachable
  namespaced: a second skill, not a shadow.
- Evidence pulled out of an own skill goes one file per skill; a private skill's report stays
  out of a public repo.

## Suggest, never execute

A skill inside a skill earns a splitting suggestion, carrying the `SKILL-MECHANICS` criterion
that decided it and the consumer that would reach it. The split is a slice of its own.

## Nothing to prune

Every target met, and no DROP or MOVE in the table: the report is one line, "nothing to
prune". The run stops there.

## The proof comes from outside

Name in the report the proof the target skill can carry:

- a run of it ends in an artefact a script can check → a `skill-creator` eval pair, the
  original as the control arm;
- a run of it ends in prose → the reviewed diff of rules.

Then hand the user the closing run: `/mattpocock-skills:code-review` over the branch that
carries the pruned file. It reads a committed diff, so the file reaches its own repo first.
Its Standards sources carry the path of `writing-for-agents`, and its Spec axis reads the
table. Tell them to declare the smell baseline inapplicable, since the target is prose.

**Done when:** the report sits at the path its first line names, the table covers every
instructing sentence, and the proof is named.
