"""Regressão para o bug real reportado pelo usuário: o Whisper pode juntar duas frases com
uma pausa real entre elas num único "segmento" de texto -- a versão antiga do núcleo só
cortava o espaço ENTRE segmentos do Whisper, então essa pausa nunca era removida. Este teste
simula exatamente isso: um único Segment cobrindo duas frases, com 1.5s de silêncio real
entre elas, e confirma que core/vad.py + core/decoupage.py cortam esse silêncio mesmo assim."""
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.transcribe import Segment, Word, TranscriptionBackend
from core.pipeline import run_conservative

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "merged_segment_take.wav"
OUT = ROOT / "out_test_intra_segmento"

# timecodes verdadeiros (conhecidos de fábrica): s1 dura 3.960680s, depois 1.5s de silêncio,
# depois s3 começa em 5.460680 e dura 4.164263s.
S1_END = 3.960680
S3_START = 5.460680
S3_END = S3_START + 4.164263


class FakeMergedBackend(TranscriptionBackend):
    """Simula o Whisper juntando as duas frases num único segmento de texto, mas com
    timestamps de palavra corretos -- é isso que acontece de verdade em áudio real."""

    def transcribe(self, audio_path, language="pt"):
        words = [
            Word("hoje eu quero falar sobre um assunto muito importante", 0.0, S1_END),
            Word("que vai mudar completamente a forma como voce trabalha", S3_START, S3_END),
        ]
        return [Segment(" ".join(w.text for w in words), 0.0, S3_END, words)]


def main():
    assert SRC.exists(), f"arquivo de teste não encontrado: {SRC}"
    original_hash = hashlib.sha256(SRC.read_bytes()).hexdigest()

    result = run_conservative(str(SRC), str(OUT), FakeMergedBackend(), language="pt")

    print("=== RESULTADO ===")
    for k, v in result.items():
        print(f"{k}: {v}")

    assert hashlib.sha256(SRC.read_bytes()).hexdigest() == original_hash, "original foi modificado!"
    print("[OK] original intacto")

    reducao = result["duracao_original_s"] - result["duracao_final_s"]
    assert reducao > 1.0, (
        f"FALHA (bug original reproduzido): só removeu {reducao:.2f}s -- o silêncio de 1.5s "
        "escondido dentro de um único segmento do Whisper não foi cortado"
    )
    print(f"[OK] silêncio DENTRO de um segmento único do Whisper foi cortado "
          f"(reduziu {reducao:.2f}s, esperado ~1.3s após margens)")

    print("\nTESTE DE REGRESSÃO (silêncio intra-segmento) PASSOU")


if __name__ == "__main__":
    main()
