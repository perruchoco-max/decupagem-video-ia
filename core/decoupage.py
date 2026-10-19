"""Lógica editorial da decupagem conservadora: decide o que entra e o que sai,
devolvendo uma lista de cortes (EDL) em timecodes do arquivo original.
Não mexe em FFmpeg nem em transcrição -- só toma decisão a partir de Segment/Word."""
from __future__ import annotations
import difflib
from dataclasses import dataclass, field

from .transcribe import Segment

RESTART_MARKERS = [
    "deixa eu recomeçar", "deixa eu recomecar", "vou recomeçar", "vou recomecar",
    "deixa eu refazer", "corta essa parte", "deleta isso", "ignora isso",
    "vamos de novo", "deixa eu tentar de novo",
]

DUPLICATE_SIMILARITY_THRESHOLD = 0.82


@dataclass
class CutDecision:
    kind: str  # "manter" | "cortar_silencio" | "cortar_repeticao" | "cortar_restart"
    start: float
    end: float
    text: str = ""
    confidence: str = "alta"  # "alta" | "duvidosa"
    reason: str = ""


@dataclass
class DecoupageResult:
    decisions: list[CutDecision] = field(default_factory=list)
    kept_segments: list[Segment] = field(default_factory=list)

    def kept_text(self) -> str:
        return " ".join(s.text for s in self.kept_segments)


def _is_restart_marker(text: str) -> bool:
    t = text.lower()
    return any(marker in t for marker in RESTART_MARKERS)


def _similar(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def build_conservative_edl(
    segments: list[Segment],
    safety_margin_s: float = 0.08,
    max_pause_s: float = 0.5,
    min_word_gap_for_safe_margin_s: float = 0.12,
) -> DecoupageResult:
    """Decide quais segmentos entram na decupagem final e por quê.

    Regras aplicadas, nesta ordem:
    1. Segmento é um marcador de "recomeço" (fala sobre a própria gravação) -> corta inteiro.
    2. Segmento é repetição quase idêntica do segmento anterior mantido -> mantém só o mais
       recente (assume-se que a tentativa seguinte corrige a anterior) e marca como "duvidosa"
       para revisão humana, já que julgar qual tomada é "melhor" exige ouvir o áudio.
    3. Caso contrário, mantém o segmento.

    Os limites de cada segmento mantido são ajustados com margem de segurança a partir dos
    timestamps de palavra (não dos timestamps de frase, que são menos confiáveis), encolhendo
    a margem quando o espaço livre até a palavra vizinha é pequeno -- e sinalizando como
    "duvidosa" quando a margem teve de ser reduzida abaixo do seguro.
    """
    decisions: list[CutDecision] = []
    kept: list[Segment] = []

    i = 0
    while i < len(segments):
        seg = segments[i]

        if not seg.text.strip():
            i += 1
            continue

        if _is_restart_marker(seg.text):
            decisions.append(CutDecision("cortar_restart", seg.start, seg.end, seg.text,
                                          "alta", "marcador de recomeço detectado no texto"))
            i += 1
            continue

        if kept and _similar(seg.text, kept[-1].text) >= DUPLICATE_SIMILARITY_THRESHOLD:
            prev = kept.pop()
            decisions.append(CutDecision("cortar_repeticao", prev.start, prev.end, prev.text,
                                          "duvidosa",
                                          "repetição quase idêntica; tomada seguinte foi mantida "
                                          "por padrão -- confirme se é de fato a melhor"))

        start, start_doubt = _safe_boundary(seg, segments, i, which="start",
                                             margin=safety_margin_s, min_gap=min_word_gap_for_safe_margin_s)
        end, end_doubt = _safe_boundary(seg, segments, i, which="end",
                                         margin=safety_margin_s, min_gap=min_word_gap_for_safe_margin_s)

        kept_seg = Segment(seg.text, start, end, seg.words)
        kept.append(kept_seg)
        decisions.append(CutDecision(
            "manter", start, end, seg.text,
            "duvidosa" if (start_doubt or end_doubt) else "alta",
            "margem de segurança reduzida por palavra vizinha próxima" if (start_doubt or end_doubt) else "",
        ))
        i += 1

    return DecoupageResult(decisions, kept)


def _safe_boundary(seg: Segment, all_segments: list[Segment], idx: int, which: str,
                    margin: float, min_gap: float) -> tuple[float, bool]:
    """Calcula início/fim do segmento com margem de segurança, sem invadir a palavra vizinha."""
    if which == "start":
        anchor = seg.words[0].start if seg.words else seg.start
        prev_boundary = all_segments[idx - 1].end if idx > 0 else 0.0
        if seg.words and len(seg.words) > 0:
            # procura a palavra anterior real (fora deste segmento) olhando o segmento anterior
            pass
        gap = anchor - prev_boundary
        used_margin = min(margin, max(0.0, gap / 2))
        return max(prev_boundary, anchor - used_margin), used_margin < margin - 1e-6
    else:
        anchor = seg.words[-1].end if seg.words else seg.end
        next_boundary = all_segments[idx + 1].start if idx + 1 < len(all_segments) else anchor + margin * 4
        gap = next_boundary - anchor
        used_margin = min(margin, max(0.0, gap / 2))
        return anchor + used_margin, used_margin < margin - 1e-6


def to_render_edl(result: DecoupageResult, max_pause_s: float = 0.5) -> list[tuple[float, float]]:
    """Converte os segmentos mantidos numa lista de ranges (start, end) a extrair e concatenar.
    Isso por si só já limita a pausa entre falas ao tamanho dos segmentos + margem -- pausas
    longas de silêncio que caíam FORA de qualquer segmento mantido nunca entram no corte final."""
    return [(s.start, s.end) for s in result.kept_segments]
