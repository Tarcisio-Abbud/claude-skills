#!/usr/bin/env python3
"""Regression suite for `tk-collisions` (../bin/tk-collisions).

Run: python3 -m unittest discover -s tk/tests   (stdlib only, no deps)

Every test here is proved by MUTATION: the defect goes back into the source and
the test must fail. `mutations_collisions.py` beside this file replays each one,
on the runner `mutations_tk_contract.py` exposes.

TWO HALVES, and the second is why `--against` exists: the pairwise tests
below prove a TEXTUAL conflict is found, and `TestUnion` proves the semantic
one is — a test one branch adds grading a file another branch edits, with
every merge clean.

The suite drives the real script as a subprocess and reads its EXIT CODE and its
printed answer — never an internal. It gets a real git repository built in a
throwaway directory, because the whole point of the script is that it PERFORMS
the merge instead of asking about it, and a faked git would prove only that the
fake was consulted.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      os.pardir, "bin", "tk-collisions")


class CollisionTest(unittest.TestCase):
    def setUp(self):
        self.tmp = os.path.realpath(tempfile.mkdtemp(prefix="tk-collisions."))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.repo = os.path.join(self.tmp, "repo")
        os.makedirs(self.repo)
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "suite@example.invalid")
        self.git("config", "user.name", "suite")
        self.commit("base", {"f.md": "one\ntwo\nthree\n", "other.md": "x\n"})

    def git(self, *argv):
        return subprocess.run(["git", "-C", self.repo, *argv], check=True,
                              capture_output=True, text=True)

    def commit(self, message, files):
        for name, text in files.items():
            path = os.path.join(self.repo, name)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
        self.git("add", "-A")
        self.git("commit", "-qm", message)

    def branch(self, name, files):
        self.git("checkout", "-q", "main")
        self.git("checkout", "-qb", name)
        self.commit(name, files)
        self.git("checkout", "-q", "main")

    def run_script(self, *argv):
        return subprocess.run([sys.executable, SCRIPT, *argv],
                              capture_output=True, text=True, timeout=120)

    def collisions(self, *refs, extra=()):
        return self.run_script("--repo", self.repo, *refs, *extra)


class TestCollisions(CollisionTest):
    def test_two_branches_each_clean_against_main_can_still_collide(self):
        """The acceptance criterion, and the reason this script exists."""
        self.branch("a", {"f.md": "one\nA CHANGED IT\nthree\n"})
        self.branch("b", {"f.md": "one\nB CHANGED IT\nthree\n"})

        # each one alone is what the forge would call MERGEABLE/CLEAN
        for ref in ("a", "b"):
            alone = self.collisions("main", ref)
            self.assertEqual(alone.returncode, 0, alone.stdout)
            self.assertIn("clean", alone.stdout)

        together = self.collisions("a", "b")
        self.assertEqual(together.returncode, 1, together.stdout)
        self.assertIn("COLLIDES  a × b", together.stdout)
        self.assertIn("f.md", together.stdout)

    def test_two_branches_editing_one_file_apart_are_clean(self):
        """The merge is PERFORMED, so two edits far apart in one file are
        clean. Nothing else in this suite tells a real three-way merge from a
        `did both branches touch this file` heuristic, which would call this
        pair colliding and pass every other test here."""
        self.commit("longer", {"f.md": "".join(f"line {n}\n" for n in range(1, 12))})
        self.branch("a", {"f.md": "A CHANGED IT\n"
                          + "".join(f"line {n}\n" for n in range(2, 12))})
        self.branch("b", {"f.md": "".join(f"line {n}\n" for n in range(1, 11))
                          + "B CHANGED IT\n"})
        r = self.collisions("a", "b")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("clean     a × b", r.stdout)

    def test_branches_that_touch_different_files_are_reported_clean(self):
        self.branch("a", {"f.md": "one\nA CHANGED IT\nthree\n"})
        self.branch("c", {"other.md": "y\n"})
        r = self.collisions("a", "c")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("clean     a × c", r.stdout)
        self.assertNotIn("COLLIDES", r.stdout)

    def test_every_pair_is_measured_not_only_the_neighbours(self):
        self.branch("a", {"f.md": "one\nA\nthree\n"})
        self.branch("c", {"other.md": "y\n"})
        self.branch("b", {"f.md": "one\nB\nthree\n"})
        r = self.collisions("a", "c", "b")
        self.assertIn("3 pair(s)", r.stdout)
        self.assertIn("1 colliding", r.stdout)
        self.assertIn("COLLIDES  a × b", r.stdout)

    def test_one_branch_is_answered_not_refused(self):
        self.branch("a", {"f.md": "one\nA\nthree\n"})
        r = self.collisions("a")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("no pair to measure", r.stdout)

    def test_json_names_the_colliding_pair_and_its_paths(self):
        self.branch("a", {"f.md": "one\nA\nthree\n"})
        self.branch("b", {"f.md": "one\nB\nthree\n"})
        r = self.collisions("a", "b", extra=("--json",))
        data = json.loads(r.stdout)
        self.assertEqual(data["counts"], {"measured": 1, "colliding": 1})
        self.assertEqual(data["pairs"][0]["paths"], ["f.md"])


class TestCollisionFailures(CollisionTest):
    def test_a_ref_that_names_no_commit_stops_the_run(self):
        self.branch("a", {"f.md": "one\nA\nthree\n"})
        r = self.collisions("a", "feat/never-fetched")
        self.assertEqual(r.returncode, 2, r.stdout)
        self.assertIn("names no commit", r.stderr)
        self.assertEqual(r.stdout, "")

    def test_a_directory_that_is_not_a_repository_stops_the_run(self):
        r = self.run_script("--repo", self.tmp, "main")
        self.assertEqual(r.returncode, 2, r.stdout)
        self.assertIn("not a git repository", r.stderr)

    def test_a_merge_that_could_not_run_is_never_reported_as_clean(self):
        """`merge-tree` exits 1 for a conflict AND for a merge it refused —
        an unknown flag on an older git. Reading the second as a clean pair is
        the silent lie this script exists to stop telling."""
        self.branch("a", {"f.md": "one\nA\nthree\n"})
        self.branch("b", {"f.md": "one\nB\nthree\n"})
        real = shutil.which("git")
        shim_dir = os.path.join(self.tmp, "shim")
        os.makedirs(shim_dir)
        shim = os.path.join(shim_dir, "git")
        with open(shim, "w", encoding="utf-8") as f:
            f.write(f'#!/bin/sh\nfor a in "$@"; do\n'
                    f'  [ "$a" = "merge-tree" ] && exit 1\ndone\n'
                    f'exec {real} "$@"\n')
        os.chmod(shim, 0o755)
        env = dict(os.environ, PATH=shim_dir + os.pathsep + os.environ["PATH"])
        r = subprocess.run([sys.executable, SCRIPT, "--repo", self.repo, "a", "b"],
                           env=env, capture_output=True, text=True, timeout=120)
        self.assertEqual(r.returncode, 2, r.stdout)
        self.assertIn("without naming a conflict", r.stderr)
        self.assertNotIn("clean", r.stdout)


# --- the union of two branches, and the suite that grades it ---------------
#
# The pairwise path above answers "do these two branches conflict TEXTUALLY".
# The class below is the collision it cannot see: a test one branch adds
# grades a file the other branch edits, every merge is clean, and the second
# merge to land leaves the base red. Measured on claude-skills #66 × #68
# (2026-09-01), where `tk-collisions` reported 0 colliding pairs.

LOCK_TEST = '''\
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestLock(unittest.TestCase):
    def test_doc_is_at_most_three_lines(self):
        with open(os.path.join(ROOT, "doc.md"), encoding="utf-8") as f:
            self.assertLessEqual(len(f.read().splitlines()), 3)
'''

SUITE = "python3 -m unittest discover tests"


class UnionTest(CollisionTest):
    """A repository where `main` carries the graded file and a `tests/` dir.

    `tests/` is on main, and importable, so that ONE suite command runs on
    every branch of the fixture — `unittest discover` on a directory that
    does not exist exits 1, which would make "each branch alone is green"
    untestable with the command the gate really uses."""

    def setUp(self):
        super().setUp()
        self.commit("doc", {"doc.md": "one\ntwo\nthree\n",
                            "tests/__init__.py": "",
                            ".gitignore": "__pycache__/\n"})

    def union(self, *refs, against="a", base="main", suite=SUITE, extra=()):
        return self.collisions(*refs, extra=("--against", against,
                                             "--base", base,
                                             "--suite", suite, *extra))

    def suite_on(self, ref):
        """The suite run in a checkout of ONE branch — "each alone green"."""
        self.git("checkout", "-q", ref)
        try:
            return subprocess.run(SUITE, shell=True, cwd=self.repo,
                                  capture_output=True, text=True, timeout=120)
        finally:
            self.git("checkout", "-q", "main")

    def worktrees(self):
        return self.git("worktree", "list").stdout.strip().splitlines()


class TestUnion(UnionTest):
    def test_a_test_one_branch_adds_grades_a_file_the_other_branch_edits(self):
        """The acceptance criterion of T295, and the reason `--against` exists."""
        self.branch("a", {"tests/test_lock.py": LOCK_TEST})
        self.branch("b", {"doc.md": "one\ntwo\nthree\nfour\nfive\n"})

        for ref in ("a", "b"):
            alone = self.suite_on(ref)
            self.assertEqual(alone.returncode, 0, alone.stderr)

        # what the pairwise path answers today: no textual conflict at all
        pairwise = self.collisions("a", "b")
        self.assertEqual(pairwise.returncode, 0, pairwise.stdout)
        self.assertIn("clean     a × b", pairwise.stdout)

        union = self.union("b")
        self.assertEqual(union.returncode, 1, union.stdout + union.stderr)
        self.assertIn("a × b", union.stdout)
        self.assertIn("test_doc_is_at_most_three_lines", union.stdout)

    def test_a_union_whose_suite_passes_is_reported_green(self):
        self.branch("a", {"tests/test_lock.py": LOCK_TEST})
        self.branch("c", {"other.md": "y\n"})
        r = self.union("c")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("green     a × c", r.stdout)

    def test_the_union_is_taken_over_the_base_and_not_between_the_pair(self):
        """`merge-tree a b` starts from `merge-base(a, b)` — the base as it
        was when the two branched. Once the base has moved, that tree is
        missing whatever landed meanwhile, INCLUDING the test that grades the
        file. Here the lock test lands on main after both branches are cut,
        so only `merge(merge(main, a), b)` can see the collision."""
        self.branch("a", {"note.md": "a\n"})
        self.branch("b", {"doc.md": "one\ntwo\nthree\nfour\nfive\n"})
        self.commit("lock", {"tests/test_lock.py": LOCK_TEST})

        pairwise = self.collisions("a", "b")
        self.assertEqual(pairwise.returncode, 0, pairwise.stdout)

        union = self.union("b")
        self.assertEqual(union.returncode, 1, union.stdout + union.stderr)
        self.assertIn("test_doc_is_at_most_three_lines", union.stdout)

    def test_a_textual_conflict_in_the_union_is_reported_without_a_suite_run(self):
        """A conflicted merge leaves no tree to run anything in, so the
        finding is the conflict the pairwise path already names."""
        self.branch("a", {"doc.md": "one\nA CHANGED IT\nthree\n"})
        self.branch("b", {"doc.md": "one\nB CHANGED IT\nthree\n"})
        marker = os.path.join(self.tmp, "the-suite-ran")

        r = self.union("b", suite=f"touch {marker}")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("COLLIDES  a × b", r.stdout)
        self.assertIn("doc.md", r.stdout)
        self.assertFalse(os.path.exists(marker),
                         "the suite ran over a union that does not exist")

    def test_the_pivot_itself_is_never_unioned_with_itself(self):
        self.branch("a", {"tests/test_lock.py": LOCK_TEST})
        r = self.union("a")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("no union to measure", r.stdout)

    def test_json_carries_the_suite_result_of_every_union(self):
        self.branch("a", {"tests/test_lock.py": LOCK_TEST})
        self.branch("b", {"doc.md": "one\ntwo\nthree\nfour\nfive\n"})
        r = self.union("b", extra=("--json",))
        data = json.loads(r.stdout)
        self.assertEqual(data["counts"], {"measured": 1, "colliding": 1})
        pair = data["pairs"][0]
        self.assertEqual([pair["a"], pair["b"]], ["a", "b"])
        self.assertNotEqual(pair["suite"]["returncode"], 0)
        self.assertIn("test_doc_is_at_most_three_lines", pair["suite"]["tail"])

    def test_the_temporary_worktree_is_removed_even_when_the_union_is_red(self):
        """The union is MATERIALISED — the one promise the pairwise path does
        not make. A worktree left behind would be registered in the real repo
        the gate runs in."""
        before = self.worktrees()
        self.branch("a", {"tests/test_lock.py": LOCK_TEST})
        self.branch("b", {"doc.md": "one\ntwo\nthree\nfour\nfive\n"})
        r = self.union("b")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertEqual(self.worktrees(), before)


class TestUnionFailures(UnionTest):
    def test_against_without_a_suite_stops_the_run(self):
        self.branch("a", {"tests/test_lock.py": LOCK_TEST})
        r = self.collisions("b", extra=("--against", "a", "--base", "main"))
        self.assertEqual(r.returncode, 2, r.stdout)
        self.assertIn("--suite", r.stderr)

    def test_against_without_a_base_stops_the_run(self):
        self.branch("a", {"tests/test_lock.py": LOCK_TEST})
        r = self.collisions("a", extra=("--against", "a", "--suite", SUITE))
        self.assertEqual(r.returncode, 2, r.stdout)
        self.assertIn("--base", r.stderr)

    def test_a_suite_without_a_pivot_stops_the_run(self):
        """Silently ignoring it would report the pairwise answer under the
        name of the union the caller asked for."""
        self.branch("a", {"tests/test_lock.py": LOCK_TEST})
        r = self.collisions("main", "a", extra=("--suite", SUITE))
        self.assertEqual(r.returncode, 2, r.stdout)
        self.assertIn("--against", r.stderr)

    def test_a_pivot_that_names_no_commit_stops_the_run(self):
        self.branch("a", {"tests/test_lock.py": LOCK_TEST})
        r = self.collisions("a", extra=("--against", "feat/never-fetched",
                                        "--base", "main", "--suite", SUITE))
        self.assertEqual(r.returncode, 2, r.stdout)
        self.assertIn("names no commit", r.stderr)

    def test_a_suite_that_could_not_be_run_is_never_reported_as_green(self):
        """A command the shell cannot find exits 127, and reading that as a
        red union would be a finding nobody can act on — while reading it as
        green is the silent lie this script exists to stop telling."""
        self.branch("a", {"tests/test_lock.py": LOCK_TEST})
        self.branch("c", {"other.md": "y\n"})
        r = self.union("c", suite="tk-no-such-command-exists")
        self.assertEqual(r.returncode, 2, r.stdout)
        self.assertIn("did not run", r.stderr)
        self.assertNotIn("green", r.stdout)


if __name__ == "__main__":
    unittest.main()
