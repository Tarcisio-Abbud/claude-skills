#!/usr/bin/env python3
"""Assembles `baseline-<date>.md` beside this file from `tk-prune-measure`.

Run from the repo root:

    python3 docs/prune/baseline.py <date> <plugin-cache-dir> > docs/prune/baseline-<date>.md

Every number in the output is the bin's own, read back from `--json --targets`.
This script chooses the files, lays the rows out and computes the totals; it
measures nothing itself, which is why it lives beside the document rather than
in `tk/bin` — the bin's contract is one file per call, and the loop belongs to
whoever is calling it.
"""

import glob
import json
import os
import subprocess
import sys

BIN = os.path.join("tk", "bin", "tk-prune-measure")

# (metric, column heading). The narrow headings are the point: forty-two rows of
# twelve numbers only read as a table if the table fits the page.
COLS = [("lines", "lines"), ("body_words", "words"), ("sentences", "sent"),
        ("mean_sentence_words", "mean"), ("max_sentence_words", "max"),
        ("sentences_over_30", ">30"), ("description_words", "desc"),
        ("inline_evidence", "evid"), ("pointers", "ptr"),
        ("negations", "neg"), ("defined_terms", "term"),
        ("terms_defined_in_sibling", "dup")]


def measure(path):
    out = subprocess.run([sys.executable, BIN, path, "--json", "--targets"],
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def cell(report, key):
    """The value, in bold when `--targets` marked it over its ceiling."""
    value = report["metrics"][key]
    if value is None:
        return "—"
    marks = {m["metric"]: m["status"] for m in report["targets"]}
    return f"**{value}**" if marks.get(key) == "over" else str(value)


def table(rows):
    out = ["| skill | " + " | ".join(label for _, label in COLS) + " |",
           "|---|" + "---|" * len(COLS)]
    for name, report in rows:
        out.append(f"| `{name}` | " + " | ".join(cell(report, k) for k, _ in COLS) + " |")
    return "\n".join(out)


def total(rows, key):
    values = [r["metrics"][key] for _, r in rows if r["metrics"][key] is not None]
    return sum(values)


def mean(rows, key):
    values = [r["metrics"][key] for _, r in rows if r["metrics"][key] is not None]
    return round(sum(values) / len(values), 1) if values else 0


def over(rows, key=None):
    return sum(1 for _, r in rows for m in r["targets"]
               if m["status"] == "over" and (key is None or m["metric"] == key))


def main(date, cache):
    tk = [(os.path.relpath(p, os.path.join("tk", "skills")), measure(p))
          for p in sorted(glob.glob(os.path.join("tk", "skills", "*", "*.md")))]
    matt = [(os.path.relpath(p, os.path.join(cache, "skills")), measure(p))
            for p in sorted(glob.glob(os.path.join(cache, "skills", "*", "*", "SKILL.md")))]
    ceilings = [(m["metric"], m["target"]) for m in tk[0][1]["targets"]]
    per_ceiling = "\n".join(
        f"| `{key}` | {value} | {over(tk, key)}/{len(tk)} | {over(matt, key)}/{len(matt)} |"
        for key, value in ceilings)
    word_ratio = round(mean(tk, "body_words") / mean(matt, "body_words"), 1)
    neg_ratio = round(mean(tk, "negations") / mean(matt, "negations"), 1)
    matt_max_over = over(matt, "max_sentence_words")

    print(f"""# Pruning baseline — {date}

The numbers a pruning pass measures against, for every markdown file of the `tk` plugin and
every skill of the `mattpocock-skills` plugin installed on this machine. It is the first run of
`tk-prune-measure` (ticket #185, spec #184), and the figure the last slice of that spec measures
its own result against.

Every number here is the bin's output. A value in **bold** is one `--targets` marked as over the
ceiling the bin carries. The columns with no ceiling — words, sentences, pointers, negations,
defined terms — are reported and not judged, which is the bin's rule rather than an omission
here: a negation the regex finds may be steering the agent or may be naming an outcome, and only
the person reading the line can tell.

## How it was produced

```sh
python3 docs/prune/baseline.py {date} \\
    {cache} \\
    > docs/prune/baseline-{date}.md
```

The bin takes one file per call, so the loop belongs to the caller. A single file, either way:

```sh
tk/bin/tk-prune-measure tk/skills/dispatch/SKILL.md --targets
tk/bin/tk-prune-measure tk/skills/dispatch/SKILL.md --json --targets
```

## Columns

| column | metric | ceiling |
|---|---|---|
| lines | lines in the file, frontmatter and code blocks included | — |
| words | words of the body, frontmatter and code blocks excluded | — |
| sent | sentences, ending at a full stop and at the end of a list item, table row or heading | — |
| mean | mean words per sentence | 22 |
| max | words in the longest sentence | 25 |
| >30 | sentences over 30 words | 4 |
| desc | words in the frontmatter description (`—` when the file carries none) | 30 |
| evid | inline evidence: ISO dates, "measured", a count before "times" or "before" | 0 |
| ptr | pointers to other files | — |
| neg | negations: never, not, no, don't, do not | — |
| term | defined terms | — |
| dup | terms a sibling file in the same directory defines too | 0 |

## `tk` — this plugin

{table(tk)}

## `mattpocock-skills` {os.path.basename(cache)} — the calibration set

{table(matt)}

## The gap

| | `tk` ({len(tk)} files) | `mattpocock-skills` ({len(matt)} files) |
|---|---|---|
| body words, total | {total(tk, "body_words")} | {total(matt, "body_words")} |
| body words, mean per file | {mean(tk, "body_words")} | {mean(matt, "body_words")} |
| sentences over 30 words, total | {total(tk, "sentences_over_30")} | {total(matt, "sentences_over_30")} |
| negations, total | {total(tk, "negations")} | {total(matt, "negations")} |
| negations, mean per file | {mean(tk, "negations")} | {mean(matt, "negations")} |
| marks over a ceiling, total | {over(tk)} | {over(matt)} |

The mean `tk` file carries {word_ratio} times the words of the mean `mattpocock-skills` file, and
{neg_ratio} times the negations. That is the gap the spec estimated, now measured.

## The ceilings against the calibration set

The spec sets the ceilings so that the `mattpocock-skills` set passes them. Read one ceiling at a
time rather than one file at a time, five of the six do that, and one does not.

| ceiling | value | `tk` over | `mattpocock-skills` over |
|---|---|---|---|
{per_ceiling}

`max_sentence_words` is the exception, and it is not near the line: it marks {matt_max_over} of the
{len(matt)} files of the set it was calibrated against. Where the number comes from explains it.
"An instruction runs to about 25 words" is a rule of THIS house's `shared-CLAUDE.md`, and the
`mattpocock-skills` set never adopted it. The other five ceilings describe a shape any skill can
be held to; this one describes a house style, applied to a corpus that writes in another.

The value stays where the ticket puts it. Moving a ceiling is a decision about the rule, and the
bin is not the place to take it. What the measurement adds is the consequence: a report that
reads a mark on this ceiling as a defect will call {matt_max_over} well-written third-party skills
defective. The slice that writes the pruning skill (#186) is where that is either accepted, or
this ceiling joins negations and defined terms as report-only, or "instruction" is bound to
something narrower than every sentence in the file.""")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__.strip(), file=sys.stderr)
        sys.exit(2)
    main(sys.argv[1], sys.argv[2])
