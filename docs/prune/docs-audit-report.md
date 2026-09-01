`docs/prune/docs-audit-report.md`

# Pruning report — `tk/skills/docs-audit/SKILL.md`

The fourth run of `/tk:prune`, and the first over a skill that is pure sequence: seven numbered
steps, each ending on its own completion criterion, with no branch that skips one. The material
this pass removed is beside this file, in `docs-audit.md`. The pass's own output directory was
`prune-out/docs-audit/`, outside git; the report and the removed material are committed here
because the ticket asks for them in the pull request.

Throughout, **run** means one execution of the target skill, and the pruning execution is a
**pruning pass**. The table's unit is the **table unit** step 4 of `prune/SKILL.md` defines.

## 1. Numbers

`tk-prune-measure <file> --targets`, on the file before and after. **Bold** is a mark over the
bin's default ceiling.

| metric | ceiling | before | after |
|---|---|---|---|
| lines | — | 104 | 91 |
| body words | — | 936 | 823 |
| sentences | — | 54 | 65 |
| mean words per sentence | 22 | 17.3 | 12.7 |
| max words in a sentence | 25 | **56** | 23 |
| sentences over 30 words | 4 | **9** | 0 |
| description words | 30 | 23 | 21 |
| inline evidence | 0 | 0 | 0 |
| pointers to other files | — | 13 | 13 |
| negations | — | 16 | 16 |
| defined terms | — | 0 | 0 |
| terms defined in a sibling too | 0 | 0 | 0 |

Two marks over a ceiling before, none after. The `before` column reproduces
`baseline-2026-08-27.md` exactly, re-measured on this branch.

**Where they were measured.** In `tk/skills/docs-audit/`, where the file lands, never in
`docs/prune/` beside this report. The bin reads every markdown file of a directory as a sibling
and `terms defined in a sibling too` is one of the targets, so a file measured beside a draft of
itself reports its own words back as shared. The `review` pass recorded that trap; this pass did
not re-discover it.

**`sentences` rose from 54 to 65 while `body words` fell by 113.** Nine long sentences were split
where the original joined two instructions with a comma or a dash, which is the whole reason
`max words in a sentence` reads 23 rather than 56. Each split is in `docs-audit.md` §7 with its
original, and none of them changed a rule.

**`negations` did not move, 16 before and 16 after.** Not a target, and the reason it held is
plain: no dropped sentence carried a negation, and the two rewritings that touched one — §4's
`detect the runner` and the `/loop` line — were checked against the count. An earlier draft of
the `/loop` line read "with no prompt to write" and pushed the count to 17; it was rewritten
positively ("the loop line only names the skill") before the commit.

**`pointers to other files` held at 13, and the set changed.** `../wrap-up/SKILL.md` survives at
a new line, `../kickoff/SKILL.md` survives, and no pointer was added or removed. The bin counts
`~/.claude/projects/`, `/memory/` and `MEMORY.md` as three separate pointers on the same line,
which is why an address the pass never touched contributes three.

### There is no line ceiling, and the skill kept every step

The bin reports `lines` with no target, so 91 is not measured against anything. It is worth
saying what the 13 lines were: two are the project-override note, three are §7's merge sentence,
three are the `/loop` prompt, and the remaining five are clauses cut from sentences that stayed.
No step, no completion criterion and no bullet of §5 left the file.

## 2. Table — KEEP / MOVE / DROP

One row per table unit of the original: every sentence that instructs, the `description`, and
each bullet the pass ruled on, plus a CLAUSE row per cut clause. Line numbers are the
original's. The `why` column is step 3's first half — the run each rule reaches; its second half
is answered once, below the table.

| where | sentence | verdict | why |
|---|---|---|---|
| frontmatter | `description`, 23 words | KEEP, rewritten | "Full documentation audit against the code, run periodically: finds stale docs, fixes, verifies, audits the project's auto-memory and opens a PR." 21 words. The skill is `disable-model-invocation: true`, so `SKILL-MECHANICS.md` makes this line human-facing — "a one-line summary, trigger lists stripped" — and its context load is zero. **It loses the branch `/loop`**, which the `## Under /loop` section owns and which no agent can act on: nothing but the human reaches a user-invoked skill. `periodic` is kept as `run periodically`, because on a user-invoked skill the human is the index and periodicity is what tells them when to reach for it. The leading word `audit` is front-loaded in the body, not here; the description opens on `Full documentation audit`, which is the same word doing the same job. |
| L7–10 | "An **audit** sweeps the ENTIRE codebase and guarantees every document reflects the current implementation — heavier than `/tk:wrap-up` (which covers only the session), done from time to time, and good to run under `/loop`." | KEEP, split | Every run: the leading word the whole file is written in, and the scope that separates it from the session-sized pass. 33 words; split in two at the dash, so the comparison with `/tk:wrap-up` stands as its own sentence. Two clauses came out, each with its own row below. |
| L9–10 | "Each step ends on an **exhaustive** criterion: "every claim verified", not "a list of changes"." | KEEP | Every run. It is the demand lever `writing-for-agents` names: without it a model reads seven "Done when" lines as a checklist to satisfy rather than a bar to clear, and samples. |
| L12 | "(Generic global version — applies to any project." | DROP | Suspected no-op: the file is where it is, and a run cannot act on being told so. |
| L12–13 | "If a project has its own `.claude/skills/docs-audit`, that one overrides this.)" | DROP | Two reasons, either sufficient. A session reading this file has already invoked `/tk:docs-audit`, so no run can act on it. And the claim is false as written: `prune/SKILL.md` states this house's resolution rule — "A copy under `.claude/skills/` takes the bare name while the plugin skill stays reachable namespaced: a second skill, not a shadow." The project copy answers to `/docs-audit`, this one to `/tk:docs-audit`, and neither overrides the other. |
| L16–19 | "Enumerate all documents (`README`, the project's instruction file — `CLAUDE.md`/`AGENTS.md`/`GEMINI.md` —, glossary `CONTEXT.md`, `docs/`, ADRs) and extract the **verifiable claims** they make: commands, file paths, counts (e.g. number of tests), script/function names, described flows, decisions." | KEEP, split | Every run: it is step 1, and both lists are live. The document list is a cache the agent cannot look up — an `ls` finds `docs/` but never tells it that `CLAUDE.md` and `GEMINI.md` are documents this audit owns. The claim list is what makes "verifiable" checkable. 34 words; split at "and extract", so each list sits in its own sentence. |
| L20 | "**Done when:** there is an inventory of claims, each with its source document." | KEEP | Every run: step 1's criterion, and the "each with its source document" half is what makes step 2 possible. |
| L23–24 | "For each claim, confirm in the codebase (run the command, `grep` the path/function, actually count the tests)." | KEEP | Every run. `actually count the tests` is the anti-default: a model asked to verify a count will accept the documented one. |
| L24 | "Mark it **exact** or **stale**, with the evidence." | KEEP | Every run: the two-valued mark step 3 consumes. |
| L25 | "**Done when:** EVERY claim in the inventory is marked exact/stale — none unchecked." | KEEP, CLAUSE cut | Every run: step 2's criterion, exhaustive over the inventory. |
| L28 | "Update each stale claim to match the implementation." | KEEP | Every run with a stale claim: step 3's instruction. |
| L28–29 | "Where the doc describes something that no longer exists, fix or remove it." | KEEP | A run whose doc describes something gone — the case where "update to match" has no target to match. |
| L29 | "Don't invent behaviour — document what the code does." | KEEP | The same run. A hard guardrail, and it is already paired with its positive target, which is what `writing-for-agents` asks of a prohibition. |
| L30–31 | "Preserve legitimate history (e.g. proposal/decision sections in a design doc or ADR are not rewritten to pretend the original plan was the final result)." | KEEP, split | A run over a repo carrying ADRs or design docs. The strongest anti-default in the file: a model told to make docs match code will rewrite an ADR's proposal section into the outcome. 24 words in one sentence with the rule inside a parenthesis; split so the rule is a sentence and not an aside. |
| L32 | "**Done when:** no claim marked stale remains." | KEEP | Every run: step 3's criterion. |
| L35–37 | "Run the project's test suite (**detect the runner**: `pytest`, `npm test`, `cargo test`, `go test ./...`, `make test`, etc.) and re-check the claims you fixed (e.g. the documented command runs; the count matches)." | KEEP, split, CLAUSE cut | Every run: step 4 is what stops a doc fix from being asserted rather than checked. 32 words; split at "and re-check", so running the suite and re-checking the fixes are two instructions. |
| L38 | "**Done when:** tests green and every fix re-confirmed against the code." | KEEP | Every run: step 4's criterion, and the second half is what binds it to the fixes rather than to the suite alone. |
| §5, whole section | the auto-memory audit, 40 of 104 lines | MOVE refused, stays inline | **The ticket's call.** Two destinations were weighed against `prune/REPORT.md`'s criteria. *A reference file beside the skill* fails the disclosure test: `writing-for-agents` disclosure is branching — "inline what every branch needs, and push behind a pointer what only some branches reach" — and every run of this skill reaches step 5, because the file is a sequence with no branch that skips a step. The saving would also be nil: the skill is user-invoked, so its context load is zero until it is invoked, and once invoked the pointer is a hop the parent may skip, which is cost with no return. *A new skill* fails `SKILL-MECHANICS`'s splitting criterion, which asks for a distinct leading word that triggers it on its own **or** another skill that must reach it. Neither holds today: nothing in the plugin invokes a memory audit, and `wrap-up` §2 does its own session-scoped memory update rather than reaching for this one. The suggestion that would satisfy the first branch is in §3. |
| L42–44 | "The repo's docs are not the only thing that goes stale: the project's auto-memory (`~/.claude/projects/<cwd-slug>/memory/`, index `MEMORY.md`) records the moment it was written." | KEEP, split | Every run: it is the address of the directory step 5 sweeps, and `<cwd-slug>` is a lookup the agent cannot perform from the repo. 24 words with the motivation and the address welded at a colon; split so the address stands alone. |
| L44–46 | "Read every file in that directory — the index alone is not the audit — and give each one exactly ONE outcome:" | KEEP | Every run. The dash clause is the anti-default: a model handed a directory with an index reads the index and stops. `exactly ONE` is what makes the four bullets a partition rather than a menu. |
| L47–48 | "The fact stopped holding: the file/flag/script it cites no longer exists, the branch merged, the PR closed, a later decision replaced it." | KEEP | A run over a memory whose fact died. The four examples are the test, not decoration: each names a lookup step 5 can run. |
| L49–51 | "Establish that against reality, not from memory (`grep` the path, `gh pr view`, `git log`), and list the memory with the evidence that killed it." | KEEP, split | The same run, and it is the file's sharpest anti-default — an agent auditing memory files will judge a memory against its own context, which is the very thing under audit. 25 words, at the ceiling; split at the comma so the three commands and the listing duty are separate instructions. |
| L51 | "The user deletes — this step proposes and leaves every file on disk." | KEEP | The same run: the one thing this step never does. It is a write into a user-data directory, and nothing else in the file forbids it. |
| L52–53 | "The fact stopped being volatile: stable knowledge (an architecture decision, an entity, a convention) any future session needs." | KEEP | A run over a memory that turned canonical: the test that separates this bullet from the one above. |
| L53–56 | "Write it into the project's canonical store — repo docs/ADR, or the site's wiki when there is one — under that store's own contract, then reduce the memory file to a pointer to it." | KEEP, split | The same run: the destination, the contract it obeys, and what happens to the file left behind. 32 words carrying two actions joined by "then"; split there. |
| L55–56 | "The boundary is volatility: what will change again next session stays in memory." | KEEP | The same run: the criterion that stops the promotion from emptying the memory directory. |
| L57–58 | "The lesson still holds, a detail around it moved (a version number, a count, a renamed command, an issue that closed)." | KEEP | A run over a memory that is right in the large and wrong in a detail — the outcome a model does not reach on its own, having only "keep" and "delete" by default. |
| L58–59 | "Fix the detail exactly as step 3 fixes a doc — a memory carrying one dead fact is read as dead whole." | KEEP | The same run: it borrows step 3's method rather than restating it, and the clause after the dash is why the outcome exists at all. |
| L60 | "**Live → keep**, and check its index line below." | KEEP | The common run: the fourth outcome, and the hand-off to the index paragraph. |
| L62–64 | "`next-steps.md` and `done-log.md` are NOT ordinary memory: they are written only by `tk-queue` (contract in `../kickoff/SKILL.md`), so they never enter the pruning proposal and are never hand-edited." | KEEP, split | Every run in a project with a queue. It is the guard on the queue's single writer, and an audit that hand-edits `next-steps.md` is exactly the failure the queue contract exists to prevent. 27 words; split before "They never enter". |
| L64–66 | "A queue item this audit finds already resolved leaves through `tk-queue done <id> --how "<what resolved it>"`, one that no longer makes sense through `tk-queue cancel <id> --why "..."`." | KEEP, CLAUSE cut | A run that finds a resolved queue item. The routing — `done` for resolved, `cancel` for senseless — is the judgement, and nothing else in the file carries it. |
| L68–70 | "Then **cut `MEMORY.md` back to an index**: one line per memory file, naming what the file holds and when to reach for it — the content itself lives in the file." | KEEP, split | Every run: the index contract, and "when to reach for it" is what makes the line a context pointer rather than a title. 30 words; split at the dash. |
| L70–71 | "Before shortening a line, confirm what it carried is also inside the file; when it isn't, move it there first." | KEEP | A run shortening an index line — the ordering that stops the cut from destroying the only copy. |
| L71–72 | "An index line that survived its file's correction is stale by the same test as the file." | KEEP | A run that corrected a file in place: the case the index paragraph would otherwise miss, since the file now reads correct and the line does not. |
| L72–73 | "A pointer with no file, a file with no pointer, and a `[[link]]` resolving to neither memory nor canonical store are all findings." | KEEP | Every run: three checks over the directory as a whole, which no per-file outcome reaches. |
| L75–79 | "**Done when:** every file in `memory/` carries one outcome (prune-proposal / promoted / corrected / kept) with none unread, each promotion is written into the canonical store, every correction is applied, `MEMORY.md` is one line per file with the two queue pointers intact, and the user has the pruning proposal — file by file, with the evidence — with nothing deleted." | KEEP, split | Every run: step 5's criterion, and the longest sentence in the file at **56 words**. Split into three, one per thing checked: the outcomes, the writes, the proposal. The parenthesis naming the four outcomes became "one of the four outcomes" — the bullets above are their definition, and repeating the names here was the meaning stated twice. |
| L82–85 | "Create a branch, commit the doc fixes and any step-5 promotion that landed in this repo (following the project's commit conventions — e.g. required `Co-Authored-By` line) and open the PR with the audit summary (what was stale, what was fixed)." | KEEP, split, CLAUSE cut | Every run: step 6. 39 words carrying two actions; split at "Open the PR". "any step-5 promotion that landed in this repo" survives, and it is the only thing tying the two halves of the audit into one commit. |
| L85 | "Don't touch production code — this audit is documentation-only." | KEEP | Every run: the scope guard. A model that has just verified a doc against the code will fix the code. |
| L86 | "**Done when:** the PR is open and referenced in the reply to the user." | KEEP | Every run: step 6's criterion, and the second half is what makes the PR reachable after the session. |
| L89–92 | "After the audit the state is externalized by definition (docs = code, green tests), so the default recommendation is **`/clear`** — with one caveat: the **audit PR stays open** and crosses the session boundary." | KEEP, split | Every run: it is the one argument this step owns and `wrap-up` step 6 does not — that an audit ends with the state externalized by construction, so the default is decided before the recommendation is weighed. 32 words; split at the dash, and the caveat is now its own sentence. |
| L91–94 | "Include the merge in the suggested opening sentence for the next conversation (e.g. "merge PR #N and let's take the next pending item") — or offer to merge still in this session if the user wants everything closed before the clear." | DROP | Duplicate: step 6 of `../wrap-up/SKILL.md`, which the surviving sentence in the same paragraph points at, already requires every PR the session opened to be anchored and sets the two shapes the opening sentence may take. Merging inside the session is the wrap-up versioning gate's decision, and this step has no standing to offer it. |
| L94–96 | "Recommend **`/compact`** only if the audit ran in the MIDDLE of another still-incomplete task (a live thread the clear would lose)." | KEEP, CLAUSE cut | A run that happened inside another task — the one branch where the default is wrong. |
| L95–96 | "Follow the same criteria as step 6 of the wrap-up skill (`../wrap-up/SKILL.md`, relative to this file)." | KEEP, rewritten | Every run: the pointer that makes the two DROPs above safe. Rewritten from "Follow the same criteria as" — a label — into an instruction naming what that step decides: the recommendation's wording and the next conversation's opening sentence. The pointer was checked: `wrap-up/SKILL.md` L309 is `## 6. Close: the report, the handoff, and the next step`, and its `### The next step` subsection at L408 is the material. |
| L97–98 | "**Done when:** the user received ONE clear recommendation with justification and the next conversation's opening sentence." | KEEP | Every run: step 7's criterion, and `ONE` is what stops the step ending in a neutral menu. |
| L101 | "For a periodic autonomous pass:" | DROP | Suspected no-op: a label with no verb, under the heading `## Under /loop`, which says it. |
| L102–104 | the four-line `/loop` prompt | KEEP, rewritten | A user setting up a periodic pass. The prompt restated steps 1 to 6 in prose and had already gone stale — it named neither step 5's promotion into the canonical store nor step 7 — which is what a restatement of a document inside that document does. The built-in `/loop` skill takes "a prompt or slash command", so the line is now `/loop Whenever a documentation pass is needed, run /tk:docs-audit.`: the condition verbatim, the restatement replaced by the skill's own name. 39 words to 11, and the steps above become the single source of truth. |
| CLAUSE, opening | "done from time to time," | CLAUSE | Suspected no-op: nothing in a run turns on it, and the sentence already says the audit is heavier than the session pass. |
| CLAUSE, opening | "and good to run under `/loop`" | CLAUSE | Duplicate: `## Under /loop` is the section that says so and carries the line to paste. |
| CLAUSE, §2 | "— none unchecked" | CLAUSE | Duplicate within one sentence: `EVERY` in capitals is the same bar, said first. |
| CLAUSE, §4 | "`pytest`, `npm test`, `cargo test`, `go test ./...`, `make test`, etc." | CLAUSE | Environment copy: the runner is a one-file lookup — `package.json`, `Makefile`, `pyproject.toml` — and `writing-for-agents` leaves those to the environment, where they cannot go stale. `**detect the runner**` stays, as `detecting the runner rather than assuming one`, because the instruction to look is the part a default would skip. |
| CLAUSE, §5 | "`<id> --how "<what resolved it>"`" and "`<id> --why "..."`" | CLAUSE | Environment copy: `tk-queue done --help` carries the flags, and `../kickoff/SKILL.md` — cited in the sentence before — carries the contract. The routing decision the sentence exists for is untouched. |
| CLAUSE, §6 | "— e.g. required `Co-Authored-By` line" | CLAUSE | Environment copy: "following the project's commit conventions" is the pointer, and the project's own instruction file is where the convention lives. One site's convention had leaked into a plugin shipped to every project. |
| CLAUSE, §7 | "(a live thread the clear would lose)" | CLAUSE | Exposition: it restates why a still-incomplete task is the exception, which the sentence has just said. |

**41 KEEP, 4 DROP and 7 CLAUSE rows, plus one refused MOVE**, over 53 rows. No MOVE was
executed. Twelve of the KEEPs carry a split, and each split is in `docs-audit.md` §7 with the
sentence it came from.

### The half of step 3 this pass could not answer, and the one it could

Step 3 asks two things of an own skill: name the run each rule serves, and say whether such a
run has happened since the rule was written. The first is the `why` column above, for every row.

The second is unanswerable per rule with the artefacts this machine has — plugin telemetry
counts invocations per plugin, not per skill, and `git blame` dates the sentence and not the
run. That finding is open from the `verify` pass and no row above claims an answer to it.

What step 3 **does** answer here: `git log -1 --format=%cs` on `tk/skills/docs-audit/SKILL.md`
returns **2026-08-14**, and the same command on `docs/prune/docs-audit-report.md` returns
nothing, because this file is the first. So no rule of this skill has ever been graded by a
pruning pass. The file's whole history is three commits, and the most recent — `5740efb`,
`2026-08-14`, "docs-audit: a auto-memória também envelhece, e o passo 5 a varre" — is the one
that added §5 entire. That is eighteen days before this pass, not one, so the argument the
`review` pass used to refuse cutting yesterday's decision does not apply here; §5 stays inline
on the disclosure test alone, which is the argument its table row makes.

## 3. Splits and notes

**The splitting suggestion: a memory-audit skill, not this slice.** §5 is a skill inside a
skill by subject — it audits a user-data directory outside the repo, with its own four-valued
partition, its own single-writer guard and its own completion criterion — and it is 40 of the
original's 104 lines. `SKILL-MECHANICS`'s invocation criterion is what would carry the split:
a distinct leading word that should trigger it on its own, or another skill that must reach it.
The leading word exists in the house's language already (**auto-memory**), and the trigger a
user would type is "audit the memory" without a codebase sweep — today that costs a full
docs-audit, steps 1 through 4 included, to reach step 5. The consumer that would make it
model-invoked does not exist yet: `wrap-up` §2 updates the session's own memory and does not
audit the directory, and nothing else in the plugin reads memory files. **So the split is a
suggestion and a slice of its own**, as `prune/SKILL.md` requires, and its first question is
whether `wrap-up` §2 should reach it — that answer decides model-invoked against user-invoked,
and it is the whole cost of the split.

**Two findings this pass did not act on**, both additions rather than subtractions, and a
pruning pass subtracts:

- **No site-extensions line.** `dispatch`, `verify`, `review`, `wrap-up` and `kickoff` each open
  with the two-line block pointing at `~/.claude/tk/<skill>.md`; `docs-audit` carries none, and
  the site directory this repo is developed against holds no `docs-audit.md`. A site with a wiki — where step 5's *canonical
  store* actually lives — has nowhere to say so, and §5 hard-codes the branch as "the site's
  wiki when there is one". Adding the block is one unit added, so it belongs to whoever asks
  for it, not to this pass.
- **The heading `## 4. Verify` collides with step 2's job**, which is also verification. Step 2
  verifies claims against the code and step 4 verifies the fixes; the two are told apart by
  their bodies, not their headings. Renaming is a reworking, not a cut.

**Fourteen rewordings, carrying no verdict**, tabulated in `docs-audit.md` §7. Twelve are one
sentence split in two to bring a unit under the 25-word ceiling; one is the heading of §7,
which nothing points at by name; one is the `/loop` line.

**No mechanical `.**` rewording was needed.** The `review` pass found that a sentence ending
`.**` measures joined to the next, because the bin's splitter needs whitespace after the full
stop. `docs-audit` ends no sentence that way, and the pass checked rather than assumed: the
before column's 54 sentences and the after column's 65 both split where the prose does.

## 4. Paths

| file | what it is |
|---|---|
| `tk/skills/docs-audit/SKILL.md` | the pruned skill, 91 lines |
| `docs/prune/docs-audit.md` | every sentence, clause and wording removed, verbatim |
| `docs/prune/docs-audit-report.md` | this file |

No file under `bin/` or `tk/bin/` is touched, and no test is edited. The suite is green on this
branch, unedited: `python3 -m pytest tk/tests/ -q` → 771 passed, 433 subtests passed.

## 5. Proof of the target skill

**The proof is the reviewed diff of rules, and there is no eval.** A run of `docs-audit` ends in
a pull request against whatever repository it swept, plus a pruning proposal over that project's
auto-memory. Neither is an artefact a script can check: the PR's content depends entirely on how
stale the swept repo was, and the memory proposal is a judgement over files outside the repo.
`prune/SKILL.md` routes exactly this case — "Prose → the reviewed diff of rules."

An eval would have measured whether a pruned `docs-audit` still produces the same set of stale
claims and the same four-valued partition on a fixed repository and a fixed memory directory.
Building that control arm means freezing a repo *and* a `memory/` directory, which is why the
`dispatch` and `verify` passes could build eval pairs and this one cannot. The reviewed diff
measures something else: whether every rule that left the file was a duplicate, an exposition,
an environment copy or a no-op, and whether every rule that stayed still names the run it
serves. Column `why` of §2 is that argument, row by row, and the review reads it against the
diff.

Two things go unmeasured by construction, and both are named here rather than discovered later:

- **the `/loop` line**, which now names the skill instead of restating it. The claim that
  `/loop` accepts a slash command comes from the built-in `/loop` skill's own description — "Run
  a prompt or slash command on a recurring interval (e.g. `/loop 5m /foo`)" — and not from a run
  of it. That is an official source, not a measurement;
- **whether the shortened §7 still reaches `wrap-up` step 6.** The pointer was verified to
  resolve — `wrap-up/SKILL.md` L309 is step 6 and L408 is its next-step subsection — but three
  sentences that restated that step's content are gone, and no pass can show that a future run
  opens the file rather than recommending `/clear` from the sentence above.

The closing review is the two-axis `/mattpocock-skills:code-review`, and it finds none of its
inputs in this repo. It is owed three: the `writing-for-agents` path for the Standards axis,
§2's table as the spec for the Spec axis, and the declaration that the smell baseline is
inapplicable because the target is prose.
