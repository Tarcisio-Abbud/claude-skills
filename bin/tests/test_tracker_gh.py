"""Suite for `bin/tracker-gh`.

Every test is proved by `mutations_tracker_gh.py`. `gh` is replaced on PATH by a stub that
records its argv and environment, so the suite exercises the wrapper's own decisions and never
touches the network.

Run: python3 -m unittest discover -s bin/tests
"""

import os
import shutil
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
WRAPPER = os.path.abspath(os.path.join(HERE, os.pardir, "tracker-gh"))

SLUG = "Fictional-Owner/private-tracker"
GHDIR = "/somewhere/private/.gh-config"

STUB = "\n".join([
    "#!/bin/sh",
    "# Records what the wrapper handed to gh, then succeeds. Never touches the network.",
    "{",
    '  printf "%s\\n" "GH_CONFIG_DIR=$GH_CONFIG_DIR"',
    '  for a in "$@"; do printf "%s\\n" "ARG=$a"; done',
    '} > "$STUB_RECORD"',
    "exit 0",
    "",
])


class Case:
    def __init__(self, tracker=SLUG, gh_dir=GHDIR):
        self.dir = tempfile.mkdtemp(prefix="tracker-gh-")
        self.bin = os.path.join(self.dir, "stub-bin")
        os.makedirs(self.bin)
        stub = os.path.join(self.bin, "gh")
        with open(stub, "w") as fh:
            fh.write(STUB)
        os.chmod(stub, 0o755)
        self.record = os.path.join(self.dir, "record.txt")
        subprocess.run(["git", "-C", self.dir, "init", "-q", "."], check=True)
        if tracker is not None:
            subprocess.run(["git", "-C", self.dir, "config", "tk.tracker", tracker], check=True)
        if gh_dir is not None:
            subprocess.run(["git", "-C", self.dir, "config", "tk.ghConfigDir", gh_dir], check=True)

    def run(self, *args):
        env = dict(os.environ)
        env["PATH"] = self.bin + os.pathsep + env["PATH"]
        env["STUB_RECORD"] = self.record
        env.pop("GH_CONFIG_DIR", None)
        return subprocess.run(
            [WRAPPER, *args], cwd=self.dir, capture_output=True, text=True, env=env
        )

    def gh_was_called(self):
        return os.path.exists(self.record)

    def call(self):
        argv = []
        gh_config_dir = None
        with open(self.record) as fh:
            for line in fh.read().splitlines():
                if line.startswith("ARG="):
                    argv.append(line[4:])
                elif line.startswith("GH_CONFIG_DIR="):
                    gh_config_dir = line[len("GH_CONFIG_DIR="):]
        return {"argv": argv, "gh_config_dir": gh_config_dir}

    def cleanup(self):
        shutil.rmtree(self.dir, ignore_errors=True)


class TrackerGhTest(unittest.TestCase):
    REFUSED = 78

    def case(self, **kwargs):
        c = Case(**kwargs)
        self.addCleanup(c.cleanup)
        return c

    def test_a_configured_clone_reaches_gh(self):
        c = self.case()
        result = c.run("issue", "list", "-R", "{tracker}")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(c.gh_was_called())

    def test_the_placeholder_is_replaced_by_the_configured_slug(self):
        c = self.case()
        c.run("issue", "list", "-R", "{tracker}")
        self.assertEqual(c.call()["argv"], ["issue", "list", "-R", SLUG])

    def test_every_argument_is_substituted_not_only_the_first(self):
        c = self.case()
        c.run("api", "repos/{tracker}/issues", "-f", "note=for {tracker}")
        self.assertEqual(
            c.call()["argv"],
            ["api", "repos/%s/issues" % SLUG, "-f", "note=for %s" % SLUG],
        )

    def test_the_gh_identity_is_exported_for_the_call(self):
        """An empty GH_CONFIG_DIR does not fail; it authenticates as whoever the environment
        happens to be."""
        c = self.case()
        c.run("issue", "list", "-R", "{tracker}")
        self.assertEqual(c.call()["gh_config_dir"], GHDIR)

    # --- the refusals, none of which may reach gh ----------------------------------

    def test_an_unconfigured_tracker_refuses_before_gh_runs(self):
        c = self.case(tracker=None)
        result = c.run("issue", "list", "-R", "{tracker}")
        self.assertEqual(result.returncode, self.REFUSED, result.stderr)
        self.assertIn("tk.tracker", result.stderr)
        self.assertFalse(c.gh_was_called(), "gh must not run with an empty -R")

    def test_an_unconfigured_gh_dir_refuses_before_gh_runs(self):
        c = self.case(gh_dir=None)
        result = c.run("issue", "list", "-R", "{tracker}")
        self.assertEqual(result.returncode, self.REFUSED, result.stderr)
        self.assertIn("tk.ghConfigDir", result.stderr)
        self.assertFalse(c.gh_was_called())

    def test_an_empty_configured_value_counts_as_unconfigured(self):
        c = self.case(tracker="")
        result = c.run("issue", "list", "-R", "{tracker}")
        self.assertEqual(result.returncode, self.REFUSED, result.stderr)
        self.assertFalse(c.gh_was_called())

    def test_a_command_naming_no_tracker_is_refused(self):
        """Forgetting `-R` is the same accident as an empty one: gh would silently use the
        cwd's repo, which is public."""
        c = self.case()
        result = c.run("issue", "list", "--state", "open")
        self.assertEqual(result.returncode, self.REFUSED, result.stderr)
        self.assertIn("{tracker}", result.stderr)
        self.assertFalse(c.gh_was_called())


if __name__ == "__main__":
    unittest.main()
