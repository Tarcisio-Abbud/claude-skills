#!/usr/bin/env python3
"""Suite for `tk-ticket-ref` and `tk-closure-check` (../bin/).

Run: python3 -m unittest discover -s tk/tests   (stdlib only, no deps)
Proved by: python3 tk/tests/mutations_closure.py

WHY THE TWO BINS SHARE ONE SUITE. They are one mechanism read from two ends:
the reader composes the owner-qualified reference a closing line carries, and
the checker asks whether the pull request's body carries that same reference.
Splitting them would give each half its own fixture for the one queue item and
the one tracker they both read.

THE SUITE NEVER TOUCHES THE NETWORK, and never reads this machine's own
configuration. Every run gets a throwaway queue built by the real `tk-queue`, a
throwaway git repository carrying `tk.tracker`, a redirected `HOME`, and
`GIT_CONFIG_GLOBAL`/`GIT_CONFIG_SYSTEM` pointed at a path that does not exist —
without those two, the machine's own tracker slug would answer `git config` and
the fixture would silently be testing this account's private repository. The
`--pr` mode gets a fake `gh` at the FRONT of PATH which records its argv; a test
asserting that record is what proves the shadowing works, since the real `gh`
would leave the record empty rather than fall.

REPOSITORY AND OWNER NAMES ARE FICTIONAL. This repo is public and neither bin
carries a name of its own, so the fixtures must not smuggle one back in.

VALUES ARE ASSERTED AT THE LITERAL. Every string that crosses a process
boundary — the reference on stdout, each condition's name and state, the verdict
line, the refusal codes — is compared against the text itself rather than
against a re-computation of it. A test that rebuilds the expected value with the
code under test agrees with any mutation of that code.
"""

import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
BIN = os.path.join(HERE, os.pardir, "bin")
QUEUE = os.path.join(BIN, "tk-queue")
READER = os.path.join(BIN, "tk-ticket-ref")
CHECKER = os.path.join(BIN, "tk-closure-check")
SKILLS = os.path.join(HERE, os.pardir, "skills")

OWNER = "Fictional-Owner"
REPO = "tracker-repo"
SLUG = f"{OWNER}/{REPO}"

HEADER = """---
name: next-steps
description: fixture
metadata:
  type: project
---

# Next steps

"""

# The fake forge CLI. It answers `pr view` and `repo view` from a table on disk
# and records every call, so a test can prove the run went through PATH.
FAKE_GH = r"""#!/usr/bin/env python3
import os, sys
table = os.environ["FAKE_GH_TABLE"]
with open(os.path.join(table, "calls"), "a", encoding="utf-8") as f:
    f.write(" ".join(sys.argv[1:]) + "\n")
name = "pr" if sys.argv[1:2] == ["pr"] else "repo"
answer = os.path.join(table, name + ".json")
if not os.path.isfile(answer):
    sys.stderr.write("no such answer staged: %s\n" % name)
    sys.exit(1)
with open(answer, encoding="utf-8") as f:
    sys.stdout.write(f.read())
"""


class Fixture(unittest.TestCase):
    """One throwaway queue, one throwaway clone, one fake `gh`."""

    def setUp(self):
        self.tmp = os.path.realpath(tempfile.mkdtemp(prefix="tk-closure-test."))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.mem = os.path.join(self.tmp, "memory")
        self.home = os.path.join(self.tmp, "home")
        self.clone = os.path.join(self.tmp, "clone")
        self.table = os.path.join(self.tmp, "gh-table")
        self.stub = os.path.join(self.tmp, "stub-bin")
        for d in (self.mem, self.home, self.clone, self.table, self.stub):
            os.makedirs(d)
        with open(os.path.join(self.mem, "next-steps.md"), "w", encoding="utf-8") as f:
            f.write(HEADER)
        subprocess.run(["git", "-C", self.clone, "init", "-q", "."], check=True)
        self.set_tracker(SLUG)
        gh = os.path.join(self.stub, "gh")
        with open(gh, "w", encoding="utf-8") as f:
            f.write(FAKE_GH)
        os.chmod(gh, os.stat(gh).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

    def set_tracker(self, value):
        if value is None:
            subprocess.run(["git", "-C", self.clone, "config", "--unset", "tk.tracker"])
            return
        subprocess.run(["git", "-C", self.clone, "config", "tk.tracker", value], check=True)

    def env(self):
        absent = os.path.join(self.tmp, "no-such-git-config")
        return dict(os.environ, HOME=self.home,
                    GIT_CONFIG_GLOBAL=absent, GIT_CONFIG_SYSTEM=absent,
                    FAKE_GH_TABLE=self.table,
                    PATH=self.stub + os.pathsep + os.environ["PATH"])

    def add(self, text="a slice", ticket=None, extra=()):
        argv = [sys.executable, QUEUE, "add", text, "--class", "AUTONOMOUS",
                "--effort", "S: 1h", "--criterion", "A: the suite is green",
                "--dir", self.mem]
        if ticket:
            argv += ["--ticket", ticket]
        argv += list(extra)
        run = subprocess.run(argv, capture_output=True, text=True, env=self.env(),
                             cwd=self.tmp)
        self.assertEqual(run.returncode, 0, run.stderr)
        return re.search(r"added (T[0-9]+)", run.stdout).group(1)

    def queue_text(self):
        with open(os.path.join(self.mem, "next-steps.md"), encoding="utf-8") as f:
            return f.read()

    def write_queue(self, text):
        with open(os.path.join(self.mem, "next-steps.md"), "w", encoding="utf-8") as f:
            f.write(text)

    def read(self, *argv):
        return subprocess.run([sys.executable, READER, *argv, "--dir", self.mem,
                               "--repo", self.clone],
                              capture_output=True, text=True, env=self.env(), cwd=self.tmp)

    def body_file(self, body):
        path = os.path.join(self.tmp, "body.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(body)
        return path

    def check(self, item, body, base="main", default="main", extra=()):
        return subprocess.run(
            [sys.executable, CHECKER, item, "--dir", self.mem, "--repo", self.clone,
             "--body-file", self.body_file(body), "--base", base,
             "--default-branch", default, *extra],
            capture_output=True, text=True, env=self.env(), cwd=self.tmp)

    def stage_gh(self, body, base="main", default="main"):
        with open(os.path.join(self.table, "pr.json"), "w", encoding="utf-8") as f:
            json.dump({"body": body, "baseRefName": base}, f)
        with open(os.path.join(self.table, "repo.json"), "w", encoding="utf-8") as f:
            json.dump({"defaultBranchRef": None if default is None else {"name": default}}, f)

    def gh_calls(self):
        path = os.path.join(self.table, "calls")
        if not os.path.exists(path):
            return []
        with open(path, encoding="utf-8") as f:
            return [line for line in f.read().splitlines() if line.strip()]

    def unpairable(self, item):
        """The `[?]` state: a second **Ticket:** in the item's own field chain.

        Written by hand into the file because `tk-queue` refuses to create it —
        which is the point. The state arrives through a hand edit, a foreign
        tool or a merge, and until now it had no remedy at all."""
        text = self.queue_text()
        self.write_queue(text.replace("**Born:**", "**Ticket:** other-repo#9. **Born:**"))
        return item


class TestTheReferenceReader(Fixture):
    def test_an_items_ticket_is_printed_owner_qualified(self):
        item = self.add(ticket=f"{REPO}#7")
        run = self.read(item)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stdout, f"{OWNER}/{REPO}#7\n")

    def test_the_trackers_spelling_of_both_halves_is_the_one_printed(self):
        """The queue lower-cases a repo name on the way in, so an emitted half
        taken from the ITEM would print a slug a human does not recognise."""
        self.set_tracker(f"{OWNER}/Tracker-Repo")
        item = self.add(ticket="Tracker-Repo#7")
        run = self.read(item)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stdout, f"{OWNER}/Tracker-Repo#7\n")

    def test_the_closing_line_flag_prints_the_whole_line(self):
        item = self.add(ticket=f"{REPO}#7")
        run = self.read(item, "--closing-line")
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stdout, f"Fixes {OWNER}/{REPO}#7\n")

    def test_an_item_naming_no_ticket_exits_three_and_prints_no_reference(self):
        item = self.add()
        run = self.read(item)
        self.assertEqual(run.returncode, 3, run.stdout + run.stderr)
        self.assertEqual(run.stdout, "")
        self.assertIn("no-ticket:", run.stderr)

    def test_an_unpairable_ticket_is_refused_with_a_reachable_remedy(self):
        """F2. Two **Ticket:** fields in one chain say two things, so the reader
        may pick neither — and the remedy has to be NAMED, because provenance is
        add-only and `edit --ticket` does not exist to point at."""
        item = self.unpairable(self.add(ticket=f"{REPO}#7"))
        run = self.read(item)
        self.assertEqual(run.returncode, 1, run.stdout + run.stderr)
        self.assertEqual(run.stdout, "")
        self.assertIn("unpairable-ticket:", run.stderr)
        self.assertIn(f"tk-queue cancel {item}", run.stderr)
        self.assertIn("--ticket", run.stderr)

    def test_an_unset_tracker_refuses_rather_than_emitting_an_ownerless_reference(self):
        self.set_tracker(None)
        item = self.add(ticket=f"{REPO}#7")
        run = self.read(item)
        self.assertEqual(run.returncode, 1, run.stdout + run.stderr)
        self.assertEqual(run.stdout, "")
        self.assertIn("tracker-unset:", run.stderr)
        self.assertIn("git config tk.tracker <owner>/<repo>", run.stderr)

    def test_a_tracker_outside_the_slug_shape_is_refused_not_pasted(self):
        """F4. The value goes through the gate `bin/tracker-gh` applies before
        it is joined to anything: a raw config read would compose
        `Fictional-Owner|tracker-repo#7` and hand it to a merge."""
        self.set_tracker(f"{OWNER}|{REPO}")
        item = self.add(ticket=f"{REPO}#7")
        run = self.read(item)
        self.assertEqual(run.returncode, 1, run.stdout + run.stderr)
        self.assertEqual(run.stdout, "")
        self.assertIn("tracker-malformed:", run.stderr)

    def test_a_ticket_in_another_repository_is_refused_not_given_this_owner(self):
        item = self.add(ticket="another-repo#7")
        run = self.read(item)
        self.assertEqual(run.returncode, 1, run.stdout + run.stderr)
        self.assertEqual(run.stdout, "")
        self.assertIn("repo-mismatch:", run.stderr)

    def test_a_claimed_item_still_answers_with_its_reference(self):
        """F3. `tk-queue list` never prints **Ticket:**, and `pack` prints it
        only while the item is ELIGIBLE — a claimed item shows up as excluded,
        with no ticket beside it. The gate session reads a claimed item's ticket
        here or nowhere."""
        item = self.add(ticket=f"{REPO}#7")
        claim = subprocess.run([sys.executable, QUEUE, "claim", item, "--as", "a-session",
                                "--dir", self.mem],
                               capture_output=True, text=True, env=self.env(), cwd=self.tmp)
        self.assertEqual(claim.returncode, 0, claim.stderr)
        run = self.read(item)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stdout, f"{OWNER}/{REPO}#7\n")

    def test_an_id_no_open_item_carries_is_a_failed_run_not_a_refusal(self):
        self.add(ticket=f"{REPO}#7")
        run = self.read("T404")
        self.assertEqual(run.returncode, 2, run.stdout + run.stderr)
        self.assertIn("T404", run.stderr)


class TestTheClosureChecker(Fixture):
    def body(self, ref=None, keyword="Fixes"):
        return ("What this slice does.\n\n"
                f"{keyword} {ref if ref else f'{OWNER}/{REPO}#7'}\n")

    def test_a_body_closing_this_items_ticket_is_green(self):
        item = self.add(ticket=f"{REPO}#7")
        run = self.check(item, self.body())
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertIn(f"verdict-5: GREEN for {item}", run.stdout)

    def test_every_condition_is_reported_by_name_green_or_red(self):
        """A gate that prints only its failures cannot be told from a gate that
        skipped a check."""
        item = self.add(ticket=f"{REPO}#7")
        run = self.check(item, self.body())
        for name in ("keyword", "number", "owner", "base"):
            self.assertRegex(run.stdout, rf"(?m)^{name}\s+ok\s")

    def test_a_body_closing_another_ticket_is_red_on_number(self):
        item = self.add(ticket=f"{REPO}#7")
        run = self.check(item, self.body(f"{OWNER}/{REPO}#8"))
        self.assertEqual(run.returncode, 1, run.stdout)
        self.assertRegex(run.stdout, r"(?m)^number\s+FAILED\s")
        self.assertIn(f"verdict-5: RED for {item} — number", run.stdout)

    def test_a_closing_word_the_forge_does_not_honour_is_red_on_keyword(self):
        """T226 (a), measured on a real pull request: `Fecha #n` is present,
        cites the right ticket, and closes nothing. The set is English."""
        item = self.add(ticket=f"{REPO}#7")
        run = self.check(item, self.body(keyword="Fecha"))
        self.assertEqual(run.returncode, 1, run.stdout)
        self.assertRegex(run.stdout, r"(?m)^keyword\s+FAILED\s")
        self.assertIn("Fecha", run.stdout)
        self.assertIn("fixes, fix, fixed, closes, close, closed, "
                      "resolves, resolve, resolved", run.stdout)

    def test_a_body_with_no_closing_line_at_all_is_red_on_keyword(self):
        item = self.add(ticket=f"{REPO}#7")
        run = self.check(item, "What this slice does, and nothing else.\n")
        self.assertEqual(run.returncode, 1, run.stdout)
        self.assertRegex(run.stdout, r"(?m)^keyword\s+FAILED\s")

    def test_an_ownerless_reference_is_red_on_owner(self):
        item = self.add(ticket=f"{REPO}#7")
        run = self.check(item, self.body(f"{REPO}#7"))
        self.assertEqual(run.returncode, 1, run.stdout)
        self.assertRegex(run.stdout, r"(?m)^owner\s+FAILED\s")
        self.assertIn("no owner half", run.stdout)

    def test_an_owner_present_but_wrong_is_red(self):
        """F5. It is present, it is well-formed, and the forge resolves it —
        against somebody else's repository. Only an identity check sees it."""
        item = self.add(ticket=f"{REPO}#7")
        run = self.check(item, self.body(f"Other-Owner/{REPO}#7"))
        self.assertEqual(run.returncode, 1, run.stdout)
        self.assertRegex(run.stdout, r"(?m)^owner\s+FAILED\s")
        self.assertIn("Other-Owner", run.stdout)
        self.assertIn(OWNER, run.stdout)

    def test_a_malformed_owner_half_is_red_on_owner(self):
        item = self.add(ticket=f"{REPO}#7")
        run = self.check(item, self.body(f"{OWNER}|x/{REPO}#7"))
        self.assertEqual(run.returncode, 1, run.stdout)
        self.assertRegex(run.stdout, r"(?m)^owner\s+FAILED\s")
        self.assertIn("is not a GitHub slug", run.stdout)

    def test_a_pull_request_off_the_default_branch_is_red_on_base(self):
        item = self.add(ticket=f"{REPO}#7")
        run = self.check(item, self.body(), base="spec/144-lane", default="main")
        self.assertEqual(run.returncode, 1, run.stdout)
        self.assertRegex(run.stdout, r"(?m)^base\s+FAILED\s")
        self.assertIn("spec/144-lane", run.stdout)

    def test_two_failing_conditions_are_both_named_in_the_verdict(self):
        item = self.add(ticket=f"{REPO}#7")
        run = self.check(item, self.body(f"Other-Owner/{REPO}#7"),
                         base="spec/144-lane", default="main")
        self.assertEqual(run.returncode, 1, run.stdout)
        self.assertIn(f"verdict-5: RED for {item} — owner, base", run.stdout)

    def test_an_item_with_no_ticket_is_green_and_the_item_is_quoted(self):
        """The escape verdict 5 honours, and it is the ITEM that gives it: the
        quoted line is what the digest is required to show."""
        item = self.add("a slice answering to no ticket")
        run = self.check(item, "What this slice does.\n")
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertIn(f"verdict-5: GREEN for {item}", run.stdout)
        self.assertIn("a slice answering to no ticket", run.stdout)

    def test_an_item_with_no_ticket_whose_body_closes_something_is_red(self):
        item = self.add("a slice answering to no ticket")
        run = self.check(item, self.body())
        self.assertEqual(run.returncode, 1, run.stdout)
        self.assertIn(f"verdict-5: RED for {item} — ticket", run.stdout)

    def test_an_unpairable_ticket_is_red_with_its_remedy(self):
        """F2's other half: verdict 5 has an EXIT for the `[?]` state now — red,
        with the repair named, instead of permanent red with nothing to do."""
        item = self.unpairable(self.add(ticket=f"{REPO}#7"))
        run = self.check(item, self.body())
        self.assertEqual(run.returncode, 1, run.stdout)
        self.assertIn("unpairable-ticket:", run.stdout)
        self.assertIn(f"tk-queue cancel {item}", run.stdout)

    def test_an_unconfigured_clone_is_red_rather_than_green_by_default(self):
        self.set_tracker(None)
        item = self.add(ticket=f"{REPO}#7")
        run = self.check(item, self.body())
        self.assertEqual(run.returncode, 1, run.stdout)
        self.assertIn("tracker-unset:", run.stdout)

    def test_the_offline_mode_refuses_to_leave_the_base_condition_unasked(self):
        item = self.add(ticket=f"{REPO}#7")
        run = subprocess.run(
            [sys.executable, CHECKER, item, "--dir", self.mem, "--repo", self.clone,
             "--body-file", self.body_file(self.body())],
            capture_output=True, text=True, env=self.env(), cwd=self.tmp)
        self.assertEqual(run.returncode, 2, run.stdout + run.stderr)
        self.assertIn("--body-file needs --base and --default-branch", run.stderr)


class TestTheForgeIsReachedThroughPath(Fixture):
    def test_the_pull_request_is_read_through_gh_on_path(self):
        item = self.add(ticket=f"{REPO}#7")
        self.stage_gh(f"Fixes {OWNER}/{REPO}#7\n")
        run = subprocess.run(
            [sys.executable, CHECKER, item, "--dir", self.mem, "--repo", self.clone,
             "--pr", "12"],
            capture_output=True, text=True, env=self.env(), cwd=self.tmp)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertIn("pr view 12 --json body,baseRefName", self.gh_calls())
        self.assertIn("repo view --json defaultBranchRef", self.gh_calls())

    def test_a_forge_naming_no_default_branch_is_a_failed_run_not_an_assumed_main(self):
        item = self.add(ticket=f"{REPO}#7")
        self.stage_gh(f"Fixes {OWNER}/{REPO}#7\n", base="main", default=None)
        run = subprocess.run(
            [sys.executable, CHECKER, item, "--dir", self.mem, "--repo", self.clone,
             "--pr", "12"],
            capture_output=True, text=True, env=self.env(), cwd=self.tmp)
        self.assertEqual(run.returncode, 2, run.stdout + run.stderr)
        self.assertIn("named no default branch", run.stderr)


class TestTheDispatchProseNamesTheCommands(unittest.TestCase):
    """F1 and F4, asked of the prose that dispatches a run.

    A skill file is code an agent executes, and the defect these two criteria
    name is in the prose: the attended path dispatched without the block or the
    reference, and the unattended path told the session to read the tracker's
    config itself. Both are checked here as text, and each pointer is required
    to resolve — a prescribed path aiming at nothing is the measured class."""

    def prose(self, *parts):
        with open(os.path.join(SKILLS, *parts), encoding="utf-8") as f:
            return f.read()

    def test_the_attended_dispatch_names_the_contract_block_and_the_reference(self):
        text = self.prose("kickoff", "SKILL.md")
        self.assertIn("tk-contract", text)
        self.assertIn("tk-ticket-ref", text)

    def test_the_unattended_dispatch_composes_the_reference_through_the_bin(self):
        text = self.prose("kickoff", "AFK.md")
        self.assertIn("tk-ticket-ref", text)
        self.assertNotIn("git config tk.tracker", text)

    def test_every_bin_the_dispatch_prose_names_is_on_disk(self):
        named = set()
        for parts in (("kickoff", "SKILL.md"), ("kickoff", "AFK.md")):
            named.update(re.findall(r"\.\./\.\./bin/(tk-[a-z-]+)", self.prose(*parts)))
        self.assertTrue(named, "the dispatch prose names no bin at all")
        for name in sorted(named):
            with self.subTest(bin=name):
                self.assertTrue(os.path.isfile(os.path.join(BIN, name)),
                                f"{name} is prescribed and is not in tk/bin")


class TestTheMergeGateStatesTheRuleTheCheckerEnforces(unittest.TestCase):
    """T226. The prose and the checker have to state ONE rule: a checker that
    enforces a set the row does not name proves the row's older, looser rule."""

    def setUp(self):
        with open(os.path.join(SKILLS, "wrap-up", "MERGE-GATE.md"), encoding="utf-8") as f:
            self.text = f.read()
        self.row = next(line for line in self.text.splitlines()
                        if line.startswith("| 5 |") and "Closure" in line)

    def test_the_verdict_row_names_the_keyword_set(self):
        for word in ("Fixes", "Closes", "Resolves"):
            self.assertIn(word, self.row)

    def test_the_verdict_row_says_the_set_is_english(self):
        """The measured defect is a Portuguese closing word, and a row that
        merely lists three examples reads as illustration, not as a closed set."""
        self.assertIn("English", self.row)

    def test_the_file_does_not_say_a_closing_keyword_the_forge_honours_counts(self):
        """The retraction applies at every site of the claim: 'any keyword the
        forge honours' is what invited the Portuguese guess in the first place."""
        flat = " ".join(self.text.split()).lower()
        self.assertNotIn("any closing keyword the forge honours counts", flat)

    def test_the_verdict_row_names_the_checker_that_asks_the_four_conditions(self):
        """The row is where a reader looks up what green means, so the command
        that answers it belongs there and not only in the section below."""
        self.assertIn("tk-closure-check", self.row)


if __name__ == "__main__":
    unittest.main()
