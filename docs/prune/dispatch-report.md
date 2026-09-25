`docs/prune/dispatch-report.md`

# Pruning report — `tk/skills/dispatch/SKILL.md`

The first real run of `/tk:prune`. The material this pass removed is beside this file, in
`dispatch.md`; the pass's own output directory was `prune-out/dispatch/`, outside git.

Throughout, **run** carries the track's sense — one execution of the target skill — and the
pruning execution is a **pruning pass**. The eval's eight executions are eight runs of
`dispatch` in exactly that sense, so the word means one thing here. The table's unit is the
**table unit** that step 4 of `prune/SKILL.md` defines, never an "instructive sentence" as a
separate idea.

## 1. Numbers

`tk-prune-measure <file> --targets`, on the file before and after. **Bold** is a mark over the
bin's default ceiling.

| metric | ceiling | before | after | `LOOP.md` |
|---|---|---|---|---|
| lines | — | 88 | 60 | 15 |
| body words | — | 787 | 541 | 70 |
| sentences | — | 40 | 37 | 5 |
| mean words per sentence | 22 | 19.7 | 14.6 | 14.0 |
| max words in a sentence | 25 | **44** | 25 | 25 |
| sentences over 30 words | 4 | **8** | 0 | 0 |
| description words | 30 | **47** | 30 | — |
| inline evidence | 0 | 0 | 0 | 0 |
| pointers to other files | — | 15 | 13 | 3 |
| negations | — | 6 | 7 | 0 |
| defined terms | — | 1 | 1 | 0 |
| terms defined in a sibling too | 0 | 0 | 0 | 0 |

Three marks over a ceiling before, none after, on either file. Both were measured where they
land, in `tk/skills/dispatch/`, and not in the output directory beside the report; defect **D4**
below is why that distinction is not cosmetic.

**The "before" column is derived, and disagrees with this repo's own baseline.**
`docs/prune/baseline-2026-08-27.md` records 80 lines, 696 body words, 35 sentences and 5
sentences over 30 for the same path. Neither number is wrong: the file grew between the two
readings, in `fa204da`, which added the `/tk:fleet` bullet to the four-dispatchers list. The
column above is this branch's base, `origin/main`, measured for this pass.

### Why `dispatch` was the right first target — and why not for the reason the ticket gives

The ticket calls `dispatch` "the skill of worst sentence metric (51 words of mean, 339
maximum)". Those figures predate `tk-prune-measure`: they were taken when a markdown table read
as one unpunctuated sentence. Under the bin's sentence unit the same file measures 19.7 and 44.

**An earlier draft of this report replaced that premise with a second false one** — that
`dispatch` held the plugin's worst `max words in a sentence` and its second-worst
`description`. Measured with the bin over every `tk/skills/*.md` at `origin/main`, it holds
neither:

| file | max sentence | description |
|---|---|---|
| `kickoff/AFK.md` | 154 | — |
| `wrap-up/SKILL.md` | 126 | 36 |
| `kickoff/SKILL.md` | 68 | 41 |
| `kickoff/WINDOW.md` | 59 | — |
| `docs-audit/SKILL.md` | 56 | 23 |
| `fleet/SKILL.md` | 54 | 27 |
| `verify/SKILL.md` | 48 | **56** |
| `dispatch/SKILL.md` | **44** | **47** |
| `second-opinion/SKILL.md` | 42 | 24 |
| `review/SKILL.md` | 31 | **86** |
| `prune/SKILL.md` | 23 | 17 |
| `prune/REPORT.md` | 18 | — |

`dispatch`'s max sentence is eighth of twelve, and its description third worst behind `review`
and `verify`.

**The real reason is the one the ticket itself supplies, and it is not a metric.** The spec
allows a `skill-creator` eval only where a run of the target ends in an artefact a script can
check, and names exactly two skills that qualify: `dispatch` and `verify`. A first real run of
`/tk:prune` had to be one of those two, because the whole point of it was to carry the eval
alongside. Between them `dispatch` is the smaller file — 88 lines against 129 — so it is the
cheaper of the two places to find out what the pass does wrong. `dispatch` was chosen for
verifiable output and for size, not for its metrics.

## 2. Table — KEEP / MOVE / DROP

One row per table unit of the original: every sentence that instructs, plus the `description`
and the one fenced block a verdict relocated. Line numbers are the original's.

The bin counted 40 sentences where this table holds 35 rows. The difference is arithmetic, not
disagreement: four headings and one table header instruct nothing, and two wrapped list items
were each counted twice, because the bin flushes a chunk at a list-item line and the
continuation line becomes a unit of its own.

Where a verdict changed after the cold review of this branch, the row says so.

| where | sentence | verdict | why |
|---|---|---|---|
| frontmatter | `description`, 47 words | KEEP, rewritten | "Dispatch a task to the mechanism that runs it unattended — `/loop`, `/schedule` — delivering the ready-to-paste line. Use when delegating, scheduling or automating work, or when a skill needs the palette." 30 words. Reached on every turn, so it pays the most per word. **Revised after review:** the first rewrite dropped the leading word `Dispatch` and the trigger verbs `delegate`, `schedule`, `automate`, which for a model-invoked skill is the whole trigger surface. |
| L6 | "**Dispatching** is matching a task to the mechanism that executes it without the user — and delivering the ready-to-paste line, never just the mechanism's name." | KEEP | Every run: it is the leading word and the deliverable in one sentence. |
| L7 | "Diagnose the task against the palette, pick ONE line (when torn between two, the cheaper one) and write the complete command/prompt." | KEEP | Every run: the procedure, and the tie-break. |
| L11 | "**Site extensions:** read `~/.claude/tk/dispatch.md` and `.claude/tk/dispatch.md` (project root) if they exist — they name the site's concrete commands for the palette rows marked "(site extensions name it)"." | MOVE → README, "Site extensions" | Any run on a site with an extension file. The README owns the extension-file contract; the sentence keeps the two paths and points there, at 17 words. |
| L19 | "Needs conversation/context from this session \| inline, now (plan mode if large) \| the agent" | KEEP | A run whose task cannot leave the session. |
| L20 | "Verifiable end state (tests green, queue empty, everything compiles) \| `/goal` — ready line per the recipe below \| the user" | KEEP | A run with a measurable end state; eval 1 is this row. |
| L21 | "Agent-ready ticket on the tracker \| the site's per-ticket implementation flow (site extensions name it) — one ticket per fresh session \| the user" | KEEP | A run dispatching a published ticket. |
| L22 | "Queue of autonomous slices WITHOUT a single termination condition \| plain `/loop` over the project's `loop.md` (contract below), one slice per iteration \| the agent" | KEEP | A run dispatching a queue; its pointer now names `LOOP.md`. |
| L23 | "Big, foggy effort — the way to the destination isn't visible, too big for one session \| a charting flow that maps it into tickets (site extensions name it); then one map ticket per session \| the user" | KEEP | A run on an effort with no visible route. |
| L24 | "Reading/investigation legwork against external sources (docs, APIs, knowledge bases) \| a background research agent that leaves a cited markdown file in the repo (site extensions may name a command; fallback: a background subagent with that same contract) \| the user" | KEEP | A run on research legwork. Its fallback clause went; the file's global nearest-neighbour rule already carries it. |
| L25 | "Waiting on external state (CI, third party) \| Monitor — background script streaming the state (no polling); `/loop` with an interval only if there is no observable command \| the agent" | KEEP | A run waiting on something outside the session. **Revised after review:** the first pass trimmed `(no polling)`, which is the instruction separating Monitor from an interval `/loop`. The row now reads "a script streaming state, not polling". |
| L26 | "Same operation over MANY items (sweep, mass migration) \| dynamic workflow (site extensions name it) — pilot on a small slice before the full sweep \| the user" | KEEP | A run on a mass sweep. |
| L27 | "Recurring (routine, not a one-off item) \| `/schedule` (cloud) or local cron — draft the COMPLETE routine: it runs without a human and without permission prompts, so the prompt is self-contained, with the done criterion embedded and a recommended model (mechanical routine → smaller model) \| the agent" | MOVE → the recipes section of the same file | A run on a recurring routine; eval 0 is this row. At 44 words it was the file's longest unit, and a routine contract is a recipe rather than a table cell. **Revised after review:** the destination had narrowed the rule to "a smaller model for mechanical work", silent about every other routine — a partial deletion wearing a MOVE label. It now reads "a model recommended — the smaller one for mechanical work". |
| L28 | "Context-independent and parallelizable \| background subagent (isolated worktree) \| the agent" | KEEP | A run that parallelizes. |
| L30 | ""The user" dispatches are native commands the agent doesn't invoke: deliver the ready-to-paste line, with the `/goal` condition or the workflow prompt already written." | KEEP | Every run landing on a "the user" row: it stops the agent trying to fire the command. |
| L31 | "If a mechanism doesn't exist in the session, use the nearest neighbour." | KEEP | A run in a session missing a mechanism. Now also carries the research row's dropped fallback. |
| L36 | "The evaluator only reads the conversation, it doesn't run commands; the ready condition carries: a measurable end state, the command that proves it ("`npm test` exits 0"), the constraints ("without touching other tests") and a cap ("or stop after 20 turns")." | KEEP | Every `/goal` run; graded by three of eval 1's four assertions. Split in two, at 41 words, and its example of a constraint went. |
| L42 | "`/loop` dies with the session and expires in 7 days — a queue that must survive goes to `/schedule`." | KEEP | A run choosing between `/loop` and `/schedule`; both eval-0 arms cited it. |
| L43 | "Scheduled fires only execute model-invocable skills: to schedule work from a `disable-model-invocation: true` skill (kickoff, wrap-up), point the prompt at the skill's file in the plugin's install folder ("follow `skills/wrap-up/SKILL.md` of the `tk` plugin")." | KEEP | A run dispatching a locked skill. Reworded into the rule and the instruction, and now covers the subagent case too. |
| L46 | "The same lock rules out dispatching such a skill to a subagent **by name**: a prompt reading "run `/implement`" reaches an agent that cannot invoke it, and the run dies there." | DROP | Duplicate: the surviving rule states the lock once, for the scheduled fire and the subagent together. |
| L48 | "Pointing a subagent at the FILE works, for the reason the scheduled fire above works — the lock is on invoking the command, and it does not reach a file being read." | DROP | Duplicate: the same rule's second half, stated a third time. |
| L49 | "`../fleet/SKILL.md` dispatches every one of its project runs on that route." | KEEP, rewritten | **Reversed after review.** The first pass DROPped it as a no-op claim about a sibling skill. `slice-rules.md` legislates that exact shape: such a claim is rewritten as a requirement on the reader, because deleting it retires a decision in silence — and `fleet/SKILL.md` carries the reciprocal pointer, so the decision was live. It now reads "Take the same route for every project of a fleet dispatch (`../fleet/SKILL.md`)." |
| L52 | "What no subagent can open is a **generation**: `../kickoff/WINDOW.md` reserves that for a scheduled fire or the user's own first line, because a generation succeeds the session rather than running inside it." | KEEP | A run asked to open work outliving the session. Its causal clause went; `WINDOW.md` owns the reason and the pointer stays. **Revised after review:** the first pass had rewritten the term as "work that outlives one run", which is a different concept — a long-running background subagent satisfies it, while `kickoff/WINDOW.md` says a subagent is not a generation. Two shipped files contradicted, and the bin cannot see it, since `terms_defined_in_sibling` scopes to the skill's own directory. The defining property is restored. |
| L54 | "So where a locked skill must open work that outlives one run, the dispatch delivers the line the user types rather than a subagent." | KEEP | The same run: this is the instruction the rule above exists for. `rather than a subagent` is back with it. |
| L57 | "The `next-steps.md` queue (contract: `../kickoff/SKILL.md`, relative to this file) has four dispatchers, by presence and scope:" | KEEP | A run dispatching the queue rather than one task. |
| L60 | "**interactive kickoff menu** — the user is present and chooses;" | KEEP | The queue run with the user present. |
| L61–62 | "**`/tk:kickoff afk` / `pack`** — one-shot package run by an orchestrator + background subagents, context-isolated (`../kickoff/AFK.md`);" | KEEP | The queue run with nobody present. The contrast with the next row is the whole value of this list. |
| L63 | "**`/loop` over `loop.md`** — same-session slices, context accumulates across iterations;" | KEEP | The queue run inside one session. **Revised after review:** it now carries `LOOP.md`, the moved contract's second pointer, since this list is where a reader arriving from `../kickoff/SKILL.md` lands. |
| L64–65 | "**`/tk:fleet`** — every project's queue on this machine at once, one full orchestrator per project at `--budget 1` (`../fleet/SKILL.md`)." | KEEP | The queue run across every project; reachable from no palette row. |
| L67 | "Tickets published on the issue tracker are dispatched by the site's per-ticket flow, one ticket per fresh session — the tracker is their source of truth." | DROP | Duplicate of the palette's ticket row, word for word on the dispatch and the one-ticket rule. |
| L72 | "`.claude/loop.md` at the project root replaces plain `/loop`'s default prompt — it turns `/loop` (5 keystrokes) into the dispatcher of the `next-steps.md` queue." | MOVE → `tk/skills/dispatch/LOOP.md` | One branch of ten. Reference every branch pays for and one branch reaches, which is where progressive disclosure applies. |
| L73 | "When dispatching a queue of slices for the first time in a project, create the file; on later runs, check it still matches the contract:" | MOVE → `tk/skills/dispatch/LOOP.md` | Same branch, same file. |
| L77–82 | the fenced `loop.md` template | MOVE → `tk/skills/dispatch/LOOP.md` | Same branch; byte-identical after the move. |
| L84 | "Edits to `loop.md` take effect on the next iteration; the file belongs to the project (versionable), the queue stays in auto-memory." | MOVE → `tk/skills/dispatch/LOOP.md` | Same branch, same file. |
| L87 | "**Done when:** the user received ONE mechanism (with the why in 1 sentence) and the complete ready-to-fire line/prompt — or the task turned out to be inline and that was said." | KEEP | Every run: it is the completion criterion. |

26 KEEP, 6 MOVE, 3 DROP.

### The run behind each rule, and the half of step 3 this pass could not answer

Step 3 of the skill asks two things of an own skill: name the run each rule serves, and say
whether such a run has happened since the rule was written. The first is the `why` column above.

The second was not answered, for any rule, and the reason is in the defect list below as **D6**.
Nothing in reach dates a run of one skill: the harness counts plugin invocations per plugin, not
per skill, so a large counter on `tk` says nothing about `dispatch`. Answering per rule would
mean dating each sentence by `git blame` and then searching session transcripts for a dispatch
run after that date — 33 searches, more than the pass costs.

## 3. Splits and notes

**No splitting suggestion.** `dispatch` is one skill: every palette row ends in the same
deliverable, and the one branch heavy enough to leave the file left as a reference file, not as
a skill of its own — `SKILL-MECHANICS` splits by invocation, and nothing else needs to invoke
the `loop.md` contract.

**Four clauses came out of sentences that stayed**, and a fifth was taken and put back. Each is
quoted in `dispatch.md`: the research row's fallback; the generation rule's causal clause; the
`/goal` recipe's example of a constraint; where the locked skill's file sits; and `(no polling)`,
which the cold review caught and the correction batch restored. None of them is a verdict and
none is a rewording, which is defect **D7** — and the one that went missing entirely is the
evidence for it.

**Rewordings, carrying no verdict.** Fourteen, tabulated in `dispatch.md` so that no word of the
diff is unexplained: the lock rule's opening, two `x/y` compounds, the queue pointer's "relative
to this file", "by presence and scope", "implementation" in the ticket row, "(project root)",
the fleet and afk bullets, the `/loop` bullet, the foggy and research rows, and the three
sentences of `LOOP.md`.

## 4. Paths

| file | what it is |
|---|---|
| `tk/skills/dispatch/SKILL.md` | the pruned skill, 60 lines |
| `tk/skills/dispatch/LOOP.md` | the destination of the `loop.md` MOVE, 15 lines |
| `docs/prune/dispatch.md` | every sentence, clause and wording removed, verbatim |
| `docs/prune/dispatch-report.md` | this file |

`prune/REPORT.md` defines the `docs/` file as the file of **inline evidence**, and the bin
measured 0 of it here. Why this file holds removed prose instead, and the ticket that settles
it, are written once — at the top of `dispatch.md`.

## 5. Proof of the target skill

A run of `dispatch` ends in a ready-to-paste line, which a script can check, so the proof is a
`skill-creator` eval pair with the original as the control arm.

**Setup.** Two prompts, two arms, `n = 2` runs per arm per prompt: 8 runs of the target skill,
Sonnet, each given the arm's file by absolute path and forbidden the Skill tool. Both arms ran
against a copy of the whole `tk/skills/` tree, so every relative pointer resolved identically;
the arms differ only in `dispatch/`.

**`n = 2`, and `benchmark.md` says 3.** The aggregator writes `runs_per_configuration: 3` as a
constant, whatever it read. Its own line "(3 runs each per configuration)" is false for this
run. Take `n = 2` from here.

**Contamination.** `tk:dispatch` is installed on this machine, and the installed copy was the
original for the whole eval. All 8 runs logged their reads; none touched the installed skills
directory under `~/.claude/skills/` and none invoked a skill. The check is mechanical and lives
in the grader.

**Grader.** Written by hand, exact: four literal-or-regex checks per prompt over `answer.md`,
no LLM judgement. The mechanism token and the proving command are two of the four, as the ticket
asks; the other two are the paste-ready block and, per prompt, the model recommendation or the
cap.

**The grader's own first draft was wrong, three times, and all three were false negatives.** It
demanded a paste-ready block of at least three lines, and both arms of prompt 0 run 2 had
delivered a correct one-line fenced block; its model synonyms missed "a small/cheap model"; and
its cap pattern missed "after 15 failed attempts", where a word sits between the count and its
unit. Each repair was checked against the answer that exposed it, applies to both arms, and was
made before any number below was taken.

**Result: parity, 16/16 against 16/16.**

| | original arm | pruned arm | delta |
|---|---|---|---|
| pass rate | 100% ± 0% | 100% ± 0% | 0 |
| assertions passed | 16 / 16 | 16 / 16 | 0 |
| wall time per run | 65.2 s ± 33.2 s | 61.4 s ± 20.6 s | 3.7 s |
| tokens per run | 55 672 ± 2 499 | 54 439 ± 2 016 | 1 234 |

Time and tokens are reported against no target, as the ticket asks. Both deltas favour the
pruned arm and both sit far inside one standard deviation, so neither is a result. Eight runs
cost 440 445 tokens and 506 s of wall time, over two waves of four.

**What this eval does not show.** Every assertion passed in every run of both arms, so the set
does not discriminate: it proves the pruned file loses none of the four behaviours, and it
cannot show the pruned file is better. Four changes sit outside its reach, and two of them are
the riskiest in the diff:

- **the rewritten `description`** — untestable in this harness by construction, since every
  executor was handed its arm's file by absolute path and no run had to be triggered by the
  description at all. For a model-invoked skill that pointer is the entire trigger surface;
- **the `generation` reword** — the cold review, not the eval, caught it redefining a term
  against `kickoff/WINDOW.md`. No assertion here touches the boundaries section;
- the dropped fallback in the research row, which no prompt exercised;
- the `LOOP.md` hop, which neither prompt made the agent take.

The eval numbers were taken before the correction batch and were not re-run after it. The batch
restores base wording in every case rather than inventing new, so the graded behaviours are
unchanged; that is an argument, not a measurement, and it is worth exactly that.

## 6. Defects this run found in the `prune` skill

Fixed in this pull request, each a sentence:

| # | defect | fix |
|---|---|---|
| D1 | `exposition range` is coined in step 4 and used again under "The table", and never defined — against the skill's own rule that a coined term is defined once or replaced. | Step 4 defines it. |
| D2 | This pass moved a sentence into another section of the same file, and `REPORT.md`'s "Where a MOVE goes" table had no destination covering it. A cell of paper is neutralised by a row in the table. | A row added. |
| D3 | Step 5 says "save every pruned file", which does not name `LOOP.md` — a file that did not exist before the pass and that a MOVE created. Its completion criterion had the same gap. | Both now read "every file the pass wrote". |
| D4 | **Step 5 contradicted its own completion criterion.** It says to save the report side by side with the pruned files, and the criterion is that the bin then reads each of those files inside the targets. The bin reads every markdown file in a directory as a sibling, and this report quotes the skill's `**Dispatching**` definition — so measured in the output directory the pruned copy read `terms defined in a sibling too: 1`, marked over, and measured where it lands it reads 0. Any report quoting a bolded term of its target does this. | The criterion now says the file is measured where it lands and not beside the report. |

A fifth edit to `prune/REPORT.md` is **not** a defect fix and is listed because criterion 4 asks
for the whole list: "A pass that found nothing to prune writes that line, then `nothing to
prune`" was deleted to keep the file at its 30-line cap while D2's row went in. Nothing is lost
— `prune/SKILL.md` carries the same rule under "Nothing to prune" — but the deletion was paid
for by the cap, not chosen on its merits. `prune/SKILL.md` now sits at exactly 90 and
`REPORT.md` at exactly 30, so the next slice that finds a sentence-level defect must delete a
sentence to fix it.

Design, filed on the tracker rather than patched here — one ticket each, their numbers in this
branch's pull request, since a bare number in this public repo would resolve against the wrong
repository:

| # | defect | why it is not a sentence |
|---|---|---|
| D5 | The skill says the report "is not committed", and the closing review it hands the user reads a committed diff with the table as the Spec axis's input. This house's pruning ticket also asks for the report in the pull request. Where the report lives, and whether the review can reach it, is unsettled. | It changes what a pruning pass delivers, and where. |
| D6 | Step 3 asks whether the run a rule serves has happened since the rule was written, and names no artefact that answers it. Plugin telemetry counts per plugin, not per skill; `git blame` dates the sentence but not the run. | Either the step names an artefact, or it drops the demand — a decision, not a rewording. |
| D7 | A table unit is a whole sentence, but a palette row carries several instructions, and removing one of them is neither a verdict nor a rewording. Five such clauses came out of `dispatch`, and the one that mattered most — `(no polling)` — reached the pull request with no record at all, because nothing obliged the pass to keep one. | The unit's definition would have to change, and every rule about verdicts with it. |
| D8 | `REPORT.md` defines the `docs/` file as the file of inline evidence, and the bin measured 0 of it on this skill. The file was used for removed prose instead, which is what a real pass needs and is not what the contract says. | Part 4 of `REPORT.md` and the MOVE destination table change together. |
