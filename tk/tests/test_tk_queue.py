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

import importlib.machinery
import importlib.util
import os
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


def item(iid, text, project=None, klass="AUTONOMOUS", risk=None):
    tag = f" **Project:** {project}." if project else ""
    risk_field = f" **Risk:** {risk}." if risk else ""
    return (f"- [ ] **T{iid:03d}** — {text} **Class:** {klass}. **Effort:** S."
            f"{risk_field} **Criterion:** A: x.{tag} **Source:** 2026-08-13\n")


class QueueTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="tk-queue-test.")
        self.mem = os.path.join(self.dir, "memory")
        os.makedirs(self.mem)
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)

    # --- helpers ---------------------------------------------------------
    def seed(self, *items, log=None):
        self.write("next-steps.md", HEADER + "".join(items))
        if log is not None:
            self.write("done-log.md", log)

    def write(self, name, text):
        with open(os.path.join(self.mem, name), "w", encoding="utf-8") as f:
            f.write(text)

    def body(self, name="next-steps.md"):
        path = os.path.join(self.mem, name)
        if not os.path.exists(path):
            return ""
        with open(path, encoding="utf-8") as f:
            return f.read()

    def run_tk(self, *argv, cwd=None):
        return subprocess.run([sys.executable, TK, *argv, "--dir", self.mem],
                              capture_output=True, text=True, cwd=cwd or self.dir)


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
        """`list` and `report` take no lock and write nothing — announcing a write
        target there would be noise on every read."""
        self.seed(item(1, "um"))
        for argv in (("list",), ("report", "--since", "2026-01-01")):
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
        self.assertIn("**Class:** AUTONOMOUS.", self.body())          # class unchanged
        self.assertIn("nota de contexto", self.body())                # prose intact
        # and the same marker cannot be deleted by clearing it either
        r = self.run_tk("edit", "T001", "--class", "BLOCKED", "--deferred", "none")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("nota de contexto", self.body())

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


if __name__ == "__main__":
    unittest.main(verbosity=2)
