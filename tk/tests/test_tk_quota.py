#!/usr/bin/env python3
"""Behaviour proof for `../bin/tk-quota`, both halves, and its caller's prose.

Run: python3 -m unittest discover -s tk/tests   (stdlib only, no deps)

WHAT IS ON TRIAL. A number nobody can check by eye. "5h 63% used" is plausible at
any value, so this suite is the only thing between a seam and a confident wrong
figure.

THE FIXTURE IS BUILT BY THE WRITER, NEVER BY HAND. That is the correction this
file exists in: an earlier version hand-built sidecars, and its idea of "window
absent" was *the key is missing* while the writer of the day actually emitted
`{"used_percentage": null}`. The two shapes were never compared, and four
wrong-number defects lived in the gap — every one of them on the writing side,
which had no suite at all. `render()` below runs the real `--write` against a
real payload shape, so a reader that stops understanding what the writer emits
fails here. Hand-built JSON appears only for states the writer CANNOT produce: a
corrupt file, a stale one, a foreign one.

TWO QUESTIONS ARE ASSERTED SEPARATELY, because collapsing them is the modelling
error that was found here: *is the window still open* (`resets_at`) and *is this
reading fresh* (`written_at` against the window's own length). A weekly window
stays open for seven days, so the first question alone lets a six-day-old reading
through.

WHY NOT ASSERT A PERCENTAGE AGAINST A REAL WINDOW. No test can: the true figure
lives in the account, changes every minute and is not reproducible. What IS
reproducible is the arithmetic, the refusals and the shape agreement, so those
are what is asserted. Agreement with a rendered statusline was checked by hand on
2026-09-03 and belongs in the PR, not here.
"""

import json
import os
import re
import subprocess
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TK_DIR = os.path.dirname(HERE)
TK_QUOTA = os.path.join(TK_DIR, "bin", "tk-quota")
KICKOFF = os.path.join(TK_DIR, "skills", "kickoff")

HOUR = 3600
ESCAPE = "\x1b]0;pwned\x07"


def payload(five=8, five_in=HOUR, seven=55, seven_in=4 * 86400, **extra):
    """A statusline payload, in the shape the official schema documents.

    Reset moments are relative: a fixture with a fixed epoch passes today and
    silently becomes a stale-file test some months from now.
    """
    now = time.time()
    limits = {}
    if five is not None:
        limits["five_hour"] = {"used_percentage": five, "resets_at": now + five_in}
    if seven is not None:
        limits["seven_day"] = {"used_percentage": seven, "resets_at": now + seven_in}
    out = {"session_id": "a-session", "rate_limits": limits}
    out.update(extra)
    return out


class QuotaFixture(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "quota.json")
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(self.home.cleanup)

    def run_it(self, *args, stdin=None, path=..., home=None):
        """`path` defaults to this fixture's file; pass None to omit --file."""
        argv = [sys.executable, TK_QUOTA, *args]
        target = self.path if path is ... else path
        if target is not None:
            argv += ["--file", target]
        env = dict(os.environ, HOME=home or self.home.name)
        return subprocess.run(argv, capture_output=True, text=True, env=env,
                              input=json.dumps(stdin) if stdin is not None else "")

    def render(self, source=None, **kw):
        """Produce a sidecar THROUGH THE WRITER, as a real render would."""
        run = self.run_it("--write", stdin=source if source is not None else payload(**kw))
        self.assertEqual(run.returncode, 0, run.stderr)
        return run

    def sidecar(self):
        with open(self.path) as fh:
            return json.load(fh)

    def write_raw(self, text):
        with open(self.path, "w") as fh:
            fh.write(text if isinstance(text, str) else json.dumps(text))


class TheWriter(QuotaFixture):

    def test_both_windows_are_recorded(self):
        self.render(five=8, seven=55)
        got = self.sidecar()
        self.assertEqual(got["five_hour"]["used_percentage"], 8)
        self.assertEqual(got["seven_day"]["used_percentage"], 55)
        self.assertIn("written_at", got)

    def test_a_render_at_the_five_hour_boundary_is_still_recorded(self):
        # Claude Code DROPS a window as it resets, so the render at the boundary
        # carries a live weekly and no 5-hour at all. A writer that records only
        # when the 5-hour is present writes nothing here, and the reader then
        # vouches for the previous weekly — measured, 41% printed against a
        # statusline showing 77% at that same instant.
        self.render(five=None, seven=77)
        got = self.sidecar()
        self.assertNotIn("five_hour", got)
        self.assertEqual(got["seven_day"]["used_percentage"], 77)

    def test_an_absent_window_is_omitted_and_never_written_as_null(self):
        # `null` is what destroyed a good weekly: it is a recorded reading that
        # is not a number, which reads as "we looked and there was nothing".
        #
        # The payload here carries the KEY with null values, not a missing key.
        # That is the shape the old shell writer emitted and the shape a fixture
        # built from the reader's imagination never had — asserting only the
        # missing-key case left the null-writing path unproved.
        source = payload(five=8, seven=None)
        source["rate_limits"]["seven_day"] = {"used_percentage": None, "resets_at": None}
        self.render(source=source)
        self.assertNotIn("seven_day", json.dumps(self.sidecar()))

    def test_a_payload_with_no_window_leaves_a_good_sidecar_alone(self):
        self.render(five=8, seven=55)
        before = self.sidecar()
        run = self.run_it("--write", stdin={"session_id": "s"})
        self.assertEqual(run.returncode, 1, run.stderr)
        self.assertEqual(self.sidecar(), before)

    def test_a_value_carrying_a_backslash_still_writes_parseable_json(self):
        # Built by printf with only `"` stripped, one backslash wrote a file
        # nothing could parse — over a good one, and it stayed broken.
        self.render(source=payload(session_id="a\\b\"c\nd" + ESCAPE))
        self.assertEqual(self.sidecar()["five_hour"]["used_percentage"], 8)

    def test_an_unreadable_payload_records_nothing(self):
        self.render(five=8, seven=55)
        before = self.sidecar()
        run = self.run_it("--write", stdin=None)
        self.assertEqual(run.returncode, 1, run.stderr)
        self.assertEqual(self.sidecar(), before)
        # On the MESSAGE too: swallowing the error into an empty payload lands
        # on the same exit and leaves the same file, so the code alone is green.
        self.assertIn("unreadable payload", run.stderr)

    def test_a_payload_that_is_not_an_object_records_nothing(self):
        run = self.run_it("--write", stdin=[1, 2, 3])
        self.assertEqual(run.returncode, 1, run.stderr)
        self.assertFalse(os.path.exists(self.path))
        # A crash also exits 1 and also writes nothing. What separates a handled
        # refusal from a traceback is the message, so that is what is asserted.
        self.assertIn("not an object", run.stderr)
        self.assertNotIn("Traceback", run.stderr)

    def test_no_temp_file_survives_a_successful_write(self):
        self.render()
        leftovers = [n for n in os.listdir(self.tmp.name) if n.startswith(".quota.")]
        self.assertEqual(leftovers, [])

    def test_an_orphan_temp_file_is_cleared_and_a_fresh_one_is_kept(self):
        # A render killed between mkstemp and replace leaves one behind, and
        # Claude Code cancels the in-flight script on every debounce: 300 kills
        # left 9 of them in a user-data directory, never cleaned.
        old = os.path.join(self.tmp.name, ".quota.old")
        new = os.path.join(self.tmp.name, ".quota.new")
        for name in (old, new):
            open(name, "w").close()
        os.utime(old, (time.time() - 3 * HOUR, time.time() - 3 * HOUR))
        self.render()
        self.assertFalse(os.path.exists(old))
        self.assertTrue(os.path.exists(new))


class TheNumbers(QuotaFixture):

    def test_both_windows_are_printed_on_one_line(self):
        self.render(five=8, five_in=HOUR + 6 * 60 + 30, seven=55)
        run = self.run_it()
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(len(run.stdout.strip().splitlines()), 1)
        self.assertIn("5h 8% used, 1h06m left", run.stdout)
        self.assertIn("7d 55% used", run.stdout)

    def test_the_weekly_window_is_spelled_in_days(self):
        self.render(seven_in=4 * 86400 + 11 * HOUR + 1800)
        self.assertIn("4d11h", self.run_it().stdout)

    def test_a_fractional_percentage_is_truncated_as_the_statusline_truncates(self):
        # Rounded, 99.6 printed `100% used` while the bar the user reads showed
        # 99 — a figure the command cannot vouch for, in the alarming direction.
        self.render(five=99.6)
        run = self.run_it()
        self.assertIn("5h 99% used", run.stdout)
        self.assertNotIn("100%", run.stdout)

    def two_sidecars(self):
        """A distinct reading at the default path and at this fixture's path.

        Both hand-written on purpose. Routing them through the writer lets a
        single mutation move BOTH halves together — `--file` ignored for the
        write as well as the read reads back exactly what it wrote, and the
        test cannot tell which file it used. Measured, as a surviving mutant.
        """
        now = time.time()
        state = os.path.join(self.home.name, ".claude", "state")
        os.makedirs(state, exist_ok=True)
        for target, pct in ((os.path.join(state, "quota.json"), 42), (self.path, 7)):
            with open(target, "w") as fh:
                json.dump({"five_hour": {"used_percentage": pct,
                                         "resets_at": now + HOUR},
                           "written_at": now}, fh)

    def test_the_default_sidecar_is_the_one_read_when_no_flag_is_given(self):
        # The invocation the wall prescribes takes no flags, and every other
        # test here passes --file: with expanduser removed the suite stayed
        # green while the documented invocation was permanently exit 2.
        self.two_sidecars()
        run = self.run_it(path=None)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("5h 42% used", run.stdout)


class AWindowThatCannotBeVouchedFor(QuotaFixture):
    """Two independent questions, and a window failing either is not reported."""

    def stale_reading(self, key, age):
        """A sidecar the writer cannot produce: written before its own window."""
        now = time.time()
        self.write_raw({key: {"used_percentage": 61, "resets_at": now + 86400},
                        "written_at": now - age})

    def test_a_reset_that_has_passed_is_not_a_low_percentage(self):
        self.render(five=4, five_in=-60, seven=None)
        run = self.run_it()
        self.assertEqual(run.returncode, 2, run.stdout)
        self.assertEqual(run.stdout.strip(), "")
        self.assertIn("already reset", run.stderr)

    def test_a_reading_older_than_its_own_window_is_refused(self):
        # The weekly window stays open for seven days, so `resets_at` alone lets
        # a six-day-old reading through: it is open, and it is ancient.
        self.stale_reading("seven_day", 8 * 86400)
        run = self.run_it()
        self.assertEqual(run.returncode, 2, run.stdout)
        self.assertIn("older than the window", run.stderr)

    def test_a_reading_inside_its_own_window_is_reported(self):
        self.stale_reading("seven_day", HOUR)
        self.assertIn("7d 61% used", self.run_it().stdout)

    def test_a_reading_still_inside_its_window_but_days_old_says_how_old(self):
        # It survives both refusals — the window is open, and the reading was
        # taken inside it. It is still two days behind, and the weekly window is
        # seven days wide: without the age the percentage reads as current.
        self.stale_reading("seven_day", 2 * 86400)
        run = self.run_it()
        self.assertIn("7d 61% used", run.stdout)
        self.assertIn("(read 2d00h ago)", run.stdout)

    def test_a_reading_from_this_minute_carries_no_age(self):
        self.render(five=8, seven=None)
        self.assertNotIn("(read", self.run_it().stdout)

    def test_a_sidecar_that_does_not_say_when_it_was_written_is_refused(self):
        now = time.time()
        self.write_raw({"five_hour": {"used_percentage": 10, "resets_at": now + HOUR}})
        run = self.run_it()
        self.assertEqual(run.returncode, 2, run.stdout)
        self.assertIn("when it was written", run.stderr)

    def test_a_percentage_that_is_a_boolean_is_not_a_percentage(self):
        # `isinstance(True, int)` is true, so a bare check prints `5h 1% used`.
        now = time.time()
        self.write_raw({"five_hour": {"used_percentage": True, "resets_at": now + HOUR},
                        "written_at": now})
        self.assertEqual(self.run_it().returncode, 2)

    def test_one_window_refused_still_prints_the_other_and_says_why(self):
        # Silence here is the defect: a line that vanishes is indistinguishable
        # from a question never asked, and the seam cannot tell it lost an answer.
        self.render(five=4, five_in=-60, seven=55)
        run = self.run_it()
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("7d 55% used", run.stdout)
        self.assertNotIn("5h", run.stdout)
        self.assertIn("5h:", run.stderr)


class WhenThereIsNoNumber(QuotaFixture):

    def assert_owed_judgement(self, run):
        self.assertEqual(run.returncode, 2, run.stdout)
        self.assertEqual(run.stdout.strip(), "")
        self.assertIn("judgement", run.stderr)

    def test_no_sidecar_at_all(self):
        # Asserted on the MESSAGE: a missing file also lands on the generic
        # OSError arm, so exit 2 alone is green with the specific guard removed.
        run = self.run_it(path=os.path.join(self.tmp.name, "nope.json"))
        self.assert_owed_judgement(run)
        self.assertIn("rendered a statusline", run.stderr)

    def test_a_sidecar_that_is_not_json(self):
        self.write_raw("{half written")
        self.assert_owed_judgement(self.run_it())

    def test_a_sidecar_that_is_not_an_object(self):
        self.write_raw("[1, 2, 3]")
        self.assert_owed_judgement(self.run_it())


class WhatComesFromOutsideThisProcess(QuotaFixture):
    """Every arm that echoes a value, not just the one a test happened to hit."""

    def test_the_missing_file_arm_prints_flat(self):
        run = self.run_it(path=os.path.join(self.tmp.name, f"no{ESCAPE}pe.json"))
        self.assertEqual(run.returncode, 2, run.stdout)
        self.assertNotIn("\x1b", run.stderr)

    def test_the_unreadable_file_arm_prints_flat(self):
        os.mkdir(os.path.join(self.tmp.name, f"d{ESCAPE}ir"))
        run = self.run_it(path=os.path.join(self.tmp.name, f"d{ESCAPE}ir"))
        self.assertEqual(run.returncode, 2, run.stdout)
        self.assertNotIn("\x1b", run.stderr)

    def test_the_every_window_refused_arm_prints_flat(self):
        self.path = os.path.join(self.tmp.name, f"q{ESCAPE}.json")
        self.render(five=4, five_in=-60, seven=None)
        run = self.run_it()
        self.assertEqual(run.returncode, 2, run.stdout)
        self.assertNotIn("\x1b", run.stderr)


class TheEdgesOfTheContract(QuotaFixture):

    def test_the_file_flag_is_the_file_that_gets_read(self):
        TheNumbers.two_sidecars(self)
        run = self.run_it()
        self.assertIn("5h 7% used", run.stdout)
        self.assertNotIn("42%", run.stdout)

    def test_a_mistyped_flag_does_not_read_as_no_number(self):
        self.render()
        self.assertEqual(self.run_it("--no-such-flag").returncode, 64)


class TheProseThatCallsIt(unittest.TestCase):
    """A command no instruction names is a command nobody runs."""

    def setUp(self):
        with open(os.path.join(KICKOFF, "WINDOW.md")) as fh:
            self.window = re.sub(r"\s+", " ", fh.read())

    def test_the_wall_sends_the_reader_to_the_command(self):
        self.assertIn("tk-quota", self.window)

    def test_the_wall_says_the_reading_can_be_a_previous_windows(self):
        # BOTH halves, anchored to this command's paragraph: that the reading can
        # belong to a window that ended, AND that the command refuses instead of
        # reporting it. An earlier draft matched the bare words "exits 2", which
        # `tk-context`'s own bullet carries a few paragraphs up.
        self.assertRegex(self.window, r"tk-quota.{0,1400}?previous window")
        self.assertRegex(self.window, r"tk-quota.{0,800}?exits 2 rather than report")

    def test_the_wall_says_an_old_reading_announces_its_age(self):
        # The refusals are two; the age is a third thing, disclosed and not
        # refused. A wall naming only the refusals lets a days-old percentage
        # be read as the current one.
        self.assertRegex(self.window, r"tk-quota.{0,1600}?read 4d02h ago")

    def test_the_wall_describes_the_partial_answer(self):
        # exit 0 can print ONE window. A seam told only about exit 2 reads the
        # surviving line as the whole answer.
        self.assertRegex(self.window, r"tk-quota.{0,1400}?one window")


if __name__ == "__main__":
    unittest.main()
