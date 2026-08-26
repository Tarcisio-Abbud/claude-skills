#!/usr/bin/env python3
"""Regression suite for `tk-collisions` (../bin/tk-collisions).

Run: python3 -m unittest discover -s tk/tests   (stdlib only, no deps)

Every test here is proved by MUTATION: the defect goes back into the source and
the test must fail. `mutations_collisions.py` beside this file replays each one,
on the runner `mutations_tk_contract.py` exposes.

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
            with open(os.path.join(self.repo, name), "w", encoding="utf-8") as f:
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


if __name__ == "__main__":
    unittest.main()
