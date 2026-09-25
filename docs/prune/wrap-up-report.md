`docs/prune/wrap-up-report.md`

# Pruning report — the `wrap-up` skill

The sixth run of `/tk:prune`, executed as prune 8/8 — the last slice of the pruning
track's spec — over the last of the three big skill files. The removed material is beside
this file, in `wrap-up.md`, keyed to the pre-prune original at commit `4127fa9` (`W:` +
line number). Like the 7/8 pass this one ran inside an unattended package, so the pass
edited the skill in its branch directly and the branch is what the closing review reads.
**First pass over this skill**: no earlier committed report exists, so no rule needed the
step-3 date check against one.

## 1. Numbers

`tk-prune-measure <file> --targets`, before and after. **Bold** marks a value over a
ceiling — the bin's, or the ticket's line ceiling (150), which the bin does not carry.

| metric | SKILL.md before | after | MERGE-GATE.md (new) | REPORT.md (new) |
|---|---|---|---|---|
| lines (ticket: ≤150 / — / —) | 498 | **172** | 205 | 88 |
| body words | 5236 | 1696 | 2225 | 706 |
| sentences | 235 | 81 | 107 | 28 |
| mean words per sentence (22) | **22.3** | 20.9 | 20.8 | **25.2** |
| max words in a sentence (25) | **126** | **57** | **99** | **60** |
| sentences over 30 words (4) | **54** | **20** | **21** | **8** |
| description words (30) | **36** | 30 | — | — |
| inline evidence (0) | **7** | 0 | 0 | 0 |
| pointers to other files | 23 | 20 | 5 | 1 |
| negations | 89 | 21 | 28 | 22 |
| defined terms | 3 | 1 | 2 | 2 |
| terms defined in a sibling too (0) | 0 | 0 | 0 | 0 |

The siblings' over-ceiling sentences are KEEPs carrying a verdict, a refusal or a check,
and KEEP outranks every ceiling; `REPORT.md`'s mean rides on its template fence, whose
placeholder lines the bin reads as sentences. The four `defined terms` of the after
columns are one real coinage each (**gate** in SKILL.md, **digest** in MERGE-GATE.md)
plus detector hits on bold-opened rule sentences, none re-coined anywhere.

**Why the SKILL.md `lines` mark stands, rule by rule** (the ticket's ceiling is 150):

- The remainder over 150 is exactly the two blocks the pruned kickoff SKILL.md (120
  lines) does not carry: the survival-gates block of step 2 (the table with its record
  rule, ~19 lines) and the inline `afk` section (~28 lines). Kickoff's unattended form
  lives in a 327-line sibling of its own; wrap-up's ticket names two siblings —
  `MERGE-GATE.md` and `REPORT.md` — and neither may own these: the afk spine spans steps
  1–6, not the gate, and the survival gates are step 2's own verdict rule, read on every
  attended close.
- Every line now in the file names a behaviour a run reaches; the classes the ceiling
  could still buy — inline evidence (7→0), duplicates, the queue-contract restatement,
  the step-5 and step-6 bodies — are already out. 172 − 150 = 22, and the two blocks
  above are 47 lines: the ceiling is reachable only by descending one of them, i.e. by a
  third sibling the ticket does not create. That split is not suggested: 28 lines is
  below what a file of its own repays, and the gates are core attended behaviour.
- `sentences over 30` stands for the same reason as in the earlier passes: the survivors
  are dense rule sentences, and splitting them adds lines, the one metric the ticket caps.

The three big files against the 1/8 baseline (`baseline-2026-08-27.md`), body words:

| | baseline 27/08 | at this pass's start | after both prunes |
|---|---|---|---|
| `kickoff/SKILL.md` | 4221 | 1096 (pruned 7/8) | 1096 |
| `kickoff/AFK.md` | 5342 | 3436 (pruned 7/8) | 3436 |
| `wrap-up/SKILL.md` | 4499 | 5236 | 1696 |
| **the three files** | **14062** | 9768 | **6228** |

The ticket's "14.5k" is the baseline total, rounded up. What remains and why: 6228 words
in the three files — 44% of baseline — every one on a rule a run reaches. The material
did not all vanish: 4500 words now live at four destinations more than one reader
reaches — `tk/reference/queue.md` (1130) and `tk/reference/session-finding.md` (439)
from the 7/8 pass, `MERGE-GATE.md` (2225) and `REPORT.md` (706) from this one — read
only when their condition holds, which is the point of the split: an attended close with
no pending version-control action loads 1696 words where it loaded 5236.

## 2. The table

One row per unit or range; ranges and every verbatim quote are in `wrap-up.md` beside
this file (its §§1–6), so the rows cite rather than repeat them. `where` cites the
original at `4127fa9`.

| where | sentence / range | verdict | why |
|---|---|---|---|
| W:3 | the `description` | rewritten | 36 → 30 words; the clauses it loses are `wrap-up.md` §6 |
| W:7–17 | intro — definition, resolve-here, fixed template | KEEP | compressed; **gate** coined here once (see fusion rows) |
| W:19–23 | argument + site extensions | KEEP | every run reads them |
| W:25–49 | step 1 — sweep, fetch-first, findings menu | KEEP | compressed; rationale ranges DROP (§5); the session-finding definition MOVE (below) |
| W:39–45 | the session-finding definition | MOVE | → pointer to `tk/reference/session-finding.md`, where the 7/8 slice coined it; one term, one definition |
| W:51–56 | step 2 memory rules | KEEP | type list CLAUSE (§4) |
| W:59–74 | the tk-queue contract restatement | DROP | duplicate — `tk/reference/queue.md` carries it since 7/8; the criterion-here and ask-the-DECISION rules stay |
| W:76–93 | the three survival gates, record rule, disjunction | KEEP | step 2's own verdict rule; the versioning-gate aside DROP (§3, fusion) |
| W:95–110 | RECURRING + encode + done-when | KEEP | compressed; exposition DROP (§5) |
| W:112–139 | steps 3–4 | KEEP | compressed |
| W:141–307 | step 5 whole — trail sections, digest, five verdicts, verdict-5 triple check, menu, stack order, accumulated lane | MOVE | → `MERGE-GATE.md`; criterion: read only when the gate has pending actions. Inbound pointers below |
| W:169–170 | "Dossier is the term here; briefing names the step-6 handoff file" | DROP | dies with the fusion — nothing left to disambiguate |
| W:311–378 | the closing template and its rules | MOVE | → `REPORT.md`; criterion: the template is read at write time, by this skill and by fleet. Inbound pointers below |
| W:386–407 | the handoff, two levels, CONCLUSIONS rule | KEEP | compressed; `briefing` → the handoff file (fusion row) |
| W:408–453 | the next step — the four paths | KEEP | compressed; the two opening-sentence shapes MOVE → `REPORT.md`, *The opening sentences* (docs-audit's citation target) |
| W:455–498 | the `afk` argument | KEEP | compressed; the strict-merge detail MOVE → `MERGE-GATE.md`, *The strict form* |

## 3. Splits, fusions and notes

**Vocabulary fusions** — each collapses terms that named one object, one row per fusion:

| terms before | term after | coining line | what changed |
|---|---|---|---|
| dossier × digest | **digest** | `MERGE-GATE.md:9` — "The digest is what the user reads instead of the diff: it says WHAT is being merged and whether it MAY be merged." | the five trail sections and the five verdicts are one artefact; `digest` was already the plugin-wide word (`vista.md`, `AFK.md`, `verify/SKILL.md`), `dossier` appeared nowhere else |
| briefing × handoff | **the handoff file** | none — described by its writer, `tk-queue handoff`; `verify/SKILL.md` keeps its own section title *The item points at the briefing*, cited as a title, not re-coined | wrap-up's uses of `briefing` become "the handoff file"; the citation into verify is the one place the old word remains, as a quoted heading |
| survival gate × versioning gate | **gate**, qualified | `SKILL.md:12` — "a gate is what lets a pending object leave the session unresolved" | one coinage; "survival" and "versioning" are qualifiers at use sites, and the aside that told the two coinages apart (W:84) died |

**Split suggestion — ticket #226 on the config repo**: the merge gate as a skill of its
own. `SKILL-MECHANICS` criterion: self-contained procedure with its own entry moment;
consumers: `/tk:wrap-up` step 5 (direct), the afk tail (`AFK.md` step 7 chains the afk
wrap-up, whose step 5 is the gate; its lane tail cites the per-item digest), and fleet —
transitively only: fleet step 4 dispatches kickoff with the `afk` load, `AFK.md` step 7
chains the wrap-up, whose step 5 is the gate; `fleet/SKILL.md` never references the gate
directly. Nothing executed in this branch.

**The plugin-wide term sweep** (this ticket's one-off; the bin's `dup` column only reads
same-directory siblings — extending it is ticket #219): `tk-prune-measure --json` over
every `tk/skills/**/*.md` and `tk/reference/*.md` (fixtures excluded), `defined_terms`
grouped case-insensitively across files. Result: after this pass, exactly one term was
defined in two files — **vista**, coined in `tk/reference/vista.md` (its contract) and
re-coined in `tk/skills/fleet/SKILL.md:244`. Fixed here: fleet's bold coinage became a
plain reference naming `vista.md` as the coinage's home. Every other multi-file hit is
zero; `session finding`, `gate` and `digest` each have one coining file.

**Rewording note (no verdict)**: the file was rewritten sentence by sentence to carry the
same rules in fewer words; `wrap-up.md` and `git show 4127fa9:tk/skills/wrap-up/SKILL.md`
hold every original.

### The MOVEs' inbound pointers (grepped over the plugin), with their rewrites

| pointer | was | now |
|---|---|---|
| `tk/skills/fleet/SKILL.md:243` | template in `../wrap-up/SKILL.md`, *The closing template* | `../wrap-up/REPORT.md` |
| `tk/skills/kickoff/AFK.md:266` | `../wrap-up/SKILL.md`'s per-item digest | `../wrap-up/MERGE-GATE.md`'s per-item digest |
| `tk/skills/docs-audit/SKILL.md:84` | step 6 decides wording and opening sentence | step 6 decides wording; shapes at `../wrap-up/REPORT.md`, *The opening sentences* |
| `tk/skills/kickoff/AFK.md:311–314` (step 7) | "the close owns … the five verdicts … and the closing template" | unchanged on purpose: the close still owns them — `SKILL.md` reaches both siblings by its own pointers, and step 7 enters at the file, not at a section |
| `tk/skills/verify/SKILL.md:90` ("a wrap-up digest") | — | unchanged: `digest` survives the fusion as the term |
| `tk/reference/vista.md`, `tk/reference/subagent-policy.md` (gate/digest mentions) | — | unchanged: they name the gate and the digest, not a section path |

## 4. Paths

- Pruned in place, this branch: `tk/skills/wrap-up/SKILL.md`, plus the three pointer
  rewrites and the fleet vista un-coinage above.
- Created: `tk/skills/wrap-up/MERGE-GATE.md`, `tk/skills/wrap-up/REPORT.md`.
- Removed material: `docs/prune/wrap-up.md`, allowlisted file by file in `.gitignore`
  like its siblings. The branch touches no bin.

## 5. Proof of the target skill

The target is prose, so the proof is the reviewed diff of rules — this pass runs inside
an accumulated lane, where the two-axis review fires ONCE over the lane's whole diff at
the package's tail (smell baseline declared inapplicable, the `writing-for-agents` path
and this table handed to the axes). No `tk/tests` file anchors on wrap-up prose (the one
mention, `test_window_wall.py:21`, is a docstring naming it as a non-prescribing site),
so the executable arm is the whole suite unchanged: 771 tests plus 411 subtests green on
the pruned tree. (The kickoff report's 409 subtests were true when measured: this pass adds
`MERGE-GATE.md` and `REPORT.md`, and the shipped-skills sweep in `test_tk_prune_measure.py`
counts one subtest per `.md` file under `tk/skills/` — hence +2.) The mutation harnesses (`tk/tests/mutations*.py`) remain the suite's
broken-arm proof.

---

# Pass 2 — 2026-09-16 (T410)

The second pruning pass over the same skill, fifteen days after the first. It created no
destination and coined no term: every verdict is a cut, and the removed text is in
`wrap-up.md` beside this file (§§7–8), keyed to the pre-pass tree at commit `89ed5d0`.

**Why a second pass.** The first left `SKILL.md` at 172 lines / 1696 body words, and
`tk/tests/prune-lock.json` locked those two numbers with 10% slack. Ten commits of new
rules later the file measured 189 / 1865 — the ceiling to the word, on both numbers. The
lock was still green and the next sentence added would have reddened it, which is the
state the item (T410) was raised for. The sibling `REPORT.md` was in the same place:
88 / 706 locked, 92 / 776 measured.

## 1. Numbers

`tk-prune-measure <file> --targets`, before and after. **Bold** marks a value over a
ceiling. `lock` is the number `prune-lock.json` holds, and `slack` its +10%.

| metric | SKILL.md lock | before | after | REPORT.md lock | before | after |
|---|---|---|---|---|---|---|
| lines (slack) | 172 (189) | **189** | 180 | 88 (96) | 95 | 92 |
| body words (slack) | 1696 (1865) | **1865** | 1731 | 706 (776) | **776** | 724 |
| sentences | — | 92 | 90 | — | 31 | 29 |
| mean words per sentence (22) | — | 20.3 | 19.2 | — | **25.0** | **25.0** |
| max words in a sentence (25) | — | **57** | **57** | — | **60** | **60** |
| sentences over 30 words (4) | — | **20** | **19** | — | **9** | **8** |
| description words (30) | — | 30 | 30 | — | — | — |
| inline evidence (0) | — | 0 | 0 | — | 0 | 0 |
| pointers to other files | — | 23 | 23 | — | 2 | 2 |
| negations | — | 23 | 21 | — | 23 | 23 |
| defined terms | — | 1 | 1 | — | 2 | 2 |
| terms defined in a sibling too (0) | — | 0 | 0 | — | 0 | 0 |

Both files end under every number they entered with, and neither gained a ceiling mark —
the two conditions `test_prune_lock.py` asserts. The marks that stand are the ones the
first pass left standing, for the reason it recorded: the survivors are dense rule
sentences, and splitting them buys words at the price of lines.

`pointers` held at 23 and the set is unchanged: no verdict of this pass touched a path,
a section title or a command, so no inbound pointer needed rewriting. Grepped to confirm
it — `cold reader` still resolves (`REPORT.md:7`, its single source of truth), and the
dropped step-1 sentence is cited nowhere in the plugin.

## 2. The table

**Scope, and the rule that sets it.** Step 3 of the pruning skill dates the target against
its committed report: a rule edited after the report was never graded by a pass. Here the
report is 01/09 and the file's last edit 16/09, so the ungraded set is exactly what the
file gained or changed since `91ae088` — ten commits, +169 words. Those units hold a row
below. The units that survived pass 1 unchanged hold their rows in that pass's table
above, and a row below repeats one only where this pass cut into it.

`where` cites `89ed5d0` (`W2:` = `SKILL.md`, `R2:` = `REPORT.md`); the verbatim text of
every DROP and CLAUSE is in `wrap-up.md` §§7–8.

| where | sentence / range | verdict | why |
|---|---|---|---|
| W2:5 | `argument-hint: "[afk]"` | KEEP | every run: the selector announces the one argument; frontmatter, not body |
| W2:13–15 | the two gates, each with what it admits | CLAUSE | steps 2 and 5 each define what their own gate admits; the enumeration restated it |
| W2:28–29 | "every other signal reads this disk only" | CLAUSE | exposition behind "The fetch comes first", whose own reason (the sibling clone) stays in the sentence |
| W2:31–33 | "The inventory drives the rest: no code change → step 4 skips the suite; …" | DROP | duplicate: step 3 opens "Runs when the inventory shows changed behaviour", step 4 "Runs when code changed", step 5 reads the inventory for its list. Step 1's "Done when" still requires each later step marked run/skip |
| W2:37–38 | "each answer can still change memory, docs or the queue below" | CLAUSE | the reason the menu fires before step 2; the instruction ("right after printing it, ONE batched `AskUserQuestion`") carries the placement |
| W2:74–77 | the consolidation of what a package queued | KEEP | ungraded (05/09): the run is an unattended package's close; held by `tk/tests/test_wrap_up_consolidation.py`, which asserts the fold's two tests and the `edit`-before-`cancel` order |
| W2:79–82 | the mechanical error, and `/retro` named when it is on disk | KEEP | ungraded (15–16/09, T409): the run is any session that corrected a fixed pattern once |
| W2:83–85 | step 2's "Done when", with consolidation counted | KEEP | the step's completeness check; the consolidation test reads it |
| W2:92–93 | "this is where conversation-only understanding gets a written address" | CLAUSE | step 6 owns the branch ("conversation-only, document it in step 3"); the same rule was written at both ends |
| W2:101–102 | "a green test doesn't prove the real flow works" | CLAUSE | the reason under an instruction that already prescribes the end-to-end run |
| W2:112–113 | "this gate is what makes the wrap-up a real close" | CLAUSE | the opening paragraph already defines a close that leaves silent pendings as no close |
| W2:114–118 | the gate's procedure is the `merge-gate` skill | KEEP | ungraded (05/09): the pointer rewrite that followed the gate's promotion to a skill of its own |
| W2:120–124 | what this session DELIVERED arrives as an action, never a new item | KEEP | ungraded (02/09, T209): the anti-hydra rule, the one an item closed and re-queued as a DECISION cost |
| W2:127–128 | "`tk-queue list` then names no item this session delivered" | KEEP | ungraded: the checkable half of the row above, in the step's "Done when" |
| W2:133 | "It is written for a cold reader, and the structure is what travels." | DROP | duplicate of `REPORT.md`'s own first rule, in the file the preceding sentence orders read before the close |
| W2:139 | `tk-queue handoff "<id>" --dir "<queue dir>" …` | KEEP | ungraded (06/09): the queue a command writes is decided by `--dir`, and `tk/tests/test_afk_audit.py` sweeps this file for it |
| W2:146 | ", leaving genuine nuance to `/compact`" | CLAUSE | the `/compact` bullet three lines below is the branch's own home |
| W2:167–169 | the afk run's one exception, the batched question over parked DECISIONs | KEEP | ungraded (09/09): the run is any afk package's close |
| W2:175–177 | "the flag for a decision nobody could ask, against one nobody bothered to ask" | CLAUSE | a gloss on `--deferred afk`; the flag stays prescribed, and its meaning is the queue's contract, not this step's |
| W2:176–177 | a session finding takes `../kickoff/FINDINGS.md` | KEEP | ungraded (09/09, T387): the unattended ladder's destination |
| W2:188–189 | "Whatever was not merged sits in the queue as a DECISION" | CLAUSE | the step-5 bullet of the same section prescribes it; "No other external effect happened." stays as the criterion |
| R2:12–13 | "An unattended run walks its items one at a time…" | DROP | the paragraph's second sentence already states that the unattended reader has no other window |
| R2:50–53 | "At an attended gate the user has already read those lines…" | DROP | exposition behind "**What changed opens the report, and it retransmits**", which is the rule in one word |

Eleven verdicts on `SKILL.md` (2 DROP, 9 CLAUSE) and two on `REPORT.md`. The first
commit message of this branch counts ten: it read the two verdicts that share one hunk —
the CLAUSE at W2:28–29 and the DROP at W2:31–33 — as one.

## 3. Splits and notes

No split is suggested and no term was coined, fused or retired. The KEEP rows above are
the whole ungraded set: those ten commits added rules and no file, and the skill's shape
(SKILL.md + REPORT.md, the gate a skill of its own since 05/09) is the one pass 1 left.

**Rewording note (no verdict):** three paragraphs — step 1's session findings, step 4, and
step 5's opening — were re-wrapped at 90 columns after their cuts, so the diff shows lines
that lost no word. That reflow is where 2 of the 9 `lines` this pass returned came from.

**What was NOT cut, and why** — three candidates the ruler marks and the pass kept:

- "Never discarded: a discard answers a question, this one needs a routine." (step 2) — a
  negation, and the positive ("RECURRING is convert-or-resolve") is beside it. Kept: the
  failure mode it names — a RECURRING item closed as DESCARTADO — is one the positive
  half does not obviously exclude, since closing an item IS how it is resolved.
- The `--objective/--state/--blockers` flags of `tk-queue handoff` (step 6) — an
  environment copy of the bin's `--help`. Kept: the three fields are what the writer must
  fill at that moment, and the lookup is a process away.
- "a session reopened by a spawn has no history to compact at all" (step 6) — exposition
  on the `/compact` branch. Kept: it rules a path out for the unattended run, which is the
  run with nobody to catch a wrong recommendation.

## 4. Paths

- Pruned in place, branch `lane/t410-prune-wrap-up`: `tk/skills/wrap-up/SKILL.md` and
  `tk/skills/wrap-up/REPORT.md`. No other file of the plugin changed.
- Removed material: `docs/prune/wrap-up.md`, §§7–8 — appended, not rewritten.
- `tk/tests/prune-lock.json` is untouched. Shrinking never fails the lock, and
  regenerating it is for growth that was earned; this pass earned none.

## 5. Proof of the target skill

The target is prose, so the proof is the reviewed diff of rules — the two axes read this
table and the `writing-for-agents` path, with the smell baseline inapplicable. The
executable arm is the suite on the pruned tree: 1472 tests and 989 subtests green,
`tk/tests/test_prune_lock.py` among them, which is the assertion that both files came in
under their locked numbers with no new ceiling mark.

Three doc-conformance files read the prose this pass cut into, and each is a broken-arm
proof written before it: `test_wrap_up_consolidation.py` (step 2's fold and its order),
`test_afk_audit.py` (every command this file prescribes names its queue with `--dir`),
`test_afk_report_line.py` (`REPORT.md` keeps both `wrap-up afk:` outcomes). They were run
first, before the full suite, for that reason.

---

# Pass 3 — 2026-09-25 (T460): `REPORT.md` alone, report only

A third pass, over one file: `tk/skills/wrap-up/REPORT.md`. Unlike passes 1 and 2, this
one edits nothing. The user reads the table below and decides which cuts, if any, a later
slice applies. `R3:` cites that file at commit `580fd9c`.

**Why this pass.** After its last edits the file sits one line and two words under the
lock's slack, so the next sentence anyone adds to it reddens `test_prune_lock.py`.

**Step-3 dating.** The file's last edit is 2026-09-24 (`c8fa29b`), and this report's last
commit is 2026-09-16 (`86956ed`). Six commits touched the file after that report, so no
pass has graded their rules: `e74c5d3` and `493e0f4` (the New group, 17/09), `b2dbb53`
(the `DIGEST.md` pointer, 22/09), and `23e3c91`, `9d617c9` and `c8fa29b` (the compact
pair, 24/09). The dispatch asked for every unit, not only the ungraded ones, so the table
below covers the whole file. Rows for the ungraded units say "ungraded".

## 1. Numbers

The first three columns come from `tk-prune-measure <file> --targets`. The lock's own
numbers come from `tk/tests/prune-lock.json`, which was generated 2026-09-23 and gives this
file the row `moved`, `lines 96`, `body_words 751`, and marks for `mean_sentence_words`,
`max_sentence_words` and `sentences_over_30`. The ceiling the test enforces is
`floor(locked × 1.10)` (`test_prune_lock.py`, `slack_ceiling`). For this file that is
**105 lines** and **826 body words**.

The three "after" columns measure the pruned copies the pass wrote. Each copy was measured
at its landing address, inside a copy of the tree with the file in place, so the sibling
scan read the real kit. `test_prune_lock.py` and `test_afk_report_line.py` pass on all
three copies. **Bold** marks a value over a bin ceiling.

| metric | ceiling | now | after tier 1 | after tiers 1–2 | after tiers 1–3 |
|---|---|---|---|---|---|
| lines (lock 96, slack 105) | 105 | 104 | 96 | 94 | 92 |
| body words (lock 751, slack 826) | 826 | 824 | 726 | 671 | 651 |
| headroom to slack, lines / words | — | 1 / 2 | 9 / 100 | 11 / 155 | 13 / 175 |
| sentences | — | 35 | 31 | 29 | 29 |
| mean words per sentence (22) | locked mark | **23.5** | **23.4** | **23.1** | **22.4** |
| max words in a sentence (25) | locked mark | **60** | **60** | **60** | **60** |
| sentences over 30 words (4) | locked mark | **8** | **8** | **6** | **5** |
| inline evidence (0) | 0 | 0 | 0 | 0 | 0 |
| pointers to other files | — | 3 | 2 | 2 | 2 |
| negations | — | 24 | 22 | 19 | 18 |
| defined terms | — | 2 | 2 | 2 | 2 |
| terms defined in a sibling too (0) | 0 | 0 | 0 | 0 | 0 |
| environment copies | — | 1 | 1 | 1 | 1 |

After tier 1 the file is back at the lock's line count (96) and 25 words under its word
count (751). No tier adds a ceiling mark, and the three marks that stand are the lock's
own: the survivors over 30 words are the template's rule sentences, and KEEP outranks
every ceiling. The pointer that leaves with tier 1 is `SKILL.md` on R3:3, which the
sentence citing it takes along. Tier 1's copy is not reflowed, and its line count comes
from whole lines deleted. The tiers-1–2 and tiers-1–3 copies reflow at 90 columns only
the paragraphs a cut touched. Of their extra lines, the two tier 3 gains come from that
rewrap and not from the words cut.

## 2. The table

One row per table unit of `REPORT.md`, where the units are 35 sentences plus the template
fence. Some rows also carry a **cut** rank:

- **tier 1** is recommended: a duplicate or an exposition range whose rule stands elsewhere.
- **tier 2** is optional: exposition that one could argue changes nothing.
- **tier 3** is not recommended: a reason clause that saves words and no line.

Each quote is verbatim, so one edit puts it back. The "saves" figures come from the bin,
applying each cut alone to the file at `580fd9c`.

| where | sentence | verdict | why |
|---|---|---|---|
| R3:1 | `# The closing template` | KEEP | `kickoff/AFK.md:343` and `reference/vista.md:72` cite this name as "the closing template" |
| R3:3 | "Read from step 6 of `SKILL.md`, before writing the close." | DROP — **cut, tier 1** | duplicate: `SKILL.md:126–127` already says this, and it is the pointer that brings the reader here ("read it before writing the close"). A reader who arrives from fleet or docs-audit never runs step 6. Together with the next row it saves **34 words and 4 lines**, because lines 3–6 go whole |
| R3:3–5 | "Any skill that closes on the wrap-up template reads it here too — the fleet's consolidated report takes block 1's five counts from this file." | DROP — **cut, tier 1** | duplicate: `fleet/SKILL.md:363–364` carries the dependency where fleet's reader runs it ("That template is also where block 1's five counts come from"). Here it describes a sibling, and `slice-rules.md` says to write such a claim as a requirement on the reader, not as a description. Keeping it also costs something real: `e74c5d3` had to edit "four" to "five" in this line. No inbound pointer (grepped) |
| R3:7 | "**Write the report for a cold reader** — someone who was not in this session." | KEEP | the file's first rule, and the one place "cold reader" is defined for the close. Pass 2 dropped `SKILL.md`'s copy so that this line holds it alone |
| R3:7–9 | "An unattended run gives them no other window, so this report is where they learn what happened." | DROP — cut, tier 2 | exposition behind R3:7, whose "not in this session" already covers the unattended reader. Saves **17 words, 1 line**. Pass 2 relied on this sentence when it dropped R2:12–13 ("the paragraph's second sentence already states…"), so this cut would remove the surviving copy of that point, not a duplicate of it |
| R3:9–12 | "What they lack is context, not vocabulary: resolve every identifier on first mention (…), name every artefact by what it does before what it is called, and let every reference resolve from the report alone." | KEEP | three instructions. The "context, not vocabulary" clause steers the model away from its default for a lay reader, which is to simplify words. The closing clause is the general criterion for references that are not identifiers (files, sections), so it stays even though it overlaps with the first clause |
| R3:14–15 | "The report follows this structure, and it is the structure that travels — a response-style preference that disagrees with it loses:" | KEEP | settles a conflict between the output style and the template. `SKILL.md:15–16` carries the same rule, but fleet reads this file without `SKILL.md`, so any duplicate to remove is `SKILL.md`'s. That is a note, outside this file's pass |
| R3:17–47 | the template fence | KEEP | the template itself. Line 24's five counts are what fleet takes. The vista's closed outcome vocabulary mirrors the groups (`tk/tests/mutations_vista.py`, "the vocabulary loses a word the closing template uses"). The New group is ungraded (17/09): it is the only place carried and new are told apart |
| R3:49 | "**What changed opens the report, and it retransmits." | KEEP | the rule in one leading word. Pass 2 cut its exposition |
| R3:49–52 | "One entry per DELIVERED item, three lines under it — … — read off the digest step 5 already wrote (lines 2 to 5 of its `../merge-gate/DIGEST.md` block ARE this entry), or off the work itself where the item closed without a PR." | KEEP | ungraded (22/09, `b2dbb53`). It says how the entry is copied from the digest, and `DIGEST.md:25` points back here as the owner of the mould. "Where there is one" makes the risk clause optional, which the fence does not show, so that clause stays |
| R3:52–55 | "The gain is concrete — … — and an item that closed with no gain worth a line says exactly that on its gain line, which is itself worth the line." | KEEP | the example steers the model away from a vague gain, and the instruction covers an item with no gain |
| R3:54–55 | ", which is itself worth the line" | CLAUSE — cut, tier 2 | a reason cut from an instruction that stands alone ("says exactly that on its gain line"). Saves **6 words**, 0 lines once reflowed |
| R3:55–57 | "A DESCARTADO item has no before and no after, so it appears in Closed alone; a session that delivered nothing writes the header with "nothing delivered" under it — an absent block reads as a block nobody wrote." | KEEP | the second half, "nothing delivered", is a rule the default misses: the model would otherwise leave out a block it has nothing for |
| R3:55–56 | "A DESCARTADO item has no before and no after, so it appears in Closed alone;" | CLAUSE — cut, tier 2 | duplicate: "One entry per DELIVERED item" (R3:49) already leaves a discarded item out, and the fence (R3:30) puts it in Closed. Saves **15 words, 1 line**. Reverse it if a close is ever seen giving a DESCARTADO item a What-changed entry |
| R3:57 | "— an absent block reads as a block nobody wrote" | CLAUSE — cut, tier 3 | a reason. Its instruction ("writes the header with 'nothing delivered'") stands alone. Saves **9 words**, 0 lines |
| R3:59–60 | "**The stats line follows, and its first four counts are the queue's balance**: what left it against what is still in it." | KEEP | gives the counts their meaning, and `reference/vista.md:72` reads the counts under it. The bin lists it as a defined term, and no sibling defines it |
| R3:60–61 | "**Blocked** outranks carried and new: …, and the Sensor line still counts it among this session's births." | KEEP | ungraded (17/09). Fence line 38 says which items are blocked. This sentence adds that blocked excludes carried and new, and that the Sensor line still counts the item among births |
| R3:62–63 | "The fifth counts a different object — … — so the group is labelled and the two are never summed." | KEEP | "never summed" is the rule. `vista.md:72` restates it for the consolidated report |
| R3:63–65 | "**The Sensor line under it is the afk close's** — `../kickoff/AFK.md` step 6 computes it, and a close that ran no package leaves it out." | KEEP | says when the line appears. Checked: `AFK.md:316` is "## 6. Measure, and hand the package to the close", and `:320` defines the sensor |
| R3:65–66 | "Discarding needs a user to do it, so an unattended run reports no discards and carries its findings to the gates instead." | KEEP | the first half fixes D = 0 for any unattended close, fleet's included. Fleet does not read `SKILL.md`'s afk section |
| R3:66 | "and carries its findings to the gates instead" | CLAUSE — **cut, tier 1** | duplicate that has drifted: `SKILL.md`'s afk section sends an unattended session finding to `../kickoff/FINDINGS.md`, whose three destinations are vehicles, not gates ("This file decides which VEHICLE a finding takes"). In this skill, **gate** means the survival gates and the versioning gate (`SKILL.md:12–14`), and neither receives a finding. Saves **8 words**, 0 lines |
| R3:66–68 | "An afk report states, literally, `wrap-up afk: rodou` or `wrap-up afk: nao rodou (<motivo>)` — …" | KEEP | **must not be cut**: `tk/tests/test_afk_report_line.py` asserts `wrap-up afk:`, `rodou` and `nao rodou` in this file |
| R3:68–70 | "The outcome groups below are the balance and nothing more: each item with its outcome, and the reason wherever the outcome does not carry it — the substance was already spent above." | KEEP | keeps the groups from repeating the What-changed entries |
| R3:69–70 | "— the substance was already spent above" | CLAUSE — cut, tier 2 | a reason. "The balance and nothing more" is the instruction. Saves **6 words**, 0 lines once reflowed |
| R3:70–72 | "Items group by outcome, never by chronology, and a group of three or more becomes a table with those same columns — the What changed entries stay in lines, a cell being no place for a before and an after." | KEEP | a layout rule the default would not produce. The negation has its positive beside it |
| R3:72 | ", a cell being no place for a before and an after" | CLAUSE — cut, tier 3 | a reason under "stay in lines". Saves **11 words**, 0 lines |
| R3:74–75 | "**The blockers line is unskippable**: "none" written out is an answer, an absent line is a rediscovery the next session pays for." | KEEP | the fence (R3:44) shows the shape, and this sentence makes the line mandatory. The bin lists it as a defined term, and no sibling defines it |
| R3:75–77 | "It is also the one line of the report that must survive the terminal — it lands in the affected item's text, and a blocker too big for the item's size ceiling is itself the signal that the handoff file is due." | KEEP | two instructions: the blocker is written into the item's text, and one too big for the item escalates to the handoff file. `kickoff/SKILL.md:35` routes unattended candidates to this line |
| R3:79 | `## The opening sentences` | KEEP | `docs-audit/SKILL.md:85` and `SKILL.md:146` cite the title |
| R3:81–82 | "When step 6 recommends `/clear`, the report ends with 1–3 ready sentences to open the next conversation, in two shapes chosen by what the sentence does:" | KEEP | where the sentences go and how many. `SKILL.md:145–146` repeats "1–3", but docs-audit's reader arrives here without that file |
| R3:84 | "**Invokes a slash command** (`/tk:kickoff afk`, `/implement`, …) — the command leads" | KEEP | the first shape |
| R3:85–88 | "the sentence alone, no prose before it, and does NOT name the project: `tk-queue` and similar resolve state from the session's `cwd`, so … — never by naming it inside the command line." | KEEP | the bin lists the `tk-queue` clause as an environment copy. It stays because it is the gotcha behind "does NOT name the project", not a restatement of `--help`. Its example, "open the session in the project's directory and type `/tk:kickoff afk` as the first line", is nearly word for word R3:94–96, and the tier-1 cut below removes that copy, not this one |
| R3:89 | "**Describes a task, no slash command** — name the project by path or name in the prose:" | KEEP | the second shape, and the instruction does not depend on where the session opens |
| R3:90 | ""in the project's directory, take T012", not "take T012"." | KEEP | a contrast example, which steers better than the bare rule |
| R3:90–92 | "The next session may open anywhere (on the desktop it does not start in the project's folder), so a cold sentence that names no project points at nothing." | DROP — **cut, tier 1** | an exposition range behind R3:89, whose instruction is unconditional and whose example shows it. The parenthesis also names one client's behaviour, which is environment copy. Saves **28 words, 2 lines** |
| R3:94 | "Site extensions may add flow-specific opening lines." | KEEP | exempts site lines from R3:81's 1–3 cap, which would otherwise forbid them |
| R3:94–96 | "Leaving rather than continuing, close with the ready pair: `/clear` now, then open the next session in the project's directory and type `/tk:kickoff afk` as its first line." | DROP — **cut, tier 1** | duplicate twice over. `SKILL.md:176–177` (the `afk` argument, the "leaving" case) prescribes "the ready pair for the user's return: `/clear` + `/tk:kickoff afk`", and R3:87–88's example already names the directory. Saves **28 words, 2 lines**. "Ready pair" survives at R3:100 and `SKILL.md:176`. It is a plain phrase, not a bold definition, so R3:100 still reads the same (`c8fa29b` reused it on purpose). Risk: fleet's close never reads `SKILL.md`, and `fleet/SKILL.md` names no ready pair. If fleet relies on this line, the cut removes it from fleet's path |
| R3:98 | `## The compact pair` | KEEP | `SKILL.md:157–158` cites "the compact pair" |
| R3:100–101 | "When step 6 nonetheless recommends `/compact`, the report ends with the ready pair: `/compact <what to preserve>`, then the next command." | KEEP | ungraded (24/09, `23e3c91`, `c8fa29b`). The only place that says how a `/compact` close ends |
| R3:101–102 | "The summary keeps what the argument names and thins the rest." | DROP — cut, tier 2 | exposition: it explains R3:102 by restating how the harness's `/compact` behaves, which is an environment fact, and R3:102 already says "in full". Saves **11 words**, 0 lines once reflowed. Ungraded (24/09) |
| R3:102–104 | "Name in full every fact the next command needs — decisions with numbers, dates, exceptions, IDs, the next step — and the reasoning no file holds: what was rejected, and why." | KEEP | ungraded (24/09, `9d617c9`). By default the model would summarize thinly, and the list says what to keep |
| R3:104 | "Spell out what an issue holds, beside its source." | KEEP | ungraded (24/09). The default is to cite `#n` bare, and the summary then loses what the issue says |

**The ranked cut list.**

| rank | cut | saves (words / lines) | running total, from 824 / 104 |
|---|---|---|---|
| 1 | R3:3 + R3:3–5, the intro paragraph (tier 1) | 34 / 4 | 790 / 100 |
| 2 | R3:94–96, the ready pair on leaving (tier 1) | 28 / 2 | 762 / 98 |
| 3 | R3:90–92, where the next session opens (tier 1) | 28 / 2 | 734 / 96 |
| 4 | R3:66, "and carries its findings to the gates instead" (tier 1; also fixes the drift) | 8 / 0 | 726 / 96 |
| 5 | R3:7–9, the unattended reader's window (tier 2) | 17 / 1 | 709 / 95 |
| 6 | R3:55–56, the DESCARTADO half (tier 2) | 15 / 1 | 694 / 94 |
| 7 | R3:101–102, what `/compact` keeps (tier 2) | 11 / 0 | 683 / 94 |
| 8 | the two tier-2 reason clauses, R3:54–55 and R3:69–70 | 12 / 0 | 671 / 94 |
| 9 | the two tier-3 reason clauses, R3:57 and R3:72 | 20 / 2 (rewrap) | 651 / 92 |

The rows add up the single-cut measurements. The pass also measured the combined copies
at each tier's end, and they agree: 726 / 96, 671 / 94 and 651 / 92. Rank 1 alone leaves
36 words and 5 lines of headroom. Ranks 1–4, tier 1, leave 100 words and 9 lines.

**Must not be cut.** Keep these whatever else goes:

- R3:66–68, the `wrap-up afk:` line, held by a test.
- The fence, which is what fleet and the vista read.
- R3:79 and R3:98, the headings that other files cite.
- R3:59–63, the count semantics, which `vista.md` reads.
- R3:74–77, the blockers line.
- R3:100–104, the compact pair: ungraded until this pass, and each sentence names a
  behaviour the model does not have by default.

## 3. Splits and notes

- **No split is suggested.** `REPORT.md` is already the step-6 reference split off `SKILL.md`,
  and every consumer (wrap-up step 6, fleet step 6, docs-audit, DIGEST, FINDINGS) reads it
  whole. The `SKILL-MECHANICS` criterion gives it no second entry moment.
- **No term was coined, fused or retired.** The two terms the bin lists (the stats line,
  the blockers line) have one defining file each.
- **Duplicate rules sitting in `SKILL.md` (a note, no verdict).** `SKILL.md:15–16` says the
  same as R3:14, and `SKILL.md:145–146` repeats "1–3 ready sentences". They are outside this
  pass's target file, and this file is the copy the other consumers reach.
- **Rewording note (no verdict).** R3:9–12 (60 words) and R3:85–88 (59 words) are the two
  longest sentences. Splitting either one adds lines, the one number this file cannot
  spare, so neither is suggested.

## 4. Paths

- Output directory (uncommitted): `prune-report.md` (this section), and
  the pruned copies `REPORT.tier1.md`, `REPORT.tier1-2.md` and `REPORT.tier1-3.md`. It also
  holds `wrap-up.removed-draft.md`, the verbatim text of every cut in the shape of
  `wrap-up.md`'s §§7–8.
- Committed: this section, added to `docs/prune/wrap-up-report.md`. Passes 1 and 2 above it
  are untouched.
- **`docs/prune/wrap-up.md` is not written by this pass.** The skill has the pruning PR
  copy the removed material "from the output directory — the diff the closing review
  reads". Here nothing is removed: the target is untouched, and the user has not chosen
  the cuts. Committing the text as "removed" now would put a record in `docs/` that
  contradicts the tree. The slice that applies the chosen cuts copies the matching entries
  from `wrap-up.removed-draft.md` as §§9–10.
- `tk/tests/prune-lock.json` is untouched. Shrinking never fails the lock. If the applying
  slice wants the recovered headroom locked in, running `lock.py --add` is a decision for
  that slice.

## 5. Proof of the target skill

The target is prose, so its proof is the reviewed diff of rules. When the user applies a
cut set, that slice's two-axis review reads this table beside the diff. It gets the
`writing-for-agents` path, and the smell baseline is declared inapplicable. The executable
arm has two tests. `tk/tests/test_prune_lock.py` asserts the file stays under 105 / 826
with no new ceiling mark. `tk/tests/test_afk_report_line.py` asserts that the one test-held
sentence survives. Both were run on all three pruned copies, in a copy of the tree with
each copy at its landing address. All three were green: 11 tests and 160 subtests each.
