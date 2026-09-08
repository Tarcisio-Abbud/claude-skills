---
name: second-opinion
description: "Second opinion from a fresh Fable subagent on what the session is discussing right now — argued to consensus within a turn budget, or a single verdict."
disable-model-invocation: true
argument-hint: "[consensus|once] [turns] [--prompt <file>]"
arguments: mode turns
---

A **second opinion** is a verdict from a mind that did not do the work: it sees the question and
the evidence, not the hours behind the session's position. That is why the opinion comes from a
**fresh** subagent on `fable`: a fork inherits this context and its blind spots.

Arguments: `$mode` is `consensus` (empty defaults to it) or `once`. `$turns` is the **turn
budget** for `consensus`: the number of subagent replies, the first opinion included; empty
defaults to 3. Both are POSITIONAL, so prose typed after the command lands in them —
`--prompt <file>` included, which step 1 reads. An unrecognised value takes its OWN default
rather than stopping the skill — `consensus` for `$mode`, 3 for `$turns` — and the report opens
with one line naming what was ignored.

## Steps

1. **Write the prompt** for a **cold reader**: the question in one sentence; the user's own words
   on it, verbatim; the options on the table; the evidence, as file paths and quoted lines the
   subagent can open itself; the session's position and its reasoning, last. The subagent
   rightly discounts a claim without a path or a quote. Then the ask: "form your own verdict from
   the evidence before reading the session's position, then attack that position", and the reply
   shape — `AGREE` or `DISAGREE`, the disputed points each with the evidence it rests on, then
   what the session should change. With `--prompt <file>`, that file is the prompt instead: take
   the mode from its first `Mode:` line, and a typed `$mode` wins. Done when someone with no
   session context could answer the question from the prompt alone.

2. **Dispatch** `Agent` with `subagent_type: "tk:second-opinion"`. Its definition pins
   `model: fable` and `effort: high`, whatever this session's effort is. In `consensus`, record
   the agent name the result returns: `SendMessage` continues it. Done when the reply is in hand
   — turn 1.

3. **Argue** (`consensus` only). Before each send, compare replies received with `$turns`;
   equal means the budget is spent, stop. Otherwise reply through `SendMessage` with one move per
   disputed point — **concede** it, saying what changes, or **hold** it with the evidence the
   subagent missed — and ask for the same two moves. A point neither side can move with new
   evidence is **deadlocked**: leave it and go on. **Consensus** is an empty list of disputed
   points. Done at every point agreed or deadlocked, or at the spent budget.

4. **Report** to the user, outcome first:
   - `once`: the verdict, the points, what changes in the session's position.
   - consensus reached: the agreed position, the turns it took, what the session conceded.
   - budget spent or deadlocked: the open points, each with both sides' evidence — the human
     settles a split.

   Close with the policy's deviation line, in the report:
   `second-opinion: none→fable, effort high — fired by the user via /tk:second-opinion`.
   Done when the user has the outcome and the line.
