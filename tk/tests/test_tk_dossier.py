#!/usr/bin/env python3
"""Regression suite for `tk-dossier` (../bin/tk-dossier), the measured half of a
merge dossier (contract: ../reference/dossier.md).

Run: python3 -m unittest discover -s tk/tests   (stdlib only, no deps)

Every test here is proved by MUTATION: the defect goes back into the source and
the test must fail. `mutations_dossier.py` beside this file replays each one, on
the runner `mutations_tk_contract.py` exposes.

The suite drives the real script as a subprocess and reads its EXIT CODE and its
printed answer — never an internal. The three codes are the contract: 0 clean, 1
a finding the dossier must carry, 2 the run could not be made. `collisions` gets
a real git repository built in a throwaway directory, because the whole point of
that subcommand is that it performs the merge instead of asking about it, and a
faked git would prove only that the fake was consulted.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

DOSSIER = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       os.pardir, "bin", "tk-dossier")

RECOMMENDATIONS = """# A trail

## Recommendations

1. **Serialize the campaigns.** The multiplier was not depth —
   it was running three review campaigns in parallel.
2. Keep five lenses on round one.
3. Lower the ceiling to three rounds.
"""


class DossierTest(unittest.TestCase):
    def setUp(self):
        self.tmp = os.path.realpath(tempfile.mkdtemp(prefix="tk-dossier."))
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def write(self, name, text, encoding="utf-8"):
        path = os.path.join(self.tmp, name)
        with open(path, "w", encoding=encoding) as f:
            f.write(text)
        return path

    def run_dossier(self, *argv):
        return subprocess.run([sys.executable, DOSSIER, *argv],
                              capture_output=True, text=True, timeout=120)

    def pointers(self, citing, *sources, lists=(), extra=()):
        argv = ["pointers", "--citing", f"pr={citing}"]
        for n, source in enumerate(sources, 1):
            argv += ["--source", f"s{n}={source}"]
        for one in lists:
            argv += ["--list", one]
        return self.run_dossier(*argv, *extra)

    def flat(self, text):
        """One line of it. A statement is WRAPPED now, so a phrase the report
        certainly carries may still straddle two lines."""
        return " ".join(text.split())

    def offered(self, out):
        """The candidates section, as its own text.

        A helper and not a `split()` on a word, because a fixture whose own
        prose carries that word cuts the region in the wrong place — a
        false pass nobody would see."""
        keep, lines = False, []
        for line in out.splitlines():
            if line.startswith("## the lists that could answer"):
                keep = True
                continue
            if keep:
                lines.append(line)
        return "\n".join(lines)

    def entry(self, out, head):
        """The block of lines the report prints for one pointer."""
        lines, keeping = [], False
        for line in out.splitlines():
            if line[:11].strip() in ("RESOLVED", "UNRESOLVED"):
                keeping = line.split(None, 1)[1].strip() == head
                if keeping:
                    lines.append(line)
            elif keeping and line.startswith("      "):
                lines.append(line)
        return "\n".join(lines)


# --- resolving a pointer against the list the CALLER declared ----------------
#
# The tool used to choose the list itself, by matching the pointer's noun
# against the prose around each block. It was wrong in the one way that
# matters — confidently, silently, at exit 0 — because Markdown carries no
# field naming a list, so any reading of the prose around one is a guess.
# Declaring is what replaced it, and these tests hold the two properties that
# survive: nothing is omitted, and nothing is chosen for the reader.

class TestBinding(DossierTest):
    def test_a_declared_list_resolves_to_the_sentence_and_to_its_own_line(self):
        citing = self.write("pr.md", "Adopted, as recommendation 2 asks.\n")
        source = self.write("issue.md", RECOMMENDATIONS)
        r = self.pointers(citing, source, lists=("recomendacao=s1:5",))
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        block = self.entry(r.stdout, "recommendation 2")
        self.assertIn("Keep five lenses on round one.", block)
        # the ENTRY's line (7), never the line the list starts on (5)
        self.assertIn("s1:7", block)

    def test_a_continuation_line_is_part_of_the_statement(self):
        citing = self.write("pr.md", "recommendation 1 stands.\n")
        source = self.write("issue.md", RECOMMENDATIONS)
        r = self.pointers(citing, source, lists=("recomendacao=s1:5",))
        self.assertIn("running three review campaigns in parallel",
                      self.flat(self.entry(r.stdout, "recommendation 1")))

    def test_an_undeclared_family_is_unresolved_and_names_the_flag(self):
        citing = self.write("pr.md", "It fires on item 3 alone.\n")
        source = self.write("issue.md", RECOMMENDATIONS)
        r = self.pointers(citing, source)
        self.assertEqual(r.returncode, 1, r.stdout)
        block = self.flat(self.entry(r.stdout, "item 3"))
        self.assertIn("no list is declared for `item`", block)
        self.assertIn("--list item=<source>:<line>", block)
        self.assertNotIn("Lower the ceiling", block)

    def test_an_index_the_declared_list_does_not_have_is_unresolved_with_the_span(self):
        citing = self.write("pr.md", "See recommendation 9.\n")
        source = self.write("issue.md", RECOMMENDATIONS)
        r = self.pointers(citing, source, lists=("recomendacao=s1:5",))
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("runs 1–3", self.flat(self.entry(r.stdout, "recommendation 9")))

    def test_a_second_list_of_the_same_shape_is_never_consulted(self):
        """The declared list is the only one read. Two lists that would both
        have answered is precisely the case the old inference got wrong."""
        citing = self.write("pr.md", "See recommendation 2.\n")
        source = self.write("issue.md", RECOMMENDATIONS + """
## Recommendations, as a comment restates them

1. a
2. THE OTHER LIST
""")
        r = self.pointers(citing, source, lists=("recomendacao=s1:5",))
        self.assertEqual(r.returncode, 0, r.stdout)
        block = self.entry(r.stdout, "recommendation 2")
        self.assertIn("Keep five lenses", block)
        self.assertNotIn("THE OTHER LIST", r.stdout.split("the lists each source")[0])


# --- declaring: the caller's instruction, and what happens when it is wrong --

class TestDeclaration(DossierTest):
    def test_the_candidates_are_shown_with_their_context_and_nothing_is_chosen(self):
        citing = self.write("pr.md", "See recommendation 2.\n")
        source = self.write("issue.md", RECOMMENDATIONS)
        r = self.pointers(citing, source)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("s1:5  list, entries 1–3", r.stdout)
        self.assertIn("## Recommendations", r.stdout)
        self.assertIn("`recomendacao`, cited as 2", r.stdout)
        self.assertIn("Nothing below is chosen for you", r.stdout)

    def test_a_line_carrying_no_list_is_refused_with_the_lines_that_do(self):
        citing = self.write("pr.md", "See recommendation 2.\n")
        source = self.write("issue.md", RECOMMENDATIONS)
        r = self.pointers(citing, source, lists=("recomendacao=s1:99",))
        self.assertEqual(r.returncode, 2, r.stdout)
        self.assertIn("no enumerated list starting on line 99", r.stderr)
        self.assertIn("line(s): 5", r.stderr)
        self.assertEqual(r.stdout, "")

    def test_a_source_that_was_never_given_is_refused(self):
        citing = self.write("pr.md", "See recommendation 2.\n")
        source = self.write("issue.md", RECOMMENDATIONS)
        r = self.pointers(citing, source, lists=("recomendacao=nope:5",))
        self.assertEqual(r.returncode, 2, r.stdout)
        self.assertIn("`nope` is not one of the sources given", r.stderr)

    def test_a_malformed_declaration_is_refused_with_its_shape(self):
        citing = self.write("pr.md", "See recommendation 2.\n")
        source = self.write("issue.md", RECOMMENDATIONS)
        r = self.pointers(citing, source, lists=("recomendacao=s1",))
        self.assertEqual(r.returncode, 2, r.stdout)
        self.assertIn("family=source:line", r.stderr)

    def test_json_carries_the_declarations_and_the_same_offering_as_the_text(self):
        """The two renderers read ONE computation. They were two branches once,
        and the JSON one kept an unfiltered, unordered candidate dump for a
        whole round after the text one stopped showing it."""
        citing = self.write("pr.md", "See recommendation 2 and item 9.\n")
        source = self.write("issue.md", RECOMMENDATIONS)
        r = self.pointers(citing, source, lists=("recomendacao=s1:5",),
                          extra=("--json",))
        data = json.loads(r.stdout)
        self.assertEqual(data["declarations"],
                         {"recomendacao": {"source": "s1", "line": 5}})
        # `item 9` is undeclared and no list holds a 9, so its offering is empty
        # and the declared family is absent entirely
        self.assertEqual(list(data["offering"]), ["item"])
        self.assertEqual(data["offering"]["item"], [])

    def test_json_offering_carries_what_each_list_holds(self):
        citing = self.write("pr.md", "See recommendation 2.\n")
        source = self.write("issue.md", RECOMMENDATIONS)
        r = self.pointers(citing, source, extra=("--json",))
        offered = json.loads(r.stdout)["offering"]["recomendacao"]
        self.assertEqual(len(offered), 1)
        self.assertEqual((offered[0]["line"], offered[0]["holds"],
                          offered[0]["of"]), (5, ["2"], 1))
        self.assertIn("Recommendations", offered[0]["context"])


# --- what counts as an enumerated list in a source --------------------------

class TestSourceShapes(DossierTest):
    def test_a_repeated_marker_is_indexed_as_a_renderer_shows_it(self):
        citing = self.write("pr.md", "See item 3.\n")
        source = self.write("issue.md", """## Items

1. first
1. second
1. third
""")
        r = self.pointers(citing, source, lists=("item=s1:3",))
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("third", self.entry(r.stdout, "item 3"))

    def test_a_single_entry_is_a_sentence_not_a_list(self):
        citing = self.write("pr.md", "See criterion A.\n")
        source = self.write("issue.md", "## Criteria\n\nA. the only one\n")
        r = self.pointers(citing, source)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("no list is declared", self.flat(self.entry(r.stdout, "criterion A")))
        self.assertNotIn("the only one", r.stdout)
        self.assertNotIn("entries", r.stdout)      # nothing is offered to declare

    def test_a_table_with_an_index_column_is_an_enumerated_list(self):
        citing = self.write("pr.md", "See block 2.\n")
        source = self.write("issue.md", """## Contract

| # | Block | Marker |
|---|---|---|
| 1 | Stats line | data-stats |
| 2 | One card per PR | data-cards |
""")
        r = self.pointers(citing, source, lists=("bloco=s1:3",))
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        self.assertIn("One card per PR", self.entry(r.stdout, "block 2"))

    def test_a_lead_in_that_wraps_is_shown_whole_in_the_candidate(self):
        citing = self.write("pr.md", "It fires on item 3 alone.\n")
        source = self.write("issue.md", """## The rule

The five below are the triggers. Items 1, 2 and 4 are stakes triggers;
item 3 alone is the size trigger.
The clause after them overrides all five.

1. an artifact a human judges by reading
2. real data crosses the code
3. the diff has a hundred lines or more
""")
        r = self.pointers(citing, source)
        self.assertEqual(r.returncode, 1, r.stdout)
        shown = self.flat(self.offered(r.stdout))
        self.assertIn("The five below are the triggers", shown)
        self.assertIn("overrides all five", shown)

    def test_a_list_inside_a_fence_is_quoted_not_enumerated(self):
        citing = self.write("pr.md", "See recommendation 2.\n")
        source = self.write("issue.md", """## Recommendations

```
1. quoted, not written
2. also quoted
```
""")
        r = self.pointers(citing, source)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertNotIn("also quoted", r.stdout)
        self.assertNotIn("entries 1–2", r.stdout)

    def test_a_citation_inside_a_fence_is_not_a_citation(self):
        citing = self.write("pr.md", "Nothing is cited here.\n\n```\nsee item 3\n```\n")
        r = self.pointers(citing)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("— 0 cited ·", r.stdout)
        self.assertIn("Nothing matched the vocabulary above", r.stdout)

    def test_a_byte_order_mark_does_not_hide_the_first_fence(self):
        """A BOM is not whitespace to `re`, so a file whose first line opens a
        code fence has that fence read as ordinary prose — and everything it
        quotes is harvested as a citation. `.[].body` over a comment thread
        produces exactly such a file whenever the first comment opens on a
        code block."""
        citing = self.write("pr.md", "﻿```\nsee item 3\n```\n")
        r = self.pointers(citing)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("— 0 cited ·", r.stdout)


# --- the harvest: what is cited, and how it is quoted back ------------------

class TestHarvest(DossierTest):
    def test_the_noun_is_quoted_as_the_trail_spelled_it(self):
        citing = self.write("pr.md", "Conforme a Recomendação 2, mantido.\n")
        source = self.write("issue.md", """## Recomendações

1. Serializar as campanhas.
2. Manter cinco lentes.
""")
        r = self.pointers(citing, source, lists=("recomendacao=s1:3",))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Recomendação 2", r.stdout)
        self.assertNotIn("Recomendacao 2", r.stdout)

    def test_one_line_citing_a_pointer_twice_is_one_site_with_its_count(self):
        citing = self.write("pr.md", "item 2 here, and item 2 again on this line.\n")
        source = self.write("issue.md", "## Items\n\n1. a\n2. b\n")
        r = self.pointers(citing, source, lists=("item=s1:3",))
        self.assertEqual(r.stdout.count("cited  pr:1"), 1, r.stdout)
        self.assertIn("(×2)", r.stdout)

    def test_a_four_digit_number_is_not_an_index(self):
        citing = self.write("pr.md", "issue 2026 and item 1234 are not pointers.\n")
        r = self.pointers(citing)
        self.assertIn("— 0 cited ·", r.stdout)

    def test_a_lowercase_letter_after_a_noun_is_prose(self):
        citing = self.write("pr.md", "an item a reader would skip\n")
        r = self.pointers(citing)
        self.assertIn("— 0 cited ·", r.stdout)

    def test_a_noun_outside_the_vocabulary_is_added_with_all_its_spellings(self):
        citing = self.write("pr.md", "Vide requisito 1 e requisitos 2.\n")
        source = self.write("issue.md", "## Requisitos\n\n1. um\n2. dois\n")
        bare = self.pointers(citing, source)
        self.assertIn("— 0 cited ·", bare.stdout)
        named = self.pointers(citing, source, lists=("requisito=s1:3",),
                              extra=("--noun", "requisito,requisitos"))
        self.assertEqual(named.returncode, 0, named.stderr + named.stdout)
        self.assertIn("um", self.entry(named.stdout, "requisito 1"))
        self.assertIn("dois", self.entry(named.stdout, "requisitos 2"))

    def test_the_report_names_the_vocabulary_it_searched(self):
        citing = self.write("pr.md", "nothing\n")
        r = self.pointers(citing)
        self.assertIn("vocabulary searched:", r.stdout)
        self.assertIn("recomendacao", r.stdout)


# --- the answer as a reader consumes it -------------------------------------

class TestReport(DossierTest):
    def test_json_carries_the_binding_the_reason_and_the_counts(self):
        citing = self.write("pr.md", "recommendation 2 and recommendation 9\n")
        source = self.write("issue.md", RECOMMENDATIONS)
        r = self.pointers(citing, source, lists=("recomendacao=s1:5",),
                          extra=("--json",))
        self.assertEqual(r.returncode, 1, r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual(data["counts"]["cited"], 2)
        self.assertEqual(data["counts"]["resolved"], 1)
        self.assertEqual(data["counts"]["unresolved"], 1)
        bound = [p for p in data["pointers"] if p["resolved"]][0]
        self.assertEqual((bound["index"], bound["source"], bound["line"]), ("2", "s1", 7))
        self.assertIn("five lenses", bound["statement"])
        loose = [p for p in data["pointers"] if not p["resolved"]][0]
        self.assertIsNone(loose["statement"])
        self.assertIn("runs 1–3", loose["reason"])

    def test_an_unreadable_citing_text_is_a_failed_run_not_an_empty_answer(self):
        r = self.run_dossier("pointers", "--citing", self.tmp)
        self.assertEqual(r.returncode, 2, r.stdout)
        self.assertIn("not a regular file", r.stderr)
        self.assertEqual(r.stdout, "")

    def test_a_label_names_the_source_every_address_is_read_from(self):
        citing = self.write("pr.md", "See recommendation 2.\n")
        source = self.write("issue.md", RECOMMENDATIONS)
        r = self.run_dossier("pointers", "--citing", f"pr156={citing}",
                             "--source", f"154={source}",
                             "--list", "recomendacao=154:5")
        self.assertIn("154:7", r.stdout)
        self.assertIn("cited  pr156:1", r.stdout)


# --- the guards the first round left uncovered -----------------------------

class TestUncoveredGuards(DossierTest):
    def test_a_statement_is_wrapped_never_printed_as_one_long_line(self):
        """Whole and readable are not in tension: the cap belongs on the LINE.
        Real entries reached 500 characters once truncation was removed."""
        source = self.write("issue.md",
                            "## Items\n\n1. um\n2. " + "palavra " * 60 + "\n")
        citing = self.write("pr.md", "See item 2.\n")
        r = self.pointers(citing, source, lists=("item=s1:3",))
        self.assertTrue(all(len(line) <= 100 for line in r.stdout.splitlines()),
                        max(r.stdout.splitlines(), key=len))
        self.assertEqual(r.stdout.count("palavra"), 60, r.stdout)

    def test_a_statement_is_quoted_whole_never_truncated(self):
        """A 150-character cut once dropped the exception clause that qualified
        a real statement — the half a merge decision turns on."""
        tail = "and it does NOT fire on the bookkeeping the gate itself writes"
        source = self.write("issue.md",
                            "## Items\n\n1. um\n2. " + "a" * 160 + " " + tail + "\n")
        citing = self.write("pr.md", "See item 2.\n")
        r = self.pointers(citing, source, lists=("item=s1:3",))
        self.assertIn(tail, self.flat(r.stdout))
        self.assertNotIn("…", self.entry(r.stdout, "item 2").split("cited")[0])

    def test_a_token_too_long_to_fit_is_never_split_mid_word(self):
        """A URL, a branch name and a path are one token each, and a split with
        no marker leaves the reader unable to tell a wrap from a hyphen that
        was really there. The line may overrun; the identifier may not."""
        url = "https://example.invalid/" + "a" * 90
        source = self.write("issue.md", f"## Items\n\n1. um\n2. Ver {url} aqui.\n")
        citing = self.write("pr.md", "See item 2.\n")
        r = self.pointers(citing, source, lists=("item=s1:3",))
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        self.assertIn(url, r.stdout)

    def test_a_run_of_spaces_in_the_source_does_not_survive_into_the_report(self):
        """`textwrap` replaces each whitespace CHARACTER and never collapses a
        run, so the normalisation before it is load-bearing."""
        source = self.write("issue.md",
                            "## Items\n\n1. um\n2. dois   com    espacos\n")
        citing = self.write("pr.md", "See item 2.\n")
        r = self.pointers(citing, source, lists=("item=s1:3",))
        self.assertIn("dois com espacos", r.stdout)
        self.assertNotIn("dois   com", r.stdout)

    def test_a_long_citation_line_is_shortened_with_a_mark(self):
        citing = self.write("pr.md", "See item 2, " + "b" * 200 + "\n")
        source = self.write("issue.md", "## Items\n\n1. um\n2. dois\n")
        r = self.pointers(citing, source, lists=("item=s1:3",))
        self.assertIn("…", r.stdout)

    def test_a_heading_above_a_lead_in_paragraph_is_shown_in_the_candidate(self):
        citing = self.write("pr.md", "See recommendation 2.\n")
        source = self.write("issue.md", """## Recommendations

Adopted after discussion.

1. Serialize.
2. Keep five lenses.
""")
        r = self.pointers(citing, source)
        shown = self.flat(self.offered(r.stdout))
        self.assertIn("## Recommendations", shown)
        self.assertIn("Adopted after discussion", shown)

    def test_a_fence_that_closes_does_not_blank_the_rest_of_the_file(self):
        citing = self.write("pr.md", "```\nsee item 3\n```\n\nBut item 2 is real.\n")
        source = self.write("issue.md", "## Items\n\n1. um\n2. dois\n")
        r = self.pointers(citing, source, lists=("item=s1:3",))
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("dois", self.entry(r.stdout, "item 2"))
        self.assertNotIn("item 3", r.stdout)

    def test_a_letter_list_is_indexed_by_position_like_a_numbered_one(self):
        citing = self.write("pr.md", "See criterion C.\n")
        source = self.write("issue.md", "## Criteria\n\nA. first\nB. second\nC. third\n")
        r = self.pointers(citing, source, lists=("criterio=s1:3",))
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("third", self.entry(r.stdout, "criterion C"))

    def test_a_one_column_table_row_carries_no_statement_so_it_is_no_entry(self):
        citing = self.write("pr.md", "See block 2.\n")
        source = self.write("issue.md", "## Blocks\n\n| # |\n|---|\n| 1 |\n| 2 |\n")
        r = self.pointers(citing, source)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("no list is declared", self.flat(self.entry(r.stdout, "block 2")))
        self.assertNotIn("entries", r.stdout)

    def test_one_blank_line_does_not_end_a_wrapped_entry(self):
        citing = self.write("pr.md", "See recommendation 1.\n")
        source = self.write("issue.md", """## Recommendations

1. Serialize the campaigns.

   The multiplier was parallelism, not depth.
2. Keep five lenses.
""")
        r = self.pointers(citing, source, lists=("recomendacao=s1:3",))
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("not depth", self.entry(r.stdout, "recommendation 1"))

    def test_a_plural_spelling_reaches_the_same_family(self):
        citing = self.write("pr.md", "Vide recomendações 3.\n")
        source = self.write("issue.md",
                            "## Recomendações\n\n1. um\n2. dois\n3. três\n")
        r = self.pointers(citing, source, lists=("recomendacao=s1:3",))
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        self.assertIn("três", self.entry(r.stdout, "recomendações 3"))


class TestOffering(DossierTest):
    """What the caller is given to choose from, and in what order."""

    # the SHORT list comes first in the file, so file order and coverage order
    # disagree — a sort that does nothing would leave it on top
    TWO = """## A shorter list of recommendations

1. x
2. y

## Recommendations, the proposal

1. a
2. b
3. c
4. d
5. e
6. f
"""

    def test_a_lead_in_is_shown_in_the_order_it_was_written(self):
        """The walk that collects it goes UPWARD. Shown unreversed, the
        paragraph a caller chooses by reads backwards — harmless while the
        string only fed a word match, fatal now that it IS the choice."""
        citing = self.write("pr.md", "See item 2.\n")
        source = self.write("issue.md", """## The rule

FIRST line of the lead-in.
SECOND line, in the middle.
THIRD and last line.

1. um
2. dois
""")
        r = self.pointers(citing, source)
        shown = self.flat(self.offered(r.stdout))
        self.assertIn("FIRST line of the lead-in. SECOND line, in the middle. "
                      "THIRD and last line.", shown)

    def test_a_list_holding_none_of_the_numbers_cited_is_not_offered(self):
        citing = self.write("pr.md", "See recommendation 6.\n")
        source = self.write("issue.md", self.TWO)
        r = self.pointers(citing, source)
        shown = self.offered(r.stdout)
        self.assertIn("s1:8", shown)                 # 1–6 holds 6
        self.assertNotIn("s1:3", shown)              # 1–2 cannot
        self.assertNotIn("A shorter list", shown)

    def test_the_lists_are_offered_by_how_much_of_the_trail_they_hold(self):
        citing = self.write("pr.md", "recommendation 1, recommendation 2 and "
                                     "recommendation 6.\n")
        source = self.write("issue.md", self.TWO)
        shown = self.offered(self.pointers(citing, source).stdout)
        self.assertLess(shown.index("s1:8"), shown.index("s1:3"))
        self.assertIn("holds 3 of the 3 cited", shown)
        self.assertIn("holds 2 of the 3 cited", shown)

    def test_a_family_is_scored_only_against_the_numbers_IT_cites(self):
        """Pooling every family's indexes credited a list for holding a number
        another family cited: on a real trail the recommendations list scored a
        perfect 2 of 2 for `item`, whose statements were in a file never
        passed."""
        citing = self.write("pr.md", "See recommendation 1 and item 4.\n")
        source = self.write("issue.md", """## Recommendations

1. Alpha
2. Beta

## Items

1. First
2. Second
3. Third
4. Fourth
""")
        shown = self.offered(self.pointers(citing, source).stdout)
        item = shown.split("`item`")[1].split("`recomendacao`")[0]
        self.assertIn("s1:8", item)
        self.assertNotIn("s1:3", item)          # 1–2 cannot hold a 4
        self.assertIn("cited as 4", shown)
        self.assertIn("cited as 1", shown)

    def test_a_family_already_declared_is_not_asked_for_again(self):
        """An index the declared list lacks is a defect in the trail or in the
        choice — not a missing declaration, and re-asking for one sends the
        reader to fix something that is not broken."""
        citing = self.write("pr.md", "See recommendation 9.\n")
        source = self.write("issue.md", RECOMMENDATIONS)
        r = self.pointers(citing, source, lists=("recomendacao=s1:5",))
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertEqual(self.offered(r.stdout), "")

    def test_the_header_counts_what_it_says_it_counts(self):
        citing = self.write("pr.md", "recommendation 1, recommendation 2 and "
                                     "recommendation 9.\n")
        source = self.write("issue.md", RECOMMENDATIONS)
        r = self.pointers(citing, source, lists=("recomendacao=s1:5",))
        self.assertIn("3 cited · 2 resolved · 1 unresolved", r.stdout)


    def test_with_nothing_to_offer_the_re_run_line_is_not_printed(self):
        """`declared` refuses a source that was not given, so telling a caller
        with no sources to re-run with `--list` is an instruction that cannot
        be carried out."""
        citing = self.write("pr.md", "See recommendation 2.\n")
        r = self.pointers(citing)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertNotIn("Then re-run", r.stdout)
        self.assertIn("no source given holds a list", r.stdout)


class TestGuardsAMutantFound(DossierTest):
    """Guards a mutation round proved live and unprotected. Each one was found
    by writing the defect back and watching the whole suite stay green."""

    def test_two_families_citing_the_same_number_are_two_pointers(self):
        citing = self.write("pr.md", "item 3 and recommendation 3.\n")
        source = self.write("issue.md", "## Items\n\n1. a\n2. b\n3. ITEM THREE\n")
        r = self.pointers(citing, source, lists=("item=s1:3",))
        self.assertIn("2 cited", r.stdout)
        self.assertIn("ITEM THREE", self.entry(r.stdout, "item 3"))
        self.assertIn("no list is declared for `recomendacao`",
                      self.flat(self.entry(r.stdout, "recommendation 3")))

    def test_one_line_number_in_two_citing_texts_is_two_sites(self):
        one = self.write("a.md", "See item 2.\n")
        two = self.write("b.md", "See item 2 again.\n")
        source = self.write("issue.md", "## Items\n\n1. a\n2. b\n")
        r = self.run_dossier("pointers", "--citing", f"one={one}",
                             "--citing", f"two={two}",
                             "--source", f"s1={source}", "--list", "item=s1:3")
        self.assertIn("cited  one:1", r.stdout)
        self.assertIn("cited  two:1", r.stdout)
        self.assertNotIn("(×2)", r.stdout)

    def test_a_blank_line_ends_the_lead_in_shown_for_a_list(self):
        citing = self.write("pr.md", "See item 2.\n")
        source = self.write("issue.md", """## The rule

AN UNRELATED PARAGRAPH about something else.

The real lead-in.

1. um
2. dois
""")
        shown = self.offered(self.pointers(citing, source).stdout)
        self.assertIn("The real lead-in.", shown)
        self.assertNotIn("AN UNRELATED PARAGRAPH", shown)

    def test_a_tilde_fence_hides_what_it_quotes_like_a_backtick_one(self):
        citing = self.write("pr.md", "~~~\nsee item 3\n~~~\n\nBut item 2 is real.\n")
        source = self.write("issue.md", "## Items\n\n1. a\n2. dois\n")
        r = self.pointers(citing, source, lists=("item=s1:3",))
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        self.assertIn("dois", self.entry(r.stdout, "item 2"))
        self.assertNotIn("item 3", r.stdout)

    def test_an_index_cell_wearing_emphasis_is_still_an_index(self):
        citing = self.write("pr.md", "See block 2.\n")
        source = self.write("issue.md", """## Contract

| # | Block |
|---|---|
| **1** | Stats |
| **2** | Cards |
""")
        r = self.pointers(citing, source, lists=("bloco=s1:3",))
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        self.assertIn("Cards", self.entry(r.stdout, "block 2"))

    def test_lists_tied_on_coverage_keep_the_order_the_sources_came_in(self):
        citing = self.write("pr.md", "See recommendation 1.\n")
        first = self.write("first.md", "## Recommendations, one\n\n1. a\n2. b\n")
        second = self.write("second.md", "## Recommendations, two\n\n1. x\n2. y\n")
        shown = self.offered(self.pointers(citing, first, second).stdout)
        self.assertLess(shown.index("s1:3"), shown.index("s2:3"))


class TestDeclarationEdges(DossierTest):
    def test_a_family_declared_in_capitals_is_the_same_family(self):
        citing = self.write("pr.md", "See recommendation 2.\n")
        source = self.write("issue.md", RECOMMENDATIONS)
        r = self.pointers(citing, source, lists=("RECOMENDACAO=s1:5",))
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        self.assertIn("Keep five lenses", self.entry(r.stdout, "recommendation 2"))

    def test_a_line_that_is_not_a_number_is_refused_not_a_traceback(self):
        citing = self.write("pr.md", "See recommendation 2.\n")
        source = self.write("issue.md", RECOMMENDATIONS)
        r = self.pointers(citing, source, lists=("recomendacao=s1:abc",))
        self.assertEqual(r.returncode, 2, r.stdout)
        self.assertIn("family=source:line", r.stderr)
        self.assertNotIn("Traceback", r.stderr)


# --- collisions: the merge performed, not the forge asked -------------------

class CollisionTest(DossierTest):
    def setUp(self):
        super().setUp()
        self.repo = os.path.join(self.tmp, "repo")
        os.makedirs(self.repo)
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "suite@example.invalid")
        self.git("config", "user.name", "suite")
        self.commit("base", {"f.md": "one\ntwo\nthree\n", "other.md": "x\n"})

    def git(self, *argv):
        return subprocess.run(["git", "-C", self.repo, *argv], check=True,
                              capture_output=True, text=True)

    def commit(self, message, files):
        for name, text in files.items():
            with open(os.path.join(self.repo, name), "w", encoding="utf-8") as f:
                f.write(text)
        self.git("add", "-A")
        self.git("commit", "-qm", message)

    def branch(self, name, files):
        self.git("checkout", "-q", "main")
        self.git("checkout", "-qb", name)
        self.commit(name, files)
        self.git("checkout", "-q", "main")

    def collisions(self, *refs, extra=()):
        return self.run_dossier("collisions", "--repo", self.repo, *refs, *extra)


class TestCollisions(CollisionTest):
    def test_two_branches_each_clean_against_main_can_still_collide(self):
        """The acceptance criterion, and the reason this subcommand exists."""
        self.branch("a", {"f.md": "one\nA CHANGED IT\nthree\n"})
        self.branch("b", {"f.md": "one\nB CHANGED IT\nthree\n"})

        # each one alone is what the forge would call MERGEABLE/CLEAN
        for ref in ("a", "b"):
            alone = self.collisions("main", ref)
            self.assertEqual(alone.returncode, 0, alone.stdout)
            self.assertIn("clean", alone.stdout)

        together = self.collisions("a", "b")
        self.assertEqual(together.returncode, 1, together.stdout)
        self.assertIn("COLLIDES  a × b", together.stdout)
        self.assertIn("f.md", together.stdout)

    def test_two_branches_editing_one_file_apart_are_clean(self):
        """The merge is PERFORMED, so two edits far apart in one file are
        clean. Nothing else in this suite tells a real three-way merge from a
        `did both branches touch this file` heuristic, which would call this
        pair colliding and pass every other test here."""
        self.commit("longer", {"f.md": "".join(f"line {n}\n" for n in range(1, 12))})
        self.branch("a", {"f.md": "A CHANGED IT\n"
                          + "".join(f"line {n}\n" for n in range(2, 12))})
        self.branch("b", {"f.md": "".join(f"line {n}\n" for n in range(1, 11))
                          + "B CHANGED IT\n"})
        r = self.collisions("a", "b")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("clean     a × b", r.stdout)

    def test_branches_that_touch_different_files_are_reported_clean(self):
        self.branch("a", {"f.md": "one\nA CHANGED IT\nthree\n"})
        self.branch("c", {"other.md": "y\n"})
        r = self.collisions("a", "c")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("clean     a × c", r.stdout)
        self.assertNotIn("COLLIDES", r.stdout)

    def test_every_pair_is_measured_not_only_the_neighbours(self):
        self.branch("a", {"f.md": "one\nA\nthree\n"})
        self.branch("c", {"other.md": "y\n"})
        self.branch("b", {"f.md": "one\nB\nthree\n"})
        r = self.collisions("a", "c", "b")
        self.assertIn("3 pair(s)", r.stdout)
        self.assertIn("1 colliding", r.stdout)
        self.assertIn("COLLIDES  a × b", r.stdout)

    def test_one_branch_is_answered_not_refused(self):
        self.branch("a", {"f.md": "one\nA\nthree\n"})
        r = self.collisions("a")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("no pair to measure", r.stdout)

    def test_json_names_the_colliding_pair_and_its_paths(self):
        self.branch("a", {"f.md": "one\nA\nthree\n"})
        self.branch("b", {"f.md": "one\nB\nthree\n"})
        r = self.collisions("a", "b", extra=("--json",))
        data = json.loads(r.stdout)
        self.assertEqual(data["counts"], {"measured": 1, "colliding": 1})
        self.assertEqual(data["pairs"][0]["paths"], ["f.md"])


class TestCollisionFailures(CollisionTest):
    def test_a_ref_that_names_no_commit_stops_the_run(self):
        self.branch("a", {"f.md": "one\nA\nthree\n"})
        r = self.collisions("a", "feat/never-fetched")
        self.assertEqual(r.returncode, 2, r.stdout)
        self.assertIn("names no commit", r.stderr)
        self.assertEqual(r.stdout, "")

    def test_a_directory_that_is_not_a_repository_stops_the_run(self):
        r = self.run_dossier("collisions", "--repo", self.tmp, "main")
        self.assertEqual(r.returncode, 2, r.stdout)
        self.assertIn("not a git repository", r.stderr)

    def test_a_merge_that_could_not_run_is_never_reported_as_clean(self):
        """`merge-tree` exits 1 for a conflict AND for a merge it refused —
        an unknown flag on an older git. Reading the second as a clean pair is
        the silent lie the whole subcommand exists to stop telling."""
        self.branch("a", {"f.md": "one\nA\nthree\n"})
        self.branch("b", {"f.md": "one\nB\nthree\n"})
        real = shutil.which("git")
        shim_dir = os.path.join(self.tmp, "shim")
        os.makedirs(shim_dir)
        shim = os.path.join(shim_dir, "git")
        with open(shim, "w", encoding="utf-8") as f:
            f.write(f'#!/bin/sh\nfor a in "$@"; do\n'
                    f'  [ "$a" = "merge-tree" ] && exit 1\ndone\n'
                    f'exec {real} "$@"\n')
        os.chmod(shim, 0o755)
        env = dict(os.environ, PATH=shim_dir + os.pathsep + os.environ["PATH"])
        r = subprocess.run([sys.executable, DOSSIER, "collisions",
                            "--repo", self.repo, "a", "b"],
                           env=env, capture_output=True, text=True, timeout=120)
        self.assertEqual(r.returncode, 2, r.stdout)
        self.assertIn("without naming a conflict", r.stderr)
        self.assertNotIn("clean", r.stdout)


if __name__ == "__main__":
    unittest.main()
