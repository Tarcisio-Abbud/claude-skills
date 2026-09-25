# The digest

Read from `SKILL.md`, the merge gate, before writing any pull request's digest. **The
digest is what the user reads instead of the diff**: it says WHAT is being merged and
whether it MAY be merged. It has two parts. The block below is the only thing per PR the
gate prints before the menu, and it opens the PR body. The trail sections follow it in the
body alone. Nothing else per PR is printed: no per-file summary, no diff, no section list.

## The block

One per pull request, in this order, **six lines, never more** — a package's lane has
its own ceiling, below:

```
<pode mesclar | não pode: <motivo>> — https://github.com/<owner>/<repo>/pull/<n>
<this item's entry in the What changed mould of ../wrap-up/REPORT.md: the item line and the three lines under it>
Testes <word> · Review <word> · Critério <word> · Reversão <word> · Fechamento <word>
```

- **Line 1 is the verdict, then the full URL.** `pode mesclar` only when all five verdicts
  read `ok` and `tk-collisions` found no colliding pair. Otherwise `não pode:` and the
  first thing in the way, in one clause. The URL is whole, never a bare `#n`. A change with
  no PR yet — a commit straight to main, a branch nobody opened — carries that commit's or
  branch's forge URL instead, and the line adds `sem PR`.
- **Lines 2 to 5 are one entry of `../wrap-up/REPORT.md`'s *What changed*.** That file owns
  the mould; follow it there. Each line is one concrete clause of at most ~25 words. Every
  identifier or hash arrives with what it is, or stays out.
- **Line 6 is the five verdicts of `SKILL.md`, in its order, one word each**: `ok`, `âmbar`
  or `vermelho`. A word other than `ok` takes its reason after a colon, in one clause. A
  type-B criterion is `âmbar` and its reason is the one-line claim the proof carries.

Filled in:

```
não pode: o critério espera seu veredito — https://github.com/acme/widgets/pull/42
- T12, item da fila: reenviar um upload que caiu — o envio tenta de novo antes de falhar
  - was: uma conexão caída falhava o envio e perdia o arquivo que o usuário escolheu
  - now: o envio tenta de novo após dois segundos, e falha guardando o arquivo
  - gain: rede instável não obriga a escolher o arquivo de novo  ·  risk: servidor lento espera 2s a mais pelo erro
Testes ok · Review ok · Critério âmbar: o vídeo anexo mostra o reenvio · Reversão ok · Fechamento ok
```

**A package's accumulated lane** writes line 1 once, for its one pull request. Each item
then takes its own entry and its own line 6, where Testes and Review read the package's
word. The ceiling is one line plus five per item.

## Where the block lives

- **The PR body opens with it.** Whoever writes or rewrites the body writes the block first:
  the PR's opening, a rewrite after review fixes, the strict form's final body.
- **The attended gate copies it from the body, and recomputes line 1 and line 6.** Collisions
  and closure run again here, since the other open PRs and the body may have moved. When a
  recomputed line differs, the gate writes it back into the body before printing.
- **A body with no block**, written before this file existed, gets one composed here from the
  trail and the diff, written at the top of the body, then printed.

## The trail sections — the PR body only

Written from the trail — the PR body, the issue it closes, the verdict comments — under the
block, never printed at the gate:

1. **Pointers resolved.** Every citation by number arrives with the sentence it names. A
   verdict citing "recommendation 2" is undecidable while the statements live in another
   artefact: open it and quote the statement inline. A number whose list stays ambiguous
   is reported as unresolved, by its number.
2. **Proposal → verdict → why**, one row per decision, naming where the field contradicted
   the proposal and which side won.
3. **Choices without data** — the uncertainties the author left scattered, gathered here.
4. **Evidence** — the block `/tk:verify` wrote, displayed and never re-derived.
5. **Merge mechanics** — `../../bin/tk-collisions <ref> <ref> ...` merges every pair of
   open branches for real. The forge cannot answer this: its `mergeable` field is blind
   between two PRs. Exit 1 reports a colliding pair, and line 1 names it.

**A PR with no trail gets a DEGRADED digest**, and line 1 adds `sem rastro` after the URL —
a commit straight to main, an issue nobody opened. Sections 1 and 2 have no source, so they
are named absent; sections 3 to 5 read off the diff and the repo, sources of their own.
