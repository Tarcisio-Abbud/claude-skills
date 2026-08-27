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
     '            return list(enumerate(lines[i + 1:], i + 2)), block',
     '            return list(enumerate(lines, 1)), block',
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
     'FENCE = re.compile(r"^(\\s*)(`{3,}|~{3,})")',
     'FENCE = re.compile(r"^(\\s*)(`{3,})")',
     ["TestWhatIsNotCounted.test_a_tilde_fenced_block_is_outside_every_count"]),

    ("T185 only tildes open a fenced block",
     'FENCE = re.compile(r"^(\\s*)(`{3,}|~{3,})")',
     'FENCE = re.compile(r"^(\\s*)(~{3,})")',
     ["TestWhatIsNotCounted.test_a_backtick_fenced_block_is_outside_every_count"]),

    ("T185 a fence closes on any fence, however short, so a nested one ends the block",
     '    return bool(m and m.group(2)[0] == fence[0] and len(m.group(2)) >= len(fence)\n                and not line[m.end():].strip()\n                and len(m.group(1).expandtabs()) <= indent + 3)',
     '    return bool(m and m.group(2)[0] == fence[0])',
     ["TestWhatIsNotCounted.test_a_fence_closes_only_on_one_at_least_as_long_as_it_opened_with"]),

    ("T185 a fence with text after it closes the block it sits inside",
     '                and not line[m.end():].strip()\n                and len(m.group(1).expandtabs()) <= indent + 3)', '                and len(m.group(1).expandtabs()) <= indent + 3)',
     ["TestWhatIsNotCounted.test_a_fence_with_text_after_it_does_not_close_a_block"]),

    ("T185 an inline code span opens a block that swallows the rest of the file",
     '    if m.group(2)[0] == "`" and "`" in line[m.end():]:\n        return None',
     '    if False:\n        return None',
     ["TestWhatIsNotCounted.test_an_inline_code_span_does_not_open_a_block"]),

    ("T185 the backtick clause is applied to tilde fences too",
     '    if m.group(2)[0] == "`" and "`" in line[m.end():]:',
     '    if "`" in line[m.end():]:',
     ["TestWhatIsNotCounted.test_a_tilde_fence_may_carry_backticks_in_its_info_string"]),

    ("T185 a YAML document-end marker no longer closes the frontmatter",
     '        if lines[i].rstrip() in ("---", "..."):', '        if lines[i].rstrip() == "---":',
     ["TestWhatIsNotCounted.test_frontmatter_closed_with_a_yaml_document_end_is_frontmatter"]),

    ("T185 a block of link definitions reads as one sentence again",
     'HARD_BREAK_ROLES = frozenset({"heading", "list", "table", "linkdef", "rule"})',
     'HARD_BREAK_ROLES = frozenset({"heading", "list", "table", "rule"})',
     ["TestUnpunctuatedRuns.test_a_block_of_link_definitions_is_one_sentence_each"]),

    ("T185 a setext underline and a thematic break stop ending the line above",
     'HARD_BREAK_ROLES = frozenset({"heading", "list", "table", "linkdef", "rule"})',
     'HARD_BREAK_ROLES = frozenset({"heading", "list", "table", "linkdef"})',
     ["TestUnpunctuatedRuns.test_a_setext_underline_ends_the_line_above_it",
      "TestUnpunctuatedRuns.test_a_thematic_break_ends_the_line_above_it"]),

    ("T185 every unpunctuated line ends a sentence, cutting wrapped prose at its breaks",
     '        if line.role in HARD_BREAK_ROLES:',
     '        if True:',
     ["TestUnpunctuatedRuns.test_a_wrapped_paragraph_is_still_not_cut_at_its_line_breaks",
      "TestTheSentenceUnit.test_a_wrapped_paragraph_is_one_sentence_across_its_lines"]),

    ("T185 a block never opens, so everything in every fence is measured",
     '            found = opens_fence(raw)', '            found = None',
     ["TestWhatIsNotCounted.test_a_block_left_unclosed_runs_to_the_end_of_the_file",
      "TestTheFenceIndent.test_a_fence_at_the_margin_holds_its_block_out_of_the_count",
      "TestTheFenceIndent.test_a_fence_three_spaces_in_holds_its_block_out_of_the_count"]),

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
     "        if last in ABBREV:", "        if False:",
     ["TestTheSentenceUnit.test_an_abbreviation_does_not_end_a_sentence",
      "TestTheSentenceUnit.test_each_abbreviation_of_the_list_is_honoured"]),

    ("T185 the list keeps only its first member, and the rest vanish unnoticed",
     'ABBREV = {"e.g", "i.e", "etc", "vs", "cf", "mr", "mrs", "ms", "dr", "prof",\n'
     '          "fig", "approx", "al", "st"}',
     'ABBREV = {"e.g"}',
     ["TestTheSentenceUnit.test_each_abbreviation_of_the_list_is_honoured"]),

    ("T185 a single letter is exempt again, and enumerated steps merge into one",
     "        if last in ABBREV:",
     "        if last in ABBREV or (len(last) == 1 and last.isalpha()):",
     ["TestTheSentenceUnit.test_an_initial_ends_a_sentence_so_enumerated_steps_stay_apart"]),

    ("T185 the chunk is flushed only after a hard break, never before it",
     '            flush(chunk)\n            chunk.append(line)\n            flush(chunk)',
     '            chunk.append(line)\n            flush(chunk)',
     ["TestTheChunkBoundary.test_a_list_measures_the_same_with_and_without_a_blank_line_before_it",
      "TestTheChunkBoundary.test_the_first_bullet_is_its_own_sentence_though_no_blank_line_precedes_it",
      "TestTheChunkBoundary.test_a_heading_straight_after_a_paragraph_does_not_swallow_it"]),

    ("T185 every sentence is attributed one line below the line it sits on",
     '            offsets.append(len(text))\n            starts.append(line.number)',
     '            offsets.append(len(text))\n            starts.append(line.number + 1)',
     ["TestSentenceLineNumbers.test_a_sentence_opening_a_chunk_keeps_its_own_line",
      "TestSentenceLineNumbers.test_a_sentence_opening_a_line_is_reported_on_that_line"]),

    ("T185 a sentence is attributed to the separator before it, pointing one line up",
     "            out.append((first_word_at(text, start), piece))",
     "            out.append((start, piece))",
     ["TestSentenceLineNumbers.test_a_sentence_opening_a_line_is_reported_on_that_line"]),

    ("T185 the trailing fragment of a chunk loses the same fix",
     "        out.append((first_word_at(text, start), tail))",
     "        out.append((start, tail))",
     ["TestSentenceLineNumbers.test_a_last_sentence_with_no_full_stop_keeps_its_line_too"]),

    ("T185 the whitespace walk never moves, so the attribution fix is inert",
     "    while start < len(text) and text[start].isspace():",
     "    while False:",
     ["TestSentenceLineNumbers.test_a_sentence_opening_a_line_is_reported_on_that_line"]),

    ("T185 the first sentence of a chunk loses the line it starts on",
     '        for line in chunk:\n            offsets.append(len(text))',
     '        for line in chunk:\n            offsets.append(len(text) + 1)',
     ["TestSentenceLineNumbers.test_a_sentence_opening_a_line_is_reported_on_that_line"]),

    ("T185 the end of a table row does not end a sentence, so a palette is one sentence",
     'HARD_BREAK_ROLES = frozenset({"heading", "list", "table", "linkdef", "rule"})',
     'HARD_BREAK_ROLES = frozenset({"heading", "list", "linkdef", "rule"})',
     ["TestTheSentenceUnit.test_a_table_row_ends_a_sentence_at_the_end_of_its_line",
      "TestTheSentenceUnit.test_two_table_rows_are_two_sentences_though_neither_ends_in_a_full_stop",
      "TestTheShippedSkills.test_the_table_heavy_skill_does_not_measure_as_one_enormous_sentence"]),

    ("T185 the end of a list item does not end a sentence",
     'HARD_BREAK_ROLES = frozenset({"heading", "list", "table", "linkdef", "rule"})',
     'HARD_BREAK_ROLES = frozenset({"heading", "table", "linkdef", "rule"})',
     ["TestTheSentenceUnit.test_a_list_item_ends_a_sentence_at_the_end_of_its_line"]),

    ("T185 the end of a heading does not end a sentence",
     'HARD_BREAK_ROLES = frozenset({"heading", "list", "table", "linkdef", "rule"})',
     'HARD_BREAK_ROLES = frozenset({"list", "table", "linkdef", "rule"})',
     ["TestTheSentenceUnit.test_a_heading_ends_a_sentence_at_the_end_of_its_line"]),

    ("T185 a blank line does not end a sentence, so two paragraphs run together",
     '        if line.role == "blank":\n            flush(chunk)\n            continue',
     '        if line.role == "blank":\n            continue',
     ["TestTheSentenceUnit.test_a_blank_line_ends_a_sentence_that_never_got_a_full_stop"]),

    ("T185 anything at all counts as a word, punctuation rows and dashes included",
     'WORD = re.compile(r"[^\\W_]", re.UNICODE)', 'WORD = re.compile(r".", re.UNICODE)',
     ["TestTheSentenceUnit.test_the_table_separator_row_is_not_a_sentence",
      "TestTheSentenceUnit.test_an_em_dash_alone_is_not_a_word",
      "TestUsage.test_a_byte_that_is_not_utf8_never_becomes_a_word",
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
    ("T185 a file with no description at all reports one of no words",
     "        found = \" \".join(p for p in parts if p).strip() or None\n    return found",
     "        found = \" \".join(p for p in parts if p).strip() or None\n    return \"\"",
     ["TestTheDescription.test_a_file_with_no_frontmatter_reports_the_description_as_absent"]),

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
     '        found = " ".join(p for p in parts if p).strip() or None',
     '        found = " ".join(p for p in parts if p).strip() or ""',
     ["TestTheDescription.test_a_description_key_with_no_value_is_absent"]),

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
     'return [{"line": line.number, "kind": kind, "match": m.group(0)}',
     'return [{"line": line.number, "kind": "evidence", "match": m.group(0)}',
     ["TestInlineEvidence.test_each_hit_names_the_kind_it_matched"]),

    # -- pointers -----------------------------------------------------------
    ("T185 only a path carrying a known extension is a pointer",
     'PATHISH = re.compile(r"(?<![\\w/])(?:~|\\.{1,2})?/[\\w./~@-]*[\\w/]"\n'
     '                     r"|(?<![\\w/])[\\w][\\w./@-]*[\\w]")',
     'PATHISH = re.compile(r"(?<![\\w/])[\\w][\\w./@-]*[\\w]")',
     
     ["TestPointers.test_a_home_relative_path_is_a_pointer",
      "TestPointers.test_a_parent_relative_path_is_a_pointer"]),

    ("T185 only a path carrying a real prefix is a pointer, so a bare filename is missed",
     'POINTER_SUFFIXES = ("md", "py", "sh", "json", "html", "txt", "yml", "yaml", "toml")',
     'POINTER_SUFFIXES = ()',
     
     ["TestPointers.test_a_bare_filename_with_a_known_extension_is_a_pointer",
      "TestPointers.test_a_repo_relative_path_with_no_dot_prefix_is_a_pointer",
      "TestTheBloatedFixture.test_the_four_pointers_are_found"]),

    
    ("T185 the URL scheme is unbounded again, and dotted text stops the run",
     'WEB_ADDRESS = re.compile(r"(?i)\\b(?:[a-z][a-z0-9+.-]{0,31}://|www\\.)\\S+")',
     'WEB_ADDRESS = re.compile(r"(?i)\\b(?:[a-z][a-z0-9+.-]*://|www\\.)\\S+")',
     ["TestPointers.test_a_long_run_of_dotted_text_measures_promptly"]),

    ("T185 the extension goes back into the pattern, where the dot overlaps itself",
     '    for line, _, found in line_matches(body, PATHISH):',
     '    for line, _, found in line_matches(body, re.compile(\n            r"(?<![\\w/])(?:(?:~|\\.{1,2})?/[\\w./~@-]*[\\w/]"\n            r"|[\\w][\\w./@-]*\\.(?:md|py|sh|json|html|txt|yml|yaml|toml)\\b)")):',
     ["TestPointers.test_a_long_run_of_dotted_text_measures_promptly"]),

    ("T185 a path-shaped token is a pointer whatever its tail",
     '            if (token.startswith(POINTER_PREFIXES) or rooted_path(token)\n                    or ("." in token\n                        and token.rsplit(".", 1)[-1].lower() in POINTER_SUFFIXES)):',
     '            if True:',
     ["TestPointers.test_a_slashed_word_that_is_not_a_path_is_not_a_pointer"]),

    ("T185 the path inside a URL is read as a file in this tree",
     '        text = WEB_ADDRESS.sub(" ", line.text)', '        text = line.text',
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

    ("T185 the context window is cut at an offset the collapse already moved",
     '    start = max(0, mapping[at] - 40)',
     '    start = max(0, at - 40)',
     ["TestNegations.test_a_long_line_is_reported_as_a_window_around_the_match"]),

    ("T185 a negation is counted and never shown, so the reader cannot judge it",
     '"context": context(collapsed, mapping, m.start())})', '"context": ""})',
     ["TestNegations.test_every_negation_is_listed_with_the_line_it_sits_on"]),

    ("T185 the whole line comes back as context, however long the line is",
     '    if len(collapsed) <= 100:',
     '    if True:',
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
     '        scanned, _ = scan(body)',
     '        scanned = [Line(n, *classify(raw)) for n, raw in body]',
     ["TestDefinedTerms.test_a_term_defined_inside_a_siblings_code_block_does_not_count"]),

    ("T185 a sibling is whatever a name in the directory points at",
     "        if os.path.dirname(os.path.realpath(full)) != root:\n            continue",
     "        if False:\n            continue",
     ["TestDefinedTerms.test_a_sibling_symlinked_out_of_the_directory_is_not_read"]),

    ("T185 the containment check refuses a symlink that never left the directory",
     "        if os.path.dirname(os.path.realpath(full)) != root:",
     "        if os.path.realpath(full) != full:",
     ["TestDefinedTerms.test_a_sibling_symlinked_within_the_directory_is_read"]),

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
    ("T185 the evidence is listed rule by rule rather than in file order",
     "    evidence.sort(key=lambda e: (e[\"line\"], e[\"match\"]))", "    pass",
     ["TestInlineEvidence.test_the_evidence_is_listed_in_the_order_a_reader_reads_it"]),

    ("T185 the metric column is padded to a fixed width and goes ragged",
     "    label_width = max(len(label) for _, label in METRICS)", "    label_width = 10",
     ["TestTextAndJsonAgree.test_the_value_column_is_aligned_to_the_longest_label"]),

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

    ("T185 a byte that is not UTF-8 is a refusal again",
     '    lines = raw.decode("utf-8-sig", errors="replace").splitlines()',
     '    lines = raw.decode("utf-8-sig").splitlines()',
     ["TestUsage.test_a_file_that_is_not_utf8_is_measured_rather_than_refused"]),

    
    ("T185 the report no longer names the file it measured",
     '        "path": path,', '        "path": os.path.basename(path),',
     ["TestUsage.test_the_report_names_the_file_it_measured"]),

    # -- the redesigned scanner, and the branches nothing exercised -------
    ('T185 the fence indent is bounded against the margin, so a list item carries neither end',
     'FENCE = re.compile(r"^(\\s*)(`{3,}|~{3,})")',
     'FENCE = re.compile(r"^(\\s{0,3})(`{3,}|~{3,})")',
     ['TestTheFenceIndent.test_a_fence_carried_by_a_list_item_holds_its_block_out_of_the_count']),

    ('T185 a close indented any distance past its opener closes the block',
     '                and len(m.group(1).expandtabs()) <= indent + 3)',
     '                )',
     ['TestTheFenceIndent.test_a_close_indented_far_past_its_opener_does_not_close_the_block']),

    ('T185 an unclosed block is never reported, so a body cut short looks small',
     '                fence, indent = found\n                opened_at = number',
     '                fence, indent = found\n                opened_at = None',
     ['TestTheUnclosedBlock.test_the_line_the_unclosed_block_opened_on_is_reported', 'TestTheUnclosedBlock.test_the_text_report_names_the_line_too']),

    ('T185 a block that closed is still reported as the one that swallowed the file',
     '            fence, opened_at = None, None',
     '            fence = None',
     ['TestTheUnclosedBlock.test_a_file_whose_blocks_all_close_reports_none', 'TestTheUnclosedBlock.test_a_file_whose_blocks_all_close_carries_no_note']),

    ('T185 the text report drops the note, so only the JSON says the file was cut short',
     '    if report["unclosed_fence"] is not None:',
     '    if False:',
     ['TestTheUnclosedBlock.test_the_text_report_names_the_line_too']),

    ('T185 a file cut short by a fence is refused instead of reported',
     '    if args.as_json:\n        if args.targets:',
     '    if report["unclosed_fence"] is not None:\n        return 1\n    if args.as_json:\n        if args.targets:',
     ['TestTheUnclosedBlock.test_the_bin_still_exits_zero_on_a_file_it_reports_cut_short']),

    ('T185 any block between two rules is frontmatter, prose and all',
     '            if looks_like_frontmatter(block):',
     '            if True:',
     ['TestTheFrontmatterBoundary.test_prose_between_two_rules_stays_in_the_body', 'TestTheFrontmatterBoundary.test_a_description_written_in_the_body_is_not_the_frontmatter_one']),

    ('T185 a line that is neither a key nor a continuation no longer disqualifies the block',
     '        elif not (line[:1].isspace() or FM_ITEM.match(line)):\n            return False',
     '        elif False:\n            return False',
     ['TestTheFrontmatterBoundary.test_prose_between_two_rules_stays_in_the_body']),

    ('T185 a block with no key at all is frontmatter',
     '    return keyed',
     '    return True',
     ['TestTheFrontmatterBoundary.test_an_indented_block_carrying_no_key_is_not_frontmatter']),

    ('T185 a list under a key disqualifies the frontmatter it belongs to',
     '        elif not (line[:1].isspace() or FM_ITEM.match(line)):',
     '        elif not line[:1].isspace():',
     ['TestTheFrontmatterBoundary.test_a_mapping_carrying_a_list_is_still_frontmatter']),

    ('T185 a scheme-less web address is read as a file in this tree',
     'WEB_ADDRESS = re.compile(r"(?i)\\b(?:[a-z][a-z0-9+.-]{0,31}://|www\\.)\\S+")',
     'WEB_ADDRESS = re.compile(r"(?i)\\b(?:[a-z][a-z0-9+.-]{0,31}://)\\S+")',
     ['TestWhatIsNotAPointer.test_a_web_address_written_with_www_is_not_prose_either']),

    ('T185 the scheme is bounded so tightly that no real one matches',
     'WEB_ADDRESS = re.compile(r"(?i)\\b(?:[a-z][a-z0-9+.-]{0,31}://|www\\.)\\S+")',
     'WEB_ADDRESS = re.compile(r"(?i)\\b(?:[a-z][a-z0-9+.-]{0,1}://|www\\.)\\S+")',
     ['TestPointers.test_a_url_is_not_a_pointer_to_a_file_in_this_tree']),

    ('T185 a token of any length is reported as a path',
     '            if len(token) > POINTER_MAX or web_host(token):\n                continue',
     '            if False:\n                continue',
     ['TestWhatIsAPointer.test_a_token_longer_than_any_filename_is_not_a_pointer']),

    ('T185 the extension test is case sensitive',
     '                        and token.rsplit(".", 1)[-1].lower() in POINTER_SUFFIXES)):',
     '                        and token.rsplit(".", 1)[-1] in POINTER_SUFFIXES)):',
     ['TestWhatIsAPointer.test_an_extension_written_in_capitals_is_a_pointer_too']),

    ('T185 a dotless token is tested by its whole self, so the word `md` is a file',
     '                    or ("." in token\n                        and token.rsplit(".", 1)[-1].lower() in POINTER_SUFFIXES)):',
     '                    or (token.rsplit(".", 1)[-1].lower() in POINTER_SUFFIXES)):',
     ['TestWhatIsAPointer.test_a_bare_word_spelt_like_an_extension_is_not_a_pointer']),

    ('T185 the home-relative prefix is dropped, so `~/…` is no longer a pointer',
     'POINTER_PREFIXES = ("./", "../", "~/")',
     'POINTER_PREFIXES = ("./", "../")',
     ['TestPointers.test_a_home_relative_path_is_a_pointer']),

    ('T185 half the extensions the bin knows are dropped',
     'POINTER_SUFFIXES = ("md", "py", "sh", "json", "html", "txt", "yml", "yaml", "toml")',
     'POINTER_SUFFIXES = ("md", "py", "sh", "html")',
     ['TestWhatIsAPointer.test_every_extension_the_bin_knows_makes_a_pointer']),

    ('T185 a dashed rule stops ending the line above it',
     'RULE = re.compile(r"^\\s{0,3}(?:=+|-{3,}|\\*{3,}|_{3,})\\s*$")',
     'RULE = re.compile(r"^\\s{0,3}(?:=+|\\*{3,}|_{3,})\\s*$")',
     ['TestThematicBreaks.test_a_dashed_rule_ends_the_line_above_it']),

    ('T185 a rule has to sit hard against the margin',
     'RULE = re.compile(r"^\\s{0,3}(?:=+|-{3,}|\\*{3,}|_{3,})\\s*$")',
     'RULE = re.compile(r"^(?:=+|-{3,}|\\*{3,}|_{3,})\\s*$")',
     ['TestThematicBreaks.test_a_rule_three_spaces_in_ends_the_line_above_it']),

    ('T185 a table row is read whole, so a cell no longer opens the text',
     '    if TABLE_ROW.match(text):\n        text = " ".join(cell.strip() for cell in text.strip().strip("|").split("|"))',
     '    if False:\n        text = " ".join(cell.strip() for cell in text.strip().strip("|").split("|"))',
     ['TestOneRolePerLine.test_a_definition_opening_a_table_cell_is_a_definition', 'TestOneRolePerLine.test_a_table_row_carried_by_a_list_item_gives_up_both_markers']),

    ('T185 the list marker stays on, so a row it carries is never read as one',
     '    text = LIST_ITEM.sub("", text)\n    if TABLE_ROW.match(text):',
     '    if TABLE_ROW.match(text):',
     ['TestOneRolePerLine.test_a_table_row_carried_by_a_list_item_gives_up_both_markers']),

    ('T185 a blockquote marker hides the construct behind it',
     '    stripped = BLOCKQUOTE.sub("", raw)\n    role = None',
     '    stripped = raw\n    role = None',
     ['TestOneRolePerLine.test_a_quoted_heading_ends_a_sentence_like_any_heading']),

    ('T185 every window is cut at the head of the line, so a later match is never in it',
     '    start = max(0, mapping[at] - 40)',
     '    start = max(0, mapping[0] - 40)',
     ['TestTheContextWindow.test_a_repeated_negation_is_windowed_at_its_own_occurrence']),

    ('T185 the line is collapsed once per match again',
     '        collapsed, mapping = collapse(text)\n        for m in found:\n            out.append(',
     '        for m in found:\n            collapsed, mapping = collapse(text)\n            out.append(',
     ['TestTheContextWindow.test_a_line_carrying_thousands_of_negations_measures_promptly']),

    ("T185 no block between two rules is ever frontmatter",
     "    return keyed",
     "    return False",
     ["TestTheFrontmatterBoundary.test_a_real_mapping_between_two_rules_is_still_frontmatter",
      "TestTheFrontmatterBoundary.test_a_mapping_whose_value_wraps_is_still_frontmatter"]),

    # -- the round-3 correction batch ------------------------------------
    ('T185 a quoted key is not a key, so the changesets format reads as prose',
     'FM_KEY = re.compile(r"""^(?:[A-Za-z_][\\w.-]*|"[^"]+"|\'[^\']+\')\\s*:""")',
     'FM_KEY = re.compile(r"""^(?:[A-Za-z_][\\w.-]*)\\s*:""")',
     ['TestTheFrontmatterShapes.test_a_quoted_key_is_a_key', 'TestTheFrontmatterShapes.test_a_single_quoted_key_is_a_key_too']),

    ('T185 a key may open with a digit, so a dated line of prose is a mapping',
     'FM_KEY = re.compile(r"""^(?:[A-Za-z_][\\w.-]*|"[^"]+"|\'[^\']+\')\\s*:""")',
     'FM_KEY = re.compile(r"""^(?:[\\w.-]*|"[^"]+"|\'[^\']+\')\\s*:""")',
     ['TestTheFrontmatterShapes.test_a_line_opening_with_a_digit_is_not_a_key']),

    ('T185 a YAML comment disqualifies the block it sits in',
     '        if FM_COMMENT.match(line):\n            continue\n',
     '',
     ['TestTheFrontmatterShapes.test_a_yaml_comment_does_not_disqualify_the_block']),

    ('T185 a blank line disqualifies the frontmatter it sits in',
     '        if not line.strip():\n            continue\n        if FM_COMMENT.match(line):',
     '        if FM_COMMENT.match(line):',
     ['TestTheFrontmatterShapes.test_a_blank_line_inside_the_block_does_not_disqualify_it']),

    ('T185 a repeated description key reports the value a loader would shadow',
     '        found = " ".join(p for p in parts if p).strip() or None\n    return found',
     '        return " ".join(p for p in parts if p).strip() or None\n    return found',
     ['TestTheFrontmatterShapes.test_the_last_description_wins_when_the_key_is_repeated']),

    ('T185 a bare slash opens a pointer again, so every slash command is a file',
     'POINTER_PREFIXES = ("./", "../", "~/")',
     'POINTER_PREFIXES = ("/", "./", "../", "~/")',
     ['TestWhatIsNotAPointer.test_a_slash_command_is_not_a_pointer', 'TestWhatIsNotAPointer.test_a_closing_html_tag_is_not_a_pointer']),

    ('T185 one segment is enough to make an absolute path',
     '    return token.startswith("/") and token.count("/") > 1',
     '    return token.startswith("/") and token.count("/") > 0',
     ['TestWhatIsNotAPointer.test_a_slash_command_is_not_a_pointer']),

    ('T185 an absolute path stops being a pointer at all',
     '            if (token.startswith(POINTER_PREFIXES) or rooted_path(token)',
     '            if (token.startswith(POINTER_PREFIXES)',
     ['TestWhatIsNotAPointer.test_an_absolute_path_of_two_segments_is_still_a_pointer',
      'TestWhatIsAPointer.test_an_absolute_path_with_no_extension_is_a_pointer']),

    ('T185 a repository host is read as a file of this tree',
     '            if len(token) > POINTER_MAX or web_host(token):',
     '            if len(token) > POINTER_MAX:',
     ['TestWhatIsNotAPointer.test_a_scheme_less_repository_host_is_not_a_pointer']),

    ('T185 a dot directory is read as a hostname',
     '    return "/" in token and not head.startswith(".") and "." in head',
     '    return "/" in token and "." in head',
     ['TestWhatIsNotAPointer.test_a_relative_path_prefix_is_not_a_hostname']),

    ('T185 a path is a host whenever any segment of it carries a dot',
     '    head = token.split("/", 1)[0]\n    return "/" in token and not head.startswith(".") and "." in head',
     '    head = token\n    return "/" in token and not head.startswith(".") and "." in head',
     ['TestWhatIsNotAPointer.test_a_repo_relative_path_of_two_segments_is_still_a_pointer']),

    ('T185 every line is prose, so a blank one no longer ends a chunk',
     '        role = "prose" if text else "blank"',
     '        role = "prose"',
     ['TestTheBlankRole.test_a_blank_line_ends_a_chunk_by_its_role']),

    ('T185 the context window is cut to a width no reader asked for',
     '    end = min(len(collapsed), start + 100)',
     '    end = min(len(collapsed), start + 60)',
     ['TestTheWindowItself.test_a_window_cut_from_a_long_line_is_a_hundred_characters']),

    ('T185 a window always opens with an ellipsis, whatever it starts at',
     'return ("…" if start else "") + collapsed[start:end]',
     'return "…" + collapsed[start:end]',
     ['TestTheWindowItself.test_a_window_that_reaches_the_head_of_the_line_carries_no_opening_ellipsis']),

    ('T185 a window never says it opened inside the line',
     'return ("…" if start else "") + collapsed[start:end]',
     'return collapsed[start:end]',
     ['TestTheWindowItself.test_a_window_that_starts_inside_the_line_opens_with_an_ellipsis']),

    ('T185 a window always closes with an ellipsis, whatever it ends at',
     '+ ("…" if end < len(collapsed) else "")',
     '+ "…"',
     ['TestTheWindowItself.test_a_window_that_reaches_the_end_of_the_line_carries_no_closing_ellipsis']),

    ('T185 a window never says it stopped short of the end',
     '+ ("…" if end < len(collapsed) else "")',
     '+ ""',
     ['TestTheWindowItself.test_a_window_that_stops_short_of_the_end_closes_with_an_ellipsis']),
]

if __name__ == "__main__":
    sys.exit(run(MUTATIONS, "test_tk_prune_measure", default_src=BIN))
