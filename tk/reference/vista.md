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

## When a vista is written

| Occasion | Who writes it |
|---|---|
| Unattended package close (`/tk:wrap-up afk` closing an afk package) | the wrap-up, by default |
| Consolidated fleet report | the fleet skill, by default |
| Any session where the user asks for one ("give me the view of this") | that session |

An ordinary wrap-up closes on the textual report alone: the vista answers the case where a
human judges several PRs at once, and one PR is read faster in the digest than in a page.

## Where it lands

The vista is a deliverable — it goes to the site's **outbox**, the directory this machine
exports to the user, named by the machine's instruction file or by the site extension
(`~/.claude/tk/wrap-up.md`). The filename is `vista-<package>-<YYYY-MM-DD>.html`.

Where the site names no such directory, the package close reports the vista as skipped, naming
what is missing: a page the user cannot reach is worse than a report that says why there is
none. Publishing it anywhere else — an Artifact on claude.ai, a gist — happens when the user
asks for it in that session, since a vista carries names, numbers and forge links.

## The five blocks

The layout is free and the markers are fixed, so a checker finds the blocks without knowing
the design. Every marker is a `data-vista-*` attribute, and `tk-vista-check` reads only these.

| # | Block | Marker | What fills it |
|---|---|---|---|
| 1 | Stats line, at the opening | `data-vista-bloco="stats"` | slices, merged, open PRs, findings, tests — the counts the reader wants before anything else |
| 2 | One card per PR or item, grouped by outcome | `data-vista-bloco="cards"` on the region; `data-vista-card="<id>"` and `data-vista-desfecho="<outcome>"` on each card | what the slice delivered, in prose a reader who will not open the diff can judge |
| 3 | Risk tag, on every card | `data-vista-risco="<low\|medium\|high>"` on the card | what could still bite, in one clause |
| 4 | Link to that slice's proof | `data-vista-bloco="prova"` on an `<a href>` inside the card | the evidence block lives in the PR (`../skills/verify/SKILL.md`); the vista points at it |
| 5 | Closed × open balance | `data-vista-bloco="saldo"` | what left the queue against what is still in it, and what this package added to it |

A card for a PR offered as merge carries the **four safe-to-merge verdicts** in its body —
tests, review, criterion, reversal — because what answers them does not vary from session to
session. They are read by a human, not by the checker.

## The gate

Run the checker on the file before naming it in any report, and treat a red run as a page that
was never written:

```
tk/bin/tk-vista-check <path to the .html>
```

It fails on an external resource (a `src`, a `<link href>`, an `@import`, a CSS `url()`, a
relative path, a network call in script), on a missing block, on a card with no outcome, no
risk tag or no proof link, and on a page with no `prefers-color-scheme: dark` rule. That last
one is why the template defines its palette as tokens twice: the reader's browser picks the
theme, and both have to be legible.
