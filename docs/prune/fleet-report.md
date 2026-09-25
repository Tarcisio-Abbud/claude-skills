`docs/prune/fleet-report.md`

# Pruning report — `tk/skills/fleet/SKILL.md`

A run of `/tk:prune` scoped to one file, `tk/skills/fleet/SKILL.md`, the fleet skill's only
markdown file (`ls tk/skills/fleet/` lists `SKILL.md` alone). This is the pass that T292's
criterion branch 2 still owed. T292 (PR #94, slice 3, `4a02151`) pruned this file to zero
marks, and its commit says branch 2 "is not available in this package": this committed
report would have made `test_prune_lock.py` demand a lock row, and the lock could not then be
regenerated. PR #114 (T396, merged at `98e71e1`) then grew the file from 312 to 434 lines with
four rules. Those rules are the fleet's quota ceiling, the stale-reading floor, where the texts
a run returns are born, and the foreground-suite order. That growth is what this pass prunes.
The branch is the output directory. The removed material is in `fleet.md` beside this file,
keyed to the original at `98e71e1`, and `where` below cites that original as `F:` plus the line.

**Step-3 date check.** `git log -1 --format=%cs -- tk/skills/fleet/SKILL.md` gives
2026-09-22 (#114's merge). No committed report existed before this one, so no verdict had
graded any rule of the file. T292's pass verified its checks by script and recorded them only in
its commit message.

**What the suite pins.** Twelve test files grep `fleet`. Two of them are mutation harnesses:
`mutations.py` and `mutations_tk_contract.py` mutate bin code, and neither anchors on this file.
Before cutting, the pass extracted every string literal of `tk/tests/*.py`, six characters or
longer, that occurs in the file, raw or whitespace-folded: 209 literals. After the cuts, 207
still occur. The two that no longer occur are `measured` (`test_tk_collisions`,
`test_tk_prune_measure`) and `pull request open` (`test_package_ledger`). None of those three
modules reads `fleet/SKILL.md`. `test_fleet_ceiling.py` pins 27 content anchors, several of
them inline evidence. Each pinned phrase survives verbatim in the section the test cuts on.

## 1. Numbers

`python3 tk/bin/tk-prune-measure tk/skills/fleet/SKILL.md --targets`, before (`98e71e1`) and
after. **Bold** marks a value over a ceiling.

| metric | before | after |
|---|---|---|
| lines | 434 | 428 |
| body words | 4291 | 4163 |
| sentences | 335 | 339 |
| mean words per sentence (22) | 12.8 | 12.3 |
| max words in a sentence (25) | **36** | 25 |
| sentences over 30 words (4) | **5** | 0 |
| description words (30) | 27 | 27 |
| inline evidence (0) | **2** | 0 |
| narrated outcomes | 6 | 6 |
| pointers to other files | 39 | 39 |
| negations | 93 | 92 |
| defined terms | 3 | 3 |
| terms defined in a sibling too (0) | 0 | 0 |
| environment copies | 9 | 8 |

**The last mark was pinned by the suite.** It was `2026-09-13` at line 221, in the
weekly-window bullet of *The fleet's quota ceiling*.
`test_fleet_ceiling.TheQuotaCeiling.test_the_default_carries_the_measurement_that_produced_it`
asserted `"2026-09-13"` inside that section, and the bin marks every ISO date in the body. The
test guards that the default stands on a measurement, and the measurement is `nine projects`
and `9 pp of the weekly`, not the day. So the lane's orchestrator moved the test's anchor from
the date to `nine projects`, and the date went (a CLAUSE row below). The file's other ISO date,
`2026-09-14`, was not pinned and went too.

**The structural checks**, by script against the original:

- The backtick spans are identical as a multiset: 139 spans, 69 distinct, before and after.
- The pointer count is identical: 39 before and 39 after, by the bin's `pointers` metric.
- The frontmatter, all 11 table rows and all 4 fenced blocks are byte-identical. No table cell
  carried a sentence the bin marked.
- Every heading and every step number is identical.
- No line exceeds 100 columns except the frontmatter `description`, which was already over.

## 2. Table

KEEP rows group by paragraph and name the run each one serves. Every DROP and CLAUSE row quotes
what went, and `fleet.md` holds the same text for a one-paste reversal.

| where | sentence / range | verdict | why |
|---|---|---|---|
| F:3 | `description` | KEEP | 27 words, under the 30 ceiling. It names the command, the unattended package, the consolidated vista and both loads. Unchanged |
| F:9–12 | fleet run, fleet orchestrator, project run; "It implements nothing and edits no code." | KEEP | every fleet run: the orchestrator's role boundary |
| F:14–18 | two units, PROJECT and ITEM | KEEP | every refill and checkpoint decision; the rest of the file rests on it |
| F:20–22 | the fleet writes no queue; `tk-queue` resolves from the cwd | KEEP | every write the fleet is tempted into; the single-writer rule |
| F:26–39 | run `tk-roster`, its five sections, the section table | KEEP | step 1 of every run; pinned by `test_tk_roster` (`not dispatchable`, `` `fleet-deny` names no queue ``) |
| F:41–46 | never build a path from a queue name; read unroutable queues with `--dir` | KEEP | a roster with a `## not dispatchable` section; pinned by `test_window_tick` |
| F:48–52 | the allow/denylist belongs to the site file | KEEP | a user asking the fleet to skip a project |
| F:54–58 | both `names no queue` sections are stray entries | KEEP | a typo in a site-file key |
| F:60–63 | the two exits of `tk-roster` | KEEP | a rotten site file; an empty roster (two of the four stop conditions) |
| F:65–69 | step 1 **Done when** | KEEP | closes step 1 |
| F:73–81 | size by the eligible count of `tk-queue pack`, from the project's directory | KEEP | step 2 of every run; the command is pinned by `test_afk_audit` |
| F:83–86 | eligible zero leaves the fleet; one line per exclusion reason | KEEP | a project with no eligible items |
| F:88–90 | largest first, ties keep the roster's order, and why | KEEP | ordering the fleet |
| F:92–93 | `pack` takes no claim | KEEP | a sized project never dispatched |
| F:95–99 | step 2 **Done when** | KEEP | closes step 2 |
| F:103–107 | `W` defined; the divisor splits the LOCAL, RAM-axis ceiling, never `max-local-opus` | KEEP | choosing `W`; split into three sentences (§3) |
| F:109–120 | read the ceilings with no divisor; paste the second block verbatim | KEEP | every dispatch's contract block; "is a fork of the policy" pinned by `test_window_tick` |
| F:122–126 | an absent ceiling is not a zero; decide and log the deviation | KEEP | a site file with no `max-local-subagents` |
| F:128–130 | the divisor never touches `max-cloud-subagents` | KEEP | a project run's cloud share |
| F:132–154 | *What the divisor does not count*: the peak, default `W` to `ceiling // 2`, report the peak | KEEP | fixing `W`; the measurement line |
| F:156–162 | step 3 **Done when** | KEEP | closes step 3 |
| F:166–171 | background subagent on the `fleet-orchestrator` row; the prompt names the file, never the command | KEEP | every dispatch |
| F:173–187 | prompt items 1–4: block, absolute load path, the load's flags with `--budget 1`, the directory first | KEEP | every dispatch prompt |
| F:188–191 | prompt item 5: the suite in the FOREGROUND with a declared timeout; step 5 grades an empty return | KEEP | every dispatch prompt; pinned by `test_fleet_ceiling` (`TheDispatchPrompt`); split (§3) |
| F:190 | "— twice on one project in the first fleet run" | CLAUSE | inline evidence; the rule and the defect it prevents stay |
| F:192–194 | prompt item 6: the texts go into the package handoff BEFORE the `done` | KEEP | every dispatch prompt; pinned |
| F:196–199 | no barrier between waves | KEEP | every return: refill at once |
| F:203–206 | read the quota before every project dispatch, both windows, never once at the start | KEEP | every dispatch; pinned (`TheQuotaCeiling`); split (§3) |
| F:208–213 | the bin can refuse a window; no weekly figure authorises nothing | KEEP | a `tk-quota` exit 2, or an exit 0 that refused one window |
| F:215–218 | the quota ceiling is a third ceiling, bounding the WINDOW, not AGENTS | KEEP | keeps the ceiling out of `--fleet`'s divisor; pinned |
| F:220–221 | 80% used is the default; "on nine projects, spent 9 pp of the weekly" | KEEP | every dispatch compares against it. The measurement is pinned (§1) |
| F:221 | "nine projects on 2026-09-13" → "on nine projects" | CLAUSE | inline evidence: the run's date, the last bin mark; the test's anchor moved to `nine projects` (§1) |
| F:221–222 | "That is about 1 pp for a small project and 4 pp for a package of four items." | DROP | inline evidence, not pinned; no step of the file sizes a fleet by it |
| F:222–223 | "It ran under a ceiling of 82% fixed by hand from a menu" | KEEP | pinned evidence (`82% fixed by hand`), beside the default it calibrates |
| F:223 | ", because this file named none" | CLAUSE | inline evidence: the history of the defect #114 fixed |
| F:223–224 | above the default a fleet cannot finish; crossing it spends the week | KEEP | the reason the number is a ceiling |
| F:225–226 | the 5-hour window adds no number; `WINDOW.md`'s "The tick" owns it | KEEP | every dispatch; pinned, with the tick's floors asserted absent |
| F:227–230 | the override is named in the firing turn, NOT a site-file key | KEEP | a user who wants another ceiling; pinned |
| F:232–233 | above the ceiling, stop dispatching and close; the runs in flight keep running | KEEP | a reading over the ceiling; pinned |
| F:233 | "What stops is the SENDING." | DROP | duplicate: the bold opener "stop dispatching and close" says it |
| F:234–235 | the close names the ceiling, the reading and the projects; a fourth stop condition | KEEP | the close after a ceiling stop; pinned |
| F:237–239 | a stale reading is a floor; `(read 58m ago)`; `WINDOW.md` owns what the age makes the percentage | KEEP | every aged reading; pinned; split (§3) |
| F:239–240 | "Read it there rather than from a number copied to here." | DROP | duplicate: the sentence before it already sends the reader to `WINDOW.md` |
| F:242–248 | the three consequences: above stops, below authorises nothing, taken AT a return | KEEP | every stale reading; pinned |
| F:249 | "In the first fleet run a 58-minute-old figure was read as current" | KEEP | pinned evidence (`58-minute-old figure was read as current`) |
| F:249–250 | ", by the monitoring turns and by the runs themselves" | CLAUSE | inline evidence, not pinned; the two-axis review put ", by the monitoring turns" back, since the passive named no reader and the phrase before it is pinned (+4 words) |
| F:254–262 | *The quota wall*: the FLEET's; stop on the first quota failure; each run keeps its own `WINDOW.md` | KEEP | a run returning a quota failure; pinned (`stop dispatching`) |
| F:266–271 | the fleet births the texts, the run does not; the hook refuses `add` in a subagent; twelve texts, none born; a report line is a deferral | KEEP | a run returning a text; pinned (`TheTextsTheRunsReturn`); split (§3) |
| F:273–279 | the birth is one menu at the close; the `add --dir` block | KEEP | the close; the fenced block is byte-identical and pinned |
| F:281–284 | why `--dir`; the head of the file holds because the address is explicit; one `AskUserQuestion` | KEEP | the close's menu; pinned; split (§3) |
| F:286–290 | unattended, the birth waits on T045 in the `.ambiente` queue | KEEP | an unattended fleet's close; pinned |
| F:292–296 | a `done` collects the briefing it closes; the two printed lines | KEEP | why item 6 says PACKAGE handoff; the printed lines are pinned evidence |
| F:293 | "on 2026-09-14" | CLAUSE | inline evidence, the second ISO-date mark; not pinned (the test keeps it in a comment) |
| F:298–303 | the package handoff hangs on the item that closes LAST; the last close sends the texts into the return; a killed run leaves them for the close | KEEP | a run writing its texts; pinned (`hangs on an item still open`, `` `WINDOW.md`'s *The wall*, step 2 ``); split twice (§3) |
| F:303–305 | "That death is the measured one: a run the ceiling stopped in the first fleet run left an item closed, its pull request open, and its text in no queue at all." | DROP | inline evidence; the rule it backs (prompt item 6, and the sentence before it) stays |
| F:309–320 | *The checkpoint is a completed project*: refill by step-2 order; checkpoint the textual report on every return | KEEP | every return |
| F:322–330 | step 4 **Done when** | KEEP | closes step 4; pinned |
| F:334–340 | a project fails alone; an empty return is a failure and never an approval | KEEP | an empty, errored or unclosed return; pinned (`A run may return empty`) |
| F:341–342 | "Two such returns arrived in the first fleet run; item 5 of step 4's prompt is what stops one being produced." | DROP | inline evidence, and a duplicate of item 5's own "this line is what stops one being produced" |
| F:344–347 | the quota wall is the one exception; the stop conditions are four | KEEP | the fleet's stop set; pinned |
| F:349–356 | never repair a run's work; verify by artefact | KEEP | a failed run |
| F:358–362 | step 5 **Done when** | KEEP | closes step 5 |
| F:366–373 | the textual report and the vista; `vista.md` is the contract | KEEP | the close |
| F:375–392 | the three fleet-only things: `fleet` in the filename, project on every card, the measurement and deviation lines with the quota ceiling and readings | KEEP | the close; pinned (`TheClose`, `test_vista_cold_reader`); one split (§3) |
| F:394–395 | birth the texts the runs returned; it is the close's, not `vista.md`'s | KEEP | the close; pinned |
| F:395–396 | "The close is where a returned text becomes an item; the report is where it stops being one." | DROP | duplicate: "a report line is a deferral with another name" (F:271) says it, with `FINDINGS.md` owning the verdict |
| F:398–409 | a red gate does not hold the fleet; step 6 **Done when** | KEEP | the close; pinned |
| F:413–420 | the load is a parameter; the loads table | KEEP | the argument |
| F:422–427 | `afk` enters at `../kickoff/SKILL.md`, not `AFK.md` | KEEP | every `afk` dispatch |
| F:429–431 | a load with no queue is unordered | KEEP | `docs-audit` |
| F:433–434 | a load the table does not name is not a load | KEEP | an unknown argument (stop) |

Counts: 60 KEEP, 6 DROP, 5 CLAUSE, 0 MOVE, 0 FIT. The inline evidence left the skill as DROP
and CLAUSE rows, and each is stored verbatim in `fleet.md`. That file is the destination the
`REPORT.md` MOVE table names for an own skill's evidence. So one edit puts any of them back. No
FIT rows: every long sentence was split, and no sentence was deleted to meet a ceiling.

## 3. Splits and notes

- **No split suggestion.** The file is one skill with one entry, and the load table already
  parameterises the only branch. `SKILL-MECHANICS`'s split-by-invocation criterion finds no
  second consumer.
- **Rewording notes: the long-sentence splits, carrying no verdict.** Ten sentences ran over 25
  words. One went with a DROP (F:303). The other nine were split at their own clause boundaries,
  and each keeps every word that carries a rule:
  - F:104–107: "…LOCAL ceiling, read from the site file by the bin — the RAM axis (…), never
    the quota axis (…), which … and which `--fleet` does not touch." became "…LOCAL ceiling,
    which the bin reads from the site file. That is the RAM axis, `max-local-subagents`. It is
    never the quota axis, `max-local-opus`, which … and `--fleet` does not touch."
  - F:189–190: ", which is no report at all" became "That is no report at all."
  - F:205–206: ": a fleet is hours long…" became ". A fleet is hours long, and…"
  - F:237–238: "— `(read 58m ago)` on the line — and what that makes the percentage is" became
    ", `(read 58m ago)` on the line. What that age makes the percentage is"
  - F:267–269: "…`ask-before-queue-add` hook, and the refusal is the point:" became "…hook. The
    refusal is the point:"
  - F:281: "The fleet's cwd is its own and … from the cwd, so an `add`" became "…its own, and
    … from the cwd. So an `add`"
  - F:299–300: "…names it, so every earlier close…" became "…names it. So every earlier close
    leaves it standing, and…"
  - F:301–302: "…survives the close: the texts go in the return…" became "…survives the close.
    The texts then go in the return…"
  - F:392: "each with its age: this run is the one…" became "each with its age. This run is
    the one…"
- **Paragraphs reflowed** to the file's 100-column wrap, wherever a cut left a short line.
- **No defined term was touched.** The bin's three terms, **textual report** (twice) and
  **measurement line**, keep their coining lines.
- **Pinned sentences kept verbatim.** Every phrase `test_fleet_ceiling.py` asserts still sits in
  the section the test cuts on. Some of those phrases are the evidence the test requires beside
  its rule: `9 pp of the weekly`, `82% fixed by hand`,
  `58-minute-old figure was read as current`, `twelve such texts and none was born`, and the two
  `handoff-T001.md` lines. Only the ISO date among them is a bin mark (§1).

## 4. Paths

- Pruned in place, this branch: `tk/skills/fleet/SKILL.md`.
- Removed material: `docs/prune/fleet.md`.
- The two docs are over their ceilings by nature, as every sibling report is. The bin counts
  each table row as one sentence, and both files quote the removed evidence with its dates.
  This report measures max sentence 49, 9 sentences over 30 and 8 inline evidence. `fleet.md`
  measures max sentence 36 and 2 inline evidence. `dispatch-report.md` measures 64, 39 and 6.
  Neither doc is a skill an agent executes, and neither is in the lock.
- This report: `docs/prune/fleet-report.md`. Its presence makes
  `test_prune_lock.py`'s `test_every_pruned_skill_has_its_file_locked` require a
  `tk/skills/fleet/SKILL.md` row in `tk/tests/prune-lock.json`. Until that row exists, the test
  fails with "fleet was pruned (fleet-report.md) and its SKILL.md is not locked". The lock
  regeneration in this same branch (T443) owns that row, which carries an empty `over` list:
  the date left the file (§1). This pass wrote no lock file.

## 5. Proof of the target skill

The target is prose, so its proof is **the reviewed diff of rules**: the two-axis
`/mattpocock-skills:code-review` over this branch. Give it three inputs. Standards gets the
`writing-for-agents` path. Spec gets this table and the original at `98e71e1`. The smell
baseline is declared inapplicable, because the target is prose. The suite's content anchors are
the standing regression check. `test_fleet_ceiling.py` holds 27 tests, and every other test that
reads this file stayed green on the pruned copy: `test_agent_hygiene`, `test_vista_cold_reader`,
`test_afk_audit`, `test_tk_roster`, `test_manifests`, `test_root_cause`, `test_window_tick`,
`test_tk_contract` and `test_tk_queue`.
