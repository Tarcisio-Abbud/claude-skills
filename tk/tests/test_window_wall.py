#!/usr/bin/env python3
"""Doc-conformance proof for step 2 of `../skills/kickoff/WINDOW.md`'s wall.

Run: python3 -m unittest discover -s tk/tests   (stdlib only, no deps)

The subject is a two-command procedure the wall PRESCRIBES: write the briefing with
`tk-queue handoff`, then run the `tk-queue edit` that command prints. The second half is
what T265 added, and it is the half nothing enforced — the warning that asks for it goes to
**stderr at exit 0**, so a run that ignores it succeeds, and the wall is the moment nobody
is reading that stream.

HOW A PROSE DEFECT IS MADE TO FAIL A BEHAVIOUR TEST. The fixture does not hard-code the
procedure: it reads step 2, runs the handoff it prescribes, and runs the printed `edit` ONLY
IF the step still says to. So deleting that instruction from the prose does not merely fail a
regex — it removes a step from what the fixture executes, and the end state it asserts (the
item carrying `[[handoff-T00N]]`) is not reached. The prose is the program.

WHY AN ORDINARY ITEM. `test_afk_audit.py` already runs a briefing recipe end to end, but its
REGRILL is a `DECISION` whose link rides in `--deferred "afk — [[handoff-T00N]]"`, written by
a command that recipe spells out. Every other site prescribing a handoff — this wall, this
file's planning seam, `AFK.md`'s close and its oversized item, `wrap-up/SKILL.md` — writes no
such field, so the link can only come from the printed `edit`. That is the path executed here.

WHAT IS ASSERTED ABOUT THE BRIEFING. The file itself, not just the item's string: it is
stat'd, read, and each field's value is asked for under its own heading. Without that the
suite proves an item pointing at a name with nothing at the other end, and a `cmd_handoff`
that never wrote the file passes.

WHERE THE ASSERTION CAN ONLY BE ABOUT WORDING, it refuses a negation. `instructs_the_printed_edit`
is not a substring check: it finds the imperative and reads what stands in front of it, so
"never run the `edit` it prints" is NOT an instruction, and "run the printed `edit`" is.
Both directions are asserted below on synthetic text, and `mutations_window_wall.py` carries
the negated form as a mutant.

WHAT IT DOES NOT PROVE. That an orchestrator meeting the wall reaches step 2 at all — nothing
here can see a session. Nor anything about the wall's other five steps, nor about the four
sibling sites that prescribe the same procedure; those are held by review. And it cannot see
whether the prose is USEFUL: a step whose wording is faithful and unreadable passes.

The only edits made to the prescribed command before running it: the metavariables the step
writes as `"<id>"` and `"..."`, and the `--dir` the fixture attaches (`queue_fixture.py`).
"""

import os
import re
import shlex
import unittest

from queue_fixture import QueueFixture, item_fields

HERE = os.path.dirname(os.path.abspath(__file__))
SKILLS = os.path.join(HERE, os.pardir, "skills")
WINDOW = os.path.join(SKILLS, "kickoff", "WINDOW.md")

WALL_HEADING = re.compile(r"^## The wall\s*$", re.M)

# The three mandatory fields, in the order the briefing RENDERS them (tk-queue's
# HANDOFF_FIELDS). A prescription that lists them in another order hands a reader
# filling three identical `"..."` left to right a briefing with its fields swapped.
MANDATORY = ("--objective", "--state", "--blockers")
HEADING_OF = {"--objective": "Objective", "--state": "State",
              "--blockers": "Blockers and notes"}
# One sentinel per field, so the briefing can be asked WHICH value reached WHICH heading.
VALUE_OF = {"--objective": "OBJECTIVE-SENTINEL resume the package where the wall stopped it",
            "--state": "STATE-SENTINEL T001 is pushed to branch t001; the window resets 14:20",
            "--blockers": "BLOCKERS-SENTINEL none, and the claims are held"}

# The item's text carries a double quote on purpose: it is what makes the printed
# remedy's shell quoting load-bearing rather than decorative.
ITEM_TEXT = 'empacotar a fatia "em curso" quando a parede chega'

# `run` with the `edit` close behind it, and nothing sentence-ending in between.
RUN_THE_EDIT = re.compile(r"\brun\b[^.;]{0,60}?`edit`", re.I)
# read backwards from that `run`: what turns an instruction into its opposite.
NEGATED = re.compile(r"(?:never|not|n't|without|avoid|skip|no need to|rather than|"
                     r"instead of)\W*$", re.I)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def section(text, heading):
    """The body under `## <heading>`, up to the next `## ` heading."""
    m = re.search(r"^## %s\s*$" % re.escape(heading), text, re.M)
    if not m:
        return None
    rest = text[m.end():]
    nxt = re.search(r"^## ", rest, re.M)
    return rest[:nxt.start()] if nxt else rest


def wall_section(text=None):
    """WINDOW.md's `## The wall`.

    Scoped for the reason `test_afk_audit.py` scopes its own extraction: a command
    prescribed under any OTHER section must not be folded into the wall's procedure
    and executed here.
    """
    return section(read(WINDOW) if text is None else text, "The wall") or ""


def numbered_step(text, n):
    """Step `n` of a numbered list, its wrapped continuation lines joined.

    The prescribed command is an inline code span broken across two lines by the
    wrapping; joining first is what lets it be read as the one line a reader pastes.
    """
    m = re.search(r"^%d\. (.*?)(?=^\d+\. |\Z)" % n, text, re.M | re.S)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""


def inline_commands(text, verb=""):
    """The `tk-queue …` inline code spans of a passage, whitespace collapsed."""
    found = [re.sub(r"\s+", " ", s).strip()
             for s in re.findall(r"`(tk-queue [^`]*)`", text)]
    return [c for c in found if c.startswith(f"tk-queue {verb}".strip())]


def instructs_the_printed_edit(text):
    """Does `text` tell the reader to RUN the `edit` the command prints?

    Not a substring check, because a substring cannot tell an instruction from its
    opposite: the same words carry "run the `edit` it prints" and "never run the
    `edit` it prints". Each imperative is found and the words in front of it read.
    """
    hits = list(RUN_THE_EDIT.finditer(text))
    return any(not NEGATED.search(text[max(0, m.start() - 40):m.start()]) for m in hits)


def pointers(text):
    """(the `*Section*` names a passage cites, the `.md` paths it names)."""
    sections = re.findall(r"(?<![*\w])\*([A-Z][^*\n]{3,})\*(?![*\w])", text)
    paths = re.findall(r"`([^`\s]+\.md)`", text)
    return sections, paths


def briefing_field(text, heading):
    """The body under `## <heading>` of a briefing file."""
    return (section(text, heading) or "").strip()


def fill(argv, iid):
    """The prescribed argv with its metavariables substituted, BY FLAG.

    Positionally would be the bug this suite exists to refuse: three identical
    `"..."` filled left to right land wherever the prose happens to list the flags,
    and nothing downstream would notice. Filled by name, the briefing can then be
    asked whether each value arrived under its own heading.
    """
    out, i = [], 0
    while i < len(argv):
        token = argv[i]
        if token == "<id>":
            out.append(iid)
        elif token in VALUE_OF and i + 1 < len(argv) and argv[i + 1] == "...":
            out += [token, VALUE_OF[token]]
            i += 2
            continue
        else:
            out.append(token)
        i += 1
    return out


class WallStep2Test(QueueFixture):
    def setUp(self):
        super().setUp()
        self.step2 = numbered_step(wall_section(), 2)

    def prescribed_handoff(self):
        cmds = inline_commands(self.step2, "handoff")
        self.assertTrue(cmds, "the wall's step 2 prescribes no `tk-queue handoff` — there is "
                              "nothing to lift, and every check that runs it is vacuous")
        return shlex.split(cmds[0])

    def add_ordinary_item(self):
        """The item the wall finds in flight: AUTONOMOUS, carrying no Deferred."""
        r = self.run_tk(["tk-queue", "add", ITEM_TEXT, "--class", "AUTONOMOUS",
                         "--effort", "M (~30min)", "--criterion", "A: a suite passa"])
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout.split()[1].rstrip(":")

    # --- what the prose has to say -------------------------------------------

    def test_the_wall_step_prescribes_the_handoff_and_instructs_the_printed_edit(self):
        """The reading the fixture below acts on, and the two ways it can be wrong."""
        self.assertTrue(wall_section().strip(), "WINDOW.md has no `## The wall` section")
        self.prescribed_handoff()
        self.assertTrue(instructs_the_printed_edit(self.step2),
                        "the wall's step 2 writes the briefing and never says to run the "
                        "`edit` the command prints — the item is left pointing at nothing, "
                        "and the briefing is one the next generation cannot find")
        # the reading refuses the opposite wording, and accepts a faithful rewrite:
        # without both, a green suite means only that some sentence has the words in it.
        for negated in ("**then never run the `edit` it prints**",
                        "the `edit` it prints is not to be run",
                        "there is no need to run the `edit` it prints"):
            with self.subTest(wording=negated):
                self.assertFalse(instructs_the_printed_edit(negated),
                                 "an instruction NOT to run the edit reads as one to run it")
        for faithful in ("**then run the printed `edit`**",
                         "Then run the `edit` the command prints.",
                         "and run the `edit` it prints (same file, *The item points*)"):
            with self.subTest(wording=faithful):
                self.assertTrue(instructs_the_printed_edit(faithful),
                                "a faithful rewrite of the instruction reads as absent")

    def test_the_prescribed_command_carries_the_mandatory_fields_in_rendered_order(self):
        """A reader fills three identical `"..."` left to right."""
        argv = self.prescribed_handoff()
        listed = [t for t in argv if t in MANDATORY]
        self.assertEqual(listed, list(MANDATORY),
                         "the prescribed handoff does not list --objective, --state and "
                         "--blockers in the order the briefing renders them — a reader "
                         "filling the placeholders in order writes a briefing with its "
                         "fields swapped, and the gate cannot see it")
        self.assertEqual(argv.count("..."), len(MANDATORY),
                         "a placeholder in the prescribed command has no field to land in")

    def test_the_pointers_in_the_step_resolve_and_the_home_states_the_rule(self):
        """A pointer aimed at a section that does not exist sends the reader nowhere."""
        names, paths = pointers(self.step2)
        self.assertTrue(names, "the wall's step 2 cites no section by name")
        targets = [read(WINDOW)] + [read(os.path.normpath(
            os.path.join(os.path.dirname(WINDOW), rel))) for rel in paths]
        for name in names:
            with self.subTest(pointer=name):
                self.assertTrue(any(section(t, name) is not None for t in targets),
                                f"*{name}* is not a section of WINDOW.md or of any file the "
                                f"step names ({', '.join(paths) or 'none'})")
        home = next((section(t, "The item points at the briefing")
                     for t in targets if section(t, "The item points at the briefing")), None)
        self.assertTrue(home, "the step names no home for the rule it points at")
        self.assertIn("[[handoff-T00N]]", home,
                      "the home does not say what the item has to carry")
        self.assertTrue(instructs_the_printed_edit(home),
                        "the section every site routes the reader to does not itself say to "
                        "run the printed `edit` — the pointers lead to silence")

    # --- what the prose does when it is run ----------------------------------

    def test_an_ordinary_item_points_at_its_briefing_after_the_prescribed_steps(self):
        """Execute step 2 as written, then ask the queue and the briefing what is there."""
        iid = self.add_ordinary_item()
        argv = fill(self.prescribed_handoff(), iid)
        self.assertNotIn("...", argv, "a placeholder the filler does not know was added")
        self.assertFalse([t for t in argv if re.fullmatch(r"<.+>", t)],
                         "an unfilled metavariable survived the filler")

        wrote = self.run_tk(argv)
        self.assertEqual(wrote.returncode, 0,
                         f"the prescribed handoff does not run:\n{' '.join(argv)}\n"
                         f"{wrote.stderr}")
        self.assertNotIn("[[handoff-", wrote.stdout,
                         "the warning reached stdout — the step names stderr because that "
                         "is the stream a run at the wall is not watching")

        # THE FILE, not only the item's string: a briefing nothing wrote is a pointer
        # to nothing, and the item would carry it just the same.
        path = wrote.stdout.split(maxsplit=1)[1].strip()
        self.assertTrue(os.path.isfile(path), f"handoff reported a file it did not write: "
                                              f"{path}")
        written = read(path)
        self.assertTrue(written.startswith(f"# Handoff {iid} "),
                        f"the briefing does not name its item:\n{written[:120]}")
        for flag in MANDATORY:
            with self.subTest(field=flag):
                self.assertEqual(briefing_field(written, HEADING_OF[flag]), VALUE_OF[flag],
                                 f"what {flag} carried is not what `## {HEADING_OF[flag]}` "
                                 f"holds — the fields landed in the wrong headings")

        self.assertNotIn(f"[[handoff-{iid}]]", self.body(),
                         "the item points at the briefing before the remedy ran — the check "
                         "below would pass on a procedure that did nothing")
        fields_before = item_fields(self.body())

        # The step is executed, not assumed: with the instruction gone from the prose
        # this block does not run, and the end state below is the assertion that falls.
        if instructs_the_printed_edit(self.step2):
            m = re.search(r"`(tk-queue edit [^`]+)`", wrote.stderr)
            self.assertTrue(m, f"the handoff printed no remedy to run:\n{wrote.stderr}")
            before = self.reached()
            remedy = self.run_shell(m.group(1))
            self.assertEqual(self.reached(), before + 1,
                             f"the pasted remedy never reached tk-queue — the shell ate it, "
                             f"which is what its quoting exists to prevent:\n$ {m.group(1)}")
            self.assertEqual(remedy.returncode, 0,
                             f"the printed remedy does not run:\n$ {m.group(1)}\n"
                             f"{remedy.stderr}")

        body = self.body()
        self.assertIn(f"[[handoff-{iid}]]", body,
                      "the procedure the step prescribes leaves the item not pointing at its "
                      "briefing — nothing in the queue leads to the file that was written")
        self.assertIn(ITEM_TEXT, body, "the remedy did not preserve the item's own text")
        self.assertIn("**Class:** AUTONOMOUS.", body)
        self.assertNotIn("**Deferred:**", body,
                         "the item acquired a Deferred field — the link under test is the "
                         "one the printed `--text` writes, not the one `--deferred` carries")
        for seg in fields_before:
            self.assertIn(seg, body, f"the printed remedy dropped {seg!r} from the item")

        again = self.run_tk(argv)
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertNotIn("does not point at", again.stderr,
                         "the linked item is still warned about — the pointer written is not "
                         "the one the command reads back")


if __name__ == "__main__":
    unittest.main()
