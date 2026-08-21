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


def item(iid, text, project=None, klass="AUTONOMOUS", risk=None, effort="S"):
    tag = f" **Project:** {project}." if project else ""
    risk_field = f" **Risk:** {risk}." if risk else ""
    return (f"- [ ] **T{iid:03d}** — {text} **Class:** {klass}. **Effort:** {effort}."
            f"{risk_field} **Criterion:** A: x.{tag} **Source:** 2026-08-13\n")


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


# --- T025: the displayed ID form must be accepted ------------------------

class TestPrefixedId(QueueTest):
    """The queue displays T006 everywhere and the contract writes `done <id>`,
    so `done T006` must work. It died in argparse's `invalid int value`."""

    def test_done_accepts_the_displayed_form(self):
        for form in ("T006", "t006", "006", "6", "T6"):
            with self.subTest(form=form):
                self.seed(item(6, "item seis"))
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
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            with self.assertRaises(subprocess.TimeoutExpired,
                                   msg="the writer did not wait for the lock"):
                proc.wait(timeout=1.5)
        finally:
            os.close(lock_fd)                      # releases the flock
        out, err = proc.communicate(timeout=30)
        self.assertEqual(proc.returncode, 0, err)  # and then it goes through
        self.assertIn("**T002**", self.body())

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
    # the ID vanish from the count. Measured on the LIVE m365 queue, which
    # carries `- [x] \u2705 **T020** \u2014 Defaults de compartilhamento ...` today:
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
                           capture_output=True, text=True, cwd=self.dir)
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
                            "--dir", other], capture_output=True, text=True, cwd=self.dir)
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

    def test_readers_stay_silent(self):
        """`list`, `report` and `pack` take no lock and write nothing — announcing a
        write target there would be noise on every read."""
        self.seed(item(1, "um"))
        for argv in (("list",), ("report", "--since", "2026-01-01"), ("pack",)):
            with self.subTest(cmd=argv[0]):
                r = self.run_tk(*argv)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertNotIn(self.mem, r.stderr)


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
        cases = {"a directory": lambda: os.mkdir(os.path.join(d, "env")),
                 "a non-UTF-8 byte": lambda: open(os.path.join(d, "env"), "wb").write(
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
        for good in ("alpha", "alpha.local", "sess-3", "Tarcisio_2"):
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


class TestPack(QueueTest):
    """The package an unattended session runs was filtered by eye until now, from
    `list` plus prose. Two things move when it becomes a command: the filter stops
    being re-derived every session, and — the reason the ticket exists — every
    exclusion becomes VISIBLE. An item dropped for its Risk or its Env leaves no
    trace anywhere else; silently absent, it is an item the user never learns
    about, on a queue they believe they have seen."""

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

    # --- the two lists ----------------------------------------------------
    def test_an_eligible_item_carries_its_id_effort_and_text(self):
        """Effort is in the package line because the caller sizes the package by it
        (3-6 items, ~2h) — raw, never summed: summing free text would put a hidden
        heuristic in a queue whose whole contract is that it has none."""
        self.seed(item(1, "um"))
        self.assertEqual(self.blocks(self.pack())["eligible"], ["T001  S             um"])

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
        self.seed(item(7, "the item's text", effort="S (~20min)")
                  + decision_item(12, "another item")
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
        self.assertEqual(self.blocks(self.pack())["eligible"], ["T001  ?             um"])

    def test_a_repair_is_printed_ONCE_however_many_items_need_it(self):
        """Six consecutive items carrying one defect is the real queue's shape, and
        six copies of a remedy that long bury the six reasons standing beside them —
        in output whose reader is a skill's prose."""
        self.seed("".join(LEGACY % i for i in (1, 2, 3)))
        out = self.pack()
        self.assertEqual(len(self.blocks(out)["excluded"]), 3)
        self.assertEqual(len(self.blocks(out)["repairs"]), 1)


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
        self.assertEqual(r.stdout,
                         "T001  AUTONOMOUS  item curto  [duplicate ID 1]\n"
                         "T0001  AUTONOMOUS  item de id largo  [duplicate ID 1]\n"
                         "\nduplicate IDs: only the FIRST item under each is reachable"
                         " — renumber the others by hand in next-steps.md.\n")

    def test_pack_reads_the_id_the_way_list_does(self):
        """Two renderings of one ID is how the package and the listing come to
        disagree about which item a line is about."""
        self.seed(item(1, "item curto"), self.wide())
        r = self.run_tk("pack")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("T001  S             item curto\n", r.stdout)
        self.assertIn("T0001  S             item de id largo\n", r.stdout)

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
        self.assertEqual(r.stdout, "T1000  AUTONOMOUS  item de quatro digitos\n")
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
                         "T005  AUTONOMOUS  primeira ocorrencia  [duplicate ID 5]\n"
                         "T007  AUTONOMOUS  item sozinho\n"
                         "T005  AUTONOMOUS  segunda ocorrencia  [duplicate ID 5]\n"
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

FOLD_LEGACY = ("- [ ] **T007** — **#9 Ingestao automatica do extrato BTG** (e-mail/OneDrive) —\n"
               "  `ready-for-agent`.\n"
               "  **Class:** AUTONOMOUS. **Effort:** L. **Source:** tracker "
               "**Project:** automacao-financeira.\n")
FOLD_CANONICAL = ("- [ ] **T007** — **#9 Ingestao automatica do extrato BTG** "
                  "(e-mail/OneDrive) — `ready-for-agent`. **Class:** AUTONOMOUS. "
                  "**Effort:** L. **Source:** tracker **Project:** automacao-financeira.\n")


class TestMigrateFold(QueueTest):
    FOLDED_LINE = ("1 item(s) with fields off the first line: folded up, where every gate "
                   "reads them — T007\n")

    def left_alone(self, *labels):
        return (f"{len(labels)} item(s) left exactly as they are: folding would have to "
                "GUESS which text is a field value — " + ", ".join(labels)
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
        self.assertEqual(self.body(), HEADER + LEGACY.replace("\n  ", " ") % 1)

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
                         "**Effort:** S. **Source:** 2026-08-13\n")

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

    def test_an_already_canonical_queue_is_untouched_and_silent(self):
        """The other direction, and the only one that can catch a fold firing on
        every item: a command that rewrites what is already right has no way to
        report that it changed nothing."""
        self.seed(item(1, "um"), item(2, "dois", project="tk"), item(3, "tres", risk="x"))
        before = self.body()
        r = self.migrate()
        self.assertEqual(self.body(), before)
        self.assertNotIn("folded up", r.stdout)
        self.assertNotIn("left exactly as they are", r.stdout)

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

    def test_a_marker_whose_value_sits_on_the_NEXT_line_is_left_and_REPORTED(self):
        """The shape the repairs text names as unfoldable. Joined blindly the
        **Class:** takes whatever follows as its value, and what follows may be a
        note — a class nobody wrote. Silence here is the worst outcome available:
        the caller reads a fold report, sees no mention of this item, and believes
        the queue is repaired."""
        seeded = ("- [ ] **T002** — marcador e valor em linhas diferentes **Class:**\n"
                  "  AUTONOMOUS. **Effort:** S. **Source:** 2026-08-13\n")
        self.seed(seeded)
        r = self.migrate()
        self.assertEqual(self.body(), HEADER + seeded)
        self.assertIn(self.left_alone("T002"), r.stdout)

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
        self.assertIn(self.left_alone("T004"), r.stdout)

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
        self.assertIn("T009  AUTONOMOUS  item que fala de",
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
        for line in ("T001  AUTONOMOUS  um", "T002  DECISION    dois",
                     "T003  RECURRING   tres"):
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
        self.assertIn("T001  AUTONOMOUS  item curto de verdade",
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
        r = self.run_tk("edit", "T0001", "--deferred", "esperando o Guilherme.")
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
#   automacao-financeira T037   a five-item bulleted list → one run-on line
#   the m365 queue T018         an eleven-line note → one run-on line
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
        """`--class` is the flag that gives the item its anchor. It is never
        located in the chain of an item that carries none — it is appended — so
        the position rule has nothing to say about it, and a rule that refused it
        would lock the repair out of the one population it exists for."""
        for seeded, iid in ((CLASSLESS_REAL, "T023"), (CLASSLESS_PROJECT, "T021")):
            with self.subTest(item=iid):
                self.seed(seeded)
                r = self.run_tk("edit", iid, "--class", "AUTONOMOUS")
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertEqual(r.stdout, f"{iid} updated\n")
                self.assertEqual(self.body(),
                                 HEADER + seeded.rstrip("\n")
                                 + " **Class:** AUTONOMOUS.\n")
                self.assertIn(f"{iid}  AUTONOMOUS", self.run_tk("list").stdout)

    def test_the_refusal_does_not_offer_a_remedy_that_is_a_dead_end(self):
        """`--class` appends the anchor at the END of the line, so the fields
        already in the chain stay before it and stay unwritable. A refusal that
        named it as the remedy would send the caller to run it and meet the same
        refusal — so it says, in the same sentence, that it is not the remedy."""
        self.seed(CLASSLESS_REAL)
        r = self.run_tk("edit", "T023", "--effort", "L")
        self.assertIn("is NOT the remedy for this", r.stderr)
        self.assertEqual(self.run_tk("edit", "T023", "--class", "AUTONOMOUS").returncode, 0)
        again = self.run_tk("edit", "T023", "--effort", "L")
        self.assertEqual(again.returncode, 1, again.stdout)      # the dead end, run

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
                         "T000  AUTONOMOUS  primeira ocorrencia  [duplicate ID 0]\n"
                         "T007  AUTONOMOUS  item sozinho\n"
                         "T000  AUTONOMOUS  segunda ocorrencia  [duplicate ID 0]\n"
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
        return (f"{len(labels)} item(s) left exactly as they are: a line between the "
                "head and the chain is not the hard-wrapped prose the fold may absorb, "
                "and absorbing a shape nobody recognised is how structure is lost in "
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
                      "**Effort:** would sit BEFORE the anchor", r.stderr)
        self.assertIn("Nothing was changed", r.stderr)

    def test_the_file_and_the_reader_no_longer_disagree_about_the_field(self):
        """The whole sequence as it was measured: `--effort L` exited 0, `--class`
        exited 0, and `pack` went on printing Effort `?` over a file that said `L`.
        The file and its reader disagreeing is the finding — not the `?`.

        They agree now, and they agree the honest way: nothing was written, so
        nothing claims a value the reader cannot see."""
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
                self.assertIn(f"an appended **{marker}:** would sit BEFORE the anchor",
                              r.stderr)

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


if __name__ == "__main__":
    unittest.main(verbosity=2)
