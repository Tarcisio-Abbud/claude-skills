# The vista — the digest's visual companion

A **vista** is one HTML page a human reads to give a verdict on a package: the stats, a card
per PR, the risk, the link to each proof, the balance. Three words fix what it is, and every
rule below follows from one of them.

- **View, not source.** The truth stays in the queue, the digest and the PRs. The vista
  presents them; deleting it loses nothing.
- **One way.** The human reads here and answers where they already answer — the wrap-up gate,
  the menu, a PR comment. Nothing is ever read back from this file, by any session.
- **Self-contained.** One file, no network: it opens from disk, on a machine that is offline,
  months later. Links a human CLICKS are the point of block 4 and stay; what the browser would
  LOAD is inlined as `data:` or written out.

`vista-template.html`, beside this file, is that page in its smallest form — copy it, fill it,
restyle it. `../bin/tk-vista-check` is the gate below.

**The baseline is a styled report**: a static page, well laid out, with collapsibles and links —
what the template already gives. An explorable or isometric map is an on-demand capability the
user asks for by name, never what a package close produces.

## When a vista is written

| Occasion | Who writes it |
|---|---|
| Unattended package close (`/tk:wrap-up afk` closing an afk package) | the wrap-up, by default |
| A consolidated report across projects | its own skill, by default |
| Any session where the user asks for one ("give me the view of this") | that session |

The second row is why this contract sits in `reference/` instead of inside the wrap-up's
`SKILL.md`: **a later consolidated reporter reads this same file**, and the five blocks are one
contract, not two copies drifting apart.

An ordinary wrap-up closes on the textual report alone: the vista answers the case where a
human judges several PRs at once, and one PR is read faster in the digest than in a page.

## Where it lands

The outbox is where it goes, by default and without asking: the machine's **outbox** is the
directory it exports to the user, and the file is `<outbox>/vista-<package>-<YYYY-MM-DD>.html`.
Two places name that directory, and the reader takes the first that answers — the machine's own
instruction file (`CLAUDE.md`/`AGENTS.md`, which normally states where deliverables go), then
the site extension `~/.claude/tk/wrap-up.md`, under a line reading `outbox = <absolute path>`.

A machine where neither names one gets a report saying the vista was skipped and which of the
two lines is missing, rather than a page written where nobody will look. Publishing it anywhere
else — an Artifact on claude.ai, a gist — happens when the user asks in that session, since a
vista carries names, numbers and forge links.

## The five blocks

The layout is free and the markers are fixed, so a checker finds the blocks without knowing
the design. Every marker is a `data-vista-*` attribute, and `tk-vista-check` reads only these.

| # | Block | Marker | What fills it |
|---|---|---|---|
| 1 | Stats line, at the opening | `data-vista-bloco="stats"` | slices, merged, open PRs, findings, tests — the counts the reader wants before anything else |
| 2 | One card per PR or item, grouped by outcome | `data-vista-bloco="cards"` on the region; `data-vista-card="<id>"` and `data-vista-desfecho="<outcome>"` on each card | what the slice delivered, in prose a reader who will not open the diff can judge |
| 3 | Risk tag, on every card | `data-vista-risco="<low\|medium\|high>"` on the card | what could still bite, in one clause |
| 4 | Link to that slice's proof | `data-vista-bloco="prova"` on an `<a href>` inside the card | the evidence block lives in the PR (`../skills/verify/SKILL.md`) and is pointed at, never copied or re-derived here |
| 5 | Closed × open balance | `data-vista-bloco="saldo"` | what left the queue against what is still in it, and what this package added to it |

The marker words are Portuguese (`bloco`, `desfecho`, `risco`, `prova`, `saldo`) because they
are the decision's own glossary; the prose of a vista is written in the reader's language, and
its markers stay as they are here.

A card for a PR offered as merge carries the **four safe-to-merge verdicts** in its body —
tests, review, criterion, reversal — one line each, marked `data-vista-veredito="tests"` and so
on. The checker does not require them: a card is a PR here and an item in a consolidated report,
and only the first kind has verdicts to give. A human reads them; a red one is named in the
card.

**A type-B item is judged here, and answered elsewhere.** Its card carries the artefact and the
one-line claim it makes, since the verdict is the user's to give — and it gives that verdict
through the wrap-up gate, a menu or a PR comment. The vista never carries a control that
displays and decides at once: that is the defect the one-way rule exists to prevent.

## The gate

Run the checker on the file before naming it in any report, and treat a red run as a page that
was never written. The path is relative to THIS file — a session runs from the user's project,
where a `tk/` directory usually means something else:

```
../bin/tk-vista-check <path to the .html>
```

It fails on an external resource (a `src`, a `<link href>`, an `@import`, a CSS `url()`, a
relative path, a network call in script), on a missing block, on a card with no outcome, no
risk tag or no proof link, and on a page with no `prefers-color-scheme: dark` rule. That last
one is why the template defines its palette as tokens twice: the reader's browser picks the
theme, and both have to be legible.
