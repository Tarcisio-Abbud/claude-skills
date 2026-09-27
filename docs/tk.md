# tk — the skills in depth

The README's table gives each skill one line; this is the long form, moved from the README
on 2026-09-26. Each skill's own `tk/skills/<name>/SKILL.md` stays the source of truth.

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

## The queue, the digest and the subagent policy

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
