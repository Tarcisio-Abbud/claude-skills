#!/usr/bin/env python3
"""Behaviour proof for `../bin/tk-quota`, and doc conformance for its caller.

Run: python3 -m unittest discover -s tk/tests   (stdlib only, no deps)

WHAT IS ON TRIAL. A number nobody can check by eye. "5h 63% used" is plausible
at any value, so the only thing standing between a seam and a confident wrong
figure is this suite.

THE STALENESS RULE IS THE SUBJECT. Everything else here is bookkeeping. The
sidecar is written only while some session renders a statusline, so a window
nobody sat through leaves the file holding the PREVIOUS window's percentage —
which reads exactly like a fresh one and is off by a whole window. Refusing on
`resets_at` is what makes the command safe to believe, and half the tests below
exist to keep that refusal from being softened into a fallback.

WHY NOT ASSERT THE PERCENTAGE AGAINST A REAL WINDOW. No test can: the true
figure lives in the account, changes every minute, and is not reproducible. What
IS reproducible is the arithmetic and the refusals, so those are what is asserted
— the number's agreement with reality was checked by rendering a statusline and
comparing, on 2026-09-03, and belongs in the PR, not here.
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


def sidecar(five=8, five_in=HOUR, seven=55, seven_in=4 * 86400, written_ago=60):
    """A sidecar as the statusline writes it, with reset moments relative to now.

    Relative, never fixed: a fixture with a hard-coded epoch passes today and
    turns into a stale-file test some months from now, silently.
    """
    now = time.time()
    out = {"written_at": now - written_ago, "written_by": "a-session"}
    if five is not None:
        out["five_hour"] = {"used_percentage": five, "resets_at": now + five_in}
    if seven is not None:
        out["seven_day"] = {"used_percentage": seven, "resets_at": now + seven_in}
    return out


class QuotaFixture(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "quota.json")
        self.addCleanup(self.tmp.cleanup)

    def write(self, payload):
        with open(self.path, "w") as fh:
            json.dump(payload, fh) if isinstance(payload, dict) else fh.write(payload)

    def run_it(self, *args, path=None):
        return subprocess.run(
            [sys.executable, TK_QUOTA, "--file", path or self.path, *args],
            capture_output=True, text=True)


class TheNumbers(QuotaFixture):

    def test_both_windows_are_printed_on_one_line(self):
        # +30s past the minute boundary on purpose. The remaining time is
        # TRUNCATED, as the statusline's own `eta` truncates, so a fixture
        # landing exactly on 1h06m flips to 1h05m the instant the clock moves —
        # a test that fails on its own slowness. The margin buys 30 seconds.
        self.write(sidecar(five=8, five_in=HOUR + 6 * 60 + 30, seven=55))
        run = self.run_it()
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(len(run.stdout.strip().splitlines()), 1)
        self.assertIn("5h 8% used, 1h06m left", run.stdout)
        self.assertIn("7d 55% used", run.stdout)

    def test_the_weekly_window_is_spelled_in_days(self):
        # 4d11h, not 107h. The seam reads this to decide whether to start work.
        self.write(sidecar(seven_in=4 * 86400 + 11 * HOUR + 1800))
        self.assertIn("4d11h", self.run_it().stdout)

    def test_a_fractional_percentage_is_rendered_whole(self):
        self.write(sidecar(five=8.4))
        self.assertIn("5h 8% used", self.run_it().stdout)


class WhenTheFileIsAPreviousWindows(QuotaFixture):
    """The failure the whole command is built around."""

    def test_a_reset_that_has_passed_is_not_a_low_percentage(self):
        # 4% left over from a window that ended reads as a nearly-empty window.
        self.write(sidecar(five=4, five_in=-60, seven=None))
        run = self.run_it()
        self.assertEqual(run.returncode, 2, run.stdout)
        self.assertEqual(run.stdout.strip(), "")
        self.assertIn("previous window", run.stderr)

    def test_the_refusal_says_how_old_the_file_is(self):
        self.write(sidecar(five=4, five_in=-60, seven=None, written_ago=3 * HOUR))
        self.assertIn("3h00m ago", self.run_it().stderr)

    def test_a_stale_five_hour_still_reports_a_live_weekly_and_says_so(self):
        # The weekly window outlives many 5-hour ones, so it is still true.
        self.write(sidecar(five=4, five_in=-60, seven=55))
        run = self.run_it()
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("7d 55% used", run.stdout)
        self.assertNotIn("5h", run.stdout)
        self.assertIn("only the weekly", run.stderr)


class WhenThereIsNoNumber(QuotaFixture):

    def assert_owed_judgement(self, run):
        self.assertEqual(run.returncode, 2, run.stdout)
        self.assertEqual(run.stdout.strip(), "")
        self.assertIn("judgement", run.stderr)

    def test_no_sidecar_at_all(self):
        # Asserted on the MESSAGE, not just the exit. A missing file also lands
        # on the generic OSError arm, so exit 2 alone is green with the specific
        # guard removed — measured as a surviving mutant. What the caller needs
        # is the difference: nothing has rendered yet, versus a file gone bad.
        run = self.run_it(path=os.path.join(self.tmp.name, "nope.json"))
        self.assert_owed_judgement(run)
        self.assertIn("rendered a statusline", run.stderr)

    def test_a_sidecar_that_is_not_json(self):
        self.write("{half written")
        self.assert_owed_judgement(self.run_it())

    def test_a_sidecar_that_is_not_an_object(self):
        self.write("[1, 2, 3]")
        self.assert_owed_judgement(self.run_it())

    def test_a_percentage_that_is_not_a_number_is_not_a_window(self):
        payload = sidecar(seven=None)
        payload["five_hour"]["used_percentage"] = "lots"
        self.write(payload)
        self.assert_owed_judgement(self.run_it())

    def test_a_reset_that_is_not_a_number_is_not_a_window(self):
        payload = sidecar(seven=None)
        payload["five_hour"]["resets_at"] = "soon"
        self.write(payload)
        self.assert_owed_judgement(self.run_it())


class TheEdgesOfTheContract(QuotaFixture):

    def test_the_file_flag_is_the_file_that_gets_read(self):
        other = os.path.join(self.tmp.name, "other.json")
        with open(other, "w") as fh:
            json.dump(sidecar(five=99, seven=None), fh)
        self.write(sidecar(five=8, seven=None))
        self.assertIn("99%", self.run_it(path=other).stdout)

    def test_a_mistyped_flag_does_not_read_as_no_number(self):
        self.write(sidecar())
        self.assertEqual(self.run_it("--no-such-flag").returncode, 64)

    def test_a_control_character_in_the_file_is_printed_flat(self):
        # The path reaches stderr on the refusal, and a directory NAME carrying
        # an escape is the measured case in this house.
        run = self.run_it(path=os.path.join(self.tmp.name, "no\x1b]0;pwned\x07pe.json"))
        self.assertEqual(run.returncode, 2, run.stdout)
        self.assertNotIn("\x1b", run.stderr)


class TheProseThatCallsIt(unittest.TestCase):
    """A command no instruction names is a command nobody runs — the finding the
    Spec axis raised against `tk-context --curve`, answered here in advance."""

    def test_the_wall_sends_the_reader_to_the_command(self):
        with open(os.path.join(KICKOFF, "WINDOW.md")) as fh:
            window = fh.read()
        self.assertIn("tk-quota", window)

    def test_the_wall_says_the_reading_can_be_a_previous_windows(self):
        # Without this the reader trusts a figure the command would have refused.
        #
        # Tied to THIS command's paragraph. An earlier draft matched the bare
        # words "exits 2", which `tk-context`'s own bullet carries a few
        # paragraphs up — the assertion was green with the whole warning gone.
        with open(os.path.join(KICKOFF, "WINDOW.md")) as fh:
            window = re.sub(r"\s+", " ", fh.read())
        # BOTH halves, and both anchored to this command's paragraph: that the
        # file can belong to a window that ended, AND that the command refuses
        # instead of reporting it. Asserting only the first left a mutant alive
        # that deleted the refusal and kept the description.
        self.assertRegex(window, r"tk-quota.{0,1200}?PREVIOUS window's percentage")
        self.assertRegex(window, r"tk-quota.{0,600}?exits 2 rather than report")


if __name__ == "__main__":
    unittest.main()
