#!/usr/bin/env python3
"""Behaviour proof for `../bin/tk-errors`, and the seam it shares with `tk-queue`.

Run: python3 -m unittest discover -s tk/tests   (stdlib only, no deps)

WHAT IS ON TRIAL. A report a session reads at its close to learn what it was
refused. Two ways it can lie, and each has its own class of test here: it can
MISS a signal — the refusal it never saw, the queue write whose success line it
could not recognise — and it can INVENT one, which is worse, because a report
that cries wolf on every `--help` gets skipped the third time and then misses the
real row too. The second is why so many cases below assert a count of zero.

THE PINNED SHAPES ARE THE BRITTLE PART. `tk-errors` recognises a queue write by
the success line `tk-queue` prints, and a rewording there would make this reader
go quiet with the suite still green. `TheQueueSeam` is what holds it shut: it
greps `tk/bin/tk-queue` for the literal each pattern was read off. That test
failing is not a bug in `tk-errors` — it is the news that the two files drifted.

WHAT THESE TESTS CANNOT SEE. Whether a real session's refusals land in the shape
the fixtures use: that was measured once, by running the command over a real
transcript (2026-09-16, session 8430d605, 14 refusals and 4 unconfirmed writes),
and the `--help` exclusion below exists because that run reported 9 before it.
Nor whether the close ACTUALLY runs the command — no test can watch a session.
That half is the pointer the last test reads, and the review.
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
TK_ERRORS = os.path.join(TK_DIR, "bin", "tk-errors")
TK_QUEUE = os.path.join(TK_DIR, "bin", "tk-queue")
WRAP_UP = os.path.join(TK_DIR, "skills", "wrap-up", "SKILL.md")

SESSION = "99999999-8888-7777-6666-555555555555"
STAMP = "2026-09-16T10:00:00.000Z"


def call_line(uid, command=None, name="Bash", stamp=STAMP, sidechain=False):
    """One assistant entry carrying a tool_use, as the transcript writes it."""
    payload = {} if command is None else {"command": command}
    record = {"type": "assistant", "timestamp": stamp,
              "message": {"role": "assistant",
                          "content": [{"type": "tool_use", "id": uid,
                                       "name": name, "input": payload}]}}
    if sidechain:
        record["isSidechain"] = True
    return json.dumps(record)


def result_line(uid, text="", is_error=False, stamp=STAMP, structured=False,
                sidechain=False):
    """The tool_result entry that answers it, in either of its two content shapes."""
    content = [{"type": "text", "text": text}] if structured else text
    block = {"type": "tool_result", "tool_use_id": uid, "content": content}
    if is_error:
        block["is_error"] = True
    record = {"type": "user", "timestamp": stamp,
              "message": {"role": "user", "content": [block]}}
    if sidechain:
        record["isSidechain"] = True
    return json.dumps(record)


def load_tk_errors():
    """The bin as a module, so a constant is read here and never retyped."""
    spec = importlib.util.spec_from_loader(
        "tk_errors", importlib.machinery.SourceFileLoader("tk_errors", TK_ERRORS))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TranscriptFixture(unittest.TestCase):
    """A HOME of its own, holding one session's transcript where the script looks."""

    def setUp(self):
        self.home = tempfile.TemporaryDirectory()
        self.project = os.path.join(self.home.name, ".claude", "projects",
                                    "-workspace-projects")
        os.makedirs(self.project)
        self.transcript = os.path.join(self.project, f"{SESSION}.jsonl")
        self.addCleanup(self.home.cleanup)

    def write(self, *lines):
        with open(self.transcript, "w") as fh:
            fh.write("\n".join(lines) + "\n")

    def write_subagent(self, name, *lines):
        """One dispatched agent's transcript, where the harness puts it.

        Beside the session's own file, in a directory named for the session:
        `<project>/<session id>/subagents/agent-<hash>.jsonl`, and one level
        deeper when a Workflow ran the agent.
        """
        directory = os.path.join(self.project, SESSION, "subagents",
                                 *os.path.split(name)[:-1])
        os.makedirs(directory, exist_ok=True)
        with open(os.path.join(self.project, SESSION, "subagents", name),
                  "w") as fh:
            fh.write("\n".join(lines) + "\n")

    def run_it(self, *args, session=SESSION):
        env = dict(os.environ, HOME=self.home.name)
        env.pop("CLAUDE_CODE_SESSION_ID", None)
        if session:
            env["CLAUDE_CODE_SESSION_ID"] = session
        return subprocess.run([sys.executable, TK_ERRORS, *args],
                              capture_output=True, text=True, env=env,
                              cwd=self.home.name)

    def counts(self, run):
        """The headline's two numbers, read from the FIRST line.

        The first line is the contract a seam greps, so it is parsed rather than
        searched for anywhere in the output: a headline that drifted below the
        rows would still satisfy a loose `assertIn` and break every caller.
        """
        return self.headline(run)[:2]

    def headline(self, run):
        """All THREE of the headline's numbers, refusals first."""
        line = run.stdout.splitlines()[0]
        found = re.match(r"^(\d+) refused tool call\(s\), "
                         r"(\d+) unconfirmed tk-queue write\(s\), "
                         r"(\d+) command\(s\) not parsed$", line)
        self.assertIsNotNone(found, run.stdout)
        return tuple(int(n) for n in found.groups())


class TheRefusals(TranscriptFixture):

    def test_a_refused_call_is_listed_with_its_tool_and_its_command(self):
        # The row has to name WHICH call: a session makes hundreds of Bash calls,
        # and a row saying only "Bash was refused" sends the reader to grep.
        self.write(call_line("t1", command="git push --force"),
                   result_line("t1", "denied by the deny rule", is_error=True))
        run = self.run_it()
        self.assertEqual(self.counts(run), (1, 0))
        self.assertIn("denied by the deny rule", run.stdout)
        self.assertIn("git push --force", run.stdout)
        self.assertIn("Bash", run.stdout)

    def test_a_result_that_is_not_an_error_is_not_a_refusal(self):
        self.write(call_line("t1", command="ls"), result_line("t1", "a.txt"))
        run = self.run_it()
        self.assertEqual(self.counts(run), (0, 0))
        self.assertEqual(run.returncode, 0, run.stderr)

    def test_a_structured_result_is_read_like_a_plain_one(self):
        # The harness writes a list of typed blocks when the tool returned
        # structured content. A reader that handled only the string shape would
        # print an empty message here and score every such call as silent.
        self.write(call_line("t1", command="ls"),
                   result_line("t1", "the structured refusal", is_error=True,
                               structured=True))
        run = self.run_it()
        self.assertEqual(self.counts(run), (1, 0))
        self.assertIn("the structured refusal", run.stdout)

    def test_a_refusal_with_no_call_recorded_is_still_reported(self):
        # The pairing is a nicety; the refusal is the signal. Dropping the row
        # because the tool_use is missing would hide exactly the transcripts
        # that were cut short.
        self.write(result_line("orphan", "something was refused", is_error=True))
        run = self.run_it()
        self.assertEqual(self.counts(run), (1, 0))
        self.assertIn("something was refused", run.stdout)

    def test_a_subagent_entry_in_the_parent_file_is_read_from_its_own(self):
        # A sidechain record in the session's own jsonl is a COPY of a line the
        # agent's file already holds. Skipped here so the row is not printed
        # twice; the agent's file is read on its own, below.
        self.write(call_line("t0", command="ls"), result_line("t0", "a.txt"),
                   call_line("t1", command="ls", sidechain=True),
                   result_line("t1", "the subagent's refusal", is_error=True,
                               sidechain=True))
        run = self.run_it()
        self.assertEqual(self.counts(run), (0, 0))
        self.assertNotIn("subagent's refusal", run.stdout)

    def test_a_dispatched_agents_refusals_are_this_sessions(self):
        # They ARE the session's: a hook that turned a dispatched agent away
        # refused work this session asked for, and the close is the only place
        # anyone reads it. Every record in that file is `isSidechain`, which is
        # why the skip above belongs to the parent file alone.
        lines = []
        for n in range(5):
            lines += [call_line(f"a{n}", command=f"cmd{n}", sidechain=True),
                      result_line(f"a{n}", f"agent refusal {n}", is_error=True,
                                  sidechain=True)]
        self.write(call_line("t0", command="ls"), result_line("t0", "a.txt"))
        self.write_subagent("agent-a1b2c3.jsonl", *lines)
        run = self.run_it()
        self.assertEqual(self.counts(run), (5, 0))
        self.assertIn("agent refusal 4", run.stdout)

    def test_an_agent_a_workflow_ran_is_read_too(self):
        # The harness nests those one level deeper, under `workflows/<id>/`.
        self.write(call_line("t0", command="ls"), result_line("t0", "a.txt"))
        self.write_subagent(os.path.join("workflows", "wf_1", "agent-z.jsonl"),
                            result_line("a1", "the workflow agent's refusal",
                                        is_error=True, sidechain=True))
        run = self.run_it()
        self.assertEqual(self.counts(run), (1, 0))

    def test_a_half_written_last_line_costs_nothing(self):
        # The transcript is appended to live, and a session asking what it was
        # refused is by definition still running.
        with open(self.transcript, "w") as fh:
            fh.write(call_line("t1", command="ls") + "\n")
            fh.write(result_line("t1", "refused", is_error=True) + "\n")
            fh.write('{"type": "assistant", "mess')
        run = self.run_it()
        self.assertEqual(self.counts(run), (1, 0))

    def test_a_control_sequence_in_a_message_is_stripped(self):
        # A refusal message is written by whatever refused — a hook, a tool, a
        # classifier — and it lands in a terminal. The escape is removed where
        # the value enters the output.
        self.write(call_line("t1", command="ls"),
                   result_line("t1", "refused \x1b[31mred\x1b[0m", is_error=True))
        run = self.run_it()
        self.assertNotIn("\x1b", run.stdout)
        self.assertIn("red", run.stdout)

    def test_the_rows_are_capped_and_the_cut_is_declared(self):
        lines = []
        for n in range(5):
            lines += [call_line(f"t{n}", command=f"cmd{n}"),
                      result_line(f"t{n}", f"refusal {n}", is_error=True)]
        self.write(*lines)
        run = self.run_it("--limit", "2")
        self.assertEqual(self.counts(run), (5, 0))
        self.assertIn("3 more", run.stdout)
        self.assertNotIn("refusal 4", run.stdout)


class TheQueueInvariant(TranscriptFixture):
    """Class 2: a write was invoked and no success line came back."""

    def transcript_for(self, command, output, is_error=False):
        self.write(call_line("t1", command=command),
                   result_line("t1", output, is_error=is_error))
        return self.run_it()

    def test_a_write_that_printed_its_success_line_is_confirmed(self):
        run = self.transcript_for("tk-queue add 'a new item' --class CHORE",
                                  "added T418: a new item")
        self.assertEqual(self.counts(run), (0, 0))

    def test_a_write_with_no_success_line_is_unconfirmed(self):
        # The silent loss this class exists for: the tool call reports success,
        # the item is simply not there.
        run = self.transcript_for("tk-queue add 'a new item' --class CHORE",
                                  "tk-queue: the WIP cap is full")
        self.assertEqual(self.counts(run), (0, 1))
        self.assertIn("add", run.stdout)

    def test_a_write_whose_call_never_returned_is_unconfirmed(self):
        # The window ended between the call and its result. Nothing says the
        # write landed, so nothing here says it did.
        self.write(call_line("t1", command="tk-queue done T418 --how 'shipped'"))
        run = self.run_it()
        self.assertEqual(self.counts(run), (0, 1))
        self.assertIn("returned nothing", run.stdout)

    def test_help_is_not_a_write(self):
        # Measured on a real transcript: 3 of 9 rows were the session reading
        # the flags. A report that cries wolf is a report nobody opens.
        run = self.transcript_for("tk-queue add --help", "usage: tk-queue add ...")
        self.assertEqual(self.counts(run), (0, 0))

    def test_a_read_only_subcommand_is_not_a_write(self):
        run = self.transcript_for("tk-queue list", "T418  something open")
        self.assertEqual(self.counts(run), (0, 0))

    def test_a_quoted_mention_is_not_an_invocation(self):
        # Briefings in this house quote queue commands verbatim.
        run = self.transcript_for("grep -n 'tk-queue add' AFK.md", "42: run it")
        self.assertEqual(self.counts(run), (0, 0))

    def test_an_unquoted_mention_after_a_reading_command_is_not_an_invocation(self):
        run = self.transcript_for("echo tk-queue add the item", "tk-queue add the item")
        self.assertEqual(self.counts(run), (0, 0))

    def test_the_dir_option_before_the_subcommand_is_skipped(self):
        # `tk-queue --dir X add ...` is how every unattended caller writes it;
        # a reader that took the path for the subcommand would see none at all.
        run = self.transcript_for(
            "tk-queue --dir /tmp/memory claim T418 --as lane-1", "")
        self.assertEqual(self.counts(run), (0, 1))
        self.assertIn("claim", run.stdout)

    def test_a_path_qualified_invocation_is_seen(self):
        run = self.transcript_for(
            "python3 /root/.claude/skills/tk/bin/tk-queue edit T418 --effort S", "")
        self.assertEqual(self.counts(run), (0, 1))

    def test_two_invocations_in_one_command_are_counted_apart(self):
        run = self.transcript_for(
            "tk-queue claim T418 --as lane-1; tk-queue edit T418 --effort S",
            "T418 claimed by lane-1 (2026-09-16)")
        self.assertEqual(self.counts(run), (0, 1))
        self.assertIn("edit", run.stdout)

    def test_two_writes_of_one_kind_need_two_success_lines(self):
        # A presence check passes the first line for both calls, and the batch
        # that half failed reports clean. The batched write is the common shape
        # here, and the second half failing is exactly what it fails at.
        run = self.transcript_for(
            "tk-queue add 'one' --class CHORE; tk-queue add 'two' --class CHORE",
            "added T418: one\ntk-queue: the WIP cap is full")
        self.assertEqual(self.headline(run), (0, 1, 0))
        self.assertIn("1 `add` success line(s) for 2 invocation(s)", run.stdout)

    def test_two_writes_with_both_lines_are_both_confirmed(self):
        run = self.transcript_for(
            "tk-queue add 'one' --class CHORE; tk-queue add 'two' --class CHORE",
            "added T418: one\nadded T419: two")
        self.assertEqual(self.headline(run), (0, 0, 0))

    def test_an_unspaced_separator_still_starts_an_invocation(self):
        # `shlex.split` breaks on whitespace and never on a metacharacter, so
        # `ready;tk-queue` arrived as ONE word and the call after it was missed
        # outright. Unspaced `;` is how this house batches commands.
        run = self.transcript_for("echo ready;tk-queue add 'an item' --class CHORE",
                                  "tk-queue: the WIP cap is full")
        self.assertEqual(self.counts(run), (0, 1))
        self.assertIn("add", run.stdout)

    def test_a_later_help_does_not_suppress_an_earlier_write(self):
        # The reported defect, end to end: the boundary after `CHORE` was not a
        # token, so the `--help` of the SECOND command landed inside the first
        # command's segment and the real, failed `add` was reported as clean.
        run = self.transcript_for(
            "tk-queue add 'an item' --class CHORE; tk-queue done --help",
            "tk-queue: the WIP cap is full")
        self.assertEqual(self.counts(run), (0, 1))
        self.assertIn("add", run.stdout)

    def test_a_newline_between_two_calls_ends_the_first_one(self):
        # A newline is whitespace to the tokenizer and leaves no separator token
        # behind, so the binary's own name has to end the segment. Without it the
        # second call's `--help` suppresses the first call's write.
        run = self.transcript_for(
            "tk-queue add 'an item' --class CHORE\ntk-queue done --help",
            "tk-queue: the WIP cap is full")
        self.assertEqual(self.counts(run), (0, 1))
        self.assertIn("add", run.stdout)

    def test_a_separator_inside_quotes_is_not_a_boundary(self):
        # The other direction: the item's own text may carry a `;`, and a reader
        # that split on the raw character would cut the segment inside it.
        run = self.transcript_for("tk-queue add 'first; then --help' --class CHORE",
                                  "tk-queue: the WIP cap is full")
        self.assertEqual(self.counts(run), (0, 1))

    def test_the_briefing_the_order_and_the_done_log_are_writes_too(self):
        # Each writes a file and none was in the table, so a failed one was
        # invisible to the close: the briefing a sibling session is waiting on,
        # the order the next kickoff reads, the done-log a migrate folds into.
        for sub, command, printed in (
                ("handoff", "tk-queue handoff T418",
                 "wrote /workspace/projects/memory/handoff-T418.md"),
                ("bump", "tk-queue bump T418", "T418 → top of the queue"),
                ("migrate", "tk-queue migrate --dir memory",
                 "2 [x] item(s) → done-log; IDs assigned up to T420")):
            with self.subTest(sub, direction="confirmed"):
                run = self.transcript_for(command, printed)
                self.assertEqual(self.headline(run), (0, 0, 0))
            with self.subTest(sub, direction="unconfirmed"):
                run = self.transcript_for(command, "tk-queue: refused")
                self.assertEqual(self.headline(run), (0, 1, 0))
                self.assertIn(sub, run.stdout)

    def test_a_bump_on_an_item_already_at_the_top_is_a_no_op_not_a_loss(self):
        run = self.transcript_for("tk-queue bump T418",
                                  "T418 is already at the top of the queue")
        self.assertEqual(self.headline(run), (0, 0, 0))

    def test_a_rewritten_briefing_counts_as_a_write(self):
        run = self.transcript_for(
            "tk-queue handoff T418 --force",
            "rewrote /workspace/projects/memory/handoff-T418.md")
        self.assertEqual(self.headline(run), (0, 0, 0))

    def test_an_honest_no_op_counts_as_a_success_line(self):
        # `release` on an unclaimed item and `done` on an item already logged are
        # reported by tk-queue in their own words. Reading them as failures would
        # report a write that did happen as missing.
        run = self.transcript_for("tk-queue release T418",
                                  "T418 carries no claim — nothing to release")
        self.assertEqual(self.counts(run), (0, 0))

    def test_an_untokenizable_command_is_its_own_class_not_a_write(self):
        # What this reader knows about it is only that it could not read it.
        # Counted as a write, it would assert a write nobody can show was
        # invoked; counted nowhere, it would hide the command it could not read.
        run = self.transcript_for("tk-queue add 'unclosed", "")
        self.assertEqual(self.headline(run), (0, 0, 1))
        self.assertIn("does not tokenize", run.stdout)

    def test_a_heredoc_body_is_data_and_not_a_command(self):
        # A heredoc carries a file, a commit message or a briefing, and this
        # house writes all three with queue commands quoted inside them. Read as
        # command text they are invocations that never ran — measured twice: 128
        # of 135 unparsed rows over 254 transcripts were heredocs the shell ran
        # fine, and a `done` row on a live transcript was a line in a commit
        # message. The apostrophe below is what used to break the tokenizer.
        run = self.transcript_for(
            "cat <<'EOF' > brief.md\n"
            "Run the tk-queue command yourself and add NO queue item — it's for\n"
            "the orchestrator to write.\n"
            "EOF",
            "")
        self.assertEqual(self.headline(run), (0, 0, 0))

    def test_a_commit_message_naming_a_write_is_not_one(self):
        run = self.transcript_for(
            "git commit -F - <<'MSG'\n"
            "T418: the close stops calling tk-queue done itself\n"
            "MSG",
            "[lane/x 1a2b3c] T418")
        self.assertEqual(self.headline(run), (0, 0, 0))

    def test_a_write_after_a_heredoc_is_still_seen(self):
        # The terminator ends the body; what follows is command text again.
        run = self.transcript_for(
            "cat <<'EOF' > brief.md\nrun tk-queue done T1 yourself\nEOF\n"
            "tk-queue edit T418 --effort S",
            "")
        self.assertEqual(self.headline(run), (0, 1, 0))
        self.assertIn("edit", run.stdout)

    def test_an_untokenizable_command_without_the_bin_is_silent(self):
        # The regression this gate exists for: without it every unbalanced quote
        # in the session was reported, which is a wrong number in the classes
        # this command exists to count.
        run = self.transcript_for("echo 'unclosed", "")
        self.assertEqual(self.headline(run), (0, 0, 0))

    def test_a_success_line_quoted_back_does_not_confirm_another_call(self):
        # The patterns are anchored at the label for this reason: briefings and
        # ledgers in this house echo queue output verbatim, and an unanchored
        # search would find a success line inside one of them.
        run = self.transcript_for(
            "tk-queue edit T418 --effort S",
            "the ledger says: 'T400 updated' — which is not this call")
        self.assertEqual(self.counts(run), (0, 1))

    def test_a_refused_write_lands_in_both_classes(self):
        # Deliberate, and the two answer different questions: the harness refused
        # the call, AND the queue did not get its item.
        run = self.transcript_for("tk-queue add 'an item' --class CHORE",
                                  "I cannot vouch for this call", is_error=True)
        self.assertEqual(self.counts(run), (1, 1))


class TheQueueSeam(unittest.TestCase):
    """The pinned shapes, against `tk-queue` itself."""

    @classmethod
    def setUpClass(cls):
        cls.module = load_tk_errors()
        with open(TK_QUEUE) as fh:
            cls.queue_source = fh.read()

    def test_every_pinned_shape_is_still_a_literal_in_tk_queue(self):
        # This is the drift alarm. `tk-errors` recognises a write by the line
        # `tk-queue` prints, so a rewording there makes this reader go quiet with
        # nothing else failing. Here it fails loudly instead.
        for sub, literals in self.module.LITERALS.items():
            for literal in literals:
                with self.subTest(sub=sub, literal=literal):
                    self.assertIn(literal, self.queue_source)

    def test_the_two_tables_cover_the_same_subcommands(self):
        # A hand-kept list beside a completeness check is the next defect: a
        # subcommand added to one table and not the other would be counted as
        # invoked and never confirmable, or confirmed by nothing.
        self.assertEqual(set(self.module.SUCCESS), set(self.module.LITERALS))
        for sub in self.module.SUCCESS:
            with self.subTest(sub=sub):
                self.assertEqual(len(self.module.SUCCESS[sub]),
                                 len(self.module.LITERALS[sub]))

    def test_every_watched_subcommand_is_a_real_one(self):
        # A typo in the table watches a subcommand that does not exist, and
        # nothing else in the suite would notice.
        declared = set(re.findall(r'sub\.add_parser\(\s*"([a-z]+)"',
                                  self.queue_source))
        self.assertTrue(declared, "no subparsers found — the grep drifted")
        self.assertLessEqual(set(self.module.SUCCESS), declared)

    def test_the_read_only_subcommands_are_left_out(self):
        # The other half of the same question: a read counted as a write reports
        # a mismatch on every `list` a session runs.
        for sub in ("list", "report", "pack"):
            with self.subTest(sub=sub):
                self.assertNotIn(sub, self.module.SUCCESS)


class TheExitCodes(TranscriptFixture):

    def test_a_clean_session_exits_zero_and_a_dirty_one_exits_one(self):
        self.write(call_line("t1", command="ls"), result_line("t1", "a.txt"))
        self.assertEqual(self.run_it().returncode, 0)
        self.write(call_line("t1", command="ls"),
                   result_line("t1", "refused", is_error=True))
        self.assertEqual(self.run_it().returncode, 1)

    def test_a_transcript_that_yielded_no_record_is_unread(self):
        # The false clean this class exists to prevent, one layer in: the file
        # was OPENED, so the reader never reached its "no transcript" branch,
        # and nothing in it survived the reading. An empty file, a file of
        # garbage and a file of somebody else's records all report the same
        # thing — nothing was read — and that is the opposite of clean.
        for label, body in (("empty", ""),
                            ("garbage", "not json\n{\"type\":\n"),
                            ("all sidechain",
                             result_line("t1", "an agent's", is_error=True,
                                         sidechain=True) + "\n")):
            with self.subTest(label):
                with open(self.transcript, "w") as fh:
                    fh.write(body)
                run = self.run_it()
                self.assertEqual(run.returncode, 2, run.stdout)
                self.assertIn("unread one", run.stderr)

    def test_an_unread_transcript_is_not_a_clean_one(self):
        # 2 and 0 are opposite facts. A seam that conflated them would report a
        # session nobody read as a session with nothing wrong in it.
        run = self.run_it(session="no-such-session")
        self.assertEqual(run.returncode, 2)
        self.assertIn("unread one", run.stderr)

    def test_a_missing_session_id_says_so(self):
        run = self.run_it(session=None)
        self.assertEqual(run.returncode, 2)
        self.assertIn("CLAUDE_CODE_SESSION_ID", run.stderr)

    def test_a_bad_flag_exits_sixty_four(self):
        # argparse's own 2 is this command's "no transcript", and a mistyped flag
        # arriving at a seam as that message is the confusion the codes prevent.
        self.write(call_line("t1", command="ls"), result_line("t1", "a.txt"))
        self.assertEqual(self.run_it("--nonsense").returncode, 64)
        self.assertEqual(self.run_it("--limit", "0").returncode, 64)

    def test_a_wildcard_session_id_does_not_glob(self):
        # Unescaped it matched a stranger's transcript, and this command would
        # report another session's refusals as this one's.
        self.write(call_line("t1", command="ls"),
                   result_line("t1", "refused", is_error=True))
        run = self.run_it(session="*")
        self.assertEqual(run.returncode, 2)

    def test_two_transcripts_for_one_id_are_refused(self):
        self.write(call_line("t1", command="ls"), result_line("t1", "a.txt"))
        twin = os.path.join(self.home.name, ".claude", "projects", "-other")
        os.makedirs(twin)
        with open(os.path.join(twin, f"{SESSION}.jsonl"), "w") as fh:
            fh.write(result_line("t2", "refused", is_error=True) + "\n")
        run = self.run_it()
        self.assertEqual(run.returncode, 2)
        self.assertIn("two transcripts", run.stderr)

    def test_a_transcript_path_wins_over_the_session_id(self):
        other = os.path.join(self.home.name, "elsewhere.jsonl")
        with open(other, "w") as fh:
            fh.write(result_line("t1", "the other file's refusal",
                                 is_error=True) + "\n")
        run = self.run_it("--transcript", other, session=None)
        self.assertEqual(run.returncode, 1)
        self.assertIn("the other file's refusal", run.stdout)


class TheSiblingSeam(TranscriptFixture):

    def test_main_takes_its_argv_like_every_sibling_bin(self):
        # `tk-context`, `tk-collisions` and `tk-closure-check` all declare
        # `main(argv=None)`. It is what lets a caller drive the parser without a
        # subprocess, and it is asserted rather than assumed.
        module = load_tk_errors()
        self.assertEqual(
            inspect.signature(module.main).parameters["argv"].default, None)

    def test_the_wrap_up_sends_its_first_step_here(self):
        # The command is useless unread. The close is where the reading belongs,
        # because that is where an unwritten item stops being recoverable.
        with open(WRAP_UP) as fh:
            text = re.sub(r"\s+", " ", fh.read())
        step_one = text.split("## 1. ", 1)[-1].split("## 2. ", 1)[0]
        self.assertIn("tk-errors", step_one)

    def test_the_first_step_cannot_close_over_what_the_command_found(self):
        # A step that PRINTS the two classes and closes without naming them is a
        # step nobody has to act on: the sweep scrolls past and the unconfirmed
        # `add` is marked done unread. The gate enumerates the categories, which
        # is the rule that a correction adding one adds it to the step that
        # reports.
        with open(WRAP_UP) as fh:
            text = re.sub(r"\s+", " ", fh.read())
        gate = text.split("**Done when:**", 1)[-1].split("## 2. ", 1)[0]
        self.assertIn("refusal", gate)
        self.assertIn("unconfirmed queue write", gate)


if __name__ == "__main__":
    unittest.main()
