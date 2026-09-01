---
name: second-opinion
description: "Second opinion from a fresh Fable subagent on what the session is discussing right now — once, or argued to consensus within a turn budget."
disable-model-invocation: true
argument-hint: "[once|consensus] [turns]"
arguments: mode turns
---

A **second opinion** is a verdict from a mind that did not do the work: it sees the question and
the evidence, not the hours the session spent arriving at its position. That is the value, and
it is why the opinion comes from a **fresh** subagent on `fable` — a fork would inherit this
context and its blind spots.

Arguments: `$mode` is `once` (empty defaults to it) or `consensus`; any other value, stop and
show the hint. `$turns` is the **turn budget** for `consensus`: the number of subagent replies,
the first opinion included; empty defaults to 3.

## Steps

1. **Write the prompt** for a **cold reader**: the question in one sentence; the user's own words
   on it, verbatim; the options on the table; the evidence, as file paths and quoted lines the
   subagent can open itself; the session's current position and its reasoning, last. A claim
   without a path or a quote is one the subagent will rightly discount. Then the ask: "form your
   own verdict from the evidence before reading the session's position, then attack that
   position", and the reply shape — `AGREE` or `DISAGREE`, the disputed points each with the
   evidence it rests on, then what the session should change. Done when someone with no session
   context could answer the question from the prompt alone.

2. **Dispatch** `Agent` with `subagent_type: general-purpose`, `model: "fable"`,
   `effort: "high"` (a verdict's depth must not depend on the session's effort setting). In
   `consensus` mode, record the agent name the result returns: `SendMessage` continues that
   agent by it. Done when the reply is in hand — turn 1.

3. **Argue** (`consensus` only). Before each send, compare replies received with `$turns`;
   equal means the budget is spent, stop. Otherwise reply through `SendMessage` with one move per
   disputed point — **concede** it, saying what changes, or **hold** it with the evidence the
   subagent missed — and ask for the same two moves back. A point neither side can move with new
   evidence is **deadlocked**: leave it and go on. **Consensus** is an empty list of disputed
   points. Done at every point agreed or deadlocked, or at the spent budget.

4. **Report** to the user, outcome first:
   - `once`: the verdict, the points, what changes in the session's position.
   - consensus reached: the agreed position, the turns it took, what the session conceded.
   - budget spent or deadlocked: the open points, each with both sides' evidence — the human
     settles a split.

   Close with the policy's deviation line, in the report itself:
   `second-opinion: none→fable, effort high — fired by the user via /tk:second-opinion`.
   Done when the user has the outcome and the line.
