# The merge dossier — the decision, resolved at the point of reading

> **Why it is not called a briefing.** The ticket that ordered it says *briefing de decisão de
> merge* (`homeserver-ambiente#157`), and inside this plugin `briefing` already names something
> else: the five-field handoff file `tk-queue handoff` writes, in 43 places in that script
> alone. One word over two objects reads as ordinary context and misleads quietly, so the
> merge artefact takes its own name. The ticket's word is not wrong; it is taken.

A **merge dossier** is the text a human reads to decide one merge. It is written before the
merge is offered, and it exists because a trail can be complete and still undecidable.

The case it was cut from: a reviewed PR, its verdict comment, and the issue both were written
against. Everything the decision needed was recorded. The verdict said "recommendation 1,
corroborated 3/3" and the sentence that names lived in the issue; the issue's own comments
renumbered it twice. The reader — who had already read all of it — still could not say what was
being proposed. Four artefacts, pointers crossed by number, nothing resolved where it was read.

So the dossier's whole job is **resolution at the point of reading**. It quotes, it never
refers. Where it cannot resolve, it says so in the same breath — an unresolved pointer named as
unresolved is a fact the reader can act on, and a pointer quietly dropped is the same wall
again with better manners.

Three words fix what it is, and every rule below follows from one.

- **Resolved.** No number stands alone. Every "recommendation 4", "item 3", "criterion A" the
  trail cites arrives with the sentence it names beside it.
- **Decision-shaped.** Proposal, verdict, what changes, and what is still a guess — never the
  record of what was done, which is the digest's.
- **Honest about its gaps.** A pointer that does not resolve, a trail that does not exist, a
  collision that could not be measured: each is stated. Nothing here is inferred to fill a hole.

## Where it fits, and where it does not

| Object | Question it answers | Owner |
|---|---|---|
| The **digest** | may this merge happen? — the four safe-to-merge verdicts | `../skills/wrap-up/SKILL.md`, step 5 |
| The **dossier** | what am I merging, and what changes if I do? | this file |
| The **proof** | did the item's criterion pass? | `../skills/verify/SKILL.md`, in the PR body |
| The **package view** | the same close, as a page a human reads | a separate slice (`homeserver-ambiente#134`); its own file owns its markers |

The digest gates and the dossier informs. They are printed together, dossier first: a reader
decides on the content and confirms on the verdicts, never the reverse.

**A view that carries a per-PR card writes that card FROM the dossier**, and the two are not
the same size. A card's visible body is two or three sentences — the dossier's lede — its
collapsibles carry whichever sections a reader of that page needs, and the full text stays in
the PR the card's proof link already reaches. The view's own file owns the markers, the layout
and the card's outcome vocabulary; this file owns what the card SAYS. Neither re-derives the
other, and a card whose body was invented beside an existing dossier is two answers to one
question.

## The five sections

Every section is written for a reader who will not open the diff. The order is fixed; a section
with nothing in it says that, and is never dropped.

| # | Section | What fills it |
|---|---|---|
| 1 | **Pointers resolved** | every number the trail cites, with the sentence it names and the address it was read from; every pointer that did not resolve, named, with the reason |
| 2 | **Proposal → verdict → why** | one row per decision: what was proposed, what was decided, and — where the evidence contradicted the proposal — which of the two won |
| 3 | **Before and after, in practice** | what the rule or the code did, and what it does from this merge on, side by side |
| 4 | **Choices without data** | the author's own declarations of uncertainty, gathered from wherever they were scattered into one place |
| 5 | **Merge mechanics** | the files, the size, and whether this branch can land beside the other open PRs |

Section 3 is the one a reader singles out, so it is written concretely: a line the rule used to
produce against the line it produces now, an input that used to pass against one that now
fails. "Improved the gate" is not a before and after.

Section 4 is a **gathering, not a judgement**. Its material is already in the trail — the
author wrote "choice without data" or "unmeasured" somewhere — and the dossier's contribution
is putting all of it in one place, where a reader can weigh it at once instead of meeting it
line by line.

## The two sections that are measured

Sections 1 and 5 are not written from memory. `tk-dossier` measures them.

**Where the script is.** Every path in this file is relative to THIS file, and a session runs
from the user's project, where `tk/` usually means something else. So resolve
`../bin/tk-dossier` against the directory holding `dossier.md` and use the resulting ABSOLUTE
path in every command below. Run as written from a session's own working directory, the lines
below fail with a shell's `No such file or directory` and exit 127 — which is not one of the
three codes this script promises, and is the sign you skipped this paragraph.

**The three exit codes** are 0 nothing is outstanding that the script itself can decide, 1 the
answer carries something this dossier must state, 2 the run did not happen. A 0 still has to be
READ: an `also` line rides on a resolved pointer and no exit code can carry it, because a trail
whose sources genuinely overlap would then never reach 0 at all. On 2 the script names what it could not read or reach on
stderr; fix that and run again, and where it cannot be fixed, section 1 or 5 says the
measurement was not made rather than going silent.

**Section 1 — the pointers.** Fetch the citing texts and the source texts first, one file each,
with the forge CLI the session already runs. The source order is the trail's order: the
artefact the numbers were written against comes first.

```
gh api repos/<owner>/<repo>/pulls/<n> --jq .body                 > pr.md
gh api repos/<owner>/<repo>/issues/<n> --jq .body                > issue.md
gh api repos/<owner>/<repo>/issues/<n>/comments --jq '.[].body'  > comments.md
<abs>/tk/bin/tk-dossier pointers --citing pr=pr.md \
      --source issue=issue.md --source comments=comments.md
```

Read its answer into the section verbatim — resolved pointers with their sentences, unresolved
ones with their reasons. **A pointer is resolved by hand or reported as unresolved**: the
reader is told which artefact was searched and what was not found there, and can go look. Two
things commonly cause one and both are repairable — a source that was never passed (the rule,
the spec, a sibling issue), and a source order that is not the trail's, which the `also` line
under a binding warns about.

**A resolved pointer can still carry an `also` line, and it goes into the section.** Two
sources both holding a list of the same family is a choice the script made for you — it took
the first one given — and the `also` line is the only place that choice becomes visible. Copy
it beside the statement, or reorder the sources and run again until no pointer carries one. A
run that ends 0 with an `also` line standing is not a clean section 1; it is a section 1 whose
reader must be told which artefact the sentence came out of.

**The vocabulary is a limit, not a promise.** A citation whose noun the script does not carry
is not reported as unresolved — it is not reported at all, and no scan replaces reading. So the
empty answer never claims the text cites nothing: it says nothing matched THE VOCABULARY, which
is the only claim a word list can make. `--noun <word>,<plural>` extends it when you know the
trail numbers under another word.

An earlier design did try to guess those words, by watching for citation shapes under nouns
that label a list in some source. It was cut, measured against real trails: `como 4` in "quero
safe-to-merge como 4 vereditos" was offered as a pointer and, with the remedy it printed, bound
confidently to an unrelated sentence. Refusing to guess is recoverable and a wrong binding is
not, which is the whole premise this file opens with.

**What the harvest does not find**, so that section 1 never reads as exhaustive when it is not:
a noun outside the vocabulary above; a noun and its index separated by anything but a space or
an ordinal marker ("o item que disparou foi o 5"); an index that is a lowercase letter or
parenthesised ("critério (b)"); an index written as a word ("o quinto item"); and a
section-numbered heading, which is not read as an enumerated list, so a trail whose steps are
`## 3. Title` answers no pointer at all. Each of those is read by a human or not at all, and
section 1 says which ones it met.

**Section 5 — the mechanics.** The files and the size come from the diff. The collision comes
from merging the branches for real:

```
<abs>/tk/bin/tk-dossier collisions --repo <dir> origin/<branch-a> origin/<branch-b> ...
```

**Never from the forge's `mergeable`/`mergeStateStatus`.** That field compares one branch with
the default branch and knows nothing of a second open PR, so several PRs rewriting one
paragraph all read green and the second to merge breaks. Naming a colliding pair does not avoid
the conflict; it decides which PR pays for it, which is a thing the reader can choose.

## A PR with no trail

A commit pushed straight to a branch, with no issue behind it, still gets a dossier — a
**degraded** one, which says at the top that it is degraded and why. It is not an empty
dossier, and it is never filled in from what the branch seems to be about.

| Section | Degraded to |
|---|---|
| 1 | run the script with `--citing` and no `--source`, and copy what it says: every pointer unresolved, each reason ending `was found in no source at all`, or — where the PR cites no number the vocabulary carries — the line saying nothing matched that vocabulary. Never a sentence claiming the PR cites nothing |
| 2 | one row per commit: what it changed, against what the commit message claims it is for. Where the message gives no reason, the row says the reason is unrecorded — never a reason read off the diff |
| 3 | written from the diff, which is a real source for this section |
| 4 | "none declared" — an author who declared no uncertainty declared none; the dossier does not go looking for it in the code |
| 5 | unchanged: files, size and collisions are measured from the repository, and a missing trail costs them nothing |

The value of the degraded dossier is exactly that it is visibly thin. A PR whose section 2
reads "the reason is unrecorded" is telling the reader something true about how it was made.

## What a dossier does not do

- **It does not decide.** The verdict is the reader's, given where they already give it: the
  gate's menu, a comment, a reply. A dossier that ends in a recommendation to merge has
  answered the question it was written to pose.
- **It does not measure review quality.** Whether the findings were fixed is verdict 2 of the
  digest, and it is measured there.
- **It does not judge a pointer it could not resolve.** "Probably recommendation 1" is the one
  sentence that must never appear in section 1.
