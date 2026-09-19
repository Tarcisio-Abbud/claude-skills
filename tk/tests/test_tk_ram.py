#!/usr/bin/env python3
"""Behaviour proof for `../bin/tk-ram`, and the prose that calls it.

Run: python3 -m unittest discover -s tk/tests   (stdlib only, no deps)

WHAT IS ON TRIAL. A number nobody can check by eye, and one that is WRONG IN
BOTH DIRECTIONS at different moments: too high and the package OOMs a container
it cannot see the inside of, too low and it dispatches one agent at a time
through a window that resets in five hours. The bin is the only thing between
those two, so the arithmetic, the clamp and every refusal are asserted here.

THE CGROUP IS A FIXTURE DIRECTORY, never the real one. `/sys/fs/cgroup` holds
whatever this machine happens to be doing at the moment the suite runs, which is
not a number a test can assert against — and a suite that reads it would pass on
the container and fail on a laptop. `--cgroup DIR` exists for the caller whose
process sits in a sub-cgroup; it is what lets this file build the two states the
item's criterion names and read them back.

THE TWO FIXTURES THE CRITERION NAMES are `NINE_SESSIONS` and `EMPTY`, and only
one of the two is measured. The afk package of 2026-09-19 sampled `memory.stat`
every 20s in this container: across 125 samples with two `claude` processes
alive, `anon` averaged 0.62 GiB — about 0.31 GiB per live session, which agrees
with those two processes' own RSS, 424 and 333 MiB. Nine of them is 2.79 GiB.

THE EMPTY CONTAINER WAS NEVER SAMPLED — every sample has at least two sessions
in it, because a sampler needs a session to start it. So that fixture's `anon` is
an assumption, and the test does not rest on it: it asserts 3 across the whole
range an empty container could be in, up to the 1.28 GiB where the arithmetic
itself would stop saying 3. A single invented number would have proved the
number, not the behaviour.

WHY NO TEST ASSERTS THE REAL CONTAINER'S FIT. It moves with every session that
opens, which is the whole reason the bin exists. What IS reproducible is the
arithmetic and the refusals, so those are what is asserted; agreement with the
live cgroup was checked by hand and belongs in the pull request.
"""

import importlib.machinery
import importlib.util
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TK_DIR = os.path.dirname(HERE)
TK_RAM = os.path.join(TK_DIR, "bin", "tk-ram")
KICKOFF = os.path.join(TK_DIR, "skills", "kickoff")

GIB = 1024 ** 3
FOUR_GIB = 4 * GIB

# Measured on this container, 2026-09-19 — see the banner.
PER_SESSION = 0.31 * GIB
NINE_SESSIONS = 9 * PER_SESSION
# Not measured: the range an empty container's `anon` can be in, up to the point
# where the arithmetic stops saying 3 on its own.
EMPTY_RANGE = (0.05 * GIB, 0.5 * GIB, 1.0 * GIB)
EMPTY = EMPTY_RANGE[0]

ESCAPE = "\x1b]0;pwned\x07"


def load_bin():
    """The bin as a module — for the one guard a subprocess cannot reach.

    `/proc/self/cgroup` is read by absolute path, and a test cannot put this
    process in another cgroup. Importing is how that branch is exercised at all;
    everything else in this file runs the real command as a real process.
    """
    spec = importlib.util.spec_from_loader(
        "tk_ram", importlib.machinery.SourceFileLoader("tk_ram", TK_RAM))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RamFixture(unittest.TestCase):

    def setUp(self):
        import tempfile
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.cgroup = os.path.join(self.tmp.name, "cgroup")
        os.makedirs(self.cgroup)

    def write(self, name, text):
        with open(os.path.join(self.cgroup, name), "w", encoding="utf-8") as handle:
            handle.write(text)

    def build(self, ceiling=FOUR_GIB, anon=EMPTY, swap=0, stat=None, max_text=None):
        """A cgroup v2 directory in the shape the kernel writes one."""
        self.write("memory.max", max_text if max_text is not None
                   else f"{int(ceiling)}\n")
        self.write("memory.stat", stat if stat is not None else
                   f"anon {int(anon)}\nfile 762540032\nkernel 136597504\n")
        if swap is not None:
            self.write("memory.swap.current", f"{int(swap)}\n")

    def run_it(self, *args, cgroup=...):
        argv = [sys.executable, TK_RAM, *args]
        target = self.cgroup if cgroup is ... else cgroup
        if target is not None:
            argv += ["--cgroup", target]
        return subprocess.run(argv, capture_output=True, text=True)

    def fit(self, **kw):
        """The number the bin printed, with the run asserted green."""
        self.build(**kw)
        run = self.run_it()
        self.assertEqual(run.returncode, 0, run.stderr)
        head = run.stdout.split()
        self.assertEqual(head[0], "tk-ram:", run.stdout)
        return int(head[1]), run


class TheFit(RamFixture):

    def test_an_empty_container_fits_three(self):
        """Half the item's criterion, asserted over a RANGE rather than a point.
        Nobody sampled an empty container — a sampler needs a session — so a
        single `anon` here would be an invented number the test then proved. The
        range is what the criterion actually claims: at 0.05 GiB the raw
        quotient is 4.66 and the clamp gives 3, at 1.00 GiB the arithmetic gives
        3 on its own, and the answer does not move in between."""
        for anon in EMPTY_RANGE:
            with self.subTest(anon=anon):
                fit, _ = self.fit(anon=anon)
                self.assertEqual(fit, 3)

    def test_nine_live_sessions_fit_no_more_than_two(self):
        """The other half. Nine sessions hold 2.79 GiB of the 4 GiB ceiling, so
        what is left after the reserve does not pay for one agent — the bin says
        1, and the assertion is the criterion's own `<= 2`, since a later
        recalibration of the per-agent cost may move it between 1 and 2 without
        making the answer wrong."""
        fit, _ = self.fit(anon=NINE_SESSIONS)
        self.assertLessEqual(fit, 2)

    def test_a_half_full_container_fits_two(self):
        """Between the two clamps, where the arithmetic alone decides:
        (4 - 0.5 - 1.8) / 0.74 = 2.29."""
        fit, _ = self.fit(anon=1.8 * GIB)
        self.assertEqual(fit, 2)

    def test_swap_counts_against_the_fit(self):
        """A swapped agent still owes its memory. Same `anon` as the case above,
        0.6 GiB of it pushed out: a bin reading `anon` alone still says 2."""
        fit, _ = self.fit(anon=1.8 * GIB, swap=0.6 * GIB)
        self.assertEqual(fit, 1)

    def test_the_reserve_is_kept_off_the_ceiling_before_the_division(self):
        """At 2.30 GiB the reserve is what separates 1 from 2: without it the
        free space divides to 2.29 and the package dispatches a second agent
        into the half gigabyte the calibration set aside."""
        fit, _ = self.fit(anon=2.3 * GIB)
        self.assertEqual(fit, 1)

    def test_a_quotient_above_three_is_capped_and_the_line_says_so(self):
        fit, run = self.fit(anon=EMPTY)
        self.assertEqual(fit, 3)
        self.assertIn("capped at 3", run.stdout,
                      "the cap is silent, so a reader cannot tell the answer from "
                      "arithmetic that never got near it")

    def test_a_quotient_below_one_is_raised_and_the_line_says_so(self):
        fit, run = self.fit(anon=3.45 * GIB)
        self.assertEqual(fit, 1)
        self.assertIn("raised to 1", run.stdout,
                      "the floor is silent, so `1 agent fits` reads as measured "
                      "when nothing fits at all")

    def test_a_raw_fit_at_or_below_zero_says_the_floor_is_not_a_measurement(self):
        """The bin never prints 0 — dispatching nothing is the quota floor's
        verdict and the wall's. What it owes instead is to say that the 1 it
        printed is a clamp, so a caller that wants to stop there can."""
        _, run = self.fit(anon=3.45 * GIB)
        self.assertIn("is a clamp and not a", run.stderr)
        self.assertIn("dispatching nothing is a verdict this bin does not give",
                      run.stderr)

    def test_the_line_names_every_number_that_went_into_the_division(self):
        """The ledger keeps this line for months and nobody re-runs the reading.
        Every operand is on it, so the arithmetic can be redone from the line."""
        _, run = self.fit(anon=1.8 * GIB, swap=0.25 * GIB)
        for piece in ("4.00 GiB max", "1.80 GiB anon", "0.25 GiB swap",
                      "0.50 GiB reserve", "0.74 GiB per agent"):
            with self.subTest(piece=piece):
                self.assertIn(piece, run.stdout)

    def test_the_anon_line_is_found_by_its_key_and_not_by_its_position(self):
        """`memory.stat` gains keys between kernel versions. A reader keyed on
        the first line reports whatever the kernel put there — as a number, in
        the direction that authorises dispatches."""
        fit, _ = self.fit(stat=f"slab 999\nfile 12\nanon {int(1.8 * GIB)}\n")
        self.assertEqual(fit, 2)


class WhenThereIsNoNumber(RamFixture):

    def refused(self, **kw):
        self.build(**kw)
        run = self.run_it()
        self.assertEqual(run.returncode, 2, run.stdout)
        self.assertEqual(run.stdout, "", "a refusal printed a number anyway")
        return run

    def test_an_unlimited_cgroup_is_refused(self):
        """`memory.max` reads `max` where nothing caps this cgroup, and there is
        no ceiling to divide. Guessing one would be a number nobody measured."""
        run = self.refused(max_text="max\n")
        self.assertIn("no memory ceiling", run.stderr)

    def test_a_memory_max_that_is_not_a_byte_count_is_refused(self):
        run = self.refused(max_text="four gigabytes\n")
        self.assertIn("not a byte count", run.stderr)

    def test_a_memory_stat_with_no_anon_line_is_refused(self):
        run = self.refused(stat="file 12\nkernel 34\n")
        self.assertIn("no `anon` line", run.stderr)

    def test_a_cgroup_directory_that_is_not_there_is_refused(self):
        run = self.run_it(cgroup=os.path.join(self.tmp.name, "nowhere"))
        self.assertEqual(run.returncode, 2)
        self.assertIn("not a directory", run.stderr)

    def test_a_cgroup_directory_missing_its_files_is_refused(self):
        run = self.run_it()
        self.assertEqual(run.returncode, 2)
        self.assertIn("is not there", run.stderr)

    def test_a_fifo_where_a_file_should_be_is_refused_before_it_blocks(self):
        """Guarding the parse is not guarding the open: a FIFO does not raise,
        it BLOCKS, and the command stops with nothing on screen and no exit."""
        self.build()
        os.remove(os.path.join(self.cgroup, "memory.stat"))
        os.mkfifo(os.path.join(self.cgroup, "memory.stat"))
        run = subprocess.run([sys.executable, TK_RAM, "--cgroup", self.cgroup],
                             capture_output=True, text=True, timeout=30)
        self.assertEqual(run.returncode, 2, run.stdout)
        self.assertIn("not a regular file", run.stderr)

    def test_the_refusal_names_the_site_key_the_caller_falls_back_on(self):
        """A refusal that stops at "no number" leaves the caller to invent one.
        The fallback is measured and it is in the site file."""
        run = self.refused(max_text="max\n")
        self.assertIn("max-local-subagents", run.stderr)
        self.assertIn("~/.claude/tk/env", run.stderr)
        self.assertIn("ledger", run.stderr,
                      "the refusal does not say the failed reading is recorded, "
                      "so a default enters the ledger looking like a reading")


class WhatIsDisclosedRatherThanRefused(RamFixture):

    def test_an_absent_swap_file_counts_as_zero_and_says_so(self):
        """cgroup v2 built without the swap controller has no such file. Refusing
        would cost the whole number over a zero; counting it silently would hide
        that a machine with swap on would have answered differently."""
        self.build(anon=1.8 * GIB, swap=None)
        run = self.run_it()
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("2 agents fit now", run.stdout)
        self.assertIn("swap controller off", run.stderr)

    def test_a_nested_cgroup_is_named_on_stderr_with_the_default_directory(self):
        """The default `/sys/fs/cgroup` is this container's own cgroup only
        inside its own namespace. Anywhere else the bin would be reading
        somebody else's file and printing the number without a word."""
        module = load_bin()
        path = os.path.join(self.tmp.name, "self-cgroup")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("0::/system.slice/docker-abc.scope\n")
        module.SELF_CGROUP = path
        captured = []
        module.note = captured.append
        module.own_cgroup_check(module.CGROUP)
        self.assertEqual(len(captured), 1, captured)
        self.assertIn("not this process's own cgroup", captured[0])
        self.assertIn("--cgroup", captured[0])

    def test_a_cgroup_given_on_the_flag_is_not_checked_against_proc(self):
        """The check answers "is the DEFAULT the right directory". A caller who
        named one has already answered it, and warning there would train the
        reader to ignore the line that matters.

        `SELF_CGROUP` is pointed at a NESTED reading here on purpose: left at
        the real one, which reads `0::/` in this container, the check returns
        quietly for its own reason and the test passes whether or not the flag
        is honoured."""
        module = load_bin()
        path = os.path.join(self.tmp.name, "self-cgroup")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("0::/system.slice/docker-abc.scope\n")
        module.SELF_CGROUP = path
        captured = []
        module.note = captured.append
        module.own_cgroup_check("/elsewhere")
        self.assertEqual(captured, [])


class WhatComesFromOutsideThisProcess(RamFixture):

    def test_a_control_sequence_in_a_cgroup_file_is_printed_flat(self):
        """The refusal quotes the file's contents back to a terminal."""
        run = self.run_it(cgroup=os.path.join(self.tmp.name, "no" + ESCAPE))
        self.assertEqual(run.returncode, 2)
        self.assertNotIn("\x1b", run.stderr)
        self.assertIn("?", run.stderr)


class Usage(RamFixture):

    def test_an_unknown_flag_exits_sixty_four(self):
        """argparse's own 2 is this command's "no number", so a mistyped flag
        would read as a cgroup it could not measure."""
        run = self.run_it("--nope")
        self.assertEqual(run.returncode, 64, run.stderr)


class TheProseThatCallsIt(unittest.TestCase):
    """A bin no document names is a bin nobody runs."""

    def read(self, name):
        with open(os.path.join(KICKOFF, name), encoding="utf-8") as handle:
            return handle.read()

    def test_the_vehicle_reads_the_axis_before_each_local_dispatch(self):
        body = self.read("AFK.md")
        self.assertIn("../../bin/tk-ram", body,
                      "AFK.md's vehicle section does not name the bin, so the "
                      "dispatch goes on reading the site key as the ceiling")
        self.assertIn("before each local dispatch", body,
                      "the reading is named without saying when it is taken, and "
                      "a reading taken once per package is a constant again")

    def test_the_tick_says_the_site_key_is_the_fallback_and_not_the_reading(self):
        body = self.read("WINDOW.md")
        self.assertIn("`../../bin/tk-ram`", body,
                      "the tick's budget does not name the bin")
        self.assertIn("exit 2", body,
                      "the budget does not say which exit hands the fire back to "
                      "the site key, so a refusal reads as a reason to guess")
        self.assertIn("max-local-subagents", body)

    def test_the_tick_says_the_harness_warning_does_not_cover_this(self):
        """Without it a reader waits for a warning that cannot fire: the
        harness reads `/proc/meminfo`, which in a container is the host's."""
        body = self.read("WINDOW.md")
        self.assertIn("/proc/meminfo", body)
        self.assertIn("blind to the cgroup", body)

    def test_the_ledger_takes_the_reading_on_the_dispatch_line(self):
        body = self.read("LEDGER.md")
        self.assertIn("../../bin/tk-ram", body,
                      "the ledger does not admit the reading, so it is taken and "
                      "then lost, and the next package starts from the key again")
        self.assertIn("never folded into `<quota>`", body,
                      "the ledger does not keep the two axes apart, and a reader "
                      "who finds one number cannot tell which sensor said what")


if __name__ == "__main__":
    unittest.main()
