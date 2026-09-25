# Lens methods

Each `##` section is one prompt, read by the agent the workflow names it to. A lens section is
a METHOD: what to probe and how. Party facts come from the ficha and the contract, never from
here. `revisao-contrato.workflow.js` holds the list of lenses; the suite checks that every key
there has exactly one section here.

Every lens receives the contract, the ficha and the GROUND sentence ("good for us means good for
<nossa_parte>", plus who drafted the text). Findings are written in pt-BR; `valor_em_risco`
cites only numbers present in the contract or the ficha, or says `n/d`.

## ficha

Write the facts every lens needs, at most 80 lines, pt-BR, no opinions:

1. Parties, their roles, and who signs — for which clauses each signatory binds itself
   (an intervening party signing "for acknowledgement" binds itself to nothing).
2. Cap table or ownership before and after any transfer the text provides for.
3. Every date, deadline, ratio, percentage, threshold and quorum, each with the arithmetic a
   reader must check (spans in months, denominators, reachable majorities).
4. Money flows: who pays whom, on what base, when; which tax each party bears on each flow.
5. Defined terms, terms used but never defined, and every placeholder (`[•]`, `XX`, blanks).
6. Statutes and regulations the text relies on, by article.
7. One line: does the contract have a services element or a pessoa-física party (the answer
   decides whether the `trabalhista` lens runs).

## juridica-civil

Test each clause for validity and enforceability under the Código Civil and the CPC. Probe:
who signed for which obligation, and whether the obligation binds that signatory; conditions
that depend on one party's will alone (CC art. 122); penalties above the principal obligation
(CC art. 412) and whether the remedy actually reaches money; dispute resolution that works in
practice (arbitration clause form, venue); termination and its effects on accrued rights;
statutes amended recently — fetch the article text on planalto.gov.br before relying on it.

## tributaria

Map every money flow in the contract to its tax, for each party: IRPF/IRPJ, CSLL, PIS/COFINS,
ISS, INSS/contribuição patronal, IOF, ITCMD, ganho de capital. For each flow state gross vs
net, what is withheld at source and by whom, and who bears it. Flag every flow whose tax
treatment depends on a choice the parties must make before signing (vehicle, regime, label of
the payment), and every label that changes the tax (distribution vs remuneration, loan vs
advance, reimbursement).

## trabalhista

Look for vínculo empregatício risk in both directions: subordination, habituality, personal
performance and onerosity written into the text, or implied by its operation (fixed hours,
exclusivity, reporting lines, benefits). Say which CLT smells matter for this contract and
which are harmless, and what wording lowers the risk without changing the economics.
Pejotização counts both ways: the risk to the party paying and the rights lost by the party
paid.

## adversaria

When autoria is `nossa`: act as the counterparty's lawyer reading our draft. Hunt loopholes,
undefined terms that the other side will define in its favour, silences (events the text does
not cover), and obligations we wrote on ourselves without noticing. When autoria is `deles`:
act as our lawyer reading their draft. Hunt traps, asymmetries (rights for them, duties for
us), buried waivers, one-sided discretion, and whatever the text makes cheap for them and
expensive for us.

## mesa

The negotiation table. When autoria is `nossa`: list what the counterparty will attack, and
classify each of our provisions FIRME (defend), TROCÁVEL (give for something) or SUPÉRFLUO
(drop before they ask). When autoria is `deles`: list what we ask for, what we can trade, and
the walk-away point. Each row names the clause and one line of reasoning.

## cenarios

Run at least twelve concrete scenarios through the LITERAL text and report what it yields in
each: exit or termination at month N, death or incapacity of a party, sale of the business,
change of control, payment in kind, deferral or reclassification of revenue, gaming a
threshold or a quorum, insolvency, a dispute mid-term. For each finding fill `valor_em_risco`
with the amount at stake and a one-line base built only from numbers in the contract or the
ficha; write `n/d` when no such number exists.

## operacional

Can a stranger execute this contract month after month without calling the drafters? Probe
every recurring obligation: who computes what, from which source document, by which date, and
what happens when it is late or disputed. List every operational term the text uses without
defining (report, statement, approval, "resultado", "receita"), and every step that depends on
information one party controls and the other cannot audit.

## referencias-cruzadas

Mechanical consistency. Check the clause numbering is continuous; every cross-reference points
at a clause that exists and says what the reference assumes; every defined term is used with
one meaning and one spelling; every arithmetic statement adds up (spans, percentages that must
sum, denominators); no placeholder is left; the signature block matches the parties in the
preamble.

## fidelidade

Build a checklist from the prior agreement (`acordo_previo`), item by item, and mark each
against the contract: PRESENTE, DIVERGENTE (quote both), AUSENTE, or creep (in the contract,
never agreed). A divergence in our favour is still a finding: the counterparty will read it as
bad faith.

## clareza

Measure the text: words, clauses, sentences over 40 words, nested exceptions ("salvo... exceto
se... ressalvado"), editorial leaks (drafting notes, comments, alternatives left in). Give a
restructuring plan with the estimated word reduction per move, and name what must NOT be cut
because another clause or a scenario depends on it. No worked rewrites.

## critico

You read lens summaries and finding titles, not the contract. Name at most two lenses still
missing whose findings would likely change the text — succession or marital regime of a party,
and a reverse reading of our own liabilities, are the kind that bit before. For each: a key
(kebab-case), two or three sentences of justification, and a full method prompt in the style
of the sections above. Reject every other candidate with one line.

## refutador

For each single-lens alta, try to refute it on three angles, in this order, stopping at the
first that bites:

1. **direito** — does the cited article (or the right one) say what the finding relies on, and
   is the proposed wording valid? Fetch the statute text when in doubt. A wrong article number
   under a right premise is an `ajuste`, not a refutation.
2. **texto** — is the problem already handled elsewhere in the contract, or is it a misreading?
   Would the proposal contradict another clause?
3. **materialidade** — does the defect cost money or the signature in a realistic scenario? Is
   the cure worse than the defect?

When no angle bites, `refutado` is false. You may downgrade (`severidade_final`) with the
reason. Refute on evidence, never on vague doubt; keep on evidence, never on sympathy.
