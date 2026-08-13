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
| `/tk:kickoff` | Session open (mirror of /tk:wrap-up): opens with the week's closed items (`tk-queue report --since`), then the pending-items agenda verified against reality, triaged and dispatched via menu. Args: `afk` — builds the package of autonomous, risk-free items and fires it with zero menus; `pack` — same package, one confirmation showing the summed Effort |
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
never enters an afk package — a required **Criterion** (acceptance: `A:` a
deterministic check, `B:` the user's verdict; required on `add`, still optional on `edit`
for legacy items), and an optional **Project** slug tagging which project an item belongs
to, for a workspace-root queue that mixes several projects — `add` warns (not errors) when
a tag is unprecedented in the queue, naming the tags already in use, and `list` groups by
tag once any item carries one, else it stays flat. Wrap-up settles the queue at close;
kickoff verifies and dispatches it at open. The queue has three
dispatchers — the interactive kickoff menu, `/tk:kickoff afk|pack`, and `/loop` over the
project's `loop.md` — spelled out in `tk/skills/dispatch/SKILL.md`, which also single-sources
the dispatch palette, the `/goal` recipe and the `loop.md` contract.

## The `tk-cowork` plugin

The same pair rebuilt for **Claude Cowork**, where there is no repo and no test suite. What
changed: the versioning gate became a gate over **irreversible** actions (send, share,
schedule, post), the queue is a plain `next-steps.md` at the **project folder's root**
(edited by the agent — `tk-queue` stays on the Claude Code side), and both skills are
model-invoked, so the agent fires the wrap-up when the user says they are closing. `afk`
survives in both, with the ceiling "every irreversible action becomes a `DECISION` item".

Since v1.1.0 the contract also names **one writer** per shared document — the session
holding the conversation — because two agents doing read-modify-write on the same file lose
the first write silently, and a tool reporting success does not prove which base version it
started from. Subagents execute and report back; the orchestrator writes once and reads the
file back to confirm.

Since v1.2.0 both skills also carry a **surface guard**: `COWORK ONLY` in the description,
a `Wrong surface?` stop before step 1, and `compatibility` naming the intended product.
Nothing in the plugin format gates a skill by product — the separation is that the Cowork
tab sources its plugins from the claude.ai account (**Customize**) while Claude Code reads
its marketplaces and `~/.claude`, so one plugin list can end up serving both. These two are
model-invoked, so without the guard a wrap-up meant for knowledge work can close a code
session with no test suite and no versioning gate. `compatibility` documents the intent per
the Agent Skills spec; Claude Code accepts the field but does not act on it.

Keep the frontmatter of both within the spec's six fields (`name`, `description`, `license`,
`compatibility`, `metadata`, `allowed-tools`). The claude.ai upload path that Cowork syncs
from rejects anything else with a hard error rather than ignoring it — which is also why
`tk`'s own skills, which use `disable-model-invocation`, could never travel that route.

Measured constraints behind that design (2026-08-04, probed with a throwaway skill): a
script bundled in a skill **does** run in the Cowork sandbox (python3, git available), but
state written there dies with the session, and `CLAUDE_PLUGIN_ROOT`/`CLAUDE_PLUGIN_DATA` are
unset for a standalone uploaded skill — so the queue lives in the project folder, never in
the sandbox. The personal upload path wants a zip with `SKILL.md` at the top level; the
plugin form here is for marketplace/organization sync.

## The `plugin-drift` plugin

Read-only drift report across every installed Claude Code plugin, in every marketplace known
to this machine (`~/.claude/plugins/known_marketplaces.json`) — one skill, `check`, wrapping
`plugin-drift/bin/plugin-drift-check`. Refreshes each marketplace's catalog first, then per
plugin: git-pinned plugins (catalog `source.sha`) compare the installed commit against the
catalog's directly — matching semver is not proof of matching commit, `mattpocock-skills` is
the canonical case where both read the same version with different commits underneath.
Plugins packaged inside the marketplace repo itself (catalog `source` is a path, no `sha`)
compare file hashes one direction instead, since the installed `gitCommitSha` on those is the
marketplace's own commit, not a per-plugin one. `--changelog <name@marketplace>` pulls the
commit-log highlights for one drifted git-pinned plugin, best-effort, from its own upstream
repo. Never applies anything — the CLI's `disable`+`install` pair, or the `/plugin` dialog
where the CLI binary is unavailable, is still how a drifted plugin actually gets updated.

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
  tests/test_tk_queue.py          regression suite for that CLI (stdlib only)
  tests/mutations.py              puts each defect back; every test must fall
tk-cowork/
  .claude-plugin/plugin.json      the Cowork plugin manifest
  CONTRACT.md                     the queue contract, shared by both skills
  skills/<name>/SKILL.md          wrap-up and kickoff, rebuilt for knowledge work
```

On the authoring machine this repo is cloned **as** `~/.claude/skills/`, so `tk/` sits
directly inside the skills directory and Claude Code auto-loads it as `tk@skills-dir` — no
install step, and a SKILL.md is edited where it actually runs. Other skills living in that
same directory (private or machine-local ones) are kept out of git by an allowlist
`.gitignore`.

Being the live directory cuts both ways: a checked-out branch changes behaviour **now**, and
returning to `main` puts the old `tk-queue` back. A fix is only in force once merged.

`tk-queue` has a suite — `python3 -m unittest discover -s tk/tests` — and every test in it is
proved by `python3 tk/tests/mutations.py`, which restores each defect and requires the tests
named for it to fail, one at a time. A test that passes with the defect back protects
nothing, so a mutation that survives is a hole, not a pass.

New own-authored skill: create `tk/skills/<name>/SKILL.md`. No `.gitignore` change needed —
the whole `tk/` tree is versioned.
