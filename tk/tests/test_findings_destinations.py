#!/usr/bin/env python3
"""Doc-conformance proof for the destinations an unattended finding has, and for
the three roles the package dispatches into them.

Run: python3 -m unittest discover -s tk/tests   (stdlib only, no deps)

WHY THIS FILE EXISTS. A package used to answer every finding with one command:
`tk-queue add`. The hydra that came of it was measured on the queue this rule was
written against — 74 of 110 open items born in seven days, all of them out of a
review campaign or an afk package. So the second rung of the unattended ladder was
retired, and `skills/kickoff/FINDINGS.md` replaced it with three destinations that
keep the finding inside the package: a correction commit, a line in the pull
request's body, a sweep lane over the UNION of the package's pull requests. A
finding that reaches none of them is not filed away — the file says so in the one
sentence a report line would otherwise satisfy.

WHAT IS PROVED. That the three destinations are written, numbered and ordered; that
the audit's own moment — before the first run, with no lane and no pull request —
has its own destination and it is not the queue; that AFK.md's two sites route
there and prescribe no `add` of their own; that AUDIT.md's **backlog** outcome does
the same while the REGRILL recipe, which halts the package instead, stays runnable;
and that the three roles the package needs parse out of the role table and reach
`tk-contract`.

WHAT IS NOT. That an orchestrator obeys any of it. Nothing here sees a session, and
the close's own block is what carries that.

VACUITY GUARD. Every extraction below is scoped to a heading or to the table's
markers, and each class opens by asserting its scope is non-empty. Deleting the
section under test empties the search, and the guard fails before the assertions
that would have passed over nothing — the failure mode this directory has paid for
more than once.
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
AUDIT = os.path.join(KICKOFF, "AUDIT.md")
FINDINGS = os.path.join(KICKOFF, "FINDINGS.md")
POLICY = os.path.join(PLUGIN, "reference", "subagent-policy.md")
CONTRACT = os.path.join(PLUGIN, "bin", "tk-contract")

OPEN_MARKER = "<!-- tk:roles schema=3 -->"
CLOSE_MARKER = "<!-- /tk:roles -->"
COLUMNS = 7

# The rows this file holds, with their five parsed cells. `note` is prose and is
# asserted non-empty only: the generator emits it verbatim and parses nothing.
NEW_ROWS = {
    "root-cause-auditor": ("opus", "high", "local", "none", "none"),
    "lane-implementer": ("opus", "high", "local", "opens", "required"),
    "cold-reviewer": ("opus", "high", "local", "none", "required"),
}
# The two rows the new ones join rather than replace: `AFK.md`'s *The fixer cap*
# and `tk-contract` both read these by name.
KEPT_ROWS = ("review", "fixer")

QUEUES_AN_ITEM = "tk-queue add"
OLD_SECTION = "A session finding, unattended"


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def flat(text):
    return " ".join(text.split())


def section(text, heading):
    """`text` from `heading` to the next `## ` heading, the heading line aside."""
    m = re.search(r"^%s\s*$" % re.escape(heading), text, re.M)
    if not m:
        return ""
    rest = text[m.end():]
    nxt = re.search(r"^## ", rest, re.M)
    return rest[:nxt.start()] if nxt else rest


def rows():
    """The data rows of the role table, as lists of stripped cells.

    Read between the markers and never over the whole file: a pipe table written
    anywhere else in the document would otherwise answer for the policy.
    """
    text = read(POLICY)
    # On its own LINE, never merely present: the schema paragraph above the table
    # quotes both markers inside code spans, and a search by substring stops there
    # — with an empty table and every check below passing over nothing.
    opened = re.search(r"^%s\s*$" % re.escape(OPEN_MARKER), text, re.M)
    closed = re.search(r"^%s\s*$" % re.escape(CLOSE_MARKER), text, re.M)
    if not (opened and closed):
        return []
    body = text[opened.end():closed.start()]
    lines = [ln.strip() for ln in body.splitlines() if ln.strip().startswith("|")]
    return [[c.strip() for c in ln.strip("|").split("|")] for ln in lines[2:]]


class TheThreeRolesAreInTheTable(unittest.TestCase):

    def setUp(self):
        self.rows = rows()
        self.by_role = {r[0]: r for r in self.rows}

    def test_the_table_is_still_readable(self):
        """The guard: a table whose markers moved leaves every check below reading
        an empty list, and an empty list passes each of them."""
        text = read(POLICY)
        self.assertRegex(text, r"(?m)^%s\s*$" % re.escape(OPEN_MARKER),
                         "the role table lost its schema=3 opener, on its own line")
        self.assertRegex(text, r"(?m)^%s\s*$" % re.escape(CLOSE_MARKER),
                         "the role table lost its closing marker, on its own line")
        self.assertTrue(self.rows, "the role table has no data rows")

    def test_each_new_role_carries_its_seven_cells(self):
        for role, cells in NEW_ROWS.items():
            with self.subTest(role=role):
                row = self.by_role.get(role)
                self.assertIsNotNone(row, f"the table has no `{role}` row")
                self.assertEqual(len(row), COLUMNS,
                                 f"`{role}` has {len(row)} cells, not {COLUMNS} — the "
                                 "parser is positional and refuses the whole table")
                self.assertEqual(tuple(row[1:6]), cells,
                                 f"`{role}` no longer reads "
                                 "model/effort/venue/pr/checkpoint as the ticket fixed them")
                self.assertTrue(row[6], f"`{role}` has an empty `note` cell")

    def test_the_rows_the_new_ones_join_are_still_there(self):
        """They SUM. `AFK.md`'s *The fixer cap* names `fixer`, and the cloud `review`
        row is what the local `cold-reviewer` is distinguished from."""
        for role in KEPT_ROWS:
            with self.subTest(role=role):
                self.assertIn(role, self.by_role,
                              f"the `{role}` row is gone, and the prose that reads it "
                              "by name now names nothing")
        self.assertEqual(self.by_role["review"][3], "cloud",
                         "the `review` row stopped being the cloud one, and the "
                         "distinction `cold-reviewer` is defined against is lost")

    def test_the_cold_reviewer_spends_a_slot_in_the_local_ceiling(self):
        """`local` in a cell is half the rule. Read alone it says where the role
        runs; what the orchestrator needs is which ceiling it draws on."""
        self.assertEqual(self.by_role["cold-reviewer"][3], "local")
        venue = flat(section(read(POLICY), "## Venue"))
        self.assertTrue(venue, "subagent-policy.md has no `## Venue` section")
        said = [s for s in re.split(r"(?<=\.)\s+", venue) if "cold-reviewer" in s]
        self.assertTrue(said, "*Venue* never names `cold-reviewer`, so the row says "
                              "local and nothing says which ceiling that spends")
        joined = " ".join(said)
        self.assertRegex(joined, r"local (?:subagent|Opus|ceiling)|local ceiling",
                         "the paragraph names the role without naming the local "
                         "ceiling it occupies a slot in")

    def test_tk_contract_emits_a_block_for_each_new_role(self):
        """The table is data for a generator, so the proof is the generator running:
        a cell outside its closed vocabulary refuses the whole file, silently to a
        reader and loudly here."""
        for role in NEW_ROWS:
            with self.subTest(role=role):
                r = subprocess.run([sys.executable, CONTRACT, "--role", role],
                                   capture_output=True, text=True)
                self.assertEqual(r.returncode, 0,
                                 f"tk-contract cannot emit `{role}`:\n{r.stderr}")
                self.assertIn(f"role={role}", r.stdout)


class TheDestinationsFile(unittest.TestCase):

    def setUp(self):
        self.text = read(FINDINGS)

    def test_the_file_is_there_and_carries_the_rule(self):
        self.assertTrue(self.text.strip(), "FINDINGS.md is empty")
        self.assertIn("No new queue item is born while a package runs", self.text,
                      "the file no longer states the rule its three destinations "
                      "exist to serve")

    def test_the_three_destinations_are_ordered(self):
        """Order is the content: destination 1 is the cheapest and destination 3 is
        the one that costs a lane, and a reader takes the first that holds."""
        body = section(self.text, "## The three destinations")
        self.assertTrue(body, "FINDINGS.md has no `## The three destinations` section")
        numbered = re.findall(r"^(\d)\. \*\*(.+?)\*\*", body, re.M)
        self.assertEqual([n for n, _ in numbered], ["1", "2", "3"],
                         "the destinations are not three numbered items in order")
        first, second, third = (t for _, t in numbered)
        self.assertIn("commit", first)
        self.assertIn("pull request's body", second)
        self.assertIn("Achados não tratados", second)
        self.assertIn("UNION", third,
                      "the third destination is a sweep lane over something other "
                      "than the union of the package's pull requests")
        self.assertRegex(flat(body), r"take the FIRST that holds",
                         "the three are listed and never ordered, so a reader picks "
                         "the convenient one")

    def test_a_report_line_is_refused_as_a_destination(self):
        """The verdict this file was written against: a line in a report is a
        deferral, and a deferral no count can see."""
        said = flat(self.text)
        self.assertIn("A report line is not a destination", said)
        self.assertIn("adiamento com outro nome", said,
                      "the refusal no longer carries the user's own words, and reads "
                      "as the agent's preference")

    def test_the_audit_moment_has_a_destination_that_is_not_the_queue(self):
        """The correction of 2026-09-08: the wave audit runs before the first run, so
        the three destinations above have nothing to attach to."""
        body = flat(section(self.text, "## Before the first run: the audit's own moment"))
        self.assertTrue(body, "FINDINGS.md never names the audit's own moment, and "
                              "AUDIT.md's **backlog** outcome points at nothing")
        self.assertIn("wave's", body)
        self.assertIn("ticket's own body", body)
        self.assertRegex(body, r"[Nn]either is the queue|never the queue",
                         "the audit's moment names two destinations and never rules "
                         "out the one this file exists to close")


class AfkRoutesToTheFile(unittest.TestCase):

    def setUp(self):
        self.text = read(AFK)

    def test_the_session_finding_section_is_a_pointer(self):
        body = section(self.text, "## " + OLD_SECTION)
        self.assertTrue(body.strip(), f"AFK.md has no `## {OLD_SECTION}` section")
        self.assertIn("FINDINGS.md", body,
                      "the section was left in place and points nowhere")
        self.assertNotIn(QUEUES_AN_ITEM, body,
                         "the pointer still prescribes the command the file it points "
                         "at exists to retire")
        self.assertLessEqual(len(body.split()), 90,
                             "the section is a pointer in name only: it still carries "
                             "the body FINDINGS.md owns")

    def test_the_fixer_cap_sends_a_re_review_finding_to_a_destination(self):
        body = section(self.text, "## The fixer cap")
        self.assertTrue(body.strip(), "AFK.md has no `## The fixer cap` section")
        self.assertIn("FINDINGS.md", body,
                      "the cap says what happens after its one cycle without naming "
                      "where the finding goes")
        self.assertNotIn(QUEUES_AN_ITEM, body)
        said = flat(body)
        self.assertIn("Achados não tratados", said,
                      "the cap names the file and leaves the reader to pick a "
                      "destination, when at that point the pull request exists and "
                      "the second is the one that fits")
        self.assertIn("counts the finding by the destination that took it", said,
                      "the close's verdict 2 is still counting a finding by a rung "
                      "no step writes any more")

    def test_afk_prescribes_no_new_item_of_its_own(self):
        """The other side of `test_unattended_ladder.py`'s move: that file follows the
        prescription into FINDINGS.md, and this one holds AFK.md empty of it."""
        self.assertNotIn(QUEUES_AN_ITEM, self.text,
                         "AFK.md prescribes an `add` again — the package is back to "
                         "answering a finding with a queue item")


class TheBacklogOutcomeRoutesToTheFile(unittest.TestCase):

    def setUp(self):
        outcomes = section(read(AUDIT), "## The four outcomes")
        self.assertTrue(outcomes.strip(), "AUDIT.md has no `## The four outcomes`")
        self.outcomes = outcomes
        start = outcomes.index("**backlog**")
        self.clause = flat(outcomes[start:outcomes.index("**refuted**", start)])

    def test_the_backlog_clause_names_the_destinations_file(self):
        self.assertIn("FINDINGS.md", self.clause)
        self.assertNotIn(QUEUES_AN_ITEM, self.clause,
                         "**backlog** still queues an item mid-package, which is the "
                         "rule the file it now points at installs")
        self.assertNotIn(OLD_SECTION, self.clause,
                         "**backlog** still cites AFK.md's retired section")
        self.assertIn("never the queue", self.clause)

    def test_the_regrill_recipe_is_untouched(self):
        """REGRILL is the one exit that still writes an item, and it may: it halts the
        package with no run fired, so there is no package left to carry the finding."""
        self.assertIn("```sh", self.outcomes, "the REGRILL recipe's fence is gone")
        self.assertIn(QUEUES_AN_ITEM, self.outcomes)
        self.assertIn("--deferred afk", self.outcomes,
                      "the REGRILL recipe lost the gate that parks it")


if __name__ == "__main__":
    unittest.main(verbosity=2)
