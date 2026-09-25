#!/usr/bin/env python3
"""Doc-conformance proof for the four rules the first fleet run paid for (T396).

Run: python3 -m unittest discover -s tk/tests   (stdlib only, no deps)

WHAT THE RULES ARE. `/tk:fleet` ran for the first time on 2026-09-13, nine projects
in 3h57m, and it measured four holes in `../skills/fleet/SKILL.md`:

  1. no quota ceiling of its own — the file stopped only on a run RETURNING a quota
     failure, so the 82% weekly ceiling that actually held had to be fixed by hand
     from a menu;
  2. a stale quota reading (`read 58m ago`) read as current, by the monitoring turns
     and by the runs, instead of as the FLOOR that `WINDOW.md` says it is;
  3. twelve texts returned by the runs born into no queue — they reached the report
     and stopped there;
  4. two empty returns from one project, each a run that fired its suite as a
     background job and ended its turn announcing the wait.

WHY A GREP TEST AND NOT A FIXTURE. Nothing here has a runnable form: no test can watch
a fleet dispatch, a window fill or a human answer a menu. What CAN be held is that each
rule is still written, that the numbers still carry the measurement that produced them,
and that every file, bin and sibling section the prose points at is real. The last of
those is the half that is not about wording — `tk-quota` is asked to still print the
age marker the prose quotes, and each sibling file the new prose points at is asked to
exist, so prose pointing at something nobody wrote goes red here.

WHERE THE EMPTY-RETURN RULE IS NOT NAMED. `../skills/kickoff/HYGIENE.md` owns it, and
`test_agent_hygiene.py` holds that `fleet/SKILL.md` must not name that file: the fleet
hands the whole of `AFK.md` to every project run, and a second address for one rule is
what that check refuses. So the dispatch prompt's foreground order points at step 5 of
its own file, and this suite asks step 5 to be the place an empty return is graded.

VACUITY GUARD FIRST. Every check cuts a slice on a heading, and a heading that moved
would leave the check reading an empty string and passing. `section()` asserts each
slice non-empty as it is taken, and `test_every_section_the_checks_cut_on_is_there`
refuses the whole file's silence.

WHAT IS NOT PROVED HERE. That any fleet run obeys the rules, that 80% is the right
ceiling, or that the hook will ever learn `fleet` — that last one is T045 in the
`.ambiente` queue, a file this repository does not own.
"""

import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.join(HERE, os.pardir)
FLEET = os.path.join(PLUGIN, "skills", "fleet", "SKILL.md")
KICKOFF = os.path.join(PLUGIN, "skills", "kickoff")
BIN = os.path.join(PLUGIN, "bin")

CEILING = "### The fleet's quota ceiling"
WALL = "### The quota wall"
TEXTS = "### The texts a run returns are born at the close"
DISPATCH = "## 4. Dispatch, and refill without a barrier"
FAILS = "## 5. A project fails alone"
VISTA = "## 6. The consolidated vista"
SECTIONS = (CEILING, WALL, TEXTS, DISPATCH, FAILS, VISTA)

# The tick's own floors. Restated here they would fork from the file that owns
# them, which is the whole reason the ceiling section points instead of copying.
TICK_FLOORS = ("15%", "35%")


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def flat(text):
    """`text` with every run of whitespace collapsed to one space.

    The file wraps at its own column, so a phrase asserted against the raw text
    depends on where the wrap fell: a reflow that changes nothing would redden,
    and a rewording that drops the rule could stay green.
    """
    return " ".join(text.split())


class DocTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = read(FLEET)
        cls.flat = flat(cls.text)

    def section(self, title, raw=False):
        """The body under `title`, up to the next heading of its level or above."""
        level = len(title) - len(title.lstrip("#"))
        upto = r"(?=^#{1,%d} |\Z)" % level
        pattern = re.compile(r"^" + re.escape(title) + r"\s*$(.*?)" + upto, re.M | re.S)
        found = pattern.findall(self.text)
        self.assertEqual(len(found), 1,
                         f"`{title}` is not there exactly once — the checks that cut "
                         f"on it would read an empty string and pass")
        self.assertTrue(found[0].strip(), f"`{title}` is empty")
        return found[0] if raw else flat(found[0])

    def assertCarries(self, body, phrases, why):
        for phrase in phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, body, why)


class TheSectionsAreThere(DocTest):
    def test_every_section_the_checks_cut_on_is_there(self):
        for title in SECTIONS:
            with self.subTest(section=title):
                self.section(title)

    def test_the_ceiling_did_not_replace_the_wall(self):
        """Two different moments — one stops the fleet while the window still has
        room, the other once it has none. Folding them leaves the fleet with a
        single rule that fires too late or too early."""
        self.assertIn("stop dispatching", self.section(WALL),
                      "the wall's own stop is gone, so the ceiling is the only "
                      "thing left between the fleet and a dead window")


class TheQuotaCeiling(DocTest):
    def body(self):
        return self.section(CEILING)

    def test_the_word_the_criterion_greps_is_the_quota_one(self):
        # `ceiling` already means two AGENT ceilings in this file. The criterion
        # greps the word, so the quota sense has to be the one that answers.
        self.assertIn("quota ceiling", self.body(),
                      "the section never spells `quota ceiling`, and the grep "
                      "lands on the RAM ceiling of step 3 instead")

    def test_the_reading_is_taken_before_every_dispatch_and_from_the_bin(self):
        self.assertCarries(self.body(), (
            "../../bin/tk-quota", "before every project dispatch",
            "both rolling windows", "never once at the start",
        ), "the ceiling is stated with no reading behind it, or with one reading "
           "taken at the start of a run that lasts hours")

    def test_the_ceiling_is_a_third_axis_and_says_which_two_it_is_not(self):
        # Read as one of the two the contract block states, it would be divided
        # by `--fleet` and spent on agents instead of on the window.
        self.assertCarries(self.body(), (
            "max-local-subagents", "max-local-opus", "bound AGENTS",
            "bounds the WINDOW",
        ), "the quota ceiling reads as one of the two agent ceilings again")

    def test_the_default_carries_the_measurement_that_produced_it(self):
        # The run's date, 2026-09-13, left the skill in the T443 pruning pass: the bin
        # marks every ISO date as inline evidence. `docs/prune/fleet.md` keeps it.
        self.assertCarries(self.body(), (
            "80% used", "nine projects", "9 pp of the weekly", "82% fixed by hand",
        ), "the number stands with no measurement behind it, and reads as a "
           "preference the next reader is free to move")

    def test_the_five_hour_window_is_pointed_at_and_not_restated(self):
        body = self.body()
        self.assertIn("adds no number", body)
        self.assertIn('`WINDOW.md`\'s "The tick"', body,
                      "the floors are referred to without naming the section that "
                      "owns them, so a reader has nowhere to go")
        for floor in TICK_FLOORS:
            with self.subTest(floor=floor):
                self.assertNotIn(floor, body,
                                 f"the tick's {floor} floor is copied to here, "
                                 f"where it forks from the file that owns it")

    def test_the_override_is_named_and_the_site_file_key_is_denied(self):
        # An unknown key in the site file is ignored in silence (`tk_site.py`),
        # so prescribing one would promise a switch nothing reads.
        self.assertCarries(self.body(), (
            "naming a ceiling in the turn that fires the run",
            "NOT a site-file key", "~/.claude/tk/env", "ignored in silence",
        ), "the override is missing, or it sends the user to a key no bin reads")

    def test_above_the_ceiling_the_fleet_stops_sending_and_closes(self):
        body = self.body()
        self.assertCarries(body, (
            "Above the ceiling, stop dispatching and close",
            "The runs in flight keep running", "fourth stop condition",
        ), "the ceiling says what to read and never what to do about it — or it "
           "kills runs whose spend is already spent")

    def test_a_stale_reading_is_a_floor_that_only_forbids(self):
        body = self.body()
        self.assertIn("(read 58m ago)", body,
                      "the marker the bin prints is gone, so a reader cannot tell "
                      "a stale line from a fresh one")
        self.assertCarries(body, (
            "a floor forbids where it can never authorise",
            "a stale reading stops the dispatch",
            "a stale reading authorises nothing",
        ), "the floor rule is named without its asymmetry, which is the half the "
           "first fleet run got wrong in both directions")

    def test_the_reading_that_decides_is_the_one_at_a_return(self):
        # The sidecar is written only while a session renders, so an unattended
        # fleet's reading ages against runs that keep spending.
        self.assertCarries(self.body(), (
            "goes stale by construction", "taken AT a return",
            "58-minute-old figure was read as current",
        ), "nothing says when the reading is taken, so the monitor reads a figure "
           "an hour old as current again")


class TheTextsTheRunsReturn(DocTest):
    def body(self):
        return self.section(TEXTS)

    def test_the_birth_is_the_fleets_and_never_the_runs(self):
        self.assertCarries(self.body(), (
            "The fleet births those texts and the run does not",
            "refused inside a subagent", "ask-before-queue-add",
        ), "the run is left free to write a queue from inside a subagent, where "
           "the hook refuses it and the item's words reach no human")

    def test_the_twelve_that_went_nowhere_are_named_with_the_verdict(self):
        self.assertCarries(self.body(), (
            "twelve such texts and none was born",
            "a report line is a deferral with another name",
            "../kickoff/FINDINGS.md",
        ), "the defect this section was written for is gone, and a report line "
           "reads as a destination again")

    def test_the_command_carries_dir_and_the_menu_shows_the_words(self):
        body = self.body()
        self.assertIn("add --dir \"<that project's queue dir>\"", body,
                      "the birth is prescribed without the flag that decides WHICH "
                      "queue it lands in — the fleet's cwd is its own")
        self.assertCarries(body, ("--class", "--effort", "--criterion"),
                           "the prescribed line is missing a flag `add` requires, so "
                           "pasting it is refused by argparse rather than run")
        self.assertCarries(body, (
            "AskUserQuestion", "in the item's own words",
        ), "the menu is gone, and an item is written before a human has seen it")

    def test_the_unattended_blocker_is_named_and_not_implemented(self):
        self.assertCarries(self.body(), (
            "`kickoff` and `wrap-up`, not `fleet`", "T045", "`.ambiente` queue",
        ), "the reason an unattended fleet births nothing is unnamed, so the next "
           "session rediscovers it or implements the hook from here")

    def test_the_done_that_collects_the_briefing_is_measured_not_assumed(self):
        # Measured 2026-09-14 in a throwaway queue: writing the texts into the
        # briefing NAMED for the item being closed loses them at that `done`.
        self.assertCarries(self.body(), (
            "A `done` collects the briefing of the item it closes",
            "handoff-T001.md removed",
            "handoff-T001.md kept — still reached by T002",
            "the prompt says the PACKAGE handoff",
        ), "the trap is stated without the run that proves it, or the texts are "
           "sent to the one briefing the next `done` deletes")

    def test_the_package_handoff_is_the_address_and_it_is_pointed_at(self):
        self.assertCarries(self.body(), (
            "`WINDOW.md`'s *The wall*, step 2", "hangs on an item still open",
        ), "the address the texts go to is not named, or the file that owns it "
           "is not pointed at")


class TheDispatchPrompt(DocTest):
    def body(self):
        return self.section(DISPATCH)

    def test_the_suite_is_ordered_in_the_foreground_with_a_timeout(self):
        self.assertCarries(self.body(), (
            "run every suite in the FOREGROUND", "declared timeout",
            "ends its turn there and returns announcing the wait",
        ), "the run is free to fire its suite in the background, which is the two "
           "empty returns of the first fleet run")

    def test_the_empty_return_points_at_the_step_that_grades_it(self):
        self.assertIn("Step 5 is where an empty return is graded", self.body(),
                      "the prompt prevents the empty return without naming what "
                      "grades one that arrives anyway")

    def test_the_step_it_points_at_really_grades_one(self):
        """A pointer is only as good as what sits at the other end. Step 5 is the
        fleet's own, so this is a check the file can answer about itself."""
        self.assertIn("A run may return empty", self.section(FAILS),
                      "step 5 no longer covers the empty return the prompt sends "
                      "readers to it for")

    def test_the_prompt_orders_the_texts_written_before_the_done(self):
        self.assertCarries(self.body(), (
            "into the package handoff, BEFORE the `done`",
        ), "a run killed between its `done` and its return again leaves its text "
           "in no queue at all")

    def test_the_done_when_carries_the_reading_and_the_two_new_orders(self):
        self.assertCarries(self.body(), (
            "a quota reading was taken before each dispatch",
            "the foreground-suite order and the order to write its texts",
        ), "the step's own checklist does not ask for what the step now requires")


class TheStopConditions(DocTest):
    def test_the_fleet_now_has_four_and_the_old_count_is_gone(self):
        # A retraction applies at every site of the claim: the sentence that
        # counted three is the one a reader reaches for.
        body = self.section(FAILS)
        self.assertIn("stop conditions are four", body,
                      "the count was not updated when the ceiling was added")
        self.assertIn("the quota ceiling and the wall", body)
        self.assertNotIn("stop conditions are three", self.flat,
                         "the old count survives somewhere in the file, and the "
                         "two sentences now contradict each other")


class TheClose(DocTest):
    def body(self):
        return self.section(VISTA)

    def test_the_measurement_line_carries_the_ceiling_and_the_readings(self):
        self.assertCarries(self.body(), (
            "carries the **quota ceiling** in force",
            "the default or the user's", "first and last quota readings",
        ), "the run that would recalibrate the ceiling reports no evidence for it")

    def test_the_close_births_the_texts_and_says_so_in_its_checklist(self):
        body = self.body()
        self.assertIn("Birth the texts the runs returned", body,
                      "the close has no step that turns a returned text into an item")
        self.assertIn("born with `--dir`, or is named in the report with the reason "
                      "it could not be", body,
                      "a text that could not be born (an unattended fleet) leaves "
                      "no trace, which is the silence this item was born for")


class WhatTheProseNamesExists(DocTest):
    """The half that is not about wording. A pointer at a file, a bin or a sibling
    section that is not there reads exactly like a pointer that works."""

    def test_the_sibling_files_the_new_prose_points_at_are_there(self):
        for name in ("FINDINGS.md", "WINDOW.md"):
            with self.subTest(file=name):
                self.assertTrue(os.path.isfile(os.path.join(KICKOFF, name)),
                                f"fleet/SKILL.md points at ../kickoff/{name}, which "
                                f"is not there")

    def test_the_quota_bin_exists_and_still_prints_the_age_marker(self):
        path = os.path.join(BIN, "tk-quota")
        self.assertTrue(os.path.isfile(path),
                        "the ceiling is read with a bin that is not there")
        source = read(path)
        self.assertIn(" (read ", source)
        self.assertIn(" ago)", source,
                      "the bin no longer marks a reading's age, so the stale-reading "
                      "rule has nothing to fire on")


if __name__ == "__main__":
    unittest.main()
