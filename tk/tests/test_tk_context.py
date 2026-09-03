#!/usr/bin/env python3
"""Behaviour proof for `../bin/tk-context`, and doc conformance for its callers.

Run: python3 -m unittest discover -s tk/tests   (stdlib only, no deps)

WHAT IS ON TRIAL. A number an orchestrator compares against a threshold. Three
things can go wrong with it and each has its own test: the arithmetic can count
the wrong tokens, the resolution can read another session's file, and the
presentation can invite the comparison the rule forbids.

THE FORMULA IS THE CLAIM. `input + cache_creation + cache_read`, output tokens
excluded, is what the official statusline documentation declares for
`context_window.total_input_tokens`. Adding output would be invisible on a real
transcript — a few hundred tokens against six figures — and would silently stop
matching the statusline it is checked against, so it is asserted on a fixture
where the output count is large enough to change the answer.

NO PERCENTAGE, ASSERTED. The threshold measures the smart zone, not the window's
capacity, so a fraction is the wrong comparison on a 1M-context model and the
right-looking one. Nothing but a test keeps a helpful `(29%)` out of the output.

WHAT THESE TESTS CANNOT SEE. Whether the number matches the live statusline —
that is measured by rendering one, and it was, twice, on 2026-09-03 (the script's
docstring carries both readings). Nor whether an orchestrator RUNS the command at
a seam: no test here can watch a session. That half is held by the prose the last
test reads, and by the review.
"""

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TK_DIR = os.path.dirname(HERE)
TK_CONTEXT = os.path.join(TK_DIR, "bin", "tk-context")
KICKOFF = os.path.join(TK_DIR, "skills", "kickoff")

SESSION = "11111111-2222-3333-4444-555555555555"


def usage_line(session_ok=True, **counts):
    """One assistant entry carrying a usage block, as the transcript writes it."""
    record = {"type": "assistant", "timestamp": "2026-09-03T12:00:00.000Z",
              "message": {"model": "claude-opus-5", "usage": counts}}
    if not session_ok:
        record["isSidechain"] = True
    return json.dumps(record)


class TranscriptFixture(unittest.TestCase):
    """A HOME of its own, holding one session's transcript where the script looks."""

    def setUp(self):
        self.home = tempfile.TemporaryDirectory()
        self.project = os.path.join(self.home.name, ".claude", "projects", "-workspace-projects")
        os.makedirs(self.project)
        self.transcript = os.path.join(self.project, f"{SESSION}.jsonl")
        self.addCleanup(self.home.cleanup)

    def write(self, *lines):
        with open(self.transcript, "w") as fh:
            fh.write("\n".join(lines) + "\n")

    def run_it(self, *args, session=SESSION):
        env = dict(os.environ, HOME=self.home.name)
        env.pop("CLAUDE_CODE_SESSION_ID", None)
        if session:
            env["CLAUDE_CODE_SESSION_ID"] = session
        return subprocess.run([sys.executable, TK_CONTEXT, *args],
                              capture_output=True, text=True, env=env)


class TheNumber(TranscriptFixture):

    def test_the_three_input_counters_are_summed_and_output_is_left_out(self):
        # Output is 9000 here: an implementation that added it would print
        # 12000, and no real transcript would make that difference visible.
        self.write(usage_line(input_tokens=1000, cache_creation_input_tokens=500,
                              cache_read_input_tokens=1500, output_tokens=9000))
        run = self.run_it()
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("3000", run.stdout)
        self.assertNotIn("12000", run.stdout)

    def test_the_newest_entry_wins_over_every_older_one(self):
        self.write(usage_line(input_tokens=10, cache_read_input_tokens=90),
                   usage_line(input_tokens=10, cache_read_input_tokens=7990))
        run = self.run_it()
        self.assertIn("8000", run.stdout)
        self.assertNotIn("100 tokens", run.stdout)

    def test_a_sidechain_entry_is_not_this_session(self):
        # A subagent's entry, were one ever written here, measures its window.
        self.write(usage_line(input_tokens=10, cache_read_input_tokens=7990),
                   usage_line(session_ok=False, input_tokens=10,
                              cache_read_input_tokens=499990))
        run = self.run_it()
        self.assertIn("8000", run.stdout)
        self.assertNotIn("500000", run.stdout)

    def test_a_half_written_last_line_costs_nothing(self):
        # The transcript is appended to live; the reading must survive landing
        # mid-write rather than crashing the seam that asked for the number.
        with open(self.transcript, "w") as fh:
            fh.write(usage_line(input_tokens=10, cache_read_input_tokens=7990) + "\n")
            fh.write('{"type": "assistant", "message": {"usa')
        run = self.run_it()
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("8000", run.stdout)

    def test_the_output_carries_no_percentage(self):
        # A fraction of the window is the comparison the rule forbids: on a
        # 1M-context model it reads as room the smart zone does not have.
        self.write(usage_line(input_tokens=10, cache_read_input_tokens=7990))
        run = self.run_it()
        self.assertNotIn("%", run.stdout)


class WhenThereIsNoNumber(TranscriptFixture):
    """Every failing path exits 2 and names what the caller owes instead."""

    def assert_owed_judgement(self, run):
        self.assertEqual(run.returncode, 2, run.stdout)
        self.assertEqual(run.stdout.strip(), "")
        self.assertIn("judgement", run.stderr)

    def test_no_session_id_in_the_environment(self):
        self.assert_owed_judgement(self.run_it(session=None))

    def test_no_transcript_for_this_session(self):
        self.assert_owed_judgement(self.run_it(session="00000000-dead-beef-0000-000000000000"))

    def test_a_transcript_with_no_api_response_yet(self):
        self.write(json.dumps({"type": "user", "message": {"role": "user"}}))
        self.assert_owed_judgement(self.run_it())


class TheCurve(TranscriptFixture):

    def test_the_curve_goes_to_stderr_and_leaves_stdout_the_bare_number(self):
        # stdout is what a caller compares or pipes; the slope is commentary.
        self.write(*[usage_line(input_tokens=n, cache_read_input_tokens=0)
                     for n in (1000, 2000, 3000, 4000)])
        run = self.run_it("--curve")
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stdout.strip(), "4000 tokens in context")
        self.assertIn("1,000", run.stderr)
        self.assertIn("+1000", run.stderr)

    def test_without_the_flag_nothing_but_the_number_is_printed(self):
        self.write(*[usage_line(input_tokens=n) for n in (1000, 2000)])
        run = self.run_it()
        self.assertEqual(run.stderr.strip(), "")


class TheProseThatCallsIt(unittest.TestCase):
    """The command is worth nothing unless the seam's instruction names it."""

    def read(self, name):
        with open(os.path.join(KICKOFF, name)) as fh:
            return fh.read()

    def test_window_and_afk_send_the_seam_to_the_command(self):
        for name in ("WINDOW.md", "AFK.md"):
            with self.subTest(file=name):
                self.assertIn("tk-context", self.read(name))

    def test_no_seam_still_sends_the_reader_to_the_statusline(self):
        # The defect this whole change answers: an instruction asking for a
        # reading the harness cannot give, obeyed by nobody for three
        # generations and then cited as though it had been.
        #
        # NOT a word ban. WINDOW.md must still be able to say the number is NOT
        # there — that sentence is what stops the next reader going to look. So
        # the assertion reads what stands in front of the mention, and only a
        # NEGATED one survives. Both directions are asserted below on synthetic
        # text, so a lookbehind that stopped matching would not pass silently.
        for name in ("WINDOW.md", "AFK.md"):
            with self.subTest(file=name):
                self.assertIsNone(self.sends_to_the_statusline(self.read(name)))

    @staticmethod
    def sends_to_the_statusline(text):
        """The first mention that is not a denial, or None.

        Every preposition the two files reach for, not just one: the shipped
        defect in AFK.md read "from the statusline", and a reader watching only
        for "in the statusline" let that exact sentence back in — measured, as a
        surviving mutant, before this line said `in|from|on`. Whitespace-folded
        because these files wrap at 96 columns and a phrase splits across lines.
        """
        return re.search(r"(?<!not )(?:in|from|on) the statusline",
                         re.sub(r"\s+", " ", text))

    def test_the_reading_of_that_assertion_goes_both_ways(self):
        self.assertIsNone(self.sends_to_the_statusline("It is not in the statusline."))
        self.assertIsNotNone(self.sends_to_the_statusline("The number is in the\n  statusline."))
        self.assertIsNotNone(self.sends_to_the_statusline("read from the statusline at that seam"))

    def test_window_states_that_the_threshold_is_absolute(self):
        # Without this the next generation reads 29% of a 1M window as room.
        window = self.read("WINDOW.md")
        self.assertIn("smart zone", window)
        self.assertRegex(window, r"never a fraction")

    def test_window_licenses_judgement_only_when_it_is_declared(self):
        # Tied to the no-number rule on purpose. An earlier draft asserted the
        # bare words "says so", which occur in an unrelated bullet of the same
        # file — the assertion was green with the whole licence deleted.
        window = re.sub(r"\s+", " ", self.read("WINDOW.md"))
        self.assertRegex(window, r"no number.{0,400}?names it as judgement")


if __name__ == "__main__":
    unittest.main()
