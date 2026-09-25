# What the `fleet` pruning pass removed

Every sentence and clause the pass took out of `tk/skills/fleet/SKILL.md`, verbatim, so that any
one of them is put back in one edit. The verdicts, their reasons and the numbers are in
`fleet-report.md` beside this file. Line numbers are the original's at commit `98e71e1`
(`git show 98e71e1:tk/skills/fleet/SKILL.md`), cited as `F:` plus the line.

The file's inline evidence lands here under the `REPORT.md` rule for an own skill: `docs/` of
the repo, verbatim. The evidence that `tk/tests/test_fleet_ceiling.py` requires stays in the
skill, and the report lists it.

## Step 4 — the dispatch prompt

**F:190, CLAUSE (inline evidence).** Cut from item 5 of the prompt. The sentence it came from
ended `…returns announcing the wait, which is no report at all — twice on one project in the
first fleet run.`; the kept remainder is now two sentences, "…returns announcing the wait. That
is no report at all."

> — twice on one project in the first fleet run

## Step 4 — *The fleet's quota ceiling*

**F:221–222, DROP (inline evidence).** From the weekly-window bullet, after "spent 9 pp of the
weekly."

> That is about 1 pp for a small project and 4 pp for a package of four items.

**F:221, CLAUSE (inline evidence).** Cut from "The first fleet run, nine projects on
2026-09-13, spent 9 pp of the weekly." The date was pinned by
`test_fleet_ceiling.py`; the test now asserts `nine projects` in its place (T443).

> nine projects on 2026-09-13

**F:223, CLAUSE (inline evidence).** Cut from "It ran under a ceiling of 82% fixed by hand from
a menu, because this file named none."

> , because this file named none

**F:233, DROP (duplicate).** After "…killing one buys none of it back." The paragraph's bold
opener, "stop dispatching and close", already says it.

> What stops is the SENDING.

**F:239–240, DROP (duplicate).** After "…in "The wall" and in "The tick"'s three modes." The
sentence before it already sends the reader to `WINDOW.md`.

> Read it there rather than from a number copied to here.

**F:249–250, CLAUSE (inline evidence).** Cut from the last sentence of the "goes stale by
construction" bullet, which ended "…was read as current, by the monitoring turns and by the runs
themselves."

> , by the monitoring turns and by the runs themselves

## Step 4 — *The texts a run returns are born at the close*

**F:293, CLAUSE (inline evidence).** Cut from "Run against `tk-queue` in a throwaway queue on
2026-09-14: `done T001` printed `handoff-T001.md removed`." The date was the file's second ISO
date mark. `test_fleet_ceiling.py` keeps it in the comment of
`test_the_done_that_collects_the_briefing_is_measured_not_assumed`.

> on 2026-09-14

**F:303–305, DROP (inline evidence).** The paragraph's last sentence, after "A run killed between
its `done` and its return leaves them there for the close to find."

> That death is the measured one: a run the ceiling stopped in the first fleet run left an item
> closed, its pull request open, and its text in no queue at all.

## Step 5 — *A project fails alone*

**F:341–342, DROP (inline evidence, and a duplicate).** The empty-return paragraph's last
sentence. Its first half is evidence. Its second half repeats item 5 of step 4's prompt, "this
line is what stops one being produced".

> Two such returns arrived in the first fleet run; item 5 of step 4's prompt is what stops one
> being produced.

## Step 6 — *The consolidated vista*

**F:395–396, DROP (duplicate).** The last sentence of the "Birth the texts the runs returned"
paragraph. "A report line is a deferral with another name", in *The texts a run returns are born
at the close*, already says it, with `../kickoff/FINDINGS.md` owning the verdict.

> The close is where a returned text becomes an item; the report is where it stops being one.
