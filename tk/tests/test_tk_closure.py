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

    def close(self, item, how="PR #52"):
        """The item leaves the queue exactly as a package closes it — through the
        real script, so the done-log entry is the one a real close writes."""
        run = subprocess.run(
            [sys.executable, QUEUE, "done", item, "--dir", self.mem, "--how", how],
            capture_output=True, text=True, env=self.env(), cwd=self.tmp)
        self.assertEqual(run.returncode, 0, run.stderr)
        return item

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

    def check_here(self, item, body, base="main", default="main"):
        """The checker with no `--repo`, for the same reason as `read_here`."""
        return subprocess.run(
            [sys.executable, CHECKER, item, "--dir", self.mem,
             "--body-file", self.body_file(body), "--base", base,
             "--default-branch", default],
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

    def read_here(self, *argv):
        """The reader with NO `--repo` — the invocation the dispatch prose
        prescribes. The clone is then whatever the item and the cwd say it is,
        and `cwd` here is a directory that is no clone at all: the position the
        real workspace root is in, and the one the diagnosis used to misread."""
        return subprocess.run([sys.executable, READER, *argv, "--dir", self.mem],
                              capture_output=True, text=True, env=self.env(), cwd=self.tmp)

    def unreadable_repo(self, item):
        """A **Repo:** field no reader may use — `origin`, which resolves against
        whoever's cwd reads it. Written by hand because the writer refuses it."""
        self.write_queue(self.queue_text().replace(
            "**Born:**", "**Repo:** origin. **Born:**"))
        return item

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
        self.assertIn(f"git -C {self.clone} config tk.tracker <owner>/<repo>", run.stderr)

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

    def test_a_path_that_is_not_a_directory_is_refused_before_git_is_asked(self):
        """D4. `--repo` naming nothing is a defect of the invocation, and the
        refusal has to say so — `git` answers it with `cannot change to`, which
        reads as a broken git rather than as a path nobody chose."""
        item = self.add(ticket=f"{REPO}#7")
        run = subprocess.run(
            [sys.executable, READER, item, "--dir", self.mem,
             "--repo", os.path.join(self.tmp, "no-such-clone")],
            capture_output=True, text=True, env=self.env(), cwd=self.tmp)
        self.assertEqual(run.returncode, 1, run.stdout + run.stderr)
        self.assertIn("not-a-repo:", run.stderr)
        self.assertIn("`--repo`", run.stderr)

    def test_a_directory_that_is_no_clone_is_not_reported_as_a_clone_with_no_key(self):
        """D4, measured: run where there is no clone at all, the diagnosis read
        `the clone at . declares no tk.tracker` and prescribed a `git config`
        nothing there could answer. `git config` cannot tell the two apart — it
        exits 1 for both — so `rev-parse` is asked once there is no value."""
        item = self.add(ticket=f"{REPO}#7")
        run = subprocess.run(
            [sys.executable, READER, item, "--dir", self.mem, "--repo", self.tmp],
            capture_output=True, text=True, env=self.env(), cwd=self.tmp)
        self.assertEqual(run.returncode, 1, run.stdout + run.stderr)
        self.assertIn("not-a-repo:", run.stderr)
        self.assertNotIn("tracker-unset:", run.stderr)

    def test_a_config_that_could_not_be_read_is_not_an_unset_key(self):
        """D4's other half. `git config` exits 1 for a key that is not there and
        128 for a file it cannot parse; configuring a key in a file nothing can
        read back writes nothing, so the two carry different repairs."""
        with open(os.path.join(self.clone, ".git", "config"), "a", encoding="utf-8") as f:
            f.write("this is not a config line\n")
        item = self.add(ticket=f"{REPO}#7")
        run = self.read(item)
        self.assertEqual(run.returncode, 1, run.stdout + run.stderr)
        self.assertIn("config-failed:", run.stderr)
        self.assertIn("bad config line", run.stderr)
        self.assertNotIn("tracker-unset:", run.stderr)

    def test_the_clone_comes_from_the_items_own_repo_field_when_no_flag_names_one(self):
        """D4. The prescribed invocation is bare — `tk-ticket-ref <id>` — and the
        item is the only thing in it that knows which clone its code lands in."""
        item = self.add(ticket=f"{REPO}#7", extra=("--repo", self.clone))
        run = self.read_here(item)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertEqual(run.stdout, f"{OWNER}/{REPO}#7\n")

    def test_an_item_naming_no_clone_and_a_cwd_that_is_none_is_refused_naming_the_gap(self):
        item = self.add(ticket=f"{REPO}#7")
        run = self.read_here(item)
        self.assertEqual(run.returncode, 1, run.stdout + run.stderr)
        self.assertIn("not-a-repo:", run.stderr)
        self.assertIn("carries no **Repo:** field", run.stderr)

    def test_an_item_whose_repo_field_no_reader_may_use_is_told_apart_from_one_with_none(self):
        """`origin` resolves against whoever's cwd reads it, so the queue's own
        reader refuses it — and an item whose address cannot be read is not an
        item that never named one. The two ask different things of whoever has
        to name the clone."""
        item = self.unreadable_repo(self.add(ticket=f"{REPO}#7"))
        run = self.read_here(item)
        self.assertEqual(run.returncode, 1, run.stdout + run.stderr)
        self.assertIn("not-a-repo:", run.stderr)
        self.assertIn("carries a **Repo:** no reader may use", run.stderr)

    def test_an_id_no_open_item_carries_is_a_failed_run_not_a_refusal(self):
        self.add(ticket=f"{REPO}#7")
        run = self.read("T404")
        self.assertEqual(run.returncode, 2, run.stdout + run.stderr)
        self.assertIn("T404", run.stderr)

    def test_an_id_that_left_the_queue_is_named_as_closed_not_as_never_seen(self):
        """The four cases of a missing id are not one answer, and this bin used to
        give the flat one — `no open item carries the id`, which reads as "never
        existed" and sends the reader to a list the item has already left."""
        item = self.close(self.add(ticket=f"{REPO}#7"))
        run = self.read(item)
        self.assertEqual(run.returncode, 2, run.stdout + run.stderr)
        self.assertIn("closed:", run.stderr)
        self.assertIn("done-log.md", run.stderr)
        self.assertNotIn("no open item", run.stderr)


class TestVerdictFiveOnAnItemThatIsNotOpen(Fixture):
    """T338 — every item of an unattended package is closed by the time the merge
    gate asks verdict 5 about it: `AFK.md` step 5 opens the pull request at stage 6
    and closes the item at stage 7, and the gate runs after both. The checker
    answered the whole package by exiting with no row at all."""

    def body(self):
        return f"What this slice does.\n\nFixes {OWNER}/{REPO}#7\n"

    def test_a_closed_item_is_a_red_verdict_naming_the_log_it_left_for(self):
        item = self.close(self.add(ticket=f"{REPO}#7"))
        run = self.check(item, self.body())
        self.assertNotEqual(run.returncode, 0,
                            "verdict 5 answered nothing and exited like a green run:\n"
                            + run.stdout + run.stderr)
        self.assertIn("ticket  FAILED  closed:", run.stdout,
                      "the run left no row — a reader of the exit code alone has "
                      "nothing to read, and the digest quotes nothing")
        self.assertIn("done-log.md", run.stdout,
                      "the checker does not say where the item went")
        self.assertIn(f"verdict-5: RED for {item}", run.stdout)

    def test_the_red_row_names_the_ordering_that_produced_it(self):
        """A refusal with no remedy is a wall. The remedy here is an order, not a
        flag: the body exists at stage 6 and the item closes at stage 7."""
        item = self.close(self.add(ticket=f"{REPO}#7"))
        run = self.check(item, self.body())
        self.assertIn("BEFORE the close", run.stdout)
        self.assertIn("stage 6", run.stdout)

    def test_an_id_the_queue_never_allocated_is_red_under_its_own_code(self):
        """The two ways an id is not open are told apart, so the reader is not sent
        to the done-log for an item that was never there."""
        self.add(ticket=f"{REPO}#7")
        run = self.check("T404", self.body())
        self.assertNotEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertIn("ticket  FAILED  not-open:", run.stdout)
        self.assertIn("never allocated", run.stdout)
        self.assertNotIn("done-log.md", run.stdout)


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
        for name in ("keyword", "number", "owner", "extras", "base"):
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

    def test_a_cited_repository_the_tracker_does_not_name_is_red(self):
        """D1. The reader REFUSES this item — `Fictional-Owner/tracker-repo` says
        who owns `tracker-repo` and nothing about who owns `other-repo` — while a
        hand-written `Fixes Fictional-Owner/other-repo#9` passed every condition,
        because the owner was checked against the tracker, the repository against
        the item, and the PAIR against nothing at all."""
        item = self.add(ticket="other-repo#9")
        run = self.check(item, self.body(f"{OWNER}/other-repo#9"))
        self.assertEqual(run.returncode, 1, run.stdout + run.stderr)
        self.assertIn("repo-mismatch:", run.stdout)
        self.assertIn(f"verdict-5: RED for {item} — ticket", run.stdout)

    def test_a_closing_line_for_another_repository_does_not_count_as_this_ticket(self):
        """The same pair, read from the body's end: the number matches and the
        repository does not, so the line closes an issue of somebody else's
        repository — and it is the repository half that says so."""
        item = self.add(ticket=f"{REPO}#7")
        run = self.check(item, self.body(f"{OWNER}/other-repo#7"))
        self.assertEqual(run.returncode, 1, run.stdout)
        self.assertRegex(run.stdout, r"(?m)^number\s+FAILED\s")
        self.assertRegex(run.stdout, r"(?m)^extras\s+FAILED\s")

    def test_a_second_closing_line_closes_a_second_ticket_and_is_red(self):
        """D2. The forge honours EVERY keyword and reference in a body, not the
        first one, so an extra closing line closes an extra ticket on merge."""
        item = self.add(ticket=f"{REPO}#7")
        run = self.check(item, f"Fixes {OWNER}/{REPO}#7\n\nCloses Other-Owner/other-repo#8\n")
        self.assertEqual(run.returncode, 1, run.stdout)
        self.assertRegex(run.stdout, r"(?m)^extras\s+FAILED\s")
        self.assertIn("Other-Owner/other-repo#8", run.stdout)
        self.assertIn(f"verdict-5: RED for {item} — extras", run.stdout)

    def test_the_same_two_closing_lines_give_the_same_verdict_in_either_order(self):
        """D2, measured: reading `honoured[0]` asked which line came FIRST, so
        one order was green on the owner and the other red — of one body."""
        item = self.add(ticket=f"{REPO}#7")
        right = f"Fixes {OWNER}/{REPO}#7"
        stray = "Closes Other-Owner/other-repo#8"
        first = self.check(item, f"{right}\n\n{stray}\n")
        second = self.check(item, f"{stray}\n\n{right}\n")
        self.assertEqual(first.returncode, second.returncode, first.stdout + second.stdout)
        self.assertEqual(
            [line.split()[:2] for line in first.stdout.splitlines() if line[:1].isalpha()],
            [line.split()[:2] for line in second.stdout.splitlines() if line[:1].isalpha()],
            first.stdout + "\n---\n" + second.stdout)
        self.assertIn(f"verdict-5: RED for {item} — extras", first.stdout)

    def test_a_word_the_forge_ignores_still_gets_the_other_conditions_answered(self):
        """D3. `Fecha <the right reference>` is wrong in exactly ONE way, and the
        keyword-red path used to return that one row and stop — against the
        file's own rule that every condition is reported, green or red."""
        item = self.add(ticket=f"{REPO}#7")
        run = self.check(item, self.body(keyword="Fecha"))
        self.assertEqual(run.returncode, 1, run.stdout)
        self.assertRegex(run.stdout, r"(?m)^keyword\s+FAILED\s")
        for name in ("number", "owner", "extras", "base"):
            with self.subTest(row=name):
                self.assertRegex(run.stdout, rf"(?m)^{name}\s+ok\s")
        self.assertIn(f"verdict-5: RED for {item} — keyword", run.stdout)

    def test_a_colon_after_the_keyword_is_a_form_the_forge_honours(self):
        """The forge's own documentation says a keyword may be followed by a
        colon, so `Fixes: <ref>` closes the ticket — and a pattern demanding
        whitespace right after the word reports it as no closing line at all."""
        item = self.add(ticket=f"{REPO}#7")
        run = self.check(item, f"What this slice does.\n\nFixes: {OWNER}/{REPO}#7\n")
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertIn(f"verdict-5: GREEN for {item}", run.stdout)

    def test_a_word_merely_ending_in_a_keyword_is_not_one(self):
        """`Not-fixes <ref>` closes nothing: the forge honours the keyword, not a
        word that ends in it. Read as a closing line it is a GREEN verdict on a
        body that closes nothing at all."""
        item = self.add(ticket=f"{REPO}#7")
        run = self.check(item, f"What this slice does.\n\nNot-fixes {OWNER}/{REPO}#7\n")
        self.assertEqual(run.returncode, 1, run.stdout)
        self.assertRegex(run.stdout, r"(?m)^keyword\s+FAILED\s")
        self.assertIn("no closing line in the body", run.stdout)

    def test_a_number_spelled_with_leading_zeros_is_not_the_form_that_resolves(self):
        """`#0007` is not a form the forge's `#N` syntax resolves — the queue says
        so where it drops the zeros on the way in — so a body spelling it that
        way fires at nothing, and a comparison through int() calls it the right
        ticket."""
        item = self.add(ticket=f"{REPO}#7")
        run = self.check(item, self.body(f"{OWNER}/{REPO}#0007"))
        self.assertEqual(run.returncode, 1, run.stdout)
        self.assertRegex(run.stdout, r"(?m)^number\s+FAILED\s")

    def test_a_re_cased_slug_resolves_to_the_same_repository_and_is_green(self):
        """Owner and repository are case-insensitive to look up on the forge, so
        two casings ARE one reference: refusing one would be a red verdict on a
        line that closes the ticket."""
        item = self.add(ticket=f"{REPO}#7")
        run = self.check(item, f"What this slice does.\n\nfixes fictional-owner/TRACKER-REPO#7\n")
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertIn(f"verdict-5: GREEN for {item}", run.stdout)

    def test_a_bare_reference_is_red_on_owner_and_not_on_the_number(self):
        """`Fixes #7` names this item's number, and it is the OWNER half that is
        missing: reporting the number wrong as well would hand a session two
        repairs for one defect."""
        item = self.add(ticket=f"{REPO}#7")
        run = self.check(item, "What this slice does.\n\nFixes #7\n")
        self.assertEqual(run.returncode, 1, run.stdout)
        self.assertRegex(run.stdout, r"(?m)^number\s+ok\s")
        self.assertRegex(run.stdout, r"(?m)^owner\s+FAILED\s")
        self.assertIn("no owner half", run.stdout)

    def test_the_clone_comes_from_the_items_repo_field_here_too(self):
        """The checker resolves the clone the same way the reader does, through
        the same function: `--repo`, then the item's **Repo:**, then the cwd."""
        item = self.add(ticket=f"{REPO}#7", extra=("--repo", self.clone))
        run = self.check_here(item, self.body())
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertIn(f"verdict-5: GREEN for {item}", run.stdout)

    def test_a_failed_run_is_spoken_under_the_command_that_made_it(self):
        """The checker loads the reader as a MODULE, so a message the reader
        writes down as its own name would tell a session that a command failed
        which never ran."""
        item = self.add(ticket=f"{REPO}#7")
        run = subprocess.run(
            [sys.executable, CHECKER, item, "--dir", os.path.join(self.tmp, "no-queue"),
             "--repo", self.clone, "--body-file", self.body_file(self.body()),
             "--base", "main", "--default-branch", "main"],
            capture_output=True, text=True, env=self.env(), cwd=self.tmp)
        self.assertEqual(run.returncode, 2, run.stdout + run.stderr)
        self.assertIn("tk-closure-check: queue dir not found", run.stderr)
        self.assertNotIn("tk-ticket-ref:", run.stderr)

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

    def reference(self, name):
        with open(os.path.join(SKILLS, os.pardir, "reference", name), encoding="utf-8") as f:
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
        texts = [self.prose("kickoff", "SKILL.md"), self.prose("kickoff", "AFK.md"),
                 self.reference("subagent-policy.md")]
        named = set()
        for text in texts:
            named.update(re.findall(r"(?:\.\./)+bin/(tk-[a-z-]+)", text))
        self.assertTrue(named, "the dispatch prose names no bin at all")
        for name in sorted(named):
            with self.subTest(bin=name):
                self.assertTrue(os.path.isfile(os.path.join(BIN, name)),
                                f"{name} is prescribed and is not in tk/bin")


class TestTheMergeGateStatesTheRuleTheCheckerEnforces(unittest.TestCase):
    """T226. The prose and the checker have to state ONE rule: a checker that
    enforces a set the row does not name proves the row's older, looser rule."""

    def setUp(self):
        with open(os.path.join(SKILLS, "merge-gate", "SKILL.md"), encoding="utf-8") as f:
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

    def test_the_verdict_row_names_the_checker_that_asks_the_conditions(self):
        """The row is where a reader looks up what green means, so the command
        that answers it belongs there and not only in the section below."""
        self.assertIn("tk-closure-check", self.row)

    def test_the_verdict_row_states_the_other_closing_line_condition(self):
        """The forge honours every keyword in a body, so a second closing line
        closes a second ticket. The row is what a session reads instead of the
        checker's help, and a row silent on that condition proves the older,
        four-condition rule the checker has already left behind."""
        self.assertIn("OTHER closing line", self.row)


class TestVerdictFiveIsAskedWhileTheItemIsStillOpen(unittest.TestCase):
    """The ordering the checker's own remedy names, asserted where it is run.

    An unattended package closes each lane item at step 5 stage 7, and the merge
    gate asks verdict 5 after that — so the checker meets an item whose
    **Ticket:** field left the queue with it, and answers red for every item of
    the package. `merge-gate/SKILL.md` turns any red into a merge that is not
    offered, so the gate could never pass a lane. The prose has to run the check
    at stage 6, while the item is still open, and carry its answer forward."""

    def setUp(self):
        with open(os.path.join(SKILLS, "kickoff", "AFK.md"), encoding="utf-8") as f:
            self.text = f.read()
        self.step = self.text.split("## 5. Verify every delivery")[1].split("\n## 6.")[0]

    def test_the_step_that_verifies_is_still_there(self):
        self.assertIn("## 5. Verify every delivery", self.text,
                      "AFK.md has no step 5 — every assertion below reads a section that "
                      "is gone")

    def test_the_close_stage_runs_the_checker(self):
        self.assertIn("tk-closure-check", self.step,
                      "step 5 never runs the checker, so verdict 5 is first asked by the "
                      "gate — after stage 7 has closed the item")

    def test_the_check_is_asked_before_the_item_closes(self):
        """Position is the whole rule: the same command after the `done` reads a
        closed item and is red by construction."""
        check = self.step.index("tk-closure-check")
        close = self.step.index("**Close the item last**")
        self.assertLess(check, close,
                        "the checker is prescribed after the close, which is the ordering "
                        "the defect is made of")

    def test_the_step_says_why_the_order_matters(self):
        self.assertIn("**Ticket:** field has left the queue", self.step,
                      "the stage orders the check and does not say what breaks without it, "
                      "so a session reordering the stages loses the reason")

    def test_the_completeness_check_counts_the_verdict(self):
        """A stage nothing checks is a stage a tight package skips."""
        done = self.step.split("**Done when:**")[1]
        self.assertIn("verdict 5 was asked of each", done,
                      "step 5's `Done when` does not count the verdict, so the stage can "
                      "be skipped with the check still green")


if __name__ == "__main__":
    unittest.main()
