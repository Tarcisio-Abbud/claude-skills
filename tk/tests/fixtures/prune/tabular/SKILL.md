---
name: tabular
description: "Use when the skill under measure carries its instructions in a table and a list."
---

Match the task against the palette and write the whole command

## The palette

| Task situation | Dispatch | Who fires it |
|---|---|---|
| Needs the context this session already holds | inline, now | the agent |
| Verifiable end state such as a green suite or an empty queue | a goal command with the ready line | the user |
| Waiting on external state such as a build or a third party | a monitor streaming that state | the agent |

## The rules

- Pick one row, and when two rows fit, pick the cheaper one
- Write the command whole, and never the mechanism's name alone
- Hand the line to whoever the third column names
