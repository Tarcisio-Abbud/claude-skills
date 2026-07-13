# claude-skills

Own-authored skills for Claude Code, shipped as the **`tk` plugin** and served by the
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
| `/tk:wrap-up` | Session close: memory + docs + tests + summary + recommendation (/clear, /compact, /tk:docs-audit) |
| `/tk:kickoff` | Session open (mirror of /tk:wrap-up): pending-items agenda verified against reality, triaged and dispatched via menu |
| `/tk:dispatch` | Matches a task to its execution mechanism (/goal, /loop, /implement, Monitor, workflow, /schedule, /wayfinder, /research, subagent) and delivers the ready-to-paste line — model-invoked, fires on its own in conversation |
| `/tk:docs-audit` | Documentation audit against the code: finds stale docs, fixes, verifies, opens a PR |

The `/tk:kickoff` ↔ `/tk:wrap-up` pair shares the canonical `next-steps.md` queue contract
(defined in `tk/skills/kickoff/SKILL.md`): one file per project in auto-memory holding the next
steps — wrap-up writes it, kickoff verifies and dispatches it. The dispatch palette (right
mechanism per task type, the `/goal` recipe, the `.claude/loop.md` contract that turns plain
`/loop` into the queue dispatcher) is single-sourced in `tk/skills/dispatch/SKILL.md` — kickoff
consumes it in step 5.

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
```

On the authoring machine this repo is cloned **as** `~/.claude/skills/`, so `tk/` sits
directly inside the skills directory and Claude Code auto-loads it as `tk@skills-dir` — no
install step, and a SKILL.md is edited where it actually runs. Third-party skills (Matt
Pocock's, via `npx skills`) live in that same directory and are kept out of git by an
allowlist `.gitignore`.

New own-authored skill: create `tk/skills/<name>/SKILL.md`. No `.gitignore` change needed
any more — the whole `tk/` tree is versioned.
