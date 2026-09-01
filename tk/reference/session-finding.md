# The session-finding ladder

A **session finding** is work this session discovered and did not come for. The qualifier
is load-bearing: a code review's findings are defects in a diff, and this is the other
thing entirely. What tells a session finding from a **pendency** is the criterion of the
item in hand: work that item's `**Criterion:**` needs in order to pass is a pendency, and
it is resolved in the session. Everything else is a session finding, and a session finding
never inherits that default — that inheritance IS the **hydra**: three heads die and six
items are born, which is how a quick job became three weeks.

Consumers: `/tk:kickoff` (its `AFK.md` for the unattended form) and `/tk:wrap-up`. The
kickoff report's discard block, and the close's veto listing, are those skills' own.

## The ladder, with the user present

Every session finding is triaged at the moment of discovery, and with the user present the
triage is a menu (`AskUserQuestion`, which waits for them — a question in prose scrolls
away in the terminal's wall of text). Three outcomes, and the one that carries
"(Recommended)" is the first that holds, read in order:

1. **Resolve now** — leaving it breaks something already delivered: a live defect in what
   this session just shipped, data the user will read as correct, a command they will type
   as written.
2. **Queue with a gate** — someone will act on it later and it has a gate to name: human
   decision · effort · external dependency. `tk-queue add` on the spot, gate in the item.
3. **Discard** — neither of the above holds. Nothing is written: the finding's whole trace
   is its one line in the session report's discard block. A discard that deserved more
   than one line was not a discard.

The ladder recommends and the user picks; their pick IS the authorization, including for a
resolve-now the ladder had placed third.

## The ladder, unattended

The ladder needs the user: nobody answers the menu, and both the discard ("this will never
happen") and the resolve-now (the hydra's own fuel) are judgements that belong to them. An
unattended session has ONE rung: **queue with a gate** — `tk-queue add` at the moment of
discovery, the gate named in the item's own text, and a finding only the user can judge
entering as a DECISION carrying `--deferred afk`.

So an unattended session reports no discards and resolves nothing on the spot. Every
finding it queued is listed in its close under the gate that kept it, for the user's
**veto** on their return — `tk-queue cancel "<id>" --why "<the veto>"` is that veto, one
command against a finding that would otherwise have been lost to nobody's judgement.
