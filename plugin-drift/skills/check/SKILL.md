---
name: plugin-drift-check
description: "Report which installed Claude Code plugins have drifted from their marketplace catalog, across every marketplace known to this machine. Use when the user asks whether a plugin or marketplace is up to date, out of date, needs updating, or has drifted -- and when a plugin update is applied, to pull the changelog highlights of what's changing."
---

Drift is the gap between what's **installed** (`installed_plugins.json`) and what the
**catalog** says is current (each marketplace's `marketplace.json`) — and it hides behind
matching semver, so `mattpocock-skills` can read `1.2.0` on both sides while the pinned commit
has moved. Never trust the version string; the script always compares the commit.

## Steps

1. Run `${CLAUDE_PLUGIN_ROOT}/bin/plugin-drift-check` (no args needed — it pulls every known
   marketplace catalog first, then diffs) with whatever Python 3 is on PATH — try `python3`,
   then `python`; on a Windows machine with neither aliased, fall back to a full interpreter
   path (`where python`/`py -3` finds it). Read every row: `up to date`, `DRIFT`, or `unknown`,
   and the marketplace header for `[STALE CATALOG]` — that marks a skipped pull (local edits
   in the clone), so rows under it are judged against whatever was already on disk.
2. For each `DRIFT` row that came from a git-pinned plugin, run it again with
   `--changelog <name@marketplace>` and surface the commit subjects it returns as the update's
   highlights — a few lines, not the full log. If it reports the installed commit wasn't found
   upstream, say so plainly instead of inventing what changed.
3. State the verdict plainly: which plugins drifted, and for each, the highlights from step 2
   if any. This script is read-only by construction — it never installs anything. Applying a
   drifted plugin still needs `claude plugin disable <name>` then `claude plugin install <name>`
   where the `claude` CLI exists, or the `/plugin` dialog where it doesn't — and neither is a
   safe default assumption: check whether this session actually has an interactive dialog
   surface to run one in before pointing the user at it, rather than assuming one is always
   one keystroke away.

## Reading the two kinds of drift

- **Git-pinned** (catalog `source` is an object with a `sha`): the installed commit is compared
  straight against the catalog's pinned commit in the plugin's own upstream repo.
- **Packaged in the marketplace repo** (catalog `source` is a path string, no `sha`): the
  installed `gitCommitSha` here is the *marketplace* repo's commit at install time, not this
  plugin's own — comparing it proves nothing, so the script instead hashes every catalog file
  against the installed copy, one direction only (extra files only in the installed copy are
  runtime noise, never a mismatch).
