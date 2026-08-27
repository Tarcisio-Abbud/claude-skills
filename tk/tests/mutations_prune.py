#!/usr/bin/env python3
"""Mutation harness for the `tk-prune-measure` suite — puts each defect back.

Run: python3 tk/tests/mutations_prune.py

Same contract as its siblings: each entry restores one defect in a COPY of `tk/`,
runs only the tests named for it, and requires each of them to fail. A mutation
that SURVIVES is a hole in the suite, not a pass.

This file holds entries only. The runner is `mutations_tk_contract.run`, which
takes the test module, the entry list and the default source as arguments. It
also enumerates the suite and reports any test NO entry names (UNPROVED) — the
half a score of N/N cannot show, because N counts the mutants someone wrote.

WHAT A GREEN SCORE HERE DOES NOT SAY. The bin reads prose, and prose is an
unbounded input: every entry below proves that a rule the suite already names is
load-bearing, and none of them can find the markdown shape nobody thought of.
Two were found that way while this slice was being written — a description whose
quotes no measurement could see, and a bare `tk/tests/x.py` that the pointer
regex walked straight past — and neither came from a mutant. Mutation proves the
tests that exist; reading the bin's output over a real skill finds the test that
does not.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mutations_tk_contract import run      # noqa: E402  (path above enables it)

BIN = os.path.join("bin", "tk-prune-measure")

# (label, old, new, [tests that must fail])
MUTATIONS = [
    # -- what is inside the count, and what is outside it -------------------
    ("T185 the line count leaves out everything the frontmatter holds",
     '        "lines": len(lines),', '        "lines": len(body),',
     ["TestTheBloatedFixture.test_lines_count_the_whole_file_frontmatter_included"]),

    ("T185 the frontmatter is measured as body, so a description is counted twice",
     "            return list(enumerate(lines[i + 1:], i + 2)), lines[1:i]",
     "            return list(enumerate(lines, 1)), lines[1:i]",
     ["TestTheBloatedFixture.test_body_words_exclude_the_frontmatter",
      "TestWhatIsNotCounted.test_the_frontmatter_is_outside_every_body_count"]),

    ("T185 a file with no frontmatter loses its whole body",
     "    if not lines or lines[0].rstrip() != \"---\":\n        return list(enumerate(lines, 1)), []",
     "    if not lines or lines[0].rstrip() != \"---\":\n        return [], []",
     ["TestWhatIsNotCounted.test_a_file_with_no_frontmatter_is_measured_all_the_same",
      "TestTheShippedSkills.test_every_skill_of_this_plugin_measures_without_a_refusal"]),

    ("T185 an unclosed opening rule is read as frontmatter, and the file measures empty",
     "    return list(enumerate(lines, 1)), []\n\n\ndef frontmatter_description",
     "    return [], []\n\n\ndef frontmatter_description",
     ["TestWhatIsNotCounted.test_a_file_that_opens_with_a_rule_and_never_closes_it_keeps_its_body"]),

    ("T185 only backticks open a fenced block",
     'FENCE = re.compile(r"^\\s{0,3}(`{3,}|~{3,})")',
     'FENCE = re.compile(r"^\\s{0,3}(`{3,})")',
     ["TestWhatIsNotCounted.test_a_tilde_fenced_block_is_outside_every_count"]),

    ("T185 only tildes open a fenced block",
     'FENCE = re.compile(r"^\\s{0,3}(`{3,}|~{3,})")',
     'FENCE = re.compile(r"^\\s{0,3}(~{3,})")',
     ["TestWhatIsNotCounted.test_a_backtick_fenced_block_is_outside_every_count"]),

    ("T185 a fence closes on any fence, however short, so a nested one ends the block",
     "        if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence):",
     "        if m and m.group(1)[0] == fence[0]:",
     ["TestWhatIsNotCounted.test_a_fence_closes_only_on_one_at_least_as_long_as_it_opened_with"]),

    ("T185 a block never opens, so everything in every fence is measured",
     "                fence = m.group(1)", "                fence = None",
     ["TestWhatIsNotCounted.test_a_block_left_unclosed_runs_to_the_end_of_the_file"]),

    ("T185 an empty file has no sentences and the maximum raises on the empty list",
     '        "max_sentence_words": max(counts) if counts else 0,',
     '        "max_sentence_words": max(counts),',
     ["TestWhatIsNotCounted.test_an_empty_file_measures_zero_of_everything",
      "TestItMeasuresAndDoesNotJudge.test_an_empty_file_exits_zero"]),

    # -- the sentence unit --------------------------------------------------
    ("T185 a full stop no longer ends a sentence",
     'SENTENCE_END = re.compile(r"[.!?]+(?=\\s|$)")',
     'SENTENCE_END = re.compile(r"(?!x)x")',
     ["TestTheBloatedFixture.test_the_sentence_count_is_the_one_the_sentence_unit_produces",
      "TestTheSentenceUnit.test_a_full_stop_inside_a_list_item_still_splits_it"]),

    ("T185 a full stop ends a sentence wherever it sits, decimals included",
     'SENTENCE_END = re.compile(r"[.!?]+(?=\\s|$)")',
     'SENTENCE_END = re.compile(r"[.!?]+")',
     ["TestTheSentenceUnit.test_a_decimal_point_does_not_end_a_sentence"]),

    ("T185 an abbreviation ends a sentence",
     "        if last in ABBREV or (len(last) == 1 and last.isalpha()):",
     "        if False:",
     ["TestTheSentenceUnit.test_an_abbreviation_does_not_end_a_sentence"]),

    ("T185 the end of a table row does not end a sentence, so a palette is one sentence",
     "    return bool(HEADING.match(stripped) or LIST_ITEM.match(stripped)\n"
     "                or TABLE_ROW.match(stripped))",
     "    return bool(HEADING.match(stripped) or LIST_ITEM.match(stripped))",
     ["TestTheSentenceUnit.test_a_table_row_ends_a_sentence_at_the_end_of_its_line",
      "TestTheSentenceUnit.test_two_table_rows_are_two_sentences_though_neither_ends_in_a_full_stop",
      "TestTheShippedSkills.test_the_table_heavy_skill_does_not_measure_as_one_enormous_sentence"]),

    ("T185 the end of a list item does not end a sentence",
     "    return bool(HEADING.match(stripped) or LIST_ITEM.match(stripped)\n"
     "                or TABLE_ROW.match(stripped))",
     "    return bool(HEADING.match(stripped) or TABLE_ROW.match(stripped))",
     ["TestTheSentenceUnit.test_a_list_item_ends_a_sentence_at_the_end_of_its_line"]),

    ("T185 the end of a heading does not end a sentence",
     "    return bool(HEADING.match(stripped) or LIST_ITEM.match(stripped)\n"
     "                or TABLE_ROW.match(stripped))",
     "    return bool(LIST_ITEM.match(stripped) or TABLE_ROW.match(stripped))",
     ["TestTheSentenceUnit.test_a_heading_ends_a_sentence_at_the_end_of_its_line"]),

    ("T185 every line ends a sentence, so a wrapped paragraph is one sentence per line",
     "        if hard_break(line):\n            flush(chunk)", "        if True:\n            flush(chunk)",
     ["TestTheSentenceUnit.test_a_wrapped_paragraph_is_one_sentence_across_its_lines"]),

    ("T185 a blank line does not end a sentence, so two paragraphs run together",
     "        if not text:\n            flush(chunk)\n            continue",
     "        if not text:\n            continue",
     ["TestTheSentenceUnit.test_a_blank_line_ends_a_sentence_that_never_got_a_full_stop"]),

    ("T185 anything at all counts as a word, punctuation rows and dashes included",
     'WORD = re.compile(r"[^\\W_]", re.UNICODE)', 'WORD = re.compile(r".", re.UNICODE)',
     ["TestTheSentenceUnit.test_the_table_separator_row_is_not_a_sentence",
      "TestTheSentenceUnit.test_an_em_dash_alone_is_not_a_word",
      "TestTheDescription.test_a_block_scalar_marker_is_not_a_word_of_the_description"]),

    ("T185 the longest sentence is reported as the shortest one",
     '        "max_sentence_words": max(counts) if counts else 0,',
     '        "max_sentence_words": min(counts) if counts else 0,',
     ["TestTheBloatedFixture.test_the_longest_sentence_is_the_fifty_one_word_one"]),

    ("T185 the mean is taken over the lines rather than over the sentences",
     '        "mean_sentence_words": round(body_words / len(sents), 1) if sents else 0.0,',
     '        "mean_sentence_words": round(body_words / len(body), 1) if sents else 0.0,',
     ["TestTheBloatedFixture.test_the_mean_is_the_body_words_over_the_sentences"]),

    ("T185 the long-sentence threshold moves, and a 51-word sentence is not long",
     "LONG_SENTENCE = 30 ", "LONG_SENTENCE = 60 ",
     ["TestTheBloatedFixture.test_one_sentence_runs_past_thirty_words"]),

    # -- the description ----------------------------------------------------
    ("T185 the description is read to its first word only",
     '        m = re.match(r"^description\\s*:\\s*(.*)$", line)',
     '        m = re.match(r"^description\\s*:\\s*(\\S*)", line)',
     ["TestTheBloatedFixture.test_the_description_is_measured_apart_from_the_body",
      "TestTheDescription.test_a_quoted_description_counts_the_words_between_the_quotes",
      "TestTheDescription.test_an_unquoted_description_is_counted_the_same",
      "TestUsage.test_a_byte_order_mark_ahead_of_the_frontmatter_still_reads"]),

    ("T185 a wrapped description stops at the end of its first line",
     "        for cont in fm_lines[i + 1:]:", "        for cont in []:",
     ["TestTheDescription.test_a_description_wrapped_over_indented_lines_is_counted_whole"]),

    ("T185 the next key of the frontmatter is swallowed into the description",
     "            if not cont[:1].isspace():\n                break", "            if False:\n                break",
     ["TestTheDescription.test_a_key_after_the_description_ends_it"]),

    ("T185 an absent description is reported as an empty one rather than as absent",
     "        return \" \".join(p for p in parts if p).strip()\n    return None",
     "        return \" \".join(p for p in parts if p).strip()\n    return \"\"",
     ["TestTheDescription.test_a_file_with_no_frontmatter_reports_the_description_as_absent"]),

    # -- inline evidence ----------------------------------------------------
    ("T185 an ISO date is not evidence",
     'ISO_DATE = re.compile(r"\\b\\d{4}-\\d{2}-\\d{2}\\b")',
     'ISO_DATE = re.compile(r"(?!x)x")',
     ["TestInlineEvidence.test_an_iso_date_is_evidence",
      "TestTheBloatedFixture.test_every_kind_of_inline_evidence_is_found"]),

    ("T185 the word measured is not evidence",
     'MEASURED = re.compile(r"(?i)\\bmeasured\\b")', 'MEASURED = re.compile(r"(?!x)x")',
     ["TestInlineEvidence.test_the_word_measured_is_evidence"]),

    ("T185 a count followed by times or before is not evidence",
     'COUNT_EVIDENCE = re.compile(r"(?i)\\b\\d+\\s+(?:times|before)\\b")',
     'COUNT_EVIDENCE = re.compile(r"(?!x)x")',
     ["TestInlineEvidence.test_a_count_followed_by_times_is_evidence",
      "TestInlineEvidence.test_a_count_followed_by_before_is_evidence"]),

    ("T185 any number at all is evidence, so a palette of five rows is a measurement",
     'COUNT_EVIDENCE = re.compile(r"(?i)\\b\\d+\\s+(?:times|before)\\b")',
     'COUNT_EVIDENCE = re.compile(r"(?i)\\b\\d+\\s+\\w+")',
     ["TestInlineEvidence.test_a_bare_number_is_not_evidence"]),

    ("T185 a hit no longer says which kind of evidence it matched",
     'return [{"line": number, "kind": kind, "match": m.group(0)}',
     'return [{"line": number, "kind": "evidence", "match": m.group(0)}',
     ["TestInlineEvidence.test_each_hit_names_the_kind_it_matched"]),

    # -- pointers -----------------------------------------------------------
    ("T185 only a path carrying a known extension is a pointer",
     '    r"(?<![\\w/])(?:(?:~|\\.{1,2})?/[\\w./~@-]*[\\w/]"\n'
     '    r"|[\\w][\\w./@-]*\\.(?:md|py|sh|json|html|txt|yml|yaml|toml)\\b)")',
     '    r"(?<![\\w/])(?:[\\w][\\w./@-]*\\.(?:md|py|sh|json|html|txt|yml|yaml|toml)\\b)")',
     ["TestPointers.test_a_home_relative_path_is_a_pointer",
      "TestPointers.test_a_parent_relative_path_is_a_pointer"]),

    ("T185 only a path carrying a real prefix is a pointer, so a bare filename is missed",
     '    r"(?<![\\w/])(?:(?:~|\\.{1,2})?/[\\w./~@-]*[\\w/]"\n'
     '    r"|[\\w][\\w./@-]*\\.(?:md|py|sh|json|html|txt|yml|yaml|toml)\\b)")',
     '    r"(?<![\\w/])(?:(?:~|\\.{1,2})?/[\\w./~@-]*[\\w/])")',
     ["TestPointers.test_a_bare_filename_with_a_known_extension_is_a_pointer",
      "TestPointers.test_a_repo_relative_path_with_no_dot_prefix_is_a_pointer",
      "TestTheBloatedFixture.test_the_four_pointers_are_found"]),

    ("T185 the tail of a word enters as a path of its own",
     '    r"(?<![\\w/])(?:(?:~|\\.{1,2})?/[\\w./~@-]*[\\w/]"',
     '    r"(?:(?:~|\\.{1,2})?/[\\w./~@-]*[\\w/]"',
     ["TestPointers.test_a_slashed_word_that_is_not_a_path_is_not_a_pointer"]),

    ("T185 the path inside a URL is read as a file in this tree",
     '        text = URL.sub(" ", line_text(line))', "        text = line_text(line)",
     ["TestPointers.test_a_url_is_not_a_pointer_to_a_file_in_this_tree"]),

    # -- negations ----------------------------------------------------------
    ("T185 never is not a negation",
     "NEGATIONS = re.compile(r\"(?i)(?<![\\w'’])(do not|don['’]t|never|not|no)(?![\\w'’])\")",
     "NEGATIONS = re.compile(r\"(?i)(?<![\\w'’])(do not|don['’]t|not|no)(?![\\w'’])\")",
     ["TestTheBloatedFixture.test_all_forty_negations_are_found"]),

    ("T185 the contraction is not a negation",
     "NEGATIONS = re.compile(r\"(?i)(?<![\\w'’])(do not|don['’]t|never|not|no)(?![\\w'’])\")",
     "NEGATIONS = re.compile(r\"(?i)(?<![\\w'’])(do not|never|not|no)(?![\\w'’])\")",
     ["TestNegations.test_the_contraction_is_counted_once"]),

    ("T185 `do not` is left out, so the phrase reports as a bare `not`",
     "NEGATIONS = re.compile(r\"(?i)(?<![\\w'’])(do not|don['’]t|never|not|no)(?![\\w'’])\")",
     "NEGATIONS = re.compile(r\"(?i)(?<![\\w'’])(don['’]t|never|not|no)(?![\\w'’])\")",
     ["TestNegations.test_do_not_is_counted_once_and_reported_whole"]),

    ("T185 a negation is matched inside a longer word",
     "NEGATIONS = re.compile(r\"(?i)(?<![\\w'’])(do not|don['’]t|never|not|no)(?![\\w'’])\")",
     "NEGATIONS = re.compile(r\"(?i)(?<![\\w'’])(do not|don['’]t|never|not|no)\")",
     ["TestNegations.test_no_inside_a_longer_word_is_not_a_negation"]),

    ("T185 a negation is counted and never shown, so the reader cannot judge it",
     '"context": context(text, m)}', '"context": ""}',
     ["TestNegations.test_every_negation_is_listed_with_the_line_it_sits_on"]),

    ("T185 the whole line comes back as context, however long the line is",
     "    collapsed = \" \".join(text.split())\n    if len(collapsed) <= 100:",
     "    collapsed = \" \".join(text.split())\n    if True:",
     ["TestNegations.test_a_long_line_is_reported_as_a_window_around_the_match"]),

    # -- defined terms ------------------------------------------------------
    ("T185 `A **term** is` is not a definition",
     'TERM_IS = re.compile(r"(?:\\b(?:an?|the)\\s+)?\\*\\*([^*\\n]+)\\*\\*\\s+(?:is|means)\\b",',
     'TERM_IS = re.compile(r"(?!x)x",',
     ["TestDefinedTerms.test_the_article_form_is_a_definition",
      "TestDefinedTerms.test_the_form_with_means_is_a_definition",
      "TestDefinedTerms.test_the_house_form_without_an_article_is_a_definition"]),

    ("T185 the article is required, so the house form `**Pruning** is` is missed",
     'TERM_IS = re.compile(r"(?:\\b(?:an?|the)\\s+)?\\*\\*([^*\\n]+)\\*\\*\\s+(?:is|means)\\b",',
     'TERM_IS = re.compile(r"(?:\\b(?:an?|the)\\s+)\\*\\*([^*\\n]+)\\*\\*\\s+(?:is|means)\\b",',
     ["TestDefinedTerms.test_the_house_form_without_an_article_is_a_definition"]),

    ("T185 bold and a colon is not a definition",
     'TERM_COLON = re.compile(r"^\\*\\*([^*\\n]+)\\*\\*\\s*:")',
     'TERM_COLON = re.compile(r"(?!x)x")',
     ["TestDefinedTerms.test_bold_and_a_colon_opening_a_line_is_a_definition",
      "TestDefinedTerms.test_bold_and_a_colon_inside_a_list_item_opens_that_line_too",
      "TestTheBloatedFixture.test_the_five_defined_terms_are_found"]),

    ("T185 bold and a colon anywhere in a line is a definition",
     'TERM_COLON = re.compile(r"^\\*\\*([^*\\n]+)\\*\\*\\s*:")',
     'TERM_COLON = re.compile(r"\\*\\*([^*\\n]+)\\*\\*\\s*:")',
     ["TestDefinedTerms.test_bold_in_the_middle_of_a_line_is_not_a_definition"]),

    ("T185 a list marker is left in place, so a definition opening a bullet is missed",
     "    text = LIST_ITEM.sub(\"\", text)", "    text = text",
     ["TestDefinedTerms.test_bold_and_a_colon_inside_a_list_item_opens_that_line_too"]),

    ("T185 the siblings are never read",
     "    for name in names:", "    for name in []:",
     ["TestDefinedTerms.test_a_term_defined_in_a_sibling_of_the_same_directory_is_reported",
      "TestTheBloatedFixture.test_the_one_term_the_sibling_defines_too_is_found"]),

    ("T185 every file beside the skill is read as markdown",
     '        if name == here or not name.lower().endswith(".md"):',
     "        if name == here:",
     ["TestDefinedTerms.test_a_sibling_that_is_not_markdown_is_not_read"]),

    ("T185 a definition inside a sibling's code block counts as a definition",
     "        for _, term in defined_terms(outside_code(body)):",
     "        for _, term in defined_terms(body):",
     ["TestDefinedTerms.test_a_term_defined_inside_a_siblings_code_block_does_not_count"]),

    ("T185 the sibling comparison is case sensitive",
     "            out.setdefault(term.casefold(), []).append(name)",
     "            out.setdefault(term, []).append(name)",
     ["TestDefinedTerms.test_the_sibling_comparison_ignores_case"]),

    ("T185 every defined term is reported as shared, sibling or no sibling",
     "    shared = [{\"line\": number, \"term\": term, \"also_in\": siblings[term.casefold()]}\n"
     "              for number, term in terms if term.casefold() in siblings]",
     "    shared = [{\"line\": number, \"term\": term, \"also_in\": []}\n"
     "              for number, term in terms]",
     ["TestDefinedTerms.test_a_term_defined_once_in_its_own_file_is_not_reported_as_shared",
      "TestDefinedTerms.test_a_term_defined_in_a_sibling_of_the_same_directory_is_reported"]),

    # -- targets ------------------------------------------------------------
    ("T185 a metric sitting exactly on its ceiling is marked over",
     '                              ("ok" if value <= TARGETS[key] else "over")})',
     '                              ("ok" if value < TARGETS[key] else "over")})',
     ["TestTargets.test_a_value_exactly_on_the_ceiling_passes",
      "TestTheLeanFixture.test_a_file_built_to_the_targets_passes_every_one_of_them"]),

    ("T185 the comparison runs the wrong way",
     '                              ("ok" if value <= TARGETS[key] else "over")})',
     '                              ("ok" if value >= TARGETS[key] else "over")})',
     ["TestTargets.test_a_metric_over_its_ceiling_is_marked_over",
      "TestTargets.test_a_metric_inside_its_ceiling_is_marked_ok"]),

    ("T185 an absent value is marked against a ceiling it cannot be compared to",
     '                    "status": "n/a" if value is None else',
     '                    "status": "ok" if value is None else',
     ["TestTheDescription.test_an_absent_description_is_marked_n_a_rather_than_passing_its_target"]),

    ("T185 a report-only metric grows a target of its own",
     "        if key not in TARGETS:\n            continue", "        if False:\n            continue",
     ["TestTargets.test_a_metric_the_bin_only_reports_gets_no_target",
      "TestTargets.test_the_targets_the_bin_carries_are_the_ones_the_house_rule_names"]),

    ("T185 a target moves off the number the house rule names",
     '    "mean_sentence_words": 22,', '    "mean_sentence_words": 12,',
     ["TestTargets.test_the_targets_the_bin_carries_are_the_ones_the_house_rule_names"]),

    ("T185 the JSON carries the marks whether or not they were asked for",
     "        if args.targets:\n            report[\"targets\"] = marks(report[\"metrics\"])",
     "        if True:\n            report[\"targets\"] = marks(report[\"metrics\"])",
     ["TestTargets.test_no_target_is_marked_unless_targets_is_asked_for"]),

    ("T185 the text report carries the target columns whether or not they were asked for",
     "    if show_targets:\n        header += f\"  {'target':>6}  status\"",
     "    if True:\n        header += f\"  {'target':>6}  status\"",
     ["TestTargets.test_the_text_report_carries_a_status_column_only_with_targets"]),

    ("T185 a mark carries the ceiling where the measured value belongs",
     '        out.append({"metric": key, "value": value, "target": TARGETS[key],',
     '        out.append({"metric": key, "value": TARGETS[key], "target": TARGETS[key],',
     ["TestTextAndJsonAgree.test_the_marks_agree_with_the_metrics_they_mark"]),

    # -- the two formats are one measurement --------------------------------
    ("T185 the text report rounds a number the JSON reports whole",
     '        shown = "—" if value is None else f"{value}"',
     '        shown = "—" if value is None else f"{round(value)}"',
     ["TestTextAndJsonAgree.test_every_fixture_reports_the_same_numbers_in_both_formats"]),

    ("T185 a metric the JSON carries has no row in the text report",
     '    ("pointers", "pointers to other files"),\n', "",
     ["TestTextAndJsonAgree.test_the_text_report_carries_a_row_for_every_metric_the_json_carries"]),

    # -- it measures, it does not judge -------------------------------------
    ("T185 asking for the targets turns the bin into a gate",
     "    if args.as_json:", "    if args.targets:\n        return 1\n    if args.as_json:",
     ["TestItMeasuresAndDoesNotJudge.test_a_file_that_misses_every_target_still_exits_zero",
      "TestItMeasuresAndDoesNotJudge.test_every_fixture_exits_zero_in_every_format"]),

    # -- usage --------------------------------------------------------------
    ("T185 a directory is reported as a file that is not there",
     "    if os.path.isdir(args.file):", "    if False:",
     ["TestUsage.test_a_directory_is_named_as_a_directory_not_reported_as_an_empty_file"]),

    ("T185 an absent path is opened, and the refusal names the wrong thing",
     "    if not os.path.isfile(args.file):", "    if False:",
     ["TestUsage.test_a_path_that_does_not_exist_is_named_rather_than_measured"]),

    ("T185 a file that is not text raises instead of being named",
     "    except (OSError, UnicodeDecodeError) as e:", "    except OSError as e:",
     ["TestUsage.test_a_file_that_is_not_text_is_named_rather_than_raising"]),

    ("T185 the report no longer names the file it measured",
     '        "path": path,', '        "path": os.path.basename(path),',
     ["TestUsage.test_the_report_names_the_file_it_measured"]),
]

if __name__ == "__main__":
    sys.exit(run(MUTATIONS, "test_tk_prune_measure", default_src=BIN))
