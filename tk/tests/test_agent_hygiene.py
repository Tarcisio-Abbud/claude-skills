#!/usr/bin/env python3
"""Doc-conformance proof for `../skills/kickoff/HYGIENE.md`.

Run: python3 -m unittest discover -s tk/tests   (stdlib only, no deps)

WHAT THE FILE IS. The seven rules an orchestrator applies to the runs it dispatched, read
from step 3 of `AFK.md`. Six were paid for in the package of 05-07/09/2026; the seventh is
the cookbook's empty-worker guard. Nothing here dispatches an agent: what is asserted is
the PROSE, because the prose is what the orchestrator executes.

WHY EACH CHECK IS HERE. A rule kept without the observation that fires it is a rule an
orchestrator carries and never applies, so every one of the seven owes a **Signal** line —
that is the property `TheSevenRules` holds, one subtest per rule. Three rules owe more
than their signal, because a defect measured against them lived in the detail:

- the `.output` rule owes its NUMBERS (size and mtime, frozen) and the refusal to read the
  file's content; without them it says "look at the file", which is the ~15k-token read the
  rule beside it exists to refuse;
- the counting rule owes the REASON the total lies. `ListAgents` counts agents and the
  question was about lanes: a reader who has only "filter by role" filters by whatever role
  looks right;
- the empty-return guard owes its SOURCE. It is the one rule with no measurement in this
  house behind it, and a rule with neither is a rule the next reader can talk out of the
  file.

VACUITY GUARD FIRST. Every check cuts a slice on a heading, and a heading that moved would
leave the check reading an empty string and passing. `section()` asserts each slice
non-empty as it is taken, and `test_the_file_carries_exactly_the_seven_rule_sections`
refuses both an eighth rule smuggled in as a heading and a seventh quietly dropped.

WHAT IS NOT PROVED HERE: that an orchestrator ever reads the file, that killing a waiter
works, or that `TaskStop` and `SendMessage` behave as described — a live subagent is not a
fixture. The one command the file prescribes (`stat`) was run in a throwaway directory when
the file was written, which is the whole proof a prescribed command can have here.

NAME COLLISION, deliberate and checked: `tk/bin/tk-hygiene` prunes branches in a repository
and shares nothing with this file but the word. `test_tk_hygiene.py` is that bin's proof;
this module is the file's. `test_the_file_separates_itself_from_the_bin_of_the_same_name`
holds the carve-out in the prose, so a reader who greps `hygiene` is told which is which.
"""

import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.join(HERE, os.pardir)
KICKOFF = os.path.join(PLUGIN, "skills", "kickoff")
HYGIENE = os.path.join(KICKOFF, "HYGIENE.md")
AFK = os.path.join(KICKOFF, "AFK.md")
FLEET = os.path.join(PLUGIN, "skills", "fleet", "SKILL.md")

# The seven, keyed by the heading each one lives under. The value is the term a `grep`
# finds the rule by — the term is the assertion, because a rule renamed out of it is a
# rule the next reader cannot search for.
THE_SEVEN = {
    "One scratchpad per lane, named in the prompt": "scratchpad",
    "Count the live lanes by ROLE, never by the total": "`ListAgents`",
    "Never ask a live agent for its output": "notification",
    "A stuck run is read OFF its `.output` file, never out of it": "`.output` file",
    "Revive by message the run that stopped waiting for a notification": "`SendMessage`",
    "An empty or malformed return is a failure, never an approval": "empty return",
    "Kill the orphan waiters before the lane is declared closed": "waiter",
}

COOKBOOK = "https://platform.claude.com/cookbook/patterns-agents-orchestrator-workers"

# What step 3 of `AFK.md` may not say. The pointer is one line under a size lock: each of
# these words belongs to a rule the pointed-at file owns, and a pointer carrying one has
# started paying AFK.md's slack for prose that already exists next door.
THE_RULES_THE_POINTER_MAY_NOT_CARRY = ("scratchpad", "ListAgents", "TaskOutput",
                                       ".output", "SendMessage", "waiter", "TaskStop",
                                       "malformed", "mtime")


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def flat(text):
    """`text` with every run of whitespace collapsed to one space.

    Every phrase asserted below is prose wrapped at the column the file is written
    to. Asserted against the raw text, a check would depend on where the wrap fell:
    a reflow that changes nothing reddens, and a rewording that drops the rule stays
    green whenever it re-wraps the same way.
    """
    return " ".join(text.split())


class DocTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = read(HYGIENE)
        cls.afk = read(AFK)

    def section(self, title, raw=False):
        """The body under `## title`, up to the next `## ` — asserted non-empty."""
        pattern = re.compile(r"^## " + re.escape(title) + r"\s*$(.*?)(?=^## |\Z)",
                             re.M | re.S)
        found = pattern.findall(self.text)
        self.assertEqual(len(found), 1,
                         f"`## {title}` is not in HYGIENE.md exactly once — the check "
                         f"that cuts on it would read an empty string and pass")
        self.assertTrue(found[0].strip(), f"`## {title}` is empty")
        return found[0] if raw else flat(found[0])

    def afk_step_three(self):
        pattern = re.compile(r"^## 3\. Claim, then dispatch\s*$(.*?)(?=^## \d\. |\Z)",
                             re.M | re.S)
        found = pattern.findall(self.afk)
        self.assertEqual(len(found), 1,
                         "AFK.md step 3 lost its heading — the pointer check would read "
                         "an empty string and pass")
        return found[0]


class TheFileIsThere(DocTest):
    def test_the_file_exists_beside_the_afk_procedure(self):
        self.assertTrue(os.path.isfile(HYGIENE), f"{HYGIENE} is missing")

    def test_the_file_carries_exactly_the_seven_rule_sections(self):
        headings = re.findall(r"^## (.+?)\s*$", self.text, re.M)
        self.assertEqual(headings, list(THE_SEVEN),
                         "the file's `## ` headings are not the seven rules in order — "
                         "an eighth heading dilutes a list the ticket counts, and a "
                         "missing one is a rule that left with nothing reddening")

    def test_the_file_separates_itself_from_the_bin_of_the_same_name(self):
        head = flat(self.text.split("\n## ")[0])
        self.assertIn("`tk/bin/tk-hygiene`", head,
                      "the word `hygiene` already names a bin in this plugin; unnamed "
                      "here, the two senses read as one and a grep returns both")
        self.assertIn("prunes branches", head,
                      "the bin is named without saying what it does, which leaves the "
                      "reader to guess which of the two they are holding")

    def test_the_file_says_who_reads_it_and_from_where(self):
        head = flat(self.text.split("\n## ")[0])
        self.assertIn("step 3 of `AFK.md`", head,
                      "a file reached by a pointer says where the pointer is, or a "
                      "reader who arrived by grep cannot tell when it fires")
        self.assertIn("ORCHESTRATOR", head,
                      "the rules are about a run seen from outside; without naming its "
                      "reader they read as rules a run applies to itself")


class TheSevenRules(DocTest):
    def test_every_rule_is_named_by_the_term_a_grep_finds_it_under(self):
        body = flat(self.text)
        for title, term in THE_SEVEN.items():
            with self.subTest(rule=title):
                self.assertIn(term, body,
                              f"the rule {title!r} is not in the file under {term!r}")

    def test_every_rule_carries_the_signal_that_fires_it(self):
        for title in THE_SEVEN:
            with self.subTest(rule=title):
                body = self.section(title)
                self.assertIn("**Signal —**", body,
                              "the rule is stated with no observation that fires it, "
                              "which is a rule an orchestrator carries and never applies")
                signal = body.split("**Signal —**", 1)[1].split(".")[0]
                self.assertGreaterEqual(len(signal.split()), 5,
                                        f"the signal for {title!r} is {signal!r} — too "
                                        f"short to name an observation")

    def test_the_file_says_which_rules_were_measured_and_when(self):
        head = flat(self.text.split("\n## ")[0])
        self.assertIn("2026-09-06", head)
        self.assertIn("the seventh is the cookbook's", head,
                      "six measured rules and one borrowed one read as seven of equal "
                      "provenance unless the file separates them")


class TheOutputFileRule(DocTest):
    def body(self):
        return self.section("A stuck run is read OFF its `.output` file, never out of it")

    def test_the_criterion_is_the_two_numbers_of_the_file(self):
        body = self.body()
        for number in ("SIZE in bytes", "MTIME"):
            with self.subTest(number=number):
                self.assertIn(number, body,
                              "the criterion is numeric or it is a judgement call, and "
                              "a judgement call re-reads the file to make itself")
        self.assertIn("stat -c", body,
                      "the command that reads the two numbers is not prescribed, so the "
                      "reader reaches for the one that prints the content")

    def test_the_criterion_says_how_long_frozen_is_dead(self):
        body = self.body()
        self.assertIn("an hour or more", body,
                      "`frozen` with no duration is satisfied by any two readings taken "
                      "close together")
        self.assertIn("119 bytes", body)
        self.assertIn("20:52", body,
                      "the measured case is what makes the hour a number rather than a "
                      "preference")

    def test_reading_the_content_is_refused_with_its_cost(self):
        body = self.body()
        self.assertIn("Opening the file instead", body,
                      "the file's content is the thing not to read, and a rule that "
                      "never says so leaves `cat` as the obvious next step")
        self.assertIn("~15k tokens", body,
                      "the refusal is stated without its cost, which is what makes it a "
                      "rule rather than a preference")

    def test_the_dead_run_is_stopped_and_re_dispatched(self):
        body = self.body()
        self.assertIn("`TaskStop`", body)
        self.assertIn("last pushed commit", body,
                      "a re-dispatch that does not say where to resume from throws away "
                      "the slice the dead run had already pushed")


class TheCountingRule(DocTest):
    def body(self):
        return self.section("Count the live lanes by ROLE, never by the total")

    def test_the_rule_names_why_the_total_lies(self):
        body = self.body()
        self.assertIn("`code-review`", body,
                      "the two reviewers are what inflates the list; unnamed, the rule "
                      "is an instruction with no reason and the next reader drops it")
        self.assertIn("SIBLINGS", body,
                      "the reviewers are miscounted because of WHERE they appear in the "
                      "list, and that is the half a summary loses")
        self.assertIn("it counts agents", body,
                      "the total is not wrong, it answers another question — a rule that "
                      "calls it wrong invites a fix in the wrong place")

    def test_the_rule_says_what_to_count_instead_and_against_what(self):
        body = self.body()
        self.assertIn("`../../reference/subagent-policy.md`", body,
                      "counting by role without naming who owns the role names leaves "
                      "the reader inventing them")
        self.assertIn("`max-local-subagents`", body,
                      "the ceiling the count feeds is unnamed, so the two numbers cannot "
                      "be told apart")


class TheEmptyReturnGuard(DocTest):
    def body(self):
        return self.section("An empty or malformed return is a failure, never an approval")

    def test_the_guard_grades_the_empty_return_as_a_failure(self):
        body = self.body()
        self.assertIn("reads as success", body,
                      "the whole hazard is that an empty return looks like an approval; "
                      "without it the rule is a preference about tidiness")
        self.assertIn("graded as a failure", body)

    def test_the_remedy_is_a_ladder_and_ends_at_the_human(self):
        body = self.body()
        for rung in ("revive it", "re-dispatch", "escalation to the human"):
            with self.subTest(rung=rung):
                self.assertIn(rung, body,
                              "a guard with no remedy stops the package instead of "
                              "moving it")
        self.assertIn("ARTIFACT", body,
                      "the grading closes on the run's own account unless the file says "
                      "otherwise")

    def test_the_guard_cites_the_cookbook_page_as_its_source(self):
        body = self.body()
        self.assertIn(COOKBOOK, body,
                      "this is the one rule with no measurement of this house behind it "
                      "— uncited, it is the one a reader can talk out of the file")
        self.assertIn("not paid for in this house", body,
                      "the borrowed rule is not marked as borrowed, so it reads as "
                      "measured here and its source cannot be checked")

    def test_what_does_not_cross_from_the_cookbook_is_named(self):
        body = self.body()
        for construct in ("`FlexibleOrchestrator`", "`llm_call`", "`extract_xml`"):
            with self.subTest(construct=construct):
                self.assertIn(construct, body,
                              "citing the page without naming what does NOT cross is "
                              "how a Messages-API construct reaches a skill")
        self.assertIn("Messages-API constructs", body)


class TheAfkPointer(DocTest):
    def pointer(self):
        found = [line for line in self.afk_step_three().splitlines()
                 if "HYGIENE.md" in line]
        self.assertEqual(len(found), 1,
                         f"AFK.md step 3 names HYGIENE.md on {len(found)} lines, not one "
                         f"— the file is under a size lock and the slack pays for a "
                         f"pointer, not a paragraph")
        return found[0]

    def test_step_3_points_at_the_file_in_one_line(self):
        line = self.pointer()
        self.assertIn("beside this file", line,
                      "the pointer names a file without saying where it sits, and the "
                      "reader has AFK.md open")
        self.assertLessEqual(len(line), 100,
                             f"the pointer is {len(line)} characters — past 100 it has "
                             f"started carrying the rules")

    def test_the_pointer_repeats_none_of_the_seven_rules(self):
        line = self.pointer()
        for word in THE_RULES_THE_POINTER_MAY_NOT_CARRY:
            with self.subTest(word=word):
                self.assertNotIn(word, line,
                                 f"{word!r} belongs to a rule HYGIENE.md owns; a pointer "
                                 f"that carries it forks the rule into two files")


class TheFleetSkillIsUntouched(DocTest):
    def test_the_fleet_skill_does_not_name_the_file(self):
        """`fleet/SKILL.md` §4 hands the whole of `AFK.md` to every project run, so the
        fleet inherits this file through AFK.md's own pointer and owes no edit. A
        mention here would be the second address of one rule."""
        self.assertNotIn("HYGIENE", read(FLEET))


if __name__ == "__main__":
    unittest.main()
