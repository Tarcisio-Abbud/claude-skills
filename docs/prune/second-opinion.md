# What the `second-opinion` pruning pass removed

Companion of `second-opinion-report.md` beside this file (prune 9/9, ticket #194, spec
#184). Keyed to the pre-prune original at commit `990a6d5` — `S:` cites
`git show 990a6d5:tk/skills/second-opinion/SKILL.md` line numbers. The pass moves
nothing; everything below is a removal, verbatim, so one edit puts it back.

## 1. DROP — environment copy

- S:5–6, the frontmatter comment:

  ```
  # The hint shows only while the name is being completed; there is no per-position hint and no
  # default-value field (code.claude.com/docs/en/skills.md, frontmatter table). Defaults live below.
  ```

  A copy of the skills doc's frontmatter table, addressed to an editor — no run reads
  it. The defaults it defends are stated beside the arguments (S:16–18).

## 2. CLAUSE — cut from sentences that stay

- S:14 ", and it ignores the model override anyway" — from the fresh-`fable` sentence.
  Environment copy: the `Agent` tool's always-loaded description says a fork ignores the
  model override, and the context-inheritance reason alone decides against a fork.
- S:41 "at consensus, " — from step 3's done line. Consensus is an empty list of
  disputed points (S:40–41), i.e. the all-agreed case of "every point agreed or
  deadlocked" two words later: one done condition stated twice in one sentence.
