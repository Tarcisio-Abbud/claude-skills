// compact-veto.js — the tk mod: a package's subagent does not auto-compact.
//
// WHY IT EXISTS. The auto-compact window is the process's, so a subagent
// compacts at the orchestrator's threshold, mid-item, and loses the item it was
// holding. Claude Code 2.1.287 hands a mod the compaction before it runs:
// `session.compact` carries `agentId` for a subagent's (or a fork's) own
// transcript and none for the main conversation, and `{ skip }` vetoes it.
// Measured on 2.1.287 in three shapes (foreground Agent, idle orchestrator
// beside a background agent, active orchestrator beside one): every subagent
// compaction carried `agentId`, no main one did, and after a skip the subagent
// kept reading and the engine asked again at its next request.
//
// WHEN IT VETOES. All five, or it passes the event on untouched:
//   1. the trigger is `auto`, by the hook's matcher (a person's `/compact` and a
//      plugin's are theirs);
//   2. the event names an `agentId` (the main conversation is never vetoed);
//   3. a package pointer is readable (no package, no veto: most sessions);
//   4. the pointer's `session` is THIS session's id. The pointer is one file per
//      machine, so without this gate every session's subagents would lose their
//      compaction while any package ran. `$.session.id()` answers the main
//      session's id inside a subagent's event too (measured on 2.1.287);
//   5. the compaction window is a number below the model window. `auto`
//      folds the threshold and the recovery from a prompt that is too long into
//      one trigger, and no field tells them apart; refusing the recovery fails
//      the request. Under a compaction window below the model window, the subagent
//      the veto keeps whole still has the distance between the two to work in.
//      The model window read is the session's model's: a subagent on a model
//      with a smaller window than the window set is outside this assumption.
//
// WHAT ELSE A VETO MEANS. The settings `PreCompact` hooks run inside the
// engine, below the last mod's `next`, so a vetoed compaction never reaches
// `tk-compact-mark` and writes no ledger line (measured on 2.1.287).
//
// FAILING OPEN. A hook that throws before calling `next` is skipped and the
// compaction runs, so a pointer nobody can read, or a call the engine refuses,
// costs the veto and never the session. On a binary older than 2.1.287 no mod
// loads at all, and every subagent compacts as before.
//
// THE POINTER is `~/.claude/state/tk-package.json`, the address the compaction
// bins read; `TK_PACKAGE_POINTER` names another one, for a test or a probe.

export const VETO = 'tk: subagent compaction vetoed; the window belongs to the orchestrator'
const POINTER = '/.claude/state/tk-package.json'

// The verdict on an `auto` compaction, as a pure function of what the hook
// reads: the skip reason, or null to let the compaction run.
export function decide({ agentId, sessionId, pointer, compactWindow, modelWindow }) {
  if (typeof agentId !== 'string' || agentId === '') return null
  if (pointer === null || typeof pointer !== 'object' || Array.isArray(pointer)) return null
  if (typeof pointer.session !== 'string' || pointer.session === '') return null
  if (pointer.session !== sessionId) return null
  if (!Number.isFinite(compactWindow) || !Number.isFinite(modelWindow)) return null
  if (compactWindow >= modelWindow) return null
  return VETO
}

async function readPointer($) {
  const path = (await $.env.get('TK_PACKAGE_POINTER')) || `${await $.env.get('HOME')}${POINTER}`
  try {
    return JSON.parse(await $.fs.read(path))
  } catch {
    return null                       // no package running: the ordinary case
  }
}

export function register(on) {
  on('session.compact', { trigger: 'auto' }, async ($, e, next) => {
    const pointer = await readPointer($)
    const usage = await $.session.usage({ breakdown: 'summary' })
    const why = decide({
      agentId: e.agentId,
      sessionId: await $.session.id(),
      pointer,
      compactWindow: usage.context.breakdown?.rawMaxTokens,
      modelWindow: usage.context.window,
    })
    return why === null ? next(e) : { skip: why }
  })
}
