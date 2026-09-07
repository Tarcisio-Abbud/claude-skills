#!/usr/bin/env python3
"""Regression suite for `tk-hygiene` (../bin/tk-hygiene).

Run: python3 -m unittest discover -s tk/tests   (stdlib only, no deps)

Every test here is proved by MUTATION: the defect is put back in the source and
the test must fail. `mutations_hygiene.py` in this directory replays each one
mechanically.

THE SUITE NEVER TOUCHES THE NETWORK. `tk-hygiene` resolves the forge CLI through
PATH, and every run below puts a fake `gh` on the front of it — one that answers
from a table on disk and records the calls it received. A test asserting that
record is what proves the shadowing works: if the real `gh` were reached, the
record would be empty and the test would fall rather than quietly go to GitHub.

REPOSITORY NAMES ARE FICTIONAL. This repo is written as if public and the bin
carries no repo name of its own, so the fixtures must not smuggle one back in
through the tests.

THE REPORT NAMES A REPO BY ITS PATH, never by its `owner/repo` slug — one of the
repos the roster reaches is the private tracker's own clone. So the tests below
assert the slug where it is legitimately visible (the argv the fake `gh` records)
and assert the PATH where the report is concerned.

THE BIN IS RUN FROM A COPY, never from the checkout it lives in. `tk-hygiene`
reaches the repository it is INSTALLED in — that is the second source of repos,
the one that finds a clone with no queue — so running the checkout's own copy
would audit this repository and PRUNE ITS BRANCHES while the suite runs. The copy
goes under the test's temporary tree, which is not a repository, so that source is
empty for every test but the one that stages a repository around a copy of its own.

The path encoding is written out LITERALLY in `encode`, for the reason the roster
suite gives beside its own copy: a test computing the expected name with the
function under test would agree with any mutation of it.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
BIN_DIR = os.path.normpath(os.path.join(HERE, os.pardir, "bin"))

HEADER = """---
name: next-steps
description: fixture
metadata:
  type: project
---

# Next steps

"""

# the fake forge CLI. It answers `gh api repos/<owner>/<repo> --jq ...` from a
# file per slug, appends every call to a log, and fails the way `gh` fails when
# the slug has no file — which is how "the forge could not be reached" is staged
FAKE_GH = r"""#!/usr/bin/env python3
import os, sys
table = os.environ["FAKE_GH_TABLE"]
with open(os.path.join(table, "calls"), "a", encoding="utf-8") as f:
    f.write(" ".join(sys.argv[1:]) + "\n")
slug = ""
for arg in sys.argv[1:]:
    if arg.startswith("repos/"):
        slug = arg[len("repos/"):]
answer = os.path.join(table, slug.replace("/", "__"))
if not os.path.isfile(answer):
    sys.stderr.write("could not resolve to a Repository with the name '%s'.\n" % slug)
    sys.exit(1)
with open(answer, encoding="utf-8") as f:
    sys.stdout.write(f.read())
"""


def encode(path):
    """The queue directory name for `path` — tk-queue's rule, written out."""
    return re.sub(r"[^A-Za-z0-9-]", "-", path)


class HygieneTest(unittest.TestCase):
    def setUp(self):
        self.tmp = os.path.realpath(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.home = os.path.join(self.tmp, "home")
        self.projects = os.path.join(self.home, ".claude", "projects")
        os.makedirs(self.projects)
        self.table = os.path.join(self.tmp, "forge")
        os.makedirs(self.table)
        self.bin = os.path.join(self.tmp, "bin")
        os.makedirs(self.bin)
        gh = os.path.join(self.bin, "gh")
        with open(gh, "w", encoding="utf-8") as f:
            f.write(FAKE_GH)
        os.chmod(gh, 0o755)
        self.hygiene = self.install(os.path.join(self.tmp, "tk", "bin"))

    def install(self, where):
        """Copy `tk/bin` to `where` and answer the path of the copied bin.

        The whole directory, because `tk-hygiene` loads `tk-roster` and
        `tk_site.py` from beside itself — a copy of the one file would import the
        checkout's siblings and resolve its own repository back to this one.
        """
        shutil.copytree(BIN_DIR, where, ignore=shutil.ignore_patterns("__pycache__"))
        return os.path.join(where, "tk-hygiene")

    # --- fixtures ----------------------------------------------------------
    def forge(self, slug, value):
        """What the fake `gh` answers for `slug`. Unlisted slugs fail, as gh does."""
        with open(os.path.join(self.table, slug.replace("/", "__")), "w",
                  encoding="utf-8") as f:
            f.write(value + "\n")

    def calls(self):
        path = os.path.join(self.table, "calls")
        if not os.path.isfile(path):
            return []
        with open(path, encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]

    def run_git(self, *args, check=True):
        env = dict(os.environ,
                   GIT_AUTHOR_NAME="fixture", GIT_AUTHOR_EMAIL="fixture@example.invalid",
                   GIT_COMMITTER_NAME="fixture", GIT_COMMITTER_EMAIL="fixture@example.invalid",
                   HOME=self.home, GIT_CONFIG_NOSYSTEM="1")
        p = subprocess.run(("git", *args), env=env, capture_output=True, text=True)
        if check:
            self.assertEqual(p.returncode, 0, f"git {args}: {p.stderr}")
        return p

    def git(self, repo, *args, check=True):
        env = dict(os.environ,
                   GIT_AUTHOR_NAME="fixture", GIT_AUTHOR_EMAIL="fixture@example.invalid",
                   GIT_COMMITTER_NAME="fixture", GIT_COMMITTER_EMAIL="fixture@example.invalid",
                   HOME=self.home, GIT_CONFIG_NOSYSTEM="1")
        p = subprocess.run(("git", "-C", repo, *args), env=env,
                           capture_output=True, text=True)
        if check:
            self.assertEqual(p.returncode, 0, f"git {args}: {p.stderr}")
        return p

    def commit(self, repo, message):
        with open(os.path.join(repo, message.replace(" ", "-")), "w",
                  encoding="utf-8") as f:
            f.write(message)
        self.git(repo, "add", "-A")
        self.git(repo, "commit", "-m", message)
        return self.git(repo, "rev-parse", "HEAD").stdout.strip()

    def repo(self, name, origin="https://github.com/example-owner/example-repo.git",
             default="main", queue=True):
        """A git repository under the tmp tree, with a queue so the roster finds it.

        `origin` is a URL, never a live remote: nothing here fetches, and the
        remote-tracking refs below are written by hand so that a branch's upstream
        can be made to exist or to be `[gone]` at will.
        """
        path = os.path.join(self.tmp, name)
        os.makedirs(path)
        self.git(path, "init", "-q", "-b", default)
        if origin:
            self.git(path, "remote", "add", "origin", origin)
        head = self.commit(path, "root commit")
        if origin:
            self.git(path, "update-ref", f"refs/remotes/origin/{default}", head)
            self.git(path, "symbolic-ref", "refs/remotes/origin/HEAD",
                     f"refs/remotes/origin/{default}")
            self.track(path, default, default)
        if queue:
            self.queue(path)
        return path

    def track(self, repo, branch, upstream_name):
        """Point `branch` at `origin/<upstream_name>` WITHOUT requiring it to exist.

        Written through config rather than `--set-upstream-to`, which refuses an
        absent ref — and an absent ref is exactly the `[gone]` state under test.
        """
        self.git(repo, "config", f"branch.{branch}.remote", "origin")
        self.git(repo, "config", f"branch.{branch}.merge", f"refs/heads/{upstream_name}")

    def queue(self, path):
        """The queue file that makes the roster sweep `path` as a project."""
        memdir = os.path.join(self.projects, encode(path), "memory")
        os.makedirs(memdir, exist_ok=True)
        with open(os.path.join(memdir, "next-steps.md"), "w", encoding="utf-8") as f:
            f.write(HEADER)

    def three_branches(self, repo):
        """The three branches the acceptance criterion names, on one repo.

        Only `merged-gone` may be pruned: its remote is gone AND it carries no
        commit outside the default. `unmerged-gone` clears the first guard and is
        held by the second; `local-only` never had an upstream at all.
        """
        head = self.git(repo, "rev-parse", "HEAD").stdout.strip()
        self.git(repo, "branch", "merged-gone", head)
        self.track(repo, "merged-gone", "merged-gone")

        self.git(repo, "branch", "unmerged-gone", head)
        self.track(repo, "unmerged-gone", "unmerged-gone")
        self.git(repo, "checkout", "-q", "unmerged-gone")
        self.commit(repo, "work of its own")
        self.git(repo, "checkout", "-q", "main")

        self.git(repo, "branch", "local-only", head)

    def squashed(self, repo, name="squashed-gone"):
        """A branch whose COMMITS are outside the default and whose CONTENT is in it.

        The shape a squash merge leaves behind: the branch's two commits were
        replayed on the default as one, so no commit of the branch is an ancestor
        of it, and the default then moved on — which is why comparing the two TIPS
        would answer that the branch still differs.
        """
        head = self.git(repo, "rev-parse", "HEAD").stdout.strip()
        self.git(repo, "checkout", "-q", "-b", name, head)
        self.commit(repo, "half of the work")
        self.commit(repo, "the other half")
        self.git(repo, "checkout", "-q", "main")
        self.git(repo, "merge", "-q", "--squash", name)
        self.git(repo, "commit", "-m", f"squash of {name}")
        self.commit(repo, "the default moves on")
        self.track(repo, name, name)
        self.advance_origin(repo)
        return name

    def conflicting(self, repo, name="conflicting-gone"):
        """A branch that cannot be merged into the default at all.

        Both sides added the same path with different content, which is the one
        answer the content test must read as `keep`: a merge that does not happen
        says nothing about where the branch's work is.
        """
        head = self.git(repo, "rev-parse", "HEAD").stdout.strip()
        self.git(repo, "checkout", "-q", "-b", name, head)
        self.write(repo, "contested", "theirs")
        self.git(repo, "checkout", "-q", "main")
        self.write(repo, "contested", "ours")
        self.track(repo, name, name)
        self.advance_origin(repo)
        return name

    def unrelated(self, repo, name="unrelated-gone"):
        """A branch with no commit in common with the default.

        `merge-tree` REFUSES that merge instead of conflicting over it, and the
        two are not one fact: a run that never happened says nothing about a
        conflict. Fetched from a repository of its own, because a history with no
        common commit cannot be grown inside this one.
        """
        other = os.path.join(self.tmp, name + "-elsewhere")
        os.makedirs(other)
        self.git(other, "init", "-q", "-b", "main")
        self.commit(other, "a history of its own")
        self.git(repo, "fetch", "-q", other, f"main:{name}")
        self.track(repo, name, name)
        return name

    def write(self, repo, path, text):
        """One file, committed on whatever branch is checked out."""
        with open(os.path.join(repo, path), "w", encoding="utf-8") as f:
            f.write(text + "\n")
        self.git(repo, "add", "-A")
        self.git(repo, "commit", "-m", f"{path}: {text}")

    def advance_origin(self, repo, default="main"):
        """Move `origin/<default>` up to the local one.

        The prune measures against the REMOTE's default branch, and these fixtures
        commit locally: left where `repo()` pinned it, the remote default would be
        the root commit and every branch would carry content it does not have.
        """
        head = self.git(repo, "rev-parse", default).stdout.strip()
        self.git(repo, "update-ref", f"refs/remotes/origin/{default}", head)

    def lane_repo(self, name="lane"):
        """A repository whose `origin` is a BARE REPO ON DISK, with main pushed.

        Real pushes, a real `ls-remote` and a real delete, with no network at
        all: the remote step's own act is `git push --delete`, and a fake remote
        would prove the argv it was called with rather than the deletion.
        """
        origin = os.path.join(self.tmp, name + "-origin.git")
        self.run_git("init", "-q", "--bare", "-b", "main", origin)
        path = os.path.join(self.tmp, name)
        os.makedirs(path)
        self.git(path, "init", "-q", "-b", "main")
        self.git(path, "remote", "add", "origin", origin)
        self.commit(path, "root commit")
        self.git(path, "push", "-q", "-u", "origin", "main")
        self.git(path, "remote", "set-head", "origin", "main")
        self.queue(path)
        return path, origin

    def pushed_branch(self, repo, name, merged):
        """A branch pushed to the remote, its work squashed into main or not.

        `merged=True` is the shape T342 measured: the lane's pull request merged,
        the forge deleted the PR's own head, and this branch — which was never any
        PR's head — stayed behind on the remote.
        """
        self.git(repo, "checkout", "-q", "-b", name, "main")
        self.commit(repo, "work of " + name.replace("/", "-"))
        self.git(repo, "push", "-q", "-u", "origin", name)
        self.git(repo, "checkout", "-q", "main")
        if merged:
            self.git(repo, "merge", "-q", "--squash", name)
            self.git(repo, "commit", "-m", "squash of " + name)
            self.git(repo, "push", "-q", "origin", "main")
        self.git(repo, "fetch", "-q", "origin")
        return name

    def push_from_elsewhere(self, origin, branch):
        """Another machine adds a commit to `branch` after this repo's last fetch."""
        other = os.path.join(self.tmp, "elsewhere")
        self.run_git("clone", "-q", origin, other)
        self.git(other, "checkout", "-q", branch)
        self.commit(other, "a commit pushed after the fetch")
        self.git(other, "push", "-q", "origin", branch)

    def remote_branches(self, repo):
        out = self.git(repo, "ls-remote", "--heads", "origin").stdout
        return sorted(line.split("refs/heads/")[-1] for line in out.splitlines()
                      if "refs/heads/" in line)

    # --- driving the bin ---------------------------------------------------
    def run_hygiene(self, *argv, hygiene=None):
        # GIT_CEILING_DIRECTORIES is the second lock on "the suite never reaches
        # the checkout": even were the temporary tree carved out of a repository
        # one day, git may not walk up out of it looking for one
        env = dict(os.environ,
                   HOME=self.home,
                   PATH=self.bin + os.pathsep + os.environ["PATH"],
                   GIT_CEILING_DIRECTORIES=self.tmp,
                   FAKE_GH_TABLE=self.table)
        env.pop("USERPROFILE", None)
        return subprocess.run([sys.executable, hygiene or self.hygiene, *argv], env=env,
                              capture_output=True, text=True, timeout=120)

    def branch_names(self, repo):
        out = self.git(repo, "for-each-ref", "--format=%(refname:short)", "refs/heads")
        return sorted(out.stdout.split())

    def forge_lines(self, out):
        """The lines under the forge heading — one per repository, or a defect."""
        lines, keeping = [], False
        for line in out.splitlines():
            if line.startswith("## "):
                keeping = line.startswith("## forge")
            elif keeping and line.strip():
                lines.append(line.strip())
        return lines

    def worktree(self, repo, name):
        """A second working tree over the SAME branches, with a queue of its own."""
        tree = os.path.join(self.tmp, name)
        self.git(repo, "worktree", "add", "-q", "-b", name, tree)
        self.queue(tree)
        return tree

    def branch_lines(self, out, repo, section="## local branches"):
        """The report lines under `repo`'s heading in one of the branch blocks.

        Scoped to a SECTION because both blocks head their rows with the same
        repository path: unscoped, an assertion about the local block would be
        satisfied by a line in the remote one.
        """
        lines, keeping, inside = [], False, False
        for line in out.splitlines():
            if line.startswith("## "):
                inside, keeping = line.startswith(section), False
            elif not inside:
                continue
            elif line and not line.startswith(" "):
                keeping = line.strip() == repo
            elif keeping and line.strip():
                lines.append(line.strip())
        return lines


# --- the forge audit: green and red are literals, and so is the exit code ---

class TestForgeAudit(HygieneTest):
    def test_a_repo_with_the_box_on_is_green_in_the_literal_and_exits_0(self):
        self.repo("green", origin="https://github.com/example-owner/green-repo.git")
        self.forge("example-owner/green-repo", "true")
        r = self.run_hygiene()
        self.assertIn("delete_branch_on_merge=true", r.stdout)
        self.assertNotIn("delete_branch_on_merge=false", r.stdout)
        self.assertIn(os.path.join(self.tmp, "green"), r.stdout)
        self.assertNotIn("example-owner/green-repo", r.stdout)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_a_repo_with_the_box_off_is_red_in_the_literal_and_exits_1(self):
        self.repo("red", origin="https://github.com/example-owner/red-repo.git")
        self.forge("example-owner/red-repo", "false")
        r = self.run_hygiene()
        self.assertIn("delete_branch_on_merge=false", r.stdout)
        self.assertNotIn("delete_branch_on_merge=true", r.stdout)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)

    def test_a_forge_that_answers_an_error_is_unknown_and_exits_3(self):
        # no table entry for the slug: the fake gh fails the way gh does
        self.repo("gone", origin="https://github.com/example-owner/absent-repo.git")
        r = self.run_hygiene()
        self.assertIn("delete_branch_on_merge=unknown", r.stdout)
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)

    def test_a_forge_answering_neither_true_nor_false_is_unknown(self):
        self.repo("odd", origin="https://github.com/example-owner/odd-repo.git")
        self.forge("example-owner/odd-repo", "null")
        r = self.run_hygiene()
        self.assertIn("delete_branch_on_merge=unknown", r.stdout)
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)

    def test_a_red_repo_outranks_an_unknown_one_in_the_exit_code(self):
        self.repo("red", origin="https://github.com/example-owner/red-repo.git")
        self.repo("gone", origin="https://github.com/example-owner/absent-repo.git")
        self.forge("example-owner/red-repo", "false")
        r = self.run_hygiene()
        self.assertIn("delete_branch_on_merge=false", r.stdout)
        self.assertIn("delete_branch_on_merge=unknown", r.stdout)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)

    def test_a_repo_with_no_github_remote_is_not_a_failed_audit(self):
        # local-only repo: the audit has nothing to say, which is not the same as
        # having failed to reach the forge — so it must not colour the exit code
        self.repo("local", origin=None)
        r = self.run_hygiene()
        self.assertIn("no-github-remote", r.stdout)
        self.assertNotIn("delete_branch_on_merge=unknown", r.stdout)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_the_slug_is_read_from_an_ssh_remote_too(self):
        # the slug is asserted where it is legitimately visible — the argv the
        # forge was called with — because the report names the repo by its path
        self.repo("ssh", origin="git@github.com:example-owner/ssh-repo.git")
        self.forge("example-owner/ssh-repo", "true")
        r = self.run_hygiene()
        self.assertTrue(any("repos/example-owner/ssh-repo" in c for c in self.calls()),
                        self.calls())
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_a_repo_hosted_elsewhere_is_not_reported_as_a_github_repo(self):
        self.repo("elsewhere", origin="https://gitlab.example/example-owner/x.git")
        r = self.run_hygiene()
        self.assertIn("no-github-remote", r.stdout)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


# --- never touching the network --------------------------------------------

class TestTheReportNamesRepositoriesByPath(HygieneTest):
    def test_the_slug_never_reaches_the_report(self):
        # one of the repos the roster reaches is the private tracker's own clone,
        # and the kickoff is told to quote this report into its own
        path = self.repo("clone",
                         origin="https://github.com/secret-owner/secret-repo.git")
        self.forge("secret-owner/secret-repo", "true")
        r = self.run_hygiene()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("secret-owner", r.stdout)
        self.assertNotIn("secret-repo", r.stdout)
        self.assertIn(path, r.stdout)


class TestNoNetwork(HygieneTest):
    def test_the_forge_cli_is_resolved_through_path_so_the_fake_is_reached(self):
        self.repo("green", origin="https://github.com/example-owner/green-repo.git")
        self.forge("example-owner/green-repo", "true")
        r = self.run_hygiene()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(any("repos/example-owner/green-repo" in c for c in self.calls()),
                        f"the fake gh was never called: {self.calls()}")

    def test_one_slug_is_asked_of_the_forge_once(self):
        # two repositories, one slug: the audit asks about a slug once however
        # many trees name it, so a machine with ten clones is not ten API calls
        self.repo("clone-a", origin="https://github.com/example-owner/green-repo.git")
        self.repo("clone-b", origin="https://github.com/example-owner/green-repo.git")
        self.forge("example-owner/green-repo", "true")
        r = self.run_hygiene()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        asked = [c for c in self.calls() if "repos/example-owner/green-repo" in c]
        self.assertEqual(len(asked), 1, asked)


class TestOneRepoPerBranchSet(HygieneTest):
    def test_a_worktree_is_not_a_second_repository(self):
        # a worktree is a second working tree over ONE set of branches. Counted
        # twice, the repo is reported twice and its branches are walked twice —
        # the second walk over a branch the first one already deleted
        repo = self.repo("main-clone",
                         origin="https://github.com/example-owner/green-repo.git")
        self.forge("example-owner/green-repo", "true")
        self.worktree(repo, "side")
        r = self.run_hygiene()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        # ONE line in the forge block: the worktree must not appear as a repo of
        # its own, and counting lines is what says so — matching the clone's path
        # would still find exactly one hit with the worktree listed beside it
        lines = self.forge_lines(r.stdout)
        self.assertEqual(len(lines), 1, lines)
        self.assertIn(repo, lines[0])


# --- the prune: which of the three branches goes ---------------------------

class TestPrune(HygieneTest):
    def test_only_the_merged_gone_branch_is_pruned(self):
        repo = self.repo("three", origin="https://github.com/example-owner/three.git")
        self.forge("example-owner/three", "true")
        self.three_branches(repo)
        self.assertEqual(self.branch_names(repo),
                         ["local-only", "main", "merged-gone", "unmerged-gone"])

        r = self.run_hygiene()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.branch_names(repo), ["local-only", "main", "unmerged-gone"])

        lines = self.branch_lines(r.stdout, repo)
        self.assertTrue(any(l.startswith("pruned") and "merged-gone" in l for l in lines),
                        lines)
        self.assertTrue(any(l.startswith("kept") and "unmerged-gone" in l for l in lines),
                        lines)
        self.assertTrue(any(l.startswith("kept") and "local-only" in l
                            and "no upstream" in l for l in lines), lines)
        self.assertTrue(any(l.startswith("kept") and "unmerged-gone" in l
                            and "outside" in l for l in lines), lines)

    def test_a_branch_whose_upstream_is_alive_is_left_alone_and_unreported(self):
        repo = self.repo("alive", origin="https://github.com/example-owner/alive.git")
        self.forge("example-owner/alive", "true")
        head = self.git(repo, "rev-parse", "HEAD").stdout.strip()
        self.git(repo, "branch", "pushed", head)
        self.track(repo, "pushed", "pushed")
        self.git(repo, "update-ref", "refs/remotes/origin/pushed", head)

        r = self.run_hygiene()
        self.assertIn("pushed", self.branch_names(repo))
        self.assertNotIn("pushed", r.stdout)

    def test_the_default_branch_is_never_reported_as_residue(self):
        # a repo that was never pushed anywhere: its default branch has no
        # upstream, and saying so every kickoff teaches the reader to skip the block
        repo = self.repo("local", origin=None)
        r = self.run_hygiene()
        self.assertIn("main", self.branch_names(repo))
        self.assertNotIn("main", self.branch_lines(r.stdout, repo))
        self.assertEqual(self.branch_lines(r.stdout, repo), [])

    def test_without_a_default_branch_to_measure_against_nothing_is_pruned(self):
        repo = self.repo("three", origin="https://github.com/example-owner/three.git")
        self.forge("example-owner/three", "true")
        self.three_branches(repo)
        # the remote's answer and both fallbacks gone: there is no anchor left,
        # and an un-anchored comparison is not a safer one
        self.git(repo, "symbolic-ref", "-d", "refs/remotes/origin/HEAD")
        self.git(repo, "update-ref", "-d", "refs/remotes/origin/main")
        self.git(repo, "branch", "-m", "main", "trunk")

        r = self.run_hygiene()
        self.assertIn("merged-gone", self.branch_names(repo))
        self.assertIn("no default branch", r.stdout)

    def test_a_branch_checked_out_in_another_worktree_survives_the_refusal(self):
        repo = self.repo("busy", origin="https://github.com/example-owner/busy.git")
        self.forge("example-owner/busy", "true")
        head = self.git(repo, "rev-parse", "HEAD").stdout.strip()
        tree = os.path.join(self.tmp, "busy-tree")
        self.git(repo, "worktree", "add", "-q", tree, "-b", "held", head)
        self.track(repo, "held", "held")

        r = self.run_hygiene()
        self.assertIn("held", self.branch_names(repo))
        self.assertTrue(any(l.startswith("kept") and "held" in l
                            for l in self.branch_lines(r.stdout, repo)),
                        self.branch_lines(r.stdout, repo))


# --- the content test: a squash merge leaves no ancestor behind ------------

class TestPrunedByContent(HygieneTest):
    """A branch whose commits are its own but whose CONTENT the default already
    carries. Ancestry answers `keep` on every one of them, and 4 of the 15
    branches left over in one clone on 2026-08-29 were exactly this."""

    def test_a_squash_merged_branch_is_pruned_though_no_commit_of_it_is_an_ancestor(self):
        repo = self.repo("squash", origin="https://github.com/example-owner/squash.git")
        self.forge("example-owner/squash", "true")
        name = self.squashed(repo)
        # the premise: ancestry says keep, and so would comparing the two tips
        self.assertNotEqual(
            self.git(repo, "rev-list", "--count", f"origin/main..{name}").stdout.strip(),
            "0")
        self.assertNotEqual(
            self.git(repo, "diff", "--quiet", "origin/main", name, check=False).returncode,
            0)

        r = self.run_hygiene()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn(name, self.branch_names(repo))
        self.assertTrue(any(l.startswith("pruned") and name in l
                            for l in self.branch_lines(r.stdout, repo)),
                        self.branch_lines(r.stdout, repo))

    def test_a_branch_that_does_not_merge_into_the_default_is_kept(self):
        repo = self.repo("conflict", origin="https://github.com/example-owner/conflict.git")
        self.forge("example-owner/conflict", "true")
        name = self.conflicting(repo)

        r = self.run_hygiene()
        self.assertIn(name, self.branch_names(repo))
        self.assertTrue(any(l.startswith("kept") and name in l and "does not merge" in l
                            for l in self.branch_lines(r.stdout, repo)),
                        self.branch_lines(r.stdout, repo))

    def test_a_merge_that_could_not_run_is_not_reported_as_a_conflict(self):
        # `merge-tree` exits 1 for a conflict AND for a merge it never attempted,
        # and the branch is kept either way — but a report that calls the second
        # one a conflict sends the reader after a merge that never happened
        repo = self.repo("unrelated",
                         origin="https://github.com/example-owner/unrelated.git")
        self.forge("example-owner/unrelated", "true")
        name = self.unrelated(repo)

        r = self.run_hygiene()
        self.assertIn(name, self.branch_names(repo))
        self.assertTrue(any(l.startswith("kept") and name in l
                            and "was not measured" in l
                            for l in self.branch_lines(r.stdout, repo)),
                        self.branch_lines(r.stdout, repo))


# --- the second source: a repository the roster cannot reach ---------------

class TestTheRepositoryThisBinLivesIn(HygieneTest):
    """The roster sweeps for QUEUES, and the plugin's own clone has none — so it
    was the one repository the audit never reached, and the only one whose box
    stayed off. The second source is the bin's own installation directory."""

    def test_a_clone_with_no_queue_is_audited_when_the_bin_lives_in_it(self):
        repo = self.repo("plugin-clone", queue=False,
                         origin="https://github.com/example-owner/plugin.git")
        self.forge("example-owner/plugin", "true")
        installed = self.install(os.path.join(repo, "tk", "bin"))

        r = self.run_hygiene(hygiene=installed)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        lines = self.forge_lines(r.stdout)
        self.assertEqual(len(lines), 1, lines)
        self.assertIn(repo, lines[0])
        self.assertIn("delete_branch_on_merge=true", lines[0])

    def test_the_branches_of_that_clone_are_pruned_like_any_other(self):
        repo = self.repo("plugin-clone", queue=False,
                         origin="https://github.com/example-owner/plugin.git")
        self.forge("example-owner/plugin", "true")
        self.three_branches(repo)
        installed = self.install(os.path.join(repo, "tk", "bin"))

        r = self.run_hygiene(hygiene=installed)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.branch_names(repo), ["local-only", "main", "unmerged-gone"])


# --- the remote side: the branch no pull request ever had as its head -------

REMOTE = "## remote branches"


class TestRemoteResidue(HygieneTest):
    """`delete_branch_on_merge` deletes the head of the PR, and a lane's
    per-ticket branch is never one. Four of them were alive on one remote on
    2026-09-02, after the lane's PR had merged."""

    def lane(self, name="lane"):
        repo, origin = self.lane_repo(name)
        self.forge("example-owner/example-repo", "true")
        return repo, origin

    def test_a_per_ticket_branch_already_in_the_default_is_deleted_from_the_remote(self):
        repo, _ = self.lane()
        branch = self.pushed_branch(repo, "spec/163/T234", merged=True)
        self.assertIn(branch, self.remote_branches(repo))

        r = self.run_hygiene()
        self.assertNotIn(branch, self.remote_branches(repo))
        self.assertTrue(any(l.startswith("deleted") and branch in l
                            for l in self.branch_lines(r.stdout, repo, REMOTE)),
                        r.stdout)

    def test_a_per_ticket_branch_still_carrying_its_work_survives(self):
        repo, _ = self.lane()
        branch = self.pushed_branch(repo, "spec/163/T235", merged=False)

        r = self.run_hygiene()
        self.assertIn(branch, self.remote_branches(repo))
        self.assertTrue(any(l.startswith("kept") and branch in l
                            for l in self.branch_lines(r.stdout, repo, REMOTE)),
                        r.stdout)

    def test_the_lane_s_own_branch_is_never_a_candidate(self):
        # `spec/<m>-<slug>` IS a pull request's head, so the forge deletes it on
        # the merge and this bin has no business touching it
        repo, _ = self.lane()
        branch = self.pushed_branch(repo, "spec/163-tk-hygiene", merged=True)

        r = self.run_hygiene()
        self.assertIn(branch, self.remote_branches(repo))
        self.assertEqual(self.branch_lines(r.stdout, repo, REMOTE), [])

    def test_a_branch_the_remote_moved_since_the_last_fetch_is_not_touched(self):
        repo, origin = self.lane()
        branch = self.pushed_branch(repo, "spec/163/T247", merged=True)
        self.push_from_elsewhere(origin, branch)

        r = self.run_hygiene()
        self.assertIn(branch, self.remote_branches(repo))
        self.assertTrue(any(l.startswith("kept") and branch in l
                            and "moved" in l
                            for l in self.branch_lines(r.stdout, repo, REMOTE)),
                        r.stdout)

    def test_the_remote_step_can_be_switched_off(self):
        repo, _ = self.lane()
        branch = self.pushed_branch(repo, "spec/163/T255", merged=True)

        r = self.run_hygiene("--no-remote")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn(branch, self.remote_branches(repo))
        self.assertNotIn(REMOTE, r.stdout)


# --- idempotence ------------------------------------------------------------

class TestIdempotence(HygieneTest):
    """Running twice changes nothing the second time.

    The property is structural — the prune is a DELETE, so the second run finds
    no candidate — which is also why no single-line mutation of the source can
    turn the second run into a different one. What the test below can be
    falsified on is the outcome it pins: the three-branch result is asserted
    after the FIRST run, so every mutation of a prune guard lands on it too.
    """

    def test_a_second_run_prunes_nothing_and_answers_the_same(self):
        repo = self.repo("three", origin="https://github.com/example-owner/three.git")
        self.forge("example-owner/three", "true")
        self.three_branches(repo)

        first = self.run_hygiene()
        after_first = self.branch_names(repo)
        self.assertEqual(after_first, ["local-only", "main", "unmerged-gone"],
                         first.stdout)
        second = self.run_hygiene()

        self.assertEqual(second.returncode, first.returncode,
                         first.stdout + second.stdout)
        self.assertEqual(self.branch_names(repo), after_first)
        self.assertNotIn("pruned", second.stdout)
        self.assertIn("delete_branch_on_merge=true", second.stdout)


if __name__ == "__main__":
    unittest.main()
