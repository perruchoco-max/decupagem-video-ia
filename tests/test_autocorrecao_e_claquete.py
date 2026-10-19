"""Regressão com a transcrição real que o usuário mandou do vídeo C9147.MP4 (A Tábua de
Esmeralda, do Jorge Ben). Dois casos novos que a v1 do núcleo não cobria:
1. Claquete de início de gravação ("Um, valendo.") -- cortada inteira por ser a 1a fala.
2. Autocorreção no meio da fala ("...que se... berrr... eu separei alguns discos que
   podem...") -- sem palavra-chave fixa, detectada por repetição de frase."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.decoupage import build_conservative_edl
from core.transcribe import Segment, Word

# Timecodes aproximados da transcrição real enviada pelo usuário, com palavras espaçadas
# uniformemente dentro de cada frase (não temos o áudio original, só o texto com timecodes
# de frase -- suficiente para testar a lógica de decisão, que é o que mudou).


def _seg(text: str, start: float, end: float) -> Segment:
    palavras = text.split()
    dur = (end - start) / max(1, len(palavras))
    words = [Word(p, start + i * dur, start + (i + 1) * dur) for i, p in enumerate(palavras)]
    return Segment(text, start, end, words)


SEGMENTOS = [
    _seg("Um, valendo.", 0.0, 1.0),
    _seg("Essa é A Tábua de Esmeralda, do Jorge Ben. Clássico absoluto, né?", 2.0, 6.0),
    _seg("Se você gosta desse tipo de música brasileira, cheia de swing, eu separei "
         "alguns discos que se berrr eu separei alguns discos que podem te agradar.", 6.0, 15.0),
    _seg("Top. Tem que ver para editar isso aí.", 16.0, 18.0),
]

# silêncios reais entre as frases (os gaps na transcrição do usuário: 1-2s, 6-6s, 15-16s)
SILENCIOS = [(1.0, 2.0), (15.0, 16.0)]


def main():
    result = build_conservative_edl(SEGMENTOS, SILENCIOS)

    tipos = [d.kind for d in result.decisions]
    print("decisões:", tipos)

    assert "cortar_marcador_gravacao" in tipos, "FALHA: claquete 'Um, valendo.' não foi cortada"
    print("[OK] claquete de início de gravação cortada")

    assert "cortar_autocorrecao" in tipos, "FALHA: autocorreção não foi detectada"
    print("[OK] autocorreção detectada e cortada")

    texto_final = result.kept_text().lower()
    assert "valendo" not in texto_final
    assert "berrr" not in texto_final
    assert "eu separei alguns discos que podem te agradar" in texto_final
    assert "jorge ben" in texto_final and "editar isso" in texto_final
    print("[OK] conteúdo real preservado, claquete e autocorreção fora do texto final")

    print("\nTESTE (claquete + autocorreção, transcrição real do usuário) PASSOU")


if __name__ == "__main__":
    main()
