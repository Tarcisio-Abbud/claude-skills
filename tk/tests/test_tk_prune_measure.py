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
    "pointers": "pointers to other files",
    "negations": "negations",
    "defined_terms": "defined terms",
    "terms_defined_in_sibling": "terms defined in a sibling too",
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

    def test_a_decimal_point_does_not_end_a_sentence(self):
        self.assertMetric(QUIET.replace("The steps below run in order.\n", "")
                          + "\nThe ratio was 3.5 against the baseline.\n", "sentences", 1)

    def test_the_table_separator_row_is_not_a_sentence(self):
        self.assertMetric(QUIET + "\n| a |\n|---|\n| b |\n", "sentences", 3)

    def test_an_em_dash_alone_is_not_a_word(self):
        self.assertMetric(QUIET.replace("The steps below run in order.\n", "")
                          + "\none — two\n", "body_words", 2)


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

    def test_a_file_that_opens_with_a_rule_and_never_closes_it_keeps_its_body(self):
        # not frontmatter: refusing this would measure the whole file as empty
        self.assertMetric("---\n\none two three\n", "body_words", 3)

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

    def test_a_sibling_that_is_not_markdown_is_not_read(self):
        self.write("**Session finding**: what a session learned.\n",
                   name="notes.txt", subdir="skill")
        path = self.write(QUIET + "\n**Session finding**: what a session learned.\n",
                          subdir="skill")
        self.assertEqual(self.report(path)["metrics"]["terms_defined_in_sibling"], 0)


class TestInlineEvidence(MeasureTest):
    def test_an_iso_date_is_evidence(self):
        self.assertMetric(QUIET + "\nThe sweep ran on 2026-06-03.\n", "inline_evidence", 1)

    def test_the_word_measured_is_evidence(self):
        self.assertMetric(QUIET + "\nThe gap was measured against the tree.\n",
                          "inline_evidence", 1)

    def test_a_count_followed_by_times_is_evidence(self):
        self.assertMetric(QUIET + "\nThe refusal fired 5 times.\n", "inline_evidence", 1)

    def test_a_count_followed_by_before_is_evidence(self):
        self.assertMetric(QUIET + "\nIt broke 3 before the fix landed.\n",
                          "inline_evidence", 1)

    def test_a_bare_number_is_not_evidence(self):
        self.assertMetric(QUIET + "\nPick 5 rows from the palette.\n", "inline_evidence", 0)

    def test_each_hit_names_the_kind_it_matched(self):
        report = self.report(self.fixture("bloated"))
        self.assertEqual(sorted({e["kind"] for e in report["inline_evidence"]}),
                         ["count", "iso date", "measured"])


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
        long_line = "word " * 60 + "never here.\n"
        report = self.report(self.write(QUIET + "\n" + long_line))
        self.assertLessEqual(len(report["negations"][0]["context"]), 102)


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

    def test_a_file_that_is_not_text_is_named_rather_than_raising(self):
        # the third refusal, beside the absent path and the directory: a file
        # with nothing measurable in it is named, not handed back as a traceback
        path = os.path.join(self.tmp, "binary.md")
        with open(path, "wb") as f:
            f.write(b"---\nname: x\n---\n\n\xff\xfe not text\n")
        r = self.run_on(path)
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("unreadable", r.stderr)

    def test_the_report_names_the_file_it_measured(self):
        path = self.fixture("lean")
        self.assertIn(path, self.run_on(path).stdout)
        self.assertEqual(self.report(path)["path"], path)


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
