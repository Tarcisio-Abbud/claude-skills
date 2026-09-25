---
name: revisao-contrato
description: Review a Brazilian contract along ten method lenses and a critic, then write one report — ranked findings with ready-to-paste wording, at most ten questions for a lawyer, a negotiation table — or apply chosen findings to the text. Use when asked to "revisar contrato", "revisar minuta", "analisar contrato que recebemos", for a "contraproposta" or "redline", "o que está faltando neste contrato", or `/contrato:revisao-contrato <file>`. Not for code review or a document that is only read.
argument-hint: <contrato.md|.docx> [nossa_parte=…] [autoria=nossa|deles] [acordo_previo=…|none] [aplicar=…]
---

# Revisão de contrato

Two invocations, never merged into one. The **review** reads the contract through the lenses
and writes the report. The **apply** runs later, on ids the human picked from that report's
table.

This skill is the opt-in for the Workflow tool, in the tool's own words: "The user invoked a
skill or slash command whose instructions tell you to call Workflow." Every agent the script
spawns has its model pinned in the script (opus or sonnet, never inherited), and the script
refuses to pass 30 agents.

`<skill dir>` below is the directory holding this file. The script is
`<skill dir>/reference/revisao-contrato.workflow.js`; `lenses.md` and `report-template.md`
beside it are read by the agents, not by you.

## Arguments

| arg | values | default |
|---|---|---|
| `contrato` | path to `.md`, `.txt` or `.docx` | required |
| `nossa_parte` | `contratante` · `contratado` · `outro:<rótulo>` | ask |
| `autoria` | `nossa` (we drafted it) · `deles` (we received it) | ask |
| `acordo_previo` | path to the prior agreement (term sheet, LOI, proposal, e-mail thread) or `none` | ask once |
| `apoio` | list of paths (glossary, ADRs, cap table, prior drafts) | `[]` |
| `data` | today, `YYYY-MM-DD` — the script cannot read the clock | today |
| `aplicar` | `none` · list of ids · `"todas"` | `none` |
| `folga` | allowed growth of the text in the apply step, a percentage with `%` | `+10%` |
| `saida` | report directory | `<contract dir>/revisao-<slug>-<data>/` |

`nossa_parte` and `autoria` are separate facts: we can draft a contract and be its contratante.
Take every value from the user's message; ask for none of them yet. Pass `skill_dir` as well.

## Review — `aplicar` is `none`

1. **Print the plan line.** Run `node "<skill dir>/reference/plan.mjs" '<args as JSON>'`. It
   runs the workflow script in plan mode, which spawns no agent, and prints the line and
   `saida:`. Exit 3 means an arg is missing or the plan must be confirmed. Where `node` is
   absent, call `Workflow({scriptPath: "<skill dir>/reference/revisao-contrato.workflow.js", args: {...args, modo: "plano"}})`
   instead: the same code, returning `linha`, `saida`, `faltando` and `perguntar`. Print the
   line verbatim, then tell the user to run `/usage` to see what the run will cost them — the
   skill cannot read it. Pass `saida` explicitly from here on.
2. **Check the numbering.** Run `python3 "<skill dir>/reference/docx-scout.py" <contrato> --out <saida>`.
   Exit 0 prints `contrato: <path>`: that Markdown is the `contrato` the review reads, and the
   file as received is kept as `original`. Exit 3 means no clause numbering survived.
3. **Gate.** Proceed without asking when step 1 exited 0 (or `perguntar` is false) and step 2
   exited 0. Otherwise ask ONE `AskUserQuestion` covering the missing args, the numbering
   failure (ask for a Markdown or plain-text export) and the count; it doubles as the
   confirmation. After the answer, rerun step 1 when an arg changed.
4. **Run.** `Workflow({scriptPath: <same>, args: {...args, contrato: <Markdown path>, saida, modo: "revisar"}})`.
5. **Dump the raw findings.** `python3 "<skill dir>/reference/brutos.py" <saida>` — the lenses
   wrote `<saida>/brutos/*.json` as they finished, so this also works after a run cut short.
6. **Report.** Confirm `<saida>/revisao.md` has at most 400 lines and section 3 at most ten
   questions. Reply with its path, the Veredito paragraph, and the apply invocation: the ids
   come from the table of section 2, and it names `saida` and the Markdown `contrato` of this
   review, which the apply needs.

Done when `revisao.md`, `medias.md` and `achados-brutos.md` exist in `<saida>` within those
limits.

## Apply — `aplicar` is set

Run this only in an invocation after the review, on ids the human chose.

1. When `aplicar` is `"todas"`, resolve it: `python3 "<skill dir>/reference/apply-edits.py" ids <saida>/revisao.md`.
2. Call the Workflow with `modo: "aplicar"`, `aplicar: [ids]` and `saida`: the directory of the
   review whose ids these are, taken from the review's reply or the report's path. The script
   refuses to run without it rather than recompute it from `contrato` and `data`, which name
   another directory on another day. One opus agent per clause group writes
   `<saida>/aplicar/<group>.json`; none of them edits the contract.
3. Run `python3 "<skill dir>/reference/apply-edits.py" apply --contrato <the Markdown the review read> --original <file as received> --edits <saida>/aplicar --data <data> --folga <folga>`.
   Omit `--original` when the contract was already Markdown. Before any write the script
   snapshots the current text to `<contract dir>/versoes/<name>-<data>.md` (and a `.docx`
   original beside it), then regenerates `<name>-aplicado-<data>.docx` beside a `.docx`
   original. Exit 5 is a snapshot or that `.docx` already there and not its own: move it and rerun.
4. Exit 4 is an overrun: nothing was written. Show the overrun and the per-id deltas, and
   offer the cuts of the report's *Clareza* plan as offsets, or fewer ids; the user chooses.

Done when the script exits 0 and you have reported the word count before → after and the
snapshot path.

## Out of scope

`.pdf` input, contracts without clause numbering, and runs inside an unattended package: the
review needs a human at the gate and at the choice of ids.
