# The session-finding ladder

A **session finding** is work this session discovered and did not come for. The qualifier is
load-bearing: a code review's findings are defects in a diff, not this. What tells a session
finding from a **pendency** is the criterion of the item in hand: work that item's
`**Criterion:**` needs to pass is a pendency, resolved in the session. Everything else is a
session finding, and a session finding never inherits that default — that inheritance IS the
**hydra**: three heads die and six items are born, which is how a quick job became three weeks.

Consumers: `/tk:kickoff` (its `AFK.md` for the unattended form) and `/tk:wrap-up`. The
kickoff report's discard block, and the close's veto listing, are those skills' own.

## The ladder, with the user present

Every session finding is triaged at the moment of discovery, and with the user present the
triage is a menu (`AskUserQuestion`, which waits for them; a question in prose scrolls away).
Three outcomes, and the one that carries "(Recommended)" is the first that holds, read in order:

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

Nobody answers a menu mid-session, so **discard** is off the table: that judgement is the user's.
Three rungs are left, read in order:

1. **Fix on the spot** — the finding reproduces inside THIS session's diff and carries a criterion a run can
   check. It goes to a `fixer` under the fixer cap, the fourth exit of `../skills/review/SKILL.md`.
2. **Queue with a gate** — `tk-queue add` at the moment of discovery, the gate in the item's own
   text. A branch-point finding takes the slice's ticket, failing that ONE item per firing
   (`../skills/review/SKILL.md`). Never a `fixer`: dispatching backlog is scope creep. At
   `max-open-items` the `add` refuses, past every flag; `edit --text` folds the finding into
   an item that exists, `tk-queue handoff` into its briefing.
3. **Park it** — only the user can judge it: a DECISION carrying `--deferred afk`, the branch pushed,
   the handoff of `../skills/kickoff/WINDOW.md` written, and the package goes on.

Every finding is listed in the close under the rung that took it, for the user's **veto** on
their return. `tk-queue cancel "<id>" --why "<the veto>"` is that veto, one command against a
finding otherwise lost to nobody's judgement.
