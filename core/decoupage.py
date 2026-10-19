"""Lógica editorial da decupagem conservadora: decide o que entra e o que sai,
devolvendo uma lista de cortes (EDL) em timecodes do arquivo original.
Não mexe em FFmpeg -- só toma decisão a partir de palavras + silêncios detectados.

Achado real (feedback do usuário testando no Mac, vídeo real): confiar só na segmentação
que o Whisper devolve não bastava -- o modelo frequentemente agrupa várias frases, com
pausas reais entre elas, num único "segmento" longo, e a versão anterior deste módulo só
cortava o espaço ENTRE segmentos do Whisper, nunca o que sobrava dentro de um. Por isso
nenhum silêncio era removido na prática. A correção: desmontar os segmentos em palavras
(timestamps já vêm de cada backend) e remontar "falas" (clauses) nos pontos onde a
detecção acústica de silêncio (core/vad.py) confirma uma pausa real -- não a frase do
modelo. Isso também ajuda a isolar correções/recomeços que o Whisper teria deixado
grudados no mesmo segmento de texto."""
from __future__ import annotations
import difflib
from dataclasses import dataclass, field

from .transcribe import Segment, Word

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


def _flatten_words(segments: list[Segment]) -> list[Word]:
    words = [w for seg in segments for w in seg.words]
    if words:
        return words
    # fallback para um backend que não deu timestamp por palavra: trata cada segmento
    # inteiro como se fosse uma só "palavra" (perde granularidade, mas não quebra).
    return [Word(seg.text, seg.start, seg.end) for seg in segments if seg.text.strip()]


def _silence_between(a_end: float, b_start: float, silences: list[tuple[float, float]]) -> bool:
    return any(s < b_start and e > a_end for s, e in silences)


def split_into_clauses(words: list[Word], silences: list[tuple[float, float]],
                        min_gap_s: float = 0.25) -> list[Segment]:
    """Agrupa palavras em falas, cortando onde há uma pausa real (gap >= min_gap_s E
    confirmada como silêncio acústico, não só um intervalo sem palavra reconhecida)."""
    if not words:
        return []
    clauses: list[Segment] = []
    current: list[Word] = [words[0]]
    for prev, nxt in zip(words, words[1:]):
        gap = nxt.start - prev.end
        if gap >= min_gap_s and _silence_between(prev.end, nxt.start, silences):
            clauses.append(Segment(" ".join(w.text for w in current), current[0].start, current[-1].end, current))
            current = [nxt]
        else:
            current.append(nxt)
    clauses.append(Segment(" ".join(w.text for w in current), current[0].start, current[-1].end, current))
    return clauses


def build_conservative_edl(
    segments: list[Segment],
    silences: list[tuple[float, float]] | None = None,
    safety_margin_s: float = 0.08,
    min_gap_s: float = 0.25,
    min_word_gap_for_safe_margin_s: float = 0.12,
) -> DecoupageResult:
    """Decide o que entra e o que sai da decupagem final e por quê.

    Primeiro remonta os segmentos do Whisper em "falas" (clauses), cortando nos pontos onde
    `silences` (de core/vad.py, detecção acústica real) confirma uma pausa de pelo menos
    `min_gap_s` -- não nos limites que o modelo de linguagem decidiu usar para seus próprios
    segmentos de texto. Qualquer pausa que fique FORA de uma fala mantida já não entra no
    corte final (ver to_render_edl) -- é assim que o silêncio é removido de verdade, inclusive
    o que ficava "escondido" dentro de um único segmento longo do Whisper.

    Depois, para cada fala, nesta ordem:
    1. É um marcador de "recomeço" (fala sobre a própria gravação) -> corta inteira.
    2. É repetição quase idêntica da fala anterior mantida -> mantém só a mais recente
       (assume-se que a tentativa seguinte corrige a anterior) e marca como "duvidosa" para
       revisão humana, já que julgar qual tomada é "melhor" exige ouvir o áudio.
    3. Caso contrário, mantém.

    Os limites de cada fala mantida são ajustados com margem de segurança a partir dos
    timestamps de palavra (não dos timestamps de frase, que são menos confiáveis), encolhendo
    a margem quando o espaço livre até a palavra vizinha é pequeno -- e sinalizando como
    "duvidosa" quando a margem teve de ser reduzida abaixo do seguro.
    """
    words = _flatten_words(segments)
    clauses = split_into_clauses(words, silences or [], min_gap_s)

    decisions: list[CutDecision] = []
    kept: list[Segment] = []

    i = 0
    while i < len(clauses):
        seg = clauses[i]

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

        start, start_doubt = _safe_boundary(seg, clauses, i, which="start",
                                             margin=safety_margin_s, min_gap=min_word_gap_for_safe_margin_s)
        end, end_doubt = _safe_boundary(seg, clauses, i, which="end",
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
        gap = anchor - prev_boundary
        used_margin = min(margin, max(0.0, gap / 2))
        return max(prev_boundary, anchor - used_margin), used_margin < margin - 1e-6
    else:
        anchor = seg.words[-1].end if seg.words else seg.end
        next_boundary = all_segments[idx + 1].start if idx + 1 < len(all_segments) else anchor + margin * 4
        gap = next_boundary - anchor
        used_margin = min(margin, max(0.0, gap / 2))
        return anchor + used_margin, used_margin < margin - 1e-6


def to_render_edl(result: DecoupageResult) -> list[tuple[float, float]]:
    """Converte as falas mantidas numa lista de ranges (start, end) a extrair e concatenar.
    Qualquer silêncio que caía FORA de uma fala mantida (ou dentro de uma fala cortada) nunca
    entra no corte final -- a pausa entre falas que sobrevivem fica só a margem de segurança
    nas duas pontas (configurável via safety_margin_s em build_conservative_edl)."""
    return [(s.start, s.end) for s in result.kept_segments]
