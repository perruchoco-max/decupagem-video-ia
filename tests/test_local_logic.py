"""Teste de ponta a ponta do backend LOCAL (whisper.cpp), rodado nesta sessão com um binário
whisper-cli compilado de verdade (CPU, sem Metal -- a interface de linha de comando e o
formato do JSON são os mesmos do Mac, só muda a aceleração de hardware). Valida que
LocalWhisperCppBackend lê corretamente a saída real do whisper.cpp antes de confiar nisso
no Mac. Requer WHISPER_CLI_BIN e WHISPER_MODEL_PATH apontando para o binário/modelo locais."""
import hashlib
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.transcribe import LocalWhisperCppBackend
from core.pipeline import run_conservative

ROOT = Path(__file__).resolve().parent.parent
SRC = Path(os.environ.get("TEST_AUDIO", str(ROOT / "raw_take_16k.wav")))
OUT = ROOT / "out_test_local"


def file_hash(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    binary = os.environ.get("WHISPER_CLI_BIN", "whisper-cli")
    model = os.environ["WHISPER_MODEL_PATH"]
    assert SRC.exists(), f"arquivo de teste não encontrado: {SRC}"
    original_hash = file_hash(SRC)

    backend = LocalWhisperCppBackend(binary_path=binary, model_path=model, dtw_preset="tiny")
    result = run_conservative(str(SRC), str(OUT), backend, language="pt")

    print("=== RESULTADO (whisper.cpp real) ===")
    for k, v in result.items():
        print(f"{k}: {v}")

    assert file_hash(SRC) == original_hash, "FALHA: arquivo original foi modificado!"
    print("[OK] original intacto (hash igual)")

    assert Path(result["arquivo_final"]).exists(), "FALHA: arquivo final não foi gerado"
    print(f"[OK] arquivo final gerado: {result['arquivo_final']}")

    reducao = result["duracao_original_s"] - result["duracao_final_s"]
    assert reducao > 5, f"esperava remover >5s de silêncio, removeu {reducao:.2f}s"
    print(f"[OK] duração reduzida em {reducao:.2f}s (de {result['duracao_original_s']:.2f}s "
          f"para {result['duracao_final_s']:.2f}s)")

    cortes = json.loads(Path(result["saidas"]["cortes_json"]).read_text(encoding="utf-8"))
    for c in cortes:
        print(f"   - {c['tipo']:18s} [{c['inicio']:6.2f}-{c['fim']:6.2f}] conf={c['confianca']:9s} {c['motivo']}")

    print("\nTESTE DO BACKEND LOCAL (whisper.cpp real) PASSOU")


if __name__ == "__main__":
    main()
