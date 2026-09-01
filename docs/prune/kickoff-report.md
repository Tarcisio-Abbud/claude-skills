`docs/prune/kickoff-report.md`

# Pruning report — the `kickoff` skill (`SKILL.md`, `AFK.md`, `WINDOW.md`)

The fifth run of `/tk:prune`, executed as prune 7/8 of the pruning track's spec, and the
first over a multi-file skill. The removed material is beside this file, in `kickoff.md`,
keyed to the pre-prune originals at commit `7fb9ad0`. Unlike the earlier passes this one ran
inside an unattended package, so the pass edited the skill in its branch directly; the
output-directory rite of `prune/SKILL.md` collapses into the branch itself, which is what
the closing review reads. **First pass over this skill**: there is no earlier committed
report, so no rule needed the step-3 date check against one.

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
| WINDOW.md, whole | — | measured only | the ticket scopes it to step 1's measurement; no verdicts this pass, numbers in §1 |

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
