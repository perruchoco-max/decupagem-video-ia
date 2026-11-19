#!/bin/bash
# Gera fala em português a partir de texto (CPU). Uso:
#   scripts/falar.sh "texto" saida.wav [--ref-wav voz.wav --ref-text voz.txt] [--steps 10] [--seed 1] [--lang Portuguese]
#   scripts/falar.sh arquivo.txt saida.wav ...      (se o 1º argumento for um arquivo, lê o texto dele)
#   scripts/falar.sh --srt legenda.srt saida.wav --ref-wav voz.wav --ref-text voz.txt   (dublagem: uma fala por trecho do SRT)
# Em CPU o ritmo é lento: ~22x o tempo do áudio com 32 passos (padrão) e ~8x com --steps 10.
set -e
D="${OMNIVOICE_DIR:-$HOME/.cache/edite-reels/omnivoice.cpp}"
QUANT="${OMNIVOICE_QUANT:-Q4_K_M}"
[ -x "$D/build/omnivoice-tts" ] || { echo "Motor de voz não instalado. Rode: bash scripts/setup-voz.sh"; exit 1; }
[ $# -ge 2 ] || { sed -n 2,7p "$0"; exit 1; }
IN="$1"; OUT="$2"; shift 2
LANG_ARG="Portuguese"; EXTRA=()
while [ $# -gt 0 ]; do case "$1" in --lang) LANG_ARG="$2"; shift 2;; *) EXTRA+=("$1"); shift;; esac; done
COMUM=(--model "$D/models/omnivoice-base-$QUANT.gguf" --codec "$D/models/omnivoice-tokenizer-$QUANT.gguf" --lang "$LANG_ARG" -o "$OUT")
if [ "$IN" = "--srt" ]; then
  SRT="${EXTRA[0]}"; EXTRA=("${EXTRA[@]:1}")
  "$D/build/omnivoice-tts" "${COMUM[@]}" --srt "$SRT" "${EXTRA[@]}"
elif [ -f "$IN" ]; then
  "$D/build/omnivoice-tts" "${COMUM[@]}" "${EXTRA[@]}" < "$IN"
else
  printf '%s\n' "$IN" | "$D/build/omnivoice-tts" "${COMUM[@]}" "${EXTRA[@]}"
fi
echo "ok: $OUT ($(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT")s)"
