`docs/prune/kickoff-report.md`

# Pruning report — the `kickoff` skill (`SKILL.md`, `AFK.md`, `WINDOW.md`)

The fifth run of `/tk:prune`, executed as prune 7/8 of the pruning track's spec, and the
first over a multi-file skill. The removed material is beside this file, in `kickoff.md`,
keyed to the pre-prune originals at commit `7fb9ad0`. Unlike the earlier passes this one ran
inside an unattended package, so the pass edited the skill in its branch directly; the
output-directory rite of `prune/SKILL.md` collapses into the branch itself, which is what
the closing review reads. **First pass over this skill**: there is no earlier committed
report, so no rule needed the step-3 date check against one. A **second pass**, over
`WINDOW.md` alone, is appended at the end of this file.

Throughout, **run** means one execution of the target skill; the table's unit is the
**table unit** step 4 of `prune/SKILL.md` defines. `where` cites the original files at
`7fb9ad0` as `S:` (SKILL.md), `A:` (AFK.md), `R:` (README.md) plus line numbers.

## 1. Numbers

`tk-prune-measure <file> --targets`, before and after. **Bold** marks a value over a
ceiling — the bin's, or the ticket's line ceiling, which the bin does not carry.

| metric | SKILL.md before | after | AFK.md before | after | WINDOW.md (untouched) |
|---|---|---|---|---|---|
| lines (ticket: ≤120 / ≤200 / —) | 485 | 120 | 1257 | **327** | 253 |
| body words | 5081 | 1096 | 14683 | 3437 | 2753 |
| sentences | 234 | 59 | 561 | 141 | 152 |
| mean words per sentence (22) | 21.7 | 18.6 | **26.2** | **24.4** | 18.1 |
| max words in a sentence (25) | **68** | **93** | **154** | **81** | **59** |
| sentences over 30 words (4) | **61** | **9** | **187** | **44** | **22** |
| description words (30) | **41** | 30 | — | — | — |
| inline evidence (0) | **6** | 0 | **30** | 0 | **10** |
| pointers to other files | 31 | 18 | 50 | 18 | 24 |
| negations | 107 | 15 | 256 | 55 | 42 |
| defined terms | 3 | 0 | 7 | 1 | 3 |
| terms defined in a sibling too (0) | **1** | 0 | **1** | 0 | 0 |

SKILL.md's 120 later became 121: line 121 is the review-restored Env clause ("runs on: X"
read off the item itself, since `tk-queue list` does not print Env) — a KEEP mandated by
the lane's Standards review (commit ba9d086), and KEEP outranks the ceiling.

The two destinations, measured at their landing address (`tk/reference/`, beside
`slice-rules.md` and `subagent-policy.md`, the repo's existing convention for material more
than one skill reaches — the placement decision this row records): `queue.md` 114 lines,
0 inline evidence, 0 sibling terms; `session-finding.md` 44 lines, 0 and 0. Both carry
sentences over the word ceilings; each such sentence is a KEEP carrying a behaviour or a
refusal, and KEEP outranks every ceiling.

**Why the AFK.md `lines` mark stands, rule by rule** (the ticket's ceiling is 200):

- The remainder over 200 is exactly the two dismemberments the ticket forbids executing in
  this branch ("never executed in this PR"). *A resumed generation starts here* is 64 lines
  and leaves to `RESUME.md` under ticket #224; step 4's audit is 51 lines and leaves to
  `AUDIT.md` under ticket #225 — the second is also pinned here by
  `tk/tests/test_afk_audit.py`, which regexes its recipe out of THIS file, and moving it
  without the test re-anchor would break the suite this PR must keep green. 327 − 64 − 51 =
  212, minus the two 2–3-line stubs' overhead ≈ 200: the ceiling is reachable by exactly
  those two ticketed splits and by nothing smaller.
- Every line now in the file names a behaviour a run reaches (the beats, the commands, the
  gates, the exits), and `prune/SKILL.md` ranks KEEP over every ceiling. The classes the
  ceiling could still buy — inline evidence (30→0), duplicates, exposition ranges — are
  already out.
- `mean words` and `sentences over 30` stand for the same reason as in the earlier passes:
  the survivors are dense rule sentences; splitting them adds lines, the one metric this
  ticket caps.

The `sessions finding` sibling-term mark (1→0 in both files) closed by coining **hydra**
and the ladder once, in `session-finding.md`. WINDOW.md was measured and read; the ticket
scopes it to step 1's measurement only (no ceiling, no verdicts), and its 10 inline-evidence
marks are noted for the pass that owns it — plausibly #224's, since most sit in the wall
and threshold sections that RESUME.md will neighbour.

## 2. The table

One row per unit or range; the ranges and every verbatim quote are in `kickoff.md` beside
this file (its §§2–6), so the rows cite rather than repeat them.

### SKILL.md

| where | sentence / range | verdict | why |
|---|---|---|---|
| S:3 | the `description` | rewritten | 41 → 30 words; the three parenthetical branches it loses are `kickoff.md` §6 |
| S:7–24 | intro, arguments, site extensions, package-handoff entry | KEEP | every kickoff run reads them; handoff entry is WINDOW.md's citation target |
| S:26–38 | hygiene open — the four exits | KEEP | each exit changes what the session does; exposition around them DROP (§5) |
| S:40–51 | agenda sources, wiki-not-agenda | KEEP | source order and the stale-doc refusal are behaviour |
| S:53–70 | weekly report block | KEEP | compressed; `###`-heading output detail DROP, environment copy of `report`'s own output |
| S:72–80 | verify against reality | KEEP | the on-the-spot `done` is the rule measured against 25 stale `[x]` items |
| S:85–123 | triage table, field fill, slicing, ask-before-BLOCKED | KEEP | classes and refusals are behaviour; command examples DROP, environment copy (§4) |
| S:126–159 | menu step | KEEP | compressed; rationale ranges DROP (§5) |
| S:161–191 | dispatch step, blocks (a)–(f) | KEEP | the report shape is what the close owes; rationale DROP (§5) |
| S:193–222 | the session-finding ladder | MOVE | → `tk/reference/session-finding.md`; criterion: one term, one definition — the ladder was stated in SKILL.md, AFK.md and wrap-up. Inbound pointers below |
| S:224–241 | queue contract header — two files, one writer, log-first crash order | MOVE | → `tk/reference/queue.md` header; the contract's canonical home |
| S:242–275 | the command palette (fenced) | DROP | environment copy — `tk-queue --help` and each subcommand's `--help` carry it; restore via `kickoff.md` §4 |
| S:277–281 | dry-run preview is not evidence; the stderr banner | MOVE | → `queue.md` *The stderr lines* |
| S:282 | `<id>` accepted as displayed or bare | MOVE | → `queue.md` header |
| S:284–289 | priority is the file's order; bump; cosmetic headings | MOVE | → `queue.md` *Priority, claims and two writers* |
| S:290–300 | claim refusal, release prints the owner, no `edit --claimed` | MOVE | → `queue.md`, same section; the silent `done` cross-claim gotcha joins it |
| S:302–317 | which IDs are taken — the two tolerances | MOVE | → `queue.md` *Which IDs are taken* |
| S:319–326 | the stderr memory-dir line | MOVE | → `queue.md` *The stderr lines* |
| S:327–334 | the exclusive lock; the not-among-open diagnostic | MOVE | → `queue.md` *Priority, claims and two writers* |
| S:336–347 | field-marker refusal; the field chain; `cancel` + `add` | MOVE | → `queue.md` *The field chain* |
| S:350–403 | field semantics (Class, Deferred, Effort, Risk, Env, Criterion, Project) | DROP | environment copy — each is one or two `--help` lines now (§4); triage-facing halves stay in S steps 3–4 |
| S:405–412 | **Born** — script-only, migrate backdates, no `edit --born` | MOVE | → `queue.md` *Born, and the age column*; no flag exists, so no `--help` can carry it |
| S:414–446 | Ticket/Spec semantics, lanes, floor, canonical spelling | DROP + ticket | environment copy of `pack --help` for the printed shape and election; the canonical-spelling and exact-validation halves are `--help` gaps → ticket #223 |
| S:447–457 | Repo field and its whitelist | DROP + ticket | gist in `add --help`; the full whitelist is a `--help` gap → ticket #223 |
| S:458–479 | the two size ceilings, the exemption, `--force` | MOVE | → `queue.md` *The two size ceilings* (the "measured" wording rephrased; original in `kickoff.md`) |
| S:481–486 | the done-log pointer rule | MOVE | → `queue.md` *The done-log pointer rule* |

### AFK.md

| where | sentence / range | verdict | why |
|---|---|---|---|
| A:1–21 | spine — package, orchestrator, one queue writer, WINDOW.md first | KEEP | compressed; the 222-line-step reading anecdote DROP, inline evidence |
| A:23–57 | reading table and per-step routing | DROP | exposition of "read by section", which survives as one sentence; the entry points stay in each section |
| A:58–124 | resumed generation — entry, preconditions, reset | KEEP | compressed; measured narrations to `kickoff.md` §2; split suggested → ticket #224 |
| A:126–199 | draft, close, fresh handoff | KEEP | compressed; the claim test and tip-over-map survive as rules |
| A:201–269 | re-dispatch, carries-on, tail-death questions | KEEP | compressed to two paragraphs |
| A:271–345 | three-deaths table and the full exit table | DROP | exposition ranges — every row's outcome survives in the exits paragraph; the tables restore via `kickoff.md` §5 and re-expand under #224 |
| A:347–526 | step 1 — pack, re-triage, double election, cut, recount, two cost lines | KEEP | compressed ~4:1; rationale ranges DROP (§5); the correction-cycles rule stays, being WINDOW.md's citation target |
| A:528–534 | step 2 confirm | KEEP | verbatim in substance |
| A:536–719 | step 3 — claim guard, re-ask, branch creation, serial lane, prompt contents | KEEP | compressed; the one-lane-one-address and clone rules restored after a first draft lost them (a fidelity slip this report records); rationale DROP (§5) |
| A:721–938 | step 4 — audit | KEEP | compressed; the `sh` REGRILL recipe verbatim, being executed by `test_afk_audit.py`; measured round to `kickoff.md` §2; split suggested → ticket #225 |
| A:940–1082 | step 5 — verify cycle, seven stages | KEEP | the stages as a numbered list; per-stage rationale DROP (§5) |
| A:1084–1166 | the lane's tail | KEEP | the three steps as a list; WINDOW.md cites *The lane's tail* by name, so the heading survives |
| A:1168–1237 | step 6 measure + step 7 chain | KEEP | compressed; the reasons ladder survives whole |
| A:1239–1257 | a session finding, unattended | MOVE | → `tk/reference/session-finding.md`; the section stays as the one-rung form plus pointer, since the audit's backlog outcome cites it |

### README.md and WINDOW.md

| where | sentence / range | verdict | why |
|---|---|---|---|
| R:30–74 | the ~40-line repetition of the queue contract | MOVE | → pointer paragraph naming `tk/reference/queue.md` and the `--help`s; the four-dispatchers half stays, being dispatch's material, not the contract's |
| WINDOW.md, whole | — | measured only | the ticket scopes it to step 1's measurement; no verdicts this pass, numbers in §1. Pruned later by the second pass, at the end of this file |

## 3. Splits and notes

- **Split — ticket #224**: *A resumed generation starts here* → `RESUME.md`.
  `SKILL-MECHANICS` criterion: a self-contained procedure with its own entry moment;
  consumer: the successor generation WINDOW.md's vehicles open — a fresh package never
  reads it.
- **Split — ticket #225**: step 4 → `AUDIT.md`. Same criterion; consumer: a wave package
  only — an aged-queue package never reads it. Carries the `test_afk_audit.py` re-anchor
  in the same commit.
- **Bin ticket #223**: the three `--help` gaps (canonical Ticket/Spec spelling, `--force`
  naming both ceilings, the full Repo whitelist) plus the bin comment still naming "the
  kickoff SKILL.md" as a prose site of the dry-run claim. The branch touches no bin.
- **Rewording note (no verdict)**: both files were rewritten sentence by sentence to carry
  the same rules in fewer words; `kickoff.md` and `git show 7fb9ad0:…` hold every original.
  The coined terms kept their coining lines: **package**, **orchestrator**, **wave** in
  AFK.md; **session finding**, **pendency**, **hydra** now in `session-finding.md`.
- **Description note**: the rewrite is in the table's first row; wording in `kickoff.md` §6.

### The MOVE's inbound pointers (grepped over the plugin), with their rewrites

| pointer | was | now |
|---|---|---|
| `tk/skills/verify/SKILL.md:8` | contract in `../kickoff/SKILL.md` | `../../reference/queue.md` |
| `tk/skills/docs-audit/SKILL.md:58` | contract in `../kickoff/SKILL.md` | `../../reference/queue.md` |
| `tk/skills/dispatch/SKILL.md:50` | contract: `../kickoff/SKILL.md` | `../../reference/queue.md` |
| `README.md:30` | defined in `tk/skills/kickoff/SKILL.md` | `tk/reference/queue.md` |
| `tk/skills/wrap-up/SKILL.md:73` (contract) and its ladder references | `../kickoff/SKILL.md` | NOT rewritten here — the wrap-up repoint is the next prune ticket's, by the spec's own slicing |
| `tk/bin/tk-queue` ~line 162 (comment) | "the kickoff SKILL.md" | NOT rewritten — no bin in this PR; ticket #223 |
| `tk/skills/fleet/SKILL.md` (entry pointers to kickoff/AFK) | — | unchanged on purpose: they name the files as entry points, not the moved contract |

## 4. Paths

- Pruned in place, this branch: `tk/skills/kickoff/SKILL.md`, `tk/skills/kickoff/AFK.md`,
  `README.md`, plus the three pointer rewrites above.
- Created: `tk/reference/queue.md`, `tk/reference/session-finding.md`.
- Removed material: `docs/prune/kickoff.md` (this pass's `docs/` file), allowlisted file by
  file in `.gitignore` like its siblings.

## 5. Proof of the target skill

The target is prose, so the proof is the reviewed diff of rules — and this pass runs inside
an accumulated lane, where the two-axis review fires ONCE over the lane's whole diff at the
package's tail (the smell baseline declared inapplicable, the `writing-for-agents` path and
this table handed to the axes). Two executable arms already ran and stay green as part of
this branch: `tk/tests/test_afk_audit.py` lifts the REGRILL recipe out of the pruned
AFK.md and executes it with vacuity guards, and `tk/tests/test_window_wall.py` resolves the
pruned files' section pointers — the full suite passed at 771 tests plus 409 subtests on
the pruned tree. Their mutation harnesses (`tk/tests/mutations*.py`) are the broken-arm
proof the suite's own docs name.

---

# Second pass — `WINDOW.md` alone (2026-09-22, T449)

A run of `/tk:prune` scoped by its queue item to one file, `tk/skills/kickoff/WINDOW.md`:
read in full at every package open (`WINDOW.md:9`, `AFK.md`, `fleet/SKILL.md`), grown
2753 → 6791 body words since the first pass measured it on 01/09, and never pruned. The
other kickoff files are out of scope. Like the first pass, it ran inside an unattended
package, so the branch is the output directory. The removed material is in `kickoff.md`,
under its own second-pass heading, keyed to the original at commit `3de11df`. `where` below
cites that original as `W:` plus line numbers.

**Step-3 date check.** `git log -1 --format=%cs` gives 2026-09-22 for `WINDOW.md` and
2026-09-01 for this report. No verdict ever graded any rule of the file: the first pass
measured it and wrote no verdicts (the row above).

**What the suite pins.** Ten test modules open or name `WINDOW.md`: `test_window_tick`,
`test_window_wall`, `test_workflow_vehicle`, `test_tk_context`, `test_tk_quota`,
`test_tk_ram`, `test_package_ledger`, `test_fleet_ceiling`, `test_tk_prune_measure` and
`test_prune_lock`. Four mutation harnesses rewrite its prose by exact raw substring: `mutations_window_wall`,
`mutations_tk_context`, `mutations_tk_quota` and `mutations_tk_ram`. Before cutting,
the pass extracted every string literal of `tk/tests/*.py` that occurs in the file, raw or
whitespace-folded (764 literals). After the cuts it checked each literal again. Every
literal a WINDOW-reading module or harness uses survives, and every harness anchor survives
byte for byte. Seven literals no longer match, and each is asserted against other text. One
example is `test_tk_context`'s "1,000", which it checks in a command's stderr.

## 1. Numbers

`tk-prune-measure tk/skills/kickoff/WINDOW.md --targets`, before (`3de11df`) and after.
**Bold** marks a value over a ceiling.

| metric | before | after |
|---|---|---|
| lines | 581 | 533 |
| body words | 6791 | 6069 |
| sentences | 344 | 319 |
| mean words per sentence (22) | 19.7 | 19.0 |
| max words in a sentence (25) | **62** | **62** |
| sentences over 30 words (4) | **68** | **58** |
| inline evidence (0) | **24** | **8** |
| narrated outcomes | 15 | 11 |
| pointers to other files | 57 | 56 |
| negations | 119 | 108 |
| defined terms | 5 | 5 |
| terms defined in a sibling too (0) | 0 | 0 |
| environment copies | 7 | 7 |

**Why the three marks stand.** The 8 inline-evidence hits left are the measurements
`test_window_tick` requires beside the numbers they justify. The test says a number without its
measurement "reads as a preference". These are the tick's resets and its ceiling rates,
the 35% review floor, the 2026-09-06 schedule that never ran, the 293k/29% example, and the idle
night. Each is a KEEP the suite pins. The long sentences carry rules, and KEEP outranks
every ceiling. The worst of them (W:388, 62 words) is the one that makes `max-local-opus` the
only authority for an Opus dispatch. Splitting it would add lines, the lock's own metric.
The lock records all three marks as permitted (`tk/tests/prune-lock.json`, row
`tk/skills/kickoff/WINDOW.md`, `"locked": "2026-09-22"`).

## 2. Table

KEEP rows group by section and name the run each one serves. Every DROP and CLAUSE row
quotes what went. `kickoff.md` holds the same text for a one-paste reversal.

| where | sentence / range | verdict | why |
|---|---|---|---|
| W:1–9 | the two ceilings, the readiness triad, "Read this file at package open, beside `AFK.md`." | KEEP | every package open; the read instruction is what `AFK.md` points at |
| W:9–10 | "Every rule here fires at a moment nobody gets to choose." | DROP | suspected no-op: no reader acts differently for it |
| W:14–15 | the checkpoint rule | KEEP | every seam of every package |
| W:15–16 | "It is the cheapest of the three, and it is what makes the other two worth writing." | DROP | suspected no-op: ranks the triad, changes no action |
| W:18–21 | the subagent half is generated by `tk-contract` | KEEP | every dispatch: the orchestrator adds nothing to the prompt |
| W:23–24 | "What collects on it: on 2026-08-18 the wall landed mid-dispatch and killed the five runs then in flight. What survived was exactly what had been committed and pushed." | DROP | inline evidence, and a duplicate: the `tk-contract` block every run receives carries the same incident under its checkpoint heading |
| W:28–49 | reading the quota: `tk-quota`, its exit 2, the old reading's age, a partial exit 0, exit 64 | KEEP | the cut and every tick; pinned by `test_tk_quota` and `mutations_tk_quota` |
| W:31–32 | "(measured 2026-09-03 across 302 files: zero occurrences)" | CLAUSE | inline evidence; the sentence keeps the fact that no transcript holds the percentages |
| W:51–62 | a wall-killed run is not an attempt; the wall's two shapes | KEEP | the first quota failure; the tick's own turn |
| W:64–117 | the five steps, the eight contents, **Done when** | KEEP | the first quota failure; pinned by `test_window_wall`, `test_workflow_vehicle`, `test_package_ledger`, `mutations_window_wall` |
| W:100–101 | "— four of them new, and the fifth one of the eight above doing a second job there" | CLAUSE | duplicate: W:121–123 says it in the section that owns the five |
| W:119–164 | the lane's five contents, the map against the tip, `RESUME.md` | KEEP | a lane package's handoff, and the successor that reads it |
| W:128–131 | "in the state where nothing has merged yet, a map pinning the branch would be empty, and" | CLAUSE | exposition: the kept clause "needs it before anything has merged" carries the reason |
| W:168–171 | review budgeted as its own line; the lens-over-implementation fallback | KEEP | the cut, sizing each slice's review |
| W:169–170 | "measured 2026-08-28, that was 144k subagent tokens against a 1,534-line slice" | CLAUSE | inline evidence |
| W:173–175 | the slope rule and `tk-context --curve` | KEEP | a seam deciding whether the next review fits |
| W:175–177 | "Measured on one orchestrator: 59k at the open — a kickoff is born carrying the CLAUDE.md and the memory index — 113k at the cut, 154k at the first lens, 210-232k while the handoff was written." | DROP | inline evidence; the ~78k birth cost the planning seams use stays at W:342 |
| W:179–181 | reviews serialize, so review time is a sum | KEEP | the cut |
| W:181–182 | "A package planned as though review rode along inside implementation is a package whose last third is unfunded." | DROP | duplicate: restates the sum rule as its consequence |
| W:184–195 | a resumed package finishes its claims and stops; the planning-seam successor's scope | KEEP | every successor generation |
| W:197–236 | auto-continue: timer-driven, armed only by a real rejection, the four limits, the tick meets the wall, the structural marker | KEEP | a session waking on `auto-continuation`; planning as though it will not fire |
| W:201–202 | "Measured 2026-09-19," / "in a `tmux` session over SSH," | CLAUSE | inline evidence; the 87 seconds stay, because W:247 times the fire against them, and so does "with nobody at the keyboard" |
| W:218–219 | "Above all four sit the server-side flags the whole coverage rides on, which can be withdrawn with no change of version." | DROP | exposition range under "Plan the package as though it will not fire": a fifth reason for a rule already stated |
| W:221–223 | "The instrument that read every fact above cannot see such a warning, so its silence is evidence of nothing, and a package waiting for one waits on a promise nobody made." | CLAUSE | exposition; the kept sentence now ends "plan without that warning" (rewording note, §3) |
| W:238–256 | the two vehicles, the conditional fire, the handoff as the ending | KEEP | opening a successor |
| W:258–298 | `--budget N`, the smart zone, the seam list, the context-number bullets | KEEP | every seam; pinned by `test_tk_context`, `mutations_tk_context`, `test_workflow_vehicle` |
| W:265–266 | "and the orchestrator measured on 2026-08-18 closed at 410k: there is no orchestrating a package from inside the smart zone" | CLAUSE | inline evidence; the claim stays as "a package cannot be orchestrated from inside it" (rewording note) |
| W:279–280 | "and three generations in a row reported the number as estimated, unread or `n/m` while this rule asked for it" | CLAUSE | inline evidence |
| W:286–290 | "Measured 2026-09-03: a generation stopped a lane's tail citing this threshold two lines after writing \"context at the cut: unread\". Read afterwards from that session's own transcript, it had been at ~210-232k against a ceiling of ~150-200k: the call was RIGHT. A right answer wearing a rule's clothes is still the defect, and that is why this bullet exists rather than a ban on estimating." | DROP | inline evidence, three sentences; the licence ("Deciding by judgement is allowed there") and its label rule stay in W:284–286 |
| W:300–306 | the ~150–200k threshold is a simple slice's; correction cycles multiply | KEEP | every seam after the first dispatch |
| W:300–302 | "One real slice — one `tk-queue` subcommand, 8 commits, five files — closed its session at **372k**, roughly twice that ceiling, with no overflow and no compaction, on six correction cycles." | DROP | inline evidence; `AFK.md` step 1 owns the multiplier |
| W:308–313 | "**Estimating the implementation before it runs** … the only number a successor can plan the next slice from." (whole paragraph) | DROP | unexercised run: this file is read at package open only, and the paragraph's first clause says the question does not arise inside a package. Its one branch, a session implementing in the parent, never opens this file, and no pointer in the plugin names the paragraph |
| W:315–320 | the workflow launch is a seam; its handoff comes right after | KEEP | a package whose vehicle is a workflow; pinned by `test_workflow_vehicle` |
| W:317–318 | "and one package spent its whole window in that stretch with the quota unread" | CLAUSE | inline evidence |
| W:322–329 | generations are sequential; write the handoff rather than compacting | KEEP | every seam |
| W:333–363 | the two planning seams, the ~130k threshold, the four steps over it | KEEP | the cut and the `pack` confirm |
| W:335–336 | "Measured 2026-08-28: a `pack` reached **~130k at the cut with zero items dispatched**, leaving 20–70k — about one item — for the whole package." | DROP | inline evidence |
| W:343 | "(measured 2026-09-21: a cut read 111k with nothing wasteful in it)" | CLAUSE | inline evidence |
| W:343–344 | "Reading ~150–200k at a planning seam would authorise exactly the session that failed." | DROP | its referent was the evidence dropped at W:335; the ~130k threshold it defends stays at W:342 |
| W:365–448 | the tick, its four numbers with what measured each, the claims crossing, the three quota modes | KEEP | every tick fire; pinned by `test_window_tick`, `test_tk_ram`, `mutations_tk_ram`, `test_fleet_ceiling` |
| W:370–372 | "It is what made that package run three hours with nobody watching — it queued while the window was spent and dispatched at the reset." | DROP | inline evidence |
| W:402–403 | "— nine live sessions and an empty container read the same 2 otherwise, and one of the two readings OOMs" | CLAUSE | exposition: the kept clause "the occupancy is what moves between packages" is the reason |
| W:429–430 | "The second half of one lane in that package ran with no claim at all, and only the crossing found it." | DROP | inline evidence |
| W:450–548 | the scheduled refresh: trigger, absolute ceiling, site decides, the key, the three pieces, the pointer file, the margin, what does not exist | KEEP | a package that arms the tick; pinned by `test_window_tick`, `test_tk_context`, `mutations_compact_hooks` |
| W:458–459 | "and Remote Control shows no statusline, so it could not be confirmed from outside either" | CLAUSE | inline evidence |
| W:470–471 | "— measured, the orchestrator of 05-07/09 crossed two days at ~10% of context on three compacts" | CLAUSE | inline evidence |
| W:471–472 | "A cold reader has both halves of the condition here and asks nobody." | DROP | suspected no-op |
| W:476–477 | "Measured on the shipped binary, 2.1.263 on 08/09 and 2.1.266 on 09/09:" | CLAUSE | inline evidence; "takes effect in the NEXT session" stays, pinned |
| W:496–498 | "Run from a worktree before this was so, the tick missed the project pair holding 300,000 and reported the 1,000,000 default (17/09, T421)." | DROP | inline evidence; `test_tk_context.py`'s class docstring keeps the incident |
| W:505–507 | "Before that guard, one package collected four lines saying its context had been emptied while its transcript held no compaction at all (19/09, T432)." | DROP | inline evidence |
| W:509 | "the user decided so on 22/09" | KEEP | records whose decision the ledger gap is, written that week by T441; a dated decision, not evidence |
| W:516 | "That is the piece that was missing on 06/09." | DROP | inline evidence |
| W:517–519 | "for the same reason the bin above does: measured on 19/09, this hook fired inside an implementer that had just compacted and told it to read the orchestrator's handoff before anything else — an instruction to drop its own item" | CLAUSE | inline evidence; the reason stays as "a compacted implementer told to read the orchestrator's handoff drops its own item" (rewording note) |
| W:550–564 | `ESPERANDO-HUMANO`: what only the human does, cancelling the crons, the re-arm line | KEEP | a package whose remaining work is the human's |
| W:565–568 | "On the night of 06-07/09 the hook rejected the end of every turn — \"the goal says kill them all; 6 pull requests are still open\" — while the user's own rule was to leave them unmerged." | DROP | inline evidence; the date moves to W:578, where the measurement it dates stays (rewording note) |
| W:568 | "The goal was unsatisfiable by construction, and the hook only burned." | CLAUSE | its anecdote went with the sentence above; it stays as "Such a goal is unsatisfiable by construction, and the hook rejects the end of every turn" (rewording note) |
| W:568–581 | the two exits, the three-rejection rule, the idle tick's one turn and the measured night | KEEP | arming a goal-check hook; an idle tick; pinned by `test_window_tick` |

No FIT rows: the pass deleted no sentence to meet a ceiling.

## 3. Splits and notes

- **Split suggestion (not executed): the three tick sections → `TICK.md`.** *The tick*,
  *The scheduled context refresh* and *`ESPERANDO-HUMANO`* are W:365–581, about 2,400 of
  the 6,069 words. `SKILL-MECHANICS` criterion: disclosure by branch. Only a package that
  arms the tick reaches them, and *Generations* already covers the package that does not
  ("where no tick is armed"). Consumer: `AFK.md`'s tick step, which would point at the new file.
  It is a slice of its own. `test_window_tick` cuts its three sections out of this file by
  heading, and `mutations_tk_ram`, `mutations_tk_quota` and `mutations_compact_hooks` anchor
  on this path, so the move needs a test re-anchor in the same PR.
- **Rewording notes (no verdict).** W:95 "The section below names them." → ", which the
  section below names." W:221 → "is unmeasured: plan without that warning." W:265 → "and a
  package cannot be orchestrated from inside it." W:517 → "It reads `agent_id` as the bin
  above does: a compacted implementer told to read the orchestrator's handoff drops its own
  item." W:568 → "Such a goal is unsatisfiable by construction, and the hook rejects the end
  of every turn." W:578 "on that night" → "on the night of 06-07/09", because the sentence that
  named the night is gone. W:128–131 compress to "…not when the first item merges: the
  successor's first command, `git -C "<path>/spec-<m>" fetch --prune origin`, needs it
  before anything has merged." The command survives verbatim. Four paragraphs were reflowed
  to the file's column. None of these touches a defined term. The five terms (**quota wall**,
  **context ceiling**, **smart zone**, and the *At the compact* / *After* list labels) keep
  their coining lines.

## 4. Paths

- Pruned in place, this branch: `tk/skills/kickoff/WINDOW.md`.
- Locked: `tk/tests/prune-lock.json`, one new row written by
  `python3 docs/prune/lock.py --add 2026-09-22 tk/skills/kickoff/WINDOW.md`. The mode is
  new in this branch. It measures only the named file, copies every other row verbatim and
  stamps `"locked"`. `tk/tests/test_prune_lock.py` skips a stamped row in the comparison
  against `baseline-2026-09-01.md`, which holds this file's unpruned numbers. It checks
  instead that every row's report is on disk. No other row changed. Regenerating the
  whole lock is T443, a pending decision.
- Removed material: `docs/prune/kickoff.md`, second-pass heading.

## 5. Proof of the target skill

The target is prose, so its proof is the reviewed diff of rules: the two-axis review over
this branch. Give Standards the `writing-for-agents` path, give Spec this table and the
original at `3de11df`, and declare the smell baseline inapplicable. The broken arm already
exists in the repo. The four mutation harnesses above, plus `mutations_compact_hooks`, put
each pinned defect back into a copy of the pruned file. All five kill every entry on this
branch (12/12, 49/49, 63/63, 37/37, 22/22). The lock itself was proved by inflation on a
throwaway copy. 120 added lines take `WINDOW.md` to 654 lines and 7149 words, past the 586 and
6675 its slack allows, and that turns the slack test red. Removing the row's `"locked"` stamp
turns the baseline comparison red.
