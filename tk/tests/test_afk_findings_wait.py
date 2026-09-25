#!/usr/bin/env python3
"""When a pull request waits on a finding — `../skills/kickoff/AFK.md`, its two sites.

Run: python3 -m unittest discover -s tk/tests   (stdlib only, no deps)

WHY THIS FILE EXISTS. Two sentences of `AFK.md` gave one subject two dispositions.
*The lane's tail*, step 2, said "A finding nobody here can close goes to the digest,
and the pull request waits on it"; *The fixer cap* said "…never as one no fixer could
close, so the pull request does not wait on it". An orchestrator following the file
could obey either, and the two answers ship different pull requests: one held for the
user, one merged with a line in its body. The collision was reported on pull request
claude-skills#136 under "Achados não tratados" and repaired here.

THE DISPOSITION THE REST OF THE SYSTEM IMPLEMENTS is the merge gate's, not either
sentence's alone. `../skills/merge-gate/SKILL.md` names one case and one only: "A
finding no fixer could close" is among the three shapes that end at "this pull request
waits for the user", the strict form's verdict 2 says a parked finding "defers this
pull request only where no fixer could close it", and the accumulated lane's paragraph
defers the whole pull request for "a criterion red at the tail's step 3, or a finding
no fixer could close". Everything else — what the one correction cycle left over, and
whatever a re-review found after it — rides in the body under "Achados não tratados"
(`../skills/kickoff/FINDINGS.md`, destination 2) and holds nothing back. So the rule is
a single boundary, and each of AFK.md's two sentences states the side that applies to
it.

WHAT IS PROVED. That the term is one term across both sites; that the tail's waiting
sentence names the case it waits on; that the cap names the spent cycle as its own
subject, excludes the waiting case by name, and states the one case that does wait;
that no sentence of either section pronounces on waiting without naming the term the
boundary hinges on; and that the merge gate still carries the disposition all of this
is aligned to.

WHAT IS NOT. That an orchestrator obeys it. Nothing here sees a session.

VACUITY GUARD. Both sections are extracted by heading and asserted non-empty before
anything is read out of them, and the sentence-level checks assert they found a
sentence before asserting anything about it. A section deleted or renamed fails the
guard rather than passing over an empty string.
"""

import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
KICKOFF = os.path.join(HERE, os.pardir, "skills", "kickoff")
AFK = os.path.join(KICKOFF, "AFK.md")
MERGE_GATE = os.path.join(HERE, os.pardir, "skills", "merge-gate", "SKILL.md")

TAIL_HEADING = re.compile(r"^### The lane's tail\s*$", re.M)
CAP_HEADING = re.compile(r"^## The fixer cap\s*$", re.M)

# The one term both sites hinge on, spelt as `merge-gate/SKILL.md` spells it. A site
# that renames it is a site the next reader cannot match against the gate.
TERM = "no fixer could close"

# The wording this repair retired. It read as the cap's own case — a finding nobody
# could close *because the cycle was spent* — which is exactly the case that does NOT
# wait, and that is how the two sentences came to collide.
RETIRED = "nobody here can close"


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def flat(text):
    """`text` with every run of whitespace collapsed to one space.

    Both sentences under test are wrapped across lines at the column this file is
    written to, so asserting against the raw text would make each check depend on
    where the wrap happened to fall.
    """
    return re.sub(r"\s+", " ", text)


def section(text, heading):
    """The section under `heading`, up to the next heading of level 2 or 3 — scoped
    for the reason every extraction in this directory is scoped: the same words under
    a neighbouring step would answer for a rule these two sites have to carry
    themselves.

    Level 3 counts because `### The lane's tail` is itself one: stopping only at `## `
    ran the tail's slice through `### The sweep over the union` and into step 6, so
    the property check below policed three sections and blamed the tail for all of
    them."""
    m = heading.search(text)
    if not m:
        return ""
    rest = text[m.end():]
    nxt = re.search(r"^#{2,3} ", rest, re.M)
    return flat(rest[:nxt.start()] if nxt else rest)


def sentences(text, word):
    return [s for s in re.split(r"(?<=\.)\s+", text) if word in s]


class SentenceCase(unittest.TestCase):
    """The shape three checks below share: the sentences of one piece of prose that
    carry a word, and the phrase they owe.

    `self.body` is the prose under test — a section for the two AFK.md sites, the
    whole file for the merge gate — and each subclass's `setUp` sets it.
    """

    body = ""

    def assert_sentence_with(self, word, phrase, silent, unnamed):
        """`self.body` says something about `word`, and says `phrase` while doing it.

        `silent` blames prose that stopped pronouncing on `word` at all; `unnamed`
        blames prose that pronounces without the phrase the boundary hinges on.
        """
        said = sentences(self.body, word)
        self.assertTrue(said, silent)
        self.assertIn(phrase, " ".join(said), unnamed)


class TheTwoSitesAreStillThere(unittest.TestCase):
    """The guard every check below cuts against."""

    def setUp(self):
        self.text = read(AFK)

    def test_the_tail_section_is_there(self):
        self.assertTrue(TAIL_HEADING.search(self.text),
                        "AFK.md has no `### The lane's tail` — re-anchor this file")
        self.assertTrue(section(self.text, TAIL_HEADING).strip(),
                        "the tail section is empty")

    def test_the_fixer_cap_section_is_there(self):
        self.assertTrue(CAP_HEADING.search(self.text),
                        "AFK.md has no `## The fixer cap` — re-anchor this file")
        self.assertTrue(section(self.text, CAP_HEADING).strip(),
                        "the fixer cap section is empty")


class TheTailWaitsOnOneCase(SentenceCase):

    def setUp(self):
        self.body = section(read(AFK), TAIL_HEADING)

    def test_the_waiting_sentence_names_the_case_it_waits_on(self):
        """The half of the collision that lived in the tail: a disposition with an
        unnamed subject, which a reader fills in with whichever finding is in front
        of them."""
        self.assert_sentence_with(
            "waits", TERM,
            "the tail no longer says the pull request waits on anything — the "
            "digest carries a finding nobody is held back for",
            f"the tail's waiting sentence does not name `{TERM}`: the pull request "
            "waits on a finding whose case the reader has to guess, and the cap's "
            "sentence answers the other way")

    def test_the_tail_routes_every_other_finding_to_the_cap(self):
        """Naming the waiting case is half the repair. Silent about the rest, the
        tail still reads as the destination for a finding the cap merely left over.

        What is pinned is the routing clause, not the cap's name: the sentence this
        repair replaced already named *The fixer cap*, so a check for the name alone
        passes unchanged on the prose that collided."""
        self.assertIn("Every other finding goes to *The fixer cap*", self.body,
                      "the tail does not route every other finding to *The fixer "
                      "cap*, so a finding it does not wait on has no route out of "
                      "this step")


class TheCapDoesNotWaitOnItsOwnCase(SentenceCase):

    def setUp(self):
        self.body = section(read(AFK), CAP_HEADING)

    def test_the_cap_names_the_spent_cycle_as_its_subject(self):
        """`What that cycle leaves unclosed` covered both cases at once — including
        the one the tail holds the pull request for. The subject is the cycle that
        RAN OUT, and the word that says so is what keeps the two apart."""
        self.assertIn("the spent cycle", self.body,
                      "the cap's subject is any finding its cycle left unclosed, "
                      "which swallows the one no fixer could close and takes the "
                      "pull request off the hook for it")

    def test_the_sentence_that_does_not_wait_excludes_the_waiting_case_by_name(self):
        self.assert_sentence_with(
            "does not wait", f"never as one {TERM}",
            "the cap no longer says the pull request does not wait, and a line "
            "under \"Achados não tratados\" now holds a pull request back",
            "the cap releases the pull request without excluding the case that "
            f"holds it: `never as one {TERM}` is the exclusion")

    def test_the_cap_states_the_one_case_that_does_wait(self):
        """Read alone — which is how this file is read, by section — the cap owes
        the reader the other side of the boundary, or the reader learns only that
        nothing waits."""
        self.assertIn(f"waits only on a finding {TERM}", self.body,
                      "the cap says which findings the pull request does not wait "
                      "on and never which one it does, so a reader who stops here "
                      "merges a pull request the tail holds")


class NeitherSiteSaysItWithoutTheTerm(unittest.TestCase):
    """The collision, stated as a property rather than as two sentences.

    Every pronouncement on waiting, in either section, hangs on one term. A future
    edit that reintroduces a bare "the pull request waits on it" — the shape the
    repair removed — fails here without anyone having to remember these two sites.
    """

    def setUp(self):
        self.text = read(AFK)
        self.sites = {"The lane's tail": section(self.text, TAIL_HEADING),
                      "The fixer cap": section(self.text, CAP_HEADING)}

    def test_every_sentence_about_waiting_names_the_term(self):
        for name, body in self.sites.items():
            said = sentences(body, "wait")
            with self.subTest(section=name):
                self.assertTrue(said, f"*{name}* says nothing about waiting")
                for sentence in said:
                    self.assertIn(TERM, sentence,
                                  f"*{name}* disposes of a finding without naming "
                                  f"`{TERM}`, which is the whole boundary: "
                                  f"{sentence}")

    def test_the_retired_wording_is_gone_from_the_file(self):
        """Two spellings of one case read as two cases. `grep` is the only index a
        reader of this file has."""
        self.assertNotIn(RETIRED, flat(self.text),
                         f"AFK.md says `{RETIRED}` again — a second name for the "
                         f"case `{TERM}` names, and the collision is back")


class TheGateStillHoldsTheDisposition(SentenceCase):
    """The prose above is aligned to `merge-gate/SKILL.md`, so the alignment is only
    worth its words while the gate still says it. A gate that changes its mind reddens
    here rather than leaving AFK.md pointing at a rule nobody implements.

    Both checks pin the gate's two deferrals by what each one disposes of plus the
    term it hinges on, never by the gate's own sentence end to end: this file has no
    say over another skill's wording, and a reword that keeps the disposition should
    not redden it.
    """

    def setUp(self):
        self.body = flat(read(MERGE_GATE))

    def test_the_gate_defers_a_pull_request_for_a_finding_no_fixer_could_close(self):
        self.assert_sentence_with(
            "defers the whole pull request", TERM,
            "the merge gate no longer defers a whole pull request at all — AFK.md's "
            "two sentences are aligned to a rule that has moved",
            "the merge gate defers the whole pull request without naming a finding "
            f"`{TERM}`, so the tail's waiting sentence now waits for a case the "
            "gate does not hold")

    def test_the_gate_holds_nothing_else_back(self):
        self.assert_sentence_with(
            "defers this pull request only", TERM,
            "the merge gate no longer confines its deferral to one case, so the "
            "cap's `does not wait` may now be wrong",
            f"the gate's confined deferral no longer names `{TERM}`, so the case "
            "the cap excludes and the case the gate holds may have parted")


if __name__ == "__main__":
    unittest.main()
