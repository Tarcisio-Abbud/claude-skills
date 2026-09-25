#!/usr/bin/env python3
"""Mutation proof for `test_revisao_contrato.py`.

Each mutation puts back one defect the review of PR #132 found, then requires the tests named
for it to FAIL. A test that still passes with the defect back guards nothing.

Two checks keep the harness honest, both borrowed from `whatsapp/tests`:

- a test named by a mutation must EXIST, or a typo reports as a killed mutant;
- every test in the suite is enumerated, and any test no mutation names is listed UNPROVED.

Unlike the whatsapp runner, an UNPROVED test does not fail the run: the tests written before
this runner guard behaviour no review found broken, and they are listed so a later slice can
write their mutants. A PROBLEM — a survivor, a missing test, an anchor that is not unique —
fails it.

Run: python3 contrato/tests/mutations_revisao_contrato.py
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.abspath(os.path.join(HERE, os.pardir, "skills", "revisao-contrato", "reference"))
WORKFLOW = os.path.join(REF, "revisao-contrato.workflow.js")
APPLY = os.path.join(REF, "apply-edits.py")
BRUTOS = os.path.join(REF, "brutos.py")
SCOUT = os.path.join(REF, "docx-scout.py")

# (file, what the defect is, the literal to replace, its replacement, tests it must kill)
MUTATIONS = [
    (
        WORKFLOW,
        "convergence counts raw ids, so two findings of one lens merged skip the refuter",
        "f.convergencia = new Set(f.origem.map(o => lensOfRaw.get(o) || o)).size",
        "f.convergencia = f.origem.length",
        ["test_two_findings_of_one_lens_merged_are_still_single_lens"],
    ),
    (
        WORKFLOW,
        "an unknown modo falls through to a full review",
        "if (!MODOS.includes(modo)) throw",
        "if (false) throw",
        ["test_an_unknown_modo_stops_and_spawns_nothing"],
    ),
    (
        APPLY,
        "a bare --folga 10 reads as 1000%",
        '    if not s.endswith("%"):\n        raise ValueError(',
        '    if not s.endswith("%"):\n        return float(s)\n        raise ValueError(',
        ["test_apply_refuses_a_folga_without_percent"],
    ),
    (
        WORKFLOW,
        "a critic extra that slugs onto an active lens takes its key, colliding brutos and raw ids",
        "for (let n = 2; takenKeys.has(key); n++)",
        "for (let n = 2; false; n++)",
        ["test_an_extra_lens_never_takes_an_active_lens_key"],
    ),
    (
        WORKFLOW,
        "the apply recomputes saida from contrato and data instead of taking the review's",
        "if (modo === 'aplicar' && !a.saida) throw",
        "if (false) throw",
        ["test_apply_reads_the_review_saida_and_never_recomputes_it"],
    ),
    (
        APPLY,
        "a .docx apply snapshots the .docx only, never the current text",
        'snaps = [(opts.contrato, os.path.join(vdir, f"{stem}-{opts.data}.md"))]\n    if ext.lower() != ".md":',
        "snaps = []\n    if True:",
        ["test_apply_on_a_docx_snapshots_the_text_as_markdown"],
    ),
    (
        BRUTOS,
        "brutos.py overwrites an achados-brutos.json it did not write",
        "if os.path.exists(json_path) and not json_is_ours(json_path):",
        "if False:",
        ["test_brutos_never_overwrites_a_json_it_did_not_write"],
    ),
    (
        APPLY,
        "apply-edits.py overwrites a -aplicado- .docx it did not write",
        "if dest and os.path.exists(dest) and not docx_is_ours(dest):",
        "if False:",
        ["test_apply_never_overwrites_a_docx_it_did_not_write"],
    ),
    (
        WORKFLOW,
        "the critic runs at effort high",
        "{ label: 'critico', phase: 'Crítico', schema: CRITIC, model: 'opus' }",
        "{ label: 'critico', phase: 'Crítico', schema: CRITIC, model: 'opus', effort: 'high' }",
        ["test_effort_high_only_on_verifier_and_report"],
    ),
    (
        WORKFLOW,
        "the lenses run at effort high",
        "phase: 'Lentes', schema: FINDINGS, model: l.model })",
        "phase: 'Lentes', schema: FINDINGS, model: l.model, effort: 'high' })",
        ["test_effort_high_only_on_verifier_and_report"],
    ),
    (
        SCOUT,
        "the numbering check asks only for one numbered paragraph, not for as many as carry w:numPr",
        "if not found or found < by_numpr:",
        "if not found:",
        ["test_scout_stops_when_style_numbering_is_lost"],
    ),
    (
        WORKFLOW,
        "the parties words win over a leading clause number",
        "  m = s.match(/^\\s*(?:cl[aá]usula\\s*)?(\\d{1,3})(?:\\.\\d+)*/i); if (m) return `c${m[1]}`\n",
        "",
        ["test_a_leading_clause_number_wins_over_the_parties_words"],
    ),
]


def suite_test_ids():
    """method name -> full unittest id. Derived, never hand-kept."""
    suite = unittest.TestLoader().discover(start_dir=HERE, pattern="test_*.py")
    ids = {}

    def walk(s):
        for item in s:
            if isinstance(item, unittest.TestSuite):
                walk(item)
            else:
                ids[item.id().rsplit(".", 1)[-1]] = item.id()

    walk(suite)
    return ids


def run_tests(names, ids):
    """Run the named tests against whatever is on disk. True when all passed."""
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "-q"] + [ids[n] for n in names],
        cwd=HERE, capture_output=True, text=True, timeout=600,
    )
    return result.returncode == 0, result.stdout + result.stderr


def main():
    files = sorted({m[0] for m in MUTATIONS})
    originals = {}
    for path in files:
        with open(path, encoding="utf-8") as fh:
            originals[path] = fh.read()

    ids = suite_test_ids()
    available = set(ids)
    named = set()
    problems = []

    ok, output = run_tests(sorted(available), ids)
    if not ok:
        print("the suite is not green before mutating; fix that first\n%s" % output)
        return 1

    backups = {}
    for path in files:
        backups[path] = tempfile.mkstemp(prefix="revisao-contrato-backup-")[1]
        shutil.copy(path, backups[path])
    try:
        for path, label, needle, replacement, targets in MUTATIONS:
            named.update(targets)
            missing = [t for t in targets if t not in available]
            if missing:
                problems.append("%s: names a test that does not exist: %s" % (label, missing))
                continue
            original = originals[path]
            if original.count(needle) != 1:
                problems.append("%s: its anchor matches %d times, so the mutation is not the one described"
                                % (label, original.count(needle)))
                continue
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(original.replace(needle, replacement))
            try:
                # One at a time, so a survivor cannot hide behind a sibling that failed.
                survivors = [t for t in targets if run_tests([t], ids)[0]]
            finally:
                shutil.copy(backups[path], path)
            if survivors:
                problems.append("%s: SURVIVED — %s still pass with the defect back" % (label, survivors))
            else:
                print("killed: %s" % label)
    finally:
        for path in files:
            shutil.copy(backups[path], path)
            os.unlink(backups[path])

    for name in sorted(available - named):
        print("UNPROVED: %s — no mutation names it" % name)
    for problem in problems:
        print("PROBLEM: %s" % problem)
    print("\n%d mutations, %d problems, %d of %d tests proved"
          % (len(MUTATIONS), len(problems), len(named & available), len(available)))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
