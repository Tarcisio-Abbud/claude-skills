#!/usr/bin/env python3
"""Where a `fixer`'s correction is committed — `../skills/kickoff/AFK.md`, *The lane's tail*.

Run: python3 -m unittest discover -s tk/tests   (stdlib only, no deps)

THE USER STORY THIS DEFENDS. A lane's pull request lands many items at once, and what the
user is given to back ONE of them out again is the merge whose title starts with `T<id>`:
`git revert -m 1` on it undoes that item and nothing else. The tail's review fires after
every item has already merged, so the `fixer` that repairs a finding was committing on the
LANE's branch — outside every merge the item owns. Measured on pull request
claude-skills#52: 54f1304 for T236, 15e97f1 and 063da1a for T237, all three outside the
merges, all three invisible to the handle the user was promised.

TWO FILES OF PROOF IN ONE. The first class reads the prose, as every doc-conformance file
here does. The second REHEARSES the two shapes in a throwaway repository and measures what
`git revert -m 1` does to each, because the rule is only worth its words if the shape it
prescribes really carries the correction and the shape it forbids really loses it. Nothing
about a session, a subagent or a review is asserted anywhere here: what is asserted is the
prose, and a git fact about two commit graphs.
"""

import os
import re
import shutil
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
AFK = os.path.join(HERE, os.pardir, "skills", "kickoff", "AFK.md")

TAIL_HEADING = re.compile(r"^### The lane's tail\s*$", re.M)
ITEM_BRANCH = "spec/<m>/T<id>"

LANE = "spec/9-lane"
TICKET = "spec/9/T007"
TITLE = "T007"


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def tail(text=None):
    """The tail section, up to the next `## ` heading.

    Scoped for the reason every extraction in this directory is scoped: the same words
    under step 5's per-item cycle would answer for a rule the tail has to carry itself.
    """
    text = read(AFK) if text is None else text
    m = TAIL_HEADING.search(text)
    if not m:
        return ""
    rest = text[m.end():]
    nxt = re.search(r"^## ", rest, re.M)
    return rest[:nxt.start()] if nxt else rest


def flat(text):
    return re.sub(r"\s+", " ", text)


class TheTailSaysWhereAFixCommits(unittest.TestCase):
    def setUp(self):
        self.text = flat(tail())

    def test_the_tail_section_is_still_there(self):
        """The guard the three checks below cut against: a tail that lost its heading
        would leave each of them reading an empty string and passing."""
        self.assertTrue(TAIL_HEADING.search(read(AFK)),
                        "AFK.md has no `### The lane's tail` — re-anchor this file")
        self.assertTrue(self.text.strip(), "the tail section is empty")
        self.assertIn("fixer", self.text,
                      "the tail no longer dispatches a fixer, and this file is about "
                      "where that fixer's commit lands")

    def test_a_fix_belonging_to_one_item_commits_on_that_items_branch(self):
        self.assertIn(ITEM_BRANCH, self.text,
                      f"the tail never names `{ITEM_BRANCH}`: the fixer commits wherever "
                      "it happens to be standing, which is the lane's worktree, and the "
                      "correction lands outside every merge the item owns")

    def test_the_items_branch_is_merged_again_under_the_items_title(self):
        """Committing on the item's branch is half a rule. Unmerged, the correction is
        not in the lane at all; merged without `T<id>` in the title, it is in the lane
        and outside the handle the user greps for."""
        said = [s for s in re.split(r"(?<=\.)\s+", self.text) if ITEM_BRANCH in s]
        self.assertTrue(said, "nothing to read — see the check above")
        joined = " ".join(said)
        self.assertRegex(joined, r"merged into the lane again",
                         "the tail says where the fix commits and not that the branch "
                         "is merged again: the correction never reaches the lane")
        self.assertIn("`T<id>` leading the title", joined,
                      "the re-merge is prescribed with no title rule, so the merge that "
                      "carries the correction is not one `git log --merges` finds by id")

    def test_a_fix_belonging_to_no_single_item_stays_on_the_lane(self):
        """The rule has to say what to do with the fix that has no item — the repair of
        the lane's own merge of `origin/main`, or one spanning two items. Silent, it
        reads as "every fix goes on some item's branch", and the fixer picks one."""
        self.assertRegex(self.text, r"stays on the lane's branch",
                         "the tail does not say where a fix belonging to no single item "
                         "goes, so the fixer attributes it to one and the user's revert "
                         "of that item takes an unrelated repair with it")


class RevertingTheItemsMerge(unittest.TestCase):
    """The rehearsal: both shapes built, both reverted, the trees compared.

    `git revert -m 1` is run against EVERY merge whose title starts with the item's id,
    newest first, which is the handle the user story gives the user. The question each
    test asks is what the tree holds afterwards.
    """

    FEATURE = "feature.py"
    BEFORE = "def f():\n    return 1\n"
    AFTER = "def f():\n    return 2\n"

    def setUp(self):
        self.tmp = os.path.realpath(tempfile.mkdtemp(prefix="tk-afk-fixer-test."))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        absent = os.path.join(self.tmp, "no-such-git-config")
        # this machine's git configuration is shut out: `merge.conflictstyle`,
        # `rerere` and a global hooks path would each change what a revert does here
        self.environ = dict(os.environ, HOME=self.tmp, GIT_CONFIG_GLOBAL=absent,
                            GIT_CONFIG_SYSTEM=absent)

    def git(self, tree, *argv, check=True):
        run = subprocess.run(["git", "-C", tree, *argv], capture_output=True, text=True,
                             env=self.environ, timeout=60)
        if check:
            self.assertEqual(run.returncode, 0,
                             f"git {' '.join(argv)}\n{run.stdout}{run.stderr}")
        return run

    def write(self, tree, name, text):
        with open(os.path.join(tree, name), "w", encoding="utf-8") as f:
            f.write(text)

    def commit(self, tree, name, text, message):
        self.write(tree, name, text)
        self.git(tree, "add", name)
        self.git(tree, "commit", "-qm", message)

    def lane_with_fixer(self, on_the_lane):
        """A lane carrying one merged item, and one `fixer` commit repairing it.

        `on_the_lane` builds the shape the tail used to leave behind; the other builds
        the one it now prescribes. Everything else about the two graphs is identical.
        """
        tree = os.path.join(self.tmp, "lane" if on_the_lane else "item")
        os.makedirs(tree)
        self.git(tree, "init", "-q", "--initial-branch=main", ".")
        self.git(tree, "config", "user.email", "fixture@example.invalid")
        self.git(tree, "config", "user.name", "Fixture")
        self.commit(tree, "base", "base\n", "base")
        self.git(tree, "checkout", "-q", "-b", LANE)
        self.git(tree, "checkout", "-q", "-b", TICKET)
        self.commit(tree, self.FEATURE, self.BEFORE, "the item's work")
        self.git(tree, "checkout", "-q", LANE)
        self.git(tree, "merge", "-q", "--no-ff", "-m", f"{TITLE} the item", TICKET)
        if not on_the_lane:
            self.git(tree, "checkout", "-q", TICKET)
        self.commit(tree, self.FEATURE, self.AFTER, f"{TITLE} fixer: the review's finding")
        if not on_the_lane:
            self.git(tree, "checkout", "-q", LANE)
            self.git(tree, "merge", "-q", "--no-ff", "-m",
                     f"{TITLE} the fixer's correction", TICKET)
        return tree

    def merges_of_the_item(self, tree):
        """The handle the user story hands the user: every merge on the lane whose
        title begins with the item's id, newest first — `git log --merges`'s order."""
        out = self.git(tree, "log", "--merges", "--format=%H\t%s", LANE).stdout
        return [line.split("\t")[0] for line in out.splitlines()
                if line.strip() and line.split("\t", 1)[1].startswith(TITLE)]

    def revert_the_item(self, tree):
        """(outcome, the file's content or None) after reverting all of them."""
        for sha in self.merges_of_the_item(tree):
            run = self.git(tree, "revert", "-m", "1", "--no-edit", sha, check=False)
            if run.returncode != 0:
                self.git(tree, "revert", "--abort", check=False)
                return "conflict", self.feature(tree)
        return "clean", self.feature(tree)

    def feature(self, tree):
        path = os.path.join(tree, self.FEATURE)
        if not os.path.exists(path):
            return None
        with open(path, encoding="utf-8") as f:
            return f.read()

    def test_the_fix_on_the_lane_survives_the_revert_of_the_item(self):
        """The defect, rehearsed. One merge carries the id, and reverting it tries to
        delete a file the lane has since modified: git stops on a conflict, and what is
        left in the tree is the item's code under the fixer's edit."""
        tree = self.lane_with_fixer(on_the_lane=True)
        self.assertEqual(len(self.merges_of_the_item(tree)), 1,
                         "the shape under test has one merge carrying the id")
        outcome, content = self.revert_the_item(tree)
        self.assertEqual(outcome, "conflict",
                         "the rehearsal no longer reproduces the defect — re-read it "
                         "before trusting the case below")
        self.assertEqual(content, self.AFTER,
                         "the correction was expected to survive the revert of the item "
                         "it belongs to; that is the whole defect")

    def test_the_fix_on_the_items_branch_goes_with_the_revert(self):
        """The prescribed shape. Two merges carry the id, both revert without a
        conflict, and the item leaves the tree whole — its work and its repair."""
        tree = self.lane_with_fixer(on_the_lane=False)
        self.assertEqual(len(self.merges_of_the_item(tree)), 2,
                         "the fixer's correction reached the lane through a merge of "
                         "its own, carrying the item's id")
        outcome, content = self.revert_the_item(tree)
        self.assertEqual(outcome, "clean",
                         "reverting the item's merges hit a conflict, so the handle the "
                         "user story gives the user does not run unattended")
        self.assertIsNone(content,
                          "the item's file is still in the tree after its merges were "
                          "reverted — the revert took the work and left the repair")


if __name__ == "__main__":
    unittest.main()
