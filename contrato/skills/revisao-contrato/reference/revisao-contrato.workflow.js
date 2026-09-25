export const meta = {
  name: 'revisao-contrato',
  description: 'Review a Brazilian contract along method lenses, verify single-lens altas, write one report',
  whenToUse: 'Only through the revisao-contrato skill, which prints the plan line and gathers the args first',
  phases: [
    { title: 'Scout', detail: 'one opus agent writes the ficha', model: 'opus' },
    { title: 'Lentes', detail: 'the core lenses in parallel', model: 'opus' },
    { title: 'Crítico', detail: 'adds at most two lenses', model: 'opus' },
    { title: 'Consolidar', detail: 'sonnet jobs sized by work', model: 'sonnet' },
    { title: 'Verificar', detail: 'one refuter for single-lens altas', model: 'opus' },
    { title: 'Relatório', detail: 'revisao.md and medias.md', model: 'opus' },
    { title: 'Aplicar', detail: 'second invocation only: edits per clause group', model: 'opus' },
  ],
}

// Every party fact enters through `args` and the ficha; this file carries none.
// Modes (args.modo): 'plano' returns the plan line and spawns NO agent; 'revisar' runs the
// review; 'aplicar' drafts the edits for the chosen ids. The plan is computed by the same
// code that enforces the cap at run time, so the line the user reads is the cap the run obeys.

const CAP = 30
const REFUTER_CHUNK = 35
const VERIFIER_RESERVE = 2
const EXPECTED_CONSOLIDATORS = 6
// Share of a 5-hour window per run. No measurement exists yet: the first acceptance run
// measures it with /usage before and after. Until then the plan line says "não medida".
const WINDOW_SHARE_PER_RUN = null

// The core lenses. `metodo` lives in lenses.md under the heading `## <key>`; the test suite
// checks that every key here has exactly one heading there and the reverse.
const LENSES = [
  { key: 'juridica-civil', model: 'opus', when: 'sempre' },
  { key: 'tributaria', model: 'opus', when: 'sempre' },
  { key: 'trabalhista', model: 'opus', when: 'servicos_ou_pf' },
  { key: 'adversaria', model: 'opus', when: 'sempre' },
  { key: 'mesa', model: 'opus', when: 'sempre' },
  { key: 'cenarios', model: 'opus', when: 'sempre' },
  { key: 'operacional', model: 'opus', when: 'sempre' },
  { key: 'referencias-cruzadas', model: 'sonnet', when: 'sempre' },
  { key: 'fidelidade', model: 'opus', when: 'acordo_previo' },
  { key: 'clareza', model: 'opus', when: 'sempre' },
]

const REQUIRED = ['contrato', 'nossa_parte', 'autoria', 'acordo_previo', 'data', 'skill_dir']
const MODELS = new Set(['opus', 'sonnet'])

const a = args || {}
const modo = a.modo || 'plano'
const MODOS = ['plano', 'revisar', 'aplicar']
// An unknown modo would otherwise fall through to a full review and spend agents.
if (!MODOS.includes(modo)) throw new Error(`revisao-contrato: modo "${modo}" desconhecido; use ${MODOS.join('|')}`)

function isoDate(s) { return typeof s === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(s) }
function dirOf(p) { const i = String(p).lastIndexOf('/'); return i < 0 ? '.' : String(p).slice(0, i) }
function stemOf(p) { const b = String(p).slice(String(p).lastIndexOf('/') + 1); const i = b.lastIndexOf('.'); return i <= 0 ? b : b.slice(0, i) }
function slug(s) { return String(s).toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') }
function hasAcordo(x) { return !!x.acordo_previo && x.acordo_previo !== 'none' }

function missingArgs(x) {
  const out = REQUIRED.filter(k => x[k] === undefined || x[k] === null || x[k] === '')
  if (x.data !== undefined && !isoDate(x.data)) out.push('data (YYYY-MM-DD)')
  if (x.nossa_parte && !/^(contratante|contratado|outro:.+)$/.test(x.nossa_parte)) out.push('nossa_parte (contratante|contratado|outro:<rótulo>)')
  if (x.autoria && !/^(nossa|deles)$/.test(x.autoria)) out.push('autoria (nossa|deles)')
  return out
}

function saidaOf(x) {
  if (x.saida) return String(x.saida).replace(/\/$/, '')
  if (!x.contrato || !x.data) return null
  return `${dirOf(x.contrato)}/revisao-${slug(stemOf(x.contrato))}-${x.data}`
}

// The plan: agent counts per role, before anything runs. `max` assumes every conditional
// lens fires and the critic adds two; consolidators take whatever the cap leaves.
function plan(x) {
  const core = LENSES.filter(l => l.when === 'sempre').length + (hasAcordo(x) ? 1 : 0)
  const conditional = 1 // trabalhista: decided by the scout
  const fixedMax = 1 + core + conditional + 1 + 2 + VERIFIER_RESERVE + 1
  const consolidatorsMax = CAP - fixedMax
  const expected = 1 + core + conditional + 1 + 2 + EXPECTED_CONSOLIDATORS + 1 + 1
  const faltando = missingArgs(x)
  const share = WINDOW_SHARE_PER_RUN === null ? 'fração da janela de 5h: não medida — rode /usage antes' : `≈${Math.round(WINDOW_SHARE_PER_RUN * expected / 28)}% da janela de 5h`
  const linha = `revisao-contrato · plano: ~${expected} agentes (teto ${CAP}; consolidadores ≤${consolidatorsMax}) · ` +
    `opus: scout, até ${core + conditional - 1} lentes, crítico, ≤2 lentes extras, verificador (high), relatório (high) · ` +
    `sonnet: referencias-cruzadas, ~${EXPECTED_CONSOLIDATORS} consolidadores · ${share}` +
    (faltando.length ? ` · FALTA: ${faltando.join(', ')}` : '')
  return {
    linha,
    agentes: { previsto: expected, teto: CAP, consolidadores_max: consolidatorsMax },
    faltando,
    perguntar: faltando.length > 0 || expected > CAP,
    saida: saidaOf(x),
  }
}

if (modo === 'plano') {
  const p = plan(a)
  log(p.linha)
  return p
}

const faltando = missingArgs(a)
if (faltando.length) throw new Error(`revisao-contrato: args ausentes ou inválidos: ${faltando.join(', ')}`)
// The apply step reads the report the review wrote: its directory is passed, never recomputed
// from contrato and data, which point elsewhere when the apply runs on another day.
if (modo === 'aplicar' && !a.saida) throw new Error('revisao-contrato: aplicar needs saida, the directory of the review it applies')
const SAIDA = saidaOf(a)
const SKILL = String(a.skill_dir).replace(/\/$/, '')
const LENSES_MD = `${SKILL}/reference/lenses.md`
const TEMPLATE_MD = `${SKILL}/reference/report-template.md`

// Every agent goes through here: model pinned (never inherited, never Fable) and the cap held.
let spawned = 0
function run(prompt, opts) {
  if (!MODELS.has(opts.model)) throw new Error(`model not pinned for ${opts.label}`)
  spawned += 1
  if (spawned > CAP) throw new Error(`cap of ${CAP} agents reached at ${opts.label}`)
  return agent(prompt, opts)
}

const bom = a.nossa_parte.startsWith('outro:') ? a.nossa_parte.slice(6) : a.nossa_parte
const GROUND = `You are one reviewer over a Brazilian contract. Good for us means good for the party "${bom}".
The text was drafted by ${a.autoria === 'nossa' ? 'US (we must find our own weaknesses before the counterparty does)' : 'THEM (we must find what they buried and what we must ask for)'}.
Files:
- the contract (Markdown, clause-numbered): ${a.contrato}
- the ficha (facts, parties, numbers, dates): ${SAIDA}/ficha.md — read it first
${(a.apoio || []).length ? `- supporting files, read when your method needs them: ${a.apoio.join(', ')}\n` : ''}Rules:
- Brazilian law. Cite the article or source of every legal claim; when you cannot verify it, set confianca "baixa" rather than asserting. Check statute text on planalto.gov.br.
- Report only what you would defend to a senior lawyer. Each finding names the clause (e.g. "7.2", "Anexo IV item 3", or "ausente"), the concrete problem, and replacement wording in contract register as "proposta".
- Findings in Portuguese (pt-BR). Return through the StructuredOutput tool.`

const FINDING = {
  type: 'object',
  properties: {
    clausula: { type: 'string' },
    categoria: { type: 'string' },
    severidade: { type: 'string', enum: ['alta', 'media', 'baixa'] },
    titulo: { type: 'string' },
    problema: { type: 'string' },
    proposta: { type: 'string', description: 'replacement wording' },
    confianca: { type: 'string', enum: ['alta', 'media', 'baixa'] },
    fontes: { type: 'array', items: { type: 'string' } },
    valor_em_risco: {
      type: 'object',
      properties: { estimativa: { type: 'string' }, base: { type: 'string', description: 'one line citing only numbers present in the contract or ficha, or n/d' } },
      required: ['estimativa', 'base'],
    },
  },
  required: ['clausula', 'categoria', 'severidade', 'titulo', 'problema', 'proposta', 'confianca', 'fontes'],
}
const FINDINGS = {
  type: 'object',
  properties: { resumo: { type: 'string', description: 'two to four sentences, pt-BR' }, findings: { type: 'array', items: FINDING } },
  required: ['resumo', 'findings'],
}

if (modo === 'aplicar') {
  const ids = Array.isArray(a.aplicar) ? a.aplicar : []
  if (!ids.length) throw new Error('revisao-contrato: aplicar needs an explicit list of ids (resolve "todas" with apply-edits.py ids)')
  phase('Aplicar')
  // Ids are `<clause-group>-NN`; one agent per clause group.
  const groups = {}
  for (const id of ids) (groups[String(id).replace(/-\d+$/, '')] ||= []).push(id)
  const names = Object.keys(groups).sort()
  if (names.length > CAP) throw new Error(`${names.length} clause groups exceed the cap of ${CAP}`)
  const EDITS = {
    type: 'object',
    properties: { arquivo: { type: 'string' }, edicoes: { type: 'integer' } },
    required: ['arquivo', 'edicoes'],
  }
  const done = await parallel(names.map(g => () => run(
    `ROLE: apply chosen review findings to one clause group of a contract. Do NOT edit the contract.
Read the contract ${a.contrato}, the report ${SAIDA}/revisao.md and ${SAIDA}/medias.md. For each id in [${groups[g].join(', ')}], take its ready-to-paste wording and turn it into exact edits.
Write ONE JSON file, ${SAIDA}/aplicar/${g}.json, shaped {"edits":[{"id":"<id>","antes":"<exact substring of the current contract, unique in it>","depois":"<replacement>"}]}. "antes" must match the contract byte for byte and exactly once; extend it with neighbouring words until it does. Keep "depois" as short as the finding allows: the text has a word budget.
Return the file path and the edit count.`,
    { label: `aplicar:${g}`, phase: 'Aplicar', schema: EDITS, model: 'opus' })))
  return { modo, saida: SAIDA, grupos: names, arquivos: done.filter(Boolean).map(r => r.arquivo), agentes: spawned }
}

// ---------- revisar ----------
const p = plan(a)
log(p.linha)

phase('Scout')
const FICHA = {
  type: 'object',
  properties: {
    linhas: { type: 'integer' },
    servicos_ou_pf: { type: 'boolean', description: 'true when the contract has a services element or a pessoa-física party' },
    clausulas: { type: 'integer' },
  },
  required: ['linhas', 'servicos_ou_pf', 'clausulas'],
}
const ficha = await run(`ROLE: scout. Read the contract ${a.contrato}${hasAcordo(a) ? ` and the prior agreement ${a.acordo_previo}` : ''}${(a.apoio || []).length ? ` and skim ${a.apoio.join(', ')}` : ''}.
Write the ficha to ${SAIDA}/ficha.md, at most 80 lines, pt-BR, facts only, following the section "## ficha" of ${LENSES_MD}. This is the only file you write.
Good for us means good for "${bom}"; the text was drafted by ${a.autoria === 'nossa' ? 'us' : 'them'}.`,
  { label: 'scout', phase: 'Scout', schema: FICHA, model: 'opus' })
if (!ficha) throw new Error('scout returned nothing; the ficha is the ground of every lens')

phase('Lentes')
const active = LENSES.filter(l => l.when === 'sempre' || (l.when === 'acordo_previo' && hasAcordo(a)) || (l.when === 'servicos_ou_pf' && ficha.servicos_ou_pf))
const lensPrompt = (key, metodo) => `${GROUND}

LENS: ${key}. ${metodo || `Your method is the section "## ${key}" of ${LENSES_MD}; read that section and follow it, framing by autoria "${a.autoria}".`}
${key === 'fidelidade' ? `Prior agreement, read in full: ${a.acordo_previo}\n` : ''}Also write your structured result, verbatim, as JSON to ${SAIDA}/brutos/${key}.json — the one file you may write.`
const lensOpts = l => ({ label: `lente:${l.key}`, phase: 'Lentes', schema: FINDINGS, model: l.model })
const round1 = await parallel(active.map(l => () => run(lensPrompt(l.key), lensOpts(l)).then(r => r && { key: l.key, ...r })))
const lensResults = round1.filter(Boolean)
log(`Lentes: ${lensResults.length}/${active.length} voltaram; ${lensResults.reduce((n, r) => n + r.findings.length, 0)} achados brutos`)

phase('Crítico')
const digest = lensResults.map(r => `## ${r.key}\n${r.resumo}\n${r.findings.map(f => `- [${f.severidade}] ${f.clausula}: ${f.titulo}`).join('\n')}`).join('\n\n')
const CRITIC = {
  type: 'object',
  properties: {
    extras: { type: 'array', maxItems: 2, items: { type: 'object', properties: { key: { type: 'string' }, justificativa: { type: 'string' }, metodo: { type: 'string', description: 'a full method prompt in English' } }, required: ['key', 'justificativa', 'metodo'] } },
    rejeitadas: { type: 'array', items: { type: 'string', description: 'one line each' } },
  },
  required: ['extras', 'rejeitadas'],
}
const critic = await run(`${GROUND}

ROLE: completeness critic, following the section "## critico" of ${LENSES_MD}. The lenses below already ran. Name at most two lenses still missing whose findings would likely change the text; reject the rest with one line each.

${digest}`, { label: 'critico', phase: 'Crítico', schema: CRITIC, model: 'opus' })
// An extra whose key slugs onto a lens that already ran is suffixed: brutos/<key>.json and the
// raw ids `<key>-<n>` would otherwise collide with that lens's own.
const takenKeys = new Set(active.map(l => l.key))
const extras = ((critic && critic.extras) || []).slice(0, 2).map(e => {
  const base = slug(e.key) || 'extra'
  let key = base
  for (let n = 2; takenKeys.has(key); n++) key = `${base}-extra${n > 2 ? n - 1 : ''}`
  takenKeys.add(key)
  return { key, metodo: e.metodo, justificativa: e.justificativa }
})
const round2 = await parallel(extras.map(e => () => run(lensPrompt(e.key, e.metodo), { label: `lente+:${e.key}`, phase: 'Crítico', schema: FINDINGS, model: 'opus' }).then(r => r && { key: e.key, ...r })))
const allLenses = [...lensResults, ...round2.filter(Boolean)]

phase('Consolidar')
const raw = []
for (const r of allLenses) r.findings.forEach((f, i) => raw.push({ ...f, id: `${r.key}-${i + 1}`, lente: r.key }))
function bucketOf(c) {
  const s = String(c || '')
  let m = s.match(/anexo\s*([ivx]+|\d+)\b/i); if (m) return `anexo-${m[1].toLowerCase()}`
  if (/considerando/i.test(s)) return 'considerandos'
  // A clause number that leads the anchor wins over the words: "7.3 (partes relacionadas)" is clause 7.
  m = s.match(/^\s*(?:cl[aá]usula\s*)?(\d{1,3})(?:\.\d+)*/i); if (m) return `c${m[1]}`
  if (/partes|assinatura|qualifica/i.test(s)) return 'partes'
  m = s.match(/(\d{1,3})(?:\.\d+)*/); if (m) return `c${m[1]}`
  return 'geral'
}
const clareza = raw.filter(f => f.lente === 'clareza')
const substantive = raw.filter(f => f.lente !== 'clareza')
const buckets = {}
for (const f of substantive) (buckets[bucketOf(f.clausula)] ||= []).push(f)
// Buckets of 15 or more go alone; the rest are packed into jobs of at most 20.
let jobs = []
let pack = null
for (const b of Object.keys(buckets).sort()) {
  if (buckets[b].length >= 15) { jobs.push({ names: [b], items: buckets[b] }); continue }
  if (!pack || pack.items.length + buckets[b].length > 20) { pack = { names: [], items: [] }; jobs.push(pack) }
  pack.names.push(b); pack.items.push(...buckets[b])
}
const consolidatorBudget = CAP - spawned - VERIFIER_RESERVE - 1
while (jobs.length > consolidatorBudget && jobs.length > 1) {
  jobs.sort((x, y) => x.items.length - y.items.length)
  const [j1, j2] = jobs.splice(0, 2)
  jobs.push({ names: [...j1.names, ...j2.names], items: [...j1.items, ...j2.items] })
  log(`teto: dois jobs de consolidação fundidos (${j1.names.join('+')} + ${j2.names.join('+')})`)
}
const MERGED = {
  type: 'object',
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          ...FINDING.properties,
          id: { type: 'string', description: '<bucket>-01, <bucket>-02, ... using the bucket of the finding' },
          origem: { type: 'array', items: { type: 'string' }, description: 'ids of the raw findings merged here' },
          divergencia: { type: 'string' },
        },
        required: ['id', 'origem', ...FINDING.required],
      },
    },
  },
  required: ['findings'],
}
const merged = await parallel(jobs.map(j => () => run(`ROLE: consolidate review findings about the contract ${a.contrato} (read the clauses they cite). Merge findings that describe the same problem; keep distinct problems apart. Every raw id must appear in exactly one "origem". Keep the highest severidade among merged findings and the best proposta; name disagreements in "divergencia". Bucket names for ids: ${j.names.join(', ')}. pt-BR.

RAW FINDINGS (JSON):
${JSON.stringify(j.items)}`, { label: `consolidar:${j.names.join('+')}`, phase: 'Consolidar', schema: MERGED, model: 'sonnet' }).then(r => ({ job: j, findings: r && r.findings })))
)
// Artifact check: every raw id in exactly one origem; a missing id passes through raw.
const all = []
const checkLog = []
for (const { job, findings } of merged.filter(Boolean)) {
  const want = new Set(job.items.map(f => f.id))
  if (!findings) { checkLog.push(`${job.names.join('+')}: sem resultado → ${job.items.length} brutos repassados`); all.push(...job.items.map(f => ({ ...f, origem: [f.id] }))); continue }
  const seen = new Map()
  for (const m of findings) {
    m.origem = (m.origem || []).filter(o => want.has(o) && !seen.has(o))
    for (const o of m.origem) seen.set(o, true)
  }
  const kept = findings.filter(m => m.origem.length)
  const missing = job.items.filter(f => !seen.has(f.id))
  if (missing.length || kept.length !== findings.length) checkLog.push(`${job.names.join('+')}: ${missing.length} ids ausentes repassados brutos; ${findings.length - kept.length} fusões vazias descartadas`)
  all.push(...kept, ...missing.map(f => ({ ...f, origem: [f.id], nota: 'não consolidado' })))
}
// Ids must be unique across jobs: the verifier's verdicts and the apply step key on them.
const usedIds = new Set()
for (const f of all) {
  let id = f.id || `${bucketOf(f.clausula)}-01`
  const base = id.replace(/-\d+$/, '')
  for (let n = 2; usedIds.has(id); n++) id = `${base}-${String(n).padStart(2, '0')}`
  if (id !== f.id && f.id) checkLog.push(`id repetido ${f.id} → ${id}`)
  f.id = id
  usedIds.add(id)
}
for (const l of checkLog) log(`checagem — ${l}`)
log(`Consolidação: ${substantive.length} → ${all.length} (+${clareza.length} de clareza sem consolidar)`)

phase('Verificar')
// Convergence is agreement between LENSES: two findings of one lens merged are still one lens.
const lensOfRaw = new Map(raw.map(f => [f.id, f.lente]))
for (const f of all) f.convergencia = new Set(f.origem.map(o => lensOfRaw.get(o) || o)).size
const lone = all.filter(f => f.severidade === 'alta' && f.convergencia === 1)
const convergent = all.filter(f => f.severidade === 'alta' && f.convergencia >= 2)
const room = Math.max(1, CAP - spawned - 1)
const chunkSize = Math.max(REFUTER_CHUNK, Math.ceil(lone.length / room))
const chunks = []
for (let i = 0; i < lone.length; i += chunkSize) chunks.push(lone.slice(i, i + chunkSize))
log(`Altas: ${convergent.length} convergentes (sem refutador), ${lone.length} de lente única → ${chunks.length} verificador(es)`)
const VERDICTS = {
  type: 'object',
  properties: {
    verdicts: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          id: { type: 'string' },
          refutado: { type: 'boolean' },
          angulo: { type: 'string', enum: ['direito', 'texto', 'materialidade', 'nenhum'] },
          motivo: { type: 'string' },
          ajuste: { type: 'string' },
          severidade_final: { type: 'string', enum: ['alta', 'media', 'baixa'] },
        },
        required: ['id', 'refutado', 'angulo', 'motivo', 'severidade_final'],
      },
    },
  },
  required: ['verdicts'],
}
const verdictSets = await parallel(chunks.map((chunk, i) => () => run(`${GROUND}

ROLE: refuter. Follow the section "## refutador" of ${LENSES_MD}: three angles in order — direito, texto, materialidade — stopping at the first that bites. One verdict per finding.

FINDINGS (JSON):
${JSON.stringify(chunk)}`, { label: `verificar:${i + 1}/${chunks.length}`, phase: 'Verificar', schema: VERDICTS, model: 'opus', effort: 'high' })))
const verdictById = {}
for (const vs of verdictSets.filter(Boolean)) for (const v of vs.verdicts) verdictById[v.id] = v
const judged = lone.map(f => ({ ...f, veredito: verdictById[f.id] || null }))
const refuted = judged.filter(f => f.veredito && f.veredito.refutado)
const survivors = judged.filter(f => !(f.veredito && f.veredito.refutado)).map(f => ({ ...f, severidade: (f.veredito && f.veredito.severidade_final) || f.severidade }))

phase('Relatório')
const altas = [...convergent.map(f => ({ ...f, status: `convergente (${f.convergencia} lentes)` })), ...survivors.filter(f => f.severidade === 'alta').map(f => ({ ...f, status: f.veredito ? 'verificada' : 'não verificada' }))]
const medias = [...all.filter(f => f.severidade === 'media'), ...survivors.filter(f => f.severidade === 'media')]
const baixas = [...all.filter(f => f.severidade === 'baixa'), ...survivors.filter(f => f.severidade === 'baixa')]
const REPORT = {
  type: 'object',
  properties: { linhas: { type: 'integer' }, perguntas: { type: 'integer' }, altas: { type: 'integer' } },
  required: ['linhas', 'perguntas', 'altas'],
}
const report = await run(`ROLE: write the review report, pt-BR, for a cold reader. Follow ${TEMPLATE_MD} exactly: its section order, table shapes and limits (≤400 lines, ≤10 lawyer questions). autoria = "${a.autoria}"; good for us = good for "${bom}". Read the contract ${a.contrato} and the ficha ${SAIDA}/ficha.md.
Write ${SAIDA}/revisao.md and ${SAIDA}/medias.md; these are the only files you write. Date of the review: ${a.data}.

ALTAS (JSON; apply each veredito.ajuste): ${JSON.stringify(altas)}
REFUTED (one line each, with the winning angle): ${JSON.stringify(refuted.map(f => ({ id: f.id, clausula: f.clausula, titulo: f.titulo, angulo: f.veredito.angulo, motivo: f.veredito.motivo })))}
MEDIAS (candidates for the ≤10 questions; the rest go to medias.md): ${JSON.stringify(medias)}
BAIXAS: ${JSON.stringify(baixas.map(f => ({ id: f.id, clausula: f.clausula, titulo: f.titulo })))}
CLAREZA (raw): ${JSON.stringify(clareza)}
LENS SUMMARIES: ${JSON.stringify(allLenses.map(r => ({ lente: r.key, resumo: r.resumo })))}
CRITIC: added ${JSON.stringify(extras.map(e => ({ key: e.key, justificativa: e.justificativa })))}; rejected ${JSON.stringify((critic && critic.rejeitadas) || [])}
COUNTS: ${raw.length} brutos → ${all.length} consolidados (+${clareza.length} clareza) → ${lone.length} verificados, ${refuted.length} refutados. Agents: ${spawned + 1}. Consolidation notes: ${JSON.stringify(checkLog)}`,
  { label: 'relatorio', phase: 'Relatório', schema: REPORT, model: 'opus', effort: 'high' })

return {
  modo,
  saida: SAIDA,
  agentes: spawned,
  contagens: { brutos: raw.length, substantivos: substantive.length, em_origem: new Set(all.flatMap(f => f.origem)).size, origens: all.reduce((n, f) => n + f.origem.length, 0), consolidados: all.length, clareza: clareza.length, altas_convergentes: convergent.length, lente_unica: lone.length, refutadas: refuted.length },
  lentes: allLenses.map(r => r.key),
  extras: extras.map(e => e.key),
  relatorio: report,
  checagem: checkLog,
}
