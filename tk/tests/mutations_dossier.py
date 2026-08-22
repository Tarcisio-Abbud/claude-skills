#!/usr/bin/env python3
"""Mutation harness for the `tk-dossier` suite — each defect put back, and the
test that claims to prove it must fall.

Run: python3 tk/tests/mutations_dossier.py

Entries only: the runner is the one `mutations_tk_contract.py` exposes, through
the seam its docstring describes — it takes the entry list, the test module and
the default source as arguments, so a sibling suite adds a file of entries and
nothing else. Same contract as its own: an anchor must match EXACTLY ONCE, a
mutant no named test kills is a SURVIVOR, and a test no entry names is reported
UNPROVED, because a green score counts only the mutants somebody wrote.

ONE ENTRY MUTATES TWO GUARDS AT ONCE, and says so where it sits: `conflicts_of`
reads a conflicted merge two ways on purpose, and either reading alone would
survive its own mutation while the other still answered. Mutating them
separately would report a hole that is really redundancy; mutating them together
is what proves the pair.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mutations_tk_contract import run   # noqa: E402  (the path above enables it)

DOSSIER = os.path.join("bin", "tk-dossier")

MUTATIONS = [
    # --- binding a pointer, or refusing to ---------------------------------
    ("a pointer is addressed to the line its LIST starts on, not its entry",
     "            pointer.line, pointer.statement = block.entries[pointer.index]",
     "            pointer.line = block.line\n"
     "            pointer.statement = block.entries[pointer.index][1]",
     ["TestBinding.test_a_pointer_resolves_to_the_sentence_and_to_its_own_line"]),

    ("an entry stops at its first line, so a wrapped statement is half a sentence",
     "            if deeper > len(indent) and held <= 1:",
     "            if False:",
     ["TestBinding.test_a_continuation_line_is_part_of_the_statement"]),

    ("any enumerated list will do, whether or not it is labelled for the noun",
     "        eligible = [b for b in blocks if pointer.family in b.families]",
     "        eligible = list(blocks)",
     ["TestBinding.test_a_pointer_with_no_list_of_its_family_is_unresolved_not_guessed"]),

    ("the reason for an out-of-range pointer does not name the span it missed",
     '        return f"{keys[0]}–{keys[-1]}" if len(keys) > 1 else keys[0]',
     "        return keys[0]",
     ["TestBinding.test_an_index_the_list_does_not_have_is_unresolved_with_the_span"]),

    ("two candidate lists in one source are resolved by taking the first",
     "        if len(eligible) > 1:",
     "        if False:",
     ["TestBinding.test_two_lists_of_one_family_in_one_source_bind_to_neither"]),

    ("a source that answered is fallen through, so a later one may supply an index",
     '                              f"{pointer.index} is not one of its entries")\n'
     "        return\n",
     '                              f"{pointer.index} is not one of its entries")\n',
     ["TestBinding.test_the_first_source_that_answers_is_the_answer"]),

    ("with no source given at all, the reason names nothing",
     '    named = ", ".join(f"`{label}`" for label, _ in sources) or "no source at all"',
     '    named = ", ".join(f"`{label}`" for label, _ in sources)',
     ["TestBinding.test_a_pointer_with_no_source_at_all_says_so"]),

    # --- what a source's enumerated lists are ------------------------------
    ("the marker is read literally, so `1. 1. 1.` is three entries all called 1",
     "        return str(int(first) + offset)", "        return first",
     ["TestSourceShapes.test_a_repeated_marker_is_indexed_as_a_renderer_shows_it"]),

    ("one `A. something` line is enough to be an enumerated list",
     "        if len(entries) >= 2:", "        if len(entries) >= 1:",
     ["TestSourceShapes.test_a_single_entry_is_a_sentence_not_a_list"]),

    ("a table is labelled by the prose above it, never by its own header row",
     '            label = label_of(lines, start) + " " + rows[0]',
     "            label = label_of(lines, start)",
     ["TestSourceShapes.test_a_table_with_an_index_column_is_a_list_labelled_by_its_header"]),

    ("the lead-in is its last line, so a label that wraps is lost",
     "        lead.append(stripped)\n        seen_text = True",
     "        if not lead:\n            lead.append(stripped)\n        seen_text = True",
     ["TestSourceShapes.test_a_lead_in_that_wraps_still_labels_the_list"]),

    ("fenced code counts as source, so a quoted list is enumerated",
     "    lines = strip_fences(lines)", "    lines = list(lines)",
     ["TestSourceShapes.test_a_list_inside_a_fence_is_quoted_not_enumerated"]),

    ("fenced code counts as citation, so a worked example cites itself",
     "        for n, line in enumerate(strip_fences(lines), 1):\n"
     "            folded, origin = unaccent_indexed(line)\n"
     "            for m in pattern.finditer(folded):",
     "        for n, line in enumerate(lines, 1):\n"
     "            folded, origin = unaccent_indexed(line)\n"
     "            for m in pattern.finditer(folded):",
     ["TestSourceShapes.test_a_citation_inside_a_fence_is_not_a_citation"]),

    # both halves at once: `utf-8-sig` alone strips a LEADING mark and the
    # replace alone strips an interior one, so either mutated by itself leaves
    # the other answering for this fixture
    ("the byte-order mark reaches the parser, glued to the first fence",
     '        with open(path, encoding="utf-8-sig") as f:\n'
     "            text = f.read()\n"
     "    except (OSError, UnicodeDecodeError) as e:\n"
     '        fail(f"{label}: {path} cannot be read: {e}")\n'
     '    return text.replace("\\ufeff", "").splitlines()',
     '        with open(path, encoding="utf-8") as f:\n'
     "            text = f.read()\n"
     "    except (OSError, UnicodeDecodeError) as e:\n"
     '        fail(f"{label}: {path} cannot be read: {e}")\n'
     "    return text.splitlines()",
     ["TestSourceShapes.test_a_byte_order_mark_does_not_hide_the_first_fence"]),

    # --- the harvest -------------------------------------------------------
    ("the noun is quoted from the folded line, so accents are stripped in the report",
     '                spelled = line[origin[m.start("noun")]:origin[m.end("noun") - 1] + 1]',
     '                spelled = noun',
     ["TestHarvest.test_the_noun_is_quoted_as_the_trail_spelled_it"]),

    ("one line citing a pointer three times is reported as three sites",
     "            if (seen, where) == (label, line):", "            if False:",
     ["TestHarvest.test_one_line_citing_a_pointer_twice_is_one_site_with_its_count"]),

    ("a four-digit number is an index, so a year is a pointer",
     '                      rf"{SEPARATOR}(?P<idx>\\d{{1,3}}|[A-Z])\\b")',
     '                      rf"{SEPARATOR}(?P<idx>\\d{{1,4}}|[A-Z])\\b")',
     ["TestHarvest.test_a_four_digit_number_is_not_an_index"]),

    ("a lowercase letter is an index, so ordinary prose becomes a citation",
     '                      rf"{SEPARATOR}(?P<idx>\\d{{1,3}}|[A-Z])\\b")',
     '                      rf"{SEPARATOR}(?P<idx>\\d{{1,3}}|[A-Za-z])\\b")',
     ["TestHarvest.test_a_lowercase_letter_after_a_noun_is_prose"]),

    ("--noun takes one spelling, so the plural in a heading answers nothing",
     "        vocabulary[spellings[0]] = spellings",
     "        vocabulary[spellings[0]] = (spellings[0],)",
     ["TestHarvest.test_a_noun_outside_the_vocabulary_is_added_with_all_its_spellings"]),

    ("the report does not say which vocabulary it searched",
     '    print("vocabulary searched: " + ", ".join(sorted(vocabulary)))',
     "    pass",
     ["TestHarvest.test_the_report_names_the_vocabulary_it_searched"]),

    # --- the answer a reader consumes --------------------------------------
    ("an unresolved pointer carries its reason in the statement field",
     '                "statement": p.statement, "reason": p.reason,',
     '                "statement": p.statement or p.reason, "reason": p.reason,',
     ["TestReport.test_json_carries_the_binding_the_reason_and_the_counts"]),

    ("a path that is not a regular file is left to the open to discover",
     "    if not os.path.isfile(path):", "    if False:",
     ["TestReport.test_an_unreadable_citing_text_is_a_failed_run_not_an_empty_answer"]),

    ("a `label=path` argument is labelled by its basename anyway",
     "    return label, path", "    return os.path.basename(path), path",
     ["TestReport.test_a_label_names_the_source_every_address_is_read_from"]),

    # --- collisions --------------------------------------------------------
    ("every merge is read as clean, which is the forge's answer restored",
     "    if run.returncode == 0:", "    if run.returncode != 999:",
     ["TestCollisions.test_two_branches_each_clean_against_main_can_still_collide"]),

    ("a merge that succeeded is taken for one that failed",
     "    run = git(repo, \"merge-tree\", \"--write-tree\", a, b)\n"
     "    if run.returncode == 0:\n        return [], []",
     "    run = git(repo, \"merge-tree\", \"--write-tree\", a, b)\n"
     "    if run.returncode == 2:\n        return [], []",
     ["TestCollisions.test_branches_that_touch_different_files_are_reported_clean"]),

    ("only neighbouring branches are paired, so a collision two apart is missed",
     "        for b in args.refs[i + 1:]:", "        for b in args.refs[i + 1:i + 2]:",
     ["TestCollisions.test_every_pair_is_measured_not_only_the_neighbours"]),

    ("a lone branch falls into the pair loop and is reported as nothing measured",
     "    if len(args.refs) < 2:", "    if False:",
     ["TestCollisions.test_one_branch_is_answered_not_refused"]),

    ("the colliding pair is reported without the files it collides in",
     '            pairs.append({"a": a, "b": b, "conflicts": bool(paths or messages),\n'
     '                          "paths": paths, "messages": messages})',
     '            pairs.append({"a": a, "b": b, "conflicts": bool(paths or messages),\n'
     '                          "paths": [], "messages": messages})',
     ["TestCollisions.test_json_names_the_colliding_pair_and_its_paths"]),

    # the two readings of a conflicted merge, mutated together — see the module
    # docstring: either one alone survives while the other still answers
    ("a conflicted merge is read by neither of its two readings",
     "        stage = re.match(r\"^\\d{6} [0-9a-f]{4,64} ([123])\\t(.*)$\", line)\n"
     "        if stage:\n"
     "            if stage.group(2) not in paths:\n"
     "                paths.append(stage.group(2))\n"
     '        elif line.startswith("CONFLICT ("):\n'
     "            messages.append(line)\n"
     '            named = re.search(r"Merge conflict in (.+)$", line)\n'
     "            if named and named.group(1) not in paths:\n"
     "                paths.append(named.group(1))",
     "        pass",
     ["TestCollisions.test_two_branches_each_clean_against_main_can_still_collide"]),

    ("a ref nobody fetched is passed to the merge and diagnosed as a conflict",
     '        if git(repo, "rev-parse", "--verify", "--quiet", ref + "^{commit}").returncode != 0:',
     "        if False:",
     ["TestCollisionFailures.test_a_ref_that_names_no_commit_stops_the_run"]),

    ("a directory that is no repository is reported as a missing ref",
     '    if git(repo, "rev-parse", "--git-dir").returncode != 0:', "    if False:",
     ["TestCollisionFailures.test_a_directory_that_is_not_a_repository_stops_the_run"]),

    ("a merge that could not run at all is reported as a clean pair",
     "    if not paths and not messages:", "    if False:",
     ["TestCollisionFailures.test_a_merge_that_could_not_run_is_never_reported_as_clean"]),

    # --- round 1: the precedence between sources, made visible -------------
    ("the source order decides in silence again",
     "        pointer.competing = competing",
     "        pointer.competing = []",
     ["TestCompetingSources.test_a_later_source_carrying_the_same_family_is_named",
      "TestCompetingSources.test_json_carries_the_competing_sources"],
     DOSSIER),

    ("the source that WON is named as competing with itself",
     "                     if other != label for b in rest",
     "                     if True for b in rest",
     ["TestCompetingSources.test_a_single_source_says_nothing_about_competing_lists"],
     DOSSIER),

    ("an unresolved pointer is told a binding happened above it",
     "        where = \", \".join(self.competing)\n        if self.resolved:",
     "        where = \", \".join(self.competing)\n        if True:",
     ["TestCompetingSources.test_an_unresolved_pointer_is_never_told_a_binding_happened"],
     DOSSIER),

    ("ambiguity inside one source drags a second artefact into the report",
     "            # deliberately WITHOUT `competing`: the ambiguity is inside this\n"
     "            # source, and naming a different artefact would point the reader\n"
     "            # away from the two lists that actually caused it\n"
     "            pointer.reason = (f\"{len(eligible)} enumerated lists in `{label}` are \"",
     "            pointer.competing = competing\n"
     "            pointer.reason = (f\"{len(eligible)} enumerated lists in `{label}` are \"",
     ["TestCompetingSources.test_ambiguity_inside_one_source_names_no_other_artefact"],
     DOSSIER),

    ("the statement is printed as one unbroken line, however long",
     "    return textwrap.fill(\" \".join(text.split()), width=96,",
     "    return indent + \" \".join(text.split()) or textwrap.fill(\"\", width=96,",
     ["TestUncoveredGuards.test_a_statement_is_wrapped_never_printed_as_one_long_line"],
     DOSSIER),

    # --- round 1: the guards the first round left uncovered ----------------
    ("the statement is truncated again, one clause before its exception",
     '            print(wrap(p.statement, f"            says   {p.source}:{p.line}  "))',
     '            print(wrap(shorten(p.statement), f"            says   {p.source}:{p.line}  "))',
     ["TestUncoveredGuards.test_a_statement_is_quoted_whole_never_truncated"],
     DOSSIER),

    ("a citation quote is never shortened, so one line swallows the report",
     '    return text if len(text) <= width else text[:width - 1].rstrip() + "…"',
     "    return text",
     ["TestUncoveredGuards.test_a_long_citation_line_is_shortened_with_a_mark"],
     DOSSIER),

    ("the heading above a lead-in paragraph stops labelling the list",
     "    if seen_text:                # the heading sits above the paragraph we took\n"
     "        for i in range(start - 1 - len(lead), -1, -1):\n"
     "            if HEADING_RE.match(lines[i]):\n"
     "                heading = lines[i].strip()\n"
     "                break",
     "    if False:\n        pass",
     ["TestUncoveredGuards.test_a_heading_above_the_lead_in_paragraph_still_labels_the_list"],
     DOSSIER),

    ("a fence never closes, so everything after the first one is blanked",
     "        if line.strip().startswith(fence):\n            fence = None",
     "        if False:\n            fence = None",
     ["TestUncoveredGuards.test_a_fence_that_closes_does_not_blank_the_rest_of_the_file"],
     DOSSIER),

    ("a letter list ignores the offset, so every entry is called A",
     "    return chr(ord(first.upper()) + offset)", "    return first.upper()",
     ["TestUncoveredGuards.test_a_letter_list_is_indexed_by_position_like_a_numbered_one"],
     DOSSIER),

    ("a one-column table row becomes an entry whose statement is empty",
     '            if len(cells) < 2 or not re.fullmatch(r"\\d{1,3}|[A-Z]", key):',
     '            if not re.fullmatch(r"\\d{1,3}|[A-Z]", key):',
     ["TestUncoveredGuards.test_a_one_column_table_row_carries_no_statement_so_it_is_no_entry"],
     DOSSIER),

    ("one blank line ends a wrapped entry, so a loose list loses its prose",
     "            if deeper > len(indent) and held <= 1:",
     "            if deeper > len(indent) and held <= 0:",
     ["TestUncoveredGuards.test_one_blank_line_does_not_end_a_wrapped_entry"],
     DOSSIER),

    ("the plural spelling leaves the family, so a plural citation is invisible",
     '    "recomendacao": ("recomendacao", "recomendacoes", "recommendation", "recommendations"),',
     '    "recomendacao": ("recomendacao", "recommendation", "recommendations"),',
     ["TestUncoveredGuards.test_a_plural_spelling_reaches_the_same_family"],
     DOSSIER),

    # the heuristic the real implementation is NOT: same file touched by both
    ("the merge is replaced by `did both branches touch this file`",
     '    run = git(repo, "merge-tree", "--write-tree", a, b)\n'
     "    if run.returncode == 0:\n        return [], []",
     '    run = git(repo, "diff", "--name-only", a, b)\n'
     "    return sorted(set(run.stdout.split())), []\n"
     "    if run.returncode == 0:\n        return [], []",
     ["TestCollisions.test_two_branches_editing_one_file_apart_are_clean"],
     DOSSIER),
]


if __name__ == "__main__":
    sys.exit(run(MUTATIONS, "test_tk_dossier", default_src=DOSSIER))
