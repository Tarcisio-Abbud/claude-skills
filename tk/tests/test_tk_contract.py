#!/usr/bin/env python3
"""Regression suite for `tk-contract` (../bin/tk-contract).

Run: python3 -m unittest discover -s tk/tests   (stdlib only, no deps)

Every test here is proved by MUTATION: the defect is put back in the source and
the test must fail. A test that still passes with the defect restored guards
nothing. `mutations_tk_contract.py` in this directory replays each mutation
mechanically.

The suite drives the real script as a subprocess against throwaway fixtures. It
writes its own role table rather than asserting against the repo's, so that
adding a role to `reference/subagent-policy.md` — an ordinary edit — never turns
red here; the one test that does read the real file asserts only that the
default path finds it.

The roster in the fixtures is INVENTED (`alpha`, `bravo`, `charlie-2`). This
repo is public and the site file is the one place a deployment's proper names
live, which is exactly why they are not in it.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest

BIN = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "bin", "tk-contract")
POLICY = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir,
                      "reference", "subagent-policy.md")

SITE = """identity = alpha
environments = alpha, bravo, charlie-2
max-local-subagents = 6
max-cloud-subagents = 4
"""

TABLE = """Prose above the table, which the parser must not read — including a
row left behind by an earlier draft:

| ghost | parent | high | cloud | Outside the markers, and therefore not a role. |

<!-- tk:roles schema=1 -->
| role | model | effort | venue | note |
|---|---|---|---|---|
| implementer | parent | session | local | Downgradable to sonnet on a mechanical ticket. |
| explore | haiku | session | local | — |
| research | sonnet | session | cloud | Rises to parent when the question turns on judgement. |
<!-- /tk:roles -->

Prose below it, likewise. | Even a stray pipe. |
"""


class ContractTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="tk-contract-test.")
        # HOME is redirected for EVERY test, not only the ones that write a site
        # file: `~/.claude/tk/env` is a real file on a real machine, and a suite
        # that reads it answers differently depending on whose machine runs it.
        # Hermetic by default; a test that wants a roster calls self.site()
        self.home = os.path.join(self.dir, "home")
        os.makedirs(self.home)
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        self.site(SITE)
        self.table(TABLE)

    def site(self, text):
        d = os.path.join(self.home, ".claude", "tk")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "env"), "w", encoding="utf-8") as f:
            f.write(text)

    def unsite(self):
        os.remove(os.path.join(self.home, ".claude", "tk", "env"))

    def table(self, text):
        self.policy = os.path.join(self.dir, "policy.md")
        with open(self.policy, "w", encoding="utf-8") as f:
            f.write(text)

    def run_tk(self, *argv, cwd=None, policy=True, timeout=None):
        env = dict(os.environ, HOME=self.home)
        args = list(argv) + (["--policy", self.policy] if policy else [])
        return subprocess.run([sys.executable, BIN, *args], capture_output=True,
                              text=True, cwd=cwd or self.dir, env=env, timeout=timeout)

    def block(self, *argv, **kw):
        r = self.run_tk(*argv, **kw)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout


# --- determinism -----------------------------------------------------------

class TestDeterminism(ContractTest):
    """"Same input, same block, byte for byte" is the acceptance criterion the
    whole design answers to: a block that drifts between two runs cannot be
    diffed, and a reviewer cannot tell a real change from noise."""

    def test_same_input_gives_the_same_bytes(self):
        first = self.block("--role", "implementer", "--fleet", "3")
        second = self.block("--role", "implementer", "--fleet", "3")
        self.assertEqual(first, second)

    def test_the_cwd_does_not_leak_into_the_block(self):
        here = self.block("--role", "explore")
        elsewhere = self.block("--role", "explore", cwd=os.path.dirname(self.dir))
        self.assertEqual(here, elsewhere)


# --- the fleet divisor -----------------------------------------------------

class TestFleetDivisor(ContractTest):
    """The ceiling is per MACHINE and the runs sharing it are not. Without a
    divisor each of three orchestrators reads the whole ceiling and the machine
    holds three times what it can."""

    def test_the_fleet_divides_the_local_ceiling(self):
        out = self.block("--role", "implementer", "--fleet", "3")
        self.assertIn("the ceiling is 6 and the fleet is 3, so this run's share is at "
                      "most 2 at a time", out)

    def test_without_a_fleet_the_whole_ceiling_is_this_run_s(self):
        out = self.block("--role", "implementer")
        self.assertIn("Local subagents: at most 6 at a time", out)
        self.assertIn("whole ceiling", out)

    def test_a_fleet_wider_than_the_ceiling_dispatches_none(self):
        self.site(SITE.replace("max-local-subagents = 6", "max-local-subagents = 2"))
        out = self.block("--role", "implementer", "--fleet", "5")
        self.assertIn("Dispatch NO local subagents", out)
        # rounding an empty share up to 1 is the ceiling not existing: five
        # members of the fleet each holding "just one" is five at once
        self.assertNotIn("share is at most", out)

    def test_the_fleet_does_not_divide_the_cloud_ceiling(self):
        out = self.block("--role", "research", "--fleet", "4")
        self.assertIn("Cloud subagents: at most 4 at a time", out)

    def test_a_fleet_that_is_not_a_positive_whole_number_is_refused(self):
        for junk in ("x", "0", "-1", "2.5", "", "３"):
            with self.subTest(junk=junk):
                r = self.run_tk("--role", "implementer", "--fleet", junk)
                self.assertEqual(r.returncode, 2, f"{junk!r} was accepted")
                self.assertIn("invalid fleet:", r.stderr)


# --- the ceilings come from the site file, or are stated as absent ---------

class TestCeilings(ContractTest):
    def test_an_absent_ceiling_is_stated_absent_never_invented(self):
        self.site("identity = alpha\nenvironments = alpha, bravo\n")
        out = self.block("--role", "implementer", "--fleet", "3")
        self.assertIn("declares no `max-local-subagents`", out)
        self.assertIn("declares no `max-cloud-subagents`", out)
        self.assertIn("Do not invent one", out)
        # the real test: no number anywhere in the ceilings section. A default
        # baked into the bin is the fork the criterion forbids
        ceilings = out.split("### Ceilings")[1].split("###")[0]
        self.assertNotRegex(ceilings, r"at most \d")

    def test_the_ceilings_are_read_from_the_file_not_from_the_bin(self):
        self.site(SITE.replace("= 6", "= 9").replace("= 4", "= 7"))
        out = self.block("--role", "implementer")
        self.assertIn("Local subagents: at most 9 at a time", out)
        self.assertIn("Cloud subagents: at most 7 at a time", out)

    def test_no_site_file_asks_for_one_and_shows_the_format(self):
        self.unsite()
        r = self.run_tk("--role", "implementer")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("does not exist", r.stderr)
        self.assertIn("identity = ", r.stderr)

    def test_a_defective_site_file_names_the_defect_instead(self):
        self.site("identity = alpha\nidentity = bravo\nenvironments = alpha, bravo\n")
        r = self.run_tk("--role", "implementer")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("duplicate key", r.stderr)
        # "create the file like this" about a file that plainly exists sends the
        # reader looking for something that is already there
        self.assertNotIn("does not exist", r.stderr)

    def test_the_identity_in_the_block_comes_from_the_file(self):
        self.site(SITE.replace("identity = alpha", "identity = charlie-2"))
        self.assertIn("dispatched from `charlie-2`", self.block("--role", "implementer"))


# --- the role table is the single source ----------------------------------

class TestRoleTable(ContractTest):
    """The criterion the bin is measured against: not one cell of the table
    copied into it — "just the implementer default" included."""

    def test_the_row_is_read_from_the_table(self):
        self.table(TABLE.replace("| implementer | parent | session | local |",
                                 "| implementer | haiku | high | cloud |"))
        out = self.block("--role", "implementer")
        self.assertIn("| implementer | haiku | high | cloud |", out)
        self.assertNotIn("| implementer | parent | session | local |", out)

    def test_the_note_is_emitted_verbatim(self):
        note = "Rises to `parent` — never below it, and log the rise."
        self.table(TABLE.replace("| — |", f"| {note} |"))
        self.assertIn(f"Note: {note}", self.block("--role", "explore"))

    def test_an_unknown_role_is_refused_with_the_roles_that_exist(self):
        r = self.run_tk("--role", "implementor")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("declares no role 'implementor'", r.stderr)
        self.assertIn("implementer, explore, research", r.stderr)
        self.assertIn("NO default", r.stderr)

    def test_a_schema_it_cannot_read_fails_loud(self):
        self.table(TABLE.replace("schema=1", "schema=2"))
        r = self.run_tk("--role", "implementer")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("schema=2", r.stderr)
        self.assertNotIn("| implementer |", r.stdout)

    def test_a_value_outside_the_vocabulary_is_a_defect_not_a_default(self):
        good = "| implementer | parent | session | local |"
        for bad_row, bad in ((good.replace("parent", "gpt"), "gpt"),
                             (good.replace("session", "medium"), "medium"),
                             (good.replace("local", "remote"), "remote")):
            with self.subTest(bad=bad):
                self.table(TABLE.replace(good, bad_row))
                r = self.run_tk("--role", "implementer")
                self.assertEqual(r.returncode, 1, f"{bad!r} was accepted")
                self.assertIn(repr(bad), r.stderr)
                self.assertIn("closed vocabulary", r.stderr)
                self.assertEqual(r.stdout, "")

    def test_a_table_that_never_closes_is_refused(self):
        self.table(TABLE.replace("<!-- /tk:roles -->", ""))
        r = self.run_tk("--role", "implementer")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("never closes", r.stderr)

    def test_no_table_at_all_is_refused(self):
        self.table("Just prose, no markers.\n")
        r = self.run_tk("--role", "implementer")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("no role table", r.stderr)

    def test_a_misspelt_marker_says_so_instead_of_just_not_finding_it(self):
        # "no role table" about a file whose table is right there, one character
        # off, sends the reader looking for the wrong thing
        self.table(TABLE.replace("<!-- tk:roles schema=1 -->", "<!-- tk:roles -->"))
        r = self.run_tk("--role", "implementer")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("probably misspelt", r.stderr)

    def test_a_table_with_no_role_in_it_is_refused(self):
        self.table("<!-- tk:roles schema=1 -->\n"
                   "| role | model | effort | venue | note |\n"
                   "|---|---|---|---|---|\n"
                   "<!-- /tk:roles -->\n")
        r = self.run_tk("--role", "implementer")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("at least three", r.stderr)

    def test_a_table_that_is_not_there_is_refused_not_defaulted(self):
        r = self.run_tk("--role", "implementer", "--policy",
                        os.path.join(self.dir, "nowhere.md"), policy=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("does not exist", r.stderr)
        self.assertNotIn("not a plain file", r.stderr)

    @unittest.skipUnless(os.path.isfile("/proc/self/mem"), "no /proc on this platform")
    def test_a_table_that_cannot_be_read_is_refused_not_defaulted(self):
        # a plain file that exists and still fails on read. It is exotic on
        # purpose: after the two guards above, only the read itself can fail,
        # and the branch that catches it needs an input a test can produce
        r = self.run_tk("--role", "implementer", "--policy", "/proc/self/mem", policy=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("cannot be read", r.stderr)
        self.assertIn("no copy of those values here", r.stderr)

    def test_a_table_that_is_not_a_plain_file_is_refused(self):
        os.remove(self.policy)
        os.makedirs(self.policy)
        r = self.run_tk("--role", "implementer")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("not a plain file", r.stderr)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "no FIFOs on this platform")
    def test_a_table_that_is_a_pipe_does_not_hang(self):
        # the reason the guard above is an isfile() check and not an except:
        # open() on a FIFO with no writer BLOCKS. A run that hangs with no
        # output is worse than any traceback, and a timeout is the only way a
        # test can tell the difference
        os.remove(self.policy)
        os.mkfifo(self.policy)
        r = self.run_tk("--role", "implementer", timeout=20)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("not a plain file", r.stderr)

    def test_a_byte_order_mark_does_not_hide_the_table(self):
        # an editor that writes one glues it onto the opening marker, and the
        # table becomes unfindable while sitting in plain view
        self.table("\ufeff" + TABLE.replace("<!-- tk:roles", "\ufeff<!-- tk:roles"))
        self.assertIn("| implementer |", self.block("--role", "implementer"))

    def test_a_table_that_is_not_utf8_is_refused(self):
        with open(self.policy, "wb") as f:
            f.write(TABLE.encode("utf-8").replace(b"Prose", b"Pr\xffse"))
        r = self.run_tk("--role", "implementer")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("not valid UTF-8", r.stderr)

    def test_a_reordered_header_is_refused(self):
        self.table(TABLE.replace("| role | model | effort | venue | note |",
                                 "| role | effort | model | venue | note |"))
        r = self.run_tk("--role", "implementer")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("BY POSITION", r.stderr)

    def test_a_missing_alignment_row_is_refused_not_skipped(self):
        # the row is skipped BY POSITION, so without it the FIRST role is the
        # one that disappears — silently, and only for whoever asked for it
        self.table(TABLE.replace("|---|---|---|---|---|\n", ""))
        r = self.run_tk("--role", "implementer")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("alignment row", r.stderr)

    def test_a_row_short_of_a_cell_is_refused(self):
        self.table(TABLE.replace("| explore | haiku | session | local | — |",
                                 "| explore | haiku | local | — |"))
        r = self.run_tk("--role", "implementer")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("cells, not 5", r.stderr)

    def test_a_duplicate_role_is_refused(self):
        self.table(TABLE.replace("| research | sonnet | session | cloud |",
                                 "| explore | sonnet | session | cloud |"))
        r = self.run_tk("--role", "explore")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("duplicate role 'explore'", r.stderr)

    def test_an_empty_note_is_refused(self):
        self.table(TABLE.replace("| explore | haiku | session | local | — |",
                                 "| explore | haiku | session | local |  |"))
        r = self.run_tk("--role", "explore")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("empty `note`", r.stderr)

    def test_a_row_outside_the_markers_is_not_a_role(self):
        # the markers are the table's boundary, not decoration: a draft row in
        # the prose above is exactly the row nobody remembers deleting
        r = self.run_tk("--role", "ghost")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("declares no role 'ghost'", r.stderr)
        self.assertNotIn("ghost", r.stderr.split("It carries:")[1])

    def test_an_empty_role_cell_is_refused(self):
        self.table(TABLE.replace("| explore | haiku | session | local | — |",
                                 "|  | haiku | session | local | — |"))
        r = self.run_tk("--role", "explore")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("empty `role` cell", r.stderr)

    def test_the_default_table_is_the_one_beside_the_bin(self):
        r = self.run_tk("--role", "implementer", policy=False)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("| implementer |", r.stdout)
        self.assertIn(os.path.basename(POLICY), r.stdout)


# --- what the block has to say --------------------------------------------

class TestBlockContent(ContractTest):
    """The four things the block exists to carry. Each was a rule that lived in
    prose in a handoff prompt, was read, and did not hold."""

    def test_it_demands_the_venue_signature_and_says_who_reads_it(self):
        out = self.block("--role", "research")
        self.assertIn("venue signature", out)
        self.assertIn("degrading SILENTLY to local", out)
        self.assertIn("counts against the LOCAL ceiling", out)

    def test_it_says_an_empty_return_is_a_failure(self):
        out = self.block("--role", "research")
        self.assertIn("EMPTY return is a failure", out)

    def test_it_never_calls_the_return_a_summary(self):
        # the word is taken: "verify by artifact, not by summary" is what the
        # package flow says about an agent's self-report, and a block that asks
        # for a "summary" asks for the thing that document says not to believe
        self.assertNotIn("summary", self.block("--role", "implementer").lower())

    def test_it_carries_the_two_measured_reading_rules(self):
        out = self.block("--role", "implementer")
        self.assertIn("~85k", out)
        self.assertIn("~100k", out)
        self.assertIn("372k", out)
        self.assertIn("~500 lines", out)
        # the counterweight: without it the rule reads as "do not open files"
        self.assertIn("Neither rule touches the file you are actually EDITING", out)

    def test_it_asks_for_the_deviation_log_in_the_policy_s_format(self):
        out = self.block("--role", "explore")
        self.assertIn("explore: haiku→<what actually ran> — reason", out)
        self.assertIn("deviation log", out.lower())

    def test_the_block_is_delimited_so_it_can_be_replaced(self):
        out = self.block("--role", "explore")
        self.assertTrue(out.startswith("<!-- tk:contract schema=1 role=explore -->"))
        self.assertTrue(out.rstrip("\n").endswith("<!-- /tk:contract -->"))


if __name__ == "__main__":
    unittest.main()
