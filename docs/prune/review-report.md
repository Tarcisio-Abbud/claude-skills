`docs/prune/review-report.md`

# Pruning report — `tk/skills/review/SKILL.md`

The third run of `/tk:prune`, and the first over a skill whose rules were still being edited the
day before the pass. The material this pass removed is beside this file, in `review.md`. The
pass's own output directory was `prune-out/review/`, outside git; the report and the removed
material are committed here because the ticket asks for them in the pull request.

Throughout, **run** means one execution of the target skill, and the pruning execution is a
**pruning pass**. The table's unit is the **table unit** step 4 of `prune/SKILL.md` defines.

## 1. Numbers

`tk-prune-measure <file> --targets`, on the file before and after. **Bold** is a mark over the
bin's default ceiling.

| metric | ceiling | before | after | `BRIEF.md` | why the mark stands |
|---|---|---|---|---|---|
| lines | 120 (ticket #189) | 167 | **127** | 32 | Reaching 120 means deleting, in whole, one of three KEEPs: §1's **retirement rule** (2 lines), the only route by which the prose exception can ever be taken back out; §3's **size-ceiling line** (2), what a correction batch owes the PR when it grows a file past a ceiling the repo declared; §5's **`Reviews serialize`** (2), the rule that stops a second review being fired into a window already holding one. Each is live behaviour a run reaches, so each is a KEEP, and **KEEP outranks every ceiling**. Three of the seven lines over target are the two-axis review's own corrections: the restored `through its own PR` clause, and the sentence sending the reader to the site's trigger items. |
| body words | — | 1369 | 1172 | 90 | — |
| sentences | — | 97 | 88 | 7 | — |
| mean words per sentence | 22 | 14.1 | 13.3 | 12.9 | — |
| max words in a sentence | 25 | **33** | 25 | 24 | — |
| sentences over 30 words | 4 | 3 | 0 | 0 | — |
| description words | 30 | **89** | 30 | — | — |
| inline evidence | 0 | 0 | 0 | 0 | — |
| pointers to other files | — | 4 | 6 | 1 | — |
| negations | — | 17 | 17 | 0 | — |
| defined terms | — | 7 | 3 | 3 | — |
| terms defined in a sibling too | 0 | 0 | 0 | 0 | — |

Two of the bin's ceilings were marked before and none after, on either file. The one mark that
stands is `lines`, and it is against the ceiling the ticket names rather than one of the bin's —
the bin reports `lines` with no target at all. The last column is where the table says why.

**Where they were measured.** Both files were measured in `tk/skills/review/`, where they land,
never in `docs/prune/` beside this report. That distinction is not cosmetic: the bin reads every
markdown file of a directory as a sibling, and `terms defined in a sibling too` is one of the
targets. It was also load-bearing during the pass — a draft measured in a scratch directory
beside an earlier draft of itself reported **3** shared terms, all of them the same file's own
words read twice.

**`defined terms` fell from 7 to 3, and nothing stopped being defined.** The before column
counts `system` twice, on the two lines that defined it. Of the seven, `system`, `data` and
`regression` went with the MOVE and are now defined once each in `BRIEF.md`; `lens`, `parent`
and `branch point` stayed. The two files share none, which is what the last row measures.

**`negations` did not move, 17 before and 17 after**, with the same distribution by word (`not`
9, `no` 5, `No` 2, `never` 1). It was not a target, and the reason it did not move is plain: not
one of the nine dropped sentences carried a negation, and no rewriting introduced or removed one.
The seventeen that stay are the hard guardrails the ruler allows — "not per file", "no vacuous
kill", "never to another lens", "not approval".

**The two `docs/prune/` files are outside the targets, deliberately.** Step 5 of
`prune/SKILL.md` ends when the bin reads each written file inside the targets *or* the pass
names the ceiling it holds and why. Measured at their landing address, each breaches four:
`review-report.md` on max 77, 64 sentences over 30 words, 11 inline evidence and 3 terms defined
in a sibling; `review.md` on max 43, 18 sentences over 30 words, 1 inline evidence and 2 terms
defined in a sibling. Both are held rather than fixed, for reasons that are the files' purpose.
They are read by a human and by the closing review, never followed by an agent, so
`writing-for-agents` is not their ruler. `review.md` quotes the originals verbatim, and its
longest quotation is the 33-word sentence this pass split; its own 43-word maximum is the
opening paragraph that says why the file carries no inline evidence. What the bin calls
`inline evidence` in both files is the word *measured* in prose about measuring — one hit in
`review.md`, eleven in this report. And both sit in `docs/prune/` beside the other pruning
reports, which is what `terms defined in a sibling too` is reading: `run` and `Bold` are shared
with `docs-audit-report.md` and `verify-report.md`, and `system` with `review.md`. The sibling
is another report of the same pass, never a skill.

### The 120-line target the ticket names, and the seven lines over it

167 → 127 in `SKILL.md`, with a further 32 in `BRIEF.md`. The skill file's body lost 197 words of
1369; 90 of those moved to `BRIEF.md` and 107 left the plugin. Those seven lines are not slack:
the `why` cell of the `lines` row above names them, rule by rule. That cell is what answers the
ticket's own wording — "≤120 linhas ou a tabela diz por que não". The bin's own targets — the
ones criterion 1 of the ticket names — are all met, on both files.

## 2. Table — KEEP / MOVE / DROP

One row per table unit of the original: every sentence that instructs, the `description`, the
fenced block, and each table or bullet the pass ruled on. Line numbers are the original's. The
`why` column is step 3's first half — the run each rule reaches; its second half is answered
once, below the table.

| where | sentence | verdict | why |
|---|---|---|---|
| frontmatter | `description`, 89 words | KEEP, rewritten | "One lens over a committed slice. Use when a diff hits a trigger item, a handoff names an unfired lens, or a skill needs the ruler, inventory or prose rule." 30 words. Reached on every turn, so it pays the most per word. **It loses one branch and a sentence of identity.** The branch "when the parent claims an exemption or fires by choice" is the trigger-item branch written twice — a parent claiming an exemption is answering an item that hit — and the ruler collapses a renamed branch. The 30 words of identity ("a single strong subagent attacks the diff from the angle the slice's class calls for, on top of the repo's mandatory review, with a severity ruler and an attack inventory") are all carried by the opening paragraph and §2. `the ruler` keeps its bare form: `../verify/SKILL.md` took `acceptance ruler` for exactly this reason when it was pruned. The leading word `lens` is front-loaded. |
| L6 | "A **lens** is a subagent that attacks the slice from one angle." | KEEP | Every run: the leading word the whole file is written in. |
| L6–7 | "The **parent** is the session that acts on the findings." | KEEP | Every run: it is what §2's "the parent fires it directly" and §3's whole grading section address. |
| L7 | "The lens fires **once**, on the committed slice, before the repo's mandatory two-axis review." | KEEP | Every run: the ordering rule, and the one the site's own flow is built on. |
| L9–10 | "**Site extensions:** read `~/.claude/tk/review.md` and `.claude/tk/review.md` (project root) if they exist." | KEEP, rewritten | Every run. It now cites the README section that says where each file sits, in the two-line form the plugin's four other skills carry. |
| L10–11 | "They name the lens tier, the user-data directories, and the measurement behind every rule below." | KEEP, rewritten, CLAUSE cut | Every run: it is what makes the thresholds in the body reachable without restating them. It now claims only what an extension file actually carries — the tier and every rule's proof. `the user-data directories` went: it is one trigger item, and the row below hands the reader the whole list at its source. |
| L11 | "The **trigger items** live in the site's CLAUDE.md." | KEEP, rewritten | Every run. It was first DROPped as an environment copy, on the reading that the extension file names where its own items live. The two-axis review showed the reference extension does the opposite — "the pointer is the source, this file only adds what the plugin cannot name" — so the DROP left the reader with no address for the items at all. It returns as a requirement on the reader rather than a fact about the site: "Read the trigger items in the site's CLAUDE.md, or wherever the extension points; where neither carries a list, §1's site-list line decides." The last clause is new, and it answers the site that has an extension file and no item list. |
| L15 | "The lens covers code and the data that code writes." | KEEP | Every run: the scope, and the first half of the test §1 exists to apply. |
| L15–17 | "Prose an agent follows — a skill, a CLAUDE.md, a runbook — is reviewed by the mandatory review alone, in one round, with one exception: when the changed paragraphs prescribe commands, one lens may fire." | KEEP, rewritten | Every run over a diff carrying prose. 33 words, the file's longest; split in two at "One exception". |
| L17–18 | "The trigger is judged per diff, not per file — a mixed file counts only what changed." | MOVE → the base paragraph, same file | The rule is about measuring the diff, not about prose, and it sat inside the prose paragraph. It now opens the paragraph that measures. |
| L18–20 | "The exception's brief adds two constraints to §2's block: report only findings proven by RUNNING a prescribed command, and refuse a finding whose fix is more prose about the prose." | KEEP, split | A run that fires under the prose exception. 30 words; split where the colon was, and its pointer repointed at `BRIEF.md`. |
| L20–22 | "A firing that returns nothing runnable retires the exception: the parent says so in the PR body, and the retirement lands as an edit to this paragraph, through its own PR." | KEEP, rewritten, split | The same run, after its report. 31 words in one sentence became 26 in two, split where the colon was. **All three duties survive**: announce in the PR body, edit the paragraph, and do it through its own PR. That last clause was first cut as a fact no run turns on. The two-axis review showed it decides something a run does turn on — whether the pull request firing under the exception may amend the paragraph it fired under — so it is restored verbatim and carries no CLAUSE row. |
| L22–23 | "Only a firing the trigger allowed counts as that evidence." | CLAUSE | Folded into the sentence it guards, which now opens "A firing **the trigger allowed** that returns nothing runnable". Same guard, one sentence fewer. |
| L23–24 | "Where the repo declares a size ceiling for the file, a correction batch that grows it past the ceiling owes a line in the PR body." | MOVE → §3, same file | It is a duty of the correction batch, and §3 is where the correction batch is defined. Co-location: the rule now sits under the paragraph that creates the thing it binds. |
| L24–25 | "A report or document a human reads gets no review: the reader is the review." | KEEP | A run over a diff carrying a report — the third class, and the one nothing else in the file decides. |
| L27 | "Inside a code slice the same line holds, as a test rather than a list." | KEEP, CLAUSE cut | Every run over a code slice. `as a test rather than a list` describes the form of the rule below it, not the rule. |
| L27–28 | "Prose is what the artifact says ABOUT ITSELF and no program reads: a comment, a docstring, a contract doc." | KEEP | The same run: it is the test, and no model applies it by default — the default reads a docstring as prose whatever consumes it. |
| L29–30 | "Everything else the slice carries is the lens's, its identifiers and the strings a run emits alike." | KEEP, reordered | The same run. It now follows the docstring exception rather than preceding it, so the list of prose examples is qualified before it is used. |
| L30–31 | "A docstring some program consumes (generated help, a parser) is read by a program, so it is the lens's too." | KEEP, rewritten | The same run, and the one case where the sentence before it reads as wrong on its own — `a docstring` sits in the prose list. The trailing "is read by a program, so" restated the test and went. |
| L33–35 | "Measure the diff against the site's trigger items at the slice's **base**: the branch point of the work item, so a rewrite split across PRs measures as one rewrite." | KEEP, split | Every run. 29 words; split at the full stop, the second half stated as its consequence. |
| L35–36 | "Capture the command once, `git diff <base>...HEAD`, and confirm `<base>` resolves before anything else." | KEEP | Every run: an unresolvable base is the failure that reads as an empty diff. |
| L36–37 | "Three dots exclude the working tree, so the slice is committed before the lens fires." | KEEP | Every run: the gotcha no config confesses, and the reason §3's correction batch is reviewed for free. |
| L37–38 | "A hit item fires the lens, unless the parent declines it in one line in the PR as worth less than it costs." | KEEP | Every run whose diff hits an item — the decision the section exists to make. |
| L38–39 | "The trigger says when the lens may fire; whether it is worth firing is the parent's own question, every time." | DROP | Duplicate: the sentence above already carries both halves, in the form that says what to write. |
| L41 | "Two **exemptions** cancel every item they answer." | KEEP | A run holding a refactor or an all-nits change. |
| L41–42 | "Each is a one-line **exemption receipt** in the PR; the wrap-up gate shows it to the user, who reviews the receipt:" | KEEP, CLAUSE cut | The same run: it says where the receipt goes and who sees it. `who reviews the receipt` says what a reader does with what they are shown. |
| L44–45 | the refactor exemption bullet | KEEP | A run over a behaviour-preserving refactor. Its second sentence carries the exception the user-data item takes, which nothing else states. |
| L46 | the all-nits exemption bullet | KEEP | A run whose findings would all be nits. |
| L48 | "No item hit: the mandatory review is the whole review." | KEEP | The common run: no item hit. |
| L48–49 | "The parent may still fire, stating why in one line." | KEEP | A run the parent fires by choice — one of the description's original branches, and the body is where it lives. |
| L49 | "No site list at all: the parent decides on its own judgement, stating why." | KEEP | A run in a repo with no extension file. It is also what makes the DROP of L11 safe. |
| L51–52 | "**Done when:** the PR carries either the firing receipt (§2) or the reason it did not fire. Where the slice has no PR, the item's note carries it." | KEEP | Every run: the completion criterion, and the branch for a slice with no pull request. |
| L56 | "Check that the window fits (§5)." | KEEP | Every firing: the ceiling is checked before the cost is spent, not after. |
| L56–57 | "Announce the **firing receipt**: the item hit, the base, the estimated cost." | KEEP | Every firing. §2's brief and §4's inventory both consume the receipt. |
| L59 | "Fire **one** subagent, on the tier the site extension names, at `effort: "high"`." | KEEP, joined | Every firing: one, not a campaign, and the two knobs it is fired with. |
| L59–60 | "Where no site names one, the parent's own model is the tier." | KEEP, joined | A firing in a repo with no extension file. Joined at a semicolon to the sentence above, which is the branch it answers. |
| L60–61 | "Where either differs from the parent's own model or effort, log the deviation." | DROP | Environment copy: the extension file that names a tier different from the parent's is the file that says to log the deviation, and it does. |
| L61–62 | "Findings live in the parent's context, so the parent fires it directly." | KEEP | Every firing: it is what stops the firing being delegated to a third agent, which would strand the report. |
| L62 | "Pick the angle from the slice's class:" | KEEP, rewritten | Every firing. It absorbed L70, so the default is named in the sentence that asks for the choice. |
| L64–68 | the class → angle table, three rows | KEEP | Every firing: the decision the section turns on. |
| L70 | "**system** is the default: a slice matching two rows, or none of them cleanly, takes it." | MOVE → the sentence above the table, same file | The default belongs in the instruction that picks, not after the table. Its bold went with the move: `BRIEF.md` defines `system`, and two files defining one term is what the last row of §1 measures. |
| L70–71 | "A rewrite that also writes data is the case the site extension prices." | DROP | The pointer resolves to nothing: the extension file this repo is developed against prices the angles and the trigger items, and carries no row for that combination. The surviving line already decides the case. |
| L73–76 | the three angle bullets | MOVE → `tk/skills/review/BRIEF.md` | They are the values of the brief's `Attack:` field, and nothing else reads them. Co-located with the block they fill. No pointer outside the skill names them: `../kickoff/AFK.md` cites §1, `../../reference/slice-rules.md` cites the rounds, budget, design signal and inventory, and `README.md` describes the skill — none is rewritten. |
| L78 | "The brief is this block, filled in:" | DROP, replaced | The block is no longer here. `SKILL.md` now reads "Hand the lens the block in `BRIEF.md`, filled in, carrying its angle's attack line." — an instruction with a verb, where the original was a label. |
| L80–101 | the fenced brief, twenty lines | MOVE → `tk/skills/review/BRIEF.md` | One branch of §1's three: a run that declines, and a run that takes an exemption, never reach it. It is a template handed over whole rather than material the parent reasons with, which is what makes it survive the hop. Verbatim but for one clause (§7 of `review.md`). |
| L103 | "**Done when:** the report is in, or the lens died and §5 hands it off." | KEEP | Every firing: the two ways it ends. |
| L107 | "Reproduce each finding first: lens grades err in both directions." | KEEP | Every run with a report in. It is the file's one anti-default: a model takes a subagent's grade as given. |
| L107–108 | "Then grade it by **impact** against the base; the size of the fix is not a grade." | KEEP | The same run: the ruler, and the wrong ruler it displaces. |
| L108–109 | "A **nit** changes nothing a reader or a run depends on." | KEEP | The same run: half the ruler, and the term §1's second exemption cites. |
| L109–110 | "Everything else is a **defect**, a one-character boundary bug included." | KEEP | The same run: the other half, with the case that is misgraded by default. |
| L110–111 | "When the parent's grade differs from the lens's, the inventory records both." | DROP | Duplicate: §4's inventory bullet is where the record is written, and it now names the case in its own words. |
| L111 | "Fix nits on the spot and list them." | KEEP | A run with nits. |
| L111 | "A nit in a queue file goes through the queue's one writer." | DROP | Duplicate: the end of §3 routes the blocked slice through the same writer, and that sentence stays. |
| L113–114 | "A finding that reproduces at the **branch point** is the repo's backlog, not this slice's: carry it to the item or the ticket and say so in the inventory." | KEEP, split | A run whose finding predates the slice. 29 words; split at the colon. |
| L116–117 | "A mismatch between what the program does and what its words say is graded by the **wrong side**." | KEEP | A run finding a doc-versus-code mismatch. |
| L117–118 | "When the run is the wrong side, it is a code defect. When the code is right and only the words are stale, it is prose, fixed on the spot like a nit." | KEEP, merged | The same run: the two branches. Two sentences of 12 and 20 words became one of 16, with both branches intact. |
| L120–121 | "Defects force a **correction batch**: fix each one, or reject it with a reason specific to the finding, recorded in the inventory." | KEEP | Every run with a defect. |
| L121–122 | "**The correction batch goes to the repo's mandatory two-axis review, never to another lens.**" | KEEP, bold moved | The same run: the rule that replaces the re-lens. The full stop moved outside the bold, so the bin's splitter sees the sentence end; not a word changed. |
| L122 | "One firing is the whole budget." | DROP | Duplicate, third statement: the opening says the lens fires **once** and the sentence before this says never to another lens. |
| L122–125 | "That review reads `base...HEAD` and the correction batch is inside it, so the repair is reviewed by the pass the slice owed anyway." | DROP | Exposition of the rule above it, and it rests on a fact §1 already states. |
| L124–125 | "Its brief carries the invariant each finding violated: the spec of a repair is the finding." | KEEP | The same run: what the mandatory review's brief must carry, which nothing else supplies. |
| L127 | "**A repeated mechanism is a design signal.**" | KEEP, bold moved | Every run with two findings. Same splitter reason as above; not a word changed. |
| L127–129 | "Two findings violating the same guard, or a correction that writes one statement in one more place, means the next instance is already written." | KEEP | The same run: the detector, and neither half is obvious from the term. |
| L129 | "An incomplete repair is a correction, not a signal." | KEEP | The same run: the false positive the detector produces most often. |
| L131 | "A design signal blocks the merge." | KEEP | A run that found the signal — the consequence the whole paragraph turns on. |
| L131–132 | "The parent answers one question and takes the answer to the user, with the findings: should the artifact exist as built?" | KEEP | The same run: the question, which is the one thing that reaches the user. |
| L132–134 | "Code earns its form where the answer must be identical every run or fail loudly. Everywhere else the form is prose." | KEEP, joined | The same run: the criterion the answer is measured against. Joined at a semicolon, 22 words. |
| L134–135 | "The repair that follows the user's call consolidates the mechanism into a single source." | KEEP | The same run: what separates a repair from the patch that leaves the next instance written. |
| L135 | "Unattended, the slice is **blocked**: a queue item carrying the findings, through the queue's one writer." | KEEP | An unattended run with a design signal — the branch with no user to ask. |
| L137–138 | "**Done when:** every finding carries a grade the parent reproduced, and a fix, a rejection or a carried-over item." | KEEP | Every run: the completion criterion, exhaustive over the findings. |
| L142 | "The lens ships an **attack inventory**:" | KEEP | Every run: the artefact §4 exists for, and the term another skill reaches this file by. |
| L144 | inventory bullet, the attacks run | KEEP | Every run. |
| L145 | inventory bullet, the trigger item answered | KEEP | Every run: it is what makes a receipt auditable against the work. |
| L146–147 | inventory bullet, every finding | KEEP, rewritten | Every run. "(both, when they differed)" became "(both, when the parent's differed)", which is where the dropped L110–111 landed. |
| L149–150 | "A lens that found nothing ships the inventory too: the artifacts are the proof of work, and an empty or one-line inventory is a failure, not approval." | KEEP, split | A run that found nothing — the branch this rule was written for. 27 words; split at the comma. |
| L150 | "Merge stays with the user." | KEEP | Every run: the one thing the skill never does. |
| L152–153 | "**Done when:** the inventory is in the PR body (unattended: there or on the item's handoff briefing), and every finding appears in it." | KEEP | Every run, and its unattended branch. |
| L157–159 | "**The lens and the review of its correction batch may not cost more window together than the implementation they review.**" | KEEP, bold moved | Every firing: the ceiling §2's first line checks. Same splitter reason; not a word changed. |
| L159 | "That ceiling binds." | DROP | Suspected no-op: a rule stated is binding, and nothing in a run turns on the sentence. |
| L159–160 | "Where the lens alone would breach it, the slice takes the mandatory review alone, with the reason in the PR." | KEEP | A firing that would breach the ceiling — the exemption the site rule calls the lens's own. |
| L161–162 | "Reviews serialize: the lens fires only when the remaining window fits it and every review already running in this session." | KEEP | A session already holding a review. Nothing else in the file stops a second firing into the same window. |
| L162–163 | "One that does not fit waits whole, as a queue item heading the next window's review line; the slice stays implemented, unreviewed, unmerged." | KEEP, CLAUSE cut | The same run: what happens to a lens that does not fit. The trailing clause is the consequence of *waits whole*. |
| L165–166 | "A lens is **dead** when the window ended, the subagent failed or the wall killed it before its report arrived." | KEEP | A run whose lens never reported — three causes, and `../kickoff/WINDOW.md` writes the handoff this defines. |
| L166 | "A handoff then names the slice, the base and the angle." | KEEP | The same run: the three fields, which is what lets the next session fire it without re-deciding. |
| L166–167 | "The lens has not run: the next session fires it whole." | KEEP | The same run. It is what stops a dead lens being reported as a firing that found nothing. |
| CLAUSE, opening | "`(project root)`" | CLAUSE | Environment copy: where the second file sits is what the README section the line now cites says. |
| CLAUSE, opening | "`the user-data directories`" | CLAUSE | Duplicate: it is one of the trigger items, and the sentence beside it now sends the reader to the whole list at its source. |
| CLAUSE, §1 | "`as a test rather than a list`" | CLAUSE | Exposition: it describes the form of the rule below it, not the rule. |
| CLAUSE, §1 | "`, who reviews the receipt`" | CLAUSE | Exposition: it says what a reader does with what they are shown. |
| CLAUSE, §2 brief | "`— the binary, the fixture, the file —`" | CLAUSE | Exposition: three instances of *artifact*, in a brief whose every other line names none. It left inside the block the MOVE carried. |
| CLAUSE, §5 | "`; the slice stays implemented, unreviewed, unmerged`" | CLAUSE | Exposition: the consequence of *waits whole*, which the sentence has just said. |

**70 KEEP, 5 MOVE, 9 DROP and 7 CLAUSE rows**, over 91 rows. Seven clauses came out of sentences
that stayed and each holds its own row: six sit together at the foot of the table, and the
seventh is the folded sentence at L22–23, which keeps its place in the original's line order.
Four of the KEEPs also carry the `CLAUSE cut` annotation, naming the cut in the row itself.
`review.md` §7 tabulates every one with the sentence it left.

### The half of step 3 this pass could not answer, and the one it could

Step 3 asks two things of an own skill: name the run each rule serves, and say whether such a
run has happened since the rule was written. The first is the `why` column above, for every row.

The second is unanswerable per rule with the artefacts this machine has — plugin telemetry
counts invocations per plugin, not per skill, and `git blame` dates the sentence and not the
run. That finding is already open from the `verify` pass and no row above claims an answer to
it.

What step 3 **does** answer here, and what it answers is unusual: `git log -1 --format=%cs` on
`tk/skills/review/SKILL.md` returns **2026-08-31**, and the same command on
`docs/prune/review-report.md` returns nothing, because this file is the first. So no rule of
this skill has ever been graded by a pruning pass, and the file's two most recent commits — the
prose-rule paragraph of §1 and the correction batch a two-axis review produced over it — both
landed the day before this pass. Two of the three lines the ceiling accounting above refuses to
cut come from those two commits. That is the reason they are refused rather than trimmed: a rule
one day old has had no chance to be wrong yet, and a pruning pass that deletes yesterday's
decision is undoing a slice, not pruning a skill.

## 3. Splits and notes

**The MOVE, and the risk it takes.** `BRIEF.md` is the brief the lens is handed plus the three
angle lines that fill its `Attack:` field. The disclosure test is branching: a run that declines
the item and a run that takes an exemption never reach the block, and `SKILL.md` §1 ends in
either of those on most diffs. Against that stands the honest objection — the firing branch is
the skill's primary path, and the block is the highest-value material in the file, so a pointer
that the parent skips costs more here than anywhere else. The pointer is therefore an
instruction with a verb, in the step that needs it, immediately before that step's completion
criterion. **This is the risk this pass takes and cannot measure**, for the reason §5 gives: the
proof available to a prose pruning pass is the reviewed diff, and a reviewed diff cannot show
whether a future run opens a file.

**No splitting suggestion.** `review` is one skill: every branch ends in the same two artefacts,
the firing receipt and the attack inventory, and `SKILL-MECHANICS` splits by invocation — nothing
needs to invoke the brief on its own.

**The MOVE that was measured and refused.** §1's prose paragraph is the natural second sibling
file: it is nine lines, another skill reaches it (the rewritten `description` advertises it as a
branch), and a code-only diff never needs it. It stays because moving it breaks a cross-file
contract written the day before. `../kickoff/AFK.md` cites it as "`../review/SKILL.md` §1 owns:
the two axes in one round, a lens only where that rule's…", and the site's own project-scope
file points at "§1's rule, which owns the prose policy". Both pointers name a section of this
file, so the MOVE would turn a prose pull request into an edit of two other files, one of them
outside this repo.

**Three rewordings are mechanical and change no word.** A sentence ending `.**` is measured
joined to the sentence after it, because the bin's splitter needs whitespace after the full
stop. Moving the full stop outside the bold separates them and keeps the emphasis where the
original put it. All three are in `review.md` §8, and they are the reason `max words in a
sentence` reads 25 rather than 41 on a draft whose longest real sentence is unchanged.

**Fourteen rewordings, carrying no verdict**, tabulated in `review.md` §8. Nine are one sentence
split in two to bring a unit under the 25-word ceiling.

**One unit added, not removed.** The site-extensions block was three sentences and is now two:
the pointer at the README's own section that the plugin's four other skills carry, and the line
routing the reader to the site's trigger items. The first has no row in §2, which rules on the
original's units; the second is L11's row, kept and rewritten rather than dropped.

## 4. Paths

| file | what it is |
|---|---|
| `tk/skills/review/SKILL.md` | the pruned skill, 127 lines |
| `tk/skills/review/BRIEF.md` | the destination of the brief MOVE, 32 lines |
| `docs/prune/review.md` | every sentence, clause and wording removed, verbatim |
| `docs/prune/review-report.md` | this file |

No file under `bin/` or `tk/bin/` is touched, and no test is edited. The suite is green on this
branch, unedited: 771 tests, `python3 -m unittest discover -s tk/tests`.

## 5. Proof of the target skill

**The proof is the reviewed diff of rules, and there is no eval.** A run of `review` ends in a
campaign — a firing receipt, a subagent's report, a correction batch and an inventory — and none
of those is an artefact a script can check. `prune/SKILL.md` routes exactly this case to the
reviewed diff: "Prose → the reviewed diff of rules."

That is weaker than the eval pair the `dispatch` and `verify` passes could build, and the
weakness is worth naming precisely rather than waving at. An eval would have measured whether a
pruned `review` still produces the same firing decision and the same inventory on a fixed slice.
The reviewed diff measures something else: whether every rule that left the file was a
duplicate, an exposition, an environment copy or a dead pointer, and whether every rule that
stayed still names the run it serves. Column `why` of §2 is that argument, row by row, and the
review reads it against the diff.

Two things therefore go unmeasured by construction, and both are named here rather than
discovered later:

- **the rewritten `description`**, which is the whole trigger surface of a model-invoked skill.
  It loses one branch and 59 words, and nothing in this pass can show that the remaining 30
  still fire it when they should;
- **whether the parent opens `BRIEF.md`.** The `verify` pass could answer the equivalent
  question with an eval and did — both of its runs on the moved branch opened the moved file.
  Here it is an open risk, stated in §3.

The closing review is the two-axis `/mattpocock-skills:code-review`, and it finds none of its
inputs in this repo. It is owed three: the `writing-for-agents` path for the Standards axis, §2's
table as the spec for the Spec axis, and the declaration that the smell baseline is inapplicable
because the target is prose.
