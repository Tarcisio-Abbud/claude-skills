#!/usr/bin/env python3
"""Regression suite for `tk-queue` (../bin/tk-queue).

Run: python3 -m unittest discover -s tk/tests   (stdlib only, no deps)

Every test here is proved by MUTATION: the defect is put back in the source and
the test must fail. A test that still passes with the defect restored guards
nothing. `mutations.py` in this directory replays each mutation mechanically.

The suite drives the real script as a subprocess against throwaway fixtures. It
never touches a real memory dir — the queue files are written ONLY by tk-queue,
and hand-editing them is exactly what the contract forbids.
"""

import datetime
import hashlib
import importlib.machinery
import importlib.util
import os
import shlex
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor

try:
    import fcntl
except ImportError:
    fcntl = None

TK = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "bin", "tk-queue")


def load_tk():
    """Import the script as a module — it has no .py extension. Safe: the file
    only calls main() under `if __name__ == "__main__"`."""
    loader = importlib.machinery.SourceFileLoader("tk_queue", TK)
    spec = importlib.util.spec_from_loader("tk_queue", loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod

HEADER = """---
name: next-steps
description: fixture
metadata:
  type: project
---

# Next steps

"""


def item(iid, text, project=None, klass="AUTONOMOUS", risk=None, effort="S", born=None):
    """The canonical item, as compose_item writes it.

    `born` is OFF by default, and that default is the legacy queue: the field
    arrived long after these fixtures, so an item without it is exactly the shape
    every reader has to keep working on. A test that wants an age asks for one.
    """
    tag = f" **Project:** {project}." if project else ""
    risk_field = f" **Risk:** {risk}." if risk else ""
    born_field = f" **Born:** {born}." if born else ""
    return (f"- [ ] **T{iid:03d}** — {text} **Class:** {klass}. **Effort:** {effort}."
            f"{risk_field} **Criterion:** A: x.{tag}{born_field} **Source:** 2026-08-13\n")


class QueueTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="tk-queue-test.")
        self.mem = os.path.join(self.dir, "memory")
        os.makedirs(self.mem)
        # HOME is redirected for EVERY test, not only the ones that write a site
        # file: `~/.claude/tk/env` is a real file on a real machine, and a suite
        # that reads it answers differently depending on whose machine runs it —
        # `--env` refused here and accepted there, with nothing in the test
        # saying so. Hermetic by default; a test that wants a roster calls
        # self.site()
        self.home = os.path.join(self.dir, "home")
        os.makedirs(self.home)
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)

    # --- helpers ---------------------------------------------------------
    def seed(self, *items, log=None):
        self.write("next-steps.md", HEADER + "".join(items))
        if log is not None:
            self.write("done-log.md", log)

    def write(self, name, text):
        with open(os.path.join(self.mem, name), "w", encoding="utf-8") as f:
            f.write(text)

    def site(self, text):
        """Write the site file this test's subprocesses will read."""
        d = os.path.join(self.home, ".claude", "tk")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "env"), "w", encoding="utf-8") as f:
            f.write(text)

    def body(self, name="next-steps.md"):
        path = os.path.join(self.mem, name)
        if not os.path.exists(path):
            return ""
        with open(path, encoding="utf-8") as f:
            return f.read()

    def run_tk(self, *argv, cwd=None, timeout=None):
        # `timeout` is not decoration: a command that BLOCKS (a FIFO where a file
        # was expected) would otherwise hang the whole suite instead of failing
        # one test, and a suite that never finishes reports nothing at all
        env = dict(os.environ, HOME=self.home)
        return subprocess.run([sys.executable, TK, *argv, "--dir", self.mem],
                              capture_output=True, text=True, cwd=cwd or self.dir,
                              env=env, timeout=timeout)


# --- the redirected HOME reaches EVERY spawn, not only run_tk's -----------

class TestEverySpawnCarriesTheRedirectedHome(unittest.TestCase):
    """`setUp` redirects HOME for every test, and `run_tk` passes it on. A test
    that reaches for `subprocess` directly does not get it for free: it reads the
    REAL `~/.claude/tk/env`, so the site file of the machine running the suite
    decides the result. Four such calls existed, and two of them failed on `main`
    once the live queue reached its open-item cap -- a green suite turning red
    because of a number in the user's queue, with nothing in the diff to blame.

    The check derives the call list from the source instead of counting it, so a
    fifth spawn written without `env=` fails here rather than years later on
    somebody's machine."""

    def test_no_spawn_of_tk_queue_inherits_the_real_home(self):
        source = open(__file__, encoding="utf-8").read()
        calls = re.findall(r"subprocess\.(?:run|Popen)\((?:[^()]|\([^()]*\))*\)",
                           source, re.S)
        self.assertTrue(calls, "the scan found no subprocess call at all -- it broke")
        naked = [c for c in calls if "env=" not in c]
        self.assertEqual(
            naked, [],
            "these spawns inherit the real HOME and read the machine's own site "
            "file: " + "; ".join(c.split("\n")[0] for c in naked))


# --- T025: the displayed ID form must be accepted ------------------------

class TestPrefixedId(QueueTest):
    """The queue displays T006 everywhere and the contract writes `done <id>`,
    so `done T006` must work. It died in argparse's `invalid int value`."""

    def test_done_accepts_the_displayed_form(self):
        for form in ("T006", "t006", "006", "6", "T6"):
            with self.subTest(form=form):
                # the LOG is reseeded too: five closes of one ID against one log
                # is five replays of the first, and since T301 slice 5 a replay
                # is recognised and writes no second entry
                self.seed(item(6, "item seis"), log="")
                r = self.run_tk("done", form, "--how", "PR #1")
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertIn("T006 → done-log as FEITO", r.stdout)
                self.assertNotIn("**T006**", self.body())

    def test_cancel_and_edit_accept_it_too(self):
        self.seed(item(6, "item seis"))
        self.assertEqual(self.run_tk("edit", "T006", "--effort", "L").returncode, 0)
        self.assertIn("**Effort:** L.", self.body())
        self.assertEqual(self.run_tk("cancel", "T006", "--why", "n/a").returncode, 0)

    def test_garbage_is_still_rejected(self):
        # `fullmatch`, not `match`: "6x" must not slip through as 6. int() would
        # also have taken "1_0" and the Unicode "０６" — a looser grammar than `done N`
        for junk in ("T", "TT6", "6x", "T-6", "", "1e3", "1_0", "０６"):
            with self.subTest(junk=junk):
                self.seed(item(6, "item seis"))
                r = self.run_tk("done", junk, "--how", "x")
                self.assertEqual(r.returncode, 2, f"{junk!r} was accepted")
                self.assertIn("invalid id:", r.stderr)
                self.assertIn("**T006**", self.body())   # nothing was closed


# --- T060: concurrent writers, and the message that induces duplicates ----

class TestConcurrency(QueueTest):
    def test_concurrent_adds_lose_nothing_and_never_reuse_an_id(self):
        """Without the lock this lost items outright, and a shared temp-file
        name let one writer rename another's half-written bytes into place —
        the queue came back truncated with ID allocation restarted at T001."""
        self.seed(item(1, "pre-existente"))
        n = 6

        def add(i):
            return self.run_tk("add", f"concorrente {i}", "--class", "AUTONOMOUS",
                               "--effort", "S", "--criterion", "A: c")

        with ThreadPoolExecutor(n) as ex:
            res = list(ex.map(add, range(n)))

        for r in res:
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertNotIn("Traceback", r.stderr)
        ids = [r.stdout.split()[1].rstrip(":") for r in res]
        self.assertEqual(len(set(ids)), n, f"duplicate ID allocated: {sorted(ids)}")
        body = self.body()
        self.assertEqual(body.count("- [ ] "), n + 1, "an add reported success but was lost")
        for iid in ids:
            self.assertIn(f"**{iid}**", body)

    @unittest.skipIf(fcntl is None, "flock unavailable on this platform")
    def test_a_second_writer_waits_for_the_lock(self):
        """The race test above is real but timing-dependent, so it cannot be a
        mutation's proof — it passes by luck often enough. This one asserts the
        lock's contract directly and deterministically: while the lock is held,
        a writer must NOT proceed; once released, it must."""
        self.seed(item(1, "um"))
        lock_fd = os.open(os.path.join(self.mem, ".tk-queue.lock"),
                          os.O_CREAT | os.O_RDWR, 0o644)
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        proc = subprocess.Popen(
            [sys.executable, TK, "add", "bloqueado", "--class", "AUTONOMOUS",
             "--effort", "S", "--criterion", "A: c", "--dir", self.mem],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            env=dict(os.environ, HOME=self.home))
        try:
            with self.assertRaises(subprocess.TimeoutExpired,
                                   msg="the writer did not wait for the lock"):
                proc.wait(timeout=1.5)
        finally:
            os.close(lock_fd)                      # releases the flock
        out, err = proc.communicate(timeout=30)
        self.assertEqual(proc.returncode, 0, err)  # and then it goes through
        self.assertIn("**T002**", self.body())

    @unittest.skipIf(fcntl is None, "flock unavailable on this platform")
    def test_the_lock_timeout_does_not_accuse_the_holder_of_writing(self):
        """`migrate --dry-run` takes this lock and writes nothing, so a holder is
        no longer necessarily a writer. The timeout message may not assert that it
        is: a session blocked by a preview would be told a rewrite is in flight.
        Slow by construction — it waits out the real LOCK_TIMEOUT, because the
        message only exists on that path."""
        self.seed(item(1, "um"))
        lock_fd = os.open(os.path.join(self.mem, ".tk-queue.lock"),
                          os.O_CREAT | os.O_RDWR, 0o644)
        fcntl.flock(lock_fd, fcntl.LOCK_EX)          # a holder that writes nothing
        try:
            r = subprocess.run(
                [sys.executable, TK, "add", "bloqueado", "--class", "AUTONOMOUS",
                 "--effort", "S", "--criterion", "A: c", "--dir", self.mem],
                capture_output=True, text=True, timeout=60,
                env=dict(os.environ, HOME=self.home))
        finally:
            os.close(lock_fd)
        self.assertNotEqual(r.returncode, 0, "the blocked command reported success")
        self.assertNotIn("is writing this queue", r.stderr,
                         "the message asserts the holder writes; a preview holds "
                         "without writing")
        self.assertIn("a writer, or a `migrate --dry-run` preview", r.stderr,
                      "the message must name both kinds of holder")
        self.assertIn("Nothing was changed", r.stderr)

    @unittest.skipIf(fcntl is None, "flock unavailable on this platform")
    def test_pack_reads_straight_through_a_held_lock(self):
        """The other side of the gate, and the one the package is dispatched
        from: `pack` writes nothing, so it may not queue behind a writer — a
        report that blocks for LOCK_TIMEOUT whenever someone is adding an item
        is a report nobody can read at the moment they need it. The claim used
        to be proved by the announcement (readers named no queue); since T215
        every command but `report` names its queue, and the LOCK is what is left
        to tell a reader from a writer."""
        self.seed(item(1, "um"))
        lock_fd = os.open(os.path.join(self.mem, ".tk-queue.lock"),
                          os.O_CREAT | os.O_RDWR, 0o644)
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        try:
            r = self.run_tk("pack", timeout=10)
        finally:
            os.close(lock_fd)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("T001", r.stdout)

    @unittest.skipIf(fcntl is None, "flock unavailable on this platform")
    def test_bump_waits_for_the_lock_like_every_other_writer(self):
        """`bump` rewrites the queue, so it belongs on the locked side of the
        gate. Nothing proved that directly until the announcement stopped being
        the observable: the queue is named on reads now too, so a command
        wrongly counted as a reader still names its dir and only the lock tells
        the two sides apart."""
        self.seed(item(1, "um"), item(2, "dois"))
        lock_fd = os.open(os.path.join(self.mem, ".tk-queue.lock"),
                          os.O_CREAT | os.O_RDWR, 0o644)
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        proc = subprocess.Popen(
            [sys.executable, TK, "bump", "T002", "--dir", self.mem],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            env=dict(os.environ, HOME=self.home))
        try:
            with self.assertRaises(subprocess.TimeoutExpired,
                                   msg="bump did not wait for the lock"):
                proc.wait(timeout=1.5)
        finally:
            os.close(lock_fd)
        out, err = proc.communicate(timeout=30)
        self.assertEqual(proc.returncode, 0, err)

    def test_concurrent_close_and_add_keep_both_files_coherent(self):
        self.seed(item(1, "um"), item(2, "dois"))
        with ThreadPoolExecutor(2) as ex:
            a = ex.submit(self.run_tk, "done", "T001", "--how", "PR #1")
            b = ex.submit(self.run_tk, "add", "novo", "--class", "AUTONOMOUS",
                          "--effort", "S", "--criterion", "A: c")
            ra, rb = a.result(), b.result()
        self.assertEqual(ra.returncode, 0, ra.stderr)
        self.assertEqual(rb.returncode, 0, rb.stderr)
        body = self.body()
        self.assertNotIn("**T001**", body)          # closed item really left
        self.assertIn("**T002**", body)             # untouched item survived
        self.assertIn("**T003**", body)             # concurrent add survived
        self.assertIn("T001", self.body("done-log.md"))


class TestAtomicWrite(QueueTest):
    """The queue lock and the unique temp name fix the same incident, and a
    test that drives the CLI exercises both at once — so it cannot tell which
    one is doing the work, and the temp-name mutation survives it.

    write_atomic has to hold on its own: `queue_lock` is a no-op wherever flock
    is missing (non-POSIX), and it does not bind a writer that never takes it.
    Calling write_atomic directly is the scenario where only the temp name
    decides.
    """

    def test_concurrent_writers_never_leave_a_mixed_or_truncated_file(self):
        tk = load_tk()
        path = os.path.join(self.mem, "atomic.md")
        # large payloads widen the window between the write and the rename
        payloads = [chr(ord("a") + i) * 300_000 + f"\nEND{i}\n" for i in range(6)]
        errors = []

        def writer(payload):
            try:
                tk.write_atomic(path, payload)
            except Exception as exc:          # noqa: BLE001 — reporting, not handling
                errors.append(repr(exc))

        with ThreadPoolExecutor(len(payloads)) as ex:
            list(ex.map(writer, payloads))

        self.assertEqual(errors, [], "a writer crashed on another's temp file")

        got = self.body("atomic.md")
        self.assertIn(got, payloads,
                      f"file is neither writer's payload — {len(got)} chars, "
                      "so a rename published half-written bytes")

    def test_the_rename_keeps_the_file_mode(self):
        """mkstemp creates 0600. Publishing that by rename would narrow a
        world-readable memory file to owner-only behind the user's back."""
        self.seed(item(1, "um"))
        path = os.path.join(self.mem, "next-steps.md")
        os.chmod(path, 0o644)
        r = self.run_tk("add", "novo", "--class", "AUTONOMOUS", "--effort", "S",
                        "--criterion", "A: c")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(os.stat(path).st_mode & 0o777, 0o644)


class TestMissingItemMessage(QueueTest):
    """Telling the caller "no open item" reads as "never existed", so the caller
    adds it again. Each cause gets its own answer, and none may invite a re-add."""

    def assert_no_duplicate_invited(self, stderr):
        self.assertNotIn("no open item", stderr)
        self.assertRegex(stderr, r"do NOT add a replacement item|Check the ID")

    def test_already_in_the_done_log(self):
        self.seed(item(2, "dois"), log="- 2026-08-01 — FEITO — T001 um — PR #1\n")
        r = self.run_tk("edit", "T001", "--effort", "L")
        self.assertEqual(r.returncode, 1)
        self.assertIn("already left the queue", r.stderr)
        self.assert_no_duplicate_invited(r.stderr)

    def test_ticked_but_never_migrated(self):
        self.seed(item(2, "dois"), "- [x] **T009** — feito à mão\n")
        r = self.run_tk("done", "T009", "--how", "x")
        self.assertEqual(r.returncode, 1)
        self.assertIn("already ticked [x]", r.stderr)
        self.assert_no_duplicate_invited(r.stderr)

    def test_never_allocated(self):
        self.seed(item(2, "dois"))
        r = self.run_tk("done", "T999", "--how", "x")
        self.assertEqual(r.returncode, 1)
        self.assertIn("never allocated", r.stderr)
        self.assert_no_duplicate_invited(r.stderr)

    def test_an_id_merely_quoted_in_the_log_is_not_closed(self):
        """Real shapes from this queue's own log: a --note saying "assigned IDs
        up to T022", and an outcome naming a sibling ticket still open in
        another project. Neither closed anything — reporting them as closed is
        a confident wrong answer from the path built to stop wrong answers."""
        # T030 open, so 22 and 54 are inside the allocated range but in neither
        # file — the branch that must NOT be confused with "already closed"
        self.seed(item(30, "trinta"), item(60, "sessenta"),
                  log="- 2026-08-04 — FEITO — T017 migrate — pointer\n"
                      "  Migrou 1 item [x] e atribuiu IDs até T022.\n"
                      "- 2026-08-13 — DESCARTADO — T033 fila errada — "
                      "re-registrado lá como T054\n")
        for iid in ("T022", "T054"):
            with self.subTest(iid=iid):
                r = self.run_tk("edit", iid, "--effort", "L")
                self.assertEqual(r.returncode, 1)
                self.assertNotIn("already left the queue", r.stderr)
                self.assertIn("Another writer", r.stderr)

    def test_a_genuinely_closed_id_is_still_recognised(self):
        # the other side of the same rule: the canonical position must still match
        self.seed(item(30, "trinta"),
                  log="- 2026-08-04 — FEITO — T017 migrate — pointer\n")
        r = self.run_tk("edit", "T017", "--effort", "L")
        self.assertEqual(r.returncode, 1)
        self.assertIn("already left the queue", r.stderr)

    def test_allocated_but_vanished_names_the_concurrent_writer(self):
        # the T060 case: the ID was handed out, the item is in neither file
        self.seed(item(5, "cinco"), log="- 2026-08-01 — FEITO — T007 sete — x\n")
        r = self.run_tk("edit", "T003", "--effort", "L")
        self.assertEqual(r.returncode, 1)
        self.assertIn("Another writer", r.stderr)
        self.assertIn("Nothing was changed", r.stderr)
        self.assert_no_duplicate_invited(r.stderr)


# --- C-17: the diagnostic answers from ONE snapshot of each file -------------
#
# The writing side of this rule was already spelled twice — `append_done_line`
# and `remove_block` both take the content the caller read under the lock and
# say why re-reading would be wrong. The READING side did not follow it: the
# error path asked the done-log whether the ID was closed, and then asked the
# same file, in a second read, what the highest ID handed out was. One decision,
# two snapshots — and a close landing between the two reads is enough to make
# the two answers disagree.

class TestTheDiagnosticReadsEachFileOnce(QueueTest):
    """A file that changes between the two reads is not a hypothetical here: the
    queue takes an exclusive lock, the done-log does not, and every close writes
    the log FIRST and the queue second (see `interrupted_close`) — so the window
    this path reads across is exactly the one another writer is inside of."""

    QUEUE = HEADER + item(5, "cinco")
    # the second snapshot: the close of T009 landed between the two reads
    CLOSED_LATER = "- 2026-08-01 — FEITO — T009 nove — PR #1\n"

    def reader(self, snapshots):
        """A `read` that serves each file a QUEUE of snapshots, last one
        repeating, and counts the calls per file."""
        self.reads = {}

        def read(path):
            name = os.path.basename(path)
            self.reads[name] = self.reads.get(name, 0) + 1
            texts = snapshots.get(name, [None])
            return texts.pop(0) if len(texts) > 1 else texts[0]
        return read

    def message(self, wanted, snapshots):
        tk = load_tk()
        tk.read = self.reader(snapshots)
        return tk.missing_item_message(self.mem, self.QUEUE, wanted)

    def test_a_close_landing_between_the_reads_blames_no_writer(self):
        """T009 was never in the caller's queue, and the done-log the path read
        does not carry it either — "never allocated" is what that state says.
        Read twice, the ID check saw the log without T009 and `max_id` saw the
        log WITH it, so the ID came back inside the allocated range and out came
        "another writer very likely removed or clobbered it" — the confident
        wrong diagnosis, from the path that exists to stop confident wrong
        diagnoses, about a writer that clobbered nothing."""
        msg = self.message(9, {"next-steps.md": [self.QUEUE],
                               "done-log.md": ["", self.CLOSED_LATER]})
        self.assertIn("was never allocated", msg)
        self.assertIn("the highest ID in use is T005", msg)
        self.assertNotIn("Another writer", msg)
        self.assertNotIn("already left the queue", msg)

    def test_neither_queue_file_is_read_a_second_time(self):
        """The rule itself, asked of the reads and not of the message: the
        done-log is read once here, and the queue not at all — the caller walked
        it already and handed it in. Counting is what keeps the rule from being
        satisfied by luck on a fixture whose two snapshots happen to agree.

        The log carries an ID that is NOT the one asked about, on purpose: a log
        holding T009 answers the first question with a return, and every read
        below that question then goes unmeasured."""
        self.message(9, {"next-steps.md": [self.QUEUE],
                         "done-log.md": ["- 2026-08-01 — FEITO — T007 sete — x\n"]})
        self.assertEqual(self.reads.get("done-log.md"), 1)
        self.assertIsNone(self.reads.get("next-steps.md"))

    def test_the_sibling_bins_still_ask_holding_a_directory_alone(self):
        """`tk-ticket-ref` calls `id_in_done_log(memdir, wanted)` with no content
        in hand, and `add` calls `max_id(memdir)` the same way. Threading the
        text through may not cost them the read they depend on."""
        tk = load_tk()
        tk.read = self.reader({"next-steps.md": [self.QUEUE],
                               "done-log.md": [self.CLOSED_LATER]})
        self.assertTrue(tk.id_in_done_log(self.mem, 9))
        self.assertEqual(tk.max_id(self.mem), 9)


# --- T088: an ID is ALLOCATED at a position, not wherever the text says it ---

class TestIdAllocationScope(QueueTest):
    """`max_id` regexed the whole TEXT of both files, so any T-number in prose
    counted as handed out. Measured 2026-08-14 on the real queue: a --note saying
    an item "virou T0NN" made the following `add` skip that number, and the live
    files still carry T054 and T086 as prose-only ghosts. A single HIGH id quoted
    in prose jumps the counter for good.

    Same defect, second face: `missing_item_message` asked `max_id` whether an ID
    was ever handed out, so an ID only ever MENTIONED was reported as "allocated
    but vanished — another writer clobbered it", sending the caller to hunt a
    writer that never existed.
    """

    def add(self, text="novo"):
        r = self.run_tk("add", text, "--class", "AUTONOMOUS", "--effort", "S",
                        "--criterion", "A: c")
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout.split()[1].rstrip(":")

    def test_a_note_quoting_an_id_does_not_burn_the_next_number(self):
        """The reported shape, end to end: close an item with a --note naming the
        very ID the next `add` is owed."""
        self.seed(item(1, "um"), item(2, "dois"))
        r = self.run_tk("done", "T001", "--how", "PR #1",
                        "--note", "duplicata: virou T003 na fila do ambiente")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("virou T003", self.body("done-log.md"))   # the note really landed
        self.assertEqual(self.add(), "T003")

    def test_neither_a_summary_nor_an_item_text_burns_a_number(self):
        """--note is not the only prose. --summary lands on the log line's text
        column, and an item's own text is prose sitting in next-steps.md."""
        self.seed(item(1, "um"))
        r = self.run_tk("done", "T001", "--how", "PR #1", "--summary", "absorvido pelo T004")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.add("sucessor do T009 da fila do ambiente"), "T002")
        self.assertEqual(self.add(), "T003")   # and the text just written burned nothing

    def test_a_bold_id_inside_an_item_text_is_not_an_allocation(self):
        """The next-steps side of the position rule: the ID is the one AT the
        item marker. An item whose text bolds a sibling's ID allocates nothing —
        and bolding is exactly how the queue's own items cite each other."""
        self.seed(item(1, "sucessor do **T040** da fila do ambiente"))
        self.assertEqual(self.add(), "T002")

    def test_a_high_id_quoted_in_prose_does_not_jump_the_counter(self):
        """The unbounded direction: one number from another tracker, quoted once,
        used to move this queue's counter there permanently."""
        self.seed(item(1, "um"))
        r = self.run_tk("done", "T001", "--how", "x", "--note", "ver T900 no outro tracker")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.add(), "T002")

    def test_the_diagnostic_stops_reading_a_prose_mention_as_an_allocation(self):
        """The second face. T050 exists only inside a --note, so the honest answer
        is "never allocated" — naming a concurrent writer instead is a confident
        wrong diagnosis from the path built to stop confident wrong diagnoses."""
        self.seed(item(1, "um"),
                  log="- 2026-08-01 — FEITO — T002 dois — PR #1\n"
                      "  duplicata: virou T050 na fila do ambiente\n")
        r = self.run_tk("edit", "T050", "--effort", "L")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("never allocated", r.stderr)
        self.assertIn("highest ID in use is T002", r.stderr)
        self.assertNotIn("Another writer", r.stderr)

    # --- the false-positive direction, which none of the above can see -------
    # A position rule that narrows too far hands out an ID ALREADY IN USE — the
    # failure the whole-file scan existed to prevent. Three writer positions, and
    # each one needs its OWN fixture holding the highest ID alone: a single
    # fixture carrying all three masks two of them, because the survivor still
    # yields the expected next number. Measured — that fixture was written first,
    # and mutations.py reported the done-log position as a SURVIVOR.

    def test_an_open_item_still_blocks_reuse_of_its_id(self):
        self.seed(item(7, "sete"), log="- 2026-08-01 — FEITO — T003 tres — PR #1\n")
        self.assertEqual(self.add(), "T008")

    def test_a_done_log_entry_still_blocks_reuse_of_its_id(self):
        self.seed(item(2, "dois"), log="- 2026-08-01 — FEITO — T009 nove — PR #1\n")
        self.assertEqual(self.add(), "T010")

    def test_a_legacy_x_line_moved_by_migrate_still_blocks_reuse(self):
        """`migrate` moves [x] items to the log verbatim; most are ID-less, but
        one that already carried a bold ID keeps it, and it is still spent."""
        self.seed(item(2, "dois"), log="- [x] **T012** — legado migrado verbatim\n")
        self.assertEqual(self.add(), "T013")


    # --- review#4: the SAME line, before and after `migrate` moves it --------
    # A legacy [x] line lives in next-steps.md until `migrate` moves it verbatim
    # into the log. Read by two different rules it gives two different answers,
    # and which one you get depends on nothing but the clock.

    def test_a_prose_id_on_a_legacy_x_line_burns_nothing_on_either_side(self):
        """Read loosely, the ID this line merely QUOTES became an allocation the
        moment `migrate` moved the line — the T088 ghost, back through the log."""
        self.seed(item(1, "um"),
                  "- [x] legado sem ID, feito junto com o **T900** do outro tracker\n")
        self.assertEqual(self.add("a"), "T002")
        # and the diagnostic must not invent a close either
        r = self.run_tk("edit", "T900", "--effort", "M")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("never allocated", r.stderr)

        self.assertEqual(self.run_tk("migrate").returncode, 0)
        self.assertIn("**T900**", self.body("done-log.md"))    # really moved
        self.assertEqual(self.add("b"), "T003")
        r = self.run_tk("edit", "T900", "--effort", "M")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("never allocated", r.stderr)

    def test_a_struck_through_legacy_id_is_spent_on_either_side(self):
        """The mirror image: an ID a human ticked off by striking it through IS
        an allocation, and reading it only in the log left it free to be handed
        out a second time while the line still sat in next-steps."""
        self.seed(item(1, "um"), item(2, "dois"), item(3, "tres"),
                  "- [x] ~~**T012**~~ — legado, ID não colado no marcador\n")
        self.assertEqual(self.add("a"), "T013")
        self.assertEqual(self.run_tk("migrate").returncode, 0)
        self.assertEqual(self.add("b"), "T014")

    # --- review#4: the positions the suite was not actually reading ----------

    def test_a_cancelled_item_still_blocks_reuse_of_its_id(self):
        """Every done-log fixture in this file closes with FEITO, so the marker
        column was never really read: pinned to that one word, a DESCARTADO
        entry stops counting and `add` hands its ID straight back."""
        self.seed(item(1, "um"))
        r = self.run_tk("cancel", "T001", "--why", "não vale mais")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("DESCARTADO — T001", self.body("done-log.md"))
        self.assertEqual(self.add(), "T002")

    def test_an_idless_item_quoting_a_bold_id_is_still_idless(self):
        """The item has NO ID and its text bolds a sibling's. Read by searching
        the block instead of its marker, that quote becomes the item's own id:
        `list` labels it with a number nobody allocated and `migrate` skips it,
        leaving it ID-less for good."""
        self.seed("- [ ] legado sem ID, sucessor do **T040** da fila do ambiente"
                  " **Class:** AUTONOMOUS. **Effort:** S.\n")
        out = self.run_tk("list").stdout
        self.assertIn("----", out)
        self.assertNotIn("T040", out)
        r = self.run_tk("migrate")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("IDs assigned up to T001", r.stdout)
        self.assertIn("- [ ] **T001** — legado sem ID", self.body())

    def test_a_plain_t_number_at_the_head_is_not_the_item_s_id(self):
        """The bold is not decoration, it is the grammar. An item whose TEXT
        opens with another tracker's number allocates nothing — dropping the
        `**` makes that number the item's id and jumps this queue's counter."""
        self.seed("- [ ] T900 do outro tracker precisa de acompanhamento"
                  " **Class:** AUTONOMOUS. **Effort:** S.\n")
        self.assertIn("----", self.run_tk("list").stdout)
        self.assertEqual(self.add(), "T001")

    # --- review#5: DECORATION is not prose ----------------------------------
    # The slot tolerated exactly one decoration, `~~`, so every other one made
    # the ID vanish from the count. Measured on a LIVE queue, which
    # carries `- [x] \u2705 **T020** \u2014 item text ...` today:
    # done_log_ids() dropped 20. And in isolation the counter walks BACKWARDS
    # against the pre-position-rule code \u2014 max_id 50 -> 3, and the next `add`
    # handed out T004 with T050 already spent.

    def test_decoration_before_the_id_is_still_an_allocation(self):
        """The real shape, done-log side: an emoji between the box and the ID."""
        self.seed(item(3, "tres"),
                  log="- [x] \u2705 **T050** \u2014 legado com emoji antes do ID\n")
        self.assertEqual(self.add(), "T051")

    def test_decoration_before_the_id_counts_in_next_steps_too(self):
        """Same line, before `migrate` moves it \u2014 the two sides must agree, which
        is the whole reason ONE regex reads both files."""
        self.seed(item(3, "tres"),
                  "- [x] \u2705 **T060** \u2014 legado com emoji, ainda em next-steps\n")
        self.assertEqual(self.add(), "T061")

    def test_decoration_counts_and_prose_does_not_in_the_same_file(self):
        """The discriminator, both sides in ONE number. `\u2705 ` is decoration and
        allocates T030; `feito junto com o ` is PROSE and allocates nothing.
        A rule that only widens gives T901 here; the old narrow one gives T002."""
        self.seed(item(1, "um"),
                  "- [x] \u2705 **T030** \u2014 decora\u00e7\u00e3o antes do ID\n",
                  "- [x] feito junto com o **T900** do outro tracker\n")
        self.assertEqual(self.add(), "T031")

    def test_a_bold_wrapped_strikethrough_id_is_spent_and_leaves_no_fragment(self):
        """`**~~T012~~**` \u2014 bold outside, strike inside \u2014 is the mirror of the
        form already covered. Unread, the ID was free to be handed out twice AND
        `item_title` leaked the raw `T012~~**` into `list`. Both faces are the
        same defect: two spellings of one grammar."""
        self.seed(item(1, "um"), "- [ ] **~~T012~~** \u2014 legado riscado por dentro\n")
        self.assertEqual(self.add(), "T013")
        out = self.run_tk("list").stdout
        self.assertIn("T012  ", out)        # it has an ID, and it is its own
        self.assertNotIn("~~", out)         # and the title carries no raw fragment
        self.assertNotIn("----", out)

    def test_an_open_box_parked_in_the_done_log_is_still_spent(self):
        """ITEM_ID_RE is blind to the box on purpose, in BOTH files. A `- [ ]`
        line sitting in done-log.md is not a shape any writer produces, but the
        ID on it is spent all the same \u2014 handing it out again is the one
        direction that cannot be undone. Locked here because the diagnostic
        answers it with confidence: `edit` says it already left the queue."""
        self.seed(item(1, "um"), log="- [ ] **T005** \u2014 caixa aberta parada no log\n")
        self.assertEqual(self.add(), "T006")
        r = self.run_tk("edit", "T005", "--effort", "M")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("already left the queue", r.stderr)

    # --- review#5: the ANCHOR and the WIDTH, not just the position -----------

    def test_the_marker_form_quoted_inside_an_item_text_is_not_an_allocation(self):
        """`^` is grammar, not decoration. An item whose TEXT quotes a whole
        marker mid-line allocates nothing; unanchored, that quote allocates and
        the diagnostic answers the confident wrong thing about it."""
        self.seed(item(1, "formato no doc: `- [ ] **T900** \u2014 exemplo` \u2014 s\u00f3 isso"))
        self.assertEqual(self.add(), "T002")
        r = self.run_tk("edit", "T900", "--effort", "M")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("never allocated", r.stderr)
        self.assertNotIn("Another writer", r.stderr)

    def test_a_two_digit_bold_number_is_no_id_at_the_marker_nor_in_a_title(self):
        """`{3,}` is the grammar the writer emits, not a formatting habit.
        Loosened to `+`, a legacy `**T7**` at a marker becomes an ID nobody
        handed out (`list` labels it T007, the next add jumps to T008) and the
        SAME regex strips a legitimate `**T7**` citation out of another title.
        One spelling, so one mutation reaches both faces."""
        self.seed(item(1, "um"),
                  "- [ ] **T7** \u2014 numera\u00e7\u00e3o legada **Class:** AUTONOMOUS. **Effort:** S.\n",
                  item(2, "cita o **T7** da fila antiga"))
        out = self.run_tk("list").stdout
        self.assertNotIn("T007", out)       # nobody allocated T007
        self.assertIn("**T7**", out)        # and the citation survives in the title
        self.assertEqual(self.add(), "T003")

    def test_an_unclosed_bold_carries_no_id(self):
        """The closing `**` is grammar too. `- [ ] **T005 \u2014 ...` is malformed;
        reading an ID out of it hands the number to a line no writer produced."""
        self.seed(item(1, "um"),
                  "- [ ] **T005 \u2014 negrito mal fechado **Class:** AUTONOMOUS. **Effort:** S.\n")
        out = self.run_tk("list").stdout
        self.assertIn("----", out)
        # the LABEL column, not the title: "T005 —" legitimately survives as text
        self.assertNotIn("T005  ", out)
        self.assertEqual(self.add(), "T002")


class TestDoneLogLineGrammar(QueueTest):
    """The done-log's own line has a grammar, and LOG_LINE is its ONE spelling.
    Two readers use it \u2014 LOG_ID_RE (which ID a log line hands out) and `report`
    (which lines are dated entries at all) \u2014 and each one respelled it before."""

    def add(self, text="novo"):
        r = self.run_tk("add", text, "--class", "AUTONOMOUS", "--effort", "S",
                        "--criterion", "A: c")
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout.split()[1].rstrip(":")

    def test_a_log_line_format_quoted_in_an_outcome_is_not_a_close(self):
        """The done-log side of `^`. A --how quoting the SHAPE of a log line
        lands mid-line; unanchored, that quote counts as a real close and the
        next add skips to T901."""
        self.seed(item(1, "um"))
        r = self.run_tk("done", "T001", "--how",
                        "formato: - 2026-08-01 \u2014 FEITO \u2014 T900 exemplo")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("T900 exemplo", self.body("done-log.md"))    # really landed
        self.assertEqual(self.add(), "T002")

    def test_a_two_digit_number_in_the_id_column_is_no_id(self):
        """Same width rule as the item marker, and it was spelled twice."""
        self.seed(item(1, "um"), log="- 2026-08-01 \u2014 FEITO \u2014 T7 legado \u2014 PR #1\n")
        self.assertEqual(self.add(), "T002")

    def test_report_reads_the_date_column_in_ascii_digits_only(self):
        r"""`\d` matches Unicode decimal digits and `[0-9]` does not. A line whose
        date is written in FULL-WIDTH digits is not a line this script ever
        wrote, and whether `report` shows it must not depend on which of the two
        spellings the reader happens to carry \u2014 LOG_LINE decides, once."""
        self.seed(item(1, "um"),
                  log="- \uff12\uff10\uff12\uff16-\uff10\uff18-\uff10\uff11 \u2014 FEITO \u2014 T002 dois \u2014 PR #1\n"
                      "- 2026-08-02 \u2014 FEITO \u2014 T003 tres \u2014 PR #2\n")
        out = self.run_tk("report").stdout
        self.assertIn("T003 tres", out)
        self.assertNotIn("T002 dois", out)


class TestCanonicalHead(QueueTest):
    """`edit --text` rewrites the item's HEAD and keeps the rest. The head it
    matches is the marker grammar plus compose_item's separator \u2014 respelled in
    cmd_edit it drifted from the allocator, and an item the allocator reads
    fine became one --text refuses to touch."""

    def test_a_decorated_head_is_still_editable(self):
        """A legacy item whose head carries an emoji is a head the allocator
        accepts; --text must accept it too, and must keep the decoration."""
        self.seed("- [ ] \u2705 **T005** \u2014 texto antigo **Class:** AUTONOMOUS."
                  " **Effort:** S. **Criterion:** A: x.\n")
        r = self.run_tk("edit", "T005", "--text", "texto novo")
        self.assertEqual(r.returncode, 0, r.stderr)
        body = self.body()
        self.assertIn("- [ ] \u2705 **T005** \u2014 texto novo **Class:** AUTONOMOUS.", body)
        self.assertNotIn("texto antigo", body)


class TestDirResolution(QueueTest):
    """`list` and `add` must resolve the SAME file from the same cwd — the
    other half of T060's criterion."""

    def test_same_file_regardless_of_where_dir_sits_on_the_line(self):
        self.seed(item(1, "um"))
        r = subprocess.run([sys.executable, TK, "--dir", self.mem, "add", "novo",
                            "--class", "AUTONOMOUS", "--effort", "S", "--criterion", "A: c"],
                           capture_output=True, text=True, cwd=self.dir,
                           env=dict(os.environ, HOME=self.home))
        self.assertEqual(r.returncode, 0, r.stderr)
        after = self.run_tk("list")
        self.assertIn("T002", after.stdout)
        self.assertIn("**T002**", self.body())

    def test_add_then_list_agree_from_the_same_cwd(self):
        self.seed()
        add = self.run_tk("add", "recem-criado", "--class", "AUTONOMOUS",
                          "--effort", "S", "--criterion", "A: c")
        self.assertEqual(add.returncode, 0, add.stderr)
        new_id = add.stdout.split()[1].rstrip(":")
        self.assertIn(new_id, self.run_tk("list").stdout)
        # and the freshly created item is editable by both ID forms
        self.assertEqual(self.run_tk("edit", new_id, "--effort", "M").returncode, 0)
        self.assertEqual(self.run_tk("edit", str(int(new_id[1:])), "--risk", "baixo").returncode, 0)


# --- T064: the project tag must survive the close, and group the report ---

class TestProjectTagInDoneLog(QueueTest):
    def test_tag_reaches_the_done_log(self):
        self.seed(item(1, "com tag", project="tk"))
        r = self.run_tk("done", "T001", "--how", "PR #9")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("**Project:** tk.", self.body("done-log.md"))

    def test_tag_survives_summary_replacing_the_text(self):
        self.seed(item(1, "com tag", project="ambiente"))
        self.run_tk("done", "T001", "--how", "PR #9", "--summary", "texto trocado")
        log = self.body("done-log.md")
        self.assertIn("texto trocado", log)
        self.assertIn("**Project:** ambiente.", log)

    def test_report_groups_by_tag_untagged_last(self):
        self.seed(item(1, "um", project="tk"), item(2, "dois", project="ambiente"),
                  item(3, "tres"))
        for iid in ("T001", "T002", "T003"):
            self.assertEqual(self.run_tk("done", iid, "--how", "x").returncode, 0)
        out = self.run_tk("report", "--since", "2026-01-01").stdout
        headers = [ln for ln in out.splitlines() if ln.startswith("#### ")]
        self.assertEqual(headers, ["#### ambiente", "#### tk", "#### no project"])

    def test_a_note_quoting_the_marker_does_not_become_a_group(self):
        """The real done-log carries a --note whose prose contains a literal
        `**Project:**`. Reading the whole entry would group it under 'para'."""
        self.seed(item(1, "um", project="tk"))
        self.run_tk("done", "T001", "--how", "x", "--note",
                    "close_item nao levava a tag Project para o done-log")
        # a legacy entry written before this fix, note included, hand-seeded to
        # reproduce exactly what is already on disk in the real log
        self.write("done-log.md", self.body("done-log.md") +
                   "- 2026-08-13 — FEITO — T059 kickoff — PR #2\n"
                   "  ficou de fora: close_item nao leva a tag **Project:** para o done-log.\n")
        out = self.run_tk("report", "--since", "2026-01-01").stdout
        headers = [ln for ln in out.splitlines() if ln.startswith("#### ")]
        self.assertNotIn("#### para", headers)
        self.assertEqual(headers, ["#### tk", "#### no project"])

    def test_an_all_untagged_log_prints_flat_as_before(self):
        self.seed(item(1, "um"), item(2, "dois"))
        self.run_tk("done", "T001", "--how", "x")
        self.run_tk("done", "T002", "--how", "y")
        out = self.run_tk("report", "--since", "2026-01-01").stdout
        self.assertNotIn("####", out)
        self.assertIn("T001", out)
        self.assertIn("T002", out)


# --- T065: a field marker inside free text hijacks the field --------------

MARKER_TEXT = ("tk-queue: preservar a tag e levar o campo **Project:** para o "
               "done-log e agrupar o report por ela")


class TestEmbeddedMarker(QueueTest):
    def test_add_refuses_a_marker_in_the_text(self):
        self.seed()
        before = self.body()
        r = self.run_tk("add", MARKER_TEXT, "--class", "AUTONOMOUS", "--effort", "S",
                        "--criterion", "A: x", "--project", "tk")
        self.assertEqual(r.returncode, 1)
        self.assertIn("field-marker shape", r.stderr)
        self.assertEqual(self.body(), before, "a refused add still wrote to the queue")

    def test_add_refuses_it_in_every_free_text_flag(self):
        for flag, val in (("--criterion", "A: roda **Source:** x"),
                          ("--effort", "S **Risk:** alto"),
                          ("--risk", "**Class:** DECISION"),
                          ("--source", "tropeço **Criterion:** y")):
            with self.subTest(flag=flag):
                self.seed()
                argv = {"--effort": "S", "--criterion": "A: x", flag: val}
                r = self.run_tk("add", "texto limpo", "--class", "AUTONOMOUS",
                                *[a for kv in argv.items() for a in kv])
                self.assertEqual(r.returncode, 1, f"{flag} was accepted: {r.stdout}")
                self.assertIn("field-marker shape", r.stderr)

    def test_edit_refuses_a_marker_in_the_new_text(self):
        self.seed(item(1, "texto limpo", project="tk"))
        before = self.body()
        r = self.run_tk("edit", "T001", "--text", "novo **Risk:** injetado")
        self.assertEqual(r.returncode, 1)
        self.assertIn("field-marker shape", r.stderr)
        self.assertEqual(self.body(), before)

    def test_close_refuses_a_marker_in_summary_and_outcome(self):
        # both share the log entry's first line with the appended project tag
        for argv in (("--how", "x", "--summary", "y **Project:** z"),
                     ("--how", "feito **Project:** z")):
            with self.subTest(argv=argv):
                self.seed(item(1, "um", project="tk"))
                r = self.run_tk("done", "T001", *argv)
                self.assertEqual(r.returncode, 1)
                self.assertIn("field-marker shape", r.stderr)
                # body() returns "" for a missing file too, so assert on the queue:
                # the item must still be open, i.e. nothing was closed
                self.assertIn("**T001**", self.body())

    def test_a_note_may_still_quote_a_marker(self):
        """--note lands on continuation lines, which log_entry_tag never reads.
        Guarding it would forbid the exact note this queue's real log carries
        while describing this very field."""
        self.seed(item(1, "um", project="tk"))
        r = self.run_tk("done", "T001", "--how", "x", "--note",
                        "close_item nao levava a tag **Project:** para o done-log")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("**Project:** para o done-log", self.body("done-log.md"))
        out = self.run_tk("report", "--since", "2026-01-01").stdout
        self.assertNotIn("#### para", out)

    def test_plain_prose_naming_the_fields_is_not_refused(self):
        """T065's own text lists the field names in parentheses. Only the bold
        '**Word:**' shape may trigger the guard — never the bare word."""
        self.seed()
        r = self.run_tk("add",
                        "texto que cita Project, Class, Effort, Risk, Criterion e Source "
                        "sem negrito, e fala de risco e do projeto",
                        "--class", "AUTONOMOUS", "--effort", "S",
                        "--criterion", "A: x", "--project", "tk")
        self.assertEqual(r.returncode, 0, r.stderr)
        out = self.run_tk("list").stdout
        self.assertIn("## tk", out)
        self.assertIn("Criterion", out)          # title not truncated at a field name

    def test_list_groups_by_the_project_that_was_passed(self):
        self.seed()
        self.run_tk("add", "item de projeto", "--class", "AUTONOMOUS", "--effort", "S",
                    "--criterion", "A: x", "--project", "tk")
        out = self.run_tk("list").stdout
        self.assertIn("## tk", out)
        self.assertNotIn("## para", out)

    def test_edit_rewrites_the_real_field_not_prose_that_looks_like_one(self):
        """Legacy items predating the guard can carry the shape in their text;
        editing a field must not replace the author's prose with the flag."""
        legacy = ("- [ ] **T001** — levar o campo **Project:** para o done-log "
                  "**Class:** AUTONOMOUS. **Effort:** S. **Criterion:** A: x. "
                  "**Project:** tk. **Source:** 2026-08-13\n")
        self.seed(legacy)
        r = self.run_tk("edit", "T001", "--project", "ambiente")
        self.assertEqual(r.returncode, 0, r.stderr)
        body = self.body()
        self.assertIn("levar o campo **Project:** para o done-log", body)  # prose intact
        self.assertIn("**Project:** ambiente.", body)
        self.assertNotIn("**Project:** tk.", body)


# --- T070: `--risk none` DELETES the field --------------------------------

class TestRiskDeletion(QueueTest):
    """`--risk ''` is a silent no-op (argparse hands an empty string and every
    writer treats it as falsy), so a Risk line written when it was true could
    never be removed — and a stale Risk keeps the item out of every afk package
    for good. The reserved word `none` clears it."""

    def test_edit_clears_the_risk_field(self):
        self.seed(item(19, "re-triar", risk="branch afk/x pode sumir"))
        r = self.run_tk("edit", "T019", "--risk", "none")
        self.assertEqual(r.returncode, 0, r.stderr)
        body = self.body()
        self.assertNotIn("**Risk:**", body)
        self.assertNotIn("branch afk/x", body)

    def test_the_surrounding_fields_survive_intact(self):
        """Deleting the middle of a one-line block must not glue its neighbours
        together nor eat one of them."""
        self.seed(item(19, "re-triar", risk="dano X", project="tk"))
        self.assertEqual(self.run_tk("edit", "T019", "--risk", "none").returncode, 0)
        body = self.body()
        self.assertIn("**Class:** AUTONOMOUS. **Effort:** S. **Criterion:** A: x.", body)
        self.assertIn("**Project:** tk.", body)
        self.assertIn("**Source:** 2026-08-13", body)
        self.assertIn("- [ ] **T019** — re-triar **Class:**", body)

    def test_no_trailing_blank_is_left_when_risk_was_the_last_field(self):
        """`edit --risk` on an item that had none APPENDS the field at the end of
        the line. Clearing it there leaves the separator blank dangling at
        end-of-line — invisible in a diff, and it is what the queue file keeps."""
        self.seed(item(19, "re-triar"))
        self.assertEqual(self.run_tk("edit", "T019", "--risk", "dano X").returncode, 0)
        self.assertTrue(self.body().rstrip("\n").endswith("**Risk:** dano X."), self.body())
        self.assertEqual(self.run_tk("edit", "T019", "--risk", "none").returncode, 0)
        for line in self.body().splitlines():
            self.assertEqual(line, line.rstrip(), f"trailing blank left: {line!r}")

    def test_the_reserved_word_is_case_and_space_tolerant(self):
        """A Risk field whose content is the word for "no risk" is never what the
        caller meant — `None` and ` none ` must clear, not write.

        Only `None`/`NONE`/` none ` prove the tolerance: the `none` subtest is
        VACUOUS against the mutation that drops `.strip().lower()`, since exact
        matching still clears it. It stays as the happy-path form the docs tell
        callers to type. Note the general trap it illustrates: subtest-level
        vacuity is invisible to mutations.py, because one falling subtest already
        reddens the whole test — see that file's docstring.
        """
        for form in ("none", "None", "NONE", " none "):
            with self.subTest(form=form):
                self.seed(item(19, "re-triar", risk="dano X"))
                r = self.run_tk("edit", "T019", "--risk", form)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertNotIn("**Risk:**", self.body())

    def test_a_hard_break_elsewhere_in_the_block_survives(self):
        """The repair of the blank left by the removal must be anchored AT the
        removal site. A sweep over the whole block eats a two-space Markdown hard
        break on a continuation line — a silent rewrap of text this command was
        never asked to touch, and invisible in a diff."""
        block = (item(19, "re-triar", risk="dano X")
                 + "  contexto na primeira linha  \n  e a continuação\n")
        self.seed(block)
        r = self.run_tk("edit", "T019", "--risk", "none")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("**Risk:**", self.body())
        self.assertIn("  contexto na primeira linha  \n", self.body())

    def test_clearing_an_item_that_has_no_risk_is_a_no_op(self):
        self.seed(item(19, "sem risco"))
        before = self.body()
        r = self.run_tk("edit", "T019", "--risk", "none")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.body(), before)

    def test_add_writes_no_risk_line_for_the_reserved_word(self):
        self.seed()
        r = self.run_tk("add", "item sem risco", "--class", "AUTONOMOUS",
                        "--effort", "S", "--criterion", "A: x", "--risk", "none")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("**Risk:**", self.body())

    def test_a_real_risk_is_still_written_and_still_replaceable(self):
        """The other direction: the reserved word must not swallow ordinary
        values, or the field becomes unwritable instead of merely clearable."""
        self.seed()
        r = self.run_tk("add", "item arriscado", "--class", "AUTONOMOUS", "--effort", "S",
                        "--criterion", "A: x", "--risk", "apaga dados de produção")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("**Risk:** apaga dados de produção.", self.body())
        self.assertEqual(self.run_tk("edit", "T001", "--risk", "nenhum de fato").returncode, 0)
        self.assertIn("**Risk:** nenhum de fato.", self.body())
        self.assertNotIn("apaga dados", self.body())

    def test_clearing_rewrites_the_real_field_not_prose_that_looks_like_one(self):
        """Same trap as the set path: a legacy item can carry the marker shape
        inside its own text, and the real field is always the LAST one."""
        legacy = ("- [ ] **T001** — decidir se o campo **Risk:** ainda vale "
                  "**Class:** AUTONOMOUS. **Effort:** S. **Risk:** dano X. "
                  "**Criterion:** A: x. **Source:** 2026-08-13\n")
        self.seed(legacy)
        r = self.run_tk("edit", "T001", "--risk", "none")
        self.assertEqual(r.returncode, 0, r.stderr)
        body = self.body()
        self.assertIn("decidir se o campo **Risk:** ainda vale", body)   # prose intact
        self.assertNotIn("dano X", body)
        # and the field really went away instead of being SET to the reserved word:
        # the only marker left is the prose one
        self.assertEqual(body.count("**Risk:**"), 1, body)


# --- T071: the size ceiling gates the TEXT, not a field edit --------------

class TestCeilingScope(QueueTest):
    """The ceiling exists to stop an item's prose from becoming an essay. Gating
    field edits too meant a legacy oversized item needed --force merely to gain a
    --project tag — which trains the caller to type --force on edits, disarming
    the guard exactly where it matters."""

    def oversized(self, iid=13):
        block = item(iid, "contexto legado que ninguém migrou. " * 20)
        self.assertGreater(len(block), load_tk().CEILING,
                           "fixture is not actually over the ceiling")
        return block

    def test_every_short_field_edit_passes_without_force(self):
        """The T071 guarantee, and it covers the SHORT fields only: those are
        bounded by construction, so exempting them from the block's budget costs
        a bounded number of chars and cannot accumulate (a field is replaced, not
        appended, once present).

        Note the `--class` subtest is vacuous against the mutation that puts the
        block ceiling back on field edits: BLOCKED is shorter than AUTONOMOUS,
        so that edit SHRINKS the item and never reaches the ceiling either way.
        It is kept as coverage of the flag, not as proof — see mutations.py's
        KNOWN BLIND SPOT. (Every class is shorter than AUTONOMOUS, so no value
        fixes that; DECISION specifically would also need --deferred, which is a
        different guard's business — TestDecisionDeferralGate.)"""
        for flag, val, expected in (("--project", "ambiente", "**Project:** ambiente."),
                                    ("--class", "BLOCKED", "**Class:** BLOCKED."),
                                    ("--effort", "L (~2h)", "**Effort:** L (~2h).")):
            with self.subTest(flag=flag):
                self.seed(self.oversized())
                r = self.run_tk("edit", "T013", flag, val)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertNotIn("ceiling", r.stderr)
                self.assertIn(expected, self.body())

    def test_a_free_text_field_edit_is_measured_against_the_block(self):
        """The other half of the split: --criterion and --risk are prose, so they
        answer to the block ceiling exactly as --text does. On an already
        oversized item that means a refusal — which is the point: growing an item
        that is already too long is what the ceiling is for."""
        for flag, val in (("--risk", "dano X"), ("--criterion", "B: veredito")):
            with self.subTest(flag=flag):
                self.seed(self.oversized())
                before = self.body()
                r = self.run_tk("edit", "T013", flag, val)
                self.assertEqual(r.returncode, 1, r.stdout)
                self.assertIn("ceiling 700", r.stderr)
                self.assertEqual(self.body(), before)
                # and --force is the documented way through
                self.assertEqual(self.run_tk("edit", "T013", flag, val, "--force").returncode,
                                 0)

    def midsized(self, iid=14):
        """A legal item — under the block ceiling — with little room left. That
        is where the combining vector bites: on a nearly empty item, two capped
        field values simply cannot reach 700, so a fixture starting there would
        pass with the guard OFF and prove nothing."""
        block = item(iid, "contexto que ocupa espaco. " * 13)
        tk = load_tk()
        self.assertLess(len(block), tk.CEILING, "fixture must start legal")
        self.assertGreater(len(block) + 2 * tk.FIELD_CEILING, tk.CEILING,
                           "fixture has too much room left to test the ceiling")
        return block

    def test_combining_free_text_fields_cannot_cross_the_block_ceiling(self):
        """The bypass one level below the per-field ceiling: every value under
        the field ceiling, several of them in ONE call. Measured before this
        rule: `--effort E*199 --risk R*199 --criterion C*199` returned 0 and left
        the item at 709 chars, past a 700 ceiling, with no --force."""
        tk = load_tk()
        self.seed(self.midsized())
        before = self.body()
        r = self.run_tk("edit", "T014", "--effort", "M (~30min)",
                        "--risk", "R" * 190, "--criterion", "C" * 190)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ceiling 700", r.stderr)
        self.assertEqual(self.body(), before)
        for line in self.body().splitlines():
            self.assertLessEqual(len(line), tk.CEILING, line[:120])

    def test_repeated_field_edits_cannot_grow_the_item_without_limit(self):
        """One call at a time, each starting from the already-inflated size — the
        shape a rule looking only at the per-call delta would never stop."""
        tk = load_tk()
        self.seed(self.midsized())
        refused = False
        for n in range(12):
            flag = "--criterion" if n % 2 else "--risk"
            r = self.run_tk("edit", "T014", flag, f"{flag[2:3]}{n} " + "y" * 185)
            if r.returncode != 0:
                refused = True
                self.assertIn("ceiling", r.stderr)
                break
        self.assertTrue(refused, "12 edits in a row and the item never hit a ceiling")
        for line in self.body().splitlines():
            self.assertLessEqual(len(line), tk.CEILING, line[:120])

    def test_a_text_edit_over_the_ceiling_is_still_refused(self):
        self.seed(item(1, "curto"))
        r = self.run_tk("edit", "T001", "--text", "ensaio. " * 120)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ceiling", r.stderr)
        self.assertIn("- [ ] **T001** — curto ", self.body())   # nothing was rewritten

    def test_a_text_edit_growing_an_already_oversized_item_is_refused(self):
        self.seed(self.oversized())
        r = self.run_tk("edit", "T013", "--text", "contexto legado que ninguém migrou. " * 30)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ceiling", r.stderr)

    def test_a_text_edit_that_shrinks_an_oversized_item_is_allowed(self):
        self.seed(self.oversized())
        r = self.run_tk("edit", "T013", "--text", "texto enxuto agora")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("- [ ] **T013** — texto enxuto agora **Class:**", self.body())

    def test_force_still_raises_the_ceiling_for_a_text_edit(self):
        self.seed(item(1, "curto"))
        r = self.run_tk("edit", "T001", "--text", "ensaio. " * 120, "--force")
        self.assertEqual(r.returncode, 0, r.stderr)

    # --- the field ceiling: what keeps the block exemption from being a bypass ---

    def test_a_field_value_over_its_ceiling_is_refused(self):
        """The exemption above is from the BLOCK's budget, not a licence to write
        an essay through another flag. Measured before this ceiling existed:
        `edit T001 --criterion "<900 chars>"` returned 0 and took a 100-char item
        to 1014 chars — past the normal ceiling AND past the forced one."""
        tk = load_tk()
        big = "x" * (tk.FIELD_CEILING + 1)
        short_big = "x" * (tk.FIELD_CEILING_SHORT + 1)
        for flag, val in (("--criterion", "A: " + big), ("--risk", big),
                          ("--effort", "S " + short_big), ("--project", "a" * 250)):
            with self.subTest(flag=flag):
                self.seed(item(1, "curto"))
                before = self.body()
                r = self.run_tk("edit", "T001", flag, val)
                self.assertEqual(r.returncode, 1, f"{flag} was accepted: {r.stdout}")
                self.assertIn("field ceiling", r.stderr)
                self.assertEqual(self.body(), before, "a refused edit still wrote")

    def test_the_bypass_cannot_push_the_item_past_the_block_ceiling(self):
        """The bug as it was reported, asserted on the outcome rather than on the
        message: no field edit may leave the item over the block ceiling."""
        tk = load_tk()
        self.seed(item(1, "curto"))
        r = self.run_tk("edit", "T001", "--criterion", "A: " + "ensaio " * 130)
        self.assertEqual(r.returncode, 1, r.stdout)
        for line in self.body().splitlines():
            self.assertLessEqual(len(line), tk.CEILING, line[:120])

    def test_add_measures_field_values_too(self):
        """Same ceiling on both, or the file could hold a value no `edit` is
        allowed to write."""
        tk = load_tk()
        self.seed()
        r = self.run_tk("add", "texto curto", "--class", "AUTONOMOUS", "--effort", "S",
                        "--criterion", "A: " + "x" * tk.FIELD_CEILING)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("field ceiling", r.stderr)

    def test_a_field_value_under_its_ceiling_still_passes(self):
        """The false-positive direction: a ceiling that over-triggers makes the
        fields unwritable, which is worse than the bypass it replaced. Measured
        on a normal-sized item, where the block ceiling has room to spare."""
        tk = load_tk()
        self.seed(item(1, "curto"))
        r = self.run_tk("edit", "T001", "--criterion", "A: " + "x" * (tk.FIELD_CEILING - 10))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("ceiling", r.stderr)
        self.seed(self.oversized())
        r = self.run_tk("edit", "T013", "--project", "ambiente")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_force_raises_the_field_ceiling(self):
        tk = load_tk()
        self.seed(item(1, "curto"))
        val = "A: " + "x" * (tk.FIELD_CEILING + 50)
        self.assertEqual(self.run_tk("edit", "T001", "--criterion", val).returncode, 1)
        r = self.run_tk("edit", "T001", "--criterion", val, "--force")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_add_is_unchanged_by_all_this(self):
        self.seed()
        r = self.run_tk("add", "ensaio. " * 120, "--class", "AUTONOMOUS",
                        "--effort", "S", "--criterion", "A: x")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ceiling", r.stderr)


# --- T072: every mutation names the queue it is writing -------------------

class TestTargetQueueAnnounced(QueueTest):
    """The target queue is INFERRED — from --dir, or from the cwd when absent —
    and an inference nobody sees is an inference nobody checks. An agent's shell
    keeps its cwd between calls, so an `edit` has already landed on a homonymous
    item in ANOTHER project's queue while reporting "T019 updated"."""

    def test_every_mutating_command_names_the_memdir_on_stderr(self):
        for argv in (("add", "novo", "--class", "AUTONOMOUS", "--effort", "S",
                      "--criterion", "A: x"),
                     ("edit", "T001", "--effort", "L"),
                     ("done", "T001", "--how", "PR #1"),
                     ("cancel", "T001", "--why", "n/a"),
                     ("bump", "T001"),
                     ("claim", "T001", "--as", "alpha"),
                     ("release", "T001"),
                     ("migrate",)):
            with self.subTest(cmd=argv[0]):
                self.seed(item(1, "um"))
                r = self.run_tk(*argv)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertIn(self.mem, r.stderr, f"{argv[0]} did not name the queue")

    def test_the_announced_dir_is_the_one_actually_written(self):
        """The incident's exact shape: two queues carrying the same ID. Only the
        printed line distinguishes the queue that was edited from the one the
        caller believed they were in."""
        other = os.path.join(self.dir, "other-memory")
        os.makedirs(other)
        self.seed(item(19, "revisar Risk obsoleto"))
        with open(os.path.join(other, "next-steps.md"), "w", encoding="utf-8") as f:
            f.write(HEADER + item(19, "revisar Risk obsoleto"))
        r = subprocess.run([sys.executable, TK, "edit", "T019", "--effort", "L",
                            "--dir", other], capture_output=True, text=True, cwd=self.dir,
                           env=dict(os.environ, HOME=self.home))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(other, r.stderr)
        self.assertNotIn(self.mem, r.stderr)
        self.assertNotIn("**Effort:** L.", self.body())   # this queue was untouched

    def test_it_goes_to_stderr_and_never_pollutes_stdout(self):
        """stdout is parsed — the suite itself reads the new ID out of `add`'s
        stdout, and so does anything scripting the CLI."""
        self.seed(item(1, "um"))
        r = self.run_tk("add", "novo", "--class", "AUTONOMOUS", "--effort", "S",
                        "--criterion", "A: x")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn(self.mem, r.stdout)
        self.assertEqual(r.stdout.splitlines()[0].split()[1].rstrip(":"), "T002")

    def test_the_readers_of_one_queue_name_it_too_and_report_stays_silent(self):
        """A read is what a decision is made from, and the same wrong cwd that
        made an `edit` land elsewhere made a `list` from the repository root
        answer with TWO items of another project's queue, in silence (2026-08-27).
        `list` and `pack` read ONE inferred queue, so they announce it. `report`
        sweeps every project's queue and has no single dir to name."""
        self.seed(item(1, "um"))
        for argv in (("list",), ("pack",)):
            with self.subTest(cmd=argv[0]):
                r = self.run_tk(*argv)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertIn(self.mem, r.stderr, f"{argv[0]} did not name the queue")
                self.assertIn("/memory", r.stderr)
                # stdout is parsed — `pack` is read by the afk flow line by line
                self.assertNotIn(self.mem, r.stdout)
        r = self.run_tk("report", "--since", "2026-01-01")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn(f"queue: {self.mem}", r.stderr)


# --- review#2: the real field is the one in the CHAIN, never the last marker ---

# the reported shape: a legacy item whose continuation note quotes the marker
# AFTER the real field. ensure_no_embedded_marker never protected these — it only
# guards items added after it existed, and legacy items are the whole population
# the ceiling exemption exists to serve.
NOTE_ITEM = ("- [ ] **T007** — item legado **Class:** AUTONOMOUS. **Effort:** S. "
             "**Risk:** risco real. **Criterion:** A: x.\n"
             "  nota de continuacao com **Risk:** dentro do texto tambem\n")


class TestFieldChain(QueueTest):
    """Taking the LAST marker in the block reaches into continuation lines. On
    `--risk none` that deleted the note's text and left the real Risk standing,
    while printing "T007 updated": a no-op on the field named, destruction of
    text nobody pointed at, on the deletion path."""

    def test_clearing_hits_the_real_field_and_spares_the_note(self):
        self.seed(NOTE_ITEM)
        r = self.run_tk("edit", "T007", "--risk", "none")
        self.assertEqual(r.returncode, 0, r.stderr)
        body = self.body()
        self.assertNotIn("**Risk:** risco real.", body)      # the real field went
        self.assertIn("nota de continuacao com **Risk:** dentro do texto tambem", body)

    def test_setting_hits_the_real_field_and_spares_the_note(self):
        self.seed(NOTE_ITEM)
        r = self.run_tk("edit", "T007", "--risk", "risco novo")
        self.assertEqual(r.returncode, 0, r.stderr)
        body = self.body()
        self.assertIn("**Risk:** risco novo.", body)
        self.assertNotIn("risco real", body)
        self.assertIn("nota de continuacao com **Risk:** dentro do texto tambem", body)

    def test_a_marker_only_outside_the_chain_is_refused_not_guessed(self):
        """No Risk among the real fields, one quoted in the note. Editing the
        note is never what the caller meant, and deleting it is unrecoverable —
        so the command refuses and says why."""
        item_ = ("- [ ] **T008** — legado **Class:** AUTONOMOUS. **Effort:** S. "
                 "**Criterion:** A: x.\n"
                 "  a nota fala de **Risk:** como conceito\n")
        self.seed(item_)
        before = self.body()
        for val in ("none", "risco novo"):
            with self.subTest(val=val):
                r = self.run_tk("edit", "T008", "--risk", val)
                self.assertEqual(r.returncode, 1, r.stdout)
                self.assertIn("OUTSIDE its field chain", r.stderr)
                self.assertIn("Nothing was changed", r.stderr)
                self.assertEqual(self.body(), before)

    def test_an_ambiguous_chain_is_refused_not_guessed(self):
        """Prose that ends in a period right before the fields is genuinely
        indistinguishable from a field — two Projects in the chain, and the
        command says so instead of picking one."""
        item_ = ("- [ ] **T009** — levar o campo **Project:** para o done-log. "
                 "**Class:** AUTONOMOUS. **Effort:** S. **Criterion:** A: x. "
                 "**Project:** tk. **Source:** 2026-08-13\n")
        self.seed(item_)
        before = self.body()
        r = self.run_tk("edit", "T009", "--project", "ambiente")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ambiguous", r.stderr)
        self.assertEqual(self.body(), before)

    def test_a_field_appended_after_source_stays_editable(self):
        """Source is the one field compose_item writes WITHOUT a trailing period,
        so a chain rule keyed on periods alone would stop there — and every field
        appended after Source (which is where `edit` used to put them) would fall
        outside the chain, making the item uneditable from the next call on."""
        self.seed(item(1, "um", project="tk"))
        self.assertEqual(self.run_tk("edit", "T001", "--risk", "dano X").returncode, 0)
        r = self.run_tk("edit", "T001", "--project", "ambiente")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("**Project:** ambiente.", self.body())
        self.assertEqual(self.run_tk("edit", "T001", "--risk", "none").returncode, 0)
        self.assertNotIn("**Risk:**", self.body())

    def test_a_marker_before_the_fields_is_still_prose(self):
        """The case the previous rule already got right, kept as the other side:
        prose that does NOT end in a period stays prose, and the real field wins."""
        legacy = ("- [ ] **T001** — levar o campo **Project:** para o done-log "
                  "**Class:** AUTONOMOUS. **Effort:** S. **Criterion:** A: x. "
                  "**Project:** tk. **Source:** 2026-08-13\n")
        self.seed(legacy)
        r = self.run_tk("edit", "T001", "--project", "ambiente")
        self.assertEqual(r.returncode, 0, r.stderr)
        body = self.body()
        self.assertIn("levar o campo **Project:** para o done-log", body)
        self.assertIn("**Project:** ambiente.", body)
        self.assertNotIn("**Project:** tk.", body)


# --- review#3: the close flags are lines too ------------------------------

class TestCloseFieldCeilings(QueueTest):
    """--how/--why/--summary/--note go to the done-log, not to the queue, so the
    damage is smaller — but it is the same hole, and the log line is the record
    that OUTLIVES the item."""

    def test_done_measures_how_summary_and_note(self):
        tk = load_tk()
        big = "x" * (tk.FIELD_CEILING + 1)
        for argv in (("--how", big), ("--how", "PR #1", "--summary", big),
                     ("--how", "PR #1", "--note", big)):
            with self.subTest(argv=argv[0] if len(argv) == 2 else argv[2]):
                self.seed(item(1, "um"))
                r = self.run_tk("done", "T001", *argv)
                self.assertEqual(r.returncode, 1, r.stdout)
                self.assertIn("field ceiling", r.stderr)
                self.assertIn("**T001**", self.body())        # nothing was closed
                self.assertEqual(self.body("done-log.md"), "")

    def test_cancel_measures_why(self):
        tk = load_tk()
        self.seed(item(1, "um"))
        r = self.run_tk("cancel", "T001", "--why", "x" * (load_tk().FIELD_CEILING + 1))
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("field ceiling", r.stderr)
        self.assertIn("**T001**", self.body())
        del tk

    def test_force_raises_it_and_an_ordinary_close_is_untouched(self):
        """The false-positive direction: --note exists for work that left no
        pointer, so it must stay writable — at ordinary length always, and
        beyond it with --force."""
        tk = load_tk()
        self.seed(item(1, "um"), item(2, "dois"))
        r = self.run_tk("done", "T001", "--how", "PR #1",
                        "--note", "n" * (tk.FIELD_CEILING - 10))
        self.assertEqual(r.returncode, 0, r.stderr)
        r = self.run_tk("done", "T002", "--how", "PR #2",
                        "--note", "n" * (tk.FIELD_CEILING + 50), "--force")
        self.assertEqual(r.returncode, 0, r.stderr)


# --- T119: a DECISION is either asked at birth or deferred on the record ---

def decision_item(iid, text, deferred="afk", **kw):
    """A DECISION item as `add` writes one — with its Deferred field."""
    base = item(iid, text, klass="DECISION", **kw)
    return base.replace("**Class:** DECISION.",
                        f"**Class:** DECISION. **Deferred:** {deferred}.", 1)


class TestDecisionDeferralGate(QueueTest):
    """A DECISION item parks the queue until the user is back, so parking it has
    to be a deliberate act. The default path is asking the decision at birth and
    writing it into the item — the item is then AUTONOMOUS. Deferring is the
    exception, and it must carry its justification into the file."""

    ADD = ("add", "decidir algo", "--effort", "S", "--criterion", "B: veredito")

    def test_add_decision_without_a_deferral_is_refused_and_names_both_paths(self):
        self.seed()
        r = self.run_tk(*self.ADD, "--class", "DECISION")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("--deferred", r.stderr)
        # the two paths, not just the refusal: embed the decision, or defer it
        self.assertIn("--criterion", r.stderr)
        self.assertIn("AUTONOMOUS", r.stderr)
        self.assertNotIn("- [ ]", self.body())          # nothing was written

    def test_the_justification_may_not_be_blank(self):
        for blank in ("", "   "):
            with self.subTest(blank=repr(blank)):
                self.seed()
                r = self.run_tk(*self.ADD, "--class", "DECISION", "--deferred", blank)
                self.assertEqual(r.returncode, 1, r.stdout)
                self.assertIn("cannot be blank", r.stderr)
                self.assertNotIn("- [ ]", self.body())

    def test_the_reserved_clear_word_is_no_justification_either(self):
        """`none` DELETES a field elsewhere in this script, so accepting it here
        would write a DECISION item carrying no deferral at all — the gate open
        by way of the one word that means "no field"."""
        self.seed()
        r = self.run_tk(*self.ADD, "--class", "DECISION", "--deferred", "none")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("--deferred", r.stderr)
        self.assertNotIn("- [ ]", self.body())

    def test_a_deferral_reaches_the_item(self):
        self.seed()
        r = self.run_tk(*self.ADD, "--class", "DECISION", "--deferred", "afk")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("**Class:** DECISION. **Deferred:** afk.", self.body())

    def test_the_other_classes_are_untouched_by_the_gate(self):
        """The over-trigger direction: a gate that fires on every add stops the
        queue rather than the silent deferral."""
        for klass in ("AUTONOMOUS", "BLOCKED", "EXTERNAL", "RECURRING"):
            with self.subTest(klass=klass):
                self.seed()
                r = self.run_tk(*self.ADD, "--class", klass)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertNotIn("**Deferred:**", self.body())

    def test_a_deferral_without_the_decision_class_is_refused(self):
        """A Deferred field on an AUTONOMOUS item is a field no reader honours —
        and `pack` reads it to keep a deferred decision out of the package."""
        self.seed()
        r = self.run_tk(*self.ADD, "--class", "AUTONOMOUS", "--deferred", "afk")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertNotIn("- [ ]", self.body())

    def test_edit_to_decision_passes_the_same_gate(self):
        """`add AUTONOMOUS` + `edit --class DECISION` is the two-command bypass
        the gate exists to close (#70)."""
        self.seed(item(1, "um"))
        r = self.run_tk("edit", "T001", "--class", "DECISION")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("--deferred", r.stderr)
        self.assertIn("**Class:** AUTONOMOUS.", self.body())     # unchanged
        r = self.run_tk("edit", "T001", "--class", "DECISION", "--deferred", "afk")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("**Class:** DECISION.", self.body())
        self.assertIn("**Deferred:** afk.", self.body())

    def test_a_deferral_already_on_the_item_satisfies_the_gate(self):
        self.seed(decision_item(1, "decidir"))
        r = self.run_tk("edit", "T001", "--class", "DECISION", "--effort", "L")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("**Effort:** L.", self.body())

    def test_a_legacy_decision_item_stays_editable(self):
        """The over-trigger direction on `edit`: the gate fires on the CHANGE to
        DECISION, never on an unrelated edit of an item that already is one —
        every DECISION item in a real queue predates this field."""
        self.seed(item(1, "decidir", klass="DECISION"))
        r = self.run_tk("edit", "T001", "--effort", "L")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("**Effort:** L.", self.body())

    def test_the_deferral_cannot_be_dropped_while_the_item_stays_a_decision(self):
        """The third bypass: clear the field and the item is a DECISION with no
        deferral on the record, reached in one command."""
        self.seed(decision_item(1, "decidir"))
        r = self.run_tk("edit", "T001", "--deferred", "none")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("**Deferred:** afk.", self.body())

    def test_leaving_the_decision_class_takes_the_deferral_with_it(self):
        """A deferral is an attribute of the DECISION: left behind on an item
        that is no longer one, it is the stale-Risk failure again — a field that
        was true when written and is read by `pack` long after."""
        self.seed(decision_item(1, "decidir"))
        r = self.run_tk("edit", "T001", "--class", "AUTONOMOUS")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("**Deferred:**", self.body())
        self.assertIn("**Class:** AUTONOMOUS.", self.body())
        self.assertIn("Deferred", r.stderr)     # the removal is announced, not silent

    def test_edit_refuses_a_deferral_on_an_item_that_is_not_a_decision(self):
        """The same refusal as on `add`, on the side that could otherwise reach in
        two commands what one command refuses."""
        self.seed(item(1, "um"))
        for argv in (("edit", "T001", "--deferred", "afk"),
                     ("edit", "T001", "--class", "AUTONOMOUS", "--deferred", "afk")):
            with self.subTest(argv=" ".join(argv)):
                r = self.run_tk(*argv)
                self.assertEqual(r.returncode, 1, r.stdout)
                self.assertIn("--deferred", r.stderr)
                self.assertNotIn("**Deferred:**", self.body())

    def test_prose_that_looks_like_a_deferral_never_satisfies_the_gate(self):
        """`field_chain` absorbs any run of `**Field:** value.` segments that ends
        the line, so an item's own prose can OPEN that run and be read as fields.
        Trusting it let `edit --class DECISION` through with no justification at
        all, and the later clear DELETED the prose it had misread."""
        legacy = ("- [ ] **T001** — item, ver a **Deferred:** nota de contexto. "
                  "**Class:** AUTONOMOUS. **Effort:** S. **Criterion:** A: x. "
                  "**Source:** 2026-08-13\n")
        self.seed(legacy)
        r = self.run_tk("edit", "T001", "--class", "DECISION")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertEqual(self.body(), HEADER + legacy)                # class and prose intact
        # and the same marker cannot be deleted by clearing it either
        r = self.run_tk("edit", "T001", "--class", "BLOCKED", "--deferred", "none")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertEqual(self.body(), HEADER + legacy)
        # WHICH guard answers, and not merely that one did. Since T121 the field
        # locator refuses this shape too, so the outcome alone no longer proves the
        # deferral's own gate ran: it is the one that names the deferral's POSITION,
        # and it runs FIRST precisely so the caller reads that diagnosis and not the
        # generic one. Without this line the stray guard could be deleted whole and
        # every assertion above would still pass.
        self.assertIn("away from the position a deferral is written in", r.stderr)

    def test_an_edit_that_never_consults_the_deferral_stays_allowed(self):
        """The over-refusal direction: refusing that item outright would make it
        uneditable, which is worse than the shape it protects against."""
        legacy = ("- [ ] **T001** — item, ver a **Deferred:** nota de contexto. "
                  "**Class:** AUTONOMOUS. **Effort:** S. **Criterion:** A: x. "
                  "**Source:** 2026-08-13\n")
        self.seed(legacy)
        r = self.run_tk("edit", "T001", "--effort", "L")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("**Effort:** L.", self.body())
        self.assertIn("nota de contexto", self.body())

    def test_the_justification_goes_through_the_free_text_guards_on_add(self):
        """--deferred is prose, so it answers to the same guards as the other
        free-text flags. Wired but unproven is not wired: each of these was a
        surviving mutation until it had a case of its own."""
        for value, expected in (("linha um\nlinha dois", "single-line"),
                                ("motivo **Project:** falso", "field-marker shape")):
            with self.subTest(value=value):
                self.seed()
                r = self.run_tk(*self.ADD, "--class", "DECISION", "--deferred", value)
                self.assertEqual(r.returncode, 1, r.stdout)
                self.assertIn(expected, r.stderr)
                self.assertNotIn("- [ ]", self.body())

    def test_the_justification_goes_through_the_free_text_guards_on_edit(self):
        for value, expected in (("", "cannot be blank"), ("   ", "cannot be blank"),
                                ("linha um\nlinha dois", "single-line"),
                                ("motivo **Project:** falso", "field-marker shape")):
            with self.subTest(value=repr(value)):
                self.seed(item(1, "um"))
                r = self.run_tk("edit", "T001", "--class", "DECISION", "--deferred", value)
                self.assertEqual(r.returncode, 1, r.stdout)
                self.assertIn(expected, r.stderr)
                self.assertIn("**Class:** AUTONOMOUS.", self.body())

    def test_a_class_named_only_in_prose_does_not_open_the_gate(self):
        """The gate reads the class from the FIELD CHAIN, not from the whole block
        the way `list` displays it. An item whose prose names DECISION before its
        real `**Class:** AUTONOMOUS.` took a deferral with no --class at all."""
        legacy = ("- [ ] **T001** — nota: itens **Class:** DECISION sao raros aqui. "
                  "**Class:** AUTONOMOUS. **Effort:** S. **Criterion:** A: x. "
                  "**Source:** 2026-08-13\n")
        self.seed(legacy)
        r = self.run_tk("edit", "T001", "--deferred", "tentando sem --class")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertNotIn("**Deferred:**", self.body())

    def test_a_chain_with_no_class_carries_no_deferral_to_find(self):
        """A deferral qualifies the class it follows, so a chain with no class at
        all has no deferral to offer the gate — whatever the marker looks like."""
        self.seed("- [ ] **T001** — item legado. **Deferred:** afk. **Effort:** S. "
                  "**Criterion:** A: x. **Source:** 2026-08-13\n")
        r = self.run_tk("edit", "T001", "--class", "DECISION")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertNotIn("**Class:** DECISION.", self.body())

    def test_the_stray_refusal_fires_for_a_bare_deferred_too(self):
        """Both arms: the outcome depends on the deferral whenever --class OR
        --deferred is passed, and the refusal has to say which problem it is."""
        legacy = ("- [ ] **T001** — item, ver a **Deferred:** nota de contexto. "
                  "**Class:** AUTONOMOUS. **Effort:** S. **Criterion:** A: x. "
                  "**Source:** 2026-08-13\n")
        self.seed(legacy)
        r = self.run_tk("edit", "T001", "--deferred", "afk")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("away from the position", r.stderr)
        self.assertIn("nota de contexto", self.body())

    def test_a_typo_in_the_class_is_answered_before_the_gate(self):
        """A gate reasoning about the RESULTING class answers a typo'd class with
        "T001 is DECISON — pass --class DECISION", which sends the caller after
        the wrong mistake. The class is validated first, as `add` does."""
        self.seed(item(1, "um"))
        r = self.run_tk("edit", "T001", "--class", "DECISON", "--deferred", "afk")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("must be one of", r.stderr)
        self.assertIn("**Class:** AUTONOMOUS.", self.body())

    def test_the_justification_is_measured_against_the_field_ceiling(self):
        tk = load_tk()
        big = "x" * (tk.FIELD_CEILING + 1)
        self.seed(item(1, "um"))
        r = self.run_tk(*self.ADD, "--class", "DECISION", "--deferred", big)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("field ceiling", r.stderr)
        r = self.run_tk("edit", "T001", "--class", "DECISION", "--deferred", big)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("field ceiling", r.stderr)
        self.assertIn("**Class:** AUTONOMOUS.", self.body())


# --- T119: priority is the file's global order, and `bump` is how it moves ---

class TestBump(QueueTest):
    """Priority is the order of the file — no hidden heuristic — and `bump` is
    the one way to change it: the afk package takes the filtered top."""

    def ids(self):
        return [ln.split()[0] for ln in self.run_tk("list").stdout.splitlines()
                if ln.startswith("T")]

    def test_bump_moves_the_item_to_the_top_and_list_follows(self):
        self.seed(item(1, "um"), item(2, "dois"), item(3, "tres"))
        r = self.run_tk("bump", "T003")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.ids(), ["T003", "T001", "T002"])
        # and the file itself, which is the order `pack` reads
        self.assertLess(self.body().index("**T003**"), self.body().index("**T001**"))

    def test_the_other_items_keep_their_relative_order(self):
        self.seed(item(1, "um"), item(2, "dois"), item(3, "tres"), item(4, "quatro"))
        self.assertEqual(self.run_tk("bump", "T003").returncode, 0)
        self.assertEqual(self.ids(), ["T003", "T001", "T002", "T004"])

    def test_bumping_the_top_item_leaves_the_file_byte_identical(self):
        self.seed(item(1, "um"), item(2, "dois"))
        before = self.body()
        r = self.run_tk("bump", "T001")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.body(), before)
        self.assertIn("already at the top", r.stdout)

    def test_the_whole_file_comes_out_exactly_as_the_move_implies(self):
        """Items sit under `##` project headings in a real queue, with prose
        paragraphs between them, and blank lines separating the items. `bump`
        moves ONE block: it lands above the first ITEM (not above the file's
        frontmatter), it keeps the blank line that separates it from the item it
        now precedes, and every heading, paragraph and blank line elsewhere is
        left where it was. Asserted as the whole file, because each of those is a
        way the move can go subtly wrong while every "is it still there?" check
        passes."""
        prose = "Um parágrafo de contexto que ninguém pediu para mexer.\n"
        self.write("next-steps.md",
                   HEADER + "## projeto a\n\n" + item(1, "um")
                   + "\n" + prose + "\n## projeto b\n\n" + item(2, "dois"))
        self.assertEqual(self.run_tk("bump", "T002").returncode, 0)
        self.assertEqual(
            self.body(),
            HEADER + "## projeto a\n\n" + item(2, "dois") + "\n" + item(1, "um")
            + "\n" + prose + "\n## projeto b\n")

    def test_the_item_is_moved_whole_and_not_duplicated(self):
        self.seed(item(1, "um"), item(2, "dois", project="tk"))
        self.assertEqual(self.run_tk("bump", "T002").returncode, 0)
        body = self.body()
        self.assertEqual(body.count("**T002**"), 1)
        self.assertIn("**Project:** tk.", body)
        self.assertEqual(len([l for l in body.splitlines() if l.startswith("- [ ]")]), 2)

    def test_a_bump_shows_in_list_on_a_tagged_queue_too(self):
        """`list` groups by the **Project:** tag, and a queue that mixes projects
        is the shape those tags exist for. Ordering the groups alphabetically
        made `bump` INVISIBLE there: the item reached the top of the file and
        still rendered under a later heading, which reads as a bump that failed.
        The groups follow the file, so the bumped item is the first line."""
        self.seed(item(1, "um", project="a"), item(2, "dois", project="a"),
                  item(3, "tres", project="b"))
        self.assertEqual(self.run_tk("bump", "T003").returncode, 0)
        out = self.run_tk("list").stdout
        self.assertEqual(self.ids(), ["T003", "T001", "T002"])
        self.assertLess(out.index("## b"), out.index("## a"))

    def test_an_unknown_id_is_diagnosed_and_nothing_moves(self):
        self.seed(item(1, "um"), item(2, "dois"))
        before = self.body()
        r = self.run_tk("bump", "T009")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("never allocated", r.stderr)
        self.assertEqual(self.body(), before)


# --- 2nd pair of eyes: an item's TEXT is not its ADDRESS -------------------

class TestClearingKeepsTheFileIntact(QueueTest):
    """Clearing a field is the one edit that computes a position INSIDE the block,
    and the item is written back at its position in the FILE. Binding both to the
    same name spliced a block offset into a file offset: the frontmatter came out
    truncated mid-word and the item duplicated, on `edit --risk none`.

    The whole suite stayed green through it, because every clearing test asked
    `assertNotIn("**Risk:**", body)` — a question a corrupted file answers the
    same way. These assert the FILE."""

    def test_clearing_a_risk_rewrites_only_that_field(self):
        risky = item(19, "re-triar", risk="dano X")
        other = item(20, "outro item")
        self.seed(risky, other)
        r = self.run_tk("edit", "T019", "--risk", "none")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.body(), HEADER + item(19, "re-triar") + other)

    def test_clearing_a_deferral_rewrites_only_that_field(self):
        deferred = decision_item(1, "decidir")
        other = item(2, "outro item")
        self.seed(deferred, other)
        r = self.run_tk("edit", "T001", "--class", "AUTONOMOUS")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.body(), HEADER + item(1, "decidir") + other)


# --- 2nd pair of eyes: an item's TEXT is not its ADDRESS -------------------

class TestBlockAddressing(QueueTest):
    """A queue about the queue quotes item lines verbatim in its notes, so an
    item's block text really does occur twice in the same file. Locating it with
    `content.index(block)` found the QUOTED copy first: `done` deleted that copy
    and left the real item open while reporting it closed, `bump` spliced a
    phantom duplicate at the top, and `edit` rewrote the quotation. Measured on
    this script — the `done` half predates `bump` and was reachable all along."""

    def seed_quoted(self):
        """T001 quotes T002's line verbatim in a continuation note (indented, so
        it is part of T001's block), and the real T002 follows."""
        quoted = item(2, "corrigir o bug")
        self.seed("- [ ] **T001** — documentar o formato do item, exemplo abaixo.\n  "
                  + quoted + "\n", quoted)
        return quoted

    def test_done_closes_the_real_item_and_spares_the_quoted_copy(self):
        quoted = self.seed_quoted()
        r = self.run_tk("done", "T002", "--how", "PR #1")
        self.assertEqual(r.returncode, 0, r.stderr)
        body = self.body()
        self.assertEqual(body.count("**T002**"), 1)          # only the quotation left
        self.assertIn("  " + quoted, body)                   # and it is intact
        self.assertIn("T002", self.body("done-log.md"))

    def test_bump_moves_the_real_item_and_leaves_no_phantom(self):
        quoted = self.seed_quoted()
        r = self.run_tk("bump", "T002")
        self.assertEqual(r.returncode, 0, r.stderr)
        body = self.body()
        self.assertEqual(body.count("**T002**"), 2)          # the real one + the quotation
        self.assertIn("  " + quoted, body)
        self.assertLess(body.index("**T002**"), body.index("**T001**"))
        self.assertEqual(len([l for l in body.splitlines() if l.startswith("- [ ]")]), 2)

    def test_edit_rewrites_the_real_item_and_not_the_quotation(self):
        self.seed_quoted()
        r = self.run_tk("edit", "T002", "--effort", "L")
        self.assertEqual(r.returncode, 0, r.stderr)
        body = self.body()
        self.assertEqual(body.count("**Effort:** L."), 1)
        for line in body.splitlines():
            if line.startswith("  - [ ]"):                   # the quotation
                self.assertIn("**Effort:** S.", line)


# --- T120: an item may name WHERE it runs, and the roster says what exists ---

# The roster used by these fixtures is deliberately made up: the plugin is
# public and ships no machine of ours. `alpha` is the machine running the suite.
SITE = """# fixture site file
identity = alpha
environments = alpha, bravo, charlie-2
max-local-subagents = 3
max-cloud-subagents = 4
"""


class TestEnvField(QueueTest):
    """`**Env:**` says where an item can run — orthogonal to the class, which
    says what it is waiting for. Absent means "the machine that owns this
    queue", so the field appears only in the exception, like Risk.

    The value is validated against the site file's roster by EXACT equality:
    an unvalidated environment name is a phantom one — an item that no machine
    ever picks up, and no error anywhere to say why.
    """

    ADD = ("add", "rodar a coleta", "--class", "AUTONOMOUS", "--effort", "S",
           "--criterion", "A: x")

    def setUp(self):
        super().setUp()
        # an EMPTY queue file, always — without it `add` fails with "next-steps.md
        # not found", which is also exit 1, and every refusal test in this class
        # would pass without the guard it names ever running
        self.seed()

    def test_add_writes_the_field_where_the_readers_look_for_it(self):
        """The composed order is the format four sibling readers parse, so it is
        asserted with the neighbouring gate field PRESENT — with `--risk`
        omitted, Risk and Env could swap places and every assertion still held."""
        self.site(SITE)
        r = self.run_tk(*self.ADD, "--risk", "apaga dado", "--env", "bravo")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("**Class:** AUTONOMOUS. **Effort:** S. **Risk:** apaga dado. "
                      "**Env:** bravo. **Criterion:** A: x.", self.body())

    def test_edit_sets_the_field_and_then_REPLACES_it(self):
        """A second `--env` must rewrite the field, not append a second one: two
        **Env:** fields in one chain is the ambiguity `edit` refuses forever
        after, and the item becomes uneditable."""
        self.site(SITE)
        self.seed(item(1, "um"))
        self.assertEqual(self.run_tk("edit", "T001", "--env", "bravo").returncode, 0)
        r = self.run_tk("edit", "T001", "--env", "charlie-2")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.body().count("**Env:**"), 1)
        self.assertIn("**Env:** charlie-2.", self.body())

    def test_add_refuses_a_value_outside_the_roster(self):
        """Refused, not warned: the whole point of the roster is that a typo
        cannot create an environment."""
        self.site(SITE)
        r = self.run_tk(*self.ADD, "--env", "delta")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("delta", r.stderr)
        self.assertIn("alpha, bravo, charlie-2", r.stderr)   # what IS valid
        self.assertNotIn("- [ ]", self.body())               # nothing written

    def test_edit_refuses_it_too(self):
        """`add` clean + `edit --env delta` is the two-command route to the same
        phantom, and it is the one a re-triage takes."""
        self.site(SITE)
        self.seed(item(1, "um"))
        r = self.run_tk("edit", "T001", "--env", "delta")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("delta", r.stderr)
        self.assertNotIn("**Env:**", self.body())

    def test_a_case_difference_is_a_different_name(self):
        self.site(SITE)
        r = self.run_tk(*self.ADD, "--env", "Bravo")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("roster", r.stderr)
        self.assertNotIn("- [ ]", self.body())

    def test_a_prefix_of_a_roster_name_is_not_that_name(self):
        self.site(SITE)
        r = self.run_tk(*self.ADD, "--env", "brav")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("roster", r.stderr)
        self.assertNotIn("- [ ]", self.body())

    def test_no_site_file_refuses_the_flag_and_says_what_to_create(self):
        """The message has to carry the format: this file is written by hand,
        once, and "not found" alone sends the reader hunting for its shape."""
        r = self.run_tk(*self.ADD, "--env", "bravo")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn(os.path.join(".claude", "tk", "env"), r.stderr)
        self.assertIn("identity", r.stderr)
        self.assertIn("environments", r.stderr)
        self.assertNotIn("- [ ]", self.body())

    def test_a_mistyped_roster_key_is_refused_and_the_keys_present_are_listed(self):
        """Unknown keys are ignored, so a MISTYPED key looks exactly like an
        absent one — listing the keys present puts the typo in the message."""
        self.site("identity = alpha\nenviroments = alpha, bravo\n")
        r = self.run_tk(*self.ADD, "--env", "bravo")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("environments", r.stderr)
        self.assertIn("enviroments", r.stderr)
        self.assertNotIn("- [ ]", self.body())

    def test_an_empty_roster_is_refused_like_an_absent_one(self):
        """It validates nothing, so it gets the same answer — one message, not a
        second and subtler failure mode. The assertion names THIS message, not
        merely the word 'environments': with the guard off the identity check
        fires instead, and its wording carries that word too — the test passed
        on the wrong error (measured by mutation)."""
        self.site("identity = alpha\nenvironments =\n")
        r = self.run_tk(*self.ADD, "--env", "bravo")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("`environments` is empty", r.stderr)
        self.assertNotIn("- [ ]", self.body())

    def test_an_absent_identity_is_refused(self):
        """`assertNotIn("Traceback")` is doing real work here: with the required-key
        check off, the reader dies on a KeyError whose text ALSO says 'identity'
        — the test passed on the crash and proved nothing (measured by mutation).
        A defect in a hand-written file has to come back as a diagnosis."""
        self.site("environments = alpha, bravo\n")
        r = self.run_tk(*self.ADD, "--env", "bravo")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertNotIn("Traceback", r.stderr)
        self.assertIn("declares no", r.stderr)
        self.assertIn("identity", r.stderr)

    def test_an_identity_outside_its_own_roster_is_refused(self):
        """A machine absent from its own roster is one where nothing is local:
        every item would read as another machine's, and the package would come
        back empty with no error to explain it."""
        self.site("identity = zulu\nenvironments = alpha, bravo\n")
        r = self.run_tk(*self.ADD, "--env", "bravo")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("zulu", r.stderr)
        self.assertNotIn("- [ ]", self.body())

    def test_a_malformed_roster_entry_is_refused(self):
        for bad in ("Bravo", "two words", "bravo.local", "-bravo", "b" * 33):
            with self.subTest(bad=bad):
                self.site(f"identity = alpha\nenvironments = alpha, {bad}\n")
                r = self.run_tk(*self.ADD, "--env", "alpha")
                self.assertEqual(r.returncode, 1, r.stdout)
                self.assertIn("environment name", r.stderr)
                self.assertNotIn("- [ ]", self.body())

    def test_the_reserved_clear_word_cannot_be_an_environment(self):
        """`none` DELETES a field everywhere in this script. A roster carrying it
        could write an Env into an item that no command could ever remove."""
        self.site("identity = alpha\nenvironments = alpha, none\n")
        r = self.run_tk(*self.ADD, "--env", "alpha")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("none", r.stderr)
        self.assertNotIn("- [ ]", self.body())

    def test_a_file_that_cannot_be_READ_is_reported_and_not_crashed(self):
        """The defect does not have to be in the file's TEXT. A site file that is
        a directory, or one carrying a byte that is not UTF-8, never reaches the
        parser at all — and an unguarded `open()` answers a hand-written-file
        mistake with a Python traceback, which names a line of OUR code and not
        the line of THEIR file that has to change."""
        d = os.path.join(self.home, ".claude", "tk")
        os.makedirs(d, exist_ok=True)
        def raw(payload):
            """A `with`, not a bare `open().write()`: the discarded handle made
            the whole suite print a ResourceWarning from this line."""
            with open(os.path.join(d, "env"), "wb") as f:
                f.write(payload)

        cases = {"a directory": lambda: os.mkdir(os.path.join(d, "env")),
                 "a non-UTF-8 byte": lambda: raw(
                     b"identity = alpha\nenvironments = alpha, bravo\n# caf\xe9\n")}
        for label, make in cases.items():
            with self.subTest(case=label):
                path = os.path.join(d, "env")
                if os.path.isdir(path):
                    os.rmdir(path)
                elif os.path.exists(path):
                    os.remove(path)
                make()
                r = self.run_tk(*self.ADD, "--env", "bravo")
                self.assertEqual(r.returncode, 1, r.stdout)
                # the ONLY assertion here that separates a diagnosis from a crash —
                # measured: on a raw traceback the other two pass anyway, one on the
                # `tk-queue: queue: …` line printed before the crash, the other on the
                # path embedded in the traceback itself. They check the message's
                # CONTENT and are not redundant, but neither can stand in for this one
                self.assertNotIn("Traceback", r.stderr)
                self.assertIn("tk-queue:", r.stderr)      # our diagnosis, not the interpreter's
                self.assertIn("env", r.stderr)            # and it names the file
                self.assertNotIn("- [ ]", self.body())

    def test_a_byte_order_mark_does_not_swallow_a_key(self):
        """An editor that writes a BOM glues it to the following key, and that
        key then reads as ABSENT while sitting in plain view — a diagnosis that
        sends the reader hunting a line that is already correct.

        Three placements, because `utf-8-sig` would only answer the first: one
        BOM at the head of the file, TWO (a file saved twice, or two files
        concatenated), and one at the head of a later line."""
        for label, text in (
                ("leading", "﻿identity = alpha\nenvironments = alpha, bravo\n"),
                ("doubled", "﻿﻿identity = alpha\nenvironments = alpha, bravo\n"),
                ("mid-file", "identity = alpha\n﻿environments = alpha, bravo\n")):
            with self.subTest(placement=label):
                self.seed()
                self.site(text)
                r = self.run_tk(*self.ADD, "--env", "bravo")
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertIn("**Env:** bravo.", self.body())

    def test_a_site_file_that_is_not_a_plain_file_is_refused_and_never_HANGS(self):
        """`open()` on a FIFO with no writer does not raise — it blocks, and the
        session stops with no output at all. A hang is worse than the traceback
        the read guards replace: nothing on screen names the cause."""
        d = os.path.join(self.home, ".claude", "tk")
        os.makedirs(d, exist_ok=True)
        os.mkfifo(os.path.join(d, "env"))
        try:
            r = self.run_tk(*self.ADD, "--env", "bravo", timeout=20)
        except subprocess.TimeoutExpired:
            self.fail("tk-queue hung reading a FIFO site file instead of refusing it")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertNotIn("Traceback", r.stderr)
        self.assertIn("not a plain file", r.stderr)
        self.assertNotIn("- [ ]", self.body())

    def test_a_duplicate_key_is_refused(self):
        """Last-wins is how a line the user believes they replaced keeps
        deciding where their work runs."""
        self.site("identity = alpha\nidentity = bravo\nenvironments = alpha, bravo\n")
        r = self.run_tk(*self.ADD, "--env", "bravo")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("duplicate", r.stderr)

    def test_a_line_that_is_not_key_value_is_refused_with_its_number(self):
        self.site("identity = alpha\nenvironments = alpha, bravo\nlixo\n")
        r = self.run_tk(*self.ADD, "--env", "bravo")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn(":3:", r.stderr)          # the line, not just the file

    def test_a_ceiling_that_is_not_a_number_is_refused(self):
        self.site(SITE.replace("max-local-subagents = 3", "max-local-subagents = três"))
        r = self.run_tk(*self.ADD, "--env", "bravo")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("max-local-subagents", r.stderr)

    def test_a_ceiling_of_zero_is_refused(self):
        """Zero is a number and it is not a ceiling: it lets nothing run, which
        reads as "the fleet is idle" rather than as a misconfigured file."""
        self.site(SITE.replace("max-cloud-subagents = 4", "max-cloud-subagents = 0"))
        r = self.run_tk(*self.ADD, "--env", "bravo")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("max-cloud-subagents", r.stderr)

    def test_comments_blank_lines_and_unknown_keys_are_tolerated(self):
        """The over-refusal direction. Unknown keys are what lets a later reader
        add its own without an older tk refusing the file — a suite that only
        proves refusals would let that tolerance be lost silently."""
        self.site("# comment\n\nidentity = alpha   # trailing comment\n"
                  "environments = alpha, bravo\nfleet-deny = something\n")
        r = self.run_tk(*self.ADD, "--env", "bravo")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("**Env:** bravo.", self.body())

    def test_the_ceilings_are_optional(self):
        self.site("identity = alpha\nenvironments = alpha, bravo\n")
        r = self.run_tk(*self.ADD, "--env", "bravo")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_the_reserved_word_clears_the_field_and_leaves_the_file_intact(self):
        """The whole file is asserted, not `assertNotIn("**Env:**")`: a clearing
        branch that corrupted the frontmatter and duplicated the item satisfied
        an assertNotIn once, with the suite still green (see
        TestClearingKeepsTheFileIntact)."""
        self.site(SITE)
        before = HEADER + item(1, "um") + item(2, "dois")
        with_env = before.replace("**Effort:** S. **Criterion:** A: x.",
                                  "**Effort:** S. **Env:** bravo. **Criterion:** A: x.", 1)
        self.write("next-steps.md", with_env)
        r = self.run_tk("edit", "T001", "--env", "none")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.body(), before)

    def test_clearing_needs_no_site_file_at_all(self):
        """Deleting a field names no environment, so it consults no roster — and
        a machine with no site file must still be able to un-pin an item."""
        before = HEADER + item(1, "um")
        with_env = before.replace("**Effort:** S.", "**Effort:** S. **Env:** bravo.", 1)
        self.write("next-steps.md", with_env)
        r = self.run_tk("edit", "T001", "--env", "none")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.body(), before)

    def test_add_writes_no_field_for_the_reserved_word(self):
        r = self.run_tk(*self.ADD, "--env", "none")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("**Env:**", self.body())

    def test_the_field_is_read_from_the_chain_never_from_prose(self):
        """Registering Env as a real field is what makes the existing chain
        reader cover it: the edit lands on the item's REAL Env and spares prose
        that merely carries the marker."""
        self.site(SITE)
        legacy = ("- [ ] **T001** — levar o campo **Env:** para o pacote "
                  "**Class:** AUTONOMOUS. **Effort:** S. **Env:** bravo. "
                  "**Criterion:** A: x. **Source:** 2026-08-13\n")
        self.seed(legacy)
        r = self.run_tk("edit", "T001", "--env", "charlie-2")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("levar o campo **Env:** para o pacote", self.body())
        self.assertIn("**Env:** charlie-2.", self.body())
        self.assertNotIn("**Env:** bravo.", self.body())
        # and the DELETION path, where guessing wrong destroys text: the whole
        # file is asserted, since assertNotIn passes on a corrupted one too
        r = self.run_tk("edit", "T001", "--env", "none")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.body(),
                         HEADER + legacy.replace(" **Env:** bravo.", "", 1))

    def test_a_marker_only_outside_the_chain_is_refused_not_guessed(self):
        """The item carries the marker on a continuation line and no real Env:
        rewriting it would edit prose nobody pointed at, and `none` would DELETE
        it. The refusal is the existing guard — it covers Env only because Env
        is a field the readers know."""
        self.site(SITE)
        self.seed(item(1, "um").rstrip("\n") + "\n  nota: **Env:** decidir depois\n")
        before = self.body()
        for value in ("bravo", "none"):
            with self.subTest(value=value):
                r = self.run_tk("edit", "T001", "--env", value)
                self.assertEqual(r.returncode, 1, r.stdout)
                self.assertEqual(self.body(), before)       # the prose survives whole

    def test_tagging_a_legacy_oversized_item_needs_no_force(self):
        """Env is bounded by the roster, so it answers to the same rule as the
        other short fields: an item already over the block ceiling — the exact
        population that has to stay taggable — gains one without --force."""
        self.site(SITE)
        self.seed(item(1, "x" * 800))
        self.assertGreater(len(self.body()), load_tk().CEILING)
        r = self.run_tk("edit", "T001", "--env", "bravo")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("**Env:** bravo.", self.body())


# --- T121: who is working on the item, so a sibling session does not too ---

CLAIMED = "**Claimed:** alpha since 2026-08-19T10:00:00Z."
STAMP_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z")


class TestClaim(QueueTest):
    """`claim` marks an item as taken, under the exclusive lock the queue already
    has, so two sibling sessions on one queue stop executing the same item —
    collisions measured 2026-08-18.

    The mark is a field like any other (**Claimed:**), which is what gives it the
    chain reader, the embedded-marker guard and the ambiguity refusal for free. It
    is NOT an `edit` flag: a flag that can set it takes a held item in a second
    command, which is what `claim` refuses in one.
    """

    def item_line(self, prefix="- [ ]"):
        """The item's first line — located, never counted: the frontmatter's height
        is not this test's business, and an index makes the assertion pass on the
        wrong line the day HEADER gains one."""
        return next(ln for ln in self.body().splitlines() if ln.startswith(prefix))

    def stamp_of(self, stdout):
        m = STAMP_RE.search(stdout)
        self.assertIsNotNone(m, f"no timestamp in {stdout!r}")
        return m.group(0)

    # --- the mark itself -------------------------------------------------
    def test_claim_writes_the_field_where_the_readers_look_for_it(self):
        """At the END of the first line, after the last field — the one place
        field_chain reads a field back from."""
        self.seed(item(1, "um"))
        r = self.run_tk("claim", "T001", "--as", "alpha")
        self.assertEqual(r.returncode, 0, r.stderr)
        stamp = self.stamp_of(r.stdout)
        self.assertIn(f"**Source:** 2026-08-13 **Claimed:** alpha since {stamp}.\n",
                      self.body())

    def test_the_moment_is_recorded_to_the_second_and_in_UTC(self):
        """A date is not enough: two sessions collide within minutes, which is the
        only interval this field is ever read over — and the queue is shared by
        more than one machine, so two local times do not compare."""
        self.seed(item(1, "um"))
        r = self.run_tk("claim", "T001", "--as", "alpha")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertRegex(self.body(), r"\*\*Claimed:\*\* alpha since "
                                      r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z\.")

    def test_the_claim_lands_in_the_chain_on_an_item_with_a_continuation_line(self):
        """Appending at the end of the BLOCK would put the field after the note,
        i.e. outside the chain — where the next `claim` cannot see it, and the item
        is claimed twice with nothing to say so."""
        self.seed(item(1, "um").rstrip("\n") + "\n  nota: contexto durável\n")
        r = self.run_tk("claim", "T001", "--as", "alpha")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("**Claimed:** alpha since", self.item_line())
        second = self.run_tk("claim", "T001", "--as", "bravo")
        self.assertEqual(second.returncode, 1, second.stdout)
        self.assertIn("already claimed by alpha", second.stderr)

    # --- exclusivity ------------------------------------------------------
    def test_a_second_claim_is_refused_naming_the_owner_and_the_moment(self):
        """`assertNotIn("Traceback")` is doing real work: with the guard off the
        item gains a SECOND **Claimed:** field, and the next read dies on the
        ambiguity refusal — whose text also names the item."""
        self.seed(item(1, "um"))
        first = self.run_tk("claim", "T001", "--as", "alpha")
        self.assertEqual(first.returncode, 0, first.stderr)
        stamp, before = self.stamp_of(first.stdout), self.body()
        r = self.run_tk("claim", "T001", "--as", "bravo")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertNotIn("Traceback", r.stderr)
        self.assertIn("already claimed by alpha", r.stderr)   # WHO
        self.assertIn(stamp, r.stderr)                        # and WHEN
        self.assertEqual(self.body(), before)                 # nothing was changed

    def test_the_same_owner_cannot_reclaim_it_either(self):
        """Letting it through would only refresh the timestamp — and the timestamp
        is how a reader tells a live claim from one a dead session left behind."""
        self.seed(item(1, "um"))
        self.assertEqual(self.run_tk("claim", "T001", "--as", "alpha").returncode, 0)
        before = self.body()
        r = self.run_tk("claim", "T001", "--as", "alpha")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("already claimed by alpha", r.stderr)
        self.assertEqual(self.body(), before)

    def test_two_writers_racing_for_one_item_and_exactly_one_wins(self):
        """The criterion's own scenario. It is timing-dependent by nature, so it is
        NOT named as any mutation's proof (the deterministic proofs are the second
        claim above and TestConcurrency's lock test) — but it is what says the
        guard and the lock hold together under real contention."""
        self.seed(item(1, "um"))
        n = 6
        with ThreadPoolExecutor(n) as ex:
            res = list(ex.map(lambda i: self.run_tk("claim", "T001", "--as", f"sess-{i}"),
                              range(n)))
        won = [r for r in res if r.returncode == 0]
        self.assertEqual(len(won), 1, "more than one session took the same item: "
                                      f"{[r.stdout.strip() for r in won]}")
        winner = won[0].stdout.split()[3]
        for r in res:
            self.assertNotIn("Traceback", r.stderr)
            if r.returncode != 0:
                self.assertIn(f"already claimed by {winner}", r.stderr)
        self.assertEqual(self.body().count("**Claimed:**"), 1)

    # --- release ----------------------------------------------------------
    def test_release_gives_the_item_back_and_leaves_the_file_INTACT(self):
        """The whole file is asserted, not `assertNotIn("**Claimed:**")`: a clearing
        branch that corrupted the frontmatter and duplicated the item satisfied an
        assertNotIn once, with the suite green (see TestClearingKeepsTheFileIntact).
        Claim is always the LAST field on its line, so it hits the dangling-blank
        repair every single time."""
        before = HEADER + item(1, "um") + item(2, "dois")
        self.write("next-steps.md", before)
        self.assertEqual(self.run_tk("claim", "T001", "--as", "alpha").returncode, 0)
        r = self.run_tk("release", "T001")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.body(), before)

    def test_release_names_the_claim_it_dropped(self):
        """`release` does not demand the owner's name — a session that died holding
        one would otherwise leave the item unreachable, a lock with no timeout. What
        keeps a wrongful release visible is this report."""
        self.seed(item(1, "um"))
        first = self.run_tk("claim", "T001", "--as", "alpha")
        r = self.run_tk("release", "T001")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("alpha", r.stdout)
        self.assertIn(self.stamp_of(first.stdout), r.stdout)

    def test_releasing_an_unclaimed_item_says_so_and_changes_nothing(self):
        """An honest no-op, like `bump` on an item already at the top: reporting a
        release that did not happen is what sends the caller on to work an item
        somebody else is still holding."""
        self.seed(item(1, "um"))
        before = self.body()
        r = self.run_tk("release", "T001")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("no claim", r.stdout)
        self.assertNotIn("released", r.stdout)
        self.assertEqual(self.body(), before)

    # --- the closes release implicitly ------------------------------------
    def test_done_takes_the_claim_with_the_item(self):
        """The mark is coordination between live sessions, not history: it must not
        reach the done-log, which is the record that outlives the item."""
        self.seed(item(1, "um"))
        self.assertEqual(self.run_tk("claim", "T001", "--as", "alpha").returncode, 0)
        r = self.run_tk("done", "T001", "--how", "PR #1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("**Claimed:**", self.body())
        self.assertNotIn("**Claimed:**", self.body("done-log.md"))
        self.assertNotIn("alpha", self.body("done-log.md"))
        self.assertIn("T001", self.body("done-log.md"))

    def test_cancel_takes_the_claim_with_the_item(self):
        self.seed(item(1, "um"))
        self.assertEqual(self.run_tk("claim", "T001", "--as", "alpha").returncode, 0)
        r = self.run_tk("cancel", "T001", "--why", "obsoleto")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("**Claimed:**", self.body())
        self.assertNotIn("**Claimed:**", self.body("done-log.md"))
        self.assertNotIn("alpha", self.body("done-log.md"))

    # --- `list` shows it --------------------------------------------------
    def test_list_marks_the_claimed_item_and_only_that_one(self):
        self.seed(item(1, "um"), item(2, "dois"))
        first = self.run_tk("claim", "T001", "--as", "alpha")
        r = self.run_tk("list")
        self.assertEqual(r.returncode, 0, r.stderr)
        um, dois = [ln for ln in r.stdout.splitlines() if ln.startswith("T")]
        self.assertIn("claimed by alpha", um)
        self.assertIn(self.stamp_of(first.stdout), um)
        self.assertNotIn("claimed", dois)

    # --- the owner is a bounded token -------------------------------------
    def test_an_empty_owner_is_refused(self):
        """argparse's required=True only proves --as was typed: an empty string
        satisfies it and would claim the item for nobody."""
        self.seed(item(1, "um"))
        r = self.run_tk("claim", "T001", "--as=")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertNotIn("**Claimed:**", self.body())

    def test_a_malformed_owner_is_refused(self):
        """A blank in the name makes owner and moment unreadable apart; the rest
        would break the block format outright."""
        for bad in ("duas palavras", "-alpha", "a" * 33, "alpha\nbravo", "**Class:**"):
            with self.subTest(bad=bad):
                self.seed(item(1, "um"))
                # `--as=<value>`, glued: a value starting with '-' is an OPTION to
                # argparse otherwise, and the subtest would prove argparse's parser
                # instead of this script's guard
                r = self.run_tk("claim", "T001", f"--as={bad}")
                self.assertEqual(r.returncode, 1, r.stdout)
                self.assertIn("owner name", r.stderr)
                self.assertNotIn("**Claimed:**", self.body())

    def test_the_reserved_clear_word_cannot_be_an_owner(self):
        """`none` DELETES a field everywhere in this script, so an item claimed
        under it reads as one nobody holds."""
        self.seed(item(1, "um"))
        r = self.run_tk("claim", "T001", "--as", "none")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("release", r.stderr)          # and it says how to hand one back
        self.assertNotIn("**Claimed:**", self.body())

    def test_an_ordinary_session_label_is_still_accepted(self):
        """The over-refusal direction: a gate that only ever refuses would make the
        command unusable, and the refusal tests above cannot see it."""
        for good in ("alpha", "alpha.local", "sess-3", "Sessao_2"):
            with self.subTest(good=good):
                self.seed(item(1, "um"))
                r = self.run_tk("claim", "T001", "--as", good)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertIn(f"**Claimed:** {good} since", self.body())

    # --- a claim that cannot be read is still a claim ---------------------
    def test_a_claim_that_does_not_parse_still_holds_the_item(self):
        """"Held, and I cannot tell by whom" is still held. Reading it as free is
        exactly how the second session takes an item the first is working — and the
        refusal quotes the raw value, which is all there is to report."""
        self.seed(item(1, "um").rstrip("\n") + " **Claimed:** lixo.\n")
        r = self.run_tk("claim", "T001", "--as", "alpha")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertNotIn("Traceback", r.stderr)
        self.assertIn("lixo", r.stderr)
        self.assertNotIn("alpha", self.body())

    def test_a_claim_that_does_not_parse_can_still_be_released(self):
        """The other half: a garbled value that could not be released would be an
        item locked forever, which is the failure the release command exists for."""
        before = HEADER + item(1, "um")
        self.write("next-steps.md", before.rstrip("\n") + " **Claimed:** lixo.\n")
        r = self.run_tk("release", "T001")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.body(), before)

    # --- ambiguity is refused, never guessed ------------------------------
    def test_two_claim_fields_in_the_chain_are_refused_as_ambiguous(self):
        """Which one holds the item is unanswerable, and picking either lets the
        other be silently overwritten."""
        two = ("- [ ] **T001** — um **Class:** AUTONOMOUS. **Effort:** S. "
               "**Criterion:** A: x. " + CLAIMED + " **Claimed:** bravo since "
               "2026-08-19T11:00:00Z.\n")
        self.seed(two)
        before = self.body()
        for argv in (("claim", "T001", "--as", "charlie"), ("release", "T001")):
            with self.subTest(cmd=argv[0]):
                r = self.run_tk(*argv)
                self.assertEqual(r.returncode, 1, r.stdout)
                self.assertIn("ambiguous", r.stderr)
                self.assertEqual(self.body(), before)

    def test_a_marker_only_outside_the_chain_is_refused_not_guessed(self):
        """The item carries the marker on a continuation line and no real claim:
        reading it as the field would let prose hold the item forever, and clearing
        it would DELETE that prose."""
        self.seed(item(1, "um").rstrip("\n") + "\n  nota: **Claimed:** ver depois\n")
        before = self.body()
        for argv in (("claim", "T001", "--as", "alpha"), ("release", "T001")):
            with self.subTest(cmd=argv[0]):
                r = self.run_tk(*argv)
                self.assertEqual(r.returncode, 1, r.stdout)
                self.assertEqual(self.body(), before)       # the prose survives whole

    def test_an_item_whose_chain_has_no_class_refuses_the_claim(self):
        """A claim is POSITIONED against **Class:**, so a chain carrying none cannot
        host one. Measured before this guard, on the legacy population `chain_class`
        already names (fields on a continuation line, or an item that never had a
        Class): `claim` returned 0 and wrote the field, `list` then showed the item
        FREE — the exact collision the command exists to prevent, now permanent —
        and `release` refused it forever, leaving the queue fixable only by the hand
        the contract forbids.

        A gate that cannot read back what it writes must refuse to write."""
        self.seed("- [ ] **T001** — algo. **Effort:** S. **Criterion:** A: x. "
                  "**Source:** 2026-08-13\n")
        before = self.body()
        r = self.run_tk("claim", "T001", "--as", "alpha")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertNotIn("Traceback", r.stderr)
        self.assertIn("**Class:**", r.stderr)
        self.assertIn("--class AUTONOMOUS", r.stderr)   # the remedy that works HERE
        self.assertEqual(self.body(), before)
        self.assertNotIn("claimed", self.run_tk("list").stdout)
        # the over-refusal direction: the way out is ONE command, and it works
        self.assertEqual(self.run_tk("edit", "T001", "--class", "AUTONOMOUS").returncode, 0)
        r = self.run_tk("claim", "T001", "--as", "alpha")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("claimed by alpha", self.run_tk("list").stdout)
        self.assertEqual(self.run_tk("release", "T001").returncode, 0)

    def test_an_item_whose_fields_sit_off_the_first_line_is_told_how_to_fold_them(self):
        """The remedy a refusal prints has to be one that WORKS. For this shape
        `edit --class` is itself refused (the marker-outside-the-chain guard), so
        naming it sends the caller to a second refusal — and this is not a rare
        shape: 31 of the 155 open items across the real queues carry it.

        It also predates this command — a continuation-line item already refused
        every per-field `edit` on `main`, measured — so the message says so and
        names the one command that lifts both at once."""
        self.seed("- [ ] **T001** — algo\n  **Class:** AUTONOMOUS. **Effort:** S. "
                  "**Criterion:** A: x. **Source:** 2026-08-13\n")
        before = self.body()
        r = self.run_tk("claim", "T001", "--as", "alpha")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertNotIn("Traceback", r.stderr)
        self.assertIn("--text", r.stderr)
        self.assertNotIn("--class AUTONOMOUS", r.stderr)   # the one that would refuse
        self.assertEqual(self.body(), before)
        # the same shape CARRYING a marker is answered by the stray guard instead —
        # one terminal refusal, never two in a row
        self.write("next-steps.md", before.replace("**Source:** 2026-08-13",
                                                   "**Source:** 2026-08-13 **Claimed:** x."))
        r = self.run_tk("release", "T001")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("cancel", r.stderr)
        # and the printed remedy really does make the item claimable
        self.write("next-steps.md", before)
        self.assertEqual(self.run_tk("edit", "T001", "--text", "algo").returncode, 0)
        r = self.run_tk("claim", "T001", "--as", "alpha")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_a_last_field_missing_its_period_refuses_the_claim_and_names_it(self):
        """The gate has to be asked of what would be WRITTEN, and three fixes in a row
        asked a proxy instead. field_chain gives its LAST segment a free pass on the
        period rule, so appending the claim MOVES that pass onto the claim — and the
        previous last field, if its value does not end in a period, then truncates the
        chain and drops **Class:** out of it. Class was in the chain before the write
        and gone after it, so every pre-write check passed.

        Measured on a real queue item carrying `**Esforço:** L,` (a typed comma): the
        item came back claimed in the FILE, shown FREE by `list` — the collision the
        command exists to prevent, made permanent — and unreleasable forever."""
        self.seed("- [ ] **T001** — algo **Class:** AUTONOMOUS. **Esforço:** L,\n")
        before = self.body()
        r = self.run_tk("claim", "T001", "--as", "alpha")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertNotIn("Traceback", r.stderr)
        self.assertIn("**Effort:**", r.stderr)      # WHICH field, not just that one is wrong
        self.assertIn("PERIOD", r.stderr)
        self.assertEqual(self.body(), before)
        self.assertNotIn("claimed", self.run_tk("list").stdout)
        # and the remedy it printed round-trips the item
        self.assertEqual(self.run_tk("edit", "T001", "--effort", "L").returncode, 0)
        self.assertEqual(self.run_tk("claim", "T001", "--as", "alpha").returncode, 0)
        self.assertIn("claimed by alpha", self.run_tk("list").stdout)
        self.assertEqual(self.run_tk("release", "T001").returncode, 0)

    def test_a_broken_chain_is_told_WHERE_it_stops_and_never_guesses_why(self):
        """The message names what it can prove — where the run of fields stops — and
        prescribes the one remedy that always works. It does NOT diagnose the cause or
        prescribe a per-field `edit`: three rewrites tried, and each was wrong for some
        shape. "Does not end in a PERIOD" was read onto a break that is a GAP of prose,
        and onto **Source:**, which is period-exempt by design; and the `edit --<field>`
        prescribed is itself refused when the field is duplicated in the chain, is a
        deferral on a non-DECISION item, or is an Env on a machine with no site file —
        besides repairing one broken field per run out of however many there are.

        The three shapes below break for three different reasons and every assertion
        here is true of all of them, which is the point."""
        cases = {
            "value with no period": "algo **Class:** AUTONOMOUS. **Esforço:** L,",
            "an earlier field broken": "algo **Class:** AUTONOMOUS, **Effort:** M.",
            "a gap of prose": "algo **Class:** A. *nota* **Effort:** M.",
        }
        for label, line in cases.items():
            with self.subTest(shape=label):
                self.seed(f"- [ ] **T001** — {line}\n")
                before = self.body()
                r = self.run_tk("claim", "T001", "--as", "alpha")
                self.assertEqual(r.returncode, 1, r.stdout)
                self.assertNotIn("Traceback", r.stderr)
                self.assertIn("stops at", r.stderr)              # WHERE, provably
                self.assertIn("cancel", r.stderr)                # the remedy that works
                self.assertNotIn("OUTSIDE the first line", r.stderr)   # they are ON it
                self.assertNotIn("--text", r.stderr)
                # no per-field edit is prescribed — each of these is refused for a
                # different reason on the very field at fault
                for flag in ("--class \"", "--effort \"", "--deferred \"", "--env \""):
                    self.assertNotIn(flag, r.stderr)
                self.assertEqual(self.body(), before)

    def test_the_refusal_names_where_the_chain_STOPS_not_where_it_starts(self):
        """The field it names has to be the one the run does not reach past — naming
        the run's own last segment names the claim itself, which tells the reader
        nothing about their item."""
        self.seed("- [ ] **T001** — algo **Class:** AUTONOMOUS. **Esforço:** L,\n")
        r = self.run_tk("claim", "T001", "--as", "alpha")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("stops at **Effort:**", r.stderr)
        self.assertNotIn("stops at **Claimed:**", r.stderr)

    def test_a_stray_marker_is_answered_BEFORE_the_missing_host(self):
        """Both are refusals; only the stray one is TERMINAL. Measured with the order
        the other way round: `claim` printed `edit --class AUTONOMOUS`, the caller ran
        it, the FILE WAS MUTATED — and the stray refusal landed anyway. A remedy that
        costs a write and fixes nothing is worse than the refusal it replaced."""
        self.seed("- [ ] **T001** — algo\n  nota: **Claimed:** ver depois\n")
        before = self.body()
        r = self.run_tk("claim", "T001", "--as", "alpha")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("cancel", r.stderr)                  # the terminal answer
        self.assertNotIn("--class AUTONOMOUS", r.stderr)   # not the one that mutates
        self.assertNotIn("--text", r.stderr)
        self.assertEqual(self.body(), before)

    def test_release_on_a_chainless_item_with_no_marker_is_still_an_honest_no_op(self):
        """The other side of that asymmetry: WRITING a claim needs a host, reading
        one does not. An item that simply holds no claim must not be answered with a
        diagnosis about its shape."""
        self.seed("- [ ] **T001** — algo\n  **Class:** AUTONOMOUS. **Effort:** S.\n")
        before = self.body()
        r = self.run_tk("release", "T001")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("no claim", r.stdout)
        self.assertEqual(self.body(), before)

    def test_list_never_shows_an_ambiguously_claimed_item_as_free(self):
        """Two owners on the record and both commands refusing: printing no mark
        would show the item FREE — to a reader, and to the afk package built from
        exactly this display. Tolerance is safe for a stray marker and dangerous
        here."""
        self.seed("- [ ] **T001** — um **Class:** AUTONOMOUS. **Effort:** S. "
                  "**Criterion:** A: x. " + CLAIMED + " **Claimed:** bravo since "
                  "2026-08-19T11:00:00Z.\n")
        out = self.run_tk("list").stdout
        self.assertIn("ambigu", out)
        self.assertEqual(self.run_tk("claim", "T001", "--as", "charlie").returncode, 1)

    def test_prose_ending_in_a_period_before_the_fields_is_not_a_claim(self):
        """The item's own text carries the marker, ends in a period and sits right
        against the fields — so field_chain absorbs it and the chain says the item
        is claimed. Measured on this very command before the position rule:
        `release` reported success and CUT four words out of the item's title, and
        `claim` refused the item naming an owner made of three words of it.

        A real claim is written AFTER the **Class:** compose_item writes first;
        anything before that is prose, whatever the chain says."""
        prose = ("- [ ] **T001** — ver a **Posse:** do item com alguém. "
                 "**Class:** AUTONOMOUS. **Effort:** S. **Criterion:** A: x. "
                 "**Source:** 2026-08-13\n")
        self.seed(prose)
        before = self.body()
        for argv in (("claim", "T001", "--as", "alpha"), ("release", "T001")):
            with self.subTest(cmd=argv[0]):
                r = self.run_tk(*argv)
                self.assertEqual(r.returncode, 1, r.stdout)
                self.assertNotIn("Traceback", r.stderr)
                self.assertEqual(self.body(), before)   # the title survives whole
        # and the display does not invent an owner out of those words either
        self.assertNotIn("claimed by", self.run_tk("list").stdout)

    def test_the_marker_shape_is_refused_in_free_text(self):
        """Registering Claimed in FIELD_VARIANTS is what puts it under the existing
        guard: an item whose TEXT carries the shape would hold itself forever."""
        for shape in ("**Claimed:**", "**Posse:**"):
            with self.subTest(shape=shape):
                self.seed()
                r = self.run_tk("add", f"levar o {shape} ao pacote", "--class",
                                "AUTONOMOUS", "--effort", "S", "--criterion", "A: x")
                self.assertEqual(r.returncode, 1, r.stdout)
                self.assertIn("field-marker shape", r.stderr)
                self.assertNotIn("- [ ]", self.body())

    # --- the mark is not an `edit` flag -----------------------------------
    def test_edit_cannot_set_a_claim(self):
        """The two-command bypass: a flag that can WRITE this field takes an item
        somebody else holds, which is what `claim` refuses in one command."""
        self.seed(item(1, "um"))
        self.assertEqual(self.run_tk("claim", "T001", "--as", "alpha").returncode, 0)
        before = self.body()
        r = self.run_tk("edit", "T001", "--claimed", "bravo")
        self.assertEqual(r.returncode, 2, r.stdout)      # argparse: no such flag
        self.assertEqual(self.body(), before)

    def test_the_claim_survives_an_unrelated_edit_and_is_still_readable(self):
        """An `edit` appends a field it did not find at the end of the first line —
        i.e. AFTER the claim — so the chain has to keep reading it there."""
        self.seed(item(1, "um"))
        self.assertEqual(self.run_tk("claim", "T001", "--as", "alpha").returncode, 0)
        self.assertEqual(self.run_tk("edit", "T001", "--effort", "L").returncode, 0)
        self.assertEqual(self.run_tk("edit", "T001", "--project", "tk").returncode, 0)
        r = self.run_tk("claim", "T001", "--as", "bravo")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("already claimed by alpha", r.stderr)
        # and releasing it from the MIDDLE of the chain leaves the rest whole
        self.assertEqual(self.run_tk("release", "T001").returncode, 0)
        self.assertNotIn("**Claimed:**", self.body())
        self.assertIn("**Effort:** L.", self.body())
        self.assertIn("**Project:** tk.", self.body())
        self.assertNotIn("  ", self.item_line())              # no dangling blank

    def test_claiming_a_legacy_oversized_item_needs_no_force(self):
        """The claim is bounded by construction (a 32-char owner plus a fixed-width
        stamp), so it answers to the short fields' rule (T071): an item already over
        the block ceiling is exactly the one a session must be able to take without
        being taught to type --force."""
        self.seed(item(1, "x" * 800))
        self.assertGreater(len(self.body()), load_tk().CEILING)
        r = self.run_tk("claim", "T001", "--as", "alpha")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("**Claimed:** alpha since", self.body())


# --- T126: pack — the eligibility filter the package was built BY EYE ------

def pack_item(iid, text, env=None, claimed=None, **kw):
    """An item as `add` and `claim` write one, with the two fields `item()` does
    not build. The POSITIONS are compose_item's, not a convenience: Env between
    Risk and Criterion, Claimed appended last. A fixture that put them elsewhere
    would prove the filter reads a shape the writer never produces."""
    line = item(iid, text, **kw)
    if env:
        line = line.replace("**Criterion:**", f"**Env:** {env}. **Criterion:**", 1)
    if claimed:
        line = line.rstrip("\n") + f" **Claimed:** {claimed}.\n"
    return line


LEGACY = ("- [ ] **T%03d** — algo\n"
          "  **Class:** AUTONOMOUS. **Effort:** S. **Criterion:** A: x. "
          "**Source:** 2026-08-13\n")


class PackOutput(QueueTest):
    """The pack output's parser, for every class that reads it. ONE copy: two
    tests stripping the same columns their own way is how one of them comes to
    assert a shape the command does not print — the answer this script's own
    FIELD_BODY_RE gives about its readers. Carries no test of its own."""

    # --- helpers ----------------------------------------------------------
    def pack(self):
        r = self.run_tk("pack")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("Traceback", r.stderr)
        return r.stdout

    def blocks(self, out):
        """The output's three named blocks, as lists of lines. Reading through this
        is what keeps a test about the FILTER from falling over a reworded heading
        — and what makes a filter change fall HERE rather than in a skill."""
        cur, res = None, {"eligible": [], "excluded": [], "repairs": []}
        for ln in out.splitlines():
            m = re.match(r"(eligible|excluded|repairs)[ :]", ln)
            if m:
                cur = m.group(1)
            elif ln.strip() and ln != "(none)":
                res[cur].append(ln)
        return res

    def labels(self, lines):
        return [ln.split()[0] for ln in lines]

    def eligible(self, out=None):
        return self.labels(self.blocks(out if out is not None else self.pack())["eligible"])

    def reason(self, out, label):
        for ln in self.blocks(out)["excluded"]:
            if ln.startswith(label + " "):
                return ln.split("  — ", 1)[1]
        self.fail(f"{label} is not in the excluded block:\n{out}")

    def repairs(self, out):
        return "\n".join(self.blocks(out)["repairs"])

    def lanes(self, out):
        """{label: lane} for the eligible block, read from the COLUMN — a test
        about the rule must not fall over the width of a title or an Effort."""
        res = {}
        for ln in self.blocks(out)["eligible"]:
            label, _effort, lane = re.split(r"\s{2,}", ln.strip())[:3]
            res[label] = lane
        return res

    def repos(self, out):
        """{label: repo} for the eligible items that carry one, read from the
        LABELLED group rather than from a position: the repo is appended after
        the ticket and either of the two may be absent, so a test counting
        bracket groups would assert the shape of the fixture and not the rule."""
        res = {}
        for ln in self.blocks(out)["eligible"]:
            m = re.search(r"\[repo: ([^\]]*)\]", ln)
            if m:
                res[ln.split()[0]] = m.group(1)
        return res


class TestPack(PackOutput):
    """The package an unattended session runs was filtered by eye until now, from
    `list` plus prose. Two things move when it becomes a command: the filter stops
    being re-derived every session, and — the reason the ticket exists — every
    exclusion becomes VISIBLE. An item dropped for its Risk or its Env leaves no
    trace anywhere else; silently absent, it is an item the user never learns
    about, on a queue they believe they have seen."""

    # --- the two lists ----------------------------------------------------
    def test_an_eligible_item_carries_its_id_effort_and_text(self):
        """Effort is in the package line because the caller sizes the package by it
        (3-6 items, ~2h) — raw, never summed: summing free text would put a hidden
        heuristic in a queue whose whole contract is that it has none."""
        self.seed(item(1, "um"))
        self.assertEqual(self.blocks(self.pack())["eligible"],
                         ["T001  S             avulso                um"])

    def test_the_eligible_follow_the_queues_own_order(self):
        """Priority IS the order of the file, global. Anything that sorted or
        grouped here would silently re-prioritise the package."""
        self.seed(item(3, "tres") + item(1, "um") + item(2, "dois"))
        self.assertEqual(self.eligible(), ["T003", "T001", "T002"])

    def test_bump_moves_an_item_to_the_top_of_the_package_too(self):
        """Through the command that DEFINES priority, not through a fixture: that
        is the only version of this test a re-ordering `pack` could not pass."""
        self.seed(item(1, "um") + item(2, "dois"))
        self.assertEqual(self.run_tk("bump", "T002").returncode, 0)
        self.assertEqual(self.eligible(), ["T002", "T001"])

    def test_the_package_is_not_grouped_by_project(self):
        """`list` groups by **Project:** and the package must not: grouping reorders,
        and the top of a grouped list is the top of one project, not of the queue."""
        self.seed(item(1, "um", project="alfa") + item(2, "dois", project="beta")
                  + item(3, "tres", project="alfa"))
        self.assertEqual(self.eligible(), ["T001", "T002", "T003"])

    def test_a_checked_item_is_not_a_candidate(self):
        self.seed(item(1, "um") + item(2, "dois").replace("- [ ]", "- [x]", 1))
        self.assertEqual(self.eligible(), ["T001"])

    def test_an_empty_queue_says_so_in_both_blocks(self):
        """The empty case is a SHAPE, not a blank: a skill's prose reading two
        headings and no marker cannot tell "nothing eligible" from "output cut"."""
        self.seed()
        out = self.pack()
        self.assertIn("eligible (0 of 0, in queue order):\n(none)", out)
        self.assertIn("excluded (0):\n(none)", out)

    def test_pack_writes_NOTHING(self):
        """The whole file, byte for byte. A reader that rewrote what it read is
        precisely the defect no assertion on its OUTPUT would ever show."""
        before = HEADER + item(1, "um") + item(2, "dois", klass="DECISION")
        self.write("next-steps.md", before)
        self.pack()
        self.assertEqual(self.body(), before)

    def test_the_output_format_is_documented_in_the_help(self):
        """The ticket's acceptance criterion: a skill's prose reads this output, so
        the shape it reads is written where the script itself carries it."""
        r = self.run_tk("pack", "--help")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(load_tk().PACK_SAMPLE, r.stdout)

    def test_the_documented_sample_IS_what_the_command_prints(self):
        """Character for character, against the queue the sample describes. A sample
        asserted only by substrings drifts from the code the moment a column or a
        quote changes — and drifting is exactly what a STABLE format may not do, in
        output whose consumer is a skill's prose rather than a person who would
        notice. Both halves of the AC are here: the shape is documented, and the
        documentation is executed."""
        self.seed(ticket_item(7, "the first ticket of the spec", spec="ambiente#171",
                              ticket="ambiente#172", effort="S (~20min)",
                              repo="https://github.com/owner/code.git")
                  + ticket_item(8, "the second one", spec="ambiente#171",
                                ticket="ambiente#173", effort="M (~1h)")
                  + ticket_item(9, "the item's text",
                                repo="/srv/projects/exemplo")
                  + ticket_item(10, "a lone ticket, under the floor", spec="ambiente#159")
                  + decision_item(12, "another item")
                  + ticket_item(21, "a ticket of a second spec", spec="ambiente#144")
                  + ticket_item(22, "and its sibling", spec="ambiente#144")
                  + "- [ ] **T031** — a legacy item **Effort:** S. **Criterion:** A: x. "
                    "**Source:** 2026-08-13\n")
        r = self.run_tk("pack")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, load_tk().PACK_SAMPLE)

    def test_the_CANCEL_repair_is_printed_and_the_command_ACCEPTS_it(self):
        """Run verbatim, as printed. `cancel` requires `--why`, so the line without it
        is refused by argparse — a remedy that cannot be run is a dead end dressed as
        an answer, and this was the one repair of the five that no test executed."""
        self.seed("- [ ] **T001** — um. **Class:** DECISION. **Class:** AUTONOMOUS. "
                  "**Effort:** S. **Criterion:** A: x. **Source:** 2026-08-13\n")
        printed = self.repairs(self.pack())
        self.assertIn("`tk-queue cancel <id> --why", printed)
        r = self.run_tk("cancel", "T001", "--why", "cadeia ilegível")
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        self.assertIn("excluded (0)", self.pack())

    # --- rule: the class, read from the CHAIN ------------------------------
    def test_every_class_but_AUTONOMOUS_is_excluded_by_name(self):
        for klass in ("DECISION", "BLOCKED", "EXTERNAL", "RECURRING"):
            with self.subTest(klass=klass):
                self.seed(decision_item(1, "um") if klass == "DECISION"
                          else item(1, "um", klass=klass))
                out = self.pack()
                self.assertEqual(self.blocks(out)["eligible"], [])
                self.assertEqual(self.reason(out, "T001"), f"class is {klass}")

    def test_a_class_QUOTED_IN_PROSE_does_not_decide_the_package(self):
        """The over-exclusion direction, and the one only a chain reader survives:
        the loose reader `list` uses takes the LEFTMOST marker in the block, so this
        item reads as DECISION to it and drops out of every package — while its real
        field, the one a writer wrote, says AUTONOMOUS."""
        self.seed("- [ ] **T001** — nota sobre **Class:** DECISION em prosa — um "
                  "**Class:** AUTONOMOUS. **Effort:** S. **Criterion:** A: x. "
                  "**Source:** 2026-08-13\n")
        self.assertEqual(self.eligible(), ["T001"])

    def test_two_classes_in_the_chain_are_ambiguous_not_guessed(self):
        self.seed("- [ ] **T001** — um. **Class:** DECISION. **Class:** AUTONOMOUS. "
                  "**Effort:** S. **Criterion:** A: x. **Source:** 2026-08-13\n")
        out = self.pack()
        self.assertEqual(self.reason(out, "T001"),
                         "2 **Class:** fields in the chain, so its value is ambiguous")

    def test_a_class_off_the_first_line_is_named_and_the_FOLD_repair_works(self):
        """The remedy is RUN and the command re-run. A refusal prescribing a command
        that is itself refused is a dead end; one prescribing a command that is
        accepted, rewrites the file and hands back the same refusal costs a write and
        repairs nothing. 31 of this machine's real open items carry this shape, and the fold lifts 29."""
        self.seed(LEGACY % 1)
        out = self.pack()
        self.assertEqual(self.reason(out, "T001"),
                         "**Class:** sits off the first line, where no gate reads it")
        self.assertIn("--text", self.repairs(out))
        self.assertEqual(self.run_tk("edit", "T001", "--text", "algo").returncode, 0)
        self.assertEqual(self.eligible(), ["T001"])

    def test_no_class_at_all_is_named_and_the_CLASS_repair_works(self):
        self.seed("- [ ] **T001** — algo **Effort:** S. **Criterion:** A: x. "
                  "**Source:** 2026-08-13\n")
        out = self.pack()
        self.assertEqual(self.reason(out, "T001"), "no **Class:** field")
        self.assertIn("--class AUTONOMOUS", self.repairs(out))
        self.assertEqual(self.run_tk("edit", "T001", "--class", "AUTONOMOUS").returncode, 0)
        self.assertEqual(self.eligible(), ["T001"])

    def test_a_chain_that_never_reaches_the_class_is_named_as_that(self):
        """Not as "off the first line", which would be false here and would send the
        caller to a fold that changes nothing: the fields ARE on the first line, and
        the run of them stops before **Class:** because a value lost its period."""
        self.seed("- [ ] **T001** — um **Class:** AUTONOMOUS, **Effort:** S. "
                  "**Criterion:** A: x. **Source:** 2026-08-13\n")
        out = self.pack()
        self.assertEqual(self.reason(out, "T001"),
                         "the field chain breaks before **Class:**, so no gate reads it")
        self.assertIn("cancel", self.repairs(out))

    # --- rule: no Risk -----------------------------------------------------
    def test_a_Risk_excludes_the_item_and_the_reason_carries_the_LINE(self):
        """The VALUE, not just the verdict: the Risk line is the whole reason a
        human re-triages the item, and `edit --risk none` is what clears an obsolete
        one. A reason that only said "carries a Risk" would make them go and look."""
        self.seed(item(1, "um", risk="apaga dado do usuário"))
        self.assertEqual(self.reason(self.pack(), "T001"), "Risk: apaga dado do usuário")

    def test_only_the_field_terminator_is_stripped_off_the_value(self):
        """One period, not every trailing period: a value ending in an ellipsis is a
        value, and a reason that ate all three would print something the file does
        not contain — on the one line a human re-triages the item from."""
        self.seed(item(1, "um", risk="depende da migração de junho..."))
        self.assertEqual(self.reason(self.pack(), "T001"),
                         "Risk: depende da migração de junho...")

    def test_a_Risk_marker_no_gate_may_read_still_excludes_the_item(self):
        """"there is a **Risk:** marker I am not allowed to read" is not "there is no
        risk", and unattended execution is the wrong place to guess. Excluded, and
        SAID — the safe direction is also the one that leaves a trace."""
        self.seed(item(1, "um").rstrip("\n") + "\n  nota: **Risk:** a migração de junho\n")
        self.assertIn("**Risk:** marker sits where no gate reads it",
                      self.reason(self.pack(), "T001"))

    # --- rule: Env absent or naming THIS machine ---------------------------
    def test_an_item_bound_to_this_machine_is_eligible(self):
        self.site(SITE)
        self.seed(pack_item(1, "um", env="alpha"))
        self.assertEqual(self.eligible(), ["T001"])

    def test_an_item_bound_to_ANOTHER_machine_is_out_naming_BOTH_names(self):
        self.site(SITE)
        self.seed(pack_item(1, "um", env="bravo"))
        self.assertEqual(self.reason(self.pack(), "T001"),
                         "Env is 'bravo', this machine is alpha")

    def test_with_no_site_file_an_Env_is_foreign_and_no_Env_is_local(self):
        """Decided, not left to explode: with no site file NO environment exists, so
        an item naming one names another machine and an item naming none is local.
        Refusing the whole command instead would deny a package to every machine that
        never wrote the file — where the overwhelming majority of items carry no Env
        and the rule decides nothing."""
        self.seed(pack_item(1, "um", env="bravo") + item(2, "dois"))
        out = self.pack()
        self.assertEqual(self.reason(out, "T001"), "Env is 'bravo', there is no site file")
        self.assertEqual(self.eligible(out), ["T002"])

    def test_a_site_file_that_EXISTS_and_is_broken_is_refused_verbatim(self):
        """The other case entirely, and telling them apart is the point: "create the
        file" and "line 2 of your file is wrong" are different instructions. Guessing
        "no environments exist" here would drop every Env-bearing item in silence."""
        self.site("identity = alpha\n")
        self.seed(item(1, "um"))
        r = self.run_tk("pack")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("environments", r.stderr)
        self.assertNotIn("Traceback", r.stderr)

    def test_the_roster_is_NOT_revalidated_on_the_way_out(self):
        """The writer already refuses a value outside the roster, so re-asking here
        is the same rule in two places — and the day the roster changes, the second
        one starts lying about items that were already in the file. An Env that does
        not match this machine is another machine's. Full stop, no verdict on whether
        the name still exists."""
        self.site(SITE)
        self.seed(pack_item(1, "um", env="delta"))
        self.assertEqual(self.reason(self.pack(), "T001"),
                         "Env is 'delta', this machine is alpha")

    def test_an_EMPTY_Env_reads_as_an_empty_value_and_not_as_no_value(self):
        """Quoted for this: unquoted, a field a hand-edit left empty prints "Env is ,
        this machine is alpha" and a value with a trailing blank prints as a clean
        name. The value is in the line precisely so a wrong one looks wrong."""
        self.site(SITE)
        self.seed(pack_item(1, "um", env="").replace("**Criterion:**",
                                                     "**Env:** . **Criterion:**", 1))
        self.assertEqual(self.reason(self.pack(), "T001"),
                         "Env is '', this machine is alpha")

    def test_two_Env_fields_are_ambiguous_not_guessed(self):
        """The first of the two names THIS machine, so a reader that took it would
        package the item — while the file says two different things about where it
        runs."""
        self.site(SITE)
        self.seed(pack_item(1, "um", env="alpha")
                  .replace("**Criterion:**", "**Env:** bravo. **Criterion:**", 1))
        self.assertEqual(self.reason(self.pack(), "T001"),
                         "2 **Env:** fields in the chain, so its value is ambiguous")

    def test_an_Env_marker_no_gate_may_read_still_excludes_the_item(self):
        """The silent failure this whole output exists to end: a junk Env value is
        not this machine's identity either, so before `pack` the item simply stopped
        appearing in every package, on every machine, with nothing anywhere saying
        why."""
        self.site(SITE)
        self.seed(item(1, "um").rstrip("\n") + "\n  nota: **Env:** a máquina do escritório\n")
        self.assertIn("**Env:** marker sits where no gate reads it",
                      self.reason(self.pack(), "T001"))

    # --- rule: not claimed by a sibling session ----------------------------
    def test_a_claimed_item_is_out_and_the_line_says_who_holds_it(self):
        """Claimed through the real command, so this asserts the two-sided contract:
        what `claim` writes is what the package reads. A fixture would only assert
        that the reader agrees with itself."""
        self.seed(item(1, "um"))
        self.assertEqual(self.run_tk("claim", "T001", "--as", "alpha").returncode, 0)
        self.assertRegex(self.reason(self.pack(), "T001"),
                         r"\Aclaimed by alpha since " + STAMP_RE.pattern + r"\Z")

    def test_the_RELEASE_repair_is_printed_and_gives_the_item_back(self):
        self.seed(item(1, "um"))
        self.run_tk("claim", "T001", "--as", "alpha")
        self.assertIn("`tk-queue release <id>`", self.repairs(self.pack()))
        self.assertEqual(self.run_tk("release", "T001").returncode, 0)
        self.assertEqual(self.eligible(), ["T001"])

    def test_two_claims_are_never_shown_as_free(self):
        """The dangerous direction of tolerance: two owners are on the record, and an
        item printed without a mark reads as FREE to the very package built from it."""
        self.seed(pack_item(1, "um", claimed="alpha since 2026-08-19T10:00:00Z")
                  .rstrip("\n") + " **Claimed:** bravo since 2026-08-19T11:00:00Z.\n")
        self.assertIn("ambiguous", self.reason(self.pack(), "T001"))

    def test_a_Claimed_marker_no_gate_may_read_still_excludes_the_item(self):
        self.seed(item(1, "um").rstrip("\n") + "\n  nota: **Claimed:** alguém\n")
        self.assertIn("**Claimed:** marker sits where no gate reads it",
                      self.reason(self.pack(), "T001"))

    # --- rule: an item with no ID cannot be closed by ID -------------------
    def test_an_item_with_no_ID_is_not_packaged_and_MIGRATE_repairs_it(self):
        """Asked LAST, so it is reached only by an item that is otherwise ready — and
        so the reason a DECISION item gets is its class, not its missing ID."""
        self.seed("- [ ] sem id **Class:** AUTONOMOUS. **Effort:** S. "
                  "**Criterion:** A: x. **Source:** 2026-08-13\n")
        out = self.pack()
        self.assertEqual(self.reason(out, "----"), "no ID")
        self.assertIn("`tk-queue migrate`", self.repairs(out))
        self.assertEqual(self.run_tk("migrate").returncode, 0)
        self.assertEqual(self.eligible(), ["T001"])

    def test_the_missing_ID_is_asked_LAST_not_first(self):
        """Order is part of the contract: the first rule that applies is the reason
        printed. Asked first, every legacy ID-less item would report a missing ID and
        never the class or the Risk that is the thing a reader can act on."""
        self.seed("- [ ] sem id **Class:** DECISION. **Deferred:** afk. **Effort:** S. "
                  "**Criterion:** B: veredito. **Source:** 2026-08-13\n")
        self.assertEqual(self.reason(self.pack(), "----"), "class is DECISION")

    # --- the rule that must NOT exist here ---------------------------------
    def test_a_Deferred_field_decides_NOTHING_here(self):
        """`--deferred` is refused on every class but DECISION and leaving that class
        drops it, so no path through this CLI produces an AUTONOMOUS item carrying
        one. Reading it here would be the same invariant in a second place — and the
        second place is the one that rots, because nothing exercises it."""
        self.seed(item(1, "um").replace("**Class:** AUTONOMOUS.",
                                        "**Class:** AUTONOMOUS. **Deferred:** afk.", 1))
        self.assertEqual(self.eligible(), ["T001"])

    # --- reading, not gating -----------------------------------------------
    def test_one_malformed_item_does_not_stop_the_others(self):
        """A gate may `fail`; a reader may not. `list` must not die on one bad item
        and stop showing the other twenty, and the package that is built from it
        inherits the rule."""
        self.seed(item(1, "um").rstrip("\n") + "\n  nota: **Claimed:** alguém\n"
                  + item(2, "dois"))
        out = self.pack()
        self.assertEqual(self.eligible(out), ["T002"])
        self.assertIn("**Claimed:** marker", self.reason(out, "T001"))

    def test_an_unreadable_Effort_does_not_cost_the_item_its_place(self):
        """Effort decides nothing about eligibility, so an item missing it is a
        candidate whose cost the caller estimates — not an item dropped over a field
        this filter was never about."""
        self.seed(item(1, "um").replace(" **Effort:** S.", "", 1))
        self.assertEqual(self.blocks(self.pack())["eligible"],
                         ["T001  ?             avulso                um"])

    def test_a_repair_is_printed_ONCE_however_many_items_need_it(self):
        """Six consecutive items carrying one defect is the real queue's shape, and
        six copies of a remedy that long bury the six reasons standing beside them —
        in output whose reader is a skill's prose."""
        self.seed("".join(LEGACY % i for i in (1, 2, 3)))
        out = self.pack()
        self.assertEqual(len(self.blocks(out)["excluded"]), 3)
        self.assertEqual(len(self.blocks(out)["repairs"]), 1)


# --- T172: provenance fields, and the lane the package reads from them -----

def ticket_item(iid, text, spec=None, ticket=None, repo=None, **kw):
    """An item as `add --ticket/--spec/--repo` writes one: the three fields sit
    between the Project tag and Source, in that order, which is where
    compose_item puts them."""
    fields = ""
    if ticket:
        fields += f" **Ticket:** {ticket}."
    if spec:
        fields += f" **Spec:** {spec}."
    if repo:
        fields += f" **Repo:** {repo}."
    return item(iid, text, **kw).replace(" **Source:**", fields + " **Source:**", 1)


class TestProvenanceFields(QueueTest):
    """Who imports a ticket into the queue records where it came from, so the
    package reads the lane as a FIELD instead of guessing it from prose. Both
    values are refs (`<repo>#<n>`), and a ref is validated by SHAPE — a typo'd
    one feeds a `closes` line that closes nothing, or a lane named after an
    issue that does not exist."""

    def add(self, *extra, text="importado"):
        return self.run_tk("add", text, "--class", "AUTONOMOUS", "--effort", "S",
                           "--criterion", "A: x", *extra)

    def test_both_fields_are_written_at_the_writers_position(self):
        """In the chain, after **Class:** — the only position the gates read a
        field at. Written anywhere else the value is there and no reader may use
        it, which is worse than absent: absent is visible."""
        self.seed()
        r = self.add("--ticket", "ambiente#172", "--spec", "ambiente#171")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("**Ticket:** ambiente#172. "
                      "**Spec:** ambiente#171. **Born:**", self.body())

    def test_the_values_round_trip_byte_for_byte(self):
        """The ticket's criterion, through the readers that exist: `pack` prints
        the lane built from the Spec and writes nothing, `list` shows the item and
        writes nothing, and the file still carries both values character for
        character. A reader that rewrote what it read is the defect no assertion on
        its OUTPUT would show."""
        self.seed()
        self.assertEqual(self.add("--ticket", "claude-skills#26",
                                  "--spec", "ambiente#171").returncode, 0)
        before = self.body()
        self.assertEqual(self.run_tk("list").returncode, 0)
        self.assertEqual(self.run_tk("pack").returncode, 0)
        self.assertEqual(self.body(), before)
        self.assertIn("**Ticket:** claude-skills#26.", before)
        self.assertIn("**Spec:** ambiente#171.", before)

    def test_an_add_without_the_flags_writes_the_item_of_today(self):
        """The whole file, byte for byte, against the same add on the version
        before the flags existed. Two new optional fields are the cheapest place
        to change the shape of EVERY item by accident."""
        self.seed()
        self.assertEqual(self.add(text="sem procedência").returncode, 0)
        today = datetime.date.today().isoformat()
        self.assertEqual(self.body(),
                         HEADER + "- [ ] **T001** — sem procedência **Class:** AUTONOMOUS. "
                         "**Effort:** S. **Criterion:** A: x. "
                         f"**Born:** {today}. **Source:** {today}\n")

    def test_a_value_outside_the_ref_shape_is_refused(self):
        for flag in ("--ticket", "--spec"):
            # `-repo#1` is NOT in this list and may not be: argparse takes any
            # value starting with `-` as an unknown option and refuses it before
            # `validate_ref` runs, so it would prove the flag exists and nothing
            # about the guard. `_repo#1` and `.repo#1` are the same shape that
            # DOES reach it — the leading-character class had no test without them
            for junk in ("172", "#172", "repo#", "repo#abc", "repo #172", "",
                         "owner/repo#172", "repo#172x", "_repo#1", ".repo#1",
                         "repo#1234567890", "r" * 101 + "#1", "repo#1.2",
                         "none", "**Spec:** repo#1"):
                with self.subTest(flag=flag, junk=junk):
                    self.seed()
                    r = self.add(flag, junk)
                    self.assertNotEqual(r.returncode, 0, f"{flag} {junk!r} was accepted")
                    self.assertNotIn("- [ ] ", self.body(), "the item was written anyway")

    def test_a_well_formed_ref_is_accepted_in_the_shapes_that_occur(self):
        for ref in ("repo#1", "ambiente#172", "claude-skills#26",
                    "a.b_c-d#999999", "repo#123456789", "r" * 100 + "#1"):
            with self.subTest(ref=ref):
                self.seed()
                r = self.add("--spec", ref)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertIn(f"**Spec:** {ref}.", self.body())

    def test_the_flags_are_independent(self):
        """`--ticket` feeds the `closes` line and `--spec` decides the lane: an
        imported ticket may legitimately have one and not the other, so coupling
        them would refuse a real case to enforce a rule nothing needs."""
        self.seed()
        self.assertEqual(self.add("--ticket", "repo#1").returncode, 0)
        body = self.body()
        self.assertIn("**Ticket:** repo#1.", body)
        self.assertNotIn("**Spec:**", body)


class TestTheSpecIsTheOneEditableFieldOfItsGroup(QueueTest):
    """**Spec:** is an address, not a provenance. It decides the LANE `pack`
    dispatches the item in, and a lane is a routing decision over a queue that
    moves — a spec closes, a track is resliced, and the same ticket belongs under
    another one. **Ticket:** and **Repo:** say where the item came from and where
    its code lands, which cannot change while it stays the same item, so they keep
    no flag here at all."""

    def test_the_field_is_written_on_an_item_that_carried_none(self):
        """Through the reader that consumes it, not by reading the file back
        alone: two items with no Spec are two `avulso` lanes, and the whole point
        of writing the field is that `pack` then builds the accumulated one."""
        self.seed(item(1, "um"), item(2, "dois"))
        for iid in ("T001", "T002"):
            r = self.run_tk("edit", iid, "--spec", "repo#171")
            self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("**Spec:** repo#171.", self.body())
        pack = self.run_tk("pack")
        self.assertEqual(pack.returncode, 0, pack.stderr)
        self.assertEqual(pack.stdout.count("spec repo#171"), 2, pack.stdout)

    def test_the_field_is_REWRITTEN_and_the_old_value_is_gone(self):
        """Writing once and refusing the second write would be the add-only rule
        wearing a flag: the case this exists for is an item already pointed at a
        spec that closed."""
        self.seed(ticket_item(1, "um", spec="repo#171"),
                  ticket_item(2, "dois", spec="repo#171"))
        r = self.run_tk("edit", "T002", "--spec", "repo#144")
        self.assertEqual(r.returncode, 0, r.stderr)
        body = self.body()
        self.assertIn("**Spec:** repo#144.", body)
        self.assertEqual(body.count("**Spec:**"), 2, "the field was duplicated")
        self.assertEqual(body.count("repo#171"), 1, "the old value survived")

    def test_the_other_two_fields_of_the_group_still_have_no_flag(self):
        """`--ticket`, `--repo` and `--source` are refused by argparse itself —
        the flag does not exist. Relaxing one field may not relax its neighbours:
        that is the whole content of the split."""
        for flag, value in (("--ticket", "repo#1"), ("--repo", "/root/x"),
                            ("--source", "hoje")):
            with self.subTest(flag=flag):
                self.seed(ticket_item(1, "um", ticket="repo#9", repo="/root/y"))
                before = self.body()
                r = self.run_tk("edit", "T001", flag, value)
                self.assertNotEqual(r.returncode, 0, f"{flag} was accepted")
                self.assertIn(flag, r.stderr)
                self.assertEqual(self.body(), before, "the queue was written anyway")

    def test_a_value_outside_the_ref_shape_is_refused_and_writes_nothing(self):
        """The same gate the way in takes, and for the same reason: a malformed
        lane address is a second branch and a second campaign for a spec that
        already has both. `none` is in the list on purpose — everywhere else in
        this script that word DELETES a field, and a lane is changed, never
        emptied."""
        for junk in ("172", "#172", "repo#", "repo#abc", "owner/repo#172",
                     "repo#172x", "_repo#1", ".repo#1", "none", "NONE", ""):
            with self.subTest(junk=junk):
                self.seed(ticket_item(1, "um", spec="repo#171"))
                before = self.body()
                r = self.run_tk("edit", "T001", "--spec", junk)
                self.assertNotEqual(r.returncode, 0, f"--spec {junk!r} was accepted")
                self.assertEqual(self.body(), before, "the queue was written anyway")

    def test_the_value_is_stored_in_the_one_spelling(self):
        """`add` canonicalises and this door has to as well, or one queue holds
        two spellings of one reference and the lane count that reads them by `==`
        sees two specs of one ticket each."""
        self.seed(item(1, "um"), item(2, "dois"))
        self.assertEqual(self.run_tk("edit", "T001", "--spec",
                                     "Repo#0171").returncode, 0)
        self.assertEqual(self.run_tk("edit", "T002", "--spec",
                                     "repo#171").returncode, 0)
        self.assertEqual(self.body().count("**Spec:** repo#171."), 2)
        self.assertEqual(self.run_tk("pack").stdout.count("spec repo#171"), 2)


def blocked_item(iid, text, blocker, **kw):
    """An item as `add --blocked-by` writes one: the field sits between Env and
    Criterion, beside the other two fields `pack` gates on."""
    return item(iid, text, **kw).replace(
        " **Criterion:**", f" **Blocked-by:** {blocker}. **Criterion:**", 1)


class TestBlockedBy(QueueTest):
    """A dependency between two items existed only as prose in a tracker, and
    `pack` reads the queue and never the forge — so the package could not know
    that one of its candidates cannot start yet, and the lane stayed serial by
    construction. The field is the third one `pack` gates on: Risk says whether
    this may run unattended, Env says where, and this says NOT YET."""

    def add(self, *extra, text="depende"):
        return self.run_tk("add", text, "--class", "AUTONOMOUS", "--effort", "S",
                           "--criterion", "A: x", *extra)

    def test_the_line_is_written_where_the_gates_read_a_field(self):
        """In the chain, beside Risk and Env. Written anywhere else the value is
        there and no reader may use it, which is worse than absent."""
        self.seed()
        r = self.add("--blocked-by", "T006")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("**Effort:** S. **Blocked-by:** T006. **Criterion:**", self.body())

    def test_every_id_spelling_is_stored_as_the_one(self):
        """`pack` prints this value in the reason it excludes the item with, and
        a caller reading `blocked by 6` has to guess what to look up."""
        for spelling in ("T006", "t006", "006", "6"):
            with self.subTest(spelling=spelling):
                self.seed()
                self.assertEqual(self.add("--blocked-by", spelling).returncode, 0)
                self.assertIn("**Blocked-by:** T006.", self.body())

    def test_a_value_that_is_no_item_id_is_refused_and_writes_nothing(self):
        for junk in ("repo#1", "T", "T00x", "amanhã", "T1 e T2", ""):
            with self.subTest(junk=junk):
                self.seed()
                r = self.add("--blocked-by", junk)
                self.assertNotEqual(r.returncode, 0, f"{junk!r} was accepted")
                self.assertNotIn("- [ ] ", self.body(), "the item was written anyway")

    def test_an_add_without_the_flag_writes_the_item_of_today(self):
        """A new optional field is the cheapest place to change the shape of
        EVERY item by accident."""
        self.seed()
        self.assertEqual(self.add(text="sem bloqueio").returncode, 0)
        today = datetime.date.today().isoformat()
        self.assertEqual(self.body(),
                         HEADER + "- [ ] **T001** — sem bloqueio **Class:** AUTONOMOUS. "
                         "**Effort:** S. **Criterion:** A: x. "
                         f"**Born:** {today}. **Source:** {today}\n")

    def test_pack_leaves_the_item_out_while_the_blocker_is_open(self):
        """And NAMES the value: an item silently missing from the package is an
        item the caller never learns about, which is what every exclusion reason
        in this command exists to prevent."""
        self.seed(item(1, "o bloqueador"), blocked_item(2, "o bloqueado", "T001"))
        r = self.run_tk("pack")
        self.assertEqual(r.returncode, 0, r.stderr)
        eligible, excluded = r.stdout.split("excluded")
        self.assertIn("T001", eligible)
        self.assertNotIn("T002", eligible)
        self.assertIn("blocked by T001, still open", excluded)

    def test_closing_the_blocker_lets_it_back_in_with_no_re_edit(self):
        """The criterion of the item, end to end: the field is a pointer read
        against the queue on every run, never a state somebody has to remember
        to clear."""
        self.seed(item(1, "o bloqueador"), blocked_item(2, "o bloqueado", "T001"))
        self.assertEqual(self.run_tk("done", "T001", "--how", "PR #1").returncode, 0)
        r = self.run_tk("pack")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("T002", r.stdout.split("excluded")[0])
        self.assertNotIn("blocked by", r.stdout)

    def test_a_blocker_this_queue_never_held_does_not_hold_the_item(self):
        """An id in no open item is a dependency already met — the blocker was
        closed and archived. Refusing there would make the field unusable on the
        very queue where it has done its work."""
        self.seed(blocked_item(1, "o bloqueado", "T099"))
        self.assertIn("T001", self.run_tk("pack").stdout.split("excluded")[0])

    def test_an_unreadable_value_excludes_the_item(self):
        """The writer's gate is not the only door — a hand edit, a foreign tool,
        a merge — and here the safe default is Risk's and Env's, not Spec's: a
        dependency nobody can read is one nobody may declare satisfied."""
        self.seed(blocked_item(1, "o bloqueado", "amanhã"))
        r = self.run_tk("pack")
        self.assertIn("which is not an item id", r.stdout.split("excluded")[1])

    def test_a_marker_where_no_gate_reads_it_excludes_the_item(self):
        """Same answer as Risk and Env, and for the same reason: what the item
        really carries cannot be told."""
        self.seed(item(1, "cita **Blocked-by:** na prosa"))
        excluded = self.run_tk("pack").stdout.split("excluded")[1]
        self.assertIn("**Blocked-by:** marker sits where no gate reads it", excluded)

    def test_edit_writes_rewrites_and_clears_the_field(self):
        self.seed(item(1, "um"))
        self.assertEqual(self.run_tk("edit", "T001", "--blocked-by", "5").returncode, 0)
        self.assertIn("**Blocked-by:** T005.", self.body())
        self.assertEqual(self.run_tk("edit", "T001", "--blocked-by", "T006").returncode, 0)
        body = self.body()
        self.assertIn("**Blocked-by:** T006.", body)
        self.assertNotIn("T005", body)
        self.assertEqual(self.run_tk("edit", "T001", "--blocked-by", "none").returncode, 0)
        self.assertNotIn("**Blocked-by:**", self.body())

    def test_list_shows_the_blocker_beside_the_item(self):
        """`list` and `pack` may not disagree about whether an item is held back:
        the caller reads the reason in one and looks the item up in the other."""
        self.seed(item(1, "livre"), blocked_item(2, "preso", "T001"))
        out = self.run_tk("list").stdout
        self.assertIn("[blocked by T001]", out)
        self.assertEqual(out.count("blocked by"), 1)

    def test_list_marks_the_item_pack_drops_for_an_ambiguous_blocker(self):
        """Two qualifying fields: `pack` excludes the item and `list` may not show
        it FREE. The tolerant answer is the dangerous one here, exactly as it is
        for a claim — the reader who looks up that exclusion sees an item nothing
        holds, and the afk package is built from this same display."""
        self.seed(blocked_item(1, "preso", "T002").replace(
            " **Criterion:**", " **Blocked-by:** T003. **Criterion:**", 1))
        out = self.run_tk("list").stdout
        self.assertIn("[blocked ambiguously", out)
        excluded = self.run_tk("pack").stdout.split("excluded")[1]
        self.assertIn("**Blocked-by:** fields in the chain", excluded)

    def test_list_marks_the_item_pack_drops_for_a_marker_no_gate_reads(self):
        """Same asymmetry, the other shape: the marker sits where the position
        rule will not read it, `pack` drops the item over it, and a silent `list`
        would be the one reading that says it is dispatchable."""
        self.seed(item(1, "cita **Blocked-by:** na prosa"))
        out = self.run_tk("list").stdout
        self.assertIn("[a **Blocked-by:** marker no gate reads]", out)
        excluded = self.run_tk("pack").stdout.split("excluded")[1]
        self.assertIn("marker sits where no gate reads it", excluded)


class TestPackLane(PackOutput):
    """The lane is what the afk orchestrator dispatches by, and it is read from
    the QUEUE — never from GitHub, which `pack` does not touch. Tickets of one
    spec share an accumulated branch; everything else is a PR of its own."""

    def test_an_item_with_no_spec_is_avulso(self):
        self.seed(item(1, "um"))
        self.assertEqual(self.lanes(self.pack()), {"T001": "avulso"})

    def test_two_tickets_of_one_spec_share_the_accumulated_lane(self):
        self.seed(ticket_item(1, "um", spec="repo#171")
                  + ticket_item(2, "dois", spec="repo#171"))
        self.assertEqual(self.lanes(self.pack()), {"T001": "spec repo#171", "T002": "spec repo#171"})

    def test_the_two_lanes_coexist_in_one_package(self):
        """Not deferring the avulsos is the point: leaving them out would leave
        capacity on the table whenever the spec has few tickets."""
        self.seed(ticket_item(1, "um", spec="repo#171") + item(2, "dois")
                  + ticket_item(3, "tres", spec="repo#171"))
        self.assertEqual(self.lanes(self.pack()),
                         {"T001": "spec repo#171", "T002": "avulso", "T003": "spec repo#171"})

    def test_a_single_ticket_of_a_spec_is_a_LANE_not_an_exclusion(self):
        """The floor: a draft PR and a tail cost more than one item is worth, so a
        lone ticket goes out as an ordinary PR. It is still IN the package — the
        failure to avoid is turning a floor into a filter."""
        self.seed(ticket_item(1, "um", spec="repo#171") + item(2, "dois"))
        out = self.pack()
        self.assertEqual(self.lanes(out), {"T001": "avulso (repo#171)", "T002": "avulso"})
        self.assertEqual(self.blocks(out)["excluded"], [])

    def test_tickets_of_a_SECOND_spec_leave_with_the_exact_reason(self):
        """One spec per package: one branch, one campaign, one tail. The excluded
        ones come back next package, and the reason names the spec that took the
        lane so the caller does not have to work out which."""
        self.seed(ticket_item(1, "um", spec="repo#171")
                  + ticket_item(2, "dois", spec="repo#180")
                  + ticket_item(3, "tres", spec="repo#171")
                  + ticket_item(4, "quatro", spec="repo#180"))
        out = self.pack()
        self.assertEqual(self.lanes(out), {"T001": "spec repo#171", "T003": "spec repo#171"})
        for label in ("T002", "T004"):
            self.assertEqual(self.reason(out, label), "lane de spec ocupada por repo#171; esta é repo#180")

    def test_a_TIE_on_ticket_count_is_broken_by_QUEUE_ORDER(self):
        """Two tickets each: the depth rule cannot separate them, so the file's
        own order does — the one priority this queue has. Reading the tie the
        other way, the LAST spec seen, would re-prioritise the queue silently."""
        self.seed(ticket_item(1, "um", spec="repo#171")
                  + ticket_item(2, "dois", spec="repo#171")
                  + ticket_item(3, "tres", spec="repo#180")
                  + ticket_item(4, "quatro", spec="repo#180"))
        out = self.pack()
        self.assertEqual(self.lanes(out), {"T001": "spec repo#171", "T002": "spec repo#171"})
        for label in ("T003", "T004"):
            self.assertEqual(self.reason(out, label), "lane de spec ocupada por repo#171; esta é repo#180")

    def test_the_lane_goes_to_the_spec_with_the_MOST_tickets(self):
        """The accumulated branch is what pays for itself — one branch, one
        campaign, one tail, over as many tickets as it can hold — and queue order
        alone spent it on whichever spec was listed first. Measured on the real
        queue: two tickets of the spec at the top took the lane and three ready
        tickets of the spec below it left the package, package after package."""
        self.seed(ticket_item(1, "um", spec="repo#171")
                  + ticket_item(2, "dois", spec="repo#171")
                  + ticket_item(3, "tres", spec="repo#180")
                  + ticket_item(4, "quatro", spec="repo#180")
                  + ticket_item(5, "cinco", spec="repo#180"))
        out = self.pack()
        self.assertEqual(self.lanes(out), {"T003": "spec repo#180", "T004": "spec repo#180",
                                           "T005": "spec repo#180"})
        for label in ("T001", "T002"):
            self.assertEqual(self.reason(out, label),
                             "lane de spec ocupada por repo#180; esta é repo#171")

    def test_a_spec_under_the_floor_does_not_take_the_lane_it_cannot_use(self):
        """The interaction #171 left open, decided by its own US 27. The lone
        ticket of #171 gets no accumulated lane — it is under the floor — so it has
        none to occupy either, and #180 takes it. The literal reading, first ticket
        wins whatever its count, ran this package with ZERO accumulated lanes while
        excluding two tickets in the name of a lane nobody was using."""
        self.seed(ticket_item(1, "um", spec="repo#171")
                  + ticket_item(2, "dois", spec="repo#180")
                  + ticket_item(3, "tres", spec="repo#180"))
        out = self.pack()
        self.assertEqual(self.lanes(out),
                         {"T001": "avulso (repo#171)", "T002": "spec repo#180", "T003": "spec repo#180"})
        self.assertEqual(self.blocks(out)["excluded"], [])

    def test_no_spec_reaching_the_floor_leaves_every_ticket_avulso(self):
        """Three specs, one ticket each: no lane exists, so nothing can occupy one
        and nothing is excluded. The direction that would turn the floor into a
        filter takes the whole package with it."""
        self.seed(ticket_item(1, "um", spec="repo#171")
                  + ticket_item(2, "dois", spec="repo#180")
                  + ticket_item(3, "tres", spec="repo#190"))
        out = self.pack()
        self.assertEqual(self.lanes(out),
                         {"T001": "avulso (repo#171)", "T002": "avulso (repo#180)",
                          "T003": "avulso (repo#190)"})
        self.assertEqual(self.blocks(out)["excluded"], [])

    def test_the_lane_is_decided_among_ELIGIBLE_items_only(self):
        """An item excluded for its class or its Risk is not in the package, so it
        cannot take the package's lane with it — the second spec would then be
        refused a lane that nothing is using."""
        self.seed(ticket_item(1, "um", spec="repo#171", klass="DECISION")
                  + ticket_item(2, "dois", spec="repo#171", klass="DECISION")
                  + ticket_item(3, "tres", spec="repo#180")
                  + ticket_item(4, "quatro", spec="repo#180"))
        out = self.pack()
        self.assertEqual(self.lanes(out), {"T003": "spec repo#180", "T004": "spec repo#180"})
        # #171 reaches the floor over the WHOLE queue and holds no lane all the same:
        # neither of its tickets is in the package
        self.assertEqual([ln for ln in self.blocks(out)["excluded"]
                          if "ocupada" in ln], [])

    def test_a_spec_QUOTED_IN_PROSE_leaves_the_item_AVULSO(self):
        """A marker before the **Class:** the chain anchors at is the item's own
        prose: it names no lane, and it does not cost the item its place either.

        That is where the two provenance fields part company with **Risk:** and
        **Env:**, and the split is what each field ANSWERS. Risk and Env answer
        "is this safe to run unattended, and here?", so a marker no gate may read
        leaves that unknown and the item is refused. Spec answers "where does this
        go?", and there the absence of an answer HAS a safe default — the topology
        the queue had before the field existed, a PR of its own.

        Excluding instead was measured costing more than it bought: one sibling
        whose note merely CITED the marker left the candidate set, and took its
        whole spec below the floor, demoting the clean siblings' lane to avulso."""
        self.seed("- [ ] **T001** — nota sobre **Spec:** repo#999 em prosa — um "
                  "**Class:** AUTONOMOUS. **Effort:** S. **Criterion:** A: x. "
                  "**Source:** 2026-08-13\n")
        out = self.pack()
        self.assertEqual(self.lanes(out), {"T001": "avulso"})
        self.assertEqual(self.blocks(out)["excluded"], [])

    def test_one_siblings_PROSE_never_demotes_a_whole_specs_lane(self):
        """The cascade the block-wide marker count caused, and the reason the
        provenance fields are read at the writer's position and nowhere else. T002's
        note merely CITES `**Spec:**`; its chain names Spec once, unambiguously. With
        the count in the ladder, T002 was excluded on a false reason — and, gone from
        the candidate set, took the spec to one ticket, so T001 and T003 lost the
        accumulated lane they had every right to."""
        self.seed(ticket_item(1, "um", spec="repo#171")
                  + ticket_item(2, "dois", spec="repo#171").rstrip("\n")
                  + "\n  nota: cita o **Spec:** de outro item, só em prosa.\n"
                  + ticket_item(3, "tres", spec="repo#171"))
        out = self.pack()
        self.assertEqual(self.blocks(out)["excluded"], [])
        self.assertEqual(self.lanes(out), {"T001": "spec repo#171",
                                           "T002": "spec repo#171",
                                           "T003": "spec repo#171"})

    def test_two_Spec_fields_in_the_chain_are_ambiguous_not_guessed(self):
        self.seed(ticket_item(1, "um", spec="repo#171").replace(
            "**Spec:** repo#171.", "**Spec:** repo#171. **Spec:** repo#180.", 1))
        self.assertEqual(self.reason(self.pack(), "T001"),
                         "2 **Spec:** fields in the chain, so its value is ambiguous")

    def test_a_Spec_that_is_not_a_forge_reference_never_forms_a_LANE(self):
        """`validate_ref` guards the writer, and the writer is not the only way the
        field arrives — a hand edit, a foreign tool, a merge. Measured before this
        existed: two items carrying `**Spec:** homeserver ambiente#999.` (a blank,
        a value `add` refuses) formed a REAL accumulated lane and pushed two tickets
        of a genuine spec out of the package, naming an issue that existed only in
        the typo."""
        self.seed(ticket_item(1, "um", spec="homeserver ambiente#999")
                  + ticket_item(2, "dois", spec="homeserver ambiente#999")
                  + ticket_item(3, "tres", spec="repo#171")
                  + ticket_item(4, "quatro", spec="repo#171"))
        out = self.pack()
        self.assertEqual(self.lanes(out), {"T003": "spec repo#171", "T004": "spec repo#171"})
        for label in ("T001", "T002"):
            self.assertIn("not a forge reference", self.reason(out, label))
        self.assertIn("cancel", self.repairs(out))

    def test_two_specs_sharing_an_issue_number_are_told_APART(self):
        """The repo half is not decoration: this account's tickets already span two
        repos, so `a#171` and `b#171` are both write-legal and both real. Printing
        only `#171` gave two different specs one label, and told the excluded ticket
        its lane was occupied by its OWN number."""
        self.seed(ticket_item(1, "um", spec="a#171") + ticket_item(2, "dois", spec="a#171")
                  + ticket_item(3, "tres", spec="b#171") + ticket_item(4, "quatro", spec="b#171"))
        out = self.pack()
        self.assertEqual(self.lanes(out), {"T001": "spec a#171", "T002": "spec a#171"})
        self.assertEqual(self.reason(out, "T003"),
                         "lane de spec ocupada por a#171; esta é b#171")

    def test_a_duplicate_ID_never_costs_the_LANE_HOLDER_its_place(self):
        """A label is not unique — `----` is every ID-less item's, and a duplicate ID
        is a shape `list` warns about rather than refuses. Keyed by it, the lane was
        measured EXCLUDING the genuine holder: the second **T001** overwrote the
        first's entry, and the real lane holder came back with a reason naming its
        own spec as the one occupying the lane."""
        self.seed(ticket_item(1, "lane holder um", spec="repo#171")
                  + ticket_item(2, "lane holder dois", spec="repo#171")
                  + ticket_item(1, "id duplicado", spec="repo#180")
                  + ticket_item(4, "segundo da outra", spec="repo#180"))
        out = self.pack()
        eligible = self.blocks(out)["eligible"]
        self.assertEqual([ln.split()[0] for ln in eligible], ["T001", "T002"])
        self.assertEqual([re.split(r"\s{2,}", ln.strip())[2] for ln in eligible],
                         ["spec repo#171", "spec repo#171"])

    def test_the_TICKET_the_PR_closes_comes_back_from_the_command(self):
        """`--ticket` feeds the `closes` line, the package is dispatched from THIS
        output, and before this the field had no reader at all: `list` prints it
        nowhere and there is no `show` subcommand. Appended in brackets, and only
        for the items that carry one."""
        self.seed(ticket_item(1, "um", spec="repo#171", ticket="repo#1")
                  + ticket_item(2, "dois", spec="repo#171", ticket="repo#2")
                  + item(3, "sem procedência"))
        lines = self.blocks(self.pack())["eligible"]
        self.assertTrue(lines[0].endswith("  [repo#1]"), lines[0])
        self.assertTrue(lines[1].endswith("  [repo#2]"), lines[1])
        self.assertNotIn("[", lines[2])

    def test_a_TICKET_the_position_rule_cannot_read_is_MARKED_not_silent(self):
        """Not excluded — Ticket decides no lane, so an unreadable one may not cost
        the item its place — and not silent either: printing nothing made an item
        whose ticket no reader may use identical to one that never had a ticket, and
        the PR then closes nothing while the work ships. `[?]`, the mark this file
        already uses where a field could not be read and the answer is not
        exclusion (`pack_effort` prints `?`)."""
        self.seed(ticket_item(1, "dois tickets", spec="repo#171", ticket="repo#1").replace(
                      "**Ticket:** repo#1.", "**Ticket:** repo#1. **Ticket:** repo#2.", 1)
                  + ticket_item(2, "forma errada", spec="repo#171", ticket="nao e ref"))
        lines = self.blocks(self.pack())["eligible"]
        self.assertEqual(len(lines), 2, lines)
        for ln in lines:
            self.assertTrue(ln.endswith("  [?]"), ln)

    def test_a_marker_QUOTED_IN_PROSE_earns_no_mark_at_all(self):
        """The other side of the same question, and the one the first `[?]` got
        wrong: an item whose only **Ticket:** is a note citing the marker never had
        a ticket, so it must read like an item that never had one. `[?]` there sends
        whoever writes the PR hunting for a ticket that does not exist."""
        self.seed(item(1, "só cita o marcador").rstrip("\n")
                  + "\n  nota: cita o **Ticket:** de outro item, só em prosa.\n"
                  + item(2, "sem marcador nenhum"))
        for ln in self.blocks(self.pack())["eligible"]:
            self.assertNotIn("[", ln, ln)

    def test_a_marker_QUOTED_IN_PROSE_does_not_hide_the_real_ticket(self):
        """The block-wide count `pack_closes` used to ask before the reader: an
        item's real, well-placed **Ticket:** printed NOTHING because a continuation
        line merely cited the marker in prose. One rule asked in two spellings, and
        the looser one silently won — the shape the consolidation exists to end."""
        self.seed(ticket_item(1, "ticket real", spec="repo#171", ticket="repo#1").rstrip("\n")
                  + "\n  nota: cita o **Ticket:** de outro item, só em prosa.\n")
        self.assertTrue(self.blocks(self.pack())["eligible"][0].endswith("  [repo#1]"))

    def test_the_ONE_reader_refuses_a_reference_quoted_before_the_ANCHOR(self):
        """The position rule, proved through `pack_ref` itself. A `**Spec:**` or
        `**Ticket:**` segment sitting BEFORE the **Class:** the chain anchors at is
        the item's own prose wearing a field's name, and the anchor-free reader was
        measured green against the whole suite: nothing exercised either caller with
        this shape, so a hand-edited item could have named a lane from its prose."""
        self.seed("- [ ] **T001** — nota: **Ticket:** repo#9. **Class:** AUTONOMOUS. "
                  "**Effort:** S. **Criterion:** A: x. **Spec:** repo#171. "
                  "**Ticket:** repo#1. **Source:** 2026-08-13\n"
                  + ticket_item(2, "dois", spec="repo#171", ticket="repo#2"))
        out = self.pack()
        self.assertEqual(self.lanes(out),
                         {"T001": "spec repo#171", "T002": "spec repo#171"})
        # the segment BEFORE the anchor is prose: the chain names Ticket twice and
        # only one of them is real, so the anchor-free reader sees two and marks the
        # item unreadable, while the position rule reads the one a writer wrote
        self.assertTrue(self.blocks(out)["eligible"][0].endswith("  [repo#1]"),
                        self.blocks(out)["eligible"][0])

    def test_two_SPELLINGS_of_one_reference_are_one_spec(self):
        """The class this consolidation ends. Equality decided the lane by raw
        string, so `Ambiente#171` and `ambiente#171` — one repo, a forge repo name
        being case-insensitive — were two specs of one ticket each, both under the
        floor, both dispatched avulso: two branches and two campaigns for one spec.
        Leading zeros were the same defect from the other side, and produced a
        reason naming the item's own spec as the one occupying the lane."""
        self.seed(ticket_item(1, "um", spec="Ambiente#171")
                  + ticket_item(2, "dois", spec="ambiente#0171"))
        self.assertEqual(self.lanes(self.pack()),
                         {"T001": "spec ambiente#171", "T002": "spec ambiente#171"})

    def test_the_canonical_spelling_is_what_the_WRITER_stores(self):
        """Canonicalised where the value is validated, so the file holds one
        spelling per reference and every later comparison is a plain `==` again.
        Fixing it only at the reader would leave the queue carrying spellings that
        agree today and disagree the next time somebody adds a reader."""
        self.seed()
        r = self.run_tk("add", "importado", "--class", "AUTONOMOUS", "--effort", "S",
                        "--criterion", "A: x", "--ticket", "Ambiente#0172",
                        "--spec", "AMBIENTE#171")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("**Ticket:** ambiente#172. **Spec:** ambiente#171.", self.body())

    def test_a_TICKET_that_is_not_a_forge_reference_is_never_printed(self):
        """The asymmetry this consolidation removes: the Ticket had a reader of its
        own, with the position rule and no shape gate, and a hand-edited
        `**Ticket:** repo#1] injetado` spliced a second bracket group and free text
        into a line whose consumer is a skill's prose. Silent, not excluded — Ticket
        decides no lane — but never printed unvalidated."""
        for junk in ("repo#1] injetado", "repo#1  coluna falsa", "", "fecha o 173"):
            with self.subTest(junk=junk):
                self.seed(ticket_item(1, "um", ticket=junk) if junk
                          else "- [ ] **T001** — um **Class:** AUTONOMOUS. **Effort:** S. "
                               "**Criterion:** A: x. **Ticket:** . **Source:** 2026-08-13\n")
                line = self.blocks(self.pack())["eligible"][0]
                if junk:
                    self.assertNotIn(junk, line, line)
                self.assertTrue(line.endswith("  [?]"), line)

    def test_the_read_side_shape_gate_refuses_a_PREFIX(self):
        """`fullmatch`, not `match`. A prefix match reads `repo#171 texto solto` as a
        well-formed `repo#171` and lets it name a lane — and the value it would name
        it after is one the writer refuses, so nothing downstream would ever see the
        text that made it wrong."""
        self.seed(ticket_item(1, "um", spec="repo#171 texto solto")
                  + ticket_item(2, "dois", spec="repo#171 texto solto"))
        out = self.pack()
        self.assertEqual(self.blocks(out)["eligible"], [])
        for label in ("T001", "T002"):
            self.assertIn("not a forge reference", self.reason(out, label))

    def test_a_below_floor_ticket_still_NAMES_its_spec(self):
        """`avulso` alone made a lone ticket of a spec identical to a ticket of no
        spec, and they are not the same thing to whoever dispatches: the open-PR
        check has to know which spec to ask about, and a lone ticket of a spec whose
        branch is already open is the case that check exists for."""
        self.seed(ticket_item(1, "um", spec="repo#171") + item(2, "dois"))
        self.assertEqual(self.lanes(self.pack()),
                         {"T001": "avulso (repo#171)", "T002": "avulso"})

    def test_a_RISK_outranks_a_malformed_Spec_on_the_ladder(self):
        """The rung the help documents: class, risk, env, spec. The shape check sat
        with the marker defects for one round, and that put a typo'd Spec ahead of a
        real **Risk:** line — the item was excluded either way, but the reason
        printed was the typo and the risk nobody saw went unprinted, on the one
        field that says unattended execution can do damage."""
        self.seed(ticket_item(1, "um", spec="nao e uma ref", risk="apaga dado do usuário"))
        self.assertEqual(self.reason(self.pack(), "T001"), "Risk: apaga dado do usuário")

    def test_the_lane_exclusion_is_the_LAST_step_of_the_ladder(self):
        """A ticket of the second spec that ALSO carries a Risk is reported for the
        Risk: the ladder's earlier steps are about the item itself, and the lane is
        about the package it did not fit in.

        Structural, not a guard of its own: the set the lane pushes out is built
        from the CANDIDATES, so an item an earlier rule already excluded can never
        be in it. What protects that is the mutant on `pack_lanes(candidates)`;
        this test is here because the ordering is the thing a reader of the output
        depends on, and a structure nobody wrote down is one a later refactor
        undoes without noticing."""
        self.seed(ticket_item(1, "um", spec="repo#171")
                  + ticket_item(2, "dois", spec="repo#180", risk="apaga dado")
                  + ticket_item(3, "tres", spec="repo#171")
                  + ticket_item(4, "quatro", spec="repo#180"))
        self.assertEqual(self.reason(self.pack(), "T002"), "Risk: apaga dado")

# --- T249: the election has to know which spec is already being worked -----

class TestPackLaneUnderWay(PackOutput):
    """`pack` elects the lane from the queue alone, and the one fact the queue
    cannot hold is whether a spec's branch is already pushed. Measured on the real
    queue: `pack` elected the open spec, the orchestrator took that spec's tickets
    out afterwards, and the second spec — two tickets ready — stayed excluded
    behind a lane the package could not use, package after package. So the caller
    asks the remote and calls `pack` a second time carrying the answer.

    The fixture below is that measured case, item for item."""

    #: the queue of the report the ticket was written from: two tickets of the spec
    #: whose branch is open (#171), two of a second spec (#144), a lone ticket of a
    #: third, an item of no spec, and three items the earlier rungs exclude
    def seed_the_measured_queue(self):
        self.seed(
            ticket_item(7, "the first ticket of the spec", spec="ambiente#171",
                        ticket="ambiente#172", repo="https://github.com/owner/code.git",
                        effort="S (~20min)")
            + ticket_item(8, "the second one", spec="ambiente#171",
                          ticket="ambiente#173", effort="M (~1h)")
            + ticket_item(9, "the item's text", repo="/srv/projects/exemplo")
            + ticket_item(10, "a lone ticket, under the floor", spec="ambiente#159")
            + item(12, "another item", klass="DECISION")
            + ticket_item(21, "a ticket of a second spec", spec="ambiente#144")
            + ticket_item(22, "and its sibling", spec="ambiente#144")
            + item(31, "a legacy item").replace(" **Class:** AUTONOMOUS.", "")
            + item(40, "a risky one", risk="toca producao"))

    # --- the flag does its work ------------------------------------------
    def test_the_named_spec_loses_the_lane_and_the_next_one_takes_it(self):
        """The whole ticket in one assertion, byte for byte. #171 is skipped when
        the lane is elected, its two tickets leave on the lane rung with the reason
        naming the occupation, and #144 — excluded in the run before, behind a lane
        nothing could use — comes back as the package's accumulated lane."""
        self.seed_the_measured_queue()
        r = self.run_tk("pack", "--spec-under-way", "ambiente#171")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, """eligible (4 of 9, in queue order):
T009  S             avulso                the item's text  [repo: /srv/projects/exemplo]
T010  S             avulso (ambiente#159)  a lone ticket, under the floor
T021  S             spec ambiente#144     a ticket of a second spec
T022  S             spec ambiente#144     and its sibling

excluded (5):
T007  the first ticket of the spec  — lane de spec ocupada por ambiente#171; declarada em curso por --spec-under-way
T008  the second one  — lane de spec ocupada por ambiente#171; declarada em curso por --spec-under-way
T012  another item  — class is DECISION
T031  a legacy item  — no **Class:** field
T040  a risky one  — Risk: toca producao

repairs:
- no **Class:** at all: `tk-queue edit <id> --class AUTONOMOUS`
""")

    def test_the_run_with_no_flag_is_what_it_has_always_been(self):
        """The same queue, byte for byte, from the binary that predates the flag.
        A flag whose default path rewrites one column silently rewrites what every
        skill reading this output parses — and the pinned bytes are the only place
        that shows up before a package is dispatched on them."""
        self.seed_the_measured_queue()
        r = self.run_tk("pack")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, """eligible (4 of 9, in queue order):
T007  S (~20min)    spec ambiente#171     the first ticket of the spec  [ambiente#172]  [repo: https://github.com/owner/code.git]
T008  M (~1h)       spec ambiente#171     the second one  [ambiente#173]
T009  S             avulso                the item's text  [repo: /srv/projects/exemplo]
T010  S             avulso (ambiente#159)  a lone ticket, under the floor

excluded (5):
T012  another item  — class is DECISION
T021  a ticket of a second spec  — lane de spec ocupada por ambiente#171; esta é ambiente#144
T022  and its sibling  — lane de spec ocupada por ambiente#171; esta é ambiente#144
T031  a legacy item  — no **Class:** field
T040  a risky one  — Risk: toca producao

repairs:
- no **Class:** at all: `tk-queue edit <id> --class AUTONOMOUS`
""")

    def test_a_spec_the_queue_never_names_changes_nothing(self):
        """The caller asks the remote about every reference the report names, and
        most answers are "free". A flag value nothing matches must be inert: a run
        that shifted a lane on it would make the number of questions asked part of
        the answer."""
        self.seed_the_measured_queue()
        plain = self.run_tk("pack").stdout
        self.assertEqual(self.run_tk("pack", "--spec-under-way", "ambiente#999").stdout,
                         plain)

    # --- the floor is no shield here --------------------------------------
    def test_a_lone_ticket_of_a_spec_under_way_leaves_TOO(self):
        """Under the floor the ticket would go out `avulso (<ref>)` — its own pull
        request, over the work the open branch is already carrying. That is the
        second pull request per spec the check exists to prevent, so the floor
        shields a ticket from the lane CONTEST and never from this rung."""
        self.seed_the_measured_queue()
        out = self.run_tk("pack", "--spec-under-way", "ambiente#159").stdout
        self.assertNotIn("T010", "".join(self.blocks(out)["eligible"]))
        self.assertEqual(self.reason(out, "T010"),
                         "lane de spec ocupada por ambiente#159; declarada em curso "
                         "por --spec-under-way")

    def test_the_two_rungs_are_told_apart_by_their_value(self):
        """One output, both exclusions. They are worded alike because they ARE one
        rung, and the second half is what says which source decided it: `esta é
        <ref>` read the queue's order, `declarada em curso` read the remote. A
        report that collapsed them could not say which spec lost why."""
        self.seed_the_measured_queue()
        out = self.run_tk("pack", "--spec-under-way", "ambiente#159").stdout
        self.assertEqual(self.reason(out, "T010"),
                         "lane de spec ocupada por ambiente#159; declarada em curso "
                         "por --spec-under-way")
        self.assertEqual(self.reason(out, "T021"),
                         "lane de spec ocupada por ambiente#171; esta é ambiente#144")

    # --- no lane left to elect --------------------------------------------
    def test_no_spec_reaching_the_floor_after_the_skip_runs_with_no_lane(self):
        """#171 is skipped and #144 holds a single ticket, so nothing reaches the
        floor: the package runs with no accumulated lane, and no ticket is excluded
        by the lane contest. Turning "no lane" into an exclusion would take the
        whole package with it."""
        self.seed(ticket_item(7, "um", spec="ambiente#171")
                  + ticket_item(8, "dois", spec="ambiente#171")
                  + ticket_item(21, "tres", spec="ambiente#144")
                  + item(9, "quatro"))
        out = self.run_tk("pack", "--spec-under-way", "ambiente#171").stdout
        self.assertEqual(self.lanes(out),
                         {"T021": "avulso (ambiente#144)", "T009": "avulso"})
        self.assertEqual(self.labels(self.blocks(out)["excluded"]), ["T007", "T008"])

    def test_every_spec_under_way_leaves_a_package_of_avulsos(self):
        """The flag is REPEATABLE, because the caller asks the remote once per
        distinct reference and more than one answer can come back taken. Both specs
        skipped, what is left is the items that never belonged to one."""
        self.seed_the_measured_queue()
        out = self.run_tk("pack", "--spec-under-way", "ambiente#171",
                          "--spec-under-way", "ambiente#144").stdout
        self.assertEqual(self.lanes(out),
                         {"T009": "avulso", "T010": "avulso (ambiente#159)"})
        for label in ("T007", "T008", "T021", "T022"):
            self.assertIn("declarada em curso", self.reason(out, label))

    # --- the value is gated exactly as `--spec` is ------------------------
    def test_a_malformed_value_is_refused_the_way_spec_refuses_one(self):
        """Same gate, same message, and a refusal rather than a warning: a value
        that matched nothing would silently elect the very spec the caller called a
        second time to skip — the blindness back, wearing a typo."""
        self.seed_the_measured_queue()
        for bad in ("nao-e-ref", "ambiente#", "#171", "ambiente#171 solto", ""):
            with self.subTest(value=bad):
                r = self.run_tk("pack", "--spec-under-way", bad)
                self.assertEqual(r.returncode, 1, r.stdout)
                self.assertIn("is not a forge reference", r.stderr)
                self.assertEqual(r.stdout, "")

    def test_the_value_is_read_in_the_ONE_canonical_spelling(self):
        """`Ambiente#0171` and `ambiente#171` are one reference, and the queue only
        ever stores the second. Comparing the flag raw would answer "no such spec"
        to a caller who copied the reference out of a tracker that title-cases it."""
        self.seed_the_measured_queue()
        self.assertEqual(self.run_tk("pack", "--spec-under-way", "Ambiente#0171").stdout,
                         self.run_tk("pack", "--spec-under-way", "ambiente#171").stdout)

    def test_the_flag_is_documented_in_the_help_the_skill_reads(self):
        """The output's shape is documented because a skill's prose parses it; the
        flag that changes which lane is elected is documented for the same reason —
        the orchestrator learns the second call exists from here."""
        r = self.run_tk("pack", "--help")
        self.assertIn("--spec-under-way", r.stdout)
        self.assertIn("declarada em curso", r.stdout)


# --- T271: the ticket the caller found blocked on the tracker ---------------

class TestPackBlockedTicket(PackOutput):
    """The floor counts ITEMS, and it counted them blind to the forge. A spec
    whose second ticket is blocked on the tracker won the accumulated lane on the
    strength of a ticket nobody could start, and the package ran a whole branch,
    campaign and tail for the one item that was actually ready.

    `pack` opens no network connection, so the fact arrives the way
    `--spec-under-way` arrives: the caller runs `pack`, asks the remote about the
    tickets the report names, and runs it a second time carrying the answer."""

    def packed(self, *flags):
        r = self.run_tk("pack", *flags)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("Traceback", r.stderr)
        return r.stdout

    # --- the flag does its work -------------------------------------------
    def test_the_named_ticket_leaves_the_package_with_the_reason(self):
        """The reason names the VALUE and the FLAG, like the lane rung above it:
        the caller supplied this fact, and a reason that did not say so would read
        as something the queue holds and the reader could go and fix."""
        self.seed(ticket_item(1, "um", ticket="repo#10")
                  + ticket_item(2, "dois", ticket="repo#11"))
        out = self.packed("--blocked", "repo#10")
        self.assertEqual(self.eligible(out), ["T002"])
        self.assertEqual(self.reason(out, "T001"),
                         "ticket repo#10 is blocked on the forge; declared by --blocked")

    def test_the_blocked_ticket_leaves_its_specs_COUNT_too(self):
        """The half the exclusion alone does not buy, and the whole reason the
        flag exists. #171 has two tickets and one of them is blocked, so it is a
        spec with ONE candidate: under the floor, holding no lane, and #180 — two
        tickets, both ready — takes the accumulated branch instead."""
        self.seed(ticket_item(1, "um", spec="repo#171", ticket="repo#10")
                  + ticket_item(2, "dois", spec="repo#171", ticket="repo#11")
                  + ticket_item(3, "tres", spec="repo#180", ticket="repo#12")
                  + ticket_item(4, "quatro", spec="repo#180", ticket="repo#13"))
        # blind to the block, #171 wins the tie on queue order and #180 leaves
        self.assertEqual(self.lanes(self.packed()),
                         {"T001": "spec repo#171", "T002": "spec repo#171"})
        out = self.packed("--blocked", "repo#10")
        self.assertEqual(self.lanes(out), {"T002": "avulso (repo#171)",
                                           "T003": "spec repo#180",
                                           "T004": "spec repo#180"})
        self.assertEqual(self.blocks(out)["excluded"],
                         ["T001  um  — ticket repo#10 is blocked on the forge; "
                          "declared by --blocked"])

    def test_the_flag_repeats(self):
        """One call carries every ticket the caller found blocked. Keeping only
        the last would dispatch the others, and the second call exists precisely
        because there is more than one answer to bring back."""
        self.seed(ticket_item(1, "um", ticket="repo#10")
                  + ticket_item(2, "dois", ticket="repo#11")
                  + ticket_item(3, "tres", ticket="repo#12"))
        out = self.packed("--blocked", "repo#10", "--blocked", "repo#11")
        self.assertEqual(self.eligible(out), ["T003"])

    # --- the value is gated exactly as `--spec-under-way` is ---------------
    def test_a_malformed_value_is_refused_the_way_spec_refuses_one(self):
        """A refusal, never a warning: a value matching nothing would dispatch the
        very ticket the caller called a second time to take out."""
        self.seed(ticket_item(1, "um", ticket="repo#10"))
        for bad in ("nao-e-ref", "repo#", "#10", "repo#10 solto", ""):
            with self.subTest(value=bad):
                r = self.run_tk("pack", "--blocked", bad)
                self.assertEqual(r.returncode, 1, r.stdout)
                self.assertIn("is not a forge reference", r.stderr)
                self.assertEqual(r.stdout, "")

    def test_the_value_is_read_in_the_ONE_canonical_spelling(self):
        """`Repo#0010` and `repo#10` are one reference. Comparing the flag raw
        would answer "no such ticket" to a caller who copied it out of a tracker
        that title-cases the repository."""
        self.seed(ticket_item(1, "um", ticket="repo#10") + ticket_item(2, "dois"))
        self.assertEqual(self.packed("--blocked", "Repo#0010"),
                         self.packed("--blocked", "repo#10"))
        self.assertEqual(self.eligible(self.packed("--blocked", "Repo#0010")), ["T002"])

    # --- and where it may NOT bite ----------------------------------------
    def test_a_ticket_the_position_rule_cannot_read_is_not_excluded(self):
        """Ticket decides no lane, so an unreadable one may not cost the item its
        place — the split the two provenance fields take, and the one
        `pack_closes` takes for this same value when it prints `[?]`. It matches
        no reference either way, so no flag can reach it."""
        self.seed(ticket_item(1, "um", ticket="repo#10").replace(
            "**Ticket:** repo#10.", "**Ticket:** repo#10. **Ticket:** repo#11.", 1))
        out = self.packed("--blocked", "repo#10")
        self.assertEqual(self.eligible(out), ["T001"])
        self.assertIn("[?]", self.blocks(out)["eligible"][0])

    def test_the_run_with_no_flag_is_what_it_has_always_been(self):
        """A flag whose default path rewrites a column silently rewrites what
        every skill parsing this output reads."""
        self.seed(ticket_item(1, "um", ticket="repo#10")
                  + ticket_item(2, "dois", ticket="repo#11"))
        self.assertEqual(self.eligible(self.packed()), ["T001", "T002"])
        self.assertEqual(self.blocks(self.packed())["excluded"], [])

    def test_the_flag_is_documented_in_the_help_the_skill_reads(self):
        r = self.run_tk("pack", "--help")
        self.assertIn("--blocked", r.stdout)
        self.assertIn("MOST tickets", r.stdout)


# --- T198: the repository the item's code LANDS in -------------------------

class TestRepoField(QueueTest):
    """`Ticket:` and `Spec:` name the TRACKER, and the tracker is routinely a
    different repository from the one the work lands in. Two consumers already
    need that second address — the open-branch check of AFK.md step 1 and the
    worktree of step 3 — and both guessed it from outside the queue. `--repo`
    is the field that carries it.

    The VALUE is a URL or an absolute path, and never a remote NAME: `origin`
    resolves against the cwd, the orchestrator's cwd is the queue's directory,
    which is routinely a clone of something else, and `git ls-remote origin`
    run from there was measured exiting 0 with no output — a clean false
    negative that reads exactly like "no branch". A relative path fails the
    same way, for the same reason, which is why neither shape is accepted."""

    def add(self, *extra, text="importado"):
        return self.run_tk("add", text, "--class", "AUTONOMOUS", "--effort", "S",
                           "--criterion", "A: x", *extra)

    def test_the_field_is_written_at_the_writers_position(self):
        """In the chain, after **Class:**, and after the two provenance fields it
        stands beside — the only position the gates read a field at. Written
        anywhere else the value is there and no reader may use it, which is worse
        than absent: absent is visible."""
        self.seed()
        r = self.add("--ticket", "ambiente#198",
                     "--spec", "ambiente#171",
                     "--repo", "https://github.com/Tarcisio-Abbud/claude-skills.git")
        self.assertEqual(r.returncode, 0, r.stderr)
        # up to **Born:**, which compose_item stamps between this field and Source
        self.assertIn("**Ticket:** ambiente#198. "
                      "**Spec:** ambiente#171. "
                      "**Repo:** https://github.com/Tarcisio-Abbud/claude-skills.git. "
                      "**Born:**", self.body())

    def test_the_value_round_trips_byte_for_byte(self):
        """Through the readers that exist: `pack` prints the value and writes
        nothing, `list` shows the item and writes nothing, and the file still
        carries the address character for character. A reader that rewrote what it
        read is the defect no assertion on its OUTPUT would show — and this value
        is one a URL-normaliser would be tempted to touch."""
        self.seed()
        self.assertEqual(self.add("--repo", "git@github.com:Tarcisio-Abbud/claude-skills.git")
                         .returncode, 0)
        before = self.body()
        listed = self.run_tk("list")
        self.assertEqual(listed.returncode, 0)
        # `list` carries no provenance column — not for Ticket, not for Spec, and
        # so not for this one either: it shows the item and writes nothing. The
        # assertion is here because the omission is a DECISION, and an undocumented
        # decision is one a later reader restores by accident
        self.assertNotIn("github.com", listed.stdout)
        out = self.run_tk("pack")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(self.body(), before)
        self.assertIn("**Repo:** git@github.com:Tarcisio-Abbud/claude-skills.git.", before)
        self.assertIn("[repo: git@github.com:Tarcisio-Abbud/claude-skills.git]", out.stdout)

    def test_an_add_without_the_flag_writes_the_item_of_today(self):
        """The whole file, byte for byte, against the same add on the version
        before the flag existed. One new optional field is the cheapest place to
        change the shape of EVERY item by accident."""
        self.seed()
        self.assertEqual(self.add(text="sem repo").returncode, 0)
        today = datetime.date.today().isoformat()
        self.assertEqual(self.body(),
                         HEADER + "- [ ] **T001** — sem repo **Class:** AUTONOMOUS. "
                         "**Effort:** S. **Criterion:** A: x. "
                         f"**Born:** {today}. **Source:** {today}\n")

    def test_a_remote_name_or_a_cwd_relative_path_is_refused(self):
        """The refusal is the whole point of the field: a value the orchestrator
        would have to resolve against a cwd answers "free" from the wrong
        repository and says nothing. `-origin` is NOT in this list and may not be:
        argparse takes any value starting with `-` as an unknown option and
        refuses it before the guard runs."""
        # the trailing '.' is in this list for a reason of its own: compose_item
        # writes `**Repo:** <value>.` and field_value strips ONE trailing period, so
        # a value ending in one would come back a character short of what was
        # written — an address silently corrupted on the field whose whole job is to
        # be handed to git
        for junk in ("origin", "upstream", "repo", "claude-skills", "../claude-skills",
                     "./tk", "workspace/projects", "~claude-skills", "", "none",
                     "https://", "git@github.com", "https://exa mple.com/r",
                     "/x\ny", "/pa*th", "https://x/**Spec:**y", "**Repo:** /x",
                     "/srv/repo.", "https://github.com/o/r.git.", "/root/.claude/skills.",
                     # `~/` is HOME-relative, so it names a different repository to
                     # a different reader — the defect `origin` has, in a path's
                     # clothes. And the two consumers disagree: `git ls-remote`
                     # expands the tilde and answers, `git -C "~/x"` cannot chdir
                     "~/.claude/skills", "~/x", "~/",
                     # a `.` or `..` SEGMENT is a second spelling of one address,
                     # and the gate cannot canonicalise — so it refuses instead
                     "/a/./b", "/a/../b", "/a/..", "/a/.",
                     "C:\\a\\.\\b", "C:\\a\\..\\b",
                     "file:///a/./b", "https://github.com/o/./r",
                     # `file://` names an authority, so the path starts at the
                     # THIRD slash: with two, the address is relative again
                     "file://srv/r.git", "file://../r",
                     # a trailing SEPARATOR is the same two spellings of one
                     # repository the dot-segment rule refuses. The URL branches
                     # refuse it by their segments being non-empty; a local path
                     # is one character class with `/` in it, so the closing
                     # lookbehind is what refuses it there
                     "/srv/foo/bar/", "file:///srv/r.git/", "C:\\a\\b\\",
                     # scp-like syntax has no port in EITHER spelling: measured
                     # under GIT_TRACE, git keeps the default port and asks for
                     # the path `2222/owner/repo.git`
                     "git@myserver:2222/owner/repo.git",
                     # a browser copies the trailing slash; the segments must be
                     # non-empty, so the message names the shape to write instead
                     "https://github.com/o/r/",
                     # scp-like syntax has NO port field: git keeps the default
                     # port and folds `2222` into the path (measured on GIT_TRACE)
                     "git@myserver:2222:owner/repo.git",
                     # a BRACKET is the other splice, and the one measured on the
                     # field beside this one: `**Ticket:** repo#1] injetado` put a
                     # second bracket group and free text into the line `pack`
                     # composes, whose consumer is a skill's prose
                     "/srv/repo]injetado", "/x[repo:/y]", "https://h/p]q",
                     # a drive letter or a slash and nothing after it is not an
                     # address; `/` was already refused, and `C:/` may not differ
                     "/", "C:/", "C:\\",
                     # a password in a URL: this file has no other copy and `pack`
                     # reprints the value on every package
                     "https://user:token@host/r.git", "git:secret@github.com:o/r.git",
                     "ssh://u:p@h/r.git",
                     # a direction override reorders what the reader sees without
                     # changing what git receives
                     "https://github.com/o/\u202egit.repo", "/srv/\u2066repo",
                     # the scp-like shape's own delimiters: a second `@`, a `:` in
                     # the host, a `/` before the colon, and an empty half
                     "us@er@host:path", "git@ho/st:path",
                     "@host:path", "git@:path", "git@host:",
                     # and the excluded characters INSIDE that shape, which no
                     # other junk value here reaches
                     "git@host:pa*th", "git@host:p]q", "git@ho*st:path",
                     # the whitelist refuses these without a rule naming any of
                     # them, which is the whole reason it is a whitelist: an
                     # encoding of a refused character, a userinfo that is not the
                     # protocol's own `git@`, an invisible character, and a host
                     # this account does not address a repository by
                     "https://user%3Atoken@host/r.git", "https://user%3Apass%40host/r.git",
                     "https://ghp_ABCDEF1234567890@github.com/o/r.git",
                     "ssh://root@github.com/o/r.git", "https://h/a%20b/r.git",
                     "https://github.com/o/r\u200b.git", "/srv/\u2060repo",
                     "https://[::1]/r.git", "https://github.com", "ssh://git@github.com",
                     "git@host:st:path"):
            with self.subTest(junk=junk):
                self.seed()
                r = self.add("--repo", junk)
                self.assertNotEqual(r.returncode, 0, f"--repo {junk!r} was accepted")
                self.assertNotIn("- [ ] ", self.body(), "the item was written anyway")

    def test_a_value_reaching_the_guard_as_an_OPTION_is_refused(self):
        """`--repo=<value>` is the one spelling that carries a leading `-` PAST
        argparse, and it is the spelling the attack used. The junk list above
        cannot hold these: argparse takes a bare `-…` as an unknown option and
        refuses it before `validate_repo` runs, so a test written that way passes
        with the guard deleted — measured, as a surviving mutant.

        What the guard is for is not the queue at all. The value is pasted into
        `git ls-remote --heads "<address>"`, and a token starting with `-` is an
        OPTION there whether it is quoted or not. Measured on git 2.39.5, in a
        clone with an `origin` configured — the reader's ordinary state:
        `git ls-remote --heads '--upload-pack=<cmd>@host:path'` read it as the
        option, fell back to that origin, and EXECUTED <cmd>."""
        for junk in ("--upload-pack=touch_pwn@host:path", "-oProxyCommand=x@h:p",
                     "-/srv/r", "--/srv/r", "-https://github.com/o/r.git"):
            with self.subTest(junk=junk):
                self.seed()
                r = self.add(f"--repo={junk}")
                self.assertNotEqual(r.returncode, 0, f"--repo={junk!r} was accepted")
                self.assertNotIn("- [ ] ", self.body(), "the item was written anyway")
                self.assertIn("--repo", r.stderr, "refused, but not by the field's own gate")

    def test_the_shapes_that_actually_occur_are_accepted(self):
        for value in ("https://github.com/Tarcisio-Abbud/claude-skills.git",
                      "https://github.com/Tarcisio-Abbud/claude-skills",
                      "http://gitea.lan:3000/t/r.git",
                      "ssh://git@github.com/Tarcisio-Abbud/claude-skills.git",
                      "git@github.com:Tarcisio-Abbud/claude-skills.git",
                      "file:///srv/git/claude-skills.git",
                      "/srv/projects/config", "/root/.claude/skills",
                      "C:/Users/dev/config", "C:\\Users\\dev\\config",
                      # a user with NO password is the ordinary git address, and a
                      # port after it is legal: it is the COLON BEFORE the `@` that
                      # makes a secret, and only that is refused
                      "ssh://git@github.com/o/r.git", "ssh://git@github.com:22/o/r.git",
                      "http://gitea.lan:3000/t/r.git",
                      # a non-ASCII path is not refused: banning it would refuse the
                      # accented paths this machine really has (see REPO_BAD)
                      "/srv/projects/projeção",
                      # a LOCAL path may carry a colon: the first `/` comes before
                      # it, so git reads a path and not an scp-like `host:path`
                      "/srv/repo:v2", "git@host:/srv/r.git",
                      # only an ALL-digit first segment reads as a port; a real
                      # path may still begin with a digit
                      "git@host:2222x/o/r.git", "git@host:2fa/o/r.git"):
            with self.subTest(value=value):
                self.seed()
                r = self.add("--repo", value)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertIn(f"**Repo:** {value}.", self.body())

    def test_a_value_past_the_field_ceiling_is_refused(self):
        """The shape bounds the CHARACTERS a path may hold and not how many of
        them: unlike a forge reference, a path has no length the world gives it,
        so the ceiling every other prose field answers to is the bound here too."""
        self.seed()
        ceiling = load_tk().FIELD_CEILING
        self.assertEqual(self.add("--repo", "/" + "a" * (ceiling - 1)).returncode, 0)
        self.seed()
        r = self.add("--repo", "/" + "a" * ceiling)
        self.assertNotEqual(r.returncode, 0, "a value past the field ceiling was accepted")
        self.assertNotIn("- [ ] ", self.body())

    def test_the_flag_is_independent_of_the_provenance_pair(self):
        """An item born in conversation lands in a repository too, and a ticket
        imported from a tracker may have no address recorded yet: coupling the
        three would refuse a real case to enforce a rule nothing needs."""
        self.seed()
        self.assertEqual(self.add("--repo", "/srv/projects/config").returncode, 0)
        body = self.body()
        self.assertIn("**Repo:** /srv/projects/config.", body)
        self.assertNotIn("**Ticket:**", body)
        self.assertNotIn("**Spec:**", body)


class TestPackRepo(PackOutput):
    """The package is dispatched from this output, so the address is returned by
    it: a field nothing prints is the prose it was added to replace. It is
    APPENDED and LABELLED, beside the ticket rather than in a column of its own,
    because almost no item carries either and a bare second bracket would be told
    from the ticket's only by its shape."""

    def test_the_repo_of_an_eligible_item_comes_back(self):
        self.seed(ticket_item(1, "um", repo="https://github.com/o/r.git"))
        self.assertEqual(self.repos(self.pack()),
                         {"T001": "https://github.com/o/r.git"})

    def test_an_item_with_no_repo_prints_the_line_of_today(self):
        """The overwhelming majority of items. An empty group would read as an
        address that was looked for and not found."""
        self.seed(item(1, "um"))
        self.assertEqual(self.blocks(self.pack())["eligible"],
                         ["T001  S             avulso                um"])

    def test_the_repo_follows_the_ticket_on_the_line(self):
        """The order is the stable half of the shape: a skill's prose reads this
        line, and two appended groups that swap places are two shapes."""
        self.seed(ticket_item(1, "um", ticket="repo#1", repo="/srv/r"))
        line, = self.blocks(self.pack())["eligible"]
        self.assertTrue(line.endswith("um  [repo#1]  [repo: /srv/r]"), line)

    def test_a_marker_QUOTED_IN_PROSE_is_not_read_as_the_repo(self):
        """The position rule, the same one every other field is read through: an
        item that never had an address must not come back carrying one from its
        own prose."""
        self.seed("- [ ] **T001** — a nota cita **Repo:** /outro/lugar em prosa — um "
                  "**Class:** AUTONOMOUS. **Effort:** S. **Criterion:** A: x. "
                  "**Source:** 2026-08-13\n")
        self.assertEqual(self.repos(self.pack()), {})

    def test_two_Repo_fields_in_the_chain_are_MARKED_and_never_guessed(self):
        """Two addresses say two things, so the chain says nothing this reader may
        pick between — and silence would make it identical to an item that never
        had one. Those are not the same thing to whoever opens the worktree: one
        needs no address, the other needs the one it cannot have."""
        self.seed(ticket_item(1, "um", repo="/srv/a").replace(
            "**Repo:** /srv/a.", "**Repo:** /srv/a. **Repo:** /srv/b.", 1))
        self.assertEqual(self.repos(self.pack()), {"T001": "?"})

    def test_a_value_no_reader_may_use_is_MARKED_too(self):
        """A hand edit is not the writer, so the shape is asked again on the way
        out — `origin` in the file is the very guess the field exists to end."""
        self.seed(ticket_item(1, "um", repo="origin"))
        self.assertEqual(self.repos(self.pack()), {"T001": "?"})

    def test_an_unreadable_repo_does_not_EXCLUDE_the_item(self):
        """Absent has a safe default here — the orchestrator names the repository
        from outside, as it did before this field existed — so the answer to a
        value this reader may not use is a mark, not the item's place in the
        package. That is where Repo parts from Risk and Env, whose absence means
        unknown danger."""
        self.seed(ticket_item(1, "um", repo="origin"))
        self.assertEqual(self.eligible(), ["T001"])

    def test_the_repo_decides_no_lane(self):
        """Two addresses for one spec are still one lane, and one address across
        two specs is still two: the lane is read from **Spec:** alone. Coupling
        them would put the branch's name in the hands of a field that does not
        name the tracker."""
        self.seed(ticket_item(1, "um", spec="repo#171", repo="/srv/a")
                  + ticket_item(2, "dois", spec="repo#171", repo="/srv/b"))
        lanes = self.lanes(self.pack())
        self.assertEqual(lanes, {"T001": "spec repo#171", "T002": "spec repo#171"})


# --- handoff: the briefing that lives and dies with the item ---------------

TK_MOD = load_tk()
HANDOFF_SAMPLE = TK_MOD.HANDOFF_SAMPLE


class HandoffTest(QueueTest):
    def handoff(self, iid, *argv):
        return self.run_tk("handoff", str(iid), *argv)

    def brief(self, iid):
        """The briefing file, or None. Read WHOLE — `assertNotIn` passes on a
        corrupted file, and this file is prose another session acts on."""
        path = os.path.join(self.mem, f"handoff-T{iid:03d}.md")
        if not os.path.exists(path):
            return None
        with open(path, encoding="utf-8") as f:
            return f.read()

    def today(self):
        return datetime.date.today().isoformat()


class TestHandoffCreation(HandoffTest):
    """Fields 1-3 are the contract; the gate is asked of the file that WOULD be
    written, never of the flags that compose it."""

    def test_the_documented_sample_is_what_the_command_actually_writes(self):
        """The format is read by another session's prose, so it is documented in
        --help. A documented shape nothing executes is the one that goes stale:
        this runs the invocation the help prints and compares the WHOLE file,
        character for character, against the constant the help embeds."""
        self.seed(item(7, "the item's text"))
        r = self.handoff(7, "--objective", "ship the parser",
                         "--state", "grammar merged in PR #12", "--blockers", "none")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.brief(7), HANDOFF_SAMPLE)

    def test_the_help_embeds_that_same_sample(self):
        """The sample lives in one place. A second copy in the epilog is a copy
        that drifts, and the drift is invisible to a reader who trusts the help."""
        r = self.run_tk("handoff", "--help")
        self.assertIn(HANDOFF_SAMPLE, r.stdout)

    def test_all_five_fields_write_all_five_sections(self):
        self.seed(item(3, "um"))
        self.handoff(3, "--objective", "o", "--state", "s", "--blockers", "b",
                     "--skills", "/tdd", "--pitfalls", "the cwd moves")
        self.assertEqual(self.brief(3),
                         "# Handoff T003 — um\n"
                         "\n## Objective\n\no\n"
                         "\n## State\n\ns\n"
                         "\n## Blockers and notes\n\nb\n"
                         "\n## Suggested skills\n\n/tdd\n"
                         "\n## Known pitfalls\n\nthe cwd moves\n")

    def test_an_absent_optional_field_writes_no_section_at_all(self):
        """An empty heading is a claim — "nothing known here" — and it is not the
        claim an omitted field makes."""
        self.seed(item(3, "um"))
        self.handoff(3, "--objective", "o", "--state", "s", "--blockers", "b",
                     "--pitfalls", "p")
        self.assertEqual(self.brief(3),
                         "# Handoff T003 — um\n"
                         "\n## Objective\n\no\n"
                         "\n## State\n\ns\n"
                         "\n## Blockers and notes\n\nb\n"
                         "\n## Known pitfalls\n\np\n")

    def test_writing_it_again_overwrites_and_never_accumulates(self):
        """Naming by ID is what makes a re-wrap-up idempotent. The whole file is
        asserted: a briefing appended to instead of replaced still contains the
        new text, and every substring check would pass on it."""
        self.seed(item(3, "um"))
        self.handoff(3, "--objective", "old", "--state", "s", "--blockers", "b")
        r = self.handoff(3, "--objective", "new", "--state", "s", "--blockers", "b")
        self.assertIn("rewrote ", r.stdout)
        self.assertEqual(self.brief(3),
                         "# Handoff T003 — um\n"
                         "\n## Objective\n\nnew\n"
                         "\n## State\n\ns\n"
                         "\n## Blockers and notes\n\nb\n")

    def test_a_mandatory_field_with_no_text_is_refused_and_the_remedy_runs(self):
        """argparse's `required` stops an ABSENT flag, never an empty one: the
        empty string reaches the writer and composes a field nobody filled. The
        remedy the refusal prints is then RUN — a remedy nothing executes is a
        remedy nobody has checked."""
        self.seed(item(3, "um"))
        r = self.handoff(3, "--objective", "o", "--state", "", "--blockers", "b")
        self.assertEqual(r.returncode, 1)
        self.assertIn('--state "none"', r.stderr)
        self.assertIsNone(self.brief(3))
        ok = self.handoff(3, "--objective", "o", "--state", "none", "--blockers", "b")
        self.assertEqual(ok.returncode, 0, ok.stderr)
        self.assertIn("\n## State\n\nnone\n", self.brief(3))

    def test_the_blockers_field_is_mandatory_too(self):
        """The one field the contract singles out as unskippable: an obstacle the
        last session already knew is the thing the next one pays to rediscover."""
        self.seed(item(3, "um"))
        r = self.handoff(3, "--objective", "o", "--state", "s", "--blockers", "")
        self.assertEqual(r.returncode, 1)
        self.assertIn('--blockers "none"', r.stderr)
        self.assertIsNone(self.brief(3))

    def test_a_heading_inside_a_value_is_refused_and_the_remedy_runs(self):
        """The gate reads the COMPOSED file, not the flags: a --state whose second
        line is `## Blockers and notes` passes every per-flag check and writes a
        file whose reader finds the third field nested in the second."""
        self.seed(item(3, "um"))
        r = self.handoff(3, "--objective", "o",
                         "--state", "done\n## Blockers and notes\nfake", "--blockers", "real")
        self.assertEqual(r.returncode, 1)
        self.assertIn("does not read back", r.stderr)
        self.assertIsNone(self.brief(3))
        ok = self.handoff(3, "--objective", "o",
                          "--state", "done\n### Blockers and notes\nfake", "--blockers", "real")
        self.assertEqual(ok.returncode, 0, ok.stderr)
        self.assertEqual(ok.stderr.count("does not read back"), 0)

    def test_a_level_one_heading_inside_a_value_is_refused_too(self):
        """`# ` frames the file the same way `## ` frames the fields. The injected
        heading carries a body on purpose: an empty one would be refused by the
        blank-field rule instead, and the test would pass without the rule it is
        about ever running."""
        self.seed(item(3, "um"))
        r = self.handoff(3, "--objective", "o",
                         "--state", "a\n# Handoff T003 — other\nbody under it",
                         "--blockers", "b")
        self.assertEqual(r.returncode, 1)
        self.assertIn("does not read back", r.stderr)
        self.assertIsNone(self.brief(3))

    def test_a_deeper_heading_is_sub_structure_and_passes(self):
        self.seed(item(3, "um"))
        r = self.handoff(3, "--objective", "o", "--state", "a\n### Files\nb", "--blockers", "b")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("\n### Files\n", self.brief(3))

    def test_the_remedy_never_truncates_the_item_it_rewrites(self):
        """`edit --text` REPLACES the text. A remedy that prints an abbreviated
        copy of it runs, reports success, and eats the item — the one failure mode
        a remedy has that is worse than being refused."""
        long_text = "palavra " * 90
        self.seed(item(4, long_text.strip()))
        r = self.handoff(4, "--objective", "o", "--state", "s", "--blockers", "b")
        m = re.search(r"`tk-queue (edit .*?)`\.", r.stderr, re.S)
        argv = __import__("shlex").split(m.group(1))
        text = argv[argv.index("--text") + 1]
        self.assertNotIn("…", text)
        # the item crosses the block ceiling, so the remedy has to carry --force
        # ITSELF — a flag the test adds is a flag nobody proved the command prints
        self.assertIn("--force", argv)
        fix = self.run_tk(*argv)          # verbatim
        self.assertEqual(fix.returncode, 0, fix.stderr)
        self.assertIn(long_text.strip() + " [[handoff-T004]]", self.body("next-steps.md"))

    def test_TWO_empty_fields_still_print_ONE_runnable_remedy(self):
        """`--objective, --state "none"` reads as a list and argparse refuses it for
        the very flag it names. The remedy is a command, so it is run as one."""
        self.seed(item(3, "um"))
        r = self.handoff(3, "--objective", "", "--state", "", "--blockers", "b")
        self.assertEqual(r.returncode, 1)
        m = re.search(r"spelling the empty answer out: (.*?)\. Nothing", r.stderr, re.S)
        argv = __import__("shlex").split(m.group(1))
        ok = self.handoff(3, *argv, "--blockers", "b")
        self.assertEqual(ok.returncode, 0, ok.stderr)
        self.assertIn("\n## Objective\n\nnone\n\n## State\n\nnone\n", self.brief(3))

    def test_writing_over_a_file_this_command_did_not_write_is_refused(self):
        """The write side of the same rule: overwriting a stranger's file that merely
        shares the name is the same loss as deleting it. The remedy is run."""
        self.seed(item(1, "um"))
        stranger = "uma nota qualquer que se chama assim por acaso\n"
        self.write("handoff-T001.md", stranger)
        r = self.handoff(1, "--objective", "o", "--state", "s", "--blockers", "b")
        self.assertEqual(r.returncode, 1)
        self.assertIn("--force", r.stderr)
        self.assertEqual(self.brief(1), stranger)
        ok = self.handoff(1, "--objective", "o", "--state", "s", "--blockers", "b", "--force")
        self.assertEqual(ok.returncode, 0, ok.stderr)
        self.assertEqual(self.brief(1),
                         "# Handoff T001 — um\n\n## Objective\n\no\n"
                         "\n## State\n\ns\n\n## Blockers and notes\n\nb\n")

    def test_rewriting_OUR_own_briefing_needs_no_force(self):
        self.seed(item(1, "um"))
        self.handoff(1, "--objective", "old", "--state", "s", "--blockers", "b")
        r = self.handoff(1, "--objective", "new", "--state", "s", "--blockers", "b")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("rewrote ", r.stdout)

    def test_TWO_empty_fields_read_as_a_plural(self):
        """Prose an agent reads. `--objective, --state carries no text` is the shape
        that tells a reader the sentence was assembled, not written."""
        self.seed(item(3, "um"))
        two = self.handoff(3, "--objective", "", "--state", "", "--blockers", "b")
        self.assertIn("--objective, --state carry no text", two.stderr)
        one = self.handoff(3, "--objective", "", "--state", "s", "--blockers", "b")
        self.assertIn("--objective carries no text", one.stderr)

    def test_an_item_that_is_not_open_gets_no_briefing(self):
        """A briefing for an item no close will ever reach is an orphan at birth."""
        self.seed(item(1, "um"))
        self.run_tk("done", "1", "--how", "PR #1")
        r = self.handoff(1, "--objective", "o", "--state", "s", "--blockers", "b")
        self.assertEqual(r.returncode, 1)
        self.assertIn("already left the queue", r.stderr)
        self.assertIsNone(self.brief(1))

    def test_the_missing_pointer_warning_names_a_remedy_that_runs(self):
        """The item is the briefing's only discovery path — and the only thing a
        close reads to know a sibling still needs it. The printed `edit` is run
        verbatim, and the warning must then be gone."""
        # the text carries both quote characters on purpose: the remedy is a
        # command line, and one printed unquoted is split by the shell somewhere
        # its author never looked
        self.seed(item(4, """um item com "aspas" e o 'outro' tipo"""))
        r = self.handoff(4, "--objective", "o", "--state", "s", "--blockers", "b")
        self.assertIn("does not point at [[handoff-T004]]", r.stderr)
        m = re.search(r"`tk-queue (edit .*?)`\.", r.stderr, re.S)
        argv = __import__("shlex").split(m.group(1))
        fix = self.run_tk(*argv)
        self.assertEqual(fix.returncode, 0, fix.stderr)
        self.assertIn("""um item com "aspas" e o 'outro' tipo [[handoff-T004]]""",
                      self.body("next-steps.md"))
        again = self.handoff(4, "--objective", "o", "--state", "s", "--blockers", "b")
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertNotIn("does not point at", again.stderr)


class TestHandoffLifecycle(HandoffTest):
    """No path through this CLI leaves a briefing nothing reaches."""

    def seed_brief(self, iid, text="um"):
        self.handoff(iid, "--objective", "o", "--state", "s", "--blockers", "b")

    def test_done_removes_the_briefing_in_the_same_command(self):
        self.seed(item(1, "um [[handoff-T001]]"))
        self.seed_brief(1)
        r = self.run_tk("done", "1", "--how", "PR #1")
        self.assertEqual(r.stdout,
                         f"T001 → done-log as FEITO ({self.today()})\n"
                         "handoff-T001.md removed\n")
        self.assertIsNone(self.brief(1))

    def test_cancel_removes_it_too(self):
        self.seed(item(1, "um"))
        self.seed_brief(1)
        r = self.run_tk("cancel", "1", "--why", "obsoleto")
        self.assertEqual(r.stdout,
                         f"T001 → done-log as DESCARTADO ({self.today()})\n"
                         "handoff-T001.md removed\n")
        self.assertIsNone(self.brief(1))

    def test_an_item_without_a_briefing_closes_exactly_as_before(self):
        self.seed(item(1, "um"))
        r = self.run_tk("done", "1", "--how", "PR #1")
        self.assertEqual(r.stdout, f"T001 → done-log as FEITO ({self.today()})\n")

    def test_the_briefing_of_another_item_is_never_touched(self):
        """Candidates are bounded by the item being closed. A sweep of the whole
        directory would collect a briefing this close has nothing to do with —
        including one written seconds earlier for an item still to be claimed."""
        self.seed(item(1, "um"), item(2, "dois"))
        self.seed_brief(2)
        self.run_tk("done", "1", "--how", "PR #1")
        self.assertIsNotNone(self.brief(2))

    def test_a_campaign_briefing_outlives_its_anchor_and_dies_with_the_last_item(self):
        """One briefing named for the anchor, pointed at by every item of the
        campaign. Deleting it when the anchor closes leaves the siblings pointing
        at a file that is gone — the `[x]` that lied, in another file."""
        self.seed(item(5, "anchor [[handoff-T005]]"), item(6, "sibling [[handoff-T005]]"))
        self.seed_brief(5)
        first = self.run_tk("done", "5", "--how", "PR #5")
        self.assertEqual(first.stdout,
                         f"T005 → done-log as FEITO ({self.today()})\n"
                         "handoff-T005.md kept — still reached by T006\n")
        self.assertIsNotNone(self.brief(5))
        last = self.run_tk("done", "6", "--how", "PR #6")
        self.assertEqual(last.stdout,
                         f"T006 → done-log as FEITO ({self.today()})\n"
                         "handoff-T005.md removed\n")
        self.assertIsNone(self.brief(5))

    def test_a_sibling_closing_first_does_not_take_the_briefing(self):
        self.seed(item(5, "anchor [[handoff-T005]]"), item(6, "sibling [[handoff-T005]]"))
        self.seed_brief(5)
        r = self.run_tk("done", "6", "--how", "PR #6")
        self.assertEqual(r.stdout,
                         f"T006 → done-log as FEITO ({self.today()})\n"
                         "handoff-T005.md kept — still reached by T005\n")
        self.assertIsNotNone(self.brief(5))
        self.run_tk("done", "5", "--how", "PR #5")
        self.assertIsNone(self.brief(5))

    def test_a_pointer_to_a_briefing_that_was_never_written_closes_cleanly(self):
        """"Cleanly" is the exit code, not the first line of stdout: the close
        prints before it collects, so a crash in the collection leaves that line
        standing and every stdout assertion about it still passes."""
        self.seed(item(1, "um [[handoff-T099]]"))
        r = self.run_tk("done", "1", "--how", "PR #1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("Traceback", r.stderr)
        # and no warning either: since the collection became best-effort, a missing
        # file no longer crashes, so silence on stderr is the only thing left that
        # tells "never a candidate" apart from "tried to remove it and could not"
        self.assertNotIn("was not written by", r.stderr)
        self.assertEqual(r.stdout, f"T001 → done-log as FEITO ({self.today()})\n")

    # --- the other two closing paths ---------------------------------------
    def test_migrate_collects_the_briefing_of_what_it_closes(self):
        """`migrate` moves legacy [x] items to the log — it CLOSES items, so it is
        a closing path, and one that left the briefing behind would be the orphan
        every other path refuses to make."""
        self.seed(item(5, "anchor [[handoff-T005]]"))
        self.seed_brief(5)
        self.write("next-steps.md", self.body().replace("- [ ] **T005**", "- [x] **T005**", 1))
        r = self.run_tk("migrate")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("handoff-T005.md removed\n", r.stdout)
        self.assertIsNone(self.brief(5))

    def test_migrate_keeps_one_an_open_item_still_reaches(self):
        self.seed(item(5, "anchor [[handoff-T005]]"), item(6, "sibling [[handoff-T005]]"))
        self.seed_brief(5)
        self.write("next-steps.md", self.body().replace("- [ ] **T005**", "- [x] **T005**", 1))
        r = self.run_tk("migrate")
        self.assertIn("handoff-T005.md kept — still reached by T006\n", r.stdout)
        self.assertIsNotNone(self.brief(5))

    def test_edit_collects_a_briefing_it_stops_pointing_at(self):
        """The measured hole: the anchor closes (briefing kept for the sibling),
        the sibling's --text is rewritten without the link, the sibling closes —
        and the briefing outlives an EMPTY queue, with nothing left that could ever
        carry the pointer that collects it. An edit that drops the last pointer is
        a closing path in disguise."""
        self.seed(item(5, "anchor [[handoff-T005]]"), item(6, "sibling [[handoff-T005]]"))
        self.seed_brief(5)
        self.run_tk("done", "5", "--how", "PR #5")
        r = self.run_tk("edit", "6", "--text", "sibling sem o ponteiro")
        self.assertEqual(r.stdout, "T006 updated\nhandoff-T005.md removed\n")
        self.assertIsNone(self.brief(5))

    def test_edit_keeps_a_briefing_another_item_still_points_at(self):
        self.seed(item(5, "anchor [[handoff-T005]]"), item(6, "sibling [[handoff-T005]]"),
                  item(7, "outro [[handoff-T005]]"))
        self.seed_brief(5)
        r = self.run_tk("edit", "6", "--text", "sibling sem o ponteiro")
        self.assertEqual(r.stdout,
                         "T006 updated\nhandoff-T005.md kept — still reached by T005, T007\n")
        self.assertIsNotNone(self.brief(5))

    def test_an_edit_that_keeps_the_pointer_collects_nothing(self):
        self.seed(item(5, "anchor [[handoff-T005]]"))
        self.seed_brief(5)
        r = self.run_tk("edit", "5", "--text", "outro texto [[handoff-T005]]")
        self.assertEqual(r.stdout, "T005 updated\n")
        self.assertIsNotNone(self.brief(5))

    def test_a_ref_quoted_in_prose_only_DELAYS_the_collection(self):
        """A `[[handoff-T00N]]` inside another item's prose counts as a pointer —
        the link is prose by contract (there is no writer position to read it at),
        so a quoting item holds the briefing it merely mentions. The tolerance is
        ONE-WAY, which is what makes it safe: it can only make MORE items hold a
        briefing, never fewer, so it delays a collection and can never cause a
        wrong deletion — and the quoting item's own close collects it."""
        self.seed(item(1, "anchor [[handoff-T001]]"),
                  item(2, "documenta o formato: um item aponta com [[handoff-T001]]"))
        self.seed_brief(1)
        first = self.run_tk("done", "1", "--how", "PR #1")
        self.assertIn("handoff-T001.md kept — still reached by T002\n", first.stdout)
        last = self.run_tk("done", "2", "--how", "PR #2")
        self.assertIn("handoff-T001.md removed\n", last.stdout)
        self.assertIsNone(self.brief(1))

    def test_a_link_without_the_writers_zero_padding_still_holds(self):
        """`[[handoff-T1]]` is what a human or a skill's prose writes. Reading only
        the writer's `T001` made it invisible, and the close DELETED a briefing a
        second item still pointed at — the one direction this tolerance may not
        fail in, since a wrong deletion cannot be undone by re-running anything."""
        self.seed(item(1, "anchor [[handoff-T001]]"), item(2, "sibling [[handoff-T1]]"))
        self.seed_brief(1)
        r = self.run_tk("done", "1", "--how", "PR #1")
        self.assertIn("handoff-T001.md kept — still reached by T002\n", r.stdout)
        self.assertIsNotNone(self.brief(1))
        last = self.run_tk("done", "2", "--how", "PR #2")
        self.assertIn("handoff-T001.md removed\n", last.stdout)

    def test_an_UNNUMBERED_open_item_holds_the_briefing_it_points_at(self):
        """An item `migrate` has not numbered yet cannot be closed, claimed or edited
        by ID — but it is OPEN and it points at this briefing. Dropping it from the
        holders was a wrong DELETE, and the crash it hid (`f"T{None:03d}"`) turned an
        already-committed close into a reported failure."""
        self.seed(item(5, "anchor [[handoff-T005]]"),
                  "- [ ] item legado sem ID, cita [[handoff-T005]]\n")
        self.seed_brief(5)
        r = self.run_tk("done", "5", "--how", "PR #5")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("Traceback", r.stderr)
        self.assertEqual(r.stdout,
                         f"T005 → done-log as FEITO ({self.today()})\n"
                         "handoff-T005.md kept — still reached by an unnumbered item\n")
        self.assertIsNotNone(self.brief(5))

    def test_the_OWNER_holds_its_briefing_even_when_it_never_points_at_it(self):
        """The missing pointer is a WARNING, not a refusal, so an owner that ignored
        it never self-cites. Recognising it only by its pointer would delete a
        briefing its own open item still needs when a sibling closes first."""
        self.seed(item(5, "anchor sem ponteiro nenhum"), item(6, "sibling [[handoff-T005]]"))
        self.seed_brief(5)
        r = self.run_tk("done", "6", "--how", "PR #6")
        self.assertEqual(r.stdout,
                         f"T006 → done-log as FEITO ({self.today()})\n"
                         "handoff-T005.md kept — still reached by T005\n")
        self.assertIsNotNone(self.brief(5))

    def test_a_file_this_command_did_not_write_is_never_deleted(self):
        """The name is the contract, but the name is also all `os.remove` needs, and
        a remove is not undone by re-running anything. Measured: a note that happened
        to be called handoff-T001.md, in a memory dir holding dozens of unrelated
        files, was deleted by closing T001."""
        self.seed(item(1, "um"))
        stranger = "uma nota qualquer que se chama assim por acaso\n"
        self.write("handoff-T001.md", stranger)
        r = self.run_tk("done", "1", "--how", "PR #1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("was not written by", r.stderr)
        self.assertNotIn("removed", r.stdout)
        self.assertEqual(self.brief(1), stranger)

    def test_a_briefing_whose_ITEM_was_edited_is_still_ours(self):
        """The header is asked of the ID, never of the item's text — an item edited
        after its briefing was written has a different title, and the briefing this
        command DID write must stay collectable."""
        self.seed(item(1, "texto original"))
        self.seed_brief(1)
        self.run_tk("edit", "1", "--text", "texto completamente outro")
        r = self.run_tk("done", "1", "--how", "PR #1")
        self.assertIn("handoff-T001.md removed\n", r.stdout)
        self.assertIsNone(self.brief(1))

    def test_an_IMPLICIT_deferred_clear_still_collects_the_pointer_it_dropped(self):
        """Leaving DECISION drops the Deferred field without `--deferred` appearing
        in the call. The drop is read from the recomposed BLOCK, not from the flags,
        so a pointer living in that field is collected like any other."""
        self.seed(item(5, "anchor [[handoff-T005]]"), item(6, "sibling", klass="DECISION")
                  .replace("**Class:** DECISION.",
                           "**Class:** DECISION. **Deferred:** afk — [[handoff-T005]].", 1))
        self.seed_brief(5)
        self.run_tk("done", "5", "--how", "PR #5")
        self.assertIsNotNone(self.brief(5))
        r = self.run_tk("edit", "6", "--class", "AUTONOMOUS")
        self.assertEqual(r.stdout, "T006 updated\nhandoff-T005.md removed\n")
        self.assertIsNone(self.brief(5))

    def test_a_DIRECTORY_at_the_briefing_name_does_not_fail_the_close(self):
        """The close's own writes are already committed when the collection runs, so
        dying here reports an APPLIED close as a failure. A directory cannot carry
        the header, so the ownership guard turns it away before `os.remove` ever
        sees it — which is why that remove needs no try/except."""
        self.seed(item(1, "um"))
        path = os.path.join(self.mem, "handoff-T001.md")
        os.makedirs(os.path.join(path, "inside"))
        r = self.run_tk("done", "1", "--how", "PR #1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("Traceback", r.stderr)
        self.assertIn("was not written by", r.stderr)
        self.assertTrue(os.path.isdir(path))
        self.assertNotIn("T001", self.body("next-steps.md"))
        self.assertIn("T001", self.body("done-log.md"))

    def test_a_TICKED_sibling_no_longer_holds_the_briefing_open(self):
        """Holders are read from OPEN items only, and a legacy `[x]` left in
        next-steps.md is the shape that tells the two apart — `done` removes the
        block, so a close alone never produces one. Counting a ticked item as a
        holder keeps the file forever: the orphan this command exists to prevent."""
        self.seed(item(5, "anchor [[handoff-T005]]"),
                  item(6, "sibling [[handoff-T005]]").replace("- [ ]", "- [x]", 1))
        self.seed_brief(5)
        r = self.run_tk("done", "5", "--how", "PR #5")
        self.assertEqual(r.stdout,
                         f"T005 → done-log as FEITO ({self.today()})\n"
                         "handoff-T005.md removed\n")
        self.assertIsNone(self.brief(5))


# --- a BOM at the head of a queue file -----------------------------------

class TestByteOrderMark(QueueTest):
    """A UTF-8 BOM (U+FEFF) surviving at byte 0 is a CHARACTER sitting between
    `^` and the first line, and every reader of these files anchors with `^`
    under re.M. So the first line stops matching — only the first, since `^`
    also matches after every newline.

    The blast radius was MEASURED, and it is narrower than "the queue reads as
    empty": in front of the usual frontmatter the BOM is harmless, because
    nothing is anchored to `---`. It bites when the file's first line is a
    STRUCTURAL one — an item marker in next-steps.md, an entry in done-log.md —
    and then it bites hard: the item vanishes from `list`, `edit` on its ID
    answers "Another writer very likely removed or clobbered it" (a confident
    wrong answer, sending the caller after a writer that never existed), and
    `add` hands its number OUT AGAIN.

    The fixtures below therefore carry NO header. One with the header would pass
    with the defect restored, and prove nothing.
    """

    BOM = "\ufeff"

    def seed_bom(self, *items):
        self.write("next-steps.md", self.BOM + "".join(items))

    def add(self, text="novo"):
        r = self.run_tk("add", text, "--class", "AUTONOMOUS", "--effort", "S",
                        "--criterion", "A: c", "--source", "2026-08-20")
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout.split()[1].rstrip(":")

    def test_the_first_item_is_neither_hidden_nor_blamed_on_a_concurrent_writer(self):
        self.seed_bom(item(1, "um"), item(2, "dois"))
        r = self.run_tk("list")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("T001", r.stdout)
        self.assertIn("T002", r.stdout)
        e = self.run_tk("edit", "T001", "--effort", "M")
        self.assertEqual(e.returncode, 0, e.stderr)
        self.assertNotIn("Another writer", e.stderr)
        # the WHOLE file, never an assertNotIn: `edit` REWRITES it, and a rewrite
        # that dropped the sibling or left the BOM in place passes any absence
        # check. The BOM is gone because write_atomic stays utf-8 — the queue
        # file is normalised by the first command that writes it
        self.assertEqual(self.body(), item(1, "um", effort="M") + item(2, "dois"))

    def test_the_hidden_items_id_is_never_handed_out_twice(self):
        """The sharp end. With the BOM'd item ALONE in the file, `max_id` sees
        nothing and `add` re-issues its number — two open items under one ID,
        which is the outcome the whole ID grammar exists to prevent."""
        self.seed_bom(item(1, "um"))
        self.assertEqual(self.add(), "T002")
        self.assertEqual(re.findall(r"\*\*T([0-9]{3})\*\*", self.body()), ["001", "002"])

    def test_a_bom_in_the_done_log_keeps_its_first_entry_allocated(self):
        """The same read(), the other file. A log whose first line is an entry
        loses that entry: the ID it closed reads as free, so `add` re-issues it,
        and `edit` on it is answered from the wrong branch."""
        self.write("next-steps.md", HEADER)     # only the LOG carries the BOM here
        self.write("done-log.md", self.BOM + "- 2026-08-01 — FEITO — T007 sete — PR #1\n")
        self.assertEqual(self.add(), "T008")
        e = self.run_tk("edit", "T007", "--effort", "L")
        self.assertEqual(e.returncode, 1)
        self.assertIn("already left the queue", e.stderr)
        self.assertNotIn("Another writer", e.stderr)

    def test_a_bom_further_INTO_the_file_is_left_alone(self):
        """utf-8-sig strips ONE BOM at the head and is plain utf-8 everywhere
        else. The inverse fix — stripping every U+FEFF out of the text — would
        silently edit the user's own words, and only this direction can see it."""
        self.seed(item(1, "um\ufeffdois"))
        r = self.run_tk("list")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("um\ufeffdois", r.stdout)
        e = self.run_tk("edit", "T001", "--effort", "M")   # a full rewrite of the file
        self.assertEqual(e.returncode, 0, e.stderr)
        self.assertEqual(self.body(), HEADER + item(1, "um\ufeffdois", effort="M"))


# --- one number, two spellings -------------------------------------------

class TestIdSpelling(QueueTest):
    """`int("0001") == int("001")`, so a label rebuilt from the parsed number
    showed `T001` for BOTH items — the collision reached the DISPLAY, and a
    caller reading `list` could not see that two items existed at all.

    The repair is in the display only, never in the grammar: `T0001` must go on
    counting as an allocated ID. The tolerances of ITEM_ID_RE are deliberately
    one-way (they may make MORE IDs count as taken, never fewer), and a width cap
    that hid `T0001` from the allocator would hand its number out a second time —
    the outcome the whole ID grammar exists to prevent. A cap would also break
    the day IDs legitimately reach four digits: `T0001` is a NON-canonical
    spelling of 1, `T1000` is the canonical spelling of 1000.
    """

    def wide(self, text="item de id largo"):
        """T0001: the same number as T001, spelled a digit wider."""
        return item(1, text).replace("**T001**", "**T0001**", 1)

    def add(self, text="novo"):
        r = self.run_tk("add", text, "--class", "AUTONOMOUS", "--effort", "S",
                        "--criterion", "A: c", "--source", "2026-08-20")
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout.split()[1].rstrip(":")

    def test_list_prints_each_item_under_its_own_spelling(self):
        self.seed(item(1, "item curto"), self.wide())
        r = self.run_tk("list")
        self.assertEqual(r.returncode, 0, r.stderr)
        # the WHOLE listing: the defect printed two identical lines, and any
        # assertIn("T0001") would also pass on a listing that showed T0001 twice.
        # The duplicate mark belongs to the ambiguity these two also are — one
        # number, two items — and is measured by TestAmbiguousId
        # the ID column is as wide as the widest label here, so the class column
        # starts at one position and not two — see TestTheColumnsHoldUnderAWideLabel
        self.assertEqual(r.stdout,
                         "T001   AUTONOMOUS     ?  item curto  [duplicate ID 1]\n"
                         "T0001  AUTONOMOUS     ?  item de id largo  [duplicate ID 1]\n"
                         "\nduplicate IDs: only the FIRST item under each is reachable"
                         " — renumber the others by hand in next-steps.md.\n")

    def test_pack_reads_the_id_the_way_list_does(self):
        """Two renderings of one ID is how the package and the listing come to
        disagree about which item a line is about."""
        self.seed(item(1, "item curto"), self.wide())
        r = self.run_tk("pack")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("T001   S             avulso                item curto"
                      "  [duplicate ID 1]\n", r.stdout)
        self.assertIn("T0001  S             avulso                item de id largo"
                      "  [duplicate ID 1]\n", r.stdout)

    def test_a_wide_spelling_is_still_an_allocated_id(self):
        """The one-way rule, at its sharp end: with `T0001` ALONE in the file, a
        fix that stopped the allocator seeing it re-issues 1, and the queue ends
        with two open items under one number."""
        self.seed(self.wide())
        self.assertEqual(self.add(), "T002")
        self.assertEqual(re.findall(r"\*\*T([0-9]+)\*\*", self.body()), ["0001", "002"])

    def test_a_four_digit_id_is_canonical_and_is_not_capped(self):
        """The future the cap would break. T1000 is not a wide spelling of
        anything — it is the only spelling of 1000."""
        self.seed(item(1000, "item de quatro digitos"))
        r = self.run_tk("list")
        self.assertEqual(r.stdout, "T1000  AUTONOMOUS     ?  item de quatro digitos\n")
        self.assertEqual(self.add(), "T1001")


# --- one number, more than one open item ---------------------------------

class TestAmbiguousId(QueueTest):
    """Two items at one address. It happens two ways — the same ID written
    twice, and a width collision (`T001` + `T0001`, one number to `int()`) — and
    it is ONE failure, so it gets one answer: act on the first occurrence, and
    say which one that was.

    Not a refusal, decided 2026-08-18: refusing would freeze the whole queue
    over two lines a human has to repair by hand, and the queue's other items are
    innocent. Silence was the defect — `edit T005` printed "T005 updated", true
    about the line it touched and a lie about the request, with nothing anywhere
    saying a second T005 existed.
    """

    WARNING = ('tk-queue: warning: duplicate ID 5 — 2 open items carry it (T005, T005). '
               'Acting on the FIRST, T005 "primeira ocorrencia"; the rest stay '
               'unreachable until one of them is renumbered by hand in next-steps.md.\n')

    def wide(self, text="item de id largo"):
        return item(1, text).replace("**T001**", "**T0001**", 1)

    def test_list_marks_every_row_under_a_duplicated_id(self):
        """The whole listing, because the mark is only worth anything if the rows
        that are NOT ambiguous stay unmarked — a mark on every line says nothing."""
        self.seed(item(5, "primeira ocorrencia"), item(7, "item sozinho"),
                  item(5, "segunda ocorrencia"))
        r = self.run_tk("list")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout,
                         "T005  AUTONOMOUS     ?  primeira ocorrencia  [duplicate ID 5]\n"
                         "T007  AUTONOMOUS     ?  item sozinho\n"
                         "T005  AUTONOMOUS     ?  segunda ocorrencia  [duplicate ID 5]\n"
                         "\nduplicate IDs: only the FIRST item under each is reachable"
                         " — renumber the others by hand in next-steps.md.\n")

    def test_edit_says_which_occurrence_it_acted_on_and_still_acts(self):
        self.seed(item(5, "primeira ocorrencia"), item(5, "segunda ocorrencia"))
        r = self.run_tk("edit", "5", "--effort", "M")
        self.assertEqual(r.returncode, 0, r.stderr)      # a warning, never a refusal
        self.assertIn(self.WARNING, r.stderr)
        self.assertEqual(r.stdout, "T005 updated\n")
        # the WHOLE file: `edit` rewrites it, and an absence check would pass just
        # as happily on one where the second occurrence had been eaten
        self.assertEqual(self.body(),
                         HEADER + item(5, "primeira ocorrencia", effort="M")
                         + item(5, "segunda ocorrencia"))

    def test_the_warning_sits_where_the_ID_is_RESOLVED_not_in_edit(self):
        """`done` and `cancel` resolve through the same function, so neither can
        keep the silence `edit` lost."""
        for cmd, extra in (("done", ("--how", "PR #1")), ("cancel", ("--why", "n/a"))):
            with self.subTest(cmd=cmd):
                self.seed(item(5, "primeira ocorrencia"), item(5, "segunda ocorrencia"),
                          log="")
                r = self.run_tk(cmd, "5", *extra)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertIn(self.WARNING, r.stderr)
                # the first went to the log, the second is still in the queue
                self.assertEqual(self.body(), HEADER + item(5, "segunda ocorrencia"))
                self.assertIn("primeira ocorrencia", self.body("done-log.md"))

    def test_a_wide_spelling_is_the_same_ambiguity(self):
        """The bridge to the other defect: `edit T0001` cannot reach the item
        spelled T0001 — `int("0001")` is 1 — so it must not pretend it did."""
        self.seed(item(1, "item curto"), self.wide())
        r = self.run_tk("edit", "T0001", "--effort", "M")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('tk-queue: warning: duplicate ID 1 — 2 open items carry it '
                      '(T001, T0001). Acting on the FIRST, T001 "item curto"; the rest '
                      'stay unreachable until one of them is renumbered by hand in '
                      'next-steps.md.\n', r.stderr)
        self.assertEqual(self.body(),
                         HEADER + item(1, "item curto", effort="M") + self.wide())

    def test_an_ID_carried_by_ONE_item_is_not_warned_about(self):
        """The other direction, and the only one that can see a warning fired at
        every resolution — which would train the reader to ignore it."""
        self.seed(item(5, "unico"), item(6, "outro"))
        r = self.run_tk("edit", "5", "--effort", "M")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("duplicate ID", r.stderr)
        self.assertNotIn("duplicate ID", self.run_tk("list").stdout)


# --- T121: `migrate` folds a chain that sits off the first line -----------
# field_chain reads the run of `**Field:** value.` segments ENDING THE FIRST
# LINE. An item whose fields sit on a continuation line therefore has, to every
# gate, no fields at all — 31 of the 155 open items across the real queues carry
# exactly that shape. `migrate` is the command documented as the repair for
# legacy shapes, and it folded nothing: measured on the real shape below, the
# file came back byte-identical while `pack` excluded the item and `claim`
# refused it.
#
# The command rewrites next-steps.md, which holds the user's own prose and has
# no other copy, so every test here asserts the WHOLE file. `assertNotIn` on a
# marker passes just as happily against one this command truncated — that exact
# vacuity was measured on `--risk none` in this script, with the suite green.

FOLD_LEGACY = ("- [ ] **T007** — **#9 Ingestao automatica do extrato bancario** (e-mail/OneDrive) —\n"
               "  `ready-for-agent`.\n"
               "  **Class:** AUTONOMOUS. **Effort:** L. **Source:** tracker "
               "**Project:** projeto-exemplo.\n")
FOLD_CANONICAL = ("- [ ] **T007** — **#9 Ingestao automatica do extrato bancario** "
                  "(e-mail/OneDrive) — `ready-for-agent`. **Class:** AUTONOMOUS. "
                  "**Effort:** L. **Source:** tracker **Project:** projeto-exemplo.\n")


class TestMigrateFold(QueueTest):
    FOLDED_LINE = ("1 item(s) with fields off the first line: folded up, where every gate "
                   "reads them — T007\n")

    def left_alone(self, *labels):
        return (f"{len(labels)} item(s) left exactly as they are: folding would have to "
                "GUESS which text is a field value — " + ", ".join(labels)
                + ". Close each with `cancel` and re-add it clean.\n")

    def block_left_alone(self, *labels):
        return (f"{len(labels)} item(s) left exactly as they are: a continuation line "
                "OPENS a Markdown block, and the wrapped fold has no chain to lift over "
                "it — joining would flatten a list the author wrote, so it declines "
                "instead of choosing which lines survive — "
                + ", ".join(labels)
                + ". Close each with `cancel` and re-add it clean.\n")

    def prose_marker_left_alone(self, *labels):
        return (f"{len(labels)} item(s) left exactly as they are: a **Field:** marker "
                "sits outside the chain the join would produce, so the fold would "
                "promote the item's own prose to a field — quote that marker in a code "
                "span (`**Class:**`) and the fold reads the rest as the chain it is — "
                + ", ".join(labels)
                + ". Close each with `cancel` and re-add it clean.\n")

    def migrate(self):
        r = self.run_tk("migrate")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("Traceback", r.stderr)
        return r

    # --- the shape, and the gates it was invisible to ---------------------

    def test_the_legacy_shape_is_folded_and_the_prose_survives_it(self):
        """The real shape off the root queue. The join replaces a newline and the
        indentation after it with ONE blank and moves no other character — which is
        why the assertion is the whole file and not a marker's presence."""
        self.seed(FOLD_LEGACY)
        self.assertIn(self.FOLDED_LINE, self.migrate().stdout)
        self.assertEqual(self.body(), HEADER + FOLD_CANONICAL)

    def test_after_the_fold_pack_claim_and_edit_all_reach_the_item(self):
        """The three gates that could not see the item before, run for real. Each
        was refused on this exact fixture on `main`: excluded from the package,
        `claim` refused naming the fold as the remedy, `edit --effort` refused by
        the marker-outside-the-chain guard."""
        self.seed(FOLD_LEGACY)
        self.migrate()
        self.assertIn("T007  L", self.run_tk("pack").stdout)
        r = self.run_tk("claim", "T007", "--as", "alpha")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("claimed by alpha", self.run_tk("list").stdout)
        self.assertEqual(self.run_tk("release", "T007").returncode, 0)
        r = self.run_tk("edit", "T007", "--effort", "M")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.body(),
                         HEADER + FOLD_CANONICAL.replace("**Effort:** L.", "**Effort:** M."))

    def test_a_chain_spread_over_TWO_continuation_lines_is_folded_too(self):
        """The joint between two field lines is a newline where the line's own
        segments carry a blank. Compared raw, that whitespace reads as a changed
        value and this item — a chain that is whole, merely wrapped — is refused."""
        self.seed("- [ ] **T001** — algo\n"
                  "  **Class:** AUTONOMOUS. **Effort:** S.\n"
                  "  **Criterion:** A: x. **Source:** 2026-08-13\n")
        self.migrate()
        # the fold's own assertion carries the birth stamp too: this command now
        # backdates as well as folds, and asserting the file minus that field
        # would be asserting a file the command does not write
        self.assertEqual(self.body(),
                         HEADER + LEGACY.replace("\n  ", " ").replace(
                             "**Source:**", "**Born:** 2026-08-13. **Source:**") % 1)

    def test_an_idless_legacy_item_is_folded_AND_numbered_in_one_pass(self):
        """Both repairs are `migrate`'s, and the report has to name the number the
        item leaves with — read before the ID is assigned it is reported as `----`,
        which names no item at all."""
        self.seed("- [ ] legado sem ID\n"
                  "  **Class:** AUTONOMOUS. **Effort:** S. **Source:** 2026-08-13\n")
        r = self.migrate()
        self.assertIn("IDs assigned up to T001", r.stdout)
        self.assertIn("folded up, where every gate reads them — T001\n", r.stdout)
        self.assertEqual(self.body(),
                         HEADER + "- [ ] **T001** — legado sem ID **Class:** AUTONOMOUS. "
                         "**Effort:** S. **Born:** 2026-08-13. **Source:** 2026-08-13\n")

    # --- idempotency: the command runs on a queue it already rewrote ------

    def test_a_second_migrate_is_a_no_op_on_the_file_and_says_nothing(self):
        """A repair that re-applies itself is a repair nobody can run twice. The
        second run must leave the bytes alone AND stop claiming a fold."""
        self.seed(FOLD_LEGACY, item(9, "ja canonico"))
        self.migrate()
        once = self.body()
        r = self.migrate()
        self.assertEqual(self.body(), once)
        self.assertNotIn("folded up", r.stdout)
        self.assertNotIn("left exactly as they are", r.stdout)
        # and the same of the backdating, which is the OTHER repair this command
        # re-applies: a second pass that restamped would give every item in the
        # queue the age of the last migration
        self.assertNotIn("backdated", r.stdout)

    def test_an_already_canonical_queue_is_untouched_and_silent(self):
        """The other direction, and the only one that can catch a fold firing on
        every item: a command that rewrites what is already right has no way to
        report that it changed nothing."""
        # dated on purpose: this test is about a repair firing on items that need
        # none, and an item with no **Born:** legitimately needs one now. The
        # backdating's own no-op case is the second migrate above
        self.seed(item(1, "um", born="2026-08-13"),
                  item(2, "dois", project="tk", born="2026-08-13"),
                  item(3, "tres", risk="x", born="2026-08-13"))
        before = self.body()
        r = self.migrate()
        self.assertEqual(self.body(), before)
        self.assertNotIn("folded up", r.stdout)
        self.assertNotIn("left exactly as they are", r.stdout)
        self.assertNotIn("backdated", r.stdout)
        self.assertNotIn("left with no age", r.stdout)

    def test_the_frontmatter_headings_and_the_done_log_move_stay_intact(self):
        """The fold runs inside the command that also moves [x] items out, so the
        whole file — both files — is the assertion."""
        self.seed("- [x] legado feito, movido verbatim\n\n",
                  "## Bloco com cabeçalho\n\n", FOLD_LEGACY)
        self.migrate()
        self.assertEqual(self.body(),
                         HEADER + "## Bloco com cabeçalho\n\n" + FOLD_CANONICAL)
        self.assertIn("- [x] legado feito, movido verbatim", self.body("done-log.md"))

    # --- what the fold REFUSES to guess, and says it refused -------------

    def test_a_marker_whose_value_sits_on_the_NEXT_line_is_folded_NOW(self):
        """T159. This shape was refused, and the refusal's fear was precise: joined
        blindly the **Class:** takes whatever follows as its value, and what follows
        may be a note — a class nobody wrote. The second fold path undoes the wrap
        and then CHECKS that fear, on the joined line: the class has to be one a
        gate reads. Here it is AUTONOMOUS, so the item is repaired instead of sent
        to `cancel` + re-add, which is the whole of T162. The note case is the test
        below, and it is still left alone."""
        self.seed("- [ ] **T002** — marcador e valor em linhas diferentes **Class:**\n"
                  "  AUTONOMOUS. **Effort:** S. **Source:** 2026-08-13\n")
        r = self.migrate()
        self.assertEqual(self.body(),
                         HEADER + "- [ ] **T002** — marcador e valor em linhas diferentes "
                         "**Class:** AUTONOMOUS. **Effort:** S. **Born:** 2026-08-13. "
                         "**Source:** 2026-08-13\n")
        self.assertIn("1 item(s) with fields off the first line: folded up, where every "
                      "gate reads them — T002\n", r.stdout)
        # DESIGN-L13 §3's idempotence proof, on the WRAPPED path: the chain now
        # ends the first line, so the second run has nothing to lift and has to
        # say so. The suite's other second-run test seeds the walk's shape and
        # never reached this one
        after = self.body()
        again = self.migrate()
        self.assertEqual(self.body(), after)
        self.assertNotIn("with fields off the first line", again.stdout)

    def test_a_chain_that_opens_MID_LINE_is_folded_too(self):
        """The commonest of the fifteen: the chain shares its line with the prose
        the item wrapped out of, so there is no field RUN to relocate and the walk
        declined. The prose before it stays prose, in order, and the chain ends the
        line where every gate reads it."""
        self.seed("- [ ] **T006** — rodar a amostra de calibração numa praça fora do\n"
                  "  Triângulo antes de usar a régua hiperlocal lá. **Class:** BLOCKED.\n")
        r = self.migrate()
        self.assertEqual(self.body(),
                         HEADER + "- [ ] **T006** — rodar a amostra de calibração numa "
                         "praça fora do Triângulo antes de usar a régua hiperlocal lá. "
                         "**Class:** BLOCKED.\n")
        self.assertIn("folded up, where every gate reads them — T006\n", r.stdout)

    def test_a_line_that_opens_a_block_stops_the_wrapped_fold(self):
        """The second path has no chain to lift OVER a list, so it declines rather
        than choose which lines to flatten. Measured on the queues the first path
        already serves: eight of the eleven items it folded carry prose in between,
        and a bullet list joined into one line is not recoverable.

        Reported under its OWN reason. This gate did not decline because it could
        not tell a field value from a note — that is the other two gates — and a
        reader who is told it did goes looking for a value to repair in an item
        whose only trouble is the list."""
        seeded = ("- [ ] **T009** — o item tem uma lista\n"
                  "  - primeiro ponto\n"
                  "  segue a frase e a cadeia. **Class:** BLOCKED.\n")
        self.seed(seeded)
        r = self.migrate()
        self.assertEqual(self.body(), HEADER + seeded)
        self.assertIn(self.block_left_alone("T009"), r.stdout)
        self.assertNotIn("GUESS which text is a field value", r.stdout)

    def test_a_NOTE_line_after_the_field_line_is_left_and_REPORTED(self):
        """Folded, the note lands inside the last field's value — FIELD_SEGMENT_RE's
        body is greedy — and `**Source:** 2026-08-13 nota solta.` is what every
        reader would then report as the source."""
        seeded = ("- [ ] **T003** — nota depois dos campos\n"
                  "  **Class:** AUTONOMOUS. **Effort:** S. **Source:** 2026-08-13\n"
                  "  nota solta depois dos campos.\n")
        self.seed(seeded)
        r = self.migrate()
        self.assertEqual(self.body(), HEADER + seeded)
        self.assertIn(self.left_alone("T003"), r.stdout)

    def test_a_marker_in_the_item_s_OWN_PROSE_is_left_and_REPORTED(self):
        """The shape claim_unwritable_message already refuses to promise the fold
        for. The prose marker ends in a period and would join the chain from the
        left, so the folded chain is not the one the item carried."""
        seeded = ("- [ ] **T004** — ver a **Deferred:** nota de contexto.\n"
                  "  **Class:** AUTONOMOUS. **Effort:** S. **Source:** 2026-08-13\n")
        self.seed(seeded)
        r = self.migrate()
        self.assertEqual(self.body(), HEADER + seeded)
        self.assertIn(self.prose_marker_left_alone("T004"), r.stdout)

    def test_a_marker_that_forms_no_chain_at_all_is_left_and_REPORTED(self):
        """A continuation line carrying a marker whose run does not reach the end of
        the line — a bold word after it stops it. Folding here repairs NOTHING, and
        a fold that repairs nothing still rewrites the user's line and reports it as
        repaired: the one direction a data-rewriting command may never take."""
        seeded = ("- [ ] **T008** — texto\n"
                  "  ver a **Risk:** de **produção** antes.\n")
        self.seed(seeded)
        r = self.migrate()
        self.assertEqual(self.body(), HEADER + seeded)
        self.assertIn(self.left_alone("T008"), r.stdout)

    def test_an_item_with_no_field_at_all_is_neither_folded_nor_reported(self):
        """A different defect with a different repair (`edit --class`). Named in
        the fold's report it would send the caller to `cancel` + re-add for an item
        one flag fixes — and a report that names items the fold is not about is one
        its reader learns to skip."""
        seeded = "- [ ] **T005** — item sem campo nenhum\n  so prosa de continuacao.\n"
        self.seed(seeded)
        r = self.migrate()
        self.assertEqual(self.body(), HEADER + seeded)
        self.assertNotIn("left exactly as they are", r.stdout)
        self.assertNotIn("folded up", r.stdout)

    def test_the_two_populations_are_separated_in_ONE_run(self):
        """The report is only worth reading if it discriminates: a run over both
        shapes must fold one, leave the other, and name each under its own line."""
        self.seed(FOLD_LEGACY,
                  "- [ ] **T003** — nota depois dos campos\n"
                  "  **Class:** AUTONOMOUS. **Effort:** S. **Source:** 2026-08-13\n"
                  "  nota solta depois dos campos.\n")
        r = self.migrate()
        self.assertIn(self.FOLDED_LINE, r.stdout)
        self.assertIn(self.left_alone("T003"), r.stdout)
        self.assertEqual(self.body(),
                         HEADER + FOLD_CANONICAL
                         + "- [ ] **T003** — nota depois dos campos\n"
                         "  **Class:** AUTONOMOUS. **Effort:** S. **Source:** 2026-08-13\n"
                         "  nota solta depois dos campos.\n")


# --- T121: prose that WEARS a real field's name is not a field -------------
#
# field_chain's two conditions — contiguous, and a value ending in '.' — do not
# separate prose that QUOTES a real field name from the field it imitates.
# Ordinary prose ending in a period was never the trigger: it forms no segment at
# all. Bolding the field's own name is what creates one, and the run then reaches
# back over it as if the user had written a field there.
#
# Both directions were measured on `main`, each exiting 0 and printing "updated",
# against next-steps.md — a user-data file with no other copy of the prose:
#
#   edit T011 --project tk    OVERWROTE "de outra fila inteira"
#   edit T012 --risk none     DELETED the quoted segment whole
#
# So every assertion below is the WHOLE file. `assertNotIn("**Risk:**")` passes
# just as happily against a file this command corrupted — that exact vacuity was
# measured on `--risk none` in this very script, with the suite green.

PROSE_PROJECT = ("- [ ] **T011** — o item cita o **Project:** de outra fila inteira. "
                 "**Class:** AUTONOMOUS. **Effort:** S. **Criterion:** A: x.\n")
PROSE_RISK = ("- [ ] **T012** — nota de risco: **Risk:** so vale ate o merge da #22. "
              "**Class:** AUTONOMOUS. **Effort:** S. **Criterion:** A: y.\n")


class TestProseWearingAFieldName(QueueTest):
    """The chain begins at **Class:**, and a segment before it is prose.

    The position rule the gates already read through (qualified_fields) now also
    locates the segment `edit` WRITES. Neither item below ever carried the field
    the command named — the marker is in the user's own sentence — so there is
    nothing to edit and the command says so instead of picking the sentence.
    """

    def test_setting_a_field_named_only_in_prose_is_refused(self):
        self.seed(PROSE_PROJECT)
        r = self.run_tk("edit", "T011", "--project", "tk")
        # the FILE first, and whole. A returncode assertion placed ahead of it
        # short-circuits the one that matters, and what this defect does to the
        # text is the finding — "it exited 1" is only how the caller learns of it
        self.assertEqual(self.body(), HEADER + PROSE_PROJECT)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("OUTSIDE its field chain", r.stderr)
        self.assertIn("Nothing was changed", r.stderr)

    def test_CLEARING_a_field_named_only_in_prose_is_refused(self):
        """The deletion path, and the worse half: the words were not overwritten
        but removed, and a removal leaves nothing to restore from."""
        self.seed(PROSE_RISK)
        r = self.run_tk("edit", "T012", "--risk", "none")
        self.assertEqual(self.body(), HEADER + PROSE_RISK)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("OUTSIDE its field chain", r.stderr)
        self.assertIn("Nothing was changed", r.stderr)

    def test_a_field_the_prose_does_NOT_name_still_edits(self):
        """The over-refusal direction. One quoted marker may not make the whole
        item uneditable: a guard that fires on every flag teaches the caller to
        cancel + re-add items that are merely untidy, which is the habit this
        refusal exists to avoid."""
        self.seed(PROSE_PROJECT)
        r = self.run_tk("edit", "T011", "--effort", "M")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.body(),
                         HEADER + PROSE_PROJECT.replace("**Effort:** S.", "**Effort:** M."))

    def test_the_anchor_does_not_move_the_fields_of_an_ordinary_item(self):
        """The rule must be a no-op on everything compose_item writes, which puts
        every field after **Class:** — Source included, the one written last and
        without a period. A position rule that slipped by one would make the
        canonical item, not the malformed one, the population it refuses."""
        for flag, val, old, repl in (
                ("--project", "ambiente", "**Project:** tk.", "**Project:** ambiente."),
                ("--risk", "none", " **Risk:** dano X.", ""),
                ("--risk", "dano Y", "**Risk:** dano X.", "**Risk:** dano Y."),
                ("--class", "BLOCKED", "**Class:** AUTONOMOUS.", "**Class:** BLOCKED."),
                ("--effort", "L", "**Effort:** S.", "**Effort:** L.")):
            with self.subTest(flag=flag, val=val):
                seeded = item(1, "um", project="tk", risk="dano X")
                self.seed(seeded)
                r = self.run_tk("edit", "T001", flag, val)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertEqual(self.body(), HEADER + seeded.replace(old, repl))

    def test_the_remedy_the_refusal_PRINTS_runs_and_lets_the_edit_through(self):
        """A refusal is only acceptable while its remedy is reachable, so the
        printed one is run for real and the refused command re-tried after it.

        `--text` is NOT a remedy here and the message does not offer it: the
        rewrite keeps everything from the FIRST marker in the block on, and that
        marker is the quoted one — the prose would survive as a field.
        """
        self.seed(PROSE_PROJECT)
        self.assertEqual(self.run_tk("edit", "T011", "--project", "tk").returncode, 1)
        r = self.run_tk("cancel", "T011", "--why", "reescrito sem o marcador em prosa")
        self.assertEqual(r.returncode, 0, r.stderr)
        r = self.run_tk("add", "o item cita o campo Project de outra fila inteira",
                        "--class", "AUTONOMOUS", "--effort", "S", "--criterion", "A: x")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("added T012", r.stdout)
        r = self.run_tk("edit", "T012", "--project", "tk")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("**Project:** tk.", self.body())


# --- T121: `list` and the gate must read the class from the same place -----
#
# `item_class` searched the WHOLE block and took the leftmost match; the gate
# reads the field chain (`chain_class`). Measured on `main`, one item, one run:
#
#   list   T009  BLOCKED      <- from the item's own sentence
#   pack   T009  S  ...       <- eligible, i.e. the gate read AUTONOMOUS
#
# The gate was already right, so the display is what moves. What makes it
# non-trivial is the population underneath: a legacy item carries its fields on a
# continuation line, and reading the chain ALONE shows every one of them with no
# class at all. `migrate` folds those, but folding is a command a human runs.

PROSE_CLASS = ("- [ ] **T009** — item que fala de **Class:** BLOCKED em prosa, mas nao e "
               "**Class:** AUTONOMOUS. **Effort:** S. **Criterion:** A: x.\n")
TWO_CLASSES = ("- [ ] **T010** — cita **Class:** DECISION. **Class:** AUTONOMOUS. "
               "**Effort:** S. **Criterion:** A: x.\n")
CLASS_OFF_LINE = ("- [ ] **T007** — legado com campos fora da primeira linha\n"
                  "  **Class:** AUTONOMOUS. **Effort:** L. **Source:** tracker\n")


class TestListReadsTheClassFromTheChain(QueueTest):
    """One reader for the display and for the gate, wherever there is a chain.

    A `list` that says BLOCKED over a `pack` that says AUTONOMOUS is worse than
    either being wrong on its own: `list` is the screen a human reads before
    dispatching, and nothing on it says the two readers have parted.
    """

    def test_a_class_named_only_in_PROSE_is_not_the_one_list_shows(self):
        self.seed(PROSE_CLASS)
        self.assertIn("T009  AUTONOMOUS     ?  item que fala de",
                      self.run_tk("list").stdout)

    def test_list_and_pack_no_longer_disagree_about_the_same_item(self):
        """The defect itself, asserted as the disagreement it was: the two
        commands are run over ONE queue and made to answer the same thing. Either
        assertion alone would still pass while the readers diverged."""
        self.seed(PROSE_CLASS)
        self.assertIn("T009  AUTONOMOUS", self.run_tk("list").stdout)
        pack = self.run_tk("pack").stdout
        self.assertIn("eligible (1 of 1", pack)
        self.assertNotIn("class is BLOCKED", pack)

    def test_a_legacy_item_with_its_fields_OFF_the_first_line_still_shows_its_class(self):
        """The regression the chain-only reading would cause, and the reason the
        block-wide search stays as the fallback. `pack` excludes this item and says
        why — that is a different question from what the item IS, and `list` must
        still show the class the user wrote."""
        self.seed(CLASS_OFF_LINE)
        out = self.run_tk("list").stdout
        self.assertIn("T007  AUTONOMOUS", out)
        self.assertNotIn("T007  ?", out)

    def test_a_class_the_GATE_calls_ambiguous_is_shown_as_unknown_not_guessed(self):
        """Two classes inside the chain: `chain_class` refuses to pick one, so the
        display may not pick one either. Showing the leftmost here is how `list`
        would print a class no gate would honour."""
        self.seed(TWO_CLASSES)
        out = self.run_tk("list").stdout
        self.assertIn("T010  ?", out)
        self.assertNotIn("DECISION", out)
        self.assertIn("2 **Class:** fields in the chain", self.run_tk("pack").stdout)

    def test_an_ordinary_item_is_displayed_exactly_as_before(self):
        """The population that is not legacy and not malformed — the one every
        other test in this file seeds. A reader change that moved these would be
        the defect, not the fix."""
        self.seed(item(1, "um"), item(2, "dois", klass="DECISION"),
                  item(3, "tres", klass="RECURRING"))
        out = self.run_tk("list").stdout
        for line in ("T001  AUTONOMOUS     ?  um", "T002  DECISION       ?  dois",
                     "T003  RECURRING      ?  tres"):
            self.assertIn(line, out)


# --- T121: a resolved ID names the item it REACHED ------------------------
#
# `item_label` gave `list` and `pack` the item's own spelling. The commands that
# RESOLVE an ID went on re-rendering the parsed number, and `int("0001") == 1`.
# Two measured faces, one root — both on a lone `T0001`:
#
#   claim T0001 -> "T001 cannot hold a claim ... `tk-queue edit T001 --text ...`"
#   done  T0001 -> "- 2026-08-20 - FEITO - T001 item largo. - feito"
#
# The first HANDS THE CALLER A COMMAND. In a queue that also holds a real T001 it
# is a command about that OTHER item, and `--text` replaces everything between
# the head and the first field, continuation prose included. The second is the
# durable record: the done-log outlives the item, and it was left naming an ID no
# item ever carried, which no grep for the real one will ever find.
#
# The ID stays the ADDRESS — `done 1`, `done T001` and `done T0001` are one call,
# and two items under one number are the ambiguity TestAmbiguousId measures. What
# moves is the NAME every message and record gives back.

WIDE_OFF_LINE = ("- [ ] **T0001** — legado de id largo, campos fora da 1a linha\n"
                 "  **Class:** AUTONOMOUS. **Effort:** L. **Source:** tracker\n")


class TestResolvedItemKeepsItsOwnSpelling(QueueTest):
    """Every message and record ABOUT an item names the block that was acted on,
    read off that block with `item_label` — never rebuilt from the number the
    caller typed."""

    def wide(self, text="item de id largo", **kw):
        """T0001: the same number as T001, spelled a digit wider."""
        return item(1, text, **kw).replace("**T001**", "**T0001**", 1)

    def today(self):
        return datetime.date.today().isoformat()

    def add(self, text="novo"):
        r = self.run_tk("add", text, "--class", "AUTONOMOUS", "--effort", "S",
                        "--criterion", "A: c")
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout.split()[1].rstrip(":")

    # --- the refusal that hands over a command ---------------------------
    def test_the_refusal_names_the_item_and_its_remedy_addresses_that_item(self):
        self.seed(WIDE_OFF_LINE)
        r = self.run_tk("claim", "T0001", "--as", "teste")
        self.assertEqual(r.returncode, 1)
        self.assertIn("T0001 cannot hold a claim the reader would find", r.stderr)
        self.assertIn('`tk-queue edit T0001 --text "<the item\'s whole text>"`', r.stderr)
        self.assertNotIn("T001 cannot hold", r.stderr)
        self.assertNotIn("edit T001 --text", r.stderr)
        # a refusal writes nothing, and the WHOLE file says so: an absence check
        # would pass just as happily on a file this run had truncated
        self.assertEqual(self.body(), HEADER + WIDE_OFF_LINE)

    def test_the_old_remedy_was_a_command_about_a_DIFFERENT_open_item(self):
        """The destruction that was one paste away. With a real T001 in the same
        queue, `tk-queue edit T001 --text "<the item's whole text>"` addresses
        that item — and --text replaces everything between its head and its first
        field. `list` shows the two as the two items they are; the refusal has to
        name the one it is about."""
        other = item(1, "item curto de verdade")
        self.seed(WIDE_OFF_LINE, other)
        self.assertIn("T001   AUTONOMOUS     ?  item curto de verdade",
                      self.run_tk("list").stdout)
        r = self.run_tk("claim", "T0001", "--as", "teste")
        self.assertEqual(r.returncode, 1)
        self.assertIn("T0001 cannot hold a claim", r.stderr)
        self.assertIn("tk-queue edit T0001 --text", r.stderr)
        self.assertNotIn("T001 cannot hold", r.stderr)
        self.assertNotIn("edit T001 --text", r.stderr)
        self.assertEqual(self.body(), HEADER + WIDE_OFF_LINE + other)

    # --- the record that outlives the item -------------------------------
    def test_the_done_log_records_the_item_under_its_own_spelling(self):
        """The WHOLE entry line, because this one is user data with no other
        copy: `assertIn("T0001")` passes on a line that also still says T001."""
        self.seed(self.wide(), log="")
        r = self.run_tk("done", "T0001", "--how", "feito")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, f"T0001 → done-log as FEITO ({self.today()})\n")
        entries = [ln for ln in self.body("done-log.md").splitlines()
                   if ln.startswith("- 2")]
        self.assertEqual(
            entries, [f"- {self.today()} — FEITO — T0001 item de id largo — feito"])

    def test_cancel_writes_the_same_name_into_the_log(self):
        """`done` and `cancel` are one function, and a fix in one of two copies
        is how the log would come to spell the same item two ways."""
        self.seed(self.wide(), log="")
        r = self.run_tk("cancel", "T0001", "--why", "nao vale")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, f"T0001 → done-log as DESCARTADO ({self.today()})\n")
        entries = [ln for ln in self.body("done-log.md").splitlines()
                   if ln.startswith("- 2")]
        self.assertEqual(
            entries,
            [f"- {self.today()} — DESCARTADO — T0001 item de id largo — nao vale"])

    def test_the_recorded_spelling_is_still_the_one_the_readers_parse(self):
        """LOG_ID_RE reads the log's ID column and `max_id` allocates from it, so
        a label the log grammar cannot parse hands 1 out a second time — the
        outcome the whole ID grammar exists to prevent."""
        self.seed(self.wide(), log="")
        self.assertEqual(self.run_tk("done", "T0001", "--how", "feito").returncode, 0)
        self.assertEqual(self.add(), "T002")
        self.assertIn("T0001 item de id largo", self.run_tk("report").stdout)

    # --- every other command that resolves an ID -------------------------
    def test_edit_reports_the_item_it_rewrote(self):
        self.seed(self.wide())
        r = self.run_tk("edit", "T0001", "--effort", "M")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, "T0001 updated\n")
        self.assertEqual(self.body(), HEADER + self.wide(effort="M"))

    def test_claim_release_and_bump_name_the_item_they_touched(self):
        self.seed(item(2, "outro"), self.wide())
        r = self.run_tk("claim", "T0001", "--as", "alpha")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertRegex(r.stdout, r"\AT0001 claimed by alpha ")
        r = self.run_tk("claim", "T0001", "--as", "beta")
        self.assertEqual(r.returncode, 1)
        self.assertIn("T0001 is already claimed by alpha since", r.stderr)
        self.assertIn("`tk-queue release T0001`", r.stderr)
        r = self.run_tk("release", "T0001")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("T0001 released — it was claimed by alpha since", r.stdout)
        self.assertEqual(self.run_tk("release", "T0001").stdout,
                         "T0001 carries no claim — nothing to release\n")
        self.assertEqual(self.run_tk("bump", "T0001").stdout,
                         "T0001 → top of the queue\n")
        self.assertEqual(self.run_tk("bump", "T0001").stdout,
                         "T0001 is already at the top of the queue\n")

    def test_the_deferral_refusal_names_the_item(self):
        """`edit`'s deferral gate reasons about the item's resulting CLASS and
        says which item it is talking about."""
        self.seed(self.wide())
        r = self.run_tk("edit", "T0001", "--deferred", "esperando o revisor.")
        self.assertEqual(r.returncode, 1)
        self.assertIn("T0001 is AUTONOMOUS.", r.stderr)
        self.assertNotIn("T001 is AUTONOMOUS.", r.stderr)
        self.assertEqual(self.body(), HEADER + self.wide())

    def test_an_item_already_ticked_is_named_by_its_own_spelling(self):
        """The one branch of missing_item_message that HAS a block. `migrate`
        moves a ticked line VERBATIM, so the log will carry T0001 and nothing
        else — a message saying T001 sends the reader to grep a name the history
        does not contain, which is the branch's whole instruction."""
        self.seed(self.wide().replace("- [ ]", "- [x]", 1))
        r = self.run_tk("done", "T0001", "--how", "feito")
        self.assertEqual(r.returncode, 1)
        self.assertIn("T0001 is in next-steps.md but already ticked [x]", r.stderr)
        self.assertNotIn("T001 is in next-steps.md", r.stderr)
        # the remedy it prints, run: the log really does carry that spelling
        self.assertEqual(self.run_tk("migrate").returncode, 0)
        self.assertIn("**T0001**", self.body("done-log.md"))

    def test_the_ambiguous_and_stray_claim_refusals_name_the_item(self):
        """`claim_segment` reads the claim for both `claim` and `release`, and its
        two refusals are about the item — which is the one they have to name."""
        two = ("- [ ] **T0001** — um **Class:** AUTONOMOUS. **Effort:** S. "
               "**Criterion:** A: x. **Claimed:** alfa since 2026-08-19T10:00:00Z. "
               "**Claimed:** bravo since 2026-08-19T11:00:00Z.\n")
        self.seed(two)
        r = self.run_tk("claim", "T0001", "--as", "charlie")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("T0001 carries 2 **Claimed:** fields", r.stderr)
        self.assertNotIn("T001 carries", r.stderr)
        self.assertEqual(self.body(), HEADER + two)

        stray = "- [ ] **T0001** — algo\n  nota: **Claimed:** ver depois\n"
        self.seed(stray)
        r = self.run_tk("release", "T0001")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("T0001 carries a **Claimed:** marker away from the position",
                      r.stderr)
        self.assertNotIn("T001 carries", r.stderr)
        self.assertEqual(self.body(), HEADER + stray)

    # --- where there is no item, there is no label -----------------------
    def test_an_ID_that_reaches_no_item_keeps_the_canonical_rendering(self):
        """No block was resolved, so there is nothing to read a label off — and
        the branch that says so must not go looking for one."""
        self.seed(item(2, "dois"),
                  log="- 2026-08-01 — FEITO — T001 um — PR #1\n")
        r = self.run_tk("done", "999", "--how", "x")
        self.assertEqual(r.returncode, 1)
        self.assertIn("T999 was never allocated", r.stderr)
        r = self.run_tk("edit", "T001", "--effort", "M")
        self.assertEqual(r.returncode, 1)
        self.assertIn("T001 already left the queue", r.stderr)

    def test_an_ordinary_item_is_reported_exactly_as_before(self):
        """Canonical spelling is zero-padded to three, so for every item a WRITER
        of these files produced the label IS the old rendering. Moving these
        would be the defect, not the fix."""
        self.seed(item(1, "um"), log="")
        self.assertEqual(self.run_tk("edit", "T001", "--effort", "M").stdout,
                         "T001 updated\n")
        self.assertEqual(self.run_tk("bump", "1").stdout,
                         "T001 is already at the top of the queue\n")
        r = self.run_tk("done", "1", "--how", "PR #1")
        self.assertEqual(r.stdout, f"T001 → done-log as FEITO ({self.today()})\n")
        self.assertIn(f"- {self.today()} — FEITO — T001 um — PR #1",
                      self.body("done-log.md"))


# --- review#3: the fold flattened the item's MARKDOWN -----------------------
#
# `fold_chain_onto_first_line` validated the trailing field run and then joined
# EVERY line of the block into one. Its readback re-derived only the field
# SEGMENTS, so prose in between was never looked at: the join passed while the
# structure that made it readable was gone. Measured on the real queues before
# the repair — 8 of the 11 items the command folded carried prose in between:
#
#   one real item's T037        a five-item bulleted list → one run-on line
#   another real item's T018    an eleven-line note → one run-on line
#
# and `migrate` printed "folded up" for both, on a file with no other copy.
#
# The repair splits the two populations the corpus actually holds. A hard-wrapped
# sentence is absorbed as before — its soft line break renders as one blank
# either way, so the join changes nothing a reader sees, and 7 of those 8 items
# are exactly that. A line that OPENS a Markdown block keeps its own line, its
# own place and its own indentation.
#
# Every test here asserts the WHOLE file, both because this command rewrites user
# data and because the defect was invisible to any assertion narrower than that.

FOLD_LIST = ("- [ ] **T005** — item com lista aninhada abaixo\n"
             "  - sub ponto A\n"
             "    - sub ponto A.1, aninhado\n"
             "  - sub ponto B\n"
             "  **Class:** AUTONOMOUS. **Effort:** S. **Criterion:** A: x.\n")
FOLD_LIST_FOLDED = ("- [ ] **T005** — item com lista aninhada abaixo **Class:** AUTONOMOUS. "
                    "**Effort:** S. **Criterion:** A: x.\n"
                    "  - sub ponto A\n"
                    "    - sub ponto A.1, aninhado\n"
                    "  - sub ponto B\n")
FOLD_WRAPPED = ("- [ ] **T006** — item cuja frase quebra no meio de um parenteses (parte um,\n"
                "  parte dois) e segue ate o fim.\n"
                "  **Class:** AUTONOMOUS. **Effort:** S. **Criterion:** A: y.\n")
FOLD_WRAPPED_FOLDED = ("- [ ] **T006** — item cuja frase quebra no meio de um parenteses "
                       "(parte um, parte dois) e segue ate o fim. **Class:** AUTONOMOUS. "
                       "**Effort:** S. **Criterion:** A: y.\n")


class TestFoldKeepsTheItemsMarkdown(QueueTest):
    """What the fold may absorb, and what it may only relocate around."""

    def migrate(self):
        r = self.run_tk("migrate")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("Traceback", r.stderr)
        return r

    def split_refusal(self, *labels):
        return (f"{len(labels)} item(s) left exactly as they are: a **Field:** marker "
                "would stay off the first line, and a chain the fold only half lifts is "
                "not a chain any gate can read — " + ", ".join(labels)
                + ". Close each with `cancel` and re-add it clean.\n")

    # --- the block structure the join used to eat ------------------------

    def test_a_bulleted_list_between_the_head_and_the_chain_survives_the_fold(self):
        """The T037 shape, and the whole finding: every bullet keeps its own line
        and its own indentation, the nested one included, while the chain moves up
        to where the gates read it. Asserted as the whole file — the old readback
        compared the field segments alone and passed on the flattened item."""
        self.seed(FOLD_LIST)
        r = self.migrate()
        self.assertIn("folded up, where every gate reads them — T005\n", r.stdout)
        self.assertEqual(self.body(), HEADER + FOLD_LIST_FOLDED)

    def test_the_gates_reach_an_item_folded_AROUND_its_list(self):
        """The fold is only worth the rewrite if the gates can read the result, and
        only acceptable if the list is still there afterwards. Both, end to end."""
        self.seed(FOLD_LIST)
        self.migrate()
        self.assertIn("T005  S", self.run_tk("pack").stdout)
        self.assertEqual(self.run_tk("claim", "T005", "--as", "alpha").returncode, 0)
        self.assertEqual(self.run_tk("release", "T005").returncode, 0)
        r = self.run_tk("edit", "T005", "--effort", "L")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.body(),
                         HEADER + FOLD_LIST_FOLDED.replace("**Effort:** S.", "**Effort:** L."))

    def test_prose_that_wraps_AFTER_a_block_is_not_lifted_over_it(self):
        """Only the wrapped lines that OPEN the block are absorbed. Lifting a line
        from under a bullet would move that text above the bullet it belongs to —
        the reordering is silent, and the item then says something else."""
        seeded = ("- [ ] **T009** — cabeca do item\n"
                  "  - primeiro ponto, que quebra\n"
                  "  a linha no meio\n"
                  "  **Class:** AUTONOMOUS. **Effort:** S. **Criterion:** A: x.\n")
        self.seed(seeded)
        self.migrate()
        self.assertEqual(self.body(),
                         HEADER
                         + "- [ ] **T009** — cabeca do item **Class:** AUTONOMOUS. "
                           "**Effort:** S. **Criterion:** A: x.\n"
                           "  - primeiro ponto, que quebra\n"
                           "  a linha no meio\n")

    # --- and the population the join was RIGHT about ----------------------

    def test_a_hard_wrapped_sentence_is_still_absorbed_into_the_head(self):
        """The other direction, and the expensive one to get wrong: 7 of the 8 real
        items are a sentence broken at column ~95, several mid-parenthesis. Kept as
        a line, the fields land inside the unclosed parenthesis and the item reads
        worse than before the command ran. Markdown renders the soft break as one
        blank, so absorbing it changes nothing a reader sees."""
        self.seed(FOLD_WRAPPED)
        r = self.migrate()
        self.assertIn("folded up, where every gate reads them — T006\n", r.stdout)
        self.assertEqual(self.body(), HEADER + FOLD_WRAPPED_FOLDED)

    def test_both_populations_fold_in_ONE_run_each_keeping_its_own_shape(self):
        self.seed(FOLD_LIST, FOLD_WRAPPED)
        r = self.migrate()
        self.assertIn("folded up, where every gate reads them — T005, T006\n", r.stdout)
        self.assertEqual(self.body(), HEADER + FOLD_LIST_FOLDED + FOLD_WRAPPED_FOLDED)

    # --- the marker the fold would leave behind ---------------------------

    def test_a_marker_stranded_on_a_BLOCK_line_is_left_and_REPORTED(self):
        """A bullet that quotes a field marker cannot be absorbed, so folding the
        run below it would leave a marker off the first line — half a chain, on an
        item that now reads as repaired. Nothing here can tell the rest of a split
        chain from prose quoting a marker, so the item is left whole and named."""
        seeded = ("- [ ] **T010** — cabeca\n"
                  "  - ponto que cita o **Risk:** de outro item.\n"
                  "  **Class:** AUTONOMOUS. **Effort:** S. **Criterion:** A: x.\n")
        self.seed(seeded)
        r = self.migrate()
        self.assertEqual(self.body(), HEADER + seeded)
        self.assertIn(self.split_refusal("T010"), r.stdout)

    def test_the_two_refusals_are_reported_under_their_OWN_reasons(self):
        """The report gained a second reason, and a reader repairs the shape the
        sentence names. Melted into one line, the split-chain item is filed under a
        sentence about guessing values and sends its reader after the wrong thing."""
        self.seed("- [ ] **T010** — cabeca\n"
                  "  - ponto que cita o **Risk:** de outro item.\n"
                  "  **Class:** AUTONOMOUS. **Effort:** S. **Criterion:** A: x.\n",
                  "- [ ] **T011** — nota depois dos campos\n"
                  "  **Class:** AUTONOMOUS. **Effort:** S. **Source:** 2026-08-13\n"
                  "  nota solta depois dos campos.\n")
        r = self.migrate()
        self.assertIn(self.split_refusal("T010"), r.stdout)
        self.assertIn("1 item(s) left exactly as they are: folding would have to GUESS "
                      "which text is a field value — T011.", r.stdout)


# --- review#3: a chain with no **Class:** anchors NOTHING -------------------
#
# `real_fields` answered a class-less chain with the WHOLE chain, and `edit`
# writes through `real_fields`. So on an item that carries no class, the position
# rule had no position to measure from and the item's own prose was the field —
# the original destructive bug, alive on one population. Measured on `main`:
#
#   edit T021 --project tk   OVERWROTE "de outra fila inteira"
#   edit T022 --risk none    DELETED the imitating segment whole
#
# both exiting 0 and printing "updated". The fallback was written so that
# `edit --class` could still repair a class-less item, and it never had to:
# **Class:** is not in that item's chain, so the locator comes back empty for it
# either way and the flag APPENDS. Every test below asserts the whole file.

CLASSLESS_PROJECT = ("- [ ] **T021** — item, cita o **Project:** de outra fila inteira. "
                     "**Criterion:** ok.\n")
CLASSLESS_RISK = ("- [ ] **T022** — item, ver a **Risk:** nota de contexto importante. "
                  "**Criterion:** ok.\n")
CLASSLESS_REAL = "- [ ] **T023** — legado sem classe. **Effort:** M. **Criterion:** ok.\n"


class TestAClassLessChainIsNotAField(QueueTest):

    def test_setting_a_field_on_a_class_less_item_is_refused(self):
        self.seed(CLASSLESS_PROJECT)
        r = self.run_tk("edit", "T021", "--project", "tk")
        # the FILE first, and whole: what this defect did to the text is the
        # finding, and "it exited 1" is only how the caller learns of it
        self.assertEqual(self.body(), HEADER + CLASSLESS_PROJECT)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("T021 names no **Class:** in its field chain", r.stderr)
        self.assertIn("Nothing was changed", r.stderr)

    def test_CLEARING_a_field_on_a_class_less_item_is_refused(self):
        """The deletion path, and the worse half: the words are not overwritten but
        removed, and a removal leaves nothing to restore from."""
        self.seed(CLASSLESS_RISK)
        r = self.run_tk("edit", "T022", "--risk", "none")
        self.assertEqual(self.body(), HEADER + CLASSLESS_RISK)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("T022 names no **Class:** in its field chain", r.stderr)
        # this guard's OWN sentence, and not merely the prefix the next one shares:
        # review#5 put a second refusal on the clearing branch below, so with the
        # position rule mutated back to eating this prose, THAT one answers and the
        # item is still safe — the file unchanged, the exit 1, and the shared prefix
        # all identical. Two corrections of one incident masking each other is what
        # the mutation run reported, and asserting the distinguishing clause is what
        # keeps this test proving the rule it was written for
        self.assertIn("would rewrite that prose (and with `none`, DELETE it)", r.stderr)

    def test_a_field_the_class_less_item_really_carries_is_refused_too(self):
        """The cost of the rule, paid deliberately and measured: with no anchor,
        a real **Effort:** and a quoted one are the same string in the same place.
        The refusal is what the command may do about that; picking one is what it
        may not. Zero of the 202 real open items are in this population."""
        self.seed(CLASSLESS_REAL)
        r = self.run_tk("edit", "T023", "--effort", "L")
        self.assertEqual(self.body(), HEADER + CLASSLESS_REAL)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("T023 names no **Class:** in its field chain", r.stderr)

    # --- and the repair the rule must NOT lock out ------------------------

    def test_a_class_less_item_can_still_be_GIVEN_a_class(self):
        """`--class` is the flag that gives the item its anchor, so a rule that
        refused it would lock the repair out of the one population it exists for.

        Where the item already ends its line with a chain, the anchor goes AHEAD
        of that chain and not after it — T169, and `TestTheClassLandsAheadOfTheChain`
        is where that position is proved. Here it is asserted only so this class,
        which owns the class-less item, cannot go on describing the old one."""
        for seeded, iid, at in ((CLASSLESS_REAL, "T023", "legado sem classe. "),
                                (CLASSLESS_PROJECT, "T021", "item, cita o ")):
            with self.subTest(item=iid):
                self.seed(seeded)
                r = self.run_tk("edit", iid, "--class", "AUTONOMOUS")
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertEqual(r.stdout, f"{iid} updated\n")
                self.assertEqual(self.body(),
                                 HEADER + seeded.replace(
                                     at, at + "**Class:** AUTONOMOUS. "))
                self.assertIn(f"{iid}  AUTONOMOUS", self.run_tk("list").stdout)

    def test_the_refusal_does_not_offer_a_remedy_that_is_a_dead_end(self):
        """A refusal that named `--class` as THE remedy would be wrong in both
        directions, and the message says which one this item is in.

        On CLASSLESS_REAL the fields are real, so the class repairs the item and
        `--effort` goes through afterwards — that is T169's whole point. On
        CLASSLESS_PROJECT the same anchor turns four words of the item's own title
        into a **Project:** value, and `--project` would then overwrite them. The
        message therefore stops calling the class a remedy for the refused edit and
        says what it does to the run it anchors."""
        self.seed(CLASSLESS_REAL)
        r = self.run_tk("edit", "T023", "--effort", "L")
        self.assertIn("is not the remedy for this either", r.stderr)
        self.assertIn("makes EVERY segment now ending that line a field", r.stderr)
        self.assertEqual(self.run_tk("edit", "T023", "--class", "AUTONOMOUS").returncode, 0)
        again = self.run_tk("edit", "T023", "--effort", "L")
        self.assertEqual(again.returncode, 0, again.stderr)   # the dead end is gone
        self.assertIn("**Effort:** L.", self.body())

    def test_the_remedy_the_refusal_PRINTS_runs_and_lets_the_edit_through(self):
        """A refusal is only acceptable while its remedy is reachable, so the
        printed one is run for real and the refused command re-tried after it."""
        self.seed(CLASSLESS_PROJECT, log="")
        self.assertEqual(self.run_tk("edit", "T021", "--project", "tk").returncode, 1)
        r = self.run_tk("cancel", "T021", "--why", "reescrito com uma classe")
        self.assertEqual(r.returncode, 0, r.stderr)
        r = self.run_tk("add", "o item cita o campo Project de outra fila inteira",
                        "--class", "AUTONOMOUS", "--effort", "S", "--criterion", "A: x")
        self.assertEqual(r.returncode, 0, r.stderr)
        r = self.run_tk("edit", "T022", "--project", "tk")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("**Project:** tk.", self.body())

    def test_an_anchored_item_is_untouched_by_the_rule(self):
        """The over-refusal direction. Every item `add` writes carries a class, so
        a rule that reached them would refuse the whole queue."""
        seeded = item(1, "um", project="tk", risk="dano X")
        self.seed(seeded)
        r = self.run_tk("edit", "T001", "--project", "ambiente")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.body(),
                         HEADER + seeded.replace("**Project:** tk.", "**Project:** ambiente."))


# --- review#3: T000 is an ID, and the mark is guarded `is not None` ---------
#
# `list_line` prints the duplicate mark `if dup is not None` on purpose: `dup` is
# the ID itself, and `if dup` drops the mark for T000 — the one allocated ID that
# is falsy. The guard was correct and untested: T000 appeared nowhere in this
# file, and swapping it for `if dup` left every test of the owning classes green.


class TestTheZeroIdIsStillAnId(QueueTest):

    def test_two_items_under_T000_are_both_marked_as_duplicates(self):
        """The whole listing: a mark on every row says nothing, so the row that is
        NOT ambiguous has to come back unmarked in the same output."""
        self.seed(item(0, "primeira ocorrencia"), item(7, "item sozinho"),
                  item(0, "segunda ocorrencia"))
        r = self.run_tk("list")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout,
                         "T000  AUTONOMOUS     ?  primeira ocorrencia  [duplicate ID 0]\n"
                         "T007  AUTONOMOUS     ?  item sozinho\n"
                         "T000  AUTONOMOUS     ?  segunda ocorrencia  [duplicate ID 0]\n"
                         "\nduplicate IDs: only the FIRST item under each is reachable"
                         " — renumber the others by hand in next-steps.md.\n")


# --- review#4: the classifier's DEFAULT was the destructive direction -------
#
# The round before this one stopped `migrate` flattening an item's Markdown by
# classifying each continuation line: a line that OPENS a block keeps its own
# line, anything else is absorbed. The enumeration was the whole guard, and its
# default was ABSORB — so every block shape not on the list reproduced the defect
# the list was written to close, and the structure readback could not see it: it
# counted the SAME regex's hits before and after the join, so for a shape the
# regex never matched both counts were zero and the check agreed with the
# flattening it was there to stop.
#
# Four shapes were found by reading, in one round — a setext underline, a link
# reference definition, a GFM footnote definition, and a table head row written
# without its leading pipe. They are enumerated now. The fifth nobody has read
# yet is what changed the default: an absorption must be LICENSED by two
# questions the enumeration cannot answer for itself (the geometry of the break,
# and the character the line opens with), and an item neither licences is left
# exactly as it is and named in the report.
#
# Every test here asserts the WHOLE file: this command rewrites user data, and
# the defect it replays was invisible to any narrower assertion.

R4_HEAD = ("- [ ] **T005** — cabeca escrita longa o bastante para que a quebra "
           "seguinte caia numa coluna de wrap\n")
R4_CHAIN = "  **Class:** AUTONOMOUS. **Effort:** S. **Criterion:** A: x.\n"
R4_FOLDED_HEAD = (R4_HEAD.rstrip("\n") + " **Class:** AUTONOMOUS. **Effort:** S. "
                  "**Criterion:** A: x.\n")

# one entry per shape: (name, the lines between the head and the chain)
R4_SHAPES = (
    ("sublinhado setext", "  ===\n"),
    ("definicao de referencia de link", '  [ref]: https://exemplo.invalid "titulo"\n'),
    ("definicao de nota de rodape", "  [^1]: a nota de rodape\n"),
    ("tabela GFM sem pipe inicial", "  Col A | Col B\n  --- | ---\n  Val 1 | Val 2\n"),
)

# the population the fold must keep absorbing — a sentence hard-wrapped at column
# ~95, which is 7 of the 8 real items with prose between head and chain. Each line
# opens the way the real ones do: a code span, a parenthesis, an emoji, a wiki
# link, a bold run. An over-tight rule refuses these, and the item then reads with
# its field chain inside the parenthesis the wrap left open.
R4_WRAPPED = (
    "- [ ] **T006** — item cuja frase quebra no meio de um parenteses (parte um, parte dois\n"
    "  `docs/proposta.md` + `docs/regua.md` + **`docs/esquema.md`** (novo, com a faixa de\n"
    "  (diferenciacao vai pelo pro-labore futuro — posicao fixada no CONTEXT.md). Falta so\n"
    "  ✅ **`Administrativo`** concedido, conferido na leitura de volta e no dry-run do dia\n"
    "  [[nota-do-wiki]]): (a) decidir se as duas listas do vault tambem migram; (b) decidir\n"
    "  **(c)** deixou de ser trabalho manual, e a caixa de entrada foi zerada nesse mesmo dia.\n"
    "  **Class:** AUTONOMOUS. **Effort:** S. **Criterion:** A: y.\n")
R4_WRAPPED_FOLDED = (
    "- [ ] **T006** — item cuja frase quebra no meio de um parenteses (parte um, parte dois "
    "`docs/proposta.md` + `docs/regua.md` + **`docs/esquema.md`** (novo, com a faixa de "
    "(diferenciacao vai pelo pro-labore futuro — posicao fixada no CONTEXT.md). Falta so "
    "✅ **`Administrativo`** concedido, conferido na leitura de volta e no dry-run do dia "
    "[[nota-do-wiki]]): (a) decidir se as duas listas do vault tambem migram; (b) decidir "
    "**(c)** deixou de ser trabalho manual, e a caixa de entrada foi zerada nesse mesmo dia. "
    "**Class:** AUTONOMOUS. **Effort:** S. **Criterion:** A: y.\n")


class TestFoldFailsSafeOnShapesNobodyEnumerated(QueueTest):

    def migrate(self):
        r = self.run_tk("migrate")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("Traceback", r.stderr)
        return r

    def prose_refusal(self, *labels):
        return (f"{len(labels)} item(s) left exactly as they are: a line the join "
                "would absorb is not the hard-wrapped prose the fold may take, and "
                "absorbing a shape nobody recognised is how structure is lost in "
                "silence — " + ", ".join(labels)
                + ". Close each with `cancel` and re-add it clean.\n")

    # --- the four shapes the enumeration was missing ----------------------

    def test_each_shape_the_join_used_to_flatten_keeps_its_own_lines(self):
        """All four, folded AROUND instead of over: the chain reaches the first
        line, where the gates read it, and the block keeps every line it had.
        Each was measured absorbed and reported as `folded up` — a success line
        printed over destroyed structure, on a file with no other copy.

        The head is deliberately long, so the break below it is one a wrapper
        would make: the shape reading is the only thing that saves these, and a
        fixture with a short head would let the geometry answer instead and prove
        nothing about the enumeration."""
        for name, middle in R4_SHAPES:
            with self.subTest(shape=name):
                self.seed(R4_HEAD.rstrip("\n") + "\n" + middle + R4_CHAIN)
                r = self.migrate()
                self.assertIn("folded up, where every gate reads them — T005\n", r.stdout)
                self.assertEqual(self.body(), HEADER + R4_FOLDED_HEAD + middle)

    def test_the_gates_reach_an_item_folded_around_a_table_written_without_pipes(self):
        """A fold is only worth a rewrite of user data if the readers can use the
        result, and only acceptable if the table is still a table afterwards."""
        self.seed(R4_HEAD.rstrip("\n") + "\n" + R4_SHAPES[3][1] + R4_CHAIN)
        self.migrate()
        self.assertIn("T005  S", self.run_tk("pack").stdout)
        r = self.run_tk("edit", "T005", "--effort", "L")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.body(),
                         HEADER + R4_FOLDED_HEAD.replace("**Effort:** S.", "**Effort:** L.")
                         + R4_SHAPES[3][1])

    # --- and the shapes NOBODY enumerated, which is the point --------------

    def test_a_shape_no_one_enumerated_is_REFUSED_and_not_flattened(self):
        """The finding this round is about, and the only test here that would
        still hold if the four shapes above had never been added.

        `!!! note` opens an admonition in Python-Markdown and MkDocs. It is on no
        list in this file, on purpose: it stands for the shape the next reader
        writes and nobody has enumerated. The fold does not recognise it, does not
        guess, and does not touch the item — a refusal costs one command, and a
        flattened queue file has no other copy."""
        seeded = R4_HEAD.rstrip("\n") + "\n" + '  !!! note "Atencao"\n' + R4_CHAIN
        self.seed(seeded)
        r = self.migrate()
        self.assertEqual(self.body(), HEADER + seeded)
        self.assertNotIn("folded up", r.stdout)
        # the MESSAGE, not merely "the file is unchanged": a crash leaves the file
        # unchanged too, and would read here as a guard doing its job
        self.assertIn(self.prose_refusal("T005"), r.stdout)

    def test_a_shape_no_one_enumerated_that_OPENS_like_prose_is_refused_too(self):
        """The second licence, and the arm the first test cannot reach. A
        `chave: valor` metadata line opens with a letter, exactly as a wrapped
        sentence does, so nothing about its first character betrays it. What does
        is the GEOMETRY: the line above it is 30 columns wide, so the break was
        the author's and not a wrapper's, and no wrapped paragraph looks like
        that."""
        seeded = ("- [ ] **T007** — cabeca curta\n"
                  "  chave: valor\n"
                  "  **Class:** AUTONOMOUS. **Effort:** S. **Criterion:** A: x.\n")
        self.seed(seeded)
        r = self.migrate()
        self.assertEqual(self.body(), HEADER + seeded)
        self.assertIn(self.prose_refusal("T007"), r.stdout)

    # --- T168: the same shape, with the geometry licence PASSING -----------

    def test_a_metadata_line_under_a_FULL_line_is_refused_and_not_flattened(self):
        """The residue T168 decided, measured live before it was closed: the same
        `chave: valor` as the test above, but under a head long enough that the
        break reads as a wrapper's. Geometry licensed it, the opener whitelist saw
        a letter and licensed it too, and the line was joined into the head and
        reported as `folded up` — silent flattening of the user's only copy, the
        class that produced every blocker in the T121 campaign.

        Refusing it is a shape question the whitelist cannot ask, so it is asked
        separately. A real parser would not have closed this one: CommonMark reads
        the line as a lazy paragraph continuation and would absorb it exactly as
        the audit did."""
        seeded = (R4_HEAD.rstrip("\n") + "\n"
                  + "  chave: valor\n" + R4_CHAIN)
        self.seed(seeded)
        r = self.migrate()
        self.assertEqual(self.body(), HEADER + seeded)
        self.assertNotIn("folded up", r.stdout)
        self.assertIn(self.prose_refusal("T005"), r.stdout)

    def test_the_GEOMETRY_alone_refuses_a_line_no_other_rule_reaches(self):
        """The geometry arm, isolated. The `chave: valor` test above stopped
        proving it the moment METADATA_LINE_RE started refusing that fixture on
        its own — two guards over the same incident, and the second masks the
        first, which the mutation harness caught as a survivor rather than a pass.

        This fixture is reached by NO other rule: it opens with a letter (the
        whitelist licenses it), it carries no colon (the metadata rule never
        matches), and it is on no enumeration. Only the break above it betrays it —
        the head is 30 columns wide, so the author, not a wrapper, ended it."""
        seeded = ("- [ ] **T012** — cabeca curta\n"
                  "  Observacao solta do autor\n"
                  + R4_CHAIN)
        self.seed(seeded)
        r = self.migrate()
        self.assertEqual(self.body(), HEADER + seeded)
        self.assertNotIn("folded up", r.stdout)
        self.assertIn(self.prose_refusal("T012"), r.stdout)

    # --- C-15: the refusal is read by items of BOTH paths ------------------

    def test_the_refusal_names_no_line_between_a_head_and_a_chain_that_share_one(self):
        """The sentence used to open "a line between the head and the chain",
        which is the WALK's geometry and only the walk's: there the chain owns
        its own lines and the absorbed prose sits between the two. This item has
        no such line — its chain shares a line with the prose it wrapped out of,
        so the line the audit refuses IS the one carrying the chain — and the
        reader of `casa-nostra-m365` T010 went looking in their item for a line
        that does not exist in it. The reason was right; the address was written
        for the older path.

        Refused on geometry: the head is 30 columns wide, so the break under it
        is one the author made and no wrapped paragraph looks like that."""
        seeded = ("- [ ] **T010** — cabeca curta\n"
                  "  a segunda linha traz a cadeia toda. **Class:** AUTONOMOUS. "
                  "**Effort:** S. **Criterion:** A: x.\n")
        self.seed(seeded)
        r = self.migrate()
        self.assertEqual(self.body(), HEADER + seeded)
        self.assertNotIn("folded up", r.stdout)
        self.assertIn(self.prose_refusal("T010"), r.stdout)
        self.assertNotIn("between the head and the chain", r.stdout)

    def test_a_wrapped_line_that_merely_resumes_with_a_word_and_a_colon_is_prose(self):
        """The over-refusal the corpus caught before this shipped, replayed on an
        item that IS foldable — which the one it was found on was not. A real
        queue item wraps a sentence that resumes `wiki: `_wiki/...`` at 92
        columns: a word, a colon, a space, and none of it structural. There the
        shape rule alone cost no fold (the item is refused for another reason) but
        printed the wrong reason; here the same line sits in an item the fold
        would otherwise take, which is what the rule costs when it is wrong. The
        width condition is what tells the line from a metadata line, which is short
        because its author ended it."""
        middle = ("  wiki: `_wiki/organizacao/planejamento-financeiro-2025-10.md`. E a frase "
                  "segue ate a coluna de wrap\n")
        self.seed(R4_HEAD.rstrip("\n") + "\n" + middle + R4_CHAIN)
        r = self.migrate()
        self.assertIn("folded up, where every gate reads them — T005\n", r.stdout)
        self.assertEqual(self.body(),
                         HEADER + R4_HEAD.rstrip("\n") + " " + middle.strip()
                         + " **Class:** AUTONOMOUS. **Effort:** S. **Criterion:** A: x.\n")

    def test_a_colon_that_prose_really_uses_does_not_trip_the_metadata_rule(self):
        """The over-refusal direction, and the reason the rule reads the character
        AFTER the colon. A URL and a clock time both put a colon inside the first
        token of a wrapped line, and both are prose the fold must go on absorbing;
        neither is followed by a space. A key of several words is not one either —
        `Col A | Col B` already has its own rule, and widening this one to spaces
        would swallow ordinary sentences whole."""
        for name, middle in (("url", "  https://exemplo.invalid/caminho segue a frase ate o fim\n"),
                             ("hora", "  14:30 foi quando a fila virou e a frase continua\n")):
            with self.subTest(forma=name):
                self.seed(R4_HEAD.rstrip("\n") + "\n" + middle + R4_CHAIN)
                r = self.migrate()
                self.assertIn("folded up, where every gate reads them — T005\n", r.stdout)
                self.assertEqual(self.body(),
                                 HEADER + R4_HEAD.rstrip("\n") + " " + middle.strip()
                                 + " **Class:** AUTONOMOUS. **Effort:** S. "
                                   "**Criterion:** A: x.\n")

    # --- the population the fold must NOT stop absorbing -------------------

    def test_the_hard_wrapped_population_is_still_absorbed_whole(self):
        """The regression the fail-safe default could break, and the expensive one:
        7 of the 8 real items with prose between head and chain are one sentence
        hard-wrapped at column ~95. Keeping those lines lands the field chain
        inside the parenthesis the wrap left open, so `keep everything not proven
        to be prose` reads worse than the defect it replaces. Every opener the real
        corpus uses is here — code span, parenthesis, emoji, wiki link, bold run."""
        self.seed(R4_WRAPPED)
        r = self.migrate()
        self.assertIn("folded up, where every gate reads them — T006\n", r.stdout)
        self.assertEqual(self.body(), HEADER + R4_WRAPPED_FOLDED)

    def test_a_wrapped_sentence_that_merely_carries_a_pipe_is_not_a_table(self):
        """The over-refusal direction of the table rule, and why it needs the line
        BELOW: a pipe is a character prose uses. Without the lookahead the rule
        reads `a | b` in the middle of a sentence as a table head, and the item is
        folded around a line that was never a block."""
        self.seed("- [ ] **T011** — cabeca longa o bastante para que a quebra seguinte caia "
                  "numa coluna de wrap\n"
                  "  o comando imprime `folded | refused | untouched` e segue a frase ate o "
                  "fim dela.\n"
                  "  **Class:** AUTONOMOUS. **Effort:** S. **Criterion:** A: x.\n")
        r = self.migrate()
        self.assertIn("folded up, where every gate reads them — T011\n", r.stdout)
        self.assertEqual(self.body(),
                         HEADER
                         + "- [ ] **T011** — cabeca longa o bastante para que a quebra "
                           "seguinte caia numa coluna de wrap o comando imprime "
                           "`folded | refused | untouched` e segue a frase ate o fim dela. "
                           "**Class:** AUTONOMOUS. **Effort:** S. **Criterion:** A: x.\n")

    def test_the_two_verdicts_land_in_ONE_run_without_touching_each_other(self):
        """A queue holds both populations, and the report must name the item it
        could not fold beside the ones it did — a run that folded most of a queue
        and stayed silent about the rest reports success for a job half done."""
        refused = R4_HEAD.replace("T005", "T008").rstrip("\n") + "\n" \
            + '  !!! note "Atencao"\n' + R4_CHAIN
        self.seed(R4_WRAPPED, refused)
        r = self.migrate()
        self.assertEqual(self.body(), HEADER + R4_WRAPPED_FOLDED + refused)
        self.assertIn("folded up, where every gate reads them — T006\n", r.stdout)
        self.assertIn(self.prose_refusal("T008"), r.stdout)


# --- review#4: a field appended to a class-less item is unreachable forever --
#
# `real_fields` answers [] for every field while the chain names no **Class:**,
# so a field appended to such an item is a field no gate and no report may read.
# `edit --effort L` appended one anyway and printed "updated"; the `--class` that
# came next appended the anchor at the END of the line, BEHIND it; and `pack`
# went on showing the item's Effort as `?`. The refusal that already existed
# covered only the item that carried the marker ALREADY — the same trap, on the
# same population, one branch to the left.

R4_BARE = "- [ ] **T009** — legado sem classe nenhuma.\n"


class TestAFieldAppendedBeforeTheAnchorIsRefused(QueueTest):

    def test_setting_a_field_on_a_class_less_item_is_refused(self):
        self.seed(R4_BARE)
        r = self.run_tk("edit", "T009", "--effort", "L")
        self.assertEqual(self.body(), HEADER + R4_BARE)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("T009 names no **Class:** in its field chain, so an appended "
                      "**Effort:** is a field no gate and no report may read", r.stderr)
        self.assertIn("Nothing was changed", r.stderr)

    def test_the_file_and_the_reader_no_longer_disagree_about_the_field(self):
        """The whole sequence as it was measured: `--effort L` exited 0, `--class`
        exited 0, and `pack` went on printing Effort `?` over a file that said `L`.
        The file and its reader disagreeing is the finding — not the `?`.

        They agree now, and they agree the honest way: nothing was written, so
        nothing claims a value the reader cannot see. T169 closed the other half of
        that sequence, so this item's `pack` line reads `?` because it carries no
        Effort at all, which is the truth about it."""
        self.seed(R4_BARE)
        self.assertEqual(self.run_tk("edit", "T009", "--effort", "L").returncode, 1)
        self.assertEqual(self.run_tk("edit", "T009", "--class", "AUTONOMOUS").returncode, 0)
        self.assertEqual(self.body(),
                         HEADER + R4_BARE.rstrip("\n") + " **Class:** AUTONOMOUS.\n")
        self.assertNotIn("**Effort:**", self.body())
        self.assertIn("T009  ?", self.run_tk("pack").stdout)

    def test_every_field_that_is_APPENDED_is_covered_not_only_effort(self):
        """One branch, every flag that reaches it: a rule that held for --effort
        and not for --risk would leave the same trap open one flag over."""
        for flag, value, marker in (("--effort", "L", "Effort"), ("--risk", "apaga X", "Risk"),
                                    ("--criterion", "A: y", "Criterion"),
                                    ("--project", "tk", "Project")):
            with self.subTest(flag=flag):
                self.seed(R4_BARE)
                r = self.run_tk("edit", "T009", flag, value)
                self.assertEqual(self.body(), HEADER + R4_BARE)
                self.assertEqual(r.returncode, 1, r.stdout)
                self.assertIn(f"an appended **{marker}:** is a field no gate and no "
                              "report may read", r.stderr)

    def test_the_remedy_the_refusal_PRINTS_runs_and_lets_the_field_through(self):
        """A refusal is only acceptable while its remedy is reachable, so the
        printed one is run for real — literally, with the caller's own value read
        back off the message — and the field is then where `pack` reads it."""
        self.seed(R4_BARE)
        r = self.run_tk("edit", "T009", "--criterion", "A: o relatorio sai com 'aspas'")
        self.assertEqual(r.returncode, 1, r.stdout)
        printed = re.search(r"Run `tk-queue (edit .*?)` — one command", r.stderr).group(1)
        argv = shlex.split(printed.replace("<CLASS>", "AUTONOMOUS"))
        again = self.run_tk(*argv)
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertEqual(self.body(),
                         HEADER + R4_BARE.rstrip("\n")
                         + " **Class:** AUTONOMOUS. **Criterion:** A: o relatorio sai com "
                           "'aspas'.\n")

    def test_class_first_in_ONE_call_lands_the_field_inside_the_chain(self):
        """The over-refusal direction: the rule may not lock out the call that is
        already correct. `--class` is applied before every other flag, so one
        command gives the item its anchor and its fields in the right order."""
        self.seed(R4_BARE)
        r = self.run_tk("edit", "T009", "--effort", "L", "--class", "AUTONOMOUS")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.body(),
                         HEADER + R4_BARE.rstrip("\n")
                         + " **Class:** AUTONOMOUS. **Effort:** L.\n")
        self.assertIn("T009  L", self.run_tk("pack").stdout)

    def test_an_anchored_item_is_untouched_by_the_rule(self):
        """Every item `add` writes carries a class, so a rule that reached them
        would refuse the whole queue."""
        seeded = item(1, "um")
        self.seed(seeded)
        r = self.run_tk("edit", "T001", "--project", "tk")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("**Project:** tk.", self.body())


# --- T169: the class anchor goes AHEAD of the chain the item already carries --
#
# `real_fields` measures every field from the **Class:** the chain begins at, and
# `edit --class` wrote that anchor at the END of the first line. So an item with no
# class but with REAL fields — exactly what `migrate` produces when it folds a
# continuation line up — came out of its own repair with every field stranded
# before the anchor, unreadable to every gate and every report, for ever. Measured
# end to end, three commands, each exiting 0 and printing success:
#
#   migrate                        "1 item(s) with fields off the first line: folded up"
#   pack                           "no **Class:** at all: `tk-queue edit <id> --class ...`"
#   edit T031 --class AUTONOMOUS   "T031 updated"
#   pack                           T031  ?          <- the Effort the file states is M
#
# The remedy in the second line is `pack`'s own, which is what made the trap a
# straight road rather than a corner. The anchor now goes ahead of the run, which
# is the position `compose_item` writes it in — the POSITION, not the whole item:
# `add` also stamps a **Born:** the repair never writes and normalises the field
# ORDER the repair preserves, so "byte-identical to one `add` would have written",
# which this comment and a test name both used to claim, is false and was measured
# false. And the price, an item whose own prose wears a field's shape being
# promoted with the rest, is announced on stderr rather than guessed at.
#
# The first review of this slice measured two things the anchor alone did not
# close, and both are below:
#
#   the promotion feeds the SAME call   the anchor makes every promoted segment a
#                                       real field for the rest of `cmd_edit`'s flag
#                                       loop, so `--class X --project tk` OVERWROTE
#                                       four words of a title and `--class X --risk
#                                       none` DELETED a segment whole, each rc 0
#   the trap survived one shape         a class-less item still UNFOLDED gets the
#                                       anchor appended to a chain-less first line,
#                                       which strands the continuation fields AND
#                                       stops `migrate` from ever folding them —
#                                       the same dead end, reached by the same
#                                       `pack` remedy, in the other order

T169_FOLDED = ("- [ ] **T031** — item legado sem classe **Effort:** M. "
               "**Criterion:** A: x. **Source:** 2026-08-13\n")
T169_UNFOLDED = ("- [ ] **T031** — item legado sem classe\n"
                 "  **Effort:** M. **Criterion:** A: x. **Source:** 2026-08-13\n")
T169_BARE = "- [ ] **T032** — legado sem campo nenhum.\n"
T169_PROSE = ("- [ ] **T033** — item, cita o **Project:** de outra fila inteira. "
              "**Effort:** M.\n")


class TestTheClassLandsAheadOfTheChain(QueueTest):

    def test_the_anchor_goes_ahead_of_the_fields_already_on_the_line(self):
        """The file first, whole: where the anchor LANDS is the finding, and the
        `?` is only how a reader meets it."""
        self.seed(T169_FOLDED)
        r = self.run_tk("edit", "T031", "--class", "AUTONOMOUS")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.body(), HEADER + T169_FOLDED.replace(
            "sem classe **Effort:**", "sem classe **Class:** AUTONOMOUS. **Effort:**"))
        pack = self.run_tk("pack").stdout
        self.assertIn("T031  M", pack)
        self.assertNotIn("T031  ?", pack)

    def test_the_anchor_lands_where_add_puts_it_and_the_item_is_not_identical(self):
        """The anchor's POSITION is what the repair shares with `add`, and the
        prefix is read off a REAL `add` rather than a literal — a literal cannot
        drift when `compose_item` does, which is the whole failure a test named
        for that function is supposed to catch.

        The second half is the correction: "byte-identical to one `add` would have
        written" was asserted by this test's old name and by the source comment,
        and it is false. `add` stamps **Born:** and writes the fields in
        `compose_item`'s order; the repair writes neither. Asserted, so the claim
        cannot come back."""
        self.seed(T169_FOLDED)
        self.assertEqual(self.run_tk("edit", "T031", "--class", "AUTONOMOUS").returncode, 0)
        self.assertEqual(
            self.body(),
            HEADER + "- [ ] **T031** — item legado sem classe **Class:** AUTONOMOUS. "
                     "**Effort:** M. **Criterion:** A: x. **Source:** 2026-08-13\n")
        repaired = next(l for l in self.body().splitlines() if "**T031**" in l)
        r = self.run_tk("add", "item legado sem classe", "--class", "AUTONOMOUS",
                        "--effort", "M", "--criterion", "A: x")
        self.assertEqual(r.returncode, 0, r.stderr)
        added = next(l for l in self.body().splitlines() if "**T032**" in l)
        body = lambda line: line.split("** — ", 1)[1]
        # everything `compose_item` writes up to the field AFTER the anchor: the
        # item's text, then `**Class:** AUTONOMOUS. ` — the repair must open the
        # same way, whatever compose_item does to that prefix later
        lead = body(added).split("**Effort:**")[0]
        self.assertEqual(lead, "item legado sem classe **Class:** AUTONOMOUS. ")
        self.assertTrue(body(repaired).startswith(lead), body(repaired))
        # and the rest is NOT the same item
        self.assertNotEqual(body(repaired), body(added))
        self.assertIn("**Born:**", added)
        self.assertNotIn("**Born:**", repaired)

    def test_a_promotion_ENDS_the_call_instead_of_feeding_the_next_flag(self):
        """The destruction the anchor opened, in one command, measured both ways.

        The anchor promotes the run, and every later iteration of the flag loop
        then reads that run as real fields — so the same command that made the
        item's own prose a **Project:** goes on to overwrite it, and `--risk none`
        deletes it whole. Before this refusal both exited 0 and printed "updated".
        The warning cannot stand in for the refusal: it fires in the same run and
        its remedy is `cancel` + re-add, which is advice about a copy that is
        already gone."""
        for flags, gone in ((("--project", "tk"), "de outra fila inteira"),
                            (("--risk", "none"), "de outra fila inteira")):
            with self.subTest(flags=flags):
                self.seed(T169_PROSE)
                r = self.run_tk("edit", "T033", "--class", "AUTONOMOUS", *flags)
                self.assertEqual(r.returncode, 1, r.stdout)
                self.assertIn("Nothing was changed", r.stderr)
                self.assertIn("**Project:**, **Effort:**", r.stderr)
                # the file, whole: this command rewrites user data and the defect
                # it replays survives any narrower assertion
                self.assertEqual(self.body(), HEADER + T169_PROSE)
                self.assertIn(gone, self.body())

    def test_the_refusals_remedy_runs_and_the_two_commands_land_the_field(self):
        """A refusal is only acceptable while its remedy is reachable, so the two
        commands the message prints are run in order and the field lands.

        The population is the one where the promoted run really IS fields — the
        folded legacy item — because that is the item for which the answer is
        "run them apart", not `cancel` + re-add."""
        self.seed(T169_FOLDED)
        r = self.run_tk("edit", "T031", "--class", "AUTONOMOUS", "--effort", "L")
        self.assertEqual(r.returncode, 1, r.stdout)
        printed = re.findall(r"`tk-queue ([^`]+)`", r.stderr)
        argv = shlex.split(printed[0].replace("<id>", "T031"))
        first = self.run_tk(*argv)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertIn("warning:", first.stderr)
        second = self.run_tk("edit", "T031", "--effort", "L")
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertIn("**Class:** AUTONOMOUS. **Effort:** L.", self.body())
        self.assertIn("T031  L", self.run_tk("pack").stdout)

    def test_the_class_alone_is_still_taken_by_the_same_item(self):
        """The over-refusal direction of the rule above: refusing the whole call
        whenever a promotion happens would lock `--class` out of the population it
        was written for."""
        self.seed(T169_PROSE)
        r = self.run_tk("edit", "T033", "--class", "AUTONOMOUS")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("de outra fila inteira", self.body())

    def test_the_promotion_warning_waits_for_the_write_to_commit(self):
        """Compose, check, act — the order every other gate in this file keeps.
        Printed before the write, the warning announced in the PAST TENSE a
        promotion `check_ceiling` then refused: exit 1, file untouched, and a
        caller told the class had gone ahead of a run it never moved.

        `--text` is the flag that reaches this, and after the refusal above it is
        the only one that does: it is measured against the BLOCK ceiling and it is
        not one of the flags the loop locates in the chain, so it rides along with
        `--class` where `--project` and `--risk` are now refused."""
        self.seed(T169_PROSE)
        r = self.run_tk("edit", "T033", "--text", "x" * 700, "--class", "AUTONOMOUS")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ceiling", r.stderr.lower())
        self.assertNotIn("went AHEAD", r.stderr)
        self.assertEqual(self.body(), HEADER + T169_PROSE)

    def test_a_class_less_item_still_UNFOLDED_is_refused_and_told_the_order(self):
        """The trap on the shape the anchor did not reach, read off `pack` and run
        verbatim — the order this time is `pack` FIRST, which is the order `pack`
        itself induces and the one the old test never exercised.

        With nothing on the first line to sit ahead of, the anchor is APPENDED
        there and the item's real fields stay on the continuation line: unreadable
        to every gate, and now unfoldable, since `fold_chain_onto_first_line`
        returns early on an item whose chain reaches a **Class:**. Measured before
        this refusal: `pack` printed `edit <id> --class AUTONOMOUS`, that command
        exited 0 with no warning at all, and `pack` then listed T031 ELIGIBLE with
        Effort `?` — a candidate for an unattended package whose own fields nothing
        can read."""
        self.seed(T169_UNFOLDED, log="")
        pack = self.run_tk("pack").stdout
        self.assertIn("T031  item legado sem classe  — no **Class:** field, and its "
                      "fields sit off the first line", pack)
        printed = next(l for l in pack.splitlines() if l.startswith("- no **Class:**"))
        first, second = [shlex.split(c.replace("<id>", "T031"))
                         for c in re.findall(r"`tk-queue ([^`]+)`", printed)]
        # the class, run before the fold the line names, is REFUSED — and the file
        # is exactly as it was
        early = self.run_tk(*second)
        self.assertEqual(early.returncode, 1, early.stdout)
        self.assertIn("Fold first", early.stderr)
        self.assertEqual(self.body(), HEADER + T169_UNFOLDED)
        # and the printed order works
        self.assertEqual(self.run_tk(*first).returncode, 0)
        self.assertEqual(self.run_tk(*second).returncode, 0)
        after = self.run_tk("pack").stdout
        self.assertIn("T031  M", after)
        self.assertNotIn("T031  ?", after)

    def test_the_claims_diagnosis_names_the_fold_before_the_class(self):
        """`claim` prescribes `edit --class` for a class-less item, and that command
        is now refused for this shape — a remedy that is itself refused is the dead
        end this file has already paid for once."""
        self.seed(T169_UNFOLDED)
        r = self.run_tk("claim", "T031", "--as", "afk-host")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("`tk-queue migrate`", r.stderr)
        argv = shlex.split(re.search(r"`tk-queue (migrate)`", r.stderr).group(1))
        self.assertEqual(self.run_tk(*argv).returncode, 0)
        self.assertEqual(self.run_tk("edit", "T031", "--class", "AUTONOMOUS").returncode, 0)
        again = self.run_tk("claim", "T031", "--as", "afk-host")
        self.assertEqual(again.returncode, 0, again.stderr)

    def test_an_item_whose_note_merely_QUOTES_a_marker_is_covered_too(self):
        """The other half of the same shape, and the reason the refusal does not
        promise the fold: a continuation line that is prose quoting a marker is
        refused by `migrate` as well, so the message names `cancel` + re-add as the
        way out and both commands say the same thing."""
        seeded = ("- [ ] **T031** — item legado sem classe\n"
                  "  ver a **Risk:** nota antiga, que ninguém escreveu como campo\n")
        self.seed(seeded, log="")
        r = self.run_tk("edit", "T031", "--class", "AUTONOMOUS")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("`cancel` and re-add", r.stderr)
        self.assertEqual(self.body(), HEADER + seeded)
        # `migrate` will not fold it either — the message never promised it would
        m = self.run_tk("migrate")
        self.assertEqual(m.returncode, 0, m.stderr)
        self.assertEqual(self.body(), HEADER + seeded)

    def test_the_whole_trap_from_the_continuation_line_through_packs_own_remedy(self):
        """The three commands as they were measured, with the repair read OFF
        `pack`'s output and run verbatim — a remedy a command prints is code, and
        this one produced the unreadable item it was printed to prevent.

        The age is asserted too: **Source:** is in that stranded run, so `migrate`
        could not backdate the item either, and `list` showed `?` beside the `?`
        `pack` showed."""
        self.seed(T169_UNFOLDED, log="")
        self.assertEqual(self.run_tk("migrate").returncode, 0)
        pack = self.run_tk("pack").stdout
        self.assertIn("T031  item legado sem classe  — no **Class:** field", pack)
        printed = next(l for l in pack.splitlines() if "no **Class:** at all" in l)
        argv = shlex.split(re.search(r"`tk-queue (.+?)`", printed).group(1)
                           .replace("<id>", "T031"))
        again = self.run_tk(*argv)
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertIn("T031  M", self.run_tk("pack").stdout)
        # and the **Source:** the fold left unreadable is reachable again
        self.assertEqual(self.run_tk("migrate").returncode, 0)
        self.assertRegex(self.run_tk("list").stdout, r"T031  AUTONOMOUS\s+\d+d")

    def test_a_field_already_on_the_line_is_WRITABLE_after_the_repair(self):
        """Readable is not the whole claim: the position rule gates the writers
        too, so the repaired item must accept an ordinary `--effort`."""
        self.seed(T169_FOLDED)
        self.assertEqual(self.run_tk("edit", "T031", "--class", "AUTONOMOUS").returncode, 0)
        r = self.run_tk("edit", "T031", "--effort", "L")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("**Effort:** L.", self.body())
        self.assertNotIn("**Effort:** M.", self.body())
        self.assertIn("T031  L", self.run_tk("pack").stdout)

    def test_an_item_with_no_chain_still_gets_its_class_APPENDED(self):
        """The over-refusal direction, and the population the flag was written for:
        with nothing on the line to sit ahead of, the anchor is appended and becomes
        the chain. Nothing is announced, because nothing was promoted."""
        self.seed(T169_BARE)
        r = self.run_tk("edit", "T032", "--class", "BLOCKED")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.body(),
                         HEADER + T169_BARE.rstrip("\n") + " **Class:** BLOCKED.\n")
        self.assertNotIn("warning", r.stderr)

    def test_the_promotion_is_ANNOUNCED_and_names_the_segments(self):
        """The price of the position, paid out loud. This item's title quotes
        `**Project:**` and the anchor makes those four words a Project value, so the
        warning names every segment the anchor now leads — the caller reads its own
        prose in that list and knows to `cancel` + re-add instead."""
        self.seed(T169_PROSE)
        r = self.run_tk("edit", "T033", "--class", "AUTONOMOUS")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("warning:", r.stderr)
        self.assertIn("**Project:**, **Effort:**", r.stderr)
        self.assertIn("`cancel` + re-add", r.stderr)
        # and the warning is not decoration: this is exactly what it warned about.
        # `list` groups by **Project:**, so the item is now filed under a project
        # called `de` and its title is cut at the marker
        listing = self.run_tk("list").stdout
        self.assertIn("## de", listing)
        self.assertIn("T033  AUTONOMOUS", listing)
        self.assertNotIn("de outra fila inteira", listing)


# --- review#5: the setext protection was asymmetric -------------------------
#
# `opens_a_block` recognised the setext UNDERLINE and kept it, and never looked
# BACK at the title line the underline retroactively turns into a heading. That
# title is plain prose by its first character and past the wrap column by its
# geometry, so both of `absorption_audit`'s licences passed it and the fold
# absorbed it — leaving the heading text merged into unrelated prose AND the
# underline orphaned, underlining nothing, reported as `folded up`.
#
# The repair is the lookahead the table-head rule already had, read from the
# other side: if the NEXT line is a setext underline, THIS line belongs to that
# block. Every test below asserts the WHOLE file — this command rewrites user
# data, and the defect it replays survives any narrower assertion.

R5_LONG_HEAD = ("- [ ] **T005** — cabeca do item que e uma frase longa o suficiente "
                "para passar da coluna de wrap sem duvida nenhuma\n")
R5_FOLDED_HEAD = (R5_LONG_HEAD.rstrip("\n")
                  + " **Class:** AUTONOMOUS. **Effort:** S. **Criterion:** A: x.\n")


class TestASetextTitleIsKeptWithItsUnderline(QueueTest):

    def migrate(self):
        r = self.run_tk("migrate")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("Traceback", r.stderr)
        return r

    def test_the_title_the_underline_promotes_keeps_its_own_line(self):
        """Both spellings of the underline, each measured absorbed: `===`, which
        is only ever a setext underline, and `---`, which is a setext H2 here and
        a thematic break after a blank. The reading is stated in `opens_a_block`;
        what this asserts is that neither spelling leaves the title behind."""
        for name, rule in (("igual", "  ===============\n"),
                           ("hifen", "  ---------------\n")):
            with self.subTest(sublinhado=name):
                middle = "  Titulo da secao\n" + rule
                self.seed(R5_LONG_HEAD + middle + R4_CHAIN)
                r = self.migrate()
                self.assertIn("folded up, where every gate reads them — T005\n", r.stdout)
                self.assertEqual(self.body(), HEADER + R5_FOLDED_HEAD + middle)

    def test_the_gates_reach_the_item_folded_around_the_heading(self):
        """A fold is only worth rewriting user data if the readers can use the
        result — and only acceptable if the heading is still a heading after."""
        middle = "  Titulo da secao\n  ===============\n"
        self.seed(R5_LONG_HEAD + middle + R4_CHAIN)
        self.migrate()
        self.assertIn("T005  S", self.run_tk("pack").stdout)
        r = self.run_tk("edit", "T005", "--effort", "L")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.body(),
                         HEADER + R5_FOLDED_HEAD.replace("**Effort:** S.", "**Effort:** L.")
                         + middle)

    def test_an_ordinary_hard_wrapped_line_is_STILL_absorbed(self):
        """The regression the lookahead could buy, and the expensive one: the same
        title line, with no underline under it, is ordinary wrapped prose and must
        go on being absorbed. A rule that kept it would cost the fold the very
        population it exists for — 7 of the 8 real items with prose between head
        and chain are one sentence hard-wrapped at column ~95."""
        self.seed(R5_LONG_HEAD + "  Titulo da secao\n" + R4_CHAIN)
        r = self.migrate()
        self.assertIn("folded up, where every gate reads them — T005\n", r.stdout)
        self.assertEqual(self.body(),
                         HEADER + R5_LONG_HEAD.rstrip("\n")
                         + " Titulo da secao **Class:** AUTONOMOUS. **Effort:** S. "
                           "**Criterion:** A: x.\n")

    def test_the_whole_hard_wrapped_population_is_still_absorbed_whole(self):
        """The same direction, on the real corpus's own shapes rather than one
        line: every opener the queues use, none of them followed by an underline."""
        self.seed(R4_WRAPPED)
        r = self.migrate()
        self.assertIn("folded up, where every gate reads them — T006\n", r.stdout)
        self.assertEqual(self.body(), HEADER + R4_WRAPPED_FOLDED)


# --- review#5: `--<field> none` on a class-less item printed success ---------
#
# The refusal that stopped a field being APPENDED where no reader may honour it
# sits on the branch that WRITES. The three clearable flags take an early
# `continue` above it, so they never reached it: `edit T009 --risk none` on a
# class-less item printed "T009 updated" and left the file byte-identical, and so
# did `--env none` and `--deferred none` — three commands exiting 0 over a file
# none of them touched, which is the pattern the append refusal exists to close.


class TestClearingOnAClassLessItemIsRefused(QueueTest):

    def refusal(self, field):
        return (f"T009 names no **Class:** in its field chain, so no segment of that "
                f"chain is a real **{field}:** for any reader")

    def test_every_clearable_flag_is_refused_and_says_so(self):
        """One branch, all three flags that reach it: a rule that held for --risk
        and not for --env would leave the same trap open one flag over.

        The MESSAGE is asserted, not merely a nonzero exit — a mutant that CRASHES
        also exits nonzero and also leaves the file alone, and would read here as
        the guard doing its job."""
        for flag, field in (("--risk", "Risk"), ("--env", "Env"),
                            ("--deferred", "Deferred")):
            with self.subTest(flag=flag):
                self.seed(R4_BARE)
                r = self.run_tk("edit", "T009", flag, "none")
                self.assertEqual(self.body(), HEADER + R4_BARE)
                self.assertEqual(r.returncode, 1, r.stdout)
                self.assertIn(self.refusal(field), r.stderr)
                self.assertIn("it is the flag that DELETES", r.stderr)
                self.assertIn("Nothing was changed", r.stderr)
                self.assertNotIn("T009 updated", r.stdout)

    def test_the_remedy_the_refusal_PRINTS_runs_and_leaves_the_item_anchored(self):
        """A refusal is acceptable only while its remedy is reachable, so the
        printed one is run for real — read back off the message, not retyped."""
        for flag, field in (("--risk", "Risk"), ("--env", "Env"),
                            ("--deferred", "Deferred")):
            with self.subTest(flag=flag):
                self.seed(R4_BARE)
                r = self.run_tk("edit", "T009", flag, "none")
                self.assertEqual(r.returncode, 1, r.stdout)
                printed = re.search(r"Run `tk-queue (edit .*?)` — one command",
                                    r.stderr).group(1)
                argv = shlex.split(printed.replace("<CLASS>", "AUTONOMOUS"))
                again = self.run_tk(*argv)
                self.assertEqual(again.returncode, 0, again.stderr)
                self.assertEqual(self.body(),
                                 HEADER + R4_BARE.rstrip("\n")
                                 + " **Class:** AUTONOMOUS.\n")
                self.assertNotIn(f"**{field}:**", self.body())

    def test_an_anchored_item_still_CLEARS_the_field_it_carries(self):
        """The over-refusal direction, and the one that would break the command
        outright: the rule may only reach the item with no anchor."""
        self.site(SITE)
        seeded = ("- [ ] **T001** — item normal **Class:** AUTONOMOUS. **Effort:** S. "
                  "**Risk:** apaga X. **Env:** bravo. **Criterion:** A: x.\n")
        self.seed(seeded)
        r = self.run_tk("edit", "T001", "--risk", "none", "--env", "none")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.body(),
                         HEADER + "- [ ] **T001** — item normal **Class:** AUTONOMOUS. "
                                  "**Effort:** S. **Criterion:** A: x.\n")

    def test_an_anchored_item_with_nothing_to_clear_is_untouched_and_reported(self):
        """The neighbouring population, asserted so the refusal's edge is on the
        record: an ANCHORED item with no Risk at all still answers "updated" and
        is left byte-identical. The chain anchors, so `real_fields` really did
        look and really did find none — which is the difference this rule is
        about, and the residue the refusal deliberately does not extend to."""
        seeded = item(1, "um")
        self.seed(seeded)
        r = self.run_tk("edit", "T001", "--risk", "none")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.body(), HEADER + seeded)


# --- T172: `migrate --dry-run`, the preview a file with no other copy earns ---
#
# `migrate` rewrites next-steps.md — the one file holding the user's own prose,
# with no other copy — and it had no preview: the only way to see what it would
# do to a 200-item queue was to let it do it. The guard while that was missing
# was a sentence in a skill ("do not run `migrate` on a real queue"), which is
# advice, not a guard.
#
# Two claims, each asserted the hard way. "Writes NOTHING" is proved on the
# BYTES of every file in the memory dir, before and against after — not on the
# queue's text, which passes just as happily against a done-log this command
# conjured out of a template, and not on one file, because this command writes
# two and deletes a third. "The SAME report" is proved by running the preview
# and the real run over one queue and comparing stdout for equality — which is
# also the second proof of the first claim: a preview that had written anything
# would leave the real run a different queue to report on.

# The enumeration the banner and `--help` both derive from one constant in the
# script. Pinned here so the two sites cannot drift apart in silence: the lens
# campaign found this same claim out of sync in five prose sites, and the banner
# was the one an operator actually reads — it said "nothing is written" while a
# preview on a queue with no `next-steps.md` left an empty lock behind.
DRY_RUN_WRITES = ("no queue, no done-log and no briefing — only an empty "
                  "`.tk-queue.lock`, which never carries a byte")
DRY_RUN_BANNER = (f"tk-queue: --dry-run: writes {DRY_RUN_WRITES}. The report below is "
                  "what a real `migrate` prints, on this queue, right now")


class TestMigrateDryRun(HandoffTest):
    """One fixture carrying every effect `migrate` has: an `[x]` item that moves
    to the done-log and drags a briefing out with it, an item whose chain folds,
    an ID-less item that gets numbered, and an item the fold refuses and names."""

    REFUSED = ("- [ ] **T003** — nota depois dos campos\n"
               "  **Class:** AUTONOMOUS. **Effort:** S. **Source:** 2026-08-13\n"
               "  nota solta depois dos campos.\n")
    IDLESS = ("- [ ] legado sem ID\n"
              "  **Class:** AUTONOMOUS. **Effort:** S. **Source:** 2026-08-13\n")
    IDLESS_MIGRATED = ("- [ ] **T008** — legado sem ID **Class:** AUTONOMOUS. "
                       "**Effort:** S. **Born:** 2026-08-13. **Source:** 2026-08-13\n")
    ANCHOR = "anchor [[handoff-T005]] e [[handoff-T006]]"

    def seed_everything(self):
        """T005 is ticked after the briefings are written, so the run closes it:
        that is what makes the [x] move, the done-log write and the collection all
        happen in one command. TWO briefings, because the collection prints two
        different lines — one removed, one kept for the sibling that still reaches
        it — and both belong under the report the criterion compares."""
        self.seed(item(5, self.ANCHOR), item(6, "irmao [[handoff-T006]]"),
                  FOLD_LEGACY, self.IDLESS, self.REFUSED)
        # written by the real command, not by hand: the briefing is prose with a
        # header this collection reads back, and a hand-made one is a file the
        # collector would leave alone for not being its own
        for iid in (5, 6):
            self.handoff(iid, "--objective", "o", "--state", "s", "--blockers", "b")
        self.write("next-steps.md",
                   self.body().replace("- [ ] **T005**", "- [x] **T005**", 1))

    def migrated_body(self):
        """The file the real run leaves, whichever way it was reached — spelled
        once, so the two tests that assert it cannot drift apart."""
        return (HEADER + item(6, "irmao [[handoff-T006]]", born="2026-08-13")
                + FOLD_CANONICAL + self.IDLESS_MIGRATED + self.REFUSED)

    def snapshot(self):
        """Every file in the memory dir, by NAME and by BYTES. The names matter as
        much as the bytes: on a queue with no done-log yet, this command's write is
        the CREATION of one, and a comparison of contents alone never sees a file
        that existed on neither side."""
        out = {}
        for name in sorted(os.listdir(self.mem)):
            with open(os.path.join(self.mem, name), "rb") as f:
                out[name] = hashlib.sha256(f.read()).hexdigest()
        return out

    # --- claim 1: the report is the real run's report ---------------------

    def test_the_report_is_the_real_runs_report_character_for_character(self):
        """The preview and the run it previews, over ONE queue, stdout against
        stdout. `assertIn` on a "would fold" line would pass on a report that named
        half the items — this is the whole of it, in order, to the character."""
        self.seed_everything()
        dry = self.run_tk("migrate", "--dry-run")
        self.assertEqual(dry.returncode, 0, dry.stderr)
        self.assertNotIn("Traceback", dry.stderr)
        real = self.run_tk("migrate")
        self.assertEqual(real.returncode, 0, real.stderr)
        self.assertEqual(dry.stdout, real.stdout)
        # and not empty agreement: every population this fixture carries is named,
        # so two silent runs could never pass this by agreeing about nothing
        self.assertEqual(dry.stdout,
                         "1 [x] item(s) → done-log; IDs assigned up to T008\n"
                         "2 item(s) with fields off the first line: folded up, where "
                         "every gate reads them — T007, T008\n"
                         "1 item(s) left exactly as they are: folding would have to "
                         "GUESS which text is a field value — T003. Close each with "
                         "`cancel` and re-add it clean.\n"
                         "2 item(s) backdated from **Source:** — T006, T008\n"
                         "1 item(s) left with no age: a **Source:** stating no "
                         "`YYYY-MM-DD` date (a `20/08` has no year, and inferring one "
                         "is inventing) — T007. Nothing here invents one.\n"
                         "1 item(s) left with no age: a **Source:** no reader may use "
                         "— off the first line, or ahead of the **Class:** anchor "
                         "(`migrate` reports the repair separately) — T003. Nothing "
                         "here invents one.\n"
                         "handoff-T006.md kept — still reached by T006\n"
                         "handoff-T005.md removed\n")

    # --- claim 2: nothing is written -------------------------------------

    def test_the_preview_leaves_every_file_in_the_dir_byte_identical(self):
        """Both files this command writes and the one it deletes, hashed together.
        The queue's own text is the least of it: the done-log write and the
        briefing's removal are the two effects a next-steps assertion cannot see."""
        self.seed_everything()
        before = self.snapshot()
        r = self.run_tk("migrate", "--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.snapshot(), before)

    def test_the_done_log_this_run_would_CREATE_is_not_created(self):
        """The write no content comparison can see. With no done-log in the dir the
        command builds one from a template, so a preview that wrote would leave
        behind a log the user never asked for, listing items still in the queue."""
        self.seed_everything()
        log = os.path.join(self.mem, "done-log.md")
        self.assertFalse(os.path.exists(log))
        self.run_tk("migrate", "--dry-run")
        self.assertFalse(os.path.exists(log))
        # the control that says this assertion is about the FLAG and not about a
        # command that never writes a log at all
        self.run_tk("migrate")
        self.assertIn(self.ANCHOR, self.body("done-log.md"))

    def test_the_only_file_a_preview_brings_into_existence_is_the_empty_lock(self):
        """The exception, pinned rather than left for a reader to trip over. The
        preview holds the queue's exclusive lock exactly as the real run does —
        reading a queue another writer is mid-rewrite of would preview a state that
        never existed — and taking that lock creates `.tk-queue.lock` where a
        never-written queue has none. It is created EMPTY and never written to, so
        "byte for byte identical" still holds of every file that carries content;
        this asserts that it is the ONE name that can appear, and that it is 0 bytes.

        The fixture carries an `[x]` item on purpose: on a queue with nothing to
        close, the real run writes no done-log either, and the delta would exclude
        a name that was never in play. No briefing here, because writing one runs a
        mutating command that would create the lock before the comparison starts."""
        self.seed("- [x] **T005** — legado feito\n\n", FOLD_LEGACY)
        before = set(os.listdir(self.mem))
        self.assertNotIn(".tk-queue.lock", before)
        self.run_tk("migrate", "--dry-run")
        self.assertEqual(set(os.listdir(self.mem)) - before, {".tk-queue.lock"})
        self.assertEqual(os.path.getsize(os.path.join(self.mem, ".tk-queue.lock")), 0)

    def test_the_briefing_the_report_calls_removed_is_still_on_disk(self):
        """A delete is the one effect no rerun undoes. The report still says
        "removed" — it is the real run's report, character for character — so the
        file on disk is the only thing that tells the preview from the run."""
        self.seed_everything()
        r = self.run_tk("migrate", "--dry-run")
        self.assertIn("handoff-T005.md removed\n", r.stdout)
        self.assertIsNotNone(self.brief(5))
        self.run_tk("migrate")
        self.assertIsNone(self.brief(5))

    # --- how the preview says what it is, without touching the report -----

    def test_the_preview_announces_itself_on_stderr_and_never_on_stdout(self):
        """stdout has to equal the real run's byte for byte, so the one line that
        says "this changed nothing" travels beside it — on stderr, where the
        resolved queue dir already goes, and it goes AFTER that line, not instead."""
        self.seed_everything()
        r = self.run_tk("migrate", "--dry-run")
        self.assertIn(f"tk-queue: queue: {self.mem}", r.stderr)
        self.assertIn(DRY_RUN_BANNER, r.stderr)
        self.assertNotIn("--dry-run", r.stdout)
        self.assertNotIn(DRY_RUN_BANNER, self.run_tk("migrate").stderr)

    def test_the_help_carries_the_same_enumeration_as_the_banner(self):
        """Banner and `--help` are the two sites a machine can hold in step, and
        they derive from one constant for exactly that reason. A future writer who
        re-inlines either one drifts from the other in silence, which is the
        mechanism the campaign kept finding: pin both to the same words."""
        help_text = " ".join(self.run_tk("migrate", "--help").stdout.split())
        self.assertIn(" ".join(DRY_RUN_WRITES.split()), help_text,
                      "`--help` no longer says what the banner says")

    def test_the_real_run_after_the_preview_still_does_the_whole_job(self):
        """The mask this flag could grow: a preview that half-wrote would hand the
        real run a job already partly done, and every assertion about the real run
        would pass on a queue that two commands built between them. The whole file,
        after the pair, is the only assertion that cannot be satisfied that way."""
        self.seed_everything()
        self.run_tk("migrate", "--dry-run")
        r = self.run_tk("migrate")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.body(), self.migrated_body())

    def test_without_the_flag_migrate_writes_exactly_as_it_did(self):
        """The flag is OFF by default, and the default is the destructive one: a
        `--dry-run` that defaulted to true would turn every documented invocation —
        the skill's, the contract's, this suite's — into a silent no-op that reports
        success. Same fixture, no flag, compared against the same expected file."""
        self.seed_everything()
        before = self.snapshot()
        r = self.run_tk("migrate")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotEqual(self.snapshot(), before)
        self.assertEqual(self.body(), self.migrated_body())
        self.assertIsNone(self.brief(5))
        self.assertIsNotNone(self.brief(6))


# --- T148: the item's birth date, and the age it gives the queue ----------
# 8 of the 32 items in the queue that motivated this had been standing there
# unmoved, the oldest for six days, and nothing anywhere said so: "old" was
# reconstructed by hand from whatever an item's prose happened to mention. The
# field is the stamp; `list` is the reader; `migrate` is what keeps the ages of
# the items that predate both from all starting on the day of the deploy.

def legacy(iid, text, source, born=None):
    """A canonical item with an arbitrary **Source:** — the field `migrate` reads
    a birth date off. `item()` hard-codes a date there; these tests are about the
    values that are NOT one."""
    born_field = f" **Born:** {born}." if born else ""
    return (f"- [ ] **T{iid:03d}** — {text} **Class:** AUTONOMOUS. **Effort:** S. "
            f"**Criterion:** A: x.{born_field} **Source:** {source}\n")


class TestBirthDate(QueueTest):
    """`add` stamps what it witnesses; `migrate` reads what an older item wrote
    down about itself. Neither ever guesses — an item with no date says so."""

    def test_a_new_item_is_born_with_todays_date(self):
        """Asserted in the file's real format, not through a helper: the stamp has
        to land IN the field chain, right before **Source:**, or `list` reads no
        age off an item the command reported as added."""
        self.seed()
        today = datetime.date.today().isoformat()
        r = self.run_tk("add", "nascido hoje", "--class", "AUTONOMOUS",
                        "--effort", "S", "--criterion", "A: x")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(f"**Criterion:** A: x. **Born:** {today}. **Source:** {today}\n",
                      self.body())

    def test_the_stamp_is_the_day_of_the_add_and_not_what_source_says(self):
        """`--source` is provenance and may name any moment; the item still entered
        this queue today. Backdating is `migrate`'s job and nothing else's."""
        self.seed()
        today = datetime.date.today().isoformat()
        r = self.run_tk("add", "pensado em julho", "--class", "AUTONOMOUS",
                        "--effort", "S", "--criterion", "A: x",
                        "--source", "conversa de 2026-07-02")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(f"**Born:** {today}. **Source:** conversa de 2026-07-02",
                      self.body())


class TestMigrateBackdates(QueueTest):
    BACKDATED = "item(s) backdated from **Source:** — "

    def migrate(self):
        r = self.run_tk("migrate")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("Traceback", r.stderr)
        return r

    def test_a_source_that_states_a_date_backdates_the_item(self):
        """The year is written down, so nothing is inferred — including when the
        date sits inside a sentence, which is how most of the real queue spells
        it (`PR #63, 2026-08-13`)."""
        self.seed(legacy(1, "achado na review", "PR #63, 2026-08-13"))
        r = self.migrate()
        self.assertIn("**Criterion:** A: x. **Born:** 2026-08-13. "
                      "**Source:** PR #63, 2026-08-13", self.body())
        self.assertIn(self.BACKDATED + "T001", r.stdout)

    def test_a_source_with_no_date_leaves_the_item_undated_and_says_so(self):
        """The direction that matters. `20/08` is a real day in a year the text
        does not name, and a stamp built by choosing that year reports an age no
        reader can tell from a right one. Undated says "unknown" out loud — and
        the report has to name the item, since nothing else ever will."""
        self.seed(legacy(1, "veio do tracker", "tracker"),
                  legacy(2, "do wrap-up", "wrap-up 20/08"))
        before = self.body()
        r = self.migrate()
        self.assertEqual(self.body(), before)
        self.assertNotIn(self.BACKDATED, r.stdout)
        self.assertIn("2 item(s) left with no age: a **Source:** stating no "
                      "`YYYY-MM-DD` date", r.stdout)
        self.assertIn("— T001, T002. Nothing here invents one.", r.stdout)

    def test_two_different_dates_in_one_source_decide_nothing(self):
        """Picking either is a choice the text does not make. The same date twice
        is one date, and still backdates."""
        self.seed(legacy(1, "duas datas", "aberto 2026-07-02, refeito 2026-08-13"),
                  legacy(2, "a mesma duas vezes", "2026-08-13 e de novo 2026-08-13"))
        r = self.migrate()
        self.assertNotIn("**Born:**", self.body().split("**T002**")[0])
        self.assertIn("**Born:** 2026-08-13. **Source:** 2026-08-13 e de novo",
                      self.body())
        self.assertIn("1 item(s) left with no age: a **Source:** stating two "
                      "different dates — T001", r.stdout)

    def test_a_source_date_in_the_future_is_not_a_birth_date(self):
        """An item cannot have been born after today, so the value is a typo or a
        plan. Honouring it would make `list` print a NEGATIVE age — the one output
        a reader has no reading for."""
        ahead = (datetime.date.today() + datetime.timedelta(days=30)).isoformat()
        self.seed(legacy(1, "datado para a frente", f"planejado para {ahead}"))
        before = self.body()
        r = self.migrate()
        self.assertEqual(self.body(), before)
        self.assertIn("1 item(s) left with no age: a **Source:** date later than "
                      "today — T001", r.stdout)

    def test_a_source_no_reader_may_use_is_reported_as_its_own_case(self):
        """A field off the first line is one repair away from an age, and an item
        with no Source at all is not. Reported as "no Source", the first sends a
        reader looking for a field the item plainly carries."""
        self.seed("- [ ] **T001** — campos fora da primeira linha **Class:**\n"
                  "  AUTONOMOUS. **Effort:** S. **Source:** 2026-08-13\n")
        r = self.migrate()
        self.assertIn("1 item(s) left with no age: a **Source:** no reader may use",
                      r.stdout)


class TestListShowsTheAge(QueueTest):
    """Displayed ALWAYS, never turned into a question: the value of a threshold is
    not decided in this slice, and a queue nobody has measured with ages visible
    is not a queue anyone can pick a number for."""

    def test_a_dated_item_shows_its_age_in_days(self):
        born = (datetime.date.today() - datetime.timedelta(days=12)).isoformat()
        self.seed(item(1, "parado ha doze dias", born=born))
        self.assertIn("T001  AUTONOMOUS   12d  parado ha doze dias",
                      self.run_tk("list").stdout)

    def test_an_item_born_today_is_zero_days_old_not_blank(self):
        """`0d` and `?` are different claims — one is an age, the other is the
        absence of one — and a display that printed both the same way would hide
        exactly the items `migrate` could not date."""
        self.seed(item(1, "nasceu hoje", born=datetime.date.today().isoformat()))
        self.assertIn("T001  AUTONOMOUS    0d  nasceu hoje", self.run_tk("list").stdout)

    def test_a_legacy_queue_lists_without_an_age_and_without_breaking(self):
        """The population that outnumbers every other one: items written before
        the field existed, beside items whose stamp is unreadable. `list` is the
        command every session runs first, so it fails on none of them."""
        self.seed(item(1, "sem carimbo nenhum"),
                  legacy(2, "carimbo ilegivel", "2026-08-13", born="ontem"),
                  legacy(3, "carimbo impossivel", "2026-08-13", born="2026-02-31"))
        r = self.run_tk("list")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("Traceback", r.stderr)
        for line in ("T001  AUTONOMOUS     ?  sem carimbo nenhum",
                     "T002  AUTONOMOUS     ?  carimbo ilegivel",
                     "T003  AUTONOMOUS     ?  carimbo impossivel"):
            self.assertIn(line, r.stdout)

    def test_the_age_survives_the_project_grouping(self):
        """`list` has two output shapes and only one of them is the flat list. A
        column added to the flat path alone is a column half the queues never see."""
        born = (datetime.date.today() - datetime.timedelta(days=3)).isoformat()
        self.seed(item(1, "com tag", project="tk", born=born), item(2, "sem tag"))
        out = self.run_tk("list").stdout
        self.assertIn("## tk", out)
        self.assertIn("T001  AUTONOMOUS    3d  com tag", out)
        self.assertIn("T002  AUTONOMOUS     ?  sem tag", out)



# --- T297: the WIP cap — how many open items this machine may hold at once ---

# The cap is SITE configuration, and the number in these fixtures is a fixture's
# number: the plugin ships none, because the machine carrying a hundred open
# items and the one carrying four run the same script. `alpha` is the machine
# running the suite, as in the roster fixtures above.
def site_cap(cap):
    return f"identity = alpha\nenvironments = alpha\nmax-open-items = {cap}\n"


class WipCapTest(QueueTest):
    """The fixtures both cap suites share: the `add` under test, a queue where
    `tk-roster` will sweep for it, and an `add` aimed at a chosen directory.

    A base class, not a parent suite: inheriting the CASES would rerun the whole
    total-cap class inside the per-queue one, and this suite already spawns a
    subprocess per case.
    """

    ADD = ("add", "achado da review", "--class", "AUTONOMOUS", "--effort", "S",
           "--criterion", "A: x")

    def roster_queue(self, name, *items):
        """A queue where `tk-roster` sweeps for them — under this test's HOME.

        The suite's own `self.mem` is a tempdir OUTSIDE ~/.claude/projects, so it
        is the target queue and never a roster one; a test that needs the roster
        to hold something writes it here.
        """
        d = os.path.join(self.home, ".claude", "projects", name, "memory")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "next-steps.md"), "w", encoding="utf-8") as f:
            f.write(HEADER + "".join(items))
        return d

    def add_in(self, memdir, *extra):
        """`add` against a chosen queue — `run_tk` always appends `self.mem`, and
        the `--dir` bypass can only be exercised by naming another directory."""
        env = dict(os.environ, HOME=self.home)
        return subprocess.run([sys.executable, TK, *self.ADD, *extra, "--dir", memdir],
                              capture_output=True, text=True, cwd=self.dir, env=env,
                              timeout=60)


class TestWipCap(WipCapTest):
    """`add` is refused once the OPEN items reach the cap, with NO bypass.

    A queue is a working set, and `add` is the cheapest action in this CLI — a
    session that cannot finish a finding enqueues it, and the queue grows faster
    than any session empties it. The gate is the whitelist form of the answer:
    refuse AT the cap, always, and let a human take an item out. There is no
    `--force` for it, deliberately: an unattended `--force` is a string no gate
    can judge, and this script has no signal of whether anyone is present.

    The count sums every queue on this machine's roster, which is what closes
    the `--dir` bypass: a cap that counted one queue is walked around by naming
    another one on the same machine, and the WIP is the same WIP.
    """

    # --- the cap itself ---------------------------------------------------

    def test_the_add_is_refused_when_the_open_items_reach_the_cap(self):
        """AT the cap, not past it: the cap is how many items may be OPEN, so the
        add that would make them cap+1 is the one refused. The WHOLE file is
        asserted unchanged, not `assertNotIn` on the new text — a refusal that
        rewrote the queue on its way out would satisfy the narrower assertion."""
        self.site(site_cap(2))
        before = HEADER + item(1, "um") + item(2, "dois")
        self.write("next-steps.md", before)
        r = self.run_tk(*self.ADD)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("2 open item(s) against a cap of 2", r.stderr)
        self.assertEqual(self.body(), before)

    def test_a_queue_already_past_the_cap_is_refused_too(self):
        """The comparison is `>=`, not `==`: a queue that grew past the cap
        before the gate existed is the population this machine actually has."""
        self.site(site_cap(2))
        self.seed(item(1, "um"), item(2, "dois"), item(3, "tres"))
        r = self.run_tk(*self.ADD)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("3 open item(s) against a cap of 2", r.stderr)

    def test_below_the_cap_the_add_goes_through(self):
        """The over-refusal direction — the one a gate loses in silence."""
        self.site(site_cap(3))
        self.seed(item(1, "um"), item(2, "dois"))
        r = self.run_tk(*self.ADD)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("added T003", r.stdout)

    def test_force_does_not_reach_the_cap(self):
        """`add --force` raises the SIZE ceilings and must not touch this one:
        an unattended `--force` is the same unjudgeable string as `--deferred`,
        and the script cannot tell whether anyone is there to judge it."""
        self.site(site_cap(2))
        self.seed(item(1, "um"), item(2, "dois"))
        r = self.run_tk(*self.ADD, "--force")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("open item(s) against a cap of 2", r.stderr)

    def test_a_done_item_is_not_open_work(self):
        """The cap counts the WORKING SET. A `[x]` line parked in the queue is
        work that left it, and counting it would refuse adds for room that is
        already free."""
        self.site(site_cap(2))
        self.seed(item(1, "um"),
                  item(2, "dois").replace("- [ ]", "- [x]"),
                  item(3, "tres").replace("- [ ]", "- [x]"))
        r = self.run_tk(*self.ADD)
        self.assertEqual(r.returncode, 0, r.stderr)

    # --- the remedy -------------------------------------------------------

    def test_the_refusal_names_done_and_cancel_and_where_the_number_lives(self):
        """The only way to make room is to take an item OUT, so the refusal names
        both commands that do it — and the file the number comes from, or a reader
        cannot tell a full machine from a misconfigured one."""
        self.site(site_cap(1))
        self.seed(item(1, "um"))
        r = self.run_tk(*self.ADD)
        self.assertEqual(r.returncode, 1, r.stdout)
        for fragment in ("tk-queue done <id> --how", "tk-queue cancel <id> --why",
                         "tk-queue list", "max-open-items",
                         os.path.join(self.home, ".claude", "tk", "env")):
            self.assertIn(fragment, r.stderr)

    def test_the_printed_remedy_RUNS_and_makes_room(self):
        """A refusal's remedy is code: prescribed lines have shipped that no flag
        combination accepts. The remedy is run with a real ID substituted for the
        placeholder, and then the refused command is re-run."""
        self.site(site_cap(1))
        self.seed(item(1, "um"))
        refusal = self.run_tk(*self.ADD)
        self.assertEqual(refusal.returncode, 1, refusal.stdout)
        self.assertIn('tk-queue done <id> --how "<outcome + pointer>"', refusal.stderr)
        closed = self.run_tk("done", "T001", "--how", "PR #1")
        self.assertEqual(closed.returncode, 0, closed.stderr)
        again = self.run_tk(*self.ADD)
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertIn("added T002", again.stdout)

    def test_the_two_sinks_a_review_prescribes_stay_open_at_the_cap(self):
        """`edit --text` and `handoff` write no new item, and they are where a
        finding that cannot become an item goes. A cap that closed them too would
        leave a session at the cap with nowhere to put what it found."""
        self.site(site_cap(1))
        self.seed(item(1, "um"))
        self.assertEqual(self.run_tk(*self.ADD).returncode, 1)
        edited = self.run_tk("edit", "T001", "--text", "um, mais o achado de hoje")
        self.assertEqual(edited.returncode, 0, edited.stderr)
        self.assertIn("mais o achado de hoje", self.body())
        wrote = self.run_tk("handoff", "T001", "--objective", "fechar o achado",
                            "--state", "nada feito", "--blockers", "none")
        self.assertEqual(wrote.returncode, 0, wrote.stderr)

    # --- the roster, which is what closes the --dir bypass ----------------

    def test_the_count_sums_every_queue_on_the_roster(self):
        """One machine, one working set. The roster comes from `tk-roster`, so a
        second queue's items count against the cap and the refusal says where
        they are — the reader has to pick the item to close out of one of them."""
        self.site(site_cap(3))
        other = self.roster_queue("-srv-outro", item(1, "um"), item(2, "dois"))
        self.seed(item(9, "nove"))
        r = self.run_tk(*self.ADD)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("3 open item(s) against a cap of 3", r.stderr)
        self.assertIn(self.mem, r.stderr)
        self.assertIn("in 1 other queue(s)", r.stderr)
        self.assertNotIn(other, r.stderr)

    def test_pointing_dir_at_another_queue_does_not_get_past_the_cap(self):
        """The measured bypass: the cap is walked around by naming a DIFFERENT
        queue on the same machine. It is closed by summing the roster, so the
        empty queue is refused exactly like the full one."""
        self.site(site_cap(2))
        self.roster_queue("-srv-cheio", item(1, "um"), item(2, "dois"))
        empty = self.roster_queue("-srv-vazio")
        r = self.add_in(empty)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("2 open item(s) against a cap of 2", r.stderr)

    def test_a_queue_the_site_file_excludes_is_not_counted(self):
        """`fleet-deny` is the roster's own answer to which queues this machine
        works, and the cap reuses it rather than re-deciding: a project the
        machine was told not to touch is not counted against the work it may do."""
        self.site(site_cap(2) + "fleet-deny = -srv-alheio\n")
        self.roster_queue("-srv-alheio", item(1, "um"), item(2, "dois"))
        self.seed()
        r = self.run_tk(*self.ADD)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_one_queue_named_twice_is_counted_once(self):
        """The target queue is added to the roster's list because `--dir` may name
        a directory no roster sweep reaches. When it names one the sweep DOES
        reach, the queue's items must not be counted twice — a doubled count
        refuses adds for room that is there."""
        self.site(site_cap(2))
        both = self.roster_queue("-srv-mesma", item(1, "um"))
        r = self.add_in(both)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("added T002", r.stdout)

    # --- what the cap is read from ----------------------------------------

    def test_no_key_in_the_site_file_is_no_cap(self):
        """Unset means NO cap: the behaviour every queue had before this gate.
        A ceiling nobody chose is not a ceiling, and a number shipped in the
        plugin would refuse every add on the first machine already above it."""
        self.site("identity = alpha\nenvironments = alpha\n")
        self.seed(*[item(n, f"item {n}") for n in range(1, 8)])
        r = self.run_tk(*self.ADD)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_no_site_file_at_all_is_no_cap(self):
        """A fresh install has no site file, and `add` is the command every
        session runs: it must not start depending on a file the plugin ships
        nothing for."""
        self.seed(*[item(n, f"item {n}") for n in range(1, 8)])
        r = self.run_tk(*self.ADD)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_a_rotten_site_file_stops_the_add_instead_of_vanishing_the_cap(self):
        """The cap lives in that file, so a half-read one is a cap that silently
        disappears. The diagnosis is the file's own line number, not a traceback
        naming a line of Python the reader cannot fix."""
        self.site("identity = alpha\nenvironments = alpha\nmax-open-items = 2\nlixo\n")
        self.seed(item(1, "um"))
        r = self.run_tk(*self.ADD)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn(":4:", r.stderr)
        self.assertNotIn("Traceback", r.stderr)

    def test_a_cap_of_zero_is_refused_by_the_site_file(self):
        """Zero is a number and it is not a cap: it refuses every add forever,
        which reads as a broken script rather than as a misconfigured file."""
        self.site(site_cap(0))
        self.seed()
        r = self.run_tk(*self.ADD)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("max-open-items", r.stderr)

    def test_a_cap_that_is_not_a_number_is_refused(self):
        self.site("identity = alpha\nenvironments = alpha\nmax-open-items = muitos\n")
        self.seed()
        r = self.run_tk(*self.ADD)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("max-open-items", r.stderr)

    # --- the reader a THIRD PARTY's file goes through (T345) --------------

    def test_a_sibling_queue_that_is_not_utf8_is_diagnosed_and_not_crashed(self):
        """Every queue counted here but one belongs to a project this session
        never opened. One of them saved as UTF-16, or carrying a single byte from
        another encoding, turned EVERY `add` on the machine into a raw
        UnicodeDecodeError — the guard the site file's reader already carried and
        this count did not, until the two shared one reader."""
        self.site(site_cap(9))
        d = os.path.join(self.home, ".claude", "projects", "-srv-outro", "memory")
        os.makedirs(d, exist_ok=True)
        queue = os.path.join(d, "next-steps.md")
        for label, raw in (("utf-16", (HEADER + item(1, "um")).encode("utf-16")),
                           ("one byte from another encoding",
                            b"# Next steps\n\n- [ ] **T001** caf\xe9\n")):
            with self.subTest(case=label):
                with open(queue, "wb") as f:
                    f.write(raw)
                self.seed(item(1, "um"))
                r = self.run_tk(*self.ADD)
                self.assertEqual(r.returncode, 1, r.stdout)
                # the one assertion that separates a diagnosis from a crash
                self.assertNotIn("Traceback", r.stderr)
                self.assertIn("tk-queue:", r.stderr)
                self.assertIn("not valid UTF-8", r.stderr)
                self.assertIn(queue, r.stderr)       # and it names THEIR file
                self.assertNotIn("achado da review", self.body())

    def test_an_invisible_bom_in_a_sibling_queue_does_not_undercount_it(self):
        """A U+FEFF glued to an item's marker takes that line out of every
        `^`-anchored grammar, so the queue counts one short — one invisible
        character waving an add past a full cap. The shared reader removes it in
        EVERY position, and its docstring carries why utf-8-sig cannot."""
        self.site(site_cap(3))
        self.roster_queue("-srv-outro", item(1, "um"), "\ufeff" + item(2, "dois"))
        self.seed(item(9, "nove"))
        r = self.run_tk(*self.ADD)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("3 open item(s) against a cap of 3", r.stderr)

    # --- the roster module, loaded on first use (T345) --------------------

    def broken_roster(self, contents):
        """A copy of the three bins with `tk-roster` broken — `None` deletes it.

        A copy, because the suite may not edit the tree it is testing, and the
        mutation harness runs against a copy of its own.
        """
        d = os.path.join(self.dir, "bin")
        os.makedirs(d, exist_ok=True)
        src = os.path.dirname(os.path.abspath(TK))
        for name in ("tk-queue", "tk_site.py"):
            shutil.copy(os.path.join(src, name), os.path.join(d, name))
        path = os.path.join(d, "tk-roster")
        if contents is None:
            if os.path.exists(path):
                os.remove(path)
        else:
            with open(path, "w", encoding="utf-8") as f:
                f.write(contents)
        return os.path.join(d, "tk-queue")

    def run_copy(self, tk, *argv):
        return subprocess.run([sys.executable, tk, *argv, "--dir", self.mem],
                              capture_output=True, text=True, cwd=self.dir,
                              env=dict(os.environ, HOME=self.home), timeout=60)

    def test_a_broken_roster_does_not_reach_the_commands_that_never_read_it(self):
        """`tk-roster` is read by the WIP cap and by nothing else in this CLI.
        Loaded at import, it put every command behind a file none of them reads:
        with it deleted or carrying a syntax error, `list` and `done` died in a
        raw traceback — `done` being the very remedy the refusal prints."""
        self.seed(item(1, "um"))
        for label, contents in (("deleted", None), ("a syntax error", "def (\n")):
            with self.subTest(roster=label):
                tk = self.broken_roster(contents)
                for argv in (("list",), ("done", "T001", "--how", "PR #1")):
                    r = self.run_copy(tk, *argv)
                    self.assertEqual(r.returncode, 0, r.stderr)
                    self.assertNotIn("Traceback", r.stderr)
                self.seed(item(1, "um"))

    def test_an_add_with_no_cap_never_loads_the_roster_either(self):
        """The design note's claim, which an import-time load falsified: with no
        cap chosen, `add` costs one small file read and nothing else."""
        self.site("identity = alpha\nenvironments = alpha\n")
        self.seed(item(1, "um"))
        r = self.run_copy(self.broken_roster(None), *self.ADD)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("added T002", r.stdout)

    def test_a_broken_roster_under_a_cap_is_reported_not_crashed(self):
        """The cap is summed over the queues that file reports, so an `add` at a
        cap cannot proceed without it — and says so, naming the file to restore."""
        self.site(site_cap(2))
        self.seed(item(1, "um"))
        r = self.run_copy(self.broken_roster("def (\n"), *self.ADD)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertNotIn("Traceback", r.stderr)
        self.assertIn("tk-roster", r.stderr)


    # --- what the refusal may PRINT (T346) --------------------------------

    def test_the_refusal_never_names_another_project(self):
        """A project directory carries a client's or a company's name, and this
        text travels — into a transcript, into a pull request body, into a repo
        that is public. The breakdown says WHERE the work is because the reader
        has to pick an item to close; the queue they can pick it from is the one
        they are in, and that is the only one named."""
        self.site(site_cap(3))
        secret = "-srv-cliente-com-nome-proprio"
        other = self.roster_queue(secret, item(1, "um"), item(2, "dois"))
        self.seed(item(9, "nove"))
        r = self.run_tk(*self.ADD)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertNotIn(secret, r.stderr)
        self.assertNotIn(other, r.stderr)
        self.assertIn(self.mem, r.stderr)                  # their own queue, named
        self.assertIn("2  in 1 other queue(s)", r.stderr)  # the rest, counted
        self.assertIn("tk-roster", r.stderr)               # and where to see them

    def test_an_empty_queue_is_not_counted_as_a_queue_holding_work(self):
        """"In N other queue(s)" is a reader's instruction to go look in them, so
        a queue with nothing in it must not be one of the N — a machine's empty
        queues would bury the two lines that matter."""
        self.site(site_cap(3))
        self.roster_queue("-srv-cheio", item(1, "um"), item(2, "dois"))
        self.roster_queue("-srv-vazio")
        self.seed(item(9, "nove"))
        r = self.run_tk(*self.ADD)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("in 1 other queue(s)", r.stderr)

    def test_a_symlink_naming_a_roster_queue_is_still_counted_once(self):
        """The reachable input for the dedup: `--dir` names any path, and a
        symlink to a queue the roster already swept is a second spelling of one
        queue. Counted twice, it refuses adds for room that is there."""
        self.site(site_cap(2))
        both = self.roster_queue("-srv-mesma", item(1, "um"))
        link = os.path.join(self.dir, "atalho")
        os.symlink(both, link)
        r = self.add_in(link)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("added T002", r.stdout)

    # --- an absent cap is a perfect no-op (T346) ---------------------------

    def test_a_rotten_site_file_with_no_cap_in_it_does_not_break_the_add(self):
        """The regression this gate introduced: a site file that would not parse
        made `add` fail on machines that never chose a number — a command that
        had ignored that file since it existed. The file is still broken, and is
        reported; the queue does not go down with it."""
        self.site("identity = alpha\nenvironments = alpha\nlixo\n")
        self.seed(item(1, "um"))
        r = self.run_tk(*self.ADD)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("added T002", r.stdout)
        self.assertIn(":3:", r.stderr)            # said, not swallowed
        self.assertIn("max-open-items", r.stderr)

    def site_bytes(self, raw):
        """The site file written as RAW BYTES — the only way to reach an
        encoding `self.site` cannot produce, and the shape this pair needs."""
        d = os.path.join(self.home, ".claude", "tk")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "env"), "wb") as f:
            f.write(raw)

    def test_a_site_file_in_utf16_that_sets_the_cap_still_stops_the_add(self):
        """The cap was written, and the scan for it read only UTF-8. In UTF-16
        the key is spelled `m\\x00a\\x00x...`, so the scan answered "no cap in
        this file", the add went through UNCAPPED, and the reason printed was
        that no cap was written — the silent disappearance the gate's own
        docstring names as the one direction it may not fail in. A Windows
        editor told "Unicode" writes exactly this file, and this house runs one.
        """
        self.site_bytes(site_cap(2).encode("utf-16"))
        self.seed(item(1, "um"), item(2, "dois"))
        r = self.run_tk(*self.ADD)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("not valid UTF-8", r.stderr)
        self.assertNotIn("no `max-open-items` line was found", r.stderr)
        self.assertNotIn("Traceback", r.stderr)
        self.assertNotIn("achado da review", self.body())

    def test_a_site_file_in_utf16_with_no_cap_in_it_still_does_not_break_the_add(self):
        """The other direction, and the vacuity guard on the test above: reading
        the wide encodings may not turn an ABSENT cap into a fatal one. A machine
        that never chose a number keeps the behaviour it had before this gate,
        whatever the file is encoded in."""
        self.site_bytes("identity = alpha\nenvironments = alpha\n".encode("utf-16"))
        self.seed(item(1, "um"))
        r = self.run_tk(*self.ADD)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("added T002", r.stdout)
        self.assertIn("not valid UTF-8", r.stderr)       # said, not swallowed
        self.assertIn("max-open-items", r.stderr)

    def test_a_home_with_no_projects_directory_says_the_count_shrank(self):
        """`HOME` resolves the site file AND the roster, so a home carrying a cap
        and no projects directory counts one queue as if it were the machine.
        Not a bypass — the same HOME chooses the cap — but a whitelist gate may
        not shrink its own count in silence."""
        self.site(site_cap(9))
        self.seed(item(1, "um"))
        shrunk = self.run_tk(*self.ADD)
        self.assertEqual(shrunk.returncode, 0, shrunk.stderr)
        self.assertIn("is counted over this queue alone", shrunk.stderr)
        self.roster_queue("-srv-outro", item(1, "um"))
        whole = self.run_tk(*self.ADD)
        self.assertEqual(whole.returncode, 0, whole.stderr)
        self.assertNotIn("is counted over this queue alone", whole.stderr)

    def test_the_overshoot_the_missing_locks_cost_is_stated_as_measured(self):
        """The count holds only the target queue's lock, and the docstring said
        that costs "one item over the cap". It costs one per add that raced —
        four adds on four queues, nine open against a cap of ten, ended at
        thirteen. A number in prose that no command knows is how this slice's
        other five wrong numbers survived to the review."""
        doc = load_tk().open_items.__doc__
        self.assertNotIn("one item over the cap", doc)
        self.assertIn("k of them land k-1 items above the cap", doc)
        self.assertIn("thirteen open, three above", doc)

    def test_no_prose_claims_a_refused_add_would_burn_an_id(self):
        """The order of the gate and `max_id` was justified by a hole in the ID
        sequence that a refusal below it would leave. `max_id` only READS: no
        number is reserved, and no refusal has ever burnt one."""
        with open(TK, encoding="utf-8") as f:
            src = f.read()
        self.assertNotIn("leaves a hole in the sequence", src)

    def test_no_prose_says_the_roster_is_imported_at_the_top_of_the_file(self):
        """`wip_queues` kept saying so after the loader was made lazy, one file
        over from the two mutation entries this batch wrote against exactly this
        class — a fact in prose that no command knows. The retraction applies at
        every site of the claim, so the claim is grepped, not remembered."""
        self.assertNotIn("imported at the top of this file", load_tk().wip_queues.__doc__)

    def test_no_prose_claims_the_refusals_channel_never_names_another_project(self):
        """The refusal names no other project, and that was written as if it held
        for the whole command. It does not: the diagnosis of an unreadable
        SIBLING queue names that queue's path, on purpose and by its own test.
        The narrow claim is true and the wide one is not."""
        with open(TK, encoding="utf-8") as f:
            # comment markers and wrapping out, so the assertion is about the
            # SENTENCE and not about where the line happened to break
            flat = " ".join(f.read().replace("#", " ").split())
        self.assertNotIn("another project's name into this session's output", flat)
        self.assertIn("names the sibling queue whose file cannot be read", flat)

    def test_the_untested_branch_says_it_is_the_race_and_not_a_first_add(self):
        """F9's decline is only recorded where a reader finds it. The `content is
        None` branch is reachable ONLY by a queue vanishing under the count:
        `tk-roster` lists a project where the queue is already a plain file, and
        a missing TARGET queue is refused further up `cmd_add`. The first `add`
        into a brand-new queue never reaches this function."""
        doc = load_tk().open_items.__doc__
        self.assertIn("THAT RACE IS THE ONLY WAY INTO THAT", doc)
        self.assertNotIn("The other reachable way in is a", doc)


class TestWipCapPerQueue(WipCapTest):
    """The total does not see CONCENTRATION. On 2026-09-04, 194 of 280 open
    items sat in TWO of twelve queues: a machine can be a long way under its
    total while the queue in front of the caller is the problem, and the total
    alone answers that by tightening on the ten queues that are not.

    So the brake is per QUEUE, one number for every queue on the roster — not a
    map, which is configuration nobody maintains and under which every new queue
    is born without an entry — and the total scales with the roster instead of
    being a fixed number that turns into a lie the day a project is added.
    """

    def three_queues(self, *sizes, per_queue=None, total=None, discount=None):
        """A site file plus three roster queues holding `sizes` items each, and
        `self.mem` (outside ~/.claude/projects) as the target queue."""
        lines = ["identity = alpha", "environments = alpha"]
        if per_queue is not None:
            lines.append(f"max-open-items-per-queue = {per_queue}")
        if total is not None:
            lines.append(f"max-open-items = {total}")
        if discount is not None:
            lines.append(f"max-open-items-discount = {discount}")
        self.site("\n".join(lines) + "\n")
        for n, size in enumerate(sizes, 1):
            self.roster_queue(f"q{n}", *(item(i, f"item {i}") for i in range(1, size + 1)))

    def add_in_roster_queue(self, name, *extra):
        return self.add_in(os.path.join(self.home, ".claude", "projects", name, "memory"),
                           *extra)

    def test_a_full_queue_is_refused_while_the_others_are_empty(self):
        """The half the total cannot express: 3 open of a per-queue cap of 3, a
        machine holding 3 items in all, and the add refused."""
        self.three_queues(3, 0, 0, per_queue=3, total="auto", discount=0)
        r = self.add_in_roster_queue("q1")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("3 open item(s) in this queue against a per-queue cap of 3",
                      r.stderr)
        self.assertIn("max-open-items-per-queue", r.stderr)

    def test_a_sibling_queue_stays_open_while_one_is_full(self):
        """The over-refusal direction: the per-queue cap is per QUEUE, and a full
        one may not close the machine."""
        self.three_queues(3, 0, 0, per_queue=3, total="auto", discount=0)
        r = self.add_in_roster_queue("q2")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_the_total_refuses_with_no_queue_at_its_own_cap(self):
        """The other half: three queues at 8 of a per-queue cap of 30, so none is
        full — and the derived total is (30 - 27) x 3 = 9 against 24 open."""
        self.three_queues(8, 8, 8, per_queue=30, total="auto", discount=27)
        r = self.add_in_roster_queue("q1")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("24 open item(s) against a cap of 9", r.stderr)
        self.assertIn("(30 - 27) x 3 queue(s)", r.stderr,
                      "the derived total has to say where it came from")

    def test_auto_counts_the_queues_the_roster_counts(self):
        """`auto` is (per-queue - discount) x N, and N moves with the roster: the
        same occupancy that refuses over three queues passes over four, which is
        the whole reason the total is derived instead of pinned."""
        self.three_queues(4, 4, 4, per_queue=30, total="auto", discount=26)
        r = self.add_in_roster_queue("q1")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("12 open item(s) against a cap of 12", r.stderr)
        self.three_queues(4, 4, 4, 0, per_queue=30, total="auto", discount=26)
        r = self.add_in_roster_queue("q4")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_without_the_per_queue_key_nothing_changes(self):
        """The compatibility half of the criterion, asserted against the two
        behaviours the file had before this key existed."""
        self.three_queues(2, 0, 0, total=3)
        self.assertEqual(self.add_in_roster_queue("q1").returncode, 0)
        self.three_queues(3, 0, 0, total=3)
        r = self.add_in_roster_queue("q1")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("3 open item(s) against a cap of 3", r.stderr)
        self.assertNotIn("per-queue", r.stderr)

    def test_an_explicit_number_still_pins_the_total(self):
        """Three options, not two: absent is no cap, a number pins it, `auto`
        derives it. A per-queue cap beside a pinned total leaves the total pinned."""
        self.three_queues(4, 4, 4, per_queue=30, total=99)
        r = self.add_in_roster_queue("q1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.three_queues(4, 4, 4, per_queue=30, total=12)
        r = self.add_in_roster_queue("q1")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("12 open item(s) against a cap of 12", r.stderr)

    def test_the_per_queue_cap_alone_leaves_the_total_uncapped(self):
        """Each key stands on its own: writing the brake must not invent a total
        the user never chose."""
        self.three_queues(2, 2, 2, per_queue=30)
        self.assertEqual(self.add_in_roster_queue("q1").returncode, 0)

    def test_auto_without_the_per_queue_key_is_refused_by_the_site_file(self):
        """`auto` derives from a number that is not there. Read as "no cap" it
        would silently drop a ceiling the user wrote a line to ask for."""
        self.three_queues(1, 0, 0, total="auto")
        r = self.add_in_roster_queue("q1")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("max-open-items-per-queue", r.stderr)
        self.assertNotIn("Traceback", r.stderr)

    def test_a_discount_at_or_above_the_per_queue_cap_is_refused(self):
        """It derives a total of zero or less — a machine that may open no item
        at all, arriving as a refusal citing a number written nowhere."""
        self.three_queues(0, 0, 0, per_queue=30, total="auto", discount=30)
        r = self.add_in_roster_queue("q1")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("max-open-items-discount", r.stderr)
        self.assertNotIn("Traceback", r.stderr)

    def test_a_per_queue_cap_that_is_not_a_number_is_refused(self):
        self.three_queues(0, 0, 0, per_queue="muitas")
        r = self.add_in_roster_queue("q1")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("max-open-items-per-queue", r.stderr)

    def test_force_does_not_reach_the_per_queue_cap_either(self):
        """The same answer `--force` gets from the total, for the same reason:
        an unattended `--force` is a string no gate can judge."""
        self.three_queues(3, 0, 0, per_queue=3)
        r = self.add_in_roster_queue("q1", "--force")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("per-queue cap of 3", r.stderr)



class TestTheCommandsSayWhatTheyDo(QueueTest):
    """One case per sentence the CLI was missing. Each defect below was a reader
    deciding how to use a command from a `--help` that did not carry the rule,
    or from a refusal that named the wrong half of what it measured.

    Every assertion reads the help with its whitespace collapsed: argparse
    rewraps to the terminal's width, so an expected phrase that spans a line
    break passes on one machine and fails on the next."""

    def help_for(self, *argv):
        r = self.run_tk(*argv, "--help")
        self.assertEqual(r.returncode, 0, r.stderr)
        return " ".join(r.stdout.split())

    def add(self, *argv):
        return self.run_tk("add", *argv, "--class", "AUTONOMOUS",
                           "--effort", "S (~20min)", "--criterion", "A: roda")

    # --- T274: the owner grammar, in all three of its spellings -----------
    def test_the_owner_grammar_names_the_first_character_rule(self):
        """OWNER_RE demands a letter or a digit at the front, so '.local' and
        '_alpha' are refused — and neither the refusal nor `claim --help` said
        why, which leaves the caller retyping a name that cannot pass."""
        self.seed(item(1, "algo"))
        for bad in (".local", "_alpha"):
            with self.subTest(owner=bad):
                r = self.run_tk("claim", "T001", "--as", bad)
                self.assertEqual(r.returncode, 1, r.stdout)
                self.assertIn("STARTS with a letter or a digit", r.stderr)
        self.assertIn("STARTING with a letter or a digit", self.help_for("claim"))
        # and the same name with a leading letter is taken, so the rule the two
        # texts now state is the rule the regex actually applies
        self.assertEqual(self.run_tk("claim", "T001", "--as", "alpha.local").returncode,
                         0)

    # --- T335 + T340: what `edit --text` destroys, and the fusion order ---
    def test_edit_help_says_that_text_replaces_and_what_it_replaces(self):
        """The semantics lived only in the code, so a reader deciding from the
        help could not know the flag deletes — which is how a document came to
        prescribe accumulating with a command that substitutes."""
        h = self.help_for("edit")
        self.assertIn("REPLACES the item's text", h)
        self.assertIn("continuation prose included", h)
        self.assertIn("it never appends", h)

    def test_cancel_and_edit_both_name_the_order_a_fusion_runs_in(self):
        """Cancel-then-edit loses the content between the two calls: the block
        ceiling can refuse the edit carrying the union, and by then the source is
        in the done-log. Three times in the consolidation of 2026-09-02."""
        cancel = self.help_for("cancel")
        self.assertIn("`edit --text` on the survivor FIRST", cancel)
        self.assertIn("not one transaction", cancel)
        self.assertIn("block ceiling can refuse the edit that carries the union", cancel)
        self.assertIn("this `edit` FIRST, then `cancel` the source", self.help_for("edit"))

    # --- T354: the refusal names the block, and which half to cut ---------
    def test_the_ceiling_refusal_names_the_block_and_the_half_over_the_line(self):
        """`item has 1011 chars` read beside a 641-char text sends the cut into
        the text when the field chain was the other 370."""
        self.seed()
        r = self.add("x " * 400)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("the item BLOCK has", r.stderr)
        self.assertIn("chars of text and", r.stderr)
        self.assertIn("the cut comes out of the text", r.stderr)

    def test_the_refusal_points_at_the_fields_when_they_are_the_larger_half(self):
        self.seed()
        r = self.run_tk("add", "curto", "--class", "AUTONOMOUS",
                        "--effort", "M " + "e" * 50,
                        "--criterion", "A: " + "c" * 190,
                        "--risk", "r" * 190, "--source", "s" * 190,
                        "--project", "p" * 50)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("the cut comes out of the fields", r.stderr)

    # --- #223: the four gaps the prune of the kickoff left behind ---------
    def test_add_help_names_the_canonical_spelling_of_a_forge_reference(self):
        h = self.help_for("add")
        self.assertIn("repo lower-cased, number without leading zeros", h)
        self.assertIn("`Ambiente#0171` is written `ambiente#171`", h)
        self.assertIn("`owner/repo#n` refused", h)
        self.assertIn("marks a hand-edited one `[?]`", h)

    def test_add_help_carries_the_whole_repo_whitelist(self):
        """The help gave the summary — a URL or an absolute path — and the five
        shapes plus the two refusals lived only in the refusal message, which a
        reader deciding how to spell the flag never sees."""
        h = self.help_for("add")
        for shape in ("https://<host>/<path>", "ssh://git@<host>/<path>",
                      "git@<host>:<path>", "file:///<path>", "an ABSOLUTE path"):
            self.assertIn(shape, h)
        self.assertIn("A `~/` address is refused", h)
        self.assertIn("`<user>@` half on an http(s) URL is refused", h)

    def test_force_names_both_ceilings_it_raises_wherever_it_is_offered(self):
        """`done --help` named one ceiling and `add --help` named none, while the
        flag raises the block ceiling and the field one together."""
        for command in ("add", "done", "cancel", "edit"):
            with self.subTest(command=command):
                h = self.help_for(command)
                self.assertIn("raise BOTH ceilings", h)
                self.assertIn("700", h)
                self.assertIn("2000", h)
        self.assertIn("does NOT reach the WIP cap", self.help_for("add"))

    def test_the_dry_run_comment_names_the_prose_site_that_exists(self):
        """The comment listed the kickoff SKILL.md as one of the three prose
        sites carrying the claim; the prune of #191 moved the queue contract to
        tk/reference/queue.md, and the comment is the list the next writer keeps
        in step."""
        with open(TK, encoding="utf-8") as fh:
            source = fh.read()
        block = source[source.index("The ONE statement of what a preview"):
                       source.index("DRY_RUN_WRITES")]
        self.assertIn("tk/reference/queue.md", block)
        self.assertNotIn("the kickoff SKILL.md) cannot read", block)

# --- one parse, one structure, one writer ---------------------------------

# The shapes the parse is measured on. Every one of them is a real population:
# the item `add` writes, the legacy item whose fields never got a Class, the
# hand-decorated `[x]` line, the item that quotes a marker in its own prose, the
# value carrying the `*` that used to cut the chain in half, and the Portuguese
# field names the queues carried before the script existed.
ROUND_TRIP_BLOCKS = (
    ("as add writes it", item(1, "um texto", project="tk")),
    ("no fields at all", "- [ ] **T002** — um item sem cadeia nenhuma\n"),
    ("a continuation line", "- [ ] **T003** — texto **Class:** AUTONOMOUS. **Effort:** S.\n"
                            "  uma nota de continuacao\n"),
    ("a hard break on a continuation line",
     "- [ ] **T004** — texto **Class:** AUTONOMOUS. **Effort:** S.\n"
     "  uma nota que termina em quebra dura  \n  e continua\n"),
    ("portuguese field names",
     "- [ ] **T005** — texto **Classe:** AUTONOMOUS. **Esforço:** M. **Critério:** A: x.\n"),
    ("a marker in the item's own prose",
     "- [ ] **T006** — cita o **Project:** de outra fila. **Class:** AUTONOMOUS. "
     "**Effort:** S. **Criterion:** A: x.\n"),
    ("a decorated done marker", "- [x] ✅ **T007** — legado **Class:** AUTONOMOUS.\n"),
    ("a marker inside a code span",
     "- [ ] **T008** — cita `**Project:** x` na prosa. **Class:** AUTONOMOUS. "
     "**Effort:** S. **Criterion:** A: x.\n"),
    ("an odd backtick",
     "- [ ] **T009** — o glob ` sozinho **Class:** AUTONOMOUS. **Effort:** S.\n"),
    ("an asterisk inside a value",
     "- [ ] **T010** — texto **Class:** AUTONOMOUS. **Criterion:** A: o glob *.md casa.\n"),
    ("no trailing newline", "- [ ] **T011** — texto **Class:** AUTONOMOUS."),
    ("blanks after the last field", "- [ ] **T012** — texto **Class:** AUTONOMOUS.   \n"),
    ("a source with no period",
     "- [ ] **T013** — texto **Class:** AUTONOMOUS. **Source:** conversa 2026-08-13\n"),
    ("not an item at all", "## Uma secao\n\ntexto solto\n"),
)


class TestOneParseOneWriter(QueueTest):
    """One parse into a structure, one writer out of it — and the invariant that
    makes the swap safe: `render_item(parse_item(b))` is `b`, byte for byte.

    The bug this closes is not untidiness. The chain's ambiguity used to be
    decided TWICE per command — once by the reader that located the field, once
    by the writer that spliced it — and the two answered differently: `edit
    --class AUTONOMOUS --project tk` overwrote four words of an item's own title
    and `--risk none` DELETED the segment its prose was imitating, each exiting 0.
    A writer that can only hand the structure back cannot splice a position the
    parse never named.
    """

    def setUp(self):
        super().setUp()
        self.tk = load_tk()

    def test_every_shape_round_trips_byte_for_byte(self):
        for name, block in ROUND_TRIP_BLOCKS:
            with self.subTest(shape=name):
                self.assertEqual(self.tk.render_item(self.tk.parse_item(block)), block)

    def test_the_blocks_the_script_itself_writes_round_trip(self):
        """The fixtures above are hand-written, so they prove the parse against
        shapes a human chose. This proves it against what the WRITERS emit —
        `add` with every optional field, then the edits that rewrite, append and
        clear one — which is the population the queue actually holds."""
        self.seed()
        for argv in (
                ("add", "um item completo", "--class", "DECISION",
                 "--deferred", "afk: muda o contrato", "--effort", "M",
                 "--risk", "alto", "--criterion", "A: x", "--project", "tk",
                 "--ticket", "claude-skills#42", "--source", "2026-08-13"),
                ("add", "outro", "--class", "AUTONOMOUS",
                 "--effort", "S", "--criterion", "A: y"),
                ("edit", "T002", "--project", "tk"),
                ("claim", "T002", "--as", "sessao-a"),
                ("edit", "T001", "--risk", "none")):
            r = self.run_tk(*argv)
            self.assertEqual(r.returncode, 0, f"{argv}: {r.stderr}")
        body = self.body()
        blocks = [text for kind, text in self.tk.split_blocks(body) if kind.startswith("item")]
        self.assertEqual(len(blocks), 2)
        for block in blocks:
            with self.subTest(block=block[:40]):
                self.assertEqual(self.tk.render_item(self.tk.parse_item(block)), block)
                # the round trip ALONE is satisfied by a file the writers have
                # already corrupted, since it round-trips the corruption too.
                # The joint between the text of an item and its chain is what
                # says they did not: one blank, where compose_item put it.
                self.assertIn(" **Class:**", block)

    def test_a_field_carries_the_spelling_the_file_uses_and_its_canonical_name(self):
        """Provenance, not normalisation: the file's own spelling is what a
        writer must put back, and the canonical name is what a reader asks by.
        Collapsing the two is how `**Esforço:**` came back from an edit spelled
        `**Effort:**` on an item nobody asked to translate."""
        block = ("- [ ] **T001** — texto **Classe:** AUTONOMOUS. **Esforço:** M. "
                 "**Critério:** A: x.\n")
        fields = self.tk.parse_item(block).fields
        self.assertEqual([f.name for f in fields], ["Classe", "Esforço", "Critério"])
        self.assertEqual([f.canonical for f in fields], ["Class", "Effort", "Criterion"])
        self.assertEqual([f.value for f in fields], ["AUTONOMOUS. ", "M. ", "A: x."])

    def test_an_odd_backtick_opens_no_span(self):
        """CommonMark's rule, and the safe direction: a backtick with no closer
        of the same length is literal text. Opening a span there would swallow
        the rest of the line — the `*` defect (T258) with a new character."""
        self.assertEqual(self.tk.code_spans("um ` sozinho e **Class:** X"), [])
        self.assertEqual(self.tk.code_spans("um `x` e ``y``"), [(3, 6), (9, 14)])
        self.assertEqual(self.tk.code_spans("``a ` b``"), [(0, 9)])

    def test_a_writer_hands_back_the_structure_and_touches_nothing_else(self):
        """Each of the three chain writers, through the structure: the item's
        prose, its continuation lines and every field the command did not name
        come back byte-identical."""
        block = ("- [ ] **T001** — texto  com  espacos **Class:** AUTONOMOUS. "
                 "**Effort:** S. **Risk:** alto. **Criterion:** A: x.\n"
                 "  uma nota com quebra dura  \n")
        tk = self.tk
        item_ = tk.parse_item(block)
        risk = next(f for f in item_.fields if f.canonical == "Risk")
        item_.set_field(risk, "Risk", "baixo")
        self.assertEqual(tk.render_item(item_), block.replace("alto", "baixo"))
        self.assertEqual(tk.clear_field_segment(block, tk.real_fields(block, "Risk")[0]),
                         block.replace(" **Risk:** alto.", ""))
        self.assertEqual(tk.append_to_first_line(block, "**Project:** tk."),
                         block.replace("A: x.\n", "A: x. **Project:** tk.\n"))

    def test_the_offsets_of_a_mutated_item_are_refused_not_stale(self):
        """A Field's span names a position in the block it was PARSED from, so
        after a write it names a position the render no longer has. Reading it
        anyway is the corruption this file has already paid for once — a branch
        that spliced with the wrong offsets truncated the frontmatter mid-word
        and duplicated the item, with the whole suite still green."""
        item_ = self.tk.parse_item(item(1, "um", project="tk"))
        first = item_.fields[0]
        self.assertEqual(first.start(), len("- [ ] **T001** — um "))
        item_.set_field(first, "Class", "DECISION")
        with self.assertRaises(ValueError):
            first.start()


# --- the door: what a queue file may carry that no reader can see ---------

class TestTheDoorNormalisesWhatNoReaderCanSee(QueueTest):
    """A byte no reader can SEE is the worst shape a queue file takes: the item
    does not fall over, it disappears, and the id it was holding is handed out
    again. All three vectors below are hand edits from outside this script — an
    editor that writes a BOM, a paste carrying a non-breaking space, a file that
    came back from a Windows tool as UTF-16 — and the contract says these files
    are written only by `tk-queue`, so nothing inside ever produced one.

    Normalisation is at the MARKER HEADER and nowhere else. The item's own text
    keeps every byte the user typed: a queue file is the user's prose, and a
    reader that tidied it would be editing what it was asked to display.
    """

    NBSP = " "
    BOM = "﻿"

    def setUp(self):
        super().setUp()
        self.tk = load_tk()

    def test_a_non_breaking_space_after_the_checkbox_still_names_the_item(self):
        """Measured before the fix: `list` printed `(queue empty)` with the item
        right there in the file, and the next new item was handed T001 AGAIN —
        the duplicate id this whole grammar exists to prevent."""
        self.seed(f"- [ ]{self.NBSP}**T001** — item invisivel **Class:** AUTONOMOUS. "
                  "**Effort:** S. **Criterion:** A: x.\n")
        r = self.run_tk("list")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("T001", r.stdout)
        self.assertIn("AUTONOMOUS", r.stdout)
        r = self.run_tk("add", "o proximo", "--class", "AUTONOMOUS",
                        "--effort", "S", "--criterion", "A: y")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("T002", self.body())
        self.assertEqual(self.body().count("**T001**"), 1)

    def test_a_bom_glued_to_a_marker_in_the_MIDDLE_of_the_file(self):
        """`read` strips a BOM at byte 0 and deliberately nowhere else. One glued
        to a marker further down turns that item into prose of the block above:
        `pack` counted "1 of 1" with two items in the file, and the id of the
        second was invisible to the allocator."""
        self.seed(item(1, "o primeiro"), self.BOM + item(2, "o segundo"))
        r = self.run_tk("list")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("T002", r.stdout)
        r = self.run_tk("add", "o terceiro", "--class", "AUTONOMOUS",
                        "--effort", "S", "--criterion", "A: y")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("**T003**", self.body())
        self.assertNotIn(self.BOM, self.body())

    def test_a_bom_glued_to_a_DONE_LOG_entry_still_spends_that_id(self):
        """The other file the allocator reads. A spent id lives in a done-log
        ENTRY, so a BOM glued to one hides it exactly as a BOM glued to an item
        marker hides an open item's — and the number is handed out a second time,
        which is the whole of T163 on the file the first repair did not reach.

        Measured before this: `done_log_ids` answered [] for an entry the file
        plainly carries, with no warning anywhere."""
        self.seed(log="# Done log\n\n" + self.BOM
                  + "- 2026-08-01 — tk — T001 — feito — how: PR #1\n")
        r = self.run_tk("add", "o proximo", "--class", "AUTONOMOUS",
                        "--effort", "S", "--criterion", "A: y")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("**T002**", self.body())
        self.assertNotIn("**T001**", self.body())

    def test_a_utf16_file_is_read_and_the_warning_says_what_the_next_write_does(self):
        """A raw UnicodeDecodeError is a traceback the caller cannot act on. And
        reading it silently would be worse than the error: this script writes
        UTF-8, so the next command CONVERTS the file, and the caller has to be
        told before that happens rather than after."""
        with open(os.path.join(self.mem, "next-steps.md"), "w", encoding="utf-16") as f:
            f.write(HEADER + item(1, "em utf-16"))
        r = self.run_tk("list")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("T001", r.stdout)
        self.assertIn("UTF-16", r.stderr)
        self.assertIn("UTF-8", r.stderr)

    def test_bytes_that_are_no_encoding_name_the_file_the_byte_and_the_encoding(self):
        """The other half: a file this cannot read must say WHICH file, WHICH
        byte and which encoding it tried. A traceback names a line of the script
        instead, which is the one place the caller cannot fix."""
        with open(os.path.join(self.mem, "next-steps.md"), "wb") as f:
            f.write((HEADER + item(1, "ok")).encode() + b"- [ ] **T002** \xff\xfe\n")
        r = self.run_tk("list")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("next-steps.md", r.stderr)
        self.assertIn("utf-8", r.stderr.lower())
        self.assertIn("byte", r.stderr.lower())
        self.assertNotIn("Traceback", r.stderr)

    def test_a_continuation_line_of_only_spaces_does_not_split_the_item(self):
        """T161: `split_blocks` closed a block on any blank-LOOKING line, so an
        item whose fields sit below a line of spaces lost them — `list` showed
        `?`, and `migrate`, the one command that repairs the shape, could not
        even see the item to report it."""
        self.seed("- [ ] **T001** — item com linha de espacos\n"
                  "   \n"
                  "  **Class:** AUTONOMOUS. **Effort:** M. **Criterion:** A: x.\n")
        r = self.run_tk("list")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("AUTONOMOUS", r.stdout)
        r = self.run_tk("migrate")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("T001", r.stdout)

    def test_a_class_value_outside_the_enum_is_named_not_displayed_as_valid(self):
        """`URGENTE` is not a class this queue has, and printing it in the class
        column reads exactly like one that is. `pack` said `class is URGENTE`,
        which reads as a state the item is IN rather than as a value nothing can
        act on."""
        self.seed(item(1, "com classe inventada", klass="URGENTE"))
        r = self.run_tk("list")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("URGENTE", r.stdout)
        self.assertIn("AUTONOMOUS", r.stdout)          # the classes it could have carried
        r = self.run_tk("pack")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("URGENTE", r.stdout)
        self.assertIn("--class", r.stdout)             # the repair, not merely the fact

    def test_the_round_trip_holds_over_the_NORMALISED_text(self):
        """The parse's invariant is stated over what `read` returns, not over the
        bytes on disk: normalisation happens ONCE, at the door, and every reader
        and every writer downstream sees the same text."""
        raw = (f"- [ ]{self.NBSP}**T001** — texto **Class:** AUTONOMOUS. **Effort:** S.\n"
               "   \n"
               "  uma nota\n").encode()
        text = self.tk.normalize_source(raw, "next-steps.md")
        blocks = [b for kind, b in self.tk.split_blocks(text) if kind.startswith("item")]
        self.assertEqual(len(blocks), 1)
        self.assertIn("- [ ] **T001**", blocks[0])
        self.assertEqual(self.tk.render_item(self.tk.parse_item(blocks[0])), blocks[0])


# --- a marker inside a code span is not a field ---------------------------

class TestAMarkerInACodeSpanIsNotAField(QueueTest):
    """The one shape the POSITION rule cannot judge: prose that quotes a real
    field name in bold-colon and ends in a period is contiguous with the chain
    and joins it, indistinguishable from the field it imitates. Measured, each
    exiting 0 and printing "updated": `edit --class AUTONOMOUS --project tk`
    overwrote four words of an item's own title, and `--risk none` DELETED the
    imitating segment whole.

    The rule: a marker inside a Markdown code span is NEVER a field. Outside
    one, the position rule is exactly what it was — a marker before the
    **Class:** the chain begins at is still prose, and `edit` still refuses it
    rather than guessing. What changes is that an item now HAS a way to say so,
    which is what makes a repair without the done-log possible: the house
    already taught this exit, in the refusal that says "or `Project:` in a code
    span".
    """

    def setUp(self):
        super().setUp()
        self.tk = load_tk()

    QUOTED = ("- [ ] **T007** — cita o `**Risk:** alto` de outra fila. "
              "**Class:** AUTONOMOUS. **Effort:** M. **Risk:** alto de verdade. "
              "**Criterion:** A: x. **Project:** tk. **Source:** 2026-08-21\n")
    QUOTED_CLASS = ("- [ ] **T007** — cita a `**Class:** DECISION` de outra fila. "
                    "**Class:** AUTONOMOUS. **Effort:** M. **Criterion:** A: x. "
                    "**Project:** tk. **Source:** 2026-08-21\n")

    def test_the_quoted_marker_is_not_the_anchor_and_the_real_risk_survives(self):
        """T164: with two Class markers, one quoted in prose and one real, the
        chain used to anchor on the FIRST — the prose one — and `--risk none`
        deleted the real Risk field."""
        self.seed(self.QUOTED)
        r = self.run_tk("edit", "T007", "--risk", "none")
        self.assertEqual(r.returncode, 0, r.stderr)
        body = self.body()
        self.assertNotIn("**Risk:** alto de verdade.", body)
        self.assertIn("cita o `**Risk:** alto` de outra fila.", body)
        self.assertIn("**Class:** AUTONOMOUS.", body)

    def test_the_quoted_marker_is_never_rewritten_by_an_edit(self):
        """The other direction of the same defect: `edit --class` rewrote the
        prose in place of the field."""
        self.seed(self.QUOTED_CLASS)
        r = self.run_tk("edit", "T007", "--class", "DECISION",
                        "--deferred", "afk: decide primeiro")
        self.assertEqual(r.returncode, 0, r.stderr)
        body = self.body()
        self.assertIn("cita a `**Class:** DECISION` de outra fila.", body)
        self.assertEqual(body.count("**Class:** DECISION."), 1)

    def test_pack_stops_excluding_it_for_a_marker_no_gate_reads(self):
        """`pack` refuses an item that carries a **Risk:** marker the position
        rule may not read: unknown danger is not dispatched unattended. A quoted
        marker used to count, so an item that merely QUOTES the field left every
        package on every machine — and `assertIn(id)` is not the check, since
        the exclusion list names the id too."""
        self.seed("- [ ] **T010** — cita o `**Risk:** de outra fila` na prosa. "
                  "**Class:** AUTONOMOUS. **Effort:** S. **Criterion:** A: x. "
                  "**Project:** tk. **Source:** 2026-08-21\n")
        r = self.run_tk("pack")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("eligible (1 of 1", r.stdout)
        self.assertNotIn("no gate reads it", r.stdout)

    def test_list_groups_it_under_the_real_tag_not_the_quoted_one(self):
        """The T063 incident with the repair in place: an item whose text said
        `**Project:** para o done-log` acquired the tag "para"."""
        self.seed("- [ ] **T008** — levar o campo `**Project:** para` o done-log. "
                  "**Class:** AUTONOMOUS. **Effort:** S. **Criterion:** A: x. "
                  "**Project:** tk. **Source:** 2026-08-21\n")
        r = self.run_tk("list")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("## tk", r.stdout)
        self.assertNotIn("## para", r.stdout)

    def test_the_remedy_the_pack_prints_is_ACCEPTED_by_the_guard(self):
        """T134's dead end: the `edit --text` the exclusion prints was refused by
        `ensure_no_embedded_marker` whenever the text carried a marker of its
        own, so the prescribed remedy could not repair the item it addressed.
        The guard now asks the SAME tokenizer the reader asks.

        The assertion is the WHOLE line, never `assertIn` on the text that went
        in: the text the caller passed is written at the head of the line, so it
        is present in a body the command also CORRUPTED. Measured on this very
        fixture while the tail was cut by a regex of its own — the cut landed
        inside the code span, the item came back as
        `cita o `**Risk:** alto` de outra fila **Risk:** alto` de outra fila.
        **Class:** …`, and this test passed over it.
        """
        self.seed(self.QUOTED)
        r = self.run_tk("edit", "T007", "--text",
                        "cita o `**Risk:** alto` de outra fila")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(
            self.body().strip().splitlines()[-1],
            "- [ ] **T007** — cita o `**Risk:** alto` de outra fila "
            "**Class:** AUTONOMOUS. **Effort:** M. **Risk:** alto de verdade. "
            "**Criterion:** A: x. **Project:** tk. **Source:** 2026-08-21")

    def test_the_tail_the_remedy_KEEPS_is_cut_outside_the_code_span(self):
        """The other half of the same write, and the one no `assertIn` sees: the
        chain `--text` preserves is found with the reader's tokenizer, so the cut
        never lands between a code span's two backticks.

        Cut inside it, the opening backtick stayed in the text being replaced and
        the closing one did not, so the quotation came back as a REAL marker
        sitting before the chain — the item's prose duplicated around it, and the
        item pushed out of `pack` into the cancel-and-re-add dead end this rule
        exists to open a way out of. Exit code 0, "T007 updated", both times.
        """
        self.seed(self.QUOTED)
        r = self.run_tk("edit", "T007", "--text", "texto novo, sem marcador nenhum")
        self.assertEqual(r.returncode, 0, r.stderr)
        line = self.body().strip().splitlines()[-1]
        self.assertEqual(
            line,
            "- [ ] **T007** — texto novo, sem marcador nenhum "
            "**Class:** AUTONOMOUS. **Effort:** M. **Risk:** alto de verdade. "
            "**Criterion:** A: x. **Project:** tk. **Source:** 2026-08-21")
        # the discriminating half: the corrupted line above put a **Risk:**
        # marker in front of the chain, and `pack` answered "a **Risk:** marker
        # sits where no gate reads it" — the exclusion whose only printed remedy
        # is cancel + re-add
        p = self.run_tk("pack")
        self.assertNotIn("no gate reads it", p.stdout)

    def test_a_quoted_marker_does_not_block_GIVING_the_item_that_field(self):
        """The refusal that guards `edit` against a marker OUTSIDE the chain asks
        the same tokenizer too: a quoted marker is not one it may fire on.

        Measured before this: an item that merely CITES `**Project:**` in a code
        span and carries no real Project field answered `--project tk` with "has a
        **Project:** marker OUTSIDE its field chain … Close the item with `cancel`
        and re-add it clean" — prescribing the done-log lie for prose the caller
        had already quoted precisely to say it was prose.
        """
        self.seed("- [ ] **T001** — o item cita `**Project:**` numa code span. "
                  "**Class:** AUTONOMOUS. **Effort:** M. **Criterion:** A: x. "
                  "**Source:** 2026-08-21\n")
        r = self.run_tk("edit", "T001", "--project", "tk")
        self.assertEqual(r.returncode, 0, r.stderr)
        body = self.body()
        self.assertIn("o item cita `**Project:**` numa code span.", body)
        self.assertIn("**Project:** tk.", body)

    def test_a_BARE_marker_in_free_text_is_still_refused(self):
        """The position rule outside a code span is unchanged, and so is the
        refusal: an unquoted marker in free text would still be read as the real
        field and hijack it."""
        self.seed(item(1, "um"))
        r = self.run_tk("edit", "T001", "--text", "leva o **Project:** para o done-log")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("field-marker shape", r.stderr)
        self.assertIn("code span", r.stderr)

    def test_an_asterisk_in_a_value_no_longer_cuts_the_chain(self):
        """T258: the value grammar stopped at the first `*`, so a criterion
        naming a glob broke the chain BEFORE **Class:** — and the item left
        `pack` with no error visible anywhere and an age of `?`."""
        self.seed()
        r = self.run_tk("add", "com um glob no criterio", "--class", "AUTONOMOUS",
                        "--effort", "S", "--criterion", "A: o glob *.md casa",
                        "--source", "2026-08-13")
        self.assertEqual(r.returncode, 0, r.stderr)
        p = self.run_tk("pack")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("eligible (1 of 1", p.stdout)
        li = self.run_tk("list")
        # the CLASS COLUMN, never the whole line: with the chain broken the
        # title stops being cut at the first marker and prints the fields
        # verbatim, so `assertIn("AUTONOMOUS")` passes on the very output that
        # shows the item has lost its class
        self.assertRegex(li.stdout, r"T001\s+AUTONOMOUS")

    def test_an_odd_backtick_leaves_the_field_a_field(self):
        """The safe direction of the tokenizer: an opener with no closer of its
        own width is literal text and opens nothing, so the fields after it are
        still fields. The other direction would swallow the rest of the line —
        the `*` defect with a different character."""
        self.seed("- [ ] **T009** — fala de uma ` crase sozinha "
                  "**Class:** AUTONOMOUS. **Effort:** S. **Criterion:** A: x.\n")
        r = self.run_tk("list")
        self.assertEqual(r.returncode, 0, r.stderr)
        # the class COLUMN: see the note in the asterisk test above
        self.assertRegex(r.stdout, r"T009\s+AUTONOMOUS")

    def test_a_marker_inside_a_code_span_is_not_a_field_at_all(self):
        """The parse's own answer, under the rule: the quoted marker is not in
        the chain, and the item's title keeps it verbatim."""
        fields = self.tk.parse_item(self.QUOTED).fields
        self.assertEqual([f.canonical for f in fields],
                         ["Class", "Effort", "Risk", "Criterion", "Project", "Source"])
        self.assertIn("`**Risk:** alto`", self.tk.parse_item(self.QUOTED).title)
        self.assertEqual(self.tk.render_item(self.tk.parse_item(self.QUOTED)), self.QUOTED)




# --- T135/T134: a class VALUE a human wrote in Portuguese --------------------
#
# The field NAME in Portuguese was never the exclusion — `**Classe:**` and
# `**Esforço:**` are read as the fields they are, and the item statement of T135
# is stale about that. What excludes is the VALUE: every gate compares it with
# CLASSES, so `**Classe:** EXTERNA.` leaves the item invisible to `pack` and to
# every afk package on every machine. Measured 2026-09-06 over the twelve real
# queues: 26 items in five of them, spelled AUTÔNOMA, BLOQUEADA, DECISÃO and
# EXTERNA — plus three (`USER`, `ASSISTANT`, `n`) that no mapping carries and
# `migrate` therefore NAMES instead of guessing at.

class TestAClassValueInPortuguese(QueueTest):
    """`migrate` translates what the map carries, names the rest, and the
    `pack` repair line is derived from that same map."""

    LEGACY = ("- [ ] **T001** — item legado com classe em português "
              "**Classe:** EXTERNA (João/contrato). **Esforço:** P. "
              "**Critério:** A: x. **Fonte:** 2026-07-31\n")

    def test_a_mapped_value_is_written_as_the_enum_and_the_item_leaves_pack(self):
        """The whole file, because this command rewrites the user's only copy —
        and the qualifier `(João/contrato)` is the item's substance, not
        decoration, so a translation that replaced the segment would delete it."""
        self.seed(self.LEGACY)
        r = self.run_tk("migrate")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.body(),
                         HEADER + self.LEGACY.replace("EXTERNA (", "EXTERNAL (")
                         .replace("**Fonte:** 2026-07-31",
                                  "**Born:** 2026-07-31. **Fonte:** 2026-07-31"))
        self.assertIn("1 item(s) with a class value in Portuguese: written as the enum "
                      "every gate reads — T001 (EXTERNA → EXTERNAL)\n", r.stdout)
        p = self.run_tk("pack")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertNotIn("which is none of", p.stdout)
        # DESIGN-L13 §3's idempotence proof, on THIS path: an enum is not a
        # spelling the map carries, so a second run has to leave the bytes alone
        # AND say nothing — a report naming work on a file it did not touch is
        # what the caller acts on. The suite's other second-run test seeds the
        # walk's shape, so it never reached the translation
        after = self.body()
        again = self.run_tk("migrate")
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertEqual(self.body(), after)
        self.assertNotIn("with a class value in Portuguese", again.stdout)

    def test_a_value_no_mapping_carries_is_left_and_NAMED(self):
        """The other half, and the one that makes this a migration rather than a
        rewrite: `USER` is not Portuguese for any of the five, so nothing here
        chooses one for it. The item keeps the value it had and the report says
        which item and why."""
        seeded = self.LEGACY.replace("EXTERNA (João/contrato)", "USER")
        self.seed(seeded)
        r = self.run_tk("migrate")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("**Classe:** USER.", self.body())
        self.assertIn("1 item(s) left with a class value no gate reads: no "
                      "Portuguese-to-enum mapping carries this spelling, and inventing "
                      "one would be inventing a class — T001. Give each one of "
                      "AUTONOMOUS, DECISION, BLOCKED, EXTERNAL, RECURRING with "
                      "`tk-queue edit <id> --class <CLASS>`.\n", r.stdout)

    def test_the_pack_repair_offers_exactly_what_migrate_translates(self):
        """T134: the printed remedy fails by promising a repair the command does
        not make. Derived from CLASS_ALIASES, so the line can only say what
        `migrate` does — asserted against the map itself, never against a copy of
        the sentence."""
        tk = load_tk()
        self.seed(self.LEGACY.replace("EXTERNA (João/contrato)", "USER"))
        p = self.run_tk("pack")
        self.assertEqual(p.returncode, 0, p.stderr)
        line = next(ln for ln in p.stdout.splitlines()
                    if ln.startswith("- a class value that is no class:"))
        self.assertIn("`tk-queue migrate` writes the spellings it maps", line)
        for pt, enum in tk.CLASS_ALIASES.items():
            self.assertIn(pt, line)
            self.assertIn(enum, line)
        self.assertIn("NAMES the rest", line)


# --- T170/T216: the close whose LOG half landed and whose QUEUE half did not --
#
# `close_item` writes the done-log and then the queue, through two separate
# `write_atomic` calls with nothing spanning them; `cmd_migrate` does the same.
# `reference/queue.md` accepts that window on purpose — "log written first, so a
# crash between the two writes can duplicate a line but never lose the item" —
# and the correction belongs on the REPLAY side, which is what this class pins.
#
# Measured on the script before this slice: with an entry for T001 already in
# the log and T001 still open, a second `done` wrote a SECOND line and printed
# "done-log as FEITO"; a second `migrate` re-inserted every moved block right
# under the migration header, duplicating the lines AND putting the newer copies
# above the older ones, so the log's order stopped being its history.

class TestAnInterruptedCloseIsFinishedNotRepeated(QueueTest):
    """The queue half is finished, the log half is never written twice."""

    def today(self):
        return datetime.date.today().isoformat()

    def test_done_and_cancel_finish_the_queue_write_without_a_second_line(self):
        """T170. Both commands close through `close_item`, so neither can keep a
        silence the other lost — and the WHOLE done-log is the assertion, because
        an `assertNotIn` on the second line would pass just as happily on a log
        this command had rewritten some other way."""
        log = "- 2026-08-01 — FEITO — T001 um — PR #1\n"
        for cmd, extra in (("done", ("--how", "PR #2")), ("cancel", ("--why", "n/a"))):
            with self.subTest(cmd=cmd):
                self.seed(item(1, "um"), log=log)
                r = self.run_tk(cmd, "1", *extra)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertIn("tk-queue: warning: T001 already has a done-log entry",
                              r.stderr)
                self.assertEqual(self.body("done-log.md"), log)
                # the queue as any other close leaves it: excise collapses the
                # blank line the removed item had held open
                self.assertEqual(self.body(), HEADER.rstrip("\n") + "\n")
                self.assertEqual(r.stdout, "T001 → out of the queue; its done-log "
                                           "entry was already written\n")

    def test_a_legacy_open_box_parked_in_the_log_is_not_an_interrupted_close(self):
        """The constraint the detection is built on. `done_log_ids` also sees a
        `- [ ] **T005**` parked in done-log.md — a deliberate tolerance, so an ID
        left there is never handed out twice. Asking THAT question here invents
        an interrupted close for an item whose entry was never written, and the
        close then leaves the queue with no record of the item anywhere."""
        self.seed(item(5, "cinco"), log="- [ ] **T005** — caixa aberta parada no log\n")
        r = self.run_tk("done", "5", "--how", "PR #1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("already has a done-log entry", r.stderr)
        self.assertEqual(r.stdout, f"T005 → done-log as FEITO ({self.today()})\n")
        self.assertIn(f"- {self.today()} — FEITO — T005 cinco — PR #1",
                      self.body("done-log.md"))

    def test_a_migrate_replayed_after_a_crash_writes_no_second_copy(self):
        """T216, the crash reconstructed. `migrate` saves the log and then the
        queue, so a kill between the two leaves every moved block in BOTH files —
        and restoring next-steps to what it was IS that state, byte for byte.
        Both whole files are asserted: the duplication showed up as much in the
        log's ORDER as in its length."""
        seeded = ("- [x] legado feito, movido verbatim\n\n"
                  "- [x] **T004** — outro legado, com ID\n\n" + item(1, "um"))
        self.seed(seeded)
        first = self.run_tk("migrate")
        self.assertEqual(first.returncode, 0, first.stderr)
        after_queue, after_log = self.body(), self.body("done-log.md")
        self.write("next-steps.md", HEADER + seeded)   # the crash: log yes, queue no
        second = self.run_tk("migrate")
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertIn("tk-queue: warning: 2 [x] item(s) are already in", second.stderr)
        self.assertEqual(self.body("done-log.md"), after_log)
        self.assertEqual(self.body(), after_queue)
        self.assertIn("0 [x] item(s) → done-log", second.stdout)

    def test_a_block_the_log_only_PREFIXES_is_still_moved(self):
        """Line-anchored equality, never any substring. A legacy `- [x] feito`
        whose text merely OPENS a longer line already in the log would otherwise
        be read as already moved: it would leave the queue and its record would
        never be written — losing the item, which is the one outcome the window
        in `queue.md` is accepted for never causing."""
        self.seed("- [x] feito\n\n" + item(1, "um"),
                  log="- [x] feito junto com o outro tracker\n")
        r = self.run_tk("migrate")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("1 [x] item(s) → done-log", r.stdout)
        self.assertIn("- [x] feito\n", self.body("done-log.md"))


# --- T173: the package and the listing show the SAME item -------------------
#
# `list` and `pack` are one pair of functions over one file, and five display
# defects lived in the gap between them. Each was measured on this tree before
# the slice that closes it, and each is a way a caller reads one thing off the
# screen and dispatches another:
#
#   the mark      `list` marks both rows of a duplicated ID and says only the
#                 first is reachable; `pack` printed the two rows plain, and
#                 `pack` is the output an unattended package is actually cut from
#   the title     it was cut at the first READABLE marker instead of at the field
#                 chain, so an item quoting a field name in its own sentence was
#                 columned mid-phrase — in BOTH readers, with nothing saying so
#   the prose     with no marker to cut at, the whitespace collapse pulled the
#                 item's continuation lines into the title
#   the column    a label is the item's own spelling, so `T0001` and `T1000` are
#                 five characters where `T001` is four, and the wide one pushed
#                 the class column one place right
#   the holder    the briefing report rebuilt the holder's label from the NUMBER,
#                 so the item spelled `T0001` was reported as `T001`

WIDE = "**T0001**"


class TestThePackShowsWhatTheListShows(QueueTest):

    def wide(self, text="item de id largo"):
        return item(1, text).replace("**T001**", WIDE, 1)

    def eligible_line(self, out, label):
        for ln in out.splitlines():
            if ln.startswith(label + " ") or ln == label:
                return ln
        self.fail(f"{label} is not in:\n{out}")

    # --- the mark ---------------------------------------------------------

    def test_the_package_marks_a_duplicated_id_the_way_the_listing_does(self):
        """Both blocks of the package, because the mark is what tells the reader
        that dispatching the second row would act on the first."""
        self.seed(item(5, "primeira ocorrencia"), item(5, "segunda ocorrencia"))
        out = self.run_tk("pack").stdout
        self.assertEqual(
            [ln for ln in out.splitlines() if ln.startswith("T005")],
            ["T005  S             avulso                primeira ocorrencia"
             "  [duplicate ID 5]",
             "T005  S             avulso                segunda ocorrencia"
             "  [duplicate ID 5]"])
        # and the sentence that says what the mark MEANS, in the block this
        # command puts its remedies in. Taken from the LISTING rather than
        # respelled here: the two describing one ambiguity differently is the
        # divergence this whole class is about, and a hardcoded copy would go on
        # passing while they drifted
        note = self.run_tk("list").stdout.split("\n\n")[-1].strip()
        self.assertTrue(note.startswith("duplicate IDs:"), note)
        self.assertIn("- " + note + "\n", out)

    def test_an_EXCLUDED_row_carries_the_mark_ahead_of_its_reason(self):
        """The exclusion reason ends the line by contract, so the mark cannot be
        appended after it — a caller reading `— class is DECISION [duplicate ID 5]`
        reads the mark as part of the reason."""
        self.seed(item(5, "excluida", klass="DECISION"), item(5, "outra", klass="DECISION"))
        out = self.run_tk("pack").stdout
        self.assertIn("T005  excluida  [duplicate ID 5]  — class is DECISION\n", out)

    def test_an_ID_carried_by_ONE_item_is_marked_in_neither_reader(self):
        """The other direction. A mark on every row says nothing, and the reader
        who learns to skip it skips the two rows it was written for."""
        self.seed(item(5, "unico"), item(6, "outro"))
        for cmd in ("list", "pack"):
            with self.subTest(cmd=cmd):
                out = self.run_tk(cmd).stdout
                self.assertNotIn("duplicate ID", out)

    # --- the title --------------------------------------------------------

    def quoting(self, tail):
        return ("- [ ] **T002** — o item cita **Project:** de outra fila e segue a frase"
                + tail + " **Class:** AUTONOMOUS. **Effort:** S. **Criterion:** A: x. "
                "**Source:** 2026-08-13\n")

    def test_a_field_name_in_the_users_own_sentence_does_not_cut_the_title(self):
        """Measured: both readers columned this item as `o item cita`, four words
        into a sentence of eleven, and nothing anywhere said the rest existed.

        Both subtests, because the period decides which BOUNDARY has to hold. With
        it, the imitating segment joins the run and only the position rule — every
        segment ahead of the **Class:** anchor is the item's own prose — puts the
        sentence back. Without it the run breaks before the marker, and the title
        is right as soon as it ends at the chain instead of at the first marker.
        A fixture carrying only the second shape passes on the first reading too,
        which is the vacuity this pair exists to avoid."""
        for name, tail in (("com ponto", "."), ("sem ponto", "")):
            with self.subTest(prosa=name):
                self.seed(self.quoting(tail))
                whole = ("o item cita **Project:** de outra fila e segue a frase"
                         + tail)
                self.assertEqual(
                    self.run_tk("list").stdout.split("?  ")[1].rstrip("\n"), whole)
                self.assertIn(whole, self.run_tk("pack").stdout)

    def test_a_continuation_line_is_not_absorbed_into_the_title(self):
        """A title is ONE line. With no marker anywhere to cut at, the collapse of
        whitespace ran straight through the newline and columned the author's note
        as the tail of their own sentence."""
        self.seed("- [ ] **T004** — titulo sem campo nenhum.\n"
                  "  uma nota de continuacao inteira.\n")
        self.assertEqual(self.run_tk("list").stdout,
                         "T004  ?              ?  titulo sem campo nenhum.\n")
        self.assertIn("T004  titulo sem campo nenhum.  — no **Class:** field\n",
                      self.run_tk("pack").stdout)

    def test_the_prose_the_title_keeps_is_STILL_kept_out_of_the_done_log_remedy(self):
        """The over-correction the title fix could buy, and the expensive one:
        `edit --text` REPLACES an item's text, so the remedy `handoff` prints has
        to carry the continuation lines the title now leaves out. Cut to the first
        line, that remedy runs, reports success and deletes the author's note."""
        self.seed("- [ ] **T004** — titulo do item.\n"
                  "  uma nota de continuacao inteira.\n"
                  "  **Class:** AUTONOMOUS. **Effort:** S. **Criterion:** A: x.\n")
        r = self.run_tk("handoff", "4", "--objective", "o", "--state", "s",
                        "--blockers", "b")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("titulo do item. uma nota de continuacao inteira. "
                      "[[handoff-T004]]", r.stderr)

    # --- the column -------------------------------------------------------

    def test_a_wide_label_does_not_push_the_column_beside_it(self):
        """`T0001` is five characters and `T001` is four, and the ID column was
        neither padded nor measured — so the class column of a queue carrying both
        started in two places, on exactly the rows that need a second look."""
        self.seed(item(1, "curto"), self.wide(), item(1000, "quatro digitos"))
        rows = self.run_tk("list").stdout.splitlines()[:3]
        self.assertEqual([ln.index("AUTONOMOUS") for ln in rows], [7, 7, 7])
        pack = self.run_tk("pack").stdout.splitlines()
        self.assertEqual([ln.index("S    ") for ln in pack[1:4]], [7, 7, 7])

    def test_a_queue_of_canonical_labels_prints_exactly_what_it_printed_before(self):
        """The over-correction direction. Widening is paid for by the listings
        that have something to widen for: a queue whose labels are all
        `T001`-shaped keeps the line every skill and every eye already reads, and
        a column one character wider than it needs moves EVERY queue's output for
        the sake of the few that carry a wide label."""
        self.seed(item(1, "um"), item(2, "dois"))
        self.assertEqual(self.run_tk("list").stdout,
                         "T001  AUTONOMOUS     ?  um\n"
                         "T002  AUTONOMOUS     ?  dois\n")

    def test_the_package_prints_its_headings_over_an_empty_queue(self):
        """The width is asked of the rows, and an empty queue has none — so the
        default is what stands between this command and a traceback on the one
        queue whose report is `nothing to do`."""
        self.write("next-steps.md", HEADER)
        r = self.run_tk("pack")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("Traceback", r.stderr)
        self.assertIn("eligible (0 of 0, in queue order):\n(none)\n", r.stdout)

    # --- the holder -------------------------------------------------------

    def test_a_kept_briefing_names_its_holder_by_the_items_own_spelling(self):
        """`f"T{iid:03d}"` rebuilds a label from the NUMBER, and `int("0001")` is
        1 — so the report sent the reader to look up a T001 that is either absent
        or a DIFFERENT item. The report is the only place the surviving holder is
        ever named."""
        self.seed(self.wide("o item de grafia larga [[handoff-T001]]"),
                  item(2, "outro que aponta [[handoff-T001]]"))
        self.write("handoff-T001.md", "# Handoff T001\n\nobjetivo\n")
        r = self.run_tk("done", "2", "--how", "PR #1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("handoff-T001.md kept — still reached by T0001\n", r.stdout)


# --- T174: what the fold does to the user's own RENDERING --------------------
#
# Two limits of the fold were declared in the source and had no test, so nothing
# said whether either was still true — and each is a silent change of how the
# item RENDERS, made under a line reporting the item as folded. Both are measured
# here on this branch before the slice that closes them:
#
#   the hard break   two spaces ending a line are CommonMark asking for a line
#                    break, and so is a backslash ending it — the visible
#                    spelling of the same request, which the rule read only in
#                    its invisible one until C-14. The join strips either and the
#                    item comes back one paragraph, reported as folded. There is
#                    no preserving answer — a join is the operation that destroys
#                    a line break — so the fold declines and names the item.
#   the underline    a setext underline promotes the WHOLE paragraph above it.
#                    `opens_a_block` protects only the line directly above, so a
#                    title hard-wrapped over two lines had its earlier lines
#                    absorbed into the head and its last one left under the
#                    underline: half a heading in each place.
#
# Every test here asserts the WHOLE file. This command rewrites the queue, which
# holds the user's own prose and has no other copy, and both defects survive any
# narrower assertion — the FIELDS end up right either way, which is all a
# substring check ever looked at.

T174_HEAD = ("- [ ] **T007** — primeira linha do titulo que passa bem da coluna de "
             "dobra para que a geometria licencie a absorcao")
T174_CHAIN = "  **Class:** AUTONOMOUS. **Effort:** S. **Criterion:** A: x.\n"


class TestTheFoldKeepsTheAuthorsLineBreaks(QueueTest):

    def migrate(self):
        r = self.run_tk("migrate")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("Traceback", r.stderr)
        return r

    def left_alone(self, why, *labels):
        return (f"{len(labels)} item(s) left exactly as they are: {why} — "
                + ", ".join(labels) + ". Close each with `cancel` and re-add it clean.\n")

    HARD = ("a line the join would absorb ends in a HARD line break (two spaces, or "
            "a backslash), which is a break the author wrote and the join cannot "
            "carry — the item is left with its rendering intact")
    SETEXT = ("a setext underline promotes the WHOLE paragraph above it, and the join "
              "would absorb part of that paragraph into the first line and leave the "
              "rest under the underline — half a heading in each place")

    # --- the hard break ---------------------------------------------------

    def test_a_hard_break_above_an_absorbed_line_stops_the_fold(self):
        """Both fold paths, because they join by two different routes and the
        break dies on either. The walk relocates a chain that owns its own lines;
        the wrapped path undoes the hard wrap that split the chain itself. A
        fixture exercising one leaves the other free to go on flattening."""
        for name, tail in (
                ("dobra por caminhada", "  segunda linha comprida o bastante para a "
                                        "geometria licenciar.\n" + T174_CHAIN),
                ("dobra da linha quebrada", "  segunda linha comprida o bastante. "
                                            "**Class:** AUTONOMOUS. **Effort:** S. "
                                            "**Criterion:** A: x.\n")):
            with self.subTest(caminho=name):
                seeded = T174_HEAD + "  \n" + tail
                self.seed(seeded)
                r = self.migrate()
                self.assertIn(self.left_alone(self.HARD, "T007"), r.stdout)
                self.assertNotIn("folded up", r.stdout)
                self.assertEqual(self.body(), HEADER + seeded)

    def test_a_break_on_an_INTERIOR_absorbed_line_stops_the_fold_too(self):
        """The scan is asked of every line the join absorbs, and the pair above
        proves only the FIRST of them: both of their fixtures put the two spaces
        at the end of the head line. Measured, with the scan narrowed to the head
        alone — `range(min(j, len(lines) - 1, 1))` — the whole suite stayed green
        while a break the author wrote on a continuation line went on dying at the
        join, under a run reporting the item as folded.

        The walk path on purpose: it is the one that absorbs a paragraph of more
        than one line, so it is the only one where `k` has anywhere to reach that
        `k == 0` does not."""
        seeded = (T174_HEAD + "\n  segunda linha comprida o bastante para a "
                  "geometria licenciar.  \n" + T174_CHAIN)
        self.seed(seeded)
        r = self.migrate()
        self.assertIn(self.left_alone(self.HARD, "T007"), r.stdout)
        self.assertNotIn("folded up", r.stdout)
        self.assertEqual(self.body(), HEADER + seeded)

    def test_the_OTHER_spelling_of_the_break_stops_the_fold_too(self):
        """C-14. CommonMark gives a trailing backslash as the second spelling of
        the hard break, and it is the one an author reaches for precisely because
        two trailing spaces are invisible in an editor. Read only in the
        invisible spelling, the visible one died at the join in silence, under a
        line reporting the item as folded.

        Both fold paths, for the reason the spaces fixture gives: they join by
        two different routes and the break dies on either."""
        for name, tail in (
                ("dobra por caminhada", "  segunda linha comprida o bastante para a "
                                        "geometria licenciar.\n" + T174_CHAIN),
                ("dobra da linha quebrada", "  segunda linha comprida o bastante. "
                                            "**Class:** AUTONOMOUS. **Effort:** S. "
                                            "**Criterion:** A: x.\n")):
            with self.subTest(caminho=name):
                seeded = T174_HEAD + "\\\n" + tail
                self.seed(seeded)
                r = self.migrate()
                self.assertIn(self.left_alone(self.HARD, "T007"), r.stdout)
                self.assertNotIn("folded up", r.stdout)
                self.assertEqual(self.body(), HEADER + seeded)

    def test_a_backslash_INSIDE_the_line_is_not_a_break(self):
        """The over-refusal direction of the same spelling, and the one that
        would cost the fold real items: a backslash only asks for a break where
        it ENDS the line. Queues carry them mid-sentence — an escape, a Windows
        path, a regex quoted in prose — and a rule that read those as the
        author's break would refuse the population the fold exists for."""
        seeded = (T174_HEAD + "\n  segunda linha com C:\\Users\\algo no meio dela, "
                  "comprida o bastante para a geometria licenciar.\n" + T174_CHAIN)
        self.seed(seeded)
        r = self.migrate()
        self.assertIn("folded up, where every gate reads them — T007\n", r.stdout)
        self.assertEqual(self.body(),
                         HEADER + T174_HEAD + " segunda linha com C:\\Users\\algo no "
                         "meio dela, comprida o bastante para a geometria licenciar. "
                         "**Class:** AUTONOMOUS. **Effort:** S. **Criterion:** A: x.\n")

    def test_the_break_is_TWO_spaces_and_not_one(self):
        """The over-refusal direction. One trailing space is not a hard break in
        any Markdown — it is whitespace nobody meant as anything, and a rule that
        read it as an author's break would refuse the wrapped population the fold
        exists for, on files editors leave trailing spaces in every day."""
        seeded = (T174_HEAD + " \n  segunda linha comprida o bastante para a "
                  "geometria licenciar.\n" + T174_CHAIN)
        self.seed(seeded)
        r = self.migrate()
        self.assertIn("folded up, where every gate reads them — T007\n", r.stdout)
        self.assertEqual(self.body(),
                         HEADER + T174_HEAD + " segunda linha comprida o bastante para "
                         "a geometria licenciar. **Class:** AUTONOMOUS. **Effort:** S. "
                         "**Criterion:** A: x.\n")

    def test_a_break_at_the_END_of_the_block_breaks_nothing(self):
        """The other over-refusal, and the one that would cost the fold real items:
        a hard break needs a line UNDER it to break before. Trailing spaces on the
        block's LAST line are the end of the item, and refusing there would take a
        whole population out over whitespace that renders as nothing.

        The fixture is the wrapped path on purpose. It is the only one that ever
        asks about the last line — the walk asks only as far as the paragraph it
        absorbs, which stops above the field run — so a walk fixture here would
        leave the rule unmeasured and read as if it had been proved."""
        self.seed(T174_HEAD + "\n  segunda linha comprida o bastante para a "
                  "geometria licenciar. **Class:** AUTONOMOUS. **Effort:** S. "
                  "**Criterion:** A: x.  \n")
        r = self.migrate()
        self.assertIn("folded up, where every gate reads them — T007\n", r.stdout)
        self.assertEqual(self.body(),
                         HEADER + T174_HEAD + " segunda linha comprida o bastante "
                         "para a geometria licenciar. **Class:** AUTONOMOUS. "
                         "**Effort:** S. **Criterion:** A: x.\n")

    # --- the setext underline ---------------------------------------------

    def test_a_paragraph_an_underline_promotes_is_not_split_by_the_fold(self):
        """Both spellings of the underline, and TWO lines above it — which is what
        makes the paragraph reach past the line `opens_a_block` protects. Measured
        on this branch: the middle line went up into the head with the chain, the
        last one stayed under the underline, and the run reported `folded up`."""
        for name, rule in (("igual", "  ===============\n"),
                           ("hifen", "  ---------------\n")):
            with self.subTest(sublinhado=name):
                seeded = (T174_HEAD + "\n"
                          "  segunda linha do mesmo paragrafo, escrita comprida o bastante "
                          "para quebrar na coluna de wrap e nao antes dela\n"
                          "  terceira linha do mesmo paragrafo, tambem comprida o "
                          "bastante, que fica logo acima do risco do sublinhado\n"
                          + rule + T174_CHAIN)
                self.seed(seeded)
                r = self.migrate()
                self.assertIn(self.left_alone(self.SETEXT, "T007"), r.stdout)
                self.assertNotIn("folded up", r.stdout)
                self.assertEqual(self.body(), HEADER + seeded)

    def test_a_heading_that_is_WHOLE_where_it_stands_is_still_folded_around(self):
        """The over-refusal direction, and the shape
        TestASetextTitleIsKeptWithItsUnderline already pins: with the underlined
        line directly under the head, nothing of the promoted paragraph is
        absorbed and the fold has nothing to split. A rule that refused here would
        take back a population the fold was measured handling correctly."""
        middle = "  Titulo da secao\n  ===============\n"
        self.seed(R5_LONG_HEAD + middle + R4_CHAIN)
        r = self.migrate()
        self.assertIn("folded up, where every gate reads them — T005\n", r.stdout)
        self.assertEqual(self.body(), HEADER + R5_FOLDED_HEAD + middle)

    def test_the_walk_still_stops_at_a_block_that_is_no_heading(self):
        """What decides the refusal has to be the SETEXT question and not "the
        walk stopped early". The walk stops at every Markdown block, and folding
        AROUND one — prose absorbed into the head, the block left with its own
        line — is the behaviour this command was measured getting right. A rule
        that fired wherever the walk stopped would refuse that whole population.

        A bullet, then, with a wrapped line above it: the walk stops at the same
        place the underline stops it, and nothing here is a promoted heading."""
        second = ("segunda linha do mesmo paragrafo, escrita comprida o bastante "
                  "para quebrar na coluna de wrap e nao antes dela")
        bullet = "  - um item de lista que o usuario escreveu\n"
        self.seed(T174_HEAD + "\n  " + second + "\n" + bullet + T174_CHAIN)
        r = self.migrate()
        self.assertIn("folded up, where every gate reads them — T007\n", r.stdout)
        self.assertEqual(self.body(),
                         HEADER + T174_HEAD + " " + second
                         + " **Class:** AUTONOMOUS. **Effort:** S. "
                         "**Criterion:** A: x.\n" + bullet)


# --- C-16: a field orphaned UNDER a chain the gates already read -------------
#
# The fold's first question was "does the chain reach **Class:**", and a YES
# ended the run: the item is in the shape every gate reads. True of the CLASS,
# and of nothing else — a second field left on a continuation line sits outside
# the chain, so no gate reads it, no repair is printed for it, and the run says
# nothing. Measured on `estudo-remuneracao-CN` T004, whose **Born:** has been
# below the chain since it was written: `list` shows its age as `?`, every
# `migrate` passes it over, and no command anywhere says why.

C16_HEAD = ("- [ ] **T004** — titulo do item, escrito comprido o bastante para que a "
            "quebra abaixo dele caia numa coluna de wrap **Class:** AUTONOMOUS. "
            "**Effort:** S. **Criterion:** A: x.")


class TestAFieldOrphanedUnderAChainThatIsAlreadyRead(QueueTest):

    def migrate(self):
        r = self.run_tk("migrate")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("Traceback", r.stderr)
        return r

    def test_the_orphan_is_lifted_and_every_other_line_keeps_its_place(self):
        """Three shapes of what can sit between the chain and the orphan, because
        the fold treats them as three: nothing, a wrapped paragraph, and a line
        that opens a Markdown block.

        The head already carries a chain, so NOTHING is absorbed in any of them —
        a line joined onto that line would land between the chain and the field
        being lifted, breaking the very chain the fold is relocating. The whole
        file is asserted: this command rewrites the user's only copy, and every
        defect this fold has produced survived a narrower check.

        The age is asserted on both sides of the run because it is the symptom
        the item was reported by: `?` while the field sits outside the chain, and
        the number the moment it joins it."""
        born = (datetime.date.today() - datetime.timedelta(days=12)).isoformat()
        orphan = f"  **Born:** {born}\n"
        for name, middle in (
                ("nada entre os dois", ""),
                ("prosa quebrada no wrap",
                 "  uma linha de prosa comprida o bastante para que a geometria "
                 "licenciasse a absorcao dela\n"),
                ("uma linha que abre bloco", "  - um item de lista do usuario\n")):
            with self.subTest(entre=name):
                self.seed(C16_HEAD + "\n" + middle + orphan)
                self.assertIn("T004  AUTONOMOUS     ?", self.run_tk("list").stdout)
                r = self.migrate()
                self.assertIn("folded up, where every gate reads them — T004\n",
                              r.stdout)
                self.assertEqual(self.body(),
                                 HEADER + C16_HEAD + f" **Born:** {born}\n" + middle)
                self.assertIn("T004  AUTONOMOUS   12d", self.run_tk("list").stdout)

    def left_alone(self, why, *labels):
        return (f"{len(labels)} item(s) left exactly as they are: {why} — "
                + ", ".join(labels) + ". Close each with `cancel` and re-add it clean.\n")

    SECOND_CLASS = ("the lift would put a SECOND **Class:** in the chain, and a chain "
                    "naming two classes is one no gate reads at all — the item is left "
                    "with the class it already has")
    ORPHAN_BREAK = ("the line the field is lifted out from under ends in a HARD line "
                    "break (two spaces, or a backslash), and the lift leaves that break "
                    "with nothing to break before — the item is left with its rendering "
                    "intact")

    def test_an_orphan_repeating_the_head_s_CLASS_is_left_and_REPORTED(self):
        """The lift may cost the item line breaks by refusing; it may never cost
        it its class. The head names one class, the orphan names another, and the
        chain the lift would write names TWO — which `chain_class` refuses to
        read, so `list` and every gate would answer `?` for an item that answers
        AUTONOMOUS today.

        The class is asserted on BOTH sides of the run, not just the file: a
        refusal that left the file byte-identical and the class unreadable would
        pass a file assertion, and the class is the whole of what this guard is
        for."""
        seeded = C16_HEAD + "\n  **Class:** DECISION. **Born:** 2026-01-01.\n"
        self.seed(seeded)
        self.assertIn("T004  AUTONOMOUS", self.run_tk("list").stdout)
        r = self.migrate()
        self.assertIn(self.left_alone(self.SECOND_CLASS, "T004"), r.stdout)
        self.assertNotIn("folded up", r.stdout)
        self.assertEqual(self.body(), HEADER + seeded)
        self.assertIn("T004  AUTONOMOUS", self.run_tk("list").stdout)

    def test_a_break_the_orphan_is_lifted_out_from_UNDER_stops_the_lift(self):
        """Both spellings, because the rule reads both and a fixture for one
        leaves the other free to go on flattening.

        This is not the break `absorption_audit` asks about. With a head that
        already carries a chain the window is empty, so the audit reaches
        `lines[0]` alone — and the line the orphan sat under keeps its place and
        still loses its break, because what it broke before has moved onto the
        first line. Measured with the guard removed: the item folded, `migrate`
        printed it as folded up, and the author's `<br>` was gone from the user's
        only copy."""
        prosa = ("  uma linha de prosa comprida o bastante para que a geometria "
                 "licenciasse a absorcao dela")
        for name, quebra in (("dois espacos", "  "), ("contrabarra", "\\")):
            with self.subTest(grafia=name):
                seeded = (C16_HEAD + "\n" + prosa + quebra + "\n"
                          + "  **Born:** 2026-01-01.\n")
                self.seed(seeded)
                r = self.migrate()
                self.assertIn(self.left_alone(self.ORPHAN_BREAK, "T004"), r.stdout)
                self.assertNotIn("folded up", r.stdout)
                self.assertEqual(self.body(), HEADER + seeded)


class TestMutationHarness(unittest.TestCase):
    """The harness is what says this suite protects anything, and until T152
    nothing checked IT. Each test here is a way the harness could go on printing
    a clean score over a list that proves less than it claims."""

    def setUp(self):
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import mutations
        self.h = mutations
        self.mod = sys.modules[__name__]

    def problem(self, entry, source="the anchor"):
        return self.h.entry_problem(entry, {"test_tk_queue": self.mod}, source)

    def test_an_entry_naming_a_test_that_does_not_exist_is_refused(self):
        """unittest answers a name it cannot load with a non-zero exit, and the
        runner reads non-zero as "the named test fell" — so a typo used to be
        scored as a mutant killed. It is the one failure worse than an uncovered
        guard: a guard reporting itself covered."""
        sound = ("a real one", "the anchor", "the mutant",
                 ["TestPrefixedId.test_garbage_is_still_rejected"])
        self.assertIsNone(self.problem(sound))
        kind, why = self.problem(("a typo", "the anchor", "the mutant",
                                  ["TestPrefixedId.test_no_such_thing"]))
        self.assertEqual(kind, "MISNAMED")
        self.assertIn("test_no_such_thing", why)
        gone = self.problem(("a class that went", "the anchor", "the mutant",
                             ["TestVanished.test_x"]))
        self.assertEqual(gone[0], "MISNAMED")

    def test_an_entry_naming_a_whole_class_is_not_read_as_a_typo(self):
        """Older entries name a CLASS, which unittest loads as readily as one
        method. Reading those as typos would report working entries as broken
        and bury the nine real ones."""
        self.assertIsNone(self.problem(("a whole class", "the anchor", "the mutant",
                                        ["TestPrefixedId"])))

    def test_a_mutation_that_changes_nothing_is_refused(self):
        kind, why = self.problem(("a no-op", "same", "same", ["TestPrefixedId"]))
        self.assertEqual(kind, "UNRUNNABLE")
        self.assertIn("no-op", why)

    def test_an_anchor_that_does_not_match_exactly_once_is_refused(self):
        """Zero matches means the code moved out from under the entry; two mean
        the mutation applied is not the one the label describes."""
        entry = ("a stale anchor", "nowhere in here", "the mutant", ["TestPrefixedId"])
        kind, why = self.problem(entry, source="a source without it")
        self.assertEqual(kind, "UNRUNNABLE")
        self.assertIn("matched 0x", why)
        twice = self.problem(("twice over", "here", "the mutant", ["TestPrefixedId"]),
                             source="here and here")
        self.assertIn("matched 2x", twice[1])

    def test_the_classes_the_baseline_runs_are_derived_not_listed(self):
        """A class missing from a hand-kept list drops out of the baseline and
        out of the orphan check at once, and says nothing on the way out. The
        list this replaced had forgotten the first two names below."""
        found = self.h.baseline_classes(self.mod)
        for name in ("TestPackLaneUnderWay", "TestEverySpawnCarriesTheRedirectedHome",
                     "TestPrefixedId", "TestMutationHarness"):
            self.assertIn(name, found)
        self.assertNotIn("QueueTest", found)   # a base class holds no tests

    def test_the_recorded_count_of_unproved_tests_is_not_below_the_real_one(self):
        """A test no entry names is a guard nobody proved, and the tally cannot
        show it: N/N counts the mutants someone wrote. The ceiling is what keeps
        a new one from arriving in silence."""
        import mutations_tk_contract
        real = mutations_tk_contract.unproved(
            self.h.per_module(self.h.MUTATIONS, "test_tk_queue"), self.mod)
        self.assertGreaterEqual(self.h.KNOWN_UNPROVED, len(real),
                                f"{len(real)} tests no entry names: {real}")

    def test_the_absorbed_roster_suite_keeps_its_own_unproved_ceiling(self):
        """The twenty entries absorbed from `mutations_roster.py` name tests in
        another module, and that suite's harness never had an orphan check. Its
        debt is a SECOND number: folded into the one above it would have raised a
        ceiling whose whole rule is that it only ever falls."""
        import mutations_tk_contract
        roster = mutations_tk_contract.load_module("test_tk_roster",
                                                   os.path.dirname(os.path.dirname(TK)))
        real = mutations_tk_contract.unproved(
            self.h.per_module(self.h.MUTATIONS, "test_tk_roster"), roster)
        self.assertGreaterEqual(self.h.KNOWN_UNPROVED_ROSTER, len(real),
                                f"{len(real)} roster tests no entry names: {real}")
        self.assertEqual(mutations_tk_contract.misnamed(
            self.h.per_module(self.h.MUTATIONS, "test_tk_roster"), roster), [])

    def test_the_recorded_count_of_misnamed_entries_is_not_below_the_real_one(self):
        """The debt is a ceiling to lower, and this is what makes it bite in two
        minutes instead of in the six the full harness takes: a tenth misnamed
        entry reddens the suite the moment it is written."""
        import mutations_tk_contract
        real = mutations_tk_contract.misnamed(
            self.h.per_module(self.h.MUTATIONS, "test_tk_queue"), self.mod)
        self.assertGreaterEqual(self.h.KNOWN_MISNAMED, len(real),
                                f"the list grew a misnamed entry: {real}")

    def test_a_name_may_say_which_suite_it_lives_in(self):
        """The one line that was a whole second harness file. `mutations_roster.py`
        existed because the module was hardcoded in `run_suite`, so an entry for
        another suite could not be written here at all — its own docstring said the
        merge was this. A leading lowercase `test_` is the whole rule, and counting
        dots instead broke the caller that hands over a whole CLASS: the baseline
        runs `module.Class`, two components naming a module."""
        self.assertEqual(self.h.qualify("TestX.test_y"),
                         ("test_tk_queue", "TestX.test_y"))
        self.assertEqual(self.h.qualify("test_tk_roster.TestX.test_y"),
                         ("test_tk_roster", "TestX.test_y"))
        self.assertEqual(self.h.qualify("test_tk_roster.TestX"),
                         ("test_tk_roster", "TestX"))
        self.assertEqual(self.h.qualify("TestX"), ("test_tk_queue", "TestX"))
        self.assertEqual(
            self.h.names_by_module(["TestX.test_y", "test_tk_roster.TestZ.test_w"]),
            {"test_tk_queue": ["TestX.test_y"], "test_tk_roster": ["TestZ.test_w"]})

    def test_an_entry_naming_a_module_this_run_never_loaded_is_refused(self):
        """`per_module` DROPS a name whose module nothing resolves, so without
        this the entry would be scored on the names that did resolve and its
        typo would never be asked about — the misnamed defect one level up."""
        kind, why = self.problem(("a typo'd module", "the anchor", "the mutant",
                                  ["test_tk_nothing.TestSweep.test_x"]))
        self.assertEqual(kind, "MISNAMED")
        self.assertIn("test_tk_nothing", why)

if __name__ == "__main__":
    unittest.main(verbosity=2)
