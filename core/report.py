"""Exportações comuns: JSON de timecodes, relatório de decisões, SRT, transcrições."""
from __future__ import annotations
import json
from pathlib import Path

from .decoupage import DecoupageResult


def write_outputs(result: DecoupageResult, original_segments, out_dir: Path, base_name: str) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {}

    paths["transcricao_original"] = out_dir / f"{base_name}_transcricao_original.txt"
    paths["transcricao_original"].write_text(
        "\n".join(f"[{s.start:.2f}-{s.end:.2f}] {s.text}" for s in original_segments), encoding="utf-8"
    )

    paths["transcricao_final"] = out_dir / f"{base_name}_transcricao_final.txt"
    paths["transcricao_final"].write_text(result.kept_text(), encoding="utf-8")

    paths["cortes_json"] = out_dir / f"{base_name}_cortes.json"
    paths["cortes_json"].write_text(json.dumps([
        {"tipo": d.kind, "inicio": round(d.start, 3), "fim": round(d.end, 3),
         "texto": d.text, "confianca": d.confidence, "motivo": d.reason}
        for d in result.decisions
    ], ensure_ascii=False, indent=2), encoding="utf-8")

    duvidosos = [d for d in result.decisions if d.confidence == "duvidosa"]
    relatorio = ["# Relatório de decisões editoriais", ""]
    relatorio.append(f"Segmentos mantidos: {len(result.kept_segments)}")
    relatorio.append(f"Cortes aplicados: {len([d for d in result.decisions if d.kind != 'manter'])}")
    relatorio.append(f"Trechos sinalizados para revisão humana: {len(duvidosos)}")
    relatorio.append("")
    if duvidosos:
        relatorio.append("## Trechos duvidosos (revise antes de publicar)")
        for d in duvidosos:
            relatorio.append(f"- [{d.start:.2f}s-{d.end:.2f}s] ({d.kind}) {d.reason} -- \"{d.text[:80]}\"")
    paths["relatorio_md"] = out_dir / f"{base_name}_relatorio.md"
    paths["relatorio_md"].write_text("\n".join(relatorio), encoding="utf-8")

    return paths


def write_srt(segments, out_path: Path) -> None:
    def fmt(t: float) -> str:
        h, rem = divmod(t, 3600)
        m, s = divmod(rem, 60)
        ms = (s - int(s)) * 1000
        return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(ms):03d}"

    lines = []
    for i, seg in enumerate(segments, 1):
        lines.append(str(i))
        lines.append(f"{fmt(seg.start)} --> {fmt(seg.end)}")
        lines.append(seg.text)
        lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")
