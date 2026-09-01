# What the `review` pruning pass removed

Every sentence, clause and wording the pass took out of `tk/skills/review/SKILL.md`, verbatim,
so that any one of them is put back in one edit. The verdicts, their reasons and the numbers
are in `review-report.md` beside this file.

`prune/REPORT.md` defines this file as the `docs/` file of **inline evidence** pulled out of an
own skill. On `review` there is none, and that is a fact about the skill rather than about the
bin: the pass this skill was born under sends its evidence to the site extension file, and the
bin reports `inline evidence: 0` before and after. Everything below is therefore removed prose,
the use `dispatch.md` and `verify.md` §2 onward also put this destination to.

## 1. DROP — duplicate

**The parent's second question, asked twice.** The sentence before it already carries both
halves: a hit item fires the lens *unless the parent declines it as worth less than it costs*.

> The trigger says when the lens may fire; whether it is worth firing is the parent's own
> question, every time.

**The two grades, recorded twice.** §4's inventory bullet is where the record is written, and
it now names the case in its own words — "its grade (both, when the parent's differed)".

> When the parent's grade differs from the lens's, the inventory records both.

**The queue's one writer, named twice in one section.** The end of §3 routes the blocked slice
through it, in the sentence that survives.

> A nit in a queue file goes through the queue's one writer.

**One firing, said three times.** The opening says the lens fires **once**, and the sentence
immediately before this one says the correction batch never goes to another lens.

> One firing is the whole budget.

## 2. DROP — exposition

**Why the mandatory review sees the repair.** The rule above it is the instruction; this is its
reason, and §1 already carries the fact it rests on (three dots exclude the working tree).

> That review reads `base...HEAD` and the correction batch is inside it, so the repair is
> reviewed by the pass the slice owed anyway.

## 3. DROP — environment copy

**Where the trigger items live.** The site extension file is the source for what a site adds,
and it names the file its own items live in. A site with no extension file is already answered
by §1's last line — "No site list at all: the parent decides on its own judgement".

> The **trigger items** live in the site's CLAUDE.md.

**The deviation log.** A site that names a tier different from the parent's own is the site that
says to log the deviation; the tier and the log belong in one place, and the extension file is
it.

> Where either differs from the parent's own model or effort, log the deviation.

## 4. DROP — suspected no-op

**A rule stated is binding.** Nothing in a run changes on this sentence.

> That ceiling binds.

## 5. DROP — pointer at material that is not there

**The priced combination.** The sentence sends the reader to the site extension for the case of
a rewrite that also writes data. The extension file this repo is developed against prices the
angles and the trigger items; it carries no row for that combination, so the pointer resolves to
nothing. §2's surviving line already decides the case — a slice matching two rows takes
**system**.

> A rewrite that also writes data is the case the site extension prices.

## 6. MOVE — the brief, to `tk/skills/review/BRIEF.md`

The fenced block and the three angle lines that fill its `Attack:` field went to a reference
file beside the skill. Nothing was reworded in the block except one clause, recorded in §7.
The three angle lines went verbatim:

> - **system**: extract the state machine; every state needs a named entry and exit; find the
>   seam where two parts must agree and neither is wrong alone.
> - **data**: feed the ugly, duplicated, real input and watch what comes out.
> - **regression**: a KEEP / MOVE / DROP table of every behaviour against the base.

The sentence that introduced the block did not move; it is replaced in `SKILL.md` by "Hand the
lens the block in `BRIEF.md`, filled in, carrying its angle's attack line."

> The brief is this block, filled in:

## 7. CLAUSE — cut from a sentence that stayed

Each clause is quoted with the sentence it left and what it carried.

| clause cut | the sentence it left | what it carried |
|---|---|---|
| `as a test rather than a list` | "Inside a code slice the same line holds, as a test rather than a list." | the form of the rule below it, not the rule |
| `(project root)` | "read `~/.claude/tk/review.md` and `.claude/tk/review.md` (project root) if they exist" | where the second file sits — the README section the line now cites says it |
| `the user-data directories` | "They name the lens tier, the user-data directories, and the measurement behind every rule below." | one of the trigger items, which the rewritten line names as a class |
| `, through its own PR` | "the retirement lands as an edit to this paragraph, through its own PR" | that an edit to a skill is a commit; no run turns on it |
| `Only a firing the trigger allowed counts as that evidence.` | its own sentence, folded into the one before it as "A firing **the trigger allowed** that returns nothing runnable" | nothing: the same guard, in the sentence it guards |
| `, who reviews the receipt` | "the wrap-up gate shows it to the user, who reviews the receipt" | what a reader does with what they are shown |
| `— the binary, the fixture, the file —` | "Run the artifact — the binary, the fixture, the file — on inputs you build from the real population it will meet." | three instances of *artifact*, in a brief whose every other line names none |
| `; the slice stays implemented, unreviewed, unmerged` | "One that does not fit waits whole, as a queue item heading the next window's review line; the slice stays implemented, unreviewed, unmerged." | the consequence of *waits whole* |

## 8. Rewordings, carrying no verdict

Fourteen sentences were reworded and none was removed. Nine are one sentence split in two to
bring a unit under the 25-word ceiling:

| before | after |
|---|---|
| "is reviewed by the mandatory review alone, in one round, with one exception: when the changed paragraphs prescribe commands, one lens may fire" | "takes the mandatory review alone, in one round. One exception: where the changed paragraphs prescribe commands, one lens may fire." |
| "The exception's brief adds two constraints to §2's block: report only findings…" | "The exception's brief adds two constraints to the block in `BRIEF.md`. Report only findings…" |
| "A firing that returns nothing runnable retires the exception: the parent says so in the PR body, and the retirement lands as an edit to this paragraph" | "A firing the trigger allowed that returns nothing runnable retires the exception: say so in the PR body, and edit this paragraph." |
| "Everything else the slice carries is the lens's… A docstring some program consumes (generated help, a parser) is read by a program, so it is the lens's too." | "A docstring a program consumes — generated help, a parser — is the lens's. So is everything else the slice carries, its identifiers and the strings a run emits alike." |
| "at the slice's **base**: the branch point of the work item, so a rewrite split across PRs measures as one rewrite" | "at the slice's **base**: the branch point of the work item. A rewrite split across PRs then measures as one rewrite." |
| "confirm `<base>` resolves before anything else" | "confirm `<base>` resolves first" |
| "Fire **one** subagent… at `effort: "high"`. Where no site names one, the parent's own model is the tier." | one sentence, joined at a semicolon |
| "**system** is the default: a slice matching two rows, or none of them cleanly, takes it." | folded into §2's paragraph as "Pick the angle from the slice's class, `system` by default: a slice matching two rows, or none of them cleanly, takes it." |
| "not this slice's: carry it to the item or the ticket" | "not this slice's. Carry it to the item or the ticket" |
| "When the run is the wrong side, it is a code defect. When the code is right and only the words are stale, it is prose, fixed on the spot like a nit." | "A wrong run is a code defect; stale words are prose, fixed on the spot like a nit." |
| "**The correction batch goes to the repo's mandatory two-axis review, never to another lens.**" | the full stop moved outside the bold, so the sentence splits: "**…never to another lens**." |
| "**A repeated mechanism is a design signal.**" | "**A repeated mechanism is a design signal**." — same reason |
| "**The lens and the review of its correction batch may not cost more window together than the implementation they review.**" | "**…than the implementation they review**." — same reason |
| "the artifacts are the proof of work, and an empty or one-line inventory is a failure" | "the artifacts are the proof of work. An empty or one-line inventory is a failure" |

The last three are the same mechanical cause: the bin's sentence splitter needs whitespace after
the full stop, so a sentence ending `.**` is measured joined to the one after it. Moving the full
stop outside the bold separates them without changing a word or the emphasis.

## 9. One unit added, not removed

`SKILL.md`'s site-extensions line was three sentences and now is one, in the form `verify`,
`dispatch`, `kickoff` and `wrap-up` all carry — a pointer at the README's own section rather
than a restatement of the contract. It has no row in the report's table, which rules on the
original's units.
