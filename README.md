# claude-skills

Own-authored Claude Code plugins — `tk`, `asr`, `whatsapp`, `contrato` and `plugin-drift` —
served by the marketplace in `.claude-plugin/marketplace.json`.

## Install

```sh
claude plugin marketplace add Tarcisio-Abbud/claude-skills
claude plugin install tk@claude-skills
claude plugin install asr@claude-skills
claude plugin install whatsapp@claude-skills
claude plugin install contrato@claude-skills
claude plugin install plugin-drift@claude-skills
```

Install only the plugins you want. Restart Claude Code afterwards.

To update:

1. `claude plugin marketplace update claude-skills`
2. `claude plugin update <plugin>@claude-skills`
3. Restart Claude Code.

What each plugin needs on the machine:

| Plugin | Needs |
|---|---|
| `tk` | `python3` (stdlib, POSIX), `git`; `gh` for `tk-hygiene` and `tk-closure-check` |
| `asr` | a Python with `onnx-asr` and `av` (plus `faster-whisper` for `--engine whisper`); `HF_HOME` on a persistent directory, so the model weights survive |
| `whatsapp` | `python3` (stdlib); the `asr` plugin, to transcribe voice notes |
| `contrato` | the Workflow tool; `python-docx` for a `.docx` contract; `node` for the plan step (optional) and the tests |
| `plugin-drift` | Python 3 on `PATH` |

The `tk` plugin ships no hooks. Its compaction hooks (`tk/bin/tk-compact-mark` on
`PreCompact`, `tk/bin/tk-compact-pointer` on `SessionStart` with matcher `compact`) and the
quota reading (`tk/bin/tk-quota --write`, called from your statusline script) are wired by
you; each bin's docstring says how. The site file `~/.claude/tk/env` is optional until a
queue item names an environment; its format is in `tk/bin/tk_site.py`.

## Skills

"Auto" means the model may fire the skill on its own; the others run only when you type them.

| Skill | Auto | What it does |
|---|---|---|
| `/tk:kickoff` | no | Opens a session: triages the project's queue, briefs each decision, dispatches the work; `afk`/`pack` build an unattended package |
| `/tk:wrap-up` | no | Closes a session on a fixed template: memory, docs, tests, and one versioning gate for every commit, push and merge |
| `/tk:dispatch` | yes | Matches a task to the mechanism that runs it unattended and hands back the ready-to-paste line |
| `/tk:merge-gate` | no | The digest a pull request is judged on and the five safe-to-merge verdicts; also read by `/tk:wrap-up` |
| `/tk:verify` | yes | Runs the item's acceptance criterion as the gate of the delivery and writes the evidence block |
| `/tk:review` | yes | One lens over a committed slice, before the repo's mandatory two-axis review |
| `/tk:second-opinion` | no | A fresh Fable subagent's verdict on the current discussion, once or argued to consensus |
| `/tk:fleet` | no | Runs every project's unattended package on this machine and closes on one consolidated HTML vista |
| `/tk:docs-audit` | no | Audits every doc and the project's auto-memory against the code, fixes, and opens a PR |
| `/tk:prune` | no | Measures a skill against the writing-for-agents ruler and reports what to keep, move and drop |
| `/asr:transcribe-audio` | yes | Transcribes audio that Read cannot decode, on CPU, in resumable batches |
| `/whatsapp:export-delta` | yes | Reads a WhatsApp export `.zip` by its delta against the previous export |
| `/contrato:revisao-contrato` | yes | Reviews a Brazilian contract along ten lenses and a critic; a second run applies the chosen findings |
| `/plugin-drift:check` | yes | Reports which installed plugins drifted from their marketplace catalog; never applies an update |

Each skill's manual is its `<plugin>/skills/<name>/SKILL.md`. Longer material:

- `docs/tk.md` — each `tk` skill in depth, the queue contract, the digest and the subagent policy.
- `docs/plugins.md` — the design notes behind `asr`, `whatsapp`, `contrato` and `plugin-drift`.
- `docs/maintaining.md` — the layout, the test and mutation harnesses, the authoring machine,
  and the public-repo rules.

## Site extensions

The skills are generic and standalone. Site-specific integrations — a wiki to update at
wrap-up, the concrete commands behind the dispatch palette rows, extra agenda sources —
plug in via optional extension files the skills read when present:

- `~/.claude/tk/<skill>.md` — global to the machine;
- `.claude/tk/<skill>.md` — per project, at the project root.

`asr` follows the same shape: `~/.claude/asr/transcribe-audio.md` holds this machine's
interpreter, cache path and provisioning notes.

Keep extension files out of public repos when they carry private paths or names.

## Working on this repo

- **Tests.** Run `python3 -m unittest discover -s <dir>` for each of `tk/tests`,
  `whatsapp/tests`, `contrato/tests`, `githooks/tests` and `bin/tests`. Each suite has a
  mutation harness beside it; `docs/maintaining.md` says how to run them.
- **A fresh clone.** Set the tracker config and install the commit guard, both in
  `docs/agents/issue-tracker.md`, before the first commit.
- **The live clone.** On the authoring machine this repo is cloned as `~/.claude/skills/`, so
  a checked-out branch changes what every session runs. Work in a linked worktree.
- **A new `tk` skill.** Advertise it in both manifests; `tk/tests/test_manifests.py` fails
  until you do.
- **Public.** This repo is public: no company, client or account names, and no private paths.
  `githooks/private-values` refuses a commit carrying a private value it was configured with.
