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

import importlib.machinery
import importlib.util
import inspect
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


def usage_line(session_ok=True, stamp="2026-09-03T12:00:00.000Z", **counts):
    """One assistant entry carrying a usage block, as the transcript writes it."""
    record = {"type": "assistant", "timestamp": stamp,
              "message": {"model": "claude-opus-5", "usage": counts}}
    if not session_ok:
        record["isSidechain"] = True
    return json.dumps(record)


def boundary_line(post=10340, stamp="2026-09-03T13:00:00.000Z"):
    """A compaction boundary, copied from a real transcript's shape: no `usage`
    anywhere in it, and the emptied window in `compactMetadata.postTokens`."""
    return json.dumps({"type": "system", "subtype": "compact_boundary",
                       "timestamp": stamp, "content": "Conversation compacted",
                       "compactMetadata": {"trigger": "manual",
                                           "preTokens": 264286,
                                           "postTokens": post}})


def load_tk_context():
    """The bin as a module, so a constant is read and never retyped here."""
    spec = importlib.util.spec_from_loader(
        "tk_context", importlib.machinery.SourceFileLoader("tk_context", TK_CONTEXT))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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

    def run_it(self, *args, session=SESSION, env=None):
        override = env or {}
        env = dict(os.environ, HOME=self.home.name)
        env.pop("CLAUDE_CODE_SESSION_ID", None)
        # Inherited from whoever ran the suite, this variable decides the window
        # under test. Cleared first, then the case sets what it means to set.
        env.pop("CLAUDE_CODE_AUTO_COMPACT_WINDOW", None)
        env.update(override)
        if session:
            env["CLAUDE_CODE_SESSION_ID"] = session
        return subprocess.run([sys.executable, TK_CONTEXT, *args],
                              capture_output=True, text=True, env=env,
                              cwd=self.home.name)


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


class AfterACompaction(TranscriptFixture):
    """The record class that carries the truth and no `usage` field.

    Measured on a real transcript before this was read: the last usage row said
    263,729 and the boundary written after it said 10,340. A reader that filters
    for `usage` prints the emptied window's PREDECESSOR, at exit 0, and looks
    exactly as sure as it does when it is right.
    """

    def test_a_boundary_newer_than_the_last_response_decides_the_number(self):
        self.write(usage_line(stamp="2026-09-03T12:00:00Z", cache_read_input_tokens=263729),
                   boundary_line(post=10340, stamp="2026-09-03T13:00:00Z"))
        run = self.run_it()
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("10340", run.stdout)
        self.assertNotIn("263729", run.stdout)

    def test_the_reading_says_it_came_from_a_boundary(self):
        # The one case where the number is not an API response's. A seam that
        # cannot tell cannot judge the reading, and this is the reading a filter
        # got wrong by 25x.
        self.write(usage_line(cache_read_input_tokens=263729), boundary_line())
        self.assertIn("compaction", self.run_it().stderr)

    def test_a_response_after_the_boundary_takes_it_back(self):
        self.write(usage_line(stamp="2026-09-03T12:00:00Z", cache_read_input_tokens=263729),
                   boundary_line(stamp="2026-09-03T13:00:00Z"),
                   usage_line(stamp="2026-09-03T14:00:00Z", cache_read_input_tokens=41000))
        self.assertIn("41000", self.run_it().stdout)

    def test_a_boundary_with_no_usable_count_refuses_and_does_not_fall_back(self):
        # The malformed case walks the closed defect back in if it falls through:
        # the pre-compaction row would win, at exit 0, over a window that was
        # emptied. What is known is that it was emptied; what is not known is to
        # what. `response_tokens` refuses on the analogous malformed counter and
        # the two classes must not disagree about that.
        self.write(usage_line(cache_read_input_tokens=263729), boundary_line(post=None))
        run = self.run_it()
        self.assertEqual(run.returncode, 2, run.stdout)
        self.assertNotIn("263729", run.stdout)
        self.assertIn("judgement", run.stderr)


class RecordsThatLookLikeAnOccupancyAndAreNot(TranscriptFixture):

    def test_an_all_zero_usage_block_is_skipped(self):
        # A synthetic reply — the rate-limit message — carries one. Taken, it
        # prints `0 tokens in context` over a real window and the seam sails on.
        self.write(usage_line(cache_read_input_tokens=190916),
                   usage_line(input_tokens=0, cache_creation_input_tokens=0,
                              cache_read_input_tokens=0, output_tokens=0))
        run = self.run_it()
        self.assertIn("190916", run.stdout)
        self.assertNotIn("0 tokens", run.stdout)

    def test_a_counter_that_is_not_a_number_refuses_rather_than_reports_an_older_window(self):
        # Refusing beats falling back: skipping the row would print the PREVIOUS
        # window's 8,000 as though it were current, which is a wrong number.
        self.write(usage_line(cache_read_input_tokens=8000),
                   usage_line(input_tokens="lots", cache_read_input_tokens=190000))
        run = self.run_it()
        self.assertEqual(run.returncode, 2, run.stdout)
        self.assertNotIn("8000", run.stdout)

    def test_a_counter_written_as_a_numeric_string_is_still_a_number(self):
        # Coerced, not refused: the value is unambiguous, and refusing it would
        # send a seam to judgement while the number sits there readable.
        self.write(usage_line(input_tokens="10", cache_read_input_tokens=7990))
        run = self.run_it()
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("8000", run.stdout)

    def test_a_byte_the_encoding_cannot_hold_costs_nothing(self):
        with open(self.transcript, "wb") as fh:
            fh.write(b'{"type": "system", "content": "\xff\xfe"}\n')
            fh.write(usage_line(cache_read_input_tokens=8000).encode() + b"\n")
        run = self.run_it()
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("8000", run.stdout)


class ResolvingTheFile(TranscriptFixture):

    def test_a_session_id_is_a_literal_and_never_a_glob(self):
        # `--session '*'` matched a stranger's transcript and printed its number
        # at exit 0 — a confident wrong answer about another session's window.
        self.write(usage_line(cache_read_input_tokens=8000))
        run = self.run_it(session="*")
        self.assertEqual(run.returncode, 2, run.stdout)
        self.assertNotIn("8000", run.stdout)

    def test_two_transcripts_for_one_id_are_refused_and_both_named(self):
        # Sorting picks a winner in silence, and the loser is as likely to be
        # the live session as the stale one.
        self.write(usage_line(cache_read_input_tokens=8000))
        second = os.path.join(self.home.name, ".claude", "projects", "-other")
        os.makedirs(second)
        with open(os.path.join(second, f"{SESSION}.jsonl"), "w") as fh:
            fh.write(usage_line(cache_read_input_tokens=1000) + "\n")
        run = self.run_it()
        self.assertEqual(run.returncode, 2, run.stdout)
        self.assertIn("-other", run.stderr)
        self.assertIn("-workspace-projects", run.stderr)

    def test_the_transcript_flag_is_the_file_that_gets_read(self):
        # The one flag that can point at a foreign session by design. Deleting
        # its handling left the whole suite green before this test existed.
        self.write(usage_line(cache_read_input_tokens=8000))
        other = os.path.join(self.home.name, "elsewhere.jsonl")
        with open(other, "w") as fh:
            fh.write(usage_line(cache_read_input_tokens=4242) + "\n")
        run = self.run_it("--transcript", other)
        self.assertIn("4242", run.stdout)
        self.assertNotIn("8000", run.stdout)


class TheExitCodes(TranscriptFixture):

    def test_a_mistyped_flag_does_not_read_as_no_number(self):
        # 2 is "no number, decide by judgement". argparse's own 2 would make a
        # typo indistinguishable from that licence.
        self.write(usage_line(cache_read_input_tokens=8000))
        run = self.run_it("--no-such-flag")
        self.assertEqual(run.returncode, 64, run.stderr)


class WhatComesFromOutsideThisProcess(TranscriptFixture):
    """Four printed values are read from somewhere else. None may reprogram a
    terminal — the sibling case in this house was a directory NAME carrying the
    escape, on a channel whose second output had been added without the gate."""

    ESCAPE = "\x1b]0;pwned\x07"

    def test_a_session_id_carrying_an_escape_is_printed_flat(self):
        run = self.run_it(session=f"nope{self.ESCAPE}")
        self.assertEqual(run.returncode, 2, run.stdout)
        self.assertNotIn("\x1b", run.stderr)

    def test_a_boundary_timestamp_from_the_file_is_printed_flat(self):
        self.write(usage_line(cache_read_input_tokens=8000),
                   boundary_line(stamp=f"2026{self.ESCAPE}-09-03T13:00:00Z"))
        run = self.run_it()
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertNotIn("\x1b", run.stderr)

    def test_a_record_uuid_from_the_file_is_printed_flat(self):
        record = json.loads(usage_line(input_tokens="lots"))
        record["uuid"] = f"abc{self.ESCAPE}"
        self.write(json.dumps(record))
        run = self.run_it()
        self.assertEqual(run.returncode, 2, run.stdout)
        self.assertNotIn("\x1b", run.stderr)


class TheCurve(TranscriptFixture):

    def test_the_curve_goes_to_stderr_and_leaves_stdout_the_bare_number(self):
        # stdout is what a caller compares or pipes; the slope is commentary.
        #
        # TWELVE readings, not four: the curve samples to six rows, and with
        # four it samples every one — the guard that re-adds the newest row
        # never fires, and a mutant deleting it survives. Measured.
        self.write(*[usage_line(input_tokens=n * 1000, cache_read_input_tokens=0)
                     for n in range(1, 13)])
        run = self.run_it("--curve")
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stdout.strip(), "12000 tokens in context")
        self.assertIn("1,000", run.stderr)
        self.assertIn("+2000", run.stderr)
        # the newest row is the slope's whole point: a curve ending short reads
        # as a session that stopped growing
        self.assertIn("12,000", run.stderr)

    def test_without_the_flag_nothing_but_the_number_is_printed(self):
        self.write(*[usage_line(input_tokens=n) for n in (1000, 2000)])
        run = self.run_it()
        self.assertEqual(run.stderr.strip(), "")


class TheWindowChannel(TranscriptFixture):
    """The harness's compaction window, on a channel of its own.

    THE CONFUSION THIS CLASS EXISTS TO REFUSE. Exit 2 is spent by `WINDOW.md` as
    a licence to decide by judgement, and it means one thing: the transcript
    holds no token count. A first draft of this flag reused the same code for
    "no window key was configured" — two conditions, one code, and every seam on
    a host where nobody had set `autoCompactWindow` would have thrown away a
    perfectly good token reading and gone to judgement. The two are asserted
    separately below, and the token-absent case is the one that keeps exit 2.

    The numbers are taken from the bin rather than retyped: a buffer changed in
    one file and not the other is exactly the fork a doc-conformance test cannot
    see.
    """

    def setUp(self):
        super().setUp()
        self.bin = load_tk_context()
        self.settings = os.path.join(self.home.name, ".claude")
        os.makedirs(self.settings, exist_ok=True)

    def write_settings(self, value):
        """`.claude/settings.local.json`, the last file of the merge.

        The fixture's cwd IS its HOME, so the user file and the project file are
        one path here and only the local one is distinguishable. What the order
        buys is asserted where it can be: the environment against the key.
        """
        with open(os.path.join(self.settings, "settings.local.json"), "w") as fh:
            json.dump({"autoCompactWindow": value}, fh)

    def run_window(self, *args, **kw):
        self.write(usage_line(input_tokens=10, cache_read_input_tokens=7990))
        return self.run_it("--window", *args, **kw)

    def test_the_window_and_the_threshold_go_to_stderr_and_stdout_stays_bare(self):
        # stdout is what a seam compares or pipes. A window printed beside the
        # number is a second field every one of those callers has to learn.
        run = self.run_window()
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stdout.strip(), "8000 tokens in context")
        self.assertIn("window", run.stderr)
        self.assertIn(str(self.bin.WINDOW_DEFAULT - self.bin.SUMMARY_BUFFER), run.stderr)

    def test_without_the_flag_a_configured_key_changes_nothing(self):
        # The invocation `WINDOW.md`'s seams already run must keep the output it
        # has, on a host where the key IS set.
        self.write_settings(300000)
        self.write(usage_line(input_tokens=10, cache_read_input_tokens=7990))
        run = self.run_it()
        self.assertEqual(run.stdout.strip(), "8000 tokens in context")
        self.assertEqual(run.stderr.strip(), "")

    # --- the two absences, one code each -------------------------------------

    def test_no_key_and_no_env_var_is_exit_0_and_the_default_marked_as_one(self):
        run = self.run_window()
        self.assertEqual(run.returncode, 0,
                         "an unconfigured window took the exit code that means "
                         "'no token number' — every seam on this host would "
                         "throw away a good reading and go to judgement")
        self.assertIn(str(self.bin.WINDOW_DEFAULT), run.stderr)
        self.assertIn("DEFAULT", run.stderr,
                      "the fallback is printed as though a key had been read")

    def test_no_token_in_the_transcript_is_still_exit_2_with_the_flag_on(self):
        # The other absence. `--window` may not rescue a run that has no number:
        # what the seam asked for is the occupancy, and there is none.
        self.write(json.dumps({"type": "user", "message": {"role": "user"}}))
        run = self.run_it("--window")
        self.assertEqual(run.returncode, 2, run.stdout)
        self.assertEqual(run.stdout.strip(), "")
        self.assertIn("judgement", run.stderr)

    # --- the resolution order the harness has --------------------------------

    def test_the_settings_key_is_read_and_the_threshold_follows_it(self):
        self.write_settings(300000)
        run = self.run_window()
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("300000", run.stderr)
        self.assertIn(str(300000 - self.bin.SUMMARY_BUFFER), run.stderr)
        self.assertNotIn("DEFAULT", run.stderr)

    def test_the_environment_variable_beats_the_key(self):
        self.write_settings(300000)
        env = {self.bin.WINDOW_ENV: "100000"}
        run = self.run_window(env=env)
        self.assertIn("100000", run.stderr)
        self.assertNotIn("300000", run.stderr)

    def test_the_word_auto_is_read_as_a_configured_key_and_not_as_absence(self):
        # `auto` is a legitimate value of the key — WINDOW.md prescribes the key
        # and says `auto` resolves to the model's own context, 1M on Fable. Read
        # as a refusal it printed "no readable `autoCompactWindow`" over a key
        # that was present, readable and valid, and the tick was told to go and
        # configure what the session already had.
        self.write_settings("auto")
        run = self.run_window()
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("autoCompactWindow` = auto", run.stderr,
                      "`auto` is not reported as the key it is, so the source line "
                      "names no key at all")
        self.assertNotIn("DEFAULT", run.stderr,
                         "a key that is present and valid is reported as absent")
        self.assertIn(str(self.bin.WINDOW_DEFAULT - self.bin.SUMMARY_BUFFER),
                      run.stderr,
                      "`auto` resolves to the model's own context, measured 1M on "
                      "Fable, and the threshold subtracts the summary buffer from it")

    def test_a_value_the_harness_would_refuse_falls_through_to_the_default(self):
        # A word that is not `auto`, a number outside the bounds: the harness
        # obeys none of them, and a reader obeying one would print a threshold no
        # compaction will ever use. `auto` is the exception and has its own test.
        default = self.bin.WINDOW_DEFAULT - self.bin.SUMMARY_BUFFER
        for value in ("three hundred thousand", 42, 5_000_000, True):
            with self.subTest(value=value):
                self.write_settings(value)
                run = self.run_window()
                self.assertEqual(run.returncode, 0, run.stderr)
                self.assertIn("DEFAULT", run.stderr)
                # the threshold is the assertion, not the word: the default line
                # names `auto` itself, so a word's absence proves nothing.
                self.assertIn(str(default), run.stderr)
                if isinstance(value, int) and not isinstance(value, bool):
                    self.assertNotIn(str(value - self.bin.SUMMARY_BUFFER),
                                     run.stderr,
                                     "a value the harness refuses was obeyed, and "
                                     "the threshold printed is one no compaction "
                                     "will ever use")

    def test_a_settings_path_that_is_a_directory_costs_the_caller_nothing(self):
        # Guarding the parse is not guarding the OPEN. The number the caller
        # asked for is the occupancy, and a settings path nobody can read is no
        # reason to withhold it.
        os.makedirs(os.path.join(self.settings, "settings.local.json"), exist_ok=True)
        run = self.run_window()
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stdout.strip(), "8000 tokens in context")
        self.assertIn("DEFAULT", run.stderr)

    def test_a_half_written_settings_file_costs_the_caller_nothing(self):
        # The other half of the same guard: the file opens and does not parse.
        with open(os.path.join(self.settings, "settings.local.json"), "w") as fh:
            fh.write('{"autoCompactWindow": 300')
        run = self.run_window()
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stdout.strip(), "8000 tokens in context")
        self.assertIn("DEFAULT", run.stderr)


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
        # The assertion is the BULLET, not the words: a second "never a fraction"
        # arrived elsewhere in the file and the loose search went vacuous — the
        # mutation that rewrites this bullet survived while the suite stayed
        # green, which is what a search unit too wide always buys.
        window = re.sub(r"\s+", " ", self.read("WINDOW.md"))
        self.assertRegex(
            window,
            r"\*\*Compare absolutes, never a fraction\.\*\* "
            r"The threshold is the smart zone's edge")

    def test_window_licenses_judgement_only_when_it_is_declared(self):
        # Tied to the no-number rule on purpose. An earlier draft asserted the
        # bare words "says so", which occur in an unrelated bullet of the same
        # file — the assertion was green with the whole licence deleted.
        window = re.sub(r"\s+", " ", self.read("WINDOW.md"))
        self.assertRegex(window, r"no number.{0,400}?names it as judgement")


class TheSiblingSeam(TranscriptFixture):

    def test_main_takes_its_argv_like_every_sibling_bin(self):
        # `tk-collisions`, `tk-vista-check` and `tk-closure-check` all declare
        # `main(argv=None)`. It is what lets a caller drive the parser without a
        # subprocess, and it is asserted rather than assumed.
        self.write(usage_line(cache_read_input_tokens=8000))
        spec = importlib.util.spec_from_loader(
            "tk_context", importlib.machinery.SourceFileLoader("tk_context", TK_CONTEXT))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(
            inspect.signature(module.main).parameters["argv"].default, None)


if __name__ == "__main__":
    unittest.main()
