# What the `verify` pruning pass removed

Every sentence, clause and wording the pass took out of `tk/skills/verify/SKILL.md`, verbatim,
so that any one of them is put back in one edit. The verdicts, their reasons and the numbers
are in `verify-report.md` beside this file.

`prune/REPORT.md` defines this file as the `docs/` file of **inline evidence** pulled out of an
own skill. On `verify` there is one such sentence, and it is in §1 below — the first time this
destination has been used for what the contract names. The bin disagrees with that count in
both directions: it reported `inline evidence: 1` and pointed at a different line, where the
word *measured* is ordinary prose. Report §6 files that under **D8**, the ticket the `dispatch`
pass opened on this contract.

Everything from §2 down is prose with no verdict of its own. It is here for the same reason as
in `dispatch.md`: so that no word of the diff is unexplained.

## 1. Inline evidence, MOVEd out of the skill

One sentence of `The proof fits the promise` was a measurement, not a rule. The rule it sat
inside stays in the skill; the measurement is here.

> a criterion read as satisfied on a minimal fixture has passed while the same command failed
> on the populated form, the moment it met one

The skill now reads "Run the criterion against the shape the data really has, not the smallest
one the wording accepts", and the next sentence — the one naming a queue with tagged items and
a file with prior content as fixtures — is untouched.

## 2. DROP — duplicate

**The three results, resolved twice.** The `Two positions` table already says the north star
logs its result and the hard gate emits one outcome.

> At the hard gate those results resolve into outcomes; before it, they are only logged.

**The outcomes, listed twice.** The four rows of the outcomes table say this.

> What survives the fit check splits by type — within A, passed or failed 3×; within B, proof
> ready or failed 3×.

**The empty return.** `../kickoff/AFK.md` states this rule for the same reader — the
orchestrator collecting a run — under *An empty return is a failed attempt*, and
`tk-contract` puts it in every subagent's block.

> A subagent that returns with no evidence block did not pass: an empty return is a failure
> that reads as success.

**Why the attempt history is not in the item.** The size cap is stated again two lines below,
where it changes what the reader types (`--force`).

> It lives there rather than in the item because the queue item is size-capped.

## 3. DROP — exposition of a rule that stayed

Each of these explains a rule stated beside it, and instructs nothing of its own.

> A criterion that passes with the defect back proves nothing, and it would carry a green
> evidence block all the way to the user.

> Work done against a broken premise is work to throw away.

> The one thing that reaches the user is what was **measured**, which is why the criterion
> travels intact: an implementer that rewrites the ruler to make it pass returns a
> self-attestation, and the gate stops meaning anything from that item on.

> From then on the Standards axis of any code review watches it for free.

> The next session starts from the handoff.

## 4. Clauses removed from a surviving sentence

Twelve, in eleven rows, and none of them a verdict: the sentence holding each one stayed. The
skill has no row for this shape, which is **D7**, the open ticket §6 of the report names. They
are listed here so the class stays visible.

| from | the clause | why it went |
|---|---|---|
| the read-only rule | "it is the ruler, and" | the `description` and the opening both call the criterion the ruler |
| the equivalence artefact | "a differential fuzz across the two implementations," | one of three examples; two remain |
| the **Approved** row | ", taken at its own gate" | the row already says the decision is the caller's |
| handoff step 1 | "(zero-padded, `T`-prefixed)" | environment: `tk-queue handoff --help` renders `# Handoff T007` |
| handoff step 1 | "refuses a briefing whose mandatory fields are empty" | environment: `--help` marks the three fields required |
| handoff step 1 | "and is what makes the file die with the item instead of outliving it" | environment: `--help` says the briefing "is deleted when the item is closed" |
| handoff step 2 | "The pointer rides in that field either way, and" | the sentence before it says where the pointer goes |
| the printed `edit` | "and carrying `--force` where the link would cross the item's size ceiling" | environment: the script puts the `--force` in the line it prints, and the instruction is to run what it printed |
| the printed `edit` | "and a briefing no item names is one the next session never finds" | explains "the briefing's only discovery path" |
| `tk-queue done` | "— `--how` is required," and "so that form keeps the output to a single line" | environment: `tk-queue done --help` marks `--how` required |
| *The item points at the briefing* | "and the five sites that prescribe a briefing route here for it" | a fact about the plugin's other files, not an instruction to the run; the five sites still point here |

## 5. MOVE — out of the file

The third-failure sequence, its three numbered steps whole, now `tk/skills/verify/HANDOFF.md`.
It is reached from the section it left, `Three attempts, then the queue`, which keeps the
ceiling-of-three rule. No pointer in any sibling file was rewritten, and the report says why
that was the deciding constraint.

The paragraph that closed the moved sequence went with it, reworded to name its new neighbour:

> The sequence above is the one exception: its step 2 writes the same pointer into
> `--deferred`, which answers the warning, so no second `edit` is due there.

## 6. Rewordings, carrying no verdict

| where | original | now |
|---|---|---|
| the opening | one 37-word sentence carrying the definition, the two types and the pointer | three sentences, the definition first |
| the north star row | "it is expected to fail until the last slice, and the result is logged, not acted on" | "expected to fail until the last slice, and logged rather than acted on" |
| the equivalence rule | "an equivalence artefact: output byte-compared…" | split in two at the colon |
| the fit check | "runs FIRST: a criterion that does not fit the promise is **rotten**…, so a satisfiable-but-wrong criterion reaches neither "approved" nor "proof ready", of either type" | "runs FIRST. A criterion that fails it is **rotten** whatever its exit code." |
| the retry rule | "is not an outcome — it is a retry" | "is a retry rather than an outcome" |
| the **Proof ready** row | "…is assembled" | dropped, the row is a noun phrase |
| the unsatisfiable bullet | "Say so **in writing before doing the work**, not after" | "Say so **in writing before doing the work**" |
| handoff step 3 | "so the dead package's ownership does not outlive it" | "so the dead package's ownership dies with it" |
| the caller's re-run | one 38-word sentence | split at "It runs once" |
| `tk-queue done` | "— `--how` is required, and `--force` raises…" | "That `--force` raises…" |
| the promotion rule | one 48-word sentence | split at "Add one line" |
| the promotion's else-branch | "A criterion that is not in suite shape" | "A criterion outside suite shape" |
| **Done when** | one 42-word sentence | split at "A 3× failure" |

## 7. The `description`, rewritten

> Runs the item's own acceptance criterion as the ruler of the delivery — north star after each
> slice, hard gate at the end, and the evidence block the next reader re-runs. Use when a
> session declares an item done, when an implementer or an orchestrator closes an unattended
> slice, or when another skill needs the acceptance ruler.

56 words, on every turn. What replaced it is in the report's table row, with the two things the
rewrite loses named there.
