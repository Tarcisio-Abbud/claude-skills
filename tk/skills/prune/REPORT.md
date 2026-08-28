# The pruning report

One markdown file per pruning pass, named `prune-report.md`; its first line is the path it was
written to. A pass that found nothing to prune writes that line, then `nothing to prune`.

1. **Numbers** — the bin's metrics for every file read, before and after.
2. **Table** — KEEP / MOVE / DROP, one row per table unit, as step 4 of `SKILL.md` defines it.
3. **Splits and notes** — each splitting suggestion with its `SKILL-MECHANICS` criterion and
   the consumer that would reach it, then every rewording, marked as carrying no verdict.
4. **Paths** — the pruned files, and for an own skill the `docs/` file of inline evidence.
5. **Proof of the target skill** — the eval pair or the reviewed diff of rules, named.

The table carries four columns:

| column | what it holds |
|---|---|
| where | the file and the line the sentence sits at |
| sentence | the sentence, quoted |
| verdict | KEEP, MOVE or DROP |
| why | the run the rule serves, the destination chosen, or the reason dropped |

## Where a MOVE goes

| destination | criterion |
|---|---|
| reference file beside the skill | only the skill and its siblings reach the material |
| a new skill | the `SKILL-MECHANICS` criterion, read in step 2 |
| `docs/` of the repo | inline evidence pulled out of an own skill |
| the report itself | inline evidence pulled out of a third-party skill |
| a ticket on the bin | contract the `--help` should carry — file it, the sentence stays KEEP |
