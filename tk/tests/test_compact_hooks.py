#!/usr/bin/env python3
"""Behaviour proof for the two compaction hooks, `../bin/tk-compact-mark` and
`../bin/tk-compact-pointer`, and for tk's mod, `../hooks/compact-veto.js`.

Run: python3 -m unittest discover -s tk/tests   (stdlib only, no deps; the mod's
     class also needs a `claude` binary with mods, 2.1.287+, and skips without)
Proved by: python3 tk/tests/mutations_compact_hooks.py

WHAT IS ON TRIAL. Two scripts wired into `~/.claude/settings.json` for EVERY
session on this machine, of which only a few are packages. So the properties
that matter are as much about silence as about output: the hook that finds no
package writes nothing, prints nothing and exits 0, and the one that finds one
writes a line another file's format governs.

THE FORMAT IS READ, NOT RETYPED. The event line's seven fields come from
`../skills/kickoff/LEDGER.md`'s own fenced format block. Retyped here, the two
would fork the day either changed and nothing would go red.

THE INJECTION IS AN ENVELOPE. What reaches a session's context is the
`hookSpecificOutput.additionalContext` of a JSON object on stdout; a hook that
exits 0 printing a plain paragraph is logged "produced no response payload" and
attached to nothing. That defect was live here and a test reading raw stdout
passed over it, so the pointer's tests parse the envelope before they read a
word of the paragraph.

THE MOD IS TESTED BY ITS OWN KIT. It is JavaScript run inside Claude Code, so
its tests are `compact_veto.test.ts`, run by `claude plugin test` on the tree
this file sits in (a mutant's copy, under the mutation runner); `TheModVeto`
turns each kit test into a unittest one by name.

WHAT THESE TESTS CANNOT SEE. Whether Claude Code ever calls either script — that
is the wiring, which lives in a settings file this repository does not own, and
it is measured by running a session, not by a suite. Nor whether the injected
paragraph changes what a compacted orchestrator does: no test here can watch a
model read anything.
"""

import json
import os
import re
import shutil
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


WINDOW_ENV = "CLAUDE_CODE_AUTO_COMPACT_WINDOW"

SESSION = "00000000-1111-2222-3333-444444444444"
PROJECT = "/home/someone/.claude/projects/-a-project"
AGENT = "a0000000000000000"


def main_thread_payload(**fields):
    """A payload as the harness builds it for a session's own thread.

    The shape is the hook input schema the CLI carries, not an invention here:
    `session_id`, `transcript_path`, `cwd` and `hook_event_name` on every hook,
    plus whatever the event adds. `agent_id` is absent on the main thread, and
    that absence is the whole discriminator the two hooks read below.
    """
    found = {"session_id": SESSION,
             "transcript_path": f"{PROJECT}/{SESSION}.jsonl",
             "cwd": "/home/someone/work",
             "hook_event_name": "PreCompact",
             "trigger": "auto",
             "custom_instructions": None}
    found.update(fields)
    return found


# What a payload firing INSIDE a subagent carries and a main thread's does not.
# Measured, not guessed, on the package of 2026-09-19: the four subagents that
# compacted wrote their `compact_boundary` to a transcript of their own under
# `<session>/subagents/`, while every record in those files carried the
# orchestrator's `sessionId` and `cwd`. So the transcript address moves and the
# session does not — and the harness adds `agent_id` and `agent_type`, which it
# documents as present only when the hook fires from a subagent. Both events'
# subagent payloads are built from this one dict, so neither can drift.
SUBAGENT_MARKS = {
    "transcript_path": f"{PROJECT}/{SESSION}/subagents/agent-{AGENT}.jsonl",
    "agent_id": AGENT,
    "agent_type": "general-purpose",
}


def subagent_payload(**fields):
    """The `PreCompact` payload as it reaches a hook firing INSIDE a subagent."""
    return main_thread_payload(**dict(SUBAGENT_MARKS, **fields))


def session_start(**fields):
    """The `SessionStart` half of the same two payloads, main thread by default."""
    found = main_thread_payload(hook_event_name="SessionStart", source="compact")
    found.pop("trigger")
    found.pop("custom_instructions")
    found.update(fields)
    return found


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

    def env(self, window=None):
        """This test's environment. The window is never the caller's: the
        variable is dropped unless `window` names one."""
        env = dict(os.environ, HOME=self.home.name)
        env.pop(WINDOW_ENV, None)
        if window is not None:
            env[WINDOW_ENV] = str(window)
        return env

    def run_hook(self, script, payload, pointer=None, window=None):
        return subprocess.run([sys.executable, script, "--file",
                               self.pointer if pointer is None else pointer],
                              input=json.dumps(payload), capture_output=True,
                              text=True, env=self.env(window), cwd=self.home.name)

    def transcript(self):
        return os.path.join(self.home.name, f"{SESSION}.jsonl")

    def append_turn(self, kind, stamp, size=0, cwd=None):
        """One main-thread record, `user` or `assistant`, stamped `stamp`. Its
        `cwd` is this fixture's HOME unless named, so the session's project
        settings are read from there and nowhere else. `size` pads the record,
        for the reader that starts at the file's end."""
        record = {"type": kind, "timestamp": stamp, "cwd": cwd or self.home.name,
                  "sessionId": SESSION, "message": {"content": "x" * size}}
        with open(self.transcript(), "a") as fh:
            fh.write(json.dumps(record) + "\n")

    def judged_payload(self, **fields):
        """A PreCompact payload with no `agent_id` and this fixture's main
        transcript: the shape measured on 2.1.286 and 2.1.287 for subagent and
        orchestrator alike."""
        return main_thread_payload(transcript_path=self.transcript(),
                                   cwd=self.home.name, **fields)

    def rows(self):
        with open(self.ledger, encoding="utf-8") as fh:
            return [line for line in fh.read().splitlines() if line.strip()]


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

    def test_a_ledger_address_that_is_a_fifo_does_not_hang_the_session(self):
        # The other half of the same guard, and the worse half: a directory
        # raises OSError and the `except` catches it, a FIFO raises nothing at
        # all — `open(..., "a")` BLOCKS until somebody reads the other end, and a
        # PreCompact hook that blocks stops the session with nothing on screen.
        # The timeout is the assertion: without the regular-file check this call
        # never returns.
        fifo = os.path.join(self.home.name, "ledger.fifo")
        os.mkfifo(fifo)
        self.write_pointer(ledger=fifo)
        env = dict(os.environ, HOME=self.home.name)
        run = subprocess.run([sys.executable, MARK, "--file", self.pointer],
                             input=json.dumps({"trigger": "auto"}),
                             capture_output=True, text=True, env=env,
                             cwd=self.home.name, timeout=20)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("not a regular file", run.stderr,
                      "the hook is silent about an address it refused, so nobody "
                      "learns why the package's ledger has no compact line")

    def test_a_ledger_nobody_has_created_yet_is_still_written(self):
        # The guard admits absence: the first compact of a package whose ledger
        # is named but not yet on disk must still leave its line.
        absent = os.path.join(self.home.name, "not-yet.md")
        self.write_pointer(ledger=absent)
        run = self.run_hook(MARK, {"trigger": "auto"})
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertTrue(os.path.isfile(absent),
                        "a ledger that did not exist yet was refused as though it "
                        "were a directory, and the compact left no trace")

    def test_a_subagents_compaction_is_not_a_seam_of_the_orchestrator(self):
        # The package of 19/09 collected four of these lines while the
        # orchestrator's own transcript held no `compact_boundary` at all: the
        # hook fires inside every subagent too, and a subagent carries its
        # parent's `session_id` and `cwd`, so only `agent_id` tells them apart.
        self.write_pointer()
        run = self.run_hook(MARK, subagent_payload())
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(self.rows(), [],
                         "a subagent's compaction was written as the "
                         "orchestrator's, and the ledger says the package's "
                         "context was emptied when it was not")

    def test_the_main_thread_of_an_agent_session_still_leaves_its_line(self):
        # `agent_type` arrives on the main thread of a session started with
        # `--agent`, with no `agent_id` beside it. Keying the guard on the type
        # would silence the very session the ledger is about.
        self.write_pointer()
        payload = dict(main_thread_payload(), agent_type="general-purpose")
        run = self.run_hook(MARK, payload)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(len(self.rows()), 1,
                         "an orchestrator's own compaction left no line because "
                         "its payload named an agent TYPE")

    def test_a_blank_agent_id_is_not_a_subagent_and_leaves_its_line(self):
        # `agent_id` is an optional string in the hook input schema: blank, or
        # not a string at all, is the absence of a subagent's identity and not
        # the presence of one. Read the other way, the session's own compaction
        # is the one that goes untraced.
        self.write_pointer()
        run = self.run_hook(MARK, dict(main_thread_payload(), agent_id=""))
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(len(self.rows()), 1,
                         "a blank agent_id was read as a subagent's identity, and "
                         "the session's own compaction left no line")

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

    def injected(self, run):
        """What the harness would attach, read out of the hook's own envelope."""
        envelope = json.loads(run.stdout)
        specific = envelope["hookSpecificOutput"]
        self.assertEqual(specific["hookEventName"], "SessionStart",
                         "the envelope names an event the harness will not match")
        return specific["additionalContext"]

    def test_a_source_other_than_compact_prints_nothing(self):
        # The matcher in the wiring selects, and this is the second guard: a
        # wiring widened by hand would otherwise inject into every session start.
        self.write_pointer()
        open(self.handoff, "w").close()
        run = self.run_hook(POINTER, {"source": "startup"})
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stdout.strip(), "")

    def test_a_payload_with_no_source_at_all_prints_nothing(self):
        # The `{}` the bin substitutes for an unreadable payload lands here too.
        # The banner promises that anything but `compact` prints nothing, and an
        # unidentified session is not a compacted one.
        self.write_pointer()
        open(self.handoff, "w").close()
        run = self.run_hook(POINTER, {})
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stdout.strip(), "",
                         "a payload naming no source was injected into, so a "
                         "wiring or a harness that stops sending the key turns "
                         "every session start into a package's instruction")

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
        said = self.injected(run)
        self.assertIn(self.handoff, said)
        self.assertIn(os.path.basename(RESUME_DOC), said)
        self.assertIn(self.ledger, said)

    def test_a_handoff_that_is_not_there_is_said_and_never_pointed_at(self):
        # A pointer at a briefing nobody wrote sends the session looking, and
        # what it finds instead is the machine summary of its own context.
        self.write_pointer()
        run = self.run_hook(POINTER, {"source": "compact"})
        self.assertEqual(run.returncode, 0, run.stderr)
        said = self.injected(run)
        self.assertIn("no file there", said)
        self.assertIn(os.path.basename(RESUME_DOC), said)

    def test_a_subagent_that_compacted_is_not_told_it_was_orchestrating(self):
        # Measured on the package of 2026-09-19, in an implementer's own
        # transcript: this hook fired INSIDE it after it compacted, and the
        # paragraph told it that it had been orchestrating the package and must
        # read the orchestrator's handoff "before anything else". That is an
        # instruction to abandon the item it was holding.
        self.write_pointer()
        open(self.handoff, "w").close()
        run = self.run_hook(POINTER, session_start(**SUBAGENT_MARKS))
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stdout.strip(), "",
                         "a subagent was sent to read the orchestrator's handoff "
                         "before anything else, mid-item")

    def test_a_blank_agent_id_is_not_a_subagent_and_the_handoff_is_still_named(self):
        # `agent_id` is an optional string in the hook input schema: blank, or
        # not a string at all, is the absence of a subagent's identity and not
        # the presence of one. Read the other way, the one wake this hook exists
        # for is the wake it goes silent on.
        self.write_pointer()
        open(self.handoff, "w").close()
        run = self.run_hook(POINTER, session_start(agent_id=""))
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn(self.handoff, self.injected(run),
                      "a blank agent_id was read as a subagent's identity, and a "
                      "compacted orchestrator was told nothing")

    def test_the_main_thread_of_an_agent_session_is_still_pointed_at_the_handoff(self):
        # `agent_type` without `agent_id` is the main thread of a session started
        # with `--agent` — the orchestrator itself, on the one wake this hook
        # exists for.
        self.write_pointer()
        open(self.handoff, "w").close()
        run = self.run_hook(POINTER, session_start(agent_type="general-purpose"))
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn(self.handoff, self.injected(run),
                      "the compacted orchestrator was told nothing because its "
                      "payload named an agent TYPE")

    def test_the_paragraph_travels_in_the_envelope_and_never_as_plain_stdout(self):
        # Measured 2026-09-09 on 2.1.266: the plain-paragraph version of this
        # hook ran for a live session that then could not find one word of it.
        # A paragraph outside the envelope is a hook that costs a session and
        # delivers nothing, and it looks identical from the terminal.
        self.write_pointer()
        open(self.handoff, "w").close()
        run = self.run_hook(POINTER, {"source": "compact"})
        try:
            envelope = json.loads(run.stdout)
        except ValueError:
            self.fail(f"stdout is not the hook envelope the harness reads: "
                      f"{run.stdout!r}")
        self.assertEqual(list(envelope), ["hookSpecificOutput"],
                         "a key outside hookSpecificOutput does not reach a context")
        self.assertEqual(sorted(envelope["hookSpecificOutput"]),
                         ["additionalContext", "hookEventName"])

    def test_a_session_the_pointer_does_not_name_hears_nothing(self):
        # The pointer is one file per machine: another session's compaction is
        # not the package's, and its subagents least of all.
        self.write_pointer(session="ffffffff-1111-2222-3333-444444444444")
        open(self.handoff, "w").close()
        run = self.run_hook(POINTER, session_start())
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stdout.strip(), "",
                         "a session the pointer does not name was sent to the handoff")

    def test_the_session_the_pointer_names_is_pointed_at_the_handoff(self):
        self.write_pointer(session=SESSION)
        open(self.handoff, "w").close()
        said = self.injected(self.run_hook(POINTER, session_start()))
        self.assertIn(self.handoff, said)

    def test_the_paragraph_opens_with_the_exclusion_a_dispatched_agent_obeys(self):
        # On 2.1.286 a subagent's wake carries no `agent_id`, so a subagent the
        # veto let through reads this paragraph too. Its FIRST instruction must
        # be the one that keeps the item; the orchestrator's comes after.
        self.write_pointer()
        open(self.handoff, "w").close()
        said = self.injected(self.run_hook(POINTER, session_start()))
        sentences = said.split(". ")
        self.assertTrue(sentences[0].startswith("tk: a compaction happened while package "),
                        f"the paragraph opens with something else: {sentences[0]!r}")
        self.assertIn("continue your item and do not read the handoff", sentences[1],
                      "the first instruction is not the one that tells a dispatched "
                      "agent to keep its item")
        self.assertLess(said.index("continue your item"), said.index(self.handoff),
                        "the handoff is named before the exclusion")


T0 = "2026-10-01T12:00:00.000Z"          # the main thread's last response
OTHER = "ffffffff-1111-2222-3333-444444444444"


class TheOrchestratorsLedger(HookFixture):
    """Whose line it is: the pointer names the orchestrator's session, and the
    line names the session and whether the mod could veto a subagent's."""

    def setUp(self):
        super().setUp()
        self.append_turn("assistant", T0)

    def sixth(self):
        rows = self.rows()
        self.assertEqual(len(rows), 1, f"one compaction wrote {len(rows)} rows")
        return rows[0].split("|")[5]

    def test_another_sessions_compaction_writes_nothing_in_this_ledger(self):
        # The pointer is one file per machine: a session that is not the
        # package's must not write the package's seams.
        self.write_pointer(session=OTHER)
        run = self.run_hook(MARK, self.judged_payload(), window=100000)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(self.rows(), [],
                         "another session's compaction was written as the package's")

    def test_the_orchestrators_own_compaction_is_written(self):
        self.write_pointer(session=SESSION)
        self.run_hook(MARK, self.judged_payload(), window=100000)
        self.assertEqual(len(self.rows()), 1,
                         "the session the pointer names left no line")

    def test_the_line_names_the_session_and_a_numeric_window(self):
        self.write_pointer(session=SESSION)
        self.run_hook(MARK, self.judged_payload(), window=100000)
        result = self.sixth()
        self.assertIn(f"session {SESSION[:8]}", result)
        self.assertIn("window 100000, so the tk mod vetoes a subagent's", result)

    def test_a_window_that_is_not_a_number_says_a_subagent_lands_here(self):
        # Under `auto` the mod vetoes nothing, so this line may be a subagent's.
        self.write_pointer(session=SESSION)
        self.run_hook(MARK, self.judged_payload(), window=None)
        self.assertIn("window not numeric", self.sixth())

    def test_the_settings_key_is_read_from_the_sessions_own_directory(self):
        # The resolver `tk-context --window` uses: the key in the project
        # settings of the directory the transcript opened in, which is neither
        # the payload's `cwd` nor the hook's own directory here.
        self.write_pointer(session=SESSION)
        project = os.path.join(self.home.name, "project")
        os.makedirs(os.path.join(project, ".claude"))
        with open(os.path.join(project, ".claude", "settings.json"), "w") as fh:
            json.dump({"autoCompactWindow": 100000}, fh)
        os.remove(self.transcript())
        self.append_turn("assistant", T0, cwd=project)
        self.run_hook(MARK, self.judged_payload(), window=None)
        self.assertIn("window 100000", self.sixth(),
                      "the project's numeric key was not read")
        self.assertNotIn("hook's directory", self.sixth(),
                         "the session's own directory was reported as a fallback")

    def test_a_window_read_without_the_sessions_directory_says_so(self):
        self.write_pointer(session=SESSION)
        payload = self.judged_payload()
        payload["transcript_path"] = None
        self.run_hook(MARK, payload, window=100000)
        self.assertIn("read from the hook's directory", self.sixth(),
                      "the fallback to the hook's directory went unsaid")

    def test_the_veto_claim_names_the_model_window_condition(self):
        self.write_pointer(session=SESSION)
        self.run_hook(MARK, self.judged_payload(), window=100000)
        self.assertIn("when the model window is larger", self.sixth(),
                      "the line claims a veto the mod's second condition may refuse")


KIT_TIMEOUT = 120
MOD_FLOOR = (2, 1, 287)                 # the first Claude Code that loads mods


def binary_version(claude):
    """The binary's version as a tuple, or None when it prints none."""
    run = subprocess.run([claude, "--version"], capture_output=True, text=True,
                         timeout=KIT_TIMEOUT)
    m = re.match(r"(\d+)\.(\d+)\.(\d+)", run.stdout.strip())
    return tuple(int(part) for part in m.groups()) if m else None


def kit_results(tk_dir):
    """{test name: passed} from one `claude plugin test` run over `tk_dir`, or
    None and the reason there is none."""
    claude = shutil.which("claude")
    if claude is None:
        return None, "no claude binary on PATH"
    version = binary_version(claude)
    if version is None or version < MOD_FLOOR:
        return None, f"claude {version} predates mods"
    run = subprocess.run([claude, "plugin", "test", tk_dir], capture_output=True,
                         text=True, timeout=KIT_TIMEOUT)
    out = run.stdout + run.stderr
    found = {m.group(2): m.group(1) == "pass"
             for m in re.finditer(r"^\((pass|fail)\) (.+?) \[[\d.]+m?s\]$", out, re.M)}
    if not found:                       # a binary with mods that ran none: the mod broke
        return {}, f"claude plugin test ran nothing: {out[-3000:]!r}"
    return found, out


class TheModVeto(unittest.TestCase):
    """`compact_veto.test.ts`, run once by the first-party kit, read test by test.

    No `claude` binary, or one older than the mod floor, skips the class: the
    kit is that binary's, and nothing else here can run the mod. A binary with
    mods whose kit runs nothing fails every test, since a mod that does not
    load is the likeliest cause."""

    @classmethod
    def setUpClass(cls):
        cls.results, cls.output = kit_results(TK_DIR)

    def kit(self, name):
        if self.results is None:
            self.skipTest(self.output)
        self.assertIn(name, self.results,
                      f"the kit ran no test named {name!r}\n{self.output[-3000:]}")
        self.assertTrue(self.results[name],
                        f"kit test failed: {name}\n{self.output[-3000:]}")

    def test_a_subagent_auto_compaction_in_the_package_session_is_vetoed(self):
        self.kit("a subagent auto-compaction in the package session is vetoed")

    def test_the_main_conversation_is_never_vetoed(self):
        self.kit("the main conversation is never vetoed")

    def test_a_manual_compaction_of_a_subagent_is_not_vetoed(self):
        self.kit("a manual compaction of a subagent is not vetoed")

    def test_with_no_package_pointer_nothing_is_vetoed(self):
        self.kit("with no package pointer nothing is vetoed")

    def test_a_pointer_nobody_can_parse_vetoes_nothing(self):
        self.kit("a pointer nobody can parse vetoes nothing")

    def test_another_sessions_subagents_compact_while_a_package_runs(self):
        self.kit("another session subagents compact while a package runs")

    def test_a_pointer_that_names_no_session_vetoes_nothing(self):
        self.kit("a pointer that names no session vetoes nothing")

    def test_a_window_at_the_model_limit_vetoes_nothing(self):
        self.kit("a window at the model limit vetoes nothing")

    def test_the_pointer_address_can_be_named_for_a_probe(self):
        self.kit("the pointer address can be named for a probe")

    def test_a_fleet_project_run_listed_as_exempt_compacts(self):
        self.kit("a fleet project run listed as exempt compacts")

    def test_a_project_run_implementer_is_vetoed_beside_the_exempt_list(self):
        self.kit("a project run implementer is vetoed beside the exempt list")

    def test_an_exempt_field_that_is_not_a_list_of_ids_vetoes_nothing(self):
        self.kit("an exempt field that is not a list of ids vetoes nothing")

    def test_decide_refuses_every_input_that_is_not_a_veto(self):
        self.kit("decide refuses every input that is not a veto")


if __name__ == "__main__":
    unittest.main()
