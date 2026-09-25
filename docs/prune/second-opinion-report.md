`docs/prune/second-opinion-report.md`

# Pruning report — the `second-opinion` skill

The seventh run of `/tk:prune`, executed as prune 9/9 — the closing slice of the pruning
track's spec — over the plugin's newest skill. The removed material is beside this file,
in `second-opinion.md`, keyed to the pre-prune original at commit `990a6d5` (`S:` + line
number). Like the 7/8 and 8/8 passes this one ran inside an unattended package, so the
pass edited the skill in its branch directly and the lane's tail review reads the branch.
**First pass over this skill**: no earlier committed report exists, so no rule needed the
step-3 date check against one. The skill is also absent from `baseline-2026-08-27.md` —
it was born (commit `4932630`, 2026-08-27, tk 2.3.0) after that baseline ran — so this
pass's baseline is the birth state, which the lane tip `990a6d5` carries unchanged:
`git log` shows no commit on the file since birth.

## 1. Numbers

`tk-prune-measure <file> --targets`, before and after. **Bold** marks a value over a
ceiling — the bin's, or the ticket's line ceiling (50), which the bin does not carry.

| metric | SKILL.md before | after |
|---|---|---|
| lines (ticket: ≤50) | **51** | 49 |
| body words | 432 | 423 |
| sentences | 28 | 28 |
| mean words per sentence (22) | 15.4 | 15.1 |
| max words in a sentence (25) | **42** | **42** |
| sentences over 30 words (4) | 4 | 3 |
| description words (30) | 24 | 24 |
| inline evidence (0) | 0 | 0 |
| pointers to other files | 0 | 0 |
| negations | 4 | 4 |
| defined terms | 2 | 2 |
| terms defined in a sibling too (0) | 0 | 0 |

The one remaining over-ceiling value is the 42-word sentence carrying the ask and the
reply shape (S:25–28): a KEEP, and `max words in a sentence` founds no verdict ever —
splitting it would add lines, the one metric the ticket caps. The skill's birth review
had already run this ruler's vocabulary pass (`round`→`turns`, `budget`→`turn budget`,
`briefing`→`prompt`), which is why a 432-word file yields three removals and no more:
the pass confirms the birth review rather than redoing it.

## 2. The table

One row per unit; the two verbatim removals are in `second-opinion.md` beside this file.
`where` cites the original at `990a6d5`.

| where | sentence / unit | verdict | why |
|---|---|---|---|
| S:3 | the `description` | KEEP | 24 words, under every ceiling; front-loads the leading term and names both branches (`once`, `consensus`); nothing to rewrite |
| S:5–6 | the frontmatter comment on `argument-hint` mechanics | DROP | environment copy — a cache of the skills doc's frontmatter table, addressed to an editor; no run reads it, and the defaults it defends are stated beside the arguments |
| S:11–12 | "A **second opinion** is a verdict from a mind that did not do the work…" | KEEP | coins the skill's leading term; drives every step-1 choice about what the prompt must carry |
| S:12–14 | "That is the value, and it is why the opinion comes from a **fresh** subagent on `fable`…" | KEEP | names the dispatch shape a default run would not take (fresh, not fork; `fable`, not parent) |
| S:14 | ", and it ignores the model override anyway" | CLAUSE | environment copy — the `Agent` tool's always-loaded description states it; the context-inheritance reason alone decides against a fork |
| S:16–17 | "`$mode` is `once` (empty defaults to it) or `consensus`; any other value, stop and show the hint." | KEEP | argument criterion and the refusal path |
| S:17–18 | "`$turns` is the **turn budget** for `consensus`…" | KEEP | coins the budget, sets its unit (subagent replies, first opinion included) and the default |
| S:22–24 | step 1, the prompt's contents and order | KEEP | the cold-reader recipe; "the session's position … last" is ordering a default prompt would not keep |
| S:24–25 | "A claim without a path or a quote is one the subagent will rightly discount." | KEEP | extends the path-or-quote bar to every claim in the prompt, the session's own position included |
| S:25–28 | "Then the ask … then what the session should change." | KEEP | the verdict-before-position instruction and the reply shape; the 42-word survivor, and KEEP outranks every ceiling |
| S:28–29 | "Done when someone with no session context could answer the question from the prompt alone." | KEEP | step 1's completion criterion |
| S:31–32 | step 2, the dispatch line (`general-purpose`, `model: "fable"`, `effort: "high"` and its reason) | KEEP | the dispatch parameters and the rule that a verdict's depth is independent of the session's effort; see the effort note in §3 |
| S:33–34 | "In `consensus` mode, record the agent name the result returns…" | KEEP | without the recorded name, step 3 cannot continue the same agent |
| S:34 | "Done when the reply is in hand — turn 1." | KEEP | step 2's completion criterion, and it anchors the turn count |
| S:36 | "**Argue** (`consensus` only)." | KEEP | the branch gate on step 3 |
| S:36–37 | "Before each send, compare replies received with `$turns`; equal means the budget is spent, stop." | KEEP | the budget check, placed before the send |
| S:37–39 | "Otherwise reply through `SendMessage` with one move per disputed point — **concede** … or **hold** …" | KEEP | the two moves and the symmetric ask back |
| S:39–40 | "A point neither side can move with new evidence is **deadlocked**: leave it and go on." | KEEP | the exit that stops a loop on an immovable point |
| S:40–41 | "**Consensus** is an empty list of disputed points." | KEEP | the skill's second defined term; makes consensus checkable |
| S:41 | "at consensus, " | CLAUSE | duplication inside the done line — consensus is the all-agreed case of "every point agreed or deadlocked" |
| S:41 | "Done at every point agreed or deadlocked, or at the spent budget." (as cut) | KEEP | step 3's completion criterion |
| S:43 | "**Report** to the user, outcome first:" | KEEP | output order |
| S:44 | the `once` bullet | KEEP | what that outcome's report must carry |
| S:45 | the consensus-reached bullet | KEEP | ditto, including what the session conceded |
| S:46–47 | the budget-spent/deadlocked bullet | KEEP | ditto, and "the human settles a split" names the handoff |
| S:49–50 | "Close with the policy's deviation line, in the report itself: `second-opinion: none→fable, effort high — fired by the user via /tk:second-opinion`." | KEEP | the literal line the subagent policy requires; quoting it spares the run a lookup |
| S:51 | "Done when the user has the outcome and the line." | KEEP | step 4's completion criterion |

No unit earns MOVE, so no inbound pointer needed a rewrite. Grepped anyway: the plugin
reaches this skill at `tk/reference/subagent-policy.md:165–168` (the user-fired
exception — consensus loops, the turn budget as the lock, the skill writing the
deviation line) and in the `plugin.json` / `marketplace.json` descriptions; every
behaviour those pointers name survives this pass unchanged.

## 3. Splits, fusions and notes

**No split suggestion**: 49 lines, one file, every branch inline — nothing meets a
`SKILL-MECHANICS` splitting criterion.

**No fusion owed.** The vocabulary was checked twice over:

- The birth review's replacements held: `round` and `briefing` have zero hits in the
  file; the bare `budget` at S:37, S:41 and S:46 is within-file shorthand for the
  coined **turn budget** (S:17), and the plugin's only other budget sense is kickoff's
  `--budget N` generations flag, always written with its sigil — no collision.
- Against the 8/8 fusions: `digest`, `handoff` and `gate` do not occur in the file —
  nothing to fuse and nothing contradicted. `turn budget` stays coined here and used by
  `subagent-policy.md:167`, one definition for the plugin.

**The plugin-wide term sweep** (this ticket's one-off; the bin's sibling check only
reads same-directory neighbours — extending it is ticket #219): a throwaway script
`exec`s `tk/bin/tk-prune-measure` as a module and runs its own detector
(`strip_frontmatter` → `scan` → `defined_terms`) over every markdown under
`tk/skills/*/` and `tk/reference/` — 22 files, the full set `find` returns — grouping
definitions case-insensitively across files. Result, on the post-prune tree: **32
definitions, 31 distinct terms, and no term defined in two or more files.** The one
double is within a single file — `fleet/SKILL.md:206` and `:242` both open a rule
sentence with **textual report** — a detector hit on a bold-opened restatement, not a
competing coinage, and outside both the two-file criterion and this pass's target; noted,
not acted on. The script is not committed: the plugin-wide check belongs to the bin via
#219, and this branch touches no bin.

**Note — the dispatch's `effort` parameter (no verdict)**: an open item elsewhere
already tracks whether the `Agent` dispatch mechanism honours an `effort` field. S:31–32
stays as written; if the mechanism drops the field, the fix belongs to that item, not to
this pass.

**Rewording notes**: none — every change is a verdict row above.

## 4. Paths

- Pruned in place, this branch: `tk/skills/second-opinion/SKILL.md` (51 → 49 lines).
- Removed material: `docs/prune/second-opinion.md`. Both docs files allowlisted file by
  file in `.gitignore` like their siblings. The branch touches no bin.

## 5. Proof of the target skill

The target is prose, so the proof is the reviewed diff of rules — this pass runs inside
an accumulated lane, where the two-axis review fires ONCE over the lane's whole diff at
the package's tail (smell baseline declared inapplicable, the `writing-for-agents` path
and this table handed to the axes). No `tk/tests` file anchors on second-opinion prose,
so the executable arm is the whole suite unchanged: 771 tests plus 411 subtests green on
the pruned tree. The mutation harnesses (`tk/tests/mutations*.py`) remain the suite's
broken-arm proof.
