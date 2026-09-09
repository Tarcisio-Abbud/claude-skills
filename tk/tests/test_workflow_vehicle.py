#!/usr/bin/env python3
"""Doc-conformance proof for the workflow as the package's dispatch vehicle.

Run: python3 -m unittest discover -s tk/tests   (stdlib only, no deps)

WHAT CHANGED AND WHY. A package used to reach its runs through the Agent tool, and
every run's return landed in the orchestrator's own context: three generations in a
row closed between 210k and 232k. Dispatched as one dynamic workflow instead, the
same shape of package spent 48k on dispatching and receiving 21 runs, because the
script chooses what comes back. What the vehicle costs is a stretch with no seam in
it — nothing between the launch and the return is the orchestrator's own turn — and
one package walked into the quota wall there with the quota unread.

WHAT IS PROVED. That `AFK.md` step 3 names the vehicle with the Agent fallback in
the words `AUDIT.md` already uses; that the one line a reader greps for — the line
carrying `agent()` — carries BOTH halves of the rule that keeps the policy in one
place: model and effort out of `args`, and never a literal in the script; that no
contract is copied into the script; that the script stops at the first `null`; that
step 5 lets stages 1-5 run as a `lane-merger` and keeps 6 and 7 for the
orchestrator; that the tip is read and proved before the first `done`; that the
`lane-merger` row parses and reaches `tk-contract`; and that `WINDOW.md` counts
eight `--state` contents, with the eighth carrying the resume handle, and names the
launch as a seam.

WHAT IS NOT. That any orchestrator obeys it. Nothing here sees a session, a
workflow or a run; the prose is the subject, and the generator running is the only
behaviour under test.

VACUITY GUARD. Every extraction is scoped to a heading or to the table's markers,
and each class opens by asserting its scope is non-empty. Deleting the section
under test empties the search, and the guard fails before the assertions that would
otherwise pass over nothing.
"""

import os
import re
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.join(HERE, os.pardir)
KICKOFF = os.path.join(PLUGIN, "skills", "kickoff")
AFK = os.path.join(KICKOFF, "AFK.md")
WINDOW = os.path.join(KICKOFF, "WINDOW.md")
AUDIT = os.path.join(KICKOFF, "AUDIT.md")
POLICY = os.path.join(PLUGIN, "reference", "subagent-policy.md")
CONTRACT = os.path.join(PLUGIN, "bin", "tk-contract")

OPEN_MARKER = "<!-- tk:roles schema=3 -->"
CLOSE_MARKER = "<!-- /tk:roles -->"
COLUMNS = 7

# The row this file holds, with its five parsed cells. `note` is prose: the
# generator emits it verbatim and parses nothing, so it is asserted non-empty only.
ROLE = "lane-merger"
CELLS = ("sonnet", "session", "local", "none", "required")


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def flat(text):
    return " ".join(text.split())


def section(text, heading):
    """`text` from `heading` to the next heading of the same depth, that line aside.

    Depth matters here: step 3's own subsection is a `###` and belongs to the step,
    so a scan that stopped at any heading would cut the vehicle out of the step it
    is being asserted about.
    """
    m = re.search(r"^%s\s*$" % re.escape(heading), text, re.M)
    if not m:
        return ""
    depth = len(heading) - len(heading.lstrip("#"))
    rest = text[m.end():]
    nxt = re.search(r"^#{1,%d} " % depth, rest, re.M)
    return rest[:nxt.start()] if nxt else rest


def grep(path, needle):
    """(line number, text) for every line holding `needle`, as `grep -n` prints it.

    Run in process rather than through the binary: the acceptance criterion names
    `grep -n`, and what it is asking about is the file, not whether this host ships
    a `grep`. Line numbers are 1-based, so a failure names the line the criterion's
    own command would print.
    """
    return [(n, line) for n, line in enumerate(read(path).splitlines(), 1)
            if needle in line]


class TheVehicleOfStepThree(unittest.TestCase):

    def setUp(self):
        self.step = section(read(AFK), "## 3. Claim, then dispatch")
        self.flat = flat(self.step)

    def test_the_step_is_still_readable(self):
        """The guard: a renamed step empties every extraction below."""
        self.assertTrue(self.step.strip(), "AFK.md has no `## 3. Claim, then dispatch`")
        self.assertIn("### The vehicle", self.step,
                      "step 3 no longer carries the vehicle subsection")

    def test_the_workflow_is_the_vehicle_and_the_agent_fallback_is_the_same_graph(self):
        """One vehicle, one fallback, and the fallback is not a second design: it
        runs the SAME graph in series, which is `AUDIT.md`'s wording and is why a
        package that falls back changes nothing but its concurrency."""
        self.assertIn("dynamic workflow", self.flat,
                      "step 3 does not name the dynamic workflow as the vehicle")
        self.assertIn("~/.claude/tk/dispatch.md", self.flat,
                      "the site file that names the mechanism is not pointed at")
        self.assertIn("the Agent-tool fallback runs the same graph in series", self.flat,
                      "the fallback is described in words other than AUDIT.md's, so "
                      "the two files can drift apart on what the fallback is")
        self.assertIn("the Agent-tool fallback runs the same graph in series",
                      flat(read(AUDIT)),
                      "AUDIT.md no longer carries the phrase step 3 borrows")

    def test_the_prose_describes_the_graph_and_not_the_script(self):
        """A script copied into prose is a script that rots there. What the reader
        needs is the shape: one run per `agent()`, the lane serial, the tail last."""
        self.assertIn("One script per package and", self.flat,
                      "step 3 does not say the script is one per package")
        self.assertRegex(self.flat, r"lane is a serial loop.*implementer.*`lane-merger`",
                         "the lane's serial order — implementer, then merger — is not "
                         "in the step")
        self.assertRegex(self.flat, r"solo items run beside it.*tail closes the graph",
                         "the solos and the tail have no place in the graph as "
                         "described")
        self.assertNotIn("```js", self.step,
                         "the step carries a copy of the script instead of the graph")

    def test_the_line_grep_finds_carries_both_halves_of_the_rule(self):
        """The acceptance criterion greps for `agent()` and expects the rule there.
        Both halves ride on ONE line on purpose: a reader who greps sees the
        permission and the prohibition together, and a rule split across a paragraph
        break is a rule half of which is read."""
        hits = grep(AFK, "agent()")
        self.assertTrue(hits, "no line of AFK.md carries `agent()`")
        carrying = [(n, ln) for n, ln in hits
                    if "`model`" in ln and "`effort`" in ln and "`args`" in ln]
        self.assertTrue(carrying,
                        "no `agent()` line names model, effort and args together: "
                        "%r" % [ln for _, ln in hits])
        for n, ln in carrying:
            with self.subTest(line=n):
                self.assertRegex(ln, r"never from a literal",
                                 "the line permits reading from args without "
                                 "forbidding the literal, which is the half that "
                                 "forks the policy")

    def test_the_two_values_are_passed_by_different_means(self):
        """`session` is not a value the harness takes: it is the absence of the key.
        A script passing the string would pin an effort nobody chose."""
        self.assertIn("`model` always, `effort` by OMITTING the key where the row "
                      "reads `session`", self.flat,
                      "the step does not say model is always passed and a `session` "
                      "effort is passed by omission")

    def test_no_contract_is_copied_into_the_script(self):
        """The block is generated per run and the lane contract is a file. Either
        one copied into the script is the fork `tk-contract` exists to prevent."""
        self.assertRegex(self.flat, r"No contract is copied into the script",
                         "the step does not forbid copying a contract into the script")
        self.assertRegex(self.flat, r"verbatim through `args`",
                         "the contract block does not reach the script through args")
        self.assertIn("the lane contract above reaches it as a path", self.flat,
                      "the lane contract is not handed over as a path")
        self.assertEqual(self.step.count("LANE-CONTRACT.md"), 1,
                         "step 3 names the lane contract file twice: the sibling rule "
                         "is one pointer line, and the file is under a size lock")

    def test_the_concurrency_ceiling_is_the_site_key(self):
        """Two ceilings meet here and the smaller one wins. What the step must say
        is what happens to the difference: it stays unused, because the alternative
        that would fill it — Agent runs beside the workflow — puts the returns back
        in the orchestrator's context, which is what the vehicle exists to stop."""
        self.assertIn("max-local-subagents", self.flat,
                      "the step does not name the site key concurrent runs count "
                      "against")
        self.assertIn("min(16, nproc - 2)", self.flat,
                      "the harness's own cap is not named beside the site key")
        self.assertRegex(self.flat, r"difference stays UNUSED",
                         "the step does not say what happens to the difference "
                         "between the two caps")
        self.assertIn("never Agent runs whose return lands in this session's context",
                      self.flat,
                      "the step leaves Agent runs beside the workflow open as a way "
                      "to fill the difference")

    def test_the_first_null_stops_the_dispatching(self):
        """A `null` is a dead run, and the three attempts belong to verify. Charging
        one to the item would spend an item's budget on a fact about the clock."""
        self.assertRegex(self.flat, r"stops dispatching at the first `null`",
                         "the step does not stop the script at the first null")
        self.assertIn("A `null` is the wall or a skip, never one of the three attempts",
                      self.flat, "the step does not say what a null is and is not")

    def test_the_launch_is_named_as_a_seam(self):
        """Step 3 is where the launch happens, and the rule that fires there lives
        in WINDOW.md. The step points; the sibling owns."""
        self.assertRegex(self.flat, r"The launch is a seam of its own: `WINDOW.md`",
                         "step 3 does not send the reader to WINDOW.md for what the "
                         "launch owes")


class TheLaneMergerOfStepFive(unittest.TestCase):

    def setUp(self):
        self.step = section(read(AFK), "## 5. Verify every delivery")
        self.flat = flat(self.step)

    def test_the_step_is_still_readable(self):
        self.assertTrue(self.step.strip(), "AFK.md has no `## 5. Verify every delivery`")

    def test_the_first_five_stages_may_run_as_a_lane_merger(self):
        """The cycle used to be the orchestrator's work end to end. What moves into
        the workflow is stages 1-5; what may never run it is the run that wrote the
        code, which would be a run judging itself."""
        hits = grep(AFK, "lane-merger")
        self.assertTrue(hits, "no line of AFK.md names `lane-merger`")
        self.assertRegex(self.flat,
                         r"Stages 1–5 may run inside the workflow as one `lane-merger` run",
                         "step 5 does not put stages 1-5 inside the workflow as a "
                         "lane-merger run")
        self.assertIn("never the run that implemented the item", self.flat,
                      "step 5 lets the item's own implementer merge its own work")

    def test_the_last_two_stages_stay_with_the_orchestrator(self):
        """Stage 6 opens the pull request and stage 7 writes the queue. Neither is a
        subagent's to do, and the moment they happen is the workflow's return."""
        self.assertRegex(self.flat,
                         r"stages 6 and 7 are the orchestrator's own, on the "
                         r"workflow's return",
                         "step 5 does not keep stages 6 and 7 for the orchestrator")
        self.assertRegex(self.flat,
                         r"first green merge the orchestrator SEES",
                         "stage 6 still fires on a merge the orchestrator has not "
                         "seen, which inside a workflow it cannot")
        self.assertIn("or in the first cycle where it dispatches by Agent", self.flat,
                      "stage 6 no longer covers the fallback path, where the "
                      "orchestrator does see each cycle")

    def test_the_tip_is_read_and_proved_before_the_first_done(self):
        """A merger's report is a self-report, and the orchestrator's `done` is
        irreversible bookkeeping. What stands between them is the remote."""
        self.assertRegex(self.flat,
                         r"Before the first `done` the remote is what is true",
                         "step 5 does not put the remote before the first done")
        self.assertIn("git log --merges origin/spec/<m>-<slug>", self.flat,
                      "the command that reads what actually merged is not prescribed")
        self.assertIn("run ONCE, by script with the exit codes read", self.flat,
                      "the tip's proof is not run once, by script, with the exit "
                      "codes read")
        self.assertRegex(self.flat, r"timeout well above 120 s",
                         "the tip's proof carries no timeout above the harness's "
                         "own 120 s, which reports a long suite as NOT-RUN")
        self.assertIn("the whole suite and the criterion of every item that tip carries",
                      self.flat,
                      "the tip's proof is not the whole suite plus every merged "
                      "item's criterion")

    def test_a_red_tip_makes_a_decision_naming_the_merge(self):
        """Red there is not the item's failure to prove: it is a green the merger
        reported and the tip refutes, so the item cannot be closed on it."""
        self.assertRegex(self.flat, r"false green a merger returned",
                         "step 5 does not name red at the tip as the merger's false "
                         "green")
        self.assertIn("becomes a DECISION naming the sha of its merge, and it is "
                      "never closed", self.flat,
                      "a red item at the tip has no outcome naming its merge")

    def test_the_tail_does_not_answer_for_the_tip(self):
        """The tail runs its suite after the `done`s, so a package that leaned on it
        would close every item before anything checked the tip."""
        self.assertIn("The tail's suite does not answer this — it runs after the `done`s",
                      self.flat,
                      "step 5 does not say why the tail's own suite is too late")

    def test_the_done_when_asks_for_the_tip(self):
        """A rule outside the step's closer is a rule the step does not gate on."""
        done = self.flat[self.flat.index("**Done when:**"):]
        self.assertIn("the tip carried the whole suite and every merged item's "
                      "criterion before the first `done`", done,
                      "step 5's `Done when` does not ask for the tip's proof")


class TheLaneMergerRow(unittest.TestCase):

    def setUp(self):
        text = read(POLICY)
        # On its own LINE, never merely present: the schema paragraph above the
        # table quotes both markers inside code spans, and a search by substring
        # stops there — with an empty table and every check below passing over
        # nothing.
        opened = re.search(r"^%s\s*$" % re.escape(OPEN_MARKER), text, re.M)
        closed = re.search(r"^%s\s*$" % re.escape(CLOSE_MARKER), text, re.M)
        body = text[opened.end():closed.start()] if opened and closed else ""
        lines = [ln.strip() for ln in body.splitlines() if ln.strip().startswith("|")]
        self.rows = [[c.strip() for c in ln.strip("|").split("|")] for ln in lines[2:]]
        self.by_role = {r[0]: r for r in self.rows}

    def test_the_table_is_still_readable(self):
        self.assertTrue(self.rows, "the role table has no data rows")

    def test_the_row_carries_its_seven_cells(self):
        row = self.by_role.get(ROLE)
        self.assertIsNotNone(row, "the table has no `%s` row" % ROLE)
        self.assertEqual(len(row), COLUMNS,
                         "`%s` has %d cells, not %d — the parser is positional and "
                         "refuses the whole table" % (ROLE, len(row), COLUMNS))
        self.assertEqual(tuple(row[1:6]), CELLS,
                         "`%s` no longer reads model/effort/venue/pr/checkpoint as "
                         "the ticket fixed them" % ROLE)
        self.assertTrue(row[6], "`%s` has an empty `note` cell" % ROLE)

    def test_the_checkpoint_cell_is_what_the_role_owes(self):
        """`pr` and `checkpoint` disagree in this row, which is the whole point of
        their being two cells: the merger pushes the lane's branch and opens no
        pull request, so dropping the invariant with the PR would drop it from
        exactly the role that merges."""
        row = self.by_role[ROLE]
        self.assertEqual(row[4], "none")
        self.assertEqual(row[5], "required")
        block = subprocess.run([sys.executable, CONTRACT, "--role", ROLE],
                               capture_output=True, text=True).stdout
        self.assertIn("checkpoint invariant", block.lower(),
                      "`%s` is marked `checkpoint = required` and its generated "
                      "block carries no invariant" % ROLE)

    def test_tk_contract_emits_the_block(self):
        """The table is data for a generator, so the proof is the generator running:
        a cell outside its closed vocabulary refuses the whole file, silently to a
        reader and loudly here."""
        r = subprocess.run([sys.executable, CONTRACT, "--role", ROLE],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0,
                         "tk-contract cannot emit `%s`:\n%s" % (ROLE, r.stderr))
        self.assertIn("role=%s" % ROLE, r.stdout)


class TheEighthStateContent(unittest.TestCase):

    def setUp(self):
        self.text = read(WINDOW)
        self.wall = section(self.text, "## The wall")

    def test_the_wall_is_still_readable(self):
        self.assertTrue(self.wall.strip(), "WINDOW.md has no `## The wall`")

    def bullets(self):
        """The contents of step 3, as bullet lines.

        Bounded on both sides: the count is the assertion, so a scan that ran past
        the list would count the lane's five as well and read eight where there are
        thirteen.
        """
        start = self.wall.index("Say what is left, in `--state`")
        end = self.wall.index("A package holding an accumulated lane", start)
        return [ln for ln in self.wall[start:end].splitlines()
                if re.match(r"^\s+- ", ln)]

    def test_the_list_holds_eight_contents(self):
        self.assertEqual(len(self.bullets()), 8,
                         "step 3 of the wall lists %d contents, not eight"
                         % len(self.bullets()))
        self.assertIn("Eight contents", self.wall,
                      "the list is not introduced as eight contents")

    def test_every_site_that_counts_them_says_eight(self):
        """A retraction applies at every site of the claim: four sentences elsewhere
        in this file count the same list, and one left saying seven sends a reader
        to a content that is not there."""
        stale = [(n, ln) for n, ln in enumerate(self.text.splitlines(), 1)
                 if re.search(r"\bseven (?:contents|above|,)", ln)]
        self.assertFalse(stale,
                         "these lines still count the `--state` contents as seven: %r"
                         % stale)

    def eighth(self):
        """The last bullet of step 3, with its continuation lines and nothing after."""
        start = self.wall.index(self.bullets()[-1])
        end = self.wall.index("A package holding an accumulated lane", start)
        return flat(self.wall[start:end])

    def test_the_eighth_content_is_the_resume_handle(self):
        block = self.eighth()
        self.assertIn("workflow's resume handle", block,
                      "the eighth content is not the workflow's resume handle")
        for part in ("script's path", "run id", "`args` were written to",
                     "transcript directory"):
            with self.subTest(part=part):
                self.assertIn(part, block,
                              "the resume handle does not name the %s" % part)
        self.assertIn("still in flight when the handoff was written", block,
                      "the handle does not say whether the run was in flight, which "
                      "is what tells the successor there is anything to resume")

    def test_the_successor_reads_the_tip_and_not_the_map(self):
        """Resuming a workflow across sessions is unmeasured, so the handle is a
        pointer to a journal and never a promise the run can be re-entered."""
        eighth = self.eighth()
        self.assertIn("journal", eighth,
                      "the handle points at no journal, so a successor whose run "
                      "cannot be resumed has nothing to read")
        self.assertIn("item→merge map below as EMPTY", eighth,
                         "the successor is not told to treat the item→merge map as "
                         "empty, and would close items on a map nobody updated")

    def test_the_launch_is_one_of_the_seams(self):
        gen = section(self.text, "## Generations, and `--budget N`")
        self.assertTrue(gen.strip(), "WINDOW.md has no `## Generations` section")
        enumeration = flat(gen[:gen.index("- **Refresh the handoff.**")])
        self.assertIn("the dispatch of a workflow", enumeration,
                      "the seam enumeration does not name the dispatch of a workflow")

    def test_the_handoff_is_written_after_the_launch(self):
        gen = flat(section(self.text, "## Generations, and `--budget N`"))
        self.assertRegex(gen, r"handoff is written right AFTER the launch",
                         "the workflow seam does not put the handoff after the "
                         "launch, and before it the run id does not exist")
        self.assertRegex(gen, r"the orchestrator holds no seam at all",
                         "the stretch between launch and return is not named as "
                         "seamless, which is the whole reason the quota goes unread")
        self.assertRegex(gen, r"reads `\.\./\.\./bin/tk-quota` there",
                         "nothing reads the quota between the launch and the return")


if __name__ == "__main__":
    unittest.main()
