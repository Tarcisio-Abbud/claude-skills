#!/usr/bin/env python3
"""Regression suite for `tk-roster` (../bin/tk-roster) and the two site-file
keys it adds (`fleet-allow`, `fleet-deny`, parsed in ../bin/tk_site.py).

Run: python3 -m unittest discover -s tk/tests   (stdlib only, no deps)

Every test here is proved by MUTATION: the defect is put back in the source and
the test must fail. `mutations.py` in this directory replays each mutation
mechanically.

The suite drives the real script as a subprocess with HOME pointed at a
throwaway tree, so it sweeps fixtures and never the machine's own projects. The
path encoding is spelled out LITERALLY below rather than imported from the bin:
a test that computes the expected name with the same function under test would
survive any mutation of that function, agreeing with the defect.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROSTER = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "bin", "tk-roster")

HEADER = """---
name: next-steps
description: fixture
metadata:
  type: project
---

# Next steps

"""

SITE = """identity = alpha
environments = alpha, bravo, charlie-2
"""


def encode(path):
    """The queue directory name for `path` — tk-queue's rule, written out."""
    return re.sub(r"[^A-Za-z0-9-]", "-", path)


class RosterTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.home = os.path.join(self.tmp, "home")
        self.projects = os.path.join(self.home, ".claude", "projects")
        os.makedirs(self.projects)

    def queue(self, name, file=os.path.join("memory", "next-steps.md")):
        """A project directory carrying `file` — the queue, unless told otherwise."""
        path = os.path.join(self.projects, name, file)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(HEADER)
        return os.path.dirname(path)

    def project_dir(self, *parts):
        """A real directory to be found by the sweep, and the name it encodes to."""
        path = os.path.join(self.tmp, *parts)
        os.makedirs(path, exist_ok=True)
        return path, encode(path)

    def site(self, text=SITE):
        path = os.path.join(self.home, ".claude", "tk", "env")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)

    def run_roster(self, *argv):
        env = dict(os.environ, HOME=self.home)
        env.pop("USERPROFILE", None)
        return subprocess.run([sys.executable, ROSTER, *argv], env=env,
                              capture_output=True, text=True, timeout=60)

    # --- reading the report ------------------------------------------------
    def block(self, out, prefix):
        """The lines under the `## <prefix>...` heading, or [] when absent."""
        lines, keeping = [], False
        for line in out.splitlines():
            if line.startswith("## "):
                keeping = line[3:].startswith(prefix)
            elif keeping and line.strip():
                lines.append(line)
        return lines

    def names(self, out, prefix):
        return [line.split()[0] for line in self.block(out, prefix)]


# --- the sweep: what is a queue, and what is merely a directory -------------

class TestSweep(RosterTest):
    def test_a_directory_without_the_queue_file_is_not_a_project(self):
        live, live_name = self.project_dir("live")
        self.queue(live_name)
        self.queue("-finished", file=os.path.join("memory", "done-log.md"))
        os.makedirs(os.path.join(self.projects, "-bare"))
        r = self.run_roster()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.names(r.stdout, "roster"), [live_name])
        self.assertNotIn("-finished", r.stdout)
        self.assertNotIn("-bare", r.stdout)

    def test_an_empty_projects_root_is_an_empty_roster_not_a_failure(self):
        r = self.run_roster()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("no project on this machine has a queue", r.stdout)

    def test_every_queue_found_is_reported(self):
        names = []
        for part in ("one", "two", "three"):
            _, name = self.project_dir(part)
            self.queue(name)
            names.append(name)
        r = self.run_roster()
        self.assertEqual(sorted(self.names(r.stdout, "roster")), sorted(names))


# --- the path: recovered from the name, or refused ------------------------

class TestProjectPath(RosterTest):
    def test_the_path_is_the_directory_that_encodes_to_the_name(self):
        path, name = self.project_dir("deep", "project_one")
        self.queue(name)
        r = self.run_roster()
        self.assertEqual(self.block(r.stdout, "roster"), [f"{name}  {path}"])

    def test_two_directories_encoding_to_one_name_are_not_dispatchable(self):
        hyphen, name = self.project_dir("x-y")
        nested, nested_name = self.project_dir("x", "y")
        self.assertEqual(name, nested_name)      # the encoding is one-way
        self.queue(name)
        r = self.run_roster()
        self.assertEqual(self.names(r.stdout, "roster"), [])
        blind = "\n".join(self.block(r.stdout, "not dispatchable"))
        self.assertIn(hyphen, blind)
        self.assertIn(nested, blind)

    def test_a_symlink_does_not_make_a_project_ambiguous(self):
        nested, name = self.project_dir("x", "y")
        # a link spelled like the nested path: followed, it is a SECOND directory
        # encoding to the same name, and the one real answer becomes ambiguous
        os.symlink(os.path.join(self.tmp, "x"), os.path.join(self.tmp, "x-y"))
        self.queue(name)
        r = self.run_roster()
        self.assertEqual(self.block(r.stdout, "roster"), [f"{name}  {nested}"])

    def test_a_queue_whose_project_directory_is_gone_is_not_dispatchable(self):
        name = encode(os.path.join(self.tmp, "vanished"))
        memdir = self.queue(name)
        r = self.run_roster()
        self.assertEqual(self.names(r.stdout, "roster"), [])
        blind = "\n".join(self.block(r.stdout, "not dispatchable"))
        self.assertIn("the project directory is gone", blind)
        self.assertIn(memdir, blind)             # the queue is still reachable


# --- the site file: absent, rotten, and the two lists ---------------------

class TestSiteFile(RosterTest):
    def test_no_site_file_sweeps_everything_and_says_the_file_is_absent(self):
        _, name = self.project_dir("free")
        self.queue(name)
        r = self.run_roster()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.names(r.stdout, "roster"), [name])
        self.assertIn("no site file", r.stderr)

    def test_a_rotten_site_file_stops_the_sweep_instead_of_ignoring_the_lists(self):
        _, name = self.project_dir("free")
        self.queue(name)
        self.site("identity = alpha\n")          # no `environments`
        r = self.run_roster()
        self.assertEqual(r.returncode, 1)
        self.assertIn("declares no `environments`", r.stderr)
        self.assertNotIn(name, r.stdout)

    def test_an_unknown_key_is_still_ignored(self):
        _, name = self.project_dir("free")
        self.queue(name)
        self.site(SITE + f"fleet-denny = {name}\n")
        r = self.run_roster()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.names(r.stdout, "roster"), [name])


class TestAllowDeny(RosterTest):
    def setUp(self):
        super().setUp()
        self.kept, self.kept_name = self.project_dir("kept")
        self.other, self.other_name = self.project_dir("other")
        self.queue(self.kept_name)
        self.queue(self.other_name)

    def test_without_lists_every_queue_enters(self):
        self.site()
        r = self.run_roster()
        self.assertEqual(sorted(self.names(r.stdout, "roster")),
                         sorted([self.kept_name, self.other_name]))

    def test_fleet_allow_admits_only_what_it_lists(self):
        self.site(SITE + f"fleet-allow = {self.kept_name}\n")
        r = self.run_roster()
        self.assertEqual(self.names(r.stdout, "roster"), [self.kept_name])
        self.assertEqual(self.names(r.stdout, "excluded"), [self.other_name])

    def test_fleet_deny_removes_what_it_lists(self):
        self.site(SITE + f"fleet-deny = {self.other_name}\n")
        r = self.run_roster()
        self.assertEqual(self.names(r.stdout, "roster"), [self.kept_name])
        self.assertEqual(self.names(r.stdout, "excluded"), [self.other_name])

    def test_a_name_in_both_lists_is_denied(self):
        self.site(SITE + f"fleet-allow = {self.kept_name}, {self.other_name}\n"
                         f"fleet-deny = {self.other_name}\n")
        r = self.run_roster()
        self.assertEqual(self.names(r.stdout, "roster"), [self.kept_name])
        self.assertIn("fleet-deny", "\n".join(self.block(r.stdout, "excluded")))

    def test_an_entry_written_as_a_path_names_the_same_project(self):
        self.site(SITE + f"fleet-deny = {self.other}\n")
        r = self.run_roster()
        self.assertEqual(self.names(r.stdout, "roster"), [self.kept_name])
        self.assertEqual(self.names(r.stdout, "excluded"), [self.other_name])

    def test_an_entry_matching_no_queue_is_reported(self):
        self.site(SITE + f"fleet-deny = {self.other_name}, -not-a-project\n")
        r = self.run_roster()
        self.assertEqual(self.names(r.stdout, "roster"), [self.kept_name])
        self.assertEqual(self.names(r.stdout, "`fleet-deny` names no queue"),
                         ["-not-a-project"])

    def test_a_matching_entry_is_not_reported_as_unmatched(self):
        self.site(SITE + f"fleet-deny = {self.other_name}\n")
        r = self.run_roster()
        self.assertEqual(self.block(r.stdout, "`fleet-deny` names no queue"), [])


# --- the site file refuses a list it cannot act on ------------------------

class TestListValidation(RosterTest):
    def refusal(self, line):
        _, name = self.project_dir("free")
        self.queue(name)
        self.site(SITE + line)
        r = self.run_roster()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertNotIn(name, r.stdout)
        return r.stderr

    def test_an_empty_list_is_refused_not_read_as_an_absent_one(self):
        self.assertIn("is empty", self.refusal("fleet-allow =\n"))

    def test_a_relative_path_names_no_project(self):
        self.assertIn("neither a project directory", self.refusal("fleet-deny = ../x\n"))

    def test_a_name_outside_the_encoding_alphabet_is_refused(self):
        self.assertIn("neither a project directory",
                      self.refusal("fleet-allow = ~/projects/x\n"))


if __name__ == "__main__":
    unittest.main()
