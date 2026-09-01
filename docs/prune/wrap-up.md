# What the `wrap-up` pruning pass removed

Companion of `wrap-up-report.md` beside this file (prune 8/8, ticket #192, spec #184).
Keyed to the pre-prune original at commit `4127fa9` — `W:` cites
`git show 4127fa9:tk/skills/wrap-up/SKILL.md` line numbers. Most of the pass is MOVE, not
DROP: step 5 lives on in `tk/skills/wrap-up/MERGE-GATE.md`, the closing template in
`tk/skills/wrap-up/REPORT.md`, the queue contract in `tk/reference/queue.md` (since the
7/8 slice) and the session-finding ladder in `tk/reference/session-finding.md`. What is
below is only what no destination carries.

## 1. MOVE — living at a destination, not here

| range | destination |
|---|---|
| W:141–307 (step 5: dossier sections, digest, five verdicts, verdict-5 checks, menu, stack order, accumulated lane) | `MERGE-GATE.md`, compressed; originals via `git show` |
| W:311–378 (cold reader, template fence, What-changed and stats-line rules) | `REPORT.md` |
| W:423–434 (the two opening-sentence shapes) | `REPORT.md`, *The opening sentences* |
| W:447–449 (the ready pair on leaving) | `REPORT.md`, last paragraph |
| W:39–45 (the session-finding definition and menu rule) | definition: `tk/reference/session-finding.md`; the menu rule stays in step 1 |
| W:59–74 (the tk-queue contract restatement) | `tk/reference/queue.md` — already there; only the criterion-here and ask-the-DECISION rules stay in step 2 |
| W:466–490 (afk: commit-push-before-review detail, digest-in-PR-body, strict verdicts, the three binding cases) | `MERGE-GATE.md`, *The strict form* |

## 2. DROP — inline evidence (verbatim)

- W:246–247 "— deleting it first CLOSES the child **(measured twice)** —" — the clause in
  bold; the rule stays in `MERGE-GATE.md` without the count.
- The seven `measured` marks the bin flagged in the original (W:245, 253, 255, 266, 279,
  303, 398) left with their ranges: rephrased at the destination ("Scope" column, "ran on
  a tree", "run for real") or gone with the moved prose.

## 3. DROP — duplicate (verbatim)

- W:169–170 "**Dossier** is the term here; `briefing` names the step-6 handoff file." —
  dies with the vocabulary fusion: `digest` is the one merge-gate artefact, the handoff
  file the one continuity artefact (report §3).
- W:10 "The step-1 inventory decides how much of steps 3–4 runs" — step 1 itself says
  "The inventory drives the rest", which is the same rule at its own step.
- W:69–72 "This holds for the one-word fix as much as for the new item: rewriting either
  file through Edit/Write/shell breaks what the script guarantees — the ID sequence, the
  item actually LEAVING the queue, and the log line that survives it." —
  `tk/reference/queue.md` carries the one-writer rule and its whys.
- W:78–79 "— a different object from the versioning gate of step 5 —" — the fusion coins
  **gate** once in the intro, where the two qualified uses are told apart; the aside that
  compensated for two coinages has nothing left to disambiguate.

## 4. DROP — environment copy

- W:54–55 "with the right frontmatter and type (`user`/`feedback`/`project`/`reference`)"
  → "with the right frontmatter and type" dropped whole; the memory system's own docs
  name the types, and the step keeps the create/update/delete behaviour.
- W:62–64 the `--env` fill rules ("only when the item runs on a machine that is NOT this
  one, since an item that names another environment is never dispatchable here") — the
  flag's own refusal and `tk/reference/queue.md` carry it; the gate table's dependency
  row keeps the WHERE-it-runs case.

## 5. DROP — exposition ranges (by range, restore via `git show`)

- W:30–33 the fetch rationale — survives as one sentence ("a sibling session in another
  clone is a fact to know now, not a rejected push at the end of the gate").
- W:95–101 RECURRING exposition — the convert-or-resolve rule, the authorization check
  and both paths survive; the restatements around them do not.
- W:183–190 type-B exposition — survives compressed in `MERGE-GATE.md`.
- W:355–378 What-changed/stats exposition — survives compressed in `REPORT.md`.
- W:409–415 the "no numeric estimate" paragraph on relearning cost — survives as the
  one-line criterion ("where the understanding lives") in step 6.
- W:436–439 /compact exposition — survives as the bullet's two examples.

## 6. CLAUSE — clauses cut from sentences that stay

| where | clause cut |
|---|---|
| W:3 (description) | "kills the session's pendings" → "resolves pendings"; "settles every commit/push/merge decision in one gate" → "settles every commit/push/merge in one gate"; "Arg: afk (no menus, strict merge)" → "(unattended, strict merge)" — 36 → 30 words |
| W:28 | "(commits still outside the default branch)" — the command's own `--not <default>` says it |
| W:33–34 | "(not just code — user choices, discoveries, external pending items)" → "not just code" |
| W:89–90 | "the effort gate is named in the text like any other" — the required `--effort` and the marks-nothing rule stay |
| W:394–395 | "and warns that the item does not yet point at it" — the printed `edit` instruction and its owning rule (`../verify/SKILL.md`) stay |
| W:79–80 | "The contract has no `Gate` field, so" — the record-in-the-item's-text rule stays without the schema rationale |
| W:401–407 | "and a prompt that says 'read the parent and six neighbours' bills that price on every run" and "say the ticket is self-sufficient" — the CONCLUSIONS rule and the subagent-brief rule stay |
| W:459–461 | "— the flag that separates a decision nobody could ask from one nobody bothered to ask" → "the flag for a decision nobody could ask, against one nobody bothered to ask" |
