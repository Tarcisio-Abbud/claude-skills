// Behaviour proof for the tk mod, `../hooks/compact-veto.js`.
//
// Run: claude plugin test tk            (the first-party kit; no session, no network)
// Read by: test_compact_hooks.py, `TheModVeto`, which runs this file and reports
// each test by name, so `mutations_compact_hooks.py` can name the one a mutant
// must break.
//
// Each test raises `session.compact` through the mod with the engine's answers
// stubbed: the pointer file, this session's id, the window figures, and the
// compaction the engine would run (one summary message), so a result with
// `messages` is a compaction let through and one with `skip` is a veto.
import { expect, mock, test } from 'claude-code/testing'
import { VETO, decide } from '../hooks/compact-veto.js'

const SESSION = '00000000-1111-2222-3333-444444444444'
const AGENT = 'a0000000000000000'
const HOME = '/home/someone'
const POINTER_PATH = HOME + '/.claude/state/tk-package.json'
const PACKAGE = { package: 'probe', ledger: '/x/ledger.md', handoff: '/x/handoff.md', session: SESSION }

const READ = { role: 'user', text: 'a long read', toolUses: [] }
const SUMMARY = { role: 'user', text: 'the summary', toolUses: [] }

type Setup = { pointer?: unknown; session?: string; raw?: number; window?: number; env?: Record<string, string> }

function stub(on: any, s: Setup = {}) {
  const pointer = 'pointer' in s ? s.pointer : PACKAGE
  mock.env(on, s.env ?? { HOME })
  on('fs.read', ($: any, e: any) =>
    pointer !== undefined && e.path.endsWith(s.env?.TK_PACKAGE_POINTER ?? POINTER_PATH)
      ? { value: typeof pointer === 'string' ? pointer : JSON.stringify(pointer) }
      : { deny: 'no such file' })
  on('session.id', () => ({ value: s.session ?? SESSION }))
  on('session.usage', () => ({
    value: { context: { window: s.window ?? 1000000, breakdown: { rawMaxTokens: s.raw ?? 100000 } }, rateLimits: [] },
  }))
  on('session.compact', () => ({ messages: [SUMMARY] }))
}

const compact = ($: any, fields: Record<string, unknown> = {}) =>
  $.session.compact({ trigger: 'auto', agentId: AGENT, messages: [READ], ...fields })

test('a subagent auto-compaction in the package session is vetoed', async ($, on) => {
  stub(on)
  const r = await compact($)
  expect(r.skip).toBe(VETO)
})

test('the main conversation is never vetoed', async ($, on) => {
  stub(on)
  const r = await compact($, { agentId: undefined })
  expect(r.skip).toBeUndefined()
  expect(r.messages).toBeDefined()
})

test('a manual compaction of a subagent is not vetoed', async ($, on) => {
  stub(on)
  const r = await compact($, { trigger: 'manual' })
  expect(r.skip).toBeUndefined()
})

test('with no package pointer nothing is vetoed', async ($, on) => {
  stub(on, { pointer: undefined })
  const r = await compact($)
  expect(r.skip).toBeUndefined()
  expect(r.messages).toBeDefined()
})

test('a pointer nobody can parse vetoes nothing', async ($, on) => {
  stub(on, { pointer: '{not json' })
  const r = await compact($)
  expect(r.skip).toBeUndefined()
})

test('another session subagents compact while a package runs', async ($, on) => {
  stub(on, { session: 'ffffffff-1111-2222-3333-444444444444' })
  const r = await compact($)
  expect(r.skip).toBeUndefined()
})

test('a pointer that names no session vetoes nothing', async ($, on) => {
  stub(on, { pointer: { package: 'probe', ledger: '/x/ledger.md' } })
  const r = await compact($)
  expect(r.skip).toBeUndefined()
})

test('a window at the model limit vetoes nothing', async ($, on) => {
  stub(on, { raw: 1000000, window: 1000000 })
  const r = await compact($)
  expect(r.skip).toBeUndefined()
})

test('the pointer address can be named for a probe', async ($, on) => {
  stub(on, { env: { HOME, TK_PACKAGE_POINTER: '/probe/pointer.json' } })
  const r = await compact($)
  expect(r.skip).toBe(VETO)
})

test('decide refuses every input that is not a veto', () => {
  const base = { agentId: AGENT, sessionId: SESSION, pointer: PACKAGE, compactWindow: 100000, modelWindow: 1000000 }
  expect(decide(base)).toBe(VETO)
  expect(decide({ ...base, agentId: '' })).toBe(null)
  expect(decide({ ...base, pointer: null })).toBe(null)
  expect(decide({ ...base, pointer: [PACKAGE] })).toBe(null)
  expect(decide({ ...base, pointer: { ...PACKAGE, session: '' }, sessionId: '' })).toBe(null)
  expect(decide({ ...base, compactWindow: undefined })).toBe(null)
  expect(decide({ ...base, compactWindow: 1200000 })).toBe(null)
})
