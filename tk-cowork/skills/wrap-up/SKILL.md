---
name: wrap-up
description: "Wrap-up — close a Cowork session so nothing lives only in the conversation. Use when the user is closing, wrapping up or leaving a session, says they are done for now, asks what is still pending before stopping, or when another skill needs the session closed. Arg: afk (runs alone, no irreversible actions)."
---

A **wrap-up** leaves the project folder reflecting what this session did, so the next
session starts aligned. A close that leaves silent pendings is not a close. Execute the
steps in order; each ends on a checkable criterion, and every skip is stated.

**Argument:** `afk` — the user left; see the last section.

**The queue** is `next-steps.md` at the project folder's root. Read `CONTRACT.md` before
writing it — beside this file, or at the plugin root (`${CLAUDE_PLUGIN_ROOT}/CONTRACT.md`)
when this skill ships inside the `tk-cowork` plugin. The fields, the ID rule and the size
ceiling live there.

**Cloud session?** The project folder is unreachable when no local folder is mounted. Say
so in step 1 and switch to **report mode**: every write below is delivered as text for the
user to paste.

## 1. Inventory the session

List, in one pass and before going deeper:

- **files** created or changed in the project folder, one line each on what changed;
- **decisions and facts** from the conversation — what the user chose, what was discovered,
  what was ruled out;
- **irreversible actions** already taken (email sent, document shared, task created in a
  connected tool) and the ones still pending;
- **external waits** — who owes an answer, an approval, a file.

The inventory drives the rest: no file changed → step 2 shrinks; nothing irreversible
pending → step 4 is one line.
**Done when:** every file touched this session, every decision taken and every pending
action appears in one list the user has seen.

## 2. Update the project's documents

Land the session's durable knowledge in the project's own files: the reference documents,
the README or index, the decision log, the spreadsheet or deck the work produced. A
decision that changes how the project works belongs in the document that describes it — the
queue holds pending actions, never knowledge. Correct, in the same pass, any statement this
session contradicted.
**Done when:** every durable fact from step 1 lives in a project file, or was declared
ephemeral out loud.

## 3. Check the deliverables

For each artifact a human will open — document, spreadsheet, presentation, report: it sits
in the project folder, its name makes it findable, and it holds the version the user
approved. A file left mid-edit is named as a draft.
**Done when:** every deliverable is in place and named, with any draft flagged as such.

## 4. The gate

Settle here every action that leaves the project folder — email to send, document to share
or move, task to create in a connected tool, meeting to schedule, file to upload. These are
**irreversible**: once sent, the recipient has it.

Ask ONE multi-select question with those actions, recommended first — **the check IS the
authorization**. Execute what was checked. Every unchecked action enters the queue as a
`DECISION` item carrying what it needs to move: deferred by choice.
**Done when:** every irreversible action from step 1 was either executed under an explicit
check or written into the queue.

## 5. Write the queue

Rewrite `next-steps.md` per `CONTRACT.md`: open items only, resolved ones moved to
`## Concluídos` with the date and what resolved them, new pendings from steps 1–4 entered
with Class, Effort and Criterion filled. An item with no criterion is an item nobody can
close, so decide it here rather than leaving "done" to the next session's judgement.
**Done when:** every open item carries its three fields and no resolved item is still
listed as open.

## 6. Recommend the next step

Close with ONE recommendation in 1–2 sentences: start a new session on the top queue item,
keep going here, or stop. When it is a new session, **give 1–3 ready sentences to open it**,
so the user pastes and goes. Name any item crossing the session boundary — someone owing an
answer, an approval in flight.
**Done when:** the user has one recommendation, its why, and the opening sentences when the
path is a new session.

## The `afk` argument

`afk` — the user typed it and left. Steps 1–3, 5 and 6 run unchanged and **without a single
question**. The gate runs under a hard ceiling: **every irreversible action becomes a
`DECISION` item**, ready to fire on the user's return, and the session ends with the project
folder as the only thing it touched.
**Done when:** the documents and the queue are up to date and every irreversible action sits
in the queue.
