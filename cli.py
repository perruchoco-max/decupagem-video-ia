#!/usr/bin/env python3
"""Linha de comando única para os dois modos. Mesmo núcleo, muda só o backend.

Modo local (Mac):
  python3 cli.py --modo local --whisper-cli local/whisper.cpp/build/bin/whisper-cli \\
      --modelo local/whisper.cpp/models/ggml-small.bin entrada.mp4 pasta_saida/

Modo nuvem:
  python3 cli.py --modo nuvem entrada.mp4 pasta_saida/
"""
import argparse
import sys

from core.transcribe import CloudFasterWhisperBackend, LocalWhisperCppBackend
from core.pipeline import run_conservative


def main():
    ap = argparse.ArgumentParser(description="Decupagem inteligente de vídeos/áudios")
    ap.add_argument("entrada", help="arquivo de vídeo ou áudio a decupar")
    ap.add_argument("saida", help="pasta onde salvar os resultados")
    ap.add_argument("--modo", choices=["local", "nuvem"], default="nuvem")
    ap.add_argument("--idioma", default="pt")
    ap.add_argument("--whisper-cli", default="whisper-cli", help="(modo local) caminho do binário")
    ap.add_argument("--modelo", default="local/whisper.cpp/models/ggml-small.bin",
                     help="(modo local) caminho do modelo .bin")
    ap.add_argument("--modelo-nuvem", default="small", help="(modo nuvem) tamanho do modelo faster-whisper")
    args = ap.parse_args()

    if args.modo == "local":
        backend = LocalWhisperCppBackend(binary_path=args.whisper_cli, model_path=args.modelo)
    else:
        backend = CloudFasterWhisperBackend(model_size=args.modelo_nuvem)

    resultado = run_conservative(args.entrada, args.saida, backend, language=args.idioma)

    print(f"\nConcluído. Duração: {resultado['duracao_original_s']:.1f}s -> "
          f"{resultado['duracao_final_s']:.1f}s")
    print(f"Arquivo final: {resultado['arquivo_final']}")
    print(f"Trechos duvidosos (revise antes de publicar): {resultado['trechos_duvidosos']}")
    print(f"Relatório completo: {resultado['saidas']['relatorio_md']}")


if __name__ == "__main__":
    sys.exit(main())
