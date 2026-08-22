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

    def pointers(self, citing, *sources, extra=()):
        argv = ["pointers", "--citing", f"pr={citing}"]
        for n, source in enumerate(sources, 1):
            argv += ["--source", f"s{n}={source}"]
        return self.run_dossier(*argv, *extra)

    def flat(self, text):
        """One line of it. A statement is WRAPPED now, so a phrase the report
        certainly carries may still straddle two lines."""
        return " ".join(text.split())

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


# --- binding a pointer to the sentence it names -----------------------------

class TestBinding(DossierTest):
    def test_a_pointer_resolves_to_the_sentence_and_to_its_own_line(self):
        citing = self.write("pr.md", "Adopted, as recommendation 2 asks.\n")
        source = self.write("issue.md", RECOMMENDATIONS)
        r = self.pointers(citing, source)
        self.assertEqual(r.returncode, 0, r.stderr)
        block = self.entry(r.stdout, "recommendation 2")
        self.assertIn("Keep five lenses on round one.", block)
        # the ENTRY's line (7), never the line the list starts on (5)
        self.assertIn("s1:7", block)

    def test_a_continuation_line_is_part_of_the_statement(self):
        citing = self.write("pr.md", "recommendation 1 stands.\n")
        source = self.write("issue.md", RECOMMENDATIONS)
        r = self.pointers(citing, source)
        self.assertIn("running three review campaigns in parallel",
                      self.entry(r.stdout, "recommendation 1"))

    def test_a_pointer_with_no_list_of_its_family_is_unresolved_not_guessed(self):
        citing = self.write("pr.md", "It fires on item 3 alone.\n")
        source = self.write("issue.md", RECOMMENDATIONS)
        r = self.pointers(citing, source)
        self.assertEqual(r.returncode, 1, r.stdout)
        block = self.entry(r.stdout, "item 3")
        self.assertIn("no enumerated list labelled `item`", block)
        self.assertNotIn("Lower the ceiling", block)

    def test_an_index_the_list_does_not_have_is_unresolved_with_the_span(self):
        citing = self.write("pr.md", "See recommendation 9.\n")
        source = self.write("issue.md", RECOMMENDATIONS)
        r = self.pointers(citing, source)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("runs 1–3", self.entry(r.stdout, "recommendation 9"))

    def test_two_lists_of_one_family_in_one_source_bind_to_neither(self):
        citing = self.write("pr.md", "See recommendation 1.\n")
        source = self.write("issue.md", RECOMMENDATIONS + """
## Recommendations, revised

1. Something else entirely.
2. And another.
""")
        r = self.pointers(citing, source)
        self.assertEqual(r.returncode, 1, r.stdout)
        block = self.entry(r.stdout, "recommendation 1")
        self.assertIn("2 enumerated lists", block)
        self.assertNotIn("Serialize the campaigns", block)
        self.assertNotIn("Something else entirely", block)

    def test_the_first_source_that_answers_is_the_answer(self):
        citing = self.write("pr.md", "See recommendation 5.\n")
        first = self.write("first.md", RECOMMENDATIONS)
        second = self.write("second.md", """## Recommendations

1. a
2. b
3. c
4. d
5. THE LATER SOURCE
""")
        r = self.pointers(citing, first, second)
        self.assertEqual(r.returncode, 1, r.stdout)
        block = self.entry(r.stdout, "recommendation 5")
        self.assertIn("runs 1–3", block)
        self.assertNotIn("THE LATER SOURCE", block)

    def test_a_pointer_with_no_source_at_all_says_so(self):
        citing = self.write("pr.md", "See recommendation 1.\n")
        r = self.pointers(citing)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("no source at all", self.entry(r.stdout, "recommendation 1"))


# --- what counts as an enumerated list in a source --------------------------

class TestSourceShapes(DossierTest):
    def test_a_repeated_marker_is_indexed_as_a_renderer_shows_it(self):
        citing = self.write("pr.md", "See item 3.\n")
        source = self.write("issue.md", """## Items

1. first
1. second
1. third
""")
        r = self.pointers(citing, source)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("third", self.entry(r.stdout, "item 3"))

    def test_a_single_entry_is_a_sentence_not_a_list(self):
        citing = self.write("pr.md", "See criterion A.\n")
        source = self.write("issue.md", "## Criteria\n\nA. the only one\n")
        r = self.pointers(citing, source)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("no enumerated list", self.entry(r.stdout, "criterion A"))

    def test_a_table_with_an_index_column_is_a_list_labelled_by_its_header(self):
        citing = self.write("pr.md", "See block 2.\n")
        source = self.write("issue.md", """## Contract

| # | Block | Marker |
|---|---|---|
| 1 | Stats line | data-stats |
| 2 | One card per PR | data-cards |
""")
        r = self.pointers(citing, source)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("One card per PR", self.entry(r.stdout, "block 2"))

    def test_a_lead_in_that_wraps_still_labels_the_list(self):
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
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("a hundred lines or more", self.entry(r.stdout, "item 3"))

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
        r = self.pointers(citing, source)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Recomendação 2", r.stdout)
        self.assertNotIn("Recomendacao 2", r.stdout)

    def test_one_line_citing_a_pointer_twice_is_one_site_with_its_count(self):
        citing = self.write("pr.md", "item 2 here, and item 2 again on this line.\n")
        source = self.write("issue.md", "## Items\n\n1. a\n2. b\n")
        r = self.pointers(citing, source)
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
        citing = self.write("pr.md", "See requisito 2.\n")
        source = self.write("issue.md", "## Requisitos\n\n1. um\n2. dois\n")
        bare = self.pointers(citing, source)
        self.assertIn("— 0 cited ·", bare.stdout)
        named = self.pointers(citing, source,
                              extra=("--noun", "requisito,requisitos"))
        self.assertEqual(named.returncode, 0, named.stdout)
        self.assertIn("dois", self.entry(named.stdout, "requisito 2"))

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
        r = self.pointers(citing, source, extra=("--json",))
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
                             "--source", f"154={source}")
        self.assertIn("154:7", r.stdout)
        self.assertIn("cited  pr156:1", r.stdout)


# --- the precedence between sources, made visible --------------------------

class TestCompetingSources(DossierTest):
    SHORT = """## Recommendations

1. a
2. b
"""

    def test_a_later_source_carrying_the_same_family_is_named(self):
        """Measured on a real trail: a comment passed before the issue it
        comments on bound every pointer to the comment's own renumbering,
        resolved, exit 0, with no sign at all."""
        citing = self.write("pr.md", "See recommendation 2.\n")
        first = self.write("first.md", RECOMMENDATIONS)
        second = self.write("second.md", """## Recommendations, as the comment restates them

1. a
2. THE OTHER ARTEFACT
""")
        r = self.pointers(citing, first, second)
        self.assertEqual(r.returncode, 0, r.stdout)
        block = self.flat(self.entry(r.stdout, "recommendation 2"))
        self.assertIn("Keep five lenses", block)
        self.assertIn("s2:", block)
        self.assertIn("FIRST source given", block)

    def test_a_single_source_says_nothing_about_competing_lists(self):
        citing = self.write("pr.md", "See recommendation 2.\n")
        source = self.write("issue.md", RECOMMENDATIONS)
        r = self.pointers(citing, source)
        self.assertNotIn("also", r.stdout)

    def test_an_unresolved_pointer_is_never_told_a_binding_happened(self):
        """The note is written for the outcome it is attached to. Over a
        pointer that never bound, "the binding above" is the tool asserting
        something it did not do — the defect it was added to prevent."""
        citing = self.write("pr.md", "See recommendation 5.\n")
        first = self.write("first.md", self.SHORT)
        second = self.write("second.md", RECOMMENDATIONS)
        r = self.pointers(citing, first, second)
        self.assertEqual(r.returncode, 1, r.stdout)
        block = self.flat(self.entry(r.stdout, "recommendation 5"))
        self.assertIn("may be the artefact this number was written against", block)
        self.assertNotIn("FIRST source given", block)

    def test_ambiguity_inside_one_source_names_no_other_artefact(self):
        """Two lists in the FIRST source is not a precedence problem, and
        pointing at a second artefact sends the reader away from the two lists
        that actually caused it."""
        citing = self.write("pr.md", "See recommendation 1.\n")
        first = self.write("first.md", RECOMMENDATIONS + "\n## Recommendations, revised\n\n1. x\n2. y\n")
        second = self.write("second.md", RECOMMENDATIONS)
        r = self.pointers(citing, first, second)
        self.assertEqual(r.returncode, 1, r.stdout)
        block = self.entry(r.stdout, "recommendation 1")
        self.assertIn("2 enumerated lists", block)
        self.assertNotIn("also", block)

    def test_json_carries_the_competing_sources(self):
        citing = self.write("pr.md", "See recommendation 2.\n")
        first = self.write("first.md", RECOMMENDATIONS)
        second = self.write("second.md", RECOMMENDATIONS)
        r = self.pointers(citing, first, second, extra=("--json",))
        data = json.loads(r.stdout)
        self.assertEqual(data["pointers"][0]["competing"], ["s2:5"])


# --- the guards the first round left uncovered -----------------------------

class TestUncoveredGuards(DossierTest):
    def test_a_statement_is_wrapped_never_printed_as_one_long_line(self):
        """Whole and readable are not in tension: the cap belongs on the LINE.
        Real entries reached 500 characters once truncation was removed."""
        source = self.write("issue.md",
                            "## Items\n\n1. um\n2. " + "palavra " * 60 + "\n")
        citing = self.write("pr.md", "See item 2.\n")
        r = self.pointers(citing, source)
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
        r = self.pointers(citing, source)
        self.assertIn(tail, self.flat(r.stdout))
        self.assertNotIn("…", self.entry(r.stdout, "item 2").split("cited")[0])

    def test_a_long_citation_line_is_shortened_with_a_mark(self):
        citing = self.write("pr.md", "See item 2, " + "b" * 200 + "\n")
        source = self.write("issue.md", "## Items\n\n1. um\n2. dois\n")
        r = self.pointers(citing, source)
        self.assertIn("…", r.stdout)

    def test_a_heading_above_the_lead_in_paragraph_still_labels_the_list(self):
        citing = self.write("pr.md", "See recommendation 2.\n")
        source = self.write("issue.md", """## Recommendations

Adopted after discussion.

1. Serialize.
2. Keep five lenses.
""")
        r = self.pointers(citing, source)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("Keep five lenses", self.entry(r.stdout, "recommendation 2"))

    def test_a_fence_that_closes_does_not_blank_the_rest_of_the_file(self):
        citing = self.write("pr.md", "```\nsee item 3\n```\n\nBut item 2 is real.\n")
        source = self.write("issue.md", "## Items\n\n1. um\n2. dois\n")
        r = self.pointers(citing, source)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("dois", self.entry(r.stdout, "item 2"))
        self.assertNotIn("item 3", r.stdout)

    def test_a_letter_list_is_indexed_by_position_like_a_numbered_one(self):
        citing = self.write("pr.md", "See criterion C.\n")
        source = self.write("issue.md", "## Criteria\n\nA. first\nB. second\nC. third\n")
        r = self.pointers(citing, source)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("third", self.entry(r.stdout, "criterion C"))

    def test_a_one_column_table_row_carries_no_statement_so_it_is_no_entry(self):
        citing = self.write("pr.md", "See block 2.\n")
        source = self.write("issue.md", "## Blocks\n\n| # |\n|---|\n| 1 |\n| 2 |\n")
        r = self.pointers(citing, source)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("no enumerated list labelled `bloco`",
                      self.entry(r.stdout, "block 2"))

    def test_one_blank_line_does_not_end_a_wrapped_entry(self):
        citing = self.write("pr.md", "See recommendation 1.\n")
        source = self.write("issue.md", """## Recommendations

1. Serialize the campaigns.

   The multiplier was parallelism, not depth.
2. Keep five lenses.
""")
        r = self.pointers(citing, source)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("not depth", self.entry(r.stdout, "recommendation 1"))

    def test_a_plural_spelling_reaches_the_same_family(self):
        citing = self.write("pr.md", "Vide recomendações 3.\n")
        source = self.write("issue.md",
                            "## Recomendações\n\n1. um\n2. dois\n3. três\n")
        r = self.pointers(citing, source)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("três", self.entry(r.stdout, "recomendações 3"))


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
