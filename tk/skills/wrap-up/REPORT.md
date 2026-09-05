# The closing template

Read from step 6 of `SKILL.md`, before writing the close. Any skill that closes on the
wrap-up template reads it here too — the fleet's consolidated report takes block 1's four
counts from this file.

**Write the report for a cold reader** — someone who was not in this session. An
unattended run gives them no other window, so this report is where they learn what
happened. What they lack is context, not vocabulary: resolve every identifier on first
mention (`T41` arrives with what it is, never as a bare ID; an item that never reached
What changed resolves its identity on its own group line), name every artefact by what it
does before what it is called, and let every reference resolve from the report alone. An
unattended run walks its items one at a time, each from zero knowledge of the session.

The report follows this structure, and it is the structure that travels — a
response-style preference that disagrees with it loses:

```
**What changed**
- <item> — <what it is, in a few words>
  - was: <what the rule or the code did>
  - now: <what it does now>
  - gain: <the concrete gain it bought>  ·  risk: <what could still bite, in one clause>

**<N> closed · <M> carried · <K> blocked · <D> discarded**

**Sensor:** <births>/<merged PRs> = <ratio> · open <before> → <after>

**Closed** — everything that left the queue, FEITO or DESCARTADO alike
- <item> — FEITO
- <item> — DESCARTADO, <why>

**Carried**
- <item> — <the survival gate that kept it in the queue>

**Blocked**
- <item> — what is missing, and from whom

**Discarded** — session findings, which never entered the queue
- <session finding> — why it was dropped

**Blockers and notes for the next session:** <text — or "none", spelled out>

**Suggestions:** <what you would do next, if you have one — last, never mixed in above>
```

**What changed opens the report, and it retransmits.** One entry per DELIVERED item,
three lines under it — the risk clause rides the gain line where there is one — read off
the digest step 5 already wrote (its section 3, *Before/after in practice*, is literally
these lines), or off the work itself where the item closed without a PR. At an attended
gate the user has already read those lines in the terminal, before the menu, so this block
repeats them where the report keeps them; an unattended run's reader meets them here
first. The gain is concrete — "the queue can no longer lose a resolved item" beats "improved
the queue" — and an item that closed with no gain worth a line says exactly that on its gain
line, which is itself worth the line. A DESCARTADO item has no before and no after, so it
appears in Closed alone; a session that delivered nothing writes the header with "nothing
delivered" under it — an absent block reads as a block nobody wrote.

**The stats line follows, and its first three counts are the queue's balance**: what left it
against what is still in it. The fourth counts a different object — session findings
discarded in step 1, which never entered the queue — so the group is labelled and the two
are never summed. **The Sensor line under it is the afk close's** — `../kickoff/AFK.md` step
6 computes it, and a close that ran no package leaves it out. Discarding needs a user to do
it, so an unattended run reports no discards and carries its findings to the gates instead.
The outcome groups below are the balance and nothing more: each item with its outcome, and
the reason wherever the outcome does not carry it — the substance was already spent above.
Items group by outcome, never by chronology, and a group of three or more becomes a table
with those same columns — the What changed entries stay in lines, a cell being no place for
a before and an after.

**The blockers line is unskippable**: "none" written out is an answer, an absent line is
a rediscovery the next session pays for. It is also the one line of the report that must
survive the terminal — it lands in the affected item's text, and a blocker too big for
the item's size ceiling is itself the signal that the handoff file is due.

## The opening sentences

When step 6 recommends `/clear`, the report ends with 1–3 ready sentences to open the
next conversation, in two shapes chosen by what the sentence does:

- **Invokes a slash command** (`/tk:kickoff afk`, `/implement`, …) — the command leads
  the sentence alone, no prose before it, and does NOT name the project: `tk-queue` and
  similar resolve state from the session's `cwd`, so the project is carried by telling
  the user where to open the session — "open the session in the project's directory and
  type `/tk:kickoff afk` as the first line" — never by naming it inside the command line.
- **Describes a task, no slash command** — name the project by path or name in the prose:
  "in the project's directory, take T012", not "take T012". The next session may open
  anywhere (on the desktop it does not start in the project's folder), so a cold sentence
  that names no project points at nothing.

Site extensions may add flow-specific opening lines. Leaving rather than continuing,
close with the ready pair: `/clear` now, then open the next session in the project's
directory and type `/tk:kickoff afk` as its first line.
