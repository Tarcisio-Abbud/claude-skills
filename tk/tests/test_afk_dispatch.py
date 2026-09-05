#!/usr/bin/env python3
"""Doc-conformance proof for the DISPATCH step of `../skills/kickoff/AFK.md` (step 3).

Run: python3 -m unittest discover -s tk/tests   (stdlib only, no deps)

What is asked of that step here is one prescription of it, born of a defect measured on a real
package:

- **the single exploration** (T176). Every implementer of a lane re-read the same base tree,
  because the prompt carried the item's distilled contract and nothing about the code around
  it. The step now explores ONCE, before the first ticket goes out, and hands every run the
  path of the notes. Two properties: the notes live OUTSIDE the repository — a path inside a
  worktree is committed by the lane and reviewed by the tail — and the exploration stands
  BEFORE the dispatch, which is the whole of its value.

- **the queue named on every reader of it** (T307). `tk-ticket-ref` resolves the queue from
  the cwd exactly as `tk-queue` does, and the step composed the closing reference with
  `--repo` alone: an orchestrator standing in the code's clone asked ANOTHER project's queue
  and got exit 2 over an item that is open in its own.

- **the ticket's branch tracking itself** (T308). The step named no command for the
  per-ticket worktree, and the recipe it was run with cut the branch from the lane's remote
  branch — which is what the new branch then tracked. Measured 2026-09-02 on T247.

THE PROSE IS WHAT IS ASSERTED, except for one recipe that is RUN. Nothing here can see an
orchestrator, so most of what this file holds is the text the orchestrator executes — the
call carrying its flag, the sentence standing in the right place. The worktree recipe is the
exception: what it does is a git fact, and a fact is cheaper to measure than to describe. It
is lifted out of the step, its metavariables filled, and executed against a throwaway
repository with a bare remote — no network, and this machine's own git configuration shut out
with `GIT_CONFIG_GLOBAL`/`GIT_CONFIG_SYSTEM`, because `push.default` is exactly what the
prescription turns on.

VACUITY GUARDS. Every check below reads a slice of step 3, and a step that lost its heading
or its dispatch paragraph would leave each of them iterating nothing. The first test asserts
the anchors the others cut against, and it fails loudly rather than passing over an empty
string.
"""

import os
import re
import shutil
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
AFK = os.path.join(HERE, os.pardir, "skills", "kickoff", "AFK.md")

STEP_HEADING = re.compile(r"^## 3\. Claim, then dispatch\s*$", re.M)
# where the lane stops preparing and starts dispatching tickets
DISPATCH_ANCHOR = "The lane is serial"
NOTES = "<notes dir>"
QUEUE_DIR = '--dir "<queue dir>"'

# The metavariables of the per-ticket recipe, and the values this file fills them with.
# `<m>` and `<slug>` are the lane's; `<id>` is the ticket's. Fictional, as every fixture
# name in this directory is.
SPEC, SLUG, TICKET = "9", "a-lane", "007"
LANE_BRANCH = f"spec/{SPEC}-{SLUG}"
TICKET_BRANCH = f"spec/{SPEC}/T{TICKET}"


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def step3(text=None):
    """AFK.md's step 3, up to the next `## ` heading.

    Scoped for the reason every doc-conformance file in this directory scopes its
    extraction: a sentence under another step must not answer for this one.
    """
    text = read(AFK) if text is None else text
    m = STEP_HEADING.search(text)
    if not m:
        return ""
    rest = text[m.end():]
    nxt = re.search(r"^## ", rest, re.M)
    return rest[:nxt.start()] if nxt else rest


def flat(text):
    """The step with its wrapping folded, so a sentence split across lines reads
    as the one sentence a reader acts on."""
    return re.sub(r"\s+", " ", text)


def sentences_with(text, needle):
    return [s for s in re.split(r"(?<=\.)\s+", flat(text)) if needle in s]


def sh_blocks(text):
    """The ```sh fences of the step, backslash-joined, as lists of lines."""
    return [[line.strip() for line in re.sub(r"\\\n\s*", " ", block).splitlines()
             if line.strip()]
            for block in re.findall(r"^```sh\n(.*?)^```", text, re.M | re.S)]


def ticket_recipe(text):
    """The fence that creates the PER-TICKET worktree, not the lane's.

    Told apart by the branch it names: both fences run `git worktree add`, and reading
    the first would test the lane's recipe under the ticket's name.
    """
    for block in sh_blocks(text):
        if any("spec/<m>/T<id>" in line for line in block):
            return block
    return []


class Step3Test(unittest.TestCase):
    def setUp(self):
        self.text = step3()

    def test_the_step_and_its_dispatch_paragraph_are_still_there(self):
        """The anchors every check below cuts against."""
        self.assertTrue(STEP_HEADING.search(read(AFK)),
                        "AFK.md has no `## 3. Claim, then dispatch` — re-anchor this file")
        self.assertTrue(self.text.strip(), "step 3 is empty")
        self.assertIn(DISPATCH_ANCHOR, self.text,
                      f"step 3 no longer says `{DISPATCH_ANCHOR}` — the ordering check "
                      "below would have nothing to place the exploration against")

    # --- T176: one exploration, before the first ticket ----------------------

    def test_the_step_prescribes_one_exploration_and_hands_its_notes_to_every_run(self):
        said = sentences_with(self.text, NOTES)
        self.assertTrue(said,
                        f"step 3 never names `{NOTES}` — nothing tells the orchestrator "
                        "where the exploration's notes go, and every implementer of the "
                        "lane re-reads the same base tree at its own cost")
        self.assertGreaterEqual(
            len(said), 2,
            f"`{NOTES}` is named once. It has two jobs — the exploration WRITES it and "
            f"every run's prompt CARRIES it — and one mention leaves the notes either "
            f"unwritten or undelivered: {said}")

    def test_the_notes_are_written_outside_the_repository(self):
        """A path inside a worktree is committed by the lane and reviewed by the
        tail: the notes are the session's, not the pull request's."""
        said = " ".join(sentences_with(self.text, NOTES))
        self.assertRegex(said, r"(?i)outside the repositor",
                         "step 3 does not say the exploration's notes live outside the "
                         "repository — inside one they are committed by the lane and "
                         "read by the tail's review as part of the diff")

    def test_the_exploration_stands_before_the_first_ticket_goes_out(self):
        """Its whole value is the ORDER: notes written after the first dispatch
        reach nobody, and the run that would have used them has already read the
        tree itself."""
        first_note = flat(self.text).index(NOTES)
        dispatch = flat(self.text).index(DISPATCH_ANCHOR)
        self.assertLess(first_note, dispatch,
                        "the exploration is prescribed after the lane starts dispatching "
                        "tickets — the first implementer explores the base anyway, which "
                        "is the defect the step was written against")

    # --- T307: the queue is named on every reader of it ----------------------

    def test_the_composed_reference_names_the_queue_it_reads(self):
        """`tk-ticket-ref` resolves the queue from the cwd, as `tk-queue` does.

        The step used to pass `--repo` and nothing else, and `--repo` names the CLONE
        the owner is read from — a different question. An orchestrator standing in the
        code's clone then asked whatever queue that path encodes to, and the reader
        exited 2 over an item open in the queue the package is running.
        """
        said = sentences_with(self.text, "tk-ticket-ref")
        self.assertTrue(said, "step 3 no longer composes the closing reference — "
                              "re-anchor this check")
        self.assertIn(QUEUE_DIR, " ".join(said),
                      f"the `tk-ticket-ref` call carries no {QUEUE_DIR}: it resolves the "
                      f"queue from the cwd, which is the code's clone while a package "
                      f"runs, and answers about another project's queue: {said}")

    def test_the_file_wide_rule_covers_both_readers_of_the_queue(self):
        """One rule, stated once at the top, or a flag remembered call by call."""
        head = flat(read(AFK).split("## 1.")[0])
        self.assertIn("tk-ticket-ref", head,
                      "the opening rule names only `tk-queue` as carrying "
                      f"{QUEUE_DIR}, so the other reader of the queue reads as exempt")


class TicketWorktreeTest(unittest.TestCase):
    """T308 — the recipe is RUN, and the upstream it leaves behind is measured.

    Two moments are asked, because the defect has two halves that fail apart: right
    after `worktree add`, where a branch cut from the lane's remote branch silently
    tracks THAT branch, and after the whole recipe, where the `push -u` is what puts
    the upstream where the pull request expects it.
    """

    def setUp(self):
        self.tmp = os.path.realpath(tempfile.mkdtemp(prefix="tk-afk-dispatch-test."))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.home = os.path.join(self.tmp, "home")
        self.trees = os.path.join(self.tmp, "trees")
        self.clone = os.path.join(self.tmp, "clone")
        for d in (self.home, self.trees):
            os.makedirs(d)
        absent = os.path.join(self.tmp, "no-such-git-config")
        # this machine's own git config is shut out: `push.default` and
        # `branch.autoSetupMerge` are the very settings under test, and a suite that
        # read them would pass or fail by whose laptop ran it
        self.environ = dict(os.environ, HOME=self.home, GIT_CONFIG_GLOBAL=absent,
                            GIT_CONFIG_SYSTEM=absent, GIT_TERMINAL_PROMPT="0")
        self.remote = os.path.join(self.tmp, "remote.git")
        self.git(None, "init", "-q", "--bare", "--initial-branch=main", self.remote)
        self.git(None, "clone", "-q", self.remote, self.clone)
        self.git(self.clone, "config", "user.email", "fixture@example.invalid")
        self.git(self.clone, "config", "user.name", "Fixture")
        self.write(self.clone, "a", "main\n")
        self.git(self.clone, "add", "a")
        self.git(self.clone, "commit", "-qm", "main")
        self.git(self.clone, "push", "-q", "-u", "origin", "main")
        self.git(self.clone, "checkout", "-q", "-b", LANE_BRANCH)
        self.write(self.clone, "b", "lane\n")
        self.git(self.clone, "add", "b")
        self.git(self.clone, "commit", "-qm", "lane")
        self.git(self.clone, "push", "-q", "-u", "origin", LANE_BRANCH)
        self.git(self.clone, "checkout", "-q", "main")

    def write(self, tree, name, text):
        with open(os.path.join(tree, name), "w", encoding="utf-8") as f:
            f.write(text)

    def git(self, tree, *argv):
        cmd = ["git"] + (["-C", tree] if tree else []) + list(argv)
        run = subprocess.run(cmd, capture_output=True, text=True, env=self.environ,
                             cwd=self.tmp, timeout=60)
        self.assertEqual(run.returncode, 0, f"{' '.join(cmd)}\n{run.stderr}")
        return run.stdout.strip()

    def filled(self):
        """The prescribed lines with their metavariables replaced — what a reader
        pastes, and the only edit made to them."""
        lines = ticket_recipe(step3())
        self.assertTrue(lines, "step 3 prescribes no per-ticket worktree recipe: the "
                               "orchestrator invents one, and the one it invented left "
                               "the ticket branch tracking the lane")
        out = []
        for line in lines:
            for was, now in (("<the lane's repo address>", self.clone),
                             ("<path>", self.trees), ("<m>", SPEC),
                             ("<slug>", SLUG), ("<id>", TICKET)):
                line = line.replace(was, now)
            out.append(line)
        return out

    def run_line(self, line):
        return subprocess.run(["bash", "-c", line], capture_output=True, text=True,
                              env=self.environ, cwd=self.tmp, timeout=120)

    def upstream(self, tree):
        run = subprocess.run(
            ["git", "-C", tree, "rev-parse", "--abbrev-ref",
             "--symbolic-full-name", "@{u}"],
            capture_output=True, text=True, env=self.environ, timeout=60)
        return run.stdout.strip() if run.returncode == 0 else None

    @property
    def ticket_tree(self):
        return os.path.join(self.trees, f"T{TICKET}")

    def test_the_new_worktree_does_not_track_the_lanes_branch(self):
        """The first line alone, because this is where the damage is done: a branch
        cut from `origin/<lane>` tracks it, and everything after inherits that."""
        first = self.filled()[0]
        run = self.run_line(first)
        self.assertEqual(run.returncode, 0,
                         f"the prescribed line does not run:\n$ {first}\n{run.stderr}")
        self.assertNotEqual(
            self.upstream(self.ticket_tree), f"origin/{LANE_BRANCH}",
            "the ticket's branch tracks the LANE's branch: a bare `push` from this "
            "worktree writes work in progress into the branch the pull request "
            "publishes, and only a name mismatch under `push.default=simple` stops it")

    def test_the_recipe_leaves_the_upstream_on_the_tickets_own_branch(self):
        for line in self.filled():
            run = self.run_line(line)
            self.assertEqual(run.returncode, 0,
                             f"the prescribed line does not run:\n$ {line}\n{run.stderr}")
        self.assertEqual(self.upstream(self.ticket_tree), f"origin/{TICKET_BRANCH}",
                         "after the whole recipe the ticket's branch still does not "
                         "track its own remote branch")

    def test_a_bare_push_cannot_reach_the_lanes_branch(self):
        """The property the two above exist for, asked of the thing itself.

        `push.default=upstream` is set here on purpose: under `simple` the wrong
        upstream is refused for having a different NAME, which is a defence nobody
        chose and one setting removes. What must hold is that the push lands on the
        ticket's branch whatever that setting says.
        """
        for line in self.filled():
            self.assertEqual(self.run_line(line).returncode, 0, line)
        before = self.git(self.clone, "rev-parse", f"origin/{LANE_BRANCH}")
        self.git(self.ticket_tree, "config", "push.default", "upstream")
        self.git(self.ticket_tree, "config", "user.email", "fixture@example.invalid")
        self.git(self.ticket_tree, "config", "user.name", "Fixture")
        self.write(self.ticket_tree, "c", "work in progress\n")
        self.git(self.ticket_tree, "add", "c")
        self.git(self.ticket_tree, "commit", "-qm", "wip")
        self.git(self.ticket_tree, "push", "-q")
        self.git(self.clone, "fetch", "-q", "origin")
        self.assertEqual(self.git(self.clone, "rev-parse", f"origin/{LANE_BRANCH}"), before,
                         "a bare push from the ticket's worktree moved the LANE's branch "
                         "— the pull request now publishes work in progress nobody "
                         "reviewed")
        self.assertNotEqual(self.git(self.clone, "rev-parse", f"origin/{TICKET_BRANCH}"),
                            before, "the push did not reach the ticket's own branch")


if __name__ == "__main__":
    unittest.main()
