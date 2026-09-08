# The cold-review contract — the reviewer who also fixes

The **cold reviewer** of a lane reviews one pull request it did not write, and fixes what it
confirms. It is not a second implementer and not a lens: it reads the whole lane against its
items, triages every finding on the merits, repairs what belongs to the lane, and hands back a
colour. `AFK.md` step 5 reaches this file for a lane that opened its own pull request under
`LANE-CONTRACT.md` beside this one; the same file binds the reviewer's own commits.

## Inputs

1. This file, then `LANE-CONTRACT.md` — the rules the implementer worked under bind the
   reviewer's fixes too.
2. `<items file>`, the full text of the lane's items, and `<brief file>` where a
   `/tk:second-opinion once` verdict decided a design: there the brief, not the item's
   statement, is what the lane was asked to build.
3. The pull request, body AND comments —
   `export GH_CONFIG_DIR="<the gh config dir>"`, then
   `gh pr view "<n>" -R "<owner>/<repo>" --comments`. The body says what the implementer left
   out and what it found stale; read it before the diff.
4. The lane's own worktree, at the path the dispatch names. `git fetch` there first, work on the
   lane's branch, and read the diff against `origin/main`.

## Steps

1. **Review both axes.** Run `mattpocock-skills:code-review` over `origin/main...HEAD` — three
   dots, so uncommitted work reviews as an empty diff and everything must already be pushed.
   Standards reads the repository's own rules and `../../reference/slice-rules.md`; Spec reads
   each item's criterion in `<items file>` and the tickets the pull request names. Where the
   skill asks which spec, hand it those two.
2. **Triage every finding on its merits.** A finding is not true because a reviewer said it:
   verify it against the code first. Three buckets, and every finding lands in exactly one —
   - **fixed** — a real defect or spec gap inside the lane's scope. Fix it, at most **one
     follow-up commit per axis** (`fix(<scope>): review findings — <axis>`), suite green, pushed.
   - **declined** — not a defect, or outside the lane's scope. One line each in the comment,
     carrying the written reason. A finding declined with no reason is a finding nobody can
     re-open.
   - **not handled** — real, but belonging to another file or another lane. One line each in the
     comment. Never into the queue.
3. **Verify by artifact.** After the fixes, re-run the suite and `git diff origin/main...HEAD
   --stat` on the final tree. **The suite runs in the FOREGROUND**, `timeout 900` or more, never
   in the background waiting on a notification — an agent that waited on a background `pytest`
   returned twice with no pull request and no comment. A mutation run, `timeout 1200` or more,
   only where a fix touched an anchor.
4. **Post ONE comment on the pull request**, in Portuguese, for a cold reader. It opens with
   "Review fria (Standards + Spec, modelo `<model>`)" and carries the three buckets by name —
   **consertado** with the commit sha of each fix, **recusado** with the reason of each, **não
   tratado** with one line each — and the suite numbers measured after the fixes.
5. **Report the colour** to the orchestrator, at most 25 lines: the counts found / fixed /
   declined / not handled, the follow-up commit shas, the suite result, and the colour below.

## The three colours, read off the five verdicts

The colour is not a new judgement. It reads the **five safe-to-merge verdicts** of
`../../reference/vista.md` — tests, review, criterion, reversal, closure — and reports which
one is red:

| Colour | When |
|---|---|
| **VERDE** | all five verdicts are green |
| **AMARELO** | one verdict is red and a **named human decision** covers it: the comment names who decided, what was decided, and where that decision is written down |
| **VERMELHO** | everything else — more than one red, or one red with no named decision behind it |

**No colour authorises a merge.** VERDE means the pull request is mergeable on the user's OK,
and the merge itself belongs to `../merge-gate/SKILL.md` and to the user. The reviewer never
merges, never deletes a branch, and never regenerates a lock file.

## A fix pull request gets the same cold review

A pull request born out of fixing a finding is reviewed cold exactly like the lane's original
pull request — same two axes, same triage, same comment, same colour. It is new code that
nobody has read: on 2026-09-06 six repair lanes each took a cold review of its own, and that is
the standard this line holds. The reviewer of the repair is never the agent that wrote it.

## The collision check closes the package

When every lane of the run has been reviewed, run the collision check over the run's OPEN pull
requests. `../merge-gate/SKILL.md` §5 owns the command and its exit codes; read it there rather
than here, so one file states the mechanics. The forge cannot answer this question: its own
`mergeable` field is blind between two pull requests.

A REAL collision — a pair that fails to merge, not a marker in a file a tool regenerates — goes
to one **Sonnet** agent, which resolves that pair alone and writes the resolved file. The agent
posts that file as a comment on the pull request, so the user merges without opening an editor:

```sh
gh pr comment "<n>" -R "<owner>/<repo>" --body-file "<abs path to the resolved file>"
```

`--body-file` takes a path; `--body @<file>` publishes the literal `@` string, which happened
twice on 2026-09-06 and was repaired by re-posting. The agent resolves and posts; it merges
nothing.

## Hard rules

Everything `LANE-CONTRACT.md` forbids the implementer, this file forbids the reviewer: no queue
writes, no writes to auto-memory or the wiki or the vault, no merge, no branch deletion, and no
work inside the live clones. A finding whose repair would grow the lane's scope becomes a line
of the comment, never a commit.
