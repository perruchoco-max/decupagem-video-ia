"""Motor de cortes: recebe a EDL (lista de ranges a manter) e renderiza com FFmpeg.
Mesmo código em Mac (ARM64) ou Linux (x86_64) -- só muda o binário ffmpeg do PATH."""
from __future__ import annotations
import shutil
import subprocess


def render_edl(src_path: str, edl: list[tuple[float, float]], out_path: str, has_video: bool) -> None:
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg não encontrado no PATH.")
    if not edl:
        raise ValueError("EDL vazia -- nada para renderizar (todo o conteúdo foi cortado?)")

    filter_parts = []
    for n, (start, end) in enumerate(edl):
        filter_parts.append(f"[0:a]atrim=start={start:.3f}:end={end:.3f},asetpts=PTS-STARTPTS[a{n}]")
        if has_video:
            filter_parts.append(f"[0:v]trim=start={start:.3f}:end={end:.3f},setpts=PTS-STARTPTS[v{n}]")

    if has_video:
        concat_inputs = "".join(f"[v{n}][a{n}]" for n in range(len(edl)))
        concat_filter = concat_inputs + f"concat=n={len(edl)}:v=1:a=1[vout][aout]"
        map_args = ["-map", "[vout]", "-map", "[aout]"]
    else:
        concat_inputs = "".join(f"[a{n}]" for n in range(len(edl)))
        concat_filter = concat_inputs + f"concat=n={len(edl)}:v=0:a=1[aout]"
        map_args = ["-map", "[aout]"]

    full_filter = ";".join(filter_parts) + ";" + concat_filter

    cmd = ["ffmpeg", "-y", "-v", "error", "-i", src_path, "-filter_complex", full_filter, *map_args]
    if has_video:
        cmd += ["-c:v", "libx264", "-preset", "fast", "-crf", "18", "-c:a", "aac", "-b:a", "192k"]
    else:
        cmd += ["-c:a", "pcm_s16le"]
    cmd.append(out_path)
    subprocess.run(cmd, check=True, capture_output=True)


def probe_duration(path: str) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
        check=True, capture_output=True, text=True,
    )
    return float(out.stdout.strip())


def has_video_stream(path: str) -> bool:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=codec_type",
         "-of", "csv=p=0", path],
        capture_output=True, text=True,
    )
    return bool(out.stdout.strip())
