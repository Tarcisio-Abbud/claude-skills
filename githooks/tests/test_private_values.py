"""Suite for `githooks/private-values`.

Every test here is proved by `mutations_private_values.py`, which restores each defect the
guard exists to prevent and requires the tests named for it to fail. A test that still passes
with the defect back protects nothing.

Run: python3 -m unittest discover -s githooks/tests
"""

import os
import shutil
import signal
import subprocess
import tempfile
import unittest

GUARD = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "private-values")
GUARD = os.path.abspath(GUARD)

SLUG = "Fictional-Owner/private-tracker"
GHDIR = "/somewhere/private/.gh-config"

# An invented private project name, as the generated file would list it. Fictitious by rule:
# this repo is public, and no real name may appear in it — not even as a fixture.
NAME = "Invented-Project-Nine"
# A name under six letters and digits, which the guard matches with its separators as listed.
# What parsing the file must strip from a name shows only on such a name: a long one is
# compared folded, and folding drops a stray mark or space on its own.
SHORT = "zq-rx"
FILE_KEY = "tk.privateValuesFile"


def guard_source():
    with open(GUARD, encoding="utf-8") as fh:
        return fh.read()


class Repo:
    """A throwaway git repo with the guard installed as both hooks."""

    def __init__(self, tracker=SLUG, gh_dir=GHDIR, names=None):
        """`names`: the text of the needle file, written OUTSIDE the repo and named by
        `tk.privateValuesFile` — as it lives on the authoring machine. None leaves the key
        unset."""
        self.dir = tempfile.mkdtemp(prefix="guard-")
        self.outside = tempfile.mkdtemp(prefix="guard-names-")
        self.names_file = os.path.join(self.outside, "private-values.txt")
        self.git("init", "-q", "-b", "main", ".")
        self.git("config", "user.email", "t@example.invalid")
        self.git("config", "user.name", "t")
        if tracker is not None:
            self.git("config", "tk.tracker", tracker)
        if gh_dir is not None:
            self.git("config", "tk.ghConfigDir", gh_dir)
        if names is not None:
            with open(self.names_file, "w", encoding="utf-8", newline="") as fh:
                fh.write(names)
            self.git("config", FILE_KEY, self.names_file)
        hooks = os.path.join(self.dir, ".git", "hooks")
        os.makedirs(hooks, exist_ok=True)
        text = guard_source()
        for name in ("pre-commit", "commit-msg"):
            path = os.path.join(hooks, name)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(text)
            os.chmod(path, 0o755)

    def git(self, *args):
        return subprocess.run(
            ["git", "-C", self.dir, *args], capture_output=True, text=True
        )

    def write(self, relpath, content, binary=False):
        path = os.path.join(self.dir, relpath)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        mode = "wb" if binary else "w"
        with open(path, mode) as fh:
            fh.write(content)
        return path

    def stage(self):
        self.git("add", "-A", ".")

    def commit(self, message="a change"):
        """Stage everything and commit. Returns the CompletedProcess."""
        self.stage()
        return self.git("commit", "-m", message)

    def commit_unguarded(self, message="planted"):
        """Commit past the hooks, to plant content the guard never inspected."""
        self.stage()
        return self.git("commit", "--no-verify", "-m", message)

    def run_hook(self, *args, timeout=20):
        """The guard run by hand, as git would run it, from the repo's top level. In its own
        process group, killed WHOLE on a timeout: killing only `sh` left a blocked reader
        running after the suite, which is what a hang under mutation used to leave behind."""
        proc = subprocess.Popen(
            ["sh", GUARD, *args], cwd=self.dir, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, start_new_session=True,
        )
        try:
            out, err = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.communicate()
            raise
        return subprocess.CompletedProcess(proc.args, proc.returncode, out, err)

    def cleanup(self):
        shutil.rmtree(self.dir, ignore_errors=True)
        shutil.rmtree(self.outside, ignore_errors=True)


class GuardTest(unittest.TestCase):
    def repo(self, **kwargs):
        r = Repo(**kwargs)
        self.addCleanup(r.cleanup)
        return r

    def assertRefused(self, result):
        self.assertEqual(
            result.returncode, 1, "expected a refusal, got:\n%s%s" % (result.stdout, result.stderr)
        )

    def assertAccepted(self, result):
        self.assertEqual(
            result.returncode, 0, "expected a pass, got:\n%s%s" % (result.stdout, result.stderr)
        )

    # --- the guard lets ordinary work through -------------------------------------

    def test_clean_commit_is_accepted(self):
        r = self.repo()
        r.write("a.txt", "nothing private here\n")
        self.assertAccepted(r.commit())

    # --- the guard refuses each place a value can hide -----------------------------

    def test_slug_in_staged_content_is_refused(self):
        """The joined reading would catch this too. What the line-wise surface earns is the
        precise diagnosis — assert that, or nothing proves the surface exists."""
        r = self.repo()
        r.write("a.txt", "see %s for the tickets\n" % SLUG)
        result = r.commit()
        self.assertRefused(result)
        self.assertIn("in a line this commit adds", result.stderr)

    def test_gh_config_dir_in_staged_content_is_refused(self):
        r = self.repo()
        r.write("a.txt", "export GH_CONFIG_DIR=%s\n" % GHDIR)
        self.assertRefused(r.commit())

    def test_value_in_a_path_is_refused(self):
        r = self.repo()
        r.write(os.path.join(SLUG, "notes.txt"), "innocent body\n")
        self.assertRefused(r.commit())

    def test_value_inside_a_binary_file_is_refused(self):
        """Without `--text`, git summarises a binary as 'Binary files ... differ' and the
        value never reaches grep."""
        r = self.repo()
        r.write("blob.bin", b"\x00\x01" + SLUG.encode() + b"\x00\xff", binary=True)
        result = r.commit()
        self.assertRefused(result)
        self.assertIn("in a line this commit adds", result.stderr)

    def test_value_only_in_the_commit_message_is_refused(self):
        """A pre-commit hook never sees the message; the commit-msg install is what covers it."""
        r = self.repo()
        r.write("a.txt", "innocent body\n")
        self.assertRefused(r.commit(message="closes %s#42" % SLUG))

    # --- the disguises a value can wear ---------------------------------------------
    # Each of these walked straight through an earlier version of the guard.

    def test_rename_into_a_leaky_path_is_refused(self):
        """A pure rename adds no line at all, so only the path betrays it."""
        r = self.repo()
        r.write("plain.txt", "innocent body\n")
        self.assertAccepted(r.commit())
        moved = os.path.join(r.dir, SLUG)
        os.makedirs(os.path.dirname(moved), exist_ok=True)
        r.git("mv", "plain.txt", SLUG)
        result = r.commit(message="move it")
        self.assertRefused(result)
        self.assertIn("in a PATH", result.stderr)

    def test_editing_a_file_whose_path_already_leaked_is_accepted(self):
        """`--diff-filter=ACR` keeps an already-tracked path from being re-reported on every
        edit near it — the false positive that misdirects the author."""
        r = self.repo()
        r.write(os.path.join(SLUG, "notes.txt"), "first\n")
        planted = r.commit_unguarded()
        self.assertEqual(planted.returncode, 0, planted.stderr)
        r.write(os.path.join(SLUG, "notes.txt"), "first\nsecond\n")
        self.assertAccepted(r.commit(message="edit inside it"))

    def test_case_changed_value_is_refused(self):
        """A GitHub slug is case-insensitive, so a re-cased copy publishes the same identity.
        Asserting the surface too: the joined reading folds case on its own, so a bare
        assertRefused would pass with the line-wise fold removed."""
        r = self.repo()
        r.write("a.txt", "see %s\n" % SLUG.upper())
        result = r.commit()
        self.assertRefused(result)
        self.assertIn("in a line this commit adds", result.stderr)

    def test_percent_encoded_value_is_refused(self):
        r = self.repo()
        r.write("a.txt", "repos/%s/issues\n" % SLUG.replace("/", "%2F"))
        self.assertRefused(r.commit())

    def test_value_wrapped_across_two_lines_is_refused(self):
        owner, name = SLUG.split("/")
        r = self.repo()
        r.write("a.txt", "see %s/\n%s here\n" % (owner, name))
        result = r.commit()
        self.assertRefused(result)
        self.assertIn("consecutive added lines", result.stderr)
        self.assertIn("a.txt", result.stderr)

    def test_wrapped_remedy_runs_and_finds_the_value(self):
        """The wrapped case needs its own remedy: the line-wise search prints nothing."""
        owner, name = SLUG.split("/")
        r = self.repo()
        r.write("a.txt", "see %s/\n%s here\n" % (owner, name))
        result = r.commit()
        self.assertRefused(result)
        printed = [
            line.split("see it:", 1)[1].strip()
            for line in result.stderr.splitlines()
            if "see it:" in line
        ]
        self.assertEqual(len(printed), 1, "expected one remedy line, got: %r" % printed)
        shown = subprocess.run(
            printed[0], shell=True, cwd=r.dir, capture_output=True, text=True
        )
        self.assertEqual(shown.returncode, 0, "the printed remedy did not run: %s" % shown.stderr)
        # It shows the wrap rather than the value: both halves, on the two lines that made it,
        # and nothing else — the `+++` header included would be noise the reader must discount.
        owner, name = SLUG.split("/")
        self.assertIn(owner.lower(), shown.stdout.lower())
        self.assertIn(name.lower(), shown.stdout.lower())
        self.assertEqual(
            [l for l in shown.stdout.splitlines() if l.strip()],
            ["see %s/" % owner, "%s here" % name],
            "the remedy should show the two wrapped lines and nothing else",
        )

    def test_refusal_names_the_surface_that_fired(self):
        r = self.repo()
        r.write("a.txt", "innocent body\n")
        result = r.commit(message="closes %s#42" % SLUG)
        self.assertRefused(result)
        self.assertIn("in the commit message", result.stderr)

    # --- joining lines must not invent a value that nobody wrote ---------------------

    def test_two_files_meeting_at_the_seam_are_accepted(self):
        """Joining the whole diff glued the last line of one file to the first of the next,
        so the alphabetical order of FILENAMES decided whether innocent text collided."""
        owner, name = SLUG.split("/")
        r = self.repo()
        r.write("a-first.md", "owner is %s" % owner)
        r.write("b-second.md", "/%s is a path fragment\n" % name)
        self.assertAccepted(r.commit())

    def test_a_wrap_inside_one_file_is_still_refused(self):
        """The other half: narrowing to one file must not blind the join."""
        owner, name = SLUG.split("/")
        r = self.repo()
        r.write("only.md", "see %s/\n%s here\n" % (owner, name))
        self.assertRefused(r.commit())

    def test_wrapped_remedy_survives_crlf_line_endings(self):
        """The refusal was already right on a CRLF file; the remedy it printed showed
        nothing, so the reader could not see why."""
        owner, name = SLUG.split("/")
        r = self.repo()
        r.write("crlf.md", "see %s/\r\n%s here\r\n" % (owner, name))
        result = r.commit()
        self.assertRefused(result)
        printed = [
            line.split("see it:", 1)[1].strip()
            for line in result.stderr.splitlines()
            if "see it:" in line
        ]
        self.assertEqual(len(printed), 1)
        shown = subprocess.run(
            printed[0], shell=True, cwd=r.dir, capture_output=True, text=True
        )
        self.assertEqual(shown.returncode, 0, shown.stderr)
        self.assertIn(owner.lower(), shown.stdout.lower())
        self.assertIn(name.lower(), shown.stdout.lower())

    def test_a_short_name_wrapped_in_a_crlf_file_is_refused(self):
        """A short name is matched raw, so the carriage return left on a CRLF line would sit
        at the seam of the join and hide it."""
        r = self.repo(names="%s\n" % SHORT)
        r.write("crlf.md", "see %s\r\n%s here\r\n" % (SHORT[:3], SHORT[3:]))
        result = r.commit()
        self.assertRefused(result)
        self.assertIn("consecutive added lines", result.stderr)

    # --- encodings and the refs that also get pushed ---------------------------------

    def test_double_encoded_value_is_refused(self):
        """`%252F` is what a second encoding pass does to the `%` of the first."""
        r = self.repo()
        r.write("a.txt", "repos/%s/issues\n" % SLUG.replace("/", "%252F"))
        self.assertRefused(r.commit())

    def test_branch_name_transliterating_the_value_is_refused(self):
        """A branch name is pushed and as visible as a path. The idiom is to swap the separators, so
        `/` and `_` are folded to `-` on both sides before comparing."""
        r = self.repo()
        r.write("seed.txt", "seed\n")
        self.assertAccepted(r.commit())
        r.git("checkout", "-q", "-b", "leak/%s" % SLUG.replace("/", "-"))
        r.write("a.txt", "entirely innocent\n")
        result = r.commit()
        self.assertRefused(result)
        self.assertIn("BRANCH NAME", result.stderr)

    def test_branch_name_carrying_the_literal_value_is_refused(self):
        r = self.repo()
        r.write("seed.txt", "seed\n")
        self.assertAccepted(r.commit())
        r.git("checkout", "-q", "-b", "leak/%s" % SLUG)
        r.write("a.txt", "entirely innocent\n")
        self.assertRefused(r.commit())

    def test_branch_name_with_other_separators_is_refused(self):
        """A dot is neither `/` nor `_`, and folding only those two let it through."""
        r = self.repo()
        r.write("seed.txt", "seed\n")
        self.assertAccepted(r.commit())
        r.git("checkout", "-q", "-b", "leak.%s" % SLUG.replace("/", "."))
        r.write("a.txt", "entirely innocent\n")
        result = r.commit()
        self.assertRefused(result)
        self.assertIn("BRANCH NAME", result.stderr)

    def test_branch_name_with_no_separators_at_all_is_refused(self):
        """`leakOwnerrepo` spells the identity as surely as `leak/Owner/repo`."""
        r = self.repo()
        r.write("seed.txt", "seed\n")
        self.assertAccepted(r.commit())
        r.git("checkout", "-q", "-b", "leak%s" % SLUG.replace("/", ""))
        r.write("a.txt", "entirely innocent\n")
        self.assertRefused(r.commit())

    def test_an_ordinary_branch_name_is_accepted(self):
        """Folding separators must not start refusing ordinary hyphenated branches."""
        r = self.repo()
        r.write("seed.txt", "seed\n")
        self.assertAccepted(r.commit())
        r.git("checkout", "-q", "-b", "fix/some-ordinary-branch-name")
        r.write("a.txt", "entirely innocent\n")
        self.assertAccepted(r.commit())

    # --- the two branches that would make the guard useless ------------------------

    def test_unset_key_protects_nothing(self):
        r = self.repo(tracker=None, gh_dir=None)
        r.write("a.txt", "see %s\n" % SLUG)
        self.assertAccepted(r.commit())

    def test_empty_value_does_not_match_every_commit(self):
        """An empty needle makes `grep -F` match anything, which would refuse all work."""
        r = self.repo(tracker="", gh_dir=None)
        r.write("a.txt", "entirely innocent\n")
        self.assertAccepted(r.commit())

    # --- the refusal has to be actionable ------------------------------------------

    def test_refusal_names_the_key_that_fired(self):
        r = self.repo()
        r.write("a.txt", "export GH_CONFIG_DIR=%s\n" % GHDIR)
        result = r.commit()
        self.assertRefused(result)
        self.assertIn("tk.ghConfigDir", result.stderr)
        self.assertNotIn("git config tk.tracker", result.stderr)

    def test_printed_remedy_runs_and_finds_the_line(self):
        """A remedy that does not run is a dead end, so run the one the guard PRINTED —
        asserting a command typed here instead would prove nothing about the message."""
        r = self.repo()
        r.write("a.txt", "see %s\n" % SLUG)
        result = r.commit()
        self.assertRefused(result)
        printed = [
            line.split("see it:", 1)[1].strip()
            for line in result.stderr.splitlines()
            if "see it:" in line
        ]
        self.assertEqual(len(printed), 1, "expected one remedy line, got: %r" % printed)
        shown = subprocess.run(
            printed[0], shell=True, cwd=r.dir, capture_output=True, text=True
        )
        self.assertEqual(shown.returncode, 0, "the printed remedy did not run: %s" % shown.stderr)
        self.assertIn(SLUG, shown.stdout)
        # and the repair it prescribes has to leave the commit acceptable
        r.write("a.txt", "see $(git config tk.tracker)\n")
        self.assertAccepted(r.commit())


    # --- the guard reads what a commit ADDS ----------------------------------------
    # A value already in the file is not this commit's doing, and refusing over it would
    # prescribe editing a line the commit never touched.

    def test_value_already_committed_nearby_does_not_trip_the_guard(self):
        r = self.repo()
        r.write("a.txt", "first\nsee %s\nthird\n" % SLUG)
        planted = r.commit_unguarded()
        self.assertEqual(planted.returncode, 0, planted.stderr)
        r.write("a.txt", "FIRST EDITED\nsee %s\nthird\n" % SLUG)
        self.assertAccepted(r.commit(message="edit the neighbour"))

    def test_the_same_value_added_now_is_still_refused(self):
        """The other half: narrowing to added lines must not blind the guard."""
        r = self.repo()
        r.write("a.txt", "first\nsecond\n")
        self.assertAccepted(r.commit())
        r.write("a.txt", "first\nsecond\nsee %s\n" % SLUG)
        result = r.commit(message="add it now")
        self.assertRefused(result)
        # The joined reading would catch it too; the line-wise surface earns the diagnosis.
        self.assertIn("in a line this commit adds", result.stderr)

    # --- the third source: names from a file outside the repo ----------------------
    # The file is what carries the machine's private PROJECT names, which no config value
    # spells. A commit message once published one of them and passed this guard.

    def test_file_name_in_staged_content_is_refused(self):
        """The pre-commit half of the criterion."""
        r = self.repo(names="%s\n" % NAME)
        r.write("a.txt", "notes on %s\n" % NAME)
        result = r.commit()
        self.assertRefused(result)
        self.assertIn("in a line this commit adds", result.stderr)

    def test_file_name_in_the_commit_message_is_refused(self):
        """The commit-msg half of the criterion, and the exact shape of the measured leak."""
        r = self.repo(names="%s\n" % NAME)
        r.write("a.txt", "innocent body\n")
        result = r.commit(message="fix: the %s report" % NAME)
        self.assertRefused(result)
        self.assertIn("in the commit message", result.stderr)

    def test_commit_msg_hook_run_by_hand_refuses_a_file_name(self):
        """Run as git runs `commit-msg` — the message file as $1 — with nothing staged: this
        is how a message is checked against the file without making a commit."""
        r = self.repo(names="%s\n" % NAME)
        leaky = r.write("leaky-msg", "fix: the %s report\n" % NAME)
        clean = r.write("clean-msg", "fix: a report\n")
        self.assertRefused(r.run_hook(leaky))
        self.assertAccepted(r.run_hook(clean))

    def test_pre_commit_hook_run_by_hand_refuses_a_file_name(self):
        """Run as git runs `pre-commit` — no argument — over what is staged."""
        r = self.repo(names="%s\n" % NAME)
        r.write("a.txt", "notes on %s\n" % NAME)
        r.stage()
        self.assertRefused(r.run_hook())

    def test_file_name_recased_is_refused(self):
        r = self.repo(names="%s\n" % NAME)
        r.write("a.txt", "notes on %s\n" % NAME.lower())
        self.assertRefused(r.commit())

    def test_file_name_wrapped_across_two_lines_is_refused(self):
        head, tail = NAME[:9], NAME[9:]
        r = self.repo(names="%s\n" % NAME)
        r.write("a.txt", "notes on %s\n%s here\n" % (head, tail))
        result = r.commit()
        self.assertRefused(result)
        self.assertIn("consecutive added lines", result.stderr)

    def test_file_name_in_a_branch_name_is_refused(self):
        r = self.repo(names="%s\n" % NAME)
        r.write("seed.txt", "seed\n")
        self.assertAccepted(r.commit())
        r.git("checkout", "-q", "-b", "fix/%s" % NAME.lower())
        r.write("a.txt", "entirely innocent\n")
        result = r.commit()
        self.assertRefused(result)
        self.assertIn("BRANCH NAME", result.stderr)

    def test_every_listed_name_is_a_needle_not_only_the_first(self):
        r = self.repo(names="Invented-Alpha-Name\n%s\n" % NAME)
        r.write("a.txt", "notes on %s\n" % NAME)
        self.assertRefused(r.commit())

    def test_file_name_refusal_names_the_file_key_and_the_name(self):
        """No lookup can print a file's name back, so the refusal names it — locally."""
        r = self.repo(names="%s\n" % NAME)
        r.write("a.txt", "notes on %s\n" % NAME)
        result = r.commit()
        self.assertRefused(result)
        self.assertIn("listed in the file that git config %s names" % FILE_KEY, result.stderr)
        self.assertIn("'%s'" % NAME, result.stderr)
        self.assertNotIn("git config tk.tracker", result.stderr)

    def test_file_name_remedy_runs_and_finds_the_line(self):
        """A listed name may carry a space or a quote; the printed search must still run."""
        name = "O'Invented Holding"
        r = self.repo(names="%s\n" % name)
        r.write("a.txt", "notes on %s\n" % name)
        result = r.commit()
        self.assertRefused(result)
        printed = [
            line.split("see it:", 1)[1].strip()
            for line in result.stderr.splitlines()
            if "see it:" in line
        ]
        self.assertEqual(len(printed), 1, "expected one remedy line, got: %r" % printed)
        shown = subprocess.run(
            printed[0], shell=True, cwd=r.dir, capture_output=True, text=True
        )
        self.assertEqual(shown.returncode, 0, "the printed remedy did not run: %s" % shown.stderr)
        self.assertIn(name, shown.stdout)

    # --- a listed name spelled with other separators ---------------------------------
    # The list is shared with a `gh` publish guard that compares it with the separators
    # dropped; matching it raw let `Invented Project Nine` through where the list says
    # `Invented-Project-Nine`, and prose spells names that way.

    def test_listed_name_with_other_separators_in_the_message_is_refused(self):
        r = self.repo(names="%s\n" % NAME)
        for spelling in ("Invented Project Nine", "InventedProjectNine", "invented_project_nine"):
            leaky = r.write("leaky-msg", "fix: the %s report\n" % spelling)
            result = r.run_hook(leaky)
            self.assertRefused(result)
            self.assertIn("spelled with other separators", result.stderr)

    def test_listed_name_with_other_separators_in_added_lines_is_refused(self):
        r = self.repo(names="%s\n" % NAME)
        r.write("a.txt", "notes on Invented Project Nine\n")
        self.assertRefused(r.commit())

    def test_listed_name_wrapped_with_other_separators_is_refused(self):
        r = self.repo(names="%s\n" % NAME)
        r.write("a.txt", "notes on Invented Project\nNine here\n")
        result = r.commit()
        self.assertRefused(result)
        self.assertIn("consecutive added lines", result.stderr)

    def test_folded_remedy_runs_and_finds_the_line(self):
        """The listed spelling is not in the diff, so the printed search must fold as the
        match did, or it finds nothing."""
        r = self.repo(names="%s\n" % NAME)
        r.write("a.txt", "notes on Invented Project Nine\n")
        result = r.commit()
        self.assertRefused(result)
        printed = [
            line.split("see it:", 1)[1].strip()
            for line in result.stderr.splitlines()
            if "see it:" in line
        ]
        self.assertEqual(len(printed), 1, "expected one remedy line, got: %r" % printed)
        shown = subprocess.run(
            printed[0], shell=True, cwd=r.dir, capture_output=True, text=True
        )
        self.assertEqual(shown.returncode, 0, "the printed remedy did not run: %s" % shown.stderr)
        self.assertIn("inventedprojectnine", shown.stdout.lower())

    def test_a_short_listed_name_keeps_its_separators(self):
        """Below six letters and digits a run of them occurs by accident in prose, so a short
        name is matched as listed, and only as listed."""
        r = self.repo(names="ab-cd\n")
        clean = r.write("clean-msg", "fix: ab cd and abcd are ordinary here\n")
        leaky = r.write("leaky-msg", "fix: the ab-cd report\n")
        self.assertAccepted(r.run_hook(clean))
        self.assertRefused(r.run_hook(leaky))

    # --- what the file holds that is not a name --------------------------------------

    def test_comment_and_blank_lines_are_not_needles(self):
        """A comment kept as a needle would refuse every commit that quotes it; a blank one
        would match every commit."""
        r = self.repo(names="# generated list\n\n   \n%s\n" % NAME)
        r.write("a.txt", "# generated list of nothing private\n")
        self.assertAccepted(r.commit())

    def test_a_byte_order_mark_does_not_hide_the_first_name(self):
        r = self.repo(names="\ufeff%s\n" % SHORT)
        r.write("a.txt", "notes on %s\n" % SHORT)
        self.assertRefused(r.commit())

    def test_a_byte_order_mark_before_a_later_name_does_not_hide_it(self):
        """Two exports joined put a second mark mid-file, in front of a later name."""
        r = self.repo(names="# list\n\ufeff%s\n" % SHORT)
        r.write("a.txt", "notes on %s\n" % SHORT)
        self.assertRefused(r.commit())

    def test_a_carriage_return_does_not_hide_a_name(self):
        r = self.repo(names="# list\r\n%s\r\n" % SHORT)
        r.write("a.txt", "notes on %s\n" % SHORT)
        self.assertRefused(r.commit())

    def test_surrounding_whitespace_does_not_hide_a_name(self):
        r = self.repo(names="# list\n  %s\t \n" % SHORT)
        r.write("a.txt", "notes on %s\n" % SHORT)
        self.assertRefused(r.commit())

    def test_an_empty_file_protects_nothing_more(self):
        """A list with nothing on it is not a broken list: the export may have found nothing."""
        r = self.repo(names="# generated, and nothing to list\n")
        r.write("a.txt", "notes on %s\n" % NAME)
        self.assertAccepted(r.commit())

    def test_unset_file_key_protects_nothing_more(self):
        r = self.repo()
        r.write("a.txt", "notes on %s\n" % NAME)
        self.assertAccepted(r.commit())

    # --- the key promises protection; a file that cannot be read breaks the promise ----

    def test_missing_file_refuses_and_the_remedy_restores_commits(self):
        """Fail closed: a failed export must not turn the guard off in silence. The remedy
        the refusal prints is run, and the commit then goes through."""
        r = self.repo(names="%s\n" % NAME)
        os.unlink(r.names_file)
        r.write("a.txt", "entirely innocent\n")
        result = r.commit()
        self.assertRefused(result)
        self.assertIn(FILE_KEY, result.stderr)
        self.assertIn("not a readable file", result.stderr)
        remedy = [l.split("with:", 1)[1].strip() for l in result.stderr.splitlines() if "with:" in l]
        self.assertEqual(len(remedy), 1, "expected one remedy, got: %r" % remedy)
        ran = subprocess.run(remedy[0], shell=True, cwd=r.dir, capture_output=True, text=True)
        self.assertEqual(ran.returncode, 0, ran.stderr)
        self.assertAccepted(r.commit())

    def test_a_directory_in_place_of_the_file_refuses(self):
        r = self.repo(names="%s\n" % NAME)
        os.unlink(r.names_file)
        os.mkdir(r.names_file)
        r.write("a.txt", "entirely innocent\n")
        self.assertRefused(r.commit())

    def test_a_fifo_in_place_of_the_file_refuses_without_blocking(self):
        """A FIFO does not fail a read, it blocks it: without the regular-file check the commit
        hangs with nothing on screen. The timeout turns that hang into a failure."""
        r = self.repo(names="%s\n" % NAME)
        os.unlink(r.names_file)
        os.mkfifo(r.names_file)
        r.write("a.txt", "entirely innocent\n")
        r.stage()
        self.assertRefused(r.run_hook(timeout=10))


if __name__ == "__main__":
    unittest.main()
