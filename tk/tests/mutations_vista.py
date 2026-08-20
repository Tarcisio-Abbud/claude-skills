#!/usr/bin/env python3
"""Mutation harness for the `tk-vista-check` suite — puts each defect back.

Run: python3 tk/tests/mutations_vista.py

Same contract as its siblings: each entry restores one defect in a COPY of
`tk/`, runs only the tests named for it, and requires each of them to fail. A
mutation that SURVIVES is a hole in the suite, not a pass.

This file holds entries only. The runner is `mutations_tk_contract.run`, which
takes the test module, the entry list and the default source as arguments —
the seam that file's docstring describes, used here for the first time. It also
enumerates the suite and reports any test NO entry names (UNPROVED), which is
the half a score of N/N cannot show: N counts the mutants someone wrote.

One entry mutates `reference/vista-template.html` rather than the bin. The
template is a shipped artefact with a test of its own, and a template that
stopped qualifying is exactly as broken as a checker that stopped checking.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mutations_tk_contract import run      # noqa: E402  (path above enables it)

CHECK = os.path.join("bin", "tk-vista-check")
TEMPLATE = os.path.join("reference", "vista-template.html")

# (label, old, new, [tests that must fail], source relative to tk/)
MUTATIONS = [
    # -- self-contained ---------------------------------------------------
    ("T139 the anchor exemption is widened to every href attribute",
     '                if tag == "a" and name == "href":',
     '                if name == "href":',
     ["TestSelfContained.test_a_stylesheet_link_is_refused"], CHECK),

    ("T139 the anchor exemption never fires, so block 4 breaks the page",
     '                if tag == "a" and name == "href":',
     '                if tag == "not-a-tag" and name == "href":',
     ["TestSelfContained.test_a_link_the_human_clicks_is_kept",
      "TestSelfContained.test_the_smallest_qualifying_page_is_accepted"], CHECK),

    ("T139 a protocol-relative URL is read as local",
     '    if not u or u.startswith("#"):',
     '    if not u or u.startswith("#") or u.startswith("//"):',
     ["TestSelfContained.test_a_protocol_relative_script_is_refused"], CHECK),

    ("T139 the naive rule: anything that is not http is local",
     '    return u.lower().startswith("data:")',
     '    return not u.lower().startswith(("http:", "https:"))',
     ["TestSelfContained.test_a_relative_image_path_is_refused_though_it_costs_no_network"],
     CHECK),

    ("T139 a data: URI is not recognised, so an inlined image is refused",
     '    return u.lower().startswith("data:")',
     '    return u.lower().startswith("data-uri:")',
     ["TestSelfContained.test_a_data_uri_image_is_kept"], CHECK),

    ("T139 srcset is not a URL-valued attribute",
     '    "src", "srcset", "poster"', '    "src", "poster"',
     ["TestSelfContained.test_a_srcset_candidate_reaching_the_network_is_refused"], CHECK),

    ("T139 @import is allowed as long as no url() sits in it",
     "    if CSS_IMPORT.search(css):", "    if False:",
     ["TestSelfContained.test_an_import_of_a_neighbouring_stylesheet_is_refused"], CHECK),

    ("T139 CSS url() is never inspected",
     "    for _, url in CSS_URL.findall(css):", "    for _, url in []:",
     ["TestSelfContained.test_a_css_url_reaching_the_network_is_refused"], CHECK),

    ("T139 fetch drops out of the network vocabulary",
     r'    r"\b(fetch|XMLHttpRequest', r'    r"\b(XMLHttpRequest',
     ["TestSelfContained.test_a_fetch_in_script_is_refused"], CHECK),

    ("T139 event handlers are not script",
     '            if name.startswith("on"):', "            if False:",
     ["TestSelfContained.test_a_send_beacon_in_an_event_handler_is_refused"], CHECK),

    ("T139 the network words are hunted in the whole document, prose included",
     '    for call in sorted({m.group(0).strip() for m in NETWORK_CALLS.finditer("\\n".join(v.script))}):',
     "    for call in sorted({m.group(0).strip() for m in NETWORK_CALLS.finditer(text)}):",
     ["TestSelfContained.test_the_word_fetch_in_the_page_prose_is_not_a_network_call"], CHECK),

    ("T139 a fetched URL is never judged, so <base> and every src walk through",
     "                    if not local(url):", "                    if False:",
     ["TestSelfContained.test_a_base_tag_is_refused"], CHECK),

    # -- the five blocks --------------------------------------------------
    ("T139 block 1 is not required",
     '    if "stats" not in v.blocks:', "    if False:",
     ["TestFiveBlocks.test_the_stats_block_is_required"], CHECK),

    ("T139 block 2's region is not required",
     '    if "cards" not in v.blocks:', "    if False:",
     ["TestFiveBlocks.test_the_cards_region_is_required"], CHECK),

    ("T139 a page with no card at all passes",
     "    if not v.cards:", "    if False:",
     ["TestFiveBlocks.test_a_page_with_no_card_is_refused"], CHECK),

    ("T139 a card need not say which outcome it is grouped under",
     '        if not card["desfecho"]:', "        if False:",
     ["TestFiveBlocks.test_each_card_names_the_outcome_it_is_grouped_by"], CHECK),

    ("T139 the risk tag is optional",
     '        if not card["risco"]:', "        if False:",
     ["TestFiveBlocks.test_each_card_carries_a_risk_tag"], CHECK),

    ("T139 the proof link is optional",
     '        if not [u for u in card["provas"] if u]:', "        if False:",
     ["TestFiveBlocks.test_each_card_carries_a_proof_link"], CHECK),

    ("T139 a proof marker counts by membership, not by carrying an href",
     '        if not [u for u in card["provas"] if u]:', '        if not card["provas"]:',
     ["TestFiveBlocks.test_a_proof_marker_with_no_href_is_not_a_proof"], CHECK),

    ("T139 ONE proof anywhere covers every card",
     '        if not [u for u in card["provas"] if u]:',
     '        if not any(c["provas"] for c in v.cards):',
     ["TestFiveBlocks.test_a_card_without_a_proof_is_named_even_when_a_sibling_has_one"],
     CHECK),

    ("T139 a card is never closed at its own end tag",
     '                while self.open_cards and self.cards[self.open_cards[-1]]["depth"] >= depth:',
     '                while self.open_cards and self.cards[self.open_cards[-1]]["depth"] > depth:',
     ["TestFiveBlocks.test_a_proof_link_outside_every_card_covers_none"], CHECK),

    ("T139 an unclosed tag detaches every card boundary under it",
     "        if tag in self.stack:", "        if self.stack and self.stack[-1] == tag:",
     ["TestFiveBlocks.test_an_unclosed_paragraph_does_not_keep_a_card_open_past_its_end"],
     CHECK),

    ("T139 block 5 is not required",
     '    if "saldo" not in v.blocks:', "    if False:",
     ["TestFiveBlocks.test_the_balance_block_is_required"], CHECK),

    # -- both themes ------------------------------------------------------
    ("T139 one theme is enough",
     "    if not DARK_THEME.search(css):", "    if False:",
     ["TestBothThemes.test_a_page_with_a_single_theme_is_refused"], CHECK),

    ("T139 the shipped template loses its dark palette",
     "  @media (prefers-color-scheme: dark) {", "  @media (min-width: 0px) {",
     ["TestShippedTemplate.test_the_template_the_plugin_ships_qualifies"], TEMPLATE),

    # -- usage ------------------------------------------------------------
    ("T139 the path guard is dropped, so an absent file reads as an unreadable page",
     "        if not os.path.isfile(path):", "        if False:",
     ["TestUsage.test_a_path_that_is_not_a_file_is_refused_before_it_is_opened"], CHECK),

    ("T139 the path guard accepts a directory, which blocks or raises at open",
     "        if not os.path.isfile(path):", "        if not os.path.exists(path):",
     ["TestUsage.test_a_directory_is_refused_as_a_path_not_reported_as_a_bad_page"], CHECK),

    ("T139 the reader assumes ascii, so a BOM and an em dash both stop the run",
     '    with open(path, encoding="utf-8-sig") as f:',
     '    with open(path, encoding="ascii") as f:',
     ["TestUsage.test_a_byte_order_mark_ahead_of_the_doctype_still_reads"], CHECK),

    ("T139 one bad file among good ones does not fail the run",
     "            failed = True", "            failed = False",
     ["TestUsage.test_a_good_page_beside_a_bad_one_still_fails_the_run"], CHECK),
]

if __name__ == "__main__":
    sys.exit(run(MUTATIONS, "test_tk_vista_check", default_src=CHECK))
