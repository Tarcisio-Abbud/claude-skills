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
KICKOFF = os.path.join(HERE, os.pardir, "skills", "kickoff")
AFK = os.path.join(KICKOFF, "AFK.md")
AUDIT = os.path.join(KICKOFF, "AUDIT.md")
RESUME = os.path.join(KICKOFF, "RESUME.md")
# every file of the kickoff skill that PRESCRIBES a command inline. The quoting
# sweep below reads all of them: a metavariable is unquoted wherever a reader
# pastes it, and the two splits moved prescriptions out of AFK.md into files a
# sweep aimed at one name would have stopped covering.
PRESCRIBING = (("AFK.md", AFK), ("AUDIT.md", AUDIT), ("RESUME.md", RESUME))

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

    def test_inline_commands_quote_their_metavariables(self):
        """Every file of the skill, not only the recipe: `tk-queue done <id>` in prose is the
        same defect the recipe was just fixed for, and a reader pastes prose too.

        This checks QUOTING, not execution — the inline commands are illustrative and
        have no fixture here. Unquoted, `<id>` is a shell redirect and the line dies
        before tk-queue sees it.
        """
        spans = [(name, span)
                 for name, path in PRESCRIBING
                 for span in re.findall(r"`(tk-queue [^`]*)`", read(path))]
        self.assertTrue(spans, "no inline tk-queue command in any of them — re-anchor "
                               "this test")
        for name, span in spans:
            bare = re.findall(r"(?<![\"'])<[^<>`\"]+>(?![\"'])", span)
            with self.subTest(file=name, cmd=span):
                self.assertEqual(bare, [],
                                 f"unquoted metavariable {bare} — a shell reads it as a "
                                 f"redirect and the line dies before tk-queue sees it")

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


if __name__ == "__main__":
    unittest.main()
