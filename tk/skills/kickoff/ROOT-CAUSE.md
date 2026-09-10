# The root-cause audit — the cut, before `tk-queue pack`

Read from step 1 of `AFK.md` beside this file, before the first `pack`, on a body of work too
big for one package. It decides the **cut**: which items are still real, which are one item
said twice, and which lanes can run at once. `AUDIT.md` beside this file is the later step and
a different question — it audits the spec and the ticket TEXT after step 3's claim, while this
one audits the QUEUE against the code, with nothing claimed yet and no run fired.

**The threshold.** The audit runs when the queue offers **more than 20 eligible candidates** to
`pack`, counted AFTER the import below — that import is not gated by this number, so the tickets
it exists to surface are inside the count that fires the audit; at or below 20, step 1's own cut
stands. The number is DERIVED, not measured: the one
run there is (05–07/09/2026) read 110 items in ~40 min and returned 12 disjoint lanes, where
the package that skipped it would have opened ~78 pull requests into the same files. A package
fits 3–6 items, so 20 is about four packages deep — where 40 minutes starts buying more than
it costs. The next run that measures the audit replaces this derivation with its number.

## The tracker import comes first

`tk-queue pack` reads the QUEUE and nothing else, and the wave audit of `AUDIT.md` only fires
over a package. On 2026-09-08 the eight tickets of one spec sat outside the root queue: no
package ever saw them, and the audit never fired. So the import runs before the audit reads
anything and before the threshold above is counted, whatever that count would have been.
Every ticket of the tracker that is `ready-for-agent`, names a spec as its **Parent**
and has no item in the queue becomes an item:

```sh
tk-queue add "<the ticket's title in one line>" --dir "<queue dir>" --class AUTONOMOUS \
  --effort "<S, M or L with its clock guess>" --criterion "A: <the command that proves it>" \
  --spec "<repo>#<n>" --ticket "<repo>#<n>" --repo "<the clone the code lands in>"
```

Written in the lane's dependency ORDER, and with **no `--blocked-by` between siblings**: the
lane is serial and runs in that order anyway, while `--blocked-by` would make `pack` leave
every blocked sibling out of the package (`tk-queue add --help`; the ledger
`blocked-by-na-fila`). `--spec` and `--ticket` take `<repo>#<n>` and refuse `owner/repo#n`. That
half is the TRACKER's, not the code's, and a mismatch with the clone `--repo` names is refused
(the same help).

The `add` belongs to the ORCHESTRATOR and to no subagent: the site's hook refuses an `add` from
inside a subagent, and while a package runs the orchestrator alone writes the queue (`AFK.md`).
These items MIRROR tickets that already exist, so they are not items being born and no menu is
owed for them. With them in the queue, `AUDIT.md`'s step fires by construction.

## The five lists the audit returns

Every list is verified against the CODE, never against the item's own text: the item says what
somebody wanted, the tree says what happened. Each candidate lands in exactly one list.

- **Already done on main**, each with the sha that did it. The check is `SKILL.md` beside this
  file, step 2 (*Verify against reality*) — this file points at it and does not restate it.
  Five of the 110 were already on main.
- **Dead by redesign**, naming the item that kills it. Verified by opening the KILLER's ticket
  and finding, in the clone, the file it replaces:
  `git -C "<the item's repo>" grep -n "<the anchor the dead item edits>" -- "<path>"`. Nine of
  the 110 died, all nine to one item.
- **Fusions**, `edit` before `cancel` — the section below.
- **Disjoint lanes, by FILE and not by theme.** Two items touching one path are one lane
  whatever they are about. The paths come from each ticket's own **Arquivos** line and are
  confirmed in the tree with `git -C "<the item's repo>" ls-files "<path>"`, never assumed.
- **Out of the cut**, each item with its reason: `pack`'s own exclusion value where it has one,
  and the answer of step 1's `git ls-remote` where the reason is a lane already under way.

## Fusing two items: `edit`, then `cancel`

```sh
tk-queue edit "<survivor id>" --dir "<queue dir>" --text "<the union of the two texts>"
tk-queue cancel "<source id>" --dir "<queue dir>" --why "<fused into the survivor>"
```

The inverse order LOSES the text. The two commands are not one transaction, and the 700-char
block ceiling can refuse the edit that carries the union; cancelled first, the source's content
is already out of the queue when that refusal arrives and there is nothing left to paste —
measured three times in the consolidation of 2026-09-02. The order is implemented and proved
already: T341 (PR #88, `fab0646`) put the step in `../wrap-up/SKILL.md` with
`../../tests/test_wrap_up_consolidation.py` holding it, and T340 (PR #90) made
`tk-queue cancel --help` say it. This file cites those two; it is not a third copy of the rule.

## The two topology rules

- **Stacked pull request** — fires when two lanes need the same FILE. The second lane branches
  from the first lane's branch, never from `main`, and its pull request targets that branch.
  Both file collisions of the 05–07/09 run took this shape: L2 over L1, and the two pull
  requests of the redesign.
- **The last lane of a repository is born from the UNION of the others** — fires when a lane's
  work is about the FINAL tree: counts, inventories, a sweep, anything whose right answer is
  only right once the other lanes have landed. It branches from the merge of that repository's
  other lanes, and that clean merge is the repository's collision test. `gh`'s own MERGEABLE
  cannot stand in: it is computed pair-by-pair against `main` and is blind between two open
  pull requests (ledger `gh-mergeable-e-cego-entre-prs`).

## chain, parallelize, route

These three name the GRAPH SHAPES the cut returns and nothing else here — the *field chain* of
`../../reference/queue.md` is a different chain, and "route" in the neighbouring files means a
path a reader takes.

- **chain** — lanes that share a file, each stacked on the previous branch; the stacked-pull-
  request rule above is its trigger.
- **parallelize** — lanes disjoint by file, dispatched at once.
- **route** — each item to the lane its file set puts it in, and each lane to the role that
  runs it (`../../reference/subagent-policy.md` owns the role table).

**The cheap gate before the fan-out.** Before returning a set of parallel lanes, the auditor asks
of each one whether it is worth N+1 calls — the orchestrator's own, plus the run it dispatches —
and answers from the lane's FILE set, never from its theme. The cookbook names that cost as the
pattern's own limitation. An item whose files already sit inside a sibling lane is fused there
under *Fusing two items* above rather than given a run of its own, and a lane of one small item
that shares no file with any other is said in the cut to be worth its call, or dropped into the
lane it is nearest.

The decomposition is decided at DISPATCH time, out of the body of work in front of the auditor;
a cut fixed in advance is what this step exists to replace. What does NOT cross from the
cookbook the shapes are named after: **`n_workers=3` is not adopted** — it is the default of a
`ThreadPoolExecutor` in that page's `parallel()` helper, a Messages-API construct with no
measurement behind it here. How many lanes run at once is the site's `max-local-subagents`
(`~/.claude/tk/env`, read by `tk-contract`), and above that the quota window `WINDOW.md`
measures. `FlexibleOrchestrator`, `llm_call` and `extract_xml` do not cross either, and for the
same reason.

## Who runs it

One agent, on Opus at high effort, reading the whole body of work — the role is
`root-cause-auditor`, and `../../reference/subagent-policy.md` owns its row: where that row is
there, it is the source and the dispatch takes model, effort and venue from it rather than from
this line. The auditor RETURNS its queue writes as text and runs none of them, for the reason
the import section gives.

**Done when:** the five lists are back with every candidate in exactly one of them; each fusion
names its survivor; the lanes are disjoint by file or declared stacked; and the cut step 1
accepts is the cut this audit returned.
