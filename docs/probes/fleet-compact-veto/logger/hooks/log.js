// Probe logger: one JSON file per event under $TK_PROBE_LOG.
async function put($, kind, value) {
  const dir = await $.env.get('TK_PROBE_LOG')
  if (!dir) return
  const id = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
  await $.fs.write(`${dir}/${kind}-${id}.json`, JSON.stringify(value))
}

export function register(on) {
  on('session.compact', async ($, e, next) => {
    const sessionId = await $.session.id()
    await put($, 'compact-in', { trigger: e.trigger, agentId: e.agentId ?? null, sessionId, messages: e.messages.length })
    const r = await next(e)
    await put($, 'compact-out', { trigger: e.trigger, agentId: e.agentId ?? null, skip: r?.skip ?? null, compacted: Array.isArray(r?.messages) })
    return r
  })
  on('agent.spawn', async ($, e, next) => {
    const r = await next(e)
    await put($, 'spawn', { parentAgentId: e.parentAgentId ?? null, background: e.background ?? null, result: r })
    return r
  })
  on('tool.call', { tool: 'Agent' }, async ($, e, next) => {
    const r = await next(e)
    await put($, 'agenttool', { callerAgentId: e.agentId ?? null, result: r })
    return r
  })
}
