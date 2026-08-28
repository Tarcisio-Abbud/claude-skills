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

NOTE (2026-08-04): this file exists in more than one place ON PURPOSE, and every copy is
BYTE-IDENTICAL to this one -- edit them in the same change. Two reasons, both measured:

  1. hookify globs `.claude/hookify.*.local.md` relative to the PROCESS CWD, and there is no
     single cwd that covers everything. Desktop sessions run in `...\Code`; server sessions
     working on this repo run in the repo. A rule placed under only one of them silently never
     fires under the other. Canonical copy: `claude/desktop/` in this repo. Mirrors:
     `...\Code\.claude\` on the desktop, and `.claude/` in this repo. Nothing copies them
     automatically -- `sync-desktop.ps1` deliberately does not -- so the mirroring is by hand,
     and `diff` is the whole check.
  2. `config_loader.py` and the transcript reader both call `open(path, 'r')` with no
     `encoding=`. On Windows that is cp1252: a rule file with one emoji is skipped silently,
     and a transcript with one emoji (7 of 8 real ones tested) reads as "" -- which made every
     `field: transcript` condition evaluate against an empty string, i.e. never fire.
     Mitigated globally by `env.PYTHONUTF8=1` in `~/.claude/settings.json`. Keep this file
     ASCII anyway: it costs nothing and survives that setting being lost.

**Commit made without a code-review in this session.**

Every code change delivered goes through `/mattpocock-skills:code-review` (2 axes: Spec +
Standards) before being called done -- including a small commit straight to main: run the
review retroactively over the commit and fix the findings in an immediate follow-up commit.

Use the full name. `/code-review` alone is Claude Code's native review, a different skill,
and does not satisfy this rule.

If no code was actually committed in this session (false positive -- e.g. only conversation
mentioning a commit, or a docs/wiki-only commit), say so explicitly and finish.

**Known weakness, so you judge the block instead of obeying it blindly:** the conditions are
substring matches over the whole transcript. `git commit` matches even when it was only
discussed, and `code-review` counts as satisfied the moment the phrase appears anywhere --
including in this very message. So it releases itself on the second stop attempt (which is
also what keeps it from looping). Treat it as a reminder, not as proof either way.
