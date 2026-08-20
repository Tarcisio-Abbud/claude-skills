# Rules earlier slices paid for

Every rule below cost a real defect — one that shipped, or that a review caught after the
code was written and believed. They are the rules an implementer rediscovers the expensive
way, so they are handed over instead.

Read the section that matches what the slice touches. A rule earns its line by changing what
you do; none of them restates care you would take anyway.

## A command that writes to a file

**A write gate asks the block it WOULD WRITE, never the one it read.** Compose the new block
first, hand it to the same reader the rest of the code uses, and require that reader to give
back exactly what you composed. Every proxy question — "does the text still carry the marker?",
asked of the block as it arrived — passes while the write corrupts, because adding a field
moves the boundaries the reader uses. Three corrections in one slice asked the proxy and the
first round's bug outlived all three; the fourth composed first and it died.

**A field a command CLEARS is located by position, not by membership.** "It appears in the
chain" is true of prose that merely quotes the marker, and clearing on that answer eats the
user's words. Ask which segment the field occupies.

**Guarding the parse is not guarding the open.** A hand-written file reader meets a path that
is a directory, a byte that is not UTF-8, a byte-order mark glued to the first key, and a FIFO
that does not raise at all — it blocks, and the session stops with nothing on screen. Confirm
the path is a regular file, open with `utf-8-sig`, strip `U+FEFF` wherever it appears
(`str.strip()` leaves it), and catch `OSError` and `UnicodeDecodeError` beside the parse error.

**A command that deletes or overwrites inside a shared directory asks whether the file is its
own** — by a mark in the content, never by the name. A directory the command does not own holds
files that merely match its naming, and `os.remove` is the one direction where running it again
repairs nothing.

**A refusal names a remedy that is reachable, runs, and leaves the text intact.** A remedy that
is itself refused is a dead end; a remedy that is accepted, rewrites the file, and returns the
same refusal costs a write and fixes nothing. Quote values for the shell and print them whole —
a printed remedy built from a truncated title silently shortens what it repairs. The test is
always the same: run the printed remedy, then re-run the command.

**A new gate field closes the gate everywhere the package is built, in the same PR.** A field
that decides eligibility is a hole until the prose that assembles the work carries it too;
leaving that to the slice that owns the assembler leaves the window open between two merges.

**A correction that adds a category adds it to every step that enumerates categories.** The
step that reports is the one that gets missed, and an item that falls out of every bucket
disappears from the screen rather than raising anything.

**Derive the list that sits beside a completeness check.** A hand-kept list next to a check
that claims coverage is the next defect, twice measured — including inside the very mechanism
written to prevent that class of hole.

## Proving it

The fixture a criterion runs against decides what it proves — that rule lives with the gate
that runs it, in `../skills/verify/SKILL.md`.

**A command prescribed in prose is code — run it in a throwaway directory.** Prescribed lines
have shipped that no flag combination accepts, and a rewrite inherits every unrun command it
merely transported. Run the ones you carried over, not only the ones you wrote.

**Re-lens the correction commit.** When a second pair of eyes finds anything non-trivial, the
fix is new code that nobody has reviewed; pointing the lenses that found the defect back at the
commit that repaired it has caught a defect born in the repair five times running, including
regressions that a fully green suite reported as healthy.

## Prose an agent will read

**A derived cell says it is derived.** When a table cell has no ratified source and you reason
it out, write the derivation into the cell. A cell that reads as ratified is the one a review
cannot tell from a fact.

**A claim about a sibling skill is written as a requirement on the reader.** Describing what a
neighbouring file does asserts a future that file may not have reached; deleting the claim
instead retires a decision in silence. State what the reader must do, and say which file owns
the path — ownership while the material is still coming, a pointer once it is there. A pointer
aimed at a file that says nothing yet sends the reader to silence.

**Grep a candidate vocabulary word across the sibling files before electing it.** A word already
carrying a meaning here collides quietly: seeing the hits is not enough, since two disjoint
senses under one token read as ordinary context. Two slices independently reached the same
qualifier for the same collision, which is what a real collision looks like.

**A retraction applies at every site of the claim.** After withdrawing an assertion from a
paragraph, grep it across the whole file — the table three lines above kept saying the opposite.

**A loosened gate names who gives the verdict, and when.** A correction that relaxes a gate for
the interactive path turns it decorative on the path that runs most, and a checkbox silently
promoted to a verdict pre-recommends the very step the gate exists to hold.

**An artifact produced under the old rule says why it is still old, and what would leave it.**
Proposing an improvement while shipping work that predates it reads as a contradiction unless
the artifact dates itself.

## Before the PR

**`git remote -v` before believing the repo topology the prompt asserts.** Dispatch prose
carries the previous slice's premise through a copy-paste; it is harmless until it makes you
doubt the remote.

**Re-read the ticket's comments before opening the PR.** A sibling slice comments on your ticket
while you work, and a review that reads the ticket cold is the wrong way to learn it.
