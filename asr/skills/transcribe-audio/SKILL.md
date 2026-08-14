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

Use the Python that has `onnx-asr` and `av` installed — usually a dedicated venv rather than
the system interpreter. This machine's venv path, model cache and provisioning script live in
the extension file `~/.claude/asr/transcribe-audio.md`; read it before the first run.

| Flag | Default | When to change it |
|---|---|---|
| `--engine parakeet\|whisper` | `parakeet` | `whisper` for a language Parakeet does not cover |
| `--lang` | `pt` | any code the chosen engine supports |
| `--chunk` | `30` | lower it on a box that OOMs |

Writes `transcript.jsonl` (one line per file: `file`, `dur`, `engine`, `text`) and a readable
`transcript.md` beside it. **Resumable** — rerunning skips what is already done, so a killed
batch resumes instead of restarting.

Expect roughly 4x realtime on a weak CPU. Background a long batch, and note that it holds
~1.1 GB resident until it finishes — on a small box, run it alone.

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
