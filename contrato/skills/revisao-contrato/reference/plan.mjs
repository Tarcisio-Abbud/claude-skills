#!/usr/bin/env node
// Runs revisao-contrato.workflow.js outside the Workflow tool, with the tool's globals stubbed.
//
//   node plan.mjs '<args as JSON>'     prints the plan line and `saida:`; exit 0, or 3 when an arg
//                                      is missing or the plan asks to be confirmed
//
// `agent` is stubbed to throw: plan mode spawning anything is a defect, and this run proves it
// did not. The test suite imports `load` to simulate a full review with a fake `agent`.
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const HERE = dirname(fileURLToPath(import.meta.url))
export const SCRIPT = join(HERE, 'revisao-contrato.workflow.js')

// The Workflow tool runs the body in an async context with these globals; so does this.
const GLOBALS = ['args', 'agent', 'parallel', 'pipeline', 'phase', 'log', 'workflow', 'budget']

export function load(path = SCRIPT) {
  const src = readFileSync(path, 'utf8')
  if (!/^export const meta = \{/.test(src)) throw new Error('script must begin with `export const meta = {`')
  const body = src.replace(/^export const meta/, 'const meta')
  const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor
  const fn = new AsyncFunction(...GLOBALS, body)
  return (env) => fn(...GLOBALS.map(g => env[g]))
}

export function baseEnv(args, overrides = {}) {
  const logs = []
  return {
    logs,
    args,
    agent: () => { throw new Error('agent() called: plan mode must spawn no agent') },
    parallel: async (thunks) => Promise.all(thunks.map(t => t().catch(() => null))),
    pipeline: async () => { throw new Error('pipeline() is not used by this script') },
    phase: () => {},
    log: (m) => logs.push(m),
    workflow: async () => { throw new Error('workflow() is not used by this script') },
    budget: { total: null, spent: () => 0, remaining: () => Infinity },
    ...overrides,
  }
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  const args = JSON.parse(process.argv[2] || '{}')
  args.modo = 'plano'
  const env = baseEnv(args)
  const result = await load()(env)
  console.log(result.linha)
  console.log(`saida: ${result.saida}`)
  console.log(`agentes despachados neste plano: 0`)
  process.exit(result.perguntar ? 3 : 0)
}
