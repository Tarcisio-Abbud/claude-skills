# claude-skills

Own-authored skills for Claude Code, shipped as the **`tk` plugin** (v2) and served by the
marketplace defined in `.claude-plugin/marketplace.json`.

## Install (a fresh machine)

```sh
claude plugin marketplace add Tarcisio-Abbud/claude-skills
claude plugin install tk@claude-skills
```

Updates from then on: `claude plugin marketplace update claude-skills`.

## Skills

| Skill | What it does |
|---|---|
| `/tk:kickoff` | Session open (mirror of /tk:wrap-up): pending-items agenda verified against reality, triaged and dispatched via menu. Args: `afk` — builds the package of autonomous, risk-free items and fires it with zero menus; `pack` — same package, one confirmation showing the summed Effort |
| `/tk:wrap-up` | Session close: parallel inventory gating the later steps, memory + docs + tests, a **versioning gate** settling every commit/push/merge decision in one menu (merges preceded by an adaptive review digest), and one explicit recommendation (/clear, /compact, /tk:docs-audit). Arg: `afk` — no menus; the ceiling is a local commit on a branch, never push/merge |
| `/tk:dispatch` | Matches a task to its execution mechanism (/goal, /loop, Monitor, dynamic workflow, /schedule, ticket flow, subagent) and delivers the ready-to-paste line — model-invoked, fires on its own in conversation |
| `/tk:docs-audit` | Documentation audit against the code: finds stale docs, fixes, verifies, opens a PR |

The `/tk:kickoff` ↔ `/tk:wrap-up` pair shares the canonical queue contract (defined in
`tk/skills/kickoff/SKILL.md`): two files per project in auto-memory — `next-steps.md`
(open items only) and `done-log.md` (what left the queue, when, and how) — written ONLY
through the deterministic CLI **`tk/bin/tk-queue`** (add / done / cancel / edit / list /
report / migrate), which moves a resolved item to the log in one command and enforces a
size ceiling on entry. Each item carries an ID (T001…), **Class** (AUTONOMOUS / DECISION /
BLOCKED / EXTERNAL / RECURRING), **Effort** (S/M/L + rough wall-clock time), an optional
**Risk** line naming what unsupervised execution could damage — an item with a Risk line
never enters an afk package — and a required **Criterion** (acceptance: `A:` a
deterministic check, `B:` the user's verdict; required on `add`, still optional on `edit`
for legacy items). Wrap-up settles the queue at close;
kickoff verifies and dispatches it at open. The queue has three
dispatchers — the interactive kickoff menu, `/tk:kickoff afk|pack`, and `/loop` over the
project's `loop.md` — spelled out in `tk/skills/dispatch/SKILL.md`, which also single-sources
the dispatch palette, the `/goal` recipe and the `loop.md` contract.

## Site extensions

The skills are generic and standalone. Site-specific integrations — a wiki to update at
wrap-up, the concrete commands behind the dispatch palette rows, extra agenda sources —
plug in via optional extension files the skills read when present:

- `~/.claude/tk/<skill>.md` — global to the machine;
- `.claude/tk/<skill>.md` — per project, at the project root.

Keep extension files out of public repos when they carry private paths or names.

Skills are written in English (the model's strongest register and the ecosystem's
standard); conversation with the user stays in Portuguese.

Projects may carry tuned local variants in `.claude/skills/` (versioned in the project's own
repo); a local skill overrides the global one of the same name.

## Layout, and the authoring machine

```
.claude-plugin/marketplace.json   the marketplace (serves the plugins below)
tk/
  .claude-plugin/plugin.json      the plugin manifest
  skills/<name>/SKILL.md          one directory per skill
  skills/kickoff/AFK.md           branch file: the afk/pack package flow
  bin/tk-queue                    deterministic CLI: only writer of the queue files
```

On the authoring machine this repo is cloned **as** `~/.claude/skills/`, so `tk/` sits
directly inside the skills directory and Claude Code auto-loads it as `tk@skills-dir` — no
install step, and a SKILL.md is edited where it actually runs. Other skills living in that
same directory (private or machine-local ones) are kept out of git by an allowlist
`.gitignore`.

New own-authored skill: create `tk/skills/<name>/SKILL.md`. No `.gitignore` change needed —
the whole `tk/` tree is versioned.
