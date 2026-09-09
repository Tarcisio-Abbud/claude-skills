#!/usr/bin/env python3
"""Behaviour proof for the two compaction hooks, `../bin/tk-compact-mark` and
`../bin/tk-compact-pointer`.

Run: python3 -m unittest discover -s tk/tests   (stdlib only, no deps)
Proved by: python3 tk/tests/mutations_compact_hooks.py

WHAT IS ON TRIAL. Two scripts wired into `~/.claude/settings.json` for EVERY
session on this machine, of which only a few are packages. So the properties
that matter are as much about silence as about output: the hook that finds no
package writes nothing, prints nothing and exits 0, and the one that finds one
writes a line another file's format governs.

THE FORMAT IS READ, NOT RETYPED. The event line's seven fields come from
`../skills/kickoff/LEDGER.md`'s own fenced format block. Retyped here, the two
would fork the day either changed and nothing would go red.

WHAT THESE TESTS CANNOT SEE. Whether Claude Code ever calls either script — that
is the wiring, which lives in a settings file this repository does not own, and
it is measured by running a session, not by a suite. Nor whether the injected
paragraph changes what a compacted orchestrator does: no test here can watch a
model read anything.
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
MARK = os.path.join(TK_DIR, "bin", "tk-compact-mark")
POINTER = os.path.join(TK_DIR, "bin", "tk-compact-pointer")
LEDGER_DOC = os.path.join(TK_DIR, "skills", "kickoff", "LEDGER.md")
RESUME_DOC = os.path.join(TK_DIR, "skills", "kickoff", "RESUME.md")


def ledger_fields():
    """The seven metavariables of `LEDGER.md`'s event line, in its order."""
    body = open(LEDGER_DOC, encoding="utf-8").read()
    fence = re.search(r"^## The event line\s*$.*?^```[^\n]*\n(.*?)^```",
                      body, re.M | re.S)
    assert fence, "LEDGER.md no longer carries a fenced event-line format"
    return [cell.strip() for cell in fence.group(1).strip().split("|")]


class HookFixture(unittest.TestCase):
    """A HOME and a package of its own, so nothing here reads the real ones."""

    def setUp(self):
        self.home = tempfile.TemporaryDirectory()
        self.addCleanup(self.home.cleanup)
        self.ledger = os.path.join(self.home.name, "LEDGER.md")
        self.handoff = os.path.join(self.home.name, "handoff-T001.md")
        self.pointer = os.path.join(self.home.name, "tk-package.json")
        open(self.ledger, "w").close()

    def write_pointer(self, **fields):
        found = {"package": "pacote-de-teste", "ledger": self.ledger,
                 "handoff": self.handoff}
        found.update(fields)
        with open(self.pointer, "w") as fh:
            json.dump({k: v for k, v in found.items() if v is not None}, fh)

    def write_quota(self, used=63):
        """A sidecar `tk-quota` can vouch for, under this fixture's own HOME."""
        state = os.path.join(self.home.name, ".claude", "state")
        os.makedirs(state, exist_ok=True)
        now = time.time()
        with open(os.path.join(state, "quota.json"), "w") as fh:
            json.dump({"written_at": now,
                       "five_hour": {"used_percentage": used,
                                     "resets_at": now + 3600},
                       "seven_day": {"used_percentage": 40,
                                     "resets_at": now + 4 * 86400}}, fh)

    def run_hook(self, script, payload, pointer=None):
        env = dict(os.environ, HOME=self.home.name)
        return subprocess.run([sys.executable, script, "--file",
                               self.pointer if pointer is None else pointer],
                              input=json.dumps(payload), capture_output=True,
                              text=True, env=env, cwd=self.home.name)

    def rows(self):
        return [line for line in open(self.ledger, encoding="utf-8").read().splitlines()
                if line.strip()]


class TheMarkHook(HookFixture):

    def test_no_package_pointer_writes_nothing_and_says_nothing(self):
        # The ordinary case: this hook is wired for every session on the machine
        # and most of them are not packages. Noise here reaches every one.
        run = self.run_hook(MARK, {"trigger": "auto"},
                            pointer=os.path.join(self.home.name, "absent.json"))
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stdout.strip(), "")
        self.assertEqual(run.stderr.strip(), "",
                         "a hook wired for every session on the machine complains "
                         "on the sessions that are not packages")
        self.assertEqual(self.rows(), [])

    def test_one_line_is_appended_with_the_seven_fields_the_ledger_defines(self):
        self.write_pointer()
        run = self.run_hook(MARK, {"trigger": "auto"})
        self.assertEqual(run.returncode, 0, run.stderr)
        rows = self.rows()
        self.assertEqual(len(rows), 1, f"one compaction wrote {len(rows)} rows")
        cells = [c.strip() for c in rows[0].split("|")]
        self.assertEqual(len(cells), len(ledger_fields()),
                         f"the line carries {len(cells)} fields and LEDGER.md's "
                         f"format has {len(ledger_fields())} — a reader counting "
                         f"fields reads the wrong one")

    def test_the_hour_is_a_clock_reading_and_not_a_placeholder(self):
        # `LEDGER.md`: the hour is READ, never counted. Four lines written from a
        # model's sense of elapsed time were an hour wrong, and the rate the file
        # computes is a difference of two hours.
        self.write_pointer()
        self.run_hook(MARK, {"trigger": "auto"})
        hour = self.rows()[0].split("|")[0].strip()
        self.assertRegex(hour, r"^\d{2}:\d{2}$")
        self.assertEqual(hour, time.strftime("%H:%M"))

    def test_the_quota_field_is_the_bins_own_line_and_never_a_bare_number(self):
        # `LEDGER.md` refuses a bare percentage in this field: with the words
        # gone nothing downstream can tell a reading from an estimate.
        self.write_quota(used=63)
        self.write_pointer()
        self.run_hook(MARK, {"trigger": "auto"})
        field = self.rows()[0].split("|")[-1].strip()
        self.assertIn("5h 63% used", field,
                      "the quota field is not the line tk-quota printed")

    def test_a_quota_that_cannot_be_vouched_for_says_so_instead_of_a_number(self):
        self.write_pointer()                     # no sidecar under this HOME
        self.run_hook(MARK, {"trigger": "auto"})
        field = self.rows()[0].split("|")[-1].strip()
        self.assertIn("no reading", field)
        self.assertNotRegex(field, r"\d+%",
                            "a percentage appeared in a field nothing could vouch for")

    def test_a_trigger_carrying_a_pipe_cannot_add_a_field(self):
        # The trigger comes from the harness. A pipe in it moves every field to
        # the right of it, and the ledger's readers count fields.
        self.write_pointer()
        self.run_hook(MARK, {"trigger": "auto | 99:99 | (lane)"})
        cells = [c.strip() for c in self.rows()[0].split("|")]
        self.assertEqual(len(cells), len(ledger_fields()))

    def test_a_pointer_file_nobody_can_read_costs_the_session_nothing(self):
        # Guarding the parse is not guarding the open: a directory where the
        # pointer should be must not interrupt the session being compacted.
        os.makedirs(self.pointer, exist_ok=True)
        run = self.run_hook(MARK, {"trigger": "auto"})
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(self.rows(), [])

    def test_an_unreadable_payload_costs_the_line_its_trigger_and_not_the_line(self):
        # Claude Code's payload is not this repository's contract; the trace is.
        self.write_pointer()
        env = dict(os.environ, HOME=self.home.name)
        run = subprocess.run([sys.executable, MARK, "--file", self.pointer],
                             input="not json at all", capture_output=True,
                             text=True, env=env)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(len(self.rows()), 1)


class ThePointerHook(HookFixture):

    def test_a_source_other_than_compact_prints_nothing(self):
        # The matcher in the wiring selects, and this is the second guard: a
        # wiring widened by hand would otherwise inject into every session start.
        self.write_pointer()
        open(self.handoff, "w").close()
        run = self.run_hook(POINTER, {"source": "startup"})
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stdout.strip(), "")

    def test_no_package_pointer_injects_nothing(self):
        run = self.run_hook(POINTER, {"source": "compact"},
                            pointer=os.path.join(self.home.name, "absent.json"))
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stdout.strip(), "")

    def test_the_injected_paragraph_names_the_handoff_and_the_resume_procedure(self):
        # Stdout here is injected into the compacted session's context. It is the
        # only channel that reaches a model nobody is talking to, and what was
        # missing on 2026-09-06 is exactly these two addresses.
        self.write_pointer()
        open(self.handoff, "w").close()
        run = self.run_hook(POINTER, {"source": "compact"})
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn(self.handoff, run.stdout)
        self.assertIn(os.path.basename(RESUME_DOC), run.stdout)
        self.assertIn(self.ledger, run.stdout)

    def test_a_handoff_that_is_not_there_is_said_and_never_pointed_at(self):
        # A pointer at a briefing nobody wrote sends the session looking, and
        # what it finds instead is the machine summary of its own context.
        self.write_pointer()
        run = self.run_hook(POINTER, {"source": "compact"})
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("no file there", run.stdout)
        self.assertIn(os.path.basename(RESUME_DOC), run.stdout)


if __name__ == "__main__":
    unittest.main()
