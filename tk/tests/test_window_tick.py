#!/usr/bin/env python3
"""Doc-conformance proof for the three tick sections of `../skills/kickoff/WINDOW.md`.

Run: python3 -m unittest discover -s tk/tests   (stdlib only, no deps)

WHAT THE SECTIONS ARE. One mechanism — a periodic tick — carrying three duties the
package of 05-07/09/2026 paid for by not having them: a budget that says what a fire
may dispatch, a context refresh that writes the handoff before the harness compacts,
and a state in which the tick switches itself off because everything left is the
human's.

WHY A GREP TEST AND NOT A FIXTURE. Nothing here has a runnable form: no test can
watch a cron fire, a window fill or a human answer. What CAN be held is that each
rule is still written, each number still carries the measurement that produced it,
and every command and bin the prose names is real. The last of those is the one
check that is not about wording — the bins are asked to exist and `--window` is
asked of the parser, so prose promising a flag nobody built goes red here.

VACUITY GUARD FIRST. Every check cuts a slice on a heading, and a heading that moved
would leave the check reading an empty string and passing. `section()` asserts each
slice non-empty as it is taken, and `test_every_section_the_checks_cut_on_is_there`
refuses the whole file's silence.

WHAT IS NOT PROVED HERE. That any orchestrator runs a tick, that the floors are the
right numbers, or that the hooks are wired into `~/.claude/settings.json` — the
wiring lives in a file this repository does not own and is measured by running a
session. The hooks' own behaviour is proved in `test_compact_hooks.py`; this file
only asks that the prose names them and that they exist.
"""

import os
import re
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.join(HERE, os.pardir)
KICKOFF = os.path.join(PLUGIN, "skills", "kickoff")
WINDOW = os.path.join(KICKOFF, "WINDOW.md")
BIN = os.path.join(PLUGIN, "bin")

BUDGET = "The tick, and what one fire may dispatch"
REFRESH = "The scheduled context refresh"
WAITING = "`ESPERANDO-HUMANO`: the state in which the tick turns itself off"
SECTIONS = (BUDGET, REFRESH, WAITING)

# The two Messages API parameters. They may appear in the file ONLY inside the
# paragraph that denies them: named anywhere else, the file is offering a
# mechanism this harness does not have.
API_ONLY = ("compaction_control", "context_token_threshold")
DENIAL = "What does not exist here."


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
        cls.text = read(WINDOW)
        cls.flat = flat(cls.text)

    def section(self, title, raw=False):
        """The body under `## title`, up to the next `## ` — asserted non-empty."""
        pattern = re.compile(r"^## " + re.escape(title) + r"\s*$(.*?)(?=^## |\Z)",
                             re.M | re.S)
        found = pattern.findall(self.text)
        self.assertEqual(len(found), 1,
                         f"`## {title}` is not there exactly once — the checks that "
                         f"cut on it would read an empty string and pass")
        self.assertTrue(found[0].strip(), f"`## {title}` is empty")
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

    def test_the_three_duties_are_one_mechanism(self):
        """Split across three unrelated sections, a reader arms one and not the
        other two. Each of the later two says whose tick it is."""
        for title in (REFRESH, WAITING):
            with self.subTest(section=title):
                self.assertIn("tick", self.section(title))


class TheDispatchBudget(DocTest):
    def body(self):
        return self.section(BUDGET)

    def test_the_opus_ceiling_is_the_site_key_and_never_a_number_here(self):
        # `fleet/SKILL.md` §3: a ceiling written by hand is a fork of the policy.
        # The key already reaches every dispatched run through tk-contract, so
        # what this file owes is the key's NAME and the measurement beside it.
        self.assertCarries(self.body(), (
            "max-local-subagents", "~/.claude/tk/env", "../../bin/tk-contract",
            "is a fork of the policy",
        ), "the Opus ceiling is not written as the site key the contract reads")

    def test_the_sibling_measurement_is_named_and_not_duplicated(self):
        self.assertIn("T270", self.body(),
                      "the measurement that recalibrates the key is unnamed, so the "
                      "next reader recalibrates it here instead")

    def test_each_of_the_four_numbers_carries_what_measured_it(self):
        self.assertCarries(self.body(), (
            # the ceiling
            "20→41% in 25 minutes", "56→70% in 14 minutes",
            # nothing below 15%
            "below 15% of the window remaining",
            # no review below 35%
            "No review is dispatched below 35%", "~150k tokens thrown away",
            # and what a review costs in wall-clock time
            "A review is 25 to 45 minutes",
        ), "a number stands with no measurement behind it, and reads as a preference")

    def test_the_review_is_what_fits_the_short_slot(self):
        self.assertIn("fits a short slot where a lane does not fit", self.body(),
                      "without it the hour before a reset is left idle, which is "
                      "the whole reason the duration is written down")

    def test_the_tick_is_periodic_and_says_why_it_is_not_aimed_at_the_reset(self):
        body = self.body()
        self.assertIn("never aimed at the reset", body)
        self.assertIn("15:20, 20:30, 01:40 and 06:50", body,
                      "the four observed resets are gone, so the claim that they "
                      "are not a grid has nothing behind it")
        self.assertIn("22:20", body,
                      "the cron that missed is not named — the rule reads as taste")

    def test_the_claims_are_crossed_by_script_and_the_divergence_is_acted_on(self):
        body = self.body()
        self.assertIn('`tk-queue list --dir "<queue dir>"`', body,
                      "the conference is prescribed without the command that "
                      "performs it, which makes it an act of memory again")
        self.assertIn("ROOT-CAUSE.md", body,
                      "the plan the queue is crossed against is unnamed")
        self.assertCarries(body, (
            "an item dispatched with no claim", "a claim with nothing dispatched",
            "writes the missing claim before its next dispatch",
            "releases the idle claim or re-dispatches its item",
        ), "the tick names a divergence and never says what it does about it")

    def test_a_reading_and_a_floor_are_not_treated_alike(self):
        body = self.body()
        self.assertIn("A READING is a measurement", body)
        self.assertIn("`tk-quota --estimate --opus <n>`", body,
                      "the floor is described without the mode that produces it")
        self.assertIn("may only ever FORBID a dispatch and never authorise one", body,
                      "the asymmetry is the whole difference: a lower bound on "
                      "spend cannot license a dispatch")

    def test_the_third_mode_is_the_floor_anchored_at_the_reset(self):
        # The bin returns no number for a window that reset with nobody
        # rendering. Inside a package that is exactly the state a tick wakes
        # into, and the boundaries are fixed and known.
        body = self.body()
        self.assertIn("The third mode is the reset", body)
        self.assertIn("anchors a floor of 0% at the reset", body,
                      "the reset case falls back to 'no number', which is the "
                      "state a whole package can sit in until a human types")
        self.assertIn("window boundaries are fixed and known", body,
                      "the reason the floor is computable at all is gone")

    def test_the_floors_do_not_contradict_the_wall(self):
        body = self.body()
        self.assertIn("The wall", body)
        self.assertIn("runs them unchanged", body,
                      "the section does not say how it sits beside the wall's own "
                      "five steps, which is where a reader looks for a conflict")


class TheScheduledRefresh(DocTest):
    def body(self):
        return self.section(REFRESH)

    def test_the_trigger_is_the_tick_and_the_failed_schedule_is_named(self):
        body = self.body()
        self.assertIn("The trigger is the tick, and not a schedule of its own", body)
        self.assertIn("2026-09-06 never ran", body,
                      "the failure that decided this is gone, and a scheduled "
                      "compact reads as the obvious design again")

    def test_the_ceiling_is_absolute_and_says_why_a_fraction_is_wrong(self):
        body = self.body()
        self.assertIn("never a fraction", body)
        self.assertIn("293k", body)
        self.assertIn("29%", body,
                      "the reason is stated without the pair that makes it "
                      "concrete: the same ceiling wearing the look of room")

    def test_the_condition_that_separates_handoff_from_compact_is_the_site(self):
        # A cold reader has to choose between two rules this file gives, and the
        # condition is not "a long package": it is whether the site names a
        # vehicle for the next generation.
        body = self.body()
        self.assertIn("~/.claude/tk/kickoff.md", body)
        self.assertIn("The vehicle that opens the next generation", body,
                      "the rule that already owns the vehicle is not pointed at, "
                      "so the two answers sit in the file unreconciled")
        self.assertIn("Where it names none, the compact is what keeps ONE generation "
                      "alive", body,
                      "the second half of the condition is missing, and a reader "
                      "with no vehicle has no answer at all")

    def test_the_compact_is_the_harnesss_key_and_the_key_is_what_is_prescribed(self):
        self.assertCarries(self.body(), (
            "autoCompactWindow", "CLAUDE_CODE_AUTO_COMPACT_WINDOW",
            "takes effect in the NEXT session", "1M on Fable",
            "prescribes the KEY and never a number in prose",
        ), "the harness's own switch is described wrongly, or a number is "
           "prescribed where the key belongs")

    def test_the_three_pieces_are_the_tick_and_the_two_hooks(self):
        self.assertCarries(self.body(), (
            "../../bin/tk-context --window",
            "`PreCompact` hook, matcher `auto`", "../../bin/tk-compact-mark",
            "`SessionStart` hook, matcher `compact`", "../../bin/tk-compact-pointer",
            "INJECTED",
        ), "a piece of the refresh is unnamed, or its matcher is — and a hook "
           "wired on the wrong matcher fires on sessions it has nothing to say to")

    def test_every_bin_the_section_names_exists(self):
        # The one check here that is not about wording. Prose promising a bin
        # nobody wrote reads exactly like prose that works.
        for name in ("tk-context", "tk-compact-mark", "tk-compact-pointer"):
            with self.subTest(bin=name):
                self.assertTrue(os.path.isfile(os.path.join(BIN, name)),
                                f"WINDOW.md sends the tick to bin/{name}, which is "
                                f"not there")

    def test_the_window_flag_the_section_prescribes_is_a_real_flag(self):
        run = subprocess.run([sys.executable, os.path.join(BIN, "tk-context"), "--help"],
                             capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("--window", run.stdout,
                      "the tick is told to read the window with a flag the bin's "
                      "parser does not have")

    def test_the_pointer_file_both_hooks_read_is_prescribed_with_its_writer(self):
        body = self.body()
        self.assertIn("~/.claude/state/tk-package.json", body)
        self.assertIn("which the orchestrator writes when the package opens", body,
                      "the file both hooks read has no writer named, so the hooks "
                      "are wired and silent forever")

    def test_the_ceiling_leaves_room_for_the_wrap_up_that_precedes_it(self):
        body = self.body()
        self.assertIn("does not retrigger the compact", body,
                      "a threshold set just under the window makes the summary "
                      "itself cross it — the cookbook's own warning")
        self.assertIn("left OUT of the budget", body)
        self.assertIn("server-side", body,
                      "runs whose cache tokens accumulate across a sampling loop "
                      "are budgeted as though they were conversation")

    def test_the_two_api_parameters_appear_only_where_they_are_denied(self):
        # Not a word ban: the file must be able to SAY they do not exist here,
        # which is what stops the next reader reaching for them. So each mention
        # is required to sit inside the denying paragraph and nowhere else.
        denial = self.body().split(DENIAL)
        self.assertEqual(len(denial), 2,
                         f"the paragraph beginning {DENIAL!r} is gone, and the two "
                         f"API parameters have nothing denying them")
        for name in API_ONLY:
            with self.subTest(parameter=name):
                self.assertNotIn(name, denial[0],
                                 f"`{name}` is named outside the denial, where it "
                                 f"reads as a mechanism this harness offers")
                self.assertIn(name, denial[1])
        self.assertIn("not of this harness", denial[1])


class TheWaitingState(DocTest):
    def body(self):
        return self.section(WAITING)

    def test_what_only_the_human_does_is_listed(self):
        self.assertCarries(self.body(), (
            "the OK to merge a pull request",
            "run on the host",
            "an edit to live configuration",
        ), "the list is what tells the orchestrator the state applies; without it "
           "the state is a mood")

    def test_entering_cancels_the_crons_and_records_the_hour_it_read(self):
        body = self.body()
        self.assertIn("CronDelete", body,
                      "the crons are the motor of the spend, and nothing here "
                      "turns them off")
        self.assertIn("the hour read from `date`", body)
        self.assertIn("the command that turns the tick back on, ready to paste", body,
                      "a state with no exit is a package that ends here")

    def test_goal_check_has_two_exits_and_the_three_rejection_rule(self):
        body = self.body()
        self.assertIn("EXCLUDES what is the human's", body)
        self.assertIn("the hook is switched off when the ledger enters this state", body,
                      "only one of the two exits is written, so a package that "
                      "cannot take it has no second answer")
        self.assertIn("three times running is the signal to stop", body,
                      "the cheap stopping rule is gone — the hook that burned a "
                      "night repeated one rejection dozens of times an hour")

    def test_the_idle_tick_costs_one_turn_and_the_night_is_measured(self):
        body = self.body()
        self.assertIn("An idle tick costs ONE turn", body)
        self.assertCarries(body, ("247 model turns", "95.1M tokens of cache read",
                                  "eight hours", "~385k"),
                           "the measurement is gone, and 'doing nothing is "
                           "expensive' reads as an opinion")
        self.assertCarries(body, ("../../bin/tk-context", "../../bin/tk-quota"),
                           "nothing is named that would make an overspending idle "
                           "session visible")


if __name__ == "__main__":
    unittest.main()
