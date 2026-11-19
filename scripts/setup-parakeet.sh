#!/bin/bash
# Opcional: instala o NVIDIA Parakeet TDT v3 (o motor local do OpenWhispr) para usar com
#   transcribe-local-whisper.py --engine parakeet     (ou EDITE_ASR=parakeet)
# ~670 MB. Em teste interno ficou mais rápido que o Whisper small, mas perdeu uma palavra ("doze mil" -> "1"):
# o padrão continua sendo o Whisper. Use o Parakeet só para comparar.
set -e
VENV="${VENV:-$HOME/.venvs/whisper}"
D="${PARAKEET_DIR:-$HOME/.cache/edite-reels/parakeet-v3}"
"$VENV/bin/python" -m pip install --quiet --disable-pip-version-check --only-binary=:all: sherpa-onnx numpy
mkdir -p "$D" && cd "$D"
B=https://huggingface.co/csukuangfj/sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8/resolve/main
for f in encoder.int8.onnx decoder.int8.onnx joiner.int8.onnx tokens.txt; do
  [ -s "$f" ] && { echo "ok: $f"; continue; }
  curl -fL --retry 3 -sS -o "$f.tmp" "$B/$f" && mv "$f.tmp" "$f" && echo "baixado: $f"
done
echo "PRONTO: Parakeet em $D"
