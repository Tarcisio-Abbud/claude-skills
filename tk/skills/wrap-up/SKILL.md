---
name: wrap-up
description: "Session close before /compact or /clear: updates memory and docs, runs the tests, settles every commit/push/merge decision in one gate and recommends the next step. Arg: afk (no menus, local-commit ceiling)"
disable-model-invocation: true
---

A **wrap-up** leaves the external state (memory + docs + tests + version control)
reflecting what this session did, so /compact loses nothing and the next session starts
aligned — a close that leaves silent pendings is not a close. Execute the steps in order;
each ends on a checkable criterion. The step-1 inventory decides how much of steps 3–4
runs; every skip is stated, never silent.

**Argument:** `afk` — the user is leaving now; see "The `afk` argument" at the end.

**Site extensions:** read `~/.claude/tk/wrap-up.md` and `.claude/tk/wrap-up.md` (project
root) if they exist — they add site-specific documentation targets and flow
recommendations. (A project's own `.claude/skills/wrap-up` overrides this skill entirely.)

## 1. Inventory the session's changes

Fire the sweep as ONE parallel batch — `git fetch`, `git status`, `git diff --stat`,
`git log --branches --not <default> --oneline` (commits still outside the default branch)
and, if `gh`/forge CLI exists, the open PRs — and print the inventory before going deeper.
The fetch comes first because every other signal here reads this disk only: a session
working from another clone leaves no local trace at all, and without it the divergence
surfaces as a rejected push at the end of the gate instead of a known fact at the start.
Add the **facts/decisions/learnings** from the conversation (not just code — user choices,
discoveries, external pending items). The inventory drives the rest: no code change →
step 4 skips the suite; nothing behaviour- or knowledge-changing → step 3 shrinks to
nothing; the version-control actions found here feed the step-5 gate.
**Done when:** the user saw a concrete list of touched files/commits, of the branches/PRs
in play, and of the new decisions/facts — with nothing material omitted — and each later
step is marked run/skip.

## 2. Update memory

For each durable and **non-obvious** fact from step 1, create/update ONE file in the
project's auto-memory (dir `memory/`, index `MEMORY.md`), with the right frontmatter and
type (`user`/`feedback`/`project`/`reference`). Prefer updating an existing file over
duplicating; delete what proved wrong. Convert relative dates to absolute. Link with
`[[slug]]`.
**Pending items go through `tk-queue`** (`../../bin/tk-queue` relative to this file) — the
only writer of `next-steps.md` and `done-log.md`. Every change to either file arrives as one
of its subcommands, run from this session: new items enter via `add` (with **Class**,
**Effort** and **Criterion**, plus **Risk** and **Project** where they apply — the criterion
is required, so decide it here rather than leaving "done" as the next closer's self-report);
a field of an open item changes via `edit`; resolved ones leave via `done --how "<pointer>"`
and discarded ones via `cancel --why`, which move them to `done-log.md`. This holds for the
one-word fix as much as for the new item: rewriting either file through Edit/Write/shell
breaks what the script guarantees — the ID sequence, the item actually LEAVING the queue,
and the log line that survives it. Contract, commands and the pointer rule:
`../kickoff/SKILL.md`.
That queue is what `/tk:kickoff` dispatches at the next session's open.
**Encode into the system:** a correction the user repeated or a check they did by hand is a
system signal, not an instance signal — propose encoding it (project skill, hook rule,
test) so it holds in every future iteration.
**Done when:** every durable fact of the session has a memory file (with a pointer in
`MEMORY.md`), `next-steps.md` reflects the post-session pending items with their fields —
or the fact was consciously discarded as already in the repo/ephemeral — and every
recurring correction has an encoding proposed or discarded.

## 3. Update the repo documentation

Runs when the inventory shows changed behaviour or new knowledge. Make the documentation
reflect the current implementation: `README`, the project's instruction file
(`CLAUDE.md`/`AGENTS.md`/`GEMINI.md`, whichever exists), glossary (`CONTEXT.md`), `docs/`
and ADRs. New commands, test counts, design sections, decisions — no command/count/path may
stay stale. Site extensions add further targets (wikis, status artifacts).
**Done when:** every behaviour changed in the session is reflected in every documentation
target — or nothing doc-relevant changed and that was said.

## 4. Verify

Runs when code changed. Run the project's test suite. **Detect the runner** from the
manifest/files: `pytest`/`python3 -m pytest`, `npm test`/`pnpm test`/`yarn test`,
`cargo test`, `go test ./...`, `make test`, etc. Changed runtime behaviour and the project
has an end-to-end verification skill (e.g. `verify`)? Run it too — a green test doesn't
prove the real flow works.
**Done when:** the tests pass — or the failures are reported to the user with the output —
or the skip was stated ("no code changed" / "project has no suite").

## 5. The versioning gate

Settle every version-control decision NOW — this gate is what makes the wrap-up a real
close. From the inventory, list the pending actions per repo: uncommitted work, unpushed
branches, PRs to open, PRs awaiting merge.

**Digest before merge:** any PR offered as "merge" gets its review digest first — the
automated review status (run the project's review flow if it hasn't run), a per-file
summary of the change, the open findings, and the forge link. Show a small diff (guidance:
≲150 lines) whole in the terminal; a large one gets digest + link.

Then ONE multiSelect `AskUserQuestion` with the actions, recommended first — the check IS
the authorization (this is how "commit/push only when the user asks" is satisfied). Execute
what was checked, following the project's conventions (required trailer lines; on the
default branch, branch first). Every unchecked action enters the queue as a DECISION item
via `tk-queue add --class DECISION` — a merge carries its digest reference (forge link +
review status), any other action carries the branch/paths involved — deferred by choice,
not by omission.
**Done when:** every pending version-control action was executed or recorded as an explicit
DECISION — none merely implied — and the user has the summary: what changed, what was
verified, what was deferred.

## 6. Recommend the next step: /tk:docs-audit, /clear or /compact

ALWAYS close by explicitly recommending ONE path, with the why in 1–2 sentences. Criteria:

- **`/clear`** — the default when the wrap-up ended clean: state 100% externalized (memory +
  docs + green tests + gate settled), nothing mid-flight, and the next task is discrete
  (starts from zero with just `MEMORY.md` + repo). Compacting here would pay to summarize
  what's already saved. When recommending, **give 1–3 ready sentences to open the next
  conversation** — two shapes, chosen by what the sentence does:
  - **Invokes a slash command** (`/tk:kickoff afk`, `/implement`, …) — the command leads the
    sentence alone, no prose before it, and does NOT name the project: `tk-queue` and similar
    resolve state from the session's `cwd`, so the project is carried by telling the user
    where to open the session, e.g. "open the session in `/workspace/projects/foo` and type
    `/tk:kickoff afk` as the first line" — never by naming it inside the command line.
  - **Describes a task, no slash command** — name the project by path or name in the prose,
    e.g. "in `/workspace/projects/foo`, take T012", not "take T012". The next session may
    open anywhere (on the desktop it does not start in the project's folder), so a cold
    sentence that names no project points at nothing.
  Site extensions may add flow-specific opening lines.
- **`/compact`** — when there is a live thread that is NOT a durable memory fact: an
  incomplete task mid-flight, debugging with open hypotheses, a half-made
  negotiation/decision, or conversation nuances the next stage still needs that don't make
  sense as a memory file. Compact preserves the thread; clear would lose it.
- **`/tk:docs-audit` (before the clear)** — when there's *drift* beyond the session's
  scope: step 3 hit stale statements this session did NOT cause, or a lot of code piled up
  since the last audit (several sessions/loops without a `docs-audit`). Audit first, then
  `/clear`.
- **None (continue)** — only when the user will immediately chain a related task and the
  current context is still short enough to beat a clean restart.

**Leaving rather than continuing?** Close with the ready pair: `/clear` now, then open the
next session in the project's directory and type `/tk:kickoff afk` as its first line — the
slash-command shape above, project carried by the `cwd`, not named in the sentence.

Also cite any pending item crossing the session boundary (e.g. open PR awaiting merge) — it
enters the suggested opening sentence.
**Done when:** the user received ONE clear recommendation (not a neutral menu), the
justification, and — when the path is `/clear` — the next conversation's opening sentences,
each in the shape that fits: a slash-command line leads with the command alone and carries
the project via the session's `cwd`; a descriptive line names the project in prose.

## The `afk` argument

`/tk:wrap-up afk` — the user typed it and left; run every step without a single menu.

- Steps 1–4 and 6 run unchanged.
- The gate (step 5) runs autonomously under a hard ceiling: **commit local work to a
  branch — never the default branch, never push, never merge.** Invoking `afk` IS the
  commit request, and a local branch commit stays reversible. Code changed → run the
  project's review flow and fix its findings BEFORE committing. **Concurrent-session
  guard** first (defined in `../kickoff/AFK.md`): `git worktree list` + the `+` marks in
  `git branch -v`; another live session in the repo → leave the tree untouched and report
  it. Push/merge/PR decisions enter the queue as DECISION via `tk-queue add` — merges with
  their digest reference ready.
- The step-6 report ends with the ready pair for the user's return: `/clear` +
  `/tk:kickoff afk`.

**Done when:** the session state is externalized, local work is committed on a branch (or
the guard/skip reported), and zero external effects (push/merge/PR) happened.
