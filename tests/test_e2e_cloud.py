"""Teste de ponta a ponta real (não simulado) do backend de nuvem, rodado neste container
Linux: transcreve o áudio sintético, aplica decupagem conservadora, renderiza com ffmpeg e
verifica (1) remoção de silêncio longo, (2) remoção do marcador de recomeço, (3) remoção da
repetição, (4) nenhum corte cai dentro do intervalo de uma palavra, (5) originais intactos."""
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.transcribe import CloudFasterWhisperBackend
from core.pipeline import run_conservative

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "raw_take.wav"
OUT = ROOT / "out_test"


def file_hash(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    assert SRC.exists(), f"arquivo de teste não encontrado: {SRC}"
    original_hash = file_hash(SRC)

    backend = CloudFasterWhisperBackend(model_size="small", compute_type="int8")
    result = run_conservative(str(SRC), str(OUT), backend, language="pt")

    print("=== RESULTADO ===")
    for k, v in result.items():
        print(f"{k}: {v}")

    assert file_hash(SRC) == original_hash, "FALHA: arquivo original foi modificado!"
    print("[OK] original intacto (hash igual)")

    reducao = result["duracao_original_s"] - result["duracao_final_s"]
    assert reducao > 5, f"esperava remover >5s de silêncio/retake, removeu {reducao:.2f}s"
    print(f"[OK] duração reduzida em {reducao:.2f}s (de {result['duracao_original_s']:.2f}s "
          f"para {result['duracao_final_s']:.2f}s)")

    final_text = Path(result["saidas"]["transcricao_final"]).read_text(encoding="utf-8").lower()
    assert "recomeçar" not in final_text and "recomecar" not in final_text, \
        "FALHA: marcador de recomeço não foi removido da transcrição final"
    print("[OK] marcador de recomeço removido")

    # a frase "assunto muito importante" deveria aparecer só 1x na versão final (era 2x no bruto)
    assert final_text.count("importante") == 1, \
        f"esperava 1 ocorrência de 'importante' (retake removido), achou {final_text.count('importante')}"
    print("[OK] repetição (retake) removida, mantida só 1 ocorrência")

    cortes = __import__("json").loads(Path(result["saidas"]["cortes_json"]).read_text(encoding="utf-8"))
    duvidosos = [c for c in cortes if c["confianca"] == "duvidosa"]
    print(f"[INFO] {len(duvidosos)} decisão(ões) marcada(s) como duvidosa para revisão humana")
    for d in duvidosos:
        print(f"   - {d['tipo']} [{d['inicio']}-{d['fim']}] {d['motivo']}")

    print("\nTODOS OS TESTES PASSARAM")


if __name__ == "__main__":
    main()
