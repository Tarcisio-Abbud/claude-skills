# The wave audit — the spec and the tickets before the first implement

Read from step 4 of `AFK.md` beside this file, on a package whose items came from a spec and
ticket set written in this flow — a **wave**. It stands between step 3's claim and that step's
first run, and it is the only step that halts a package with no run fired. A package assembled
from an aged queue has no spec to read, and the block owed to step 6 says so. Skipping is
allowed only for a wave of at most two tickets judged mechanical and fully specified — a bet
with no hedge, stated in the block with what was read to judge it — and a wave re-sliced after
a REGRILL refuses the bet.

## The lenses and the verifiers

Fire the site's dynamic workflow from this session (`~/.claude/tk/dispatch.md` names the
mechanism; the Agent-tool fallback runs the same graph in series). **Three finders**, one per
lens — **adversarial**, **blast radius**, **contract** — each checking every acceptance criterion
against the decision it cites; an empty return is a failure, never an approval — finding nothing,
a lens lists the attacks it ran. Dedup here, by the DEFECT and not the quoted line. Then **one
verifier per finding**, mandate to refute, default verdict refuted, declaring
`high`/`medium`/`low` confidence: `low`, or a correction that edits spec or ticket, goes to
`verifier-2`; disagreement to `tiebreak`; a verifier that writes gets `isolation: 'worktree'`.
Rows: `audit-finder`, `verifier-1`, `verifier-2`, `tiebreak`. One question stays with the
orchestrator: can the first implement session START — repo, tracker configuration, credentials,
the fixture its criterion runs against?

## The four outcomes

Exactly one outcome per surviving finding: **resolve here** — the correction fits the spec or the
tickets, the orchestrator edits them recording what the text said before (correcting the audited
documents, not the resolving the session-finding ladder forbids); **backlog** —
`tk-queue add --dir "<queue dir>"` with the gate named, as *A session finding, unattended*
prescribes; **refuted** — one line naming the verifier and how; **REGRILL** — the spec's own
premise is hit, and the package halts with no run fired. A **rotten criterion** (term:
`../verify/SKILL.md`) routes by which document is wrong: the criterion alone misses the promise →
resolve here, through `verifier-2` before it is applied; criterion and spec agree and together
miss → REGRILL.

```sh
tk-queue add "REGRILL: <the promise the audit could not close> — package halted before the first implement" \
  --dir "<queue dir>" --class DECISION --deferred afk --effort "M (~40min)" \
  --criterion "B: the user re-grills the promise, and the wave is re-sliced from the spec that grill leaves"
tk-queue handoff "<id>" --dir "<queue dir>" --objective "<what the re-grill has to settle>" \
  --state "<the finding, its verifier's verdict, and where the spec and the tickets stand>" \
  --blockers "<what the package stopped holding, and every claim it released>"
```

Every `<...>` is a metavariable — substitute before running, `<id>` being the id the `add`
printed; the quoting is load-bearing, since a shell reads a bare `<id>` as a redirect. **Then run
the `edit` the handoff prints** (`../verify/SKILL.md`, *The item points at the briefing*),
release what the package was holding per step 3, and hand the halt to step 6.
`../../tests/test_afk_audit.py` proves this recipe and its gate; whether the step ran is what the
block is for.

**Done when:** the block step 6 is owed names one of four states — **ran**, each finding under
its outcome with its verifier's verdict; **skipped**, with the judgement; **partial** — the
lenses delivered and the verifier died: re-dispatch it, else every unverdicted finding goes to
backlog as *unverified by the audit*, counted; or **failed** — a lens nobody could make run, and
the wave is unaudited.
