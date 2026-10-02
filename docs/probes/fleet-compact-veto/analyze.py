"""Summarise one probe run: spawns, Agent results, compaction outcomes per
agent id (from the logger), and compact_boundary entries per transcript.

Usage: analyze.py <log dir> <session id>
"""
import json,glob,os,collections,sys
L,SID=sys.argv[1],sys.argv[2]
def rows(k):
    fs=sorted(glob.glob(f"{L}/{k}-*.json"), key=lambda f:int(os.path.basename(f).split('-')[-2]))
    return [json.load(open(f)) for f in fs]
print("spawns (parent -> child, background):")
for r in rows('spawn'): print("  ", r['parentAgentId'], '->', r['result'].get('agentId'), r['background'])
print("Agent tool results as the caller saw them:")
for r in rows('agenttool'):
    res=r['result'].get('result')
    print("  caller", r['callerAgentId'], '->', res.get('status') if isinstance(res,dict) else res[:80], res.get('agentId') if isinstance(res,dict) else '')
c=collections.Counter((r['agentId'],r['trigger'],'skip' if r['skip'] else ('compacted' if r['compacted'] else 'other')) for r in rows('compact-out'))
print("compaction outcomes per agentId:")
for k,v in sorted(c.items(), key=str): print("  ",k,v)
print("sessionId seen by the mod:", {r['sessionId'] for r in rows('compact-in')})
D=glob.glob(os.path.expanduser(f"~/.claude/projects/*/{SID}"))[0]
print("compact_boundary entries per transcript:")
for p in [D+'.jsonl']+sorted(glob.glob(D+'/subagents/agent-*.jsonl')):
    n=0; peak=0
    for l in open(p):
        r=json.loads(l)
        if r.get('subtype')=='compact_boundary': n+=1
        m=r.get('message')
        if isinstance(m,dict) and m.get('usage'):
            u=m['usage']; peak=max(peak,u.get('input_tokens',0)+u.get('cache_read_input_tokens',0)+u.get('cache_creation_input_tokens',0))
    print("  ", os.path.basename(p), "boundaries", n, "peak_ctx", peak)
