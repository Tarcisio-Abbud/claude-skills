---
name: docs-audit
description: "Full documentation audit against the code: finds stale docs, fixes, verifies and opens a PR (good under /loop, periodic)"
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

## 5. Open the PR
Create a branch, commit the doc fixes (following the project's commit conventions — e.g.
required `Co-Authored-By` line) and open the PR with the audit summary (what was stale, what
was fixed). Don't touch production code — this audit is documentation-only.
**Done when:** the PR is open and referenced in the reply to the user.

## 6. Recommend the next step: /clear or /compact
After the audit the state is externalized by definition (docs = code, green tests), so the
default recommendation is **`/clear`** — with one caveat: the **audit PR stays open** and
crosses the session boundary. Include the merge in the suggested opening sentence for the
next conversation (e.g. "merge PR #N and let's take the next pending item") — or offer to
merge still in this session if the user wants everything closed before the clear. Recommend
**`/compact`** only if the audit ran in the MIDDLE of another still-incomplete task (a live
thread the clear would lose). Follow the same criteria as step 6 of the wrap-up skill
(`/root/.claude/skills/tk/skills/wrap-up/SKILL.md`).
**Done when:** the user received ONE clear recommendation with justification and the next
conversation's opening sentence.

## Under /loop
For a periodic autonomous pass:
`/loop Whenever a documentation pass is needed, run the docs-audit skill: review the whole
codebase, ensure every doc reflects the current implementation, fix stale docs, verify, and
open a PR.`
