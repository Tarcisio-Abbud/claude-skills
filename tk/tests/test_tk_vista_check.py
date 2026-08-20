#!/usr/bin/env python3
"""Regression suite for `tk-vista-check` (../bin/tk-vista-check).

Run: python3 -m unittest discover -s tk/tests   (stdlib only, no deps)

Every test here is proved by MUTATION — `mutations_vista.py` beside it puts each
defect back and requires the test named for it to fall. A test that still passes
with the guard removed protects nothing.

The suite drives the real script as a SUBPROCESS and asserts the literal exit
code, because that code is what a wrap-up (and any hook) reads across a process
boundary: a symbolic assertion on a Python function would leave `sys.exit`
untested and the number it hands back unproved.

`PAGE` below is the smallest page that qualifies, written out here rather than
loaded from `../reference/vista-template.html`: a fixture derived from the
shipped template would agree with any defect the template grew. The template is
checked too, in `TestShippedTemplate`, which is a different question — is the
file we hand people still valid — and it is asked separately on purpose.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CHECK = os.path.join(HERE, os.pardir, "bin", "tk-vista-check")
TEMPLATE = os.path.join(HERE, os.pardir, "reference", "vista-template.html")

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Vista</title>
<style>
  :root { --bg:#ffffff; --ink:#111111; }
  @media (prefers-color-scheme: dark) { :root { --bg:#111111; --ink:#eeeeee; } }
  body { background:var(--bg); color:var(--ink); }
</style></head>
<body><main>
<ul data-vista-bloco="stats"><li><b>1</b><span>slice</span></li></ul>
<div data-vista-bloco="cards">
  <article data-vista-card="T001" data-vista-desfecho="open" data-vista-risco="low">
    <h4>T001 — what it delivered</h4>
    <p><a data-vista-bloco="prova" href="https://github.com/acme/repo/pull/1">proof — PR #1</a></p>
  </article>
</div>
<div data-vista-bloco="saldo">1 closed, 2 open</div>
</main></body></html>
"""

SECOND_CARD = """  <article data-vista-card="T002" data-vista-desfecho="merged" data-vista-risco="high">
    <h4>T002</h4>
  </article>
"""


class CheckTest(unittest.TestCase):
    def setUp(self):
        self.tmp = os.path.realpath(tempfile.mkdtemp(prefix="tk-vista-test."))
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def check(self, html, name="vista.html", encoding="utf-8"):
        path = os.path.join(self.tmp, name)
        with open(path, "w", encoding=encoding) as f:
            f.write(html)
        return self.run_on(path)

    def run_on(self, *paths):
        return subprocess.run([sys.executable, CHECK, *paths],
                              capture_output=True, text=True)

    def assertRefused(self, html, *needles):
        r = self.check(html)
        self.assertEqual(r.returncode, 1, f"expected a refusal, got:\n{r.stdout}{r.stderr}")
        for needle in needles:
            self.assertIn(needle, r.stdout)

    def assertAccepted(self, html):
        r = self.check(html)
        self.assertEqual(r.returncode, 0, f"expected acceptance, got:\n{r.stdout}{r.stderr}")


class TestSelfContained(CheckTest):
    def test_the_smallest_qualifying_page_is_accepted(self):
        self.assertAccepted(PAGE)

    def test_a_stylesheet_link_is_refused(self):
        self.assertRefused(
            PAGE.replace("<style>", '<link rel="stylesheet" href="https://cdn.invalid/a.css">\n<style>'),
            "external resource", "link")

    def test_a_link_the_human_clicks_is_kept(self):
        # block 4 IS an off-machine link: the page loads nothing until a click
        self.assertAccepted(PAGE.replace(">proof — PR #1<", ">https://github.com/acme/repo/pull/1<"))

    def test_a_protocol_relative_script_is_refused(self):
        self.assertRefused(PAGE.replace("<style>", '<script src="//cdn.invalid/a.js"></script>\n<style>'),
                           "external resource")

    def test_a_relative_image_path_is_refused_though_it_costs_no_network(self):
        # self-contained, not merely offline: the file travels alone
        self.assertRefused(PAGE.replace("<main>", '<main><img src="logo.png">'),
                           "external resource")

    def test_a_data_uri_image_is_kept(self):
        self.assertAccepted(PAGE.replace("<main>", '<main><img alt="" src="data:image/gif;base64,R0lGOD">'))

    def test_a_srcset_candidate_reaching_the_network_is_refused(self):
        self.assertRefused(PAGE.replace("<main>", '<main><img alt="" srcset="https://cdn.invalid/a.png 2x">'),
                           "external resource")

    def test_an_import_of_a_neighbouring_stylesheet_is_refused(self):
        # no url() in it: only the @import guard can catch this one
        self.assertRefused(PAGE.replace("<style>", "<style>\n  @import 'theme.css';"),
                           "@import")

    def test_a_css_url_reaching_the_network_is_refused(self):
        self.assertRefused(PAGE.replace("body {", "body { background-image:url(https://cdn.example/a.png);"),
                           "CSS fetches")

    def test_a_css_url_on_a_relative_path_is_refused(self):
        # no scheme to catch here: only the function-argument rule sees it
        self.assertRefused(PAGE.replace("body {", "body { background-image:url(logo.png);"),
                           "CSS fetches")

    def test_a_script_element_is_refused_whatever_it_holds(self):
        self.assertRefused(PAGE.replace("</main>", "</main><script>var x = 1;</script>"),
                           "the page runs code")

    def test_an_image_built_in_script_is_refused(self):
        # no rule for `Image` could have caught this: the class of thing is the
        # rule, and the class is "this page runs code"
        self.assertRefused(
            PAGE.replace("</main>", '</main><script>var i=new Image();i.src="http://x.example/p"</script>'),
            "the page runs code")

    def test_a_bracketed_fetch_is_refused(self):
        self.assertRefused(
            PAGE.replace("</main>", '</main><script>window["fet"+"ch"]("http://x.example/d")</script>'),
            "the page runs code")

    def test_an_aliased_xhr_is_refused(self):
        self.assertRefused(
            PAGE.replace("</main>", '</main><script>var X=window["XMLHttpRequest"];new X()</script>'),
            "the page runs code")

    def test_a_javascript_url_is_refused(self):
        self.assertRefused(PAGE.replace('href="https://github.com/acme/repo/pull/1"',
                                        'href="javascript:location=1"'),
                           "the page runs code")

    def test_a_javascript_url_split_by_a_tab_is_refused(self):
        # measured in Chromium: the link EXECUTES. WHATWG removes tab, CR and LF
        # from the whole string before parsing, so the browser reads a scheme
        # where `.strip()` sees none
        self.assertRefused(PAGE.replace('href="https://github.com/acme/repo/pull/1"',
                                        'href="java\tscript:alert(1)"'),
                           "the page runs code")

    def test_a_javascript_url_split_by_a_newline_is_refused(self):
        self.assertRefused(PAGE.replace('href="https://github.com/acme/repo/pull/1"',
                                        'href="java\nscript:alert(1)"'),
                           "the page runs code")

    def test_a_javascript_url_behind_a_control_character_is_refused(self):
        self.assertRefused(PAGE.replace('href="https://github.com/acme/repo/pull/1"',
                                        'href="\x01 javascript:alert(1)"'),
                           "the page runs code")

    def test_a_javascript_url_in_capitals_is_refused(self):
        self.assertRefused(PAGE.replace('href="https://github.com/acme/repo/pull/1"',
                                        'href="JAVASCRIPT:alert(1)"'),
                           "the page runs code")

    def test_a_vbscript_url_is_refused(self):
        self.assertRefused(PAGE.replace('href="https://github.com/acme/repo/pull/1"',
                                        'href="vbscript:msgbox 1"'),
                           "the page runs code")

    def test_a_meta_refresh_is_refused(self):
        self.assertRefused(
            PAGE.replace("<title>", '<meta http-equiv="refresh" content="0;url=http://x.example/">\n<title>'),
            "navigates on its own")

    def test_an_image_set_reaching_the_network_is_refused(self):
        self.assertRefused(
            PAGE.replace("body {", 'body { background-image:image-set("http://cdn.example/a.png" 1x);'),
            "CSS fetches")

    def test_a_class_named_http_is_not_an_address(self):
        # every place CSS fetches from is a FUNCTION, so the functions are the
        # whole list: a catch-all over the stylesheet text refused these two
        self.assertAccepted(PAGE.replace("body {", ".http:hover { color:red; }\n  body {"))

    def test_an_address_inside_generated_text_is_not_a_fetch(self):
        self.assertAccepted(PAGE.replace(
            "body {", '.badge::after { content:"See http://example-internal/docs"; }\n  body {'))

    def test_an_event_handler_is_refused(self):
        self.assertRefused(PAGE.replace("<h4>T001", '<h4 onclick="void 0">T001'),
                           "the page runs code")

    def test_the_word_fetch_in_the_page_prose_is_not_a_network_call(self):
        # nothing scans prose for call-shaped words: the rule is about elements
        self.assertAccepted(PAGE.replace("what it delivered", "the fetch( in this heading is prose"))

    def test_a_self_closing_script_is_refused_like_any_other(self):
        # `<script/>` fires handle_startendtag, never handle_endtag: a rule that
        # only watches the closing tag never sees this one
        self.assertRefused(PAGE.replace("<main>", "<main><script/>"), "the page runs code")

    def test_an_empty_src_is_refused(self):
        # `src=""` is not "no URL": the browser resolves it to the page itself
        self.assertRefused(PAGE.replace("<main>", '<main><img alt="" src="">'),
                           "external resource")

    def test_a_base_tag_is_refused(self):
        # <base> is judged by the URL rule like any other fetched attribute:
        # it needs no guard of its own, and a guard of its own would be one no
        # input can reach
        self.assertRefused(PAGE.replace("<title>", '<base href="https://x.invalid/"><title>'),
                           "external resource", "base")


class TestFiveBlocks(CheckTest):
    def test_the_stats_block_is_required(self):
        self.assertRefused(PAGE.replace('data-vista-bloco="stats"', 'class="stats"'), "block 1")

    def test_the_cards_region_is_required(self):
        self.assertRefused(PAGE.replace('data-vista-bloco="cards"', 'class="cards"'), "block 2")

    def test_a_page_with_no_card_is_refused(self):
        self.assertRefused(PAGE.replace('data-vista-card="T001"', 'class="card"'),
                           "no data-vista-card")

    def test_each_card_names_the_outcome_it_is_grouped_by(self):
        self.assertRefused(PAGE.replace('data-vista-desfecho="open" ', ""), "data-vista-desfecho")

    def test_each_card_carries_a_risk_tag(self):
        self.assertRefused(PAGE.replace('data-vista-risco="low"', ""), "data-vista-risco")

    def test_each_card_carries_a_proof_link(self):
        self.assertRefused(PAGE.replace('data-vista-bloco="prova" ', ""), "T001")

    def test_a_proof_marker_with_no_href_is_not_a_proof(self):
        self.assertRefused(PAGE.replace('href="https://github.com/acme/repo/pull/1"', ""), "block 4")

    def test_a_card_without_a_proof_is_named_even_when_a_sibling_has_one(self):
        r = self.check(PAGE.replace("</div>\n<div data-vista-bloco=\"saldo\"",
                                    SECOND_CARD + "</div>\n<div data-vista-bloco=\"saldo\""))
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("T002", r.stdout)
        self.assertNotIn("card T001", r.stdout)

    def test_a_proof_link_outside_every_card_covers_none(self):
        moved = PAGE.replace('    <p><a data-vista-bloco="prova" href="https://github.com/acme/repo/pull/1">proof — PR #1</a></p>\n', "")
        moved = moved.replace("</div>\n<div data-vista-bloco=\"saldo\"",
                              '<p><a data-vista-bloco="prova" href="https://github.com/acme/repo/pull/1">proof</a></p>'
                              "</div>\n<div data-vista-bloco=\"saldo\"")
        self.assertRefused(moved, "block 4", "T001")

    def test_an_unclosed_paragraph_does_not_keep_a_card_open_past_its_end(self):
        # the card's proof sits AFTER </article>: it belongs to no card, and a
        # parser that never closed the card would count it and pass
        loose = PAGE.replace('    <p><a data-vista-bloco="prova" href="https://github.com/acme/repo/pull/1">proof — PR #1</a></p>\n',
                             "    <p>a paragraph nobody closed\n")
        loose = loose.replace("  </article>\n",
                              '  </article>\n  <a data-vista-bloco="prova" href="https://github.com/acme/repo/pull/1">proof</a>\n')
        self.assertRefused(loose, "block 4", "T001")

    def test_an_outcome_outside_the_vocabulary_is_refused(self):
        self.assertRefused(PAGE.replace('data-vista-desfecho="open"', 'data-vista-desfecho="pending"'),
                           "outside the vocabulary")

    def test_every_outcome_of_the_vocabulary_is_accepted(self):
        for outcome in ("merged", "closed", "open", "carried", "blocked", "discarded"):
            with self.subTest(outcome=outcome):
                self.assertAccepted(PAGE.replace('data-vista-desfecho="open"',
                                                 f'data-vista-desfecho="{outcome}"'))

    def test_a_proof_pointing_at_a_reserved_placeholder_domain_is_refused(self):
        self.assertRefused(PAGE.replace("https://github.com/acme/repo/pull/1",
                                        "https://example.invalid/pull/0"),
                           "links no real proof", "placeholder name")

    def test_a_proof_on_a_name_that_never_resolves_is_refused(self):
        # RFC 2606 and RFC 6761 reserve these to resolve to nothing, ever
        for host in ("localhost", "forge.test", "forge.example", "example.com."):
            with self.subTest(host=host):
                self.assertRefused(PAGE.replace("github.com/acme/repo", host + "/acme/repo"),
                                   "links no real proof")

    def test_a_proof_that_is_only_a_fragment_is_refused(self):
        self.assertRefused(PAGE.replace("https://github.com/acme/repo/pull/1", "#"),
                           "links no real proof")

    def test_a_proof_still_carrying_a_fill_marker_is_refused(self):
        self.assertRefused(PAGE.replace("https://github.com/acme/repo/pull/1",
                                        "https://forge.example/FILL"),
                           "FILL marker")

    def test_a_card_with_an_empty_id_is_named_by_its_position(self):
        r = self.check(PAGE.replace('data-vista-card="T001"', 'data-vista-card=""')
                           .replace('data-vista-risco="low"', ""))
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("card #1", r.stdout)

    def test_the_balance_block_is_required(self):
        self.assertRefused(PAGE.replace('data-vista-bloco="saldo"', 'class="saldo"'), "block 5")


class TestWhatTheReaderSEES(CheckTest):
    """The page is judged by a human reading it, so text that should not be on
    it at all is a defect the five markers cannot see."""

    def test_text_left_outside_every_element_is_refused(self):
        self.assertRefused("A note nobody meant to publish.\n" + PAGE,
                           "text printed outside <body>")

    def test_a_page_that_declares_no_body_keeps_its_text(self):
        # `<html>` and `<body>` are optional in HTML5. Such a page holds its
        # prose at depth zero with nothing leaked, and the layout is free
        bare = PAGE.replace('<html lang="en">', "").replace("<body>", "").replace("</body>", "")
        # the sentence is wrapped in NOTHING: inside a <p> it would sit one
        # level deep and the fixture would prove nothing about depth zero
        bare = bare.replace("</html>", "").replace(
            "</head>", "</head>\nA note the author meant to publish.")
        self.assertAccepted(bare)

    def test_a_comment_holding_a_nested_comment_is_caught_where_it_leaks(self):
        # the outer comment ends at the FIRST `-->`; everything after it prints
        leaky = "<!-- fill in the <!-- FILL --> notes and keep the markers -->\n" + PAGE
        self.assertRefused(leaky, "text printed outside <body>")


class TestBothThemes(CheckTest):
    def test_a_page_with_a_single_theme_is_refused(self):
        self.assertRefused(PAGE.replace("prefers-color-scheme: dark", "min-width: 0px"),
                           "prefers-color-scheme")


class TestShippedTemplate(CheckTest):
    """The template is not a deliverable: its proof link is a placeholder, and
    the gate says so. What this asserts is that the placeholder is the ONLY
    thing wrong with it — the blocks, the themes and the self-containment of the
    file we hand people are checked here, and a second finding fails the test."""

    def test_the_template_is_refused_for_its_placeholder_and_nothing_else(self):
        r = self.run_on(TEMPLATE)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        findings = [l.strip("- ").strip() for l in r.stdout.splitlines() if l.startswith("  - ")]
        self.assertEqual(len(findings), 1, findings)
        self.assertIn("placeholder name", findings[0])


class TestUsage(CheckTest):
    def test_a_path_that_is_not_a_file_is_refused_before_it_is_opened(self):
        r = self.run_on(os.path.join(self.tmp, "nope.html"))
        self.assertEqual(r.returncode, 2)
        self.assertIn("not a regular file", r.stderr)

    def test_a_directory_is_refused_as_a_path_not_reported_as_a_bad_page(self):
        r = self.run_on(self.tmp)
        self.assertEqual(r.returncode, 2)
        self.assertIn("not a regular file", r.stderr)

    def test_a_byte_order_mark_ahead_of_the_doctype_still_reads(self):
        self.assertAccepted(PAGE)
        r = self.check(PAGE, name="bom.html", encoding="utf-8-sig")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_a_good_page_beside_a_bad_one_still_fails_the_run(self):
        good = os.path.join(self.tmp, "good.html")
        bad = os.path.join(self.tmp, "bad.html")
        with open(good, "w", encoding="utf-8") as f:
            f.write(PAGE)
        with open(bad, "w", encoding="utf-8") as f:
            f.write(PAGE.replace('data-vista-bloco="saldo"', ""))
        r = self.run_on(good, bad)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ok   " + good, r.stdout)
        self.assertIn("FAIL " + bad, r.stdout)


if __name__ == "__main__":
    unittest.main()
