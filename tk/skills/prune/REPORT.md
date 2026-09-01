# The pruning report

One markdown file per pruning pass, named `prune-report.md`, whose first line is its own path.

1. **Numbers** — the bin's metrics for every file read, before and after.
2. **Table** — one row per table unit (step 4 of `SKILL.md`), plus a CLAUSE row per cut clause.
3. **Splits and notes** — each splitting suggestion with its `SKILL-MECHANICS` criterion and
   the consumer that would reach it, then every rewording, marked as carrying no verdict.
4. **Paths** — the pruned files, and for an own skill the `docs/` file of removed material.
5. **Proof of the target skill** — the eval pair or the reviewed diff of rules, named.

The table carries four columns:

| column | what it holds |
|---|---|
| where | the file and the line the sentence sits at |
| sentence | the sentence, quoted; on a CLAUSE row, the clause alone |
| verdict | KEEP, MOVE, DROP or CLAUSE |
| why | what the row owes — the run served, the destination with its rewritten pointers, or the reason dropped or cut |

## Where a MOVE goes

| destination | criterion |
|---|---|
| reference file beside the skill | only the skill and its siblings reach the material |
| a new skill | the `SKILL-MECHANICS` criterion, read in step 2 |
| `docs/` of the repo | inline evidence pulled out of an own skill — verbatim, so one edit puts it back |
| the report itself | inline evidence pulled out of a third-party skill |
| another section of the same file | the material stays in this skill, and the unit holding it is the wrong shape |
| a ticket on the bin | contract the `--help` should carry — file it, the sentence stays KEEP |
