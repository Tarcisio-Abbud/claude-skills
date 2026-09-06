---
name: transcribe-audio
description: Transcribe audio to text locally on CPU — voice notes (.opus/.ogg), recordings, any .m4a/.mp3/.wav that Read cannot decode. Use when a task needs the words in an audio file, or when a folder or a WhatsApp export .zip must be turned into text.
---

# Transcribe audio

Runs on CPU, so nothing leaves the machine.

## Run it

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/transcribe.py" <folder|file|export.zip> [options]
```

`${CLAUDE_PLUGIN_ROOT}` is set only while this skill runs as an installed PLUGIN. Anywhere
else it expands to nothing and the line dies as `python3 /bin/transcribe.py`; then spell the
path from THIS file, where the script is `../../bin/transcribe.py`.

Use the Python that has `onnx-asr` and `av` installed — usually a dedicated venv rather than
the system interpreter. A machine already provisioned keeps its venv path, model cache and
provisioning script in `~/.claude/asr/transcribe-audio.md`: read that file before the first
run. **No such file means no venv on this machine**, not a blocked run — make one,
`pip install onnx-asr av` (plus `faster-whisper` for `--engine whisper`), and point `HF_HOME`
at a persistent directory so the weights survive.

| Flag | Default | When to change it |
|---|---|---|
| `--engine parakeet\|whisper` | `parakeet` | `whisper` for a language Parakeet does not cover |
| `--lang` | `pt` | any code the chosen engine supports |
| `--chunk` | `30` | lower it on a box that OOMs (parakeet only) |
| `--glob` | every audio extension | pick a subset by name — `'PTT-*.opus'`. It REPLACES the extension filter, so the pattern alone decides what is read |
| `--out` | `transcript.jsonl` beside the target | give it a FILE path ending `.jsonl` — `transcript.md` takes that stem. Without it the run writes into the user's own audio folder |

Writes `transcript.jsonl` (one line per file: `file`, `dur`, `engine`, `text`) and a readable
`transcript.md` beside it. **Resumable** — rerunning skips what is already done, so a killed
batch resumes instead of restarting.

The factor counts on the audio's side: the run is FASTER than the recording, 2x to 4x
depending on the CPU — ~2x measured on this container on 2026-08-26, ten minutes of audio in
about five of wall clock. Background a long batch, and note that it holds ~1.1 GB resident
until it finishes — on a small box, run it alone.

## Which engine

**Parakeet TDT 0.6B v3 int8** is the default: faster than whisper small on CPU and sharper on
the things that matter in a voice note — numbers, jargon, proper nouns — with punctuation and
capitalization already applied.

**Whisper** (`--engine whisper`) covers the 74 languages Parakeet lacks. `--model medium`
exists but needs real RAM; on a small box it gets OOM-killed at load.

## Two traps

**Parakeet transcribes a whole clip in one pass**, so a long file OOMs a small box. The
chunking in `split_points` is load-bearing: keep it, and keep the cut at the quietest frame
near each boundary, which is what stops a window edge from splitting a number in half.

**`onnx_asr` reads WAV from disk only.** `decode` sidesteps that with PyAV, handing over a
float32 array — which is also why `.opus` works with no system ffmpeg and no temp files.

## Cross-referencing a WhatsApp export

The audio usually carries the value or the decision the chat text omits. Extract the zip, read
`_chat.txt`, then match each transcript to its chat line by the **timestamp in the filename**
(`...-YYYY-MM-DD-HH-MM-SS.opus`, `PTT-YYYYMMDD-WAxxxx.opus`).
