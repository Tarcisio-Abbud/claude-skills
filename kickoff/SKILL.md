---
name: kickoff
description: "Session opening — mirror of /wrap-up: gathers the project's pending items, verifies each against reality, triages and dispatches the ones the user checks in the menu"
disable-model-invocation: true
---

A **kickoff** opens the session that `/wrap-up` closed: it builds the **agenda** of the
project's pending items, checks what is still real, triages item by item and **dispatches**
what the user checks. Execute the steps in order; each ends on a checkable criterion.

(Global version — applies to any project. If a project has its own `.claude/skills/kickoff`,
that one overrides this.)

## 1. Gather the agenda

Sources, in this order:

- **`next-steps.md`** in the project's auto-memory (dir `memory/`; the `MEMORY.md` index is
  already in context) — the canonical queue, contract at the end of this file. If it doesn't
  exist yet (project's first kickoff), fall back to the memory files the index flags as
  having pending/NEXT/waiting/idea items.
- **Open issues and PRs** on the repo (`gh issue list`, `gh pr list`), when there's a
  tracker — including any open **wayfinder map** (label `wayfinder:map`): its frontier
  tickets (open, unblocked, unclaimed) are agenda items.

Wiki and repo docs are NOT agenda sources — volatile state doesn't live there; a pending
item found there is stale doc, not queue.
**Done when:** there is a single list of candidate items, each with its source.

## 2. Verify against reality

Memory reflects the moment it was written. Before any item enters the agenda, check the
current state: is the PR still open? did a commit/merge already resolve it? did the issue
close? does the cited file/flag/script still exist? (`gh pr list`, `gh issue view`,
`git log`, read the code). An already-resolved item leaves the agenda AND the memory citing
it is fixed ON THE SPOT — don't leave it for the next wrap-up.
**Done when:** every remaining item is confirmed genuinely open and no known-stale memory is
left uncorrected.

## 3. Triage

Each item gets exactly ONE class:

| Class | Criterion |
|---|---|
| **AUTONOMOUS** | well-specified; an agent executes it without the user |
| **DECISION** | missing a user choice; once decided, becomes AUTONOMOUS |
| **BLOCKED** | depends on data/action/credentials only the user has |
| **EXTERNAL** | waiting on a third party; at most chase/remind |
| **RECURRING** | not a one-off item — should become a scheduled routine |

An AUTONOMOUS item that is already an agent-ready ticket on the tracker (from `/to-tickets`,
`/triage`, or a wayfinder frontier) has its dispatch pre-made: `/implement`, one ticket per
fresh session. An item too big and foggy to triage cleanly — a whole effort, not a slice —
isn't forced into a class: propose charting it with `/wayfinder`.

**Done when:** every pending item has a class and, if actionable, a recommended dispatch
from the `dispatch` skill's palette (step 5).

## 4. Build the menu

Before asking, show the **full triaged agenda** — ALL items, one line each, with class — so
the user sees nothing was lost before checking (BLOCKED/EXTERNAL show up here; their detail
waits for the final report).

Then one multiSelect `AskUserQuestion` with the actionable items (AUTONOMOUS + RECURRING)
prioritized by impact/urgency, recommendation first with "(Recommended)". DECISION items
become their own questions — the options are the choices themselves, not "yes/no". Tool
limit: 4 questions × 4 options; what doesn't fit becomes a line in the final report, not an
option. BLOCKED and EXTERNAL are never options.
**Done when:** the whole agenda was shown and the user's selection is captured.

## 5. Dispatch

The menu check IS the authorization — execute in sequence, without re-confirming. The
task→mechanism matching (palette), the `/goal` recipe, the mechanism boundaries and the
`loop.md` contract live in the `dispatch` skill: read
`/root/.claude/skills/dispatch/SKILL.md` before the first dispatch. Dispatches that are
user-native commands (`/goal`, `/implement`, `/wayfinder`, workflow) don't block the flow —
they enter the final report as ready-to-paste lines.
Close with: (a) what is running/scheduled, (b) BLOCKED items with what's missing from the
user, (c) EXTERNAL items with who to chase — and rewrite the resulting queue to
`next-steps.md`.
**Done when:** every checked item is running or scheduled, the report covers (b) and (c),
and `next-steps.md` reflects the post-kickoff queue.

## The `next-steps.md` contract

Single source for a project's queue of pending items. Lives in the project's auto-memory
(`/root/.claude/projects/<cwd-slug>/memory/next-steps.md`, with a pointer in `MEMORY.md`)
and is updated by ANY session where a pending item is born or dies — `/wrap-up` guarantees
it at close; `/kickoff` rewrites the verified queue at open.

```markdown
---
name: next-steps
description: canonical queue of the project's next steps — consumed by /kickoff
metadata:
  type: project
---

# Next steps

- [ ] <concrete action> — one-line context. **Class:** AUTONOMOUS. **Source:** PR #12, 2026-07-01
```

Rules: one item per line; absolute dates; a resolved item LEAVES the file (no
strikethrough); the recorded class is the writer's guess — kickoff always re-verifies and
re-triages. Tickets already published on the issue tracker are referenced, not mirrored —
the tracker is their source of truth.
