# The pruning report

One markdown file per run, its first line the path it was written to. Five parts, in order:

1. **Numbers** — the bin's metrics for the target, before and after.
2. **Table** — KEEP / MOVE / DROP, one row per sentence that instructs or defines a criterion.
3. **Splits** — each suggestion with the `SKILL-MECHANICS` criterion that decided it and the
   consumer that would reach it.
4. **Paths** — the pruned file, and for an own skill the `docs/` file holding the evidence.
5. **Proof** — the eval pair or the reviewed diff of rules, named.

The table carries four columns:

| column | what it holds |
|---|---|
| line | where the sentence sits in the source |
| sentence | the sentence, quoted |
| verdict | KEEP, MOVE or DROP |
| why | the behaviour kept, the destination chosen, or the reason dropped |

## Where a MOVE goes

| destination | criterion |
|---|---|
| reference file beside the skill | only the skill and its siblings reach the material |
| a new skill | a leading word the user would type, or another skill must reach it alone |
| `docs/` of the repo | evidence pulled out of an own skill |
| the report itself | evidence pulled out of a third-party skill |
| a ticket on the bin | contract the `--help` should carry; the sentence stays KEEP until then |
