#!/usr/bin/env python3
"""Mutation harness for the `tk-dossier` suite — each defect put back, and the
test that claims to prove it must fall.

Run: python3 tk/tests/mutations_dossier.py

Entries only: the runner is the one `mutations_tk_contract.py` exposes, through
the seam its docstring describes. Same contract as its own: an anchor must
match EXACTLY ONCE, a mutant no named test kills is a SURVIVOR, and a test no
entry names is reported UNPROVED, because a green score counts only the mutants
somebody wrote.

WHAT THIS SUITE LEARNED THE EXPENSIVE WAY. An earlier version of `tk-dossier`
chose which enumerated list a pointer meant, by matching the pointer's noun
against the prose around each block. Two review rounds and a design escalation
later, that inference is gone — the caller declares the list — and the reason
is written here because it is the shape of defect these entries exist to catch:
the tool asserting to the reader something that is not true of what it did. A
wrong binding does not crash. It reads exactly like a right one.

ONE ENTRY MUTATES TWO GUARDS AT ONCE, and says so where it sits: `conflicts_of`
reads a conflicted merge two ways on purpose, and either reading alone would
survive its own mutation while the other still answered.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mutations_tk_contract import run   # noqa: E402  (the path above enables it)

DOSSIER = os.path.join("bin", "tk-dossier")

MUTATIONS = [
    # --- resolving against the list the CALLER declared --------------------
    ("a declared pointer is addressed to the line its LIST starts on, not its entry",
     "        pointer.line, pointer.statement = block.entries[pointer.index]",
     "        pointer.line = block.line\n"
     "        pointer.statement = block.entries[pointer.index][1]",
     ["TestBinding.test_a_declared_list_resolves_to_the_sentence_and_to_its_own_line"],
     DOSSIER),

    ("an entry stops at its first line, so a wrapped statement is half a sentence",
     "            if deeper > len(indent) and held <= 1:",
     "            if False:",
     ["TestBinding.test_a_continuation_line_is_part_of_the_statement"],
     DOSSIER),

    ("an undeclared family binds anyway, to whatever list came first",
     "    if pointer.family not in declarations:",
     "    if pointer.family not in declarations and False:",
     ["TestBinding.test_an_undeclared_family_is_unresolved_and_names_the_flag"],
     DOSSIER),

    ("the reason for an out-of-range pointer does not name the span it missed",
     '        return f"{keys[0]}–{keys[-1]}" if len(keys) > 1 else keys[0]',
     "        return keys[0]",
     ["TestBinding.test_an_index_the_declared_list_does_not_have_is_unresolved_with_the_span"],
     DOSSIER),

    ("the declared line is ignored and the source's last list read instead",
     "            return family.lower(), source, block",
     "            return family.lower(), source, known[source][-1]",
     ["TestBinding.test_a_second_list_of_the_same_shape_is_never_consulted"],
     DOSSIER),

    # --- declaring: the caller's instruction, and what happens when it fails
    ("the candidates are hidden, so there is nothing to declare from",
     "    if undeclared:",
     "    if False:",
     ["TestDeclaration.test_the_candidates_are_shown_with_their_context_and_nothing_is_chosen"],
     DOSSIER),

    ("the context of a candidate is not shown, so choosing one is a coin flip",
     '            print(wrap(b.context or "(no heading or lead-in above it)",',
     '            print(wrap("" or "(no heading or lead-in above it)",',
     ["TestDeclaration.test_the_candidates_are_shown_with_their_context_and_nothing_is_chosen"],
     DOSSIER),

    ("a declared line that carries no list falls through to the first one",
     '    at = ", ".join(str(b.line) for b in known[source]) or "none at all"',
     "    return family.lower(), source, known[source][0]",
     ["TestDeclaration.test_a_line_carrying_no_list_is_refused_with_the_lines_that_do"],
     DOSSIER),

    ("a source nobody gave is treated as one that exists",
     "    if source not in known:",
     "    if False:",
     ["TestDeclaration.test_a_source_that_was_never_given_is_refused"],
     DOSSIER),

    ("a malformed declaration is parsed as far as it goes",
     "    if not (sep and colon) or not line.isdigit() or not family:",
     "    if False:",
     ["TestDeclaration.test_a_malformed_declaration_is_refused_with_its_shape"],
     DOSSIER),

    ("the machine-readable answer drops what was declared",
     '            "declarations": {family: {"source": source, "line": block.line}\n'
     '                             for family, (source, block) in declarations.items()},',
     '            "declarations": {},',
     ["TestDeclaration.test_json_carries_the_declarations_and_the_candidates"],
     DOSSIER),

    ("the machine-readable answer drops the candidates it offered",
     '            "candidates": [{"source": label, "line": b.line, "kind": b.kind,\n'
     '                            "span": b.span(), "context": " ".join(b.context.split())}\n'
     '                           for label, blocks in sources for b in blocks],',
     '            "candidates": [],',
     ["TestDeclaration.test_json_carries_the_declarations_and_the_candidates"],
     DOSSIER),

    # --- what a source's enumerated lists are ------------------------------
    ("the marker is read literally, so `1. 1. 1.` is three entries all called 1",
     "        return str(int(first) + offset)", "        return first",
     ["TestSourceShapes.test_a_repeated_marker_is_indexed_as_a_renderer_shows_it"],
     DOSSIER),

    ("one `A. something` line is enough to be an enumerated list, and to be offered",
     "        if len(entries) >= 2:", "        if len(entries) >= 1:",
     ["TestSourceShapes.test_a_single_entry_is_a_sentence_not_a_list"],
     DOSSIER),

    ("a table with an index column is not read as an enumerated list at all",
     '            if len(cells) < 2 or not re.fullmatch(r"\\d{1,3}|[A-Z]", key):',
     "            if True:",
     ["TestSourceShapes.test_a_table_with_an_index_column_is_an_enumerated_list"],
     DOSSIER),

    ("the lead-in is its last line, so the context shown loses its opening",
     "        lead.append(stripped)\n        seen_text = True",
     "        if not lead:\n            lead.append(stripped)\n        seen_text = True",
     ["TestSourceShapes.test_a_lead_in_that_wraps_is_shown_whole_in_the_candidate"],
     DOSSIER),

    ("fenced code counts as source, so a quoted list becomes a candidate",
     "    lines = strip_fences(lines)", "    lines = list(lines)",
     ["TestSourceShapes.test_a_list_inside_a_fence_is_quoted_not_enumerated"],
     DOSSIER),

    ("fenced code counts as citation, so a worked example cites itself",
     "        for n, line in enumerate(strip_fences(lines), 1):",
     "        for n, line in enumerate(lines, 1):",
     ["TestSourceShapes.test_a_citation_inside_a_fence_is_not_a_citation"],
     DOSSIER),

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
     ["TestSourceShapes.test_a_byte_order_mark_does_not_hide_the_first_fence"],
     DOSSIER),

    # --- the harvest -------------------------------------------------------
    ("the noun is quoted from the folded line, so accents are stripped in the report",
     '                spelled = line[origin[m.start("noun")]:origin[m.end("noun") - 1] + 1]',
     "                spelled = noun",
     ["TestHarvest.test_the_noun_is_quoted_as_the_trail_spelled_it"],
     DOSSIER),

    ("one line citing a pointer three times is reported as three sites",
     "            if (seen, where) == (label, line):", "            if False:",
     ["TestHarvest.test_one_line_citing_a_pointer_twice_is_one_site_with_its_count"],
     DOSSIER),

    ("a four-digit number is an index, so a year is a pointer",
     '                      rf"{SEPARATOR}(?P<idx>\\d{{1,3}}|[A-Z])\\b")',
     '                      rf"{SEPARATOR}(?P<idx>\\d{{1,4}}|[A-Z])\\b")',
     ["TestHarvest.test_a_four_digit_number_is_not_an_index"],
     DOSSIER),

    ("a lowercase letter is an index, so ordinary prose becomes a citation",
     '                      rf"{SEPARATOR}(?P<idx>\\d{{1,3}}|[A-Z])\\b")',
     '                      rf"{SEPARATOR}(?P<idx>\\d{{1,3}}|[A-Za-z])\\b")',
     ["TestHarvest.test_a_lowercase_letter_after_a_noun_is_prose"],
     DOSSIER),

    ("--noun takes one spelling, so the plural in a citation answers nothing",
     "        vocabulary[spellings[0]] = spellings",
     "        vocabulary[spellings[0]] = (spellings[0],)",
     ["TestHarvest.test_a_noun_outside_the_vocabulary_is_added_with_all_its_spellings"],
     DOSSIER),

    ("the report does not say which vocabulary it searched",
     '    print("vocabulary searched: " + ", ".join(sorted(vocabulary)))',
     "    pass",
     ["TestHarvest.test_the_report_names_the_vocabulary_it_searched"],
     DOSSIER),

    # --- the answer a reader consumes --------------------------------------
    ("an unresolved pointer carries its reason in the statement field",
     '                "statement": p.statement, "reason": p.reason,',
     '                "statement": p.statement or p.reason, "reason": p.reason,',
     ["TestReport.test_json_carries_the_binding_the_reason_and_the_counts"],
     DOSSIER),

    ("a path that is not a regular file is left to the open to discover",
     "    if not os.path.isfile(path):", "    if False:",
     ["TestReport.test_an_unreadable_citing_text_is_a_failed_run_not_an_empty_answer"],
     DOSSIER),

    ("a `label=path` argument is labelled by its basename anyway",
     "    return label, path", "    return os.path.basename(path), path",
     ["TestReport.test_a_label_names_the_source_every_address_is_read_from"],
     DOSSIER),

    # --- the guards a review round proved live and untested ----------------
    ("the statement is truncated again, one clause before its exception",
     '            print(wrap(p.statement, f"            says   {p.source}:{p.line}  "))',
     '            print(wrap(shorten(p.statement), f"            says   {p.source}:{p.line}  "))',
     ["TestUncoveredGuards.test_a_statement_is_quoted_whole_never_truncated"],
     DOSSIER),

    ("the statement is printed as one unbroken line, however long",
     "    return textwrap.fill(\" \".join(text.split()), width=96,",
     "    return indent + \" \".join(text.split()) or textwrap.fill(\"\", width=96,",
     ["TestUncoveredGuards.test_a_statement_is_wrapped_never_printed_as_one_long_line"],
     DOSSIER),

    ("a token too long to fit is split mid-word again",
     "                         break_long_words=False, break_on_hyphens=False)",
     "                         break_long_words=True, break_on_hyphens=True)",
     ["TestUncoveredGuards.test_a_token_too_long_to_fit_is_never_split_mid_word"],
     DOSSIER),

    ("the whitespace run reaches textwrap, which replaces but never collapses",
     '    return textwrap.fill(" ".join(text.split()), width=96,',
     "    return textwrap.fill(text, width=96,",
     ["TestUncoveredGuards.test_a_run_of_spaces_in_the_source_does_not_survive_into_the_report"],
     DOSSIER),

    ("a citation quote is never shortened, so one line swallows the report",
     '    return text if len(text) <= width else text[:width - 1].rstrip() + "…"',
     "    return text",
     ["TestUncoveredGuards.test_a_long_citation_line_is_shortened_with_a_mark"],
     DOSSIER),

    ("the heading above a lead-in paragraph stops reaching the context shown",
     "    if seen_text:                # the heading sits above the paragraph we took\n"
     "        for i in range(start - 1 - len(lead), -1, -1):\n"
     "            if HEADING_RE.match(lines[i]):\n"
     "                heading = lines[i].strip()\n"
     "                break",
     "    if False:\n        pass",
     ["TestUncoveredGuards.test_a_heading_above_a_lead_in_paragraph_is_shown_in_the_candidate"],
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

    # --- what the caller is given to choose from ---------------------------
    ("the lead-in is shown in the order the walk collected it, which is backwards",
     '    return heading + " " + " ".join(reversed(lead))',
     '    return heading + " " + " ".join(lead)',
     ["TestOffering.test_a_lead_in_is_shown_in_the_order_it_was_written"],
     DOSSIER),

    ("a list holding none of the numbers cited is offered anyway",
     "        offered = sorted((o for o in offered if o[2]),",
     "        offered = sorted((o for o in offered),",
     ["TestOffering.test_a_list_holding_none_of_the_numbers_cited_is_not_offered"],
     DOSSIER),

    ("the lists are offered in file order, not by what they could account for",
     "                         key=lambda o: -len(o[2]))",
     "                         key=lambda o: 0)",
     ["TestOffering.test_the_lists_are_offered_by_how_much_of_the_trail_they_hold"],
     DOSSIER),

    ("a candidate does not say how much of the trail it holds",
     '            print(f"{label}:{b.line}  {b.kind}, entries {b.span()} — holds "\n'
     '                  f"{len(covers)} of the {len(wanted)} number(s) cited")',
     '            print(f"{label}:{b.line}  {b.kind}, entries {b.span()}")',
     ["TestOffering.test_the_lists_are_offered_by_how_much_of_the_trail_they_hold"],
     DOSSIER),

    ("a family already declared is asked for all over again",
     "    undeclared = sorted({p.family for p in unresolved\n"
     "                         if p.family not in declarations})",
     "    undeclared = sorted({p.family for p in unresolved})",
     ["TestOffering.test_a_family_already_declared_is_not_asked_for_again"],
     DOSSIER),

    ("the header line counts the wrong things",
     '    print(f"## pointers — {len(pointers)} cited · {len(resolved)} resolved · "\n'
     '          f"{len(unresolved)} unresolved\\n")',
     '    print(f"## pointers — {len(unresolved)} cited · {len(resolved)} resolved · "\n'
     '          f"{len(pointers)} unresolved\\n")',
     ["TestOffering.test_the_header_counts_what_it_says_it_counts"],
     DOSSIER),

    ("with nothing to offer, the caller is told to re-run with --list anyway",
     "        if offered:\n"
     '            print("\\nThen re-run with `--list <family>=<source>:<line>` for each.")',
     '        if True:\n            print("\\nThen re-run with `--list <family>=<source>:<line>` for each.")',
     ["TestOffering.test_with_nothing_to_offer_the_re_run_line_is_not_printed"],
     DOSSIER),

    ("a family declared in capitals is a different family",
     "            return family.lower(), source, block",
     "            return family, source, block",
     ["TestDeclarationEdges.test_a_family_declared_in_capitals_is_the_same_family"],
     DOSSIER),

    ("a line that is not a number reaches int() and the run dies on a traceback",
     "    if not (sep and colon) or not line.isdigit() or not family:",
     "    if not (sep and colon) or not family:",
     ["TestDeclarationEdges.test_a_line_that_is_not_a_number_is_refused_not_a_traceback"],
     DOSSIER),

    # --- collisions --------------------------------------------------------
    ("every merge is read as clean, which is the forge's answer restored",
     "    if run.returncode == 0:", "    if run.returncode != 999:",
     ["TestCollisions.test_two_branches_each_clean_against_main_can_still_collide"],
     DOSSIER),

    ("a merge that succeeded is taken for one that failed",
     '    run = git(repo, "merge-tree", "--write-tree", a, b)\n'
     "    if run.returncode == 0:\n        return [], []",
     '    run = git(repo, "merge-tree", "--write-tree", a, b)\n'
     "    if run.returncode == 2:\n        return [], []",
     ["TestCollisions.test_branches_that_touch_different_files_are_reported_clean"],
     DOSSIER),

    ("only neighbouring branches are paired, so a collision two apart is missed",
     "        for b in args.refs[i + 1:]:", "        for b in args.refs[i + 1:i + 2]:",
     ["TestCollisions.test_every_pair_is_measured_not_only_the_neighbours"],
     DOSSIER),

    ("a lone branch falls into the pair loop and is reported as nothing measured",
     "    if len(args.refs) < 2:", "    if False:",
     ["TestCollisions.test_one_branch_is_answered_not_refused"],
     DOSSIER),

    ("the colliding pair is reported without the files it collides in",
     '            pairs.append({"a": a, "b": b, "conflicts": bool(paths or messages),\n'
     '                          "paths": paths, "messages": messages})',
     '            pairs.append({"a": a, "b": b, "conflicts": bool(paths or messages),\n'
     '                          "paths": [], "messages": messages})',
     ["TestCollisions.test_json_names_the_colliding_pair_and_its_paths"],
     DOSSIER),

    # the merge is PERFORMED. This mutant is the heuristic it is not: the two
    # branches touched one file, so call it a collision
    ("the merge is replaced by `did both branches touch this file`",
     '    run = git(repo, "merge-tree", "--write-tree", a, b)\n'
     "    if run.returncode == 0:\n        return [], []",
     '    run = git(repo, "diff", "--name-only", a, b)\n'
     "    return sorted(set(run.stdout.split())), []\n"
     "    if run.returncode == 0:\n        return [], []",
     ["TestCollisions.test_two_branches_editing_one_file_apart_are_clean"],
     DOSSIER),

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
     ["TestCollisions.test_two_branches_each_clean_against_main_can_still_collide"],
     DOSSIER),

    ("a ref nobody fetched is passed to the merge and diagnosed as a conflict",
     '        if git(repo, "rev-parse", "--verify", "--quiet", ref + "^{commit}").returncode != 0:',
     "        if False:",
     ["TestCollisionFailures.test_a_ref_that_names_no_commit_stops_the_run"],
     DOSSIER),

    ("a directory that is no repository is reported as a missing ref",
     '    if git(repo, "rev-parse", "--git-dir").returncode != 0:', "    if False:",
     ["TestCollisionFailures.test_a_directory_that_is_not_a_repository_stops_the_run"],
     DOSSIER),

    ("a merge that could not run at all is reported as a clean pair",
     "    if not paths and not messages:", "    if False:",
     ["TestCollisionFailures.test_a_merge_that_could_not_run_is_never_reported_as_clean"],
     DOSSIER),
]


if __name__ == "__main__":
    sys.exit(run(MUTATIONS, "test_tk_dossier", default_src=DOSSIER))
