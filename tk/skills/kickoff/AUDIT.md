# The wave audit — the spec and the tickets before the first implement

Read from step 4 of `AFK.md` beside this file, on a package whose items came from a spec and
ticket set written in this flow — a **wave**. It stands between step 3's claim and that step's
first run, and it is the only step that halts a package with no run fired. A package assembled
from an aged queue has no spec to read, and the block owed to step 6 says so. Skipping an
unaudited wave is allowed only for a wave of at most two tickets judged mechanical and fully
specified — a bet with no hedge, stated in the block with what was read to judge it — and a
wave re-sliced after a REGRILL refuses the bet. Budget about 50pp of the 5h window for an
eight-ticket wave. A wave re-sliced after a REGRILL is a new wave, audited again.

## Two orchestrators, one wave

A claim guards one queue, and one spec can feed packages in two. Before the first lens, read
the spec issue's comments for `Wave audit <date> em curso — <queue dir>`, age from `created_at`:
`gh api "repos/<owner>/<repo>/issues/<n>/comments" --paginate --jq '.[]|[.created_at,.body]'`.
One under 5h old is a sibling mid-audit: take that spec's tickets out as held elsewhere (`AFK.md`
step 3) and release their claims. Report that comment to step 6 as **skipped**. An older one is a
dead run, and the block says so. With none live, post that comment there before the first lens.
The per-ticket comment below still closes the audit.

## What the lenses read

The lenses check only the criteria of the tickets IN THE PACKAGE. The spec and the sibling
tickets enter as context, and blast radius still crosses into them. Closing the audit, comment
`Wave audit <date>` on each ticket checked, and on no other. A later package over the same spec
audits its tickets lacking that comment, and inherits the earlier findings against the spec. A
package whose every ticket carries it reports **skipped** to step 6, naming the date and the
ticket read — an inherited audit, not the two-ticket bet above.

## The lenses and the verifiers

Fire the site's dynamic workflow from this session (`~/.claude/tk/dispatch.md` names the
mechanism; the Agent-tool fallback runs the same graph in series). **Three finders**, one per
lens — **adversarial**, **blast radius**, **contract** — each checking every in-scope criterion
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
documents, not the resolving the session-finding ladder forbids); **backlog** — the destination
`FINDINGS.md` beside this file gives a finding at THIS moment, before the first run: the wave's
plan, or the audited ticket's own body, never the queue; **refuted** — one line naming the
verifier and how; **REGRILL** — the spec's own premise is hit, and the package halts with no run
fired. A **rotten criterion** (term: `../verify/SKILL.md`) routes by which document is wrong: the
criterion alone misses the promise → resolve here, through `verifier-2` before it is applied;
criterion and spec agree and together miss → REGRILL.

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

**Done when:** the block step 6 is owed names one of four states — **ran**, each finding under
its outcome with its verifier's verdict; **skipped**, with the judgement or the inherited
audit's date; **partial** — the lenses delivered and the verifier died: re-dispatch it, else
every unverdicted finding goes to backlog as *unverified by the audit*, counted; or **failed** — a
lens nobody could make run, and the wave is unaudited.
