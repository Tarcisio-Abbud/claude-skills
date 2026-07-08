---
name: wrap-up
description: "Session close before /compact or /clear: updates memory, docs and status artifacts, runs the tests, summarizes what's pending and recommends the next step"
disable-model-invocation: true
---

A **wrap-up** leaves the external state (memory + docs + tests) reflecting what this session
did, so /compact loses nothing and the next session starts aligned. Execute the steps in
order; each ends on a checkable criterion.

(Generic global version — applies to any project. If a project has its own
`.claude/skills/wrap-up`, that one overrides this.)

## 1. Inventory the session's changes
Gather EVERYTHING that changed since the last wrap-up. The session may have committed to
**branches with open PRs**, so `git status`/`git diff` of the current branch isn't enough:
also check `git log --branches --not <default> --oneline` (commits still outside the default
branch) and, if `gh`/forge CLI exists, the open PRs. Add the **facts/decisions/learnings**
from the conversation (not just code — user choices, discoveries, external pending items).
**Done when:** there is a concrete list of touched files/commits, of the branches/PRs in
play, and of the new decisions/facts — with nothing material omitted.

## 2. Update memory
For each durable and **non-obvious** fact from step 1, create/update ONE file in the
project's auto-memory (dir `memory/`, index `MEMORY.md`), with the right frontmatter and
type (`user`/`feedback`/`project`/`reference`). Prefer updating an existing file over
duplicating; delete what proved wrong. Convert relative dates to absolute. Link with
`[[slug]]`.
**Pending items go to the canonical queue:** also update the project's `next-steps.md` in
memory — new items enter, resolved ones leave (contract and format:
`/root/.claude/skills/kickoff/SKILL.md`). That queue is what `/kickoff` dispatches at the
next session's open.
**Encode into the system:** a correction the user repeated or a check they did by hand is a
system signal, not an instance signal — propose encoding it (project skill, hookify rule,
test) so it holds in every future iteration.
**Done when:** every durable fact of the session has a memory file (with a pointer in
`MEMORY.md`), `next-steps.md` reflects the post-session pending items — or the fact was
consciously discarded as already in the repo/ephemeral — and every recurring correction has
an encoding proposed or discarded.

## 3. Update the repo documentation
Make the documentation reflect the current implementation: `README`, the project's
instruction file (`CLAUDE.md`/`AGENTS.md`/`GEMINI.md`, whichever exists), glossary
(`CONTEXT.md`), `docs/` and ADRs. New commands, test counts, design sections, decisions — no
command/count/path may stay stale.
**Also update the LLM-Wiki** (`/workspace/projects/_wiki/`): if the session changed
canonical knowledge (decisions, architecture, entities, companies, people, a project's
stable vision), reflect it in the affected pages — see `_wiki/README.md` for the canonical ×
volatile boundary. Volatile state stays in memory (step 2), not in the wiki.
**Update the project's status artifact(s)**, if any: check the `/project-artifact` skill
registry (`$CLAUDE_PLUGIN_DATA/artifacts/<slug>/config.md` — usually
`/root/.claude/plugins/data/project-artifact-claude-plugins-official/artifacts/`) and the
project memory (`reference`-type entry with a `claude.ai/code/artifact/...` URL). If the
session changed something the page mirrors (workstreams, PRs, next steps, decisions),
refresh via the skill's own flow: re-gather, edit the existing HTML in place, republish the
SAME path/URL and report only the delta. Session with no impact on what the page shows = say
so and don't republish.
**Done when:** every behaviour changed in the session is reflected in docs and wiki, no
statement is stale — or nothing canonical changed and that was said — and the status
artifact (if any) reflects the session or was declared delta-free.

## 4. Verify
Run the project's test suite. **Detect the runner** from the manifest/files: `pytest`/
`python3 -m pytest`, `npm test`/`pnpm test`/`yarn test`, `cargo test`, `go test ./...`,
`make test`, etc. If code changed, it must be green. Changed runtime behaviour and the
project has an end-to-end verification skill (e.g. `verify`)? Run it too — a green test
doesn't prove the real flow works.
**Done when:** the tests pass — or the failures are reported to the user with the output
(or, if the project has no suite, that is said explicitly).

## 5. Summarize and (on request) version
Deliver a short summary: what changed, what was verified, what remains **pending a user
decision**. Commit/push/PR **only when the user asks** (follow the project's conventions —
e.g. required `Co-Authored-By` line); if on the default branch, create a branch first.
**Done when:** the user has the summary and no external effect (commit/push) happened
without an explicit request.

## 6. Recommend the next step: /docs-audit, /clear or /compact
ALWAYS close by explicitly recommending ONE path, with the why in 1–2 sentences. Criteria:

- **`/clear`** — the default when the wrap-up ended clean: state 100% externalized (memory +
  docs + green tests), nothing mid-flight, and the next task is discrete (starts from zero
  with just `MEMORY.md` + repo). Compacting here would pay to summarize what's already
  saved. When recommending, **give 1–3 ready sentences to open the next conversation**
  (e.g. "let's take the next pending item", or the most mature specific one). If the session
  published a spec or tickets (`/to-spec`, `/to-tickets`), the opening line is
  `/implement <first frontier ticket>` — each ticket in a fresh window is the flow's
  canonical context hygiene.
- **`/compact`** — when there is a live thread that is NOT a durable memory fact: an
  incomplete task mid-flight, debugging with open hypotheses, a half-made
  negotiation/decision, or conversation nuances the next stage still needs that don't make
  sense as a memory file. Compact preserves the thread; clear would lose it.
- **`/docs-audit` (before the clear)** — when there's *drift* beyond the session's scope:
  step 3 hit stale statements this session did NOT cause, or a lot of code piled up since
  the last audit (several sessions/loops without a `docs-audit`). Audit first, then
  `/clear`.
- **None (continue)** — only when the user will immediately chain a related task and the
  current context is still short enough to beat a clean restart.

Also cite any pending item crossing the session boundary (e.g. open PR awaiting merge) — it
enters the suggested opening sentence.
**Done when:** the user received ONE clear recommendation (not a neutral menu), the
justification, and the next conversation's opening sentences when the path is `/clear`.
