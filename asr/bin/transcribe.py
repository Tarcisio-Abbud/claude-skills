#!/usr/bin/env python3
"""Transcribe audio (a folder, a single file, or a WhatsApp export .zip) locally on CPU.

Default engine is Parakeet TDT 0.6B v3 (ONNX int8); faster-whisper covers the languages
Parakeet lacks. Writes transcript.jsonl (resumable) plus a readable transcript.md.

    python3 transcribe.py <folder|file|export.zip> [--engine parakeet|whisper] [--lang pt]

Set HF_HOME to keep model weights on a persistent volume.
"""
import argparse
import glob
import json
import os
import shutil
import sys
import tempfile
import time
import zipfile

AUDIO_EXTS = (".opus", ".ogg", ".m4a", ".mp3", ".wav", ".aac", ".flac", ".mp4", ".amr")
SAMPLE_RATE = 16000


def resolve_target(target):
    """Return (search_root, out_dir, tmp_to_clean) for a zip, a folder, or a single file.

    A .zip is extracted into a tempdir the caller must clean, but its output belongs beside
    the .zip itself, which outlives the tempdir.
    """
    if target.lower().endswith(".zip"):
        tmp = tempfile.mkdtemp(prefix="asr-zip-")
        with zipfile.ZipFile(target) as archive:
            archive.extractall(tmp)
        return tmp, os.path.dirname(os.path.abspath(target)), tmp
    if os.path.isfile(target):
        return target, os.path.dirname(os.path.abspath(target)), None
    return target, target, None


def find_audio(root, pattern):
    """Every audio file under root, or root itself when it is already one file."""
    if os.path.isfile(root):
        return [root]
    if pattern:
        return sorted(glob.glob(os.path.join(root, "**", pattern), recursive=True))
    return sorted(p for p in glob.glob(os.path.join(root, "**", "*"), recursive=True)
                  if p.lower().endswith(AUDIO_EXTS))


def decode(path):
    """Decode any container to mono float32 at 16 kHz, in memory, via PyAV.

    PyAV carries its own codecs, so .opus and .m4a work with no system ffmpeg. onnx_asr
    reads WAV from disk only, so handing it an array is also what avoids temp files.
    """
    import av
    import numpy as np

    with av.open(path) as container:
        resampler = av.AudioResampler(format="s16", layout="mono", rate=SAMPLE_RATE)
        parts = [r.to_ndarray().reshape(-1)
                 for frame in container.decode(audio=0)
                 for r in resampler.resample(frame)]
    if not parts:
        return np.zeros(0, dtype=np.float32)
    return np.concatenate(parts).astype(np.float32) / 32768.0


def split_points(audio, chunk_s, search_s=2.0):
    """Yield (start, end) sample offsets, cutting at the quietest point near each boundary.

    A fixed cut every N seconds lands mid-word often enough to corrupt the numbers and proper
    nouns this exists to capture. Scanning a +/- search_s window for the lowest-energy 20 ms
    frame moves the cut into a pause when there is one, and costs nothing when there is not.
    """
    import numpy as np

    chunk = int(chunk_s * SAMPLE_RATE)
    search = int(search_s * SAMPLE_RATE)
    frame = int(0.02 * SAMPLE_RATE)
    start = 0
    while start < len(audio):
        end = start + chunk
        if end >= len(audio):
            yield start, len(audio)
            return
        lo, hi = max(start + frame, end - search), min(len(audio) - frame, end + search)
        if hi > lo:
            window = audio[lo:hi]
            usable = (len(window) // frame) * frame
            if usable:
                energy = np.abs(window[:usable]).reshape(-1, frame).mean(axis=1)
                end = lo + int(energy.argmin()) * frame
        yield start, end
        start = end


def available_mb():
    """Free RAM in MB, or None where /proc/meminfo does not exist (macOS, Windows)."""
    try:
        with open("/proc/meminfo") as fh:
            for line in fh:
                if line.startswith("MemAvailable:"):
                    return int(line.split()[1]) // 1024
    except OSError:
        pass
    return None


def safe_chunk(requested):
    """Shrink the Parakeet window when RAM left for activations is tight, and say so.

    Call this only once the weights are resident: measured before the ~640 MB load, free RAM
    reads at its highest point of the run and the guard waves through exactly the run it
    exists to catch. Halving the window roughly halves activation memory; the weights are the
    floor and cannot be traded away.
    """
    free = available_mb()
    if free is None or free >= 1400:
        return requested
    reduced = 15.0 if free >= 800 else 8.0
    if reduced >= requested:
        return requested
    print(f"warning: {free} MB free after loading weights, "
          f"reducing --chunk {requested:g} -> {reduced:g}", file=sys.stderr)
    return reduced


class Parakeet:
    def __init__(self, chunk_s):
        try:
            import onnx_asr
        except ImportError:
            sys.exit("onnx-asr is not installed: pip install onnx-asr av")
        import onnxruntime as ort

        opts = ort.SessionOptions()
        # The arena over-reserves on a small box; disabling it keeps peak RSS near the model
        # size instead of climbing until the kernel kills the process.
        opts.enable_cpu_mem_arena = False
        opts.intra_op_num_threads = min(4, os.cpu_count() or 2)
        self.name = "parakeet-tdt-0.6b-v3-int8"
        self.model = onnx_asr.load_model("nemo-parakeet-tdt-0.6b-v3",
                                         quantization="int8", sess_options=opts)
        self.chunk_s = safe_chunk(chunk_s)

    def transcribe(self, path, lang):
        audio = decode(path)
        if len(audio) == 0:
            return "", 0.0
        parts = []
        for start, end in split_points(audio, self.chunk_s):
            segment = audio[start:end]
            if len(segment) < int(0.1 * SAMPLE_RATE):
                continue
            parts.append(self.model.recognize(segment, sample_rate=SAMPLE_RATE, language=lang))
        return " ".join(p.strip() for p in parts if p and p.strip()), len(audio) / SAMPLE_RATE


class Whisper:
    def __init__(self, size):
        from faster_whisper import WhisperModel
        self.name = f"faster-whisper-{size}"
        self.model = WhisperModel(size, device="cpu", compute_type="int8")

    def transcribe(self, path, lang):
        segments, info = self.model.transcribe(path, language=lang, vad_filter=True)
        return " ".join(s.text.strip() for s in segments).strip(), round(info.duration, 1)


def already_done(out):
    done = set()
    if os.path.exists(out):
        with open(out) as fh:
            for line in fh:
                try:
                    done.add(json.loads(line)["file"])
                except (ValueError, KeyError):
                    pass
    return done


def write_markdown(out, engine_name):
    with open(out) as fh:
        records = sorted((json.loads(line) for line in fh), key=lambda r: r["file"])
    path = os.path.splitext(out)[0] + ".md"
    with open(path, "w") as fh:
        fh.write(f"# Transcripts ({len(records)} files, {engine_name})\n\n")
        for record in records:
            body = record.get("text") or f"[{record.get('error', 'empty')}]"
            fh.write(f"**{record['file']}** ({record.get('dur', '?')}s)\n\n> {body}\n\n")
    return len(records)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target", help="folder with audio, a single audio file, or a .zip export")
    ap.add_argument("--engine", default="parakeet", choices=("parakeet", "whisper"))
    ap.add_argument("--lang", default="pt")
    ap.add_argument("--model", default="small", help="whisper size (whisper engine only)")
    ap.add_argument("--glob", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--chunk", type=float, default=30.0)
    args = ap.parse_args()

    root, out_dir, cleanup = resolve_target(args.target)
    try:
        audios = find_audio(root, args.glob)
        if not audios:
            sys.exit(f"no audio found in {args.target}")
        out = args.out or os.path.join(out_dir, "transcript.jsonl")

        engine = Parakeet(args.chunk) if args.engine == "parakeet" else Whisper(args.model)
        done = already_done(out)

        started = time.time()
        new = 0
        with open(out, "a") as fout:
            for path in audios:
                name = os.path.basename(path)
                if name in done:
                    continue
                try:
                    text, duration = engine.transcribe(path, args.lang)
                    record = {"file": name, "dur": round(duration, 1),
                              "engine": engine.name, "text": text}
                except Exception as exc:  # one bad file must not lose the batch
                    record = {"file": name, "engine": engine.name,
                              "error": f"{type(exc).__name__}: {exc}", "text": ""}
                fout.write(json.dumps(record, ensure_ascii=False) + "\n")
                fout.flush()
                done.add(name)
                new += 1
                print(f"{name}: {record.get('text', '')[:90]}", flush=True)

        total = write_markdown(out, engine.name)
        print(f"\nOK: {new} new, {total} total, {time.time() - started:.0f}s -> {out}",
              flush=True)
    finally:
        if cleanup:
            shutil.rmtree(cleanup, ignore_errors=True)


if __name__ == "__main__":
    main()
