#!/usr/bin/env python3
"""Doc-conformance proof for the wave audit, `../skills/kickoff/AUDIT.md`.

Run: python3 -m unittest discover -s tk/tests   (stdlib only, no deps)

The audit was step 4 of `AFK.md` until it was split out into its own branch file
(ambiente#225); the recipe travelled with it and this file was re-anchored in the
same commit, which is what keeps a split from being a silent deletion of the proof.

What it proves: the `tk-queue` recipe the audit PRESCRIBES for a REGRILL is lifted out of
`AUDIT.md`'s outcomes SECTION and made to run — as an argv list and, separately, in a real
shell — landing a `DECISION` item that carries its **Deferred:** gate and, after the remedy
the tool prints, points at its briefing. Every prescribed command that sets
`--class DECISION`, whatever its subcommand, must carry `--deferred`; and the `add` with
`--deferred` removed must be refused with nothing entering the queue.

Four properties are deliberate, each having been a hole once:

- the extraction is scoped to the outcomes section of ONE file, so a ```sh example added
  under any other section of `AUDIT.md`, or anywhere in `AFK.md`, is neither folded into
  "the recipe" nor executed here;
- the gate sweep asks `--class DECISION` of every subcommand, not only of `add`: an ungated
  `edit --class DECISION` beside the real recipe once sat under a green suite;
- the recipe is run through a shell as well as through argv, because `shlex.split` plus
  `subprocess.run(list)` never meets a shell;
- and one shell run is made with the metavariables left ALONE. Substituting them first is
  what a reader is told to do, and it is also what hides an unquoted `<id>`: substituted, it
  is an ordinary word either way. Left alone it is the shell's own metacharacter, and the
  line dies at `bash: id: No such file or directory` before `tk-queue` is reached. So that
  run asserts the weaker, real property — the shell HANDS the line to `tk-queue` — measured
  through a shim that records every invocation.

Two limits of the extraction, decided rather than inherited. The scope is *The four outcomes*
and everything under it, so a `tk-queue` line in ANY H3 of that section counts as the recipe.
And only ```sh fences are read: a fence written ```bash, or indented inside a blockquote, is
invisible. Rewriting the REAL recipe that way empties the list and the vacuity guard fires
loud; what would pass unseen is a SUPPLEMENTARY recipe added in one of those formats.

What it does NOT prove: that an orchestrator running a package reaches the audit at all, or
that a REGRILL it decided on was really queued. Nothing here can see a session — that is
what the block the step owes step 6 is for. It also does not execute prescribed subcommands
other than `add` and `handoff`: those are swept for the gate, not run, since giving each one
a fixture is work of its own.

The only edits made to a prescribed command before running it: `--dir <throwaway>`, applied
by the shim so no real memory dir is touched, and `<id>`, which becomes the id the `add`
printed.

THE SWEEP OVER THE PLUGIN'S PROSE, `TheQueueFlagSweep`, is the second half of this
file and it is not about the audit. A command a reader pastes is the same hazard
wherever it is written, and the sweep that read only the kickoff skill let five
prescriptions reach `merge-gate/SKILL.md` naming no queue at all (T334). It now walks
every markdown file of the plugin outside `tests/` and reads three bins, not one:
`tk-ticket-ref` and `tk-closure-check` resolve the same queue from the same flag.
It asks two things of every command carrying a metavariable — that the metavariables
are quoted, and that the queue directory is named — and it is read, never run: an
illustrative command has no fixture, and the fixture the recipe does have would mask
the missing flag anyway, for the reason below. Commands another lane of this package
owns are exempt BY THEIR EXACT TEXT in `AWAITING_A_SWEEP`, and the exemption reddens
the day the command is repaired.

WHY THE QUEUE FLAG IS ASSERTED ON THE ARGV AND NOT ON THE RUN. That first edit is also a
mask. The recipe writes `--dir "<queue dir>"` itself, and both routes into the script —
`run_tk` and the shell shim — append a `--dir` of their own, which argparse then takes as
the winner. So every run here SUCCEEDS whether or not the prose names the queue, and no
assertion downstream of the fixture can tell the two apart: the recipe could lose the flag
and this file would stay green, while an orchestrator pasting it wrote whichever queue its
cwd encodes to. The flag is therefore asserted on the argv the PROSE produced, before the
fixture is reached — as `test_window_wall.py` asserts the same flag for the same reason.
"""

import os
import re
import shlex
import unittest

from queue_fixture import QueueFixture, item_fields

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.join(HERE, os.pardir)
KICKOFF = os.path.join(PLUGIN, "skills", "kickoff")
AFK = os.path.join(KICKOFF, "AFK.md")
AUDIT = os.path.join(KICKOFF, "AUDIT.md")

# The three bins that resolve a queue. Each takes the directory from `--dir` and,
# failing that, from the cwd — so all three write the wrong project's queue from a
# code worktree, and a sweep aimed at `tk-queue` alone proved nothing about the
# other two (T334).
QUEUE_BINS = ("tk-queue", "tk-ticket-ref", "tk-closure-check")
NAMES_A_BIN = re.compile(r"\b(?:%s)\b" % "|".join(QUEUE_BINS))
METAVARIABLE = re.compile(r"<[^<>]+>")
# A code span, delimited by a RUN of backticks and closed by a run of the same
# length — CommonMark's own rule. Reading one backtick as the delimiter puts the
# scan out of phase at the first ``double-delimited`` span, and from there every
# span it returns is the prose BETWEEN two commands. `fleet/SKILL.md` has such a
# table, and that is why its prose measured as prescribing nothing.
CODE_SPAN = re.compile(r"(?<!`)(`+)(?!`)(.+?)(?<!`)\1(?!`)", re.S)
DOUBLE_QUOTED = re.compile(r'"[^"]*"')
# `--help` prints the same text from any directory, so it names no queue: the one
# carve-out T334's criterion grants.
NO_QUEUE_TO_NAME = "--help"

# Prescriptions this sweep sees and cannot fix here, because another lane of the
# same package owns the file. Keyed by the command itself, which is unique across
# the tree; `test_the_exemptions_are_still_earned` reddens the day one is repaired,
# so the list cannot outlive its reason.
AWAITING_A_SWEEP = {
    '../../bin/tk-closure-check "<id>" --dir "<queue dir>" --pr <n>':
        "skills/kickoff/AFK.md",
    'tk-queue report --dir "<queue dir>" --since <today minus 7 days>':
        "skills/kickoff/SKILL.md",
    '../../bin/tk-ticket-ref <id> --dir "<queue dir>" --closing-line':
        "skills/kickoff/SKILL.md",
    'tk-queue list --dir <that path>':
        "skills/fleet/SKILL.md",
    '(cd "<the project\'s directory>" && python3 <.../tk/bin>/tk-queue pack)':
        "skills/fleet/SKILL.md",
}

# The audit's own file, and the numbered step of AFK.md that routes into it.
OUTCOMES_HEADING = re.compile(r"^## The four outcomes\s*$", re.M)
AUDIT_STEP_HEADING = re.compile(r"^## \d+\. Audit\b.*$", re.M)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def afk_text():
    return read(AFK)


def audit_text():
    return read(AUDIT)


def prose_files():
    """Every markdown file of the plugin, `tests/` aside.

    A walk and not a list: the two splits that moved prescriptions out of AFK.md
    would each have needed a hand-written name added here, and the sweep aimed at a
    fixed list is the one that stops covering the file it was written for.
    """
    found = []
    for folder, folders, names in os.walk(PLUGIN):
        folders[:] = [d for d in folders if d != "tests"]
        found += [os.path.join(folder, name)
                  for name in names if name.endswith(".md")]
    return sorted(found)


def command_spans(text):
    """Every command in `text` naming one of `QUEUE_BINS`, whitespace-normalised.

    Two shapes, because a reader pastes both: a code span, and a line of a fenced
    block. Backslash continuations are joined FIRST — a command cut across lines is
    one command, and reading its halves apart is how a flag on the second half goes
    unseen.

    The fences are cut OUT before the code spans are read, rather than read on top of
    them: a ``` opener is a three-backtick run, and letting `CODE_SPAN` meet one puts
    the scan out of phase for the rest of the file. A fenced line carrying its own
    code span is read as that span, so a prompt template quoting a command still
    yields the command.
    """
    joined = re.sub(r"\\\n\s*", " ", text)
    spans, prose, cut = [], [], 0
    for fence in re.finditer(r"^```[a-z]*\n(.*?)^```", joined, re.M | re.S):
        prose.append(joined[cut:fence.start()])
        cut = fence.end()
        for line in fence.group(1).splitlines():
            spans += code_spans(line) if "`" in line else [line]
    prose.append(joined[cut:])
    for chunk in prose:
        spans += code_spans(chunk)
    return [" ".join(span.split()) for span in spans if NAMES_A_BIN.search(span)]


def code_spans(text):
    return [m.group(2) for m in CODE_SPAN.finditer(text)]


def unquoted_metavariables(span):
    """The `<...>` of `span` a shell reads as a redirect rather than as text.

    What sits inside double quotes is text: `--deferred "<why it waits>"` is safe,
    and so is a placeholder in the middle of a quoted item. Stripping the quoted runs
    first is what tells the two apart — hunting `<...>` in the raw span calls every
    quoted placeholder a defect.
    """
    return METAVARIABLE.findall(DOUBLE_QUOTED.sub("", span))


def prescribes_a_run(span):
    """Whether `span` is a line to fill in and paste, or the name of a subcommand.

    The metavariable is the mark. `tk-queue done` in a sentence names a subcommand
    and writes nothing; `tk-queue done "<id>"` is a line an orchestrator runs, and
    only a line owes the queue directory it writes.
    """
    return bool(METAVARIABLE.search(span))


def audit_section(text=None):
    """AUDIT.md from *The four outcomes* to the next `## ` heading.

    Scoped on purpose, and on two axes: the extraction used to regex the whole of
    AFK.md, so a legitimate ```sh example under any other step was folded into the
    recipe and executed here — the test's own target moving with no signal. Reading
    one section of one file keeps that shut now that the audit has a file of its own.
    """
    text = audit_text() if text is None else text
    m = OUTCOMES_HEADING.search(text)
    if not m:
        return ""
    rest = text[m.end():]
    nxt = re.search(r"^## ", rest, re.M)
    return rest[:nxt.start()] if nxt else rest


def logical_lines(section):
    """The `tk-queue` lines of the section's ```sh fences, backslash-joined."""
    out = []
    for block in re.findall(r"^```sh\n(.*?)^```", section, re.M | re.S):
        joined = re.sub(r"\\\n\s*", " ", block)
        for line in joined.splitlines():
            line = line.strip()
            if line.startswith("tk-queue "):
                out.append(line)
    return out


def prescribed_commands():
    """The prescribed lines as (text, argv) pairs, in file order."""
    return [(line, shlex.split(line)) for line in logical_lines(audit_section())]


def sets_decision(argv):
    """Whether this command sets --class DECISION — for ANY subcommand.

    `add` is not the only route: `edit --class DECISION` reaches the same state and
    tk-queue gates it the same way. Asking only about `add` let an ungated
    `edit --class DECISION` sit beside the real recipe with the suite green.
    """
    return "--class" in argv and argv[argv.index("--class") + 1] == "DECISION"


def subcommand(argv):
    return argv[1] if len(argv) > 1 else ""


def without_flag(argv, flag):
    i = argv.index(flag)
    return argv[:i] + argv[i + 2:]


class AfkAuditTest(QueueFixture):
    """The queue, the shim and the paste live in `queue_fixture.QueueFixture`."""

    def setUp(self):
        super().setUp()
        self.cmds = prescribed_commands()

    def runnable(self):
        """The prescribed lines this file executes, in order."""
        return [(line, argv) for line, argv in self.cmds
                if subcommand(argv) in ("add", "handoff")]

    # --- the guards that stop every check below from passing over nothing ----

    def test_the_audit_step_and_its_regrill_recipe_are_still_there(self):
        """Each check below iterates a list derived from AUDIT.md; an empty list
        would let all of them pass while the recipe was gone."""
        text = audit_text()
        # assertTrue, not assertRegex: the latter prints the whole file on failure.
        self.assertTrue(OUTCOMES_HEADING.search(text),
                        "AUDIT.md has no `## The four outcomes` section")
        self.assertTrue(audit_section(text).strip(), "the outcomes section is empty")
        self.assertTrue([a for _, a in self.cmds if sets_decision(a)],
                        "the audit section prescribes no `--class DECISION` command — "
                        "the REGRILL recipe is gone, and every gate check below is vacuous")
        self.assertTrue([a for _, a in self.cmds if subcommand(a) == "handoff"],
                        "the REGRILL recipe prescribes no handoff")

    def intruder(self):
        """A ```sh fence prescribing a command that is NOT the recipe."""
        return ('\n```sh\ntk-queue add "not the recipe" --class AUTONOMOUS '
                '--effort S --criterion "A: x"\n```\n')

    def test_the_extraction_is_scoped_to_the_outcomes_section(self):
        """A ```sh example under another section must not be folded into the recipe."""
        text = audit_text()
        m = OUTCOMES_HEADING.search(text)
        self.assertTrue(m, "AUDIT.md lost its outcomes heading; re-anchor this test")
        # BEFORE that heading, so the intruder really sits in an earlier section:
        # inserted after it, it lands inside the outcomes section, which is the scope.
        spiked = text[:m.start()] + self.intruder() + text[m.start():]
        self.assertIn("not the recipe", spiked)
        self.assertEqual(logical_lines(audit_section(spiked)),
                         logical_lines(audit_section(text)),
                         "a command from another section was folded into the recipe")

    def test_the_extraction_reads_the_audit_file_not_the_step_that_routes_to_it(self):
        """The split (ambiente#225) left a routing step behind in AFK.md.

        Nothing of AFK.md may reach the recipe list: before the split the whole file
        was in scope, and a fence added anywhere in it would have been executed here.
        The route itself is asserted too, because an audit no step reaches never runs.
        """
        self.assertTrue(AUDIT_STEP_HEADING.search(afk_text()),
                        "AFK.md has no numbered Audit step routing to AUDIT.md")
        self.assertIn("AUDIT.md", afk_text(),
                      "AFK.md never names AUDIT.md — the audit is unreachable from the "
                      "package flow, and the seam between the claim and the first run "
                      "sends the orchestrator nowhere")
        self.assertEqual(logical_lines(audit_section(afk_text() + self.intruder())), [],
                         "AFK.md is being read for the recipe — the extraction moved "
                         "back to the file the audit left")

    # --- the gate ------------------------------------------------------------

    def test_every_prescribed_command_names_the_queue_it_writes(self):
        """Which project's queue the recipe writes is decided by `--dir`, not by the cwd.

        Asserted on the argv, never on the run: see the module docstring — the fixture
        appends its own `--dir` to everything it executes, so the run is green either way.
        """
        self.assertTrue(self.cmds, "the recipe prescribes no command — re-anchor this file")
        for line, argv in self.cmds:
            with self.subTest(cmd=line):
                self.assertIn("--dir", argv,
                              "a prescribed command names no queue directory — without "
                              "`--dir` the script resolves from the cwd, which while a "
                              "package runs is the code's clone, and the item lands in "
                              "another project's queue")
                self.assertEqual(argv[argv.index("--dir") + 1], "<queue dir>",
                                 "`--dir` is prescribed with no metavariable to fill — the "
                                 "reader has nothing to substitute and pastes the literal")

    def test_every_prescribed_decision_command_carries_the_deferral(self):
        for line, argv in self.cmds:
            if sets_decision(argv):
                with self.subTest(cmd=line):
                    self.assertIn("--deferred", argv,
                                  "a DECISION prescribed with no --deferred: the recipe asks "
                                  "the orchestrator to run a command tk-queue refuses")

    def test_the_prescribed_regrill_runs_and_lands_a_gated_decision(self):
        """The recipe is code. Run it, in order, in a throwaway dir."""
        iid, ran = None, 0
        for line, argv in self.runnable():
            if subcommand(argv) == "add":
                r = self.run_tk(argv)
                self.assertEqual(r.returncode, 0, f"{line}\n{r.stderr}")
                iid = r.stdout.split()[1].rstrip(":")
                ran += 1
            else:
                self.assertTrue(iid, "a handoff is prescribed before any add")
                r = self.run_tk([a if a != "<id>" else iid for a in argv])
                self.assertEqual(r.returncode, 0, f"{line}\n{r.stderr}")
                self.assertTrue(os.path.exists(r.stdout.split(maxsplit=1)[1].strip()),
                                "handoff reported a file it did not write")
        self.assertTrue(ran, "no prescribed add was run")
        self.assertIn("**Class:** DECISION.", self.body())
        self.assertIn("**Deferred:**", self.body())

    def test_the_recipe_runs_in_a_shell_once_its_metavariables_are_filled(self):
        """The reader is told to substitute `<id>` and run. Do exactly that."""
        iid = None
        for line, argv in self.runnable():
            with self.subTest(cmd=line):
                r = self.run_shell(line if iid is None else line.replace("<id>", iid))
                self.assertEqual(r.returncode, 0,
                                 f"the prescribed line does not survive a shell:\n"
                                 f"$ {line}\n{r.stderr}")
                if subcommand(argv) == "add":
                    iid = r.stdout.split()[1].rstrip(":")
        self.assertTrue(iid, "no prescribed add reached the shell")

    def test_a_raw_paste_reaches_tk_queue_instead_of_dying_in_the_shell(self):
        """The metavariables are left ALONE here, which is the only way an unquoted
        one is visible: substituted, `<id>` is an ordinary word either way.

        The property asserted is deliberately weak, and it is the true one — the
        shell HANDS the line to tk-queue. What tk-queue then says about a literal
        `<id>` is its own business (it refuses it, which is correct). Unquoted, the
        line never gets that far: bash reads `<id>` as a redirect and dies.
        """
        lines = self.runnable()
        self.assertTrue(lines, "no prescribed line to paste")
        for line, _ in lines:
            with self.subTest(cmd=line):
                before = self.reached()
                r = self.run_shell(line)
                self.assertEqual(self.reached(), before + 1,
                                 f"the shell never reached tk-queue — a metavariable is "
                                 f"unquoted and the shell ate the line:\n$ {line}\n{r.stderr}")

    def test_the_briefing_is_reachable_from_the_item_after_the_printed_edit(self):
        """The handoff warns (exit 0) that the item does not point at its briefing
        and prints the `edit` that repairs it. The recipe says to run it — so run
        it here, as printed, and check the link is really there afterwards."""
        iid, warned = None, None
        for line, argv in self.runnable():
            if subcommand(argv) == "add":
                r = self.run_tk(argv)
                self.assertEqual(r.returncode, 0, r.stderr)
                iid = r.stdout.split()[1].rstrip(":")
            else:
                r = self.run_tk([a if a != "<id>" else iid for a in argv])
                self.assertEqual(r.returncode, 0, r.stderr)
                warned = r.stderr
        self.assertTrue(iid and warned is not None, "the recipe lost its add or its handoff")
        self.assertNotIn(f"[[handoff-{iid}]]", self.body(),
                         "the item already points at the briefing — this test proves nothing")
        m = re.search(r"`(tk-queue edit [^`]+)`", warned)
        self.assertTrue(m, f"the handoff printed no remedy to run:\n{warned}")
        # The remedy REWRITES the item, so what it leaves behind is asked of the whole
        # field chain, captured first and compared segment by segment. Asking only
        # whether the link arrived let a rebuild that dropped Class/Deferred/Effort/
        # Criterion through — the remedy erasing the very gate this file exists to
        # protect, with all eight tests green.
        fields_before = item_fields(self.body())
        self.assertIn("**Class:** DECISION.", fields_before,
                      "the item under test is not a gated DECISION — this proves nothing")
        r = self.run_shell(m.group(1))
        self.assertEqual(r.returncode, 0, f"the printed remedy does not run:\n{r.stderr}")
        self.assertIn(f"[[handoff-{iid}]]", self.body(),
                      "the remedy ran and the item still does not point at its briefing")
        fields_after = item_fields(self.body())
        for seg in fields_before:
            self.assertIn(seg, fields_after,
                          f"the printed remedy dropped {seg!r} from the item — the recipe "
                          f"tells the orchestrator to run a command that erases the gate")

    def test_the_same_regrill_without_the_gate_is_refused(self):
        """Checked backwards: the presence check above passes on a flag the script
        might no longer enforce, so the gate is watched firing."""
        for line, argv in self.cmds:
            if sets_decision(argv) and "--deferred" in argv:
                with self.subTest(cmd=line):
                    r = self.run_tk(without_flag(argv, "--deferred"))
                    self.assertNotEqual(r.returncode, 0,
                                        "a REGRILL entered the queue with no gate")
                    self.assertIn("--deferred", r.stderr)
                    self.assertEqual(self.body().count("- [ ] "), 0,
                                     "the refusal wrote the item anyway")


class TheQueueFlagSweep(unittest.TestCase):
    """Every pasteable command in the plugin's prose, not only the audit's recipe.

    The recipe is proved above by running it. Prose is proved here by reading it,
    which is the only proof available: an illustrative command has no fixture, and
    the fixture the recipe does have appends a `--dir` of its own that would mask a
    missing flag anyway (module docstring).

    Two properties, one sweep, because a reader pastes what the prose wrote:

    - the metavariables are QUOTED, or the shell eats the line as a redirect before
      the bin is reached;
    - the command names the queue it writes, since all three bins fall back to the
      cwd, which during a package is the code's clone and not the project's memory.
    """

    @classmethod
    def setUpClass(cls):
        cls.spans = [(os.path.relpath(path, PLUGIN), span)
                     for path in prose_files()
                     for span in command_spans(read(path))]

    def swept(self):
        return [(name, span) for name, span in self.spans
                if span not in AWAITING_A_SWEEP]

    def test_the_sweep_reaches_the_prose_outside_the_kickoff_skill(self):
        """Vacuity guard, and the one T334 needed: the sweep read only the kickoff
        files while `merge-gate/SKILL.md` prescribed five commands naming no queue."""
        files = {name for name, _ in self.spans}
        for name in ("skills/kickoff/AFK.md", "skills/merge-gate/SKILL.md",
                     "skills/verify/HANDOFF.md", "skills/wrap-up/SKILL.md",
                     "skills/dispatch/LOOP.md", "reference/session-finding.md",
                     "reference/subagent-policy.md"):
            with self.subTest(file=name):
                self.assertIn(name, files,
                              f"{name} prescribes no command the sweep can see — "
                              f"either it lost one, or `command_spans` stopped "
                              f"reading the shape it writes them in")

    def test_the_sweep_reads_the_two_bins_that_are_not_tk_queue(self):
        """`tk-ticket-ref` and `tk-closure-check` resolve the same queue from the
        same flag. A sweep aimed at `tk-queue` alone left both unmeasured, which is
        how five of them reached the merge gate with no `--dir` (T334)."""
        for bin_name in ("tk-ticket-ref", "tk-closure-check"):
            with self.subTest(bin=bin_name):
                self.assertTrue([s for _, s in self.spans if bin_name in s],
                                f"no {bin_name} command found in the plugin's prose "
                                f"— re-anchor this sweep")

    def test_every_pasteable_command_quotes_its_metavariables(self):
        for name, span in self.swept():
            bare = unquoted_metavariables(span)
            with self.subTest(file=name, cmd=span):
                self.assertEqual(bare, [],
                                 f"unquoted metavariable {bare} — a shell reads it as "
                                 f"a redirect and the line dies before the bin sees it")

    def test_every_pasteable_command_names_the_queue_it_writes(self):
        for name, span in self.swept():
            if not prescribes_a_run(span) or NO_QUEUE_TO_NAME in span:
                continue
            with self.subTest(file=name, cmd=span):
                self.assertIn("--dir", span,
                              "a prescribed command names no queue directory — without "
                              "`--dir` the bin resolves from the cwd, which while a "
                              "package runs is the code's clone, and the write lands in "
                              "another project's queue")

    def test_the_exemptions_are_still_earned(self):
        """An exemption outlives its reason in silence: the command is repaired, the
        entry stays, and the day the file regresses the sweep says nothing. Each one
        is therefore asserted still present and still red."""
        present = {span: name for name, span in self.spans}
        for span, where in AWAITING_A_SWEEP.items():
            with self.subTest(cmd=span):
                self.assertEqual(present.get(span), where,
                                 f"{span!r} is no longer in {where} — drop its entry "
                                 f"from AWAITING_A_SWEEP")
                red = (unquoted_metavariables(span)
                       or (prescribes_a_run(span) and NO_QUEUE_TO_NAME not in span
                           and "--dir" not in span))
                self.assertTrue(red,
                                f"{span!r} passes the sweep now — drop its entry from "
                                f"AWAITING_A_SWEEP so the file is held")


if __name__ == "__main__":
    unittest.main()
