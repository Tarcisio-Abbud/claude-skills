# What the `kickoff` pruning pass removed

Every verdict of the pass, its reason and the numbers are in `kickoff-report.md` beside this
file. This file is the reversal path: the material the pass took out of
`tk/skills/kickoff/SKILL.md` and `tk/skills/kickoff/AFK.md`, either verbatim or by the exact
range of the pre-prune originals, which are the two files at commit `7fb9ad0`
(`git show 7fb9ad0:tk/skills/kickoff/SKILL.md`, `git show 7fb9ad0:tk/skills/kickoff/AFK.md`).
A sentence quoted here goes back in one paste; a range goes back in one `git show`. Line
numbers below are the originals' at that commit.

`prune/REPORT.md` defines this file as the home of an own skill's removed **inline
evidence**; this pass also uses it the way `dispatch.md` and `verify.md` do, for every other
class of removed prose.

## 1. MOVE — living at a destination, not here

- SKILL.md 224–485, the queue contract, split three ways: the gotchas to
  `tk/reference/queue.md`, the help-covered contract to the CLI's own `--help`s (DROP,
  environment copy — §4), and three help gaps to ticket #223 on the tracker.
- SKILL.md 193–222 and AFK.md 1239–1257, the session-finding ladder, fused into
  `tk/reference/session-finding.md` — the hydra is coined there and nowhere else now.
- README.md 30–74, the ~40-line repetition of the same contract, now a pointer paragraph.

## 2. DROP — inline evidence (verbatim)

The AFK.md originals carried 30 `measured` narrations and 6 dated ones; the rule each one
backed stays, the narration lives here. The load-bearing ones:

> Measured: `git worktree add "<path>/spec-<m>" "origin/spec/<m>-<slug>"` without it leaves
> a **detached** HEAD, and a commit made there reaches nobody. (AFK 118–123)

> measured, after that deletion `git fetch origin` exits 0 and `git rev-parse
> "origin/spec/<m>-<slug>"` still answers the stale sha, while `git fetch --prune origin`
> reports `- [deleted]` and the same `rev-parse` then exits 128. (AFK 133–136)

> Measured in this ticket's rehearsal: `done T001` printed `handoff-T001.md removed`, and
> the re-dispatch would have read nothing. (AFK 82–84)

> measured, `claim T001 --as afk-host` run twice answered `T001 is already claimed by
> afk-host` at exit 1. (AFK 89–90)

> measured, `tk-queue done` on an item claimed by another owner closed it at exit 0 with no
> warning. (AFK 173–174)

> Dispatched on that stale name, the item is implemented and merged a second time —
> reproduced, the lane ended carrying two `T002:` merge commits of one name. Rehearsed
> through the order above, the re-dispatch declined the stale id and the lane kept one merge
> per `T<id>`. (AFK 208–210; the queue's refusal line was `T002 already left the queue`, exit 1)

> measured in this ticket's rehearsal, it exits 0 on a lane whose `origin/main` never moved
> and that never merged main at all. (AFK 287–288, on `merge-base --is-ancestor`)

> Measured against this repository: over a merged lane's branch it returned
> `[{"headRefName":"…","mergeCommit":{"oid":"3eedd21…"},"number":51,"state":"MERGED"}]`, and
> over a branch that never existed it returned `[]`. (AFK 333–336)

> on 2026-08-19 one such sibling ran `git pull --ff-only` and landed the fast-forward on the
> branch another session had checked out. (AFK 548–549)

> run from there, `origin` was measured returning exit 0 and no output — a clean false
> negative that reads exactly like "no branch". (AFK 405–408)

> Asking the question here instead was measured costing more than it bought — it needs a
> clone whose trunk is current, a ref name step 1 does not yet know, and an exit code of its
> own, and each of the three was a way to answer "free" over live work. (AFK 422–425)

> The shapes behind them were measured against one 5-hour quota window (2026-08-18) — a
> survey ≈5% of the window, one implement + review + fix lane ≈15–20%, a full-method second
> pair of eyes ≈8%. … budgeting a lane by its diff was measured underestimating by ~3×
> (2026-08-19). (AFK 479–485)

> a prompt that says "read #X, #Y and #Z" bills that price on every run, and was measured
> starting an implementer at ~150k of context — the edge of the smart zone — before its
> first line of code (2026-08-19). (AFK 675–677)

> The lenses are fixed by measurement: on 2026-08-14 the grave findings came from lenses
> aimed at breaking a promise, and generic "review this" reading returned none. (AFK 791–793)

> That prompt broke 22% of the finders' findings on that same round. … the four
> low-confidence verdicts were exactly the four the tiebreak decided — two of them real, two
> refuted. (AFK 810–815)

> a shared tree was measured contaminating reviewers of one another (2026-08-14). (AFK 817–818)

> One round is measured (2026-08-19, run over this package's own spec and tickets): three
> Sonnet finders, ≈280k tokens and 10.5 minutes, returned 11 findings with one of them
> reached by two lenses; the verifier plus one effort-high tiebreak, ≈152k tokens and 10.6
> minutes, confirmed 7 and refuted 2. It found one real REGRILL — a gap that the spec, its
> quiz and a human approval had all let through. Run in series the token cost is the same
> and the wall clock is roughly three times it — derived from the round's shape, not
> measured. (AFK 829–836)

> Overriding `implementer` in the prompt instead was measured failing: the block states that
> where it and the surrounding prose disagree the block wins, and the run opens the
> per-ticket pull request the lane exists to prevent. (AFK 696–698)

> collisions measured 2026-08-18 (SKILL.md 294); 25 of them had, before 2026-08-03
> (SKILL.md 238 — the `[x]` lines that silently accumulated)

## 3. DROP — duplicate (verbatim)

> A **session finding** is work this session discovered and did not come for; what separates
> it from a pendency is the criterion of the item in hand, and the ladder that triages it
> lives in `SKILL.md` beside this file. (AFK 1241–1243 — the definition now lives once, in
> `tk/reference/session-finding.md`)

> Discarding is a judgement ("this will never happen") nobody here can make, so an
> unattended package reports no discards. Resolving on the spot is the hydra's own fuel:
> three heads die and six items are born, which is how a quick job became three weeks.
> (AFK 1248–1251 — kept in the reference file; AFK keeps the one-line form)

> This step names the two shapes and nothing more. The procedure that recovers each of them
> … has ONE home, *A resumed generation starts here* at the top of this file; a second
> statement of it here is a copy to go out of step with that one. (AFK 1063–1067 — the two
> death shapes at stage 7 are now stated once, inside stage 7)

> The remote cannot tell a sibling's branch from this package's own … This check therefore
> runs for a package being BUILT, where a branch on the remote is always somebody else's.
> (AFK 581–586 — exposition of the step 3 rule that survives in one sentence)

## 4. DROP — environment copy (the `--help` covers it)

The whole command palette of SKILL.md 242–275 (the fenced `tk-queue …` block) and the field
paragraphs at 350–457 where they restate flag semantics: `--risk none` deletes (edit
`--help`), `--env none` deletes and the roster/site-file refusal (add/edit `--help`),
`--deferred` demanded by DECISION and dropped by leaving the class (add/edit `--help`),
Criterion `A:`/`B:` (add `--help`), Project slug shape, warn-on-unseen and grouping (add
`--help` + list behaviour), Ticket/Spec feeding the closes line and the lane (add `--help`
+ `pack --help`), the Repo whitelist gist and `[repo: ?]` printing (add `--help` +
`pack --help`), the pack output shape, lane election, floor of two and `--spec-under-way`
(`pack --help`), migrate's fold and dry-run scope (`migrate --help`). Restore any of it
from `git show 7fb9ad0:tk/skills/kickoff/SKILL.md`; three residues the help SHOULD carry
and does not are ticket #223.

## 5. DROP — exposition ranges (by range, restore via `git show`)

SKILL.md: 34–38 (hygiene exit prose around the four exits, kept as one line each); 55–62
(what the weekly report is for, beyond the rule); 100–113 (why Env slicing and
ask-before-BLOCKED work, kept as rules); 133–141 (why briefing is retransmission);
150–158 (why env-bound items leave the menu); 172–190 (report blocks (d)–(f) rationale,
kept as the block list); 277–347 (contract rationale prose now condensed in
`tk/reference/queue.md`).

AFK.md: 25–38 (what reading by section buys — kept as one sentence); 60–94 (the resumed
generation's entry cases, kept compressed); 96–124 (the two preconditions' rationale — the
recreate recipe survives); 141–146 (what the reset discards and why that is right);
155–159, 178–199 (draft/close rationale); 203–219 (why the handoff is belief); 246–262
(green-item and never-pushed shapes, kept as two sentences); 271–345 (the three-deaths
table and the full exit table — compressed to the exits paragraph; the table itself
restores from the sha, and re-expands under ticket #224); 355–376 (re-triage rationale and
the legacy-class fold caveat); 391–435 (the remote-question rationale, kept as rules);
446–526 (second-call mechanics, recount arithmetic, the two cost lines' pricing — kept
compressed); 546–563 (claim-first rationale beyond the rule); 566–620 (step 3 remote
re-ask and branch-creation rationale, kept as rules); 640–719 (vehicle sizing, oversized
item, prompt contents — kept compressed); 726–768 (audit scope and workflow rationale);
770–836 (the two concurrency paths, the finder/verifier prompt fixed lines, the measured
round — kept as the graph summary); 849–889 (outcome exposition and rotten-criterion
routing prose — kept as the outcome list); 902–938 (metavariable, gate and
partial/failed exposition — kept compressed); 940–1006 (verify-cycle stage rationale —
stages kept as the numbered list); 1008–1082 (merge/push/close rationale — kept in the
stages); 1084–1166 (tail rationale — kept as the three-step list); 1168–1237 (measure and
close rationale — kept as the block list).

## 6. CLAUSE — clauses cut from sentences that stay

- SKILL.md 3 (description): "(auto-dispatch, zero menus)", "(same package, one
  confirmation)", "(orchestrator generations the package may spend, default 1)" — the three
  parentheticals the 30-word rewrite loses; the argument meanings stay in the body.
- SKILL.md 20–23: "with its items, its claims and its lane (`WINDOW.md`), so the triage and
  the verification against reality that steps 1–3 would run are paid for already" — kept as
  "has paid for steps 1–3 already".
- SKILL.md 56–57: "It is context, not agenda: it says what moved while the user was away" —
  kept as "context, not agenda".
- AFK 87–94: the enumeration of what the resumed dispatch does not run — kept, each item as
  a parenthesis.
- AFK 1035–1038: "Not at branch creation: the forge refuses a pull request with no commits
  between the branch and its base, so the first merge is the earliest moment it can exist.
  It opens as a draft because the package fills its body item by item and the review runs
  once, at the tail." — kept as the stage-6 heading line.
- AFK 1140–1143: "all of them, not a sample — … under this step's opening rule: the caller
  re-runs the proof, and a run's account of it is never the proof" — kept once in the step
  5 opening.
