# Design notes — asr, whatsapp, contrato, plugin-drift

Moved from the README on 2026-09-26. Each plugin's `skills/<name>/SKILL.md` stays the
manual; this file carries the reasons behind it.

## The asr plugin

`transcribe-audio` turns audio Read cannot decode — voice notes, recordings, a WhatsApp
export `.zip` — into text, entirely on CPU, so nothing leaves the machine. Parakeet TDT 0.6B
v3 int8 is the default engine and faster-whisper the fallback for the languages Parakeet does
not cover.

Two design points carry the plugin. Parakeet transcribes a whole clip in one pass, so
`bin/transcribe.py` slices long audio into windows and cuts each at the quietest nearby frame
— without that, a long file OOMs a small box, and a naive cut splits numbers in half. And
`onnx_asr` reads WAV from disk only, so the script decodes with PyAV into an array and hands
that over, which is what makes `.opus` work with no system ffmpeg.

Machine-specific addresses — which interpreter, where the weights live, how they are
provisioned — stay out of this repo and live in the extension file below.

## The whatsapp plugin

`whatsapp:export-delta` reads an export `.zip` by its **delta** against the previous export. A
WhatsApp export is cumulative: every one carries the whole conversation again, so reading the
new one costs the entire history to learn the fifty lines that arrived since. `bin/wa_export.py`
hands over what is new — the messages with their line numbers, the attachments extracted beside
the zip, the voice notes routed to `asr:transcribe-audio` and folded back in, so one file
carries the whole delta.

Three design points carry it, each measured against two real exports of one conversation
eleven days apart. Messages are matched on **date, sender and text, never the clock**: an
untouched message had moved from `16:04` to `16:05`, and a key carrying the minute reports it
as edited. An attachment is credited to the message naming it **exactly** before the folded
name is tried: WhatsApp stores a repeated `invoice (1).pdf` as `invoice (1)-1.pdf`, and
folding first hands the new file to the older message that sent its namesake. And because an
export only ever grows, anything but a tail of inserts is **surfaced as an anomaly** rather
than absorbed — that, plus an overlap floor that refuses a pair of exports which is not the
same conversation, is what stops a wrong pair reading as a clean delta.

A first run over nine real exports left five things to the person running it, and the script
now carries all five. A conversation with no earlier export is read whole with `--first`
instead of refused. A refused pair says **why** — the same messages under different dates
(two phone locales), under different sender names (two phones of one group), under both at
once, or a share that is genuinely there and merely under the floor. Each cause is measured
against the overlap the refusal prints, so none is named that those numbers contradict. And
every new attachment is probed: one with no extension is saved under the
one its bytes earn, a password-protected PDF and a scan with no text layer are flagged with
the command that opens them, since both otherwise read as an empty document rather than as
one that needs a step first.

## The contrato plugin

`contrato:revisao-contrato` reviews a Brazilian contract and writes one report: findings ranked
by the money at stake, each with ready-to-paste wording, at most ten questions for a lawyer, and
a negotiation table. It works both ways — a draft we wrote, or one we received — and a second
invocation applies the findings the human picked, under a word budget.

The review is a Workflow script in the skill's own `reference/`: a scout writes a ficha of the
contract's facts, ten lenses read contract and ficha in parallel, a critic may add two more,
sonnet jobs merge duplicates, and only the altas a single lens raised go to a refuter. Three
design points come from a measured manual run: the spawn is the cost (so jobs are packed by
size and the run is capped at 30 agents), convergence between lenses is free verification, and
a lawyer answers ten questions, not eighty. Every party fact enters through the args and the
ficha; the lens methods in `lenses.md` carry none.

`modo: "plano"` runs the same script with no agent and returns the plan line;
`python3 -m unittest discover -s contrato/tests` proves that, and simulates a full review with a
fake `agent`, through `node`.

## The `plugin-drift` plugin

Read-only drift report across every installed Claude Code plugin, in every marketplace known
to this machine (`~/.claude/plugins/known_marketplaces.json`) — one skill, `check`, wrapping
`plugin-drift/bin/plugin-drift-check`. Refreshes each marketplace's catalog first, then per
plugin: git-pinned plugins (catalog `source.sha`) compare the installed commit against the
catalog's directly — matching semver is not proof of matching commit, `mattpocock-skills` is
the canonical case where both read the same version with different commits underneath.
Plugins packaged inside the marketplace repo itself (catalog `source` is a path, no `sha`)
compare file hashes one direction instead, since the installed `gitCommitSha` on those is the
marketplace's own commit, not a per-plugin one. `--changelog <name@marketplace>` pulls the
commit-log highlights for one drifted git-pinned plugin, best-effort, from its own upstream
repo. Never applies anything — the CLI's `disable`+`install` pair, or the `/plugin` dialog
where the CLI binary is unavailable, is still how a drifted plugin actually gets updated.
