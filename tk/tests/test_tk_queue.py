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
        block ceiling back on field edits: DECISION is shorter than AUTONOMOUS,
        so that edit SHRINKS the item and never reaches the ceiling either way.
        It is kept as coverage of the flag, not as proof — see mutations.py's
        KNOWN BLIND SPOT."""
        for flag, val, expected in (("--project", "ambiente", "**Project:** ambiente."),
                                    ("--class", "DECISION", "**Class:** DECISION."),
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
