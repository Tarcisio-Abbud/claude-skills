#!/usr/bin/env bash
# Probe for the fleet's compact veto (Claude Code 2.1.287+). Spends quota: one
# Sonnet orchestrator and four Haiku subagents, about 120k tokens each at most.
#
# A main session stands in for the fleet orchestrator: it writes a pointer with
# its session and an empty `exempt` list, dispatches two background project
# runs, and appends each run's agentId. Each run dispatches one foreground
# implementer that reads past the 80k threshold, then reads past it itself.
# Expected: every implementer compaction is skipped and its transcript holds no
# compact_boundary; each project run compacts.
#
# The mod under test is a COPY of tk/hooks/compact-veto.js whose pointer
# variable is renamed, so the installed tk plugin (reading the real pointer,
# which never names the probe's session) stays inert beside it.
#
# Usage: run.sh <work dir>
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
REPO=$(cd "$HERE/../../.." && pwd)
W=$(mkdir -p "$1" && cd "$1" && pwd)
mkdir -p "$W/corpus" "$W/log" "$W/veto/.claude-plugin" "$W/veto/hooks" "$W/run"

cat "$REPO/tk/bin/tk-queue" "$REPO/tk/tests/test_tk_queue.py" > "$W/corpus/all.txt"
(cd "$W/corpus" && split -C 30000 -d -a 2 --additional-suffix=.txt all.txt c- && rm all.txt)
echo '{ "name": "tkvetocopy", "version": "0.1.0", "description": "probe copy of the tk compact veto" }' \
  > "$W/veto/.claude-plugin/plugin.json"
echo '{ "modules": ["./compact-veto.js"] }' > "$W/veto/hooks/hooks.json"
sed 's/TK_PACKAGE_POINTER/TK_PROBE_POINTER/g' "$REPO/tk/hooks/compact-veto.js" > "$W/veto/hooks/compact-veto.js"

files() { local out=""; for i in "$@"; do out+="$W/corpus/c-$i.txt, "; done; printf '%s' "${out%, }"; }
IMPL="Use the Read tool to read these files in order, ONE Read call per message: never put two Read calls in the same message, wait for each result before the next call. Files: $(files 00 01 02 03 04 05 06 07 08 09). After the last one, reply with the single word DONE."
RUN="You are a project run. Step 1: dispatch exactly ONE subagent with the Agent tool: subagent_type general-purpose, model haiku, in the FOREGROUND (do not set run_in_background). Its prompt, verbatim: \\\"$IMPL\\\" Step 2: when it returns (whatever it returns, never dispatch it again), use the Read tool yourself to read these files in order, ONE Read call per message, never two Read calls in the same message: $(files 10 11 12 13 14 15 16 17). Step 3: reply with the single word DONE."
cat > "$W/run/prompt.txt" <<PROMPT
You are a fleet orchestrator in a measurement. Follow these steps exactly.

Step 1. Run this Bash command verbatim, before any dispatch:
printf '%s\n' "{\"package\": \"fleet-probe\", \"session\": \"\$CLAUDE_CODE_SESSION_ID\", \"exempt\": []}" > "\$TK_PROBE_POINTER"

Step 2. In ONE message, dispatch two subagents with the Agent tool, both with subagent_type general-purpose, model haiku, run_in_background true, descriptions "project run A" and "project run B". Each one's prompt is, verbatim:
"$RUN"

Step 3. Each Agent result names the launched agent's agentId. For EACH of the two ids, run this Bash command with the id in place of AGENT_ID:
python3 -c 'import json, os, sys; p = os.environ["TK_PROBE_POINTER"]; d = json.load(open(p)); d.setdefault("exempt", []).append(sys.argv[1]); t = p + ".tmp"; json.dump(d, open(t, "w")); os.replace(t, p)' AGENT_ID
Then run: cat "\$TK_PROBE_POINTER"

Step 4. Wait until both background agents have completed. Do not end your turn before both completion notifications have arrived. Then reply with the two agentIds and the final pointer content.
PROMPT

cd "$W/run"
env -u CLAUDE_CODE_SESSION_ID -u TK_PACKAGE_POINTER CLAUDE_CODE_AUTO_COMPACT_WINDOW=100000 \
  TK_PROBE_LOG="$W/log" TK_PROBE_POINTER="$W/run/pointer.json" \
  timeout 2400 claude -p --model sonnet --plugin-dir "$HERE/logger" --plugin-dir "$W/veto" \
  --allowedTools "Read Agent Bash" --output-format json "$(cat prompt.txt)" > out.json
SID=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["session_id"])' out.json)
python3 "$HERE/analyze.py" "$W/log" "$SID"
