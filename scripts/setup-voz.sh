#!/bin/bash
# Opcional: instala o motor de voz (TTS / clonagem / dublagem) usado pelo VoiceStudio em CPU: omnivoice.cpp + pesos GGUF.
# Substitui a ElevenLabs para narração. Baixa ~660 MB de pesos e compila (uns 5 min). Idempotente.
# Versões fixadas: as mesmas que o VoiceStudio fixa em backend/engines/omnivoice_gguf/quant_map.json.
set -e
D="${OMNIVOICE_DIR:-$HOME/.cache/edite-reels/omnivoice.cpp}"
RUNTIME_SHA=040c8b344d8c670ce1475194751d119b5ef82c78
GGML_SHA=d5152bf4348453068aa8de0d479caef40a613b9d
MODEL_REV=361609388ae572a820d085185bbbe2a2aac4b30e
QUANT="${OMNIVOICE_QUANT:-Q4_K_M}"   # Q4_K_M (CPU, ~660 MB) · Q8_0 (~945 MB) · BF16 (~1,6 GB)
command -v cmake >/dev/null && command -v g++ >/dev/null || { echo "ERRO: precisa de cmake e g++ (apt-get install -y cmake g++)"; exit 1; }

if [ ! -x "$D/build/omnivoice-tts" ]; then
  mkdir -p "$D" && cd "$D"
  [ -d .git ] || { git init -q && git remote add origin https://github.com/ServeurpersoCom/omnivoice.cpp; }
  GIT_LFS_SKIP_SMUDGE=1 git fetch -q --depth 1 origin "$RUNTIME_SHA" && git checkout -q FETCH_HEAD
  mkdir -p ggml && cd ggml
  [ -d .git ] || { git init -q && git remote add origin https://github.com/ServeurpersoCom/ggml.git; }
  GIT_LFS_SKIP_SMUDGE=1 git fetch -q --depth 1 origin "$GGML_SHA" && git checkout -q FETCH_HEAD
  cd "$D" && mkdir -p build && cd build
  cmake .. -DCMAKE_BUILD_TYPE=Release >/dev/null && cmake --build . --config Release -j "$(nproc)" --target omnivoice-tts omnivoice-codec
else echo "ok: omnivoice-tts já compilado"; fi

mkdir -p "$D/models" && cd "$D/models"
for f in omnivoice-base-$QUANT.gguf omnivoice-tokenizer-$QUANT.gguf; do
  [ -s "$f" ] && { echo "ok: $f"; continue; }
  curl -fL --retry 3 -sS -o "$f.tmp" "https://huggingface.co/Serveurperso/OmniVoice-GGUF/resolve/$MODEL_REV/$f" && mv "$f.tmp" "$f" && echo "baixado: $f"
done
echo "PRONTO: voz instalada em $D"
