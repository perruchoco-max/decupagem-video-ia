"""Teste de ponta a ponta do NÚCLEO (decisão + corte real com ffmpeg), usando uma transcrição
sintética com os timecodes verdadeiros do áudio construído em samples/ (conhecidos de fábrica,
já que fomos nós que concatenamos as peças). Isola o núcleo do download do modelo Whisper, que
está bloqueado pela política de rede deste ambiente (huggingface.co) -- ver AUDITORIA.md.
Quando o acesso a huggingface.co for liberado, test_e2e_cloud.py cobre o caminho real completo
(transcrição real + decisão + corte)."""
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.transcribe import Segment, Word, TranscriptionBackend
from core.pipeline import run_conservative

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "raw_take.wav"
OUT = ROOT / "out_test_core"


class FakeBackend(TranscriptionBackend):
    """Devolve os timecodes verdadeiros do áudio sintético (conhecidos de fábrica),
    para testar decoupage.py e cutter.py com ffmpeg real, sem depender de rede."""

    def transcribe(self, audio_path, language="pt"):
        def seg(text, start, end):
            return Segment(text, start, end, [Word(text, start, end, 1.0)])

        return [
            seg("hoje eu quero falar sobre um assunto muito importante", 0.500, 4.460680),
            seg("hoje eu quero falar sobre um assunto muito importante", 7.460680, 11.421360),
            seg("entao eh deixa eu recomecar", 13.921360, 16.789251),
            seg("que vai mudar completamente a forma como voce trabalha", 17.789251, 21.953514),
            seg("o segredo esta em simplificar cada etapa do processo", 23.953514, 28.091881),
        ]


def file_hash(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    assert SRC.exists(), f"arquivo de teste não encontrado: {SRC}"
    original_hash = file_hash(SRC)

    result = run_conservative(str(SRC), str(OUT), FakeBackend(), language="pt")

    print("=== RESULTADO ===")
    for k, v in result.items():
        print(f"{k}: {v}")

    assert file_hash(SRC) == original_hash, "FALHA: arquivo original foi modificado!"
    print("[OK] original intacto (hash igual)")

    assert Path(result["arquivo_final"]).exists(), "FALHA: arquivo final não foi gerado"
    print(f"[OK] arquivo final gerado: {result['arquivo_final']}")

    reducao = result["duracao_original_s"] - result["duracao_final_s"]
    assert reducao > 14, f"esperava remover >14s (3 silêncios longos + 1 retake + 1 restart), removeu {reducao:.2f}s"
    print(f"[OK] duração reduzida em {reducao:.2f}s (de {result['duracao_original_s']:.2f}s "
          f"para {result['duracao_final_s']:.2f}s)")

    final_text = Path(result["saidas"]["transcricao_final"]).read_text(encoding="utf-8").lower()
    assert "recomecar" not in final_text, "FALHA: marcador de recomeço não foi removido"
    print("[OK] marcador de recomeço ('entao eh deixa eu recomecar') removido inteiro")

    assert final_text.count("importante") == 1, \
        f"esperava 1 ocorrência de 'importante' (retake removido), achou {final_text.count('importante')}"
    print("[OK] retake duplicado removido, mantida só a 2a tentativa")

    assert "mudar completamente" in final_text and "simplificar cada etapa" in final_text, \
        "FALHA: conteúdo real foi perdido no corte"
    print("[OK] conteúdo real preservado (s3 e s5 presentes)")

    cortes = json.loads(Path(result["saidas"]["cortes_json"]).read_text(encoding="utf-8"))
    for c in cortes:
        print(f"   - {c['tipo']:18s} [{c['inicio']:6.2f}-{c['fim']:6.2f}] conf={c['confianca']:9s} {c['motivo']}")
    duvidosos = [c for c in cortes if c["confianca"] == "duvidosa"]
    assert any(c["tipo"] == "cortar_repeticao" for c in duvidosos), \
        "FALHA: repetição não foi sinalizada como duvidosa para revisão humana"
    print(f"[OK] {len(duvidosos)} decisão(ões) corretamente sinalizada(s) como duvidosa")

    # verifica integridade do mux: duração do arquivo final bate com a soma dos trechos mantidos
    esperado = sum(e - s for s, e in [(7.460680, 11.421360), (17.789251, 21.953514), (23.953514, 28.091881)])
    margem_total_esperada = 0.08 * 2 * 3  # 3 segmentos, margem em cada lado (aprox, pode encolher)
    assert abs(result["duracao_final_s"] - esperado) < margem_total_esperada + 0.2, \
        f"duração final {result['duracao_final_s']:.2f}s fora do esperado ~{esperado:.2f}s"
    print(f"[OK] duração final bate com a soma dos trechos mantidos (+margens): "
          f"esperado~{esperado:.2f}s, obtido {result['duracao_final_s']:.2f}s")

    print("\nTODOS OS TESTES DO NÚCLEO PASSARAM (corte real via ffmpeg, decisão real)")


if __name__ == "__main__":
    main()
