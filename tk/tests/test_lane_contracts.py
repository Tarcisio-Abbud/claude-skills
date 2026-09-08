#!/usr/bin/env python3
"""Doc-conformance proof for the two lane contracts,
`../skills/kickoff/LANE-CONTRACT.md` and `../skills/kickoff/REVIEW-CONTRACT.md`.

Run: python3 -m unittest discover -s tk/tests   (stdlib only, no deps)

WHAT THE FILES ARE. The two prompts that made the package of 05-07/09/2026 fit inside one
orchestrator: the contract one lane implementer is handed, and the contract the cold
reviewer of that lane's pull request is handed. They lived in an outbox directory with
that weekend's own addresses in them; they enter the skill with metavariables instead.

WHAT IS ASSERTED IS THE PROSE, because prose is what the two agents execute. Nothing here
dispatches an agent or opens a pull request. Four properties carry the weight:

- **no address of that weekend survived the move.** A path, a lane name or a session id
  from 05-07/09 makes the contract unusable for the next package while still reading as
  complete;
- **every rule that has a measured defect behind it is NAMED.** Each one below cost a run:
  a lane that lost uncommitted work, a shared scratchpad that truncated a mutation log, an
  implementer that waited on a background `pytest` and returned with nothing. A rule the
  file drops is a rule the next dispatch will not carry;
- **the three colours are read off `../reference/vista.md`'s five verdicts**, and the five
  are taken FROM that file here rather than retyped, so a rename there reddens this test
  instead of silently forking the vocabulary;
- **the dispatch prompt still fits the budget.** Its whole point is that the rules live in
  the file and the prompt carries addresses; a prompt that grows past 15 lines has started
  re-stating the contract.

VACUITY GUARD FIRST. Every check cuts a slice on a heading, and a heading that moved would
leave the check reading an empty string and passing. `test_every_section_the_checks_cut_on
_is_still_there` refuses that, and `section()` asserts each slice non-empty as it is taken.

WHAT IS NOT PROVED HERE: that an orchestrator ever hands either contract over, that a lane
obeys it, or that the prescribed `gh` lines run — a pull request is not a fixture. The
`tk-queue` mention inside `LANE-CONTRACT.md` is swept for its flags by
`test_afk_audit.py`'s `TheQueueFlagSweep`, like every other pasteable command in the
plugin's prose.
"""

import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.join(HERE, os.pardir)
KICKOFF = os.path.join(PLUGIN, "skills", "kickoff")
LANE = os.path.join(KICKOFF, "LANE-CONTRACT.md")
REVIEW = os.path.join(KICKOFF, "REVIEW-CONTRACT.md")
AFK = os.path.join(KICKOFF, "AFK.md")
VISTA = os.path.join(PLUGIN, "reference", "vista.md")

LANE_SECTIONS = ("Inputs, read in this order",
                 "The worktree is cut from `origin/main`, never the live clone",
                 "Per slice: one slice = one commit, pushed",
                 "The lane's end: one pull request, never merged by the agent",
                 "Hard rules",
                 "The dispatch prompt")

REVIEW_SECTIONS = ("Inputs",
                   "Steps",
                   "The three colours, read off the five verdicts",
                   "A fix pull request gets the same cold review",
                   "The collision check closes the package",
                   "Hard rules")

# The weekend the two files were written in. Its addresses are what the move had to
# strip: an outbox path, a lane slug, and the session id in the two trailers.
THE_WEEKEND = ("fds-2026-09-05", "_outbox", "PLANO-LANES", "ITENS-L",
               "session_01CZifBbznYWuR5faL4wDE99", "projects-da",
               "memory/next-steps.md")

# Every rule the ticket names, keyed by the term a `grep` finds it under. The value is
# the term, and the assertion is membership: a rule renamed out of its term is a rule
# the next reader cannot search for.
LANE_RULES = {
    "worktree cut from origin/main": "worktree add",
    "never the live clone": "live clone",
    "one slice = one commit": "one slice = one commit",
    "the commit is pushed": "did not happen",
    "scope does not grow": "let no scope grow",
    "the adjacent defect is a report line": "Achados não tratados",
    "item text outside the queue": "OUTSIDE the queue",
    "the hook refuses even the read": "refuses even the READ",
    "a scratchpad per lane": "scratchpad of its own per lane",
    "declared timeouts": "timeout 900",
    "mutation timeout": "timeout 1200",
    "the suite runs in the foreground": "FOREGROUND",
    "one pull request per lane": "Open ONE pull request",
    "never merged by the agent": "Never merge",
    "the body is for a cold reader": "cold reader",
    "gh api -F body=@file": "-F \"body=@",
    "the lane implements the brief": "the brief is what the lane implements",
    "the delegation merges nothing": "delegation merges nothing",
}


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def flat(text):
    """`text` with every run of whitespace collapsed to one space.

    Every phrase asserted below is prose, and prose in these files is wrapped at
    the column the file is written to. Asserting a phrase against the raw text
    makes the check depend on where the wrap happened to fall, so a reflow that
    changes nothing reddens, and a rewording that drops the rule stays green when
    it happens to re-wrap the same way.
    """
    return " ".join(text.split())


def the_five_verdicts():
    """The five safe-to-merge verdicts, taken from `reference/vista.md` itself.

    Retyping them here would let the two vocabularies fork in silence, which is the
    one thing the colour table cannot survive: a colour read off a verdict nobody
    else names is a colour nobody can check.
    """
    text = read(VISTA)
    line = re.search(r"\*\*five safe-to-merge verdicts\*\*(.*?)\n\n", text, re.S)
    assert line, "vista.md no longer names the five safe-to-merge verdicts"
    names = re.search(r"—\s*\n?([a-z, ]+?)\s*—", line.group(1))
    assert names, "vista.md's five verdicts are no longer listed after the term"
    found = [w.strip() for w in names.group(1).split(",")]
    assert len(found) == 5, f"vista.md lists {len(found)} verdicts, not five: {found}"
    return found


class DocTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lane = read(LANE)
        cls.review = read(REVIEW)
        cls.afk = read(AFK)
        cls.lane_flat = flat(cls.lane)
        cls.review_flat = flat(cls.review)

    def section(self, text, title, raw=False):
        """The body under `## title`, up to the next `## ` — asserted non-empty.

        Whitespace-collapsed unless `raw`, so a phrase check does not depend on
        where the file's wrap fell. `raw` is for the checks that read lines.
        """
        pattern = re.compile(r"^## " + re.escape(title) + r"\s*$(.*?)(?=^## |\Z)",
                             re.M | re.S)
        found = pattern.findall(text)
        self.assertEqual(len(found), 1,
                         f"`## {title}` is not there exactly once — the check that "
                         f"cuts on it would read an empty string and pass")
        self.assertTrue(found[0].strip(), f"`## {title}` is empty")
        return found[0] if raw else flat(found[0])

    def afk_step(self, number, title):
        pattern = re.compile(r"^## %d\. %s\s*$(.*?)(?=^## \d\. |\Z)"
                             % (number, re.escape(title)), re.M | re.S)
        found = pattern.findall(self.afk)
        self.assertEqual(len(found), 1,
                         f"AFK.md step {number} lost its heading — the pointer check "
                         f"would read an empty string")
        return found[0]


class TheFilesAreThere(DocTest):
    def test_both_files_exist_under_the_kickoff_skill(self):
        for path in (LANE, REVIEW):
            with self.subTest(file=os.path.basename(path)):
                self.assertTrue(os.path.isfile(path), f"{path} is missing")

    def test_every_section_the_checks_cut_on_is_still_there(self):
        for title in LANE_SECTIONS:
            with self.subTest(file="LANE-CONTRACT.md", section=title):
                self.section(self.lane, title)
        for title in REVIEW_SECTIONS:
            with self.subTest(file="REVIEW-CONTRACT.md", section=title):
                self.section(self.review, title)

    def test_no_address_of_the_weekend_survived_the_move(self):
        for name, text in (("LANE-CONTRACT.md", self.lane),
                           ("REVIEW-CONTRACT.md", self.review)):
            for token in THE_WEEKEND:
                with self.subTest(file=name, token=token):
                    self.assertNotIn(token, text,
                                     f"{token!r} is one package's own address — the "
                                     f"next package cannot paste a contract that "
                                     f"names it")

    def test_the_addresses_became_metavariables(self):
        """A file with the addresses merely deleted reads as complete and dispatches
        an agent to nothing. Each one has to be a slot the orchestrator fills."""
        for name, text, slots in (
                ("LANE-CONTRACT.md", self.lane_flat,
                 ("<items file>", "<notes dir>", "<scratch dir>", "<session URL>")),
                ("REVIEW-CONTRACT.md", self.review_flat,
                 ("<items file>", "<n>", "<owner>/<repo>"))):
            for slot in slots:
                with self.subTest(file=name, slot=slot):
                    self.assertIn(slot, text,
                                  f"{slot} is not a slot in {name} — the address it "
                                  f"replaces was dropped, not parameterised")


class TheLaneIsDefinedFirst(DocTest):
    def opening(self):
        head = re.search(r"^# .*?\n\n(.*?)\n\n", self.lane, re.S)
        self.assertIsNotNone(head, "LANE-CONTRACT.md lost its opening block")
        return flat(head.group(1))

    def test_the_first_line_says_what_a_lane_is_here(self):
        opening = self.opening()
        for part in ("one branch", "one worktree", "one repository",
                     "ONE pull request", "touch no file any other lane touches"):
            with self.subTest(part=part):
                self.assertIn(part, opening,
                              "the definition drops a term, and a lane defined by "
                              "four of its five properties is a lane a dispatch can "
                              "get wrong in the fifth")

    def test_the_first_line_distinguishes_the_accumulated_spec_lane(self):
        opening = self.opening()
        self.assertIn("accumulated spec lane", opening)
        self.assertIn("`AFK.md`", opening,
                      "the other lane is named without saying which file owns it, so "
                      "a reader cannot go and read the difference")
        self.assertIn("merges nothing", opening,
                      "the two shapes differ on who merges, which is the whole of the "
                      "distinction: dropping it makes the sentence decorative")


class TheLaneRules(DocTest):
    def test_every_rule_is_named_by_the_term_a_grep_finds_it_under(self):
        for rule, term in LANE_RULES.items():
            with self.subTest(rule=rule):
                self.assertIn(term, self.lane_flat,
                              f"the rule {rule!r} is not in the file under {term!r} — "
                              f"each of these cost a run that lacked it")

    def test_the_foreground_rule_names_what_the_background_run_cost(self):
        body = self.section(self.lane, "Per slice: one slice = one commit, pushed")
        self.assertIn("waiting on a notification", body)
        self.assertIn("no pull request and no comment", body,
                      "the rule is stated without its measured cost, which is what "
                      "makes it a rule rather than a preference")

    def test_the_timeouts_are_declared_with_the_measurement_behind_them(self):
        body = self.section(self.lane, "Per slice: one slice = one commit, pushed")
        self.assertIn("708 s", body)
        self.assertIn("NOT-RUN", body,
                      "a short timeout reporting a run as not-run under a green check "
                      "is the failure the number exists to prevent")

    def test_the_brief_wins_over_the_item_and_merges_nothing(self):
        body = self.section(self.lane, "Inputs, read in this order")
        self.assertIn("/tk:second-opinion", body)
        self.assertIn("`once`", body)
        self.assertIn("stays as history", body,
                      "without saying what happens to the item's own statement, a "
                      "reader implements both")
        self.assertIn("waits for the user's OK", body)

    def test_the_body_file_flag_is_prescribed_with_the_two_forms_it_replaces(self):
        body = self.section(self.lane,
                            "The lane's end: one pull request, never merged by the agent")
        self.assertIn("gh pr edit --body", body,
                      "the flag that fails on this account is not named, so a reader "
                      "reaches for it first")
        self.assertIn("-f", body,
                      "`gh api -f` writes the literal path; unnamed, it is the next "
                      "thing tried when `-F` looks verbose")


class TheDispatchPrompt(DocTest):
    def block(self):
        body = self.section(self.lane, "The dispatch prompt", raw=True)
        fence = re.search(r"^```\n(.*?)^```", body, re.M | re.S)
        self.assertIsNotNone(fence, "the dispatch prompt has no fenced block")
        lines = fence.group(1).splitlines()
        self.assertTrue(lines, "the dispatch prompt's block is empty")
        return lines

    def test_the_prompt_fits_fifteen_lines(self):
        lines = self.block()
        self.assertLessEqual(len(lines), 15,
                             f"the dispatch prompt is {len(lines)} lines — past 15 it "
                             f"has started re-stating the contract the file carries")

    def test_the_prompt_points_at_the_contract_instead_of_repeating_it(self):
        block = "\n".join(self.block())
        self.assertIn("LANE-CONTRACT.md", block,
                      "a prompt that does not name the contract leaves an implementer "
                      "with the addresses and none of the rules")

    def test_the_prompt_carries_the_addresses_the_file_cannot_know(self):
        block = "\n".join(self.block())
        for slot in ("<items file>", "<notes dir>", "<scratch dir>", "<lane>"):
            with self.subTest(slot=slot):
                self.assertIn(slot, block)


class TheThreeColours(DocTest):
    def table(self):
        return self.section(self.review, "The three colours, read off the five verdicts")

    def test_the_three_colours_are_named(self):
        body = self.table()
        for colour in ("**VERDE**", "**AMARELO**", "**VERMELHO**"):
            with self.subTest(colour=colour):
                self.assertIn(colour, body)

    def test_the_colours_map_onto_vista_s_own_five_verdicts(self):
        body = self.table()
        self.assertIn("`../../reference/vista.md`", body,
                      "the colours claim to read five verdicts and do not say whose")
        for verdict in the_five_verdicts():
            with self.subTest(verdict=verdict):
                self.assertIn(verdict, body,
                              f"vista.md's verdict {verdict!r} is missing from the "
                              f"mapping — four verdicts read as complete and the "
                              f"fifth is the one nobody checked")

    def test_amarelo_requires_a_named_human_decision(self):
        body = self.table()
        self.assertIn("named human decision", body)
        self.assertIn("who decided", body,
                      "AMARELO without naming who decided is a colour an agent gives "
                      "itself")

    def test_no_colour_authorises_a_merge(self):
        body = self.table()
        self.assertIn("No colour authorises a merge", body)
        self.assertIn("`../merge-gate/SKILL.md`", body,
                      "the merge is refused here without saying who owns it, which "
                      "leaves the reader with no next step")


class TheReviewerFixes(DocTest):
    def steps(self):
        return self.section(self.review, "Steps")

    def test_the_reviewer_fixes_in_one_follow_up_commit_per_axis(self):
        body = self.steps()
        self.assertIn("one follow-up commit per axis", body)

    def test_every_finding_lands_in_exactly_one_of_three_buckets(self):
        body = self.steps()
        for bucket in ("**fixed**", "**declined**", "**not handled**"):
            with self.subTest(bucket=bucket):
                self.assertIn(bucket, body)
        self.assertIn("exactly one", body,
                      "three buckets with no rule that a finding lands in one of them "
                      "lets a finding be counted twice or not at all")

    def test_a_decline_carries_a_written_reason(self):
        body = self.steps()
        self.assertIn("written reason", body)

    def test_the_comment_reports_the_three_buckets_in_portuguese(self):
        body = self.steps()
        for word in ("consertado", "recusado", "não tratado"):
            with self.subTest(word=word):
                self.assertIn(word, body,
                              "the comment is read by a human in Portuguese, and a "
                              "bucket missing from it is a finding nobody sees")

    def test_the_reviewer_runs_the_suite_in_the_foreground(self):
        body = self.steps()
        self.assertIn("FOREGROUND", body)
        self.assertIn("waiting on a notification", body,
                      "the rule holds in the review contract for the same measured "
                      "reason it holds in the lane contract")

    def test_the_triage_is_on_the_merits(self):
        body = self.steps()
        self.assertIn("not true because a reviewer said it", body)


class TheFixPullRequest(DocTest):
    def test_a_fix_pull_request_takes_the_same_cold_review(self):
        body = self.section(self.review, "A fix pull request gets the same cold review")
        self.assertIn("same two axes", body)
        self.assertIn("never the agent that wrote it", body,
                      "a repair reviewed by its own author is the review this rule "
                      "exists to refuse")


class TheCollisionCheck(DocTest):
    def body(self):
        return self.section(self.review, "The collision check closes the package")

    def test_the_check_names_the_bin_it_prescribes(self):
        self.assertIn("`tk-collisions`", self.body(),
                      "the section prescribes a check without naming the bin that "
                      "runs it, and a reader cannot search for what it never named")

    def test_the_check_points_at_the_merge_gate_and_does_not_restate_it(self):
        body = self.body()
        self.assertIn("`../merge-gate/SKILL.md` §5", body,
                      "the collision command is owned by the merge gate; a copy here "
                      "is the copy the next edit forgets")
        self.assertNotIn("tk-collisions <", body,
                         "the command was re-stated instead of pointed at")

    def test_a_real_collision_goes_to_a_sonnet_agent(self):
        body = self.body()
        self.assertIn("**Sonnet**", body)
        self.assertIn("resolves that pair", body)

    def test_the_resolved_file_is_posted_with_body_file_and_not_with_an_at_sign(self):
        body = self.body()
        self.assertIn('gh pr comment "<n>" -R "<owner>/<repo>" --body-file', body,
                      "the exact command is what a reader pastes; a described one is "
                      "re-composed wrong")
        self.assertIn("--body @", body,
                      "the form that publishes the literal `@` string is not named, "
                      "so the reader has no way to recognise the failure")


class TheAfkPointers(DocTest):
    def pointer(self, step, title, filename):
        body = self.afk_step(step, title)
        found = [line for line in body.splitlines() if filename in line]
        self.assertEqual(len(found), 1,
                         f"AFK.md step {step} names {filename} on {len(found)} lines, "
                         f"not one — the file is under a size lock and the slack pays "
                         f"for a pointer, not a paragraph")
        return found[0]

    def test_step_3_points_at_the_lane_contract_in_one_line(self):
        line = self.pointer(3, "Claim, then dispatch", "LANE-CONTRACT.md")
        self.assertIn("beside this file", line)
        self.assertIn("its own branch and pull request", line,
                      "the pointer names the file without saying which lane shape it "
                      "governs, and the accumulated lane would take it too")

    def test_step_5_points_at_the_review_contract_in_one_line(self):
        line = self.pointer(5, "Verify every delivery", "REVIEW-CONTRACT.md")
        self.assertIn("beside this file", line)
        self.assertIn("cold review", line)

    def test_neither_pointer_repeats_a_rule_the_contract_owns(self):
        """The size lock is what makes this expensive: a pointer that summarises the
        contract pays AFK.md's slack for prose that already exists next door."""
        for step, title, filename in ((3, "Claim, then dispatch", "LANE-CONTRACT.md"),
                                      (5, "Verify every delivery", "REVIEW-CONTRACT.md")):
            line = self.pointer(step, title, filename)
            with self.subTest(step=step):
                self.assertLessEqual(len(line), 100,
                                     f"step {step}'s pointer is {len(line)} characters "
                                     f"— it has started carrying the rules")


if __name__ == "__main__":
    unittest.main()
