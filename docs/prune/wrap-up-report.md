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
