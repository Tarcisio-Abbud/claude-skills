#!/usr/bin/env python3
"""Doc-conformance proof for `../skills/kickoff/LEDGER.md`.

Run: python3 -m unittest discover -s tk/tests   (stdlib only, no deps)

WHAT THE FILE IS. The FORMAT of a package's ledger and the prompt that restarts one
dead lane from it. The ledger itself is a file of each run's outbox and no test can
see one; what ships in the skill is the shape the orchestrator writes into, and the
shape is what a successor reads back after a compact or a quota wall.

WHAT IS ASSERTED, and why each one costs something when it goes:

- **the seven fields of the event line are named, each one under the metavariable a
  `grep` finds it by.** A ledger missing a field is not short, it is unreadable at
  the moment it matters: the hour, the lane, the agent, the model, the event, the
  result and the quota reading each answer a question a successor cannot ask anyone;
- **the hour is read from `date`, and the file says what an estimated hour cost.**
  Four lines of the package this format comes from were written from the
  orchestrator's own sense of elapsed time and were an hour wrong. The rate the same
  file computes is a difference of two hours, so the rule is not tidiness;
- **the quota field distinguishes a reading from a floor, with the nature and the
  anchor's age on the line.** The two example lines are checked against
  `../bin/tk-quota`'s own format strings rather than read as literals, so the day the
  bin changes what it prints, this reddens instead of the file forking quietly;
- **the lane restart is a pasteable prompt, ≤15 lines, with slots and not addresses**,
  and its first line separates it from `RESUME.md`, which resumes a GENERATION. A
  prompt past that budget has started restating `LANE-CONTRACT.md`;
- **`WINDOW.md` points here on exactly ONE line, inside the handoff step.** The ticket
  budgets one line; a pointer that drifts out of the handoff step points from nowhere.

VACUITY GUARD FIRST. Every check cuts a slice on a heading, and a heading that moved
would leave the check reading an empty string and passing. `section()` asserts each
slice non-empty as it is taken, and `test_every_section_the_checks_cut_on_is_still_there`
refuses the whole file's silence.

WHAT IS NOT PROVED HERE. That any orchestrator writes a ledger, that a lane restart
was ever dispatched, or that the prompt works — none of the three has a fixture. The
`tk-queue` mention in the file is swept for its flags by `test_afk_audit.py`'s
`TheQueueFlagSweep`, like every other pasteable command in the plugin's prose.
"""

import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.join(HERE, os.pardir)
KICKOFF = os.path.join(PLUGIN, "skills", "kickoff")
LEDGER = os.path.join(KICKOFF, "LEDGER.md")
WINDOW = os.path.join(KICKOFF, "WINDOW.md")
QUOTA = os.path.join(PLUGIN, "bin", "tk-quota")

SECTIONS = ("The event line",
            "The quota field: a reading and a floor are not the same claim",
            "The state table",
            "The lane restart")

# The seven fields, keyed by the metavariable the format line writes them as. The
# value is a phrase from that field's own bullet — membership is the assertion, so a
# field kept in the format line and dropped from the prose still reddens.
FIELDS = {
    "<hh:mm>": "never counted",
    "<lane>": "state table",
    "<agent>": "subagent-policy.md",
    "<model>": "as DISPATCHED",
    "<event>": "in one clause",
    "<result>": "what came back",
    "<quota>": "tk-quota",
}

# The four states a lane row passes through, in order.
STATES = ("alive", "pull request open", "review dispatched", "verdict")


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def flat(text):
    """`text` with every run of whitespace collapsed to one space.

    The phrases below are prose, and prose here is wrapped at the file's own column.
    Asserted against the raw text, a check depends on where the wrap fell: a reflow
    that changes nothing reddens, and a rewording that drops the rule stays green
    when it happens to re-wrap the same way.
    """
    return " ".join(text.split())


def quota_words():
    """The words `tk-quota` itself prints on its two lines, read from the bin.

    Retyping them here would let the two vocabularies fork in silence — the ledger's
    example would keep saying `estimate` long after the bin stopped, and a reader
    pasting what the bin prints would be pasting something this file calls wrong.
    """
    src = read(QUOTA)
    reading = re.search(r"said = f\"(.*?)\"", src)
    estimate = re.search(r"return \(f\"(.*?)\"\s*\n\s*f\"(.*?)\"\s*\n\s*f\"(.*?)\"\)",
                         src, re.S)
    assert reading, "tk-quota no longer builds its reading line as one f-string"
    assert estimate, "tk-quota no longer builds its estimate line as three f-strings"
    # The literal runs of each template, placeholders dropped: what a printed line
    # carries whatever the numbers are.
    template = reading.group(1) + " " + " ".join(estimate.groups())
    return [w for w in re.split(r"\{[^{}]*\}", template) if w.strip()]


class DocTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = read(LEDGER)
        cls.flat = flat(cls.text)
        cls.window = read(WINDOW)

    def section(self, title, raw=False):
        """The body under `## title`, up to the next `## ` — asserted non-empty."""
        pattern = re.compile(r"^## " + re.escape(title) + r"\s*$(.*?)(?=^## |\Z)",
                             re.M | re.S)
        found = pattern.findall(self.text)
        self.assertEqual(len(found), 1,
                         f"`## {title}` is not there exactly once — the check that "
                         f"cuts on it would read an empty string and pass")
        self.assertTrue(found[0].strip(), f"`## {title}` is empty")
        return found[0] if raw else flat(found[0])

    def fence(self, title, which=0):
        body = self.section(title, raw=True)
        fences = re.findall(r"^```[^\n]*\n(.*?)^```", body, re.M | re.S)
        self.assertGreater(len(fences), which,
                           f"`## {title}` has no fenced block #{which}")
        lines = fences[which].splitlines()
        self.assertTrue(lines, f"the fenced block of `## {title}` is empty")
        return lines


class TheFileIsThere(DocTest):
    def test_the_file_exists_under_the_kickoff_skill(self):
        self.assertTrue(os.path.isfile(LEDGER), f"{LEDGER} is missing")

    def test_every_section_the_checks_cut_on_is_still_there(self):
        for title in SECTIONS:
            with self.subTest(section=title):
                self.section(title)

    def test_the_opening_separates_this_file_from_resume(self):
        head = re.search(r"^# .*?\n\n(.*?)\n\n", self.text, re.S)
        self.assertIsNotNone(head, "LEDGER.md lost its opening block")
        opening = flat(head.group(1))
        self.assertIn("RESUME.md", opening)
        self.assertIn("GENERATION", opening)
        self.assertIn("LANE", opening,
                      "the opening names the other file without saying what THIS one "
                      "resumes, so a reader picks whichever they read last")

    def test_the_ledger_is_the_packages_and_the_handoff_is_the_items(self):
        """One sentence, and it carries three claims: whose the ledger is, whose the
        handoff is, and that the queue still has a single writer. Dropping the third
        turns a format file into a licence to write the queue."""
        self.assertIn("the PACKAGE's", self.flat)
        self.assertIn("handoff is the ITEM's", self.flat)
        self.assertIn("single-writer rule does not change", self.flat,
                      "the queue's writer rule is not restated, and a file about "
                      "package-wide state is exactly where a reader would assume it "
                      "had been relaxed")


class TheEventLine(DocTest):
    def format_line(self):
        lines = self.fence("The event line")
        self.assertEqual(len(lines), 1,
                         f"the format block is {len(lines)} lines — the event line is "
                         f"one line, and a block of several is a second format")
        return lines[0]

    def test_the_format_line_carries_the_seven_fields_in_order(self):
        cells = [c.strip() for c in self.format_line().split("|")]
        self.assertEqual(cells, list(FIELDS),
                         "the format line no longer writes the seven fields in the "
                         "order the prose names them")

    def test_every_field_is_described_under_its_own_metavariable(self):
        body = self.section("The event line")
        for field, phrase in FIELDS.items():
            with self.subTest(field=field):
                self.assertIn(f"**`{field}`**", body,
                              f"{field} is in the format line and nowhere in the "
                              f"prose — a reader has the slot and not the question "
                              f"it answers")
                self.assertIn(phrase, body,
                              f"{field}'s own rule is gone; the bullet survives as a "
                              f"label")

    def test_the_line_is_appended_and_never_edited(self):
        body = self.section("The event line")
        self.assertIn("appended, never edited once written", body,
                      "without it the ledger becomes a summary, and a summary cannot "
                      "be differenced for the rate the quota section computes")


class TheHourIsRead(DocTest):
    def test_the_hour_comes_from_date(self):
        self.assertIn("read from `date`, never counted in the head", self.flat)
        self.assertIn("date '+%H:%M'", self.flat,
                      "the rule is stated without the command that satisfies it")

    def test_the_file_says_what_an_estimated_hour_cost(self):
        self.assertIn("Four lines", self.flat)
        self.assertIn("an hour wrong", self.flat,
                      "the measurement behind the rule is gone, and a rule with no "
                      "cost behind it reads as a preference")
        self.assertIn("difference between two hours", self.flat,
                      "the file does not say WHY a wrong hour is worse than a wrong "
                      "label: it is the input of the rate, not decoration")


class TheQuotaField(DocTest):
    def test_the_two_lines_are_written_as_tk_quota_prints_them(self):
        body = self.section("The quota field: a reading and a floor are not the same claim")
        for word in quota_words():
            with self.subTest(word=word):
                self.assertIn(word.strip(), body,
                              f"tk-quota prints {word.strip()!r} and the ledger's "
                              f"example does not carry it — the example has forked "
                              f"from the bin it tells the reader to paste")

    def test_the_nature_and_the_anchors_age_are_required_on_the_line(self):
        body = self.section("The quota field: a reading and a floor are not the same claim")
        for term in ("a READING", "a FLOOR", "the anchor's AGE"):
            with self.subTest(term=term):
                self.assertIn(term, body)

    def test_a_bare_percentage_is_refused(self):
        body = self.section("The quota field: a reading and a floor are not the same claim")
        self.assertIn("A bare number in this field is refused", body)
        self.assertIn("8%", body,
                      "the refusal is stated without the reading that earned it — one "
                      "1h25m old said 8% against an account near 70%")

    def test_the_rate_is_recalibrated_from_this_file(self):
        body = self.section("The quota field: a reading and a floor are not the same claim")
        self.assertIn("recalibrated per package FROM this file", body)
        self.assertIn("50-65 pp/h", body,
                      "the starting rate is unnamed, so the first package has nothing "
                      "to put in the line before it has two lines to difference")


class TheStateTable(DocTest):
    def test_the_table_has_a_row_per_lane_and_is_rewritten_in_place(self):
        body = self.section("The state table")
        self.assertIn("One row per lane, rewritten in place", body)
        self.assertIn("history", body,
                      "without the contrast, a reader appends state rows and the "
                      "table stops being the present")

    def test_the_four_states_are_named_in_order(self):
        body = self.section("The state table")
        found = [s for s in STATES if f"**{s}**" in body]
        self.assertEqual(found, list(STATES),
                         f"the states named are {found} — the four are what the "
                         f"orchestrator answers 'who is standing' with")

    def test_the_verdict_word_is_taken_from_the_review_contract(self):
        """The colours live in `REVIEW-CONTRACT.md`, which reads them off
        `reference/vista.md`'s five verdicts. A ledger minting its own would be a
        third vocabulary for one fact."""
        body = self.section("The state table")
        self.assertIn("REVIEW-CONTRACT.md", body)
        self.assertIn("rather than minting one of its own", body)


class TheLaneRestart(DocTest):
    def block(self):
        return self.fence("The lane restart")

    def test_the_prompt_fits_fifteen_lines(self):
        lines = self.block()
        self.assertLessEqual(len(lines), 15,
                             f"the lane restart is {len(lines)} lines — past 15 it has "
                             f"started restating LANE-CONTRACT.md instead of pointing "
                             f"at it")

    def test_the_first_line_says_which_file_resumes_which(self):
        first = self.block()[0]
        self.assertIn("RESUME.md", first)
        self.assertIn("GENERATION", first)
        self.assertIn("LANE", first,
                      "the prompt's own first line is what a pasting reader sees; "
                      "without the distinction the wrong recipe gets pasted")

    def test_the_prompt_carries_slots_and_no_address(self):
        block = "\n".join(self.block())
        for slot in ("<lane>", "<package>", "<branch>", "<items file>",
                     "<ledger file>", "<notes dir>", "<the remaining item ids>"):
            with self.subTest(slot=slot):
                self.assertIn(slot, block,
                              f"{slot} is not a slot — an address deleted rather than "
                              f"parameterised leaves the prompt reading complete and "
                              f"dispatching to nothing")

    def test_the_prompt_points_at_the_contract_instead_of_repeating_it(self):
        block = "\n".join(self.block())
        self.assertIn("LANE-CONTRACT.md", block)
        self.assertIn("tk-contract --role lane-implementer", block,
                      "the contract block is generated per run; a prompt that does "
                      "not name the role gets none")

    def test_the_prompt_reconstructs_nothing(self):
        body = self.section("The lane restart")
        self.assertIn("reconstructs nothing", body)
        block = "\n".join(self.block())
        for command in ("git log --oneline", "git status --porcelain"):
            with self.subTest(command=command):
                self.assertIn(command, block,
                              f"{command} is what the prompt reads the lane's state "
                              f"back with; without it the run rebuilds the state by "
                              f"asking, and there is nobody to ask")

    def test_the_prompt_neither_merges_nor_recreates_the_worktree(self):
        block = "\n".join(self.block())
        self.assertIn("Do not recreate it and do not reset it", block,
                      "a reset discards exactly the pushed work the restart exists "
                      "to continue from")
        self.assertIn("Never merge", block)


class TheWindowPointer(DocTest):
    def pointing_lines(self):
        return [line for line in self.window.splitlines() if "LEDGER.md" in line]

    def test_window_points_at_the_file_on_exactly_one_line(self):
        found = self.pointing_lines()
        self.assertEqual(len(found), 1,
                         f"WINDOW.md names LEDGER.md on {len(found)} lines, not one — "
                         f"the budget is one line, and a second copy is a second place "
                         f"to go stale")

    def test_the_pointer_sits_in_the_handoff_step(self):
        step = re.search(r"^2\. \*\*Refresh one handoff\*\*(.*?)(?=^\d\. \*\*)",
                         self.window, re.M | re.S)
        self.assertIsNotNone(step,
                             "WINDOW.md's handoff step lost its heading — the pointer "
                             "check would have nothing to sit inside")
        self.assertIn("LEDGER.md", step.group(1),
                      "the pointer drifted out of the handoff step, which is the one "
                      "place a reader is holding the item's state and needs to be "
                      "told the package's lives elsewhere")

    def test_the_pointer_says_what_the_other_file_owns(self):
        line = self.pointing_lines()[0]
        self.assertIn("PACKAGE", line,
                      "a bare pointer sends the reader to a file without saying which "
                      "question it answers")


if __name__ == "__main__":
    unittest.main()
