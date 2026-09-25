// Drives revisao-contrato.workflow.js with a fake `agent` and prints what it was asked to do.
//   node sim.mjs '<args JSON>' '<scenario JSON>'
// Output (stdout, JSON): {calls: [{label, model, effort, schemaKeys, prompt}], result, logs, error}
import { load, baseEnv } from '../skills/revisao-contrato/reference/plan.mjs'

const args = JSON.parse(process.argv[2])
const sc = JSON.parse(process.argv[3] || '{}')
const calls = []

function finding(clausula, severidade, titulo) {
  return { clausula, categoria: 'x', severidade, titulo, problema: 'p', proposta: 'q', confianca: 'media', fontes: [] }
}

async function agent(prompt, opts) {
  calls.push({ label: opts.label, model: opts.model, effort: opts.effort || null, schemaKeys: Object.keys((opts.schema || {}).properties || {}), prompt })
  const l = opts.label
  if (l === 'scout') return { linhas: 60, servicos_ou_pf: !!sc.servicos_ou_pf, clausulas: 40 }
  if (l.startsWith('lente')) {
    const key = l.split(':')[1]
    // Every lens raises an alta on clause 4.2 (convergent) and one of its own (single-lens).
    const own = sc.lensAltas === false ? [] : [finding(`${10 + key.length}.1`, 'alta', `own ${key}`)]
    // sc.twiceFrom: that lens raises two altas on one clause of its own, which the fake
    // consolidator merges — one lens, two raw ids.
    const twice = sc.twiceFrom === key ? [finding('77.1', 'alta', 'a'), finding('77.1', 'alta', 'b')] : []
    // sc.anchorFrom: that lens raises one finding anchored on sc.anchor.
    const anchored = sc.anchorFrom === key ? [finding(sc.anchor, 'media', 'anchored')] : []
    return { resumo: `r ${key}`, findings: [finding('4.2', 'alta', 'prazo'), ...own, ...twice, ...anchored, finding('3.1', 'media', 'm')] }
  }
  if (l === 'critico') return { extras: (sc.extras || []).map(k => ({ key: k, justificativa: 'j', metodo: 'm' })), rejeitadas: ['x'] }
  if (l.startsWith('consolidar')) {
    const items = JSON.parse(prompt.slice(prompt.indexOf('RAW FINDINGS (JSON):') + 'RAW FINDINGS (JSON):'.length))
    const byClause = {}
    for (const f of items) (byClause[f.clausula] ||= []).push(f)
    const out = Object.values(byClause).map((fs, i) => ({ ...fs[0], id: `g-${String(i + 1).padStart(2, '0')}`, origem: fs.map(f => f.id) }))
    if (sc.dropOne && out.length && out[0].origem.length > 1) out[0].origem.pop()
    return { findings: out }
  }
  if (l.startsWith('verificar')) {
    const items = JSON.parse(prompt.slice(prompt.indexOf('FINDINGS (JSON):') + 'FINDINGS (JSON):'.length))
    return { verdicts: items.map((f, i) => ({ id: f.id, refutado: i % 2 === 0, angulo: i % 2 === 0 ? 'texto' : 'nenhum', motivo: 'm', severidade_final: 'alta' })) }
  }
  if (l === 'relatorio') return { linhas: 300, perguntas: 8, altas: 5 }
  if (l.startsWith('aplicar')) return { arquivo: `/x/${l}.json`, edicoes: 1 }
  throw new Error(`unexpected label ${l}`)
}

const env = baseEnv(args, sc.noAgent ? {} : { agent })
let result = null, error = null
try { result = await load()(env) } catch (e) { error = String(e.message || e) }
console.log(JSON.stringify({ calls, result, logs: env.logs, error }))
