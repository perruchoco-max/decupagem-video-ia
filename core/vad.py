"""Detecção acústica de silêncio via FFmpeg (filtro silencedetect). Independe de como o
backend de transcrição segmentou o texto -- é o que permite cortar pausas que o Whisper
(local ou nuvem) decidiu manter dentro de um único segmento, em vez de só confiar na
segmentação do modelo de linguagem."""
from __future__ import annotations
import re
import subprocess


def detect_silences(audio_path: str, noise_db: float = -35.0, min_silence_s: float = 0.12) -> list[tuple[float, float]]:
    """Devolve intervalos (início, fim) em segundos onde o áudio está abaixo de `noise_db`
    por pelo menos `min_silence_s`. `noise_db` mais alto (ex: -25) detecta mais silêncio
    (mais sensível); mais baixo (ex: -45) exige silêncio mais "puro"."""
    cmd = [
        "ffmpeg", "-i", audio_path, "-af",
        f"silencedetect=noise={noise_db}dB:d={min_silence_s}", "-f", "null", "-",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    starts = [float(m) for m in re.findall(r"silence_start:\s*([\d.]+)", proc.stderr)]
    ends = [float(m) for m in re.findall(r"silence_end:\s*([\d.]+)", proc.stderr)]
    # se o silêncio vai até o fim do arquivo, o ffmpeg não loga "silence_end" -- ignora o
    # start sem par correspondente em vez de quebrar.
    return list(zip(starts, ends))
