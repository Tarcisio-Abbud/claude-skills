# claude-skills

Own-authored skills for Claude Code, shipped as the **`tk`** (v3), **`tk-cowork`**, **`asr`**
and **`plugin-drift`** plugins, served by the marketplace defined in
`.claude-plugin/marketplace.json`.

## Install (a fresh machine)

```sh
claude plugin marketplace add Tarcisio-Abbud/claude-skills
claude plugin install tk@claude-skills
```

Updates from then on: `claude plugin marketplace update claude-skills`.

## Skills

| Skill | What it does |
|---|---|
| `/tk:kickoff` | Session open (mirror of /tk:wrap-up): opens on `tk-hygiene` and the week's closed items (`tk-queue report --since`), then the pending-items agenda verified against reality and triaged — **Effort, Risk and Env** on every item, and an item half here and half elsewhere SLICED, one item per machine. Each DECISION is **briefed in prose before the menu**, retransmitting what the item already carries (its text, its `Criterion`, the memory behind a `[[slug]]` at one hop, its handoff) rather than summarising it. The close reports (a) what is running or scheduled, (b) BLOCKED, (c) EXTERNAL, (d) items bound to ANOTHER environment with their ready-to-paste line, (e) the **session findings** discarded here and (f) the age of what is left standing. A session finding is triaged where it is found, on the three-rung ladder of `tk/reference/session-finding.md` — resolve now, queue with a gate, discard — read in that order, the first that holds being the recommendation. Args: `afk` — builds the package of autonomous, risk-free items and fires it with zero menus; `pack` — same package, one confirmation showing the summed Effort; `--budget N` — the orchestrator generations either mode may spend |
| `/tk:wrap-up` | Session close: parallel inventory gating the later steps, memory + docs + tests, a **versioning gate** settling every commit/push/merge decision in one menu (every PR preceded by a **digest** — what is being merged, and whether it may be, then the five verdicts of **safe-to-merge**), and one explicit recommendation (/clear, /compact, /tk:docs-audit). An item survives into the queue only under one of three **survival gates** — decision · effort · dependency — and records which one; what passes none is resolved in the session. The close follows a **fixed template** (`tk/skills/wrap-up/REPORT.md`), which wins over any response-style preference. Arg: `afk` — no menus; the work is committed and pushed before any review, and each item ends merged under the strict five verdicts or at an open PR carrying its evidence block |
| `/tk:dispatch` | Matches a task to its execution mechanism (/goal, /loop, Monitor, dynamic workflow, /schedule, ticket flow, subagent) and delivers the ready-to-paste line — model-invoked, fires on its own in conversation |
| `/tk:merge-gate` | The versioning gate's own procedure, reached by three consumers and invocable on its own: the **digest** a pull request is judged on — its five trail sections, the per-file summary, the evidence block — and the five verdicts of **safe-to-merge**, with the triple check of the closing line (`tk/bin/tk-closure-check`), the action menu, the stack's merge order, the accumulated lane's per-item form and the strict form an unattended close runs. Read by `/tk:wrap-up` step 5 and by the afk tail; fired on its own for a merge settled outside a close |
| `/tk:verify` | Turns the item's acceptance criterion into the ruler of the delivery: north star after each slice, hard gate at the end (three failed attempts → DECISION with its handoff), a distinct outcome for a rotten criterion, and the evidence block the caller re-runs — written once, in the PR body or on the item that closes without one — model-invoked |
| `/tk:review` | One lens over a delivered code or data slice — the second pair of eyes, fired on the committed slice before the repo's mandatory two-axis review: a single subagent on the site's strongest tier, fired once, its angle picked from the slice's class; the severity ruler (nit/defect); the design signal a repeated mechanism raises, answered by the parent where the repo handles no business data and by the user otherwise; and the attack inventory it ships whether or not it found anything — model-invoked. Prose an agent follows takes the mandatory review alone, with ONE exception — where the changed paragraphs prescribe commands, a lens may fire, and it reports only what RUNNING a prescribed command proved. The trigger items live in the site's CLAUDE.md, or wherever the extension points; `~/.claude/tk/review.md` carries the provenance of every threshold and the site's user-data directories |
| `/tk:second-opinion` | A fresh Fable subagent judges what the session is discussing right now, from a prompt written for a cold reader. Args: `consensus [turns]` (default) — argued through `SendMessage` until no disputed point remains or the turn budget is spent (3 turns absent `turns`); a spent budget hands the open points to the user; `once` — a single verdict. User-invoked; every run logs the Fable deviation line |
| `/tk:fleet` | Runs the unattended package of EVERY project on this machine from one command: the roster comes from `tk-roster` and the site file's `fleet-allow`/`fleet-deny`, the machine's local subagent ceiling is divided across the runs by the generated contract block, and one full orchestrator per project runs at `--budget 1`. Largest project first; a slot refills the moment a run returns, with no wait for the wave; a project that fails fails alone. Closes on one consolidated vista in the outbox, gated by `tk-vista-check`. The load is a parameter — `afk` by default, `docs-audit` for a documentation sweep. User-invoked |
| `/tk:docs-audit` | Documentation audit against the code: finds stale docs, fixes, verifies, opens a PR. Also audits the project's **auto-memory** — proposes pruning the memories whose fact stopped holding (the user deletes), promotes what turned canonical to the repo docs or the site's wiki, and cuts `MEMORY.md` back to one line per file; the two `tk-queue` files are exempt |
| `/tk:prune` | Prunes a skill against the `writing-for-agents` ruler with a bias to subtraction: `tk/bin/tk-prune-measure` supplies the numbers and the ceilings, and the run leaves a report — metrics before and after, a KEEP / MOVE / DROP / CLAUSE / FIT table with one row per sentence that instructs, splitting suggestions, and the named proof — in `./prune-out/<skill>/`, never in place. User-invoked; args: `<skill-path> [<output-dir>]` |

The `/tk:kickoff` ↔ `/tk:wrap-up` pair shares the canonical queue contract, defined in
`tk/reference/queue.md`: two files per project in auto-memory — `next-steps.md` (open
items only) and `done-log.md` (what left the queue, when, and how) — written ONLY through
the deterministic CLI **`tk/bin/tk-queue`**. Commands, flags and field shapes live in the
CLI's own `--help`s; the reference file carries the contract the helps do not confess (the
two size ceilings, ID allocation, the stderr lines, the field chain, the done-log pointer
rule). Wrap-up settles the queue at close; kickoff verifies and dispatches it at open. The
queue has four dispatchers — the interactive kickoff menu, `/tk:kickoff afk|pack`, `/loop`
over the project's `loop.md`, and `/tk:fleet` across every project at once — spelled out in
`tk/skills/dispatch/SKILL.md`, which also single-sources the dispatch palette and the
`/goal` recipe; the `loop.md` contract sits beside it, in `tk/skills/dispatch/LOOP.md`.

A **digest** is written for every PR the versioning gate handles, before its menu
opens — what is being merged and whether it may be, made readable where it is read, with
every citation-by-number resolved to the sentence it names. The `merge-gate` skill says
how to write it, and `/tk:wrap-up` step 5 is one of its three consumers.
**`tk/bin/tk-collisions`** supplies the one section prose cannot: it merges every pair of open
branches for real, because the forge's `mergeable` field is blind between two PRs. With
`--against`, it instead builds one UNION per other branch on top of the assumed-landed pivot,
graded by a suite command — the collision no pairwise merge sees, where a test one branch adds
grades a file another branch edits.

Every subagent an orchestrator dispatches gets its model, reasoning effort, **venue**
(local × cloud), whether the role opens a pull request of its own and whether it owes the
**checkpoint invariant** — commit and push at every seam, so the quota wall costs at most the
work since the last one — from
`tk/reference/subagent-policy.md` — one row per role, the hybrid rule
that lets the orchestrator deviate by logging one line, and the venue eligibility test
(cloud only where the proof fits in the pushed repo). Its role table is delimited and
carries its own parsing schema, so a generator injecting those cells into a subagent's
contract block reads them verbatim instead of keeping a second copy. That same block points
every role at `tk/reference/slice-rules.md` — the rules earlier slices paid for, each one the
residue of a defect that a green suite or a passing review had already called healthy.

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

## The asr plugin

`transcribe-audio` turns audio Read cannot decode — voice notes, recordings, a WhatsApp
export `.zip` — into text, entirely on CPU, so nothing leaves the machine. Parakeet TDT 0.6B
v3 int8 is the default engine and faster-whisper the fallback for the languages Parakeet does
not cover.

Two design points carry the plugin. Parakeet transcribes a whole clip in one pass, so
`bin/transcribe.py` slices long audio into windows and cuts each at the quietest nearby frame
— without that, a long file OOMs a small box, and a naive cut splits numbers in half. And
`onnx_asr` reads WAV from disk only, so the script decodes with PyAV into an array and hands
that over, which is what makes `.opus` work with no system ffmpeg.

Machine-specific addresses — which interpreter, where the weights live, how they are
provisioned — stay out of this repo and live in the extension file below.

## Site extensions

The skills are generic and standalone. Site-specific integrations — a wiki to update at
wrap-up, the concrete commands behind the dispatch palette rows, extra agenda sources —
plug in via optional extension files the skills read when present:

- `~/.claude/tk/<skill>.md` — global to the machine;
- `.claude/tk/<skill>.md` — per project, at the project root.

`asr` follows the same shape: `~/.claude/asr/transcribe-audio.md` holds this machine's
interpreter, cache path and provisioning notes.

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
  skills/dispatch/LOOP.md         branch file: the `.claude/loop.md` contract, reached
                                  from the palette row that dispatches a queue of slices
  skills/verify/HANDOFF.md        branch file: the `tk-queue` sequence a third failed
                                  attempt at the hard gate runs, and the form every
                                  site that prescribes a briefing reads
  skills/review/BRIEF.md          branch file: the block the lens is handed, and the
                                  one line per angle that fills its `Attack:` field
  skills/prune/REPORT.md          branch file: the five parts of a pruning report
  skills/wrap-up/REPORT.md        branch file: the fixed closing template, read by every
                                  skill that closes on it
  skills/kickoff/AFK.md           branch file: the afk/pack package flow
  skills/kickoff/RESUME.md        branch file: what a generation that inherited a
                                  package mid-flight runs before anything else —
                                  reset, draft, close, re-dispatch, and the exits
                                  that grade a package it cannot resume
  skills/kickoff/AUDIT.md         branch file: the wave audit AFK.md step 4 routes
                                  to — the three lenses, one verifier per finding,
                                  the four outcomes, and the REGRILL that halts a
                                  package before its first run
  skills/kickoff/WINDOW.md        branch file: what the package does when it runs
                                  out of window rather than out of work — the
                                  checkpoint invariant, the quota wall's handoff,
                                  the five contents an accumulated lane adds to
                                  it, what the review lens costs the window, the
                                  --budget generations, and the seams the context
                                  threshold fires at — the cut and the pack confirm
                                  among them
  reference/queue.md              the queue contract `/tk:kickoff` and `/tk:wrap-up`
                                  share: the two files, the field chain, ID allocation
                                  and the gotchas the CLI's `--help`s do not confess
  reference/session-finding.md    what a session finding is, and the three-rung ladder
                                  that triages one — attended and unattended
  reference/subagent-policy.md    model, effort, venue, PR-authorship and the
                                  checkpoint invariant per subagent role; the role
                                  table is parseable, schema declared in the file
  reference/slice-rules.md        the rules earlier slices paid for — writing a command
                                  that touches a file, proving it, and prose another
                                  agent reads; reached from the contract block
  reference/vista.md              the vista: the digest's visual companion — what it is,
                                  when it is written, where it lands, and the five blocks
                                  it fixes; the contract the consolidated reporter reads.
                                  A fleet run writes one by default; every other close
                                  writes one only when the user asks
  reference/vista-template.html   that page in its smallest form: the five markers, both
                                  themes, and nothing the browser fetches
  bin/tk-queue                    deterministic CLI: only writer of the queue files.
                                  `add` also refuses at the site file's WIP cap,
                                  summed over the roster's queues and with no bypass
  bin/tk_site.py                  reads the site file (~/.claude/tk/env): this machine's
                                  identity, the roster of environments, the ceilings (two
                                  for subagents, one for the queue's open items), and the
                                  fleet's allow/denylist of projects
  bin/tk-contract                 generates the block a dispatched subagent is handed,
                                  from the site file and the role table — never written
                                  from memory, and carrying no copy of either
  bin/tk-roster                   sweeps ~/.claude/projects for the queues that exist and
                                  where their projects are, minus the site file's lists
  bin/tk-hygiene                  audits delete_branch_on_merge across every repo it
                                  reaches — the roster's, plus the clone it is installed
                                  in — and prunes what the default branch already has, by
                                  ancestry or after a squash: a local branch whose remote
                                  is gone, and a lane's spec/<m>/T<id> left on the remote,
                                  which no PR's head ever was and the forge never deletes.
                                  `--no-remote` skips that second one, the only step here
                                  that reaches the network for git. Exit 0 green, 1 a box
                                  still off, 3 a repo it could not audit, 2 the run did
                                  not happen
  bin/tk-collisions               merges each pair of open branches for real, so a pair
                                  that cannot both land is named before either does; with
                                  `--against`, one UNION per other branch instead, graded by
                                  `--suite`. No network: the refs must already be local
  bin/tk-vista-check              the gate on a vista: refuses a page that fetches anything,
                                  and one missing a block, a risk tag or a proof link
  bin/tk-prune-measure            measures one markdown file for a pruning pass: length,
                                  sentence shape, inline evidence, pointers, negations and
                                  defined terms, with `--targets` marking each against the
                                  ceilings it carries as defaults. It measures and does not
                                  judge, so every measurement exits 0
  bin/tk-ticket-ref               a queue item's ticket as `<owner>/<repo>#<n>`, the form a
                                  closing line needs — number from the item, owner and
                                  repository from the tracker config of the clone `--repo`
                                  names, or the item's own **Repo:** field, through the
                                  shape gate `bin/tracker-gh` applies. It refuses rather
                                  than emit an ownerless or guessed reference
  bin/tk-closure-check            verdict 5 of the merge gate, asked of the pull request:
                                  the closing keyword, the ticket's identity, the owner
                                  half, any OTHER closing line in the body and the base
                                  branch, each reported by name. It compares against the
                                  reference the reader composes, so it cannot greenlight
                                  what the reader refuses to emit. Exit 1 names the ones
                                  that failed
  bin/tk-context                  this session's context occupancy in tokens, read from its
                                  own transcript — the number WINDOW.md's seams compare, and
                                  which no orchestrator can see in the statusline. Absolute,
                                  never a fraction: the threshold is the smart zone, not the
                                  window's capacity. Reads the two record classes that decide
                                  occupancy — an API response and a compaction boundary — and
                                  the last recorded wins. `--curve` prints the occupancy
                                  across the session, since the slope is what says whether
                                  another review fits. Exit 2 no number, 64 bad usage: a
                                  mistyped flag may not read as the licence to use judgement
  bin/tk-quota                    what is left of the rolling usage windows — the 5h and
                                  weekly figures reach the STATUSLINE SCRIPT at render time
                                  and are in no transcript, so this is the only way an agent
                                  knows them. BOTH HALVES of the seam are here: `--write`
                                  records the payload arriving on stdin, and the default
                                  reads it back from the sidecar. A window must pass two
                                  tests to be reported — that it has not reset, and that the
                                  reading is not older than the window it describes — and the
                                  other window still prints when one fails. A reading that
                                  passes both and is still old announces its age rather than
                                  passing as current. The site installs it by calling
                                  `tk-quota --write` from its statusline script, by absolute
                                  path: a path that resolves to nothing no-ops in silence and
                                  reads exactly like "no session has rendered". Exit 1 nothing
                                  was recorded, 2 no number, 64 bad usage
  tests/test_tk_queue.py          regression suite for tk-queue (stdlib only)
  tests/test_tk_contract.py       regression suite for the generator
  tests/test_tk_roster.py         regression suite for the sweep and the two list keys
  tests/test_tk_hygiene.py        regression suite for the audit and the prune, against
                                  throwaway repos and a fake forge CLI on PATH — never
                                  the network
  tests/test_tk_collisions.py     regression suite, against a real git repository built
                                  in a throwaway directory
  tests/test_tk_vista_check.py    regression suite for the vista gate
  tests/test_tk_context.py        regression suite for the reading, and the doc conformance
                                  of the seams that call it
  tests/mutations_tk_context.py   its mutations — four on the prose, one on
                                  the suite's own reader of it, the rest on the bin
  tests/test_tk_quota.py          regression suite for the quota reading, and the doc
                                  conformance of the wall that calls it
  tests/mutations_tk_quota.py     its mutations — nine on the writer, which lived
                                  outside any suite until a lens found four wrong-number
                                  defects in it, four on the wall's prose, and one on the
                                  map pairing each window's label with its length
  tests/mutations.py              puts each defect back; every test must fall
  tests/anchor_check.py           the cheap half of that, over every harness in the
                                  directory: each anchor still matches its source
                                  exactly once, in a second instead of in minutes
  tests/mutations_tk_contract.py  its mutations, with a runner that takes the suite as
                                  an argument — and that reports a test no mutation
                                  names, since a green score counts only the mutants
                                  someone wrote
  tests/mutations_collisions.py   entries only: it enters through that runner's seam,
                                  which is what the seam was written for
  tests/mutations_vista.py        entries only: it folds into the same runner, through the
                                  seam that runner exposes for a module and its entries
  tests/mutations_hygiene.py      entries only, through the same seam
  tests/test_tk_prune_measure.py  regression suite for the measure bin, over the fixtures
                                  beside it
  tests/fixtures/prune/           seven skill directories whose numbers were counted by
                                  hand; the third-party one is a verbatim MIT copy, so that
                                  no fixture was adjusted to agree with the measurement
  tests/mutations_prune.py        entries only, through the same seam
  tests/test_afk_audit.py         audit of the afk contract against the skill files
  tests/test_unattended_ladder.py the rung an unattended session has left when the WIP
                                  cap refuses its `add`: both documents that prescribe
                                  `add` must name `edit --text` and `handoff`, and both
                                  commands must RUN against a queue at its cap
  tests/test_window_wall.py       step 2 of the wall, lifted out of WINDOW.md and run
                                  against a throwaway queue: an ORDINARY item (no
                                  DECISION, no --deferred) ends up pointing at its
                                  briefing through the edit the handoff prints
  tests/mutations_window_wall.py  entries only, through the same seam; six of its eleven
                                  entries edit a skill file, the other five the bin
  tests/queue_fixture.py          the throwaway queue the three doc-conformance suites run
                                  their prescriptions against: the directory, the tk-queue
                                  shim on PATH, the paste-into-bash and the reached() log
  tests/test_manifests.py         the two tk manifests against the skills on disk:
                                  every skill advertised, and nothing advertised that
                                  is not there
  tests/mutations_manifests.py    entries only, through the same seam; it mutates the
                                  manifests themselves, one of them at the repo root
  tests/test_tk_closure.py        the two closure bins against a throwaway queue, a
                                  throwaway clone carrying `tk.tracker`, and a fake forge
                                  CLI on PATH — plus the dispatch prose and the verdict-5
                                  row, which have to state the rule the checker enforces
  tests/mutations_closure.py      entries only, through the same seam; five sources, since
                                  two of the defects live in skill files rather than in a bin
tk-cowork/
  .claude-plugin/plugin.json      the Cowork plugin manifest
  CONTRACT.md                     the queue contract, shared by both skills
  skills/<name>/SKILL.md          wrap-up and kickoff, rebuilt for knowledge work
asr/
  .claude-plugin/plugin.json      the plugin manifest
  skills/transcribe-audio/SKILL.md
  bin/transcribe.py               the transcription CLI (Parakeet / faster-whisper)
docs/agents/                      what the mattpocock engineering skills read; versioned,
                                  for the reason given below
  issue-tracker.md                where the issues live and how to reach them, with the
                                  private half resolved from local git config
  triage-labels.md                the five triage roles, mapped to label strings
docs/prune/                       the pruning track's committed output: the baselines —
                                  what the skills of this plugin and of `mattpocock-skills`
                                  measure, and the gap between them — and one pair of files
                                  per skill already pruned
  baseline.py                     lays a baseline out from the bin's `--json --targets`; it
                                  measures nothing itself, which is why it is here and not
                                  in `tk/bin`
  baseline-<date>.md              one run. Named file by file in `.gitignore`, like the
                                  block above: a pruning report on a PRIVATE skill must not
                                  reach this repo
  <skill>-report.md               one pruning pass over an own skill: the metrics before and
                                  after, the KEEP / MOVE / DROP / CLAUSE / FIT table, the
                                  splitting suggestions and the named proof
  <skill>.md                      what that pass removed from that skill — every DROPped
                                  sentence and every cut clause, kept where a reader looking
                                  for a retired rule can still find it
.claude/                          this repo's own agent config; versioned for the reason
                                  given below, and named file by file in `.gitignore` like
                                  the two blocks above
  hookify.code-review-before-done.local.md
                                  the stop rule that reminds a session which committed
                                  code to run the two-axis review before calling it done
githooks/
  private-values                  refuses a commit that would publish a value from this
                                  clone's local git config; installed as two hooks
  tests/                          its suite and mutation harness
bin/
  tracker-gh                      runs one gh command against the private tracker,
                                  resolving it in the SAME process — a shell variable
                                  does not survive to the next tool call, and gh
                                  discards an empty -R onto the cwd's repo
  tests/                          its suite and mutation harness
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
nothing, so a mutation that survives is a hole, not a pass. `tk-contract` answers to the same
rule through `python3 tk/tests/mutations_tk_contract.py`, the commit guard through
`python3 githooks/tests/mutations_private_values.py`, the tracker wrapper through
`python3 bin/tests/mutations_tracker_gh.py`, `tk-vista-check` through
`python3 tk/tests/mutations_vista.py`, `tk-hygiene` through
`python3 tk/tests/mutations_hygiene.py`, `tk-prune-measure` through
`python3 tk/tests/mutations_prune.py`, the two manifests through
`python3 tk/tests/mutations_manifests.py`, the wall's step 2 through
`python3 tk/tests/mutations_window_wall.py`, and the two closure bins through
`python3 tk/tests/mutations_closure.py`, `tk-context` through
`python3 tk/tests/mutations_tk_context.py`, and `tk-quota` through
`python3 tk/tests/mutations_tk_quota.py`. The harnesses are separate files sharing
one shape; the oldest differs only in naming its test module inline. FOUR of them mutate
more than a bin: the manifests one mutates DATA only — its subject is the repository's
own state, and `marketplace.json` sits at the repo root, outside the `tk/` the runner
copies — the wall one mutates PROSE alongside the bin, an instruction removed from a
skill file being exactly the defect its suite exists to catch, and the `tk-context` one
mutates prose, the bin AND its own TEST FILE, the last being the only way to prove a
reader that lives in the suite: its statusline check must let the prose SAY the number is
not there while refusing an instruction to go and read it there — and the `tk-quota` one
mutates the wall's prose, since a command the wall does not name is a command nobody runs.

Every one of those anchors is a literal substring of its source, and it has to match
exactly once. `python3 tk/tests/anchor_check.py` asks that of every harness in the
directory in under a second, so an edit that reflows a source is checked where it is made
— the answer used to arrive only at the end of a six-minute run, which is how `main` once
shipped an anchor that had quietly stopped matching. It says the entries can still be
APPLIED, never that a test notices when they are: that stays the full harnesses' answer.

New own-authored skill: create `tk/skills/<name>/SKILL.md`, then advertise it in BOTH
manifests — a `<name> (…)` clause in `tk/.claude-plugin/plugin.json` and a `/tk:<name>`
mention in `.claude-plugin/marketplace.json` — and bump the plugin version.
`tk/tests/test_manifests.py` fails until both descriptions name it; the version is on you.
No `.gitignore` change needed — the whole `tk/` tree is versioned.

`docs/agents/` and `.claude/` are versioned, which is unusual for repo-local agent config and
follows from the paragraph above: a worktree is the standard way to work on a clone whose
primary tree is live, and `git worktree add` materialises tracked files only. Left untracked,
that config reached the primary tree and nowhere else, so every dispatched agent and every
`/mattpocock-skills:code-review` ran with no tracker config at all, and every worktree ran with
no stop rule holding it to that review.

This repo is written AS IF PUBLIC — private since 2026-09-01, but the flip back is one
command and everything it published before that date is already indexed. The private half
stays out of it — out of the FILES, that is. One
line of one surface names the tracker deliberately: the `Fixes <owner>/<repo>#<n>` closing
line in a PR body, which is what makes a merge close its ticket. PR bodies are not committed,
so nothing about the rule below moves; `docs/agents/issue-tracker.md` sets out which surface
may carry what. The tracker's slug and the `gh`
config directory live in the clone's local git config, under `tk.tracker` and
`tk.ghConfigDir`, which git never pushes. Tracker commands run through `bin/tracker-gh`,
which resolves those values in the same process that uses them: a shell variable does not
survive to an agent's next tool call, and `gh` answers an empty `-R` by silently targeting the
cwd's repo — this one. `docs/agents/issue-tracker.md` carries that reasoning, the two
`git config` lines a fresh clone needs, and the block that installs
`githooks/private-values` as both the `pre-commit` and the `commit-msg` hook.
