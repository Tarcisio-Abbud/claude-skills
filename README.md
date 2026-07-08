# claude-skills

Own-authored global skills for Claude Code, installed at `/root/.claude/skills/` (that
directory IS the clone of this repo; an allowlist `.gitignore` keeps third-party skills out
of version control).

| Skill | What it does |
|---|---|
| `/wrap-up` | Session close: memory + docs + tests + summary + recommendation (/clear, /compact, /docs-audit) |
| `/kickoff` | Session open (mirror of /wrap-up): pending-items agenda verified against reality, triaged and dispatched via menu |
| `/dispatch` | Matches a task to its execution mechanism (/goal, /loop, /implement, Monitor, workflow, /schedule, /wayfinder, /research, subagent) and delivers the ready-to-paste line — model-invoked, fires on its own in conversation |
| `/docs-audit` | Documentation audit against the code: finds stale docs, fixes, verifies, opens a PR |

The `/kickoff` ↔ `/wrap-up` pair shares the canonical `next-steps.md` queue contract
(defined in `kickoff/SKILL.md`): one file per project in auto-memory holding the next
steps — wrap-up writes it, kickoff verifies and dispatches it. The dispatch palette (right
mechanism per task type, the `/goal` recipe, the `.claude/loop.md` contract that turns plain
`/loop` into the queue dispatcher) is single-sourced in `dispatch/SKILL.md` — kickoff
consumes it in step 5.

Skills are written in English (the model's strongest register and the ecosystem's
standard); conversation with the user stays in Portuguese.

Projects may carry tuned local variants in `.claude/skills/` (versioned in the project's own
repo); a local skill overrides the global one of the same name.

New own-authored skill: create the directory here and **add the exception to `.gitignore`**.
