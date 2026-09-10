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
  LOAD is inlined as `data:` or written out. **A vista carries no script** — collapsibles are
  `<details>`, themes a media query, drawings inline SVG — because a page that runs code can
  fetch in a hundred spellings, and none of them is worth the reading.

`vista-template.html`, beside this file, is that page in its smallest form — copy it, fill it,
restyle it. `../bin/tk-vista-check` is the gate below.

**The baseline is a styled report**: a static page, well laid out, with collapsibles and links —
what the template already gives. An explorable or isometric map is an on-demand capability the
user asks for by name, never what a package close produces.

## When a vista is written

| Occasion | Who writes it |
|---|---|
| Unattended package close (`/tk:wrap-up afk` closing an afk package) | nobody yet — **held back**, below |
| A consolidated report across projects | `../skills/fleet/SKILL.md`, by default |
| Any session where the user asks for one ("give me the view of this") | that session |

The second row is why this contract sits in `reference/` instead of inside the wrap-up's
`SKILL.md`: **the consolidated reporter reads this same file**, and the five blocks are one
contract, not two copies drifting apart.

**The consolidated reporter is `../skills/fleet/SKILL.md`**, and its closing step is the second
row above: a fleet run writes one vista across every project it swept, by default and without
being asked.

**The first row is still held back.** A package small enough to read in the digest does not earn
a page, and judging that belongs to the reporter that sees several projects at once, not to the
wrap-up. So outside a fleet run, a session writes a vista only when it is asked for one.

A wrap-up closes on the textual report alone. The vista answers the case where a human judges
several PRs at once; for a single PR the digest is faster.

## Where it lands

The outbox is where it goes, by default and without asking: the machine's **outbox** is the
directory it exports to the user, and the file is `<outbox>/vista-<package>-<YYYY-MM-DD>.html`.
A package has no id of its own, so `<package>` is the name the session already calls it by — the
anchor item's id (`T139`) for a package built around one, otherwise its first item's id, and the
campaign's name where the user gave it one. A **fleet run** has neither anchor nor first item —
it is one run over many queues — so its slot takes the literal `fleet`.

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
| 1 | Stats line, at the opening | `data-vista-bloco="stats"` | the closing template's own four counts — closed · carried · blocked · discarded, which never sum with each other — plus whatever else the run earned (open PRs, tests). Across several projects each count is the sum of that count over them, and the line says how many queues it covers |
| 2 | One card per PR or item, grouped by outcome | `data-vista-bloco="cards"` on the region; `data-vista-card="<id>"` and `data-vista-desfecho="<outcome>"` on each card | what the slice delivered, in prose a reader who will not open the diff can judge |

**The outcome vocabulary is closed**: `merged` · `closed` · `open` · `carried` · `blocked` ·
`discarded`. The gate refuses anything else, because the CSS that colours a card knows only
these — a card carrying a seventh word renders grey and reads as unremarkable. Grouping headings
are prose and free; the attribute is not.

**A proof link is a real address.** The gate refuses a placeholder — an empty or `#` href, a
`FILL` marker still in it, or a reserved domain (`*.invalid`, `example.com/net/org`) — so a
close at 3am cannot ship a card whose proof was never filled in and still be called green.
| 3 | Risk tag, on every card | `data-vista-risco="<low\|medium\|high>"` on the card | what could still bite, in one clause |
| 4 | Link to that slice's proof | `data-vista-bloco="prova"` on an `<a href>` inside the card | the evidence block lives in the PR (`../skills/verify/SKILL.md`) and is pointed at, never copied or re-derived here |
| 5 | Closed × open balance | `data-vista-bloco="saldo"` | what left the queue against what is still in it, and what this run added to it. One queue for a package close; a consolidated run gives one row per project and a total row, since two projects' queues never merge into one number |

The marker words are Portuguese (`bloco`, `desfecho`, `risco`, `prova`, `saldo`) because they
are the decision's own glossary; the prose of a vista is written in the reader's language, and
its markers stay as they are here.

A card for a PR offered as merge carries the **five safe-to-merge verdicts** in its body —
tests, review, criterion, reversal, closure — one line each, marked
`data-vista-veredito="tests"` and so on. The checker does not require them: a card is a PR here and an item in a consolidated report,
and only the first kind has verdicts to give. It does require them **all or none** — a card
that gives any of the five gives the other four, each named from that closed vocabulary,
because a list of four reads as complete and the missing verdict is the one nobody checked. A
human reads them; a red one is named in the card.

**A type-B item is judged here, and answered elsewhere.** Its card carries the artefact and the
one-line claim it makes, since the verdict is the user's to give — and it gives that verdict
through the wrap-up gate, a menu or a PR comment. The vista never carries a control that
displays and decides at once: that is the defect the one-way rule exists to prevent.

## The variant for a cold reader

A package that runs unattended is judged later, far away, by someone who was not in the
session. **Remote Control is blind**: it shows no statusline and echoes no local command. So a
number the session had on screen reaches that reader only if this page carries it in TEXT.

This is a SHAPE, not a sixth occasion. When one of the occasions above writes a page for a run
its reader did not watch — a fleet run, or a long unattended package the user asked a page for
— that page carries the five sections below, the last of them the prohibition that closes
them. The five blocks do not change: the variant adds to them.

**1. Quota and context, in text, every number carrying its NATURE.** Paste the line
`../bin/tk-quota` printed and the count `../bin/tk-context` printed, never a percentage retyped
from either. A reading and a floor are different claims, and the reader tells them apart by the
bins' own words: a reading is `<n>% used`, with `(read <age> ago)` once it is stale; a floor
carries `estimate`, `at least`, and `floor from <n>% read <age> ago`. A number the writer
reasoned out instead of reading is marked as reasoned, in the same place, with the age of what
it was reasoned from. Four lines of the ledger of 06/09/2026 were written with the two
confused, and every rate computed off them was wrong by the same hour.

**2. The chronology, one line per event, out of the ledger.** The source is the package's own
ledger — the event line of `../skills/kickoff/LEDGER.md` — and never the writer's memory of the
run. The hour on the page is the hour that ledger read from `date`. A chronology recalled at
the end of a long package is the one thing on the page the reader can check against nothing.

**3. The measurement line, at LANE granularity.** The variant defines its own line, here:
**lanes planned × lanes completed × wall clock × peak agents**, the peak being the most
subagents alive at once. `../skills/fleet/SKILL.md` §6 prescribes a measurement line too, and
it counts PROJECTS — `projects planned × projects completed × wall clock` — with no word for a
lane; a package of thirteen lanes measured there reads one project against one project. Two
things the variant does inherit from §6, by POINTER and not by copy: what **planned** counts
(the dispatchable units with work, never the roster's own total) and that the clock starts at
the first dispatch, both read there in lanes instead of projects. Beside the measurement line
goes the **deviation line** per role, one per departure from the role table. That line is
already §6's, so the variant points there for its format and does not restate it.

**4. The untreated findings of every lane, in ONE section.** A defect a lane saw and did not
fix belongs to the package, not to the card of the slice that met it. Scattered across cards
each one reads as a footnote, and the reader who decides what happens to them cannot count
them. One line per finding, naming the lane it came from; a package that treated everything
says so in a line rather than dropping the section.

**5. What does not enter**, as in any vista, and it earns saying here because this page
travels: no company name, no account name, no internal content. The reader opens it on a phone,
over a link, off the machine that wrote it.

None of the five sections is a new marker. `tk-vista-check` reads the five blocks and this
variant hands it nothing more to read, so the sections are prose under free headings, in the
reader's language, and a variant page is green or red for the same reasons as any other.

## The gate

Run the checker on the file before naming it in any report, and treat a red run as a page that
was never written. The path is relative to THIS file — a session runs from the user's project,
where a `tk/` directory usually means something else:

```
../bin/tk-vista-check <path to the .html>
```

It fails on an external resource (a `src`, a `<link href>`, an `@import`, a CSS `url()` or
`image-set()` — the functions are where CSS fetches, so an address in a class name or in
generated text is prose — a relative path, an empty `src`), on any script at all (a `<script>`,
an `on*` handler, a `javascript:` or `vbscript:` URL read the way a browser reads it, a
`<meta http-equiv="refresh">`), on a missing block, on a card whose outcome is outside the vocabulary or which has
no risk tag or no real proof link, on a card that gives some of the five verdicts and not the
rest (or one outside their vocabulary), on text printed outside the `<body>` a page declared,
and on a page with no `prefers-color-scheme: dark` rule.

**A red gate does not hold the run.** The vista is a companion; the digest is the close. So a
run that gets a refusal keeps going and reports one of four states, never silence:

| Exit | State | What the report says |
|---|---|---|
| 0 | delivered | the path, called a vista |
| 1 | refused | that the vista was REFUSED, quoting the checker's findings; no line calls the file a vista |
| 2 | not checkable | that the file could not be read — a failed write, a path that is not a regular file — naming the path; there are no findings to quote |
| — | skipped | that no outbox was named, and which of the two lines is missing |

## What the gate does not measure

A green run means the five things above, and a report may claim no more than that:

- **Legibility.** The gate sees that the page ANSWERS the dark scheme, not that either palette
  is readable — `--ink` equal to `--bg` inside that block passes. Legibility is measured by
  RENDERING the file in both schemes before delivering it, which is a step, not a regex.
- **Block 1's content.** A `stats` marker around an empty list passes. The markers say where the
  blocks are; what is in them is the writer's.
- **Whether a card owes verdicts at all.** A card is a PR here and an item in a consolidated
  report, and only the first kind has verdicts to give, so a card giving none passes. What the
  gate refuses is a card that gives some of them.
- **Where a link leads.** `<a href>` is exempt by design and only the placeholder rule touches
  it. A link to the wrong PR is a green page.
- **One way.** That nothing is read back from a vista is a rule of the flow, held by prose here
  and by no mechanism. Nothing stops a future session from parsing one; the contract says do
  not, and the gate cannot say it.

One deliberate over-match sits beside these: an `on*` handler inside a `<template>` is inert and
still refused. Keeping it costs a page nobody writes; teaching the parser about inert subtrees
costs a branch that would have to stay right.
