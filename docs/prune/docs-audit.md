# What the `docs-audit` pruning pass removed

Every sentence, clause and wording the pass took out of `tk/skills/docs-audit/SKILL.md`,
verbatim, so that any one of them is put back in one edit. The verdicts, their reasons and the
numbers are in `docs-audit-report.md` beside this file.

`prune/REPORT.md` defines this file as the `docs/` file of **inline evidence** pulled out of an
own skill. On `docs-audit` there is none — the bin reports `inline evidence: 0` before and
after — so everything below is removed prose, the use `dispatch.md`, `verify.md` and `review.md`
also put this destination to.

## 1. DROP — the project-override note

**Two sentences that a run cannot act on, and whose claim the plugin contradicts.** A session
reading this file has already invoked `/tk:docs-audit`; being told a different skill overrides it
changes nothing the run can do. The claim is also wrong as written: `prune/SKILL.md` states the
resolution rule this house works to — "A copy under `.claude/skills/` takes the bare name while
the plugin skill stays reachable namespaced: a second skill, not a shadow." A project copy is
reached as `/docs-audit` and this one stays reachable as `/tk:docs-audit`; neither overrides the
other.

> (Generic global version — applies to any project. If a project has its own
> `.claude/skills/docs-audit`, that one overrides this.)

## 2. DROP — duplicate of `wrap-up` step 6

**The merge, decided twice.** The sentence that survives beside it points at step 6 of
`../wrap-up/SKILL.md`, and that step already carries both halves: its `/clear` bullet requires
every PR the session opened to be anchored (merged, or carried in the queue as a DECISION), and
it sets the two shapes the next conversation's opening sentence may take. Merging inside the
session is the wrap-up versioning gate's decision, not this step's.

> Include the merge in the suggested opening sentence for the next conversation (e.g. "merge
> PR #N and let's take the next pending item") — or offer to merge still in this session if the
> user wants everything closed before the clear.

## 3. DROP — a label the heading already carries

**"For a periodic autonomous pass".** A label with no verb, sitting under the heading
`## Under /loop`, which says the same thing.

> For a periodic autonomous pass:

## 4. Rewritten — the `/loop` prompt

The four-line prompt restated steps 1 to 6 of the skill in prose, and had gone stale: it named
neither step 5's promotion into the canonical store nor step 7. The restatement itself is not
optional. This skill is `disable-model-invocation: true`, so the loop's model can never invoke
it, and a slash command written inside prose expands nowhere — a line reading "run
`/tk:docs-audit`" is a loop that does nothing. So the prompt stays self-sufficient: the
condition that opens it is kept verbatim, and the restatement after it is refreshed to cover
steps 1 to 7.

> `/loop Whenever a documentation pass is needed, run the docs-audit skill: review the whole
> codebase, ensure every doc reflects the current implementation, fix stale docs, verify,
> audit the project's auto-memory and open a PR.`

It reads now:

> `/loop Whenever a documentation pass is needed, audit every doc against the code. Inventory
> the claims and verify each against the codebase. Fix the stale ones, then run the project's
> tests. Audit the project's auto-memory, promoting what turned canonical. Open a
> documentation-only PR and recommend the next step.`
> The loop's model cannot invoke a user-invoked skill, so the line restates the steps.

## 5. Rewritten — the `description`

Twenty-three words to twenty-one. The skill is `disable-model-invocation: true`, so
`SKILL-MECHANICS.md` makes the description human-facing: "a one-line summary, trigger lists
stripped". `/loop` is the stripped trigger; `periodic` stays, because on a user-invoked skill
the human is the index and periodicity is what tells them when to reach for it.

> Full documentation audit against the code: finds stale docs, fixes, verifies, audits the
> project's auto-memory and opens a PR (good under /loop, periodic)

It reads now:

> Full documentation audit against the code, run periodically: finds stale docs, fixes,
> verifies, audits the project's auto-memory and opens a PR

## 6. CLAUSE — cut from sentences that stayed

Seven clauses, each with the sentence it left. The sentence itself is in the file; only the
clause is removed here.

| where | clause removed | the sentence it left |
|---|---|---|
| opening | `done from time to time,` | "An **audit** sweeps the ENTIRE codebase and guarantees every document reflects the current implementation — heavier than `/tk:wrap-up` (which covers only the session), done from time to time, and good to run under `/loop`." |
| opening | `and good to run under `/loop`` | the same sentence |
| §2 `Done when` | `— none unchecked` | "**Done when:** EVERY claim in the inventory is marked exact/stale — none unchecked." |
| §4 | `: `pytest`, `npm test`, `cargo test`, `go test ./...`, `make test`, etc.` | "Run the project's test suite (**detect the runner**: `pytest`, `npm test`, `cargo test`, `go test ./...`, `make test`, etc.) and re-check the claims you fixed (e.g. the documented command runs; the count matches)." |
| §5 queue | `<id> --how "<what resolved it>"` and `<id> --why "..."` | "A queue item this audit finds already resolved leaves through `tk-queue done <id> --how \"<what resolved it>\"`, one that no longer makes sense through `tk-queue cancel <id> --why \"...\"`." |
| §6 | `— e.g. required `Co-Authored-By` line` | "Create a branch, commit the doc fixes and any step-5 promotion that landed in this repo (following the project's commit conventions — e.g. required `Co-Authored-By` line) and open the PR with the audit summary (what was stale, what was fixed)." |
| §7 | `(a live thread the clear would lose)` | "Recommend **`/compact`** only if the audit ran in the MIDDLE of another still-incomplete task (a live thread the clear would lose)." |

## 7. Rewordings, carrying no verdict

No sentence below lost a rule; each was split or restructured to bring a unit under the
25-word ceiling, or to state positively what the original stated as an aside. The originals:

> An **audit** sweeps the ENTIRE codebase and guarantees every document reflects the current
> implementation — heavier than `/tk:wrap-up` (which covers only the session), done from time to
> time, and good to run under `/loop`.

> Enumerate all documents (`README`, the project's instruction file — `CLAUDE.md`/
> `AGENTS.md`/`GEMINI.md` —, glossary `CONTEXT.md`, `docs/`, ADRs) and extract the
> **verifiable claims** they make: commands, file paths, counts (e.g. number of tests),
> script/function names, described flows, decisions.

> Preserve legitimate history (e.g. proposal/decision sections in a design doc or ADR are not
> rewritten to pretend the original plan was the final result).

> Run the project's test suite (**detect the runner**: `pytest`, `npm test`, `cargo test`,
> `go test ./...`, `make test`, etc.) and re-check the claims you fixed (e.g. the documented
> command runs; the count matches).

> The repo's docs are not the only thing that goes stale: the project's auto-memory
> (`~/.claude/projects/<cwd-slug>/memory/`, index `MEMORY.md`) records the moment it was
> written.

> Establish that against reality, not from memory (`grep` the path, `gh pr view`, `git log`),
> and list the memory with the evidence that killed it.

> Write it into the project's canonical store — repo docs/ADR, or the site's wiki when there
> is one — under that store's own contract, then reduce the memory file to a pointer to it.

> `next-steps.md` and `done-log.md` are NOT ordinary memory: they are written only by
> `tk-queue` (contract in `../kickoff/SKILL.md`), so they never enter the pruning proposal and
> are never hand-edited.

> Then **cut `MEMORY.md` back to an index**: one line per memory file, naming what the file
> holds and when to reach for it — the content itself lives in the file.

> **Done when:** every file in `memory/` carries one outcome (prune-proposal / promoted /
> corrected / kept) with none unread, each promotion is written into the canonical store,
> every correction is applied, `MEMORY.md` is one line per file with the two queue pointers
> intact, and the user has the pruning proposal — file by file, with the evidence — with
> nothing deleted.

> Create a branch, commit the doc fixes and any step-5 promotion that landed in this repo
> (following the project's commit conventions — e.g.
> required `Co-Authored-By` line) and open the PR with the audit summary (what was stale, what
> was fixed).

> After the audit the state is externalized by definition (docs = code, green tests), so the
> default recommendation is **`/clear`** — with one caveat: the **audit PR stays open** and
> crosses the session boundary.

> Recommend **`/compact`** only if the audit ran in the MIDDLE of another still-incomplete task
> (a live thread the clear would lose). Follow the same criteria as step 6 of the wrap-up skill
> (`../wrap-up/SKILL.md`, relative to this file).

One heading was shortened, and nothing points at it by name:

> ## 7. Recommend the next step: /clear or /compact
