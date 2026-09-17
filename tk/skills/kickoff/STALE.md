# An item already resolved

An item is one author's claim about the tree, not the tree. It ages in the queue while the fix
arrives from another front. `AFK.md` step 3 sends every item that cites a code line here, before
that item's run is composed — the distillation is the second place the author's shallow read
enters, now with contract authority.

## The check

Open the cited line AND the two below it: the remedy sits one line down as often as on the line
named. Then date the last commit over those lines against the item's `**Born:**` in the queue
file.

```sh
git -C "<the item's repo address>" log -1 -L <line>,+3:<file> --date=short --format='%h %ad %s'
```

`+3` counts lines from the start, so `<line>,+3` is the cited line and the two below it.
`<the item's repo address>` is the clone the item's `**Repo:**` field names.

## Reading it

The three lines carry the verdict. The date only says which story to expect: a commit after
`**Born:**` is a fix that landed while the item waited, one before it a fix the author never
read.

## On a hit

Where the remedy the item asks for already exists, the item does not dispatch. Release its claim
— `tk-queue release "<id>" --dir "<queue dir>"` — and report it on step 6's already-resolved
rung, with the sha, its date and the line.

**Close nothing here.** A commit over the cited line is evidence, not the verdict. The item may
ask for more than the line carries, and `tk-queue done` over it is the user's call.

## What this cost

T151, measured 2026-09-03. The item named `open(..., encoding="utf-8")` in two bins as the
defect. The line immediately below already stripped the byte-order mark, committed the day
before the item was born, and the item then waited 14 days in the queue. The orchestrator greped
the same keyword, read the same single line, and spent a whole implementer discovering it.
