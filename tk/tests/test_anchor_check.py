#!/usr/bin/env python3
"""The anchoring check, proved on a tree where an anchor really stopped matching.

A checker that never fails is indistinguishable from one that always prints
"fine", so the two cases that matter are staged for real: an anchor edited out
of its source (0 matches) and one duplicated into it (2 matches). Both are
staged in a COPY of the repository, never in the tree the suite runs from.
"""

import glob
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TK_DIR = os.path.dirname(HERE)

sys.path.insert(0, HERE)
import anchor_check  # noqa: E402  (the path above enables it)


def run_checker(tk_dir, *args):
    """The command as a user runs it, from the tree given."""
    return subprocess.run([sys.executable, os.path.join(tk_dir, "tests", "anchor_check.py")]
                          + list(args), capture_output=True, text=True)


def an_entry(harness_name="mutations_vista", position=0):
    """One real entry, read through the checker's own loader — never a literal
    copied into this file, which would go stale the moment the entry is edited."""
    path = os.path.join(HERE, harness_name + ".py")
    harness = anchor_check.load(path)
    entry = harness.mutations[position]
    rel = entry[4] if len(entry) > 4 else harness.default_src
    return entry[0], entry[1], rel


class TestTheTreeItRunsIn(unittest.TestCase):
    def test_every_harness_beside_this_file_is_found(self):
        """Discovery is a glob, so a harness added later is checked by existing.
        A hand-kept list would be the failure mode the check exists to remove."""
        expected = sorted(glob.glob(os.path.join(HERE, "mutations*.py")))
        self.assertEqual(anchor_check.discover(HERE), expected)
        self.assertGreaterEqual(len(expected), 11)

    def test_the_working_tree_has_every_anchor_matching_once(self):
        result = run_checker(TK_DIR)
        self.assertEqual(result.returncode, 0,
                         f"anchors are stale in this tree:\n{result.stdout}")
        self.assertIn("every anchor matches exactly once", result.stdout)

    def test_it_answers_in_seconds_and_not_in_a_mutation_run(self):
        """The whole point: the full harness answers this in minutes. Thirty
        seconds is the item's ceiling, and the measured time is under a second —
        the margin is there so a slower machine does not turn this red."""
        start = time.monotonic()
        result = run_checker(TK_DIR)
        self.assertEqual(result.returncode, 0)
        self.assertLess(time.monotonic() - start, 30)

    def test_it_counts_the_entries_it_read(self):
        """A silent green run cannot be told from one that found no entries."""
        result = run_checker(TK_DIR)
        self.assertRegex(result.stdout, r"1[1-9] harness\(es\), \d{3,} entries")


class TestABrokenAnchorIsNamed(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="anchor-check-test.")
        # the WHOLE repository, not just `tk/`: one entry anchors into
        # `../.claude-plugin/marketplace.json`, a repo-root file, and a copy that
        # stopped at `tk/` would fail for a reason the staging never staged
        root = os.path.join(self.tmp, "repo")
        shutil.copytree(os.path.dirname(TK_DIR), root,
                        ignore=shutil.ignore_patterns("__pycache__", ".git"))
        self.tree = os.path.join(root, "tk")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def edit_source(self, rel, edit):
        path = os.path.join(self.tree, rel)
        with open(path, encoding="utf-8") as fh:
            source = fh.read()
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(edit(source))

    def test_an_anchor_edited_out_of_its_source_fails_the_run(self):
        label, old, rel = an_entry()
        self.edit_source(rel, lambda s: s.replace(old, "# the code moved", 1))
        result = run_checker(self.tree)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn(label, result.stdout)
        self.assertIn("matched 0x", result.stdout)
        self.assertIn(rel, result.stdout)

    def test_an_anchor_that_matches_twice_fails_the_run(self):
        """Two matches is not a smaller problem than none: the mutation that
        gets applied is not the one the label describes."""
        label, old, rel = an_entry()
        self.edit_source(rel, lambda s: s + "\n# " + old + "\n")
        result = run_checker(self.tree)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn(label, result.stdout)
        self.assertIn("matched 2x", result.stdout)

    def test_a_source_an_entry_names_and_the_tree_lacks_is_named(self):
        label, _, rel = an_entry()
        os.remove(os.path.join(self.tree, rel))
        result = run_checker(self.tree)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn(label, result.stdout)
        self.assertIn("cannot be read", result.stdout)

    def test_the_clean_copy_still_passes(self):
        """The staging above is what fails, not the copying."""
        self.assertEqual(run_checker(self.tree).returncode, 0)


class TestTheEntryShapes(unittest.TestCase):
    """The checks that read an entry rather than a source file."""

    def harness(self, mutations, base=TK_DIR, default_src=os.path.join("bin", "tk-queue")):
        return anchor_check.Harness("probe", "<probe>", mutations, base, default_src)

    def test_a_no_op_mutation_is_reported(self):
        found = anchor_check.check(self.harness([("a no-op", "x", "x", ["T.t"])]))
        self.assertEqual(len(found), 1)
        self.assertIn("no-op", found[0])

    def test_paired_lists_of_unequal_length_are_reported(self):
        found = anchor_check.check(
            self.harness([("half a pair", ["a", "b"], ["c"], ["T.t"])]))
        self.assertEqual(len(found), 1)
        self.assertIn("same length", found[0])

    def test_an_entry_that_names_no_test_is_reported(self):
        found = anchor_check.check(self.harness([("proves nothing", "x", "y", [])]))
        self.assertTrue(any("names no test" in line for line in found))

    def test_an_entry_with_no_source_and_no_default_is_reported(self):
        found = anchor_check.check(
            self.harness([("nowhere to look", "x", "y", ["T.t"])], default_src=None))
        self.assertEqual(len(found), 1)
        self.assertIn("no default", found[0])

    def test_a_harness_without_a_mutations_list_is_reported(self):
        found = anchor_check.check(self.harness(None))
        self.assertEqual(len(found), 1)
        self.assertIn("no MUTATIONS list", found[0])


class TestTheCommandLine(unittest.TestCase):
    def test_help_says_what_a_green_run_does_not_prove(self):
        result = run_checker(TK_DIR, "--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("does not replace it", result.stdout)

    def test_an_argument_it_does_not_take_is_refused(self):
        result = run_checker(TK_DIR, "--fix")
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
