#!/usr/bin/env bash
# Instala o whisper.cpp no Mac (M1/ARM64) com o modelo multilíngue Small.
# Não remove nem modifica nada que já existe -- só instala o que falta.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WHISPER_DIR="$REPO_DIR/local/whisper.cpp"
MODEL_NAME="small"

echo "== 1/4: verificando Homebrew =="
if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew não encontrado. Instale primeiro: https://brew.sh"
  echo "Depois rode este script de novo."
  exit 1
fi

echo "== 2/4: verificando cmake e ffmpeg =="
brew list cmake >/dev/null 2>&1 || brew install cmake
brew list ffmpeg >/dev/null 2>&1 || brew install ffmpeg

echo "== 3/4: compilando whisper.cpp (Metal é ativado automaticamente em Apple Silicon) =="
if [ ! -d "$WHISPER_DIR" ]; then
  git clone --depth 1 https://github.com/ggml-org/whisper.cpp "$WHISPER_DIR"
fi
cmake -B "$WHISPER_DIR/build" -S "$WHISPER_DIR" -DCMAKE_BUILD_TYPE=Release
cmake --build "$WHISPER_DIR/build" -j"$(sysctl -n hw.ncpu)" --config Release

echo "== 4/4: baixando modelo multilíngue Small (GGML) =="
bash "$WHISPER_DIR/models/download-ggml-model.sh" "$MODEL_NAME"

echo ""
echo "Pronto. Binário em: $WHISPER_DIR/build/bin/whisper-cli"
echo "Modelo em:          $WHISPER_DIR/models/ggml-${MODEL_NAME}.bin"
echo ""
echo "Instalando dependências Python (faster-whisper não é usado no Mac -- só o núcleo comum):"
python3 -m pip install --quiet --upgrade pip
echo "Pronto para rodar. Veja docs/INSTALACAO_MAC.md para o comando de teste."
