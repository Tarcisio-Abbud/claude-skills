---
name: plugin-drift-check
description: "Drift report for installed Claude Code plugins: which ones no longer match their marketplace catalog. Use when the user asks whether a plugin is current, and when applying a plugin update, to pull the changelog highlights of what's changing."
---

Drift is the gap between what's **installed** (`installed_plugins.json`) and what the
**catalog** says is current (each marketplace's `marketplace.json`) — and it hides behind
matching semver: both sides can read the same version string while the pinned commit has
moved. Never trust the version string; the script always compares the commit.

## The two kinds of drift

- **Git-pinned** (catalog `source` is an object with a `sha`): the installed commit is compared
  straight against the catalog's pinned commit in the plugin's own upstream repo.
- **Packaged in the marketplace repo** (catalog `source` is a path string, no `sha`): the
  installed `gitCommitSha` here is the *marketplace* repo's commit at install time, not this
  plugin's own — comparing it proves nothing, so the script instead hashes every catalog file
  against the installed copy, one direction only (extra files only in the installed copy are
  runtime noise, never a mismatch).

## Steps

1. Run `${CLAUDE_PLUGIN_ROOT}/bin/plugin-drift-check` (no args needed — it pulls every known
   marketplace catalog first, then diffs) with whatever Python 3 is on PATH. On Windows,
   `python3` resolves to the Microsoft Store alias, which prints an install ad and **exits 0** —
   a run that produced no report while looking like success. Seeing that, use `python` or
   `py -3`. Read every row: `up to date`, `DRIFT`, or `unknown`, and the marketplace header for
   `[STALE CATALOG]` — that marks a skipped pull (local edits in the clone), so rows under it
   are judged against whatever was already on disk.
2. For each `DRIFT` row from a git-pinned plugin, run it again with
   `--changelog <name@marketplace>` and surface the commit subjects it returns as the update's
   highlights — a few lines, not the full log. If it reports the installed commit wasn't found
   upstream, report exactly that: the highlights for that plugin are unavailable.
3. State the verdict: which plugins drifted, and for each, the highlights from step 2 if any.

## Applying is a different job

This script is read-only by construction — it never installs anything. Applying a drifted
plugin needs `claude plugin disable <name>` then `claude plugin install <name>` where the
`claude` CLI exists, or the `/plugin` dialog where it doesn't. Before pointing the user at
either, confirm this session has the surface to run it.
