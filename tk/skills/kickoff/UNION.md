# The sweep over the union

Read from step 5 of `AFK.md` beside this file, by the ORCHESTRATOR: once per package, after the
last item is verified and BEFORE step 6 measures. `REVIEW-CONTRACT.md` beside this file reaches
half 1 again, as the collision check that closes the package.

Both halves are FIXED: a finding is what they RETURN, never what summons them. Gated on a
finding instead, the sweep sleeps through the package that needs it most — every branch green
alone, main red once they land, which is how one weekend left a repository's main red twice.

## 1. Grade the union, per repository

`../../bin/tk-collisions` answers this in TWO passes over the package's OPEN pull requests. The
first pass merges every PAIR for real, and `../merge-gate/SKILL.md` §5 owns that form. The
second pass grades the merged state with the repository's whole SUITE:

```sh
../../bin/tk-collisions --repo "<clone>" --base origin/main \
  --against "<branch assumed to land first>" \
  --suite "<that repository's whole suite>" "<other branch>" ...
```

`--against` names the pivot, the branch assumed to land first. The script builds
`merge(merge(--base, pivot), ref)` once per other branch — N-1 unions, not N² pairs — and grades
each in a temporary worktree it removes itself. That is the question a pair-wise merge leaves
open: a union merges textually clean and still comes back RED, because a test one branch adds
grades a file another branch edits.

One repository per run, since a suite belongs to one repository and a union crosses no
repository boundary. Exit 1 is the FINDING — a colliding pair in the first pass, a red union in
the second; exit 2 is a run that could not be made. A pivot with no other branch beside it has
no union to measure and exits 0, and there the tail's own suite is what stands.
`tk-collisions --help` carries the rest of the form.

## 2. Read the package's diffs together

`git diff origin/main...<branch>` per branch, for what no single branch holds: one rule two
lanes wrote twice, a pointer one lane retired while another still aims at it, a helper each
lane added under its own name. Half 1 catches what turns the merged tree red; this half catches
what stays green and wrong.

## Where a finding goes

`FINDINGS.md` beside this file owns the routing. Its third destination — a sweep lane over the
union — is dispatched HERE, under `LANE-CONTRACT.md`, cut over the merged state of what the
package opened. `AFK.md`'s *The fixer cap* counts that lane's correction cycles like any other
lane's, and what the cap leaves unclosed takes destination 2, a line under "Achados não
tratados".

A RED UNION reaches this routing from `REVIEW-CONTRACT.md`'s collision check too. Report the
failing suite's tail and the pivot the run assumed, since another merge order is another
measurement.

**Done when:** every repository holding more than one open pull request was graded, the
package's diffs were read together, and every finding names the destination that took it.
