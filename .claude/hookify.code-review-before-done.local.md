---
name: code-review-before-done
enabled: true
event: stop
action: block
conditions:
  - field: transcript
    operator: contains
    pattern: git commit
  - field: transcript
    operator: not_contains
    pattern: code-review
---

**Commit made without a code-review in this session.**

Every code change delivered goes through the two-axis review (Standards + Spec),
`/mattpocock-skills:code-review`, before being called done.

Since 2026-08-28 the two axes run in a SEPARATE, COLD session. The HOT session writes the
code, commits and pushes. A COLD one then reads the ticket and reviews. A commit with no
review in THIS transcript is therefore often correct. Name the case, satisfy it, then finish:

  - **the hot session of a ticket** -- the review is the next session. Name the artefact that
    summons it there: the ticket, or the queue item, still OPEN. Nothing open to name means
    nothing will summon the review, so open it before finishing;
  - **a small commit straight to main** -- the review still runs retroactively, from a fresh
    session, and its findings go into an immediate follow-up commit;
  - **nothing was committed here** -- the transcript only mentions a commit;
  - **the commit carries no code and no prose an agent follows** -- a typo, a report, a
    wiki page.

That last case is narrow. Prose an agent follows -- a skill, a CLAUDE.md, a runbook -- takes
both axes exactly as code does. A docs-only commit is NOT an exit on its own.

Use the full name. `/code-review` alone is Claude Code's native review, a different skill,
and does not satisfy this rule.

**Known weakness, so you judge the block instead of obeying it blindly:** the conditions are
substring matches over the whole transcript. `git commit` matches even when it was only
discussed, and `code-review` counts as satisfied the moment the phrase appears anywhere --
including in this very message. So it releases itself on the second stop attempt (which is
also what keeps it from looping). Treat it as a reminder, not as proof either way.

---

NOTE (2026-08-04, revised 2026-09-25) -- addressed to whoever EDITS this file, not to the
session the block above stopped.

This rule lives in more than one place ON PURPOSE. Two reasons, both measured:

  1. hookify globs `.claude/hookify.*.local.md` relative to the PROCESS CWD, and there is no
     single cwd that covers everything. A session working on a repo runs in that repo, the
     vault is another cwd, and the workspace root a third. A rule placed under only one of
     them silently never fires under the others.

     The canonical copy is this file, `claude/` in the private config repo, cloned on this
     machine at `/workspace/projects/.ambiente`. Every destination that
     `bin/hookify-propagate.py` lists tracks it byte for byte, and an edit here is not landed
     until each of them carries it. Some destinations are VERSIONED -- the config repo, the
     skills repo, the project repos -- so a change there is a commit, not just a file write;
     the script names each repo that owes one.

     The script only reports by default and writes under `--write`, because most copies are
     read by live sessions. A copy that differs from this file is drift for the script to
     report, never a second source: do not seed from it, and do not diff one copy against
     another to decide which is right.

     The Windows desktop kept a copy of its own until 2026-09-25 (#376), when the desktop
     became a client that opens its sessions inside the container.
  2. `config_loader.py` and the transcript reader both call `open(path, 'r')` with no
     `encoding=`. On Windows that resolves to cp1252. A rule file carrying one emoji is then
     skipped silently. A transcript carrying one emoji reads as "" -- 7 of 8 real ones tested.
     Every `field: transcript` condition then evaluated against an empty string, so the rule
     never fired. `env.PYTHONUTF8=1` in `~/.claude/settings.json` mitigates this globally.
     Keep this file ASCII anyway: it costs nothing and survives that setting being lost.
