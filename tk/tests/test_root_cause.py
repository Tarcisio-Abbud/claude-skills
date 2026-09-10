#!/usr/bin/env python3
"""Doc-conformance proof for the root-cause audit, `../skills/kickoff/ROOT-CAUSE.md`.

Run: python3 -m unittest discover -s tk/tests   (stdlib only, no deps)

WHAT THE FILE IS. The step that decides the CUT before `tk-queue pack` — which items
are still real, which are one item said twice, which lanes can run at once — plus the
tracker import that has to precede it. It is read from step 1 of `AFK.md`, and it is
not `AUDIT.md`: that one audits the spec and ticket TEXT after the claim, this one
audits the queue against the code before anything is claimed.

WHAT IS ASSERTED IS THE PROSE, because prose is what an orchestrator executes here.
Nothing in this file runs a package. Two properties carry the weight:

- the five lists are NAMED and each one says what verifies it — a list with no check
  beside it is a list an orchestrator fills in from the item's own text, which is the
  single failure this step exists to prevent;
- the tracker import is prescribed with the three provenance flags and WITHOUT
  `--blocked-by` between siblings. That flag would make `pack` drop every blocked
  sibling out of the package (ledger `blocked-by-na-fila`), and the eight tickets that
  sat outside the queue on 2026-09-08 are why the import is written down at all.

VACUITY GUARD FIRST. Every check below cuts a slice on a heading, and a heading that
moved would leave the check reading an empty string and passing. `test_every_section_
the_checks_cut_on_is_still_there` is what refuses that, and the slices are asserted
non-empty as they are taken.

WHAT IS NOT PROVED HERE: that the audit ever runs, that the threshold of 20 is the
right number (it is derived in the file and says so), or that a prescribed command
executes. The `tk-queue` lines are read by `test_afk_audit.py`'s sweep, which asks
every pasteable command in the plugin's prose to quote its metavariables and to name
the queue it writes; running the `add` is impossible from a subagent by design.
"""

import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
KICKOFF = os.path.join(HERE, os.pardir, "skills", "kickoff")
ROOT_CAUSE = os.path.join(KICKOFF, "ROOT-CAUSE.md")
AFK = os.path.join(KICKOFF, "AFK.md")
FLEET = os.path.join(HERE, os.pardir, "skills", "fleet", "SKILL.md")

SECTIONS = ("The tracker import comes first",
            "The five lists the audit returns",
            "Fusing two items: `edit`, then `cancel`",
            "The two topology rules",
            "chain, parallelize, route",
            "Who runs it")

THE_FIVE_LISTS = ("Already done on main",
                  "Dead by redesign",
                  "Fusions",
                  "Disjoint lanes, by FILE and not by theme",
                  "Out of the cut")


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


class DocTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = read(ROOT_CAUSE)
        cls.afk = read(AFK)

    def section(self, title):
        """The body under `## title`, up to the next `## ` — asserted non-empty."""
        pattern = re.compile(r"^## " + re.escape(title) + r"\s*$(.*?)(?=^## |\Z)",
                             re.M | re.S)
        found = pattern.findall(self.text)
        self.assertEqual(len(found), 1,
                         f"`## {title}` is not in ROOT-CAUSE.md exactly once — the "
                         f"check that cuts on it would read an empty string")
        self.assertTrue(found[0].strip(), f"`## {title}` is empty")
        return found[0]

    def bullets(self, body):
        """The `- ` items of `body`, continuation lines folded in."""
        items, current = [], None
        for line in body.splitlines():
            if line.startswith("- "):
                if current is not None:
                    items.append(" ".join(current.split()))
                current = line[2:]
            elif current is not None and line.startswith("  "):
                current += " " + line.strip()
            elif current is not None and not line.strip():
                items.append(" ".join(current.split()))
                current = None
        if current is not None:
            items.append(" ".join(current.split()))
        return items


class TheFileIsThere(DocTest):
    def test_the_file_exists_where_afk_step_1_sends_the_reader(self):
        self.assertTrue(os.path.isfile(ROOT_CAUSE),
                        "tk/skills/kickoff/ROOT-CAUSE.md is missing")

    def test_every_section_the_checks_cut_on_is_still_there(self):
        for title in SECTIONS:
            with self.subTest(section=title):
                self.section(title)


class TheFiveLists(DocTest):
    def test_the_five_lists_are_named(self):
        body = self.section("The five lists the audit returns")
        for name in THE_FIVE_LISTS:
            with self.subTest(list=name):
                self.assertIn(name, body,
                              f"the audit's list {name!r} is not named — an "
                              f"orchestrator cannot return a list it never read")

    def test_the_section_holds_exactly_five_lists_and_no_sixth(self):
        items = self.bullets(self.section("The five lists the audit returns"))
        self.assertEqual(len(items), 5,
                         f"the section lists {len(items)} bullets, not five — a "
                         f"sixth list nobody named is a list nobody verifies")

    def test_each_list_says_what_verifies_it_in_the_code(self):
        """The rule the file opens the section with. A list verified against the
        item's own TEXT is the defect: the item says what somebody wanted, and only
        the tree says what happened. So each bullet must carry a command, or point at
        the file that owns the check."""
        for item in self.bullets(self.section("The five lists the audit returns")):
            with self.subTest(bullet=item[:60]):
                self.assertTrue(re.search(r"`git -C |`git ls-remote`|`tk-queue |"
                                          r"`SKILL\.md`|section below", item),
                                f"no check named beside this list: {item[:120]!r}")

    def test_the_section_says_the_verification_is_the_code_and_not_the_text(self):
        body = self.section("The five lists the audit returns")
        self.assertIn("verified against the CODE, never against the item's own text",
                      body)


class TheFusionOrder(DocTest):
    def test_edit_comes_before_cancel_in_the_prescribed_block(self):
        body = self.section("Fusing two items: `edit`, then `cancel`")
        edit, cancel = body.find("tk-queue edit"), body.find("tk-queue cancel")
        self.assertNotEqual(edit, -1, "no `tk-queue edit` prescribed")
        self.assertNotEqual(cancel, -1, "no `tk-queue cancel` prescribed")
        self.assertLess(edit, cancel,
                        "the block prescribes `cancel` before `edit` — the order the "
                        "section exists to refuse")

    def test_the_file_says_what_the_inverse_order_breaks(self):
        body = self.section("Fusing two items: `edit`, then `cancel`")
        for token in ("inverse order", "700-char", "nothing left to paste"):
            with self.subTest(token=token):
                self.assertIn(token, body,
                              "the order is prescribed without saying what breaks "
                              "when it is reversed, which is what makes it a rule "
                              "rather than a preference")

    def test_the_existing_implementation_is_cited_and_not_recopied(self):
        body = self.section("Fusing two items: `edit`, then `cancel`")
        for citation in ("T341", "PR #88", "test_wrap_up_consolidation.py",
                         "T340", "PR #90", "tk-queue cancel --help"):
            with self.subTest(citation=citation):
                self.assertIn(citation, body,
                              f"{citation} is not cited — the rule is implemented "
                              f"and proved elsewhere, and a copy of it here is the "
                              f"copy the next edit forgets")


class TheTopologyRules(DocTest):
    def test_both_rules_are_named_with_the_criterion_that_fires_them(self):
        items = self.bullets(self.section("The two topology rules"))
        self.assertEqual(len(items), 2, "the section is not two rules")
        stacked, union = items
        self.assertIn("Stacked pull request", stacked)
        self.assertIn("UNION of the others", union)
        for item in items:
            with self.subTest(rule=item[:50]):
                self.assertIn("fires when", item,
                              "a topology rule with no trigger is a rule nobody "
                              "knows to apply")

    def test_the_stacked_rule_fires_on_a_shared_file(self):
        stacked = self.bullets(self.section("The two topology rules"))[0]
        self.assertIn("same FILE", stacked)
        self.assertIn("never from `main`", stacked)

    def test_the_union_rule_names_the_merge_as_the_collision_test(self):
        union = self.bullets(self.section("The two topology rules"))[1]
        self.assertIn("collision test", union)
        self.assertIn("MERGEABLE", union,
                      "`gh`'s pair-by-pair MERGEABLE is the thing this rule refuses "
                      "to rely on; dropping the mention leaves the reader with it")


class TheGraphVocabulary(DocTest):
    def test_the_three_shapes_are_adopted_by_name(self):
        body = self.section("chain, parallelize, route")
        for shape in ("**chain**", "**parallelize**", "**route**"):
            with self.subTest(shape=shape):
                self.assertIn(shape, body)

    def test_the_collision_with_the_field_chain_is_declared(self):
        """`chain` and `route` already carry a meaning in these files. Two disjoint
        senses under one token read as ordinary context, so the file says which one
        it means."""
        body = self.section("chain, parallelize, route")
        self.assertIn("field chain", body)
        self.assertIn("queue.md", body)

    def test_the_cheap_gate_before_the_fan_out_is_carried(self):
        """Spec #252 story 62: the cookbook names N+1 calls as the pattern's own
        limitation, and the gate that asks whether a lane is worth them is one of
        the crossings this section settles. Without it the cut returns every
        disjoint file set as a lane, however small."""
        body = self.section("chain, parallelize, route")
        self.assertIn("cheap gate before the fan-out", body)
        self.assertIn("N+1 calls", body,
                      "the gate is named without the cost it weighs, which is what "
                      "makes it a gate rather than a preference")
        self.assertIn("FILE set", body,
                      "the gate is answered from the lane's theme, which is the "
                      "grouping the rest of this file refuses")

    def test_n_workers_3_is_refused_and_the_real_ceiling_named(self):
        body = self.section("chain, parallelize, route")
        self.assertIn("`n_workers=3` is not adopted", body)
        self.assertIn("max-local-subagents", body,
                      "refusing the cookbook's number without naming what replaces "
                      "it leaves the reader with no ceiling at all")


class TheTrackerImport(DocTest):
    def test_the_rule_names_which_ticket_becomes_an_item(self):
        body = self.section("The tracker import comes first")
        for token in ("`ready-for-agent`", "**Parent**", "has no item in the queue"):
            with self.subTest(token=token):
                self.assertIn(token, body)

    def test_the_prescribed_add_carries_the_three_provenance_flags(self):
        body = self.section("The tracker import comes first")
        for flag in ("--spec", "--ticket", "--repo"):
            with self.subTest(flag=flag):
                self.assertIn(flag + " \"", body,
                              f"the prescribed `add` does not pass {flag} — the "
                              f"item's provenance is add-only and cannot be "
                              f"corrected later by `edit`")

    def test_the_import_forbids_blocked_by_between_siblings(self):
        body = self.section("The tracker import comes first")
        self.assertIn("no `--blocked-by` between siblings", body)
        self.assertIn("out of the package", body,
                      "the ban is stated without its reason — `pack` excludes a "
                      "blocked item, which is what makes the flag harmful here")

    def test_the_add_is_the_orchestrator_s(self):
        body = self.section("The tracker import comes first")
        self.assertIn("ORCHESTRATOR", body)
        self.assertIn("refuses an `add` from", body,
                      "the hook that enforces this is the reason the rule holds; "
                      "without it the line reads as etiquette")

    def test_the_import_runs_before_the_audit(self):
        body = self.section("The tracker import comes first")
        self.assertIn("before the audit reads", body)


class TheAfkPointer(DocTest):
    def step_one_pointer(self):
        head = re.search(r"^## 1\. Build the package\s*\n\n(.*?)\n\n",
                         self.afk, re.M | re.S)
        self.assertIsNotNone(head, "`## 1. Build the package` lost its opening block")
        return head.group(1)

    def test_step_1_points_at_the_file_by_its_relative_path(self):
        self.assertIn("`ROOT-CAUSE.md` beside this file", self.step_one_pointer())

    def test_step_1_declares_the_threshold_above_which_the_audit_runs(self):
        pointer = self.step_one_pointer()
        self.assertIn("20 eligible candidates", pointer)
        self.assertIn("at or below 20", pointer,
                      "the pointer names the threshold without saying what happens "
                      "below it, which leaves step 1's own cut unclaimed")

    def test_the_pointer_is_a_pointer_and_not_a_paragraph(self):
        lines = self.step_one_pointer().splitlines()
        self.assertLessEqual(len(lines), 2,
                             f"the pointer grew to {len(lines)} lines — AFK.md is "
                             f"under a size lock and the slack pays for a pointer")

    def test_the_threshold_the_pointer_states_is_the_file_s_own(self):
        self.assertIn("more than 20 eligible candidates", self.text)
        self.assertIn("The number is DERIVED", self.text,
                      "a threshold with no ratified source says so in the cell, or "
                      "it reads as measured")

    def test_the_fleet_inherits_and_is_not_edited(self):
        """The audit's writes are queue writes, and `fleet/SKILL.md` writes no
        project's queue: the fleet reaches this file through kickoff, so naming it
        in the fleet skill would be a second route to maintain."""
        self.assertNotIn("ROOT-CAUSE", read(FLEET))


if __name__ == "__main__":
    unittest.main()
