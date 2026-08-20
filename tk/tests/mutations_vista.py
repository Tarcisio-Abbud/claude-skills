#!/usr/bin/env python3
"""Mutation harness for the `tk-vista-check` suite — puts each defect back.

Run: python3 tk/tests/mutations_vista.py

Same contract as its siblings: each entry restores one defect in a COPY of
`tk/`, runs only the tests named for it, and requires each of them to fail. A
mutation that SURVIVES is a hole in the suite, not a pass.

This file holds entries only. The runner is `mutations_tk_contract.run`, which
takes the test module, the entry list and the default source as arguments — the
seam that file's docstring describes. It also enumerates the suite and reports
any test NO entry names (UNPROVED), which is the half a score of N/N cannot
show: N counts the mutants someone wrote.

Two entries mutate `reference/vista-template.html` rather than the bin. The
template is a shipped artefact with a test of its own, and a template that
stopped qualifying is exactly as broken as a checker that stopped checking.

WHAT A GREEN SCORE HERE DOES NOT SAY. Five bypasses of the earlier
literal-matching rule (`new Image()`, `window["fet"+"ch"]`, an aliased
`XMLHttpRequest`, `<meta http-equiv=refresh>`, CSS `image-set()`) were found by
a reviewer ATTACKING the checker with complete pages, not by any mutant below.
Mutation proves the tests that exist; an attack finds the test that does not.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mutations_tk_contract import run      # noqa: E402  (path above enables it)

CHECK = os.path.join("bin", "tk-vista-check")
TEMPLATE = os.path.join("reference", "vista-template.html")

# (label, old, new, [tests that must fail], source relative to tk/)
MUTATIONS = [
    # -- fetches nothing --------------------------------------------------
    ("T139 the anchor exemption never fires, so block 4 breaks the page",
     '                if tag == "a" and name == "href":',
     '                if tag == "not-a-tag" and name == "href":',
     ["TestSelfContained.test_a_link_the_human_clicks_is_kept",
      "TestSelfContained.test_the_smallest_qualifying_page_is_accepted"], CHECK),

    ("T139 the anchor exemption is widened to every href attribute",
     '                if tag == "a" and name == "href":',
     '                if name == "href":',
     ["TestSelfContained.test_a_stylesheet_link_is_refused"], CHECK),

    ("T139 a protocol-relative URL is read as local",
     '    if u.startswith("#"):',
     '    if u.startswith("#") or u.startswith("//"):',
     ["TestSelfContained.test_a_protocol_relative_script_is_refused"], CHECK),

    ("T139 the naive rule: anything that is not http is local",
     '    return u.lower().startswith("data:")',
     '    return not u.lower().startswith(("http:", "https:"))',
     ["TestSelfContained.test_a_relative_image_path_is_refused_though_it_costs_no_network"],
     CHECK),

    ("T139 an empty URL is read as no URL at all",
     '    return u.lower().startswith("data:")',
     '    return u.lower().startswith("data:") or not u',
     ["TestSelfContained.test_an_empty_src_is_refused"], CHECK),

    ("T139 a data: URI is not recognised, so an inlined image is refused",
     '    return u.lower().startswith("data:")',
     '    return u.lower().startswith("data-uri:")',
     ["TestSelfContained.test_a_data_uri_image_is_kept"], CHECK),

    ("T139 srcset is not a URL-valued attribute",
     '    "src", "srcset", "poster"', '    "src", "poster"',
     ["TestSelfContained.test_a_srcset_candidate_reaching_the_network_is_refused"], CHECK),

    ("T139 a fetched URL is never judged, so <base> and every src walk through",
     "                    if not local(url):", "                    if False:",
     ["TestSelfContained.test_a_base_tag_is_refused"], CHECK),

    ("T139 @import is allowed as long as no url() sits in it",
     "    if CSS_IMPORT.search(css):", "    if False:",
     ["TestSelfContained.test_an_import_of_a_neighbouring_stylesheet_is_refused"], CHECK),

    ("T139 the CSS is never asked what it fetches",
     "    for url in css_urls(css):", "    for url in []:",
     ["TestSelfContained.test_a_css_url_reaching_the_network_is_refused"], CHECK),

    ("T139 a CSS URL is collected and then never judged",
     "        if not local(url):\n            bad.append(f\"external resource: CSS fetches",
     "        if False:\n            bad.append(f\"external resource: CSS fetches",
     ["TestSelfContained.test_a_css_url_on_a_relative_path_is_refused"], CHECK),

    ("T139 the argument list is read by a regex that cannot nest",
     "        content = balanced(css, m.end() - 1)",
     '        content = (css[m.end():] + ")").split(")", 1)[0]',
     ["TestSelfContained.test_a_refused_css_url_is_named_whole_even_with_parens_in_it"], CHECK),

    ("T139 a nested url() is read as a token of the function around it",
     "            if not candidate or CSS_URL_FUNC.match(candidate):",
     "            if not candidate:",
     ["TestSelfContained.test_an_image_set_wrapping_a_data_uri_is_kept"], CHECK),

    ("T139 the scan resumes past the whole function, so a nested url() is never seen",
     "        pos = m.end()\n        content = balanced",
     "        pos = m.end() + len(balanced(css, m.end() - 1)) + 1\n        content = balanced",
     ["TestSelfContained.test_an_image_set_wrapping_a_remote_url_is_refused"], CHECK),

    ("T139 the candidates are split on every comma, quotes and parens included",
     "        for candidate in top_level_commas(content):",
     '        for candidate in content.split(","):',
     ["TestSelfContained.test_an_image_set_wrapping_a_data_uri_is_kept"], CHECK),

    ("T139 every candidate of an image-set is reported, local ones included",
     '        if not local(url):\n            bad.append(f"external resource: CSS fetches',
     '        if True:\n            bad.append(f"external resource: CSS fetches',
     ["TestSelfContained.test_only_the_offending_candidate_of_an_image_set_is_refused"], CHECK),

    ("T139 only url() counts as a CSS function that fetches",
     r'CSS_URL_FUNC = re.compile(r"(?<![\w-])(url|image-set|-webkit-image-set)\s*\("',
     r'CSS_URL_FUNC = re.compile(r"(?<![\w-])(url)\s*\("',
     ["TestSelfContained.test_an_image_set_reaching_the_network_is_refused"], CHECK),

    ("T139 the catch-all over the CSS text is back, and it refuses legitimate CSS",
     "    for url in css_urls(css):",
     '    for url in css_urls(css) + re.findall(r"https?:", css):',
     ["TestSelfContained.test_a_class_named_http_is_not_an_address",
      "TestSelfContained.test_an_address_inside_generated_text_is_not_a_fetch"], CHECK),

    # -- runs nothing -----------------------------------------------------
    ("T139 a <script> element is not collected, and every spelling of a call returns",
     '        if tag == "script":\n            self.scripts.append("<script>")',
     '        if tag == "script":\n            pass',
     ["TestSelfContained.test_an_image_built_in_script_is_refused",
      "TestSelfContained.test_a_bracketed_fetch_is_refused",
      "TestSelfContained.test_an_aliased_xhr_is_refused"], CHECK),

    ("T139 the ways the page would run code are collected and never reported",
     "    for how in sorted(set(v.scripts)):", "    for how in []:",
     ["TestSelfContained.test_a_script_element_is_refused_whatever_it_holds"], CHECK),

    ("T139 a self-closing tag skips the element reader",
     "        self._element(tag, attrs)\n",
     '        if tag != "script":\n            self._element(tag, attrs)\n',
     ["TestSelfContained.test_a_self_closing_script_is_refused_like_any_other"], CHECK),

    ("T139 event handlers are not code",
     '            if name.startswith("on"):', "            if False:",
     ["TestSelfContained.test_an_event_handler_is_refused"], CHECK),

    ("T139 a javascript: URL is judged as a link like any other",
     "                if script_url(value):", "                if False:",
     ["TestSelfContained.test_a_javascript_url_is_refused"], CHECK),

    ("T139 the URL is compared as the file spells it, not as the browser reads it",
     '    return URL_JUNK.sub("", url or "").strip(C0_OR_SPACE)',
     '    return (url or "").strip(C0_OR_SPACE)',
     ["TestSelfContained.test_a_javascript_url_split_by_a_tab_is_refused",
      "TestSelfContained.test_a_javascript_url_split_by_a_newline_is_refused"], CHECK),

    ("T139 only the tab is removed, and a newline still splits the scheme",
     r'URL_JUNK = re.compile(r"[\t\n\r]")', r'URL_JUNK = re.compile(r"[\t]")',
     ["TestSelfContained.test_a_javascript_url_split_by_a_newline_is_refused"], CHECK),

    ("T139 only whitespace is stripped, so a C0 control hides the scheme",
     '    return URL_JUNK.sub("", url or "").strip(C0_OR_SPACE)',
     '    return URL_JUNK.sub("", url or "").strip()',
     ["TestSelfContained.test_a_javascript_url_behind_a_control_character_is_refused"], CHECK),

    ("T139 the scheme is compared case-sensitively",
     "    return normalise(url).lower().startswith(SCRIPT_SCHEMES)",
     "    return normalise(url).startswith(SCRIPT_SCHEMES)",
     ["TestSelfContained.test_a_javascript_url_in_capitals_is_refused"], CHECK),

    ("T139 vbscript: is not a scheme that runs code",
     'SCRIPT_SCHEMES = ("javascript:", "vbscript:")', 'SCRIPT_SCHEMES = ("javascript:",)',
     ["TestSelfContained.test_a_vbscript_url_is_refused"], CHECK),

    ("T139 a meta refresh is not noticed",
     '        if tag == "meta" and a.get("http-equiv", "").strip().lower() == "refresh":',
     "        if False:",
     ["TestSelfContained.test_a_meta_refresh_is_refused"], CHECK),

    ("T139 the old literal blocklist is back, and it reads prose as a call",
     "    for how in sorted(set(v.scripts)):",
     '    for how in sorted(set(v.scripts)) + (["fetch("] if "fetch(" in text else []):',
     ["TestSelfContained.test_the_word_fetch_in_the_page_prose_is_not_a_network_call"], CHECK),

    # -- the five blocks --------------------------------------------------
    ("T139 block 1 drops out of the table the checks are derived from",
     '    "stats": (1, "the opening stats line"),\n', "",
     ["TestFiveBlocks.test_the_stats_block_is_required"], CHECK),

    ("T139 block 2's region drops out of the table the checks are derived from",
     '    "cards": (2, "the cards region"),\n', "",
     ["TestFiveBlocks.test_the_cards_region_is_required"], CHECK),

    ("T139 block 5 drops out of the table the checks are derived from",
     '    "saldo": (5, "closed × open balance"),\n', "",
     ["TestFiveBlocks.test_the_balance_block_is_required"], CHECK),

    ("T139 a page with no card at all passes",
     "    if not v.cards:", "    if False:",
     ["TestFiveBlocks.test_a_page_with_no_card_is_refused"], CHECK),

    ("T139 a card need not say which outcome it is grouped under",
     '        if not card["desfecho"]:', "        if False:",
     ["TestFiveBlocks.test_each_card_names_the_outcome_it_is_grouped_by"], CHECK),

    ("T139 any word at all is an outcome",
     '        elif card["desfecho"] not in OUTCOMES:', "        elif False:",
     ["TestFiveBlocks.test_an_outcome_outside_the_vocabulary_is_refused"], CHECK),

    ("T139 the vocabulary loses a word the closing template uses",
     'OUTCOMES = ("merged", "closed", "open", "carried", "blocked", "discarded")',
     'OUTCOMES = ("merged", "closed", "open", "blocked", "discarded")',
     ["TestFiveBlocks.test_every_outcome_of_the_vocabulary_is_accepted"], CHECK),

    ("T139 the risk tag is optional",
     '        if not card["risco"]:', "        if False:",
     ["TestFiveBlocks.test_each_card_carries_a_risk_tag"], CHECK),

    ("T139 the proof link is optional",
     '        if not card["provas"]:', "        if False:",
     ["TestFiveBlocks.test_each_card_carries_a_proof_link"], CHECK),

    ("T139 ONE proof anywhere covers every card",
     '        if not card["provas"]:',
     '        if not any(c["provas"] for c in v.cards):',
     ["TestFiveBlocks.test_a_card_without_a_proof_is_named_even_when_a_sibling_has_one"],
     CHECK),

    ("T139 a proof marker counts even with no href on it",
     "            if why and all(why):", "            if False:",
     ["TestFiveBlocks.test_a_proof_marker_with_no_href_is_not_a_proof",
      "TestFiveBlocks.test_a_proof_that_is_only_a_fragment_is_refused"], CHECK),

    ("T139 the reserved placeholder names stop being placeholders",
     'PLACEHOLDER_HOSTS = ("localhost", "invalid", "test", "example", "local",\n'
     '                     "example.com", "example.org", "example.net")',
     'PLACEHOLDER_HOSTS = ("example.com", "example.org", "example.net")',
     ["TestFiveBlocks.test_a_proof_pointing_at_a_reserved_placeholder_domain_is_refused",
      "TestShippedTemplate.test_the_template_is_refused_for_its_placeholder_and_nothing_else"],
     CHECK),

    ("T139 the list is back to the four names of the first round",
     'PLACEHOLDER_HOSTS = ("localhost", "invalid", "test", "example", "local",\n'
     '                     "example.com", "example.org", "example.net")',
     'PLACEHOLDER_HOSTS = ("invalid", "example.com", "example.org", "example.net")',
     ["TestFiveBlocks.test_a_proof_on_a_name_that_never_resolves_is_refused"], CHECK),

    ("T139 a trailing dot buys a way past the comparison",
     '    host = (urlparse(u).hostname or "").lower().rstrip(".")',
     '    host = (urlparse(u).hostname or "").lower()',
     ["TestFiveBlocks.test_a_proof_on_a_name_that_never_resolves_is_refused"], CHECK),

    ("T139 a FILL marker left in the href is a real address",
     '    if "FILL" in u:', "    if False:",
     ["TestFiveBlocks.test_a_proof_still_carrying_a_fill_marker_is_refused"], CHECK),

    ("T139 a card is never closed at its own end tag",
     '                while self.open_cards and self.cards[self.open_cards[-1]]["depth"] >= depth:',
     '                while self.open_cards and self.cards[self.open_cards[-1]]["depth"] > depth:',
     ["TestFiveBlocks.test_a_proof_link_outside_every_card_covers_none"], CHECK),

    ("T139 an unclosed tag detaches every card boundary under it",
     "        if tag in self.stack:", "        if self.stack and self.stack[-1] == tag:",
     ["TestFiveBlocks.test_an_unclosed_paragraph_does_not_keep_a_card_open_past_its_end"],
     CHECK),

    ("T139 a card with no id of its own is named by an empty string",
     '            "id": a.get("data-vista-card", "").strip() or f"#{len(self.cards) + 1}",',
     '            "id": a.get("data-vista-card", "").strip(),',
     ["TestFiveBlocks.test_a_card_with_an_empty_id_is_named_by_its_position"], CHECK),

    # -- what the reader sees ---------------------------------------------
    ("T139 text outside every element is never collected",
     "        elif not self.stack and data.strip():", "        elif False:",
     ["TestWhatTheReaderSEES.test_text_left_outside_every_element_is_refused"], CHECK),

    ("T139 the loose text is collected and then never reported",
     "    for text_out in v.loose if v.declared_structure else []:",
     "    for text_out in []:",
     ["TestWhatTheReaderSEES.test_a_comment_holding_a_nested_comment_is_caught_where_it_leaks"],
     CHECK),

    ("T139 a page that declares no body is judged as if it had one",
     "    for text_out in v.loose if v.declared_structure else []:",
     "    for text_out in v.loose:",
     ["TestWhatTheReaderSEES.test_a_page_that_declares_no_body_keeps_its_text"], CHECK),

    ("T139 the shipped template lets its own instructions leak onto the page",
     "  Write no `<!` + `--` inside this comment: it would end here, and the rest\n"
     "  would print at the top of the page.",
     "  Fill in the <!" + "-- FILL --" + "> notes.",
     ["TestShippedTemplate.test_the_template_is_refused_for_its_placeholder_and_nothing_else"],
     TEMPLATE),

    # -- answers the dark scheme ------------------------------------------
    ("T139 one theme is enough",
     "    if not DARK_THEME.search(css):", "    if False:",
     ["TestBothThemes.test_a_page_with_a_single_theme_is_refused"], CHECK),

    ("T139 the shipped template loses its dark palette",
     "  @media (prefers-color-scheme: dark) {", "  @media (min-width: 0px) {",
     ["TestShippedTemplate.test_the_template_is_refused_for_its_placeholder_and_nothing_else"],
     TEMPLATE),

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
