#!/usr/bin/env python3
"""Assembles `tk/tests/prune-lock.json` from `tk-prune-measure`.

Run from the repo root:

    python3 docs/prune/lock.py 2026-09-01 > tk/tests/prune-lock.json

The lock is what holds the pruning track's result (spec #184) after the track
closed: `tk/tests/test_prune_lock.py` re-measures every file below and refuses a
tree where one of them grew past its slack or gained a ceiling mark. This script
writes the numbers; the test spends them. Neither counts anything itself — every
figure is read back from the bin, as `baseline.py` beside this file does.

REGENERATING IS A DECISION, not a repair. A file over its slack means either the
prose grew back or the growth was earned; the second case is a pruning verdict,
and re-running this script records it. Say in the commit message which it was.
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
    ("tk/skills/kickoff/SKILL.md", "kickoff-report.md"),
    ("tk/skills/kickoff/AFK.md", "kickoff-report.md"),
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
    ("tk/skills/wrap-up/MERGE-GATE.md", "wrap-up-report.md"),
    ("tk/skills/wrap-up/REPORT.md", "wrap-up-report.md"),
    ("tk/reference/queue.md", "kickoff-report.md"),
    ("tk/reference/session-finding.md", "kickoff-report.md"),
]


def measure(path):
    out = subprocess.run([sys.executable, BIN, path, "--json", "--targets"],
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def row(measured, role, report):
    """One locked row: the two uncapped numbers, and the marks the file carries.

    `over` is the list of ceilings the bin marks TODAY. The test reads it as a
    permission — every mark here may stay, and no other mark may appear — so a
    later pruning that clears one keeps the suite green without a regeneration.
    """
    return {
        "role": role,
        "report": report,
        "lines": measured["metrics"]["lines"],
        "body_words": measured["metrics"]["body_words"],
        "over": [m["metric"] for m in measured["targets"] if m["status"] == "over"],
    }


def main(date):
    plan = ([(path, "pruned", report) for path, report in PRUNED]
            + [(path, "moved", report) for path, report in MOVED])
    measured = {path: measure(path) for path, _, _ in plan}
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
        "files": {path: row(measured[path], role, report)
                  for path, role, report in plan},
    }, indent=2, sort_keys=False))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__.strip(), file=sys.stderr)
        sys.exit(2)
    main(sys.argv[1])
