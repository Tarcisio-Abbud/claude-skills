`docs/prune/verify-report.md`

# Pruning report — `tk/skills/verify/SKILL.md`

The second run of `/tk:prune`, and the first under the skill as `claude-skills#59` calibrated
it. The material this pass removed is beside this file, in `verify.md`. The pass's own output
directory was `prune-out/verify/`, outside git; the report and the removed material are
committed here because the ticket asks for them in the pull request, which is the contradiction **D5**
holds open — §6.

Throughout, **run** means one execution of the target skill, and the pruning execution is a
**pruning pass**. The table's unit is the **table unit** step 4 of `prune/SKILL.md` defines.

## 1. Numbers

`tk-prune-measure <file> --targets`, on the file before and after. **Bold** is a mark over the
bin's default ceiling.

| metric | ceiling | before | after | `HANDOFF.md` |
|---|---|---|---|---|
| lines | — | 143 | 115 | 18 |
| body words | — | 1352 | 929 | 170 |
| sentences | — | 77 | 70 | 16 |
| mean words per sentence | 22 | 17.6 | 13.3 | 10.6 |
| max words in a sentence | 25 | **48** | 25 | 21 |
| sentences over 30 words | 4 | **12** | 0 | 0 |
| description words | 30 | **56** | 29 | — |
| inline evidence | 0 | **1** | 0 | 0 |
| pointers to other files | — | 3 | 5 | 3 |
| negations | — | 23 | 9 | 3 |
| defined terms | — | 1 | 1 | 0 |
| terms defined in a sibling too | 0 | 0 | 0 | 0 |

Four marks over a ceiling before, none after, on either file.

**Where they were measured, and why the question is live.** Both files were measured in
`tk/skills/verify/`, where they land — never in `docs/prune/` beside this report. That is the
first of the two ways D5 allows, and it costs nothing here: the landing directory holds the
two skill files and no report, so the bin's sibling scan has nothing false to find. Measuring
in `docs/prune/` would: this report quotes the skill's bolded `**Verifying**`, and the bin reads
every markdown file of a directory as a sibling.

**The 80-line target the ticket names was not reached, and this is the accounting.** 143 → 115
is 28 lines, and the body lost 423 words of 1352 — a third — while gaining the three lines of
the site-extensions pointer the ticket also asks for. The remaining 35 lines are not slack.
Reaching 80 would mean deleting, in whole: `Promoting the criterion to a test` (11
lines, the only route by which a criterion outlives its evidence block), `The caller re-runs it`
(7 lines, the rule the whole `Approved` outcome rests on), and either the outcomes table or the
two shapes of a rotten criterion (14 lines, both cited by name from `../kickoff/AFK.md`). Each
is live behaviour reached by a run, so each is a KEEP, and **KEEP outranks every ceiling**.
The bin's own targets — the ones criterion 1 of the ticket names — are all met.

## 2. Table — KEEP / MOVE / DROP

One row per table unit of the original: every sentence that instructs, the `description`, the
fenced block, and the one term the ticket sends here for a verdict. Line numbers are the
original's. The `why` column is step 3's first half —
the run each rule reaches; its second half is answered once, below the table.

| where | sentence | verdict | why |
|---|---|---|---|
| frontmatter | `description`, 56 words | KEEP, rewritten | "Verify a delivery against the item's acceptance criterion, emitting the evidence block. Use when a slice lands, an item is declared done, or a skill needs the acceptance ruler." 29 words. Reached on every turn, so it pays the most per word. Its three branches are the skill's own: a slice lands (the north star position), an item is declared done (the hard gate), a skill needs the ruler. **It loses two things**: the leading words `north star` and `hard gate`, identity the body carries under *Two positions*, and "the next reader re-runs", which the body owns under *The caller re-runs it*. `acceptance` stays in the last branch on purpose — `../review/SKILL.md`'s description ends "needs the ruler or the inventory", and two always-loaded pointers claiming the bare token *the ruler* is a trigger collision. The leading word `Verify` is front-loaded, where the original opened on "Runs". |
| L6–9 | "**Verifying** is running the item's **criterion** — the acceptance line the item was born with (`A:` a deterministic check, `B:` the user's verdict; contract in `../kickoff/SKILL.md`) — against the tree actually delivered, and emitting **evidence** someone else can re-run." | KEEP | Every run: the leading word, the two criterion types and the deliverable. Split in two at 37 words. |
| L9–10 | "The criterion is read-only here: it is the ruler, and a ruler bent to fit the delivery measures nothing." | KEEP | Every run. It is the file's one anti-default: an agent whose criterion will not pass edits the criterion. |
| L10 | "A criterion that has to change belongs to the user." | KEEP | The run that finds its ruler wrong; merged into the sentence above, which keeps both halves in one place. |
| L16 | the **North star** row | KEEP | Every run after a slice that is not the last. It carries the regress exception, which is the only thing a north star result acts on. |
| L17 | the **Hard gate** row | KEEP | Every run on the final tree. |
| L19 | "One run yields one of three results: **passes** · **fails** · **does not execute**." | KEEP | Every run: the three results the outcomes are built from. |
| L19–20 | "At the hard gate those results resolve into outcomes; before it, they are only logged." | DROP | Duplicate: the two rows above already say the north star logs and the hard gate emits one outcome. |
| L24 | "A criterion A proves what the item promised, in the promise's own currency." | KEEP | Every type-A run, and the fit check that the outcomes section runs first. |
| L24–25 | "A behaviour promise → the behaviour exercised." | KEEP | A run on a behaviour item — the common branch. |
| L25–27 | "An **equivalence** promise (a refactor, a port, a rewrite) → an equivalence artefact: output byte-compared against real data, a differential fuzz across the two implementations, dumps compared on a copy of the real database." | KEEP | A run on a refactor or a port. Split in two; one of the three artefact examples went (§4 of `verify.md`). |
| L27–28 | "A green suite there proves the suite still runs, which is not what the item promised." | KEEP | The same run: it is what stops a green suite being accepted as an equivalence proof. |
| L30 | "The fixture carries the same weight as the currency." | KEEP | Every run whose subject has a real population. |
| L30–33 | "Run the criterion against the shape the data really has, not the smallest one the wording accepts: a criterion read as satisfied on a minimal fixture has passed while the same command failed on the populated form, the moment it met one." | KEEP, its evidence MOVEd → `docs/prune/verify.md` | The rule serves every run against a populated subject. The clause after the colon is a measurement, not a rule — the one piece of genuine inline evidence in the file, and `REPORT.md` sends it here. |
| L33–34 | "When the item's subject has a real population — a queue with tagged items, a file with prior content — that population is the fixture." | KEEP | The same run: it names what counts as the population. |
| L38–39 | "The first time a criterion A is run at all, prove once that it **can** fail: put the defect back and watch it fall." | KEEP | The first run of any criterion. No model does this by default. |
| L39–40 | "A criterion that passes with the defect back proves nothing, and it would carry a green evidence block all the way to the user." | DROP | Exposition of the sentence above it, which already carries the instruction and the reason. |
| L44–46 | "Exactly one holds, and the fit check in *The proof fits the promise* runs FIRST: a criterion that does not fit the promise is **rotten** whatever its exit code, so a satisfiable-but-wrong criterion reaches neither "approved" nor "proof ready", of either type." | KEEP, rewritten | Every hard gate: it is the ordering rule. Split in two at 42 words; the "reaches neither" clause went, since "whatever its exit code" carries it. |
| L46–47 | "What survives the fit check splits by type — within A, passed or failed 3×; within B, proof ready or failed 3×." | DROP | Duplicate: the four rows below are that split, column by column. |
| L48 | "Fewer than three failed attempts is not an outcome — it is a retry." | KEEP | A run whose first or second attempt failed. It is what stops a single red run being reported as an outcome. |
| L52 | the **Approved** row | KEEP | A passing type-A run. |
| L53 | the **Proof ready** row | KEEP | A type-B run; it carries the rule that a type-B item never merges unattended. |
| L54 | the **Failed 3×** row | KEEP | A run out of attempts. |
| L55 | the **Rotten criterion** row | KEEP | A run whose ruler is wrong; `../kickoff/AFK.md` routes to this row by name. |
| L59–61 | "**Unsatisfiable by construction** — no delivery could pass it. Say so **in writing before doing the work**, not after: name the contradiction and the criterion that would carry the same guarantee." | KEEP | A run that can see the contradiction before spending the budget. `AFK.md` cites the term. |
| L61 | "Work done against a broken premise is work to throw away." | DROP | Exposition of "before doing the work", in the same bullet. |
| L62–64 | "**Satisfiable but wrong** — it passes while measuring something else (the AST where the promise was behaviour; the suite where the promise was equivalence). Same outcome, same remedy." | KEEP | A run whose criterion is green and measuring the wrong thing. `AFK.md` cites the term. |
| L66 | "Both are honest outcomes and count as a finished run." | KEEP | Either rotten run: it is what stops the agent treating a rotten criterion as its own failure. |
| L66–69 | "The one thing that reaches the user is what was **measured**, which is why the criterion travels intact: an implementer that rewrites the ruler to make it pass returns a self-attestation, and the gate stops meaning anything from that item on." | DROP | Exposition of the read-only rule stated in the opening paragraph, 41 words. |
| L73 | "The ceiling of three applies at the hard gate." | KEEP | Every failing run: it says where the ceiling binds. |
| L73–74 | "Attempt 1 fails → fix the delivery and rerun; same for attempt 2." | KEEP | The first two failures. |
| L74 | "On the third failure, in this order:" | KEEP, rewritten | The third failure. It now names the outcome and `HANDOFF.md`, so the branch is reachable from the sentence that opens it. |
| L76–82 | handoff step 1, `tk-queue handoff` | MOVE → `tk/skills/verify/HANDOFF.md` | One branch of many, reached only by a run out of attempts. Three of its clauses were environment copies of `tk-queue handoff --help` and went with the move (§4 of `verify.md`). |
| L83–86 | handoff step 2, `tk-queue edit --class DECISION` | MOVE → `tk/skills/verify/HANDOFF.md` | Same branch, same file. |
| L87–88 | handoff step 3, `tk-queue release` | MOVE → `tk/skills/verify/HANDOFF.md` | Same branch, same file. |
| L81–82 | "It lives there rather than in the item because the queue item is size-capped." | DROP | Duplicate reason: the item's size cap is stated again two lines below, in step 2, where it changes what the reader types (`--force`). Dropped from step 1 rather than moved with it. |
| L88 | "The next session starts from the handoff." | DROP | Suspected no-op: nothing in the run changes on it, and the briefing's whole purpose is stated where it is written. |
| L92–93 | "Every caller of `tk-queue handoff` owes this step, and the five sites that prescribe a briefing route here for it." | KEEP | Every run that writes a briefing, from any route. The count of sites is a fact about the plugin's other files, not an instruction, and went; the sentence now reads "whatever brought it there", which is the same reach stated as a rule. |
| L95–96 | "`tk-queue handoff` writes the file, then warns on stderr, at exit 0, that the item carries no `[[handoff-T00N]]`." | KEEP | The same run. `exit 0` is the gotcha: the warning rides on a success. |
| L96–98 | "It prints the `tk-queue edit` that repairs the link, quoted for the shell and carrying `--force` where the link would cross the item's size ceiling." | KEEP | The same run. The `--force` clause went: the script puts it in the line it prints, and the instruction is to run what was printed. |
| L98 | "**Run the `edit` it prints.**" | KEEP, verbatim including its line break | The same run — the instruction the section exists for. `tk/tests/mutations_window_wall.py` anchors two mutations on this exact string and its wrap; §3 says what that costs a pruning pass. |
| L98–99 | "That pointer is the briefing's only discovery path, and a briefing no item names is one the next session never finds." | KEEP | The same run: the reason a reader does not skip the step. The second clause explains the first and went. |
| L101–102 | "The sequence above is the one exception: its step 2 writes the same pointer into `--deferred`, which answers the warning, so no second `edit` is due there." | MOVE → `tk/skills/verify/HANDOFF.md` | It is about the moved sequence and belongs beside it; reworded there to name its new neighbour. |
| L106–108 | "The evidence that carries a merge verdict is the criterion re-run **by the caller** — the orchestrator of a package, or the session accepting the work — once, on the final tree, after the last slice and before the wrap-up." | KEEP | Every run a caller collects. Split at 38 words. |
| L108–109 | "The implementer's report is an input to that run, never a substitute for it." | KEEP | The same run: `../wrap-up/SKILL.md` repeats it for its own reader, and this is the home. |
| L109–110 | "A subagent that returns with no evidence block did not pass: an empty return is a failure that reads as success." | DROP | Duplicate: `../kickoff/AFK.md` states it for the same reader under *An empty return is a failed attempt*, and `tk-contract` puts it in every subagent's block. |
| L114 | "Lives in the **body of the PR**." | KEEP | Every run: where the block goes. |
| L114–118 | "A session with no PR puts it on the item as it closes: `tk-queue done <id> --how "<pointer>" --note "<the block>" --force` — `--how` is required, and `--force` raises the field ceiling without removing it, so that form keeps the output to a single line." | KEEP | A run with no pull request. 44 words; two clauses went — `--how` being required is `tk-queue done --help`, and the single-line remark explains the flag rather than instructing. |
| L117–118 | "Either way the block is written once, here: a wrap-up digest, a reviewer or the next session reads and displays it rather than re-deriving it." | KEEP | Every run. `../wrap-up/SKILL.md` and `../../reference/vista.md` both rely on this being the single home. |
| L120–128 | the fenced evidence block, six fields | KEEP, byte-identical | Every run: it is the artefact. The eval in §5 grades exactly these six fields. |
| L130 | "Type B adds the artefact and its one-line claim in the same block." | KEEP | A type-B run. |
| L134–137 | "A criterion A already in the shape of the target repo's suite is **promoted**: commit it as an acceptance test named `acceptance_*`, and add one line to that repo's `CODING_STANDARDS.md` (or wherever it documents its standards) — "every delivered item carries its acceptance test; `acceptance_*` tests only get stronger"." | KEEP | A run whose criterion is already suite-shaped. 48 words, the file's longest; split at "Add one line". |
| L137–138 | "From then on the Standards axis of any code review watches it for free." | DROP | Exposition: it is the payoff, and the decision is already gated by "already in the shape of the target repo's suite". |
| L138–139 | "A criterion that is not in suite shape stays ephemeral, living in the evidence block." | KEEP | The other branch of the same run. |
| the term `north star` | the vocabulary unit the ticket sends to the table | KEEP, unmerged | It recruits a pretraining prior in exactly the sense the row uses, two sibling files this pass does not touch use it the same way, and its definition costs one cell the `Two positions` table pays for anyway. The reasons are set out under the table. |
| L141–143 | "**Done when:** exactly one outcome above is named for the item, its evidence block sits in the PR body (or the item's `--note`), and — for a 3× failure or a rotten criterion — the DECISION is already in the queue with its handoff." | KEEP | Every run: the completion criterion. Split at 42 words. |

**43 KEEP, 4 MOVE, 9 DROP**, over 56 rows.

### The vocabulary decision the ticket asks for

The table's `north star` row carries the verdict the ticket asks for — **it stays, as a
leading word, and is not merged**. These are the three counts it survives on. It recruits a pretraining prior — the fixed point you steer by —
and that prior is exactly the sense the row uses: the item's whole criterion, run after a slice
that cannot yet satisfy it. It is used with the same sense by two sibling files that this pass
does not touch, `../kickoff/AFK.md` and `../../reference/subagent-policy.md`, where a "north
star reached" is a seam at which work is pushed; merging it here would leave those two using a
word this skill had retired. And its definition costs one table cell that the `Two positions`
table pays for anyway. Against that, the only case for merging is the pair `north star` /
`hard gate` reading as decoration in the `description` — which is why the rewritten description
drops both, while the body keeps them.

`Verifying`, `criterion`, `evidence`, `regress`, `equivalence`, `rotten` and `promoted` are the
file's other coined or loaded terms. Each is defined once, in the file, and none is defined in
a sibling — the bin's `terms defined in a sibling too` is 0 before and after.

### The half of step 3 this pass could not answer

Step 3 asks two things of an own skill: name the run each rule serves, and say whether such a
run has happened since the rule was written. The first is the `why` column above, for every
row.

The second is unanswerable with the artefacts this machine has, and it is written once here
rather than guessed at per rule. Plugin telemetry counts invocations per plugin, so a counter
on `tk` says nothing about `verify`; `git blame` dates the sentence and not the run. That is **D6**, open.
No row above claims an answer to it.

## 3. Splits and notes

**Why no sibling pointer moved with the sequence.** Three sites send a reader to
`../verify/SKILL.md` "in the form it prescribes" and then add "(same file, *The item points at
the briefing*)". Repointing the first half at `HANDOFF.md` makes the second half's *same file*
false, so the pair moves together or neither does — and the briefing section is the one that
cannot move. Every such caller therefore lands in `Three attempts, then the queue`, whose one
sentence names the `tk-queue` sequence and the file holding it.

**One unit added, not removed.** The ticket asks the pruned skill for a single sentence of
site extensions, and `verify` carried none — the only skill of the four that reads a per-site
file without saying so. It now carries the two-line form `kickoff`, `wrap-up`, `dispatch` and
`review` all use, pointing at the README rather than restating the contract. It has no row in
§2, which rules on the original's units only.

**No splitting suggestion.** `verify` is one skill: every branch ends in the same artefact, the
evidence block, and the one branch heavy enough to leave the file left as a reference file
beside it — `SKILL-MECHANICS` splits by invocation, and nothing needs to invoke the handoff
sequence on its own.

**The MOVE that was measured and refused.** *The item points at the briefing* is the natural
second half of `HANDOFF.md`: five sites route to it by name, it is about the handoff rather
than about verifying, and moving it would have taken the file to 106 lines. It stays in
`SKILL.md` because moving it costs more than it buys, in two ways that only appear when you
try it. Seven pointers, in four files of two sibling skills, cite it as a section of
`../verify/SKILL.md`, and one of those files, `../kickoff/WINDOW.md`, is read verbatim by
`tk/tests/test_window_wall.py` — which
resolves every section name the wall's step 2 cites against the files that step names. And
`tk/tests/mutations_window_wall.py` anchors two mutations on the exact wording and line wrap of
"**Run the `edit` it prints.**", inside that section. Moving it turns a prose pull request into
a test change, against the ticket's own shape. The whole suite (771 tests) and that mutation
set (11/11 killed) are green on this branch, unedited — the artefact that the refusal held.

**Twelve clauses came out of sentences that stayed**, each quoted in `verify.md` §4 with the
sentence it left and what it carried. None is a verdict and none is a rewording, which is **D7**,
open. Six of the twelve are copies of `--help` output — the environment
as a source of truth — and that concentration is itself the finding: the class is not rare.

**Fourteen rewordings, carrying no verdict**, tabulated in `verify.md` §6. Nine of them are one
sentence split in two to bring a unit under the 25-word ceiling.

**Negations fell from 23 to 8** without that being a target of the pass. Most went with the
sentences they sat in; four are positive rewrites ("is a retry rather than an outcome", "a
different thing from what the item promised", "dies with it", "outside suite shape"). The
remaining eight are hard guardrails the ruler allows: "never by hand", "never a substitute",
"never merges", and the three results, where "does not execute" is the name of a result.

## 4. Paths

| file | what it is |
|---|---|
| `tk/skills/verify/SKILL.md` | the pruned skill, 115 lines |
| `tk/skills/verify/HANDOFF.md` | the destination of the third-failure MOVE, 18 lines |
| `docs/prune/verify.md` | every sentence, clause and wording removed, verbatim, and the one piece of inline evidence |
| `docs/prune/verify-report.md` | this file |

`prune/REPORT.md` defines the `docs/` file as the file of **inline evidence** pulled out of an
own skill. On this pass it holds one — see §6 on what the bin counted instead.

## 5. Proof of the target skill

A run of `verify` ends in an evidence block and in queue state, both of which a script can
check, so the proof is a `skill-creator` eval pair with the original as the control arm.

**Setup.** Two prompts, three arms, `n = 2` per real arm per prompt: 8 runs of the target skill,
Sonnet, each handed its arm's file by absolute path, forbidden the Skill tool and forbidden
`/root/.claude/`. Each arm is a copy of the whole `tk/skills/` tree, so every relative pointer
resolves identically; the arms differ only in `verify/`.

| prompt | what the run does | what the grader reads |
|---|---|---|
| P0 | a type-A criterion that fits a behaviour promise and passes; the caller accepts the delivery | `answer.md` — the six fields of the evidence block |
| P1 | three attempts have failed at the hard gate, with the history given and no budget for a fourth | the run's own queue directory afterwards |

P0 is the prompt the ticket asks for. P1 was added to attack what this pass actually moved:
its assertions read the filesystem `tk-queue` left behind, never prose.

**Grader.** Written by hand and before any run existed, exact: four literal-or-regex checks on
P0's `answer.md`, six on P1's queue directory and briefing file. No model judgement anywhere.

**Contamination.** `tk:verify` is installed on this machine and its installed copy is the
original, so a pruned-arm run could reach it for free. All 10 runs logged the files they read;
none names a path under `/root/.claude/`, and none invoked a skill.

**The control arm, and the two grader defects it exposed.** The broken arm is the pruned file
with the evidence-block section, its template and the third-failure route deleted. Its first
build left the **Failed 3×** outcome row standing, and that one cell was enough: the control
scored **6/6** on P1, which proves the assertion set and not the skill. It was broken again,
that row removed with it, and rerun. The same first control run also exposed two false
negatives in the grader, both repaired before any real arm ran: the briefing's heading is
`## Blockers and notes`, which the pattern for `## Blockers` refused; and the first P1 fixture
made an **equivalence** promise, so the fit check correctly returned *rotten criterion* rather
than *failed 3×*, and an assertion demanding `release` graded a step that route does not owe.
The fixture now makes a behaviour promise, and the ambiguity is gone.

**Result: parity, 20/20 against 20/20.**

| | original arm | pruned arm | control |
|---|---|---|---|
| P0, six-field evidence block | 8 / 8 | 8 / 8 | 1 / 4 |
| P1, the queue after three failures | 12 / 12 | 12 / 12 | 4 / 6 |
| tokens per run | 63 323 ± 4 098 | 59 349 ± 4 900 | — |
| wall time per run | 69.3 s ± 13.0 s | 68.7 s ± 26.7 s | — |

Both deltas favour the pruned arm and both sit well inside one standard deviation, so neither
is a result. The eight real runs cost **490 688 tokens** and 554 s of wall clock; the three
control runs (one of them the discarded first build) cost a further 207 622, for **698 310
tokens** over the whole eval. `n = 2`, taken from here and not from any `benchmark.md`, whose
aggregator writes `runs_per_configuration: 3` as a constant.

**What the control could not break, and what that says.** On P1 the control still scored 4 of
6: with the whole route deleted from the skill, a run still wrote the briefing with its three
fields and still pointed the item at it. Those four assertions are satisfied by `tk-queue`
itself — `--help` names the mandatory fields, and `handoff` warns on stderr and prints the
`edit` that repairs the link. Only `--class DECISION` and `release` fell. So the moved sequence
is, for four of its six graded effects, a **cache of the tool's own contract** rather than
behaviour the prose supplies. That is an argument for the MOVE beyond the line count, and it is
also the ceiling on what this prompt can measure.

**The MOVE was taken, and cost one file read.** Both pruned P1 runs opened `HANDOFF.md` — 4
files read against the original arm's 3 — and both then scored 6/6. The hop is made, not
skipped.

**What this eval does not show.** Every assertion passed in every run of both real arms, so the
set proves the pruned file loses none of the ten graded behaviours and cannot show it is
better. Three changes sit outside its reach, and the first is the riskiest in the diff:

- **the rewritten `description`** — untestable in this harness by construction, since every
  run was handed its arm's file by absolute path and none had to be triggered by the
  description. For a model-invoked skill that pointer is the whole trigger surface;
- **the fit check's rewritten sentence** — P0's criterion fits and P1's fits, so no run had to
  reject one; the *rotten criterion* route was exercised only by the discarded first fixture;
- **the twelve removed clauses**, none of which any assertion touches.

**One difference between what was measured and what ships.** The arms were taken at commit
`b5cde9a`. One sentence of `HANDOFF.md`'s opening was reworded afterwards; the pruned arm was
re-synced to the shipped file before the P1 runs, so P1 measured exactly what ships, and the
P0 runs — none of whose provenance names `HANDOFF.md` — ran against the earlier wording of a
file they never opened.

## 6. The four open findings, and what this run did with each

Four defects the `dispatch` pass found in the `prune` skill are still open, under the labels
that report gave them. None is fixed here: each is a ticket of its own on the tracker, and this
pass edits no file of the `prune` skill. Their ticket numbers are in this branch's pull request,
since a bare number in this public repo resolves against the wrong repository.

| # | what it holds open | what this run did |
|---|---|---|
| D5 | the report "is not committed" against a ticket that asks for it in the pull request | The ticket won: the report and the removed material are committed under `docs/prune/`, named file by file in `.gitignore`. The measurement was taken in `tk/skills/verify/`, where the files land, so the report never sat beside what the bin read — §1 says so in the numbers. |
| D6 | step 3 asks whether the run a rule serves has happened, and names no artefact that answers it | Answered once, in §2, as unanswerable with today's artefacts, with the reason. No row pretends otherwise. |
| D7 | a clause taken out of a surviving sentence gets neither verdict nor reworing row | All twelve are recorded in `verify.md` §4 anyway, verbatim, each with the sentence it left. Marked there as a record outside the contract. Six of the twelve are `--help` copies, which is new information about the class. |
| D8 | `REPORT.md` calls the `docs/` file inline evidence, and the `dispatch` pass measured 0 of it | **Measured.** The bin reports `inline evidence: 1` on `verify` and points at line 67, where "what was **measured**" is ordinary prose — a false positive. The file's one real piece of inline evidence, at line 31, the bin does not see. So `docs/prune/verify.md` carries what the contract names, for the first time, plus the removed prose the `dispatch` pass used it for. The finding for `#217` is not "0 again": it is that the counter is wrong in both directions on this file, so a pass cannot use it to decide what the `docs/` file holds. |
