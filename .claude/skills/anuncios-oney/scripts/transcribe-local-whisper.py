"""Local word-level transcription with faster-whisper, tuned for slow PCs.

Writes the kit's transcript shape: {"words": [{text,start,end}], "audio_duration_secs"}.

Usage:
  python transcribe-local-whisper.py <media> <out.json>              # captions quality
  python transcribe-local-whisper.py <media> <out.json> --fast       # raw take, only to choose the cut
  python transcribe-local-whisper.py <media> --windows 12.4,30.1,... # check splices: text of a 3 s window
                                                                      # around each time, ONE model load
Options: --model NAME_OR_DIR (env WHISPER_MODEL) · --lang pt · --span 3
         --dict FILE   personal dictionary (one name/term per line; default: dicionario.txt in the kit root,
                       env EDITE_DICT). Biases the model toward your names, brands and jargon.
         --engine parakeet   NVIDIA Parakeet TDT v3 via sherpa-onnx (multilingual, same engine OpenWhispr uses).
                       Model files in ~/.cache/edite-reels/parakeet-v3 (see scripts/setup-cloud.sh).

Speed rules (measured on CPU, 1 min of speech, 4 threads):
  medium beam 5 = 19.5 s · medium beam 1 = 14.5 s · small beam 1 = 5.5 s (base is too inaccurate for PT)
  With an NVIDIA GPU everything uses medium beam 5 (fast anyway).
  Without one: --fast and --windows use small; captions use medium with beam 1.
"""
import argparse, glob, json, os, subprocess, sys, site, tempfile


def add_cuda_dlls():
    if os.name != "nt":
        return
    for base in site.getsitepackages():
        for d in glob.glob(os.path.join(base, "nvidia", "*", "bin")):
            os.add_dll_directory(d)
            os.environ["PATH"] = d + os.pathsep + os.environ["PATH"]


def to_wav(media, start=None, dur=None):
    """Decode with ffmpeg to 16 kHz mono WAV: avoids decoder errors on phone files and is faster to read."""
    fd, path = tempfile.mkstemp(suffix=".wav"); os.close(fd)
    cmd = ["ffmpeg", "-v", "error", "-y"]
    if start is not None:
        cmd += ["-ss", f"{start:.3f}"]
    cmd += ["-i", media]
    if dur is not None:
        cmd += ["-t", f"{dur:.3f}"]
    subprocess.run(cmd + ["-vn", "-ac", "1", "-ar", "16000", path], check=True)
    return path


def load(model_name, fast):
    add_cuda_dlls()
    from faster_whisper import WhisperModel
    try:
        m = WhisperModel(model_name or "medium", device="cuda", compute_type="float16")
        return m, "cuda", 5
    except Exception:
        name = model_name or ("small" if fast else "medium")
        m = WhisperModel(name, device="cpu", compute_type="int8", cpu_threads=os.cpu_count() or 4)
        return m, "cpu", 1


def load_dict(path):
    """Personal dictionary: one term per line, '#' comments allowed. Returns a comma-joined hint string or None."""
    path = path or os.environ.get("EDITE_DICT")
    if not path:
        cand = os.path.join(os.getcwd(), "dicionario.txt")
        path = cand if os.path.exists(cand) else None
    if not path or not os.path.exists(path):
        return None
    terms = []
    for line in open(path, encoding="utf-8"):
        line = line.split("#", 1)[0].strip()
        if line:
            terms.append(line)
    return ", ".join(terms[:80]) or None


def parakeet_words(wav, chunk=40.0):
    """Word timings from Parakeet TDT v3 (sherpa-onnx). Audio is processed in fixed windows with a time offset."""
    import wave
    import numpy as np
    import sherpa_onnx
    d = os.environ.get("PARAKEET_DIR") or os.path.expanduser("~/.cache/edite-reels/parakeet-v3")
    rec = sherpa_onnx.OfflineRecognizer.from_transducer(
        encoder=os.path.join(d, "encoder.int8.onnx"), decoder=os.path.join(d, "decoder.int8.onnx"),
        joiner=os.path.join(d, "joiner.int8.onnx"), tokens=os.path.join(d, "tokens.txt"),
        num_threads=os.cpu_count() or 4, model_type="nemo_transducer")
    with wave.open(wav) as f:
        sr = f.getframerate(); pcm = np.frombuffer(f.readframes(f.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    n = int(chunk * sr); words = []
    for off in range(0, len(pcm), n):
        st = rec.create_stream(); st.accept_waveform(sr, pcm[off:off + n]); rec.decode_stream(st)
        r = st.result; t0 = off / sr; cur = None
        for tok, ts in zip(r.tokens, r.timestamps):
            if tok.startswith((" ", "\u2581")) or cur is None:   # this model marks a new word with a leading space
                if cur and cur["text"]: words.append(cur)
                cur = {"text": tok.lstrip(" \u2581"), "start": round(t0 + ts, 3), "end": round(t0 + ts + 0.2, 3)}
            else:
                cur["text"] += tok; cur["end"] = round(t0 + ts + 0.2, 3)
        if cur and cur["text"]: words.append(cur)
    for a, b in zip(words, words[1:]):
        a["end"] = round(min(a["end"], b["start"]), 3)
    return words, len(pcm) / sr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("media")
    ap.add_argument("out", nargs="?")
    ap.add_argument("--model", default=os.environ.get("WHISPER_MODEL"))
    ap.add_argument("--lang", default="pt")
    ap.add_argument("--fast", action="store_true")
    ap.add_argument("--windows", default="")
    ap.add_argument("--span", type=float, default=3.0)
    ap.add_argument("--dict", default=None)
    ap.add_argument("--engine", choices=["whisper", "parakeet"], default=os.environ.get("EDITE_ASR", "whisper"))
    a = ap.parse_args()
    hot = load_dict(a.dict)

    if a.windows:
        model, device, beam = load(a.model, True)
        for t in [float(x) for x in a.windows.split(",") if x.strip()]:
            start = max(0.0, t - a.span / 2)
            wav = to_wav(a.media, start, a.span)
            segs, _ = model.transcribe(wav, language=a.lang, beam_size=beam, condition_on_previous_text=False, hotwords=hot)
            print(f"[{t:8.2f}] {' '.join(s.text.strip() for s in segs)}", flush=True)
            os.remove(wav)
        return

    if not a.out:
        sys.exit("usage: transcribe-local-whisper.py <media> <out.json> [--fast]")
    if a.engine == "parakeet":
        wav = to_wav(a.media)
        words, dur = parakeet_words(wav); device, beam = "cpu-parakeet", 0
        os.remove(wav)
        print(" ".join(w["text"] for w in words), flush=True)
    else:
        model, device, beam = load(a.model, a.fast)
        wav = to_wav(a.media)
        segments, info = model.transcribe(wav, language=a.lang, beam_size=beam, word_timestamps=True,
                                          vad_filter=False, condition_on_previous_text=False, hotwords=hot)
        dur = info.duration
        words = []
        for seg in segments:
            for w in seg.words or []:
                words.append({"text": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3)})
            print(f"[{seg.start:7.2f}] {seg.text.strip()}", flush=True)
        os.remove(wav)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump({"language_code": a.lang, "audio_duration_secs": round(dur, 3),
                   "text": " ".join(w["text"] for w in words), "words": words}, f, ensure_ascii=False, indent=1)
    print(f"DONE device={device} beam={beam} words={len(words)} -> {a.out}")


if __name__ == "__main__":
    main()
