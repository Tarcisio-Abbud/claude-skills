---
name: code-review-antes-de-pronto
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

Since 2026-08-28 the two axes run in a SEPARATE, COLD session. The session that writes the
code commits and pushes. A fresh one reads the ticket and reviews. A commit with no review in
THIS transcript is therefore often correct. Name the case, then finish:

  - **the hot session of a ticket** -- the review is the next session, and it runs there;
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

NOTE (2026-08-04, revised 2026-08-28) -- addressed to whoever EDITS this file, not to the
session the block above stopped.

This rule lives in more than one place ON PURPOSE. Two reasons, both measured:

  1. hookify globs `.claude/hookify.*.local.md` relative to the PROCESS CWD, and there is no
     single cwd that covers everything. Desktop sessions run in `...\Code`; server sessions
     working on a repo run in that repo. A rule placed under only one of them silently never
     fires under the other.

     The canonical copy is `claude/desktop/` in the private config repo, cloned on this
     machine at `/workspace/projects/.ambiente`. Three copies track it byte for byte, and an
     edit to any one of the four goes to all four in the same change:

       - `...\Code\.claude\` on the Windows desktop;
       - `.claude/` in the config repo itself;
       - `.claude/` in the public skills repo (`Tarcisio-Abbud/claude-skills`), versioned
         there since 2026-08-28 so that repo's worktrees inherit the guard.

     Nothing copies them automatically -- `sync-desktop.ps1` deliberately does not -- so the
     mirroring is by hand, and `diff` is the whole check.

     A fifth text exists and is NOT one of these copies: a shorter translated variant, with no
     NOTE, still runs in the project repos under `/workspace/projects` and in the vault. It
     describes the superseded topology and is converted repo by repo. Do not diff against it
     and conclude the mirrors have drifted.
  2. `config_loader.py` and the transcript reader both call `open(path, 'r')` with no
     `encoding=`. On Windows that resolves to cp1252. A rule file carrying one emoji is then
     skipped silently. A transcript carrying one emoji reads as "" -- 7 of 8 real ones tested.
     Every `field: transcript` condition then evaluated against an empty string, so the rule
     never fired. `env.PYTHONUTF8=1` in `~/.claude/settings.json` mitigates this globally.
     Keep this file ASCII anyway: it costs nothing and survives that setting being lost.
