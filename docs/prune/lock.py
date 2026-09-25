#!/usr/bin/env python3
"""Assembles `tk/tests/prune-lock.json` from `tk-prune-measure`.

Run from the repo root:

    python3 docs/prune/lock.py 2026-09-23 > tk/tests/prune-lock.json

or, to lock ONE more file a later pass pruned, leaving every other row as it is:

    python3 docs/prune/lock.py --add 2026-09-22 tk/skills/kickoff/WINDOW.md \
        > prune-lock.new && mv prune-lock.new tk/tests/prune-lock.json

The lock is what holds the pruning track's result (spec #184) after the track
closed: `tk/tests/test_prune_lock.py` re-measures every file below and refuses a
tree where one of them grew past its slack or gained a ceiling mark. This script
writes the numbers; the test spends them. Neither counts anything itself — every
figure is read back from the bin, as `baseline.py` beside this file does.

REGENERATING IS A DECISION, not a repair. A file over its slack means either the
prose grew back or the growth was earned; the second case is a pruning verdict,
and re-running this script records it. Say in the commit message which it was.

`--add` is the narrow form of that decision. It measures only the files it names,
copies every other row of the committed lock verbatim, and stamps the new rows
`"locked": <date>`: their numbers postdate the lock's baseline document, so the test
does not compare them against that document. A pruned or moved row's provenance is
then the report it names; a guarded row names none, and its provenance is that date.
"""

import json
import os
import subprocess
import sys

BIN = os.path.join("tk", "bin", "tk-prune-measure")

# The slack the lock allows over each locked number. Prose an agent reads gets
# edited between prunings — a correction adds a clause, a review restores a line
# — and a lock with no slack turns every such edit into a red suite. Ten per cent
# is wide enough for the edits and far narrower than the growth the track
# measured: `wrap-up/SKILL.md` went 4499 -> 5236 body words, +16%, in the four
# days between the first baseline and its own pruning pass.
SLACK = 0.10

# The files the pruning track rewrote, and the report that records each pass.
# `docs/prune/<report>` is the provenance of every number below; the test derives
# its own completeness check from those same report filenames, so a pruned skill
# dropped from this table is caught rather than silently unlocked.
PRUNED = [
    ("tk/skills/dispatch/SKILL.md", "dispatch-report.md"),
    ("tk/skills/docs-audit/SKILL.md", "docs-audit-report.md"),
    ("tk/skills/fleet/SKILL.md", "fleet-report.md"),          # T443, after T292 and #114
    ("tk/skills/kickoff/SKILL.md", "kickoff-report.md"),
    ("tk/skills/kickoff/AFK.md", "kickoff-report.md"),
    ("tk/skills/kickoff/WINDOW.md", "kickoff-report.md"),     # second pass, T449
    ("tk/skills/review/SKILL.md", "review-report.md"),
    ("tk/skills/second-opinion/SKILL.md", "second-opinion-report.md"),
    ("tk/skills/verify/SKILL.md", "verify-report.md"),
    ("tk/skills/wrap-up/SKILL.md", "wrap-up-report.md"),
]

# The files those passes CREATED to hold material they took out. They carry the
# other half of the track's words, and a lock that watched only the eight above
# would let every pruned sentence come back next door.
MOVED = [
    ("tk/skills/dispatch/LOOP.md", "dispatch-report.md"),
    ("tk/skills/review/BRIEF.md", "review-report.md"),
    ("tk/skills/verify/HANDOFF.md", "verify-report.md"),
    ("tk/skills/merge-gate/SKILL.md", "wrap-up-report.md"),
    ("tk/skills/wrap-up/REPORT.md", "wrap-up-report.md"),
    ("tk/reference/queue.md", "kickoff-report.md"),
    ("tk/reference/session-finding.md", "kickoff-report.md"),
    ("tk/skills/kickoff/RESUME.md", "kickoff-report.md"),     # the split it named, #224
    ("tk/skills/kickoff/AUDIT.md", "kickoff-report.md"),      # the split it named, #225
]

# Files no pass has pruned yet, named one by one by the T443 verdict and locked AS
# FOUND so they cannot drift while they wait for one. The table is that verdict, not
# every unpruned file: `tk/skills/prune/` stays outside it. `kickoff/WINDOW.md` is why:
# read by every package and outside the lock, it went 2753 -> 6794 body words in three
# weeks. `slice-rules.md` and `vista.md` joined at T453: the tk-contract hands
# slice-rules.md to every role beside `subagent-policy.md`, already guarded below. A
# guarded row names no report — there is none — and its provenance is the lock's own
# date. When a pass prunes one of these, its row moves to PRUNED with the report it wrote.
GUARDED = [
    "tk/skills/kickoff/FINDINGS.md",
    "tk/skills/kickoff/HYGIENE.md",
    "tk/skills/kickoff/LANE-CONTRACT.md",
    "tk/skills/kickoff/LEDGER.md",
    "tk/skills/kickoff/REVIEW-CONTRACT.md",
    "tk/skills/kickoff/ROOT-CAUSE.md",
    "tk/skills/kickoff/STALE.md",
    "tk/skills/kickoff/UNION.md",
    "tk/skills/merge-gate/DIGEST.md",
    "tk/reference/subagent-policy.md",
    "tk/reference/slice-rules.md",
    "tk/reference/vista.md",
]


def measure(path):
    out = subprocess.run([sys.executable, BIN, path, "--json", "--targets"],
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out)


# A file the tree RENAMED after the lock was written. The baseline table is keyed
# by the name the pruning pass measured it under, so the row carries that name beside
# the new path: without it the comparison against `docs/prune/baseline-<date>.md`
# silently stops covering the file. The NUMBERS are untouched by a rename.
# Empty since the 2026-09-23 baseline, which measured merge-gate/SKILL.md under its
# own path; the 2026-09-01 one knew it as wrap-up/MERGE-GATE.md (ambiente#226).
BASELINE_NAME = {}


def row(measured, role, report, path=None):
    """One locked row: the two uncapped numbers, and the marks the file carries.
    A guarded row passes `report=None` and carries no `report` key.

    `over` is the list of ceilings the bin marks TODAY. The test reads it as a
    permission — every mark here may stay, and no other mark may appear — so a
    later pruning that clears one keeps the suite green without a regeneration.
    """
    return {
        "role": role,
        **({"report": report} if report else {}),
        "lines": measured["metrics"]["lines"],
        "body_words": measured["metrics"]["body_words"],
        "over": [m["metric"] for m in measured["targets"] if m["status"] == "over"],
        **({"baseline": BASELINE_NAME[path]} if path in BASELINE_NAME else {}),
    }


def plan():
    return ([(path, "pruned", report) for path, report in PRUNED]
            + [(path, "moved", report) for path, report in MOVED]
            + [(path, "guarded", None) for path in GUARDED])


def main(date):
    rows = plan()
    measured = {path: measure(path) for path, _, _ in rows}
    # The ceilings travel with the lock: `over` names a verdict, and a ceiling
    # moved after the lock was written would silently redefine every row. Read
    # off a measured file rather than listed here — the bin owns them, and
    # `--targets` emits one row per ceiling whatever the file said.
    ceilings = {m["metric"]: m["target"]
                for m in next(iter(measured.values()))["targets"]}
    print(json.dumps({
        "generated": date,
        "baseline": f"docs/prune/baseline-{date}.md",
        "generator": "docs/prune/lock.py",
        "slack": SLACK,
        "ceilings": ceilings,
        "files": {path: row(measured[path], role, report, path)
                  for path, role, report in rows},
    }, indent=2, sort_keys=False))


def add(date, paths):
    """The committed lock with `paths` measured and (re)locked, every other row
    copied verbatim. A path must already sit in PRUNED, MOVED or GUARDED: those
    tables are the list of what the lock holds, and `--add` never widens it by itself."""
    rows = plan()
    unknown = sorted(set(paths) - {path for path, _, _ in rows})
    if unknown:
        print(f"not in PRUNED, MOVED or GUARDED: {unknown} — add the row to the table first",
              file=sys.stderr)
        sys.exit(2)
    with open(LOCK, encoding="utf-8") as f:
        lock = json.load(f)
    files = {}
    for path, role, report in rows:
        if path in paths:
            files[path] = {**row(measure(path), role, report, path), "locked": date}
        elif path in lock["files"]:
            files[path] = lock["files"][path]
    lock["files"] = files
    print(json.dumps(lock, indent=2, sort_keys=False))


LOCK = os.path.join("tk", "tests", "prune-lock.json")


if __name__ == "__main__":
    if len(sys.argv) >= 4 and sys.argv[1] == "--add":
        add(sys.argv[2], sys.argv[3:])
    elif len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        print(__doc__.strip(), file=sys.stderr)
        sys.exit(2)
