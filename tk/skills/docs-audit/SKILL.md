---
name: docs-audit
description: "Full documentation audit against the code: finds stale docs, fixes, verifies, audits the project's auto-memory and opens a PR (good under /loop, periodic)"
disable-model-invocation: true
---

An **audit** sweeps the ENTIRE codebase and guarantees every document reflects the current
implementation — heavier than `/tk:wrap-up` (which covers only the session), done from time to
time, and good to run under `/loop`. Each step ends on an **exhaustive** criterion: "every
claim verified", not "a list of changes".

(Generic global version — applies to any project. If a project has its own
`.claude/skills/docs-audit`, that one overrides this.)

## 1. Inventory the docs' claims
Enumerate all documents (`README`, the project's instruction file — `CLAUDE.md`/
`AGENTS.md`/`GEMINI.md` —, glossary `CONTEXT.md`, `docs/`, ADRs) and extract the
**verifiable claims** they make: commands, file paths, counts (e.g. number of tests),
script/function names, described flows, decisions.
**Done when:** there is an inventory of claims, each with its source document.

## 2. Verify each claim against the code
For each claim, confirm in the codebase (run the command, `grep` the path/function, actually
count the tests). Mark it **exact** or **stale**, with the evidence.
**Done when:** EVERY claim in the inventory is marked exact/stale — none unchecked.

## 3. Fix the stale docs
Update each stale claim to match the implementation. Where the doc describes something that
no longer exists, fix or remove it. Don't invent behaviour — document what the code does.
Preserve legitimate history (e.g. proposal/decision sections in a design doc or ADR are not
rewritten to pretend the original plan was the final result).
**Done when:** no claim marked stale remains.

## 4. Verify
Run the project's test suite (**detect the runner**: `pytest`, `npm test`, `cargo test`,
`go test ./...`, `make test`, etc.) and re-check the claims you fixed (e.g. the documented
command runs; the count matches).
**Done when:** tests green and every fix re-confirmed against the code.

## 5. Audit the project's auto-memory

The repo's docs are not the only thing that goes stale: the project's auto-memory
(`~/.claude/projects/<cwd-slug>/memory/`, index `MEMORY.md`) records the moment it was
written. Read every file in that directory — the index alone is not the audit — and give
each one exactly ONE outcome:

- **Obsolete → propose pruning.** The fact stopped holding: the file/flag/script it cites no
  longer exists, the branch merged, the PR closed, a later decision replaced it. Establish
  that against reality, not from memory (`grep` the path, `gh pr view`, `git log`), and list
  the memory with the evidence that killed it. The user deletes — this step proposes and
  leaves every file on disk.
- **Canonical → promote.** The fact stopped being volatile: stable knowledge (an
  architecture decision, an entity, a convention) any future session needs. Write it into
  the project's canonical store — repo docs/ADR, or the site's wiki when there is one —
  under that store's own contract, then reduce the memory file to a pointer to it. The
  boundary is volatility: what will change again next session stays in memory.
- **Stale in part → correct in place.** The lesson still holds, a detail around it moved (a
  version number, a count, a renamed command, an issue that closed). Fix the detail exactly
  as step 3 fixes a doc — a memory carrying one dead fact is read as dead whole.
- **Live → keep**, and check its index line below.

`next-steps.md` and `done-log.md` are NOT ordinary memory: they are written only by
`tk-queue` (contract in `../kickoff/SKILL.md`), so they never enter the pruning proposal and
are never hand-edited. A queue item this audit finds already resolved leaves through
`tk-queue done <id> --how "<what resolved it>"`, one that no longer makes sense through
`tk-queue cancel <id> --why "..."`.

Then **cut `MEMORY.md` back to an index**: one line per memory file, naming what the file
holds and when to reach for it — the content itself lives in the file. Before shortening a
line, confirm what it carried is also inside the file; when it isn't, move it there first.
An index line that survived its file's correction is stale by the same test as the file. A
pointer with no file, a file with no pointer, and a `[[link]]` resolving to neither memory
nor canonical store are all findings.

**Done when:** every file in `memory/` carries one outcome (prune-proposal / promoted /
corrected / kept) with none unread, each promotion is written into the canonical store,
every correction is applied, `MEMORY.md` is one line per file with the two queue pointers
intact, and the user has the pruning proposal — file by file, with the evidence — with
nothing deleted.

## 6. Open the PR
Create a branch, commit the doc fixes and any step-5 promotion that landed in this repo
(following the project's commit conventions — e.g.
required `Co-Authored-By` line) and open the PR with the audit summary (what was stale, what
was fixed). Don't touch production code — this audit is documentation-only.
**Done when:** the PR is open and referenced in the reply to the user.

## 7. Recommend the next step: /clear or /compact
After the audit the state is externalized by definition (docs = code, green tests), so the
default recommendation is **`/clear`** — with one caveat: the **audit PR stays open** and
crosses the session boundary. Include the merge in the suggested opening sentence for the
next conversation (e.g. "merge PR #N and let's take the next pending item") — or offer to
merge still in this session if the user wants everything closed before the clear. Recommend
**`/compact`** only if the audit ran in the MIDDLE of another still-incomplete task (a live
thread the clear would lose). Follow the same criteria as step 6 of the wrap-up skill
(`../wrap-up/SKILL.md`, relative to this file).
**Done when:** the user received ONE clear recommendation with justification and the next
conversation's opening sentence.

## Under /loop
For a periodic autonomous pass:
`/loop Whenever a documentation pass is needed, run the docs-audit skill: review the whole
codebase, ensure every doc reflects the current implementation, fix stale docs, verify,
audit the project's auto-memory and open a PR.`
