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


def item(iid, text, project=None, klass="AUTONOMOUS"):
    tag = f" **Project:** {project}." if project else ""
    return (f"- [ ] **T{iid:03d}** — {text} **Class:** {klass}. **Effort:** S. "
            f"**Criterion:** A: x.{tag} **Source:** 2026-08-13\n")


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

    def test_close_refuses_a_marker_in_summary_and_note(self):
        for flag in ("--summary", "--note"):
            with self.subTest(flag=flag):
                self.seed(item(1, "um", project="tk"))
                r = self.run_tk("done", "T001", "--how", "x", flag, "y **Project:** z")
                self.assertEqual(r.returncode, 1)
                self.assertIn("field-marker shape", r.stderr)
                self.assertEqual(self.body("done-log.md"), "")

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


if __name__ == "__main__":
    unittest.main(verbosity=2)
