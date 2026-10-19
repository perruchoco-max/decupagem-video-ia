"""Orquestra transcrição -> decupagem -> corte -> relatórios. Usado por local e nuvem."""
from __future__ import annotations
from pathlib import Path

from .transcribe import TranscriptionBackend
from .decoupage import build_conservative_edl, to_render_edl
from .cutter import render_edl, probe_duration, has_video_stream
from .report import write_outputs, write_srt
from .vad import detect_silences


def run_conservative(src_path: str, out_dir: str, backend: TranscriptionBackend,
                      language: str = "pt", min_gap_s: float = 0.25,
                      noise_db: float = -35.0) -> dict:
    src = Path(src_path)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    segments = backend.transcribe(str(src), language=language)
    silences = detect_silences(str(src), noise_db=noise_db, min_silence_s=min_gap_s)
    result = build_conservative_edl(segments, silences, min_gap_s=min_gap_s)
    edl = to_render_edl(result)

    has_video = has_video_stream(str(src))
    ext = ".mp4" if has_video else ".wav"
    final_path = out / f"{src.stem}_decupado{ext}"
    render_edl(str(src), edl, str(final_path), has_video)

    paths = write_outputs(result, segments, out, src.stem)
    write_srt(result.kept_segments, out / f"{src.stem}.srt")

    return {
        "arquivo_final": str(final_path),
        "duracao_original_s": probe_duration(str(src)),
        "duracao_final_s": probe_duration(str(final_path)),
        "segmentos_originais": len(segments),
        "segmentos_mantidos": len(result.kept_segments),
        "trechos_duvidosos": len([d for d in result.decisions if d.confidence == "duvidosa"]),
        "saidas": {k: str(v) for k, v in paths.items()},
    }
