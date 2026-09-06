#!/usr/bin/env python3
"""Regression suite for `tk-prune-measure` (../bin/tk-prune-measure).

Run: python3 -m unittest discover -s tk/tests   (stdlib only, no deps)

Every test here is proved by MUTATION — `mutations_prune.py` beside it puts each
defect back and requires the test named for it to fall. A test that still passes
with the guard removed protects nothing.

The suite drives the real script as a SUBPROCESS and reads the numbers off its
OUTPUT, because the output is the whole product: a caller assembling a baseline
table reads the text or the JSON across a process boundary, and a symbolic
assertion on a Python function would leave the layout, the `n/a` marking and the
exit code unproved.

TWO KINDS OF FIXTURE live in `fixtures/prune/`, and the difference is the point.
The seven skill directories are files on disk with values counted BY HAND — the
bloated one carries a 51-word sentence, three dates, forty negations and five
defined terms, one of them repeated in the sibling beside it, and each of those
numbers was verified against the file before any of it ran. Tests that probe one
rule at a time write a small file into a temporary directory instead, so that
the rule under test is the only thing in the file.

`third-party/SKILL.md` is a VERBATIM copy of a skill from the `mattpocock-skills`
plugin (MIT; `NOTICE.md` beside it carries the attribution). It is not edited to
suit this bin, deliberately: a fixture adjusted to agree with the measurement
would agree with any defect the measurement grew.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
BIN = os.path.join(HERE, os.pardir, "bin", "tk-prune-measure")
FIXTURES = os.path.join(HERE, "fixtures", "prune")

# Every metric's label in the text report, so a test can name a metric once and
# read it out of either format. Derived from the bin's own row order by reading
# it here would be circular; this list is written out and the two are compared
# in `TestTextAndJsonAgree`.
LABELS = {
    "lines": "lines",
    "body_words": "body words",
    "sentences": "sentences",
    "mean_sentence_words": "mean words per sentence",
    "max_sentence_words": "max words in a sentence",
    "sentences_over_30": "sentences over 30 words",
    "description_words": "description words",
    "inline_evidence": "inline evidence",
    "narrated_outcomes": "narrated outcomes",
    "pointers": "pointers to other files",
    "negations": "negations",
    "defined_terms": "defined terms",
    "terms_defined_in_sibling": "terms defined in a sibling too",
    "environment_copies": "environment copies",
}


class MeasureTest(unittest.TestCase):
    def setUp(self):
        self.tmp = os.path.realpath(tempfile.mkdtemp(prefix="tk-prune-test."))
        self.addCleanup(shutil.rmtree, self.tmp, True)

    # -- driving the bin ---------------------------------------------------
    def run_on(self, *args):
        return subprocess.run([sys.executable, BIN, *args],
                              capture_output=True, text=True)

    def fixture(self, name, file="SKILL.md"):
        return os.path.join(FIXTURES, name, file)

    def write(self, text, name="SKILL.md", subdir=""):
        """One markdown file in a directory of its own, so the sibling scan sees
        only what the test put there."""
        directory = os.path.join(self.tmp, subdir) if subdir else self.tmp
        os.makedirs(directory, exist_ok=True)
        path = os.path.join(directory, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return path

    # -- reading the numbers back ------------------------------------------
    def metrics(self, path, *flags):
        """The metric table as the TEXT report prints it."""
        r = self.run_on(path, *flags)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        out = {}
        for key, label in LABELS.items():
            m = re.search(rf"^{re.escape(label)}\s{{2,}}(\S+)", r.stdout, re.MULTILINE)
            self.assertIsNotNone(m, f"no row for {label!r} in:\n{r.stdout}")
            out[key] = m.group(1)
        return out

    def report(self, path, *flags):
        """The whole report, as JSON."""
        r = self.run_on(path, "--json", *flags)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return json.loads(r.stdout)

    def metrics_of(self, text, **kwargs):
        """The metrics of a file written for this test alone."""
        return self.report(self.write(text, **kwargs))["metrics"]

    def assertMetric(self, text, key, value, **kwargs):
        self.assertEqual(self.metrics_of(text, **kwargs)[key], value)


# A file that sits under every target, used wherever a test needs one rule
# changed and everything else quiet.
QUIET = """---
name: quiet
description: "Use when a test needs a file that carries no finding of its own."
---

The steps below run in order.
"""


class TestTheBloatedFixture(MeasureTest):
    """Every metric against the fixture whose values were counted by hand."""

    def setUp(self):
        super().setUp()
        self.m = self.report(self.fixture("bloated"))["metrics"]

    def test_lines_count_the_whole_file_frontmatter_included(self):
        with open(self.fixture("bloated"), encoding="utf-8") as f:
            self.assertEqual(self.m["lines"], len(f.read().splitlines()))

    def test_body_words_exclude_the_frontmatter(self):
        self.assertEqual(self.m["body_words"], 437)

    def test_the_sentence_count_is_the_one_the_sentence_unit_produces(self):
        self.assertEqual(self.m["sentences"], 57)

    def test_the_mean_is_the_body_words_over_the_sentences(self):
        self.assertEqual(self.m["mean_sentence_words"],
                         round(self.m["body_words"] / self.m["sentences"], 1))

    def test_the_longest_sentence_is_the_fifty_one_word_one(self):
        self.assertEqual(self.m["max_sentence_words"], 51)

    def test_one_sentence_runs_past_thirty_words(self):
        self.assertEqual(self.m["sentences_over_30"], 1)

    def test_the_description_is_measured_apart_from_the_body(self):
        self.assertEqual(self.m["description_words"], 35)

    def test_every_kind_of_inline_evidence_is_found(self):
        self.assertEqual(self.m["inline_evidence"], 6)     # 3 dates, 2 measured, 1 count

    def test_the_four_pointers_are_found(self):
        self.assertEqual(self.m["pointers"], 4)

    def test_all_forty_negations_are_found(self):
        self.assertEqual(self.m["negations"], 40)

    def test_the_five_defined_terms_are_found(self):
        self.assertEqual(self.m["defined_terms"], 5)

    def test_the_one_term_the_sibling_defines_too_is_found(self):
        self.assertEqual(self.m["terms_defined_in_sibling"], 1)


class TestTheLeanFixture(MeasureTest):
    def test_a_file_built_to_the_targets_passes_every_one_of_them(self):
        marks = self.report(self.fixture("lean"), "--targets")["targets"]
        self.assertTrue(marks)
        over = [m["metric"] for m in marks if m["status"] != "ok"]
        self.assertEqual(over, [], f"{over} missed a target the fixture was built to hit")


class TestTheSentenceUnit(MeasureTest):
    """A full stop is half the rule; the other half is the end of a line that
    carries an instruction. `dispatch` measures 51 words per sentence without
    it, because a table row almost never ends in a full stop."""

    def test_a_table_row_ends_a_sentence_at_the_end_of_its_line(self):
        m = self.report(self.fixture("tabular"))["metrics"]
        self.assertEqual(m["sentences"], 10)
        self.assertEqual(m["max_sentence_words"], 21)

    def test_two_table_rows_are_two_sentences_though_neither_ends_in_a_full_stop(self):
        self.assertMetric(QUIET + "\n| a b c | d |\n| e f | g |\n", "sentences", 3)

    def test_a_list_item_ends_a_sentence_at_the_end_of_its_line(self):
        self.assertMetric(QUIET + "\n- one two three\n- four five\n", "sentences", 3)

    def test_a_heading_ends_a_sentence_at_the_end_of_its_line(self):
        self.assertMetric(QUIET + "\n## One two three\nfour five\n", "sentences", 3)

    def test_a_wrapped_paragraph_is_one_sentence_across_its_lines(self):
        self.assertMetric(QUIET.replace("The steps below run in order.\n", "")
                          + "\none two three\nfour five six.\n", "sentences", 1)

    def test_a_blank_line_ends_a_sentence_that_never_got_a_full_stop(self):
        self.assertMetric(QUIET.replace("The steps below run in order.\n", "")
                          + "\none two\n\nthree four\n", "sentences", 2)

    def test_a_full_stop_inside_a_list_item_still_splits_it(self):
        # three: the one QUIET carries, and the two this list item holds
        self.assertMetric(QUIET + "\n- One two. Three four.\n", "sentences", 3)

    def test_an_abbreviation_does_not_end_a_sentence(self):
        self.assertMetric(QUIET.replace("The steps below run in order.\n", "")
                          + "\nRead the docs, e.g. the README, before you start.\n",
                          "sentences", 1)

    def test_each_abbreviation_of_the_list_is_honoured(self):
        # named one by one: switching the WHOLE check off is one mutation, and it
        # leaves every individual member free to vanish unnoticed
        for abbrev in ("e.g.", "i.e.", "etc.", "vs.", "cf.", "Dr.", "Prof.",
                       "Fig.", "approx.", "et al.", "St."):
            with self.subTest(abbrev=abbrev):
                self.assertMetric(f"See the note {abbrev} before you start today.\n",
                                  "sentences", 1, name=f"{abbrev.strip('.')}.md")

    def test_an_initial_ends_a_sentence_so_enumerated_steps_stay_apart(self):
        # the other side of that trade: exempting a single letter merged
        # "Run step A. Run step B." into one sentence, and steps are what a
        # skill is made of while `J. R. R.` is not
        self.assertMetric("Run step A. Run step B. Run step C.\n", "sentences", 3)

    def test_a_decimal_point_does_not_end_a_sentence(self):
        self.assertMetric(QUIET.replace("The steps below run in order.\n", "")
                          + "\nThe ratio was 3.5 against the baseline.\n", "sentences", 1)

    def test_the_table_separator_row_is_not_a_sentence(self):
        self.assertMetric(QUIET + "\n| a |\n|---|\n| b |\n", "sentences", 3)

    def test_an_em_dash_alone_is_not_a_word(self):
        self.assertMetric(QUIET.replace("The steps below run in order.\n", "")
                          + "\none — two\n", "body_words", 2)

    def test_a_full_stop_inside_bold_ends_the_sentence_it_closes(self):
        """The stop the author wrote is the stop the author meant, whatever
        emphasis closes over it. Written `**… .**`, the period is followed by an
        asterisk instead of a space, and the two sentences either side of it
        were counted as ONE — seen on a legitimate draft (T209), which rose from
        20 long sentences to 22 and came back only when the period was moved
        outside the bold."""
        self.assertMetric(QUIET.replace("The steps below run in order.\n", "")
                          + "\n**The gate refuses it.** The next step runs.\n",
                          "sentences", 2)

    def test_a_full_stop_inside_bold_does_not_inflate_the_long_sentence_counts(self):
        """The count is not the damage; the two numbers riding on it are. Joined,
        the pair below reads as one 32-word sentence and marks
        `sentences_over_30`."""
        text = (QUIET.replace("The steps below run in order.\n", "")
                + "\n**" + "word " * 16 + "stop.** " + "word " * 15 + "end.\n")
        m = self.metrics_of(text)
        self.assertEqual(m["sentences"], 2)
        self.assertEqual(m["sentences_over_30"], 0)
        self.assertEqual(m["max_sentence_words"], 17)

    def test_a_full_stop_inside_italics_ends_the_sentence_too(self):
        self.assertMetric(QUIET.replace("The steps below run in order.\n", "")
                          + "\n_The gate refuses it._ The next step runs.\n",
                          "sentences", 2)

    def test_a_full_stop_inside_a_code_span_does_not_end_a_sentence(self):
        """The emphasis markers close over PROSE and the stop inside them is the
        author's; a backtick closes over CODE, where a trailing dot belongs to
        the token — `git log.` names a command, not a sentence. The bin cannot
        tell one from the other, so the marker it does not follow is the one
        whose contents are not prose."""
        self.assertMetric(QUIET.replace("The steps below run in order.\n", "")
                          + "\nRun `git log.` and read what it prints.\n",
                          "sentences", 1)

    def test_a_stop_before_bold_that_opens_the_next_sentence_still_splits(self):
        # the run of markers after the stop is optional, not required
        self.assertMetric(QUIET.replace("The steps below run in order.\n", "")
                          + "\nThe gate refuses it. **The next step runs.**\n",
                          "sentences", 2)


class TestTheChunkBoundary(MeasureTest):
    """A hard-break line is a chunk of its own on BOTH sides. Flushing only after
    it glued the first bullet of a list to the paragraph above whenever no blank
    line separated them — which CommonMark does not require."""

    # no full stop on the lead line: with one, the split separates it from the
    # bullet anyway and the merge leaves no trace in any number
    LEAD = "The rows below are the palette\n"
    LIST = "- one two three four five six seven eight nine ten\n- eleven twelve\n"

    def test_a_list_measures_the_same_with_and_without_a_blank_line_before_it(self):
        spaced = self.metrics_of(self.LEAD + "\n" + self.LIST, name="spaced.md")
        tight = self.metrics_of(self.LEAD + self.LIST, name="tight.md")
        self.assertEqual(spaced["sentences"], tight["sentences"])
        self.assertEqual(spaced["max_sentence_words"], tight["max_sentence_words"])

    def test_the_first_bullet_is_its_own_sentence_though_no_blank_line_precedes_it(self):
        self.assertMetric("prose line\n- one two three\n- four five\n", "sentences", 3)

    def test_a_heading_straight_after_a_paragraph_does_not_swallow_it(self):
        self.assertMetric("prose line\n## A heading\nmore prose\n", "sentences", 3)


class TestSentenceLineNumbers(MeasureTest):
    """The line a sentence is reported on is the line its first WORD sits on —
    pointing a reader at the wrong line is the one thing the section must not do."""

    LONG = " ".join(f"w{i}" for i in range(32)) + "."

    def test_a_sentence_opening_a_line_is_reported_on_that_line(self):
        # QUIET is six lines, then a blank, then `First.` on 8 and the long one on 9
        report = self.report(self.write(QUIET + "\nFirst.\n" + self.LONG + "\n"))
        self.assertEqual([e["line"] for e in report["long_sentences"]], [9])

    def test_a_sentence_opening_a_chunk_keeps_its_own_line(self):
        report = self.report(self.write(QUIET + "\n" + self.LONG + "\n"))
        self.assertEqual([e["line"] for e in report["long_sentences"]], [8])

    def test_a_last_sentence_with_no_full_stop_keeps_its_line_too(self):
        # the tail of a chunk leaves `split_sentences` by its own path, and that
        # path needs the same whitespace walk as the punctuated one
        report = self.report(self.write(QUIET + "\nFirst.\n" + self.LONG.rstrip(".") + "\n"))
        self.assertEqual([e["line"] for e in report["long_sentences"]], [9])


class TestWhatIsNotCounted(MeasureTest):
    def test_the_frontmatter_is_outside_every_body_count(self):
        m = self.report(self.fixture("code-block"))["metrics"]
        self.assertEqual(m["body_words"], 12)

    def test_a_backtick_fenced_block_is_outside_every_count(self):
        m = self.report(self.fixture("code-block"))["metrics"]
        self.assertEqual(m["sentences"], 2)
        self.assertEqual(m["negations"], 0)      # "Never run this" sits in the fence

    def test_a_tilde_fenced_block_is_outside_every_count(self):
        m = self.report(self.fixture("code-block"))["metrics"]
        self.assertEqual(m["inline_evidence"], 0)   # a date and a count sit in the fence
        self.assertEqual(m["defined_terms"], 0)     # a bold definition sits in the fence

    def test_a_fence_closes_only_on_one_at_least_as_long_as_it_opened_with(self):
        text = QUIET + "\n````\n```\nnever\n````\n\nafter the block\n"
        self.assertMetric(text, "negations", 0)

    def test_a_block_left_unclosed_runs_to_the_end_of_the_file(self):
        self.assertMetric(QUIET + "\n```\nnever\nno\n", "negations", 0)

    def test_an_inline_code_span_does_not_open_a_block(self):
        # ```echo hi``` is one line of inline code, not a fence: read as an
        # opener it closes on nothing and swallows the rest of the file
        text = QUIET + "\n```echo hi```\n\nAfter it, never skip step two.\n"
        self.assertMetric(text, "negations", 1)

    def test_a_tilde_fence_may_carry_backticks_in_its_info_string(self):
        # the CommonMark clause is about BACKTICK fences only
        self.assertMetric(QUIET + "\n~~~ `x`\nnever\n~~~\n", "negations", 0)

    def test_a_fence_with_text_after_it_does_not_close_a_block(self):
        self.assertMetric(QUIET + "\n```\nnever\n``` and more\nno\n```\n",
                          "negations", 0)

    def test_a_file_that_opens_with_a_rule_and_never_closes_it_keeps_its_body(self):
        # not frontmatter: refusing this would measure the whole file as empty
        self.assertMetric("---\n\none two three\n", "body_words", 3)

    def test_frontmatter_closed_with_a_yaml_document_end_is_frontmatter(self):
        self.assertMetric("---\nname: x\ndescription: one two three four\n...\n\n"
                          "body text here\n", "description_words", 4)

    def test_a_file_with_no_frontmatter_is_measured_all_the_same(self):
        m = self.report(self.fixture("no-frontmatter"))["metrics"]
        self.assertEqual(m["body_words"], 32)

    def test_an_empty_file_measures_zero_of_everything(self):
        m = self.report(self.fixture("empty"))["metrics"]
        self.assertEqual(m["lines"], 0)
        self.assertEqual(m["sentences"], 0)
        self.assertEqual(m["mean_sentence_words"], 0.0)
        self.assertEqual(m["max_sentence_words"], 0)


class TestTheDescription(MeasureTest):
    def test_a_quoted_description_counts_the_words_between_the_quotes(self):
        # the quotes are left where they are: neither holds an alphanumeric, so
        # neither is a word, and stripping them could not change this number
        self.assertMetric('---\nname: x\ndescription: "one two three"\n---\n\nbody\n',
                          "description_words", 3)

    def test_an_unquoted_description_is_counted_the_same(self):
        self.assertMetric("---\nname: x\ndescription: one two three\n---\n\nbody\n",
                          "description_words", 3)

    def test_a_description_wrapped_over_indented_lines_is_counted_whole(self):
        self.assertMetric("---\nname: x\ndescription: one two\n  three four\n---\n\nbody\n",
                          "description_words", 4)

    def test_a_block_scalar_marker_is_not_a_word_of_the_description(self):
        self.assertMetric("---\nname: x\ndescription: >-\n  one two\n---\n\nbody\n",
                          "description_words", 2)

    def test_a_key_after_the_description_ends_it(self):
        self.assertMetric("---\ndescription: one two\nname: three four five\n---\n\nbody\n",
                          "description_words", 2)

    def test_a_description_key_with_no_value_is_absent(self):
        # not a description of zero words: counted as 0 it scored the BEST
        # possible mark against a ceiling of 30, so a missing context pointer
        # came back as the tidiest one in the set
        self.assertIsNone(self.metrics_of("---\nname: x\ndescription:\n---\n\nbody\n")
                          ["description_words"])
        marks = {m["metric"]: m for m in
                 self.report(self.write("---\nname: x\ndescription:\n---\n\nbody\n"),
                             "--targets")["targets"]}
        self.assertEqual(marks["description_words"]["status"], "n/a")

    def test_a_file_with_no_frontmatter_reports_the_description_as_absent(self):
        # absent, never zero: the bin measures any markdown, and a runbook has none
        self.assertIsNone(self.report(self.fixture("no-frontmatter"))
                          ["metrics"]["description_words"])

    def test_an_absent_description_is_marked_n_a_rather_than_passing_its_target(self):
        marks = self.report(self.fixture("no-frontmatter"), "--targets")["targets"]
        mark = [m for m in marks if m["metric"] == "description_words"][0]
        self.assertEqual(mark["status"], "n/a")


class TestDefinedTerms(MeasureTest):
    def test_the_article_form_is_a_definition(self):
        self.assertMetric(QUIET + "\nA **dispatch line** is the command.\n",
                          "defined_terms", 1)

    def test_the_form_with_means_is_a_definition(self):
        self.assertMetric(QUIET + "\nA **palette row** means one situation.\n",
                          "defined_terms", 1)

    def test_the_house_form_without_an_article_is_a_definition(self):
        self.assertMetric(QUIET + "\n**Pruning** is subtraction.\n", "defined_terms", 1)

    def test_bold_and_a_colon_opening_a_line_is_a_definition(self):
        self.assertMetric(QUIET + "\n**Session finding**: what a session learned.\n",
                          "defined_terms", 1)

    def test_bold_and_a_colon_inside_a_list_item_opens_that_line_too(self):
        self.assertMetric(QUIET + "\n- **Session finding**: what a session learned.\n",
                          "defined_terms", 1)

    def test_bold_in_the_middle_of_a_line_is_not_a_definition(self):
        self.assertMetric(QUIET + "\nRead it and **then**: start.\n", "defined_terms", 0)

    def test_a_term_defined_in_a_sibling_of_the_same_directory_is_reported(self):
        self.write("**Session finding**: what a session learned.\n",
                   name="REFERENCE.md", subdir="skill")
        path = self.write(QUIET + "\n**Session finding**: what a session learned.\n",
                          subdir="skill")
        report = self.report(path)
        self.assertEqual(report["metrics"]["terms_defined_in_sibling"], 1)
        self.assertEqual(report["terms_defined_in_sibling"][0]["also_in"], ["REFERENCE.md"])

    def test_a_sibling_that_defines_the_term_twice_is_named_once(self):
        """The counter counts the TARGET's terms, so it never saw this; the
        finding did, and named one file twice — `also in b.md, b.md` reports
        two files that do not exist."""
        self.write("# B\n\n**Widget**: a thing.\n\n**Widget**: and again.\n",
                   name="b.md")
        found = self.report(self.write("# A\n\n**Widget**: a thing.\n")
                            )["terms_defined_in_sibling"]
        self.assertEqual([e["also_in"] for e in found], [["b.md"]])

    def test_the_sibling_comparison_ignores_case(self):
        self.write("**Session FINDING**: what a session learned.\n",
                   name="REFERENCE.md", subdir="skill")
        path = self.write(QUIET + "\n**session finding**: what a session learned.\n",
                          subdir="skill")
        self.assertEqual(self.report(path)["metrics"]["terms_defined_in_sibling"], 1)

    def test_a_term_defined_once_in_its_own_file_is_not_reported_as_shared(self):
        self.write("nothing defined here\n", name="REFERENCE.md", subdir="skill")
        path = self.write(QUIET + "\n**Session finding**: what a session learned.\n",
                          subdir="skill")
        self.assertEqual(self.report(path)["metrics"]["terms_defined_in_sibling"], 0)

    def test_a_term_defined_inside_a_siblings_code_block_does_not_count(self):
        self.write("```\n**Session finding**: what a session learned.\n```\n",
                   name="REFERENCE.md", subdir="skill")
        path = self.write(QUIET + "\n**Session finding**: what a session learned.\n",
                          subdir="skill")
        self.assertEqual(self.report(path)["metrics"]["terms_defined_in_sibling"], 0)

    def test_a_sibling_symlinked_out_of_the_directory_is_not_read(self):
        # the name makes it look like a sibling; the bin reads the directory it
        # was pointed at, and a symlink out of it is not that directory
        outside = self.write("**API_KEY** is the token.\n", name="secret.md",
                             subdir="elsewhere")
        path = self.write(QUIET + "\n**API_KEY** is the token.\n", subdir="skill")
        os.symlink(outside, os.path.join(self.tmp, "skill", "leak.md"))
        self.assertEqual(self.report(path)["metrics"]["terms_defined_in_sibling"], 0)

    def test_a_sibling_symlinked_within_the_directory_is_read(self):
        # both names are asserted: with only the count, the real file behind the
        # link answers for it and a containment check that refused every symlink
        # would still pass
        real = self.write("**Session finding**: what a session learned.\n",
                          name="real.md", subdir="skill")
        path = self.write(QUIET + "\n**Session finding**: what a session learned.\n",
                          subdir="skill")
        os.symlink(real, os.path.join(self.tmp, "skill", "REFERENCE.md"))
        shared = self.report(path)["terms_defined_in_sibling"]
        self.assertEqual(shared[0]["also_in"], ["REFERENCE.md", "real.md"])

    def test_a_sibling_that_is_not_markdown_is_not_read(self):
        self.write("**Session finding**: what a session learned.\n",
                   name="notes.txt", subdir="skill")
        path = self.write(QUIET + "\n**Session finding**: what a session learned.\n",
                          subdir="skill")
        self.assertEqual(self.report(path)["metrics"]["terms_defined_in_sibling"], 0)


class TestTheKitIsTheUniverse(MeasureTest):
    """The sibling scan over a PLUGIN, where a term is coined one skill away.

    The metric read the target's own directory and stopped there, so
    **generation**, redefined by `dispatch` against `kickoff/WINDOW.md`, scored
    zero and only a cold review found it (#219). A kit is recognised by the
    marker a plugin carries, `.claude-plugin/plugin.json`, and every skill
    markdown under it joins the target's own directory in the comparison.
    """

    def kit(self, layout, marker=True):
        """A plugin on disk — {relative path: text} — and its root."""
        root = os.path.join(self.tmp, "kit")
        if marker:
            os.makedirs(os.path.join(root, ".claude-plugin"), exist_ok=True)
            with open(os.path.join(root, ".claude-plugin", "plugin.json"),
                      "w", encoding="utf-8") as f:
                f.write('{"name": "kit"}\n')
        for relative, text in layout.items():
            full = os.path.join(root, relative)
            os.makedirs(os.path.dirname(full), exist_ok=True)
            with open(full, "w", encoding="utf-8") as f:
                f.write(text)
        return root

    def test_a_term_defined_in_another_skill_of_the_kit_is_reported(self):
        """The case of #219: restricted to the directory this is 0."""
        root = self.kit({
            "skills/alpha/SKILL.md": QUIET + "\n**Generation** is one dispatch.\n",
            "skills/kickoff/WINDOW.md": "**Generation** is one dispatch.\n",
        })
        report = self.report(os.path.join(root, "skills", "alpha", "SKILL.md"))
        self.assertEqual(report["metrics"]["terms_defined_in_sibling"], 1)
        self.assertEqual(report["terms_defined_in_sibling"][0]["also_in"],
                         ["skills/kickoff/WINDOW.md"])

    def test_two_skill_files_of_the_same_name_are_told_apart_by_their_path(self):
        root = self.kit({
            "skills/alpha/SKILL.md": QUIET + "\n**Generation** is one dispatch.\n",
            "skills/beta/SKILL.md": "**Generation** is one dispatch.\n",
            "skills/gamma/SKILL.md": "**Generation** is one dispatch.\n",
        })
        report = self.report(os.path.join(root, "skills", "alpha", "SKILL.md"))
        self.assertEqual(report["terms_defined_in_sibling"][0]["also_in"],
                         ["skills/beta/SKILL.md", "skills/gamma/SKILL.md"])

    def test_the_only_definition_in_the_whole_kit_is_not_reported(self):
        root = self.kit({
            "skills/alpha/SKILL.md": QUIET + "\n**Generation** is one dispatch.\n",
            "skills/beta/SKILL.md": "nothing defined here\n",
        })
        path = os.path.join(root, "skills", "alpha", "SKILL.md")
        self.assertEqual(self.report(path)["metrics"]["terms_defined_in_sibling"], 0)

    def test_a_kit_file_that_is_not_a_skill_keeps_its_own_directory(self):
        """The universe is the kit's SKILLS. A reference page, a fixture or a
        test file under the same plugin is measured as it always was — against
        its own directory, by basename — and the kit's skills never reach it."""
        root = self.kit({
            "reference/queue.md": QUIET + "\n**Generation** is one dispatch.\n",
            "reference/session-finding.md": "**Generation** is one dispatch.\n",
            "skills/alpha/SKILL.md": "**Handoff** is a briefing.\n",
        })
        report = self.report(os.path.join(root, "reference", "queue.md"))
        self.assertEqual(report["terms_defined_in_sibling"][0]["also_in"],
                         ["session-finding.md"])

    def test_a_skill_of_the_kit_never_collides_with_a_file_outside_skills(self):
        root = self.kit({
            "reference/queue.md": "**Generation** is one dispatch.\n",
            "skills/alpha/SKILL.md": QUIET + "\n**Generation** is one dispatch.\n",
        })
        path = os.path.join(root, "skills", "alpha", "SKILL.md")
        self.assertEqual(self.report(path)["metrics"]["terms_defined_in_sibling"], 0)

    def test_a_kit_file_symlinked_out_of_the_kit_is_not_read(self):
        """The boundary moved from the directory to the kit; it did not go."""
        outside = self.write("**API_KEY** is the token.\n", name="secret.md",
                             subdir="elsewhere")
        root = self.kit({
            "skills/alpha/SKILL.md": QUIET + "\n**API_KEY** is the token.\n",
            "skills/beta/SKILL.md": "nothing defined here\n",
        })
        os.symlink(outside, os.path.join(root, "skills", "beta", "leak.md"))
        path = os.path.join(root, "skills", "alpha", "SKILL.md")
        self.assertEqual(self.report(path)["metrics"]["terms_defined_in_sibling"], 0)

    def test_a_kit_file_symlinked_to_another_skill_is_read_once(self):
        """Both names reach the same real file, and the finding names it once —
        the count alone would pass on a guard that refused every symlink."""
        root = self.kit({
            "skills/alpha/SKILL.md": QUIET + "\n**Generation** is one dispatch.\n",
            "skills/beta/SKILL.md": "**Generation** is one dispatch.\n",
        })
        os.symlink(os.path.join(root, "skills", "beta", "SKILL.md"),
                   os.path.join(root, "skills", "gamma.md"))
        report = self.report(os.path.join(root, "skills", "alpha", "SKILL.md"))
        self.assertEqual(report["metrics"]["terms_defined_in_sibling"], 1)
        self.assertEqual(report["terms_defined_in_sibling"][0]["also_in"],
                         ["skills/beta/SKILL.md"])

    def test_the_measured_file_is_not_its_own_sibling_under_a_second_name(self):
        root = self.kit({
            "skills/alpha/SKILL.md": QUIET + "\n**Generation** is one dispatch.\n",
        })
        os.symlink(os.path.join(root, "skills", "alpha", "SKILL.md"),
                   os.path.join(root, "skills", "mirror.md"))
        path = os.path.join(root, "skills", "alpha", "SKILL.md")
        self.assertEqual(self.report(path)["metrics"]["terms_defined_in_sibling"], 0)

    def test_a_target_under_no_kit_measures_by_its_own_directory_and_no_error(self):
        root = self.kit({
            "skills/alpha/SKILL.md": QUIET + "\n**Generation** is one dispatch.\n",
            "skills/beta/SKILL.md": "**Generation** is one dispatch.\n",
        }, marker=False)
        path = os.path.join(root, "skills", "alpha", "SKILL.md")
        r = self.run_on(path, "--json")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(json.loads(r.stdout)["metrics"]["terms_defined_in_sibling"], 0)


class TestUnpunctuatedRuns(MeasureTest):
    """The table rule, in the other constructs that carry one item per line and
    no full stop. A block of link definitions measured 536 words as one sentence
    on a real CHANGELOG before these breaks existed."""

    def test_a_block_of_link_definitions_is_one_sentence_each(self):
        text = (QUIET + "\n[a]: https://example.com/a\n"
                "[b]: https://example.com/b\n[c]: https://example.com/c\n")
        self.assertMetric(text, "sentences", 4)

    def test_a_setext_underline_ends_the_line_above_it(self):
        self.assertMetric(QUIET + "\nA Title\n=======\nthen prose\n", "sentences", 3)

    def test_a_thematic_break_ends_the_line_above_it(self):
        self.assertMetric(QUIET + "\nsome prose\n***\nmore prose\n", "sentences", 3)

    def test_a_wrapped_paragraph_is_still_not_cut_at_its_line_breaks(self):
        # the general rule "an unpunctuated line ends a sentence" would do this,
        # and it is the commoner error
        self.assertMetric("one two three\nfour five six.\n", "sentences", 1)


class TestInlineEvidence(MeasureTest):
    def test_an_iso_date_is_evidence(self):
        self.assertMetric(QUIET + "\nThe sweep ran on 2026-06-03.\n", "inline_evidence", 1)

    def test_the_word_measured_is_evidence(self):
        # WITH the measurement it names. The bare word was evidence until T284:
        # it is also how a skill writes the rule about evidence, and
        # `TestEvidenceInBothDirections` carries that case
        self.assertMetric(QUIET + "\nThe gap was measured at 12 words.\n",
                          "inline_evidence", 1)

    def test_a_count_followed_by_times_is_evidence(self):
        self.assertMetric(QUIET + "\nThe refusal fired 5 times.\n", "inline_evidence", 1)

    def test_a_count_followed_by_before_is_evidence(self):
        self.assertMetric(QUIET + "\nIt broke 3 before the fix landed.\n",
                          "inline_evidence", 1)

    def test_a_bare_number_is_not_evidence(self):
        self.assertMetric(QUIET + "\nPick 5 rows from the palette.\n", "inline_evidence", 0)

    def test_the_evidence_is_listed_in_the_order_a_reader_reads_it(self):
        # the three rules are scanned one after another, so without the sort a
        # date on a later line is listed before a `measured` on an earlier one
        text = QUIET + "\nThe gap was measured at 12 words.\nThe sweep ran on 2026-06-03.\n"
        report = self.report(self.write(text))
        self.assertEqual([e["line"] for e in report["inline_evidence"]], [8, 9])

    def test_each_hit_names_the_kind_it_matched(self):
        report = self.report(self.fixture("bloated"))
        self.assertEqual(sorted({e["kind"] for e in report["inline_evidence"]}),
                         ["count", "iso date", "measured"])


class TestEvidenceInBothDirections(MeasureTest):
    """The inline-evidence counter missed in BOTH directions on one file, and
    the two misses are the two cases below (T284).

    The pruning pass over `verify/SKILL.md` (2026-08-31) read `inline evidence 1`
    where the file held the opposite of that number: the one it counted was the
    bare word in ordinary prose, and the one piece of real evidence — a clause
    narrating what happened the one time a minimal fixture was trusted — it never
    saw. A pass cannot decide what leaves a file on a counter that wrong.

    THE TWO CASES ANSWER ON DIFFERENT ROWS, and that is the fix rather than a
    dodge. `inline_evidence` carries a ceiling of zero, so what enters it is a
    verdict; a narrated outcome is a shape a regex can find and cannot weigh —
    `A criterion passed only because a reflow refilled its line` is a war story
    and `an item the ladder had placed third` is a rule — so it is REPORTED with
    its line, beside the negations, and marked against nothing.
    """

    FALSE_POSITIVE = ("The one thing that reaches the user is what was **measured**, which is why the criterion travels intact.")
    FALSE_NEGATIVE = ("Run the criterion against the shape the data really has: a criterion read as satisfied on a minimal fixture has passed while the same command failed on the populated form.")

    def test_the_word_measured_alone_is_not_inline_evidence(self):
        """The false positive: prose about what a report must carry, holding no
        measurement of its own."""
        self.assertMetric(QUIET + "\n" + self.FALSE_POSITIVE + "\n",
                          "inline_evidence", 0)

    def test_the_word_measured_beside_a_number_is_inline_evidence(self):
        self.assertMetric(QUIET + "\nThe gap was measured at 12 words.\n",
                          "inline_evidence", 1)

    def test_the_word_measured_beside_a_date_is_inline_evidence(self):
        # two findings on the line: the date is one of its own
        self.assertMetric(QUIET + "\nMeasured against the tree of 2026-08-31.\n",
                          "inline_evidence", 2)

    def test_a_clause_narrating_what_happened_is_reported(self):
        """The false negative: no date, no count, no `measured` — a perfect
        tense, which is how prose stops instructing and starts recounting."""
        report = self.report(self.write(QUIET + "\n" + self.FALSE_NEGATIVE + "\n"))
        self.assertEqual(report["metrics"]["narrated_outcomes"], 1)
        self.assertEqual(report["narrated_outcomes"][0]["match"], "has passed")
        self.assertIn("minimal fixture", report["narrated_outcomes"][0]["context"])

    def test_a_rule_in_the_present_tense_is_not_a_narrated_outcome(self):
        # `restored` is a participle and the sentence still instructs: what
        # separates the two is the auxiliary in front of it, not the ending
        self.assertMetric(QUIET + "\nA criterion that passes with the defect "
                          "restored proves nothing.\n", "narrated_outcomes", 0)

    def test_a_participle_belonging_to_a_noun_is_not_a_narrated_outcome(self):
        # `has an encoding proposed` — two words between the auxiliary and the
        # participle, and the participle belongs to the noun. Real line, from
        # `wrap-up/SKILL.md`
        self.assertMetric(QUIET + "\nEvery finding has an encoding proposed "
                          "by the close.\n", "narrated_outcomes", 0)

    def test_the_two_cases_of_the_verify_file_are_green_side_by_side(self):
        """The regression the item asks for: both sentences in one file, each
        answering on its own row and neither answering on the other's."""
        m = self.metrics_of(QUIET + "\n" + self.FALSE_POSITIVE
                            + "\n\n" + self.FALSE_NEGATIVE + "\n")
        self.assertEqual(m["inline_evidence"], 0)
        self.assertEqual(m["narrated_outcomes"], 1)

    def test_a_narrated_outcome_is_marked_against_no_target(self):
        """Reported, never marked: which perfect tense recounts a run and which
        one states a rule is the reader's call, and a target that fails
        `writing-for-agents` is not a target."""
        marked = {m["metric"] for m in
                  self.report(self.write(QUIET + "\n" + self.FALSE_NEGATIVE + "\n"),
                              "--targets")["targets"]}
        self.assertNotIn("narrated_outcomes", marked)

    def test_the_text_report_lists_the_narrated_outcomes_with_their_lines(self):
        out = self.run_on(self.write(QUIET + "\n" + self.FALSE_NEGATIVE + "\n"),
                          ).stdout
        self.assertIn("narrated outcomes (1)", out)
        self.assertIn("has passed", out)


class TestTheEnvironmentBoundary(MeasureTest):
    """What the bin may run, and what it may not do when the run goes wrong.

    `scan_environment` reads a tool's `--help` out of a SUBPROCESS, which is the
    only place this bin leaves its own process. Both cases below were found by
    the cold review of the lane that added it.
    """

    def setUp(self):
        super().setUp()
        self.bin = os.path.join(self.tmp, "bin")
        os.makedirs(self.bin)
        previous = os.environ.get("TK_PRUNE_BIN")
        os.environ["TK_PRUNE_BIN"] = self.bin
        self.addCleanup(self.restore_bin, previous)

    def restore_bin(self, previous):
        if previous is None:
            os.environ.pop("TK_PRUNE_BIN", None)
        else:
            os.environ["TK_PRUNE_BIN"] = previous

    def tool(self, name, source):
        path = os.path.join(self.bin, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(source)
        os.chmod(path, 0o755)
        return path

    def test_a_help_that_is_not_utf8_is_measured_rather_than_traced_back(self):
        """The bin promises to exit 0 for every measurement. A help carrying a
        byte the locale cannot decode raised inside `subprocess.run`, and a
        `UnicodeDecodeError` is a `ValueError` — it passed every `except` on the
        way out and the whole run ended in a traceback."""
        self.tool("tk-badhelp",
                  "#!/usr/bin/env python3\n"
                  "import sys\n"
                  "sys.stdout.buffer.write(b'usage: tk-badhelp [-h]\\n\\n"
                  "refuses \\xff an empty mandatory field\\n')\n")
        r = self.run_on(self.write(QUIET + "\n- `tk-badhelp <id>` refuses an "
                                           "empty mandatory field.\n"))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("Traceback", r.stderr)

    def test_only_a_subcommand_the_usage_names_reaches_the_subprocess(self):
        """The allowlist of `kit_tools` covers the EXECUTABLE. The prefetch sent
        `argv[1]` straight from the markdown, so a file writing a tool name
        followed by `rmdash` ran that tool with an argument no author of this
        kit ever wrote.

        Both directions in ONE assertion: `done` is in the tool's own braced
        usage and its help is read, `rmdash` is not and never runs. A test that
        only forbade would pass on a bin that stopped passing arguments at all.
        """
        log = os.path.join(self.tmp, "argv.log")
        self.tool("tk-probe",
                  "#!/usr/bin/env python3\n"
                  "import sys\n"
                  "open(%r, 'a').write(' '.join(sys.argv[1:]) + chr(10))\n"
                  "sys.stdout.write('usage: tk-probe [-h] {done,list} ...\\n')\n"
                  % log)
        self.run_on(self.write(QUIET + "\n- run `tk-probe rmdash` and it "
                                       "refuses an empty mandatory field.\n"
                                       "- run `tk-probe done` and it refuses "
                                       "an empty mandatory field.\n"))
        with open(log, encoding="utf-8") as f:
            ran = sorted(line.split() for line in f.read().splitlines())
        self.assertEqual(ran, [["--help"], ["done", "--help"]])


class TestPointers(MeasureTest):
    def test_a_home_relative_path_is_a_pointer(self):
        # extensionless on purpose: a path carrying `.md` is found by the other
        # branch too, and would pass with this one gone
        self.assertMetric(QUIET + "\nRun `~/.claude/skills/tk/bin/tk-queue` first.\n",
                          "pointers", 1)

    def test_a_parent_relative_path_is_a_pointer(self):
        self.assertMetric(QUIET + "\nThen `../reference/vista.md`.\n", "pointers", 1)

    def test_a_bare_filename_with_a_known_extension_is_a_pointer(self):
        self.assertMetric(QUIET + "\nThe harness is `mutations_prune.py`.\n", "pointers", 1)

    def test_a_repo_relative_path_with_no_dot_prefix_is_a_pointer(self):
        self.assertMetric(QUIET + "\nThe suite lives in `tk/tests/test_x.py`.\n",
                          "pointers", 1)

    def test_a_slashed_word_that_is_not_a_path_is_not_a_pointer(self):
        self.assertMetric(QUIET + "\nEach row is KEEP/MOVE/DROP and nothing else.\n",
                          "pointers", 0)

    def test_a_long_run_of_dotted_text_measures_promptly(self):
        # the extension used to sit inside the pattern, where `.` was in the star
        # AND in the literal before it: 16 000 dots took 3.6 s, and a longer line
        # never came back. The timeout IS the assertion.
        path = self.write(QUIET + "\n" + "a." * 40000 + "zz\n")
        r = subprocess.run([sys.executable, BIN, path, "--json"],
                           capture_output=True, text=True, timeout=20)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(json.loads(r.stdout)["metrics"]["pointers"], 0)

    def test_a_url_is_not_a_pointer_to_a_file_in_this_tree(self):
        self.assertMetric(QUIET + "\nSee https://example.com/a/b.md for the rest.\n",
                          "pointers", 0)


class TestNegations(MeasureTest):
    def test_do_not_is_counted_once_and_reported_whole(self):
        # the count alone cannot tell the two apart — both are one hit — so the
        # MATCH is what this asserts: a reader judging the line needs the phrase
        report = self.report(self.write(QUIET + "\nTargets do not judge.\n"))
        self.assertEqual(report["metrics"]["negations"], 1)
        self.assertEqual(report["negations"][0]["match"], "do not")

    def test_the_contraction_is_counted_once(self):
        self.assertMetric(QUIET + "\nDon't commit the output directory.\n", "negations", 1)

    def test_no_inside_a_longer_word_is_not_a_negation(self):
        self.assertMetric(QUIET + "\nThe note names nobody in particular.\n", "negations", 0)

    def test_every_negation_is_listed_with_the_line_it_sits_on(self):
        # a count alone would be a verdict the regex cannot support: `never`
        # steering an agent and `never` naming an outcome look identical to it
        report = self.report(self.fixture("bloated"))
        self.assertEqual(len(report["negations"]), 40)
        for entry in report["negations"]:
            self.assertTrue(entry["context"], entry)
            self.assertGreater(entry["line"], 0)

    def test_a_long_line_is_reported_as_a_window_around_the_match(self):
        # AROUND the match: a window cut at an offset the whitespace collapse
        # already moved is still short, and still does not hold the negation
        long_line = "word  " * 60 + "never here.\n"
        report = self.report(self.write(QUIET + "\n" + long_line))
        context = report["negations"][0]["context"]
        self.assertLessEqual(len(context), 102)
        self.assertIn("never", context)


class TestEnvironmentCopies(MeasureTest):
    """Prose that caches the `--help` of a tool it names (T293).

    The environment is the source of truth and a sentence repeating it grows a
    second copy to keep in sync. It is the class with the highest recurrence the
    pruning track measured: six of the twelve clauses one pass cut off `verify`
    were this, and whole sections of `kickoff`.

    THE FIXTURE OWNS ITS HELP. `TK_PRUNE_BIN` points the resolution at a stub
    written here, so these numbers do not move when the real tool grows a flag —
    and so the proof by mutation exists at all: editing the stub's help must
    unmark the sentence that copies it.

    The blocks are the pre-pruning `verify/SKILL.md`'s own steps, wrapped the
    way that file wraps them.
    """

    STUB = '#!/usr/bin/env python3\n"""A stand-in for the queue gate, so the fixture measures a help it owns."""\nimport sys\n\nHANDOFF = (\n    "usage: tk-queue handoff [-h] --objective OBJECTIVE --state STATE id\\n\\n"\n    "write the item briefing\\n\\n"\n    "options:\\n"\n    "  --objective OBJECTIVE  where this front is going\\n"\n    "  --state STATE          what is done and decided\\n\\n"\n    "An empty mandatory field is refused, and the file is deleted when the item closes.\\n")\n\nHELP = {\n    (): "usage: tk-queue [-h] {done,handoff,release,edit} ...\\n\\n"\n        "tk-queue - the gate over a project queue.\\n",\n    ("handoff",): HANDOFF,\n    ("done",): "usage: tk-queue done [-h] [--dir DIR] --how HOW [--note NOTE] "\n               "[--force] id\\n\\nconclude the item\\n",\n    ("release",): "usage: tk-queue release [-h] id\\n\\nhand the item back\\n",\n    ("edit",): "usage: tk-queue edit [-h] [--force] id\\n\\nchange an open item\\n",\n}\n\nif __name__ == "__main__":\n    argv = tuple(a for a in sys.argv[1:] if a != "--help")\n    sys.stdout.write(HELP.get(argv, HELP[()]))\n'
    CLAUSE = 'An empty mandatory field is refused, and the file is deleted when the item closes.'

    # invocation whole on the opening line, description wrapped under it
    STEP_ONE = ("- Write the briefing with the script — `tk-queue handoff <id> "
                '--objective "..." --state "..."`.\n'
                "  It writes the file beside the queue files, refuses a briefing\n"
                "  whose mandatory fields are empty, and is what makes it deleted\n"
                "  when the item closes.\n")
    # the same step with its invocation BROKEN across the line, as the real file
    # wraps it: the code span opens on one line and closes on the next
    WRAPPED = ("- Write the briefing with the script — `tk-queue handoff <id>\n"
               '  --objective "..."`. It writes the file beside the queue files,\n'
               "  refuses a briefing whose mandatory fields are empty, and is\n"
               "  what makes it deleted when the item closes.\n")
    DONE = ('- `tk-queue done <id> --how "..." --force` — `--how` is required, and\n'
            "  `--force` raises the ceiling without removing it, so that form\n"
            "  keeps the output to a single line.\n")
    NAMED_ONLY = ('- `tk-queue done <id> --how "..."` — the pointer to the delivery goes\n'
                  "  in `--how`, and the outcome goes in front of it.\n")
    NO_TOOL = ("- It writes the file beside the queue files, refuses a briefing\n"
               "  whose mandatory fields are empty, and is what makes it deleted\n"
               "  when the item closes.\n")
    RELEASE = ("- `tk-queue release <id>` when the item was claimed, so the dead\n"
               "  package ownership does not outlive it.\n")
    FORCE = ("- `tk-queue edit <id> --class DECISION` — the `--force` flag is required\n"
             "  where the link would cross the size ceiling of an open row.\n")

    INVOCATION_LINE = 8              # the line a block opens on

    def setUp(self):
        super().setUp()
        self.bin = os.path.join(self.tmp, "bin")
        os.makedirs(self.bin, exist_ok=True)
        self.stub(self.STUB)
        previous = os.environ.get("TK_PRUNE_BIN")
        os.environ["TK_PRUNE_BIN"] = self.bin
        self.addCleanup(self.restore_bin, previous)

    def restore_bin(self, previous):
        if previous is None:
            os.environ.pop("TK_PRUNE_BIN", None)
        else:
            os.environ["TK_PRUNE_BIN"] = previous

    def stub(self, text):
        path = os.path.join(self.bin, "tk-" + "queue")
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        os.chmod(path, 0o755)

    def copies(self, *blocks):
        return self.report(self.write(QUIET + "\n" + "\n".join(blocks))
                           )["environment_copies"]

    def test_a_sentence_restating_the_help_of_the_tool_it_names_is_a_copy(self):
        found = self.copies(self.STEP_ONE)
        self.assertEqual(len(found), 1, found)
        self.assertEqual(found[0]["tool"].split()[-1], "handoff")
        self.assertGreaterEqual(len(found[0]["shared"]), 4)

    def test_the_sentence_that_only_invokes_the_tool_is_not_a_copy(self):
        """The step opens by TYPING the command, and what it types carries the
        help's own words. Held out of the comparison, that sentence describes
        four things and shares two; left in, every call site is a copy."""
        found = self.copies(self.STEP_ONE)
        self.assertEqual(len(found), 1, found)
        self.assertGreater(found[0]["line"], self.INVOCATION_LINE)

    def test_the_tool_is_read_off_a_code_span_broken_across_a_line(self):
        """The real file wraps that invocation, so the span opens on one line
        and closes on the next — a pattern needing both ends reads the two
        halves as neither, and the block resolves to no tool at all."""
        found = self.copies(self.WRAPPED)
        self.assertEqual(len(found), 1, found)
        self.assertEqual(found[0]["tool"].split()[-1], "handoff")

    def test_the_tool_is_inherited_by_the_lines_under_the_one_that_named_it(self):
        found = self.copies(self.STEP_ONE)
        self.assertGreater(found[0]["line"], self.INVOCATION_LINE)

    def test_a_sentence_claiming_an_obligation_the_usage_marks_is_a_copy(self):
        """The second reading: not four stems, one fact. `--how` sits outside
        the brackets of the usage, and the sentence says it is required."""
        found = self.copies(self.DONE)
        self.assertEqual(len(found), 1, found)
        self.assertEqual(found[0]["fact"], "--how required")
        self.assertLess(len(found[0]["shared"]), 4)

    def test_naming_a_required_flag_without_claiming_it_is_not_a_copy(self):
        """The fact is the CLAIM, not the flag: prose may route a reader to
        `--how` without restating what the usage says about it."""
        self.assertEqual(self.copies(self.NAMED_ONLY), [])

    def test_a_flag_the_usage_marks_optional_carries_no_fact(self):
        """The mirror class (#223): the help does NOT know what the prose
        knows, and the metric must not bend to it. `--force` is bracketed."""
        self.assertEqual(self.copies(self.FORCE), [])

    def test_a_sentence_that_only_names_the_tool_is_not_a_copy(self):
        self.assertEqual(self.copies(self.RELEASE), [])

    # ONE SENTENCE OF WRAPPED PROSE, written twice. A list item ends a sentence
    # at the end of its own line, so this case only exists in a paragraph: here
    # the span opens on the sentence's SECOND line, and in `SPAN_FIRST` on its
    # first. Nothing else about the two differs.
    SPAN_LATER = ("The orchestrator writes the briefing with\n"
                  "`tk-queue handoff <id>`, which refuses a briefing whose\n"
                  "mandatory fields are empty and is what makes it deleted\n"
                  "when the item closes.\n")
    SPAN_FIRST = ("`tk-queue handoff <id>` is how the orchestrator writes the\n"
                  "briefing, which refuses a briefing whose mandatory fields are\n"
                  "empty and is what makes it deleted when the item closes.\n")

    def test_a_sentence_is_attributed_by_a_span_of_its_own_after_its_first_line(self):
        """The brief attributes a sentence to the tool named IN THE SENTENCE or
        earlier in the same block. The line map answered only the second half —
        it is keyed by line, and a sentence is filed under the line it OPENS on
        — so one sentence marked with its invocation first and did not with the
        same invocation wrapped onto the line below. That is a difference the
        author's line breaks make and the sentence's meaning does not."""
        later = self.copies(self.SPAN_LATER)
        self.assertEqual([e["tool"].split()[-1] for e in later], ["handoff"])
        self.assertEqual([e["tool"] for e in self.copies(self.SPAN_FIRST)],
                         [e["tool"] for e in later])

    def test_a_later_block_does_not_inherit_the_tool_of_an_earlier_one(self):
        """Two steps of one list, no blank line between them, and the second
        names no tool at all: without the block boundary it would answer for
        the `handoff` of the first, and describe its help word for word."""
        found = self.copies(self.STEP_ONE, self.NO_TOOL)
        self.assertEqual([e["tool"].split()[-1] for e in found], ["handoff"])

    def test_editing_the_help_unmarks_the_sentence_that_copied_it(self):
        """The proof by mutation, run against the ENVIRONMENT rather than the
        code: take the clause out of the stub's help and the sentence stops
        sharing enough of it to be a copy. It is also what proves the fixture
        reads the stub at all rather than the tool installed beside the bin."""
        self.assertEqual(len(self.copies(self.STEP_ONE)), 1)
        self.stub(self.STUB.replace(self.CLAUSE, "It conducts a front."))
        self.assertEqual(self.copies(self.STEP_ONE), [])

    def test_a_tool_the_kit_does_not_carry_is_not_resolved(self):
        """The allowlist is the derived directory: a name the prose invents
        resolves to nothing, and the file measures all the same."""
        m = self.metrics_of(QUIET + "\n"
                            + self.STEP_ONE.replace("tk-queue handoff", "tk-nowhere"))
        self.assertEqual(m["environment_copies"], 0)

    def test_environment_copies_are_marked_against_no_target(self):
        """Listed, never marked: whether a copy should go is the pruning
        table's question, and the mirror class is a different ticket."""
        marked = {m["metric"] for m in
                  self.report(self.write(QUIET + "\n" + self.STEP_ONE),
                              "--targets")["targets"]}
        self.assertNotIn("environment_copies", marked)

    def test_the_text_report_lists_the_copies_with_their_tool(self):
        out = self.run_on(self.write(QUIET + "\n" + self.DONE)).stdout
        self.assertIn("environment copies (1)", out)
        self.assertIn("--how required", out)

    def test_the_criterion_of_the_item_read_over_the_four_steps(self):
        """Criterion A as the brief rewrote it: the environment clauses mark,
        the step that only names does not, and the `--force` one — the mirror
        class — does not either."""
        found = self.copies(self.STEP_ONE, self.DONE, self.RELEASE, self.FORCE)
        self.assertEqual([e["tool"].split()[-1] for e in found],
                         ["handoff", "done"])


class TestTargets(MeasureTest):
    def test_no_target_is_marked_unless_targets_is_asked_for(self):
        self.assertNotIn("targets", self.report(self.fixture("bloated")))

    def test_a_metric_over_its_ceiling_is_marked_over(self):
        marks = {m["metric"]: m for m in
                 self.report(self.fixture("bloated"), "--targets")["targets"]}
        self.assertEqual(marks["max_sentence_words"]["status"], "over")
        self.assertEqual(marks["description_words"]["status"], "over")
        self.assertEqual(marks["inline_evidence"]["status"], "over")
        self.assertEqual(marks["terms_defined_in_sibling"]["status"], "over")

    def test_a_metric_inside_its_ceiling_is_marked_ok(self):
        marks = {m["metric"]: m for m in
                 self.report(self.fixture("bloated"), "--targets")["targets"]}
        self.assertEqual(marks["mean_sentence_words"]["status"], "ok")
        self.assertEqual(marks["sentences_over_30"]["status"], "ok")

    def test_a_value_exactly_on_the_ceiling_passes(self):
        marks = {m["metric"]: m for m in
                 self.report(self.write('---\nname: x\ndescription: "'
                                        + "one " * 30 + '"\n---\n\nbody\n'),
                             "--targets")["targets"]}
        self.assertEqual(marks["description_words"]["value"], 30)
        self.assertEqual(marks["description_words"]["status"], "ok")

    def test_a_metric_the_bin_only_reports_gets_no_target(self):
        # negations and defined terms are report-only on purpose: a target that
        # fails `writing-for-agents` is not a target
        marked = {m["metric"] for m in
                  self.report(self.fixture("bloated"), "--targets")["targets"]}
        self.assertNotIn("negations", marked)
        self.assertNotIn("defined_terms", marked)
        self.assertNotIn("pointers", marked)

    def test_the_text_report_carries_a_status_column_only_with_targets(self):
        plain = self.run_on(self.fixture("lean")).stdout
        marked = self.run_on(self.fixture("lean"), "--targets").stdout
        self.assertNotIn("status", plain)
        self.assertIn("status", marked)

    def test_the_targets_the_bin_carries_are_the_ones_the_house_rule_names(self):
        marks = {m["metric"]: m["target"] for m in
                 self.report(self.fixture("lean"), "--targets")["targets"]}
        self.assertEqual(marks, {"max_sentence_words": 25, "description_words": 30,
                                 "mean_sentence_words": 22, "sentences_over_30": 4,
                                 "inline_evidence": 0, "terms_defined_in_sibling": 0})


class TestTextAndJsonAgree(MeasureTest):
    """`--json` is the same measurement in another shape, never a second one."""

    def each_fixture(self):
        for name in sorted(os.listdir(FIXTURES)):
            path = self.fixture(name)
            if os.path.isfile(path):
                yield name, path

    def test_every_fixture_reports_the_same_numbers_in_both_formats(self):
        for name, path in self.each_fixture():
            with self.subTest(fixture=name):
                text = self.metrics(path)
                data = self.report(path)["metrics"]
                for key, value in data.items():
                    self.assertEqual(text[key], "—" if value is None else str(value),
                                     f"{name}: {key}")

    def test_the_value_column_is_aligned_to_the_longest_label(self):
        # the metric table only: the detail sections below it open with the same
        # labels, and they are not columns
        body = self.run_on(self.fixture("bloated")).stdout.split("---\n", 1)[1]
        rows = [l for l in body.split("\n\n", 1)[0].splitlines() if l.strip()]
        self.assertEqual(len(rows), len(LABELS))
        ends = {len(r.rstrip()) for r in rows}
        self.assertEqual(ends, {max(ends)}, f"ragged value column:\n" + "\n".join(rows))

    def test_the_text_report_carries_a_row_for_every_metric_the_json_carries(self):
        data = self.report(self.fixture("bloated"))["metrics"]
        self.assertEqual(sorted(data), sorted(LABELS))
        self.assertEqual(sorted(self.metrics(self.fixture("bloated"))), sorted(data))

    def test_the_marks_agree_with_the_metrics_they_mark(self):
        report = self.report(self.fixture("bloated"), "--targets")
        for mark in report["targets"]:
            self.assertEqual(mark["value"], report["metrics"][mark["metric"]])


class TestItMeasuresAndDoesNotJudge(MeasureTest):
    def test_a_file_that_misses_every_target_still_exits_zero(self):
        r = self.run_on(self.fixture("bloated"), "--targets")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_an_empty_file_exits_zero(self):
        self.assertEqual(self.run_on(self.fixture("empty")).returncode, 0)

    def test_every_fixture_exits_zero_in_every_format(self):
        for name in sorted(os.listdir(FIXTURES)):
            path = self.fixture(name)
            if not os.path.isfile(path):
                continue
            for flags in ([], ["--targets"], ["--json"], ["--json", "--targets"]):
                with self.subTest(fixture=name, flags=flags):
                    r = self.run_on(path, *flags)
                    self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


class TestUsage(MeasureTest):
    def test_a_path_that_does_not_exist_is_named_rather_than_measured(self):
        r = self.run_on(os.path.join(self.tmp, "nope.md"))
        self.assertEqual(r.returncode, 2)
        self.assertIn("no such file", r.stderr)

    def test_a_directory_is_named_as_a_directory_not_reported_as_an_empty_file(self):
        r = self.run_on(self.tmp)
        self.assertEqual(r.returncode, 2)
        self.assertIn("is a directory", r.stderr)

    def test_a_byte_order_mark_ahead_of_the_frontmatter_still_reads(self):
        path = os.path.join(self.tmp, "bom.md")
        with open(path, "w", encoding="utf-8-sig") as f:
            f.write(QUIET)
        self.assertEqual(self.report(path)["metrics"]["description_words"], 14)

    def test_a_file_that_is_not_utf8_is_measured_rather_than_refused(self):
        # `café` from a Windows editor is measurable markdown. There are two
        # refusals and only two: the path that is not there, and the directory.
        path = os.path.join(self.tmp, "latin1.md")
        with open(path, "wb") as f:
            f.write("---\nname: x\ndescription: d\n---\n\nUm café e um résumé.\n"
                    .encode("latin-1"))
        r = self.run_on(path)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.report(path)["metrics"]["body_words"], 5)

    def test_a_byte_that_is_not_utf8_never_becomes_a_word(self):
        path = os.path.join(self.tmp, "bytes.md")
        with open(path, "wb") as f:
            f.write(b"---\nname: x\ndescription: d\n---\n\none \xff\xfe two\n")
        self.assertEqual(self.report(path)["metrics"]["body_words"], 2)

    def test_the_report_names_the_file_it_measured(self):
        path = self.fixture("lean")
        self.assertIn(path, self.run_on(path).stdout)
        self.assertEqual(self.report(path)["path"], path)


class TestTheFenceIndent(MeasureTest):
    """The margin a fence is measured against is the fence that opened the block,
    not the left edge of the file. Bounded against the edge, a fence carried by a
    list item was neither an opener nor a closer, and its contents were counted as
    prose — one space of indent moved this fixture from 7 body words to 15."""

    BLOCK = "One two three four five six seven.\n\n{indent}```\nnever run this\n{indent}```\n"

    def test_a_fence_at_the_margin_holds_its_block_out_of_the_count(self):
        self.assertMetric(self.BLOCK.format(indent=""), "body_words", 7)

    def test_a_fence_three_spaces_in_holds_its_block_out_of_the_count(self):
        self.assertMetric(self.BLOCK.format(indent="   "), "body_words", 7)

    def test_a_fence_carried_by_a_list_item_holds_its_block_out_of_the_count(self):
        self.assertMetric(self.BLOCK.format(indent="    "), "body_words", 7)

    def test_a_close_indented_far_past_its_opener_does_not_close_the_block(self):
        # three spaces further in is CommonMark's allowance; the eighth is not,
        # and a line that deep is content of the block rather than its end
        text = ("One two three four five six seven.\n\n```\nnever\n"
                "        ```\nno\n```\n")
        self.assertMetric(text, "negations", 0)


class TestTheUnclosedBlock(MeasureTest):
    """A body that stops at a fence is a small number with a cause no metric can
    show. Same-character fences do not nest, so a skill written with a ```markdown
    block around a ```ts one loses everything after the inner block's close — six
    installed skills are written that way, and every renderer breaks them the same.
    The bin follows CommonMark and SAYS the file was cut short."""

    UNCLOSED = QUIET + "\n```\nnever run this\n"

    def test_the_line_the_unclosed_block_opened_on_is_reported(self):
        self.assertEqual(self.report(self.write(self.UNCLOSED))["unclosed_fence"], 8)

    def test_a_file_whose_blocks_all_close_reports_none(self):
        closed = QUIET + "\n```\nnever run this\n```\n"
        self.assertIsNone(self.report(self.write(closed))["unclosed_fence"])

    def test_the_text_report_names_the_line_too(self):
        r = self.run_on(self.write(self.UNCLOSED))
        self.assertIn("the fenced block opened on line 8 is never closed", r.stdout)

    def test_a_file_whose_blocks_all_close_carries_no_note(self):
        r = self.run_on(self.write(QUIET + "\n```\nnever\n```\n"))
        self.assertNotIn("never closed", r.stdout)

    def test_the_bin_still_exits_zero_on_a_file_it_reports_cut_short(self):
        # a note about the reading, not a verdict on the file
        self.assertEqual(self.run_on(self.write(self.UNCLOSED)).returncode, 0)


class TestTheFrontmatterBoundary(MeasureTest):
    """`---` has two readings and the file has to choose one. A block of prose
    between two rules is a document that opens with a thematic break, whatever
    keys the prose happens to name: read as frontmatter it loses its body, and a
    `description:` written in a sentence is harvested as the skill's own."""

    OPENS_WITH_A_RULE = ("---\n\nA paragraph of prose here.\n\n"
                         "description: not the frontmatter one\n\n---\n\n"
                         "More prose after the second rule.\n")

    def test_prose_between_two_rules_stays_in_the_body(self):
        self.assertMetric(self.OPENS_WITH_A_RULE, "body_words", 16)

    def test_a_description_written_in_the_body_is_not_the_frontmatter_one(self):
        self.assertIsNone(self.metrics_of(self.OPENS_WITH_A_RULE)["description_words"])

    def test_an_indented_block_carrying_no_key_is_not_frontmatter(self):
        # every line of it could belong to a mapping and none of them names a
        # key: a mapping with no keys in it is not one
        self.assertMetric("---\n   indented text\n---\n\none two three\n",
                          "body_words", 5)

    def test_a_real_mapping_between_two_rules_is_still_frontmatter(self):
        self.assertMetric("---\nname: x\ndescription: one two three\n---\n\nbody\n",
                          "description_words", 3)

    def test_a_mapping_whose_value_wraps_is_still_frontmatter(self):
        # `>-` holds no alphanumeric, so the block marker is not one of them
        self.assertMetric("---\ndescription: >-\n  one two three four\n---\n\nbody\n",
                          "description_words", 4)

    def test_a_mapping_carrying_a_list_is_still_frontmatter(self):
        self.assertMetric("---\ntags:\n- one\n- two\ndescription: a b\n---\n\nbody\n",
                          "description_words", 2)


class TestTheFrontmatterShapes(MeasureTest):
    """Every shape a real mapping is written in has to pass the gate, and the
    campaign found the gate rejecting two of them. A rejected block is read as
    body prose, delimiters and all — the file's counts move and nothing says why."""

    def test_a_quoted_key_is_a_key(self):
        # the changesets format: 17 of the 165 files on this machine that open
        # with `---` were read as prose while this was bare-word only
        self.assertMetric('---\n"pkg-name": patch\ndescription: one two three\n---\n\nbody\n',
                          "description_words", 3)

    def test_a_quoted_phrase_is_not_a_key(self):
        # the quoted branch admitted any run between two quotes, so a first
        # paragraph opening on a quotation was held out of the body: this case
        # measured 29 body words before the whitespace test and 0 after
        self.assertMetric('---\n"To be, or not to be": that is the question, '
                          'whether tis nobler in the mind\n  to suffer the slings '
                          'and arrows of outrageous fortune or to take arms\n---\n',
                          "body_words", 29)

    def test_a_single_quoted_key_is_a_key_too(self):
        self.assertMetric("---\n'pkg-name': patch\ndescription: one two\n---\n\nbody\n",
                          "description_words", 2)

    def test_a_yaml_comment_does_not_disqualify_the_block(self):
        self.assertMetric("---\n# a normal YAML comment\ndescription: one two three\n"
                          "---\n\nbody\n", "description_words", 3)

    def test_a_blank_line_inside_the_block_does_not_disqualify_it(self):
        # an empty string is not `isspace()`, so without the skip the blank line
        # fails the shape test and the whole frontmatter is read as body
        self.assertMetric("---\nname: x\n\ndescription: one two three four\n---\n\n"
                          "Body prose here now.\n", "description_words", 4)

    def test_a_line_opening_with_a_digit_is_not_a_key(self):
        # `2026-08-27: the day` is prose with a colon in it, and a block holding
        # one is a document that opened with a thematic break
        self.assertMetric("---\n2026-08-27: the day it was measured\n---\n\n"
                          "one two three\n", "body_words", 9)

    def test_the_last_description_wins_when_the_key_is_repeated(self):
        # malformed YAML either way; reporting the shadowed value is reporting a
        # number about a line no loader reads
        self.assertMetric("---\ndescription: first value here\n"
                          "description: the second value that wins\n---\n\nbody\n",
                          "description_words", 5)


class TestWhatIsNotAPointer(MeasureTest):
    """A pointer is a file of this tree. The prefix and suffix tests each admitted
    a whole class that is not one, and this repo's own README carried 21 of them."""

    def test_a_slash_command_is_not_a_pointer(self):
        # `/tk` appears eleven times in this repo's README; a command is a slash
        # and a word, exactly like a one-segment path
        self.assertMetric(QUIET + "\nRun /tk and then /clear before /compact.\n",
                          "pointers", 0)

    def test_a_closing_html_tag_is_not_a_pointer(self):
        self.assertMetric(QUIET + "\nWrite <div>alpha</div> and <b>beta</b> here.\n",
                          "pointers", 0)

    def test_an_absolute_path_of_two_segments_is_still_a_pointer(self):
        self.assertMetric(QUIET + "\nThe file is `/etc/hosts` on this machine.\n",
                          "pointers", 1)

    def test_a_scheme_less_repository_host_is_not_a_pointer(self):
        # it ends in `.md` and it is not a file of this tree; the dot in the
        # segment before the first slash is what says so
        self.assertMetric(QUIET + "\nSee github.com/anthropics/claude-code/README.md now.\n",
                          "pointers", 0)

    def test_a_relative_path_prefix_is_not_a_hostname(self):
        # `./` and `../` put a dot in the segment before the first slash, which
        # is the very thing that marks a host; what says they are not is that
        # the segment's last dot leaves nothing after it
        self.assertMetric(QUIET + "\nRead `./foo.md` and `../bar/baz.md` next.\n",
                          "pointers", 2)

    def test_a_web_address_written_with_www_is_not_prose_either(self):
        # the `www.` branch of WEB_ADDRESS earns its place here rather than in
        # the pointer count: `never` inside a hostname is not a negation
        self.assertMetric(QUIET + "\nSee www.never-mind.com for it.\n", "negations", 0)

    def test_a_repo_relative_path_of_two_segments_is_still_a_pointer(self):
        self.assertMetric(QUIET + "\nThe script is `docs/prune/baseline.py` here.\n",
                          "pointers", 1)

    def test_a_versioned_directory_is_not_a_hostname(self):
        # the dot alone marked a host, and a release directory carries one; the
        # head's last segment has to read as a TLD for the token to be an address
        self.assertMetric(QUIET + "\nSee 3.3.0/CHANGELOG.md and v1.2/notes.md now.\n",
                          "pointers", 2)

    def test_a_single_letter_head_segment_is_not_a_TLD(self):
        # no TLD is one character; a head that short is a path someone wrote
        self.assertMetric(QUIET + "\nThe file is `a.b/config.json` in the tree.\n",
                          "pointers", 1)


class TestTheBlankRole(MeasureTest):
    def test_a_blank_line_ends_a_chunk_by_its_role(self):
        # `classify` decides once what a line is; the chunker reads that decision
        # rather than making the same judgement a second time
        self.assertMetric("First paragraph with no full stop\n\n"
                          "second paragraph with no full stop\n", "sentences", 2)


class TestThematicBreaks(MeasureTest):
    def test_a_dashed_rule_ends_the_line_above_it(self):
        # `---` is the form written by hand; the starred one is a separate
        # alternative of the same pattern and passes with this one gone
        self.assertMetric("Paragraph one\n---\nParagraph two\n", "sentences", 2)

    def test_a_rule_three_spaces_in_ends_the_line_above_it(self):
        self.assertMetric("Paragraph one\n   ***\nParagraph two\n", "sentences", 2)


class TestOneRolePerLine(MeasureTest):
    """Role and prose are two answers about one line, and `classify` gives both at
    once. Seven regexes read independently at ten call sites is what they replaced,
    and the readings had drifted: a construct that ended a sentence at one site did
    not give up its marker at another."""

    def test_a_definition_opening_a_table_cell_is_a_definition(self):
        # the cells are split apart, so a term opening one opens the text
        # `defined_terms` reads; left as one row it opens nothing
        report = self.report(self.write(QUIET + "\n| **Lens**: a subagent | one |\n"))
        self.assertEqual(report["metrics"]["defined_terms"], 1)

    def test_a_table_row_carried_by_a_list_item_gives_up_both_markers(self):
        # the list marker comes off FIRST and the row is read in what is left:
        # one of the two strips alone leaves the cells joined
        report = self.report(self.write(QUIET + "\n- | **Lens**: a subagent | one |\n"))
        self.assertEqual(report["metrics"]["defined_terms"], 1)

    def test_a_quoted_heading_ends_a_sentence_like_any_heading(self):
        self.assertMetric("> # A quoted heading\nAnd prose under it\n", "sentences", 2)


class TestTheContextWindow(MeasureTest):
    def test_a_repeated_negation_is_windowed_at_its_own_occurrence(self):
        # the window used to be cut around the FIRST occurrence of the matched
        # token, so every later `never` on a long line showed the same context
        line = ("alpha " * 20 + "FIRST never beta " + "gamma " * 20
                + "SECOND never delta")
        found = self.report(self.write(QUIET + "\n" + line + "\n"))["negations"]
        self.assertEqual(len(found), 2)
        self.assertIn("FIRST", found[0]["context"])
        self.assertIn("SECOND", found[1]["context"])
        self.assertNotIn("FIRST", found[1]["context"])

    def test_a_line_carrying_thousands_of_negations_measures_promptly(self):
        # the line was collapsed once PER MATCH: 12 000 of them took 10 s, and a
        # report nobody waits for is a report nobody runs. The timeout IS the
        # assertion.
        path = self.write(QUIET + "\nx " + "not " * 12000 + "end.\n")
        r = subprocess.run([sys.executable, BIN, path, "--json"],
                           capture_output=True, text=True, timeout=20)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(json.loads(r.stdout)["metrics"]["negations"], 12000)


class TestTheWindowItself(MeasureTest):
    """The width and the two ellipsis marks are what make a window a window. Each
    survived mutation until it was named here."""

    def negation_on_a_long_line(self, before, after):
        line = "alpha " * before + "never " + "omega " * after
        return self.report(self.write(QUIET + "\n" + line + "\n"))["negations"][0]

    def test_a_window_cut_from_a_long_line_is_a_hundred_characters(self):
        found = self.negation_on_a_long_line(30, 30)
        body = found["context"].strip("…")
        self.assertEqual(len(body), 100)

    def test_a_window_that_starts_inside_the_line_opens_with_an_ellipsis(self):
        self.assertTrue(self.negation_on_a_long_line(30, 30)["context"].startswith("…"))

    def test_a_window_that_reaches_the_head_of_the_line_carries_no_opening_ellipsis(self):
        # the match sits at the front, so there is nothing to the left to elide
        self.assertFalse(self.negation_on_a_long_line(0, 40)["context"].startswith("…"))

    def test_a_window_that_stops_short_of_the_end_closes_with_an_ellipsis(self):
        self.assertTrue(self.negation_on_a_long_line(30, 30)["context"].endswith("…"))

    def test_a_window_that_reaches_the_end_of_the_line_carries_no_closing_ellipsis(self):
        self.assertFalse(self.negation_on_a_long_line(40, 0)["context"].endswith("…"))


class TestWhatIsAPointer(MeasureTest):
    """The suffix list and the prefix list are each one branch of the same test,
    and a branch nothing exercises is a branch nobody can tell is gone."""

    def test_an_absolute_path_with_no_extension_is_a_pointer(self):
        # the `/` prefix is the only branch that admits it: `hosts` is no suffix
        self.assertMetric(QUIET + "\nThe file is `/etc/hosts` on this machine.\n",
                          "pointers", 1)

    def test_every_extension_the_bin_knows_makes_a_pointer(self):
        for suffix in ("md", "py", "sh", "json", "html", "txt", "yml", "yaml", "toml"):
            with self.subTest(suffix=suffix):
                self.assertMetric(QUIET + f"\nRead `config.{suffix}` first.\n",
                                  "pointers", 1)

    def test_an_extension_written_in_capitals_is_a_pointer_too(self):
        self.assertMetric(QUIET + "\nRead `README.MD` first.\n", "pointers", 1)

    def test_a_bare_word_spelt_like_an_extension_is_not_a_pointer(self):
        # without the dot test the tail of a dotless token is the token itself,
        # and the word `md` in a sentence becomes a file
        self.assertMetric(QUIET + "\nThe files are md and nothing else.\n",
                          "pointers", 0)

    def test_a_token_longer_than_any_filename_is_not_a_pointer(self):
        # a run of punctuation the shape happens to admit, reported as a path,
        # puts a screenful where the report shows one line
        self.assertMetric(QUIET + "\n" + "a." * 200 + "md\n", "pointers", 0)


class TestTheShippedSkills(MeasureTest):
    """The bin runs on this plugin's own skills — the baseline in `docs/prune/`
    is exactly this call, and a bin that cannot read a real skill has no
    baseline to produce."""

    def shipped(self):
        skills = os.path.join(HERE, os.pardir, "skills")
        return sorted(os.path.join(root, name)
                      for root, _, names in os.walk(skills)
                      for name in names if name.endswith(".md"))

    def test_every_skill_of_this_plugin_measures_without_a_refusal(self):
        found = self.shipped()
        self.assertGreaterEqual(len(found), 7, found)
        for path in found:
            with self.subTest(skill=path):
                m = self.report(path)["metrics"]
                self.assertGreater(m["body_words"], 0)

    def test_the_table_heavy_skill_does_not_measure_as_one_enormous_sentence(self):
        """`dispatch` is the real file the sentence unit exists for: its palette
        is one table, its rows carry no full stop, and by the punctuation rule
        alone it measures over 50 words per sentence. This is that claim held
        against the shipped file rather than against a fixture built to show it."""
        m = self.report(os.path.join(HERE, os.pardir, "skills", "dispatch",
                                     "SKILL.md"))["metrics"]
        self.assertLess(m["mean_sentence_words"], 25)


if __name__ == "__main__":
    unittest.main()
