#!/bin/bash
# Prepara o kit Edite Reels para rodar no Claude Code na nuvem (app no celular ou navegador) ou em Linux.
# Idempotente: pode rodar quantas vezes quiser; o que já existe é pulado.
# Variáveis opcionais: SKIP_WHISPER=1 (não instala a transcrição), SKIP_MODELS=1 (não baixa modelos).
set -u
cd "$(dirname "$0")/.."
KIT="$PWD"
VENV="${VENV:-$HOME/.venvs/whisper}"
aviso() { echo "  aviso: $*"; }
passo() { echo; echo "[$1] $2"; }

passo 1/5 "Dependências do kit (HyperFrames + GSAP)"
if [ -d node_modules/hyperframes ] && [ -d node_modules/gsap ]; then echo "  ok: já instaladas"
else npm install --no-audit --no-fund || { echo "ERRO: npm install falhou"; exit 1; }; fi

passo 2/5 "Navegador de renderização"
if [ -z "${HYPERFRAMES_BROWSER_PATH:-}" ]; then
  for c in /opt/pw-browsers/chromium_headless_shell-*/chrome-linux/headless_shell \
           /opt/pw-browsers/chromium-*/chrome-linux/chrome /opt/pw-browsers/chromium \
           "$(command -v chromium 2>/dev/null)" "$(command -v google-chrome 2>/dev/null)"; do
    [ -n "$c" ] && [ -x "$c" ] && { export HYPERFRAMES_BROWSER_PATH="$c"; break; }
  done
fi
if [ -n "${HYPERFRAMES_BROWSER_PATH:-}" ]; then echo "  ok: usando $HYPERFRAMES_BROWSER_PATH"
else npx --yes hyperframes browser ensure || aviso "navegador não instalou; o render não vai funcionar"; fi

passo 3/5 "FFmpeg"
if command -v ffmpeg >/dev/null && ffmpeg -hide_banner -encoders 2>/dev/null | grep -q libx264; then echo "  ok: $(ffmpeg -version | head -1 | cut -d' ' -f1-3)"
else aviso "ffmpeg com libx264 não encontrado (apt-get install -y ffmpeg)"; fi

passo 4/5 "Transcrição local (faster-whisper)"
if [ "${SKIP_WHISPER:-0}" = 1 ]; then echo "  pulado (SKIP_WHISPER=1)"
else
  if ! "$VENV/bin/python" -c "import faster_whisper" >/dev/null 2>&1; then
    mkdir -p "$(dirname "$VENV")"
    python3 -m venv "$VENV" && "$VENV/bin/python" -m pip install --quiet --disable-pip-version-check --only-binary=:all: --upgrade pip faster-whisper onnxruntime \
      || aviso "faster-whisper não instalou"
    "$VENV/bin/python" -m pip install --quiet --disable-pip-version-check --only-binary=:all: mediapipe opencv-python \
      || aviso "mediapipe não instalou; a /vsl usa legenda fixa"
  else echo "  ok: faster-whisper já instalado"; fi
  if [ "${SKIP_MODELS:-0}" != 1 ] && "$VENV/bin/python" -c "import faster_whisper" >/dev/null 2>&1; then
    "$VENV/bin/python" -c "from faster_whisper import WhisperModel; [WhisperModel(m, device='cpu', compute_type='int8') for m in ('small','medium')]; print('  ok: modelos prontos')" \
      || aviso "modelos não baixaram (huggingface.co precisa estar liberado na rede do ambiente)"
  fi
fi

passo 5/5 "Pastas e teste"
mkdir -p meus-videos video-projects
bash scripts/teste-instalacao.sh && echo && echo "PRONTO!"
