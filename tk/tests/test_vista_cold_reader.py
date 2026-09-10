#!/usr/bin/env python3
"""Doc-conformance proof for `../reference/vista.md`'s cold-reader variant.

Run: python3 -m unittest discover -s tk/tests   (stdlib only, no deps)

WHAT THE VARIANT IS. The shape a vista takes when its reader was not in the
session: a long unattended package, read hours later on a phone. Remote Control
shows no statusline and echoes no local command, so every number the session had
on screen is lost unless the page writes it out. The variant is prose in
`vista.md`; what ships is the requirement, and this file is what pins it.

WHAT IS ASSERTED, and what each one costs when it goes:

- **the five requirements are each findable by their own number.** A reader
  writing the page greps this section; a requirement folded into a neighbour's
  paragraph is one nobody writes;
- **the nature of a number is marked in the bins' OWN words.** The marks are read
  out of `../bin/tk-quota` rather than retyped, so the day the bin stops printing
  `estimate` or `at least` this reddens instead of the two forking in silence.
  Confusing a reading with a floor is what put four wrong lines in the ledger of
  06/09/2026;
- **the measurement line is DEFINED here, in lanes**, with its four numbers named.
  A pointer alone resolved to `fleet/SKILL.md` §6, which counts projects: a package
  of thirteen lanes measured there reads one project against one project;
- **§6 is still the project-granularity file that reason rests on.** Asserted
  against `fleet/SKILL.md` itself, so a future fleet that learns the word lane
  reddens this and the decision is retaken rather than inherited;
- **the deviation line is pointed at and not restated.** §6 owns its format;
- **the example page passes `../bin/tk-vista-check`.** The variant adds no marker,
  and the claim that it stays green under the existing gate is worth a run, not an
  argument.

VACUITY GUARD FIRST. Every check cuts a slice on a heading, and a heading that
moved would leave the check reading an empty string and passing. `section()`
asserts its slice non-empty, and the example is greppped for the same five marks
it is supposed to demonstrate — a page that carries the blocks and none of the
variant would otherwise pass the gate and prove nothing.

WHAT IS NOT PROVED HERE. That any close writes a variant, that a ledger existed to
copy a chronology from, or that the numbers on the example are true. The gate does
not read prose, and no fixture can hold a package that ran.
"""

import os
import re
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.join(HERE, os.pardir)
VISTA = os.path.join(PLUGIN, "reference", "vista.md")
FLEET = os.path.join(PLUGIN, "skills", "fleet", "SKILL.md")
QUOTA = os.path.join(PLUGIN, "bin", "tk-quota")
CHECK = os.path.join(PLUGIN, "bin", "tk-vista-check")

SECTION = "The variant for a cold reader"

# The five requirements, by the number the section writes them under. The value is
# a phrase from that requirement's own text: membership is the assertion, so a
# requirement kept as a heading and emptied of its rule still reddens.
REQUIREMENTS = {
    "1": "../bin/tk-context",
    "2": "../skills/kickoff/LEDGER.md",
    "3": "lanes planned",
    "4": "One line per finding",
    "5": "no company name",
}

# The four numbers of the variant's own measurement line.
MEASURES = ("lanes planned", "lanes completed", "wall clock", "peak agents")

# What `fleet/SKILL.md` §6 counts, and the reason the variant defines a line of its
# own instead of pointing at that one.
FLEET_COUNTS = "projects planned × projects completed × wall clock"

# The three words that mark a quota number as a FLOOR rather than a reading. Each
# one is asserted against `../bin/tk-quota` too, so a mark the bin stopped printing
# cannot go on being prescribed here.
FLOOR_MARKS = ("estimate", "at least", "floor from")

# The example: the smallest page that is BOTH a vista and the variant. Written out
# here rather than derived from `../reference/vista-template.html`, for the reason
# `test_tk_vista_check.py`'s own PAGE gives — a fixture cut from the shipped
# template would agree with any defect the template grew.
EXAMPLE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Vista — package T378</title>
<style>
  :root { --bg:#ffffff; --ink:#111111; }
  @media (prefers-color-scheme: dark) { :root { --bg:#111111; --ink:#eeeeee; } }
  body { background:var(--bg); color:var(--ink); }
</style></head>
<body><main>

<ul data-vista-bloco="stats"><li><b>4</b><span>closed</span></li>
<li><b>1</b><span>carried</span></li><li><b>0</b><span>blocked</span></li>
<li><b>0</b><span>discarded</span></li><li><b>1</b><span>queue</span></li></ul>

<section>
  <h2>Quota and context</h2>
  <p>Quota, as <code>tk-quota</code> printed it: <b>5h 63% used, 1h21m left</b> — a reading.
  At the last dispatch it was a floor: <b>5h estimate: at least 91% used, 2h09m left
  (floor from 41% read 1h00m ago, 50 pp/h = 5 Opus x 10)</b>.</p>
  <p>Context, as <code>tk-context</code> printed it: <b>156320 tokens in context</b> — a
  reading, taken at 14:40. The 40k it grew after that is reasoned from the two readings
  before it, not read.</p>
</section>

<section>
  <h2>Chronology</h2>
  <p>One line per event, copied from the package ledger; every hour was read from
  <code>date</code>.</p>
  <ul>
    <li>09:12 | lane-a | implementer | opus/high | dispatched | - | 5h 41% used, 3h02m left</li>
    <li>11:48 | lane-a | implementer | opus/high | returned | PR #106, 3 commits | 5h 63% used,
    1h21m left</li>
    <li>12:30 | (sistema) | - | - | quota wall | two lanes died | 5h estimate: at least 91%
    used, 2h09m left (floor from 41% read 1h00m ago, 50 pp/h = 5 Opus x 10)</li>
  </ul>
</section>

<section>
  <h2>Measurement</h2>
  <p><b>5 lanes planned × 4 lanes completed × 3h20m wall clock × peak agents 4.</b></p>
  <p>Deviation: <code>review: opus→sonnet — mechanical sweep, no judgement in the diff</code>.</p>
</section>

<div data-vista-bloco="cards">
  <article data-vista-card="T378" data-vista-desfecho="open" data-vista-risco="low">
    <h4>T378 — the cold reader's variant of the vista</h4>
    <ul class="verdicts">
      <li data-vista-veredito="tests"><b>Tests</b> — green on the final tree</li>
      <li data-vista-veredito="review"><b>Review</b> — one lens, findings fixed</li>
      <li data-vista-veredito="criterion"><b>Criterion</b> — the claim the proof carries</li>
      <li data-vista-veredito="reversal"><b>Reversal</b> — revert the commit</li>
      <li data-vista-veredito="closure"><b>Closure</b> — Fixes acme/repo#261</li>
    </ul>
    <p><a data-vista-bloco="prova" href="https://github.com/acme/repo/pull/106">proof — PR #106</a></p>
  </article>
</div>

<section>
  <h2>Untreated findings</h2>
  <p>One line per finding, with the lane that met it; none of them entered the queue.</p>
  <ul>
    <li>lane-a — the gate reads no prose, so a variant with an empty section is green.</li>
    <li>lane-c — two lanes wrote one scratchpad and each truncated the other's log.</li>
  </ul>
</section>

<div data-vista-bloco="saldo">4 left the queue, 9 are still in it, this run added 0</div>

</main></body></html>
"""

# What the example has to SHOW, or it demonstrates the blocks and not the variant.
EXAMPLE_MARKS = ("estimate: at least", "read 1h00m ago", "tokens in context",
                 "read from\n  <code>date</code>", "lanes planned", "peak agents",
                 "Deviation:", "Untreated findings")


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def flat(text):
    """`text` with every run of whitespace collapsed to one space.

    The phrases below are prose, wrapped at the file's own column. Asserted against
    the raw text, a check depends on where the wrap fell: a reflow that changes
    nothing reddens, and a rewording that drops the rule stays green when it happens
    to re-wrap the same way.
    """
    return " ".join(text.split())


def quota_estimate_template():
    """The template `../bin/tk-quota` builds its FLOOR line from, read from the bin.

    Retyping its words here would let the two vocabularies fork in silence: the
    variant would go on prescribing a mark the bin no longer prints, and a reader
    following it would write a page whose nature marks match nothing.
    """
    src = read(QUOTA)
    line = re.search(r"return \(f\"(.*?)\"\s*\n\s*f\"(.*?)\"\s*\n\s*f\"(.*?)\"\)", src, re.S)
    assert line, "tk-quota no longer builds its estimate line as three f-strings"
    return " ".join(line.groups())


class DocTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = read(VISTA)
        cls.fleet = flat(read(FLEET))

    def section(self):
        """The body under `## <SECTION>`, up to the next `## ` — asserted non-empty."""
        pattern = re.compile(r"^## " + re.escape(SECTION) + r"\s*$(.*?)(?=^## |\Z)",
                             re.M | re.S)
        found = pattern.search(self.text)
        self.assertIsNotNone(found, f"vista.md has no section {SECTION!r}")
        body = found.group(1).strip()
        self.assertTrue(body, f"section {SECTION!r} is empty — every check below reads it")
        return flat(body)

    def test_the_section_the_checks_cut_on_is_still_there(self):
        self.assertTrue(self.section())

    def test_each_of_the_five_requirements_is_findable_by_its_number(self):
        body = self.section()
        for number, phrase in REQUIREMENTS.items():
            with self.subTest(requirement=number):
                self.assertIn(f"**{number}.", body,
                              f"requirement {number} lost the number a reader greps it by")
                self.assertIn(phrase, body,
                              f"requirement {number} no longer carries {phrase!r}")

    def test_a_number_says_whether_it_was_read_or_estimated(self):
        body = self.section()
        template = quota_estimate_template()
        self.assertIn("NATURE", body, "the variant no longer demands the nature of a number")
        for mark in FLOOR_MARKS:
            with self.subTest(mark=mark):
                self.assertIn(mark, template,
                              "tk-quota no longer prints this mark — the variant is "
                              "prescribing a word nothing produces")
                self.assertIn(mark, body,
                              "the variant lost the mark that separates a floor from a "
                              "reading, which is the confusion it exists to prevent")
        self.assertIn("(read <age> ago)", body,
                      "the variant no longer says how a stale READING announces itself")

    def test_the_measurement_line_is_defined_here_with_its_four_numbers(self):
        body = self.section()
        for number in MEASURES:
            with self.subTest(number=number):
                self.assertIn(number, body,
                              "the variant's measurement line lost one of its four numbers")

    def test_the_variant_points_at_fleet_six_for_the_deviation_line(self):
        body = self.section()
        self.assertIn("../skills/fleet/SKILL.md", body,
                      "the variant no longer says which file the deviation line comes from")
        self.assertIn("deviation line", body)
        # The format itself stays in §6. A variant that spells the line out has
        # forked it, and the two copies drift with nothing going red.
        self.assertNotRegex(body, r"<role>\s*:\s*<default>",
                            "the variant restates the deviation format instead of pointing")

    def test_the_reason_the_variant_defines_its_own_line_is_still_true(self):
        """§6 counts PROJECTS, and the variant's whole case rests on that.

        Asserted against `fleet/SKILL.md` itself: the day the fleet learns the word
        lane, this reddens and someone retakes the decision, instead of the variant
        going on defining a line the file beside it already gives.
        """
        self.assertIn(FLEET_COUNTS, self.fleet,
                      "fleet/SKILL.md §6 no longer counts projects — re-decide whether "
                      "the variant still needs a measurement line of its own")
        self.assertNotIn(" lane ", self.fleet,
                         "fleet/SKILL.md now knows the word lane — the variant's "
                         "measurement line may be its §6's job now")

    def test_the_variant_keeps_the_five_blocks_and_adds_no_marker(self):
        body = self.section()
        self.assertNotRegex(body, r"data-vista-(?!bloco=\"|card=\"|desfecho=\")",
                            "the variant invents a marker no checker reads")
        self.assertIn("tk-vista-check", body,
                      "the variant no longer says which gate reads a variant page")


class ExampleTest(unittest.TestCase):
    """One page written to the variant, put through the real gate as a subprocess.

    The exit code is the assertion, because that number is what a close reads
    across a process boundary — the same reason `test_tk_vista_check.py` drives
    the script instead of importing it.
    """

    def test_the_example_carries_the_variant_and_not_only_the_blocks(self):
        for mark in EXAMPLE_MARKS:
            with self.subTest(mark=mark):
                self.assertIn(mark, EXAMPLE,
                              "the example stopped demonstrating the variant, so the "
                              "run below would prove the five blocks alone")

    def test_the_gate_accepts_the_example(self):
        with tempfile.TemporaryDirectory(prefix="tk-vista-cold.") as tmp:
            path = os.path.join(tmp, "vista-T378-2026-09-09.html")
            with open(path, "w", encoding="utf-8") as f:
                f.write(EXAMPLE)
            r = subprocess.run([sys.executable, CHECK, path],
                               capture_output=True, text=True)
        self.assertEqual(r.returncode, 0,
                         f"the gate refused the variant example:\n{r.stdout}{r.stderr}")


if __name__ == "__main__":
    unittest.main()
