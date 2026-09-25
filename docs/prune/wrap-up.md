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

## 7. Second pass over `MERGE-GATE.md` (T320) — what came out

Not part of prune 8/8: a later pass, run when the file had drifted to 2445 body words and
sat 2 words under the lock's ceiling (2225 + 10% = 2447). 2445 → 2271 words, 220 → 209
lines, no rule dropped and the lock untouched. `G:` cites
`git show 54da98e:tk/skills/wrap-up/MERGE-GATE.md` line numbers.

**DROP — exposition (verbatim)**

- G:31–32 "An invented section reads exactly like a sourced one, which is why the absence
  is written down." — the rule it explains ("they are named absent") stays at G:29–30.
- G:89–91 "**Owner-qualified, the keyword crosses repositories** — a merge here closes a
  private tracker's ticket, by merge commit and by squash alike. The owner half is what
  makes it fire, so condition 3 is the mechanism and not a formality." — the paragraph
  restated the verdict-5 row; its one fact the row did not carry ("by merge commit and by
  squash alike") moved into condition 3, which is where the owner half is checked.

**CLAUSE — clauses cut from sentences that stay**

| where | clause cut |
|---|---|
| G:52–55 | "that would read a verdict out of a checkbox" — the rule ("never a bare 'merge'") stays |
| G:61–62 | "The closing keyword is what makes the merge close the ticket, and it" → "The closing keyword" — the verdict-5 row already says what the keyword does |
| G:73–74 | "and the merge then closes a ticket nobody worked on" — the WRONG-ticket condition stays; condition 3 states the same harm |
| G:85–87 | "and the merge looks exactly like a successful one" and "retargeting a child onto the new base is a step this gate already performs" → "a step this gate itself performs" |
| G:102–104 | "in the same breath", "on a ticket nobody is looking at any more" — the two costs stay named |
| G:108–110 | "tells the reviewer something the branch no longer does" → "tells the reviewer what the branch no longer does", with the rule pulled to the front of the sentence |
| G:112–113 | "(this is how 'commit/push only when the user asks' is satisfied)" — "the check IS the authorization" stays |
| G:147–148 | "are what let the user tell a measurement ... from a measurement of something older" → "separate a measurement ... from an older one" |
| G:153–155 | "— the per-item way back exists only while each item is a merge commit of its own" — verdict 4's row states it; "until somebody deletes it" |
| G:164–166 | "rather than to merge on a green line that has aged" — the remedy stays |
| G:191 | "and nothing unpushed" — the same sentence commits AND pushes before the review |
| G:209 | "exactly as a type-B item defers it" — the type-B case is the bullet above it |

**Note — no verdict:** G:213–220, the 101-word "Done when", was split into four sentences
with its clauses intact. G:18–20, G:47–49, G:152–158 and G:190–194 were reworded around
the cuts above.

---

# Pass 2 — 2026-09-16 (T410)

The second pass over the same skill, keyed to the pre-pass tree at commit `89ed5d0`:
`W2:` cites `git show 89ed5d0:tk/skills/wrap-up/SKILL.md` line numbers, `R2:` cites
`git show 89ed5d0:tk/skills/wrap-up/REPORT.md`. Every verdict of this pass is a cut — it
created no destination, so nothing below lives anywhere else. The report beside this file
(`wrap-up-report.md`, *Pass 2*) carries the reasons; what follows is the text, verbatim,
so one edit puts any of it back.

## 7. DROP — whole sentences (verbatim)

- W2:31–33 — "The inventory drives the rest: no code change → step 4 skips the suite;
  nothing behaviour- or knowledge-changing → step 3 shrinks to nothing; the
  version-control actions feed step 5."
- W2:133 — "It is written for a cold reader, and the structure is what travels."
- R2:12–13 — "An unattended run walks its items one at a time, each from zero knowledge
  of the session."
- R2:50–53 — "At an attended gate the user has already read those lines in the terminal,
  before the menu, so this block repeats them where the report keeps them; an unattended
  run's reader meets them here first."

## 8. CLAUSE — clauses cut from sentences that stay

| where | clause cut |
|---|---|
| W2:13–15 | "admit an item to the queue" and "admits work to version control" → "step 2's survival gates and step 5's versioning gate" |
| W2:28–29 | "every other signal reads this disk only, and" — "The fetch comes first" and its sibling-session reason stay |
| W2:37–38 | "each answer can still change memory, docs or the queue below, and" — the batched menu and its destination stay |
| W2:92–93 | "— and this is where conversation-only understanding gets a written address, making the `/clear` cheap" — "Site extensions add further targets." stays |
| W2:101–102 | "— a green test doesn't prove the real flow works" — the instruction to run the end-to-end skill stays |
| W2:112–113 | "— this gate is what makes the wrap-up a real close" — "Settle every version-control decision NOW." stays |
| W2:146 | ", leaving genuine nuance to `/compact`" — the two other branches of the sentence stay |
| W2:175–177 | "— the flag for a decision nobody could ask, against one nobody bothered to ask" — `--deferred afk` stays prescribed |
| W2:188–189 | "Whatever was not merged sits in the queue as a DECISION, and no other external effect happened." → "No other external effect happened." |

**Note — no verdict:** three paragraphs (step 1's findings, step 4, step 5's opening) were
re-wrapped at 90 columns after the cuts above; no word of them changed.
